#!/usr/bin/env python3
"""C6-101r PHASE 1 child: in-sim residual attribution, ONE synthetic 1024^2 tile.

SYNTHETIC dev-tier observation on a single-lease host; no statistical or
actual-target claims.

Modes (each mode is a FRESH process; prime runs first and its timing is
discarded, wall/profile reps reuse the prime's run dir + NUMBA_CACHE_DIR so
JIT is warm):

  prime   cold run (fresh run dir + fresh JIT cache): compiles every kernel;
          outputs discarded, cache+run dir kept for the reps
  wall    warm, NO profiler: stage A + stage B + the in-process simulate loop
          timed as-is (quantifies profiler distortion vs the profiled run)
  profile warm, cProfile around the SAME in-process simulate loop; pstats
          dumped binary (.pstats) + sorted cumulative text (.txt)

The chronology-probe transport swap is used for stage C
(evidence/integration/chronology_probe.py): runtime.execute_tiles is replaced
by an in-process loop over pipeline.run_tile on the same job dicts, so
cProfile sees THIS process.  Only the transport differs; the numerical work
under test is the public run_tile entry.

C6-01 discipline: thread limits set BEFORE any numerical import, native mask
verified, module origin asserted, math profile fingerprint recorded.
"""
from __future__ import annotations

import argparse
import cProfile
import hashlib
import json
import os
import pstats
import platform
import resource
import shutil
import sys
import time
from pathlib import Path

T_MONOTONIC_START = time.monotonic()

PARSER = argparse.ArgumentParser(description=__doc__)
PARSER.add_argument("--site", required=True)
PARSER.add_argument("--scene-src", required=True)
PARSER.add_argument("--run-root", required=True)
PARSER.add_argument("--tile", default="0_0")
PARSER.add_argument("--threads", type=int, default=4)
PARSER.add_argument("--mode", choices=("prime", "wall", "profile"), required=True)
PARSER.add_argument("--out", required=True)
PARSER.add_argument("--pstats", default=None)
ARGS = PARSER.parse_args()

OUT_PATH = Path(ARGS.out).resolve()
RUN_ROOT = Path(ARGS.run_root).resolve()
RUN_DIR = RUN_ROOT / "run_scene"
PREP = RUN_DIR / "processed_inputs"

THREAD_VARS = ("BLIS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS",
               "NUMEXPR_NUM_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
               "VECLIB_MAXIMUM_THREADS")
for _name in THREAD_VARS:
    os.environ[_name] = str(ARGS.threads)
NUMBA_CACHE_DIR = RUN_ROOT / "numba_cache"
os.environ["NUMBA_CACHE_DIR"] = str(NUMBA_CACHE_DIR)
ENV_THREADS_AT_START = {name: os.environ.get(name) for name in THREAD_VARS}
SITE = str(Path(ARGS.site).resolve())
os.environ["PYTHONPATH"] = SITE

T_NUMPY_IMPORT_START = time.monotonic()
import numpy as np  # noqa: E402
import numba  # noqa: E402
T_NUMPY_IMPORT_S = time.monotonic() - T_NUMPY_IMPORT_START

CONFIG_THREADS = int(numba.config.NUMBA_NUM_THREADS)
SET_NUM_THREADS_ERROR = None
if CONFIG_THREADS != ARGS.threads:
    SET_NUM_THREADS_ERROR = (f"config.NUMBA_NUM_THREADS={CONFIG_THREADS} != "
                             f"requested {ARGS.threads}")
else:
    numba.set_num_threads(ARGS.threads)
    if numba.get_num_threads() != ARGS.threads:
        SET_NUM_THREADS_ERROR = (f"get_num_threads()={numba.get_num_threads()} != "
                                 f"requested {ARGS.threads}")

T_SOLWEIG_IMPORT_START = time.monotonic()
sys.path.insert(0, SITE)
import dataclasses  # noqa: E402
import solweig_light  # noqa: E402
from solweig_light import api, pipeline, runtime_options  # noqa: E402
from solweig_light.runtime import get_runtime_options  # noqa: E402
from solweig_light.radiation import _math_profile, ground_view  # noqa: E402
T_SOLWEIG_IMPORT_S = time.monotonic() - T_SOLWEIG_IMPORT_START

