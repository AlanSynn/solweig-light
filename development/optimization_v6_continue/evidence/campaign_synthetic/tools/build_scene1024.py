#!/usr/bin/env python3
"""C6-101r SYNTHETIC scene builder: 4 DISTINCT tiles at 1024 square.

SYNTHETIC dev-tier load fixture — never an actual-target claim (the 24-tile
dataset is absent; VALIDATION_POLICY "Final-only campaign").

Pattern reused verbatim from the C6-80 portfolio builder
(optimization_v6_continue/evidence/portfolio/tools/build_scene.py):
dense_urban 32-pixel motif of the pinned p7 generator lineage, no RNG, and a
real own-met file byte-for-byte from the C6-01 dense256 workload (header +
24 records).  Extension: FOUR tiles (``0_0`` ``1_0`` ``0_1`` ``1_1``) on a
2x2 spatial grid, each with distinct content via the per-tile motif height
AND tree shift (tile index 0..3), so per-tile input sha256 must be distinct.

Pristine layout: no walls/aspect/SVF/cache — all produced INSIDE the timed
stages.  Scenes are built ONCE and hashed.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

CAMPAIGN = Path(__file__).resolve().parents[1]
SCENES = CAMPAIGN / "scenes"
DENSE256 = Path("/Users/alansynn/Workspace/solweig-light-claude-v5/optimization_v5_claude"
                "/evidence/census/scene_dense256/processed_inputs/metfiles/metfile_0_0.txt")
EPSG = 32618
SIZE = 1024
TILES = ("0_0", "1_0", "0_1", "1_1")  # naming = (col, row) as in the C6-80 scenes


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _motif(size: int, tile_index: int):
    """dense_urban 32-pixel motif; tile_index shifts heights/trees -> distinct tiles.

    (motif lineage: pinned p7 generator lineage, as recorded in the C6-80
    build_scene.py docstring; deterministic, no RNG)
    """
    import numpy as np
    dem = np.full((size, size), 3, dtype=np.float32)
    building = dem.copy()
    trees = np.zeros_like(dem)
    for row in range(0, size, 32):
        for col in range(0, size, 32):
            height = 16 + 8 * ((row // 32 + col // 32 + tile_index) % 3)
            building[row+4:row+28, col+4:col+28] += height
            building[row+12:row+20, col+12:col+20] = dem[row+12:row+20, col+12:col+20]
            trees[row+1+tile_index:row+3+tile_index, col+14:col+18] = 6
    return dem, building, trees


def build_scene() -> dict:
    import numpy as np
    from osgeo import gdal, osr
    gdal.UseExceptions()
    destination = SCENES / f"scene_t{SIZE}"
    if destination.exists():
        shutil.rmtree(destination)
    prep = destination / "processed_inputs"
    for name in ("Building_DSM", "DEM", "Trees", "metfiles"):
        (prep / name).mkdir(parents=True)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(EPSG)
    hashes = {}
    positions = {"0_0": (0, 0), "1_0": (1, 0), "0_1": (0, 1), "1_1": (1, 1)}
    for tile_index, tile in enumerate(TILES):
        col, row = positions[tile]
        dem, building, trees = _motif(SIZE, tile_index)
        # Spatially coherent 2x2 grid: col step = SIZE east, row step = SIZE south.
        x0 = 583017.5 + SIZE * col - SIZE / 2
        transform = (x0, 1., 0., 4506984. + SIZE / 2 - SIZE * row, 0., -1.)
        for name, values in (("DEM", dem), ("Building_DSM", building), ("Trees", trees)):
            path = prep / name / f"{name}_{tile}.tif"
            dataset = gdal.GetDriverByName("GTiff").Create(str(path), SIZE, SIZE, 1, gdal.GDT_Float32)
            dataset.SetGeoTransform(transform)
            dataset.SetProjection(srs.ExportToWkt())
            dataset.GetRasterBand(1).WriteArray(values)
            dataset = None
            check = gdal.Open(str(path))
            assert np.array_equal(check.ReadAsArray(), values), f"read-back failed: {path}"
            check = None
            hashes[str(path.relative_to(destination))] = _sha256(path)
        met_target = prep / "metfiles" / f"metfile_{tile}.txt"
        shutil.copyfile(DENSE256, met_target)
        hashes[str(met_target.relative_to(destination))] = _sha256(met_target)
    def _distinct_across_tiles(name: str) -> int:
        if name == "metfiles":
            keys = [str(Path("processed_inputs") / "metfiles" / f"metfile_{tile}.txt")
                    for tile in TILES]
        else:
            keys = [str(Path("processed_inputs") / name / f"{name}_{tile}.tif")
                    for tile in TILES]
        return len({hashes[key] for key in keys})

    per_tile_distinct = {name: _distinct_across_tiles(name)
                         for name in ("DEM", "Building_DSM", "Trees", "metfiles")}
    info = {
        "schema": "sw6-campaign-synthetic-scene-v1",
        "label": "SYNTHETIC dev-tier load fixture (C6-101r); NOT the actual-target dataset",
        "dir": str(destination),
        "tile_size": [SIZE, SIZE],
        "tiles": list(TILES),
        "tile_grid": positions,
        "tile_distinct_building_sha_count": per_tile_distinct,
        "tile_distinction": "motif height/tree shift by tile index 0..3 (deterministic, no RNG)",
        "motif": "dense_urban 32-pixel motif (pinned p7 generator lineage), no RNG",
        "met_source": str(DENSE256),
        "met_records_including_header": sum(1 for _ in open(DENSE256)),
        "epsg": EPSG,
        "sha256": hashes,
        "layout": "processed_inputs/{Building_DSM,DEM,Trees,metfiles}; walls/aspect/SVF/"
                  "cache are produced INSIDE the timed stages, pristine scene has none",
    }
    (destination / "scene_manifest.json").write_text(json.dumps(info, indent=1) + "\n")
    return info


def main() -> int:
    info = build_scene()
    out = CAMPAIGN / "scene_manifest.json"
    out.write_text(json.dumps(info, indent=1) + "\n")
    print(json.dumps({"out": str(out), "tile_size": info["tile_size"],
                      "tiles": info["tiles"],
                      "distinct_building_hashes": info["tile_distinct_building_sha_count"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
