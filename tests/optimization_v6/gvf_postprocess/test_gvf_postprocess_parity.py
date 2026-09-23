"""C6-31 L1 differentials: typed GVF block postprocess vs the untouched
ground_view._postprocess_block (base 5e1fab46).

All comparisons are bitwise (uint32 views catch NaN payloads and signed
zeros). The original runs on views of a pristine block; the candidate runs on
a bit-identical copy; the in-place receiver-plane mutations of both are
compared plane by plane, and the planes the original never mutates must be
bit-identical to their incoming values after the candidate call.
"""
import warnings

import numpy as np
import pytest

from solweig_light.radiation.ground_view import _postprocess_block
from solweig_light.radiation.gvf_postprocess import (
    DEBUG_NODES,
    _postprocess_block_debug,
    gvf_postprocess_block,
)

import _cases as cases

PARAM_SIZES = (16, 64, 128)
SMALL_SIZES = (16, 17)  # 17 exercises a non-multiple block shape


def run_original(case, n):
    block = case['block'].copy()
    planes = tuple(block[index] for index in range(16))
    outputs = _postprocess_block(planes, case['buildings'], case['facesh'],
                                 case['lup_term'], case['alb_term'], case['nosh_term'],
                                 case['first'], case['second'])
    return block, outputs


def run_candidate(case, n, parallel=False):
    block = case['block'].copy()
    outputs = gvf_postprocess_block(block, case['buildings'], case['facesh'],
                                    case['lup_term'], case['alb_term'], case['nosh_term'],
                                    case['first'], case['second'], parallel=parallel)
    return block, outputs


def assert_calls_match(case, n, parallel=False):
    original_block, original = run_original(case, n)
    candidate_block, candidate = run_candidate(case, n, parallel=parallel)
    for index, (left, right) in enumerate(zip(original, candidate)):
        assert isinstance(right, np.ndarray) and right.dtype == np.float32
        assert right.shape == (n, n)
        assert cases.bits_equal(left, right), f'output {index} differs'
    for index in range(16):
        left = original_block[index]
        right = candidate_block[index]
        assert cases.bits_equal(left, right), f'mutated plane {index} differs'
        if index not in cases.MUTATED_PLANES:
            assert cases.bits_equal(right, case['block'][index]), \
                f'plane {index} must be untouched by the candidate'
    return original, candidate


@pytest.mark.parametrize('n', PARAM_SIZES)
@pytest.mark.parametrize('builder', cases.ALL_CASES, ids=lambda b: b.__name__)
def test_original_matches_replica(builder, n):
    """Validates the node inventory: the statement-by-statement replica must
    reproduce the untouched original bitwise before it may judge the kernel."""
    case = builder(n)
    original_block, original = run_original(case, n)
    planes = tuple(case['block'][index].copy() for index in range(16))
    replica, _ = cases.replica_postprocess(planes, case['buildings'], case['facesh'],
                                           case['lup_term'], case['alb_term'], case['nosh_term'],
                                           case['first'], case['second'])
    for index, (left, right) in enumerate(zip(original, replica)):
        assert cases.bits_equal(left, right), f'replica output {index} differs'
    for index in range(16):
        assert cases.bits_equal(original_block[index], planes[index]), \
            f'replica mutated plane {index} differs'


@pytest.mark.parametrize('n', PARAM_SIZES)
@pytest.mark.parametrize('builder', cases.ALL_CASES, ids=lambda b: b.__name__)
def test_bitwise_parity(builder, n):
    assert_calls_match(builder(n), n)


@pytest.mark.parametrize('n', SMALL_SIZES)
def test_bitwise_parity_nonmultiple_block(n):
    assert_calls_match(cases.case_random(n, seed=101), n)


