"""C6-20 L1 gate: bitwise parity of the private anisotropic Lside fast path.

Compares ``lside_veg_v2022a_demanded`` (PIPELINE_CYLINDER_ANISOTROPIC) against
the untouched ``engine.Lside_veg_v2022a`` on real small kernels (16-128 square,
adversarial day/night schedules, degenerate Lup fields) at every timestep.
Equality is required bitwise: dtype, shape and raw bytes, which also preserves
nonfinite payloads and signed zeros.  The original function is called through
a spy so the test also proves whether the candidate took the fast path or the
original fallback, and exception-class/message parity is asserted for inputs
where the original itself fails.
"""
from __future__ import annotations

import os

os.environ.setdefault('NUMBA_NUM_THREADS', '2')  # development thread cap

import sys
import warnings
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[3]
SRC = REPO / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import solweig_light.radiation.engine as engine_mod  # noqa: E402
from solweig_light.radiation.engine import Lside_veg_v2022a  # noqa: E402
from solweig_light.radiation.pipeline_demand import (  # noqa: E402
    RadiationDemand,
    lside_veg_v2022a_demanded,
)

PARAM_ORDER = (
    'svfS', 'svfW', 'svfN', 'svfE', 'svfEveg', 'svfSveg', 'svfWveg', 'svfNveg',
    'svfEaveg', 'svfSaveg', 'svfWaveg', 'svfNaveg',
    'azimuth', 'altitude', 'Ta', 'Tw', 'SBC', 'ewall', 'Ldown', 'esky', 't',
    'F_sh', 'CI', 'LupE', 'LupS', 'LupW', 'LupN', 'anisotropic_longwave',
)


def assert_bits_equal(result, reference, label):
    assert len(result) == len(reference), label
    for name, got, want in zip(('Least', 'Lsouth', 'Lwest', 'Lnorth'), result, reference):
        assert got.dtype == want.dtype, f"{label}/{name}: dtype {got.dtype} != {want.dtype}"
        assert got.shape == want.shape, f"{label}/{name}: shape mismatch"
        if got.dtype == object:
            assert [str(v) for v in got.ravel()] == [str(v) for v in want.ravel()], (
                f"{label}/{name}: object values differ")
        else:
            assert got.tobytes() == want.tobytes(), f"{label}/{name}: bytes differ"


def make_case(shape, dtype, svf_mode, seed):
    """Deterministic input bundle for one svf regime."""
    rng = np.random.default_rng(seed)

    def svf(lo=0.05, hi=0.99):
        return (lo + (hi - lo) * rng.random(shape)).astype(dtype)

    case = dict(
        svfS=svf(), svfW=svf(), svfN=svf(), svfE=svf(),
        svfEveg=svf(), svfSveg=svf(), svfWveg=svf(), svfNveg=svf(),
        svfEaveg=svf(), svfSaveg=svf(), svfWaveg=svf(), svfNaveg=svf(),
        azimuth=137.5, altitude=32.0, Ta=np.float64(21.5),
        Tw=(30.0 * rng.random(shape)).astype(dtype),
        SBC=5.67e-8, ewall=0.95,
        Ldown=(400.0 * rng.random(shape)).astype(dtype),
        esky=0.85, t=15,
        F_sh=rng.random(shape).astype(dtype),
        CI=0.72,
        LupE=(450.0 * rng.random(shape)).astype(dtype),
        LupS=(450.0 * rng.random(shape)).astype(dtype),
        LupW=(450.0 * rng.random(shape)).astype(dtype),
        LupN=(450.0 * rng.random(shape)).astype(dtype),
        anisotropic_longwave=1,
    )
    if svf_mode == 'svf_one_E':
        case['svfE'] = np.full(shape, 1.0, dtype=dtype)
    elif svf_mode == 'svf_one_E_and_N':
        case['svfE'] = np.full(shape, 1.0, dtype=dtype)
        case['svfN'] = np.full(shape, 1.0, dtype=dtype)
    elif svf_mode == 'svf_zero_pixels':
        for key in ('svfS', 'svfW', 'svfN', 'svfE'):
            case[key][0, :] = dtype(0.0)
    elif svf_mode == 'svf_bounds':
        for key in ('svfS', 'svfW', 'svfN', 'svfE'):
            case[key] = np.linspace(dtype(0.0), dtype(1.0), shape[0] * shape[1]).reshape(shape)
    elif svf_mode == 'svf_int':
        for key in ('svfS', 'svfW', 'svfN', 'svfE'):
            case[key] = (case[key] > 0.5).astype(np.int64)
    return case


