"""Bounded compiled block schedule for already leased longwave plans.

The public defensive producers and reducer remain unchanged. Each prange
iteration owns one block's scratch and uses exclusively serial leaves; the
only parallel launch covers the entire invocation. Validation scans blocks
and channels in the original observable order before any parallel work.
"""
import numpy as np
from numba import njit, prange
from .direct_aosoa import (_produce_patchmajor, _preflight_packed,
                          _classes_table_masked_aosoa)
from .lw_b_control import lw_primary_b_serial


@njit(cache=True, fastmath=False)
def _preflight_blocks(sh, vs, vb, total, capacity, patches):
    for start in range(0, total, capacity):
        stop = min(start + capacity, total)
        _preflight_packed(sh[0], sh[1], start, stop, patches)
        _preflight_packed(vs[0], vs[1], start, stop, patches)
        _preflight_packed(vb[0], vb[1], start, stop, patches)


@njit(cache=True, fastmath=False, parallel=True)
def _batch(sh, vs, vb, heights, coefficients, factor, altitudes, indices,
           solid, sine, cosine, directions, gate, solar_gate, sky_down,
           sky_side, surface_sun, surface_sh, lup, reflection_factor,
           total, capacity, width, output):
    patches = solid.size
    for block in prange((total + capacity - 1) // capacity):
        start = block * capacity
        stop = min(start + capacity, total)
        rows = stop - start
        gangs = (rows + width - 1) // width
        sh_out = np.empty((gangs, patches, width), np.uint32)
        vs_out = np.empty_like(sh_out)
        vb_out = np.empty_like(sh_out)
        sun = np.zeros((gangs, patches, width), np.bool_)
        shade = np.zeros_like(sun)
        _classes_table_masked_aosoa(heights[start:stop], coefficients,
                                   factor, altitudes, indices, sun, shade, rows)
        _produce_patchmajor(sh[0], sh[1], start, stop, patches, sh_out, width)
        _produce_patchmajor(vs[0], vs[1], start, stop, patches, vs_out, width)
        _produce_patchmajor(vb[0], vb[1], start, stop, patches, vb_out, width)
        frame = np.empty((rows, 7), np.float32)
        lw_primary_b_serial(sh_out.view(np.float32), vs_out.view(np.float32),
                            vb_out.view(np.float32), sun, shade, solid, sine,
                            cosine, directions, gate, solar_gate, sky_down,
                            sky_side, surface_sun, surface_sh, lup[start:stop],
                            reflection_factor, rows, frame)
        for row in range(rows):
            for column in range(7):
                output[column, start + row] = frame[row, column]


@njit(cache=True, fastmath=False)
def _batch_serial(sh, vs, vb, heights, coefficients, factor, altitudes, indices,
           solid, sine, cosine, directions, gate, solar_gate, sky_down,
           sky_side, surface_sun, surface_sh, lup, reflection_factor,
           total, capacity, width, output):
    patches = solid.size
    for block in range((total + capacity - 1) // capacity):
        start = block * capacity
        stop = min(start + capacity, total)
        rows = stop - start
        gangs = (rows + width - 1) // width
        sh_out = np.empty((gangs, patches, width), np.uint32)
        vs_out = np.empty_like(sh_out)
        vb_out = np.empty_like(sh_out)
        sun = np.zeros((gangs, patches, width), np.bool_)
        shade = np.zeros_like(sun)
        _classes_table_masked_aosoa(heights[start:stop], coefficients,
                                   factor, altitudes, indices, sun, shade, rows)
        _produce_patchmajor(sh[0], sh[1], start, stop, patches, sh_out, width)
        _produce_patchmajor(vs[0], vs[1], start, stop, patches, vs_out, width)
        _produce_patchmajor(vb[0], vb[1], start, stop, patches, vb_out, width)
        frame = np.empty((rows, 7), np.float32)
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
    Scratch is O(runtime threads * capacity * patches), never O(total*P).
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
    output = np.empty((7, plan.total), np.float32)
    kernel = _batch if parallel else _batch_serial
    kernel(plan.borrowed.sh, plan.borrowed.vs, plan.borrowed.vb, heights,
           coefficients, np.asarray(rad2deg, dtype=field.dtype)[()],
           plan.geometry.altitude[indices], indices, plan.solid, plan.sine,
           plan.cosine, plan.directions, plan.gate, plan.solar_gate,
           plan.sky_down, plan.sky_side, plan.surface_sun, plan.surface_sh,
           plan.lup, plan.reflection_factor, plan.total, plan.block_pixels,
           plan.width, output)
    return output
