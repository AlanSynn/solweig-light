#!/usr/bin/env python3
"""C6-01 paired L2 timing: child-isolated H=1 vs H=4 vs the old-style label.

Design (predeclared before any run):
  - 3 alternating pairs on the dense256 scene, order H1,H4 / H4,H1 / H1,H4;
    every run is a FRESH child process (native limits before first import).
  - A third "old_style" label reproduces the old portfolio harness: inherited
    environment (Numba default pool) + in-process
    RuntimeOptions(threads_per_worker=4), interleaved in the same schedule.
  - min-of-3 per label; raw seconds + metadata recorded; no profiler during
    timed runs. Host exclusivity is checked before each timed pair and
    recorded; runs are not discarded on contention, contention is reported.
  - Every child pays cold JIT (fresh NUMBA_CACHE_DIR) and a cold pipeline
    cache (fresh run dir, legacy_cache_policy=recompute) -- identical for all
    labels, inside the timer, declared.

Run: paired_timing.py --out <json> [--pairs 3] [--timeout 300]
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
PARSER.add_argument("--pairs", type=int, default=3)
PARSER.add_argument("--python", default=sys.executable)
PARSER.add_argument("--site", default=None)
PARSER.add_argument("--scene-src", default=None)
PARSER.add_argument("--run-root", default=None)
PARSER.add_argument("--timeout", type=float, default=300.0)
PARSER.add_argument("--out", required=True)
ARGS = PARSER.parse_args()

RUN_ROOT = Path(ARGS.run_root).resolve() if ARGS.run_root else Path(ARGS.out).resolve().parent / "paired_runs"
RUN_ROOT.mkdir(parents=True, exist_ok=True)

# Predeclared alternating schedule; old_style slots interleave after each pair.
SCHEDULE = []
for pair_index in range(ARGS.pairs):
    order = [("isolated", 1), ("isolated", 4)] if pair_index % 2 == 0 \
        else [("isolated", 4), ("isolated", 1)]
    SCHEDULE.append(("pair", pair_index, order))
    SCHEDULE.append(("old_style", pair_index, [("old_style", 4)]))


def run_slot(label: str, threads: int, slot_index: int) -> dict:
    run_root = RUN_ROOT / f"slot{slot_index:02d}_{label}_h{threads}"
    out_json = run_root / "record.json"
    cmd = [ARGS.python, str(Path(__file__).resolve().parent / "child_runner.py"),
           "--threads", str(threads), "--label", label, "--out", str(out_json)]
    if ARGS.site:
        cmd += ["--site", ARGS.site]
    if ARGS.scene_src:
        cmd += ["--scene-src", ARGS.scene_src]
    old_style_env = {"SOLWEIG_PAIR_LABEL": label}
    env = child_environment(threads, str(run_root / "numba_cache"), override=(label == "isolated"))
    env.update(old_style_env)
    started = time.monotonic()
    try:
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True,
                              timeout=ARGS.timeout)
        returncode, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
        timed_out = False
    except subprocess.TimeoutExpired as error:
        def _text(value) -> str:
            if value is None:
                return ""
            return value.decode(errors="replace") if isinstance(value, bytes) else value
        returncode, stdout, stderr = None, _text(error.stdout), _text(error.stderr)
        timed_out = True
    wall = round(time.monotonic() - started, 3)
    entry = {"slot": slot_index, "label": label, "requested_threads": threads,
             "wall_s": wall, "returncode": returncode, "timed_out": timed_out,
             "child_stderr_tail": stderr.strip().splitlines()[-15:]}
    record_path = run_root / "record.json"
    if returncode == 0 and record_path.exists():
        record = json.loads(record_path.read_text())
        entry["record"] = record
        entry["run_tile_s"] = record["timing_s"]["run_tile_total"]
    else:
        entry["status"] = "FAILED_OR_TIMED_OUT"  # preserved, never skipped
        entry["child_stdout_tail"] = stdout.strip().splitlines()[-5:]
    return entry


slot_index = 0
slots = []
pair_checks = []
for kind, pair_index, order in SCHEDULE:
    if kind == "pair":
        check = heavy_jobs()
        pair_checks.append({"pair": pair_index, "before_pair": check})
        if not check["exclusive_now"]:
            print(f"WARNING: host not exclusive before pair {pair_index}: "
                  f"{check['busy_non_browser']}", file=sys.stderr)
    for label, threads in order:
        slots.append(run_slot(label, threads, slot_index))
        slot_index += 1


def mins_of(label: str, threads: int) -> dict:
    runs = [slot["run_tile_s"] for slot in slots
            if slot["label"] == label and slot["requested_threads"] == threads
            and "run_tile_s" in slot]
    return {"label": f"{label}_h{threads}", "n_ok": len(runs), "all_s": runs,
            "min_s": min(runs) if runs else None,
            "median_s": sorted(runs)[len(runs) // 2] if runs else None}


labels = sorted({(slot["label"], slot["requested_threads"]) for slot in slots})
payload = {
    "schema": "sw6-thread-paired-timing-v1",
    "commit_under_test": subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True,
        cwd=str(Path(__file__).resolve().parents[3])).stdout.strip(),
    "protocol": {"tier": "L2 (real 256x256 TIFF, full 24-record chronology, 153 patches)",
                 "pairs": ARGS.pairs,
                 "schedule_predeclared": "H1/H4 alternating; old_style after each pair",
                 "per_run_timeout_s": ARGS.timeout,
                 "jit_state": "cold per child (fresh NUMBA_CACHE_DIR), inside timer",
                 "pipeline_cache": "cold fresh run dir, legacy_cache_policy=recompute",
                 "profiler": "none during timed runs",
                 "labels": {
                     "isolated_h1": "fresh child, env limits =1 before first import, "
                                    "numba.set_num_threads(1) verified",
                     "isolated_h4": "fresh child, env limits =4 before first import, "
                                    "numba.set_num_threads(4) verified",
                     "old_style_h4": "fresh child, inherited env (Numba default pool), "
                                     "in-process RuntimeOptions(threads_per_worker=4) "
                                     "only -- the old portfolio harness pattern"}},
    "host_facts": host_facts(),
    "exclusivity_checks": pair_checks,
    "slots": slots,
    "summary": [mins_of(label, threads) for label, threads in labels],
}
write_json(Path(ARGS.out), payload)
print(json.dumps({"out": ARGS.out, "summary": payload["summary"]}, indent=1))
