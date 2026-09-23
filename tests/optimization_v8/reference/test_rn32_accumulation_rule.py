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
"""N8-04 (ii): the RN32 accumulation rule is an observable, not a style.

With float64 surface scalars the vegetation and sun/shade chains carry
float64 bits; the contract rounds ONCE, at the accumulator store:

    a = RN32( f64(a_prev) + c64 )            -- the current kernels

The forbidden spelling

    a = RN32( a_prev + RN32(c64) )           -- rounds the chain early

is bit-different on the discriminating input below. This file proves the
current kernels take the f64-then-round path and -- as a MUTATION CHECK with
teeth -- that a local NumPy mock of the forbidden spelling FAILS this same
assertion (see ``lw_reference_oracle.lw_primary_reference(...,
st_add_rule='round_chain_first')``).

Discriminating input (f64-surface profile), P=2, veg on (vs=0):
  surface_sh = surface_sun = s = 1 + 2^-25 (a float64 scalar)
  patch 0: solid=2^24, cosine=1 -> c0 = s*2^24 = 2^24 + 2^-1 exactly (f64);
           a6 = RN32(+0 + 2^24+0.5) = 2^24 (below the 2^24+1 midpoint;
           the f32 grid at 2^24 has ulp 2)
  patch 1: solid=1, cosine=1    -> c1 = s = 1 + 2^-25;
           contract: a6 = RN32(f64(2^24) + 1+2^-25) = RN32(2^24+1+2^-25)
                     -> strictly above the 2^24+1 tie midpoint -> 2^24+2
                     (bits 0x4B800001)
           mock:    RN32(c1) = 1.0 (1+2^-25 is below the 1+2^-24 midpoint),
                    a6 = RN32(2^24f + 1.0f) = exact tie -> round to even
                    -> 2^24 (bits 0x4B800000)
"""
import numpy as np

from lw_reference_oracle import (F32, bitwise_equal, kernel_pair,
                                 lw_primary_reference, u32)

PARALLEL, SERIAL = kernel_pair()

SURFACE = 1 + 2.0 ** -25          # float64 scalar, not float32-representable


def discriminator_args():
    return dict(
        sh=np.zeros((1, 2), F32), vs=np.zeros((1, 2), F32),
        vb=np.ones((1, 2), F32),
        sun=np.zeros((1, 2), np.bool_), shade=np.zeros((1, 2), np.bool_),
        solid=np.array([2.0 ** 24, 1.0], F32),
        sine=np.ones(2, F32), cosine=np.ones(2, F32),
        directions=np.zeros((2, 4), F32), gate=np.zeros((2, 4), np.bool_),
        solar_gate=np.zeros(2, np.bool_),
        sky_down=np.zeros(2, F32), sky_side=np.zeros(2, F32),
        surface_sun=SURFACE, surface_sh=SURFACE,
        lup=np.zeros(1, F32), reflection_factor=F32(1.0))


def test_kernel_takes_f64_then_round_path():
    """The current kernels produce 0x4B800001 (2^24+2): the single-rounding
    f64-then-RN32 path, for the vegetation side chain (a6, column 3)."""
    args = discriminator_args()
    for kernel in (PARALLEL, SERIAL):
        out = kernel(**args)
        assert u32(out[0, 3])[0] == 0x4B800001, 'a6 must be 2^24+2'
        assert bitwise_equal(
            out, lw_primary_reference(surface_st='f64', **args))


def test_down_chain_follows_same_rule():
    """The vegetation DOWN chain (a1) and the else-branch shade DOWN chain
    (a2, building is true here since sh=0, vb=1) both follow the same rule:
    each is 2^24+2, so the left-fold out0 = 2^25+4."""
    args = discriminator_args()
    out = SERIAL(**args)
    assert u32(out[0, 0])[0] == 0x4C000001      # 2^25+4 = (2^24+2)+(2^24+2)


# ---------------------------------------------------------------------------
# MUTATION CHECK (teeth). The mock below is a deliberate wrong-order
# reimplementation kept ONLY in this test to prove the discriminator can
# fail. It must NOT be used as a reference by anything else.
# ---------------------------------------------------------------------------

def test_mutation_check_forbidden_rule_fails_the_discriminator():
    """The forbidden RN32(a + RN32(c)) mock must DISAGREE with the kernels
    on the discriminating input (proves this file has teeth), while still
    agreeing on a benign input (proves it is a faithful single-rule
    mutation, not a broken kernel)."""
    args = discriminator_args()
    kernel_out = SERIAL(**args)
    mutated = lw_primary_reference(surface_st='f64', st_add_rule='round_chain_first',
                                   **args)
    assert not bitwise_equal(kernel_out, mutated), (
        'discriminator lost its teeth: the forbidden early-round rule no '
        'longer differs from the kernel path')
    assert u32(mutated[0, 3])[0] == 0x4B800000   # mock lands on 2^24

    benign = dict(args)
    benign.update(solid=np.ones(2, F32), surface_sun=2.0, surface_sh=2.0)
    assert bitwise_equal(
        SERIAL(**benign),
        lw_primary_reference(surface_st='f64',
                             st_add_rule='round_chain_first', **benign)), (
        'mock disagrees on a benign input; it is no longer a single-rule '
        'mutation')
