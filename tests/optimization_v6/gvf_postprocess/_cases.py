"""Adversarial input cases and the node-by-node NumPy replica for C6-31.

The replica transcribes ``ground_view._postprocess_block`` (base 5e1fab46)
statement by statement with the real ``engine._operate``/``engine._divide``
helpers, capturing every intermediate node in the original order. The parity
tests first prove replica == original function (which validates the node
inventory), then prove kernel debug nodes == replica nodes (which validates
the compiled kernel node by node), on top of the end-to-end bitwise parity.
"""
import numpy as np

MUTATED_PLANES = (1, 3, 5)  # weightsumwall, weightsumLwall, weightsumalbwall


def bits_equal(left, right):
    """Bitwise equality including NaN payloads and signed zeros."""
    left = np.asarray(left)
    right = np.asarray(right)
    if left.dtype != right.dtype or left.shape != right.shape:
        return False
    return bool(np.array_equal(left.view(np.uint32), right.view(np.uint32)))


def _signs(rng, shape):
    return rng.choice(np.array([1.0, -1.0], dtype=np.float32), shape)


def _finite_planes(rng, n):
    block = np.empty((16, n, n), dtype=np.float32)
    scales = rng.choice(np.array([0.0, 1e-3, 1.0, 1e3, 1e7], dtype=np.float32), (n, n))
    for index in range(16):
        block[index] = (rng.standard_normal((n, n)) * scales).astype(np.float32)
    # Integer-valued influence planes so weightsumwall == second hits exactly.
    for index in (1, 7, 9, 15):
        block[index] = rng.integers(0, 7, (n, n)).astype(np.float32) * _signs(rng, (n, n))
    # Subnormals sprinkled into the sum planes.
    for index in (0, 2, 4, 6, 8, 10, 12, 14):
        mask = rng.random((n, n)) < 0.1
        block[index][mask] = np.float32(1e-40) * rng.integers(1, 5, (int(mask.sum()),)).astype(np.float32)
    return block


def case_random(n, seed=11):
    rng = np.random.default_rng(seed)
    block = _finite_planes(rng, n)
    buildings = (rng.random((n, n)) < 0.5).astype(np.float32)
    facesh = rng.integers(-1, 4, (n, n)).astype(np.float32)
    terms = [(rng.standard_normal((n, n)) * 10).astype(np.float32) for _ in range(3)]
    return dict(block=block, buildings=buildings, facesh=facesh,
                lup_term=terms[0], alb_term=terms[1], nosh_term=terms[2],
                first=np.float64(3.0), second=np.float64(2.0), warns=None)


