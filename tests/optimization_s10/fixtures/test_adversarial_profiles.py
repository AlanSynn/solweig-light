"""S10-14: adversarial scalar/U/F/nonfinite/alias probes over the admitted S10 routes.

Every expected trace comes from the original serial source or from a stated
invariance identity — never from the candidate path (see adversarial.py for
the disclosure). The fixture manifest in this directory is generated from
adversarial.FIXTURES; test_manifest_matches_registry pins it against drift.
"""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

_SPEC = importlib.util.spec_from_file_location(
    's10_adversarial',
    Path(__file__).resolve().parent / 'adversarial.py')
adv = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(adv)

from solweig_light.radiation import engine, patch_radiation

LCYL_FIELDS = ('Ldown', 'Lside', 'Least_', 'Lwest_', 'Lnorth_', 'Lsouth_')
PROTOCOL = json.loads((Path(__file__).resolve().parents[3] /
                       'tests/reference/contracts/comparison_v1.json').read_text())


def within_budget(function_field, actual, expected):
    rule = PROTOCOL['field_rules'][function_field]
    actual, expected = np.asarray(actual), np.asarray(expected)
    for mask in (np.isnan, np.isposinf, np.isneginf):
        np.testing.assert_array_equal(mask(actual), mask(expected))
    np.testing.assert_allclose(actual, expected, atol=rule.get('atol', rule.get('max_abs', 0)),
                               rtol=rule.get('rtol', 0), err_msg=function_field)


def counters():
    return dict(patch_radiation.ROUTE_COUNTS)


@pytest.fixture
def rng():
    return np.random.default_rng(1407)


# ---------------------------------------------------------------------------
# manifest integrity
# ---------------------------------------------------------------------------

def test_manifest_matches_registry():
    manifest = json.loads((Path(__file__).resolve().parent / 'fixture_manifest.json').read_text())
    assert manifest['fixtures'] == adv.FIXTURES
    declared = {entry['test'] for entry in manifest['fixtures'] if entry['test']}
    assert declared <= set(globals()), f'manifest names missing tests: {declared - set(globals())}'
    assert all(entry['evidence_class'] == 'standalone_semantic_probe'
               for entry in manifest['fixtures'])


# ---------------------------------------------------------------------------
# typed-wrapper category invariance (scalar / 0-d / U)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('dtype', [np.float32, np.float64])
def test_lcyl_category_invariance(rng, dtype):
    """One logical Tgwall value across the admitted typed wrappers.

    The ndarray wrapper classes (numpy scalar, 0-d, (1,), (1,1)) form the
    bit-identity set: pairwise bit-identical outputs, all inside the frozen
    budgets against the reference. A *python float* Tgwall is admitted and
    budget-qualified but is NOT in the bit-identity set — the observed
    singleton-identity boundary (the SEMANTIC_CONTRACT caveat, live): only
    ndarray wrappers share one extracted-value arithmetic."""
    wrappers = {
        'np_scalar': lambda v: adv.category_np_scalar(v, dtype),
        'ndarray_0d': lambda v: adv.category_ndarray_0d(v, dtype),
        'singleton_1d': lambda v: adv.category_singleton_1d(v, dtype),
        'singleton_2d': lambda v: adv.category_singleton_2d(v, dtype),
    }
    outputs = {}
    base = adv.lcyl_arguments(rng, Tgwall=np.float64(15.0))
    for name, wrapper in wrappers.items():
        arguments = dict(base, Tgwall=wrapper(15.0))
        before = counters()
        outputs[name] = patch_radiation.Lcyl_v2022a(**arguments)
        after = counters()
        assert after['Lcyl_v2022a_primary'] - before['Lcyl_v2022a_primary'] == 1
        reference = patch_radiation._reference('Lcyl_v2022a')(**arguments)
        for name_field, field in zip(LCYL_FIELDS, outputs[name]):
            within_budget(f'Lcyl_v2022a/{name_field}', field, reference[LCYL_FIELDS.index(name_field)])
    values = list(outputs.values())
    for other in values[1:]:
        for field, rest in zip(values[0], other):
            assert adv.bitwise_equal(field, rest)
    # python float: same primary route, budget-qualified, not bit-claimed.
    arguments = dict(base, Tgwall=adv.category_python_float(15.0))
    before = counters()
    python_float_output = patch_radiation.Lcyl_v2022a(**arguments)
    after = counters()
    assert after['Lcyl_v2022a_primary'] - before['Lcyl_v2022a_primary'] == 1
    reference = patch_radiation._reference('Lcyl_v2022a')(**arguments)
    for name_field, field in zip(LCYL_FIELDS, python_float_output):
        within_budget(f'Lcyl_v2022a/{name_field}', field, reference[LCYL_FIELDS.index(name_field)])


