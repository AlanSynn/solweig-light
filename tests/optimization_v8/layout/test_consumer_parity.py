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
"""N8-11 end-to-end consumer parity against the N8-04 frozen contract.

encode -> produce_block_aosoa -> classify_block_aosoa -> trivial Numba
consumer (lw_primary_aosoa_serial) must reproduce the independent NumPy
oracle AND the frozen baseline kernel bitwise (uint32 view, all seven
output columns) on adversarial small inputs. This proves the lane layout
carries the exact decoder bits into the frozen reduction graph.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

from solweig_light._native_dispatch import direct_aosoa as da
from solweig_light.geometry.visibility import VisibilityBuilder
from solweig_light.geometry.visibility_compiled import _decode, _descriptor
from solweig_light.radiation.cylinder_longwave import _longwave_primary_serial
from solweig_light.radiation.patch_radiation import _classes, patch_geometry

_REFERENCE = Path(__file__).resolve().parents[1] / 'reference'
if str(_REFERENCE) not in sys.path:
    sys.path.insert(0, str(_REFERENCE))
from lw_reference_oracle import lw_primary_reference  # noqa: E402

F32 = np.float32
VALUE_POOL = np.array([
    0.0, -0.0, 1.0, -1.0, 2.0, 0.5, -7.3, 2.0 ** 24, 2.0 ** -24, 2.0 ** -25,
    1.0 + 2.0 ** -23, 1.0 - 2.0 ** -24, 3.4028235e38, 1.1754944e-38,
    1.4012985e-45, np.inf, -np.inf, np.nan, 6.022047e23, 0.1,
], dtype=np.float32)
CODEBOOK = np.array([0.0, 1.0, 2.0], dtype=np.float32)
REGIME = {'raw': 0, 'codebook': 1, 'mixed': 2}


def tensor32(value):
    return np.array(np.float32(value))


def seeded_channel(rng, pixels, patches, regime):
    """Encoded channel plus the exact dense bits it must round-trip.

    ``raw`` forces arbitrary-bit payloads (nonfinite, subnormal, signed
    zero); ``codebook`` encodes 0/1/2 compactly; ``mixed`` alternates the
    two pools per patch.
    """
    planes = np.empty((pixels, patches), dtype=np.float32)
    for patch in range(patches):
        pool = VALUE_POOL if regime in ('raw', 'mixed') and (regime == 'raw' or patch % 2) else CODEBOOK
        planes[:, patch] = rng.choice(pool, size=pixels)
    builder = VisibilityBuilder((1, pixels, patches))
    for patch in range(patches):
        builder.append(np.ascontiguousarray(planes[:, patch]).reshape(1, pixels))
    return builder.finish(), planes


def vault_table(patches):
    return np.column_stack((np.full(patches, 30.0, dtype=np.float32),
                            np.linspace(0.0, 350.0, max(patches, 1),
                                        dtype=np.float32)[:patches]))


@pytest.mark.parametrize('regime', sorted(REGIME))
@pytest.mark.parametrize('patches', [1, 3, 13])
@pytest.mark.parametrize('pixels', [0, 1, 7, 8, 9, 13, 128])
@pytest.mark.parametrize('surface_st', ['f64', 'f32'])
def test_consumer_matches_oracle_and_frozen_kernel(pixels, patches, regime, surface_st):
    rng = np.random.default_rng(1_000_003 * pixels + 1009 * patches + REGIME[regime]
                                + (0 if surface_st == 'f64' else 7919))
    geometry = patch_geometry(vault_table(patches))
    channel, _ = seeded_channel(rng, pixels, patches, regime)
    width = 8
    sh = da.produce_block_aosoa(channel, 0, pixels, patches, width=width).view(np.float32)
    vs = da.produce_block_aosoa(channel, 0, pixels, patches, width=width).view(np.float32)
    vb = da.produce_block_aosoa(channel, 0, pixels, patches, width=width).view(np.float32)
    altitude, azimuth = tensor32(rng.uniform(5, 80)), tensor32(rng.uniform(0, 360))
    asvf = rng.uniform(0.02, 1.0, size=pixels).astype(np.float32)
    sun, shade = da.classify_block_aosoa(altitude, azimuth, geometry, asvf, 0, pixels)
    dense = _decode(*_descriptor(channel), 0, pixels, patches)
    reference_masks = _classes(altitude, azimuth, geometry, asvf, 0, pixels)
    count = patches
    solid = rng.uniform(0.001, 0.05, count).astype(np.float32)
    sine = rng.uniform(-1, 1, count).astype(np.float32)
    cosine = rng.uniform(-1, 1, count).astype(np.float32)
    directions = rng.uniform(-1, 1, (count, 4)).astype(np.float32)
    gate = rng.random((count, 4)) < 0.5
    solar_gate = rng.random(count) < 0.5
    sky_down = rng.uniform(300, 500, count).astype(np.float32)
    sky_side = rng.uniform(300, 500, count).astype(np.float32)
    lup = rng.choice(VALUE_POOL, size=max(pixels, 1))[:pixels].astype(np.float32)
    factor = np.float32(rng.uniform(0.1, 0.6))
    surface = (float(rng.uniform(300, 480)), float(rng.uniform(290, 330))) \
        if surface_st == 'f64' else (F32(rng.uniform(300, 480)), F32(rng.uniform(290, 330)))
    produced = da.lw_primary_aosoa_serial(sh, vs, vb, sun, shade, solid, sine, cosine,
                                          directions, gate, solar_gate, sky_down, sky_side,
                                          surface[0], surface[1], lup, factor, pixels)
    oracle = lw_primary_reference(dense, dense.copy(), dense.copy(),
                                  reference_masks[0], reference_masks[1], solid, sine,
                                  cosine, directions, gate, solar_gate, sky_down, sky_side,
                                  surface[0], surface[1], lup, factor,
                                  surface_st=surface_st)
    frozen = _longwave_primary_serial(dense, dense.copy(), dense.copy(),
                                      reference_masks[0], reference_masks[1], solid, sine,
                                      cosine, directions, gate, solar_gate, sky_down,
                                      sky_side, surface[0], surface[1], lup, factor)
    assert np.array_equal(produced.view(np.uint32), oracle.view(np.uint32))
    assert np.array_equal(produced.view(np.uint32), frozen.view(np.uint32))


def test_consumer_reflects_inf_mask_observables():
    """Pinned discriminator: with reflected = Inf, visible patches give
    NaN (Inf*0) and occluded patches +Inf (Inf*1) in the folded col-0."""
    pixels, patches = 13, 1
    rng = np.random.default_rng(101)
    geometry = patch_geometry(vault_table(patches))
    channel, planes = seeded_channel(rng, pixels, patches, 'codebook')
    sh = da.produce_block_aosoa(channel, 0, pixels, patches).view(np.float32)
    sun, shade = da.classify_block_aosoa(tensor32(35), tensor32(140), geometry,
                                         np.full(pixels, 0.5, np.float32), 0, pixels)
    dense = _decode(*_descriptor(channel), 0, pixels, patches)
    masks = _classes(tensor32(35), tensor32(140), geometry,
                     np.full(pixels, 0.5, np.float32), 0, pixels)
    one = np.ones(patches, np.float32)
    gate = np.ones((patches, 4), bool)
    solar_gate = np.zeros(patches, bool)
    sky_down = np.zeros(patches, np.float32)
    lup = np.full(pixels, np.inf, np.float32)  # a0 + lup = Inf -> reflected = Inf
    produced = da.lw_primary_aosoa_serial(sh, sh, sh, sun, shade, one, one, one,
                                          np.ones((patches, 4), np.float32), gate,
                                          solar_gate, sky_down, sky_down, 1.0, 1.0,
                                          lup, np.float32(0.5), pixels)
    oracle = lw_primary_reference(dense, dense.copy(), dense.copy(), masks[0], masks[1],
                                  one, one, one, np.ones((patches, 4), np.float32), gate,
                                  solar_gate, sky_down, sky_down, 1.0, 1.0, lup,
                                  np.float32(0.5))
    assert np.array_equal(produced.view(np.uint32), oracle.view(np.uint32))
    visible = dense[:, 0] == 2  # sh=vs=vb=2: no channel is 0 -> mask false
    occluded = dense[:, 0] == 0
    assert np.isnan(produced[visible, 0]).all()
    assert (produced[occluded, 0] == np.inf).all()


def test_consumer_reads_only_valid_lanes():
    """Gang padding poison must never reach the consumer's arithmetic."""
    pixels, patches = 13, 3   # 13 rows -> gangs=2, lanes 13..15 padding
    rng = np.random.default_rng(103)
    geometry = patch_geometry(vault_table(patches))
    channel, _ = seeded_channel(rng, pixels, patches, 'mixed')
    sh = da.produce_block_aosoa(channel, 0, pixels, patches).view(np.float32)
    vs = da.produce_block_aosoa(channel, 0, pixels, patches).view(np.float32)
    vb = da.produce_block_aosoa(channel, 0, pixels, patches).view(np.float32)
    asvf = rng.uniform(0.02, 1.0, size=pixels).astype(np.float32)
    sun, shade = da.classify_block_aosoa(tensor32(35), tensor32(140), geometry,
                                         asvf, 0, pixels)
    solid = np.full(patches, 0.01, np.float32)
    trig = np.full(patches, 0.5, np.float32)
    gate = np.ones((patches, 4), bool)
    solar = np.ones(patches, bool)
    sky = np.full(patches, 400.0, np.float32)
    lup = np.full(pixels, 400.0, np.float32)
    clean = da.lw_primary_aosoa_serial(sh.copy(), vs.copy(), vb.copy(), sun.copy(),
                                       shade.copy(), solid, trig, trig,
                                       np.ones((patches, 4), np.float32), gate, solar,
                                       sky, sky, 350.0, 320.0, lup, np.float32(0.3),
                                       pixels)
    # Poison the real tail padding: last gang, lanes >= pixels % W. A lane-axis
    # [:, :, 13:] slice on [G, P, W=8] is empty — F1 note, n8_30 review of N8-12.
    tail = pixels % 8
    assert sh[-1, :, tail:].size == (8 - tail) * patches  # poison is non-vacuous
    sh[-1, :, tail:] = np.float32(1e30)
    vs[-1, :, tail:] = np.float32(1e30)
    vb[-1, :, tail:] = np.float32(1e30)
    sun[-1, :, tail:] = True
    shade[-1, :, tail:] = True
    produced = da.lw_primary_aosoa_serial(sh, vs, vb, sun, shade, solid, trig, trig,
                                          np.ones((patches, 4), np.float32), gate, solar,
                                          sky, sky, 350.0, 320.0, lup, np.float32(0.3),
                                          pixels)
    assert produced.shape == (pixels, 7)
    assert np.array_equal(produced.view(np.uint32), clean.view(np.uint32)), \
        'padding lanes leaked into valid outputs'
    assert np.isfinite(produced).all()
