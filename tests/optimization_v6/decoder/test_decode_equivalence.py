"""L1: prepared multi-channel decode is bitwise-equal to the accepted path.

Every comparison is uint32-view exact (NaN payloads, signed zeros, every
raw-mode float32 bit). Baselines are the unchanged accepted functions on the
same objects: ``patch_radiation._shortwave_visibility_blocks`` (which itself
composes decode_block and diff_from_shared_decoded) and the longwave
``_block`` triple from ``define_patch_characteristics``.
"""
import importlib.util as _ilu
import sys as _sys
from pathlib import Path as _Path
# Load THIS family's conftest by file path: bare `import conftest` is
# shadowed by sibling families' conftest modules when several test
# directories are collected in one pytest invocation.
_conftest_path = _Path(__file__).resolve().parent / 'conftest.py'
_spec = _ilu.spec_from_file_location('_decoder_conftest', str(_conftest_path))
_conftest = _ilu.module_from_spec(_spec)
_sys.modules['_decoder_conftest'] = _conftest
_spec.loader.exec_module(_conftest)
cube = _conftest.cube
mapped_roundtrip = _conftest.mapped_roundtrip
original_longwave = _conftest.original_longwave
original_shortwave = _conftest.original_shortwave
packed = _conftest.packed
recipe_longwave = _conftest.recipe_longwave
recipe_shortwave = _conftest.recipe_shortwave
assert_channels_bitwise = _conftest.assert_channels_bitwise
import numpy as np
import pytest


from solweig_light.geometry.visibility import LazyDiffVisibility, PackedVisibility
from solweig_light.geometry.visibility_prepared import prepare_channels

BLOCKS = ((0, 256, 5), (0, 0, 5), (37, 37, 5), (3, 251, 5), (253, 256, 5),
          (0, 256, 1), (128, 253, 3))


def assert_demand_equal(shadow, vegetation, vegetation_building, diffuse,
                        start, stop, patches):
    expected = original_shortwave(shadow, vegetation, vegetation_building,
                                  diffuse, start, stop, patches)
    prepared = prepare_channels(shadow, vegetation, vegetation_building, diffuse)
    assert prepared is not None
    actual = prepared.decode(start, stop, patches)
    assert_channels_bitwise(expected, actual)
    recipe = recipe_shortwave(shadow, vegetation, vegetation_building,
                              diffuse, start, stop, patches)
    assert_channels_bitwise(expected, recipe)


def assert_longwave_equal(shadow, vegetation, vegetation_building, start, stop, patches):
    expected = original_longwave(shadow, vegetation, vegetation_building, start, stop, patches)
    prepared = prepare_channels(shadow, vegetation, vegetation_building)
    assert prepared is not None
    assert_channels_bitwise(expected, prepared.decode(start, stop, patches))
    assert_channels_bitwise(expected, recipe_longwave(shadow, vegetation,
                                                      vegetation_building, start, stop, patches))


@pytest.mark.parametrize('rows_cols,patches', [(16, 1), (16, 5), (16, 153), (64, 5), (96, 153), (128, 5)])
@pytest.mark.parametrize('kinds', [('binary',), ('ternary',), ('raw',),
                                   ('binary', 'ternary'), ('ternary', 'raw'),
                                   ('signed_zero',), ('nonfinite',)])
def test_shortwave_matches_original_bitwise(rows_cols, patches, kinds):
    rng = np.random.default_rng(rows_cols*1000 + patches)
    rows = cols = rows_cols
    shadow = packed(rng, rows, cols, patches, kinds)
    vegetation = packed(rng, rows, cols, patches, kinds[::-1])
    vegetation_building = packed(rng, rows, cols, patches, ('binary', 'raw'))
    diffuse = LazyDiffVisibility(shadow, vegetation)
    pixels = rows*cols
    for start, stop, demanded in BLOCKS:
        stop = min(stop, pixels)
        if start > stop:
            continue
        assert_demand_equal(shadow, vegetation, vegetation_building, diffuse,
                            start, stop, min(demanded, patches))


def test_shortwave_matches_original_with_mapped_owners(tmp_path):
    rng = np.random.default_rng(11)
    rows = cols = 64
    channels = [packed(rng, rows, cols, 5, ('binary', 'ternary', 'raw')) for _ in range(3)]
    owners = [mapped_roundtrip(tmp_path, channel, f'channel{index}')
              for index, channel in enumerate(channels)]
    try:
        diffuse = LazyDiffVisibility(owners[0], owners[1])
        for start, stop, demanded in ((0, 4096, 5), (7, 4089, 5), (0, 0, 5), (500, 500, 3)):
            assert_demand_equal(owners[0], owners[1], owners[2], diffuse,
                                start, stop, demanded)
            assert_longwave_equal(owners[0], owners[1], owners[2], start, stop, demanded)
    finally:
        for owner in owners:
            owner.close()