def test_dpc_category_invariance(rng):
    """The dpc primary shows the same wrapper partition on its Tgwall input:
    ndarray wrappers bit-identical, python float budget-only."""
    outputs = {}
    base = adv.dpc_arguments(rng, np.float64(12.7))
    for name, build in adv.ADMITTED_CATEGORIES.items():
        arguments = list(base)
        arguments[14] = build(12.7)
        before = counters()
        outputs[name] = patch_radiation.define_patch_characteristics(*arguments)
        after = counters()
        assert (after['define_patch_characteristics_primary']
                - before['define_patch_characteristics_primary']) == 1
    ndarray_names = [n for n in outputs if n != 'python_float_f64']
    for name in ndarray_names[1:]:
        for field, rest in zip(outputs[ndarray_names[0]], outputs[name]):
            assert adv.bitwise_equal(field, rest)


# ---------------------------------------------------------------------------
# nonfinite propagation on the admitted U route
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('kind', adv.NONFINITE_KINDS)
@pytest.mark.parametrize('target', ['Tgwall', 'Ta', 'Lup'])
def test_lcyl_nonfinite_u_route(rng, kind, target):
    """NaN/+Inf/-Inf on the admitted route: masks equal to the reference,
    finite parts inside the frozen budgets; admission stays value-blind."""
    if target == 'Tgwall':
        override = {target: adv.category_singleton_2d(adv.NONFINITE_VALUES[kind], np.float32)}
    elif target == 'Ta':
        override = {target: np.array(adv.NONFINITE_VALUES[kind], dtype=np.float32)}
    else:
        override = {target: adv.nonfinite_field(rng, (16, 16), kind)}
    arguments = adv.lcyl_arguments(rng, **override)
    reference = patch_radiation._reference('Lcyl_v2022a')(**arguments)
    before = counters()
    output = patch_radiation.Lcyl_v2022a(**arguments)
    after = counters()
    assert after['Lcyl_v2022a_primary'] - before['Lcyl_v2022a_primary'] == 1
    for name, field in zip(LCYL_FIELDS, output):
        within_budget(f'Lcyl_v2022a/{name}', field, reference[LCYL_FIELDS.index(name)])


def test_lcyl_signed_zero_trace(rng):
    """-0.0 vs +0.0 Tgwall: the candidate's signbit pattern matches the
    reference's on every field, and the +/-0.0 difference masks agree —
    signed zero survives the admitted route exactly as the original says."""
    def run(value):
        arguments = adv.lcyl_arguments(rng, Tgwall=adv.category_singleton_2d(value, np.float32))
        return (patch_radiation._reference('Lcyl_v2022a')(**arguments),
                patch_radiation.Lcyl_v2022a(**arguments))
    (neg_ref, neg_cand) = run(-0.0)
    (pos_ref, pos_cand) = run(0.0)
    for index, name in enumerate(LCYL_FIELDS):
        np.testing.assert_array_equal(np.signbit(np.asarray(neg_cand[index])),
                                      np.signbit(np.asarray(neg_ref[index])),
                                      err_msg=f'signbit {name}')
        np.testing.assert_array_equal(np.signbit(neg_cand[index]) ^ np.signbit(pos_cand[index]),
                                      np.signbit(neg_ref[index]) ^ np.signbit(pos_ref[index]),
                                      err_msg=f'+/-0 difference mask {name}')


# ---------------------------------------------------------------------------
# caller-buffer purity and operand aliasing
# ---------------------------------------------------------------------------

def test_lcyl_input_purity_and_alias(rng):
    """The primary must not mutate caller buffers, and shadow-matrix aliasing
    must be invisible: with identical contents in distinct buffers vs one
    shared buffer, outputs are bit-identical and match the reference."""
    arguments = adv.lcyl_arguments(rng, Tgwall=adv.category_singleton_2d(15.0, np.float32))
    before = adv.snapshot_arguments(arguments)
    distinct = patch_radiation.Lcyl_v2022a(**arguments)
    adv.assert_inputs_unmutated(before, arguments)

    shared = arguments['shmat']
    # Equal-content distinct buffers first, so the only difference in the
    # aliased call is the binding, not the values.
    equal_content = dict(arguments, vegshmat=shared.copy(), vbshvegshmat=shared.copy())
    distinct = patch_radiation.Lcyl_v2022a(**equal_content)
    aliased = patch_radiation.Lcyl_v2022a(**dict(equal_content,
                                                 vegshmat=shared, vbshvegshmat=shared))
    for field, rest in zip(distinct, aliased):
        assert adv.bitwise_equal(field, rest)
    reference = patch_radiation._reference('Lcyl_v2022a')(**equal_content)
    for name, field in zip(LCYL_FIELDS, aliased):
        within_budget(f'Lcyl_v2022a/{name}', field, reference[LCYL_FIELDS.index(name)])