def call_both(case, spy):
    """Call candidate (spied) and original on identical inputs.

    Returns ``(outcome, fell_back)`` where each outcome is either
    ``('ok', tuple_of_arrays)`` or ``('error', exception)``.
    """
    args = [case[name] for name in PARAM_ORDER]
    spy['calls'] = 0
    original = engine_mod.Lside_veg_v2022a

    def counting(*a, **k):
        spy['calls'] += 1
        return original(*a, **k)

    engine_mod.Lside_veg_v2022a = counting
    try:
        try:
            got = ('ok', lside_veg_v2022a_demanded(*args, demand=RadiationDemand.PIPELINE_CYLINDER_ANISOTROPIC))
        except Exception as exc:  # noqa: BLE001 - parity must hold for failures too
            got = ('error', exc)
    finally:
        engine_mod.Lside_veg_v2022a = original
    try:
        want = ('ok', Lside_veg_v2022a(*args))
    except Exception as exc:  # noqa: BLE001
        want = ('error', exc)
    return got, want


def assert_same_outcome(got, want, label):
    kind_got, payload_got = got
    kind_want, payload_want = want
    assert kind_got == kind_want, f"{label}: candidate {kind_got} but original {kind_want}"
    if kind_got == 'error':
        assert type(payload_got) is type(payload_want), f"{label}: exception class differs"
        assert str(payload_got) == str(payload_want), f"{label}: exception message differs"
        return
    assert_bits_equal(payload_got, payload_want, label)


@pytest.mark.parametrize('svf_mode', [
    'clean', 'svf_one_E', 'svf_one_E_and_N', 'svf_zero_pixels', 'svf_bounds', 'svf_int',
])
@pytest.mark.parametrize('shape,dtype,seed', [
    ((16, 16), np.float32, 101),
    ((64, 64), np.float32, 202),
    ((128, 128), np.float32, 303),
    ((16, 16), np.float64, 404),
])
def test_bitwise_parity_adversarial_schedule(svf_mode, shape, dtype, seed):
    """24-step adversarial schedule: every timestep bitwise equal, fast path taken."""
    case = make_case(shape, dtype, svf_mode, seed)
    spy = {}
    for step in range(24):
        step_case = dict(case)
        # Day/night altitude cycle including exact boundary values.
        step_case['altitude'] = (-8.0 if step % 5 == 0 else (0.0 if step % 7 == 0 else 4.0 + 2.5 * step))
        # Azimuth sweep with out-of-range adversarial values.
        azimuth = (122.0 + 15.0 * step) % 360.0
        if step % 11 == 3:
            azimuth = 361.0
        if step % 11 == 5:
            azimuth = -30.0
        step_case['azimuth'] = azimuth
        # CI across the anisotropic all-sky branches.
        step_case['CI'] = (0.2, 0.72, 0.95, 1.0)[step % 4]
        # Lup as carried state: accumulate, then inject degenerate values.
        if step > 0:
            for key in ('LupE', 'LupS', 'LupW', 'LupN'):
                step_case[key] = (step_case[key] + dtype(0.25)).astype(dtype)
        if step == 6:
            for key in ('LupE', 'LupS', 'LupW', 'LupN'):
                step_case[key] = np.zeros(shape, dtype=dtype)
        if step == 9:
            step_case['LupE'] = np.full(shape, np.nan, dtype=dtype)
            step_case['LupS'] = step_case['LupS'].copy()
            step_case['LupS'][0, 0] = np.inf
            step_case['LupS'][1, 1] = -np.inf
        if step == 12:
            step_case['LupW'] = np.full(shape, -0.0, dtype=dtype)
            step_case['LupN'] = np.full(shape, 5e-324 if dtype == np.float64 else 1e-45, dtype=dtype)
        if step == 15:
            step_case['Tw'] = np.full(shape, 400.0, dtype=dtype)
        got, want = call_both(step_case, spy)
        label = f"step={step} mode={svf_mode} shape={shape} dtype={np.dtype(dtype).name}"
        assert_same_outcome(got, want, label)
        # Every case in this matrix is inside the admitted domain: the fast
        # path must be taken (the original runs only as the reference).
        assert spy['calls'] == 0, f"fast path not taken at {label}"


