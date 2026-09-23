#SOLWEIG-GPU: GPU-accelerated SOLWEIG model for urban thermal comfort simulation
#Copyright (C) 2022–2025 Harsh Kamath and Naveen Sudharsan

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
"""N8-04 L0/L1 typed-graph identity tests for the longwave primary reducer.

These pin the CURRENT kernels (parallel and serial) against the independent
NumPy oracle in ``lw_reference_oracle.py`` on adversarial small inputs, with
exact uint32 bits for all seven output columns. They are ADDITIONS: the B7-02
capture replay (tests/optimization_v7/reference/test_v7_contract_freeze.py,
520 real-pipeline calls) remains the provenance-backed golden and is not
touched. Any N8-12/N8-13 candidate must reproduce these bits exactly.
"""
import numpy as np
import pytest

from lw_reference_oracle import (F32, bitwise_equal, kernel_pair,
                                 lw_primary_reference, u32)

PARALLEL, SERIAL = kernel_pair()

# ---------------------------------------------------------------------------
# Deterministic adversarial input construction (seeded; no environment input).
# ---------------------------------------------------------------------------

F32_POOL = [
    F32(0.0), F32(-0.0), F32(1.0), F32(-1.0), F32(2.0), F32(0.5), F32(-7.3),
    F32(2.0 ** 24), F32(2.0 ** 24 + 2.0), F32(2.0 ** -24), F32(2.0 ** -25),
    F32(2.0 ** -49), F32(1.0 + 2.0 ** -23), F32(1.0 - 2.0 ** -24),
    F32(1.0 - 2.0 ** -23), F32(3.4028235e38), F32(1.1754944e-38),
    F32(1.4012985e-45), F32(-1.4012985e-45), F32(np.inf), F32(-np.inf),
    F32(np.nan), F32(2.0 ** -126), F32(6.022047e23),
]

# Visibility scalars additionally exercise the raw (non-0/1) sh/vb values the
# typed predicates must handle exactly: building needs (1-sh)*vb == 1, which
# raw values like sh=1-2^-23 with vb=2^23 satisfy.
VIS_POOL = F32_POOL + [F32(3.0), F32(2.0 ** 23), F32(-2.0 ** 23)]

