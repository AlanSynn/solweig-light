#!/usr/bin/env python3
"""C5-62 monitored final installed-wheel run for the two 1024 fixtures.

Adapted from the v4 qualification harness
(reports/characterization/local_cpu_optimization_v1/qualification/
final_combined_v1/large_harness/run_final_large.py). Differences: repo root is
the integration worktree, the installed wheel target is the C5-61 freeze
site-packages, RSS sampling uses stdlib `ps` (psutil is not installed), and
runs land under optimization_v5_claude/evidence/final_batch/runs_v1/.

This evidence harness is deliberately local. It does not alter the package,
tests, or the frozen comparison protocol.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import time

LIMIT = 12 * 1024**3
RESERVE = 10 * 1024**3
REPO = Path("/Users/alansynn/Workspace/solweig-light-claude-v5")
CASES = ("dense1024", "vegetation1024")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ps_table() -> dict[int, tuple[int, int]]:
    """One `ps` snapshot: pid -> (ppid, rss_kb)."""
    out = subprocess.run(["ps", "-axo", "pid=,ppid=,rss="], capture_output=True, text=True).stdout
    table = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) != 3:
            continue
        try:
            table[int(parts[0])] = (int(parts[1]), int(parts[2]))
        except ValueError:
            continue
    return table


def tree_rss(root_pid: int, table: dict[int, tuple[int, int]]) -> int:
    children: dict[int, list[int]] = {}
    for pid, (ppid, _rss) in table.items():
        children.setdefault(ppid, []).append(pid)
    total = 0
    seen = set()
    stack = [root_pid]
    while stack:
        pid = stack.pop()
        if pid in seen:
            continue
        seen.add(pid)
        entry = table.get(pid)
        if entry is None:
            continue
        total += max(0, entry[1]) * 1024
        stack.extend(children.get(pid, ()))
    return total


def available_bytes(path: Path) -> int:
    return int(shutil.disk_usage(path).free)


def child(args: argparse.Namespace) -> int:
    run = args.run.resolve()
    scene = run / "scene"
    scene.mkdir(parents=True, exist_ok=False)
    fixture = args.fixture.resolve()
    for name in ("Building_DSM.tif", "Trees.tif", "DEM.tif", "met.txt", "manifest.json"):
        shutil.copy2(fixture / name, scene / name)
    kwargs = json.loads(args.kwargs.read_text())
    kwargs["base_path"] = str(scene)
    kwargs["own_met_file"] = str(scene / "met.txt")
    (run / "kwargs_used.json").write_text(json.dumps(kwargs, indent=2, sort_keys=True) + "\n")

    import solweig_light
    from solweig_light import thermal_comfort, RuntimeOptions, runtime_options
    from solweig_light.radiation._math_profile import profile_identity
    origins = {}
    for name in ("solweig_light", "solweig_light.api", "solweig_light.pipeline",
                 "solweig_light.runtime", "solweig_light.geometry.service",
                 "solweig_light.radiation.engine"):
        module = __import__(name, fromlist=["*"])
        origin = Path(module.__file__).resolve()
        if args.site.resolve() not in origin.parents:
            raise RuntimeError(f"module escaped installed target: {name}={origin}")
        origins[name] = str(origin)
    if "torch" in sys.modules:
        raise RuntimeError("installed candidate imported torch")
    options = RuntimeOptions(memory_budget_bytes=LIMIT, cpu_budget=4, workers=1,
                             threads_per_worker=4, block_pixels=1024,
                             checkpoint_interval=1, cache_enabled=True,
                             legacy_cache_policy="recompute")
    started = time.perf_counter()
    with runtime_options(options):
        result = thermal_comfort(**kwargs)
    elapsed = time.perf_counter() - started
    if result is not None:
        raise RuntimeError(f"thermal_comfort returned {result!r}")
    outputs = sorted((scene / "output_folder" / "0_0").glob("*.tif"))
    expected = {"TMRT", "UTCI", "Kup", "Kdown", "Lup", "Ldown", "Shadow", "WBGT", "Ta", "Wind"}
    actual = {path.name.split("_0_0.tif")[0] for path in outputs}
    if actual != expected or len(outputs) != 10:
        raise RuntimeError(f"output fields differ: {sorted(actual)}")
    import osgeo.gdal as gdal
    for path in outputs:
        ds = gdal.Open(str(path))
        if ds.RasterCount != 24 or (ds.RasterYSize, ds.RasterXSize) != (1024, 1024):
            raise RuntimeError(f"unexpected output shape/bands: {path}")
    manifest = {
        "schema": "claude-v5-final-batch-large-candidate.v1",
        "case": args.case,
        "package_origin": str(Path(solweig_light.__file__).resolve()),
        "module_origins": origins,
        "profile": profile_identity(),
        "runtime_options": options.as_dict(),
        "torch_imported": "torch" in sys.modules,
        "elapsed_diagnostic_seconds": elapsed,
        "performance_claim": False,
        "fixture_manifest_sha256": digest(scene / "manifest.json"),
        "outputs": [{"path": str(path.relative_to(run)), "bytes": path.stat().st_size,
                     "sha256": digest(path)} for path in outputs],
    }
    (run / "candidate_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"case": args.case, "elapsed": elapsed, "outputs": len(outputs)}, sort_keys=True), flush=True)
    return 0


def monitor(args: argparse.Namespace) -> int:
    run = args.run.resolve()
    run.mkdir(parents=True, exist_ok=False)
    stdout_path, stderr_path = run / "stdout.log", run / "stderr.log"
    samples_path = run / "rss_samples.jsonl"
    env = os.environ.copy()
    env.update({"PYTHONPATH": str(args.site.resolve()), "PYTHONNOUSERSITE": "1",
                "PYTHONDONTWRITEBYTECODE": "1", "NUMBA_NUM_THREADS": "4",
                "OMP_NUM_THREADS": "4", "OPENBLAS_NUM_THREADS": "4",
                "MKL_NUM_THREADS": "4", "NUMEXPR_NUM_THREADS": "4",
                "VECLIB_MAXIMUM_THREADS": "4", "BLIS_NUM_THREADS": "4",
                "NUMBA_CACHE_DIR": str((run / "numba_cache").resolve()),
                "CUDA_VISIBLE_DEVICES": ""})
    command = [sys.executable, __file__, "--child", "--case", args.case,
               "--run", str(run), "--fixture", str(args.fixture),
               "--kwargs", str(args.kwargs), "--site", str(args.site)]
    started = time.perf_counter()
    peak = 0
    samples = 0
    aborted = False
    abort_reason = None
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr, samples_path.open("w") as samples_file:
        process = subprocess.Popen(command, cwd=str(REPO), env=env, stdout=stdout, stderr=stderr,
                                   start_new_session=True)
        while process.poll() is None:
            value = tree_rss(process.pid, ps_table())
            if value > 0:
                peak = max(peak, value)
                samples += 1
                samples_file.write(json.dumps({"monotonic": time.monotonic(), "rss": value}) + "\n")
                samples_file.flush()
            if value > LIMIT:
                aborted = True
                abort_reason = "process_tree_rss_limit_exceeded"
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                break
            time.sleep(0.020)
        if aborted:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        exit_code = process.wait()
    elapsed = time.perf_counter() - started
    record = {"schema": "claude-v5-final-batch-large-monitor.v1",
              "case": args.case, "command": command, "exit_code": exit_code,
              "aborted": aborted, "abort_reason": abort_reason,
              "limit_bytes": LIMIT, "disk_reserve_bytes": RESERVE,
              "available_disk_before_bytes": args.disk_before,
              "available_disk_after_bytes": available_bytes(REPO),
              "peak_summed_process_tree_rss_bytes": peak, "positive_rss_samples": samples,
              "sample_interval_seconds": 0.020, "elapsed_seconds": elapsed,
              "performance_claim": False}
    (run / "monitor.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    return 0 if exit_code == 0 and not aborted and peak > 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=CASES, required=True)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--kwargs", type=Path, required=True)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--child", action="store_true")
    args = parser.parse_args()
    if args.child:
        return child(args)
    if available_bytes(REPO) < RESERVE:
        raise RuntimeError("disk reserve unavailable before large run")
    args.disk_before = available_bytes(REPO)
    return monitor(args)


if __name__ == "__main__":
    raise SystemExit(main())
