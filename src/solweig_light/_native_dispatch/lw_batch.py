"""Bounded compiled block schedule for already leased longwave plans.

The public defensive producers and reducer remain unchanged. Each prange
iteration owns one block's scratch and uses exclusively serial leaves; the
only parallel launch covers the entire invocation. Validation scans blocks
and channels in the original observable order before any parallel work.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from functools import partial

import numpy as np
from numba import njit, prange
from solweig_light.radiation._jit_cache import bind_cache_identity
from .direct_aosoa import (_produce_patchmajor, _preflight_packed,
                          _classes_table_masked_aosoa)
from .lw_b_control import lw_primary_b_serial, lw_primary_b_lanes_serial

_bind_preflight_cache = partial(bind_cache_identity, dependencies=(
    "_native_dispatch/direct_aosoa.py",
))
_bind_batch_cache = partial(bind_cache_identity, dependencies=(
    "_native_dispatch/direct_aosoa.py",
    "_native_dispatch/lw_b_control.py",
    "radiation/_sleef_classifier.py",
))
_RESIDENT_MASKS = ContextVar('solweig_resident_lw_masks', default=None)


class _ResidentMasks:
    def __init__(self, owners):
        self.owners = tuple(owners)
        self.descriptors = self.shape = self.flags = None


@contextmanager
def _resident_masks_scope(owners=None):
    """Retain masks only for this tile's exact owners; None disables reuse."""
    state = None if owners is None else _ResidentMasks(owners)
    token = _RESIDENT_MASKS.set(state)
    try:
        yield state
    finally:
        _RESIDENT_MASKS.reset(token)
        if state is not None:
            state.owners = ()
            state.descriptors = state.flags = None


@njit(cache=True, fastmath=False)
@_bind_batch_cache
def _mask_block(sh_source, vs_source, vb_source, start, stop, flags):
    gangs, patches, width = flags.shape
    rows = stop - start
    sh_out = np.empty((gangs, patches, width), np.uint32)
    vs_out = np.empty_like(sh_out)
    vb_out = np.empty_like(sh_out)
    _produce_patchmajor(sh_source[0], sh_source[1], start, stop, patches, sh_out, width)
    _produce_patchmajor(vs_source[0], vs_source[1], start, stop, patches, vs_out, width)
    _produce_patchmajor(vb_source[0], vb_source[1], start, stop, patches, vb_out, width)
    sh, vs, vb = sh_out.view(np.float32), vs_out.view(np.float32), vb_out.view(np.float32)
    for gang in range(gangs):
        live = min(width, rows - gang * width)
        for patch in range(patches):
            for lane in range(live):
                sky = sh[gang, patch, lane] == 1 and vs[gang, patch, lane] == 1
                veg = vs[gang, patch, lane] == 0 or vb[gang, patch, lane] == 0
                building = np.float32(np.float32(1)-sh[gang, patch, lane])*vb[gang, patch, lane] == 1
                reflection = sh[gang, patch, lane] == 0 or vs[gang, patch, lane] == 0 or vb[gang, patch, lane] == 0
                flags[gang, patch, lane] = (
                    np.uint8(sky) | (np.uint8(veg) << np.uint8(1))
                    | (np.uint8(building) << np.uint8(2))
                    | (np.uint8(reflection) << np.uint8(3)))


