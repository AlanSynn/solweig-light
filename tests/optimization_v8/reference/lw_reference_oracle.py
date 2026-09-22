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
"""N8-04 frozen NumPy reference oracle for the longwave primary reducer.

This module is an INDEPENDENT re-implementation of the typed operation graph
of ``solweig_light.radiation.cylinder_longwave._longwave_primary`` and
``_longwave_primary_serial`` (frozen at HEAD 16cdc56c, kernel bodies identical
to the B7-02 freeze at dca2035c, reducer blob 27ba6ce4...). It exists so that
N8-12 (Numba B) and N8-13 (native C) candidates can be gated against the
exact graph BEFORE any new kernel is written: candidate == oracle, bitwise
(uint32 view), on every admitted input.

Typed-graph rules encoded here (see
optimization_v8_native_default/evidence/contract/n8_04_typed_lw_contract.md):

* ten float32 accumulators a0..a9, zero-initialized (+0.0, bits 0x00000000);
* two ordered patch sweeps, p = 0..P-1, left-fold accumulation;
* sweep 1: sky/vegetation/wall terms; solar_gate selects a REAL branch (the
  inactive expressions are not evaluated);
* reflection reads the COMPLETED first-sweep sky accumulator a0 and lup:
  reflected = RN32(RN32(RN32(RN32(a0+lup)*factor)*RN32(.5))/RN32(pi)),
  with pi the exact stored float32 0x40490FDB and a true IEEE division --
  never a reciprocal multiply;
* sweep 2: occlusion-mask multiply (0.0f/1.0f NUMBER multiply, so 0*Inf = NaN
  and signed-zero propagation are preserved, never a branch);
* surface-scalar profiles: with float64 surface scalars the vegetation and
  sun/shade chains are computed in float64 and rounded ONCE at the
  accumulator add -- a = RN32(f64(a) + c64); with float32 surface scalars the
  chains stay float32 throughout. These are DIFFERENT typed graphs and can
  give different bits for the same supplied numeric value;
* predicates: sky = (sh==1)&(vs==1); veg = (vs==0)|(vb==0);
  building = (RN32(1f-sh)*vb) == 1 -- an exact comparison on the float32
  subtract/product, so raw non-0/1 sh/vb values are meaningful;
* output: two left-fold combinations (((a0+a1)+a2)+a3)+a4 and
  (((a5+a6)+a7)+a8)+a9, then columns 2..6 = a5..a9 verbatim.

The ``st_add_rule='round_chain_first'`` mode is a DELIBERATE MUTATION kept
only to give the RN32-rule test teeth: it implements the forbidden
a = RN32(a + RN32(c)) and must differ from the kernels on the discriminating
input. Never use it as a reference.
"""
import numpy as np

F32 = np.float32
F64 = np.float64
PI32 = F32(np.pi)            # exact stored bits 0x40490FDB
HALF32 = F32(0.5)


def lw_primary_reference(sh, vs, vb, sun, shade, solid, sine, cosine,
                         directions, gate, solar_gate, sky_down, sky_side,
                         surface_sun, surface_sh, lup, reflection_factor,
                         surface_st='f64', st_add_rule='f64_then_round'):
    """Exact typed-graph reference; returns float32 [B, 7].

    ``surface_st``: 'f64' (float64 surface scalars -- the real accepted
    pipeline specialization) or 'f32' (float32 surface scalars -- the
    synthetic specialization also admitted by the B7-02 freeze).

    ``st_add_rule``: 'f64_then_round' is the contract rule
    a = RN32(f64(a) + c). 'round_chain_first' is the MUTATION
    a = RN32(a + RN32(c)) kept for test teeth; it is NOT the contract.
    """
    if st_add_rule not in ('f64_then_round', 'round_chain_first'):
        raise ValueError(f'unknown st_add_rule {st_add_rule!r}')
    if surface_st == 'f64':
        ST = F64
    elif surface_st == 'f32':
        ST = F32
    else:
        raise ValueError(f'unknown surface_st {surface_st!r}')
    # The mutation is only meaningful in the f64-surface profile (the chain
    # carries float64 bits that the wrong rule would round early).
    if st_add_rule == 'round_chain_first' and ST is not F64:
        raise ValueError('round_chain_first mutation applies to f64 surface only')

    # Invalid/overflow operations are VALUES on this graph (0*Inf = NaN,
    # Inf+finite = Inf); the kernels compute them silently, so the oracle
    # must too.
    with np.errstate(all='ignore'):
        return _lw_primary_reference_core(
            sh, vs, vb, sun, shade, solid, sine, cosine, directions, gate,
            solar_gate, sky_down, sky_side, surface_sun, surface_sh, lup,
            reflection_factor, ST, st_add_rule)


