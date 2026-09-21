#!/usr/bin/env python3
"""C5-15 stage census: cProfile one warm dense_urban_256 run.

Diagnostic only: relative stage fractions at the selected v4 candidate config
(4 native threads, block 1024, 1 worker). Not a benchmark timing.
Run: census_v1.py <fixture_dir> <out_json>
"""
from __future__ import annotations
import cProfile
import json
import pstats
import shutil
import sys
import tempfile
from pathlib import Path

FIXTURE = Path(sys.argv[1])
OUT = Path(sys.argv[2])


def main() -> int:
    import solweig_light
    from solweig_light import RuntimeOptions, runtime_options, thermal_comfort

    work = Path(tempfile.mkdtemp(prefix="census_v1_"))
    scene = work / "scene"
    scene.mkdir()
    for name in ("Building_DSM.tif", "Trees.tif", "DEM.tif", "met.txt"):
        shutil.copy2(FIXTURE / name, scene / name)
    kwargs = json.loads((FIXTURE / "kwargs.json").read_text())
    kwargs["base_path"] = str(scene)
    kwargs["own_met_file"] = str(scene / "met.txt")

    options = RuntimeOptions(memory_budget_bytes=12 * 1024**3, cpu_budget=4, workers=1,
                             threads_per_worker=4, block_pixels=1024,
                             checkpoint_interval=1, cache_enabled=True,
                             legacy_cache_policy="recompute")

    # Warmup: first use compiles JIT; excluded from the census sample.
    with runtime_options(options):
        thermal_comfort(**kwargs)

    profiler = cProfile.Profile()
    with runtime_options(options):
        profiler.enable()
        thermal_comfort(**kwargs)
        profiler.disable()

    stats = pstats.Stats(profiler)
    rows = []
    for func, (cc, nc, tt, ct, callers) in stats.stats.items():
        filename, lineno, name = func
        rows.append({"file": filename, "line": lineno, "name": name,
                     "calls": nc, "tottime": round(tt, 4), "cumtime": round(ct, 4)})
    rows.sort(key=lambda r: -r["cumtime"])
    total = stats.total_tt
    payload = {
        "schema": "c5-15-stage-census-v1",
        "fixture": str(FIXTURE),
        "config": {"threads_per_worker": 4, "block_pixels": 1024, "workers": 1},
        "measurement_class": "diagnostic stage census, not benchmark timing",
        "profile_total_seconds": round(total, 4),
        "top_by_cumtime": rows[:80],
        "svf_stage": [r for r in rows if "svf" in r["file"] or "sky_compiled" in r["file"]][:20],
        "wall_stage": [r for r in rows if "wall_shadows" in r["file"]][:20],
        "radiation_stage": [r for r in rows if "patch_radiation" in r["file"]][:20],
        "gvf_stage": [r for r in rows if "ground_view" in r["file"]][:20],
        "decode_stage": [r for r in rows if "visibility" in r["file"]][:20],
        "engine_stage": [r for r in rows if "engine" in r["file"]][:30],
    }
    OUT.write_text(json.dumps(payload, indent=1))
    print(json.dumps({"total_s": round(total, 3), "out": str(OUT)}))
    shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
