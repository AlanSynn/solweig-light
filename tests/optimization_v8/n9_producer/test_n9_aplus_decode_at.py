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
"""N9 F1D A-plus comparator tests.

The A-plus variant of the shipped row-A decode (``_decode_at_plus`` and the
transcribed fused kernels) must be BITWISE identical to the A8 control on
small inputs: per-element decode equality over all modes, fused serial and
parallel output equality, and unchanged preflight error observability. The
A-plus module is never dispatched; these tests are its only consumer.
"""
import numpy as np
import pytest

from solweig_light._native_dispatch.aplus_decode import (
    _decode_at_plus, _longwave_fused_primary_aplus,
    _longwave_fused_primary_aplus_serial)
from solweig_light.geometry.visibility_compiled import (_decode_at,
                                                        _fused_descriptor,
                                                        _preflight_flat)
from solweig_light.radiation.cylinder_longwave import (_longwave_fused_primary,
                                                       _longwave_fused_primary_serial)
from solweig_light.radiation.patch_radiation import _classes, patch_geometry

from n9_producer_ref import n9_build_channel, n9_tensor32, n9_vault


def _patch_args(rng, pixels, patches):
    return dict(solid=rng.uniform(0.001, 0.05, patches).astype(np.float32),
                sine=rng.uniform(-1, 1, patches).astype(np.float32),
                cosine=rng.uniform(-1, 1, patches).astype(np.float32),
                directions=np.zeros((patches, 4), np.float32),
                gate=np.zeros((patches, 4), np.bool_),
                solar_gate=rng.random(patches) < 0.5,
                sky_down=rng.uniform(300, 500, patches).astype(np.float32),
                sky_side=rng.uniform(300, 500, patches).astype(np.float32),
                lup=rng.uniform(200, 460, pixels).astype(np.float32))


def _aplus_call(kernels, channel, start, stop, args, surface):
    flat, offsets, modes = _fused_descriptor(channel)
    rows = stop - start
    geometry = patch_geometry(n9_vault(3))
    masks = _classes(n9_tensor32(35.0), n9_tensor32(140.0), geometry,
                     np.full(200, 0.5, dtype=np.float32), start, stop)
    call = (flat, offsets, modes, flat, offsets, modes, flat, offsets, modes,
            start, stop, masks[0], masks[1], args['solid'], args['sine'],
            args['cosine'], args['directions'], args['gate'],
            args['solar_gate'], args['sky_down'], args['sky_side'],
            surface[0], surface[1], args['lup'], np.float32(0.85))
    return kernels(*call)


def _f32_bits(value):
    """uint32 bits of a numba-returned float32 scalar (NaN-safe compare)."""
    return np.array(value, dtype=np.float32).view(np.uint32)


@pytest.mark.parametrize('mode_name', ['binary', 'ternary', 'raw'])
def test_n9_aplus_elementwise_decode_matches(mode_name):
    """_decode_at_plus == _decode_at elementwise over every (patch, pixel),
    compared at the BIT level (raw payloads include NaN patterns)."""
    channel = n9_build_channel(97, (mode_name, mode_name, mode_name), seed=11)
    flat, offsets, modes = _fused_descriptor(channel)
    for patch in range(3):
        for pixel in range(3, 97):
            a = _decode_at_plus(flat, offsets, modes, patch, pixel)
            b = _decode_at(flat, offsets, modes, patch, pixel)
            assert _f32_bits(a) == _f32_bits(b), (patch, pixel)


def test_n9_aplus_fused_serial_bitwise_matches_a8():
    """Small mixed vault: A-plus serial output is bitwise the A8 serial's."""
    rng = np.random.default_rng(13)
    channel = n9_build_channel(131, ('binary', 'ternary', 'raw'), seed=12)
    flat, offsets, modes = _fused_descriptor(channel)
    _preflight_flat(flat, offsets, modes, 0, 131, 3)
    args = _patch_args(rng, 131, 3)
    surface = (float(315.0), float(295.0))  # f64 provenance scalars
    a8 = _aplus_call(_longwave_fused_primary_serial, channel, 0, 131, args, surface)
    plus = _aplus_call(_longwave_fused_primary_aplus_serial, channel, 0, 131,
                       args, surface)
    assert a8.dtype == plus.dtype == np.float32
    assert a8.tobytes() == plus.tobytes()


def test_n9_aplus_fused_parallel_bitwise_matches_serial():
    rng = np.random.default_rng(17)
    channel = n9_build_channel(131, ('binary', 'ternary', 'raw'), seed=14)
    flat, offsets, modes = _fused_descriptor(channel)
    _preflight_flat(flat, offsets, modes, 3, 100, 3)
    args = _patch_args(rng, 131, 3)
    surface = (np.float32(300.5), np.float32(299.5))  # f32 provenance scalars
    serial = _aplus_call(_longwave_fused_primary_aplus_serial, channel, 3, 100,
                         args, surface)
    parallel = _aplus_call(_longwave_fused_primary_aplus, channel, 3, 100,
                           args, surface)
    assert serial.tobytes() == parallel.tobytes()
    a8 = _aplus_call(_longwave_fused_primary, channel, 3, 100, args, surface)
    assert a8.tobytes() == serial.tobytes()


def test_n9_aplus_preflight_error_order_unchanged():
    """The reserved-code contract stays with _preflight_flat: same first
    error before any A-plus kernel runs."""
    codes = np.zeros(13, np.uint8)
    codes[6] = 3
    padded = np.zeros(16, np.uint8)
    padded[:13] = codes
    payload = (padded[0::4] | (padded[1::4] << 2) | (padded[2::4] << 4)
               | (padded[3::4] << 6)).tobytes()
    corrupt = n9_build_channel(13, ('ternary', 'ternary', 'binary'), seed=15)
    patches = list(corrupt._patches)
    patches[1] = type(patches[0])('ternary', payload)
    from solweig_light.geometry.visibility import PackedVisibility
    corrupt = PackedVisibility((1, 13, 3), tuple(patches))
    flat, offsets, modes = _fused_descriptor(corrupt)
    with pytest.raises(IndexError, match='Reserved visibility code'):
        _preflight_flat(flat, offsets, modes, 0, 13, 3)
