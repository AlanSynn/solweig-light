"""Shared builders for the R04+G06 exact patch-classification table tests.

Every parity gate is bitwise (uint32 view, NaN-payload/sign-aware) against
the retained ungated classification route: the per-patch scalar coefficient
loop plus the per-block NumPy tan/atan sequence in ``patch_radiation._classes``.
Real-motif inputs use the engine patch vaults from ``create_patches`` and the
admitted float32 wrapper profile; a crafted vault with repeated azimuths,
signed-zero and NaN states exercises the exact source-state classes.
"""
import os

import numpy as np
import pytest

from solweig_light.geometry.shadows import create_patches
from solweig_light.radiation import engine as e, patch_radiation as p

GATE_ENV = 'SOLWEIG_LIGHT_PATCH_CLASS_TABLES'

FIELD_NAMES = ('Keast', 'Ksouth', 'Kwest', 'Knorth', 'KsideI', 'KsideD', 'Kside')


def bitwise(a, b):
    """Exact float32 equality: same bits, NaN payload and sign included."""
    a, b = np.asarray(a), np.asarray(b)
    if a.dtype != b.dtype or a.shape != b.shape:
        return False
    view = np.uint32 if a.dtype == np.float32 else (np.uint64 if a.dtype == np.float64 else None)
    if view is None:
        return np.array_equal(a, b)
    return np.array_equal(a.view(view), b.view(view))


def assert_fields_bitwise(actual, expected, names, context):
    for name, got, want in zip(names, actual, expected):
        got, want = np.asarray(got), np.asarray(want)
        assert got.dtype == want.dtype, f'{context}/{name}: dtype {got.dtype} vs {want.dtype}'
        assert got.shape == want.shape, f'{context}/{name}: shape {got.shape} vs {want.shape}'
        assert bitwise(got, want), f'{context}/{name}: bits differ'


def real_vault(option=2):
    """Real engine sky vault (n,3): altitude, azimuth, zero luminance."""
    skyvaultalt, skyvaultazi, *_ = create_patches(option)
    altitude = np.swapaxes(np.atleast_2d(skyvaultalt), 0, 1)
    azimuth = np.swapaxes(np.atleast_2d(skyvaultazi), 0, 1)
    table = np.concatenate((altitude, azimuth,
                            np.zeros((altitude.size, 1), np.float32)), axis=1)
    return table.astype(np.float32)


def crafted_vault():
    """Nine-patch vault with repeated azimuths, signed zeros and a NaN state."""
    table = np.array([
        [10.0, 45.0], [25.0, 45.0], [40.0, 45.0],
        [10.0, 135.0], [25.0, 135.0], [40.0, 135.0],
        [55.0, -0.0], [70.0, 0.0], [85.0, np.nan],
    ], dtype=np.float32)
    return np.column_stack((table, np.zeros(table.shape[0], np.float32)))


def asvf_field(rng, rows, cols, mode='realistic'):
    """Admitted float32 asvf rasters, including the tan32 domain boundary."""
    if mode == 'realistic':
        return rng.uniform(0.05, 1.5, (rows, cols)).astype(np.float32)
    if mode == 'adversarial':
        field = rng.uniform(0.05, 1.5, (rows, cols)).astype(np.float32)
        field.reshape(-1)[0::13] = np.float32(0.0)
        field.reshape(-1)[1::13] = np.float32(-0.0)
        field.reshape(-1)[2::13] = np.float32(200.0)   # outside the SLEEF tan domain
        field.reshape(-1)[3::13] = np.float32(-300.0)  # outside the SLEEF tan domain
        field.reshape(-1)[4::13] = np.float32('nan')
        field.reshape(-1)[5::13] = np.float32('inf')
        field.reshape(-1)[6::13] = np.float32(-np.inf)
        return field
    raise ValueError(mode)