def _lw_primary_reference_core(sh, vs, vb, sun, shade, solid, sine, cosine,
                               directions, gate, solar_gate, sky_down,
                               sky_side, surface_sun, surface_sh, lup,
                               reflection_factor, ST, st_add_rule):
    sh = np.asarray(sh, F32); vs = np.asarray(vs, F32); vb = np.asarray(vb, F32)
    solid = np.asarray(solid, F32); sine = np.asarray(sine, F32)
    cosine = np.asarray(cosine, F32)
    sky_down = np.asarray(sky_down, F32); sky_side = np.asarray(sky_side, F32)
    lup = np.asarray(lup, F32)
    factor = F32(reflection_factor)
    B, P = sh.shape
    surf_sun = ST(surface_sun)
    surf_sh = ST(surface_sh)

    def st_add(acc_col, chain):
        """Accumulator add for an ST-typed chain, per the selected rule."""
        if st_add_rule == 'f64_then_round':
            # Contract: a = RN32(f64(a) + c)  (single rounding at the store)
            return (acc_col.astype(ST) + chain).astype(F32)
        # MUTATION (test teeth only): a = RN32(a + RN32(c))
        return (acc_col + chain.astype(F32)).astype(F32)

    acc = np.zeros((B, 10), F32)
    for p in range(P):
        shv = sh[:, p]; vsv = vs[:, p]; vbv = vb[:, p]
        sky = (shv == F32(1.0)) & (vsv == F32(1.0))
        veg = (vsv == F32(0.0)) | (vbv == F32(0.0))
        building = (F32(F32(1.0) - shv) * vbv) == F32(1.0)
        skyf = sky.astype(F32)
        vegf = veg.astype(ST)
        buif = building.astype(ST)
        acc[:, 0] = acc[:, 0] + skyf * sky_down[p]
        acc[:, 5] = acc[:, 5] + skyf * sky_side[p]
        sd = ST(solid[p]); sn = ST(sine[p]); cs = ST(cosine[p])
        vegetation_side = (((surf_sh * sd) * cs) * vegf)
        vegetation_down = (((surf_sh * sd) * sn) * vegf)
        acc[:, 6] = st_add(acc[:, 6], vegetation_side)
        acc[:, 1] = st_add(acc[:, 1], vegetation_down)
        if bool(solar_gate[p]):
            sunf = np.asarray(sun, np.bool_)[:, p].astype(ST)
            shaf = np.asarray(shade, np.bool_)[:, p].astype(ST)
            sun_side = ((((surf_sun * sunf) * sd) * cs) * buif)
            shade_side = ((((surf_sh * shaf) * sd) * cs) * buif)
            sun_down = ((((surf_sun * sunf) * sd) * sn) * buif)
            shade_down = ((((surf_sh * shaf) * sd) * sn) * buif)
            acc[:, 8] = st_add(acc[:, 8], sun_side)
            acc[:, 7] = st_add(acc[:, 7], shade_side)
            acc[:, 3] = st_add(acc[:, 3], sun_down)
            acc[:, 2] = st_add(acc[:, 2], shade_down)
        else:
            shade_side = (((surf_sh * sd) * cs) * buif)
            shade_down = (((surf_sh * sd) * sn) * buif)
            acc[:, 7] = st_add(acc[:, 7], shade_side)
            acc[:, 2] = st_add(acc[:, 2], shade_down)
    # Reflection reads the completed ordered first-sweep sky accumulator.
    reflected = (acc[:, 0] + lup) * factor * HALF32 / PI32
    for p in range(P):
        shv = sh[:, p]; vsv = vs[:, p]; vbv = vb[:, p]
        occl = (shv == F32(0.0)) | (vsv == F32(0.0)) | (vbv == F32(0.0))
        occlf = occl.astype(F32)
        side = ((reflected * solid[p]) * cosine[p]) * occlf
        down = ((reflected * solid[p]) * sine[p]) * occlf
        acc[:, 9] = acc[:, 9] + side
        acc[:, 4] = acc[:, 4] + down
    output = np.zeros((B, 7), F32)
    output[:, 0] = (((acc[:, 0] + acc[:, 1]) + acc[:, 2]) + acc[:, 3]) + acc[:, 4]
    output[:, 1] = (((acc[:, 5] + acc[:, 6]) + acc[:, 7]) + acc[:, 8]) + acc[:, 9]
    output[:, 2:7] = acc[:, 5:10]
    return output


def bitwise_equal(a, b):
    """Exact float32 equality including NaN payloads and signed zeros."""
    a = np.asarray(a, F32); b = np.asarray(b, F32)
    if a.shape != b.shape:
        return False
    return np.array_equal(a.view(np.uint32), b.view(np.uint32))


def u32(x):
    """uint32 bit view of a float32 value/array (scalars allowed)."""
    return np.atleast_1d(np.asarray(x, F32)).view(np.uint32)


def kernel_pair():
    """(parallel, serial) baseline kernels of the frozen family."""
    from solweig_light.radiation import cylinder_longwave as cyl
    return cyl._longwave_primary, cyl._longwave_primary_serial
