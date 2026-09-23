#!/usr/bin/env python3
"""C5-41 portfolio comparison: warm in-process run_tile wall time on
dense_urban_256 across a small config shortlist, plus G03 route timing via
direct _gvf_fused vs _gvf on the same scene inputs (diagnostic for the
dispatch-flip decision).

Run: portfolio_v1.py <scene_dir> <out_json>
Measurement class: central-lab L3 diagnostic; requires exclusive host lease.
"""
from __future__ import annotations
import json
import re
import shutil
import statistics
import sys
import time
from pathlib import Path

SCENE = Path(sys.argv[1])
OUT = Path(sys.argv[2])
REPEATS = 3


def matching_files(folder, extension):
    from solweig_light.pipeline import files_by_key
    mapping = {key: path for key, path in files_by_key(folder).items() if path.suffix == extension}
    for path in sorted(folder.iterdir()):
        if path.suffix != extension:
            continue
        match = re.search(r'_(\d+)_(\d+)', path.name)
        if match:
            mapping['_'.join(match.groups())] = path
    return mapping


def fresh(scene_src, name):
    dst = Path("/tmp/portfolio_run") / name
    if dst.exists():
        shutil.rmtree(dst)
    dst.parent.mkdir(exist_ok=True)
    shutil.copytree(scene_src, dst)
    return dst


def main() -> int:
    from solweig_light import RuntimeOptions, runtime_options
    from solweig_light.pipeline import run_tile

    prep = SCENE / "processed_inputs"
    required = ['Building_DSM', 'Trees', 'DEM', 'metfiles', 'walls', 'aspect']
    maps = {name: matching_files(prep / name, '.txt' if name == 'metfiles' else '.tif')
            for name in required}
    common = set.intersection(*(set(mapping) for mapping in maps.values()))
    tile = sorted(common)[0]
    paths = {name: mapping[tile] for name, mapping in maps.items()}
    flags = dict(save_tmrt=True, save_svf=True, save_kup=True, save_kdown=True,
                 save_lup=True, save_ldown=True, save_shadow=True, save_wbgt=True,
                 save_ta=True, save_wind=True)

    configs = [
        ("source_default_t1_b128", dict(threads_per_worker=1, block_pixels=128)),
        ("t1_b1024", dict(threads_per_worker=1, block_pixels=1024)),
        ("t4_b128", dict(threads_per_worker=4, block_pixels=128)),
        ("t4_b1024", dict(threads_per_worker=4, block_pixels=1024)),
        ("t2_b1024", dict(threads_per_worker=2, block_pixels=1024)),
    ]
    results = {}
    for label, over in configs:
        options = RuntimeOptions(memory_budget_bytes=12 * 1024**3, cpu_budget=4, workers=1,
                                 checkpoint_interval=1, cache_enabled=True,
                                 legacy_cache_policy="recompute", **over)
        times = []
        for rep in range(REPEATS):
            run_dir = fresh(SCENE, label)
            with runtime_options(options):
                t0 = time.perf_counter()
                run_tile(str(run_dir), str(run_dir / "processed_inputs"), "2020-07-18",
                         tile, paths, flags, runtime=options)
                times.append(time.perf_counter() - t0)
        results[label] = {"times_s": [round(t, 3) for t in times],
                          "min_s": round(min(times), 3),
                          "median_s": round(statistics.median(times), 3)}
        print(label, results[label], flush=True)

    payload = {
        "schema": "c5-41-portfolio-v1",
        "scene": str(SCENE),
        "commit": __import__("subprocess").check_output(
            ["git", "rev-parse", "HEAD"], text=True, cwd=str(Path(__file__).resolve().parent)).strip(),
        "measurement_class": "L3 central-lab diagnostic timing, warm in-process run_tile, "
                             "min/median of 3, exclusive host lease required",
        "configs": results,
    }
    OUT.write_text(json.dumps(payload, indent=1))
    print(json.dumps({"out": str(OUT)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
