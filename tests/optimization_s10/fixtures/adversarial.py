"""S10-14: adversarial input/profile fixtures for the admitted S10 routes.

Disclosure (VALIDATION_POLICY verification boundary): all fixture INPUTS here
are synthetic, generated inline with seeded ``numpy.random.default_rng``
generators — candidate-generated inputs with disclosed generation. Expected
traces are NEVER produced by the code under test: oracles are either the
original serial source (``patch_radiation._reference`` and the verbatim
pre-optimization ``engine.gvf_2018a_numpy`` body, "original_source") or
mathematical invariance identities over typed wrappers ("invariance_identity":
the same logical value in different dtype/rank wrappers must give identical
bits where the route admits both). No numerical mocks; every probe compares
real kernel execution.

Evidence class for every fixture: standalone_semantic_probe (these are L0/L1
probes; they are not SOLWEIG TIFF goldens and never stand in for them).

Warning-stream note: comparison across the numba JIT boundary asserts output
observables (nonfinite masks, frozen comparison_v1 budgets, bit traces).
Python warning-stream parity between the compiled primary and the reference
is outside the frozen standard every shipped kernel is qualified against
(comparison_v1 budgets; see evidence/t01_l1_kernel_differential.md) and is
deliberately not asserted here; both sides run under the same np.errstate.
"""
import importlib.util
import json
from pathlib import Path

import numpy as np

_TESTS = Path(__file__).resolve().parents[3]  # repository root

_SPEC = importlib.util.spec_from_file_location(
    'v6_cylinder_lw_conftest',
    _TESTS / 'tests/optimization_v6/cylinder_lw/conftest.py')
_V6 = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_V6)

_GVF_SPEC = importlib.util.spec_from_file_location(
    'gvf_prepare_cases',
    _TESTS / 'tests/optimization_v6/gvf_prepare/gvf_prepare_cases.py')
_CASES = importlib.util.module_from_spec(_GVF_SPEC)
_GVF_SPEC.loader.exec_module(_CASES)

# Reuse the C6-21 builders and the T01 engine-order dpc bundle so the fixture
# set cannot drift from the already-reviewed argument encodings.
lcyl_arguments = _V6.lcyl_arguments
bitwise_equal = _V6.bitwise_equal


