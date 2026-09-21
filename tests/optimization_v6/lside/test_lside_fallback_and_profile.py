"""C6-20 demand-profile, ownership and full-diagnostic fallback tests.

Gate: the FULL_DIAGNOSTICS profile must remain the untouched original path
end-to-end at kernel level, unsupported profiles must fall back, omitted
diagnostics are ``NOT_REQUESTED`` sentinels (never zeros), and returned arrays
keep original allocation ownership (fresh arrays, never views of Lup).
"""
from __future__ import annotations

import os
import threading

os.environ.setdefault('NUMBA_NUM_THREADS', '2')  # development thread cap

import sys
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
    LSIDE_ANISOTROPIC_DEMAND_PROFILE,
    NOT_REQUESTED,
    RadiationDemand,
    current_demand,
    demand_identity,
    lside_veg_v2022a_demanded,
    radiation_demand,
)

PARAM_ORDER = (
    'svfS', 'svfW', 'svfN', 'svfE', 'svfEveg', 'svfSveg', 'svfWveg', 'svfNveg',
    'svfEaveg', 'svfSaveg', 'svfWaveg', 'svfNaveg',
    'azimuth', 'altitude', 'Ta', 'Tw', 'SBC', 'ewall', 'Ldown', 'esky', 't',
    'F_sh', 'CI', 'LupE', 'LupS', 'LupW', 'LupN', 'anisotropic_longwave',
)


