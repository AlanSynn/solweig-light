#!/usr/bin/env python3
"""C6-80 portfolio child: one measured cold/warm run in a fresh process.

Reuses the C6-01 child-isolation discipline (thread limits set BEFORE any
numerical import, native mask verified, call-through route wrappers, no
profiler) with the public three-stage workflow of dossier-01's cold census:

  stage A walls_aspect : api.run_walls_aspect          (geometry production)
  stage B svf_geometry : api.calculate_svf             (geometry production via
                         the shared C6-10 recipe + export/publication; at
                         workers>1 & cache_enabled & >1 pending tiles the
                         C6-40 GEOMETRY phase barrier runs first)
  stage C simulation   : api.run_utci_tiles, 10 flags  (24 timesteps per tile)

Component separation comes from call-through wrappers on:
  - GeometryStore.get_or_create   (times every producer callback -> production
                                   seconds per key; parent-process only, phase
                                   children roll up into the phase wall)
  - service.prepare_geometry_exports (per-tile export totals)
  - runtime_phases.execute_geometry_phase (integrated only; absent at base)
  - the two ground_view leaves    (C6-01 GVF route telemetry, unchanged)

The pristine scene is copied ONCE per cell by the cold run; warm runs reuse
the same run dir (geometry cache + published exports) in place.
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

PARSER = argparse.ArgumentParser(description=__doc__)
PARSER.add_argument("--site", required=True, help="solweig_light src tree to import")
PARSER.add_argument("--scene-src", required=True, help="pristine scene dir (copied on cold)")
PARSER.add_argument("--run-root", required=True)
PARSER.add_argument("--temp", choices=("cold", "warm_geom", "warm_full"), required=True)
PARSER.add_argument("--workers", type=int, required=True)
PARSER.add_argument("--threads", type=int, required=True)
PARSER.add_argument("--cpu-budget", type=int, default=4)
PARSER.add_argument("--memory-budget-gib", type=int, default=12)
PARSER.add_argument("--block-pixels", type=int, default=1024)
PARSER.add_argument("--numba-cache-dir", default=None,
                    help="override NUMBA_CACHE_DIR (warm_geom points at a fresh dir)")
PARSER.add_argument("--out", required=True)
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
NUMBA_CACHE_DIR = (Path(ARGS.numba_cache_dir) if ARGS.numba_cache_dir
                   else RUN_ROOT / "numba_cache").resolve()
os.environ["NUMBA_CACHE_DIR"] = str(NUMBA_CACHE_DIR)
ENV_THREADS_AT_START = {name: os.environ.get(name) for name in THREAD_VARS}
GDAL_CACHEMAX_AT_START = os.environ.get("GDAL_CACHEMAX")

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
SITE = str(Path(ARGS.site).resolve())
sys.path.insert(0, SITE)
# Deployment parity: execute_tiles and the C6-40 phase pool spawn worker
# children via `python -m solweig_light.runtime_worker`; those children inherit
# this process environment (runtime._child_environment = os.environ.copy()).
# An installed-wheel deployment imports the package the same way.
_path = os.environ.get("PYTHONPATH")
os.environ["PYTHONPATH"] = SITE if not _path else SITE + os.pathsep + _path
import solweig_light  # noqa: E402
from solweig_light import api, pipeline, runtime_options  # noqa: E402
from solweig_light.runtime import get_runtime_options, plan_admission  # noqa: E402
from solweig_light.radiation import ground_view, _math_profile  # noqa: E402
from solweig_light.cache.geometry import GeometryStore  # noqa: E402
from solweig_light.geometry import service as geometry_service  # noqa: E402
T_SOLWEIG_IMPORT_S = time.monotonic() - T_SOLWEIG_IMPORT_START

import dataclasses  # noqa: E402  (stdlib; kept after stdlib-only argparse head)

# --- call-through instrumentation (diagnostic; no numerics altered) ---------
STORE_CALLS: list[dict] = []
PHASE_CALLS: list[dict] = []
ROUTE_EVENTS: list[str] = []
FIRST_KERNEL_SNAPSHOT: dict = {}

try:
    from solweig_light import runtime_phases as _runtime_phases  # noqa: E402
    HAS_PHASES = True
except ImportError:
    _runtime_phases = None
    HAS_PHASES = False


def _native_snapshot(tag: str) -> dict:
    try:
        layer = numba.threading_layer()
        layer_error = None
    except Exception as error:
        layer, layer_error = None, f"{type(error).__name__}: {error}"
    return {"tag": tag,
            "numba_get_num_threads": int(numba.get_num_threads()),
            "numba_config_NUMBA_NUM_THREADS": int(numba.config.NUMBA_NUM_THREADS),
            "numba_threading_layer": layer,
            "threading_layer_error": layer_error,
            "wall_since_start_s": round(time.monotonic() - T_MONOTONIC_START, 3)}


def _key_id(key) -> dict:
    """Distinguish the standalone vs pipeline geometry identities (C6-02)."""
    if isinstance(key, dict):
        return {"keys": sorted(key),
                "has_standalone_implementation": "standalone_implementation" in key,
                "has_construction": "construction" in key,
                "digest": hashlib.sha256(
                    json.dumps(key, sort_keys=True, default=str).encode()).hexdigest()[:16]}
    return {"repr": str(key)[:120]}


_orig_get_or_create = GeometryStore.get_or_create


def _timed_get_or_create(self, key, producer, *args, **kwargs):
    production = {"s": 0.0, "n": 0}

    def timed_producer():
        t0 = time.monotonic()
        try:
            return producer()
        finally:
            production["s"] += time.monotonic() - t0
            production["n"] += 1
    t0 = time.monotonic()
    handle = _orig_get_or_create(self, key, timed_producer, *args, **kwargs)
    elapsed = time.monotonic() - t0
    STORE_CALLS.append({"key": _key_id(key), "total_s": round(elapsed, 4),
                        "production_s": round(production["s"], 4),
                        "production_calls": production["n"],
                        "hit": bool(getattr(handle, "hit", False))})
    return handle


GeometryStore.get_or_create = _timed_get_or_create

_orig_exports = geometry_service.prepare_geometry_exports
EXPORT_CALLS: list[dict] = []


def _timed_exports(*args, **kwargs):
    t0 = time.monotonic()
    try:
        return _orig_exports(*args, **kwargs)
    finally:
        EXPORT_CALLS.append({"tile": str(args[1]) if len(args) > 1 else kwargs.get("tile"),
                             "s": round(time.monotonic() - t0, 4)})


geometry_service.prepare_geometry_exports = _timed_exports

if HAS_PHASES:
    _orig_phase = _runtime_phases.execute_geometry_phase

    def _timed_phase(*args, **kwargs):
        t0 = time.monotonic()
        try:
            return _orig_phase(*args, **kwargs)
        finally:
            PHASE_CALLS.append({"s": round(time.monotonic() - t0, 4)})
    _runtime_phases.execute_geometry_phase = _timed_phase


def _wrap_leaf(name: str, route_name: str) -> None:
    original = getattr(ground_view, name)

    def recorder(*args, **kwargs):
        if not ROUTE_EVENTS:
            FIRST_KERNEL_SNAPSHOT.update(_native_snapshot(route_name))
        ROUTE_EVENTS.append(route_name)
        return original(*args, **kwargs)
    recorder.__wrapped_original__ = original
    setattr(ground_view, name, recorder)


_wrap_leaf("_gvf_fused", "gvf_fused_g03")
_wrap_leaf("gvf_2018a", "gvf_serial_full")


def output_manifest(run_dir: Path) -> dict:
    files = []
    for path in sorted(run_dir.rglob("*")):
        rel = path.relative_to(run_dir)
        if path.is_file() and not any(part.startswith(".solweig-light")
                                      for part in rel.parts):
            files.append({"path": str(rel), "size": path.stat().st_size,
                          "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    # Only the final published TIFFs are byte-deterministic across runs/trees;
    # ZIP/NPZ members embed creation timestamps, so they are counted, not
    # digested (the smoke run showed their churn).
    simulation = [entry for entry in files
                  if entry["path"].startswith("output_folder/")]
    return {"file_count": len(files),
            "total_bytes": sum(entry["size"] for entry in files),
            "digest": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()[:16],
            "simulation_tiff_count": len(simulation),
            "simulation_tiff_digest": hashlib.sha256(
                json.dumps(simulation, sort_keys=True).encode()).hexdigest()[:16],
            "files": files}


def cache_census(prep: Path) -> dict:
    cache_root = prep / ".solweig-light" / "cache"
    entries = []
    if cache_root.is_dir():
        for child in sorted(cache_root.iterdir()):
            if child.is_dir():
                entries.append(child.name)
    phases_root = prep / ".solweig-light" / "phases" / "geometry"
    phase_files = sorted(path.name for path in phases_root.rglob("*") if path.is_file()) \
        if phases_root.is_dir() else []
    return {"cache_entry_count": len(entries), "cache_entries": entries[:32],
            "phase_publication_files": phase_files[:32],
            "phase_route_fired": bool(phase_files)}


def main() -> int:
    scene_src = Path(ARGS.scene_src).resolve()
    if ARGS.temp == "cold":
        if RUN_ROOT.exists():
            shutil.rmtree(RUN_ROOT)  # cold owns a fresh cache dir
        RUN_ROOT.mkdir(parents=True)
        shutil.copytree(scene_src, RUN_DIR)
        stale = RUN_DIR / "output_folder"
        if stale.exists():
            shutil.rmtree(stale)
        run_dir_fresh = True
    else:
        if not RUN_DIR.is_dir():
            raise SystemExit(f"warm run requires existing {RUN_DIR}; run the cold run first")
        run_dir_fresh = False

    manifest = json.loads((scene_src / "scene_manifest.json").read_text())
    tiles = manifest["tiles"]
    shapes = []
    for tile in tiles:
        from osgeo import gdal
        dataset = gdal.Open(str(PREP / "Building_DSM" / f"Building_DSM_{tile}.tif"), gdal.GA_ReadOnly)
        shapes.append({"tile": tile, "rows": dataset.RasterYSize, "cols": dataset.RasterXSize})
        dataset = None

    options = dataclasses.replace(
        get_runtime_options(),
        memory_budget_bytes=ARGS.memory_budget_gib * 1024**3,
        cpu_budget=ARGS.cpu_budget,
        workers=ARGS.workers,
        threads_per_worker=ARGS.threads,
        block_pixels=ARGS.block_pixels,
        checkpoint_interval=1,
        cache_enabled=True,
        legacy_cache_policy="recompute",
        cache_dir=None,
    )
    plan = plan_admission([{"rows": shape["rows"], "cols": shape["cols"]} for shape in shapes],
                          options)
    flags = dict(save_tmrt=True, save_svf=True, save_kup=True, save_kdown=True,
                 save_lup=True, save_ldown=True, save_shadow=True, save_wbgt=True,
                 save_ta=True, save_wind=True)

    STORE_CALLS.clear(), EXPORT_CALLS.clear(), PHASE_CALLS.clear()
    with runtime_options(options):
        t0 = time.monotonic()
        api.run_walls_aspect(str(PREP))
        walls_s = time.monotonic() - t0

        t0 = time.monotonic()
        api.calculate_svf(str(PREP), patch_option=2, overwrite=False)
        svf_s = time.monotonic() - t0

        exports_before = len(EXPORT_CALLS)
        stores_before = len(STORE_CALLS)
        t0 = time.monotonic()
        api.run_utci_tiles(base_path=str(RUN_DIR), preprocess_dir=str(PREP),
                           selected_date_str="2020-07-18", tile_keys=None, **flags)
        sim_s = time.monotonic() - t0
        sim_export_calls = len(EXPORT_CALLS) - exports_before
        sim_store_calls = len(STORE_CALLS) - stores_before
        sim_store_production = round(sum(call["production_s"]
                                         for call in STORE_CALLS[stores_before:]), 4)
        sim_store_hits = sum(1 for call in STORE_CALLS[stores_before:] if call["hit"])

    final_native = _native_snapshot("after_run")
    stage_b_production = round(sum(call["production_s"]
                                   for call in STORE_CALLS[:stores_before]), 4)
    stage_b_exports = round(sum(call["s"] for call in EXPORT_CALLS), 4)
    record = {
        "schema": "sw6-portfolio-child-v1",
        "requested": {"temp": ARGS.temp, "workers": ARGS.workers, "threads": ARGS.threads,
                      "cpu_budget": ARGS.cpu_budget,
                      "memory_budget_bytes": options.memory_budget_bytes,
                      "block_pixels": ARGS.block_pixels,
                      "site": str(Path(ARGS.site).resolve()),
                      "scene_src": str(scene_src)},
        "env": {"threads_at_numerical_import": ENV_THREADS_AT_START,
                "gdal_cachemax_env": GDAL_CACHEMAX_AT_START,
                "numba_cache_dir": str(NUMBA_CACHE_DIR)},
        "numba": {"config_NUMBA_NUM_THREADS": CONFIG_THREADS,
                  "set_num_threads_error": SET_NUM_THREADS_ERROR,
                  "final_get_num_threads": final_native["numba_get_num_threads"],
                  "threading_layer": final_native["numba_threading_layer"],
                  "version": numba.__version__},
        "route": {"observed_events": ROUTE_EVENTS,
                  "observed_counts": {name: ROUTE_EVENTS.count(name)
                                      for name in sorted(set(ROUTE_EVENTS))},
                  "first_kernel_entry": FIRST_KERNEL_SNAPSHOT,
                  "observation_point": "ground_view leaf wrappers (C6-01 pattern, call-through)"},
        "admission": {"plan_active_workers": plan.active_workers,
                      "plan_native_threads": plan.native_threads,
                      "requested_native_threads": options.requested_native_threads},
        "options": options.as_dict(),
        "module_origin": {"solweig_light": Path(solweig_light.__file__).resolve().as_posix(),
                          "pipeline": Path(pipeline.__file__).resolve().as_posix(),
                          "runtime_phases_present": HAS_PHASES,
                          "pythonpath_env": os.environ.get("PYTHONPATH")},
        "math_profile": _math_profile.profile_identity(),
        "workload": {"tiles": tiles, "tile_shapes": shapes, "date": "2020-07-18",
                     "timesteps_per_tile": manifest["met_records_including_header"] - 1,
                     "flags": sorted(flags), "scene_manifest": manifest,
                     "run_dir_fresh_this_run": run_dir_fresh},
        "stage_splits_s": {
            "walls_aspect": round(walls_s, 4),
            "svf_geometry_total": round(svf_s, 4),
            "svf_phase_wall": round(sum(call["s"] for call in PHASE_CALLS), 4),
            "svf_phase_calls": len(PHASE_CALLS),
            "svf_store_production": stage_b_production,
            "svf_export_calls_total": stage_b_exports,
            "svf_export_calls_count": len(EXPORT_CALLS),
            "simulation_total": round(sim_s, 4),
            "simulation_store_calls": sim_store_calls,
            "simulation_store_production": sim_store_production,
            "simulation_store_hits": sim_store_hits,
            "simulation_export_calls": sim_export_calls,
            "total_measured": round(walls_s + svf_s + sim_s, 4),
        },
        "store_calls": STORE_CALLS,
        "export_calls": EXPORT_CALLS,
        "phase_calls": PHASE_CALLS,
        "cache_census_after_run": cache_census(PREP),
        "output_manifest": output_manifest(RUN_DIR),
        "versions": {"python": platform.python_version(), "numpy": np.__version__,
                     "numba": numba.__version__,
                     "llvmlite": __import__("llvmlite").__version__,
                     "machine": platform.machine(), "system": platform.system()},
        "timing_s": {"numpy_numba_import": round(T_NUMPY_IMPORT_S, 3),
                     "solweig_import": round(T_SOLWEIG_IMPORT_S, 3),
                     "child_total": round(time.monotonic() - T_MONOTONIC_START, 3)},
        "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "peak_rss_note": "macOS ru_maxrss is bytes; parent only (worker children not summed)",
        "process": {"pid": os.getpid()},
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(record, indent=1) + "\n")
    print(json.dumps({"out": str(OUT_PATH), "temp": ARGS.temp,
                      "workers": ARGS.workers, "threads": ARGS.threads,
                      "native_mask": record["numba"]["final_get_num_threads"],
                      "stages_s": record["stage_splits_s"],
                      "route_counts": record["route"]["observed_counts"],
                      "phase_route_fired": record["cache_census_after_run"]["phase_route_fired"],
                      "cache_entries": record["cache_census_after_run"]["cache_entry_count"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
