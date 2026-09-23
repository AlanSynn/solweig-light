#!/usr/bin/env python3
"""N8-03 held-out scene builder: 128/256 square x 24 records, dense + vegetation.

Adapted from the C6-101r synthetic builder
(optimization_v6_continue/evidence/campaign_synthetic/tools/build_scene1024.py):
same dense_urban 32-pixel motif (pinned p7 generator lineage, no RNG), same
own-met TIFF generation via GDAL, same pristine processed_inputs layout
(walls/aspect/SVF produced inside timed stages, never shipped).

Adaptations recorded here (this file IS the provenance record):
  - two sizes: 128 and 256 square (single tile ``0_0`` each);
  - two variants per size: ``dense`` (motif verbatim) and ``veg`` (motif plus
    deterministic street-tree canopy lines and park-block courtyards);
  - met source: the ORIGINAL v5 dense256 own-met file is no longer present on
    this machine, so the met file is derived from the real reference scene
    own-met record (tests/reference/state_sequence_original_cpu/scene/met.txt)
    by taking the header plus the first 24 data records (day 200 = the
    2020-07-18 hourly cycle, it 0..23). Byte-deterministic, no edits to values.

LABEL: SYNTHETIC-DEVELOPMENT fixture. Per BENCHMARK_PROTOCOL a synthetic
medium motif is a development case and CANNOT represent the actual 24-tile
corpus. Scenes are built ONCE and hashed; hashes are frozen in
benchmarks/protocols/optimization_v8/n8_03_protocol.json.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

WORKTREE = Path(__file__).resolve().parents[2]
FIXTURES = WORKTREE / "benchmarks" / "fixtures" / "optimization_v8" / "scenes"
MET_SOURCE = WORKTREE / "tests" / "reference" / "state_sequence_original_cpu" / "scene" / "met.txt"
EPSG = 32618
SIZES = (128, 256)
VARIANTS = ("dense", "veg")
MET_RECORDS = 24
MET_DATE = "2020-07-18"
GENERATOR = "tools/optimization_v8/n8_03_build_scenes.py"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _met_24() -> str:
    """Header + first 24 data records of the real own-met file (day 200)."""
    lines = MET_SOURCE.read_text().splitlines()
    header, records = lines[0], lines[1:]
    if len(records) < MET_RECORDS:
        raise SystemExit(f"met source has only {len(records)} records")
    chosen = records[:MET_RECORDS]
    iys = {float(line.split()[0]) for line in chosen}
    ids = {float(line.split()[1]) for line in chosen}
    its = sorted(float(line.split()[2]) for line in chosen)
    if iys != {2020.0} or ids != {200.0} or its != [float(i) for i in range(MET_RECORDS)]:
        raise SystemExit(f"met selection is not one clean day: iy={iys} id={ids} it={its}")
    return "\n".join([header, *chosen]) + "\n"


def _motif(size: int):
    """dense_urban 32-pixel motif verbatim from build_scene1024 (tile_index=0)."""
    import numpy as np
    dem = np.full((size, size), 3, dtype=np.float32)
    building = dem.copy()
    trees = np.zeros_like(dem)
    for row in range(0, size, 32):
        for col in range(0, size, 32):
            height = 16 + 8 * ((row // 32 + col // 32) % 3)
            building[row+4:row+28, col+4:col+28] += height
            building[row+12:row+20, col+12:col+20] = dem[row+12:row+20, col+12:col+20]
            trees[row+1:row+3, col+14:col+18] = 6
    return dem, building, trees


def _vegetation(size: int, dem, trees):
    """Deterministic canopy additions; never touches building footprints.

    Street canopy at dem+6 on the E-W street strips (block rows 28..31) and
    N-S street strips (block cols 28..31); park courtyards at dem+5 on the
    carved courtyard of every other block in both dimensions.
    """
    import numpy as np
    veg = trees.copy()
    for row in range(0, size, 32):
        for col in range(0, size, 32):
            veg[row+28:row+32, col+8:col+24] = dem[row+28:row+32, col+8:col+24] + 6
            veg[row+8:row+24, col+28:col+32] = dem[row+8:row+24, col+28:col+32] + 6
            if (row // 32) % 2 == 1 and (col // 32) % 2 == 1:
                veg[row+12:row+20, col+12:col+20] = dem[row+12:row+20, col+12:col+20] + 5
    canopy = int(np.count_nonzero(veg))
    return veg, canopy, round(canopy / (size * size), 4)


def build_scene(size: int, variant: str, met_text: str) -> dict:
    import numpy as np
    from osgeo import gdal, osr
    gdal.UseExceptions()
    destination = FIXTURES / f"scene_{size}_{variant}"
    prep = destination / "processed_inputs"
    if destination.exists():
        import shutil
        shutil.rmtree(destination)
    for name in ("Building_DSM", "DEM", "Trees", "metfiles"):
        (prep / name).mkdir(parents=True)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(EPSG)
    dem, building, trees = _motif(size)
    canopy_fraction = None
    if variant == "veg":
        trees, canopy, canopy_fraction = _vegetation(size, dem, trees)
    x0 = 583017.5 - size / 2
    transform = (x0, 1., 0., 4506984. + size / 2, 0., -1.)
    hashes = {}
    for name, values in (("DEM", dem), ("Building_DSM", building), ("Trees", trees)):
        path = prep / name / f"{name}_0_0.tif"
        dataset = gdal.GetDriverByName("GTiff").Create(str(path), size, size, 1, gdal.GDT_Float32)
        dataset.SetGeoTransform(transform)
        dataset.SetProjection(srs.ExportToWkt())
        dataset.GetRasterBand(1).WriteArray(values)
        dataset = None
        check = gdal.Open(str(path))
        assert np.array_equal(check.ReadAsArray(), values), f"read-back failed: {path}"
        check = None
        hashes[str(path.relative_to(destination))] = _sha256(path)
    met_target = prep / "metfiles" / "metfile_0_0.txt"
    met_target.write_text(met_text)
    hashes[str(met_target.relative_to(destination))] = _sha256(met_target)
    return {
        "label": "SYNTHETIC-DEVELOPMENT held-out fixture (N8-03); NOT the actual 24-tile corpus",
        "dir": str(destination),
        "tile_size": [size, size],
        "tiles": ["0_0"],
        "variant": variant,
        "motif": "dense_urban 32-pixel motif (pinned p7 generator lineage), no RNG",
        "vegetation_additions": ("street canopy dem+6 on block rows 28..31 (cols 8..24) and "
                                 "cols 28..31 (rows 8..24); park courtyards dem+5 on carved "
                                 "courtyards of odd/odd 32-blocks") if variant == "veg" else None,
        "canopy_fraction_of_pixels": canopy_fraction,
        "met_source": str(MET_SOURCE),
        "met_derivation": f"header + first {MET_RECORDS} data records (day 200 = {MET_DATE} "
                          "hourly cycle, it 0..23); values unmodified",
        "met_records_including_header": MET_RECORDS + 1,
        "selected_date": MET_DATE,
        "epsg": EPSG,
        "geotransform": list(transform),
        "generator": GENERATOR,
        "generator_sha256": _sha256(WORKTREE / GENERATOR),
        "sha256": hashes,
    }


def main() -> int:
    met_text = _met_24()
    manifests = {}
    for size in SIZES:
        for variant in VARIANTS:
            info = build_scene(size, variant, met_text)
            (Path(info["dir"]) / "scene_manifest.json").write_text(json.dumps(info, indent=1) + "\n")
            manifests[f"{size}_{variant}"] = info
            print(json.dumps({"scene": f"{size}_{variant}", "dir": info["dir"],
                              "files": len(info["sha256"]),
                              "canopy_fraction": info["canopy_fraction_of_pixels"]}))
    out = FIXTURES / "n8_03_scene_manifests.json"
    out.write_text(json.dumps({
        "schema": "sw8-n8-03-scenes-v1",
        "generator": GENERATOR,
        "generator_sha256": manifests["128_dense"]["generator_sha256"],
        "met_source": str(MET_SOURCE),
        "met_source_sha256": _sha256(MET_SOURCE),
        "met_derivation": manifests["128_dense"]["met_derivation"],
        "scenes": manifests,
    }, indent=1) + "\n")
    print(json.dumps({"out": str(out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
