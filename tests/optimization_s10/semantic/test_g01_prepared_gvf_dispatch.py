"""G01: prepared GVF route at one thread, plus the Tgwall U-profile admission.

The C6-30 differentials already prove prepared_gvf_step bitwise against both
the fused baseline and the verbatim original engine body for
parallel=[False, True]; these tests cover the S10 dispatch change (engine
routes the threads==1 path through the prepared route with the serial gather,
delegating unsupported inputs to the exact H=1 baseline) and the _admits
extension that admits size-one arrays of any float dtype (S10 T01 U profile;
the production landcover Tgwall is (1,1) float64).
"""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

_SPEC = importlib.util.spec_from_file_location(
    'gvf_prepare_cases',
    Path(__file__).resolve().parents[3] / 'tests/optimization_v6/gvf_prepare/gvf_prepare_cases.py')
_CASES = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_CASES)
build_scene = _CASES.build_scene
call_original = _CASES.call_original
snapshots = _CASES.snapshots


@pytest.fixture
def one_thread(monkeypatch):
    from solweig_light.runtime import runtime_options
    with runtime_options(threads_per_worker=1):
        yield


def routes(monkeypatch):
    """Install call counters on the prepared route and the serial baseline."""
    from solweig_light.radiation import gvf_prepared
    import solweig_light.radiation.ground_view as ground_view
    counts = {'prepared': 0, 'serial': 0, 'fused': 0}
    real_prepared, real_serial = gvf_prepared.prepared_gvf_step, ground_view.gvf_2018a

    def counted_prepared(*args, **kwargs):
        counts['prepared'] += 1
        return real_prepared(*args, **kwargs)

    def counted_serial(*args, **kwargs):
        counts['serial'] += 1
        return real_serial(*args, **kwargs)

    monkeypatch.setattr(gvf_prepared, 'prepared_gvf_step', counted_prepared)
    # engine.gvf_2018a resolves its delegate by in-function import from the
    # ground_view module, so patch there.
    import solweig_light.radiation.ground_view as gv_module
    monkeypatch.setattr(gv_module, 'gvf_2018a', counted_serial)
    return counts


def call_engine(scene):
    from solweig_light.radiation import engine
    local = snapshots(scene)
    with np.errstate(invalid='ignore', divide='ignore'):
        outputs = engine.gvf_2018a(**local)
    return outputs, local['Tg']


def test_u64_tgwall_prepared_at_one_thread_bitwise(one_thread):
    """(1,1) float64 Tgwall takes the prepared route and matches the original."""
    scene = build_scene(33, 21, seed=3, water=True)
    scene['Tgwall'] = np.array([[21.0]], dtype=np.float64)
    oracle, oracle_Tg = call_original(scene)
    actual, actual_Tg = call_engine(scene)
    _CASES.assert_exact(actual_Tg, oracle_Tg, 'Tg after the call')
    _CASES.assert_gvf_outputs(actual, oracle)


@pytest.mark.parametrize('shape', [(1,), (1, 1)])
@pytest.mark.parametrize('dtype', [np.float32, np.float64])
def test_u_profiles_route_prepared(one_thread, monkeypatch, shape, dtype):
    counts = routes(monkeypatch)
    scene = build_scene(16, 16, seed=2)
    scene['Tgwall'] = np.array(21.0, dtype=dtype).reshape(shape)
    call_engine(scene)
    assert counts['prepared'] == 1 and counts['serial'] == 0


def test_multielement_f32_tgwall_still_prepared(one_thread, monkeypatch):
    """The pre-existing multi-element float32 admission is unchanged."""
    counts = routes(monkeypatch)
    scene = build_scene(16, 16, seed=1)
    scene['Tgwall'] = np.full((16, 16), 21.0, dtype=np.float32)
    call_engine(scene)
    assert counts['prepared'] == 1 and counts['serial'] == 0


