#!/usr/bin/env python3
"""C6-01 child runner: one SOLWEIG run in a fresh, native-limit-isolated process.

Every numerical import happens AFTER the launcher-supplied environment limits
are in place (this module's top-level imports are stdlib only). The child runs
the dense256 full-chronology run_tile workload (L2 tier, 24 records, 153
patches, one 256x256 tile) and reports the ACTUAL native thread mask, the
admitted worker plan and the observed GVF kernel route at first real kernel
entry.

Labels:
  isolated  -- env limits set to --threads before first import; numba mask
               verified and pinned with numba.set_num_threads.
  old_style -- env left inherited (no overrides): reproduces the old portfolio
               harness, which only set RuntimeOptions(threads_per_worker=H)
               in-process; the native mask stays at Numba's default pool while
               the dispatch route still flips.

Run: child_runner.py --threads 4 --label isolated --out <json> [--site <src>] \
     [--scene-src <scene>] [--run-root <dir>] [--keep-run-dir]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import resource
import shutil
import sys
import time
from pathlib import Path

T_MONOTONIC_START = time.monotonic()

# stdlib-only argument handling; NO numerical imports above this point.
PARSER = argparse.ArgumentParser(description=__doc__)
PARSER.add_argument("--threads", type=int, required=True,
                    help="requested native threads per worker (label value)")
PARSER.add_argument("--label", choices=("isolated", "old_style"), required=True)
PARSER.add_argument("--workers", type=int, default=1)
PARSER.add_argument("--site", default=str(Path(__file__).resolve().parents[3] / "src"),
                    help="solweig_light source tree to import (default: this worktree src)")
PARSER.add_argument("--scene-src", default=str(Path(
    "/Users/alansynn/Workspace/solweig-light-claude-v5/optimization_v5_claude"
    "/evidence/census/scene_dense256")))
PARSER.add_argument("--run-root", default=None,
                    help="directory for the fresh run dir + NUMBA_CACHE_DIR (default: out's parent)")
PARSER.add_argument("--out", required=True)
PARSER.add_argument("--keep-run-dir", action="store_true")
ARGS = PARSER.parse_args()

OUT_PATH = Path(ARGS.out).resolve()
RUN_ROOT = Path(ARGS.run_root).resolve() if ARGS.run_root else OUT_PATH.parent
RUN_ROOT.mkdir(parents=True, exist_ok=True)
RUN_DIR = RUN_ROOT / "run_scene"
NUMBA_CACHE_DIR = RUN_ROOT / "numba_cache"

if ARGS.label == "isolated":
    # Native limits BEFORE any numerical import.  Same variable set the
    # production scheduler writes before worker first import.
    for _name in ("BLIS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS",
                  "NUMEXPR_NUM_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                  "VECLIB_MAXIMUM_THREADS"):
        os.environ[_name] = str(ARGS.threads)
elif any(os.environ.get(_name) for _name in
         ("NUMBA_NUM_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
          "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
          "BLIS_NUM_THREADS")):
    PARSER.error("old_style label requires an environment without thread overrides")
os.environ["NUMBA_CACHE_DIR"] = str(NUMBA_CACHE_DIR)

ENV_THREADS_AT_START = {name: os.environ.get(name) for name in
                        ("BLIS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS",
                         "NUMEXPR_NUM_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                         "VECLIB_MAXIMUM_THREADS")}

T_NUMPY_IMPORT_START = time.monotonic()
import numpy as np  # noqa: E402
import numba  # noqa: E402
T_NUMPY_IMPORT_S = time.monotonic() - T_NUMPY_IMPORT_START

CONFIG_THREADS = int(numba.config.NUMBA_NUM_THREADS)
DEFAULT_MASK_AT_IMPORT = numba.get_num_threads()
SET_NUM_THREADS_CALLED = False
SET_NUM_THREADS_ERROR = None
if ARGS.label == "isolated":
    try:
        if CONFIG_THREADS != ARGS.threads:
            raise AssertionError(
                f"config.NUMBA_NUM_THREADS={CONFIG_THREADS} != requested {ARGS.threads}")
        numba.set_num_threads(ARGS.threads)
        SET_NUM_THREADS_CALLED = True
        if numba.get_num_threads() != ARGS.threads:
            raise AssertionError(
                f"get_num_threads()={numba.get_num_threads()} != requested {ARGS.threads}")
    except Exception as error:  # recorded, never silently skipped
        SET_NUM_THREADS_ERROR = f"{type(error).__name__}: {error}"

T_SOLWEIG_IMPORT_START = time.monotonic()
sys.path.insert(0, str(Path(ARGS.site).resolve()))
import solweig_light  # noqa: E402
from solweig_light import RuntimeOptions, runtime_options  # noqa: E402
from solweig_light import pipeline  # noqa: E402
from solweig_light.runtime import get_runtime_options, plan_admission  # noqa: E402
from solweig_light.radiation import ground_view, _math_profile  # noqa: E402
T_SOLWEIG_IMPORT_S = time.monotonic() - T_SOLWEIG_IMPORT_START

# --- route observation: wrap the two GVF leaves engine.gvf_2018a dispatches
# between (engine.py reads these attributes at call time). Wrappers call the
# originals through; nothing is mocked or replaced numerically.
ROUTE_EVENTS: list[str] = []
OBSERVATIONS: dict = {}


def _native_snapshot(tag: str) -> dict:
    try:
        layer = numba.threading_layer()
        layer_error = None
    except Exception as error:  # not initialized until a parallel kernel runs
        layer, layer_error = None, f"{type(error).__name__}: {error}"
    try:
        tid = int(numba.get_thread_id())
    except Exception:
        tid = None
    return {"tag": tag,
            "numba_get_num_threads": int(numba.get_num_threads()),
            "numba_config_NUMBA_NUM_THREADS": int(numba.config.NUMBA_NUM_THREADS),
            "numba_get_thread_id": tid,
            "numba_threading_layer": layer,
            "threading_layer_error": layer_error,
            "wall_since_start_s": round(time.monotonic() - T_MONOTONIC_START, 3)}


def _wrap_leaf(name: str, route_name: str) -> None:
    original = getattr(ground_view, name)

    def recorder(*args, **kwargs):
        if not ROUTE_EVENTS:  # first real kernel entry of this run
            OBSERVATIONS["first_kernel_entry"] = _native_snapshot(route_name)
        ROUTE_EVENTS.append(route_name)
        return original(*args, **kwargs)

    recorder.__wrapped_original__ = original
    setattr(ground_view, name, recorder)


_wrap_leaf("_gvf_fused", "gvf_fused_g03")
_wrap_leaf("gvf_2018a", "gvf_serial_full")


def matching_files(folder: Path, extension: str) -> dict:
    mapping = {key: path for key, path in pipeline.files_by_key(folder).items()
               if path.suffix == extension}
    import re
    for path in sorted(folder.iterdir()):
        if path.suffix != extension:
            continue
        match = re.search(r"_(\d+)_(\d+)", path.name)
        if match:
            mapping["_".join(match.groups())] = path
    return mapping


def output_manifest(run_dir: Path) -> list[dict]:
    entries = []
    for path in sorted(run_dir.rglob("*")):
        rel = path.relative_to(run_dir)
        if path.is_file() and not any(part.startswith(".solweig-light")
                                      for part in rel.parts):
            entries.append({"path": str(rel), "size": path.stat().st_size,
                            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return entries


def main() -> int:
    scene_src = Path(ARGS.scene_src).resolve()
    if RUN_DIR.exists():
        shutil.rmtree(RUN_DIR)
    shutil.copytree(scene_src, RUN_DIR)
    # Stale artifacts from earlier runs of the source scene are infra, not
    # inputs; run_tile republishes output_folder/<tile> itself.
    stale_output = RUN_DIR / "output_folder"
    removed_stale = False
    if stale_output.exists():
        shutil.rmtree(stale_output)
        removed_stale = True
    prep = RUN_DIR / "processed_inputs"
    required = ["Building_DSM", "Trees", "DEM", "metfiles", "walls", "aspect"]
    maps = {name: matching_files(prep / name, ".txt" if name == "metfiles" else ".tif")
            for name in required}
    common = set.intersection(*(set(mapping) for mapping in maps.values()))
    tile = sorted(common)[0]
    paths = {name: mapping[tile] for name, mapping in maps.items()}

    from osgeo import gdal
    dataset = gdal.Open(str(paths["Building_DSM"]), gdal.GA_ReadOnly)
    actual_shape = [dataset.RasterYSize, dataset.RasterXSize]
    dataset = None

    options = RuntimeOptions(memory_budget_bytes=12 * 1024**3, cpu_budget=4,
                             workers=ARGS.workers, threads_per_worker=ARGS.threads,
                             block_pixels=1024, checkpoint_interval=1,
                             cache_enabled=True, legacy_cache_policy="recompute")
    plan = plan_admission([{"rows": actual_shape[0], "cols": actual_shape[1]}], options)
    flags = dict(save_tmrt=True, save_svf=True, save_kup=True, save_kdown=True,
                 save_lup=True, save_ldown=True, save_shadow=True, save_wbgt=True,
                 save_ta=True, save_wind=True)

    t0 = time.monotonic()
    with runtime_options(options):
        pipeline.run_tile(str(RUN_DIR), str(prep), "2020-07-18", tile, paths,
                          flags, runtime=options)
    run_elapsed = time.monotonic() - t0

    final_native = _native_snapshot("after_run")
    manifest = output_manifest(RUN_DIR)
    if not ARGS.keep_run_dir:
        shutil.rmtree(RUN_DIR)
        shutil.rmtree(NUMBA_CACHE_DIR, ignore_errors=True)

    record = {
        "schema": "sw6-thread-child-v1",
        "requested": {"label": ARGS.label, "threads_per_worker": ARGS.threads,
                      "workers": ARGS.workers},
        "env_threads_at_numerical_import": ENV_THREADS_AT_START,
        "numba": {"config_NUMBA_NUM_THREADS": CONFIG_THREADS,
                  "default_mask_at_import": int(DEFAULT_MASK_AT_IMPORT),
                  "set_num_threads_called": SET_NUM_THREADS_CALLED,
                  "set_num_threads_error": SET_NUM_THREADS_ERROR,
                  "final_get_num_threads": final_native["numba_get_num_threads"],
                  "threading_layer": final_native["numba_threading_layer"],
                  "threading_layer_error": final_native["threading_layer_error"],
                  "version": numba.__version__},
        "route": {"observed_events": ROUTE_EVENTS,
                  "observed_counts": {name: ROUTE_EVENTS.count(name) for name in
                                      sorted(set(ROUTE_EVENTS))},
                  "observation_point": "ground_view leaf wrappers installed around "
                                       "engine.gvf_2018a dispatch targets (call-through)",
                  "first_kernel_entry": OBSERVATIONS.get("first_kernel_entry")},
        "admission": {"requested_workers": ARGS.workers,
                      "plan_active_workers": plan.active_workers,
                      "plan_native_threads": plan.native_threads,
                      "options_requested_native_threads": options.requested_native_threads},
        "options": options.as_dict(),
        "runtime_context_inside_run": {"threads_per_worker":
                                       get_runtime_options().threads_per_worker},
        "versions": {"python": platform.python_version(),
                     "python_implementation": platform.python_implementation(),
                     "numpy": np.__version__, "numba": numba.__version__,
                     "llvmlite": __import__("llvmlite").__version__,
                     "gdal": gdal.__version__,
                     "machine": platform.machine(), "system": platform.system()},
        "math_profile": _math_profile.profile_identity(),
        "module_origin": {"solweig_light": Path(solweig_light.__file__).resolve().as_posix(),
                          "pipeline": Path(pipeline.__file__).resolve().as_posix(),
                          "site_arg": str(Path(ARGS.site).resolve())},
        "workload": {"scene_src": str(scene_src), "tile": tile,
                     "actual_shape": actual_shape, "date": "2020-07-18",
                     "timesteps": 24, "flags": sorted(flags),
                     "numba_cache_dir": str(NUMBA_CACHE_DIR),
                     "jit_state": "cold_per_child_fresh_NUMBA_CACHE_DIR",
                     "pipeline_cache_state": "cold_fresh_run_dir_legacy_recompute"},
        "timing_s": {"numpy_numba_import": round(T_NUMPY_IMPORT_S, 3),
                     "solweig_import": round(T_SOLWEIG_IMPORT_S, 3),
                     "run_tile_total": round(run_elapsed, 3),
                     "child_total": round(time.monotonic() - T_MONOTONIC_START, 3)},
        "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "peak_rss_note": "macOS ru_maxrss is bytes",
        "process": {"pid": os.getpid(), "parent_pid": os.getppid()},
        "output_manifest": {"file_count": len(manifest), "files": manifest},
        "stale_output_folder_removed": removed_stale,
        "run_dir_kept": bool(ARGS.keep_run_dir),
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(record, indent=1) + "\n")
    print(json.dumps({"out": str(OUT_PATH),
                      "label": ARGS.label,
                      "requested_threads": ARGS.threads,
                      "native_mask": record["numba"]["final_get_num_threads"],
                      "route_counts": record["route"]["observed_counts"],
                      "run_tile_s": record["timing_s"]["run_tile_total"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
