"""C6-40 geometry precompute phase adapter tests (L0/L1, synthetic tiles).

Unless a test is explicitly marked ``real-scene``, every tile here is a
synthetic workload: tiny GDAL rasters written per test plus a stub phase
worker (real numba native mask, synthetic store payloads) driven through the
real scheduler subprocess protocol.  Delays inject adversarial completion
orders; they are correctness injections, not timing measurements (contended
host: no elapsed-time claims are made anywhere).

The one ``real-scene`` test runs the REAL worker module and the C6-10 recipe
producer end-to-end on three small raster tiles (<=96 square) plus a serial
in-process reference production for bitwise comparison.  No 1024 run.
"""
from __future__ import annotations

import dataclasses
import json
import os
from pathlib import Path
import sys
import textwrap
import time

import pytest

os.environ.setdefault('NUMBA_NUM_THREADS', '2')  # in-process serial reference parity

REPO = Path(__file__).resolve().parents[3]
SRC = REPO / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from solweig_light.runtime import (  # noqa: E402
    ResourceAdmissionError,
    RuntimeOptions,
    TileExecutionError,
)
from solweig_light.runtime_phases import (  # noqa: E402
    GEOMETRY_PHASE_WORKER,
    GeometryPhaseJob,
    PHASE_STAGE_SCHEMA,
    execute_geometry_phase,
    geometry_phase_jobs,
)


# ---------------------------------------------------------------------------
# Fixtures: tiny real rasters (geometry identities fingerprint raster bytes)
# and a stub phase worker speaking the persistent protocol.
# ---------------------------------------------------------------------------

SIZE = 16
TRANSFORM = (583017.5 - SIZE / 2, 1.0, 0.0, 4506984.0 + SIZE / 2, 0.0, -1.0)


def _write_tiff(path: Path, values, size: int = SIZE) -> None:
    import numpy as np
    from osgeo import gdal, osr

    gdal.UseExceptions()
    path.parent.mkdir(parents=True, exist_ok=True)
    dataset = gdal.GetDriverByName('GTiff').Create(str(path), size, size, 1, gdal.GDT_Float32)
    dataset.SetGeoTransform(TRANSFORM)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(32618)
    dataset.SetProjection(srs.ExportToWkt())
    dataset.GetRasterBand(1).WriteArray(np.asarray(values, dtype=np.float32))
    dataset = None


def synthetic_tile_paths(root: Path, tile: str, variant: int) -> dict[str, str]:
    """Three tiny rasters whose content depends on ``variant`` (distinct keys)."""
    import numpy as np

    base = np.full((SIZE, SIZE), 3.0, dtype=np.float32)
    building = base.copy()
    building[4:12, 4:12] += 10.0 + variant
    trees = np.zeros_like(base)
    trees[2:4, 6:8] = 6.0 + variant
    folder = root / tile
    for name, values in (('Building_DSM', building), ('Trees', trees), ('DEM', base)):
        _write_tiff(folder / f'{name}_{tile}.tif', values)
    return {name: str(folder / f'{name}_{tile}.tif')
            for name in ('Building_DSM', 'Trees', 'DEM')}


@dataclasses.dataclass(frozen=True)
class StubJob(GeometryPhaseJob):
    """Test knobs carried inside the scheduler's own job payload."""

    delay_seconds: float = 0.0
    fail_with: str | None = None
    crash: bool = False
    lie_mask: int | None = None

    def to_dict(self):
        return dict(
            super().to_dict(),
            delay_seconds=self.delay_seconds,
            fail_with=self.fail_with,
            crash=self.crash,
            lie_mask=self.lie_mask,
        )


