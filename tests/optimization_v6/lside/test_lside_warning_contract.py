"""C6-20 warning/error contract tests for the anisotropic Lside fast path.

Gate: a domain where the original warns must see the candidate warn with the
same category, message and per-call count; strict-error regimes must see the
identical FloatingPointError.  Tier B of the fast path re-executes the original
``log(1 - svf)`` pair per affected direction, and any promoted error falls back
to the original function so the raised error originates from the original site
(this is asserted by construction via the fallback spy).
"""
from __future__ import annotations

import os
import warnings

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
    RadiationDemand,
    lside_veg_v2022a_demanded,
)

PARAM_ORDER = (
    'svfS', 'svfW', 'svfN', 'svfE', 'svfEveg', 'svfSveg', 'svfWveg', 'svfNveg',
    'svfEaveg', 'svfSaveg', 'svfWaveg', 'svfNaveg',
    'azimuth', 'altitude', 'Ta', 'Tw', 'SBC', 'ewall', 'Ldown', 'esky', 't',
    'F_sh', 'CI', 'LupE', 'LupS', 'LupW', 'LupN', 'anisotropic_longwave',
)


def make_case(shape=(32, 32), dtype=np.float32, seed=4242):
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


def run(case, demand=RadiationDemand.PIPELINE_CYLINDER_ANISOTROPIC, filters=('always',), errstate=None, spy=None):
    """Run the candidate under a warning/errstate regime; record warnings."""
    args = [case[name] for name in PARAM_ORDER]
    original = engine_mod.Lside_veg_v2022a
    state = {'calls': 0}

    def counting(*a, **k):
        state['calls'] += 1
        return original(*a, **k)

    engine_mod.Lside_veg_v2022a = counting
    try:
        with warnings.catch_warnings(record=True) as caught:
            for item in filters:
                warnings.simplefilter(item)
            if errstate is None:
                result = lside_veg_v2022a_demanded(*args, demand=demand)
            else:
                with np.errstate(**errstate):
                    result = lside_veg_v2022a_demanded(*args, demand=demand)
    finally:
        engine_mod.Lside_veg_v2022a = original
        if spy is not None:
            spy.update(state)
    return result, [(w.category.__name__, str(w.message)) for w in caught]


def run_original(case, filters=('always',), errstate=None):
    args = [case[name] for name in PARAM_ORDER]
    with warnings.catch_warnings(record=True) as caught:
        for item in filters:
            warnings.simplefilter(item)
        if errstate is None:
            result = Lside_veg_v2022a(*args)
        else:
            with np.errstate(**errstate):
                result = Lside_veg_v2022a(*args)
    return result, [(w.category.__name__, str(w.message)) for w in caught]


def test_tier_b_warning_parity_svf_one():
    """svf == 1 pixels: same category, same message, same per-call count."""
    case = make_case()
    case['svfE'] = np.full(case['svfE'].shape, 1.0, dtype=np.float32)
    spy = {}
    _, warned = run(case, spy=spy)
    _, warned_original = run_original(case)
    assert spy['calls'] == 0, 'svf==1 within bounds must stay on the fast path'
    assert warned == warned_original
    assert warned.count(('RuntimeWarning', 'divide by zero encountered in log')) == 1


def test_tier_b_warning_count_per_direction():
    """Only directions containing svf == 1 emit; counts match the original."""
    case = make_case()
    case['svfN'] = np.full(case['svfN'].shape, 1.0, dtype=np.float32)
    spy = {}
    _, warned = run(case, spy=spy)
    _, warned_original = run_original(case)
    assert spy['calls'] == 0
    assert warned == warned_original
    assert len(warned) == 1

    case = make_case()
    for key in ('svfE', 'svfW'):
        case[key] = np.full(case[key].shape, 1.0, dtype=np.float32)
    spy = {}
    _, warned = run(case, spy=spy)
    _, warned_original = run_original(case)
    assert warned == warned_original
    assert len(warned) == 2