def kside_values(rng, rows=64, cols=64, vault=None, cyl=1.0,
                 altitude=35.0, azimuth=180.0, asvf_mode='realistic', seed=7, t=0.0):
    """Admitted-profile Kside_veg_v2022a boundary bundle on a real vault.

    The wrapper routes scalar-angle cyl!=1 bundles to the serial engine
    reference, whose box path requires a tensor-origin condition; box-route
    cases therefore pass ``t`` as a 0-d array to stay on the compiled body.
    """
    vault = real_vault(2) if vault is None else vault
    patches = vault.shape[0]
    rng = np.random.default_rng(seed)
    plane = lambda lo, hi: rng.uniform(lo, hi, (rows, cols)).astype(np.float32)
    cube = lambda lo, hi: rng.uniform(lo, hi, (rows, cols, patches)).astype(np.float32)
    return {
        'radI': np.float32(650.0), 'radD': np.float32(120.0), 'radG': np.float32(700.0),
        'shadow': plane(0.0, 1.0),
        'svfS': plane(0.4, 1.0), 'svfW': plane(0.4, 1.0),
        'svfN': plane(0.4, 1.0), 'svfE': plane(0.4, 1.0),
        'svfEveg': plane(0.3, 0.9), 'svfSveg': plane(0.3, 0.9),
        'svfWveg': plane(0.3, 0.9), 'svfNveg': plane(0.3, 0.9),
        'azimuth': azimuth, 'altitude': altitude, 'psi': np.float32(0.03), 't': t,
        'albedo': np.float32(0.2), 'F_sh': plane(0.3, 0.9),
        'KupE': plane(0.0, 50.0), 'KupS': plane(0.0, 50.0),
        'KupW': plane(0.0, 50.0), 'KupN': plane(0.0, 50.0),
        'cyl': np.float32(cyl),
        'lv': vault, 'anisotropic_diffuse': 1,
        'diffsh': cube(0.0, 1.0),
        'rows': rows, 'cols': cols,
        'asvf': asvf_field(rng, rows, cols, asvf_mode),
        'shmat': (rng.random((rows, cols, patches)) > 0.5).astype(np.float32),
        'vegshmat': (rng.random((rows, cols, patches)) > 0.5).astype(np.float32),
        'vbshvegshmat': (rng.random((rows, cols, patches)) > 0.5).astype(np.float32),
    }


def lcyl_arguments(rng, rows=16, cols=16, vault=None, esky=0.85, Ta=21.0,
                   solar_altitude=35.0, solar_azimuth=180.0):
    """Float32 engine-profile Lcyl_v2022a bundle on a real vault."""
    vault = real_vault(2) if vault is None else vault
    patches = vault.shape[0]
    rng = np.random.default_rng(20260921)
    return {
        'esky': np.array(esky, np.float32),
        'sky_patches': vault,
        'Ta': np.array(Ta, np.float32),
        'Tgwall': np.array(15.0, np.float32),
        'ewall': np.array(0.9, np.float32),
        'Lup': (rng.random(rows * cols).reshape(rows, cols) * 450 + 350).astype(np.float32),
        'shmat': (rng.random((rows, cols, patches)) > .3).astype(np.float32),
        'vegshmat': (rng.random((rows, cols, patches)) > .5).astype(np.float32),
        'vbshvegshmat': (rng.random((rows, cols, patches)) > .6).astype(np.float32),
        'solar_altitude': np.array(solar_altitude, np.float32),
        'solar_azimuth': np.array(solar_azimuth, np.float32),
        'rows': rows, 'cols': cols,
        'asvf': np.full((rows, cols), .6, np.float32),
    }


@pytest.fixture
def rng():
    """Deterministic per-test generator (no repo-wide fixture exists)."""
    return np.random.default_rng(20260921)


@pytest.fixture
def gate_off():
    """Guarantee the retained route for one test, restoring the env after."""
    saved = os.environ.pop(GATE_ENV, None)
    try:
        yield
    finally:
        if saved is not None:
            os.environ[GATE_ENV] = saved
        else:
            os.environ.pop(GATE_ENV, None)


@pytest.fixture
def gate_on(gate_off):
    """Opt the exact-table route in for one test (inherits gate_off cleanup)."""
    os.environ[GATE_ENV] = '1'
    yield


@pytest.fixture(scope='session', autouse=True)
def warm_classes_table():
    """Compile the serial exact-table kernel once (16 pixels, 9 patches)."""
    previous = os.environ.pop(GATE_ENV, None)
    os.environ[GATE_ENV] = '1'
    try:
        geometry = p.patch_geometry(crafted_vault())
        field = np.full((4, 4), 0.6, np.float32)
        p._classes(np.array(35.0, np.float32), 180.0, geometry, field, 0, 16)
    finally:
        os.environ.pop(GATE_ENV, None)
        if previous is not None:
            os.environ[GATE_ENV] = previous