# ---------------------------------------------------------------------------
# prepared-GVF route: alias exclusion, mutation epoch, nonfinite payloads
# ---------------------------------------------------------------------------

@pytest.fixture
def one_thread():
    from solweig_light.runtime import runtime_options
    with runtime_options(threads_per_worker=1):
        yield


def _call_engine(scene):
    from solweig_light.radiation import engine
    local = adv._CASES.snapshots(scene)
    with np.errstate(invalid='ignore', divide='ignore'):
        outputs = engine.gvf_2018a(**local)
    return outputs, local['Tg']


def test_gvf_tg_lcgrid_alias_keeps_exact_route(one_thread, monkeypatch):
    """Tg aliasing lc_grid is the C6-30 exclusion: the prepared guard must
    delegate, and the result must stay bitwise against the original body."""
    from solweig_light.radiation import gvf_prepared
    import solweig_light.radiation.ground_view as ground_view
    counts = {'prepared': 0, 'serial': 0}
    real_prepared, real_serial = gvf_prepared.prepared_gvf_step, ground_view.gvf_2018a

    def counted_prepared(*args, **kwargs):
        counts['prepared'] += 1
        return real_prepared(*args, **kwargs)

    def counted_serial(*args, **kwargs):
        counts['serial'] += 1
        return real_serial(*args, **kwargs)

    monkeypatch.setattr(gvf_prepared, 'prepared_gvf_step', counted_prepared)
    # engine.gvf_2018a resolves its delegate by in-function import, so patch
    # the ground_view module attribute (same seam as the G01 dispatch tests).
    monkeypatch.setattr(ground_view, 'gvf_2018a', counted_serial)

    scene = adv._CASES.build_scene(16, 16, seed=6, water=True)
    scene['Tg'] = scene['Tg'].astype(np.float64)
    scene['Tgwall'] = np.array([[21.0]], dtype=np.float64)
    # Alias the buffers in the CALL arguments: _call_engine snapshots the
    # scene dict, which would silently copy the alias away. The oracle
    # reproduces the identical aliased binding over the original body —
    # alias-visibility, not content equality.
    local = adv._CASES.snapshots(scene)
    local['lc_grid'] = local['Tg']  # the excluded alias
    assert np.shares_memory(local['Tg'], local['lc_grid'])
    with np.errstate(invalid='ignore', divide='ignore'):
        outputs = engine.gvf_2018a(**local)
    assert counts['prepared'] == 1 and counts['serial'] == 1  # delegated, not snapshotted
    oracle_local = adv._CASES.snapshots(scene)
    oracle_local['lc_grid'] = oracle_local['Tg']
    with np.errstate(invalid='ignore', divide='ignore'):
        oracle = engine.gvf_2018a_numpy(**oracle_local)
    adv._CASES.assert_exact(local['Tg'], oracle_local['Tg'], 'aliased Tg state')
    adv._CASES.assert_gvf_outputs(outputs, oracle)


def test_gvf_mutation_epoch(one_thread):
    """Nothing survives a prepared call: mutating Tg (and lc_grid) in place
    between calls gives exactly the fresh calls' results."""
    scene = adv._CASES.build_scene(33, 21, seed=7, water=True)
    scene['Tg'] = scene['Tg'].astype(np.float64)
    first, first_Tg = _call_engine(scene)
    first_oracle, first_oracle_Tg = adv._CASES.call_original(scene)
    adv._CASES.assert_exact(first_Tg, first_oracle_Tg, 'first-call Tg')
    adv._CASES.assert_gvf_outputs(first, first_oracle)

    scene['Tg'] += np.float64(1.5)          # in-place caller mutation
    scene['lc_grid'][0, 0] = 3              # landcover class flip
    second, second_Tg = _call_engine(scene)
    second_oracle, second_oracle_Tg = adv._CASES.call_original(scene)
    adv._CASES.assert_exact(second_Tg, second_oracle_Tg, 'mutated-epoch Tg')
    adv._CASES.assert_gvf_outputs(second, second_oracle)


def test_gvf_nonfinite_tg_bitwise(one_thread):
    """NaN/+Inf payloads over the f64 production Tg profile: the prepared
    route stays bitwise against the original, payload positions included."""
    for kind in adv.NONFINITE_KINDS:
        scene = adv._CASES.build_scene(33, 21, seed=8, water=True)
        scene['Tg'] = scene['Tg'].astype(np.float64)
        scene['Tg'].reshape(-1)[1::17] = np.float64(adv.NONFINITE_VALUES[kind])
        outputs, Tg = _call_engine(scene)
        oracle, oracle_Tg = adv._CASES.call_original(scene)
        adv._CASES.assert_exact(Tg, oracle_Tg, f'Tg after {kind} poison')
        adv._CASES.assert_gvf_outputs(outputs, oracle)
