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
"""N8-12 bit-exactness gates for the B control (AoSoA Numba consumer).

The B control must reproduce the independent N8-04 NumPy oracle BITWISE
(uint32 view, all seven columns) on the FULL frozen adversarial grid --
imported read-only from tests/optimization_v8/reference -- including every
discriminator of the typed contract: RN32 single-rounding rule, ordered
sweeps, reflection division by stored pi, mask number-multiplies, signed
zeros, nonfinite payloads, raw visibility values, strided sky columns.
Parallel must equal serial BITWISE, and the experimental lanes formulation
must equal the row-major control BITWISE. The frozen baseline kernels are
pinned alongside (they equal the oracle by the N8-04 suite; equality here
cross-checks both on identical inputs).

The pack helper poisons padding lanes with canonical NaN / True: parity on
the B valid rows then also proves padding lanes are never read.
"""
import numpy as np
import pytest

from solweig_light._native_dispatch import lw_b_control as bc
from lw_reference_oracle import (F32, bitwise_equal, kernel_pair,
                                 lw_primary_reference, u32)
# Frozen adversarial grid + discriminators (READ-ONLY imports).
from test_typed_graph_identity import (B_GRID, P_GRID, _pin_args,
                                       adversarial_inputs)
from test_rn32_accumulation_rule import discriminator_args
from test_sweep_order import ordered_args

FROZEN_PARALLEL, FROZEN_SERIAL = kernel_pair()

POISON_U32 = 0x7FC00000          # canonical NaN: padding must never be read


