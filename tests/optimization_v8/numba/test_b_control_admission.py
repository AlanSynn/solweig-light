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
"""N8-12 admission gates: the B-control adapter mirrors the native
contract's rejection set AND order (lw_native.primary), against the same
kinds of inputs, with the AoSoA boundary substitutions documented in
lw_b_control. Every rejection is an UnsupportedInput (TypeError subclass)
raised BEFORE any kernel work; each test also pins the precedence by
checking the FIRST violated rule wins on multi-violation inputs.
"""
import numpy as np
import pytest

import lw_b_control as bc
from lw_reference_oracle import F32

from test_b_control_bitexact import b_call, pack_aosoa, pack_bool


def base_bundle(rows=9, patches=5, width=8):
    """One valid admitted bundle (dense form + packed views + shared args)."""
    rng = np.random.default_rng(31)
    sh = rng.choice([0.0, 1.0, 2.0, 0.5], (rows, patches)).astype(np.float32)
    vs = rng.choice([0.0, 1.0, 2.0], (rows, patches)).astype(np.float32)
    vb = rng.choice([0.0, 1.0, 2.0], (rows, patches)).astype(np.float32)
    sun = rng.integers(0, 2, (rows, patches)).astype(np.bool_)
    shade = rng.integers(0, 2, (rows, patches)).astype(np.bool_)
    shared = dict(
        solid=np.full(patches, 0.01, F32), sine=np.full(patches, 0.5, F32),
        cosine=np.full(patches, 0.5, F32),
        directions=np.zeros((patches, 4), F32),
        gate=np.zeros((patches, 4), np.bool_),
        solar_gate=rng.random(patches) < 0.5,
        sky_down=np.full(patches, 400.0, F32), sky_side=np.full(patches, 390.0, F32),
        surface_sun=350.0, surface_sh=320.0,
        lup=np.full(rows, 400.0, F32), reflection_factor=np.float32(0.3))
    packed = dict(sh=pack_aosoa(sh, width), vs=pack_aosoa(vs, width),
                  vb=pack_aosoa(vb, width), sun=pack_bool(sun, width),
                  shade=pack_bool(shade, width))
    return packed, shared


def call(packed=None, shared=None, rows=9, **over):
    packed, shared = dict(packed or base_bundle()[0]), dict(shared or base_bundle()[1])
    for key, value in over.items():
        (packed if key in packed else shared)[key] = value
    return bc.lw_primary_b(**packed, **shared, rows=over.get('rows', rows))


def rejects(overlap_msg, **over):
    with pytest.raises(bc.UnsupportedInput, match=overlap_msg):
        call(**over)


def test_unsupported_input_is_typeerror_subclass():
    assert issubclass(bc.UnsupportedInput, TypeError)


def test_valid_bundle_runs_and_out_parameter_receives_result():
    packed, shared = base_bundle()
    out = bc.lw_primary_b(**packed, **shared, rows=9)
    assert out.shape == (9, 7) and out.dtype == F32
    caller = np.zeros((9, 7), F32)
    returned = bc.lw_primary_b(**packed, **shared, rows=9, out=caller)
    assert returned is caller
    assert np.array_equal(returned.view(np.uint32), out.view(np.uint32))


# --- native order: sh type/dtype/ndim, gang width, P bounds, rows domain ---

def test_sh_not_ndarray_rejected_first():
    rejects('sh: expected ndarray', sh=[1, 2, 3])

def test_sh_dtype_rejected():
    rejects('sh: dtype', sh=np.zeros((2, 5, 8), np.float32))

def test_sh_ndim_rejected():
    rejects('sh: ndim', sh=np.zeros((9, 5), np.uint32))

def test_gang_width_outside_shortlist_rejected():
    rejects('gang must be 4 or 8', sh=np.zeros((2, 5, 7), np.uint32),
            vs=np.zeros((2, 5, 7), np.uint32), vb=np.zeros((2, 5, 7), np.uint32),
            sun=np.zeros((2, 5, 7), np.bool_), shade=np.zeros((2, 5, 7), np.bool_),
            rows=9)

def test_patch_bounds_rejected():
    rejects('outside admitted 1..609', sh=np.zeros((2, 0, 8), np.uint32),
            vs=np.zeros((2, 0, 8), np.uint32), vb=np.zeros((2, 0, 8), np.uint32),
            sun=np.zeros((2, 0, 8), np.bool_), shade=np.zeros((2, 0, 8), np.bool_),
            rows=9)

def test_negative_rows_rejected():
    rejects('negative', rows=-1)

def test_rows_not_integer_rejected():
    rejects('rows: expected an integer', rows=9.0)

def test_gang_count_inconsistent_with_rows_rejected():
    rejects('cannot carry rows=9', sh=np.zeros((1, 5, 8), np.uint32),
            vs=np.zeros((1, 5, 8), np.uint32), vb=np.zeros((1, 5, 8), np.uint32),
            sun=np.zeros((1, 5, 8), np.bool_), shade=np.zeros((1, 5, 8), np.bool_))


# --- native order: vs/vb agreement, layout, masks, patch arrays ---

def test_vs_shape_disagreement_rejected():
    rejects('vs: shape', vs=np.zeros((1, 5, 8), np.uint32))

