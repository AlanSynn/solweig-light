"""Real-scene fixtures for the C6-10 geometry recipe tests (L1/L2-small).

Two genuine scenes are used, both read-only sources:

1. ``tests/reference/small_original_cpu/scene`` — the pinned 35x32 real
   reference TIFF scene (copied byte-for-byte into the test tmp dir).
2. A deterministic 96x96 dense_urban motif scene (explicit 32-pixel motif,
   no RNG), verbatim from the pinned synthetic-input generator
   ``reports/p7_fixture_sources/00318d13…py``, with the same reference own-met
   file copied byte-for-byte. This is the same fixture the C6-02 census used,
   so counts here are directly comparable to census evidence.
"""
from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SRC = REPO / 'src'
REFERENCE_SCENE = REPO / 'tests' / 'reference' / 'small_original_cpu' / 'scene'
MET_SOURCE = REFERENCE_SCENE / 'met.txt'
DATE = '2020-07-18'
SIZE = 96
TRANSFORM = (583017.5 - SIZE / 2, 1., 0., 4506984. + SIZE / 2, 0., -1.)
EPSG = 32618
INPUT_NAMES = ('Building_DSM', 'Trees', 'DEM')


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def reference_paths(tmp_path):
    """Copy the pinned real reference scene rasters; return paths + hashes."""
    paths = {}
    for name in INPUT_NAMES:
        target = tmp_path / (name + '.tif')
        shutil.copyfile(REFERENCE_SCENE / (name + '.tif'), target)
        paths[name] = target
    return {'paths': paths, 'sha256': {name: _sha256(paths[name]) for name in INPUT_NAMES},
            'origin': 'tests/reference/small_original_cpu/scene (byte-for-byte copies)', 'size': [35, 32]}


def _dense_urban_motif(size):
    """Verbatim dense_urban branch of the pinned generator's geometry()."""
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


def build_scene(destination: Path) -> dict:
    """Build the deterministic 96x96 dense_urban scene with the reference met file."""
    import numpy as np
    from osgeo import gdal, osr
    gdal.UseExceptions()
    destination.mkdir(parents=True)
    dem, building, trees = _dense_urban_motif(SIZE)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(EPSG)
    transform = TRANSFORM
    for name, values in (('DEM.tif', dem), ('Building_DSM.tif', building), ('Trees.tif', trees)):
        dataset = gdal.GetDriverByName('GTiff').Create(str(destination / name), SIZE, SIZE, 1, gdal.GDT_Float32)
        dataset.SetGeoTransform(transform)
        dataset.SetProjection(srs.ExportToWkt())
        dataset.GetRasterBand(1).WriteArray(values)
        dataset = None
        check = gdal.Open(str(destination / name))
        assert np.array_equal(check.ReadAsArray(), values), f'fixture read-back failed: {name}'
        check = None
    shutil.copyfile(MET_SOURCE, destination / 'met.txt')
    names = ('DEM.tif', 'Building_DSM.tif', 'Trees.tif', 'met.txt')
    return {'dir': destination, 'rows': SIZE, 'cols': SIZE, 'epsg': 32618,
            'transform': list(transform),
            'sha256': {name: _sha256(destination / name) for name in names},
            'generator_motif': 'dense_urban 32-pixel motif (pinned p7 generator 00318d13), no RNG',
            'met_source': 'tests/reference/small_original_cpu/scene/met.txt (byte-for-byte copy)'}


def field_bits(value):
    """Exact bit-level bytes of one producer field (packed channels decoded)."""
    import numpy as np
    array = value.to_dense() if hasattr(value, 'to_dense') else value
    return np.ascontiguousarray(array).view(np.uint32)


def fields_equal(left, right):
    """Per-field bitwise comparison (dtype, shape, signed zeros, NaN payloads)."""
    import numpy as np
    result = {}
    for name in left:
        a, b = field_bits(left[name]), field_bits(right[name])
        result[name] = bool(a.shape == b.shape and a.dtype == b.dtype and np.array_equal(a, b))
    return result
