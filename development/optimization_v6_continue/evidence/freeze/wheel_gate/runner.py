#!/usr/bin/env python3
"""C6-100 wheel-gate runner: one tiny end-to-end scene, wheel or src tree.

Reuses the C6-01 child-process discipline: native thread limits are set in
the ENVIRONMENT before this process starts (the runner only records them),
NUMBA_CACHE_DIR is fresh per side, module origin is asserted, and the math
profile fingerprint is recorded.  The workload is the public
``solweig_light.api.thermal_comfort`` entry over the in-tree true small
fixture (tests/reference/small_original_cpu/scene root files, 35x32, 24 met
records) with the pinned RuntimeOptions of the C6-80 portfolio
(12 GiB budget, workers 1, threads 1, block 1024, checkpoint 1, cache on,
legacy recompute).  Every file in the run root is hashed into a manifest.

Correctness gate only -- elapsed times are recorded but no claim is made.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import sys
import time
from pathlib import Path

THREAD_LIMIT_VARS = (
    "BLIS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS",
    "NUMEXPR_NUM_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def manifest_of(root: Path) -> dict:
    files = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            files[str(path.relative_to(root))] = {
                "size": path.stat().st_size, "sha256": sha256(path)}
    return files


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene-src", required=True, type=Path)
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--label", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    record: dict = {"schema": "sw6-freeze-wheelgate-child-v1", "label": args.label}
    record["env_threads"] = {name: os.environ.get(name) for name in THREAD_LIMIT_VARS}
    record["pythonpath_env"] = os.environ.get("PYTHONPATH")
    record["loadavg_before"] = list(os.getloadavg())

    # Fresh run root with the identical scene inputs (copied, never shared).
    if args.run_root.exists():
        shutil.rmtree(args.run_root)
    args.run_root.mkdir(parents=True)
    for name in ("Building_DSM.tif", "DEM.tif", "Trees.tif", "met.txt"):
        shutil.copyfile(args.scene_src / name, args.run_root / name)
    record["scene_inputs"] = {name: sha256(args.run_root / name)
                              for name in ("Building_DSM.tif", "DEM.tif", "Trees.tif", "met.txt")}

    import numpy
    import numba
    from numba import config as numba_config

    import solweig_light
    from solweig_light import api
    from solweig_light.radiation._math_profile import profile_identity
    from solweig_light.runtime import get_runtime_options, runtime_options

    record["module_origin"] = {
        "solweig_light": solweig_light.__file__,
        "api": api.__file__,
        "package_dir": str(Path(solweig_light.__file__).resolve().parent),
        "sys_path0": sys.path[0],
    }
    record["numba"] = {
        "config_NUMBA_NUM_THREADS": numba_config.NUMBA_NUM_THREADS,
        "get_num_threads": numba.get_num_threads(),
        "threading_layer": None,
        "version": numba.__version__,
    }
    record["versions"] = {
        "python": platform.python_version(),
        "numpy": numpy.__version__,
        "numba": numba.__version__,
        "machine": platform.machine(),
        "system": platform.system(),
    }
    record["math_profile"] = profile_identity()
    try:
        numba.set_num_threads(int(os.environ["NUMBA_NUM_THREADS"]))
        record["numba"]["set_num_threads_called"] = True
    except Exception as error:  # pragma: no cover - recorded, never tuned
        record["numba"]["set_num_threads_error"] = repr(error)
    record["numba"]["final_get_num_threads"] = numba.get_num_threads()

    pinned = dict(memory_budget_bytes=12 * 1024**3, cpu_budget=4, workers=1,
                  threads_per_worker=1, block_pixels=1024, checkpoint_interval=1,
                  cache_enabled=True, legacy_cache_policy="recompute")
    record["pinned_options"] = pinned
    assert importlib_torch_absent(), "torch must not be importable (CPU gate)"
    flags = {f"save_{name}": True for name in
             ("tmrt", "svf", "kup", "kdown", "lup", "ldown", "shadow", "wbgt", "ta", "wind")}
    started = time.perf_counter()
    with runtime_options(**pinned):
        record["options_inside_run"] = get_runtime_options().as_dict()
        api.thermal_comfort(
            str(args.run_root), "2020-07-18",
            own_met_file=str(args.run_root / "met.txt"),
            tile_size=64, overlap=0, ERA_5_z0_find=False, use_own_met=True,
            use_uhi=False, **flags)
    record["workflow_seconds"] = time.perf_counter() - started
    try:
        record["numba"]["threading_layer"] = numba.threading_layer()
    except Exception as error:  # not yet resolved is fine for a record
        record["numba"]["threading_layer_error"] = repr(error)
    record["loadavg_after"] = list(os.getloadavg())
    record["output_manifest"] = manifest_of(args.run_root)
    record["output_file_count"] = len(record["output_manifest"])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=1, sort_keys=False) + "\n")
    print(json.dumps({"label": args.label, "files": record["output_file_count"],
                      "module": record["module_origin"]["solweig_light"],
                      "profile": record["math_profile"]["id"],
                      "ok": True}))
    return 0


def importlib_torch_absent() -> bool:
    import importlib.util
    return importlib.util.find_spec("torch") is None


if __name__ == "__main__":
    raise SystemExit(main())
