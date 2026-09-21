"""Complete fallback: unadmitted demand yields None and the original path runs.

The fallback IS the original code path, so equality is by construction; these
tests pin the admission boundary (never raise, never partially optimize) and
verify the recipe shape (prepared-then-original) reproduces the accepted
results bitwise on every unadmitted demand.
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
original_shortwave = _conftest.original_shortwave
outcome = _conftest.outcome
packed = _conftest.packed
recipe_longwave = _conftest.recipe_longwave
recipe_shortwave = _conftest.recipe_shortwave
import numpy as np
import pytest


from solweig_light.geometry.visibility import LazyDiffVisibility, PackedVisibility
from solweig_light.geometry.visibility_prepared import (decode_longwave_block,
                                                        decode_shortwave_block,
                                                        prepare_channels)


def dense(rows=16, cols=16, patches=3):
    rng = np.random.default_rng(rows*100 + cols)
    return rng.integers(0, 3, (rows, cols, patches)).astype(np.float32)


def packed_channels(patches=3):
    rng = np.random.default_rng(patches)
    return [packed(rng, 16, 16, patches, ('binary', 'ternary')) for _ in range(3)]


class DuckChannel:
    """Duck type with the decode_pixels surface; never admitted."""
    def __init__(self, array):
        self._array = array
        self.shape = array.shape
        self.dtype = np.dtype(np.float32)

    def decode_pixels(self, patch, start, stop):
        return self._array[:, :, patch].reshape(-1)[start:stop]


@pytest.mark.parametrize('name', ['duck_diffuse', 'dense_diffuse', 'lazy_base',
                                  'lazy_unpacked_leaves', 'lazy_subclass_unpacked',
                                  'int_channel', 'independent_lazy_mixed'])
def test_unadmitted_demands_return_none(name):
    channels = packed_channels()
    base_lazy = LazyDiffVisibility(channels[0], channels[1])

    class LazySubclass(LazyDiffVisibility):
        pass

    demands = {
        'duck_diffuse': (channels[0], channels[1], channels[2], DuckChannel(dense())),
        'dense_diffuse': (channels[0], channels[1], channels[2], dense()),
        'lazy_base': (base_lazy, channels[1], channels[2], channels[0]),
        'lazy_unpacked_leaves': (channels[0], channels[1], channels[2],
                                 LazyDiffVisibility(dense(), dense())),
        'lazy_subclass_unpacked': (channels[0], channels[1], channels[2],
                                   LazySubclass(dense(), dense())),
        'int_channel': (channels[0], channels[1], channels[2], 3),
        'independent_lazy_mixed': (channels[0], channels[1], channels[2],
                                   LazyDiffVisibility(channels[0], dense())),
    }
    shadow, vegetation, building, diffuse = demands[name]
    assert prepare_channels(shadow, vegetation, building, diffuse) is None
    assert decode_shortwave_block(shadow, vegetation, building, diffuse, 0, 16, 3) is None


def test_recipe_fallback_is_bitwise_original_for_duck_diffuse():
    channels = packed_channels()
    diffuse = DuckChannel(dense())
    expected = original_shortwave(*channels, diffuse, 2, 200, 3)
    actual = recipe_shortwave(*channels, diffuse, 2, 200, 3)
    for one, other in zip(expected, actual):
        assert np.array_equal(one.view(np.uint32), other.view(np.uint32))


def test_recipe_fallback_is_bitwise_original_for_unpacked_lazy():
    channels = packed_channels()
    diffuse = LazyDiffVisibility(dense(), dense())
    # Even the original path's own AttributeError on decode_pixels-less leaves
    # is preserved identically by the complete fallback.
    expected = outcome(original_shortwave, *channels, diffuse, 0, 256, 3)
    actual = outcome(recipe_shortwave, *channels, diffuse, 0, 256, 3)
    assert expected == actual
    assert expected[:3] == ('err', AttributeError,
                            "'numpy.ndarray' object has no attribute 'decode_pixels'")


def test_recipe_longwave_fallback_bitwise():
    channels = packed_channels()
    unpacked = dense(16, 16, 3)
    expected_from = recipe_longwave(channels[0], unpacked, channels[2], 0, 16, 3)
    import solweig_light.radiation.patch_radiation as patch_radiation
    expected = tuple(patch_radiation._block(channel, 0, 16, 3)
                     for channel in (channels[0], unpacked, channels[2]))
    for one, other in zip(expected, expected_from):
        assert np.array_equal(one.view(np.uint32), other.view(np.uint32))


def test_prepare_never_raises_on_garbage_demand():
    assert prepare_channels(None, None, None) is None
    assert prepare_channels(3, 'x', object()) is None
    assert decode_shortwave_block(3, 'x', object(), None, 0, 1, 1) is None
    assert decode_longwave_block(None, None, None, 0, 0, 0) is None


def test_buffer_contract_errors_are_new_api_errors():
    """Buffer misuse is a private-API programming error raised before locks;
    it has no original counterpart and never masks an original checkpoint."""
    channels = packed_channels()
    diffuse = LazyDiffVisibility(channels[0], channels[1])
    prepared = prepare_channels(*channels, diffuse)
    wrong_count = [np.empty((16, 3), np.float32)]
    with pytest.raises(ValueError, match='one buffer per demanded channel'):
        prepared.decode(0, 16, 3, wrong_count)
    wrong_shape = [np.empty((16, 3), np.float32) for _ in range(4)]
    with pytest.raises(ValueError, match='shape differs'):
        prepared.decode(0, 15, 3, wrong_shape)
    wrong_dtype = [np.empty((16, 3), np.float64) for _ in range(4)]
    with pytest.raises(ValueError, match='C-contiguous writeable float32'):
        prepared.decode(0, 16, 3, wrong_dtype)
    readonly = [np.empty((16, 3), np.float32) for _ in range(4)]
    for buffer in readonly:
        buffer.flags.writeable = False
    with pytest.raises(ValueError, match='C-contiguous writeable float32'):
        prepared.decode(0, 16, 3, readonly)


def test_admitted_packed_subclass_base_is_not_fallback():
    channels = packed_channels()

    class PackedSubclass(PackedVisibility):
        pass

    shadow = PackedSubclass(channels[0].shape, channels[0]._patches)
    prepared = prepare_channels(shadow, channels[1], channels[2])
    assert prepared is not None
