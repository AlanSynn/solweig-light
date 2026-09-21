#!/usr/bin/env python3
"""C5-15 stage census v2: cProfile one warm in-process tile run.

Uses pipeline.run_tile directly (execute_tiles always spawns a child). Requires
a prepared preprocess_dir (from one prior thermal_comfort call).
Run: census_v2.py <preprocess_dir> <out_json>
"""
from __future__ import annotations
import cProfile
import json
import pstats
import re
import sys
from pathlib import Path

PREP = Path(sys.argv[1])
OUT = Path(sys.argv[2])


def matching_files(folder, extension):
    mapping = {key: path for key, path in __import__('solweig_light.pipeline', fromlist=['files_by_key']).files_by_key(folder).items() if path.suffix == extension}
    for path in sorted(folder.iterdir()):
        if path.suffix != extension:
            continue
        match = re.search(r'_(\d+)_(\d+)', path.name)
        if match:
            mapping['_'.join(match.groups())] = path
    return mapping


def main() -> int:
    from solweig_light import RuntimeOptions, runtime_options
    from solweig_light.pipeline import run_tile

    required = ['Building_DSM', 'Trees', 'DEM', 'metfiles', 'walls', 'aspect']
    maps = {name: matching_files(PREP / name, '.txt' if name == 'metfiles' else '.tif')
            for name in required}
    common = set.intersection(*(set(mapping) for mapping in maps.values()))
    tile = sorted(common)[0]
    paths = {name: mapping[tile] for name, mapping in maps.items()}
    flags = dict(save_tmrt=True, save_svf=True, save_kup=True, save_kdown=True,
                 save_lup=True, save_ldown=True, save_shadow=True, save_wbgt=True,
                 save_ta=True, save_wind=True)
    options = RuntimeOptions(memory_budget_bytes=12 * 1024**3, cpu_budget=4, workers=1,
                             threads_per_worker=4, block_pixels=1024,
                             checkpoint_interval=1, cache_enabled=True,
                             legacy_cache_policy="recompute")
    profiler = cProfile.Profile()
    with runtime_options(options):
        profiler.enable()
        run_tile(str(PREP.parent), str(PREP), "2020-07-18", tile, paths, flags, runtime=options)
        profiler.disable()

    stats = pstats.Stats(profiler)
    rows = []
    for func, (cc, nc, tt, ct, callers) in stats.stats.items():
        filename, lineno, name = func
        rows.append({"file": filename, "line": lineno, "name": name,
                     "calls": nc, "tottime": round(tt, 4), "cumtime": round(ct, 4)})
    rows.sort(key=lambda r: -r["cumtime"])
    payload = {
        "schema": "c5-15-stage-census-v2",
        "fixture": str(PREP),
        "config": {"threads_per_worker": 4, "block_pixels": 1024, "workers": 1},
        "measurement_class": "diagnostic stage census, not benchmark timing",
        "profile_total_seconds": round(stats.total_tt, 4),
        "top_by_cumtime": rows[:100],
    }
    OUT.write_text(json.dumps(payload, indent=1))
    print(json.dumps({"total_s": round(stats.total_tt, 3), "out": str(OUT)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
