"""Real-scene checks for the persistent worker pool (L1/L2).

References are the tiny real ``small_original_cpu`` scene; single-execution
references run through the same thread-limited subprocess machinery so the
bitwise comparison is not affected by parent-process threading.  Worker RSS
is sampled with stdlib ``ps`` diagnostics, not timed benchmarks.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

import pytest

from solweig_light.runtime import RuntimeOptions, execute_tiles

from worker_helpers import (
    FLAGS,
    PIPELINE_MEMORY_BUDGET,
    WorkerMonitor,
    child_worker_pids,
    extend_met_file,
    prepare_scene,
    tiff_digests,
    tile_job,
)


def watch_worker_pids(observed: set[int], stop: threading.Event) -> None:
    while not stop.is_set():
        observed |= child_worker_pids()
        time.sleep(0.05)


def test_persistent_batch_matches_single_execution_bitwise(tmp_path):
    flags_variants = (
        FLAGS,
        {name: value for name, value in FLAGS.items()
         if name not in ("save_wbgt", "save_ta", "save_wind")},
        {name: value for name, value in FLAGS.items() if name not in ("save_wbgt",)},
    )
    options = RuntimeOptions(memory_budget_bytes=PIPELINE_MEMORY_BUDGET,
                             cpu_budget=2, workers=2, threads_per_worker=1)

    # References: each job alone, through the same isolated child machinery.
    references = []
    for index, flags in enumerate(flags_variants):
        base = tmp_path / f"reference-{index}"
        prepared = prepare_scene(base)
        results = execute_tiles([tile_job(base / "out", prepared, flags=flags)],
                                RuntimeOptions(memory_budget_bytes=PIPELINE_MEMORY_BUDGET))
        assert [item.returncode for item in results] == [0]
        references.append(tiff_digests(base / "out"))
    assert all(references)

    # Batch: three heterogeneous-flag jobs on the two admitted workers.
    jobs = []
    for index, flags in enumerate(flags_variants):
        base = tmp_path / f"batch-{index}"
        prepared = prepare_scene(base)
        jobs.append(tile_job(base / "out", prepared, flags=flags))
    observed: set[int] = set()
    stop = threading.Event()
    watcher = threading.Thread(target=watch_worker_pids, args=(observed, stop), daemon=True)
    watcher.start()
    try:
        results = execute_tiles(jobs, options)
    finally:
        stop.set()
        watcher.join(timeout=10)
    assert [(item.index, item.tile, item.returncode) for item in results] == [
        (0, "0_0", 0), (1, "0_0", 0), (2, "0_0", 0)]
    # Three jobs ran on exactly the two admitted persistent workers.
    assert len(observed) == 2, observed
    for index in range(3):
        digests = tiff_digests(tmp_path / f"batch-{index}" / "out")
        assert digests == references[index], f"job {index} outputs differ"


def test_worker_rss_plateaus_across_sequential_jobs(tmp_path):
    prepared = prepare_scene(tmp_path)
    bases = [tmp_path / f"job-{index}" / "out" for index in range(3)]
    jobs = [tile_job(base, prepared) for base in bases]
    # Default options: one worker (cpu_budget=1) serves the whole batch.
    options = RuntimeOptions(memory_budget_bytes=PIPELINE_MEMORY_BUDGET)
    with WorkerMonitor(bases) as monitor:
        results = execute_tiles(jobs, options)
    assert [(item.index, item.returncode) for item in results] == [(0, 0), (1, 0), (2, 0)]
    assert len(monitor.pids) == 1, monitor.pids
    after_first = monitor.rss_after(0)
    after_second = monitor.rss_after(1)
    after_third = monitor.rss_after(2)
    growth = max(after_second, after_third) - after_first
    print(f"RSS KiB after jobs 1/2/3 on one worker: "
          f"{after_first} {after_second} {after_third}; growth {growth}")
    # No tile state may accumulate across jobs: the worker plateaus after the
    # first (JIT-warming) job instead of growing with each assignment.
    assert growth < 0.15 * after_first, (after_first, after_second, after_third, growth)


def test_injected_failure_cancels_the_batch_and_reaps_workers(tmp_path):
    prepared = prepare_scene(tmp_path)
    extend_met_file(prepared, days=32)  # the long job must outlast the failure
    long_base = tmp_path / "long" / "out"
    bad_job = tile_job(tmp_path / "bad" / "out", prepared)
    bad_job["paths"] = dict(bad_job["paths"],
                            metfiles=str(tmp_path / "missing" / "metfile_0_0.txt"))
    jobs = [tile_job(long_base, prepared), bad_job,
            tile_job(tmp_path / "queued" / "out", prepared)]
    options = RuntimeOptions(memory_budget_bytes=PIPELINE_MEMORY_BUDGET,
                             cpu_budget=2, workers=2)
    started = time.monotonic()
    with pytest.raises(FileNotFoundError, match="No such file"):
        execute_tiles(jobs, options)
    elapsed = time.monotonic() - started
    assert elapsed < 150, elapsed
    # The queued job was cancelled before it started; the failing job's
    # payload was rebuilt from the child's failure file.
    assert not (tmp_path / "queued" / "out" / "output_folder").exists()
    deadline = time.monotonic() + 5
    while child_worker_pids() and time.monotonic() < deadline:
        time.sleep(0.1)
    assert not child_worker_pids(), "worker processes survived cancellation"


def test_one_shot_worker_entry_still_runs(tmp_path):
    base = tmp_path / "scene"
    prepared = prepare_scene(base)
    job = tile_job(base / "out", prepared)
    # The scheduler normalizes job values with runtime._json_safe; the raw
    # one-shot payload must already be JSON-serializable here.
    job["paths"] = {name: os.fspath(path) for name, path in job["paths"].items()}
    job_file = base / "job.json"
    job_file.write_text(json.dumps(job), encoding="utf-8")
    options = json.dumps(RuntimeOptions(memory_budget_bytes=PIPELINE_MEMORY_BUDGET).as_dict())
    env = os.environ.copy()
    for name in ("NUMBA_NUM_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                 "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
                 "BLIS_NUM_THREADS"):
        env[name] = "1"
    env.pop("SOLWEIG_LIGHT_WORKER_POOL", None)
    result = subprocess.run(
        [sys.executable, "-m", "solweig_light.runtime_worker",
         "--job", str(job_file), "--options", options],
        env=env, cwd=str(Path(__file__).resolve().parents[3]),
        capture_output=True, text=True, timeout=240,
    )
    assert result.returncode == 0, result.stderr[-2000:]
    digests = tiff_digests(base / "out")
    assert "UTCI_0_0.tif" in digests
    assert not Path(str(job_file)).with_suffix(".failure.json").exists()