def test_multielement_f64_tgwall_delegates_to_baseline(one_thread, monkeypatch):
    """A spatially varying float64 field stays on the exact H=1 baseline."""
    counts = routes(monkeypatch)
    scene = build_scene(16, 16, seed=4)
    scene['Tgwall'] = (np.random.default_rng(5).random((16, 16)) * 4 + 19).astype(np.float64)
    outputs, Tg = call_engine(scene)
    assert counts['prepared'] == 1 and counts['serial'] == 1  # via delegate
    oracle, oracle_Tg = call_original(scene)
    _CASES.assert_exact(Tg, oracle_Tg, 'delegated Tg')
    _CASES.assert_gvf_outputs(outputs, oracle)


def test_kill_switch_routes_serial_at_one_thread(one_thread, monkeypatch):
    """SOLWEIG_LIGHT_GVF_PREPARE=0 restores the exact H=1 baseline."""
    from solweig_light.radiation import gvf_prepared
    monkeypatch.setattr(gvf_prepared, 'prepared_enabled', lambda: False)
    counts = routes(monkeypatch)
    scene = build_scene(16, 16, seed=2)
    scene['Tgwall'] = np.array([[21.0]], dtype=np.float64)
    outputs, Tg = call_engine(scene)
    assert counts['prepared'] == 1 and counts['serial'] == 1  # via delegate
    oracle, oracle_Tg = call_original(scene)
    _CASES.assert_exact(Tg, oracle_Tg, 'kill-switch Tg')
    _CASES.assert_gvf_outputs(outputs, oracle)


def test_multi_thread_dispatch_unchanged(monkeypatch):
    """threads>1 keeps the C6-30 parallel prepared route (regression guard)."""
    from solweig_light.runtime import runtime_options
    counts = routes(monkeypatch)
    with runtime_options(threads_per_worker=2, cpu_budget=2):
        scene = build_scene(16, 16, seed=2)
        scene['Tgwall'] = np.array([[21.0]], dtype=np.float64)
        call_engine(scene)
    assert counts['prepared'] == 1 and counts['serial'] == 0


def test_f64_tg_prepared_matches_original_bitwise(one_thread):
    """G02: production landcover profile (float64 Tg) — the prepared route is
    bitwise-equal to the verbatim original engine body, Tg state included."""
    for water, with_buildings in ((False, True), (True, True), (True, False)):
        scene = build_scene(33, 21, seed=3 + water + 2 * with_buildings,
                            water=water, with_buildings=with_buildings)
        scene['Tg'] = scene['Tg'].astype(np.float64)
        oracle, oracle_Tg = call_original(scene)
        actual, actual_Tg = call_engine(scene)
        _CASES.assert_exact(actual_Tg, oracle_Tg, f'Tg water={water} built={with_buildings}')
        _CASES.assert_gvf_outputs(actual, oracle)


def test_f32_tg_still_prepared(one_thread, monkeypatch):
    """The pre-existing float32-Tg admission is unchanged by G02."""
    counts = routes(monkeypatch)
    scene = build_scene(16, 16, seed=2)
    call_engine(scene)
    assert counts['prepared'] == 1 and counts['serial'] == 0


@pytest.mark.parametrize('bad', [np.float16, np.int32])
def test_unsupported_tg_dtype_delegates(one_thread, monkeypatch, bad):
    counts = routes(monkeypatch)
    scene = build_scene(16, 16, seed=2)
    scene['Tg'] = scene['Tg'].astype(bad)
    outputs, Tg = call_engine(scene)
    assert counts['prepared'] == 1 and counts['serial'] == 1
    oracle, oracle_Tg = call_original(scene)
    _CASES.assert_exact(Tg, oracle_Tg, 'delegated Tg')
    _CASES.assert_gvf_outputs(outputs, oracle)


def test_f64_tg_multi_thread_prepared(monkeypatch):
    """G02 also unlocks the compiled route at threads>1 on landcover scenes."""
    from solweig_light.runtime import runtime_options
    counts = routes(monkeypatch)
    with runtime_options(threads_per_worker=2, cpu_budget=2):
        scene = build_scene(16, 16, seed=2)
        scene['Tg'] = scene['Tg'].astype(np.float64)
        call_engine(scene)
    assert counts['prepared'] == 1 and counts['serial'] == 0