STUB_WORKER = textwrap.dedent(
    """
    import argparse, json, os, sys, time
    from pathlib import Path

    EVENTS = os.environ.get('SOLWEIG_PHASE_STUB_EVENTS')

    def _event(kind, order):
        if not EVENTS:
            return
        with open(EVENTS, 'a') as stream:
            stream.write(json.dumps(
                {'event': kind, 'order': order, 't': time.time(),
                 'pid': os.getpid()}) + '\\n')

    def _pin(configured):
        import numba
        if int(numba.config.NUMBA_NUM_THREADS) != configured:
            raise AssertionError(
                'numba config %d != configured %d'
                % (numba.config.NUMBA_NUM_THREADS, configured))
        numba.set_num_threads(configured)
        if int(numba.get_num_threads()) != configured:
            raise AssertionError('mask mismatch after set_num_threads')
        return numba

    def _kernel_entry_mask(numba):
        import numpy as np
        from numba import njit, prange
        @njit(parallel=True)
        def probe(values):
            total = 0.0
            for i in prange(values.size):
                total += values[i]
            return total
        assert probe(np.ones(8)) == 8.0  # first parallel kernel = kernel entry
        return int(numba.get_num_threads())

    def _atomic_json(path, payload):
        tmp = path.with_name(path.name + '.tmp-%d' % os.getpid())
        tmp.write_text(json.dumps(payload, sort_keys=True))
        os.replace(tmp, path)

    def _run(job_path):
        payload = json.loads(job_path.read_text())
        job = payload['job']
        order = job['order']
        _event('start', order)
        try:
            time.sleep(job.get('delay_seconds') or 0.0)
            if job.get('crash'):
                os._exit(9)
            if job.get('fail_with'):
                raise ValueError(job['fail_with'])
            configured = int(payload['configured_threads'])
            numba = _pin(configured)
            mask = _kernel_entry_mask(numba)
            from solweig_light.cache import GeometryStore
            from solweig_light.cache.geometry import _manifest_digest
            from solweig_light.geometry.recipe import numerical_geometry_recipe
            recipe = numerical_geometry_recipe(job['paths'], job['patch_option'])
            store = GeometryStore(payload['store_root'])
            key = store.key_for(recipe.identity)
            fake_arrays = {'svf': {'name': 'g/svf.npy',
                                   'shape': [job['rows'], job['cols']],
                                   'fingerprint': {'size_bytes': 4,
                                                   'sha256': '0' * 64}}}
            manifest = {'format': 'stub', 'version': 1,
                        'model_version': 'p6-geometry-v1', 'key': key,
                        'identity': recipe.identity,
                        'arrays': fake_arrays, 'visibility': {}}
            manifest['manifest_sha256'] = _manifest_digest(manifest)
            (Path(payload['store_root']) / key).mkdir(parents=True, exist_ok=True)
            _atomic_json(Path(payload['store_root']) / key / 'manifest.json',
                         manifest)
            lie = job.get('lie_mask')
            record = {
                'schema': 'sw6-geometry-phase-stage-v1',
                'order': order, 'tile': job['tile'],
                'recipe_digest': recipe.digest,
                'native_key': key,
                'store_root': str(payload['store_root']),
                'cache_hit': False,
                'store_manifest': {
                    'manifest_sha256': manifest['manifest_sha256'],
                    'identity': recipe.identity,
                    'arrays': fake_arrays, 'visibility': {}},
                'native': {
                    'configured_threads': configured,
                    'mask_pinned': int(numba.get_num_threads()),
                    'mask_at_kernel_entry': mask if lie is None else lie,
                    'gdal_cachemax_env': os.environ.get('GDAL_CACHEMAX'),
                    'snapshot_at_import': None,
                    'snapshot_at_kernel_entry': None},
            }
            _atomic_json(job_path.with_suffix('.stage.json'), record)
            _event('stop', order)
            return 0
        except BaseException as error:
            _event('stop', order)
            try:
                _atomic_json(job_path.with_suffix('.failure.json'), {
                    'schema_version': 1,
                    'exception_type': type(error).__name__,
                    'exception_module': type(error).__module__,
                    'args': list(error.args), 'message': str(error)})
            except BaseException:
                pass
            return 1

    def main():
        parser = argparse.ArgumentParser()
        parser.add_argument('--job', required=True)
        parser.add_argument('--options', required=True)
        args = parser.parse_args()
        job_path = Path(args.job)
        code = _run(job_path)
        pool = os.environ.get('SOLWEIG_LIGHT_WORKER_POOL')
        if pool is None:
            return code
        pid = os.getpid()
        (Path(pool) / ('stub-worker-%d.pid' % pid)).write_text(str(pid))
        marker = job_path.with_suffix('.done')
        tmp = marker.with_name(marker.name + '.tmp-%d' % pid)
        tmp.write_text(json.dumps({'returncode': code}))
        os.replace(tmp, marker)
        while True:
            line = sys.stdin.readline()
            if not line:
                return 0
            nxt = Path(line.strip())
            if not nxt.name:
                continue
            code = _run(nxt)
            marker = nxt.with_suffix('.done')
            tmp = marker.with_name(marker.name + '.tmp-%d' % pid)
            tmp.write_text(json.dumps({'returncode': code}))
            os.replace(tmp, marker)

    if __name__ == '__main__':
        raise SystemExit(main())
    """
)