@pytest.mark.parametrize('steps', [
    (1, np.float64(1.0)),                # clamped python-int first
    (np.float64(3.0), np.float64(2.0)),  # production float64 0-d
    (np.float32(2.0), np.float32(1.0)),  # float32 0-d
    (2.0, 1.0),                          # plain python floats
    (0.5, 1.0),                          # non-integer -> reference route
    (np.float64(2.0 ** 24), np.float64(1.0)),  # >= 2**24 -> reference route
    (np.float64(-1.0), np.float64(1.0)),       # negative -> reference route
    (np.float64(np.nan), np.float64(1.0)),     # nonfinite -> reference route
    (np.float64(3.0), np.float64(0.5)),        # sub-unity second -> reference route
])
def test_step_domain_parity(steps):
    first, second = steps
    case = cases.case_random(16, seed=7)
    case['first'], case['second'] = first, second
    assert_calls_match(case, 16)


@pytest.mark.parametrize('builder', cases.WARN_CASES, ids=lambda b: b.__name__)
def test_warning_parity(builder):
    """The candidate must fire the identical warnings as the original (the
    silent fast path would be a contract break on these inputs)."""
    n = 16
    case = builder(n)

    def collect(call):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            call()
        return sorted((type(item).__name__, str(item.message)) for item in caught)

    original_warnings = collect(lambda: run_original(case, n))
    candidate_warnings = collect(lambda: run_candidate(case, n))
    assert candidate_warnings, 'candidate must not silently swallow the warning'
    assert candidate_warnings == original_warnings


@pytest.mark.parametrize('builder', cases.CLEAN_CASES, ids=lambda b: b.__name__)
def test_clean_inputs_stay_silent(builder):
    """On inputs where the original cannot warn, the fast path must be quiet."""
    n = 16

    def collect(call):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            call()
        return list(caught)

    case = builder(n)
    assert collect(lambda: run_candidate(case, n)) == []
    assert collect(lambda: run_original(case, n)) == []


@pytest.mark.parametrize('builder', cases.WARN_CASES, ids=lambda b: b.__name__)
def test_errstate_raise_parity(builder):
    """Under np.errstate(all='raise') both paths raise the identical
    FloatingPointError and leave the caller's block in the identical state."""
    n = 16
    case = builder(n)

    def call_and_capture(call):
        block = case['block'].copy()
        with np.errstate(all='raise'):
            try:
                call(block)
                raised = None
            except FloatingPointError as error:
                raised = str(error)
        return raised, block

    def original_direct(block):
        planes = tuple(block[index] for index in range(16))
        _postprocess_block(planes, case['buildings'], case['facesh'],
                           case['lup_term'], case['alb_term'], case['nosh_term'],
                           case['first'], case['second'])

    def candidate_direct(block):
        gvf_postprocess_block(block, case['buildings'], case['facesh'],
                              case['lup_term'], case['alb_term'], case['nosh_term'],
                              case['first'], case['second'])

    original_message, original_state = call_and_capture(original_direct)
    candidate_message, candidate_state = call_and_capture(candidate_direct)
    assert original_message is not None, 'original must raise on this input'
    assert original_message == candidate_message
    for index in range(16):
        assert cases.bits_equal(original_state[index], candidate_state[index]), \
            f'post-raise plane {index} state differs'


def test_underflow_regime_contract():
    """Review C6-60 F1 scope pin: the kernel inspects result values, not the
    underflow flag. Under NumPy's DEFAULT regime both paths are silent and
    bitwise-equal on subnormal-underflow inputs. Under a non-default
    errstate(under='raise') the original raises FloatingPointError where the
    wrapper returns silently with bitwise-identical outputs. This asymmetry
    is documented in the module docstring and is not production-reachable
    (the engine runs the default regime)."""
    n = 16
    case = cases.case_underflow_subnormal(n)

    def collect(call):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            call()
        return sorted((type(item).__name__, str(item.message)) for item in caught)

    # Default regime: both silent, outputs and planes bitwise-equal.
    original_block, original = run_original(case, n)
    candidate_block, candidate = run_candidate(case, n)
    assert collect(lambda: run_original(case, n)) == []
    assert collect(lambda: run_candidate(case, n)) == []
    for index, (left, right) in enumerate(zip(original, candidate)):
        assert cases.bits_equal(left, right), f'output {index} differs'
    for index in range(16):
        assert cases.bits_equal(original_block[index], candidate_block[index])
    # The original did underflow here (guard against the case rotting into a
    # no-op): under errstate(under='raise') it must raise.
    with pytest.raises(FloatingPointError, match='underflow'):
        with np.errstate(all='raise'):
            run_original(case, n)
    # ...while the wrapper returns silently (documented carve-out), with
    # outputs bitwise-identical to the original's default-regime result.
    with np.errstate(all='raise'):
        raised_block, raised_candidate = run_candidate(case, n)
    for index, (left, right) in enumerate(zip(original, raised_candidate)):
        assert cases.bits_equal(left, right), f'output {index} differs'
    for index in range(16):
        assert cases.bits_equal(original_block[index], raised_block[index])


