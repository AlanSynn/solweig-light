"""Gate: no hidden whole-payload copy and no full-cube allocation.

The Python side is measured with tracemalloc around prepare+decode; the only
numba-side allocation in the prepared path is the single exactly-sized uint32
scratch for the independent lazy pair (source-inspectable in _decode_channels
plus asserted here through the allocation budget of the fallback-free kinds).
Descriptors must be the accepted path's own cached borrow (tuple identity),
proving zero payload copies are shared rather than added.
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
mapped_roundtrip = _conftest.mapped_roundtrip
original_shortwave = _conftest.original_shortwave
packed = _conftest.packed
import gc
import tracemalloc

import numpy as np


from solweig_light.geometry.visibility import LazyDiffVisibility
from solweig_light.geometry.visibility_compiled import decode_block
from solweig_light.geometry.visibility_prepared import prepare_channels

BLOCK_ROWS = 64
# Numba dispatch wrappers, views, lists and the ExitStack cost a few KB of
# Python allocations per decode; every budget below adds this allowance and
# stays far below the smallest forbidden copy size.
OVERHEAD = 32768


def warm_decode(warm_demand, start, stop, patches):
    """Compile the kernels before a measurement window (compilation itself
    allocates hundreds of KB inside the process and is not under test)."""
    warm = prepare_channels(*warm_demand)
    warm.decode(start, stop, patches, [np.empty((stop-start, patches), dtype=np.float32)
                                       for _ in range(warm.channels)])


def large_demand(tmp_path):
    """128-square, 153-patch raw demand: a whole-payload copy would be ~10 MB."""
    rng = np.random.default_rng(64)
    channels = [packed(rng, 128, 128, 153, ('raw',)) for _ in range(3)]
    mapped = [mapped_roundtrip(tmp_path, channel, f'big{index}')
              for index, channel in enumerate(channels)]
    diffuse = LazyDiffVisibility(mapped[0], mapped[1])
    return mapped, diffuse


def test_descriptors_are_the_accepted_path_cached_borrow():
    rng = np.random.default_rng(65)
    channels = [packed(rng, 16, 16, 5, ('binary', 'ternary')) for _ in range(3)]
    prepared = prepare_channels(*channels)
    for slot, channel in zip(prepared.slots, channels):
        payloads, modes = slot.streams[0]
        # Tuple identity: the accepted decode_block path reads the very same
        # borrowed descriptor object; nothing was copied to prepare.
        assert slot.streams[0] is channel._block_descriptor
        assert len(payloads) == channel.shape[2]
        assert sum(view.nbytes for view in payloads) == channel.nbytes
        assert all(not view.flags.writeable for view in payloads)
    # decode_block on the same channel reuses the same cached descriptor.
    decode_block(channels[0], 0, 16, 5)
    assert channels[0]._block_descriptor is prepared.slots[0].streams[0]


def test_no_payload_copy_on_python_path(tmp_path):
    mapped, diffuse = large_demand(tmp_path)
    try:
        warm_decode((*mapped, diffuse), 0, BLOCK_ROWS, 153)
        buffers = [np.empty((BLOCK_ROWS, 153), dtype=np.float32) for _ in range(4)]
        tracemalloc.start()
        prepared = prepare_channels(*mapped, diffuse)
        results = prepared.decode(0, BLOCK_ROWS, 153, buffers)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        expected = original_shortwave(*mapped, diffuse, 0, BLOCK_ROWS, 153)
        for one, other in zip(expected, results):
            assert np.array_equal(one.view(np.uint32), other.view(np.uint32))
        # Any whole-payload borrow-to-flat copy would add ~10 MB here; the
        # Python side allocates no payload-sized object at all.
        assert peak < 1_000_000, peak
    finally:
        for owner in mapped:
            owner.close()


def test_reuse_diffuse_adds_no_decoded_shadow_copy(tmp_path):
    """The accepted reuse copies the decoded shadow; the prepared path must not."""
    rng = np.random.default_rng(66)
    rows = cols = 128
    mapped = [mapped_roundtrip(tmp_path, packed(rng, rows, cols, 153, ('binary', 'ternary')),
                               f'reuse{index}') for index in range(2)]
    building = mapped_roundtrip(tmp_path, packed(rng, rows, cols, 153, ('binary',)), 'reuse2')
    diffuse = LazyDiffVisibility(mapped[0], mapped[1])
    try:
        warm_decode((*mapped, building, diffuse), 0, BLOCK_ROWS, 153)
        buffers = [np.empty((BLOCK_ROWS, 153), dtype=np.float32) for _ in range(4)]
        tracemalloc.start()
        prepared = prepare_channels(*mapped, building, diffuse)
        results = prepared.decode(0, BLOCK_ROWS, 153, buffers)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        expected = original_shortwave(*mapped, building, diffuse, 0, BLOCK_ROWS, 153)
        for one, other in zip(expected, results):
            assert np.array_equal(one.view(np.uint32), other.view(np.uint32))
        # A decoded-shadow copy would be rows*patches*4 = 393216 bytes here;
        # the measured warm peak is a few KB of dispatch overhead only.
        assert peak < BLOCK_ROWS*153*4, peak
    finally:
        for owner in mapped + [building]:
            owner.close()


def test_lazy_pair_scratch_is_exactly_one_block(tmp_path):
    rng = np.random.default_rng(67)
    mapped = [mapped_roundtrip(tmp_path, packed(rng, 64, 64, 5, ('raw',)), f'pair{index}')
              for index in range(2)]
    building = packed(np.random.default_rng(68), 64, 64, 5, ('binary',))
    diffuse = LazyDiffVisibility(
        packed(np.random.default_rng(69), 64, 64, 5, ('nonfinite',)),
        packed(np.random.default_rng(70), 64, 64, 5, ('raw',)))
    try:
        warm_decode((*mapped, building, diffuse), 0, BLOCK_ROWS, 5)
        prepared = prepare_channels(*mapped, building, diffuse)
        assert prepared.diff_kind == 3
        buffers = [np.empty((BLOCK_ROWS, 5), dtype=np.float32) for _ in range(4)]
        tracemalloc.start()
        results = prepared.decode(0, BLOCK_ROWS, 5, buffers)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        expected = original_shortwave(*mapped, building, diffuse, 0, BLOCK_ROWS, 5)
        for one, other in zip(expected, results):
            assert np.array_equal(one.view(np.uint32), other.view(np.uint32))
        # The documented scratch is one (rows, patches) uint32 block plus the
        # fixed dispatch overhead; any payload copy (>= 81920 bytes/channel)
        # would exceed this budget.
        assert peak < BLOCK_ROWS*5*4 + OVERHEAD, peak
    finally:
        for owner in mapped:
            owner.close()


def test_exactly_sized_outputs_without_buffers():
    rng = np.random.default_rng(71)
    channels = [packed(rng, 16, 16, 5, ('binary', 'ternary')) for _ in range(3)]
    diffuse = LazyDiffVisibility(channels[0], channels[1])
    prepared = prepare_channels(*channels, diffuse)
    gc.collect()
    tracemalloc.start()
    results = prepared.decode(4, 100, 5)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    for result in results:
        assert result.shape == (96, 5)
        assert result.dtype == np.dtype(np.float32)
        assert result.nbytes == 96*5*4
    # Four exactly-sized outputs plus small descriptor/modes objects only.
    assert peak < 4*96*5*4 + 65536, peak


def test_kernel_has_no_payload_sized_allocation_source():
    """Structural guard: the only np.empty inside the combined kernel is the
    documented lazy-pair scratch sizing path (and here it is caller-visible)."""
    import inspect
    from solweig_light.geometry import visibility_prepared
    source = inspect.getsource(visibility_prepared._decode_channels)
    assert 'np.empty' not in source
    assert 'np.zeros' not in source and 'np.copy' not in source and 'tobytes' not in source
    decode_source = inspect.getsource(visibility_prepared._decode_into)
    assert 'np.empty' not in decode_source