@pytest.fixture()
def stub_module(tmp_path, monkeypatch):
    module = tmp_path / "phase_stub.py"
    module.write_text(STUB_WORKER, encoding="utf-8")
    events = tmp_path / "stub-events.jsonl"
    monkeypatch.setenv("SOLWEIG_PHASE_STUB_EVENTS", str(events))
    monkeypatch.setenv(
        "PYTHONPATH",
        os.pathsep.join((str(tmp_path), str(SRC), os.environ.get("PYTHONPATH", ""))),
    )
    return "phase_stub"


def make_options(**overrides) -> RuntimeOptions:
    fields = dict(cache_enabled=True, memory_budget_bytes=64 * 1024**3,
                  cpu_budget=4, workers=2, threads_per_worker=2)
    fields.update(overrides)
    return RuntimeOptions(**fields)


def make_jobs(tiles: list[StubJob]) -> list[StubJob]:
    return tiles


def job_tiles(count: int, variant_base: int = 0, **knobs) -> list[StubJob]:
    """Synthetic jobs in original order; rows/cols are honest-tiny accounting."""
    tiles = []
    for index in range(count):
        tiles.append(StubJob(
            order=index,
            tile=f"{index}_{index}",
            paths={name: f"placeholder-{name}" for name in
                   ("Building_DSM", "Trees", "DEM")},
            patch_option=2,
            rows=64, cols=64, patches=153, windchannels=12, block_pixels=128,
            **knobs,
        ))
    return tiles


def fixture_jobs(root: Path, count: int, **knobs) -> list[StubJob]:
    """Jobs whose paths point at real tiny rasters (parent rebuilds recipes)."""
    tiles = []
    for index in range(count):
        tile = f"{index}_{index}"
        tiles.append(StubJob(
            order=index, tile=tile,
            paths=synthetic_tile_paths(root / "inputs" / tile, tile, index),
            patch_option=2,
            rows=SIZE, cols=SIZE, patches=153, windchannels=12, block_pixels=128,
            **knobs,
        ))
    return tiles


def journal_events(publication_root: Path) -> list[dict]:
    journal = publication_root / "publication.journal.jsonl"
    return [json.loads(line) for line in
            journal.read_text(encoding="utf-8").splitlines() if line.strip()]


def published_tiles(publication_root: Path) -> list[int]:
    return sorted(int(path.parent.name.split("-")[1]) for path in
                  publication_root.glob("tile-*/result.json"))


def max_concurrency(events: list[dict]) -> int:
    live = 0
    peak = 0
    for entry in sorted(events, key=lambda item: (item["t"], item["event"] != "start")):
        live += 1 if entry["event"] == "start" else -1
        peak = max(peak, live)
    return peak


# ---------------------------------------------------------------------------
# L0: descriptor and module-level contracts
# ---------------------------------------------------------------------------

def test_module_is_inert_until_wired():
    """The module stays private: only the integrator-owned api.py hook
    (C6-40 integration, _precompute_geometry_phase) may reference it.

    Worker-era form asserted nothing in src mentions runtime_phases; the
    C6-40 integration fulfills that premise's purpose (a private, unwired
    adapter) by wiring exactly one reference from api.py, so the adapted
    contract pins the single legal reference site."""
    offenders = []
    for path in (SRC).rglob("*.py"):
        if path.name == "runtime_phases.py" or "__pycache__" in path.parts:
            continue
        if "runtime_phases" in path.read_text(encoding="utf-8", errors="replace"):
            offenders.append(str(path))
    assert offenders == [str(SRC / 'solweig_light' / 'api.py')], offenders


def test_job_descriptor_json_round_trip_and_memory_dimension(tmp_path):
    job = GeometryPhaseJob(
        order=0, tile="0_0",
        paths=synthetic_tile_paths(tmp_path / "inputs" / "0_0", "0_0", 0),
        patch_option=2, rows=SIZE, cols=SIZE, patches=153,
        windchannels=12, block_pixels=128,
    )
    restored = GeometryPhaseJob.from_dict(json.loads(json.dumps(job.to_dict())))
    assert restored == job
    memory = restored.memory_job
    assert memory.phase == "geometry"
    assert memory.tile == "0_0"
    assert (memory.rows, memory.cols, memory.patches) == (SIZE, SIZE, 153)
    assert memory.visibility_mode == "unknown_cold"