GATE_PATTERNS = [
    lambda P: np.zeros(P, np.bool_),
    lambda P: np.ones(P, np.bool_),
    lambda P: (np.arange(P) % 2 == 1),
    lambda P: (np.arange(P) < P // 2),
]


def _pick(rng, pool, size):
    return np.asarray(pool, F32)[rng.integers(0, len(pool), size=size)]


def adversarial_inputs(B, P, seed, surface_st='f64'):
    """Seeded adversarial argument bundle for the 17-argument kernel."""
    rng = np.random.default_rng(seed)
    sh = _pick(rng, VIS_POOL, (B, P))
    vs = _pick(rng, VIS_POOL, (B, P))
    vb = _pick(rng, VIS_POOL, (B, P))
    # Guarantee each predicate class actually occurs somewhere.
    if B and P:
        sh[0, 0] = F32(1.0); vs[0, 0] = F32(1.0)                       # sky true
        if P > 1:  # fully visible patch: mask false in sweep 2
            sh[0, 1] = F32(0.5); vs[0, 1] = F32(1.0); vb[0, 1] = F32(1.0)
        if P > 2:  # building predicate true via raw values
            sh[0, 2] = F32(1.0 - 2.0 ** -23); vb[0, 2] = F32(2.0 ** 23)
    sun = rng.integers(0, 2, (B, P)).astype(np.bool_)
    shade = rng.integers(0, 2, (B, P)).astype(np.bool_)
    solid = _pick(rng, F32_POOL, P)
    sine = _pick(rng, F32_POOL, P)
    cosine = _pick(rng, F32_POOL, P)
    if P:
        # Keep patch 0 finite and unit-scale so the building/veg chains
        # exercise finite cancellation rather than only NaN saturation.
        solid[0] = F32(1.0); sine[0] = F32(1.0); cosine[0] = F32(1.0)
    solar_gate = GATE_PATTERNS[seed % len(GATE_PATTERNS)](P)
    sky_down = _pick(rng, F32_POOL, P)
    sky_side = _pick(rng, F32_POOL, P)
    if P >= 3:  # finite-cancellation triple survives the pool draw
        sky_down[:3] = np.array([6.022047e23, -6.022047e23, 1.0], F32)
    lup = _pick(rng, F32_POOL, B) if B else np.zeros(0, F32)
    factor = F32((0.3, 1.0, 0.5, 0.0)[seed % 4])
    if surface_st == 'f64':
        surface = (float(F32_POOL[seed % len(F32_POOL)]),
                   float(F32_POOL[(seed + 5) % len(F32_POOL)]))
    else:
        surface = (F32(F32_POOL[seed % len(F32_POOL)]),
                   F32(F32_POOL[(seed + 5) % len(F32_POOL)]))
    return dict(sh=sh, vs=vs, vb=vb, sun=sun, shade=shade, solid=solid,
                sine=sine, cosine=cosine,
                directions=np.zeros((P, 4), F32),
                gate=np.zeros((P, 4), np.bool_),
                solar_gate=solar_gate, sky_down=sky_down, sky_side=sky_side,
                surface_sun=surface[0], surface_sh=surface[1], lup=lup,
                reflection_factor=factor)


def _pin_args(B, P, **over):
    """Deterministic minimal base for hand-derived bit pins."""
    args = dict(sh=np.zeros((B, P), F32), vs=np.ones((B, P), F32),
                vb=np.ones((B, P), F32),
                sun=np.zeros((B, P), np.bool_), shade=np.zeros((B, P), np.bool_),
                solid=np.ones(P, F32), sine=np.ones(P, F32),
                cosine=np.ones(P, F32),
                directions=np.zeros((P, 4), F32), gate=np.zeros((P, 4), np.bool_),
                solar_gate=np.zeros(P, np.bool_), sky_down=np.zeros(P, F32),
                sky_side=np.zeros(P, F32), surface_sun=1.0, surface_sh=1.0,
                lup=np.zeros(B, F32), reflection_factor=F32(1.0))
    args.update(over)
    return args


B_GRID = (1, 7, 8, 9, 11, 13)          # B=1; W=8 tails W-1/W/W+1; primes
P_GRID = (1, 2, 3, 5, 7, 11, 13, 153)  # P=1, primes, production P=153


@pytest.mark.parametrize('surface_st', ('f64', 'f32'))
@pytest.mark.parametrize('P', P_GRID)
@pytest.mark.parametrize('B', B_GRID)
def test_adversarial_grid_bitwise(B, P, surface_st):
    """Kernel == oracle, exact bits, all 7 columns, both kernels, both
    surface-scalar profiles, on the seeded adversarial grid."""
    args = adversarial_inputs(B, P, seed=1000 * B + P, surface_st=surface_st)
    expected = lw_primary_reference(surface_st=surface_st, **args)
    for kernel in (PARALLEL, SERIAL):
        observed = kernel(**args)
        assert observed.shape == (B, 7) and observed.dtype == F32
        assert bitwise_equal(observed, expected), (B, P, surface_st)


def test_adversarial_grid_parallel_equals_serial():
    """The scheduling label is not observable: prange vs range, exact bits."""
    for B, P, seed in ((9, 153, 71), (13, 609, 72), (7, 5, 73), (1, 1, 74)):
        args = adversarial_inputs(B, P, seed=seed)
        assert bitwise_equal(PARALLEL(**args), SERIAL(**args)), (B, P)


def test_patch_count_upper_boundary_609():
    """P=609 is the top of the admitted producer domain (driver guard
    0 < P <= 609); the kernels themselves are pinned there too."""
    args = adversarial_inputs(3, 609, seed=75)
    expected = lw_primary_reference(**args)
    assert bitwise_equal(SERIAL(**args), expected)
    assert bitwise_equal(PARALLEL(**args), expected)


def test_zero_pixels():
    """B=0: both kernels return the zero-filled (0,7) float32 frame without
    touching any patch data (also the native adapter's early return)."""
    args = adversarial_inputs(0, 3, seed=76)
    for kernel in (PARALLEL, SERIAL):
        out = kernel(**args)
        assert out.shape == (0, 7) and out.dtype == F32


# ---------------------------------------------------------------------------
# Strided sky columns (the real pipeline passes stride-12 column-2 views of
# [P,3] tables; the native ABI passes the element stride explicitly).
# ---------------------------------------------------------------------------

def test_strided_sky_columns():
    base_args = adversarial_inputs(5, 13, seed=77)
    contiguous = SERIAL(**base_args)
    table_down = np.zeros((13, 3), F32)
    table_down[:, 2] = base_args['sky_down']
    table_side = np.zeros((13, 3), F32)
    table_side[:, 2] = base_args['sky_side']
    strided = dict(base_args)
    strided['sky_down'] = table_down[:, 2]        # element stride 12 bytes
    strided['sky_side'] = table_side[:, 2]
    assert strided['sky_down'].strides == (12,)
    assert bitwise_equal(SERIAL(**strided), contiguous)
    # One-element strided views (P=1) with an arbitrary large stride.
    one = adversarial_inputs(2, 1, seed=78)
    ref = SERIAL(**one)
    col = np.zeros(7, F32)
    col[3] = one['sky_down'][0]
    one['sky_down'] = col[3:4:3]                   # shape (1,), stride 12
    assert one['sky_down'].strides == (12,)
    assert bitwise_equal(SERIAL(**one), ref)
    assert bitwise_equal(lw_primary_reference(**one), ref)
    # Negative-stride (reversed) sky columns stay admitted for the kernels;
    # they must match a contiguous copy of the same reversed values.
    rev = dict(base_args)
    reversed_down = base_args['sky_down'][::-1]    # view, stride -4
    assert reversed_down.strides[0] < 0
    rev['sky_down'] = reversed_down
    flat = dict(base_args)
    flat['sky_down'] = np.ascontiguousarray(reversed_down)
    assert bitwise_equal(SERIAL(**rev), SERIAL(**flat))


# ---------------------------------------------------------------------------
# Hand-derived bit pins. Each expected pattern is derived by IEEE-754
# arithmetic in the comments; the kernel must produce exactly these bits.
# These are NEW pins for tiny deterministic cases -- no existing golden is
# read or overwritten.
# ---------------------------------------------------------------------------

def test_pin_mask_times_infinity_is_nan():
    """sky=false is a 0.0f MULTIPLY, not a skipped branch: 0*Inf = NaN."""
    args = _pin_args(1, 1, sh=np.full((1, 1), F32(0.5)),
                     sky_down=np.array([np.inf], F32))
    out = SERIAL(**args)          # sh=0.5 -> sky false
    # a0 = RN32(+0 + 0.0f*Inf) = NaN (canonical 0x7FC00000); out0 = NaN too.
    assert u32(out[0, 0])[0] == 0x7FC00000
    assert np.isnan(out[0, 0])
    assert bitwise_equal(out, lw_primary_reference(**args))


def test_pin_reflected_inf_visible_patch_is_nan_occluded_is_inf():
    """Sweep-2 occlusion mask is a number multiply: reflected=Inf gives NaN
    on visible patches (Inf*0.0f) and +Inf on occluded patches (Inf*1.0f)."""
    visible = _pin_args(1, 1, sh=np.ones((1, 1), F32), vs=np.ones((1, 1), F32),
                        vb=np.ones((1, 1), F32),
                        lup=np.array([np.inf], F32))
    out = SERIAL(**visible)       # mask false -> 0.0f multiply
    assert u32(out[0, 6])[0] == 0x7FC00000          # a9 = Inf*0 = NaN
    occluded = _pin_args(1, 1, sh=np.zeros((1, 1), F32),
                         lup=np.array([np.inf], F32))
    out = SERIAL(**occluded)      # mask true -> 1.0f multiply
    assert u32(out[0, 6])[0] == 0x7F800000          # a9 = Inf*1*1*1 = +Inf


def test_pin_building_predicate_raw_values():
    """building = (RN32(1f - sh) * vb) == 1 exactly; raw values count:
    sh=1-2^-23 with vb=2^23 makes (2^-23 * 2^23) == 1 true."""
    def run(vb_value):
        args = _pin_args(1, 1, sh=np.full((1, 1), F32(1.0 - 2.0 ** -23)),
                         vb=np.full((1, 1), F32(vb_value)),
                         sun=np.ones((1, 1), np.bool_),
                         shade=np.ones((1, 1), np.bool_),
                         solar_gate=np.ones(1, np.bool_))
        return SERIAL(**args)
    # building true: sun_down=shade_down=1 -> a2=a3=1 -> out0 = 2.0.
    assert u32(run(2.0 ** 23)[0, 0])[0] == 0x40000000
    # building false (vb=1: product 2^-23 != 1): out0 = 0.0.
    assert u32(run(1.0)[0, 0])[0] == 0x00000000


def test_pin_signed_zeros():
    """+0 + -0 = +0 under round-to-nearest: a0=+0, lup=-0 gives reflected
    +0, and a -0.0 surface scalar accumulates onto +0 as +0."""
    args = _pin_args(1, 1, lup=np.array([F32(-0.0)]))
    out = SERIAL(**args)
    assert u32(out[0, 6])[0] == 0x00000000         # a9: (+0 + -0) path -> +0
    assert not np.signbit(out[0, 6])
    args = _pin_args(1, 1, surface_sun=-0.0, surface_sh=-0.0)
    out = SERIAL(**args)
    assert u32(out[0, 3])[0] == 0x00000000         # a6 = RN32(+0 + -0) = +0
    assert not np.signbit(out[0, 3])
    assert bitwise_equal(out, lw_primary_reference(**args))


def test_pin_reflection_divides_by_stored_pi_not_reciprocal():
    """reflected = RN32(x / 0x40490FDB) -- a true division. For
    x = 11.000000953674316 the reciprocal rewrite would give 0x40601715,
    the division gives 0x40601716; the kernel must take the division."""
    x = F32(11.000000953674316)
    # sh=0: sky stays false (sh!=1) but the patch is occluded, so the
    # sweep-2 mask is 1.0f and a9 = reflected*solid*cosine*1.
    args = _pin_args(1, 1, sh=np.zeros((1, 1), F32),
                     lup=np.array([F32(x * 2)], F32))
    out = SERIAL(**args)
    # a0=+0 (sky false): r0 = 0 + x*2; r1 = r0*1; r2 = RN32(x*2*0.5) = x;
    # reflected = RN32(x / pi32) = 0x40601716; a9 = reflected*1*1*1.
    assert u32(out[0, 6])[0] == 0x40601716
    assert u32(F32(x / F32(np.pi)))[0] == 0x40601716
    assert u32(F32(x * F32(1.0 / np.pi)))[0] == 0x40601715   # the forbidden path


def test_pin_f32_and_f64_surface_profiles_are_different_graphs():
    """surface = 1+2^-25 with solid=[1, 2^-24], cosine=1, veg on.
    f64 profile keeps the scalar: c0 = (1+2^-25)*1*1 so
    a6 = RN32(1+2^-25) = 1.0 (below the 1+2^-24 midpoint); c1 =
    (1+2^-25)*2^-24 = 2^-24+2^-49 so a6 = RN32(f64(1.0)+2^-24+2^-49) =
    1+2^-23 (strictly above the midpoint).  f32 profile rounds the scalar
    to 1.0f at provenance: c1 = 1.0f*2^-24 = 2^-24 and the f32 add
    1.0f + 2^-24f is the exact tie, rounding to even -> 1.0."""
    s = 1 + 2.0 ** -25
    common = dict(vs=np.zeros((1, 2), F32),
                  solid=np.array([1.0, 2.0 ** -24], F32),
                  cosine=np.ones(2, F32), sine=np.ones(2, F32))
    args64 = _pin_args(1, 2, surface_sun=s, surface_sh=s, **common)
    args32 = _pin_args(1, 2, surface_sun=F32(s), surface_sh=F32(s), **common)
    out64, out32 = SERIAL(**args64), SERIAL(**args32)
    assert u32(out64[0, 3])[0] == 0x3F800001      # a6 = 1 + 2^-23
    assert u32(out32[0, 3])[0] == 0x3F800000      # a6 = 1.0
    assert not np.array_equal(out64.view(np.uint32), out32.view(np.uint32))
    assert bitwise_equal(out64, lw_primary_reference(surface_st='f64', **args64))
    assert bitwise_equal(out32, lw_primary_reference(surface_st='f32', **args32))
