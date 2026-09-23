#SOLWEIG-GPU: GPU-accelerated SOLWEIG model for urban thermal comfort simulation
#Copyright (C) 2022–2025 Harsh Kamath and Naveen Sudharsan
import pytest
pytest.skip(
    'archived with the N8 native row and qualification machinery '
    '(n8_32 selection closed N9 F3 NATIVE_LOSS; archived at N9 F4 closed_cpu_only): research copies preserved under '
    'experiments/optimization_v8/native_dispatch/',
    allow_module_level=True)

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
"""N8-13 bitwise parity: native AoSoA consumer vs the frozen N8-04 oracle.

Every comparison is exact uint32 bits (NaN payloads and signed zeros
included) against BOTH the independent NumPy oracle and the frozen serial
Numba kernel, on the frozen adversarial grid (B tails around W=8, prime
and production P, both surface-scalar profiles), plus the padding-lane
poison invariant, the N8-11 producer bit-identity feed, strided sky
columns, and the N8-04 hand-derived bit pins re-expressed through the
native path.
"""
import numpy as np
import pytest
from solweig_light.geometry.visibility import PackedVisibility, _EncodedPatch
from solweig_light.geometry.visibility_compiled import _decode, _descriptor

from solweig_light._native_dispatch import direct_aosoa as da
from native_test_helpers import (F32, SERIAL, _pin_args, adversarial_inputs,
                                 aosoa_rows, bitwise_equal,
                                 lw_primary_reference, run_native, to_aosoa,
                                 u32)

B_GRID = (1, 7, 8, 9, 11, 13)            # W=8 tails W-1/W/W+1 and primes
P_GRID = (1, 2, 3, 5, 7, 11, 13, 153, 609)


@pytest.mark.parametrize('surface_st', ('f64', 'f32'))
@pytest.mark.parametrize('P', P_GRID)
@pytest.mark.parametrize('B', B_GRID)
def test_adversarial_grid_bitwise(B, P, surface_st, generation_dir):
    """Native AoSoA == oracle == frozen SERIAL kernel, exact bits, all 7
    columns, both surface-scalar profiles, seeded adversarial grid."""
    args = adversarial_inputs(B, P, seed=1000 * B + P, surface_st=surface_st)
    expected = lw_primary_reference(surface_st=surface_st, **args)
    observed = run_native(to_aosoa(args, B), B)
    assert observed.shape == (B, 7) and observed.dtype == F32
    assert bitwise_equal(observed, expected), (B, P, surface_st)
    assert bitwise_equal(observed, SERIAL(**args)), (B, P, surface_st)


def test_patch_count_upper_boundary_609(generation_dir):
    args = adversarial_inputs(13, 609, seed=75)
    expected = lw_primary_reference(**args)
    assert bitwise_equal(run_native(to_aosoa(args, 13), 13), expected)


@pytest.mark.parametrize('B,P', ((97, 13), (128, 153), (100, 1)))
def test_many_gangs_bitwise(B, P, generation_dir):
    """The frozen grid caps at two gangs; these exercise the sequential
    multi-gang loop (full gangs + tail) at both profiles."""
    for surface_st in ('f64', 'f32'):
        args = adversarial_inputs(B, P, seed=B * 7 + P, surface_st=surface_st)
        expected = lw_primary_reference(surface_st=surface_st, **args)
        observed = run_native(to_aosoa(args, B), B)
        assert bitwise_equal(observed, expected), (B, P, surface_st)
        assert bitwise_equal(observed, SERIAL(**args)), (B, P, surface_st)


def test_parallel_equals_serial_equals_native(generation_dir):
    """Scheduling label is not observable: frozen parallel == frozen serial
    == native AoSoA, exact bits."""
    from lw_reference_oracle import kernel_pair
    parallel, _ = kernel_pair()
    for B, P, seed in ((9, 153, 71), (13, 609, 72), (7, 5, 73), (1, 1, 74)):
        args = adversarial_inputs(B, P, seed=seed)
        assert bitwise_equal(parallel(**args), SERIAL(**args)), (B, P)
        assert bitwise_equal(run_native(to_aosoa(args, B), B), SERIAL(**args))


def test_zero_pixels(generation_dir):
    """B=0: the zero-filled (0,7) float32 frame without any native launch."""
    args = adversarial_inputs(0, 3, seed=76)
    out = run_native(to_aosoa(args, 0), 0)
    assert out.shape == (0, 7) and out.dtype == F32


