#SOLWEIG-GPU: GPU-accelerated SOLWEIG model for urban thermal comfort simulation
#Copyright (C) 2022–2025 Harsh Kamth and Naveen Sudharsan

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
"""N8-12 producer identity: the B control consumes N8-11's ACTUAL output.

Feeding ``produce_blocks_aosoa`` output and feeding an oracle-constructed
AoSoA of the same dense bits must give identical results (asserted on the
buffers' valid lanes AND on the kernel outputs), for both producer orders
and all encoding regimes -- so the A/B/C leaf comparison measures the
consumer, not the feed. Padding lanes are poisoned after production to
prove they are never read; the producer's uninitialized padding is
exercised by construction (np.empty).
"""
import numpy as np
import pytest

from solweig_light._native_dispatch import direct_aosoa as da
from solweig_light._native_dispatch import lw_b_control as bc
from lw_reference_oracle import F32, bitwise_equal, lw_primary_reference
from solweig_light.geometry.visibility import VisibilityBuilder
from solweig_light.geometry.visibility_compiled import _decode, _descriptor
from solweig_light.radiation.cylinder_longwave import _longwave_primary_serial
from solweig_light.radiation.patch_radiation import _classes, patch_geometry

from test_b_control_bitexact import pack_aosoa, pack_bool

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
    """Encoded channel plus the exact dense bits it must round-trip."""
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


def dense_patch_args(rng, pixels, patches, surface_st):
    """Patch-level arguments (everything except the packed channels)."""
    count = patches
    solid = rng.uniform(0.001, 0.05, count).astype(np.float32)
    sine = rng.uniform(-1, 1, count).astype(np.float32)
    cosine = rng.uniform(-1, 1, count).astype(np.float32)
    sky_down = rng.uniform(300, 500, count).astype(np.float32)
    sky_side = rng.uniform(300, 500, count).astype(np.float32)
    surface = (float(rng.uniform(300, 480)), float(rng.uniform(290, 330))) \
        if surface_st == 'f64' else (F32(rng.uniform(300, 480)), F32(rng.uniform(290, 330)))
    return dict(solid=solid, sine=sine, cosine=cosine,
                directions=np.zeros((count, 4), F32),
                gate=np.zeros((count, 4), np.bool_),
                solar_gate=rng.random(count) < 0.5,
                sky_down=sky_down, sky_side=sky_side,
                surface_sun=surface[0], surface_sh=surface[1],
                lup=rng.choice(VALUE_POOL, size=pixels).astype(np.float32),
                reflection_factor=np.float32(rng.uniform(0.1, 0.6)))


