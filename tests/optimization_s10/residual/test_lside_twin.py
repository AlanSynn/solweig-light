"""S10-23: the exact dispatch twin of the anisotropic ``Lside_veg_v2022a`` slice.

The S10-23 recon probe (landcover golden, sha256 in the task evidence) showed
every call reaching the NumPy body carries ``anisotropic_longwave == 1``: the
body's returned cardinal fields are exactly ``Lup*0.5`` (pipeline_demand rule
R-A), while its transcendental prologue and wall chains are discarded work.
The twin certifies the identical removed-operation domain and admits the
demanded result under regimes where the ambient state already silences every
warning the removed operations can emit; everything else declines to the
serial reference.

The reference is always ``engine._serial_Lside_veg_v2022a`` (the verbatim
original body).  Acceptance is bit-level: the twin claims exactness, not a
comparison_v1 budget — the demanded result is the same ``_operate`` multiply
the body's anisotropic branch performs, so byte parity is the contract on the
whole admitted domain, and byte parity after every decline as well (the
reference IS the original).
"""
import warnings
from pathlib import Path

import numpy as np
import pytest

from solweig_light.radiation import engine, patch_radiation
from solweig_light.radiation.pipeline_demand import (
    RadiationDemand,
    _demanded_anisotropic_result,
    lside_veg_v2022a_demanded,
)

PARAM_ORDER = (
    'svfS', 'svfW', 'svfN', 'svfE', 'svfEveg', 'svfSveg', 'svfWveg', 'svfNveg',
    'svfEaveg', 'svfSaveg', 'svfWaveg', 'svfNaveg',
    'azimuth', 'altitude', 'Ta', 'Tw', 'SBC', 'ewall', 'Ldown', 'esky', 't',
    'F_sh', 'CI', 'LupE', 'LupS', 'LupW', 'LupN', 'anisotropic_longwave',
)


def make_case(shape=(32, 35), seed=4242):
    """Landcover-golden-shaped production profile (probe: day step 7)."""
    rng = np.random.default_rng(seed)

    def svf():
        return (0.1 + 0.8 * rng.random(shape)).astype(np.float32)

    return dict(
        svfS=svf(), svfW=svf(), svfN=svf(), svfE=svf(),
        svfEveg=svf(), svfSveg=svf(), svfWveg=svf(), svfNveg=svf(),
        svfEaveg=svf(), svfSaveg=svf(), svfWaveg=svf(), svfNaveg=svf(),
        azimuth=336.23211880734254, altitude=7.7567, Ta=23.0,
        Tw=np.full((1, 1), 30.5, dtype=np.float64),
        SBC=np.float32(5.67051e-8), ewall=0.9,
        Ldown=(390.0 * rng.random(shape)).astype(np.float32),
        esky=0.8390366278089432, t=0.0,
        F_sh=rng.random(shape).astype(np.float32), CI=np.float64(0.62),
        LupE=(430.0 * rng.random(shape)).astype(np.float32),
        LupS=(430.0 * rng.random(shape)).astype(np.float32),
        LupW=(430.0 * rng.random(shape)).astype(np.float32),
        LupN=(430.0 * rng.random(shape)).astype(np.float32),
        anisotropic_longwave=1,
    )


def args_of(case):
    return [case[name] for name in PARAM_ORDER]


def bitwise(outputs_a, outputs_b):
    return all(a.dtype == b.dtype and a.tobytes() == b.tobytes()
               for a, b in zip(outputs_a, outputs_b))


def counters():
    return {key: patch_radiation.ROUTE_COUNTS[key]
            for key in ('Lside_veg_v2022a_primary', 'Lside_veg_v2022a_reference')}


@pytest.fixture
def counter_delta():
    before = counters()

    def taken():
        now = counters()
        return {'primary': now['Lside_veg_v2022a_primary'] - before['Lside_veg_v2022a_primary'],
                'reference': now['Lside_veg_v2022a_reference'] - before['Lside_veg_v2022a_reference']}
    return taken