# --- call-through GVF route counters (no numerics altered) ------------------
ROUTE_EVENTS: list[str] = []


def _wrap_leaf(name: str, route_name: str) -> None:
    original = getattr(ground_view, name)

    def recorder(*args, **kwargs):
        ROUTE_EVENTS.append(route_name)
        return original(*args, **kwargs)
    recorder.__wrapped_original__ = original
    setattr(ground_view, name, recorder)


def _wrap_module_leaf(module, name: str, route_name: str) -> None:
    if not hasattr(module, name):
        return
    original = getattr(module, name)

    def recorder(*args, **kwargs):
        ROUTE_EVENTS.append(route_name)
        return original(*args, **kwargs)
    recorder.__wrapped_original__ = original
    setattr(module, name, recorder)


_wrap_leaf("_gvf_fused", "gvf_fused_g03")
_wrap_leaf("gvf_2018a", "gvf_serial_full")
_wrap_leaf("gvf_2018a_parallel", "gvf_serial_parallel")
# Integrated threads>1 dispatcher routes to the prepared GVF step (C6-30);
# guard-rejected calls delegate to _gvf_fused above.
from solweig_light.radiation import gvf_prepared  # noqa: E402
_wrap_module_leaf(gvf_prepared, "prepared_gvf_step", "gvf_prepared_step")