# ---------------------------------------------------------------------------
# Padding-lane poison: the producer never writes padding lanes, so they hold
# arbitrary bits; the consumer must never let them reach any stored result.
# ---------------------------------------------------------------------------

POISONS = (0x7FC0DEAD, 0xFF800000, 0x7F800000, 0x00000000, 0xDEADBEEF)


@pytest.mark.parametrize('poison', POISONS)
@pytest.mark.parametrize('B', (1, 7, 9, 11, 13))
def test_padding_poison_never_read(B, poison, generation_dir):
    """Every poison bit pattern in the padding lanes of sh/vs/vb (plus True
    padding in sun/shade) leaves all B rows bit-identical to the oracle."""
    P = 13
    args = adversarial_inputs(B, P, seed=1000 * B + P)
    expected = lw_primary_reference(**args)
    observed = run_native(to_aosoa(args, B, poison=poison), B)
    assert bitwise_equal(observed, expected), (B, hex(poison))


@pytest.mark.parametrize('B', (9, 13))
def test_inputs_never_written(B, generation_dir):
    """The kernel treats every input as const: all input buffers keep their
    exact bytes (poison padding included) across the call."""
    P = 7
    args = adversarial_inputs(B, P, seed=1000 * B + P)
    aosoa = to_aosoa(args, B)
    snapshots = {name: a.tobytes() for name, a in aosoa.items()
                 if isinstance(a, np.ndarray)}
    run_native(aosoa, B)
    for name, a in aosoa.items():
        if isinstance(a, np.ndarray):
            assert a.tobytes() == snapshots[name], name


# ---------------------------------------------------------------------------
# Strided sky columns (the real pipeline passes stride-12 column views of
# [P,3] tables; the ABI passes the element stride explicitly).
# ---------------------------------------------------------------------------

def test_strided_sky_columns(generation_dir):
    base_args = adversarial_inputs(5, 13, seed=77)
    contiguous = run_native(to_aosoa(base_args, 5), 5)
    table_down = np.zeros((13, 3), F32)
    table_down[:, 2] = base_args['sky_down']
    table_side = np.zeros((13, 3), F32)
    table_side[:, 2] = base_args['sky_side']
    strided = dict(base_args)
    strided['sky_down'] = table_down[:, 2]        # element stride 12 bytes
    strided['sky_side'] = table_side[:, 2]
    assert strided['sky_down'].strides == (12,)
    assert bitwise_equal(run_native(to_aosoa(strided, 5), 5), contiguous)
    # One-element strided views (P=1) with an arbitrary large stride.
    one = adversarial_inputs(2, 1, seed=78)
    ref = run_native(to_aosoa(one, 2), 2)
    col = np.zeros(7, F32)
    col[3] = one['sky_down'][0]
    one['sky_down'] = col[3:4:3]                   # shape (1,), stride 12
    assert one['sky_down'].strides == (12,)
    assert bitwise_equal(run_native(to_aosoa(one, 2), 2), ref)
    # Negative-stride (reversed) sky columns match a contiguous copy.
    rev = dict(base_args)
    rev['sky_down'] = base_args['sky_down'][::-1]  # view, stride -4
    assert rev['sky_down'].strides[0] < 0
    flat = dict(base_args)
    flat['sky_down'] = np.ascontiguousarray(rev['sky_down'])
    assert bitwise_equal(run_native(to_aosoa(rev, 5), 5),
                         run_native(to_aosoa(flat, 5), 5))


# ---------------------------------------------------------------------------
# N8-04 hand-derived bit pins, re-expressed through the native consumer.
# ---------------------------------------------------------------------------

def _pin_aosoa(B, P, **over):
    args = _pin_args(B, P, **over)
    return args, to_aosoa(args, B)


def test_pin_mask_times_infinity_is_nan(generation_dir):
    args, aosoa = _pin_aosoa(1, 1, sh=np.full((1, 1), F32(0.5)),
                             sky_down=np.array([np.inf], F32))
    out = run_native(aosoa, 1)
    assert u32(out[0, 0])[0] == 0x7FC00000
    assert np.isnan(out[0, 0])
    assert bitwise_equal(out, lw_primary_reference(**args))


def test_pin_reflected_inf_visible_patch_is_nan_occluded_is_inf(generation_dir):
    args, visible = _pin_aosoa(1, 1, sh=np.ones((1, 1), F32),
                               vs=np.ones((1, 1), F32), vb=np.ones((1, 1), F32),
                               lup=np.array([np.inf], F32))
    out = run_native(visible, 1)
    assert u32(out[0, 6])[0] == 0x7FC00000          # a9 = Inf*0 = NaN
    args, occluded = _pin_aosoa(1, 1, sh=np.zeros((1, 1), F32),
                                lup=np.array([np.inf], F32))
    out = run_native(occluded, 1)
    assert u32(out[0, 6])[0] == 0x7F800000          # a9 = Inf*1 = +Inf