def test_production_day_profile_bitwise_default_and_leaked_regime(counter_delta):
    """Day step 7 profile: bitwise under default AND the leaked ignore regime."""
    case = make_case()
    args = args_of(case)
    reference = engine._serial_Lside_veg_v2022a(*args)
    got = engine.Lside_veg_v2022a(*args)
    assert bitwise(got, reference), 'default regime must be bitwise'
    with np.errstate(divide='ignore', invalid='ignore'):
        got_leaked = engine.Lside_veg_v2022a(*args)
        reference_leaked = engine._serial_Lside_veg_v2022a(*args)
    assert bitwise(got_leaked, reference_leaked), 'leaked regime must be bitwise'
    assert bitwise(got, got_leaked), 'the regime must not change the values'
    taken = counter_delta()
    assert taken == {'primary': 2, 'reference': 0}, taken


def test_production_night_profile_bitwise(counter_delta):
    """Night steps 21-23: int 0-d Tw, altitude < 0, leaked regime -> primary."""
    case = make_case(seed=777)
    case['altitude'] = -11.2684
    case['Tw'] = np.int64(0)
    case['F_sh'] = np.zeros((32, 35), dtype=np.float32)
    args = args_of(case)
    with np.errstate(divide='ignore', invalid='ignore'):
        got = engine.Lside_veg_v2022a(*args)
        reference = engine._serial_Lside_veg_v2022a(*args)
    assert bitwise(got, reference)
    assert counter_delta() == {'primary': 1, 'reference': 0}


def test_demanded_result_is_lup_half(counter_delta):
    """The admitted result equals the R-A demanded operations bitwise."""
    case = make_case()
    Lup = (case['LupE'], case['LupS'], case['LupW'], case['LupN'])
    got = engine.Lside_veg_v2022a(*args_of(case))
    assert bitwise(got, _demanded_anisotropic_result(*Lup))
    assert counter_delta()['primary'] == 1


def test_wall_inputs_do_not_change_admitted_result():
    """R-A: the anisotropic branch never reads the discarded-work inputs."""
    base = engine.Lside_veg_v2022a(*args_of(make_case()))
    for field, value in (('svfS', 0.0), ('svfN', 1.0), ('Tw', np.float64(99.0)),
                         ('Ldown', 0.0), ('CI', np.float64(1.0)),
                         ('F_sh', 1.0), ('altitude', 85.0), ('azimuth', 1.0),
                         ('esky', 0.5)):
        case = make_case()
        case[field] = value
        assert bitwise(engine.Lside_veg_v2022a(*args_of(case)), base), field


def test_caller_inputs_not_mutated():
    case = make_case()
    snapshot = {name: (np.asarray(case[name]).copy()
                       if np.asarray(case[name]).ndim else case[name])
                for name in PARAM_ORDER if np.asarray(case[name]).ndim}
    engine.Lside_veg_v2022a(*args_of(case))
    for name, value in snapshot.items():
        assert np.array_equal(np.asarray(case[name]), value), name


def test_decline_anisotropic_off(counter_delta):
    """anisotropic_longwave != 1 declines to the reference bitwise."""
    case = make_case()
    case['anisotropic_longwave'] = 0
    args = args_of(case)
    got = engine.Lside_veg_v2022a(*args)
    assert bitwise(got, engine._serial_Lside_veg_v2022a(*args))
    assert counter_delta() == {'primary': 0, 'reference': 1}


def test_decline_out_of_domain_svf_with_warning_parity(counter_delta):
    """svf outside [0, 1]: reference owns the invalid-domain warnings."""
    case = make_case()
    case['svfE'] = np.full((32, 35), np.float32(1.5), dtype=np.float32)
    args = args_of(case)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        got = engine.Lside_veg_v2022a(*args)
    with warnings.catch_warnings(record=True) as caught_original:
        warnings.simplefilter('always')
        reference = engine._serial_Lside_veg_v2022a(*args)
    assert [(w.category.__name__, str(w.message)) for w in caught] == \
           [(w.category.__name__, str(w.message)) for w in caught_original]
    assert bitwise(got, reference)
    assert counter_delta() == {'primary': 0, 'reference': 1}


