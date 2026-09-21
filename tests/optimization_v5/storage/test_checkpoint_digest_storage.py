"""S07 checkpoint digest+IO reductions stay byte-identical (L0/L1).

Three independent guarantees on the tiny real ``small_original_cpu`` scene:
write-time buffer digests equal the read-back digests that recovery compares
against disk (including NaN payloads, signed zeros, denormals and layout
corners); a real 24-step run records digests that match independent read-back
of the published TIFFs and durable state payloads; and SIGKILL at a committed
checkpoint followed by resume reproduces the reference outputs bitwise.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import numpy as np
import pytest
from osgeo import gdal

from solweig_light.io.rasters import RasterMetadata, StreamingOutputs
from solweig_light.persistence import _band_digest, _digest, _stored_bytes_digest
from solweig_light.runtime import RuntimeOptions, execute_tiles

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "runtime"))
from worker_helpers import (  # noqa: E402
    PIPELINE_MEMORY_BUDGET,
    prepare_scene,
    tile_job,
)

MET = np.zeros((1, 4))
MET[:, 2] = [6]
MET[:, 3] = [30]
META = RasterMetadata(3, 4, (1.0, 2.0, 0.0, 8.0, 0.0, -2.0), "")

ADVERSARIAL = {
    "quiet_nan": np.full((3, 4), np.nan, dtype=np.float32),
    "negative_zero": np.full((3, 4), -0.0, dtype=np.float32),
    "positive_zero": np.zeros((3, 4), dtype=np.float32),
    "signed_zero_mix": np.where(np.arange(12).reshape(3, 4) % 2 == 0,
                                np.float32(-0.0), np.float32(0.0)),
    "infinity": np.full((3, 4), np.inf, dtype=np.float32),
    "denormal": np.full((3, 4), np.nextafter(np.float32(0), np.float32(1))),
    "float64_rounding": np.full((3, 4), 1 / 3),
    "fortran_order": np.asfortranarray(
        np.arange(12, dtype=np.float32).reshape(3, 4) * np.float32(1.5)),
    "big_endian": np.arange(12, dtype=">f4").reshape(3, 4),
    "mixed_nan_pattern": np.where(np.arange(12).reshape(3, 4) % 3 == 0,
                                  np.nan, np.arange(12).reshape(3, 4)).astype(np.float32),
    "zero_with_signbit_rows": np.where(np.arange(12).reshape(3, 4) // 4 == 1,
                                       np.float32(-0.0), np.float32(7.5)),
}


@pytest.mark.parametrize("name", sorted(ADVERSARIAL))
def test_recorded_digest_matches_read_back_digest(tmp_path, name):
    values = ADVERSARIAL[name]
    with StreamingOutputs(tmp_path, "0_0", META, MET, "2020-07-18", ("UTCI",)) as writer:
        writer.write(0, {"UTCI": values})
    dataset = gdal.Open(str(tmp_path / "UTCI_0_0.tif"))
    band = dataset.GetRasterBand(1)
    recorded = _stored_bytes_digest(band, values)
    assert recorded == _band_digest(band, META.rows, META.cols), name


def raster_identity(path):
    """Content identity of a finished raster: band values, georeferencing, timestamps.

    The internal TIFF byte layout is deliberately excluded: a resumed dataset
    is rewritten through a GDAL update cycle, which relocates its directory
    and strip offsets even when every pixel, tag and timestamp is identical.
    """
    dataset = gdal.Open(str(path))
    return ([_band_digest(dataset.GetRasterBand(i + 1), dataset.RasterYSize, dataset.RasterXSize)
             for i in range(dataset.RasterCount)],
            tuple(dataset.GetGeoTransform()), dataset.GetProjection(),
            [dataset.GetRasterBand(i + 1).GetMetadata() for i in range(dataset.RasterCount)])


def payload_entries(value):
    if isinstance(value, dict):
        if value.get("type") in ("array", "scalar") and "file" in value:
            yield value
        else:
            for item in value.values():
                yield from payload_entries(item)
    elif isinstance(value, list):
        for item in value:
            yield from payload_entries(item)


@pytest.mark.parametrize("name", sorted(ADVERSARIAL))
def test_npy_serialization_digest_matches_durable_file(tmp_path, name):
    array = np.asarray(ADVERSARIAL[name])
    with io.BytesIO() as buffer:
        np.save(buffer, array, allow_pickle=False)
        payload = buffer.getvalue()
    path = tmp_path / "array-0.npy"
    with open(path, "xb") as target:
        np.save(target, array, allow_pickle=False)
    assert hashlib.sha256(payload).hexdigest() == _digest(path)


def test_recorded_checkpoint_digests_match_published_bytes(tmp_path):
    base = tmp_path / "run"
    prepared = prepare_scene(base)
    results = execute_tiles([tile_job(base / "out", prepared)],
                            RuntimeOptions(memory_budget_bytes=PIPELINE_MEMORY_BUDGET,
                                           threads_per_worker=1))
    assert [item.returncode for item in results] == [0]

    record_path = next((base / "out" / ".solweig-light" / "transactions").glob("*/transaction.json"))
    checkpoint = json.loads(record_path.read_text())["checkpoint"]
    assert checkpoint["next_timestep"] == 24

    # The state manifest digest recorded at commit time (computed from the
    # serialized buffer) equals the durable file's digest.
    generation = record_path.parent / checkpoint["generation"]
    assert checkpoint["state_sha256"] == _digest(generation / "state.json")
    state = json.loads((generation / "state.json").read_text())
    for entry in payload_entries(state):
        assert _digest(generation / entry["file"]) == entry["sha256"]

    # Every recorded band digest matches an independent GDAL read-back of the
    # published artifact -- the identity the old re-read implementation gave.
    for name, hashes in checkpoint["band_hashes"].items():
        dataset = gdal.Open(str(base / "out" / "output_folder" / "0_0" / f"{name}_0_0.tif"))
        assert dataset.RasterCount == len(hashes)
        for index, recorded in enumerate(hashes):
            digest = _band_digest(dataset.GetRasterBand(index + 1),
                                  dataset.RasterYSize, dataset.RasterXSize)
            assert digest == recorded, (name, index)


RESUME_CHILD = """\
import json, sys
from solweig_light.runtime import RuntimeOptions, execute_tiles
with open(sys.argv[1]) as source:
    job = json.load(source)
