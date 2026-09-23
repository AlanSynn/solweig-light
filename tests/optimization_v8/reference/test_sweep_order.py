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
"""N8-04 (iii): the p=0..P-1 left-fold sweep order is an observable.

Both sweeps accumulate with float32 adds in patch order; float addition is
not associative, so reordering patches can change the result. Any candidate
(N8-12/N8-13) must preserve the exact order -- no sorted-by-magnitude sweep,
no pairwise/tree reduction, no reassociation.

Discriminating input (sweep 1): sky true on three patches with sky_down
values [2^24, 1, 1] (visibility sh=vs=vb=1, veg off, building off, gates
off):
  ordered  [2^24, 1, 1]: ((0+2^24)+1)+1 -- both adds hit exact ties at the
      2^24 grid midpoint (ulp 2) and round to even -> a0 = 2^24 (0x4B800000)
  permuted [1, 1, 2^24]: (0+1)+1 = 2; 2+2^24 = 2^24+2 is exactly
      representable -> a0 = 2^24+2 (0x4B800001)

Discriminating input (sweep 2): all patches occluded (sh=0, mask true),
lup = 2*pi32 so reflected = RN32(pi32/pi32) = 1.0 exactly, and the per-patch
addends are ((1.0*solid_p)*1.0)*1.0f = solid_p: the same [2^24, 1, 1] vs
[1, 1, 2^24] multiset lands differently in a9 (column 6).
"""
import numpy as np

from lw_reference_oracle import F32, bitwise_equal, kernel_pair, u32

PARALLEL, SERIAL = kernel_pair()


def ordered_args(sky_down):
    sky_down = np.asarray(sky_down, F32)
    P = sky_down.size
    return dict(
        sh=np.ones((1, P), F32), vs=np.ones((1, P), F32),
        vb=np.ones((1, P), F32),
        sun=np.zeros((1, P), np.bool_), shade=np.zeros((1, P), np.bool_),
        solid=np.ones(P, F32), sine=np.ones(P, F32), cosine=np.ones(P, F32),
        directions=np.zeros((P, 4), F32), gate=np.zeros((P, 4), np.bool_),
        solar_gate=np.zeros(P, np.bool_),
        sky_down=sky_down, sky_side=np.zeros(P, F32),
        surface_sun=1.0, surface_sh=1.0,
        lup=np.zeros(1, F32), reflection_factor=F32(0.0))


def test_sweep_one_order_changes_bits():
    """The constructed pair differs in exact bits: order is an observable."""
    ordered = SERIAL(**ordered_args([2.0 ** 24, 1.0, 1.0]))
    permuted = SERIAL(**ordered_args([1.0, 1.0, 2.0 ** 24]))
    assert u32(ordered[0, 0])[0] == 0x4B800000        # a0 = 2^24
    assert u32(permuted[0, 0])[0] == 0x4B800001       # a0 = 2^24+2
    assert not bitwise_equal(ordered, permuted)
    for out in (ordered, permuted):                   # both kernels agree
        args = ordered_args([2.0 ** 24, 1.0, 1.0])
        assert bitwise_equal(PARALLEL(**args), SERIAL(**args))


def test_sweep_two_order_changes_bits():
    """Reflected sweep: same multiset of addends, different order, different
    a9 bits (reflected is exactly 1.0 via lup = 2*pi32)."""

    def run(solid):
        args = ordered_args([0.0, 0.0, 0.0])
        args['sh'] = np.zeros((1, 3), F32)            # mask true on all
        args['lup'] = np.array([F32(2.0) * F32(np.pi)], F32)
        args['reflection_factor'] = F32(1.0)
        args['solid'] = np.asarray(solid, F32)
        return SERIAL(**args)

    ordered = run([2.0 ** 24, 1.0, 1.0])
    permuted = run([1.0, 1.0, 2.0 ** 24])
    assert u32(ordered[0, 6])[0] == 0x4B800000        # a9 = 2^24
    assert u32(permuted[0, 6])[0] == 0x4B800001       # a9 = 2^24+2
    assert not bitwise_equal(ordered, permuted)


def _permute_patches(args, permutation):
    """Consistently permute every patch-indexed input."""
    perm = np.asarray(permutation)
    out = dict(args)
    for name in ('sh', 'vs', 'vb', 'sun', 'shade'):
        out[name] = np.ascontiguousarray(args[name][:, perm])
    for name in ('solid', 'sine', 'cosine', 'solar_gate', 'sky_down',
                 'sky_side'):
        out[name] = np.ascontiguousarray(args[name][perm])
    out['directions'] = np.ascontiguousarray(args['directions'][perm, :])
    out['gate'] = np.ascontiguousarray(args['gate'][perm, :])
    return out


def test_permuted_inputs_reproduce_permuted_kernel_result():
    """Sanity for the observable claim: permuting the INPUT patches equals
    running the kernel on the permuted data -- the bit differences above
    come from accumulation order, not hidden patch identity."""
    args = ordered_args([2.0 ** 24, 1.0, 1.0])
    direct = SERIAL(**_permute_patches(args, (1, 2, 0)))
    expected = SERIAL(**ordered_args([1.0, 1.0, 2.0 ** 24]))
    assert bitwise_equal(direct, expected)
    args = ordered_args([2.0 ** 24, 1.0, 1.0])
    assert bitwise_equal(SERIAL(**args),
                         SERIAL(**_permute_patches(_permute_patches(args, (0, 2, 1)), (0, 2, 1))))