def test_pin_building_predicate_raw_values(generation_dir):
    def run(vb_value):
        args, aosoa = _pin_aosoa(1, 1,
                                 sh=np.full((1, 1), F32(1.0 - 2.0 ** -23)),
                                 vb=np.full((1, 1), F32(vb_value)),
                                 sun=np.ones((1, 1), np.bool_),
                                 shade=np.ones((1, 1), np.bool_),
                                 solar_gate=np.ones(1, np.bool_))
        return run_native(aosoa, 1)
    assert u32(run(2.0 ** 23)[0, 0])[0] == 0x40000000
    assert u32(run(1.0)[0, 0])[0] == 0x00000000


def test_pin_signed_zeros(generation_dir):
    args, aosoa = _pin_aosoa(1, 1, lup=np.array([F32(-0.0)]))
    out = run_native(aosoa, 1)
    assert u32(out[0, 6])[0] == 0x00000000 and not np.signbit(out[0, 6])
    args, aosoa = _pin_aosoa(1, 1, surface_sun=-0.0, surface_sh=-0.0)
    out = run_native(aosoa, 1)
    assert u32(out[0, 3])[0] == 0x00000000 and not np.signbit(out[0, 3])
    assert bitwise_equal(out, lw_primary_reference(**args))


def test_pin_reflection_divides_by_stored_pi_not_reciprocal(generation_dir):
    x = F32(11.000000953674316)
    args, aosoa = _pin_aosoa(1, 1, sh=np.zeros((1, 1), F32),
                             lup=np.array([F32(x * 2)], F32))
    out = run_native(aosoa, 1)
    assert u32(out[0, 6])[0] == 0x40601716
    assert u32(F32(x * F32(1.0 / np.pi)))[0] == 0x40601715   # forbidden path


def test_pin_f32_and_f64_surface_profiles_are_different_graphs(generation_dir):
    """Discriminator surface=1+2^-25, solid=[2^-24,1]: f64 profile gives
    a6 = 1+2^-23 (0x3F800001), f32 profile ties to even 1.0 (0x3F800000)."""
    s = 1 + 2.0 ** -25
    common = dict(vs=np.zeros((1, 2), F32),
                  solid=np.array([2.0 ** -24, 1.0], F32),
                  cosine=np.ones(2, F32), sine=np.ones(2, F32))
    _, aosoa64 = _pin_aosoa(1, 2, surface_sun=s, surface_sh=s, **common)
    _, aosoa32 = _pin_aosoa(1, 2, surface_sun=F32(s), surface_sh=F32(s),
                            **common)
    out64, out32 = run_native(aosoa64, 1), run_native(aosoa32, 1)
    assert u32(out64[0, 3])[0] == 0x3F800001
    assert u32(out32[0, 3])[0] == 0x3F800000
    assert not np.array_equal(out64.view(np.uint32), out32.view(np.uint32))


def test_pin_f64_accumulator_round_discriminator(generation_dir):
    """RN32(f64(a6)+c64) discriminator: surface=1+2^-25, solid=[2^24,1],
    cosine=1, veg on. Patch 0: c=2^24+2^-1 -> tie -> 2^24 (0x4B800000);
    patch 1 adds (1+2^-25)*1: f64 2^24+1+2^-25 -> RN32 2^24+1 (0x4B800001).
    An early-rounded f32 graph would stay 0x4B800000."""
    s = 1 + 2.0 ** -25
    args, aosoa = _pin_aosoa(
        1, 2, surface_sun=s, surface_sh=s,
        vs=np.zeros((1, 2), F32),
        solid=np.array([2.0 ** 24, 1.0], F32),
        cosine=np.ones(2, F32), sine=np.ones(2, F32))
    out = run_native(aosoa, 1)
    assert u32(out[0, 3])[0] == 0x4B800001
    assert bitwise_equal(out, lw_primary_reference(**args))


# ---------------------------------------------------------------------------
# N8-11 producer bit-identity: feeding the producer's output must give
# bit-identical results to feeding the oracle-constructed AoSoA.
# ---------------------------------------------------------------------------

