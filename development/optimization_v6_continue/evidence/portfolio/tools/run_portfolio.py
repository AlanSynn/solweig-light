#!/usr/bin/env python3
"""C6-80 portfolio scheduler: predeclared sequential cold/warm matrix.

Exclusive-benchmark-lease discipline (dossier-01): one child process at a
time, no pytest/xdist/builds alongside, load-average + ps snapshot recorded
before and after EVERY measured run.  The schedule below is frozen before the
first measured run and written into the master JSON first; runs are never
reordered after inspecting results.

Cells (2 shapes x 3 configs x 2 trees):
  S1 = workers 1, threads 1  (serial default)
  P2 = workers 2, threads 1  (C6-40 GEOMETRY phase gate: >1 tile, cache on)
  T2 = workers 1, threads 2  (prepared-GVF threads>1 branch, C6-30/70f)
Temps per cell: cold x2, warm_geom x1 (S1 only), warm_full x3.
Tree order alternates at every opportunity; warm runs reuse their cell's cold
run dir (fresh NUMBA_CACHE_DIR for warm_geom via --numba-cache-dir).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
PORTFOLIO = TOOLS.parent
sys.path.insert(0, str(TOOLS))
from thread_limits import child_environment, host_facts, heavy_jobs, write_json  # noqa: E402

INTEGRATED = Path("/Users/alansynn/Workspace/solweig-light-claude-v5")
BASE = Path("/Users/alansynn/Workspace/solweig-light-v6-base-l2")
TREES = {"integrated": INTEGRATED, "base": BASE}
SCENES = {128: PORTFOLIO / "scenes" / "scene_t128",
          256: PORTFOLIO / "scenes" / "scene_t256"}
CONFIGS = {"S1": (1, 1), "P2": (2, 1), "T2": (1, 2)}
COLD_REPS = 2
WARM_GEOM_REPS = 1
WARM_FULL_REPS = 3
TIMEOUT_S = 900.0
PYTHON = "/Users/alansynn/Workspace/solweig-light/.venv-light/bin/python"

PARSER = argparse.ArgumentParser(description=__doc__)
PARSER.add_argument("--out", default=str(PORTFOLIO / "portfolio_v1.json"))
PARSER.add_argument("--shapes", default="128,256")
PARSER.add_argument("--configs", default="S1,P2,T2")
ARGS = PARSER.parse_args()

SHAPES = [int(value) for value in ARGS.shapes.split(",")]
CONFIG_NAMES = ARGS.configs.split(",")
OUT_PATH = Path(ARGS.out).resolve()
RUNS = PORTFOLIO / "runs"


def build_schedule():
    """Frozen before any measured run; tree order alternates at every step."""
    schedule = []
    flip = 0
    for shape in SHAPES:
        for config in CONFIG_NAMES:
            cell_temps = ([("cold", rep) for rep in range(COLD_REPS)]
                          + ([("warm_geom", rep) for rep in range(WARM_GEOM_REPS)]
                             if config == "S1" else [])
                          + [("warm_full", rep) for rep in range(WARM_FULL_REPS)])
            for temp, rep in cell_temps:
                order = list(TREES) if flip % 2 == 0 else list(TREES)[::-1]
                flip += 1
                for tree in order:
                    schedule.append({"shape": shape, "config": config, "temp": temp,
                                     "rep": rep, "tree": tree})
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


def run_slot(slot_index: int, step: dict) -> dict:
    shape, config, temp, rep, tree = (step["shape"], step["config"], step["temp"],
                                      step["rep"], step["tree"])
    workers, threads = CONFIGS[config]
    run_root = RUNS / f"t{shape}_{config}" / tree
    record_path = run_root / "records" / f"{temp}_r{rep}.json"
    numba_override = str(run_root / f"numba_cache_geomcold_r{rep}") \
        if temp == "warm_geom" else None
    cmd = [PYTHON, str(TOOLS / "portfolio_child.py"),
           "--site", str(TREES[tree] / "src"),
           "--scene-src", str(SCENES[shape]),
           "--run-root", str(run_root),
           "--temp", temp, "--workers", str(workers), "--threads", str(threads),
           "--out", str(record_path)]
    if numba_override:
        cmd += ["--numba-cache-dir", numba_override]
    before = heavy_jobs()
    started = time.monotonic()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_S)
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
    entry = {"slot": slot_index, **step, "wall_s": wall, "returncode": returncode,
             "timed_out": timed_out,
             "host_before": before, "host_after": after,
             "stderr_tail": stderr.strip().splitlines()[-15:] if stderr else []}
    if returncode == 0 and record_path.exists():
        child = json.loads(record_path.read_text())
        entry["stages_s"] = child["stage_splits_s"]
        entry["native_mask"] = child["numba"]["final_get_num_threads"]
        entry["route_counts"] = child["route"]["observed_counts"]
        entry["phase_route_fired"] = child["cache_census_after_run"]["phase_route_fired"]
        entry["cache_entries"] = child["cache_census_after_run"]["cache_entry_count"]
        entry["output_digest"] = child["output_manifest"]["digest"]
        entry["simulation_tiff_digest"] = child["output_manifest"]["simulation_tiff_digest"]
        entry["simulation_tiff_count"] = child["output_manifest"]["simulation_tiff_count"]
        entry["output_file_count"] = child["output_manifest"]["file_count"]
        entry["peak_rss_parent_bytes"] = child["peak_rss_bytes"]
    else:
        entry["status"] = "FAILED_OR_TIMED_OUT"  # preserved, never skipped
        entry["stdout_tail"] = stdout.strip().splitlines()[-8:] if stdout else []
    with open(OUT_PATH.with_suffix(".jsonl"), "a") as stream:
        stream.write(json.dumps(entry) + "\n")
    return entry


def main() -> int:
    schedule = build_schedule()
    payloads = {
        "schema": "sw6-portfolio-v1",
        "protocol": {
            "tier": "L3 (128/256-square distinct-tile batch, 2 tiles/scene, 24 records each); "
                    "NOT the actual 24-tile target; no actual-target claims",
            "lease": "exclusive local-program lease: sequential children only, no pytest/"
                     "builds/profilers alongside; unrelated OS/browser system activity "
                     "recorded per run via loadavg + ps, never claimed absent",
            "same_resource": "identical RuntimeOptions per paired cell: "
                             "memory_budget_bytes pinned 12 GiB via dataclasses.replace, "
                             "cpu_budget=4, block_pixels=1024, checkpoint_interval=1, "
                             "cache_enabled=True, legacy_cache_policy='recompute'",
            "temps": {"cold": "fresh run dir + fresh NUMBA_CACHE_DIR (cold geometry cache, "
                              "cold JIT, inside timer)",
                      "warm_geom": "same run dir, FRESH NUMBA_CACHE_DIR (geometry+exports "
                                   "warm, JIT cold again)",
                      "warm_full": "same run dir + same NUMBA_CACHE_DIR (fully warm)"},
            "stages": {"A_walls_aspect": "api.run_walls_aspect (geometry production)",
                       "B_svf_geometry": "api.calculate_svf patch_option=2 overwrite=False "
                                         "(shared C6-10 recipe production + export/publication; "
                                         "C6-40 phase barrier when it fires)",
                       "C_simulation": "api.run_utci_tiles 10 flags, 24 records/tile"},
            "labels": "single-run observations; warm_full x3 medians are dev-tier paired "
                      "observations, no statistical claims",
            "timeout_s_per_run": TIMEOUT_S,
        },
        "trees": {name: {"root": str(root), "head": git_rev(str(root)),
                         "runtime_phases_sha": module_sha(root, "src/solweig_light/runtime_phases.py"),
                         "service_sha": module_sha(root, "src/solweig_light/geometry/service.py"),
                         "patch_radiation_sha": module_sha(root, "src/solweig_light/radiation/patch_radiation.py"),
                         "visibility_prepared_sha": module_sha(root, "src/solweig_light/geometry/visibility_prepared.py")}
                  for name, root in TREES.items()},
        "host_facts": host_facts(),
        "scene_manifests": json.loads((PORTFOLIO / "scene_manifests.json").read_text()),
        "schedule": schedule,
        "slots": [],
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_json(OUT_PATH, payloads)  # frozen protocol BEFORE the first measured run
    OUT_PATH.with_suffix(".jsonl").unlink(missing_ok=True)

    for index, step in enumerate(schedule):
        entry = run_slot(index, step)
        payloads["slots"].append(entry)
        write_json(OUT_PATH, payloads)
        ok = entry.get("status") != "FAILED_OR_TIMED_OUT"
        print(json.dumps({"slot": index, "tree": step["tree"], "shape": step["shape"],
                          "config": step["config"], "temp": step["temp"], "rep": step["rep"],
                          "ok": ok,
                          "total_s": entry.get("stages_s", {}).get("total_measured")}),
              flush=True)
    print(json.dumps({"out": str(OUT_PATH), "slots": len(payloads["slots"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