def output_digest(tile: str) -> dict:
    out_dir = RUN_DIR / "output_folder" / tile
    files = []
    if out_dir.is_dir():
        for path in sorted(out_dir.rglob("*")):
            if path.is_file():
                files.append({"path": path.name, "size": path.stat().st_size,
                              "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return {"tile": tile, "file_count": len(files),
            "digest": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()[:16],
            "files": files}


def main() -> int:
    scene_src = Path(ARGS.scene_src).resolve()
    if ARGS.mode == "prime":
        if RUN_ROOT.exists():
            shutil.rmtree(RUN_ROOT)  # prime owns a fresh cache dir
        RUN_ROOT.mkdir(parents=True)
        shutil.copytree(scene_src, RUN_DIR)
    else:
        if not RUN_DIR.is_dir():
            raise SystemExit(f"{ARGS.mode} run requires existing {RUN_DIR}; run prime first")

    manifest = json.loads((scene_src / "scene_manifest.json").read_text())
    if ARGS.tile not in manifest["tiles"]:
        raise SystemExit(f"tile {ARGS.tile} not in scene")

    options = dataclasses.replace(
        get_runtime_options(),
        memory_budget_bytes=12 * 1024**3,
        cpu_budget=4,
        workers=1,
        threads_per_worker=ARGS.threads,
        block_pixels=1024,
        checkpoint_interval=1,
        cache_enabled=True,
        legacy_cache_policy="recompute",
        cache_dir=None,
    )
    flags = dict(save_tmrt=True, save_svf=True, save_kup=True, save_kdown=True,
                 save_lup=True, save_ldown=True, save_shadow=True, save_wbgt=True,
                 save_ta=True, save_wind=True)

    # --- stage A + B (timed, UNPROFILED in every mode) ----------------------
    with runtime_options(options):
        t0 = time.monotonic()
        api.run_walls_aspect(str(PREP))
        walls_s = time.monotonic() - t0
        t0 = time.monotonic()
        api.calculate_svf(str(PREP), patch_option=2, overwrite=False)
        svf_s = time.monotonic() - t0

        # --- stage C: chronology-probe in-process transport -----------------
        import solweig_light.runtime as _runtime_module
        from solweig_light.pipeline import run_tile as _run_tile

        def _in_process_execute(jobs, runtime=None, **kwargs):
            selected = [job for job in jobs if job.get("tile") == ARGS.tile]
            t0 = time.monotonic()
            results = tuple(_run_tile(**job, runtime=runtime) for job in selected)
            LOOP_S["s"] = time.monotonic() - t0
            LOOP_S["jobs_total"] = len(jobs)
            LOOP_S["jobs_selected"] = len(selected)
            return results

        LOOP_S = {"s": 0.0, "jobs_total": 0, "jobs_selected": 0}
        _real_execute_tiles = _runtime_module.execute_tiles
        _runtime_module.execute_tiles = _in_process_execute
        try:
            if ARGS.mode == "profile":
                profiler = cProfile.Profile()
                t0 = time.monotonic()
                profiler.enable()
                api.run_utci_tiles(base_path=str(RUN_DIR), preprocess_dir=str(PREP),
                                   selected_date_str="2020-07-18", tile_keys=[ARGS.tile],
                                   **flags)
                profiler.disable()
                sim_wall_s = time.monotonic() - t0
                if ARGS.pstats:
                    pstats_path = Path(ARGS.pstats).resolve()
                    pstats_path.parent.mkdir(parents=True, exist_ok=True)
                    profiler.dump_stats(str(pstats_path))
                    with open(pstats_path.with_suffix(".txt"), "w") as handle:
                        stats = pstats.Stats(str(pstats_path), stream=handle)
                        stats.sort_stats("cumulative").print_stats(120)
                        handle.write("\n\n===== sorted by internal time =====\n")
                        stats.sort_stats("tottime").print_stats(80)
            else:
                t0 = time.monotonic()
                api.run_utci_tiles(base_path=str(RUN_DIR), preprocess_dir=str(PREP),
                                   selected_date_str="2020-07-18", tile_keys=[ARGS.tile],
                                   **flags)
                sim_wall_s = time.monotonic() - t0
        finally:
            _runtime_module.execute_tiles = _real_execute_tiles

    try:
        layer = numba.threading_layer()
    except Exception as error:
        layer = f"{type(error).__name__}: {error}"
    record = {
        "schema": "sw6-campaign-synthetic-profile-child-v1",
        "label": "SYNTHETIC dev-tier in-sim residual attribution (C6-101r); "
                 "single-lease, no statistical/actual-target claims",
        "requested": {"mode": ARGS.mode, "tile": ARGS.tile, "threads": ARGS.threads,
                      "site": SITE, "scene_src": str(scene_src)},
        "env": {"threads_at_numerical_import": ENV_THREADS_AT_START,
                "numba_cache_dir": str(NUMBA_CACHE_DIR),
                "pythonpath_env": os.environ.get("PYTHONPATH")},
        "numba": {"config_NUMBA_NUM_THREADS": CONFIG_THREADS,
                  "set_num_threads_error": SET_NUM_THREADS_ERROR,
                  "final_get_num_threads": int(numba.get_num_threads()),
                  "threading_layer": layer, "version": numba.__version__},
        "module_origin": {"solweig_light": Path(solweig_light.__file__).resolve().as_posix(),
                          "pipeline": Path(pipeline.__file__).resolve().as_posix()},
        "math_profile": _math_profile.profile_identity(),
        "options": options.as_dict(),
        "stage_splits_s": {
            "walls_aspect": round(walls_s, 4),
            "svf_geometry_total": round(svf_s, 4),
            "simulation_total_wall": round(sim_wall_s, 4),
            "simulation_in_process_loop": round(LOOP_S["s"], 4),
            "jobs_total": LOOP_S["jobs_total"],
            "jobs_selected": LOOP_S["jobs_selected"],
        },
        "route": {"observed_counts": {name: ROUTE_EVENTS.count(name)
                                      for name in sorted(set(ROUTE_EVENTS))},
                  "observation_point": "ground_view leaf wrappers, call-through"},
        "output_digest": output_digest(ARGS.tile),
        "versions": {"python": platform.python_version(), "numpy": np.__version__,
                     "numba": numba.__version__,
                     "llvmlite": __import__("llvmlite").__version__,
                     "machine": platform.machine(), "system": platform.system()},
        "timing_s": {"numpy_numba_import": round(T_NUMPY_IMPORT_S, 3),
                     "solweig_import": round(T_SOLWEIG_IMPORT_S, 3),
                     "child_total": round(time.monotonic() - T_MONOTONIC_START, 3)},
        "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "process": {"pid": os.getpid()},
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(record, indent=1) + "\n")
    print(json.dumps({"out": str(OUT_PATH), "mode": ARGS.mode, "tile": ARGS.tile,
                      "native_mask": record["numba"]["final_get_num_threads"],
                      "stages_s": record["stage_splits_s"],
                      "route_counts": record["route"]["observed_counts"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