@njit(cache=True, fastmath=False, parallel=True)
@_bind_batch_cache
def _build_masks(sh, vs, vb, total, capacity, flags):
    for block in prange((total + capacity - 1) // capacity):
        start = block * capacity
        stop = min(start + capacity, total)
        _mask_block(sh, vs, vb, start, stop, flags[start // 32:(stop + 31) // 32])


@njit(cache=True, fastmath=False)
@_bind_batch_cache
def _build_masks_serial(sh, vs, vb, total, capacity, flags):
    for start in range(0, total, capacity):
        stop = min(start + capacity, total)
        _mask_block(sh, vs, vb, start, stop, flags[start // 32:(stop + 31) // 32])


def _resident_masks_for(plan, parallel):
    state = _RESIDENT_MASKS.get()
    if state is None:
        return None
    descriptors = (plan.borrowed.sh, plan.borrowed.vs, plan.borrowed.vb)
    # Plan minting already acquired these exact owners' leases and checked
    # mappings are open. Do not mint descriptors or cache an unrelated call.
    if len(state.owners) != 3 or any(
            getattr(owner, '_block_descriptor', None) is not descriptor
            or owner.shape[0] * owner.shape[1] != plan.total
            or owner.shape[2] != plan.patches
            for owner, descriptor in zip(state.owners, descriptors)):
        return None
    shape = (plan.total, plan.patches)
    if state.descriptors is not None and (
            state.shape != shape or any(a is not b for a, b in zip(state.descriptors, descriptors))):
        return None
    if state.flags is None:
        flags = np.empty(((plan.total + 31) // 32, plan.patches, 32), np.uint8)
        builder = _build_masks if parallel else _build_masks_serial
        builder(*descriptors, plan.total, plan.block_pixels, flags)
        flags.setflags(write=False)
        state.descriptors, state.shape, state.flags = descriptors, shape, flags
    return state.flags


@njit(cache=True, fastmath=False, inline="always")
@bind_cache_identity
def _binary_preflight_admitted(payloads, modes, total, patches):
    if len(payloads) < patches or modes.size < patches:
        return False
    packed_bytes = total // 8 + (total % 8 != 0)
    for patch in range(patches):
        if modes[patch] != 1 or payloads[patch].size < packed_bytes:
            return False
    return True


@njit(cache=True, fastmath=False)
@_bind_preflight_cache
def _preflight_blocks(sh, vs, vb, total, capacity, patches):
    # A binary decode cannot produce reserved code 3. Check whole-input
    # extents once; other descriptors retain the original discovery order.
    if (total > 0 and capacity > 0 and patches > 0
            and _binary_preflight_admitted(sh[0], sh[1], total, patches)
            and _binary_preflight_admitted(vs[0], vs[1], total, patches)
            and _binary_preflight_admitted(vb[0], vb[1], total, patches)):
        return
    for start in range(0, total, capacity):
        stop = min(start + capacity, total)
        _preflight_packed(sh[0], sh[1], start, stop, patches)
        _preflight_packed(vs[0], vs[1], start, stop, patches)
        _preflight_packed(vb[0], vb[1], start, stop, patches)


@njit(cache=True, fastmath=False)
@bind_cache_identity
def _finite_lane_fields(solid, sine, cosine, sky_down, sky_side, lup, total):
    for patch in range(solid.size):
        if not (0 <= solid[patch] <= 1 and abs(sine[patch]) <= 1
                and abs(cosine[patch]) <= 1 and abs(sky_down[patch]) <= 1e20
                and abs(sky_side[patch]) <= 1e20):
            return False
    for row in range(total):
        if not abs(lup[row]) <= 1e20:
            return False
    return True


def _lanes_admitted(plan):
    # These bounds keep every intermediate below 1e27, including both
    # ordered 609-patch sweeps. Raw and exceptional inputs retain the strict
    # serial leaf, whose invalid-arithmetic NaN bits are already pinned.
    if not (plan.total >= plan.block_pixels > 0 and plan.block_pixels % 32 == 0
            and 1 <= plan.patches <= 609 and abs(float(plan.surface_sun)) <= 1e20
            and abs(float(plan.surface_sh)) <= 1e20
            and abs(float(plan.reflection_factor)) <= 1):
        return False
    for _, modes in (plan.borrowed.sh, plan.borrowed.vs, plan.borrowed.vb):
        if not bool(((modes == 1) | (modes == 2)).all()):
            return False
    return _finite_lane_fields(plan.solid, plan.sine, plan.cosine,
                               plan.sky_down, plan.sky_side, plan.lup,
                               plan.total)


@njit(cache=True, fastmath=False, parallel=True)
@_bind_batch_cache
def _batch(sh, vs, vb, heights, coefficients, factor, altitudes, indices,
           solid, sine, cosine, directions, gate, solar_gate, sky_down,
           sky_side, surface_sun, surface_sh, lup, reflection_factor,
           total, capacity, width, output, lanes, flags=None):
    patches = solid.size
    for block in prange((total + capacity - 1) // capacity):
        start = block * capacity
        stop = min(start + capacity, total)
        rows = stop - start
        gangs = (rows + width - 1) // width
        if flags is None:
            sh_out = np.empty((gangs, patches, width), np.uint32)
            vs_out = np.empty_like(sh_out)
            vb_out = np.empty_like(sh_out)
        sun = np.zeros((gangs, patches, width), np.bool_)
        shade = np.zeros_like(sun)
        _classes_table_masked_aosoa(heights[start:stop], coefficients,
                                   factor, altitudes, indices, sun, shade, rows)
        if flags is None:
            _produce_patchmajor(sh[0], sh[1], start, stop, patches, sh_out, width)
            _produce_patchmajor(vs[0], vs[1], start, stop, patches, vs_out, width)
            _produce_patchmajor(vb[0], vb[1], start, stop, patches, vb_out, width)
        frame = np.empty((rows, 7), np.float32)
        if flags is not None:
            # The read-only compact array supplies layout only for unused channels.
            block_flags = flags[start // width:(stop + width - 1) // width]
            lw_primary_b_lanes_serial(
                block_flags, block_flags, block_flags, sun, shade, solid, sine, cosine,
                directions, gate, solar_gate, sky_down, sky_side,
                surface_sun, surface_sh, lup[start:stop],
                reflection_factor, rows, frame, block_flags)
        elif lanes:
            lw_primary_b_lanes_serial(
                sh_out.view(np.float32), vs_out.view(np.float32),
                vb_out.view(np.float32), sun, shade, solid, sine, cosine,
                directions, gate, solar_gate, sky_down, sky_side,
                surface_sun, surface_sh, lup[start:stop],
                reflection_factor, rows, frame)
        else:
            lw_primary_b_serial(sh_out.view(np.float32), vs_out.view(np.float32),
                                vb_out.view(np.float32), sun, shade, solid, sine,
                                cosine, directions, gate, solar_gate, sky_down,
                                sky_side, surface_sun, surface_sh, lup[start:stop],
                                reflection_factor, rows, frame)
        for row in range(rows):
            for column in range(7):
                output[column, start + row] = frame[row, column]


@njit(cache=True, fastmath=False)
@_bind_batch_cache
def _batch_serial(sh, vs, vb, heights, coefficients, factor, altitudes, indices,
           solid, sine, cosine, directions, gate, solar_gate, sky_down,
           sky_side, surface_sun, surface_sh, lup, reflection_factor,
           total, capacity, width, output, lanes, flags=None):
    patches = solid.size
    for block in range((total + capacity - 1) // capacity):
        start = block * capacity
        stop = min(start + capacity, total)
        rows = stop - start
        gangs = (rows + width - 1) // width
        if flags is None:
            sh_out = np.empty((gangs, patches, width), np.uint32)
            vs_out = np.empty_like(sh_out)
            vb_out = np.empty_like(sh_out)
        sun = np.zeros((gangs, patches, width), np.bool_)
        shade = np.zeros_like(sun)
        _classes_table_masked_aosoa(heights[start:stop], coefficients,
                                   factor, altitudes, indices, sun, shade, rows)
        if flags is None:
            _produce_patchmajor(sh[0], sh[1], start, stop, patches, sh_out, width)
            _produce_patchmajor(vs[0], vs[1], start, stop, patches, vs_out, width)
            _produce_patchmajor(vb[0], vb[1], start, stop, patches, vb_out, width)
        frame = np.empty((rows, 7), np.float32)
        if flags is not None:
            # The read-only compact array supplies layout only for unused channels.
            block_flags = flags[start // width:(stop + width - 1) // width]
            lw_primary_b_lanes_serial(
                block_flags, block_flags, block_flags, sun, shade, solid, sine, cosine,
                directions, gate, solar_gate, sky_down, sky_side,
                surface_sun, surface_sh, lup[start:stop],
                reflection_factor, rows, frame, block_flags)
        elif lanes:
            lw_primary_b_lanes_serial(
                sh_out.view(np.float32), vs_out.view(np.float32),
                vb_out.view(np.float32), sun, shade, solid, sine, cosine,
                directions, gate, solar_gate, sky_down, sky_side,
                surface_sun, surface_sh, lup[start:stop],
                reflection_factor, rows, frame)
        else:
            lw_primary_b_serial(sh_out.view(np.float32), vs_out.view(np.float32),
                                vb_out.view(np.float32), sun, shade, solid, sine,
                                cosine, directions, gate, solar_gate, sky_down,
                                sky_side, surface_sun, surface_sh, lup[start:stop],
                                reflection_factor, rows, frame)
        for row in range(rows):
            for column in range(7):
                output[column, start + row] = frame[row, column]


def _admitted_arguments(plan):
    """Certify the bypassed leaf adapter once, otherwise retain its errors."""
    from .lw_b_control import (_need_array, _need_c_contig, _scalar_spec,
                               _reflection_spec, UnsupportedInput)
    try:
        if plan.width not in (4,8):
            return False
        patches = plan.patches
        for name in ('solid','sine','cosine'):
            value = getattr(plan,name)
            _need_array(value,name,np.float32,1,(patches,))
            _need_c_contig(value,name,4)
        _need_array(plan.solar_gate,'solar_gate',np.bool_,1,(patches,))
        if plan.solar_gate.strides != (1,):
            return False
        for name in ('sky_down','sky_side'):
            _need_array(getattr(plan,name),name,np.float32,1,(patches,))
        _need_array(plan.directions,'directions',np.float32,2,(patches,4))
        _need_array(plan.gate,'gate',np.bool_,2,(patches,4))
        _need_array(plan.lup,'lup',np.float32,1)
        _need_c_contig(plan.lup,'lup',4)
        if plan.lup.size < plan.total:
            return False
        if _scalar_spec(plan.surface_sun,'surface_sun') != _scalar_spec(plan.surface_sh,'surface_sh'):
            return False
        _reflection_spec(plan.reflection_factor)
        return True
    except UnsupportedInput:
        return False


def execute(plan, parallel=True):
    """Run an admitted leased plan; return None for exotic tangent profiles.

    Finite SLEEF tangent inputs permit one whole-field evaluation without
    moving a NumPy warning ahead of an earlier block's decode failure.
    Default scratch is O(runtime threads * capacity * patches). An explicit
    tile mask scope may additionally retain one byte per pixel and patch.
    """
    from solweig_light.radiation.static_geometry import owned_tangent
    field = np.asarray(plan.asvf).reshape(-1)
    if not _admitted_arguments(plan):
        return None
    if owned_tangent(plan.asvf) is None and not bool((np.isfinite(field) & (np.abs(field) < np.float32(125))).all()):
        return None
    indices, coefficients, rad2deg = plan.prepared
    _preflight_blocks(plan.borrowed.sh, plan.borrowed.vs, plan.borrowed.vb,
                      plan.total, plan.block_pixels, plan.patches)
    from solweig_light.radiation.static_geometry import classification_heights
    heights = classification_heights(plan.asvf)
    lanes = _lanes_admitted(plan)
    # Wider private groups reach the reducer's vector loops. Admission keeps
    # each padded final gang within the already budgeted block capacity.
    width = 32 if lanes else plan.width
    flags = _resident_masks_for(plan, parallel) if lanes else None
    output = np.empty((7, plan.total), np.float32)
    kernel = _batch if parallel else _batch_serial
    kernel(plan.borrowed.sh, plan.borrowed.vs, plan.borrowed.vb, heights,
           coefficients, np.asarray(rad2deg, dtype=field.dtype)[()],
           plan.geometry.altitude[indices], indices, plan.solid, plan.sine,
           plan.cosine, plan.directions, plan.gate, plan.solar_gate,
           plan.sky_down, plan.sky_side, plan.surface_sun, plan.surface_sh,
           plan.lup, plan.reflection_factor, plan.total, plan.block_pixels,
           width, output, lanes, flags)
    return output
