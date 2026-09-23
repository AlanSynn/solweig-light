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
"""N9 A2 WIRING parity: the shipped fused kernels decode via _decode_at_plus.

Release-owner A2 wired the shipped fused kernels to the F1D mode-specialized
decode (``from .._native_dispatch.aplus_decode import _decode_at_plus as
_decode_at`` in radiation/cylinder_longwave.py and radiation/patch_radiation.py).
These tests assert the wiring end to end: every shipped fused kernel entry
point must produce BITWISE identical output to the same kernel body running
the GENERIC decode (``geometry.visibility_compiled._decode_at``), across all
three payload modes (binary / ternary / raw, including tail rows and a
nonzero start window).

The reference is not a transcription: each test clones the shipped kernel's
own ``py_func`` bytecode with a copied globals dict whose ``_decode_at`` is
rebound to the generic function, and compiles that twin fresh
(``cache=False`` -- the twin is a test-only counterfactual, never a cached
production kernel). Identical bytecode + only-the-decode difference makes
any output mismatch a real wiring or specialization defect.
"""
import types

import numpy as np
import pytest
from numba import njit

from solweig_light._native_dispatch.aplus_decode import _decode_at_plus
from solweig_light.geometry.visibility_compiled import (_decode_at,
                                                        _fused_descriptor,
                                                        _preflight_flat)
from solweig_light.radiation import cylinder_longwave as clw
from solweig_light.radiation import patch_radiation as pr
from solweig_light.radiation.patch_radiation import _classes, patch_geometry

from n9_producer_ref import n9_build_channel, n9_tensor32, n9_vault

_MIXES = [('binary',), ('ternary',), ('raw',), ('binary', 'ternary', 'raw')]


def _generic_twin(dispatcher, parallel):
    """The same kernel body compiled against the GENERIC decode."""
    py = dispatcher.py_func
    glb = dict(py.__globals__)
    glb['_decode_at'] = _decode_at
    clone = types.FunctionType(py.__code__, glb, py.__name__)
    return njit(cache=False, fastmath=False, parallel=parallel)(clone)


def _patch_args(rng, pixels, patches):
    return dict(solid=rng.uniform(0.001, 0.05, patches).astype(np.float32),
                sine=rng.uniform(-1, 1, patches).astype(np.float32),
                cosine=rng.uniform(-1, 1, patches).astype(np.float32),
                directions=rng.uniform(-1, 1, (patches, 4)).astype(np.float32),
                gate=rng.random((patches, 4)) < 0.5,
                diff_gate=rng.random((patches, 4)) < 0.5,
                ref_gate=rng.random((patches, 4)) < 0.5,
                box_gate=rng.random(patches) < 0.5,
                solar_gate=rng.random(patches) < 0.5,
                sky_down=rng.uniform(300, 500, patches).astype(np.float32),
                sky_side=rng.uniform(300, 500, patches).astype(np.float32),
                lup=rng.uniform(200, 460, pixels).astype(np.float32),
                lum=rng.uniform(100, 500, patches).astype(np.float32))


def _masks(start, stop, patches, asvf=0.5):
    geometry = patch_geometry(n9_vault(patches))
    return _classes(n9_tensor32(35.0), n9_tensor32(140.0), geometry,
                    np.full(200, asvf, dtype=np.float32), start, stop)


def _lw_call(channel, start, stop, args, surface):
    """The frozen 25-argument fused-longwave argument tuple."""
    flat, offsets, modes = _fused_descriptor(channel)
    sun, shade = _masks(start, stop, channel.shape[2])
    return (flat, offsets, modes, flat, offsets, modes, flat, offsets, modes,
            start, stop, sun, shade, args['solid'], args['sine'],
            args['cosine'], args['directions'], args['gate'],
            args['solar_gate'], args['sky_down'], args['sky_side'],
            surface[0], surface[1], args['lup'], np.float32(0.85))


def _sw_call(sh, vs, vb, dsh, dveg, flags, start, stop, args, surface):
    """The frozen 32-argument fused-shortwave argument tuple."""
    sun, shade = _masks(start, stop, sh.shape[2])
    lazy, dsh_shared, dveg_shared = flags
    return (*_fused_descriptor(sh), *_fused_descriptor(vs),
            *_fused_descriptor(vb), *_fused_descriptor(dsh),
            *_fused_descriptor(dveg), lazy, dsh_shared, dveg_shared,
            start, stop, sun, shade, args['lum'], args['solid'],
            args['cosine'], args['directions'], args['diff_gate'],
            args['ref_gate'], args['box_gate'], surface[0], surface[1], True)


def _assert_bitwise(left, right, label):
    assert left.dtype == right.dtype == np.float32
    assert left.shape == right.shape, label
    assert left.tobytes() == right.tobytes(), label