def test_decode_reproduces_the_dense_source_bits():
    """Conservation end-to-end: from_dense planes reappear bit-exact."""
    rng = np.random.default_rng(12)
    rows = cols = 32
    patches = 4
    dense = (cube(rng, rows, cols, patches, ('binary', 'ternary', 'raw', 'nonfinite')),
             cube(rng, rows, cols, patches, ('ternary', 'signed_zero')),
             cube(rng, rows, cols, patches, ('raw',)))
    channels = tuple(PackedVisibility.from_dense(source) for source in dense)
    diffuse = LazyDiffVisibility(channels[0], channels[1])
    pixels = rows*cols
    prepared = prepare_channels(*channels, diffuse)
    results = prepared.decode(0, pixels, patches)
    for result, source in zip(results, dense):
        expected = np.stack([source[:, :, patch].reshape(-1) for patch in range(patches)], axis=1)
        assert np.array_equal(result.view(np.uint32), expected.view(np.uint32))


def test_direct_packed_diffuse_channel_matches():
    rng = np.random.default_rng(13)
    channels = [packed(rng, 16, 16, 5, kind) for kind in
                (('binary', 'ternary'), ('binary',), ('ternary', 'raw'), ('raw',))]
    assert_demand_equal(*channels, 0, 256, 5)
    assert_demand_equal(*channels, 11, 200, 3)


def test_independent_lazy_diffuse_pair_matches():
    rng = np.random.default_rng(14)
    shadow = packed(rng, 16, 16, 5, ('binary', 'ternary'))
    vegetation = packed(rng, 16, 16, 5, ('ternary',))
    vegetation_building = packed(rng, 16, 16, 5, ('binary',))
    diffuse_shadow = packed(rng, 16, 16, 5, ('raw',))
    diffuse_vegetation = packed(rng, 16, 16, 5, ('nonfinite',))
    diffuse = LazyDiffVisibility(diffuse_shadow, diffuse_vegetation)
    prepared = prepare_channels(shadow, vegetation, vegetation_building, diffuse)
    assert prepared.diff_kind == 3
    assert_demand_equal(shadow, vegetation, vegetation_building, diffuse, 0, 256, 5)
    assert_demand_equal(shadow, vegetation, vegetation_building, diffuse, 5, 129, 2)


def test_subclass_leaves_follow_decode_block_admission():
    rng = np.random.default_rng(15)
    base = packed(rng, 16, 16, 3, ('binary',))
    other = packed(rng, 16, 16, 3, ('ternary',))

    class PackedSubclass(PackedVisibility):
        pass
    class LazySubclass(LazyDiffVisibility):
        pass

    shadow = PackedSubclass(base.shape, base._patches)
    vegetation = PackedVisibility.from_dense(np.ones((16, 16, 3), np.float32))
    vegetation_building = other
    # Packed leaf subclass: decode_block admits it natively; so does prepare.
    prepared = prepare_channels(shadow, vegetation, vegetation_building)
    assert prepared is not None
    # Lazy subclass over packed leaves: reuse rejected, native lazy pair kept.
    diffuse = LazySubclass(shadow, vegetation)
    prepared = prepare_channels(shadow, vegetation, vegetation_building, diffuse)
    assert prepared is not None and prepared.diff_kind == 3
    assert_demand_equal(shadow, vegetation, vegetation_building, diffuse, 0, 256, 3)


@pytest.mark.parametrize('with_buffers', [False, True])
def test_buffer_contract_returns_identical_bits(with_buffers):
    rng = np.random.default_rng(16)
    channels = [packed(rng, 16, 16, 5, ('binary', 'ternary')) for _ in range(3)]
    diffuse = LazyDiffVisibility(channels[0], channels[1])
    prepared = prepare_channels(*channels, diffuse)
    expected = original_shortwave(*channels, diffuse, 9, 200, 4)
    buffers = [np.empty((191, 4), dtype=np.float32) for _ in range(4)] if with_buffers else None
    actual = prepared.decode(9, 200, 4, buffers)
    assert_channels_bitwise(expected, actual)
    if with_buffers:
        assert all(one is two for one, two in zip(actual, buffers))


def test_empty_channel_shape_decodes_to_empty():
    empty = PackedVisibility.from_dense(np.zeros((0, 0, 0), np.float32))
    for runner in (original_shortwave, recipe_shortwave):
        result = runner(empty, empty, empty, LazyDiffVisibility(empty, empty), 0, 0, 0)
        assert all(channel.shape == (0, 0) for channel in result)
    prepared = prepare_channels(empty, empty, empty, LazyDiffVisibility(empty, empty))
    assert prepared is not None
    result = prepared.decode(0, 0, 0)
    assert all(channel.shape == (0, 0) for channel in result)
    assert_channels_bitwise(result, result)  # trivial; shape is the assertion


def test_longwave_matches_original_bitwise():
    rng = np.random.default_rng(17)
    channels = [packed(rng, 16, 16, 5, kinds) for kinds in
                (('binary', 'ternary'), ('ternary',), ('raw', 'binary'))]
    for start, stop, demanded in ((0, 256, 5), (13, 250, 3), (0, 0, 5), (200, 200, 5)):
        assert_longwave_equal(*channels, start, stop, min(demanded, 5))


def test_longwave_matches_original_with_mapped_owners(tmp_path):
    rng = np.random.default_rng(18)
    channels = [packed(rng, 32, 32, 7, ('binary', 'ternary')) for _ in range(3)]
    owners = [mapped_roundtrip(tmp_path, channel, f'lw{index}') for index, channel in enumerate(channels)]
    try:
        assert_longwave_equal(*owners, 0, 1024, 7)
        assert_longwave_equal(*owners, 31, 1000, 5)
    finally:
        for owner in owners:
            owner.close()
