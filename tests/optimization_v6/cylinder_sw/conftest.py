"""Shared fixtures for the cylinder shortwave narrow-scratch specialization.

The oracle for every parity gate is the untouched serial engine reference
``engine._serial_Kside_veg_v2022a``; real captured boundary inputs come from
the ``patch_radiation_original_cpu`` reference packet.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
from solweig_light.radiation import cylinder_shortwave, engine, patch_radiation

PACKET_ROOT = Path(__file__).resolve().parents[2] / 'reference/patch_radiation_original_cpu'

FIELD_NAMES = ('Keast', 'Ksouth', 'Kwest', 'Knorth', 'KsideI', 'KsideD', 'Kside')


def packet_cases():
    manifest = json.loads((PACKET_ROOT / 'manifest.json').read_text())
    return [case for case in manifest['cases']
            if case['function'] == 'Kside_veg_v2022a' and case['status'] == 'captured']


def load_packet_values(case):
    """Load one captured boundary input with sha256 verification."""
    path = PACKET_ROOT / case['input']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == case['input_sha256']
    with np.load(path) as archive:
        return {name: archive[name].copy() for name in archive.files}


def serial_reference(values):
    """Call the untouched original CPU translation with the same binding.

    No errstate shaping here: callers control warning visibility so the
    observability audit can compare warning classes with the wrapper.
    """
    import inspect
    reference = engine._serial_Kside_veg_v2022a
    bound = inspect.signature(reference).bind(**values).arguments
    return reference(**bound)


def assert_bitwise(actual, expected, context):
    """float32 bit equality: preserves NaN payloads, signed zeros, infinities."""
    for name, got, want in zip(FIELD_NAMES, actual, expected):
        got = np.asarray(got)
        want = np.asarray(want)
        assert got.dtype == np.float32 == want.dtype, f'{context}/{name}: dtype {got.dtype} vs {want.dtype}'
        assert got.shape == want.shape, f'{context}/{name}: shape {got.shape} vs {want.shape}'
        assert np.array_equal(got.view(np.uint32), want.view(np.uint32)), f'{context}/{name}: bits differ'


PROTOCOL = json.loads((Path(__file__).resolve().parents[3] / 'benchmarks/protocols/comparison_v1.json').read_text())


def assert_within_original_budget(actual, expected, context):
    """Compare against the serial reference with the untouched upstream budget
    (comparison_v1 Kside_veg_v2022a rules). The compiled route differs from
    the serial translation on transcendental-driven fields by a pre-existing
    float32/float64 degree-radian profile difference; no specialization of
    the route can be bitwise vs serial, so the original budget governs there
    while the bitwise gate binds to the retained wrapper route."""
    for name, got, want in zip(FIELD_NAMES, actual, expected):
        got = np.asarray(got)
        want = np.asarray(want)
        assert np.array_equal(np.isfinite(got), np.isfinite(want)), f'{context}/{name}: nonfinite sentinel masks differ'
        got64 = got.astype(np.float64)
        want64 = want.astype(np.float64)
        budget = PROTOCOL['field_rules'][f'Kside_veg_v2022a/{name}']
        finite = np.isfinite(want)
        error = np.abs(got64[finite] - want64[finite])
        limits = budget['atol'] + budget['rtol'] * np.abs(want64[finite])
        assert np.all(error <= limits), f'{context}/{name}: max error {error.max()} budget {limits.max()}'


def wrapper_route(values, block_pixels=17, parallel=False):
    """The retained compiled wrapper route on the same bound arguments."""
    import inspect
    bound = inspect.signature(engine._serial_Kside_veg_v2022a).bind(**values).arguments
    with np.errstate(all='ignore'):
        return patch_radiation.Kside_veg_v2022a(**bound, block_pixels=block_pixels, parallel=parallel)


def synthetic_values(rows, cols, mode='baseline', altitude=35.0, azimuth=180.0, seed=7):
    """Adversarial cylinder-anisotropic Kside inputs on a six-patch vault."""
    if mode == 'extreme-sun' and altitude == 35.0 and azimuth == 180.0:
        altitude, azimuth = 89.5, 359.9
    rng = np.random.default_rng(seed)
    patches = 6
    lv = np.zeros((patches, 3), dtype=np.float32)
    lv[:, 0] = (10.0, 25.0, 40.0, 55.0, 70.0, 85.0)
    lv[:, 1] = (45.0, 135.0, 225.0, 315.0, 90.0, 270.0)
    lv[:, 2] = rng.uniform(0.1, 10.0, patches).astype(np.float32)
    pixels = rows * cols

    def cube(lo, hi):
        return rng.uniform(lo, hi, (rows, cols, patches)).astype(np.float32)

    def plane(lo, hi):
        return rng.uniform(lo, hi, (rows, cols)).astype(np.float32)

    if mode == 'zero-sentinel':
        shmat = np.zeros((rows, cols, patches), dtype=np.float32)
        vegshmat = np.zeros_like(shmat)
        vbsh = np.zeros_like(shmat)
        diffsh = np.zeros_like(shmat)
        shadow = np.zeros((rows, cols), dtype=np.float32)
        asvf = plane(0.1, 1.5)
        kup = [np.zeros((rows, cols), dtype=np.float32) for _ in range(4)]
        rad_i = np.float32(0.0)
        rad_d = np.float32(0.0)
    elif mode == 'vegetated':
        shmat = cube(0.0, 1.0)
        vegshmat = np.zeros((rows, cols, patches), dtype=np.float32)
        vbsh = np.zeros((rows, cols, patches), dtype=np.float32)
        diffsh = cube(0.0, 1.0)
        shadow = plane(0.0, 1.0)
        asvf = plane(0.1, 1.5)
        kup = [plane(0.0, 50.0) for _ in range(4)]
        rad_i = np.float32(650.0)
        rad_d = np.float32(120.0)
    elif mode == 'extreme-sun':
        shmat = cube(0.0, 1.0)
        vegshmat = (rng.random((rows, cols, patches)) > 0.5).astype(np.float32)
        vbsh = (rng.random((rows, cols, patches)) > 0.5).astype(np.float32)
        diffsh = cube(0.0, 1.0)
        shadow = plane(0.0, 1.0)
        asvf = plane(0.1, 1.5)
        kup = [plane(0.0, 50.0) for _ in range(4)]
        rad_i = np.float32(650.0)
        rad_d = np.float32(120.0)
    else:
        shmat = (rng.random((rows, cols, patches)) > 0.5).astype(np.float32)
        vegshmat = (rng.random((rows, cols, patches)) > 0.5).astype(np.float32)
        vbsh = (rng.random((rows, cols, patches)) > 0.5).astype(np.float32)
        diffsh = cube(0.0, 1.0)
        shadow = plane(0.0, 1.0)
        asvf = plane(0.1, 1.5)
        kup = [plane(0.0, 50.0) for _ in range(4)]
        rad_i = np.float32(650.0)
        rad_d = np.float32(120.0)

    return {
        'radI': rad_i,
        'radD': rad_d,
        'radG': np.float32(700.0),
        'shadow': shadow,
        'svfS': plane(0.4, 1.0), 'svfW': plane(0.4, 1.0),
        'svfN': plane(0.4, 1.0), 'svfE': plane(0.4, 1.0),
        'svfEveg': plane(0.3, 0.9), 'svfSveg': plane(0.3, 0.9),
        'svfWveg': plane(0.3, 0.9), 'svfNveg': plane(0.3, 0.9),
        'azimuth': azimuth,
        'altitude': altitude,
        'psi': np.float32(0.03),
        't': 0.0,
        'albedo': np.float32(0.2),
        'F_sh': plane(0.3, 0.9),
        'KupE': kup[0], 'KupS': kup[1], 'KupW': kup[2], 'KupN': kup[3],
        'cyl': np.float32(1),
        'lv': lv,
        'anisotropic_diffuse': 1,
        'diffsh': diffsh,
        'rows': rows,
        'cols': cols,
        'asvf': asvf,
        'shmat': shmat,
        'vegshmat': vegshmat,
        'vbshvegshmat': vbsh,
    }


@pytest.fixture()
def admitted_profile():
    """Opt the private demand profile in for one test, restoring it after."""
    previous = cylinder_shortwave.demand_profile()
    cylinder_shortwave.set_demand_profile(cylinder_shortwave.PIPELINE_CYLINDER_ANISOTROPIC)
    yield
    cylinder_shortwave.set_demand_profile(previous)


@pytest.fixture(scope='session', autouse=True)
def warm_kernels():
    """Compile both narrow kernels once so later instrumentation sees only
    steady-state calls (numba resolves module globals at compile time)."""
    values = synthetic_values(16, 16, seed=3)
    cylinder_shortwave.set_demand_profile(cylinder_shortwave.PIPELINE_CYLINDER_ANISOTROPIC)
    for parallel in (False, True):
        cylinder_shortwave.kside_cylinder_anisotropic(values, block_pixels=16, parallel=parallel)
    cylinder_shortwave.set_demand_profile(cylinder_shortwave.FULL_DIAGNOSTICS)
    yield
