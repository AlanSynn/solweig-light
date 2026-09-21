"""L0 protocol checks for the persistent worker pool: stub workers only.

The stubs pin the worker-side protocol contract claimed by
``solweig_light.runtime``: a one-shot module exits after its single ``--job``;
a protocol-aware module records each job, publishes ``<job>.done`` containing
``{"returncode": ...}``, and serves further job paths from stdin until
end-of-input.  No numerical pipeline is exercised here.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from solweig_light.runtime import RuntimeOptions, TileExecutionError, execute_tiles


# Records every job it is given, dies on demand, and speaks the serve
# protocol only when the scheduler's pool variable is present.
SERVE_STUB = """
    import argparse, json, os, sys
    from pathlib import Path
    parser = argparse.ArgumentParser()
    parser.add_argument('--job'); parser.add_argument('--options')
    args = parser.parse_args()

    def run(path):
        job = json.loads(Path(path).read_text())
        record = f"{job['tile']}:{os.getpid()}:{os.environ['OMP_NUM_THREADS']}\\n"
        Path(os.environ['STUB_MARKER']).open('a').write(record)
        if job.get('die'):
            os._exit(70)
        code = int(job.get('code', 0))
        Path(path).with_suffix('.done').write_text(json.dumps({'returncode': code}))
        return code

    run(args.job)
    if os.environ.get('SOLWEIG_LIGHT_WORKER_POOL'):
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            run(line.strip())
"""

# A worker module without any protocol support, matching today's one-shot
# entry and the existing unit-test stubs.
ONESHOT_STUB = """
    import argparse, json, os
    from pathlib import Path
    parser = argparse.ArgumentParser()
    parser.add_argument('--job'); parser.add_argument('--options')
    args = parser.parse_args()
    job = json.loads(Path(args.job).read_text())
    Path(os.environ['STUB_MARKER']).open('a').write(
        f"{job['tile']}:{os.getpid()}:{os.environ['OMP_NUM_THREADS']}\\n")
"""


@pytest.fixture
def stub_factory(tmp_path, monkeypatch):
    def install(name: str, source: str) -> str:
        module = tmp_path / name
        module.write_text(textwrap.dedent(source), encoding="utf-8")
        monkeypatch.setenv("PYTHONPATH", os_pathsep_join(tmp_path))
        monkeypatch.setenv("STUB_MARKER", str(tmp_path / "marker.txt"))
        return name.removesuffix(".py")
    return install


def os_pathsep_join(directory: Path) -> str:
    import os

    current = os.environ.get("PYTHONPATH", "")
    return os.pathsep.join((str(directory), *(part for part in current.split(os.pathsep) if part)))


def records(tmp_path: Path) -> list[tuple[str, str, str]]:
    return [tuple(line.split(":"))
            for line in (tmp_path / "marker.txt").read_text().splitlines()]


def stub_options(**overrides) -> RuntimeOptions:
    return RuntimeOptions(memory_budget_bytes=1_000_000, **overrides)


def test_persistent_worker_serves_whole_batch_on_the_admitted_pool(tmp_path, stub_factory):
    module = stub_factory("serve_stub.py", SERVE_STUB)
    options = stub_options(cpu_budget=2, workers=2, threads_per_worker=1)
    jobs = [{"tile": f"t{index}", "memory_estimate_bytes": 10} for index in range(4)]
    results = execute_tiles(jobs, options, worker_module=module)
    assert [(item.index, item.tile, item.returncode) for item in results] == [
        (0, "t0", 0), (1, "t1", 0), (2, "t2", 0), (3, "t3", 0)]
    rows = records(tmp_path)
    assert len(rows) == 4
    # The admission plan allows two workers; four jobs must run on exactly
    # those two processes instead of one process per tile.
    assert len({row[1] for row in rows}) == 2
    assert {row[2] for row in rows} == {"1"}


def test_one_shot_worker_modules_keep_the_per_job_behavior(tmp_path, stub_factory):
    module = stub_factory("oneshot_stub.py", ONESHOT_STUB)
    options = stub_options(cpu_budget=2, workers=2, threads_per_worker=1)
    jobs = [{"tile": f"t{index}", "memory_estimate_bytes": 10} for index in range(3)]
    results = execute_tiles(jobs, options, worker_module=module)
    assert [item.tile for item in results] == ["t0", "t1", "t2"]
    rows = records(tmp_path)
    assert len(rows) == 3
    # Without protocol support every job respawns a fresh one-shot child.
    assert len({row[1] for row in rows}) == 3


def test_persistent_child_honors_threads_per_worker(tmp_path, stub_factory):
    module = stub_factory("serve_stub.py", SERVE_STUB)
    options = stub_options(cpu_budget=2, workers=1, threads_per_worker=2)
    jobs = [{"tile": f"t{index}", "memory_estimate_bytes": 10} for index in range(3)]
    results = execute_tiles(jobs, options, worker_module=module)
    assert len(results) == 3
    rows = records(tmp_path)
    assert len(rows) == 3
    # One worker serves all three jobs, and every assignment observes the
    # native thread limit the scheduler placed in the child environment.
    assert len({row[1] for row in rows}) == 1
    assert {row[2] for row in rows} == {"2"}


def test_dead_persistent_worker_fails_the_batch_deterministically(tmp_path, stub_factory):
    module = stub_factory("serve_stub.py", SERVE_STUB)
    options = stub_options()
    jobs = [{"tile": "t0", "memory_estimate_bytes": 10},
            {"tile": "boom", "die": 1, "memory_estimate_bytes": 10},
            {"tile": "never", "memory_estimate_bytes": 10}]
    with pytest.raises(TileExecutionError, match="exit code 70"):
        execute_tiles(jobs, options, worker_module=module)
    tiles = [row[0] for row in records(tmp_path)]
    assert tiles == ["t0", "boom"]  # the queued job is cancelled, not reassigned


def test_marker_reported_failures_raise_without_killing_the_protocol(tmp_path, stub_factory):
    module = stub_factory("serve_stub.py", SERVE_STUB)
    options = stub_options()
    jobs = [{"tile": "t0", "code": 1, "memory_estimate_bytes": 10},
            {"tile": "never", "memory_estimate_bytes": 10}]
    with pytest.raises(TileExecutionError, match="tile job 0 failed with exit code 1"):
        execute_tiles(jobs, options, worker_module=module)
    assert [row[0] for row in records(tmp_path)] == ["t0"]