def _load_t01():
    spec = importlib.util.spec_from_file_location(
        's10_t01_admission',
        _TESTS / 'tests/optimization_s10/semantic/test_t01_tgwall_admission.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dpc_arguments(rng, tgwall):
    """Engine-order dpc argument bundle (delegates to the T01 encoding)."""
    return _T01.dpc_arguments(rng, tgwall)


_T01 = _load_t01()


# ---------------------------------------------------------------------------
# Typed-wrapper category builders (SEMANTIC_CONTRACT typed operation graph):
# one logical value, five wrapper classes on the admitted scalar/U boundary.
# ---------------------------------------------------------------------------

def category_python_float(value, dtype=np.float64):
    return float(value)


def category_np_scalar(value, dtype=np.float64):
    return dtype(value)


def category_ndarray_0d(value, dtype=np.float64):
    return np.array(value, dtype=dtype)


def category_singleton_1d(value, dtype=np.float64):
    return np.array([value], dtype=dtype)


def category_singleton_2d(value, dtype=np.float64):
    return np.array([[value]], dtype=dtype)


# The route admits python floats, numpy scalars, 0-d and size-one arrays of
# either float dtype (patch_radiation._is_singleton; T01 admission). The
# empty and multi-element decline classes live in the T01 decline matrix.
ADMITTED_CATEGORIES = {
    'python_float_f64': category_python_float,
    'np_scalar_f64': category_np_scalar,
    'ndarray_0d_f64': category_ndarray_0d,
    'singleton_1d_f64': category_singleton_1d,
    'singleton_2d_f64': category_singleton_2d,
}

NONFINITE_KINDS = ('nan', 'posinf', 'neginf')
NONFINITE_VALUES = {'nan': np.nan, 'posinf': np.inf, 'neginf': -np.inf,
                    'signed_zero': -0.0}


def nonfinite_field(rng, shape, kind, dtype=np.float32, stride=11):
    """A field with the nonfinite payload laid on a stride over a finite base."""
    field = rng.random(shape).astype(dtype)
    flat = field.reshape(-1)
    flat[1::stride] = dtype(NONFINITE_VALUES[kind])
    return field


def snapshot_arguments(arguments):
    """Bitwise copies of every ndarray argument (caller-mutation observable)."""
    return {key: (np.array(value, copy=True) if isinstance(value, np.ndarray) else value)
            for key, value in arguments.items()}


def assert_inputs_unmutated(before, after):
    for key, value in before.items():
        if isinstance(value, np.ndarray):
            assert np.array_equal(value.view(np.uint32) if value.dtype.kind == 'f'
                                  else value,
                                  after[key].view(np.uint32) if value.dtype.kind == 'f'
                                  else after[key]), f'caller input mutated: {key}'


# ---------------------------------------------------------------------------
# Fixture registry — single source for tests/optimization_s10/fixtures/
# fixture_manifest.json. test_manifest_matches_registry fails if the
# checked-in manifest drifts from this registry.
# ---------------------------------------------------------------------------

FIXTURES = [
    {
        'id': 'lcyl_category_invariance',
        'route': 'patch_radiation.Lcyl_v2022a (primary)',
        'input_axis': 'Tgwall typed wrappers; bit-identity set = ndarray scalar/0-d/(1,)/(1,1) (f32/f64); python float admitted but budget-only (singleton identity is not scalar equivalence — observed 1-ulp boundary)',
        'oracle': 'original_source (patch_radiation._reference(Lcyl_v2022a)) + invariance_identity (pairwise bit-equality across the ndarray wrapper set)',
        'expectation_source': 'original_source|invariance_identity',
        'evidence_class': 'standalone_semantic_probe',
        'test': 'test_lcyl_category_invariance',
    },
    {
        'id': 'dpc_category_invariance',
        'route': 'patch_radiation.define_patch_characteristics (primary)',
        'input_axis': 'Tgwall typed wrappers: ndarray scalar/0-d/(1,)/(1,1) bit-identity set vs python float (budget-only)',
        'oracle': 'original_source + invariance_identity over the ndarray wrapper set',
        'expectation_source': 'original_source|invariance_identity',
        'evidence_class': 'standalone_semantic_probe',
        'test': 'test_dpc_category_invariance',
    },
    {
        'id': 'lcyl_nonfinite_u_route',
        'route': 'patch_radiation.Lcyl_v2022a (primary, admitted U route)',
        'input_axis': 'NaN/+Inf/-Inf injected into Tgwall (U), Ta (scalar), Lup (field), f32',
        'oracle': 'original_source; nonfinite-mask equality + frozen comparison_v1 budgets on finite values',
        'expectation_source': 'original_source',
        'evidence_class': 'standalone_semantic_probe',
        'test': 'test_lcyl_nonfinite_u_route',
    },
    {
        'id': 'lcyl_signed_zero',
        'route': 'patch_radiation.Lcyl_v2022a (primary)',
        'input_axis': 'Tgwall = -0.0 vs +0.0',
        'oracle': 'original_source; signbit vectors equal per field; +/-0.0 difference masks equal between candidate and reference',
        'expectation_source': 'original_source|invariance_identity',
        'evidence_class': 'standalone_semantic_probe',
        'test': 'test_lcyl_signed_zero_trace',
    },
    {
        'id': 'lcyl_input_purity_and_alias',
        'route': 'patch_radiation.Lcyl_v2022a (primary)',
        'input_axis': 'caller-buffer mutation check; shmat/vegshmat/vbshvegshmat aliasing one base buffer',
        'oracle': 'invariance_identity (aliased call bit-equal to distinct-buffer call) + original_source budgets',
        'expectation_source': 'invariance_identity|original_source',
        'evidence_class': 'standalone_semantic_probe',
        'test': 'test_lcyl_input_purity_and_alias',
    },
    {
        'id': 'gvf_tg_lcgrid_alias',
        'route': 'engine.gvf_2018a dispatch (prepared route guard union)',
        'input_axis': 'Tg aliasing lc_grid (the C6-30 stronger-hoist exclusion)',
        'oracle': 'original_source (engine.gvf_2018a_numpy), bitwise incl. Tg caller state',
        'expectation_source': 'original_source',
        'evidence_class': 'standalone_semantic_probe',
        'test': 'test_gvf_tg_lcgrid_alias_keeps_exact_route',
    },
    {
        'id': 'gvf_mutation_epoch',
        'route': 'engine.gvf_2018a dispatch (prepared route)',
        'input_axis': 'in-place Tg and lc_grid mutation between two calls (no state survives a call)',
        'oracle': 'original_source, bitwise, fresh call per value',
        'expectation_source': 'original_source',
        'evidence_class': 'standalone_semantic_probe',
        'test': 'test_gvf_mutation_epoch',
    },
    {
        'id': 'gvf_nonfinite_tg',
        'route': 'engine.gvf_2018a dispatch (prepared route, f64 Tg production profile)',
        'input_axis': 'NaN/+Inf payloads laid on strides over Tg; water mutation path active',
        'oracle': 'original_source, bitwise uint64 views incl. payload positions',
        'expectation_source': 'original_source',
        'evidence_class': 'standalone_semantic_probe',
        'test': 'test_gvf_nonfinite_tg_bitwise',
    },
    {
        'id': 'anilum_nonfinite_payloads',
        'route': 'patch_radiation.anilum_packed (R03)',
        'input_axis': 'raw-mode NaN/-0.0/Inf uint32 payloads; ternary decline',
        'oracle': 'covered_elsewhere: tests/optimization_s10/semantic/test_r03_anilum_packed.py (uint32-view equality against the verbatim retained loop)',
        'expectation_source': 'transcribed_expression (retained engine loop)',
        'evidence_class': 'standalone_semantic_probe',
        'test': None,
    },
]


def manifest():
    return {
        'packet_task': 'S10-14',
        'disclosure': (
            'Synthetic seeded-rng inputs (candidate-generated, disclosed). '
            'Expected traces from the original serial source or mathematical '
            'invariance identities only; no candidate-generated expectations; '
            'no numerical mocks. Evidence class: standalone_semantic_probe.'),
        'fixtures': FIXTURES,
    }


def write_manifest(path):
    Path(path).write_text(json.dumps(manifest(), indent=2) + '\n')
