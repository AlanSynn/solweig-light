#!/usr/bin/env python3
"""C6-101r PHASE 2 scheduler: frozen paired SYNTHETIC 1024^2 campaign.

Exclusive-benchmark-lease discipline: one child at a time, no pytest/builds
alongside, loadavg + ps snapshot before and after EVERY run.  Protocol frozen
BEFORE the first measured run; runs never reordered after inspecting results.

Cells: 2 trees x {T4 primary, S1 secondary}:
  T4 = workers 1, threads 4  (v5-campaign-comparable config)  cold x2 + warm x3
  S1 = workers 1, threads 1  (serial default)                 cold x1 + warm x2
S1 is TIME-CONDITIONAL (predeclared): if the S1 phase starts after
S1_DEADLINE_S of campaign wall clock, every S1 slot is recorded
SKIPPED_TIME_BUDGET and left unmeasured (never silently dropped).
Tree order alternates at every opportunity.  Warm runs reuse the cell's cold
run dir + NUMBA_CACHE_DIR.  Per-run child timeout 5400 s (4-tile stage C).
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
BASE = Path("/Users/alansynn/Workspace/solweig-light-v6-base-l2")
TREES = {"integrated": INTEGRATED, "base": BASE}
SCENE = CAMPAIGN / "scenes" / "scene_t1024"
RUNS = CAMPAIGN / "runs"
PYTHON = "/Users/alansynn/Workspace/solweig-light/.venv-light/bin/python"
CONFIGS = {"T4": (1, 4), "S1": (1, 1)}
COLD_REPS = {"T4": 2, "S1": 1}
WARM_REPS = {"T4": 3, "S1": 2}
S1_DEADLINE_S = 4.5 * 3600.0
TIMEOUT_S = 5400.0

OUT_PATH = CAMPAIGN / "campaign_v1.json"


def build_schedule():
    """Frozen before any measured run; T4 first, S1 conditional, trees alternate."""
    schedule = []
    flip = 0
    for config in ("T4", "S1"):
        temps = ([("cold", rep) for rep in range(COLD_REPS[config])]
                 + [("warm_full", rep) for rep in range(WARM_REPS[config])])
        for temp, rep in temps:
            order = list(TREES) if flip % 2 == 0 else list(TREES)[::-1]
            flip += 1
            for tree in order:
                schedule.append({"config": config, "temp": temp, "rep": rep, "tree": tree})
    return schedule


def git_rev(worktree: str) -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                          cwd=worktree).stdout.strip()


def module_sha(worktree: Path, rel: str) -> str:
    import hashlib
    path = worktree / rel
    if not path.exists():
        return "ABSENT"
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def run_slot(slot_index: int, step: dict, campaign_start: float) -> dict:
    config, temp, rep, tree = step["config"], step["temp"], step["rep"], step["tree"]
    workers, threads = CONFIGS[config]
    run_root = RUNS / f"t1024_{config}" / tree
    record_path = run_root / "records" / f"{temp}_r{rep}.json"
    entry = {"slot": slot_index, **step}
    if config == "S1" and time.monotonic() - campaign_start > S1_DEADLINE_S:
        entry.update({"status": "SKIPPED_TIME_BUDGET", "wall_s": 0.0,
                      "note": "predeclared S1 time condition fired; slot left unmeasured"})
        with open(OUT_PATH.with_suffix(".jsonl"), "a") as stream:
            stream.write(json.dumps(entry) + "\n")
        return entry
    cmd = [PYTHON, str(TOOLS / "campaign_child.py"),
           "--site", str(TREES[tree] / "src"),
           "--scene-src", str(SCENE),
           "--run-root", str(run_root),
           "--temp", temp, "--workers", str(workers), "--threads", str(threads),
           "--out", str(record_path)]
    env = child_environment(threads, str(run_root / "numba_cache"))
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
    entry.update({"wall_s": wall, "returncode": returncode, "timed_out": timed_out,
                  "host_before": before, "host_after": after,
                  "stderr_tail": stderr.strip().splitlines()[-15:] if stderr else []})
    if returncode == 0 and record_path.exists():
        child = json.loads(record_path.read_text())
        entry["stages_s"] = child["stage_splits_s"]
        entry["native_mask"] = child["numba"]["final_get_num_threads"]
        entry["set_num_threads_error"] = child["numba"]["set_num_threads_error"]
        entry["phase_route_fired"] = child["cache_census_after_run"]["phase_route_fired"]
        entry["cache_entries"] = child["cache_census_after_run"]["cache_entry_count"]
        entry["output_digest"] = child["output_manifest"]["digest"]
        entry["simulation_tiff_digest"] = child["output_manifest"]["simulation_tiff_digest"]
        entry["simulation_tiff_digest_per_tile"] = \
            child["output_manifest"]["simulation_tiff_digest_per_tile"]
        entry["peak_rss_parent_bytes"] = child["peak_rss_bytes"]
        entry["module_origin"] = child["module_origin"]["solweig_light"]
        entry["math_profile_id"] = child["math_profile"].get("profile_id")
    else:
        entry["status"] = "FAILED_OR_TIMED_OUT"  # preserved, never skipped
        entry["stdout_tail"] = stdout.strip().splitlines()[-8:] if stdout else []
    with open(OUT_PATH.with_suffix(".jsonl"), "a") as stream:
        stream.write(json.dumps(entry) + "\n")
    return entry


def main() -> int:
    campaign_start = time.monotonic()
    schedule = build_schedule()
    payloads = {
        "schema": "sw6-campaign-synthetic-v1",
        "label": "SYNTHETIC 1024^2 4-tile paired campaign (C6-101r); dev-tier single-lease; "
                 "NOT the actual-target dataset; no statistical or actual-target claims",
        "protocol": {
            "tier": "L3+: SYNTHETIC 4x1024^2 distinct-tile batch, 24 records/tile, "
                    "user-authorized scope extension (2026-09-21); synthetic dev-tier only",
            "lease": "exclusive local-program lease: sequential children only, no pytest/"
                     "builds/profilers alongside; unrelated OS/browser/system activity "
                     "(including other session agents) recorded per run via loadavg+ps, "
                     "never claimed absent",
            "same_resource": "identical RuntimeOptions per paired cell: "
                             "memory_budget_bytes pinned 12 GiB via dataclasses.replace, "
                             "cpu_budget=4, block_pixels=1024, checkpoint_interval=1, "
                             "cache_enabled=True, legacy_cache_policy='recompute'",
            "configs": {"T4": "workers 1, threads 4 (v5-campaign-comparable); primary",
                        "S1": "workers 1, threads 1 (serial default); secondary, "
                              "predeclared time-conditional (S1_DEADLINE_S=16200s campaign "
                              "wall clock at first S1 slot, else SKIPPED_TIME_BUDGET)"},
            "temps": {"cold": "fresh run dir + fresh NUMBA_CACHE_DIR (cold geometry cache, "
                              "cold JIT, inside timer)",
                      "warm_full": "same run dir + same NUMBA_CACHE_DIR (fully warm)"},
            "stages": {"A_walls_aspect": "api.run_walls_aspect (geometry production)",
                       "B_svf_geometry": "api.calculate_svf patch_option=2 overwrite=False",
                       "C_simulation": "api.run_utci_tiles 10 flags, 24 records/tile, "
                                       "public execute_tiles worker transport"},
            "parity": "simulation TIFF sha256 per tile must be bitwise-identical across "
                      "trees/configs/temps; any mismatch recorded verbatim, not tuned",
            "timeout_s_per_run": TIMEOUT_S,
        },
        "trees": {name: {"root": str(root), "head": git_rev(str(root)),
                         "runtime_phases_sha": module_sha(root, "src/solweig_light/runtime_phases.py"),
                         "service_sha": module_sha(root, "src/solweig_light/geometry/service.py"),
                         "patch_radiation_sha": module_sha(root, "src/solweig_light/radiation/patch_radiation.py"),
                         "pipeline_sha": module_sha(root, "src/solweig_light/pipeline.py"),
                         "engine_sha": module_sha(root, "src/solweig_light/radiation/engine.py"),
                         "ground_view_sha": module_sha(root, "src/solweig_light/radiation/ground_view.py"),
                         "api_sha": module_sha(root, "src/solweig_light/api.py")}
                  for name, root in TREES.items()},
        "host_facts": host_facts(),
        "scene_manifest": json.loads((CAMPAIGN / "scene_manifest.json").read_text()),
        "schedule": schedule,
        "slots": [],
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_json(OUT_PATH, payloads)  # frozen BEFORE the first measured run
    OUT_PATH.with_suffix(".jsonl").unlink(missing_ok=True)

    for index, step in enumerate(schedule):
        entry = run_slot(index, step, campaign_start)
        payloads["slots"].append(entry)
        write_json(OUT_PATH, payloads)
        ok = entry.get("status") not in ("FAILED_OR_TIMED_OUT", "SKIPPED_TIME_BUDGET")
        print(json.dumps({"slot": index, "tree": step["tree"], "config": step["config"],
                          "temp": step["temp"], "rep": step["rep"], "ok": ok,
                          "status": entry.get("status", "ok"),
                          "total_s": entry.get("stages_s", {}).get("total_measured"),
                          "sim_s": entry.get("stages_s", {}).get("simulation_total")}),
              flush=True)
    print(json.dumps({"out": str(OUT_PATH), "slots": len(payloads["slots"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
