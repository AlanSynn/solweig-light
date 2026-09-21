"""Shared builders for the C6-21 cylinder-longwave primary-output reduction tests.

Every comparison is bitwise (uint32 view, NaN/sign-aware) against the untouched
full kernels and the untouched public wrapper. All comparisons use the
repository math profile: numba njit(cache=True, fastmath=False), no new math.
"""
import numpy as np
import pytest

from solweig_light.geometry.shadows import create_patches
from solweig_light.geometry.visibility import PackedVisibility
from solweig_light.radiation import engine as e


def bitwise_equal(a, b):
    """Exact float32 equality: same bits, NaN payload and sign included."""
    a, b = np.asarray(a, dtype=np.float32), np.asarray(b, dtype=np.float32)
    if a.shape != b.shape:
        return False
    return np.array_equal(a.view(np.uint32), b.view(np.uint32))


def lcyl_patches(patch_option=2):
    """Real engine patch table (n,3): altitude, azimuth, patch emissivity."""
    skyvaultalt, skyvaultazi, _, _, _, _, _ = create_patches(patch_option)
    patch_emissivities = e._zeros(skyvaultalt.shape[0])
    return np.concatenate((np.swapaxes(np.atleast_2d(skyvaultalt), 0, 1),
                           np.swapaxes(np.atleast_2d(skyvaultazi), 0, 1),
                           np.swapaxes(np.atleast_2d(patch_emissivities), 0, 1)), axis=1)


def lcyl_arguments(rng, rows=16, cols=16, patch_option=2, **overrides):
    """Float32 engine-profile argument bundle for Lcyl_v2022a, with overrides."""
    table = overrides.pop('sky_patches', lcyl_patches(patch_option))
    patches = table.shape[0]
    args = dict(
        esky=np.array(0.85, dtype=np.float32),
        sky_patches=table,
        Ta=np.array(21.0, dtype=np.float32),
        Tgwall=np.array(15.0, dtype=np.float32),
        ewall=np.array(0.9, dtype=np.float32),
        Lup=(rng.random(rows*cols).reshape(rows, cols)*450+350).astype(np.float32),
        shmat=(rng.random((rows, cols, patches)) > .3).astype(np.float32),
        vegshmat=(rng.random((rows, cols, patches)) > .5).astype(np.float32),
        vbshvegshmat=(rng.random((rows, cols, patches)) > .6).astype(np.float32),
        solar_altitude=np.array(35.0, dtype=np.float32),
        solar_azimuth=np.array(180.0, dtype=np.float32),
        rows=rows,
        cols=cols,
        asvf=np.full((rows, cols), .6, dtype=np.float32),
    )
    args.update(overrides)
    return args


def lw_blocks(rng, pixels, patches):
    """Dense longwave visibility blocks with adversarial float32 payloads."""
    def block(kinds):
        planes = []
        for patch in range(patches):
            kind = kinds[patch % len(kinds)]
            if kind == 'binary':
                plane = rng.integers(0, 2, pixels).astype(np.float32)
            elif kind == 'ternary':
                plane = rng.integers(0, 3, pixels).astype(np.float32)
            elif kind == 'raw':
                bits = rng.integers(0, 2**32, pixels, dtype=np.uint64).astype(np.uint32)
                bits[0] = 0x40600000  # 3.5f: never a codebook pattern, so raw mode
                plane = bits.view(np.float32)
            elif kind == 'nonfinite':
                plane = rng.integers(0, 2, pixels).astype(np.float32)
                plane[1::11] = np.float32('nan')
                plane[2::11] = np.float32('inf')
                plane[3::11] = np.float32('-inf')
                plane[5::11] = np.float32(-0.0)
            elif kind == 'signed_zero':
                plane = rng.integers(0, 2, pixels).astype(np.float32)
                plane[1::7] = np.float32(-0.0)
            else:
                raise ValueError(kind)
            planes.append(plane)
        return np.stack(planes, axis=1).astype(np.float32)
    return block(('binary', 'ternary')), block(('ternary', 'raw', 'binary')), block(('raw', 'signed_zero', 'nonfinite'))


def lw_coefficients(rng, patches, pixels):
    """Longwave kernel coefficients with production dtypes, incl. nonfinite."""
    solid = rng.random(patches).astype(np.float32)+.01
    sky_down = rng.random(patches).astype(np.float32)
    sky_down[1] = np.float32('nan')
    sky_side = rng.random(patches).astype(np.float32)
    sky_side[2] = np.float32('inf')
    sun_surface = rng.random(()).astype(np.float32)
    shade_surface = rng.random(()).astype(np.float32)
    lup = rng.random(pixels).astype(np.float32)
    lup[3::17] = np.float32('nan')
    lup[5::23] = np.float32('inf')
    lup[7::29] = np.float32(-0.0)
    return dict(
        solid=solid,
        sine=rng.random(patches).astype(np.float32),
        cosine=rng.random(patches).astype(np.float32),
        directions=rng.random((patches, 4)).astype(np.float32),
        gate=rng.random((patches, 4)) < .5,
        solar_gate=rng.random(patches) < .7,
        sky_down=sky_down,
        sky_side=sky_side,
        sun_surface=sun_surface,
        shade_surface=shade_surface,
        lup=lup,
        factor=rng.random(()).astype(np.float32),
    )


def packed(rng, rows, cols, patches, kinds):
    """Packed visibility channel over an adversarial dense cube."""
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
            bits[0] = 0x40600000
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
    return PackedVisibility.from_dense(np.stack(planes, axis=2))


@pytest.fixture
def rng():
    """Deterministic per-test generator (no repo-wide fixture exists)."""
    return np.random.default_rng(20260921)


@pytest.fixture
def demand_scope_factory():
    from solweig_light.radiation.cylinder_longwave import demand_scope
    return demand_scope