@pytest.mark.parametrize('order', ('patchmajor', 'blocked'))
@pytest.mark.parametrize('regime', sorted(REGIME))
@pytest.mark.parametrize('patches', [1, 3, 13])
@pytest.mark.parametrize('pixels', [0, 1, 7, 8, 9, 13, 128])
@pytest.mark.parametrize('surface_st', ['f64', 'f32'])
def test_producer_output_feeds_bit_identically(pixels, patches, regime,
                                               order, surface_st):
    """B kernel on produce_blocks_aosoa output == B kernel on the
    oracle-constructed AoSoA == oracle == frozen kernel, bitwise."""
    rng = np.random.default_rng(2_000_003 * pixels + 1009 * patches
                                + REGIME[regime] + (0 if surface_st == 'f64' else 7919))
    geometry = patch_geometry(vault_table(patches))
    channels, planes = zip(*(seeded_channel(rng, pixels, patches, regime)
                             for _ in range(3)))
    shared = dense_patch_args(rng, pixels, patches, surface_st)
    produced = da.produce_blocks_aosoa(*channels, 0, pixels, patches,
                                       width=8, order=order)
    dense = tuple(_decode(*_descriptor(channel), 0, pixels, patches)
                  for channel in channels)
    for decoded, plane in zip(dense, planes):
        assert np.array_equal(decoded.view(np.uint32), plane.view(np.uint32))
    manual = tuple(pack_aosoa(block) for block in dense)
    # The producer's valid lanes carry exactly the oracle-constructed bits.
    for prod, man in zip(produced, manual):
        lanes_prod = prod.transpose(0, 2, 1).reshape(-1, patches)[:pixels]
        lanes_man = man.transpose(0, 2, 1).reshape(-1, patches)[:pixels]
        assert np.array_equal(lanes_prod, lanes_man)
    asvf = rng.uniform(0.02, 1.0, size=pixels).astype(np.float32)
    altitude, azimuth = tensor32(rng.uniform(5, 80)), tensor32(rng.uniform(0, 360))
    sun, shade = da.classify_block_aosoa(altitude, azimuth, geometry, asvf,
                                         0, pixels)
    ref_masks = _classes(altitude, azimuth, geometry, asvf, 0, pixels)
    for direct, ref in zip((sun, shade), ref_masks):
        lanes = direct.transpose(0, 2, 1).reshape(-1, patches)[:pixels]
        assert np.array_equal(lanes, ref)
    kwargs = dict(sun=sun, shade=shade, **shared)
    out_prod = bc.lw_primary_b(*produced, rows=pixels, **kwargs)
    out_manual = bc.lw_primary_b(*manual, rows=pixels, **kwargs)
    assert bitwise_equal(out_prod, out_manual)
    expected = lw_primary_reference(surface_st=surface_st, sh=dense[0],
                                    vs=dense[1], vb=dense[2],
                                    sun=ref_masks[0], shade=ref_masks[1],
                                    **shared)
    assert bitwise_equal(out_prod, expected)
    frozen = _longwave_primary_serial(dense[0], dense[1], dense[2],
                                      ref_masks[0], ref_masks[1], **shared)
    assert bitwise_equal(out_prod, frozen)


def test_padding_lanes_poisoned_after_production():
    """Poison written into the producer's unwritten TAIL-GANG padding lanes
    must not change any valid output. 13 rows at W=8 give G=2 with lanes 5..7
    of gang 1 as padding (rows 13..15 of 16); the poison targets exactly
    those lanes (n8_30_review_n8_12 note F1: the earlier block[:, :, 13:]
    slice was EMPTY at W=8 and therefore a vacuous no-op). Benign finite
    arguments keep isfinite meaningful as a leak probe."""
    pixels, patches = 13, 3
    width = 8
    tail = pixels % width
    assert -(-pixels // width) == 2 and tail == 5   # guard the geometry claim
    rng = np.random.default_rng(203)
    geometry = patch_geometry(vault_table(patches))
    channel, _ = seeded_channel(rng, pixels, patches, 'codebook')
    shared = dict(
        solid=np.full(patches, 0.01, F32), sine=np.full(patches, 0.5, F32),
        cosine=np.full(patches, 0.5, F32),
        directions=np.zeros((patches, 4), F32),
        gate=np.zeros((patches, 4), np.bool_),
        solar_gate=np.ones(patches, np.bool_),
        sky_down=np.full(patches, 400.0, F32), sky_side=np.full(patches, 390.0, F32),
        surface_sun=350.0, surface_sh=320.0,
        lup=np.full(pixels, 400.0, F32), reflection_factor=np.float32(0.3))
    produced = list(da.produce_blocks_aosoa(channel, channel, channel, 0, pixels,
                                            patches))
    asvf = rng.uniform(0.02, 1.0, size=pixels).astype(np.float32)
    sun, shade = da.classify_block_aosoa(tensor32(35), tensor32(140), geometry,
                                         asvf, 0, pixels)
    clean = bc.lw_primary_b(*produced, rows=pixels, sun=sun, shade=shade, **shared)
    for block in produced:
        block[-1, :, tail:] = np.uint32(0x7FC00000)  # NaN poison, tail gang only
    sun[-1, :, tail:] = True
    shade[-1, :, tail:] = True
    poisoned = bc.lw_primary_b(*produced, rows=pixels, sun=sun, shade=shade,
                               **shared)
    assert bitwise_equal(clean, poisoned)
    assert np.isfinite(clean).all()
    # Sentinel survives the kernel run: the padding lanes were never touched.
    for block in produced:
        assert (block[-1, :, tail:] == np.uint32(0x7FC00000)).all()
    assert sun[-1, :, tail:].all() and shade[-1, :, tail:].all()