def test_job_descriptor_rejects_incomplete_sources_and_bad_orders(tmp_path):
    good = synthetic_tile_paths(tmp_path / "inputs" / "a", "a", 0)
    with pytest.raises(ValueError, match="missing numerical geometry input"):
        GeometryPhaseJob(order=0, tile="a", paths={"Building_DSM": good["Building_DSM"]},
                         patch_option=2, rows=1, cols=1, patches=153,
                         windchannels=12, block_pixels=128)
    with pytest.raises(ValueError, match="order"):
        GeometryPhaseJob(order=-1, tile="a", paths=good, patch_option=2,
                         rows=1, cols=1, patches=153, windchannels=12, block_pixels=128)
    built = geometry_phase_jobs(
        [{"tile": f"{i}_{i}", "paths": good, "rows": 1, "cols": 1, "patches": 153}
         for i in range(3)],
        patch_option=2, windchannels=12, block_pixels=128,
    )
    assert [item.order for item in built] == [0, 1, 2]


def test_scheduler_requires_cache_enabled_and_unique_ordered_tiles(tmp_path, stub_module):
    options = make_options(cache_enabled=False)
    with pytest.raises(ValueError, match="cache_enabled"):
        execute_geometry_phase(job_tiles(1), options,
                               publication_root=tmp_path / "pub",
                               store_root=tmp_path / "store",
                               worker_module=stub_module)
    options = make_options()
    duplicated = job_tiles(2)
    with pytest.raises(ValueError, match="unique"):
        execute_geometry_phase(
            [duplicated[0], dataclasses.replace(duplicated[1], order=1, tile="0_0")],
            options, publication_root=tmp_path / "pub",
            store_root=tmp_path / "store", worker_module=stub_module)
    with pytest.raises(ValueError, match="contiguous"):
        execute_geometry_phase([dataclasses.replace(duplicated[0], order=3)],
                               options, publication_root=tmp_path / "pub",
                               store_root=tmp_path / "store", worker_module=stub_module)


# ---------------------------------------------------------------------------
# Gate 1: ordered publication under adversarial completion orders
# ---------------------------------------------------------------------------

def test_ordered_publication_survives_reversed_completion_orders(tmp_path, stub_module):
    publication = tmp_path / "pub"
    jobs = fixture_jobs(tmp_path, 5)
    delays = [2.0, 0.6, 0.4, 0.2, 0.0]  # tile 0 finishes LAST
    jobs = [dataclasses.replace(job, delay_seconds=delays[job.order])
            for job in jobs]
    options = make_options(workers=2, cpu_budget=4)

    outcome = execute_geometry_phase(jobs, options,
                                     publication_root=publication,
                                     store_root=tmp_path / "store",
                                     worker_module=stub_module,
                                     gdal_cache_bytes=1 * 1024 * 1024)

    assert published_tiles(publication) == [0, 1, 2, 3, 4]
    events = journal_events(publication)
    commits = [entry["order"] for entry in events if entry["event"] == "commit"]
    # The one load-bearing ordering property: commits are exactly the original
    # sorted order, regardless of the observed completion order.
    assert commits == [0, 1, 2, 3, 4]
    begins = [entry["order"] for entry in events if entry["event"] == "begin"]
    assert begins == [0, 1, 2, 3, 4]
    # Staged-prefix ceremony: a tile is begun only after the previous tile's
    # commit line exists.
    last_commit_position = -1
    for position, entry in enumerate(events):
        if entry["event"] == "commit":
            assert entry["order"] == last_commit_position + 1
            last_commit_position = entry["order"]
        elif entry["event"] == "begin":
            assert entry["order"] == last_commit_position + 1
    # Adversarial sanity: the injected delays really did reverse completion.
    stub_events = [json.loads(line) for line in
                   (tmp_path / "stub-events.jsonl").read_text().splitlines()]
    first_stop = min((entry for entry in stub_events if entry["event"] == "stop"),
                     key=lambda entry: entry["t"])
    assert first_stop["order"] != 0

    assert [item.order for item in outcome.results] == [0, 1, 2, 3, 4]
    manifest = outcome.phase_manifest
    assert [tile["order"] for tile in manifest["tiles"]] == [0, 1, 2, 3, 4]
    assert Path(publication / "PHASE_MANIFEST.json").is_file()
    assert outcome.plan.status in ("admitted", "queued")
    assert outcome.plan.admissible_workers >= 1


