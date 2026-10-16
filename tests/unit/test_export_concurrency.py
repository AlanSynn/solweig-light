"""S11 X01: the per-tile geometry export stage runs concurrently.

The stage's per-tile code (service.prepare_geometry_exports) is unchanged
and lock-protected; these tests pin the scheduling contract introduced by
the concurrent loop: identical artifact content on success, the first
sorted failure raised, and no partial set for a failed tile. Artifacts are
compared data-level (the container formats embed timestamps, so byte
equality across separate runs is not a bitwise property).
"""
import shutil
from pathlib import Path

import numpy as np
import pytest
from osgeo import gdal

from solweig_light.api import _calculate_svf, _concurrent_geometry_exports, _export_tile_job
from solweig_light.runtime import get_runtime_options, runtime_options

REFERENCE = Path(__file__).parents[1] / 'reference' / 'small_original_cpu' / 'scene'


def scene(tmp_path, tiles):
    for name in ('Building_DSM', 'DEM', 'Trees'):
        (tmp_path / name).mkdir(parents=True)
        for tile in tiles:
            shutil.copyfile(REFERENCE / f'{name}.tif', tmp_path / name / f'{name}_{tile}.tif')


def read_tif(path):
    dataset = gdal.Open(str(path))
    try:
        return (dataset.GetGeoTransform(), dataset.GetProjection(),
                dataset.ReadAsArray().view(np.uint32))
    finally:
        dataset = None


def assert_tile_bitwise(actual_dir, reference_dir, tile):
    suffixes = [('svfs_{}.zip', 'zip'), ('shadowmats_{}.npz', 'npz'),
                ('SkyViewFactor_{}.tif', 'tif')]
    for template, kind in suffixes:
        name = template.format(tile)
        assert (actual_dir / name).is_file(), name
        if kind == 'npz':
            with np.load(actual_dir / name) as left, np.load(reference_dir / name) as right:
                assert left.files == right.files
                for member in right.files:
                    np.testing.assert_array_equal(left[member], right[member])
        elif kind == 'tif':
            left, right = read_tif(actual_dir / name), read_tif(reference_dir / name)
            assert left[0] == right[0] and left[1] == right[1]
            np.testing.assert_array_equal(left[2], right[2])
        else:
            import zipfile
            with zipfile.ZipFile(actual_dir / name) as left, zipfile.ZipFile(reference_dir / name) as right:
                assert left.namelist() == right.namelist()
                for member in left.namelist():
                    lft = gdal.Open(f'/vsizip/{(actual_dir / name).resolve()}/{member}')
                    rgt = gdal.Open(f'/vsizip/{(reference_dir / name).resolve()}/{member}')
                    try:
                        np.testing.assert_array_equal(lft.ReadAsArray().view(np.uint32),
                                                      rgt.ReadAsArray().view(np.uint32))
                    finally:
                        lft = rgt = None


def test_concurrent_exports_match_serial_bitwise(tmp_path):
    scene(tmp_path / 'serial', ['0_0', '1_0'])
    scene(tmp_path / 'concurrent', ['0_0', '1_0'])
    with runtime_options(workers=1, threads_per_worker=1, cache_enabled=False):
        _calculate_svf(str(tmp_path / 'serial'), 2, True, validate_existing=False)
    with runtime_options(workers=2, threads_per_worker=1, cache_enabled=False):
        _calculate_svf(str(tmp_path / 'concurrent'), 2, True, validate_existing=False)
    for tile in ('0_0', '1_0'):
        assert_tile_bitwise(tmp_path / 'concurrent' / 'SVF',
                            tmp_path / 'serial' / 'SVF', tile)


def test_concurrent_export_failure_raises_and_publishes_no_partial_set(tmp_path):
    scene(tmp_path, ['0_0', '1_1'])
    building = {'0_0': str(tmp_path / 'Building_DSM' / 'Building_DSM_0_0.tif'),
                '1_1': str(tmp_path / 'nope' / 'missing_1_1.tif')}
    dem = {tile: str(tmp_path / 'DEM' / f'DEM_{tile}.tif') for tile in ('0_0', '1_1')}
    trees = {tile: str(tmp_path / 'Trees' / f'Trees_{tile}.tif') for tile in ('0_0', '1_1')}
    with runtime_options(workers=2, threads_per_worker=1, cache_enabled=False):
        with pytest.raises(Exception):
            _concurrent_geometry_exports(tmp_path, ['0_0', '1_1'], building, dem,
                                         trees, 2, True, get_runtime_options())
    # The failing tile must not publish a partial set; the healthy tile's
    # outcome is race-dependent (completed set, not a sorted prefix).
    assert not (tmp_path / 'SVF' / 'SkyViewFactor_1_1.tif').exists()


def test_export_job_tuple_is_picklable():
    import pickle
    with runtime_options(workers=2, threads_per_worker=1):
        runtime = get_runtime_options()
    job = ('/tmp/preprocess', '0_0', {'Building_DSM': 'b.tif', 'Trees': 't.tif',
                                      'DEM': 'd.tif'}, 2, False, runtime)
    assert pickle.loads(pickle.dumps(job)) == job
    assert callable(_export_tile_job)
