"""Shared builders for the C6-50 prepared multi-channel decoder tests (L0/L1).

Fixtures are the production codec itself: dense planes go through
``VisibilityBuilder``/``from_dense`` (the pipeline encoder) or the real
native save/open roundtrip; corrupted payloads are built directly through
the frozen ``_EncodedPatch`` record exactly as tests/unit does.
"""
import contextlib
import os
import sys
from pathlib import Path

os.environ.setdefault('NUMBA_NUM_THREADS', '2')  # census cap: at most two native threads

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[3]
SRC = REPO / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from solweig_light.geometry.visibility import LazyDiffVisibility, PackedVisibility, _EncodedPatch  # noqa: E402
from solweig_light.geometry.visibility_native import open_native_visibility, save_native_visibility  # noqa: E402


def cube(rng, rows, cols, patches, kinds):
    """Dense float32 cube whose per-patch content forces the requested mode."""
    planes = []
    for patch in range(patches):
        kind = kinds[patch % len(kinds)]
        pixels = rows*cols
        if kind == 'binary':
            plane = rng.integers(0, 2, pixels).astype(np.float32)
        elif kind == 'ternary':
            plane = rng.integers(0, 3, pixels).astype(np.float32)
        elif kind == 'raw':
            bits = rng.integers(0, 2**32, pixels, dtype=np.uint64).astype(np.uint32)
            bits[0] = 0x40600000  # 3.5f: never a codebook pattern, so the mode is raw
            plane = bits.view(np.float32)
        elif kind == 'signed_zero':
            plane = rng.integers(0, 2, pixels).astype(np.float32)
            plane[1::7] = np.float32(-0.0)
        elif kind == 'nonfinite':
            plane = rng.integers(0, 2, pixels).astype(np.float32)
            plane[1::11] = np.float32('nan')
            plane[2::11] = np.float32('inf')
            plane[3::11] = np.float32('-inf')
            plane[5::11] = np.float32(-0.0)
        else:
            raise ValueError(kind)
        planes.append(plane.reshape(rows, cols))
    return np.stack(planes, axis=2)


def packed(rng, rows, cols, patches, kinds):
    return PackedVisibility.from_dense(cube(rng, rows, cols, patches, kinds))


def reserved_ternary(rows, cols, patches, reserved_pixels):
    """Packed ternary channel holding reserved code 3 at the requested pixels."""
    pixels = rows*cols
    codes = np.arange(pixels, dtype=np.uint8) % 3
    codes[reserved_pixels] = 3
    padded = np.zeros((codes.size+3)//4*4, dtype=np.uint8)
    padded[:codes.size] = codes
    packed_bits = padded[0::4] | (padded[1::4] << 2) | (padded[2::4] << 4) | (padded[3::4] << 6)
    payload = tuple(_EncodedPatch('ternary', bytes(packed_bits)) for _ in range(patches))
    return PackedVisibility((rows, cols, patches), payload)


def mapped_roundtrip(tmp_path, channel, name='channel'):
    """Real production storage roundtrip: save_native + open_native."""
    path = tmp_path / f'{name}.json'
    save_native_visibility(path, channel)
    return open_native_visibility(path)


@pytest.fixture(autouse=True)
def _prepared_route_on(request):
    """Arm the opt-in prepared route for this suite.

    C6-81 gated ``prepare_channels`` behind SOLWEIG_LIGHT_PREPARED_VIS=1
    (default OFF after the C6-80 measured regression). The decoder suite
    validates the prepared route itself, so every test runs with the
    variable set except the default-off pin, which removes it explicitly.
    """
    if request.node.get_closest_marker('prepared_default_off') is not None:
        yield
        return
    monkey = pytest.MonkeyPatch()
    monkey.setenv('SOLWEIG_LIGHT_PREPARED_VIS', '1')
    try:
        yield
    finally:
        monkey.undo()


@contextlib.contextmanager
def retained_route():
    """Pin the fused route OFF for the duration of one test.

    The v5 fused suite sets SOLWEIG_LIGHT_FUSED_RAD=1 process-wide at import;
    these tests validate the default retained route, so the variable is
    function-scoped and restored afterwards.
    """
    import pytest
    monkey = pytest.MonkeyPatch()
    monkey.setenv('SOLWEIG_LIGHT_FUSED_RAD', '0')
    try:
        yield
    finally:
        monkey.undo()


def bitwise(left, right):
    """Exact uint32-view equality; compares NaN payloads and signed zeros."""
    return np.array_equal(np.asarray(left).view(np.uint32), np.asarray(right).view(np.uint32))


def assert_channels_bitwise(left, right):
    assert len(left) == len(right)
    for index, (one, other) in enumerate(zip(left, right)):
        assert bitwise(one, other), f'channel {index} differs bitwise'


def outcome(call, *args, **kwargs):
    """Run one decode demand; return ('ok', outputs) or ('err', type, message)."""
    try:
        with np.errstate(all='ignore'):
            return ('ok', call(*args, **kwargs))
    except Exception as error:  # noqa: BLE001 - the comparison target is the error itself
        return ('err', type(error), str(error))


def original_shortwave(shadow, vegetation, vegetation_building, diffuse, start, stop, patches):
    """The unchanged accepted consumer sequence (retained route)."""
    import solweig_light.radiation.patch_radiation as patch_radiation
    return patch_radiation._shortwave_visibility_blocks(
        shadow, vegetation, vegetation_building, diffuse, start, stop, patches)


def original_longwave(shadow, vegetation, vegetation_building, start, stop, patches):
    """The unchanged accepted longwave demand (define_patch_characteristics' triple)."""
    import solweig_light.radiation.patch_radiation as patch_radiation
    return tuple(patch_radiation._block(channel, start, stop, patches)
                 for channel in (shadow, vegetation, vegetation_building))


def recipe_shortwave(shadow, vegetation, vegetation_building, diffuse, start, stop, patches):
    """The integration recipe shape: prepared first, complete original fallback."""
    from solweig_light.geometry.visibility_prepared import decode_shortwave_block
    prepared = decode_shortwave_block(
        shadow, vegetation, vegetation_building, diffuse, start, stop, patches)
    if prepared is not None:
        return prepared
    return original_shortwave(shadow, vegetation, vegetation_building, diffuse, start, stop, patches)


def recipe_longwave(shadow, vegetation, vegetation_building, start, stop, patches):
    from solweig_light.geometry.visibility_prepared import decode_longwave_block
    prepared = decode_longwave_block(shadow, vegetation, vegetation_building,
                                     start, stop, patches)
    if prepared is not None:
        return prepared
    return original_longwave(shadow, vegetation, vegetation_building, start, stop, patches)


@pytest.fixture(scope='session')
def three_channel_demand(tmp_path_factory):
    """A plain packed (shadow, vegetation, building) triple plus dense sources."""
    rng = np.random.default_rng(50)
    rows = cols = 16
    dense = (cube(rng, rows, cols, 5, ('binary', 'ternary')),
             cube(rng, rows, cols, 5, ('binary',)),
             cube(rng, rows, cols, 5, ('ternary', 'raw')))
    channels = tuple(PackedVisibility.from_dense(source) for source in dense)
    return dense, channels