def test_non_contiguous_sh_rejected():
    _, shared = base_bundle()
    packed, _ = base_bundle()
    transposed = packed['sh'].transpose(2, 1, 0)     # [W,P,G], not C order
    with pytest.raises(bc.UnsupportedInput, match='sh: strides'):
        bc.lw_primary_b(**{**packed, 'sh': np.ascontiguousarray(transposed).transpose(2, 1, 0)},
                        **shared, rows=9)

def test_sun_dtype_rejected():
    rejects('sun: dtype', sun=np.zeros((2, 5, 8), np.uint8))

def test_sun_shape_rejected():
    # ndim is checked before shape (native _need_array order), so the wrong
    # shape must keep the right ndim to reach the shape rule.
    rejects('sun: shape', sun=np.zeros((1, 5, 8), np.bool_))

def test_solid_dtype_rejected():
    rejects('solid: dtype', solid=np.zeros(5, np.float64))

def test_sine_length_rejected():
    rejects('sine: shape', sine=np.zeros(4, F32))

def test_solar_gate_stride_rejected():
    gate_grid = np.zeros((5, 2), np.bool_)
    rejects('solar_gate: strides', solar_gate=gate_grid[:, 0])

def test_sky_down_length_rejected():
    rejects('sky_down: shape', sky_down=np.zeros(4, F32))

def test_sky_down_strided_column_admitted():
    # The real pipeline's stride-12 column-2 view is admitted (positive gate).
    packed, shared = base_bundle()
    table = np.zeros((5, 3), F32)
    table[:, 2] = shared['sky_down']
    strided = dict(shared)
    strided['sky_down'] = table[:, 2]
    assert strided['sky_down'].strides == (12,)
    straight = bc.lw_primary_b(**packed, **shared, rows=9)
    assert np.array_equal(
        bc.lw_primary_b(**packed, **strided, rows=9).view(np.uint32),
        straight.view(np.uint32))

def test_directions_shape_rejected():
    rejects('directions: shape', directions=np.zeros((5, 3), F32))

def test_gate_dtype_rejected():
    rejects('gate: dtype', gate=np.zeros((5, 4), np.uint8))

def test_lup_dtype_rejected():
    rejects('lup: dtype', lup=np.zeros(9, np.float64))

def test_lup_length_rejected():
    rejects('lup: shape', lup=np.zeros(8, F32))


# --- native order: surface provenance, reflection factor, out ---

def test_surface_mixed_provenance_rejected():
    rejects('specialization mismatch', surface_sun=np.float32(350.0))

def test_surface_int_rejected():
    rejects('unsupported scalar provenance', surface_sun=350, surface_sh=320)

def test_reflection_python_float_rejected():
    rejects('reflection_factor: unsupported', reflection_factor=0.3)

def test_reflection_zero_d_f32_array_admitted():
    packed, shared = base_bundle()
    scalar = bc.lw_primary_b(**packed, **shared, rows=9)
    zero_d = dict(shared)
    zero_d['reflection_factor'] = np.array(np.float32(0.3))
    assert np.array_equal(
        bc.lw_primary_b(**packed, **zero_d, rows=9).view(np.uint32),
        scalar.view(np.uint32))

def test_out_wrong_shape_rejected():
    packed, shared = base_bundle()
    with pytest.raises(bc.UnsupportedInput, match='out: shape'):
        bc.lw_primary_b(**packed, **shared, rows=9, out=np.zeros((9, 6), F32))

def test_out_aliases_input_rejected():
    packed, shared = base_bundle()
    # A float32 view into sh's own bytes: same extents as the input buffer.
    alias = packed['sh'].reshape(-1)[:63].view(np.float32).reshape(9, 7)
    with pytest.raises(bc.UnsupportedInput, match='out aliases input sh'):
        bc.lw_primary_b(**packed, **shared, rows=9, out=alias)


# --- precedence: the FIRST violated rule in native order wins ---

def test_dtype_precedes_patch_bounds():
    rejects('sh: dtype', sh=np.zeros((2, 0, 8), np.float32))

def test_patch_bounds_precede_rows_domain():
    rejects('outside admitted', sh=np.zeros((2, 0, 8), np.uint32),
            vs=np.zeros((2, 0, 8), np.uint32), vb=np.zeros((2, 0, 8), np.uint32),
            sun=np.zeros((2, 0, 8), np.bool_), shade=np.zeros((2, 0, 8), np.bool_),
            rows=-1)

def test_surface_precedes_reflection_factor():
    rejects('specialization mismatch', surface_sun=np.float32(350.0),
            reflection_factor=0.3)

def test_rows_zero_early_return_beats_all_downstream_violations():
    # rows=0 mirrors the native B=0 path: the zero frame returns before any
    # downstream validation (even a bogus reflection_factor).
    _, shared = base_bundle()
    packed = dict(sh=np.zeros((0, 5, 8), np.uint32), vs=np.zeros((0, 5, 8), np.uint32),
                  vb=np.zeros((0, 5, 8), np.uint32), sun=np.zeros((0, 5, 8), np.bool_),
                  shade=np.zeros((0, 5, 8), np.bool_))
    broken = dict(shared)
    broken['reflection_factor'] = 0.3               # would reject if reached
    out = bc.lw_primary_b(**packed, **broken, rows=0)
    assert out.shape == (0, 7) and out.dtype == F32