def pack_aosoa(dense, width=8):
    """dense float32 [B, P] -> uint32 [G, P, W] producer-layout buffer.

    The lane mapping ((g*P+p)*W+lane == dense[g*W+lane, p] bits) is exactly
    produce_block_aosoa's; padding lanes are POISONED (canonical NaN) rather
    than left unwritten, so any padding read changes the result loudly.
    """
    dense = np.ascontiguousarray(dense, dtype=np.float32)
    rows, patches = dense.shape
    gangs = -(-rows // width)
    padded = np.full((gangs * width, patches), POISON_U32, dtype=np.uint32)
    if rows:
        padded[:rows] = dense.view(np.uint32)
    return padded.reshape(gangs, width, patches).transpose(0, 2, 1).copy()


def pack_bool(mask, width=8):
    """bool [B, P] -> bool [G, P, W] with poisoned (True) padding lanes."""
    mask = np.asarray(mask, np.bool_)
    rows, patches = mask.shape
    gangs = -(-rows // width)
    padded = np.ones((gangs * width, patches), dtype=np.bool_)
    if rows:
        padded[:rows] = mask
    return padded.reshape(gangs, width, patches).transpose(0, 2, 1).copy()


def packed_args(args, width=8):
    """Pack the 17-argument bundle's per-pixel arrays into the AoSoA feed."""
    return dict(sh=pack_aosoa(args['sh'], width), vs=pack_aosoa(args['vs'], width),
                vb=pack_aosoa(args['vb'], width), sun=pack_bool(args['sun'], width),
                shade=pack_bool(args['shade'], width))


def b_call(args, rows, parallel=False, width=8, **over):
    """Adapter call on a dense 17-argument bundle (with overrides)."""
    merged = dict(args)
    merged.update(over)
    packed = packed_args(merged, width)
    shared = {k: v for k, v in merged.items() if k not in packed}
    return bc.lw_primary_b(**packed, **shared, rows=rows, parallel=parallel)


def run_b(packed, args, rows, width=8):
    """(parallel, serial, lanes) B-control outputs on a packed bundle."""
    shared = {k: v for k, v in args.items() if k not in packed}
    out_par = bc.lw_primary_b(**packed, **shared, rows=rows, parallel=True)
    out_ser = bc.lw_primary_b(**packed, **shared, rows=rows, parallel=False)
    out = np.zeros((rows, 7), dtype=np.float32)
    out_lanes = bc.lw_primary_b_lanes_serial(
        packed['sh'].view(np.float32), packed['vs'].view(np.float32),
        packed['vb'].view(np.float32), packed['sun'], packed['shade'],
        shared['solid'], shared['sine'], shared['cosine'],
        shared['directions'], shared['gate'], shared['solar_gate'],
        shared['sky_down'], shared['sky_side'], shared['surface_sun'],
        shared['surface_sh'], shared['lup'], shared['reflection_factor'],
        rows, out)
    return out_par, out_ser, out_lanes


# ---------------------------------------------------------------------------
# Full adversarial grid: B == oracle == frozen, bitwise, both profiles.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('surface_st', ('f64', 'f32'))
@pytest.mark.parametrize('P', P_GRID)
@pytest.mark.parametrize('B', B_GRID)
def test_b_control_matches_oracle_bitwise(B, P, surface_st):
    """All three B formulations == oracle (and the frozen kernels), exact
    bits, all 7 columns, both surface-scalar profiles, poisoned padding."""
    args = adversarial_inputs(B, P, seed=1000 * B + P, surface_st=surface_st)
    expected = lw_primary_reference(surface_st=surface_st, **args)
    out_par, out_ser, out_lanes = run_b(packed_args(args), args, B)
    for name, out in (('parallel', out_par), ('serial', out_ser),
                      ('lanes', out_lanes)):
        assert out.shape == (B, 7) and out.dtype == F32, (name, B, P)
        assert bitwise_equal(out, expected), (name, B, P, surface_st)
    assert bitwise_equal(out_par, out_ser), ('parallel != serial', B, P)
    assert bitwise_equal(out_lanes, out_ser), ('lanes != serial', B, P)
    assert bitwise_equal(out_ser, FROZEN_SERIAL(**args)), (B, P)
    assert bitwise_equal(out_par, FROZEN_PARALLEL(**args)), (B, P)


def test_b_control_parallel_equals_serial_wide():
    """Scheduling label is not observable at larger shapes too (incl. 609)."""
    for B, P, seed in ((9, 153, 71), (13, 609, 72), (7, 5, 73), (1, 1, 74)):
        args = adversarial_inputs(B, P, seed=seed)
        out_par, out_ser, _ = run_b(packed_args(args), args, B)
        assert bitwise_equal(out_par, out_ser), (B, P)


def test_b_control_patch_count_upper_boundary_609():
    """P=609 top of the admitted domain, pinned like the reference suite."""
    args = adversarial_inputs(3, 609, seed=75)
    expected = lw_primary_reference(**args)
    out_par, out_ser, out_lanes = run_b(packed_args(args), args, 3)
    assert bitwise_equal(out_ser, expected)
    assert bitwise_equal(out_par, expected)
    assert bitwise_equal(out_lanes, expected)
    assert bitwise_equal(out_ser, FROZEN_SERIAL(**args))


def test_b_control_zero_pixels():
    """rows=0: adapter returns the zero frame before touching patch data
    (native B=0 mirror); the raw kernels also yield the untouched zeros."""
    args = adversarial_inputs(0, 3, seed=76)
    packed = packed_args(args)
    out = b_call(args, 0)
    assert out.shape == (0, 7) and out.dtype == F32
    shared = {k: v for k, v in args.items() if k not in packed}
    for kernel in (bc.lw_primary_b_parallel, bc.lw_primary_b_serial):
        raw = kernel(packed['sh'].view(np.float32), packed['vs'].view(np.float32),
                     packed['vb'].view(np.float32), packed['sun'], packed['shade'],
                     *(shared[k] for k in ('solid', 'sine', 'cosine', 'directions',
                                           'gate', 'solar_gate', 'sky_down', 'sky_side',
                                           'surface_sun', 'surface_sh', 'lup',
                                           'reflection_factor')), 0,
                     np.zeros((0, 7), dtype=np.float32))
        assert raw.shape == (0, 7) and raw.dtype == F32


def test_b_control_width_four_also_admitted():
    """W=4 (the other native gang width) carries the same bits: pack at 4,
    run, compare with the W=8 result and the oracle."""
    args = adversarial_inputs(9, 13, seed=79)
    expected = lw_primary_reference(**args)
    out8_ser = b_call(args, 9, width=8)
    out4_par, out4_ser, out4_lanes = run_b(packed_args(args, 4), args, 9, width=4)
    assert bitwise_equal(out4_ser, expected)
    assert bitwise_equal(out4_par, out4_ser)
    assert bitwise_equal(out4_lanes, out4_ser)
    assert bitwise_equal(out4_ser, out8_ser)


# ---------------------------------------------------------------------------
# Strided sky columns (real path: stride-12 column-2 views; numba consumes
# any element stride natively, matching the native ABI's stride argument).
# ---------------------------------------------------------------------------

def test_b_control_strided_sky_columns():
    base_args = adversarial_inputs(5, 13, seed=77)
    contiguous = b_call(base_args, 5)
    table_down = np.zeros((13, 3), F32)
    table_down[:, 2] = base_args['sky_down']
    table_side = np.zeros((13, 3), F32)
    table_side[:, 2] = base_args['sky_side']
    strided = dict(base_args)
    strided['sky_down'] = table_down[:, 2]        # element stride 12 bytes
    strided['sky_side'] = table_side[:, 2]
    assert strided['sky_down'].strides == (12,)
    assert bitwise_equal(b_call(strided, 5), contiguous)
    # One-element strided views (P=1) with an arbitrary large stride.
    one = adversarial_inputs(2, 1, seed=78)
    ref = b_call(one, 2)
    col = np.zeros(7, F32)
    col[3] = one['sky_down'][0]
    one['sky_down'] = col[3:4:3]                  # shape (1,), stride 12
    assert one['sky_down'].strides == (12,)
    assert bitwise_equal(b_call(one, 2), ref)
    assert bitwise_equal(lw_primary_reference(**one), ref)
    # Negative-stride (reversed) sky columns stay admitted; a contiguous copy
    # of the same reversed values must give identical bits.
    rev = dict(base_args)
    reversed_down = base_args['sky_down'][::-1]   # view, stride -4
    assert reversed_down.strides[0] < 0
    rev['sky_down'] = reversed_down
    flat = dict(base_args)
    flat['sky_down'] = np.ascontiguousarray(reversed_down)
    assert bitwise_equal(b_call(rev, 5), b_call(flat, 5))


# ---------------------------------------------------------------------------
# Contract discriminators, re-pinned through the B control.
# ---------------------------------------------------------------------------

def test_b_pin_mask_times_infinity_is_nan():
    args = _pin_args(1, 1, sh=np.full((1, 1), F32(0.5)),
                     sky_down=np.array([np.inf], F32))
    out = b_call(args, 1)
    assert u32(out[0, 0])[0] == 0x7FC00000        # 0.0f * Inf = NaN
    assert np.isnan(out[0, 0])
    assert bitwise_equal(out, lw_primary_reference(**args))


def test_b_pin_reflected_inf_visible_nan_occluded_inf():
    visible = _pin_args(1, 1, sh=np.ones((1, 1), F32), vs=np.ones((1, 1), F32),
                        vb=np.ones((1, 1), F32), lup=np.array([np.inf], F32))
    out = b_call(visible, 1)
    assert u32(out[0, 6])[0] == 0x7FC00000       # Inf * 0.0f = NaN
    occluded = _pin_args(1, 1, sh=np.zeros((1, 1), F32),
                         lup=np.array([np.inf], F32))
    out = b_call(occluded, 1)
    assert u32(out[0, 6])[0] == 0x7F800000       # Inf * 1.0f = +Inf


def test_b_pin_building_predicate_raw_values():
    def run(vb_value):
        args = _pin_args(1, 1, sh=np.full((1, 1), F32(1.0 - 2.0 ** -23)),
                         vb=np.full((1, 1), F32(vb_value)),
                         sun=np.ones((1, 1), np.bool_),
                         shade=np.ones((1, 1), np.bool_),
                         solar_gate=np.ones(1, np.bool_))
        return b_call(args, 1)
    assert u32(run(2.0 ** 23)[0, 0])[0] == 0x40000000   # building true
    assert u32(run(1.0)[0, 0])[0] == 0x00000000         # building false


def test_b_pin_signed_zeros():
    args = _pin_args(1, 1, lup=np.array([F32(-0.0)]))
    out = b_call(args, 1)
    assert u32(out[0, 6])[0] == 0x00000000 and not np.signbit(out[0, 6])
    args = _pin_args(1, 1, surface_sun=-0.0, surface_sh=-0.0)
    out = b_call(args, 1)
    assert u32(out[0, 3])[0] == 0x00000000 and not np.signbit(out[0, 3])
    assert bitwise_equal(out, lw_primary_reference(**args))


def test_b_pin_reflection_divides_by_stored_pi():
    x = F32(11.000000953674316)
    args = _pin_args(1, 1, sh=np.zeros((1, 1), F32),
                     lup=np.array([F32(x * 2)], F32))
    out = b_call(args, 1)
    assert u32(out[0, 6])[0] == 0x40601716       # division, not reciprocal
    assert u32(out[0, 6])[0] != 0x40601715


def test_b_pin_f32_and_f64_surface_profiles_differ():
    s = 1 + 2.0 ** -25
    common = dict(vs=np.zeros((1, 2), F32),
                  solid=np.array([1.0, 2.0 ** -24], F32),
                  cosine=np.ones(2, F32), sine=np.ones(2, F32))
    args64 = _pin_args(1, 2, surface_sun=s, surface_sh=s, **common)
    args32 = _pin_args(1, 2, surface_sun=F32(s), surface_sh=F32(s), **common)
    out64 = b_call(args64, 1)
    out32 = b_call(args32, 1)
    assert u32(out64[0, 3])[0] == 0x3F800001
    assert u32(out32[0, 3])[0] == 0x3F800000
    assert not np.array_equal(out64.view(np.uint32), out32.view(np.uint32))
    assert bitwise_equal(out64, lw_primary_reference(surface_st='f64', **args64))
    assert bitwise_equal(out32, lw_primary_reference(surface_st='f32', **args32))


def test_b_pin_rn32_rule_single_rounding():
    """a = RN32(f64(a) + c64), never RN32(a + RN32(c)): the frozen
    discriminator input must give a6 = 2^24+2 (0x4B800001) through the B
    control, for all three formulations."""
    args = discriminator_args()
    out_par, out_ser, out_lanes = run_b(packed_args(args), args, 1)
    for name, out in (('parallel', out_par), ('serial', out_ser),
                      ('lanes', out_lanes)):
        assert u32(out[0, 3])[0] == 0x4B800001, name
        assert bitwise_equal(out, lw_primary_reference(surface_st='f64', **args))
    assert u32(out_ser[0, 0])[0] == 0x4C000001   # down chains follow the rule


def test_b_pin_float32_view_convention_is_binding():
    """Review note N6 (n8_30_review_n8_11_layout.md): the kernels must be fed
    float32 views of the produced blocks. The adapter constructs the views
    internally (parity holds), and a raw uint32 feed FAILS the discriminating
    input -- the sky predicate collapses because bit 0x3F800000 (1.0f) is not
    integer 1 -- proving the convention is load-bearing, not decorative."""
    args = _pin_args(1, 1, sh=np.ones((1, 1), F32), vs=np.ones((1, 1), F32),
                     sky_down=np.array([400.0], F32),
                     sky_side=np.array([390.0], F32))
    expected = lw_primary_reference(**args)
    packed = packed_args(args)
    shared = {k: v for k, v in args.items() if k not in packed}
    # Correct path: the adapter feeds .view(np.float32) blocks itself.
    out = bc.lw_primary_b(**packed, **shared, rows=1, parallel=False)
    assert bitwise_equal(out, expected)
    assert u32(out[0, 2])[0] == 0x43C30000            # a5 = 390.0f
    # MUTATION CHECK (teeth): the same kernel fed the RAW uint32 blocks
    # compiles and silently loses the sky term.
    mutated = bc.lw_primary_b_serial(
        packed['sh'], packed['vs'], packed['vb'], packed['sun'], packed['shade'],
        *(shared[k] for k in ('solid', 'sine', 'cosine', 'directions', 'gate',
                              'solar_gate', 'sky_down', 'sky_side', 'surface_sun',
                              'surface_sh', 'lup', 'reflection_factor')),
        1, np.zeros((1, 7), F32))
    assert not bitwise_equal(mutated, expected)
    assert u32(mutated[0, 2])[0] == 0x00000000        # sky term silently lost


def test_b_pin_sweep_order_is_observable():
    """Both sweeps keep p = 0..P-1 left folds: [2^24,1,1] vs [1,1,2^24]
    land on different bits through the B control too."""
    ordered = b_call(ordered_args([2.0 ** 24, 1.0, 1.0]), 1)
    permuted = b_call(ordered_args([1.0, 1.0, 2.0 ** 24]), 1)
    assert u32(ordered[0, 0])[0] == 0x4B800000
    assert u32(permuted[0, 0])[0] == 0x4B800001

    def sweep_two(solid):
        args = ordered_args([0.0, 0.0, 0.0])
        args['sh'] = np.zeros((1, 3), F32)
        args['lup'] = np.array([F32(2.0) * F32(np.pi)], F32)
        args['reflection_factor'] = F32(1.0)
        args['solid'] = np.asarray(solid, F32)
        return b_call(args, 1)

    ordered2 = sweep_two([2.0 ** 24, 1.0, 1.0])
    permuted2 = sweep_two([1.0, 1.0, 2.0 ** 24])
    assert u32(ordered2[0, 6])[0] == 0x4B800000
    assert u32(permuted2[0, 6])[0] == 0x4B800001
    assert not bitwise_equal(ordered, permuted)
    assert not bitwise_equal(ordered2, permuted2)