options = RuntimeOptions(memory_budget_bytes=4 * 1024**3, workers=1, threads_per_worker=1)
sys.exit(execute_tiles([job], options)[0].returncode)
"""


def test_checkpoint_kill_then_resume_is_bitwise(tmp_path):
    # Reference: one clean full run.
    reference_base = tmp_path / "reference"
    reference_prepared = prepare_scene(reference_base)
    results = execute_tiles([tile_job(reference_base / "out", reference_prepared)],
                            RuntimeOptions(memory_budget_bytes=PIPELINE_MEMORY_BUDGET,
                                           threads_per_worker=1))
    assert [item.returncode for item in results] == [0]
    reference_identities = {path.name: raster_identity(path) for path in
                            sorted((reference_base / "out" / "output_folder" / "0_0").glob("*.tif"))}
    assert reference_identities

    # Crash run: SIGKILL the whole process group once a committed checkpoint
    # exists past step 5.
    crash_base = tmp_path / "crash"
    prepared = prepare_scene(crash_base)
    job = tile_job(crash_base / "out", prepared)
    job_path = crash_base / "job.json"
    job_path.write_text(json.dumps(job, default=str))
    child = subprocess.Popen([sys.executable, "-c", RESUME_CHILD, str(job_path)],
                             stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                             start_new_session=True)
    transactions = crash_base / "out" / ".solweig-light" / "transactions"
    record_path = None
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        if record_path is None:
            found = list(transactions.glob("*/transaction.json"))
            record_path = found[0] if found else None
        elif record_path.exists():
            try:
                checkpoint = json.loads(record_path.read_text()).get("checkpoint")
            except (OSError, ValueError):
                checkpoint = None
            if checkpoint is not None and checkpoint["next_timestep"] >= 5:
                break
        if child.poll() is not None:
            _, err = child.communicate()
            raise AssertionError(
                f"crash run exited early rc={child.returncode}: {err.decode()[-2000:]}")
        time.sleep(0.02)
    else:
        os.killpg(child.pid, signal.SIGKILL)
        raise AssertionError("checkpoint cursor never reached step 5")
    os.killpg(child.pid, signal.SIGKILL)
    child.wait(timeout=60)
    checkpoint = json.loads(record_path.read_text())["checkpoint"]
    assert 5 <= checkpoint["next_timestep"] < 24

    # Resume through the same pool machinery: recovery validates every
    # committed band on disk against the recorded write-time digests, then
    # the remaining steps are written, checkpointed and published.
    results = execute_tiles([job], RuntimeOptions(memory_budget_bytes=PIPELINE_MEMORY_BUDGET,
                                                  threads_per_worker=1, resume=True))
    assert [item.returncode for item in results] == [0]
    for name, identity in reference_identities.items():
        assert raster_identity(crash_base / "out" / "output_folder" / "0_0" / name) == identity, name