def test_phase_manifest_written_last_and_digest_verifies(tmp_path, stub_module):
    publication = tmp_path / "pub"
    jobs = fixture_jobs(tmp_path, 3)
    options = make_options(workers=1, cpu_budget=2)
    execute_geometry_phase(jobs, options, publication_root=publication,
                           store_root=tmp_path / "store",
                           worker_module=stub_module,
                           gdal_cache_bytes=1 * 1024 * 1024)
    manifest = json.loads((publication / "PHASE_MANIFEST.json").read_text())
    digest = manifest.pop("manifest_sha256")
    import hashlib

    recomputed = hashlib.sha256(json.dumps(
        manifest, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")).hexdigest()
    assert digest == recomputed
    for tile in manifest["tiles"]:
        record = json.loads(
            (publication / f"tile-{tile['order']:04d}" / "result.json").read_text())
        record_digest = record.pop("record_sha256")
        recomputed = hashlib.sha256(json.dumps(
            record, sort_keys=True, separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")).hexdigest()
        assert record_digest == recomputed == tile["record_sha256"]


# ---------------------------------------------------------------------------
# Gate 2: failure semantics (identical public error, prefix-only publication,
# survivors reaped)
# ---------------------------------------------------------------------------

def test_mid_phase_failure_preserves_serial_error_and_prefix_publication(
        tmp_path, stub_module):
    publication = tmp_path / "pub"
    jobs = fixture_jobs(tmp_path, 5)
    jobs = [dataclasses.replace(job, delay_seconds=0.3) for job in jobs]
    jobs[2] = dataclasses.replace(jobs[2], delay_seconds=0.0,
                                  fail_with="tile 2 exploded")
    options = make_options(workers=2, cpu_budget=4)

    with pytest.raises(ValueError, match="tile 2 exploded"):
        execute_geometry_phase(jobs, options, publication_root=publication,
                               store_root=tmp_path / "store",
                               worker_module=stub_module,
                               gdal_cache_bytes=1 * 1024 * 1024)

    assert published_tiles(publication) == [0, 1]
    commits = [entry["order"] for entry in journal_events(publication)
               if entry["event"] == "commit"]
    assert commits == [0, 1]
    for order in (2, 3, 4):
        assert not (publication / f"tile-{order:04d}").exists()
        assert not (publication / f"tile-{order:04d}" / "result.json").exists()
    assert not (publication / "PHASE_MANIFEST.json").exists()


def test_numerically_first_failure_controls_the_public_error(tmp_path, stub_module):
    publication = tmp_path / "pub"
    jobs = fixture_jobs(tmp_path, 6)
    jobs = [dataclasses.replace(job, delay_seconds=0.5) for job in jobs]
    jobs[1] = dataclasses.replace(jobs[1], delay_seconds=1.5,
                                  fail_with="lower tile 1 failure")
    jobs[5] = dataclasses.replace(jobs[5], delay_seconds=0.1,
                                  fail_with="later tile 5 failure")
    options = make_options(workers=4, cpu_budget=4)

    with pytest.raises(ValueError, match="lower tile 1 failure"):
        execute_geometry_phase(jobs, options, publication_root=publication,
                               store_root=tmp_path / "store",
                               worker_module=stub_module,
                               failure_grace_seconds=10.0,
                               gdal_cache_bytes=1 * 1024 * 1024)
    assert published_tiles(publication) == [0]


def test_crashing_worker_surfaces_generic_error_and_prefix_holds(tmp_path, stub_module):
    publication = tmp_path / "pub"
    jobs = fixture_jobs(tmp_path, 3)
    jobs = [dataclasses.replace(job, delay_seconds=0.2) for job in jobs]
    jobs[1] = dataclasses.replace(jobs[1], crash=True)
    options = make_options(workers=2, cpu_budget=4)

    with pytest.raises(TileExecutionError, match="exit code 9"):
        execute_geometry_phase(jobs, options, publication_root=publication,
                               store_root=tmp_path / "store",
                               worker_module=stub_module,
                               gdal_cache_bytes=1 * 1024 * 1024)
    assert published_tiles(publication) == [0]


def test_live_children_are_reaped_after_first_failure(tmp_path, stub_module):
    publication = tmp_path / "pub"
    jobs = fixture_jobs(tmp_path, 4)
    jobs = [dataclasses.replace(job, delay_seconds=1.5) for job in jobs]
    jobs[0] = dataclasses.replace(jobs[0], delay_seconds=0.1,
                                  fail_with="early failure")
    options = make_options(workers=2, cpu_budget=4)

    with pytest.raises(ValueError, match="early failure"):
        execute_geometry_phase(jobs, options, publication_root=publication,
                               store_root=tmp_path / "store",
                               worker_module=stub_module,
                               gdal_cache_bytes=1 * 1024 * 1024)

    events_path = tmp_path / "stub-events.jsonl"
    deadline = time.monotonic() + 5
    pids = set()
    while time.monotonic() < deadline:
        if events_path.exists():
            pids = {entry["pid"] for entry in
                    (json.loads(line) for line in
                     events_path.read_text().splitlines() if line.strip())}
        alive = []
        for pid in pids:
            try:
                os.kill(pid, 0)
                alive.append(pid)
            except ProcessLookupError:
                pass
        if pids and not alive:
            break
        time.sleep(0.05)
    assert pids, "stub workers never recorded their pids"
    alive = []
    for pid in pids:
        try:
            os.kill(pid, 0)
            alive.append(pid)
        except ProcessLookupError:
            pass
    assert alive == [], f"survivor workers not reaped: {alive}"


# ---------------------------------------------------------------------------
# Gate 3: actual native thread caps
# ---------------------------------------------------------------------------

def test_child_native_mask_recorded_at_kernel_entry_equals_configured(
        tmp_path, stub_module):
    publication = tmp_path / "pub"
    jobs = fixture_jobs(tmp_path, 4)
    options = make_options(workers=2, cpu_budget=4, threads_per_worker=2)

    outcome = execute_geometry_phase(jobs, options, publication_root=publication,
                                     store_root=tmp_path / "store",
                                     worker_module=stub_module,
                                     gdal_cache_bytes=1 * 1024 * 1024)
    for result in outcome.results:
        assert result.native["configured_threads"] == 2
        assert result.native["mask_pinned"] == 2
        assert result.native["mask_at_kernel_entry"] == 2


def test_tampered_native_mask_is_rejected_at_publication(tmp_path, stub_module):
    publication = tmp_path / "pub"
    jobs = fixture_jobs(tmp_path, 3)
    jobs = [dataclasses.replace(job, delay_seconds=0.1) for job in jobs]
    jobs[1] = dataclasses.replace(jobs[1], lie_mask=7)
    options = make_options(workers=2, cpu_budget=4)

    with pytest.raises(ValueError, match="kernel entry"):
        execute_geometry_phase(jobs, options, publication_root=publication,
                               store_root=tmp_path / "store",
                               worker_module=stub_module,
                               gdal_cache_bytes=1 * 1024 * 1024)
    assert published_tiles(publication) == [0]


# ---------------------------------------------------------------------------
# Gate 4: memory admission honoured before dispatch
# ---------------------------------------------------------------------------

def _worst_shape_job(order: int, tile: str) -> StubJob:
    return StubJob(order=order, tile=tile,
                   paths={name: f"p-{name}" for name in
                          ("Building_DSM", "Trees", "DEM")},
                   patch_option=2, rows=1024, cols=1024, patches=153,
                   windchannels=12, block_pixels=1024)


def test_rejected_width_never_dispatches_any_child(tmp_path, stub_module):
    from solweig_light.runtime_memory import (
        DEFAULT_PARENT_FOOTPRINT_BYTES,
        TileShapeDescriptor,
        geometry_reservation,
    )

    jobs = [_worst_shape_job(index, f"{index}_{index}") for index in range(4)]
    reservation = geometry_reservation(
        TileShapeDescriptor(1024, 1024, 153, 12, 1024),
        gdal_cache_bytes=1 * 1024 * 1024,
    )
    # Two fit exactly with room to spare; four are requested.
    budget = (DEFAULT_PARENT_FOOTPRINT_BYTES + 2 * reservation.total_bytes
              + 16 * 1024 * 1024)
    options = make_options(memory_budget_bytes=budget, workers=4, cpu_budget=4,
                           threads_per_worker=1)
    publication = tmp_path / "pub"

    with pytest.raises(ResourceAdmissionError, match="only 2 fit"):
        execute_geometry_phase(jobs, options, publication_root=publication,
                               store_root=tmp_path / "store",
                               worker_module=stub_module,
                               policy="reject",
                               gdal_cache_bytes=1 * 1024 * 1024)
    assert not (tmp_path / "stub-events.jsonl").exists(), \
        "a child was dispatched despite rejection"
    assert published_tiles(publication) == []
    assert not (publication / "publication.journal.jsonl").exists()


def test_individually_infeasible_job_raises_even_under_queue(tmp_path, stub_module):
    from solweig_light.runtime_memory import (
        DEFAULT_PARENT_FOOTPRINT_BYTES,
        TileShapeDescriptor,
        geometry_reservation,
    )

    job = _worst_shape_job(0, "0_0")
    reservation = geometry_reservation(
        TileShapeDescriptor(1024, 1024, 153, 12, 1024),
        gdal_cache_bytes=1 * 1024 * 1024,
    )
    budget = DEFAULT_PARENT_FOOTPRINT_BYTES + reservation.total_bytes - 1024
    options = make_options(memory_budget_bytes=budget, workers=1, cpu_budget=1,
                           threads_per_worker=1)
    with pytest.raises(ResourceAdmissionError, match="queueing cannot make"):
        execute_geometry_phase([job], options,
                               publication_root=tmp_path / "pub",
                               store_root=tmp_path / "store",
                               worker_module=stub_module,
                               gdal_cache_bytes=1 * 1024 * 1024)


def test_admitted_width_bounds_concurrent_children(tmp_path, stub_module):
    publication = tmp_path / "pub"
    jobs = fixture_jobs(tmp_path, 4)
    jobs = [dataclasses.replace(job, delay_seconds=0.4) for job in jobs]
    options = make_options(workers=2, cpu_budget=4, threads_per_worker=2)

    outcome = execute_geometry_phase(jobs, options, publication_root=publication,
                                     store_root=tmp_path / "store",
                                     worker_module=stub_module,
                                     gdal_cache_bytes=1 * 1024 * 1024)
    assert outcome.plan.admissible_workers == 2
    events = [json.loads(line) for line in
              (tmp_path / "stub-events.jsonl").read_text().splitlines()
              if line.strip()]
    assert len({entry["pid"] for entry in events}) == 2  # persistent pool width
    assert max_concurrency(events) <= 2
    assert published_tiles(publication) == [0, 1, 2, 3]
    commits = [entry["order"] for entry in journal_events(publication)
               if entry["event"] == "commit"]
    assert commits == [0, 1, 2, 3]


def test_gdal_cachemax_env_reaches_children(tmp_path, stub_module):
    publication = tmp_path / "pub"
    jobs = fixture_jobs(tmp_path, 2)
    options = make_options(workers=1, cpu_budget=2)
    outcome = execute_geometry_phase(jobs, options,
                                     publication_root=publication,
                                     store_root=tmp_path / "store",
                                     worker_module=stub_module,
                                     gdal_cache_bytes=1 * 1024 * 1024)
    # m7 §1 W3: the child sees the calculator's per-worker allowance in MB,
    # placed before its first import.
    for result in outcome.results:
        assert result.native["gdal_cachemax_env"] == "1"


# ---------------------------------------------------------------------------
# Real-scene end-to-end (labeled): real worker + C6-10 recipe producer.
# Three raster tiles <=96 square; correctness only, no timing claims.
# ---------------------------------------------------------------------------

REFERENCE_SCENE = REPO / 'tests' / 'reference' / 'small_original_cpu' / 'scene'


def _real_tiles(root: Path) -> list[GeometryPhaseJob]:
    """Three genuinely distinct small raster tiles derived from the pinned
    reference scene (byte content differs, so every recipe key is distinct)."""
    import numpy as np
    from osgeo import gdal

    gdal.UseExceptions()
    tiles = []
    for index in range(3):
        tile = f"{index}_{index}"
        folder = root / "inputs" / tile
        folder.mkdir(parents=True, exist_ok=True)
        paths = {}
        shape = None
        for name in ("Building_DSM", "Trees", "DEM"):
            source = gdal.Open(str(REFERENCE_SCENE / f"{name}.tif"))
            values = source.GetRasterBand(1).ReadAsArray()
            transform = source.GetGeoTransform()
            projection = source.GetProjection()
            source = None
            shape = values.shape
            if name == "Building_DSM" and index >= 1:
                values = values + np.float32(2 * index)  # deterministic height shift
            if name == "Trees" and index == 2:
                values[2:6, 8:14] = np.float32(6.0)
            target = folder / f"{name}.tif"
            dataset = gdal.GetDriverByName('GTiff').Create(
                str(target), values.shape[1], values.shape[0], 1, gdal.GDT_Float32)
            dataset.SetGeoTransform(transform)
            dataset.SetProjection(projection)
            dataset.GetRasterBand(1).WriteArray(values)
            dataset = None
            paths[name] = str(target)
        tiles.append(GeometryPhaseJob(
            order=index, tile=tile, paths=paths, patch_option=2,
            rows=shape[0], cols=shape[1], patches=153,
            windchannels=12, block_pixels=128,
        ))
    return tiles


def test_real_scene_phase_matches_serial_production_bitwise(tmp_path):
    """Real worker, real recipe producer, 3 tiles (35x32): the phase-published
    store generation is bitwise identical to a serial in-process production,
    one production per logical tile across two phase runs, ordered publication
    holds, and the actual native mask equals the configured one."""
    pytest.importorskip("osgeo")
    publication = tmp_path / "pub"
    store_root = tmp_path / "store"
    jobs = _real_tiles(tmp_path)
    options = make_options(workers=2, cpu_budget=4, threads_per_worker=2,
                           memory_budget_bytes=12 * 1024**3)

    first = execute_geometry_phase(jobs, options, publication_root=publication,
                                   store_root=store_root)
    assert [item.order for item in first.results] == [0, 1, 2]
    assert [item.tile for item in first.results] == ["0_0", "1_1", "2_2"]
    assert all(item.cache_hit is False for item in first.results)
    for result in first.results:
        assert result.native["mask_pinned"] == 2
        assert result.native["mask_at_kernel_entry"] == 2
    assert published_tiles(publication) == [0, 1, 2]
    commits = [entry["order"] for entry in journal_events(publication)
               if entry["event"] == "commit"]
    assert commits == [0, 1, 2]

    # Serial in-process reference for tile 0_0 through the same store type:
    # the phase must have produced exactly what the serial producer produces.
    from solweig_light.cache import GeometryStore
    from solweig_light.cache.geometry import _read_json
    from solweig_light.geometry.recipe import numerical_geometry_recipe

    recipe = numerical_geometry_recipe(jobs[0].paths, jobs[0].patch_option)
    serial_store = GeometryStore(tmp_path / "serial-store")
    handle = serial_store.get_or_create(recipe.identity, recipe.produce)
    try:
        serial_manifest = _read_json(serial_store.root / handle.key / "manifest.json")
    finally:
        handle.close()
    phase_manifest = _read_json(
        Path(store_root) / first.results[0].native_key / "manifest.json")

    # Generation directories and native payload files are named randomly per
    # publication (uuid/generation names, mkstemp payload names).  Array
    # fingerprints hash deterministic .npy bytes, so stripping names is
    # enough there.  A visibility entry's own fingerprint hashes the JSON
    # file bytes including its random payload name, so it is excluded; the
    # content oracle is the encoded payload digest (exactly what the store
    # validates when it re-opens a generation), plus shape and patch table.
    def strip_names(value):
        if isinstance(value, dict):
            return {key: strip_names(item) for key, item in value.items()
                    if key != "name"}
        if isinstance(value, list):
            return [strip_names(item) for item in value]
        return value

    def visibility_content(manifest):
        return {channel: strip_names(
                    {key: value for key, value in entry.items()
                     if key not in ("name", "fingerprint")})
                for channel, entry in manifest["visibility"].items()}

    assert strip_names(phase_manifest["arrays"]) == strip_names(serial_manifest["arrays"])
    assert (visibility_content(phase_manifest)
            == visibility_content(serial_manifest))
    assert phase_manifest["identity"] == serial_manifest["identity"]

    # Second phase run over the same store: zero new productions (one
    # production per logical tile), records still published in order.
    second = execute_geometry_phase(jobs, options,
                                    publication_root=tmp_path / "pub2",
                                    store_root=store_root)
    assert all(item.cache_hit is True for item in second.results)
    for result in second.results:
        assert result.native["mask_pinned"] == 2
        assert result.native["mask_at_kernel_entry"] is None
