#!/usr/bin/env python3
"""C6-101r PHASE 1 scheduler: frozen in-sim attribution slots, one child at a time.

Exclusive-benchmark-lease discipline: sequential single children only, no
pytest/builds alongside, loadavg + ps snapshot (thread_limits.heavy_jobs)
before and after EVERY run.  The schedule is frozen before the first run:

  0 prime    (discarded; cold JIT + fresh run dir)
  1-3 wall   x3 warm reps, fresh child each (profiler distortion reference)
  4 profile  warm cProfile run (pstats dump)

All slots: integrated tree, tile 0_0, threads 4, 3600 s per-slot timeout.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
CAMPAIGN = TOOLS.parent
sys.path.insert(0, str(TOOLS))
from thread_limits import child_environment, host_facts, heavy_jobs, write_json  # noqa: E402

INTEGRATED = Path("/Users/alansynn/Workspace/solweig-light-claude-v5")
SCENE = CAMPAIGN / "scenes" / "scene_t1024"
RUN_ROOT = CAMPAIGN / "runs" / "profile_t1024_tile0_0"
PYTHON = "/Users/alansynn/Workspace/solweig-light/.venv-light/bin/python"
TILE = "0_0"
THREADS = 4
TIMEOUT_S = 3600.0

SLOTS = ([{"mode": "prime", "rep": 0}]
         + [{"mode": "wall", "rep": rep} for rep in range(3)]
         + [{"mode": "profile", "rep": 0}])

OUT_PATH = CAMPAIGN / "phase1_profile.json"


def run_slot(index: int, step: dict) -> dict:
    mode = step["mode"]
    record_path = RUN_ROOT / "records" / f"{mode}_r{step['rep']}.json"
    pstats_path = RUN_ROOT / "pstats" / f"{mode}_r{step['rep']}.pstats" if mode == "profile" else None
    cmd = [PYTHON, str(TOOLS / "profile_child.py"),
           "--site", str(INTEGRATED / "src"),
           "--scene-src", str(SCENE),
           "--run-root", str(RUN_ROOT),
           "--tile", TILE,
           "--threads", str(THREADS),
           "--mode", mode,
           "--out", str(record_path)]
    if pstats_path:
        cmd += ["--pstats", str(pstats_path)]
    env = child_environment(THREADS, str(RUN_ROOT / "numba_cache"))
    before = heavy_jobs()
    started = time.monotonic()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_S, env=env)
        returncode, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
        timed_out = False
    except subprocess.TimeoutExpired as error:
        def _text(value):
            if value is None:
                return ""
            return value.decode(errors="replace") if isinstance(value, bytes) else value
        returncode, stdout, stderr = None, _text(error.stdout), _text(error.stderr)
        timed_out = True
    wall = round(time.monotonic() - started, 3)
    after = heavy_jobs()
    entry = {"slot": index, **step, "wall_s": wall, "returncode": returncode,
             "timed_out": timed_out, "host_before": before, "host_after": after,
             "stderr_tail": stderr.strip().splitlines()[-15:] if stderr else []}
    if returncode == 0 and record_path.exists():
        child = json.loads(record_path.read_text())
        entry["stages_s"] = child["stage_splits_s"]
        entry["native_mask"] = child["numba"]["final_get_num_threads"]
        entry["set_num_threads_error"] = child["numba"]["set_num_threads_error"]
        entry["route_counts"] = child["route"]["observed_counts"]
        entry["output_digest"] = child["output_digest"]["digest"]
        entry["module_origin"] = child["module_origin"]["solweig_light"]
        entry["math_profile_id"] = child["math_profile"].get("profile_id")
    else:
        entry["status"] = "FAILED_OR_TIMED_OUT"  # preserved, never skipped
        entry["stdout_tail"] = stdout.strip().splitlines()[-8:] if stdout else []
    with open(OUT_PATH.with_suffix(".jsonl"), "a") as stream:
        stream.write(json.dumps(entry) + "\n")
    return entry


def main() -> int:
    payloads = {
        "schema": "sw6-campaign-synthetic-phase1-v1",
        "label": "SYNTHETIC 1024^2 in-sim residual attribution; dev-tier single-lease",
        "protocol": {
            "scene": str(SCENE), "tile": TILE, "threads": THREADS,
            "transport": "chronology-probe in-process run_tile loop (execute_tiles swap)",
            "temps": {"prime": "cold JIT, fresh run dir; timing discarded",
                      "wall": "warm JIT + warm caches, NO profiler, fresh child per rep",
                      "profile": "warm, cProfile around the same in-process simulate region"},
            "timeout_s_per_slot": TIMEOUT_S,
            "lease": "sequential single children only; unrelated OS/browser activity "
                     "recorded via loadavg+ps per slot, never claimed absent",
        },
        "host_facts": host_facts(),
        "scene_manifest": json.loads((CAMPAIGN / "scene_manifest.json").read_text()),
        "schedule": SLOTS,
        "slots": [],
    }
    write_json(OUT_PATH, payloads)  # frozen BEFORE the first measured run
    OUT_PATH.with_suffix(".jsonl").unlink(missing_ok=True)

    for index, step in enumerate(SLOTS):
        entry = run_slot(index, step)
        payloads["slots"].append(entry)
        write_json(OUT_PATH, payloads)
        ok = entry.get("status") != "FAILED_OR_TIMED_OUT"
        print(json.dumps({"slot": index, "mode": step["mode"], "ok": ok,
                          "sim_s": entry.get("stages_s", {}).get("simulation_total_wall"),
                          "loop_s": entry.get("stages_s", {}).get("simulation_in_process_loop"),
                          "route_counts": entry.get("route_counts")}), flush=True)
    print(json.dumps({"out": str(OUT_PATH), "slots": len(payloads["slots"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