def make_case(shape=(24, 24), dtype=np.float32, seed=1717):
    rng = np.random.default_rng(seed)

    def svf():
        return (0.1 + 0.8 * rng.random(shape)).astype(dtype)

    return dict(
        svfS=svf(), svfW=svf(), svfN=svf(), svfE=svf(),
        svfEveg=svf(), svfSveg=svf(), svfWveg=svf(), svfNveg=svf(),
        svfEaveg=svf(), svfSaveg=svf(), svfWaveg=svf(), svfNaveg=svf(),
        azimuth=137.5, altitude=32.0, Ta=21.5,
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


def test_profile_members_and_identity():
    assert set(RadiationDemand) == {
        RadiationDemand.FULL_DIAGNOSTICS,
        RadiationDemand.PIPELINE_CYLINDER_ANISOTROPIC,
    }
    identity = demand_identity()
    assert identity['math_profile'] == 'solweig-portable-sleef-5a1d179d-v1'
    assert identity['fastmath'] is False
    assert identity['reduction_rule'] == 'R-A'


def test_not_requested_sentinel_is_not_a_zero():
    assert NOT_REQUESTED is NOT_REQUESTED  # singleton
    assert not isinstance(NOT_REQUESTED, np.ndarray)
    assert repr(NOT_REQUESTED) == '<not_requested>'
    profile = LSIDE_ANISOTROPIC_DEMAND_PROFILE
    assert profile['Least'] == 'demanded'
    assert profile['Lsouth'] == 'demanded'
    assert profile['Lwest'] == 'demanded'
    assert profile['Lnorth'] == 'demanded'
    # Everything the original evaluates beyond the four demanded results is
    # explicitly not requested, never a zero-filled stand-in.
    diagnostics = {k: v for k, v in profile.items() if v != 'demanded'}
    assert diagnostics and all(v is NOT_REQUESTED for v in diagnostics.values())


def test_full_diagnostics_is_the_original_path():
    """FULL_DIAGNOSTICS must call the original function with identical args."""
    case = make_case()
    args = [case[name] for name in PARAM_ORDER]
    observed = {}
    original = engine_mod.Lside_veg_v2022a

    def spy(*a, **k):
        observed['args'] = a
        return original(*a, **k)

    engine_mod.Lside_veg_v2022a = spy
    try:
        result = lside_veg_v2022a_demanded(*args, demand=RadiationDemand.FULL_DIAGNOSTICS)
    finally:
        engine_mod.Lside_veg_v2022a = original
    assert observed['args'] == tuple(args)
    reference = Lside_veg_v2022a(*args)
    for got, want in zip(result, reference):
        assert got.tobytes() == want.tobytes()


def test_default_demand_is_full_diagnostics():
    assert current_demand() is RadiationDemand.FULL_DIAGNOSTICS
    case = make_case()
    args = [case[name] for name in PARAM_ORDER]
    result = lside_veg_v2022a_demanded(*args)
    reference = Lside_veg_v2022a(*args)
    for got, want in zip(result, reference):
        assert got.tobytes() == want.tobytes()


def test_pipeline_profile_day_and_night_end_to_end():
    """Both schedules, full 24-step chronology, bitwise against the original."""
    case = make_case(shape=(24, 24))
    args = [case[name] for name in PARAM_ORDER]
    for step in range(24):
        step_args = list(args)
        step_args[13] = -8.0 if step % 6 == 0 else 12.0 + step  # altitude in PARAM_ORDER
        step_args[12] = (100.0 + 15.0 * step) % 360.0
        got = lside_veg_v2022a_demanded(*step_args, demand=RadiationDemand.PIPELINE_CYLINDER_ANISOTROPIC)
        want = Lside_veg_v2022a(*step_args)
        for g, w in zip(got, want):
            assert g.tobytes() == w.tobytes(), f'step {step} bytes differ'


def test_isotropic_request_falls_back_even_under_pipeline_profile():
    """anisotropic_longwave != 1 keeps the full original isotropic branch."""
    case = make_case()
    case['anisotropic_longwave'] = 0
    args = [case[name] for name in PARAM_ORDER]
    result = lside_veg_v2022a_demanded(*args, demand=RadiationDemand.PIPELINE_CYLINDER_ANISOTROPIC)
    reference = Lside_veg_v2022a(*args)
    multiplied = tuple(
        np.multiply(case[key], np.float32(0.5))
        for key in ('LupE', 'LupS', 'LupW', 'LupN')
    )
    for got, want, halved in zip(result, reference, multiplied):
        assert got.tobytes() == want.tobytes()
        assert got.tobytes() != halved.tobytes()


def test_demand_context_manager_and_thread_isolation():
    assert current_demand() is RadiationDemand.FULL_DIAGNOSTICS
    with radiation_demand(RadiationDemand.PIPELINE_CYLINDER_ANISOTROPIC):
        assert current_demand() is RadiationDemand.PIPELINE_CYLINDER_ANISOTROPIC
        seen = {}

        def other_thread():
            seen['demand'] = current_demand()

        thread = threading.Thread(target=other_thread)
        thread.start()
        thread.join()
        assert seen['demand'] is RadiationDemand.FULL_DIAGNOSTICS
    assert current_demand() is RadiationDemand.FULL_DIAGNOSTICS
    with pytest.raises(TypeError):
        radiation_demand('pipeline_cylinder_anisotropic')


def test_returned_arrays_own_storage():
    """Original ownership contract: fresh arrays, never views over Lup."""
    case = make_case()
    args = [case[name] for name in PARAM_ORDER]
    result = lside_veg_v2022a_demanded(*args, demand=RadiationDemand.PIPELINE_CYLINDER_ANISOTROPIC)
    for array, key in zip(result, ('LupE', 'LupS', 'LupW', 'LupN')):
        assert array.base is None
        snapshot = case[key].tobytes()
        array[...] = -1.0
        assert case[key].tobytes() == snapshot, 'mutating the result leaked into Lup input'


def test_nonfinite_and_signed_zero_payload_preserved():
    case = make_case()
    shape = case['LupE'].shape
    case['LupE'] = np.full(shape, np.nan, dtype=np.float32)
    case['LupS'] = np.full(shape, np.inf, dtype=np.float32)
    case['LupW'] = np.full(shape, -np.inf, dtype=np.float32)
    case['LupN'] = np.full(shape, -0.0, dtype=np.float32)
    args = [case[name] for name in PARAM_ORDER]
    result = lside_veg_v2022a_demanded(*args, demand=RadiationDemand.PIPELINE_CYLINDER_ANISOTROPIC)
    reference = Lside_veg_v2022a(*args)
    for got, want in zip(result, reference):
        assert got.tobytes() == want.tobytes()
    assert np.signbit(result[3]).all(), 'signed zero payload must be preserved'