def test_boundary_requires_float32_block():
    """Review C6-60 F4: an out-of-contract dtype/shape must be refused loudly,
    not silently answered with float32 outputs."""
    case = cases.case_random(16)
    for mutate in (
        lambda b: b.astype(np.float64),
        lambda b: b[0],
        lambda b: b[:15],
    ):
        bad = mutate(case['block'].copy())
        with pytest.raises(TypeError, match='float32'):
            gvf_postprocess_block(bad, case['buildings'], case['facesh'],
                                  case['lup_term'], case['alb_term'], case['nosh_term'],
                                  case['first'], case['second'])
    # The admitted shape still works (sanity on the guard itself).
    run_candidate(case, 16)


@pytest.mark.parametrize('n', (16, 64))
@pytest.mark.parametrize('builder', cases.ALL_CASES, ids=lambda b: b.__name__)
def test_parallel_bitwise_parity(builder, n):
    """The prange variant is order-identical per element: bitwise parity with
    the original (and therefore with the serial kernel) on every case."""
    assert_calls_match(builder(n), n, parallel=True)


def test_parallel_matches_serial_bitwise():
    for builder, seed in ((cases.case_random, 5), (cases.case_boundary, 6)):
        case = builder(32)
        case['block'] = case['block'].copy()
        serial_block, serial = run_candidate(case, 32, parallel=False)
        parallel_block, parallel = run_candidate(case, 32, parallel=True)
        for left, right in zip(serial, parallel):
            assert cases.bits_equal(left, right)
        for index in range(16):
            assert cases.bits_equal(serial_block[index], parallel_block[index])


@pytest.mark.parametrize('n', PARAM_SIZES)
@pytest.mark.parametrize('builder', cases.CLEAN_CASES, ids=lambda b: b.__name__)
def test_debug_nodes_match_replica(builder, n):
    """Per-node proof: every comparison/keep/clamp node exported by the debug
    kernel is bit-identical to the replica's node, and the debug outputs match
    the original's (keeping the debug kernel itself honest)."""
    case = builder(n)
    original_block, original = run_original(case, n)
    planes = tuple(case['block'][index].copy() for index in range(16))
    replica, nodes = cases.replica_postprocess(planes, case['buildings'], case['facesh'],
                                               case['lup_term'], case['alb_term'], case['nosh_term'],
                                               case['first'], case['second'])
    kernel_block = case['block'].copy()
    kernel_out = _postprocess_block_debug(kernel_block, case['buildings'], case['facesh'],
                                          case['lup_term'], case['alb_term'], case['nosh_term'],
                                          float(case['first']), float(case['second']))
    debug_outputs = kernel_out[:5]
    exported = kernel_out[6]
    for index, (left, right) in enumerate(zip(original, debug_outputs)):
        assert cases.bits_equal(left, right), f'debug output {index} differs'
    for plane, (name, value) in enumerate(zip(DEBUG_NODES, nodes.values())):
        if name in ('eq_second', 'wallsuninfluence_first', 'wallinfluence_first',
                    'wallsuninfluence_second', 'wallinfluence_second',
                    'keep_mask', 'gvf2_clamp_mask'):
            expected = value.astype(np.float32)
        else:
            expected = value
        assert cases.bits_equal(exported[plane], expected.astype(np.float32)), \
            f'debug node {name} differs'


