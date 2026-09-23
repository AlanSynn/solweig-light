#!/usr/bin/env python3
"""R04+G06 exclusive-lease warm timing: SOLWEIG_LIGHT_PATCH_CLASS_TABLES
OFF vs ON, production-shape SYNTHETIC scene (campaign scene_t1024, 4x1024^2,
24 records/tile), T4 shape (workers 1, threads 4).

Adapted from the C6-101r scheduler (campaign_synthetic/tools/run_campaign.py)
and reusing campaign_child.py + thread_limits.py verbatim. Lease discipline:
one child at a time, no pytest/builds alongside, loadavg+ps snapshot before
and after EVERY run. Schedule frozen BEFORE the first measured run:

  slot 0  priming  cold (gate OFF)  state establishment only: fresh run dir,
                                    cold geometry cache + JIT -> NOT a rep
  slot 1  priming  JIT (gate ON)    compile the two gated kernels into the
                                    shared NUMBA_CACHE_DIR -> NOT a rep
  slots 2-7         warm_full       MEASURED, interleaved OFF/ON/OFF/ON/OFF/ON
                                    (reps 0,0,1,1,2,2)

WARM state: all measured runs share the priming run dir + NUMBA_CACHE_DIR
(geometry store hits, JIT cached for both gates). The gate only arms the
classification route inside stage C; stages A/B are gate-independent.

SYNTHETIC dev-tier; verdict input only, promotion decision is the
integrator's. Runs are never reordered after inspecting results; failures
are recorded verbatim and never retried beyond this frozen schedule.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
R04 = TOOLS.parent
CAMPAIGN_TOOLS = R04.parent / "campaign_synthetic" / "tools"
sys.path.insert(0, str(CAMPAIGN_TOOLS))
from thread_limits import child_environment, host_facts, heavy_jobs, write_json  # noqa: E402

TREE = Path("/Users/alansynn/Workspace/solweig-light-v6-r04")
SITE = TREE / "src"
SCENE = Path("/Users/alansynn/Workspace/solweig-light-claude-v5/optimization_v6_continue/"
             "evidence/campaign_synthetic/scenes/scene_t1024")
RUN_ROOT = R04 / "runs" / "lease_t1024"
PYTHON = "/Users/alansynn/Workspace/solweig-light/.venv-light/bin/python"
GATE_VAR = "SOLWEIG_LIGHT_PATCH_CLASS_TABLES"
WORKERS, THREADS = 1, 4
TIMEOUT_S = 5400.0
OUT_JSONL = R04 / "lease_timing.jsonl"
OUT_JSON = R04 / "lease_timing.json"

# Frozen before the first measured run. ("priming" slots are unmeasured.)
SCHEDULE = [
    {"slot": 0, "kind": "priming_cold", "gate": "OFF"},
    {"slot": 1, "kind": "priming_jit", "gate": "ON"},
    {"slot": 2, "kind": "measured_warm", "gate": "OFF", "rep": 0},
    {"slot": 3, "kind": "measured_warm", "gate": "ON", "rep": 0},
    {"slot": 4, "kind": "measured_warm", "gate": "OFF", "rep": 1},
    {"slot": 5, "kind": "measured_warm", "gate": "ON", "rep": 1},
    {"slot": 6, "kind": "measured_warm", "gate": "OFF", "rep": 2},
    {"slot": 7, "kind": "measured_warm", "gate": "ON", "rep": 2},
]

JIT_PRIMER = """
import numpy as np
from solweig_light.radiation import patch_radiation as p
table = np.array([[10.,45.],[25.,135.],[40.,225.],[55.,315.],[70.,90.],[85.,270.]], np.float32)
lv = np.column_stack((table, np.zeros(6, np.float32)))
g = p.patch_geometry(lv)
f = np.full((4, 4), .6, np.float32)
alt = np.array(35., np.float32)
p._classes(alt, 180., g, f, 0, 16)                       # contiguous kernel
p._classes(alt, 180., g, f, 0, 16, np.array([1,0,1,0,1,0], bool))  # masked kernel
print('jit-primed', p._classes_exact_enabled())
"""

def git_rev() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                          cwd=str(TREE)).stdout.strip()


def module_sha(rel: str) -> str:
    path = TREE / rel
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16] if path.exists() else "ABSENT"


def append_jsonl(entry: dict) -> None:
    with open(OUT_JSONL, "a") as stream:
        stream.write(json.dumps(entry) + "\n")


def run_slot(slot_index: int, step: dict) -> dict:
    gate = step["gate"]
    entry = {"slot": slot_index, **step,
             "patch_radiation_sha": module_sha("src/solweig_light/radiation/patch_radiation.py"),
             "tree_head": git_rev()}
    if step["kind"] == "priming_jit":
        env = child_environment(THREADS, str(RUN_ROOT / "numba_cache"))
        env[GATE_VAR] = "1"
        env["PYTHONPATH"] = str(SITE)
        before = heavy_jobs()
        started = time.monotonic()
        proc = subprocess.run([PYTHON, "-c", JIT_PRIMER], capture_output=True, text=True,
                              timeout=600, env=env)
        entry.update({"wall_s": round(time.monotonic() - started, 3),
                      "returncode": proc.returncode,
                      "stdout_tail": proc.stdout.strip().splitlines()[-3:],
                      "stderr_tail": proc.stderr.strip().splitlines()[-8:] if proc.stderr else [],
                      "host_before": before, "host_after": heavy_jobs()})
        append_jsonl(entry)
        return entry

    temp = "cold" if step["kind"] == "priming_cold" else "warm_full"
    record_path = RUN_ROOT / "records" / f"{step['kind']}_gate{gate}_r{step.get('rep', 'na')}.json"
    cmd = [PYTHON, str(CAMPAIGN_TOOLS / "campaign_child.py"),
           "--site", str(SITE), "--scene-src", str(SCENE), "--run-root", str(RUN_ROOT),
           "--temp", temp, "--workers", str(WORKERS), "--threads", str(THREADS),
           "--out", str(record_path)]
    env = child_environment(THREADS, str(RUN_ROOT / "numba_cache"))
    env[GATE_VAR] = "1" if gate == "ON" else "0"
    before = heavy_jobs()
    started = time.monotonic()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_S, env=env)
        returncode, stderr = proc.returncode, proc.stderr
        timed_out = False
    except subprocess.TimeoutExpired as error:
        def _text(value):
            if value is None:
                return ""
            return value.decode(errors="replace") if isinstance(value, bytes) else value
        returncode, stderr, timed_out = None, _text(error.stderr), True
    wall = round(time.monotonic() - started, 3)
    entry.update({"wall_s": wall, "returncode": returncode, "timed_out": timed_out,
                  "host_before": before, "host_after": heavy_jobs(),
                  "stderr_tail": stderr.strip().splitlines()[-15:] if stderr else []})
    if returncode == 0 and record_path.exists():
        child = json.loads(record_path.read_text())
        entry.update({"stages_s": child["stage_splits_s"],
                      "native_mask": child["numba"]["final_get_num_threads"],
                      "set_num_threads_error": child["numba"]["set_num_threads_error"],
                      "cache_entries": child["cache_census_after_run"]["cache_entry_count"],
                      "simulation_store_hits": child["stage_splits_s"]["simulation_store_hits"],
                      "output_digest": child["output_manifest"]["digest"],
                      "simulation_tiff_digest": child["output_manifest"]["simulation_tiff_digest"],
                      "simulation_tiff_digest_per_tile":
                          child["output_manifest"]["simulation_tiff_digest_per_tile"],
                      "module_origin": child["module_origin"]["solweig_light"],
                      "math_profile_id": child["math_profile"].get("profile_id"),
                      "site": child["requested"]["site"]})
    else:
        entry["status"] = "FAILED_OR_TIMED_OUT"  # preserved, never skipped or retried
    append_jsonl(entry)
    return entry


def main() -> int:
    payload = {
        "schema": "sw6-r04-lease-timing-v1",
        "label": "SYNTHETIC dev-tier exclusive-lease warm timing, R04+G06 classification "
                 "gate OFF vs ON; verdict input only; no statistical/actual-target claims",
        "protocol": {
            "tier": "SYNTHETIC 4x1024^2 distinct-tile batch, 24 records/tile (campaign "
                    "scene_t1024 reused verbatim), T4 shape workers=1 threads=4",
            "temp": "warm state only for measured slots: shared priming run dir + shared "
                    "NUMBA_CACHE_DIR; slot 0 cold priming and slot 1 JIT priming are "
                    "unmeasured state establishment",
            "schedule_frozen_before_first_measured_run": SCHEDULE,
            "interleave": "measured slots strictly alternate OFF/ON/OFF/ON/OFF/ON",
            "lease": "exclusive local-program lease: sequential children only, no pytest/"
                     "builds/profilers alongside; unrelated host activity recorded via "
                     "loadavg+ps per run, never claimed absent",
            "runtime_options": "identical pinned options both arms: cpu_budget=4, "
                               "block_pixels=1024, checkpoint_interval=1, cache_enabled=True, "
                               "legacy_cache_policy='recompute'",
            "parity": "simulation TIFF sha256 per tile recorded per run; OFF vs ON bitwise "
                      "identity expected; any mismatch recorded verbatim, not tuned",
            "no_tuning": "runs never reordered after inspecting results; failures never "
                         "retried beyond this frozen schedule",
            "timeout_s_per_run": TIMEOUT_S,
        },
        "tree": {"root": str(TREE), "head": git_rev(),
                 "patch_radiation_sha": module_sha("src/solweig_light/radiation/patch_radiation.py")},
        "scene_src": str(SCENE),
        "run_root": str(RUN_ROOT),
        "gate_var": GATE_VAR,
        "host_facts": host_facts(),
        "lease_started_epoch_s": time.time(),
    }
    write_json(OUT_JSON, payload)
    OUT_JSONL.unlink(missing_ok=True)
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    for index, step in enumerate(SCHEDULE):
        entry = run_slot(index, step)
        payload["slots"] = payload.get("slots", []) + [entry]
        write_json(OUT_JSON, payload)
        measured = step["kind"] == "measured_warm"
        print(json.dumps({"slot": index, "kind": step["kind"], "gate": step["gate"],
                          "rep": step.get("rep"),
                          "measured": measured,
                          "ok": entry.get("status") != "FAILED_OR_TIMED_OUT"
                          and entry.get("returncode") == 0,
                          "wall_s": entry.get("wall_s"),
                          "sim_s": entry.get("stages_s", {}).get("simulation_total")}),
              flush=True)
    print(json.dumps({"out_jsonl": str(OUT_JSONL), "slots": len(payload["slots"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