def _raw_channel(dense, B, P):
    """PackedVisibility whose P patches are raw mode carrying dense's bits."""
    bits = np.ascontiguousarray(dense, F32).view(np.uint32)
    patches = [_EncodedPatch('raw', bits[:, p].astype('<u4').tobytes())
               for p in range(P)]
    return PackedVisibility((1, B, P), tuple(patches))


@pytest.mark.parametrize('P', (1, 3, 153))
@pytest.mark.parametrize('B', (1, 7, 9, 13))
def test_producer_output_feeds_consumer_bit_identically(B, P, generation_dir):
    args = adversarial_inputs(B, P, seed=1000 * B + P)
    expected = lw_primary_reference(**args)
    oracle_feed = to_aosoa(args, B)
    produced_feed = dict(oracle_feed)
    for name in ('sh', 'vs', 'vb'):
        channel = _raw_channel(args[name], B, P)
        produced = da.produce_block_aosoa(channel, 0, B, P, width=8)
        # producer layout == the dense bit patterns on every valid row
        assert np.array_equal(aosoa_rows(produced)[:B],
                              args[name].view(np.uint32)), (name, B, P)
        # N8-11 review note N6: consumers are fed the .view(np.float32) block
        produced_feed[name] = produced.view(np.float32)
    via_oracle = run_native(oracle_feed, B)
    via_produced = run_native(produced_feed, B)
    assert bitwise_equal(via_produced, expected), (B, P)
    assert bitwise_equal(via_produced, via_oracle), (B, P)


def test_producer_mixed_modes_feed(generation_dir):
    """binary/ternary/raw mode mixture: _decode is the ground truth for the
    dense values, then producer -> native == oracle(dense) == SERIAL(dense)."""
    B, P = 11, 6
    rng = np.random.default_rng(1234)
    channels = []
    for name, modes in (('sh', ('binary', 'raw', 'ternary')),
                        ('vs', ('ternary', 'binary', 'raw')),
                        ('vb', ('raw', 'ternary', 'binary'))):
        patches = []
        for i in range(P):
            mode = modes[i % len(modes)]
            if mode == 'raw':
                bits = rng.integers(0, 2 ** 32, size=B, dtype=np.uint64
                                    ).astype(np.uint32)
                payload = bits.astype('<u4').tobytes()
            elif mode == 'ternary':
                codes = rng.integers(0, 3, size=B).astype(np.uint8)
                padded = np.zeros((B + 3) // 4 * 4, dtype=np.uint8)
                padded[:B] = codes
                payload = (padded[0::4] | (padded[1::4] << 2)
                           | (padded[2::4] << 4) | (padded[3::4] << 6)).tobytes()
            else:
                codes = rng.integers(0, 2, size=B).astype(np.uint8)
                payload = np.packbits(codes, bitorder='little').tobytes()
            patches.append(_EncodedPatch(mode, payload))
        channels.append(PackedVisibility((1, B, P), tuple(patches)))

    dense = {name: _decode(*_descriptor(ch), 0, B, P)
             for name, ch in zip(('sh', 'vs', 'vb'), channels)}
    base = adversarial_inputs(B, P, seed=55)
    args = dict(base)
    args.update(dense)
    expected = lw_primary_reference(**args)

    feed = to_aosoa(args, B)
    for name, ch in zip(('sh', 'vs', 'vb'), channels):
        feed[name] = da.produce_block_aosoa(ch, 0, B, P,
                                            width=8).view(np.float32)
    assert bitwise_equal(run_native(feed, B), expected)
    assert bitwise_equal(run_native(feed, B), SERIAL(**args))


def test_caller_out_bitwise(generation_dir):
    """out= is filled in place (same object returned) with the same bits."""
    B, P = 13, 3
    args = adversarial_inputs(B, P, seed=1000 * B + P)
    feed = to_aosoa(args, B)
    expected = run_native(feed, B)
    out = np.full((B, 7), np.nan, dtype=F32)
    returned = lw_call(feed, B, out=out)
    assert returned is out
    assert bitwise_equal(out, expected)


def lw_call(feed, B, out):
    from solweig_light._native_dispatch import lw_native_aosoa
    return lw_native_aosoa.primary_aosoa(
        feed['sh'], feed['vs'], feed['vb'], feed['sun'], feed['shade'],
        feed['solid'], feed['sine'], feed['cosine'], feed['directions'],
        feed['gate'], feed['solar_gate'], feed['sky_down'], feed['sky_side'],
        feed['surface_sun'], feed['surface_sh'], feed['lup'],
        feed['reflection_factor'], B, out=out)
