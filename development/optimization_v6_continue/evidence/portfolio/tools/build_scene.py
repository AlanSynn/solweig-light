#!/usr/bin/env python3
"""C6-80 deterministic scene builder: 2 distinct tiles at 128 and 256 square.

Pattern reused from the pinned C6-10 geometry_recipe fixture
(tests/optimization_v6/geometry_recipe/scene_fixtures.py, verbatim
``dense_urban`` 32-pixel motif of the pinned p7 generator 0038d13 lineage,
no RNG).  Each scene holds TWO tiles with distinct content (per-tile motif
height shift + tree-band shift), laid out as a ready ``processed_inputs``
tree so the measured workflow can start at the public post-preprocess entry
(walls/aspect, SVF geometry and simulation are all INSIDE the timed stages).

Met file is a byte-for-byte copy of the real own-met file used by the C6-01
dense256 workload (24 records + header).  Scenes are built ONCE and hashed;
every measured run copies the pristine scene fresh (cold) or reuses the run
copy (warm).
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

PORTFOLIO = Path(__file__).resolve().parents[1]
SCENES = PORTFOLIO / "scenes"
DENSE256 = Path("/Users/alansynn/Workspace/solweig-light-claude-v5/optimization_v5_claude"
                "/evidence/census/scene_dense256/processed_inputs/metfiles/metfile_0_0.txt")
EPSG = 32618
DATE = "2020-07-18"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _motif(size: int, tile_index: int):
    """dense_urban 32-pixel motif; tile_index shifts heights/trees -> distinct tiles.

    (motif lineage: pinned p7 generator 00318d13, as recorded in the C6-10
    scene_fixtures.py docstring)
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


def build_scene(size: int) -> dict:
    import numpy as np
    from osgeo import gdal, osr
    gdal.UseExceptions()
    destination = SCENES / f"scene_t{size}"
    if destination.exists():
        shutil.rmtree(destination)
    prep = destination / "processed_inputs"
    for name in ("Building_DSM", "DEM", "Trees", "metfiles"):
        (prep / name).mkdir(parents=True)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(EPSG)
    hashes = {}
    for tile_index, tile in enumerate(("0_0", "1_0")):
        dem, building, trees = _motif(size, tile_index)
        # Spatially coherent extents: tile 1_0 sits S pixels east of 0_0.
        x0 = 583017.5 + size * tile_index - size / 2
        transform = (x0, 1., 0., 4506984. + size / 2, 0., -1.)
        for name, values in (("DEM", dem), ("Building_DSM", building), ("Trees", trees)):
            path = prep / name / f"{name}_{tile}.tif"
            dataset = gdal.GetDriverByName("GTiff").Create(str(path), size, size, 1, gdal.GDT_Float32)
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
    info = {
        "schema": "sw6-portfolio-scene-v1",
        "dir": str(destination),
        "tile_size": [size, size],
        "tiles": ["0_0", "1_0"],
        "tile_distinction": "motif height/tree shift by tile index (deterministic, no RNG)",
        "motif": "dense_urban 32-pixel motif (pinned p7 generator lineage), no RNG",
        "met_source": str(DENSE256),
        "met_records_including_header": sum(1 for _ in open(DENSE256)),
        "epsg": EPSG,
        "sha256": hashes,
        "layout": "processed_inputs/{Building_DSM,DEM,Trees,metfiles}; walls/aspect/SVF/"
                  "cache are produced INSIDE the measured stages, pristine scene has none",
    }
    (destination / "scene_manifest.json").write_text(json.dumps(info, indent=1) + "\n")
    return info


def main() -> int:
    payload = {f"scene_t{size}": build_scene(size) for size in (128, 256)}
    out = PORTFOLIO / "scene_manifests.json"
    out.write_text(json.dumps(payload, indent=1) + "\n")
    print(json.dumps({"out": str(out),
                      "scenes": {key: value["tile_size"] for key, value in payload.items()}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
