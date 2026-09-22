#!/usr/bin/env python3
"""B7-60 SYNTHETIC 4x1024^2 scene builder (user-directed whole-pipeline A/B).

Adapted from the C6-101r builder
(optimization_v6_continue/evidence/campaign_synthetic/tools/build_scene1024.py):
identical deterministic dense_urban 32-pixel motif (no RNG), four distinct
tiles on a 2x2 grid. One substitution, disclosed in the manifest: the C6-101r
met source (scene_dense256 metfile_0_0.txt) no longer exists on this machine,
so the real own-met file of the small_original_cpu reference scene (header +
24 records, 2020-07-18, the b7_50 chronology scene) is used byte-for-byte
instead. Load fixture only — NOT the actual-target dataset.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT_ROOT = HERE.parents[1] / 'optimization_v7_backends' / 'evidence' / 'trials' / 'b7_60'
MET_SOURCE = (HERE.parents[1] / 'tests' / 'reference' / 'small_original_cpu'
              / 'scene' / 'processed_inputs' / 'metfiles' / 'metfile_0_0.txt')
EPSG = 32618
SIZE = 1024
TILES = ('0_0', '1_0', '0_1', '1_1')


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def _motif(size: int, tile_index: int):
    """dense_urban 32-pixel motif; tile_index shifts heights/trees (no RNG)."""
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
    destination = OUT_ROOT / 'scenes' / f'scene_t{SIZE}'
    if destination.exists():
        shutil.rmtree(destination)
    prep = destination / 'processed_inputs'
    for name in ('Building_DSM', 'DEM', 'Trees', 'metfiles'):
        (prep / name).mkdir(parents=True)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(EPSG)
    hashes = {}
    positions = {'0_0': (0, 0), '1_0': (1, 0), '0_1': (0, 1), '1_1': (1, 1)}
    for tile_index, tile in enumerate(TILES):
        col, row = positions[tile]
        dem, building, trees = _motif(SIZE, tile_index)
        x0 = 583017.5 + SIZE * col - SIZE / 2
        transform = (x0, 1., 0., 4506984. + SIZE / 2 - SIZE * row, 0., -1.)
        for name, values in (('DEM', dem), ('Building_DSM', building), ('Trees', trees)):
            path = prep / name / f'{name}_{tile}.tif'
            dataset = gdal.GetDriverByName('GTiff').Create(
                str(path), SIZE, SIZE, 1, gdal.GDT_Float32)
            dataset.SetGeoTransform(transform)
            dataset.SetProjection(srs.ExportToWkt())
            dataset.GetRasterBand(1).WriteArray(values)
            dataset = None
            check = gdal.Open(str(path))
            assert np.array_equal(check.ReadAsArray(), values), f'read-back failed: {path}'
            check = None
            hashes[str(path.relative_to(destination))] = _sha256(path)
        met_target = prep / 'metfiles' / f'metfile_{tile}.txt'
        shutil.copyfile(MET_SOURCE, met_target)
        hashes[str(met_target.relative_to(destination))] = _sha256(met_target)

    def _distinct(name: str) -> int:
        if name == 'metfiles':
            keys = [f'processed_inputs/metfiles/metfile_{tile}.txt' for tile in TILES]
        else:
            keys = [f'processed_inputs/{name}/{name}_{tile}.tif' for tile in TILES]
        return len({hashes[k] for k in keys})

    info = {
        'schema': 'sw7-b7-60-synthetic-scene-v1',
        'label': 'SYNTHETIC dev-tier load fixture (B7-60, user-directed); '
                 'NOT the actual-target dataset (24-tile corpus absent)',
        'dir': str(destination),
        'tile_size': [SIZE, SIZE],
        'tiles': list(TILES),
        'tile_grid': positions,
        'tile_distinct_building_sha_count': {n: _distinct(n) for n in
                                             ('DEM', 'Building_DSM', 'Trees', 'metfiles')},
        'motif': 'dense_urban 32-pixel motif (pinned p7 generator lineage), no RNG; '
                 'identical geometry bytes to the C6-101r scene_t1024 builder',
        'met_source': str(MET_SOURCE),
        'met_source_note': 'C6-101r met source (scene_dense256) no longer exists on '
                           'this machine; substituted the real own-met file of the '
                           'small_original_cpu reference scene (header + 24 records)',
        'met_records_including_header': sum(1 for _ in open(MET_SOURCE)),
        'epsg': EPSG,
        'sha256': hashes,
        'layout': 'processed_inputs/{Building_DSM,DEM,Trees,metfiles}; walls/aspect/SVF/'
                  'cache produced INSIDE the timed stages',
    }
    (destination / 'scene_manifest.json').write_text(json.dumps(info, indent=1) + '\n')
    return info


if __name__ == '__main__':
    info = build_scene()
    print(json.dumps({'scene': info['dir'],
                      'tiles': info['tiles'],
                      'distinct_building': info['tile_distinct_building_sha_count']['Building_DSM'],
                      'met_records': info['met_records_including_header']}))
