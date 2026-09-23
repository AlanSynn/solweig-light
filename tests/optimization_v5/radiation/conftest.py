"""Shared builders for the P01 fused ordered decode+accumulate differential tests."""
import contextlib
import os

import numba
import numpy as np
import pytest

from solweig_light.geometry.visibility import LazyDiffVisibility, PackedVisibility, _EncodedPatch

# The fused route is opt-in in production; this suite exists to exercise it.
os.environ.setdefault('SOLWEIG_LIGHT_FUSED_RAD', '1')

PATCHES = 153


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


def sw_coefficients(rng, patches):
    """Shortwave kernel coefficients with production shapes."""
    return dict(
        lum=rng.random(patches).astype(np.float32),
        solid=rng.random(patches).astype(np.float32)+.01,
        cosine=rng.random(patches).astype(np.float32),
        directions=rng.random((patches, 4)).astype(np.float32),
        diff_gate=rng.random((patches, 4)) < .5,
        ref_gate=rng.random((patches, 4)) < .5,
        box_gate=rng.random(patches) < .5,
        surface_sun=np.float32(.37),
        surface_sh=np.float32(.11),
    )


def lw_coefficients(rng, patches, pixels):
    """Longwave kernel coefficients; Lup varies per pixel."""
    return dict(
        solid=rng.random(patches).astype(np.float32)+.01,
        sine=rng.random(patches).astype(np.float32),
        cosine=rng.random(patches).astype(np.float32),
        directions=rng.random((patches, 4)).astype(np.float32),
        gate=rng.random((patches, 4)) < .5,
        solar_gate=rng.random(patches) < .7,
        sky_down=rng.random(patches).astype(np.float32),
        sky_side=rng.random(patches).astype(np.float32),
        steradian=rng.random(patches).astype(np.float32),
        sun_surface=np.float32(.41),
        shade_surface=np.float32(.23),
        lup=rng.random(pixels).astype(np.float32),
        factor=np.float32(.05),
    )


def classes(rng, pixels, patches):
    return (rng.integers(0, 2, (pixels, patches)).astype(np.bool_),
            rng.integers(0, 2, (pixels, patches)).astype(np.bool_))


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


def kside_arguments(rng, rows, cols, patches, packed_inputs):
    """Full Kside_veg_v2022a keyword set for the compiled admission profile."""
    lv = rng.random((patches, 3)).astype(np.float32)
    lv[:, 0] = rng.integers(5, 90, patches)
    lv[:, 1] = rng.integers(0, 360, patches)
    def maybe(channel_dense):
        return PackedVisibility.from_dense(channel_dense) if packed_inputs else channel_dense
    arguments = dict(
        radI=np.float64(480.0), radD=np.float64(130.0), radG=np.float64(0.0),
        shadow=rng.integers(0, 2, (rows, cols)).astype(np.float32),
        svfS=.5, svfW=.5, svfN=.5, svfE=.5, svfEveg=.5, svfSveg=.5, svfWveg=.5, svfNveg=.5,
        azimuth=np.float64(123.0), altitude=np.float64(37.0), psi=np.float64(7.0),
        t=np.float64(0.0), albedo=np.float64(.2), F_sh=.8,
        KupE=rng.random((rows, cols)).astype(np.float32),
        KupS=rng.random((rows, cols)).astype(np.float32),
        KupW=rng.random((rows, cols)).astype(np.float32),
        KupN=rng.random((rows, cols)).astype(np.float32),
        cyl=1, lv=lv, anisotropic_diffuse=1,
        diffsh=maybe(cube(rng, rows, cols, patches, ('binary', 'ternary'))),
        rows=rows, cols=cols,
        asvf=rng.random((rows, cols)).astype(np.float32),
        shmat=maybe(cube(rng, rows, cols, patches, ('binary', 'ternary'))),
        vegshmat=maybe(cube(rng, rows, cols, patches, ('binary',))),
        vbshvegshmat=maybe(cube(rng, rows, cols, patches, ('ternary', 'binary'))),
    )
    return arguments


def define_arguments(rng, rows, cols, patches, packed_inputs):
    """Full define_patch_characteristics keyword set for the compiled profile."""
    def maybe(channel_dense):
        return PackedVisibility.from_dense(channel_dense) if packed_inputs else channel_dense
    return dict(
        solar_altitude=np.array(37.0, dtype=np.float32),
        solar_azimuth=np.array(201.0, dtype=np.float32),
        patch_altitude=rng.integers(5, 90, patches).astype(np.float32),
        patch_azimuth=rng.integers(0, 360, patches).astype(np.float32),
        steradian=rng.random(patches).astype(np.float32),
        asvf=rng.random((rows, cols)).astype(np.float32),
        shmat=maybe(cube(rng, rows, cols, patches, ('binary', 'ternary'))),
        vegshmat=maybe(cube(rng, rows, cols, patches, ('binary',))),
        vbshvegshmat=maybe(cube(rng, rows, cols, patches, ('ternary',))),
        Lsky_down=rng.random((patches, 3)).astype(np.float32),
        Lsky_side=rng.random((patches, 3)).astype(np.float32),
        Lsky=rng.random((patches, 3)).astype(np.float32),
        Lup=rng.random((rows, cols)).astype(np.float32),
        Ta=np.float32(297.0), Tgwall=np.float32(299.0), ewall=np.float32(.9),
        rows=rows, cols=cols,
    )


def lcyl_arguments(rng, rows, cols, patches, packed_inputs):
    """Full Lcyl_v2022a keyword set for the compiled profile."""
    values = define_arguments(rng, rows, cols, patches, packed_inputs)
    table = np.column_stack((values['patch_altitude'], values['patch_azimuth'],
                             np.zeros(patches, dtype=np.float32)))
    return dict(
        esky=np.float32(.85), sky_patches=table,
        Ta=values['Ta'], Tgwall=values['Tgwall'], ewall=values['ewall'],
        Lup=values['Lup'],
        shmat=values['shmat'], vegshmat=values['vegshmat'], vbshvegshmat=values['vbshvegshmat'],
        solar_altitude=values['solar_altitude'], solar_azimuth=values['solar_azimuth'],
        rows=rows, cols=cols, asvf=values['asvf'],
    )


@contextlib.contextmanager
def threads(count):
    """Bound the numba thread pool for one test; policy cap is 2."""
    previous = numba.get_num_threads()
    numba.set_num_threads(min(count, previous))
    try:
        yield
    finally:
        numba.set_num_threads(previous)


def bitwise(left, right):
    """Exact uint32-view equality; compares NaN payloads and signed zeros."""
    return np.array_equal(np.asarray(left).view(np.uint32), np.asarray(right).view(np.uint32))


def assert_fields_bitwise(left, right):
    assert len(left) == len(right)
    for index, (one, other) in enumerate(zip(left, right)):
        assert bitwise(one, other), f'field {index} differs'


@pytest.fixture(scope='session')
def patch_count():
    return PATCHES