def test_bitwise_parity_real_svf_fixture():
    """Real processed SVF rasters (svfE contains exact-1.0 pixels)."""
    zip_path = REPO / 'tests' / 'reference' / 'small_original_cpu' / 'scene' / 'processed_inputs' / 'SVF' / 'svfs_0_0.zip'
    if not zip_path.exists():
        pytest.skip('real SVF fixture not present')
    import tempfile
    import zipfile

    from osgeo import gdal

    gdal.UseExceptions()
    shape = (32, 35)
    case = make_case(shape, np.float32, 'svf_one_E', 505)
    with zipfile.ZipFile(zip_path) as bundle:
        names = {Path(n).name: n for n in bundle.namelist()}
        for key in ('svfS', 'svfW', 'svfN', 'svfE', 'svfEveg', 'svfSveg', 'svfWveg', 'svfNveg',
                    'svfEaveg', 'svfSaveg', 'svfWaveg', 'svfNaveg'):
            with tempfile.TemporaryDirectory() as tmp:
                target = Path(tmp) / f'{key}.tif'
                target.write_bytes(bundle.read(names[f'{key}.tif']))
                dataset = gdal.Open(str(target))
                raster = dataset.GetRasterBand(1).ReadAsArray()
                dataset = None
            case[key] = np.ascontiguousarray(raster.astype(np.float32))
    assert float(case['svfE'].max()) == 1.0, 'fixture svfE must contain exact 1.0 pixels'
    spy = {}
    for step in range(24):
        step_case = dict(case)
        step_case['altitude'] = 10.0 + step
        step_case['azimuth'] = 90.0 + 15.0 * step
        got, want = call_both(step_case, spy)
        assert_same_outcome(got, want, f"fixture step={step}")
        assert spy['calls'] == 0, f"fast path not taken on real fixture step={step}"


# (label, overrides, expect_fallback): every rejected domain must route through
# the original function; night schedules with shape-mismatched Tw stay admitted
# because the anisotropic night branch never reads Tw.  Array azimuth/t are
# rejected in BOTH regimes: the prologue azi* sums (engine.py:1375-1378) run
# unconditionally and can overflow-warn on arrays (removed-operation effect).
REJECT_MATRIX = (
    ('svfE_above_one', dict(svfE=None), True),                # filled below
    ('svfS_negative', dict(svfS=None), True),
    ('svfS_nan', dict(svfS=None), True),
    ('svfEveg_beyond_bound', dict(svfEveg=None), True),
    ('Tw_beyond_bound', dict(Tw=None), True),
    ('F_sh_beyond_bound', dict(F_sh=None), True),
    ('Ta_beyond_bound', dict(Ta=1e30), True),
    ('SBC_beyond_bound', dict(SBC=np.float64(1e38)), True),
    ('altitude_1d_single', dict(altitude=np.array([32.0])), True),
    ('altitude_1d_multi', dict(altitude=np.array([32.0, 33.0])), True),
    ('Tw_shape_day', dict(Tw=None), True),
    ('F_sh_shape_day', dict(F_sh=None), True),
    ('t_array_day', dict(t=np.array([0.0, 10.0])), True),
    ('azimuth_array_night', dict(azimuth=None, altitude=-5.0), True),
    ('t_array_night', dict(t=None, altitude=-5.0), True),
    ('anisotropic_zero', dict(anisotropic_longwave=0), True),
    ('anisotropic_array', dict(anisotropic_longwave=np.array([1, 1])), True),
    ('Tw_shape_night', dict(Tw=None, altitude=-5.0), False),
)


