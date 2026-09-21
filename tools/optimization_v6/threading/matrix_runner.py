#!/usr/bin/env python3
"""C6-01 H-matrix runner: fresh child per requested H, collected records.

For each H (default 1, 2, 4) a NEW child process is started with native limits
in its environment before any numerical import; the child runs the dense256
full-chronology run_tile workload and reports its actual native mask and GVF
route. Host facts (macOS sysctl, affinity absence, load) are recorded once.

Run: matrix_runner.py --out <json> [--threads 1 2 4] [--run-root <dir>]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from thread_limits import child_environment, host_facts, heavy_jobs, write_json  # noqa: E402

PARSER = argparse.ArgumentParser(description=__doc__)
PARSER.add_argument("--threads", type=int, nargs="+", default=[1, 2, 4])
PARSER.add_argument("--python", default=sys.executable)
PARSER.add_argument("--site", default=None)
PARSER.add_argument("--scene-src", default=None)
PARSER.add_argument("--run-root", default=None)
PARSER.add_argument("--out", required=True)
ARGS = PARSER.parse_args()

RUN_ROOT = Path(ARGS.run_root).resolve() if ARGS.run_root else Path(ARGS.out).resolve().parent / "matrix_runs"
RUN_ROOT.mkdir(parents=True, exist_ok=True)
TIMEOUT_S = 600

records = []
for threads in ARGS.threads:
    run_root = RUN_ROOT / f"h{threads}"
    out_json = run_root / "record.json"
    cmd = [ARGS.python, str(Path(__file__).resolve().parent / "child_runner.py"),
           "--threads", str(threads), "--label", "isolated", "--out", str(out_json)]
    if ARGS.site:
        cmd += ["--site", ARGS.site]
    if ARGS.scene_src:
        cmd += ["--scene-src", ARGS.scene_src]
    started = time.monotonic()
    proc = subprocess.run(cmd, env=child_environment(threads, str(run_root / "numba_cache")),
                          capture_output=True, text=True, timeout=TIMEOUT_S)
    entry = {"requested_threads": threads,
             "child_stdout_tail": proc.stdout.strip().splitlines()[-3:],
             "child_stderr_tail": proc.stderr.strip().splitlines()[-15:],
             "returncode": proc.returncode,
             "wall_s": round(time.monotonic() - started, 3)}
    if proc.returncode == 0 and out_json.exists():
        entry["record"] = json.loads(out_json.read_text())
    else:
        entry["status"] = "FAILED"  # preserved honestly, never skipped
    records.append(entry)

summary = []
for entry in records:
    if "record" not in entry:
        summary.append({"requested_threads": entry["requested_threads"], "status": "FAILED"})
        continue
    rec = entry["record"]
    summary.append({
        "requested_threads": rec["requested"]["threads_per_worker"],
        "label": rec["requested"]["label"],
        "numba_config_threads": rec["numba"]["config_NUMBA_NUM_THREADS"],
        "final_native_mask": rec["numba"]["final_get_num_threads"],
        "threading_layer": rec["numba"]["threading_layer"],
        "threading_layer_error": rec["numba"]["threading_layer_error"],
        "requested_workers": rec["admission"]["requested_workers"],
        "plan_active_workers": rec["admission"]["plan_active_workers"],
        "plan_native_threads": rec["admission"]["plan_native_threads"],
        "route_counts": rec["route"]["observed_counts"],
        "route_first_entry_mask": (rec["route"]["first_kernel_entry"] or {})
        .get("numba_get_num_threads"),
        "run_tile_s": rec["timing_s"]["run_tile_total"],
        "peak_rss_bytes": rec["peak_rss_bytes"],
        "workload_shape": rec["workload"]["actual_shape"],
        "math_profile_id": rec["math_profile"]["id"],
        "math_profile_fingerprint": rec["math_profile"]["fingerprint"],
        "solweig_module": rec["module_origin"]["solweig_light"],
    })

payload = {
    "schema": "sw6-thread-matrix-v1",
    "commit_under_test": subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True,
        cwd=str(Path(__file__).resolve().parents[3])).stdout.strip(),
    "host_facts": host_facts(),
    "heavy_jobs_at_start": heavy_jobs(),
    "timeout_s_per_child": TIMEOUT_S,
    "records": records,
    "summary": summary,
}
write_json(Path(ARGS.out), payload)
print(json.dumps({"out": ARGS.out, "summary": summary}, indent=1))