def test_clamp_boundary_exact_and_nextafter():
    """Order gate: gvf2 is clamped only after computation. A raw gvf2 of
    exactly 1.0 is kept; values above 1.0 (right down to one ulp) become
    exactly 1.0; the combine consumes the clamped value, which the output
    bits prove on a row whose unclamped gvf2 is far enough above 1.0 for the
    difference to survive rounding."""
    n = 4
    case = cases.case_boundary(n)
    case['block'] = case['block'].copy()
    # first/second = 1.0 -> d = f32(2.0). Rows: 0 raw==1.0 kept; 1 raw is
    # nextafter(1.0), clamped; 2 keep==1 zeroing band; 3 keep==-1 band.
    case['block'][9] = np.float32(0.5)
    case['block'][8] = np.float32(1.5)
    # row 3 becomes a clearly-above-1.0 clamp: raw gvf2 = 1 + 2**-19.
    case['block'][1, 3] = np.float32(0.5) + np.float32(2.0 ** -20)
    case['block'][0, 3] = np.float32(1.5)
    case['lup_term'] = np.zeros((n, n), dtype=np.float32)
    original_block, original = run_original(case, n)
    candidate_block, candidate = run_candidate(case, n)
    one = np.float32(1.0)
    # exact 1.0 survives unclamped in both (checked via the debug raw node on
    # the candidate side and via the gvf combine bits below).
    assert cases.bits_equal(original[4][0], np.full(n, one))
    assert cases.bits_equal(candidate[4][0], np.full(n, one))
    # nextafter(1.0) is clamped to exactly 1.0 in both
    assert cases.bits_equal(original[4][1], np.full(n, one))
    assert cases.bits_equal(candidate[4][1], np.full(n, one))
    # A clearly-above-1.0 raw value also clamps: gvf row 3 carries
    # (1.0*0.5 + 1.0*0.4)/0.9, not the unclamped (1+2**-19) combine.
    gvf1 = one  # (0.5 + 1.5)/f32(2.0) on the first planes
    expected = ((gvf1 * np.float32(0.5) + one * np.float32(0.4)) / np.float32(0.9)).astype(np.float32)
    raw_above = np.float32(1.0) + np.float32(2.0 ** -19)
    unclamped = ((gvf1 * np.float32(0.5) + raw_above * np.float32(0.4)) / np.float32(0.9)).astype(np.float32)
    assert not cases.bits_equal(expected, unclamped)
    assert cases.bits_equal(original[0][3], np.full(n, expected))
    assert cases.bits_equal(candidate[0][3], np.full(n, expected))


def test_influence_computed_before_zeroing():
    """Order gate: wallsuninfluence_second is the pre-zeroing comparison. With
    keep == 1 the plane is zeroed, and gvf2 must still use the influence flag
    from before the zeroing; the swapped order computes a different value."""
    n = 4
    case = cases.case_boundary(n)
    case['block'] = case['block'].copy()
    case['block'][1] = np.float32(1.0)  # == second, > 0 -> influence True
    case['block'][0] = np.float32(0.5)
    case['facesh'] = np.zeros((n, n), dtype=np.float32)  # keep = 1 -> zeroing
    case['lup_term'] = np.zeros((n, n), dtype=np.float32)
    case['alb_term'] = np.zeros((n, n), dtype=np.float32)
    case['nosh_term'] = np.zeros((n, n), dtype=np.float32)
    case['block'][9] = np.float32(0.0)
    case['block'][8] = np.float32(0.0)
    case['block'][11] = np.float32(0.0)
    case['block'][10] = np.float32(0.0)
    case['block'][13] = np.float32(0.0)
    case['block'][12] = np.float32(0.0)
    case['block'][15] = np.float32(0.0)
    case['block'][14] = np.float32(0.0)
    case['block'][7] = np.float32(0.0)
    case['block'][6] = np.float32(0.0)
    case['buildings'] = np.zeros((n, n), dtype=np.float32)
    original_block, original = run_original(case, n)
    candidate_block, candidate = run_candidate(case, n)
    # Zeroed plane: gvf2 = (0 + 0.5)/f32(2.0) * influence(True) = 0.25.
    expected_gvf2 = np.full((n, n), np.float32(0.25), dtype=np.float32)
    assert cases.bits_equal(original[4], expected_gvf2)
    assert cases.bits_equal(candidate[4], expected_gvf2)
    # The wrong order (influence from the zeroed plane) would give
    # 0.5/f32(1.0) * 1.0 = 0.5 and must NOT be what either produced.
    wrong_order = np.full((n, n), np.float32(0.5), dtype=np.float32)
    assert not cases.bits_equal(original[4], wrong_order)
    assert not cases.bits_equal(candidate[4], wrong_order)


