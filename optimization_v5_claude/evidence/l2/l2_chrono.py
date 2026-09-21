#!/usr/bin/env python3
"""C5-40 L2 chronological check: run_tile on dense_urban_256, hash all artifacts.

Run: l2_chrono.py <scene_src> <run_dir> <out_json>
Copies the prepared scene (processed_inputs present) to a fresh run dir, runs
one in-process run_tile (24 steps, 153 patches), then records sha256 + size +
relative path for every file under the run dir. Candidate runs are compared
against the pristine reference manifest by the caller (compare mode).
"""
from __future__ import annotations
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

SCENE_SRC = Path(sys.argv[1])
RUN_DIR = Path(sys.argv[2])
OUT = Path(sys.argv[3])
COMPARE = len(sys.argv) > 4 and sys.argv[4] == "--compare"


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


def main() -> int:
    from solweig_light import RuntimeOptions, runtime_options
    from solweig_light.pipeline import run_tile

    if RUN_DIR.exists():
        shutil.rmtree(RUN_DIR)
    shutil.copytree(SCENE_SRC, RUN_DIR)
    prep = RUN_DIR / "processed_inputs"
    required = ['Building_DSM', 'Trees', 'DEM', 'metfiles', 'walls', 'aspect']
    maps = {name: matching_files(prep / name, '.txt' if name == 'metfiles' else '.tif')
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
    with runtime_options(options):
        run_tile(str(RUN_DIR), str(prep), "2020-07-18", tile, paths, flags, runtime=options)

    entries = []
    for path in sorted(RUN_DIR.rglob("*")):
        rel = path.relative_to(RUN_DIR)
        if path.is_file() and not any(part.startswith('.solweig-light') for part in rel.parts):
            # Volatile infrastructure (transaction ids, locks, cache trees,
            # incl. nested cache generations) is excluded; every remaining
            # artifact must be bit-identical across runs and commits.
            data = path.read_bytes()
            entries.append({"path": str(rel), "size": len(data),
                            "sha256": hashlib.sha256(data).hexdigest()})
    payload = {
        "schema": "c5-40-l2-chrono-v1",
        "scene_src": str(SCENE_SRC),
        "run_dir": str(RUN_DIR),
        "tile": tile,
        "config": {"threads_per_worker": 4, "block_pixels": 1024, "workers": 1,
                   "checkpoint_interval": 1, "cache_enabled": True},
        "files": entries,
    }
    OUT.write_text(json.dumps(payload, indent=1))
    print(json.dumps({"files": len(entries), "out": str(OUT)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