def test_n9_wiring_is_live():
    """Guard against silent unwiring: each fused module's ``_decode_at``
    global must BE the shipped A-plus decode, or these parity tests would
    compare the generic kernel against itself."""
    for kernel in (clw._longwave_fused_primary, clw._longwave_fused_primary_serial,
                   pr._longwave_fused, pr._longwave_fused_serial,
                   pr._shortwave_fused, pr._shortwave_fused_serial):
        assert kernel.py_func.__globals__['_decode_at'] is _decode_at_plus, \
            f'{kernel.py_func.__module__} is no longer wired to _decode_at_plus'


@pytest.mark.parametrize('mix', _MIXES)
def test_n9_wired_cylinder_longwave_bitwise_matches_generic(mix):
    """cylinder_longwave._longwave_fused_primary[_serial], wired to the
    specialized decode, is bitwise the generic-decode twin of itself."""
    rng = np.random.default_rng(21)
    channel = n9_build_channel(131, mix, seed=22)
    flat, offsets, modes = _fused_descriptor(channel)
    patches = channel.shape[2]
    args = _patch_args(rng, 131, patches)
    surface = (float(315.0), float(295.0))  # f64 provenance scalars
    twin_s = _generic_twin(clw._longwave_fused_primary_serial, parallel=False)
    twin_p = _generic_twin(clw._longwave_fused_primary, parallel=True)
    for start, stop in ((0, 131), (3, 100)):  # tail rows and an inner window
        _preflight_flat(flat, offsets, modes, start, stop, patches)
        call = _lw_call(channel, start, stop, args, surface)
        _assert_bitwise(clw._longwave_fused_primary_serial(*call), twin_s(*call),
                        f'cylinder serial {mix} [{start}:{stop}]')
        _assert_bitwise(clw._longwave_fused_primary(*call), twin_p(*call),
                        f'cylinder parallel {mix} [{start}:{stop}]')


@pytest.mark.parametrize('mix', [('binary', 'ternary', 'raw'), ('raw',)])
def test_n9_wired_patch_longwave_bitwise_matches_generic(mix):
    """patch_radiation._longwave_fused[_serial] (11-column K-side row) —
    same wiring, same bitwise contract through the shipped entry point."""
    rng = np.random.default_rng(23)
    channel = n9_build_channel(131, mix, seed=24)
    flat, offsets, modes = _fused_descriptor(channel)
    patches = channel.shape[2]
    args = _patch_args(rng, 131, patches)
    surface = (np.float32(300.5), np.float32(299.5))  # f32 provenance scalars
    twin_s = _generic_twin(pr._longwave_fused_serial, parallel=False)
    twin_p = _generic_twin(pr._longwave_fused, parallel=True)
    for start, stop in ((0, 131), (3, 100)):
        _preflight_flat(flat, offsets, modes, start, stop, patches)
        call = _lw_call(channel, start, stop, args, surface)
        _assert_bitwise(pr._longwave_fused_serial(*call), twin_s(*call),
                        f'patch longwave serial {mix} [{start}:{stop}]')
        _assert_bitwise(pr._longwave_fused(*call), twin_p(*call),
                        f'patch longwave parallel {mix} [{start}:{stop}]')


@pytest.mark.parametrize('mix,flags', [
    (('binary', 'ternary', 'raw'), (True, False, False)),   # lazy separate leaves
    (('binary', 'ternary'), (False, False, True)),          # eager separate dsh
    (('ternary',), (True, True, True)),                     # fully shared leaves
    (('raw',), (True, False, False)),                       # mode 4 at every site
])
def test_n9_wired_shortwave_bitwise_matches_generic(mix, flags):
    """patch_radiation._shortwave_fused[_serial]: every _decode_at call site
    (base channels, separate diffuse leaves, shared-leaf reuse, lazy branch)
    decodes bitwise identically through the shipped wiring."""
    rng = np.random.default_rng(25)
    sh = n9_build_channel(131, mix, seed=26)
    vs = n9_build_channel(131, mix, seed=27)
    vb = n9_build_channel(131, mix, seed=28)
    dsh = n9_build_channel(131, mix, seed=29)
    dveg = n9_build_channel(131, mix, seed=30)
    for channel in (sh, vs, vb, dsh, dveg):
        flat, offsets, modes = _fused_descriptor(channel)
        _preflight_flat(flat, offsets, modes, 0, 131, channel.shape[2])
    args = _patch_args(rng, 131, sh.shape[2])
    surface = (float(310.0), float(290.0))
    twin_s = _generic_twin(pr._shortwave_fused_serial, parallel=False)
    twin_p = _generic_twin(pr._shortwave_fused, parallel=True)
    call = _sw_call(sh, vs, vb, dsh, dveg, flags, 0, 131, args, surface)
    _assert_bitwise(pr._shortwave_fused_serial(*call), twin_s(*call),
                    f'shortwave serial {mix} flags={flags}')
    _assert_bitwise(pr._shortwave_fused(*call), twin_p(*call),
                    f'shortwave parallel {mix} flags={flags}')