def case_boundary(n, seed=23):
    """Exact threshold boundaries: raw gvf2 == 1.0 (kept) and > 1.0 (clamped),
    full keep==1 zeroing bands, keep == -1 bands, subnormal sums."""
    rng = np.random.default_rng(seed)
    block = np.zeros((16, n, n), dtype=np.float32)
    band = max(1, n // 4)
    for row in range(n):
        phase = (row // band) % 4
        if phase == 0:  # raw gvf2 == 1.0 exactly, not clamped
            block[1, row] = np.float32(0.5)
            block[0, row] = np.float32(1.5)
        elif phase == 1:  # raw gvf2 == nextafter(1.0), clamped
            block[1, row] = np.float32(0.5) + np.float32(2.0 ** -22)
            block[0, row] = np.float32(1.5)
        elif phase == 2:  # keep == 1 everywhere: eq and zeroing fire
            block[1, row] = np.float32(1.0)  # == second -> eq
            block[0, row] = np.float32(0.5)
            block[3, row] = np.float32(4.0)
            block[5, row] = np.float32(6.0)
        else:  # keep == -1 band (zeroed back to 0), +Inf and NaN payloads
            block[1, row] = np.float32(2.0)
            block[7, row] = np.float32(5.0)
            block[0, row] = np.float32(1e-40)
    facesh = np.zeros((n, n), dtype=np.float32)
    for row in range(n):
        phase = (row // band) % 4
        if phase == 2:
            facesh[row] = np.float32(0.0)  # keep = 1 - 0 = 1 -> zeroing fires
        elif phase == 3:
            facesh[row] = np.float32(1.0)  # keep = 0 - 1 = -1 -> zeroed back
        else:
            facesh[row] = np.float32(3.0)  # keep = -3, untouched
    buildings = (rng.random((n, n)) < 0.5).astype(np.float32)
    terms = [(rng.standard_normal((n, n)) * 1e-3).astype(np.float32) for _ in range(3)]
    # first-block mirrors of the boundary bands
    block[9] = np.float32(0.5)
    block[8] = np.float32(1.5)
    block[15] = np.float32(0.5)
    block[14] = np.float32(1.5)
    return dict(block=block, buildings=buildings, facesh=facesh,
                lup_term=terms[0], alb_term=terms[1], nosh_term=terms[2],
                first=np.float64(1.0), second=np.float64(1.0), warns=None)


def case_signed_zero(n, seed=31):
    """Bare -0.0 must survive to the outputs exactly as in the original."""
    rng = np.random.default_rng(seed)
    block = np.zeros((16, n, n), dtype=np.float32)
    half = rng.random((n, n)) < 0.5
    for index in range(16):
        block[index][half] = np.float32(-0.0)
        block[index][~half] = np.float32(-3.5) * (rng.random((n, n))[~half] < 0.5)
    buildings = np.zeros((n, n), dtype=np.float32)
    buildings[rng.random((n, n)) < 0.5] = np.float32(1.0)
    facesh = np.full((n, n), np.float32(-0.0), dtype=np.float32)
    facesh[rng.random((n, n)) < 0.5] = np.float32(1.0)
    terms = [np.full((n, n), np.float32(-0.0), dtype=np.float32) for _ in range(3)]
    terms[0][rng.random((n, n)) < 0.3] = np.float32(2.5)
    return dict(block=block, buildings=buildings, facesh=facesh,
                lup_term=terms[0], alb_term=terms[1], nosh_term=terms[2],
                first=np.float64(2.0), second=np.float64(3.0), warns=None)


def _payload_nan(bits):
    return np.array([bits], dtype=np.uint32).view(np.float32)[0]


def case_nan_payloads(n, seed=41):
    """Quiet NaN payloads and nonfinite terms: silent NaN propagation in both
    paths, exercising the restore+reference fallback. (Signaling NaN inputs
    warn in the original -- case_snan covers that contract.)"""
    rng = np.random.default_rng(seed)
    case = case_random(n, seed)
    block = case['block']
    block[9][0, 0] = _payload_nan(0x7FC00001)
    block[0][0, 1] = _payload_nan(0xFFC00042)
    block[1][1, 0] = _payload_nan(0x7FC00099)
    block[7][n - 1, n - 1] = _payload_nan(0xFFC00000)
    case['facesh'][2, 2] = _payload_nan(0x7FC00000)
    case['lup_term'][3, 3] = _payload_nan(0x7FC000AB)
    case['nosh_term'][4, 4] = _payload_nan(0xFFC000CD)
    case['warns'] = 'none'  # quiet NaN propagation is silent in the original
    return case


def case_snan(n, seed=43):
    """A signaling NaN input raises the invalid flag in every original NumPy
    op it touches ('invalid value encountered in ...'); the kernel cannot
    fire that warning, so the flagged fallback must reproduce it."""
    case = case_nan_payloads(n, seed)
    case['block'][11][5, 5] = _payload_nan(0x7F800001)  # signaling
    case['warns'] = 'invalid'
    return case


def case_inf_zero_invalid(n, seed=51):
    """0 * inf: (0 + Inf)/first * wallsuninfluence 0 -> invalid warning."""
    rng = np.random.default_rng(seed)
    case = case_random(n, seed)
    block = case['block']
    block[9] = np.float32(0.0)   # wallsuninfluence_first False everywhere
    block[8] = np.float32(np.inf)
    block[1] = np.float32(0.0)   # wallsuninfluence_second False
    block[0] = np.float32(np.inf)
    block[15] = np.float32(0.0)
    block[14] = np.float32(-np.inf)
    case['warns'] = 'invalid'
    return case


def case_inf_minus_inf(n, seed=61):
    """Overflow in both sums plus Inf*0 and (via the combine) Inf - Inf."""
    rng = np.random.default_rng(seed)
    case = case_random(n, seed)
    block = case['block']
    block[9] = np.float32(3.0e38)
    block[8] = np.float32(3.0e38)
    block[1] = np.float32(-3.0e38)
    block[0] = np.float32(-3.0e38)
    case['warns'] = 'invalid'
    return case


def case_overflow_clamp_hidden(n, seed=71):
    """The critical flag case: the gvf2 sum overflows (original warns
    'overflow encountered in add') but the gvf2[gvf2 > 1.0] = 1.0 clamp hides
    the resulting Inf, so every returned field is finite. Only the raw
    pre-clamp gvf2 check can route this to the reference."""
    rng = np.random.default_rng(seed)
    case = case_random(n, seed)
    block = case['block']
    block[1] = np.float32(3.0e38)
    block[0] = np.float32(3.0e38)
    for index in (9, 8, 11, 10, 13, 12, 15, 14, 7, 6, 5, 4, 3, 2):
        block[index] = np.float32(0.0)
    case['lup_term'] = np.zeros((n, n), dtype=np.float32)
    case['alb_term'] = np.zeros((n, n), dtype=np.float32)
    case['nosh_term'] = np.zeros((n, n), dtype=np.float32)
    case['warns'] = 'overflow'
    return case


def case_overflow_output(n, seed=81):
    """Overflow visible in an unclamped returned field (gvfLup)."""
    rng = np.random.default_rng(seed)
    case = case_random(n, seed)
    block = case['block']
    block[11] = np.float32(3.0e38)
    block[10] = np.float32(3.0e38)
    block[15] = np.float32(0.0)
    block[14] = np.float32(0.0)
    case['lup_term'] = np.full((n, n), np.float32(1.0e30), dtype=np.float32)
    case['warns'] = 'overflow'
    return case


def case_first_zero(n, seed=91):
    """first = 0: the original divides by zero ('divide by zero encountered
    in divide'); outside the kernel's admitted step domain."""
    case = case_random(n, seed)
    case['first'] = np.float64(0.0)
    case['warns'] = 'divide'
    return case


def case_underflow_subnormal(n, seed=101):
    """Subnormal plane sums divided by a large admitted step underflow to
    zero. Silent under NumPy's default regime in BOTH paths (bitwise-equal
    outputs); under errstate(under='raise') the original raises
    FloatingPointError where the wrapper returns (the kernel cannot observe
    the underflow flag) -- test_underflow_regime_contract pins that scoped
    asymmetry (review C6-60 F1)."""
    rng = np.random.default_rng(seed)
    case = case_random(n, seed)
    block = case['block']
    mins = np.float32(1.4e-45)  # smallest float32 subnormal
    block[9] = mins
    block[8] = mins
    block[1] = mins
    block[0] = mins
    case['first'] = np.float64(16777215.0)   # < 2**24: admitted domain
    case['second'] = np.float64(16777215.0)
    case['warns'] = 'none'
    return case


WARN_CASES = (case_inf_zero_invalid, case_inf_minus_inf, case_snan,
              case_overflow_clamp_hidden, case_overflow_output, case_first_zero)
CLEAN_CASES = (case_random, case_boundary, case_signed_zero, case_nan_payloads,
               case_underflow_subnormal)
ALL_CASES = CLEAN_CASES + WARN_CASES


def replica_postprocess(planes, buildings_b, facesh_b, lup_term_b, alb_term_b, nosh_term_b, first, second):
    """Statement-by-statement replica of ground_view._postprocess_block
    (base 5e1fab46) with every intermediate node captured in original order.
    Mutates the plane views exactly like the original.
    """
    from solweig_light.radiation.engine import _operate, _divide
    (weightsumsh, weightsumwall, weightsumLupsh, weightsumLwall,
     weightsumalbsh, weightsumalbwall, weightsumalbnosh, weightsumalbwallnosh,
     weightsumsh_first, weightsumwall_first, weightsumLupsh_first, weightsumLwall_first,
     weightsumalbsh_first, weightsumalbwall_first, weightsumalbnosh_first, weightsumalbwallnosh_first) = planes
    nodes = {}
    nodes['wallsuninfluence_first'] = weightsumwall_first > 0
    nodes['wallinfluence_first'] = weightsumalbwallnosh_first > 0
    nodes['wallsuninfluence_second'] = weightsumwall > 0
    nodes['wallinfluence_second'] = weightsumalbwallnosh > 0
    nodes['eq_second'] = (weightsumwall == second)
    keep = _operate(np.subtract, nodes['eq_second'].astype(np.float32), facesh_b)
    keep[keep == -1] = 0
    nodes['keep'] = keep.copy()
    gvf1 = _operate(np.add, _operate(np.multiply, _divide(_operate(np.add, weightsumwall_first, weightsumsh_first), _operate(np.add, first, 1)), nodes['wallsuninfluence_first']), _operate(np.multiply, _divide(weightsumsh_first, first), _operate(np.add, _operate(np.multiply, nodes['wallsuninfluence_first'], -1), 1)))
    nodes['gvf1'] = gvf1.copy()
    nodes['keep_mask'] = keep == 1
    weightsumwall[nodes['keep_mask']] = 0
    gvf2 = _operate(np.add, _operate(np.multiply, _divide(_operate(np.add, weightsumwall, weightsumsh), _operate(np.add, second, 1)), nodes['wallsuninfluence_second']), _operate(np.multiply, _divide(weightsumsh, second), _operate(np.add, _operate(np.multiply, nodes['wallsuninfluence_second'], -1), 1)))
    nodes['gvf2_raw'] = gvf2.copy()
    nodes['gvf2_clamp_mask'] = gvf2 > 1.0
    gvf2[nodes['gvf2_clamp_mask']] = 1.0
    gvfLup1 = _operate(np.add, _operate(np.multiply, _divide(_operate(np.add, weightsumLwall_first, weightsumLupsh_first), _operate(np.add, first, 1)), nodes['wallsuninfluence_first']), _operate(np.multiply, _divide(weightsumLupsh_first, first), _operate(np.add, _operate(np.multiply, nodes['wallsuninfluence_first'], -1), 1)))
    nodes['gvfLup1'] = gvfLup1.copy()
    weightsumLwall[nodes['keep_mask']] = 0
    gvfLup2 = _operate(np.add, _operate(np.multiply, _divide(_operate(np.add, weightsumLwall, weightsumLupsh), _operate(np.add, second, 1)), nodes['wallsuninfluence_second']), _operate(np.multiply, _divide(weightsumLupsh, second), _operate(np.add, _operate(np.multiply, nodes['wallsuninfluence_second'], -1), 1)))
    nodes['gvfLup2'] = gvfLup2.copy()
    gvfalb1 = _operate(np.add, _operate(np.multiply, _divide(_operate(np.add, weightsumalbwall_first, weightsumalbsh_first), _operate(np.add, first, 1)), nodes['wallsuninfluence_first']), _operate(np.multiply, _divide(weightsumalbsh_first, first), _operate(np.add, _operate(np.multiply, nodes['wallsuninfluence_first'], -1), 1)))
    nodes['gvfalb1'] = gvfalb1.copy()
    weightsumalbwall[nodes['keep_mask']] = 0
    gvfalb2 = _operate(np.add, _operate(np.multiply, _divide(_operate(np.add, weightsumalbwall, weightsumalbsh), _operate(np.add, second, 1)), nodes['wallsuninfluence_second']), _operate(np.multiply, _divide(weightsumalbsh, second), _operate(np.add, _operate(np.multiply, nodes['wallsuninfluence_second'], -1), 1)))
    nodes['gvfalb2'] = gvfalb2.copy()
    gvfalbnosh1 = _operate(np.add, _operate(np.multiply, _divide(_operate(np.add, weightsumalbwallnosh_first, weightsumalbnosh_first), _operate(np.add, first, 1)), nodes['wallinfluence_first']), _operate(np.multiply, _divide(weightsumalbnosh_first, first), _operate(np.add, _operate(np.multiply, nodes['wallinfluence_first'], -1), 1)))
    nodes['gvfalbnosh1'] = gvfalbnosh1.copy()
    gvfalbnosh2 = _operate(np.add, _operate(np.multiply, _divide(_operate(np.add, weightsumalbwallnosh, weightsumalbnosh), second), nodes['wallinfluence_second']), _operate(np.multiply, _divide(weightsumalbnosh, second), _operate(np.add, _operate(np.multiply, nodes['wallinfluence_second'], -1), 1)))
    nodes['gvfalbnosh2'] = gvfalbnosh2.copy()
    gvf = _divide(_operate(np.add, _operate(np.multiply, gvf1, 0.5), _operate(np.multiply, gvf2, 0.4)), 0.9)
    gvfLup = _divide(_operate(np.add, _operate(np.multiply, gvfLup1, 0.5), _operate(np.multiply, gvfLup2, 0.4)), 0.9)
    gvfLup = _operate(np.add, gvfLup, lup_term_b)
    gvfalb = _divide(_operate(np.add, _operate(np.multiply, gvfalb1, 0.5), _operate(np.multiply, gvfalb2, 0.4)), 0.9)
    gvfalb = _operate(np.add, gvfalb, alb_term_b)
    gvfalbnosh = _divide(_operate(np.add, _operate(np.multiply, gvfalbnosh1, 0.5), _operate(np.multiply, gvfalbnosh2, 0.4)), 0.9)
    gvfalbnosh = _operate(np.add, _operate(np.multiply, gvfalbnosh, buildings_b), nosh_term_b)
    return (gvf, gvfLup, gvfalb, gvfalbnosh, gvf2), nodes