def test_tier_a_no_warnings():
    """svf < 1 everywhere: neither path warns."""
    case = make_case()
    spy = {}
    _, warned = run(case, spy=spy)
    _, warned_original = run_original(case)
    assert spy['calls'] == 0
    assert warned == warned_original == []


def test_warning_filter_error_falls_back_to_original_site():
    """A filter promoting the warning to an error falls back; original raises."""
    case = make_case()
    case['svfE'] = np.full(case['svfE'].shape, 1.0, dtype=np.float32)
    spy = {}
    with pytest.raises(RuntimeWarning, match='divide by zero encountered in log'):
        run(case, filters=['error'], spy=spy)
    assert spy['calls'] == 1, 'promoted warning must be re-raised from the original'


def test_seterr_divide_raise_falls_back_identically():
    case = make_case()
    case['svfE'] = np.full(case['svfE'].shape, 1.0, dtype=np.float32)
    spy = {}
    with pytest.raises(FloatingPointError, match='divide by zero encountered in log'):
        run(case, errstate=dict(divide='raise'), spy=spy)
    assert spy['calls'] == 1, 'non-default errstate must use the original function'


def test_seterr_invalid_raise_falls_back_identically():
    case = make_case()
    case['svfW'] = np.full(case['svfW'].shape, np.float32(1.5), dtype=np.float32)
    spy = {}
    with pytest.raises(FloatingPointError, match='invalid value encountered in log'):
        run(case, errstate=dict(invalid='raise'), spy=spy)
    assert spy['calls'] == 1


def test_seterr_under_warn_falls_back_with_identical_warnings():
    """Tiny svf underflows the removed Lvikt polynomial: fallback preserves it."""
    case = make_case()
    case['svfE'] = np.full(case['svfE'].shape, np.float32(1e-20), dtype=np.float32)
    spy = {}
    result, warned = run(case, errstate=dict(under='warn'), spy=spy)
    assert spy['calls'] == 1, 'under != ignore must fall back'
    reference, warned_original = run_original(case, errstate=dict(under='warn'))
    assert warned == warned_original
    assert any('underflow' in message for _, message in warned)
    for got, want in zip(result, reference):
        assert got.tobytes() == want.tobytes()


def test_seterr_ignore_silent_parity():
    case = make_case()
    case['svfE'] = np.full(case['svfE'].shape, 1.0, dtype=np.float32)
    spy = {}
    result, warned = run(case, filters=['ignore'], errstate=dict(divide='ignore', invalid='ignore'), spy=spy)
    reference, warned_original = run_original(case, filters=['ignore'], errstate=dict(divide='ignore', invalid='ignore'))
    assert warned == warned_original == []
    for got, want in zip(result, reference):
        assert got.tobytes() == want.tobytes()


@pytest.mark.parametrize('field,value,message', (
    ('svfE', np.float32(1.5), 'invalid value encountered in log'),
    ('svfS', np.float32(-0.25), 'invalid value encountered in arcsin'),
))
def test_fallback_warning_parity_invalid_domains(field, value, message):
    """Outside [0,1] svf: fallback re-warns exactly like the original."""
    case = make_case()
    case[field] = np.full(case[field].shape, value, dtype=np.float32)
    spy = {}
    _, warned = run(case, spy=spy)
    _, warned_original = run_original(case)
    assert spy['calls'] == 1
    assert warned == warned_original
    assert ('RuntimeWarning', message) in warned


def test_nan_svf_silent_parity():
    case = make_case()
    case['svfS'] = np.full(case['svfS'].shape, np.nan, dtype=np.float32)
    spy = {}
    result, warned = run(case, spy=spy)
    reference, warned_original = run_original(case)
    assert warned == warned_original == []
    for got, want in zip(result, reference):
        assert got.tobytes() == want.tobytes()