def test_zeroing_applied_before_gvf2():
    """Order gate: weightsumwall[keep == 1] = 0 happens before gvf2 reads the
    plane; the swapped order computes a different value."""
    n = 4
    case = cases.case_boundary(n)
    case['block'] = case['block'].copy()
    case['block'][1] = np.float32(1.0)  # == second -> keep = 1 - 0 = 1
    case['block'][0] = np.float32(0.5)
    case['facesh'] = np.zeros((n, n), dtype=np.float32)
    for name in ('lup_term', 'alb_term', 'nosh_term'):
        case[name] = np.zeros((n, n), dtype=np.float32)
    for index in (9, 8, 11, 10, 13, 12, 15, 14, 7, 6, 5, 4, 3, 2):
        case['block'][index] = np.float32(0.0)
    case['buildings'] = np.zeros((n, n), dtype=np.float32)
    original_block, original = run_original(case, n)
    candidate_block, candidate = run_candidate(case, n)
    expected = np.full((n, n), np.float32(0.25), dtype=np.float32)  # (0+0.5)/2
    assert cases.bits_equal(original[4], expected)
    assert cases.bits_equal(candidate[4], expected)
    wrong_order = np.full((n, n), np.float32(0.75), dtype=np.float32)  # (1+0.5)/2
    assert not cases.bits_equal(original[4], wrong_order)
    assert not cases.bits_equal(candidate[4], wrong_order)


def test_untouched_planes_stay_pristine_on_fallback():
    """On the flagged (reference) route the three mutated planes must end in
    exactly the state the original leaves, and nothing else may move."""
    n = 16
    case = cases.case_overflow_clamp_hidden(n)
    assert_calls_match(case, n)


def test_one_wide_and_single_pixel_blocks():
    for n, cols in ((1, 1), (3, 1), (1, 5)):
        block = np.empty((16, n, cols), dtype=np.float32)
        rng = np.random.default_rng(3)
        for index in range(16):
            block[index] = (rng.standard_normal((n, cols))).astype(np.float32)
        case = dict(block=block,
                    buildings=(rng.random((n, cols)) < 0.5).astype(np.float32),
                    facesh=rng.integers(-1, 3, (n, cols)).astype(np.float32),
                    lup_term=(rng.standard_normal((n, cols))).astype(np.float32),
                    alb_term=(rng.standard_normal((n, cols))).astype(np.float32),
                    nosh_term=(rng.standard_normal((n, cols))).astype(np.float32),
                    first=np.float64(2.0), second=np.float64(2.0), warns=None)
        original_block = block.copy()
        planes = tuple(original_block[index] for index in range(16))
        original = _postprocess_block(planes, case['buildings'], case['facesh'],
                                      case['lup_term'], case['alb_term'], case['nosh_term'],
                                      case['first'], case['second'])
        candidate_block = block.copy()
        candidate = gvf_postprocess_block(candidate_block, case['buildings'], case['facesh'],
                                          case['lup_term'], case['alb_term'], case['nosh_term'],
                                          case['first'], case['second'])
        for left, right in zip(original, candidate):
            assert cases.bits_equal(left, right)
        for index in range(16):
            assert cases.bits_equal(original_block[index], candidate_block[index])