def build_reject_cases():
    rng = np.random.default_rng(909)
    shape = (16, 16)
    dtype = np.float32
    base = make_case(shape, dtype, 'clean', 606)
    fills = {
        'svfE_above_one': np.full(shape, np.float32(1.5), dtype=dtype),
        'svfS_negative': np.full(shape, np.float32(-0.25), dtype=dtype),
        'svfS_nan': np.full(shape, np.nan, dtype=dtype),
        'svfEveg_beyond_bound': np.full(shape, np.float32(1e6), dtype=dtype),
        'Tw_beyond_bound': np.full(shape, np.float32(1e38), dtype=dtype),
        'F_sh_beyond_bound': np.full(shape, np.float32(-1e38), dtype=dtype),
        'Tw_shape_day': np.full((4, 4), np.float32(20.0), dtype=dtype),
        'F_sh_shape_day': np.full((8, 8), np.float32(0.5), dtype=dtype),
        'Tw_shape_night': np.full((4, 4), np.float32(20.0), dtype=dtype),
        'azimuth_array_night': np.full(shape, np.float32(3e38), dtype=dtype),
        't_array_night': np.full(shape, np.float32(3e38), dtype=dtype),
    }
    cases = []
    for label, overrides, expect_fallback in REJECT_MATRIX:
        case = dict(base)
        for key, value in overrides.items():
            case[key] = fills[label] if value is None else value
        cases.append((label, case, expect_fallback))
    return cases


@pytest.mark.parametrize('label,case,expect_fallback', build_reject_cases(), ids=[r[0] for r in REJECT_MATRIX])
def test_guard_rejected_and_admitted_domains(label, case, expect_fallback):
    """Rejected domains fall back; night shape-mismatch stays admitted; all parity."""
    spy = {}
    got, want = call_both(case, spy)
    assert_same_outcome(got, want, label)
    assert spy['calls'] == (1 if expect_fallback else 0), f"{label}: wrong route"


def test_bool_svf_admitted_bitwise_and_warning_parity():
    """Bool svf rasters: admitted fast path, bitwise equal, warning parity.

    A True/False mix is the degenerate svf case (exact 0.0 and 1.0 pixels);
    the 1.0 pixels route through Tier B, whose replicated log warnings must
    match the original's stream exactly.
    """
    shape = (8, 8)
    case = make_case(shape, np.float32, 'clean', 808)
    rng = np.random.default_rng(809)
    for key in ('svfS', 'svfW', 'svfN', 'svfE'):
        case[key] = rng.random(shape) > 0.4  # mix of exact 0.0 and 1.0
    args = [case[name] for name in PARAM_ORDER]
    spy = {'calls': 0}
    original = engine_mod.Lside_veg_v2022a

    def counting(*a, **k):
        spy['calls'] += 1
        return original(*a, **k)

    with warnings.catch_warnings(record=True) as caught_candidate:
        warnings.simplefilter('always')
        engine_mod.Lside_veg_v2022a = counting
        try:
            got = lside_veg_v2022a_demanded(*args, demand=RadiationDemand.PIPELINE_CYLINDER_ANISOTROPIC)
        finally:
            engine_mod.Lside_veg_v2022a = original
    with warnings.catch_warnings(record=True) as caught_reference:
        warnings.simplefilter('always')
        want = Lside_veg_v2022a(*args)
    assert spy['calls'] == 0, 'bool svf must stay on the admitted fast path'
    assert_bits_equal(got, want, 'bool svf')
    candidate_stream = [(w.category.__name__, str(w.message)) for w in caught_candidate]
    reference_stream = [(w.category.__name__, str(w.message)) for w in caught_reference]
    assert candidate_stream == reference_stream, 'warning streams differ'


def test_exotic_inputs_match_original():
    """Empty/object/longdouble inputs keep the original behavior exactly."""
    spy = {}
    shape = (8, 8)
    dtype = np.float32
    base = make_case(shape, dtype, 'clean', 707)

    empty = dict(base)
    for key in ('svfS', 'svfW', 'svfN', 'svfE'):
        empty[key] = np.zeros((0, 0), dtype=dtype)
    got, want = call_both(empty, spy)
    assert_same_outcome(got, want, 'empty svf arrays')
    assert spy['calls'] == 1, 'empty arrays must use the conservative fallback'

    object_lup = dict(base)
    for key in ('LupE', 'LupS', 'LupW', 'LupN'):
        object_lup[key] = np.full(shape, 350.0, dtype=object)
    got, want = call_both(object_lup, spy)
    assert_same_outcome(got, want, 'object lup')
    assert spy['calls'] == 0, 'object Lup never enters the guard (Lup is unguarded)'

    longdouble = dict(base)
    longdouble['svfE'] = base['svfE'].astype(np.longdouble)
    got, want = call_both(longdouble, spy)
    assert_same_outcome(got, want, 'longdouble svf')