def test_decline_nan_svf_silent_parity(counter_delta):
    case = make_case()
    case['svfS'] = np.full((32, 35), np.nan, dtype=np.float32)
    args = args_of(case)
    got = engine.Lside_veg_v2022a(*args)
    assert bitwise(got, engine._serial_Lside_veg_v2022a(*args))
    assert counter_delta() == {'primary': 0, 'reference': 1}


def test_decline_non_broadcastable_tw(counter_delta):
    """(32, 2) Tw does not broadcast against the svf shape: the twin declines
    and the reference owns the original ValueError."""
    case = make_case()
    case['Tw'] = np.zeros((32, 2), dtype=np.float64)
    args = args_of(case)
    with pytest.raises(ValueError, match='could not be broadcast'):
        engine.Lside_veg_v2022a(*args)
    with pytest.raises(ValueError, match='could not be broadcast'):
        engine._serial_Lside_veg_v2022a(*args)
    assert counter_delta() == {'primary': 0, 'reference': 1}


def test_malformed_call_owned_by_reference(counter_delta):
    """A missing argument raises TypeError owned by the original site, not by
    the twin's signature binding (review finding R5). Through the public
    engine wrapper the wrapper's own verbatim signature raises before the
    twin is consulted; through the dispatch directly the bind failure
    declines and the reference raises."""
    args = args_of(make_case())[:-1]
    with pytest.raises(TypeError):
        engine.Lside_veg_v2022a(*args)
    assert counter_delta() == {'primary': 0, 'reference': 0}, \
        'the wrapper signature owns it before any routing'
    with pytest.raises(TypeError):
        patch_radiation.Lside_veg_v2022a(*args)
    with pytest.raises(TypeError):
        engine._serial_Lside_veg_v2022a(*args)
    assert counter_delta() == {'primary': 0, 'reference': 1}


def test_replication_under_default_regime(counter_delta):
    """svf == 1 under the default regime: dispatch replicates the log warning."""
    case = make_case()
    case['svfE'] = np.full((32, 35), 1.0, dtype=np.float32)
    args = args_of(case)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        got = engine.Lside_veg_v2022a(*args)
    with warnings.catch_warnings(record=True) as caught_original:
        warnings.simplefilter('always')
        reference = engine._serial_Lside_veg_v2022a(*args)
    assert [(w.category.__name__, str(w.message)) for w in caught] == \
           [(w.category.__name__, str(w.message)) for w in caught_original]
    assert ('RuntimeWarning', 'divide by zero encountered in log') in \
        [(w.category.__name__, str(w.message)) for w in caught]
    assert bitwise(got, reference)
    assert counter_delta() == {'primary': 1, 'reference': 0}


def test_promoted_warning_falls_back_to_original_site(counter_delta):
    """A filter promoting the replicated warning to an error is owned by the
    original site (the reference), matching the C6-20 tier-B contract."""
    case = make_case()
    case['svfE'] = np.full((32, 35), 1.0, dtype=np.float32)
    args = args_of(case)
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        with pytest.raises(RuntimeWarning, match='divide by zero encountered in log'):
            engine.Lside_veg_v2022a(*args)
    assert counter_delta() == {'primary': 0, 'reference': 1}


@pytest.mark.parametrize('errstate,expect_decline', (
    (dict(divide='raise'), True),
    (dict(invalid='raise'), True),
    (dict(under='warn'), True),
    (dict(divide='call'), True),
    (dict(invalid='call'), True),
    (dict(divide='ignore', invalid='ignore'), False),
    (dict(divide='ignore'), False),
))
def test_regime_matrix(counter_delta, errstate, expect_decline):
    """Admit only when over/under stay at defaults and divide/invalid are not
    raise; the underflow escape (tiny svf, removed Lvikt polynomial) keeps its
    C6-20 fallback pin."""
    case = make_case()
    if errstate.get('under') == 'warn':
        case['svfE'] = np.full((32, 35), np.float32(1e-20), dtype=np.float32)
    args = args_of(case)
    with np.errstate(**errstate):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            got = engine.Lside_veg_v2022a(*args)
            reference = engine._serial_Lside_veg_v2022a(*args)
    assert bitwise(got, reference), errstate
    if expect_decline:
        assert counter_delta() == {'primary': 0, 'reference': 1}, errstate
    else:
        assert counter_delta() == {'primary': 1, 'reference': 0}, errstate
    if errstate.get('under') == 'warn':
        assert any('underflow' in str(w.message) for w in caught), \
            'the under regime must surface the original underflow warnings'


def test_kill_switch_routes_everything_to_reference(counter_delta, monkeypatch):
    monkeypatch.setenv('SOLWEIG_LIGHT_LSIDE_DISPATCH', '0')
    case = make_case()
    args = args_of(case)
    got = engine.Lside_veg_v2022a(*args)
    assert bitwise(got, engine._serial_Lside_veg_v2022a(*args))
    assert counter_delta() == {'primary': 0, 'reference': 1}


def test_full_diagnostics_demand_lands_on_certified_twin(counter_delta):
    """The FULL_DIAGNOSTICS branch (untouched-original contract) preserves
    values and warnings now that the public name resolves to the dispatch:
    in-domain aniso calls get the bitwise-identical demanded result."""
    case = make_case()
    case['svfE'] = np.full((32, 35), 1.0, dtype=np.float32)
    args = args_of(case)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        got = lside_veg_v2022a_demanded(*args, demand=RadiationDemand.FULL_DIAGNOSTICS)
    with warnings.catch_warnings(record=True) as caught_original:
        warnings.simplefilter('always')
        reference = engine._serial_Lside_veg_v2022a(*args)
    assert [(w.category.__name__, str(w.message)) for w in caught] == \
           [(w.category.__name__, str(w.message)) for w in caught_original]
    assert bitwise(got, reference)
    assert counter_delta() == {'primary': 1, 'reference': 0}


def test_production_demand_fallback_uses_twin(counter_delta):
    """The PIPELINE_CYLINDER_ANISOTROPIC fallback (regime-defeated guard)
    reaches the twin and returns the demanded result."""
    case = make_case()
    args = args_of(case)
    with np.errstate(divide='ignore', invalid='ignore'):
        got = lside_veg_v2022a_demanded(*args,
                                        demand=RadiationDemand.PIPELINE_CYLINDER_ANISOTROPIC)
        reference = engine._serial_Lside_veg_v2022a(*args)
    assert bitwise(got, reference)
    assert counter_delta() == {'primary': 1, 'reference': 0}


def test_engine_wrapper_wiring():
    """The public engine name resolves to the patch_radiation dispatch and the
    serial capture keeps the original body addressable as the reference."""
    from solweig_light.radiation import patch_radiation as pr
    assert engine.Lside_veg_v2022a is not engine._serial_Lside_veg_v2022a
    assert engine._serial_Lside_veg_v2022a.__module__ == engine.__name__
    assert pr._reference('Lside_veg_v2022a') is engine._serial_Lside_veg_v2022a
    assert patch_radiation.Lside_veg_v2022a.__module__ == pr.__name__


def test_signature_compatible_call_styles(counter_delta):
    """Keyword and positional callers bind to the same certified domain."""
    case = make_case()
    positional = engine.Lside_veg_v2022a(*args_of(case))
    keyword = engine.Lside_veg_v2022a(**case)
    assert bitwise(positional, keyword)
    assert counter_delta() == {'primary': 2, 'reference': 0}
