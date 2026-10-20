"""Cylinder shortwave invocation schedule over leased shared diffuse leaves."""
from functools import partial

import numpy as np
from numba import njit, prange
from solweig_light.radiation._jit_cache import bind_cache_identity
from .direct_aosoa import (_produce_patchmajor, _classes_table_masked_aosoa,
                          _classes_table_grouped_aosoa, _coefficient_bit_groups)
from .lw_batch import _preflight_blocks

_bind_batch_cache = partial(bind_cache_identity, dependencies=(
    "_native_dispatch/direct_aosoa.py",
    "radiation/_sleef_classifier.py",
))


@njit(cache=True, fastmath=False)
@_bind_batch_cache
def _block(block, sh, vs, vb, heights, coefficients, factor, altitudes, indices,
           group_offsets, group_columns,
           lum, solid, cosine, surface_sun, surface_sh, total, capacity,
           width, output):
    patches = solid.size
    start = block * capacity
    stop = min(start + capacity, total)
    rows = stop - start
    gangs = (rows + width - 1) // width
    sh_out = np.empty((gangs, patches, width), np.uint32)
    vs_out = np.empty_like(sh_out)
    vb_out = np.empty_like(sh_out)
    sun = np.zeros((gangs, patches, width), np.bool_)
    shade = np.zeros_like(sun)
    if group_offsets.size:
        _classes_table_grouped_aosoa(heights[start:stop], coefficients, factor,
            altitudes, indices, group_offsets, group_columns, sun, shade, rows)
    else:
        _classes_table_masked_aosoa(heights[start:stop], coefficients, factor,
                                   altitudes, indices, sun, shade, rows)
    _produce_patchmajor(sh[0], sh[1], start, stop, patches, sh_out, width)
    _produce_patchmajor(vs[0], vs[1], start, stop, patches, vs_out, width)
    _produce_patchmajor(vb[0], vb[1], start, stop, patches, vb_out, width)
    sf = sh_out.view(np.float32)
    vf = vs_out.view(np.float32)
    bf = vb_out.view(np.float32)
    for row in range(rows):
        gang, lane = row // width, row % width
        a0=a1=a2=a3=np.float32(0)
        for patch in range(patches):
            sh_v, vs_v, vb_v = sf[gang,patch,lane], vf[gang,patch,lane], bf[gang,patch,lane]
            d_v = np.float32(sh_v - np.float32(np.float32(np.float32(1)-vs_v)*np.float32(1-.03)))
            veg=vs_v==0 or vb_v==0
            building=np.float32(np.float32(1)-sh_v)*vb_v==1
            contribution=np.float32(np.float32(np.float32(d_v*lum[patch])*cosine[patch])*solid[patch])
            a0=np.float32(a0+contribution)
            v=((surface_sh*veg)*solid[patch])*cosine[patch]
            a3=np.float32(a3+v)
            a=((((surface_sun*sun[gang,patch,lane])*building)*solid[patch])*cosine[patch])
            b=((((surface_sh*shade[gang,patch,lane])*building)*solid[patch])*cosine[patch])
            a1=np.float32(a1+a)
            a2=np.float32(a2+b)
        output[5,start+row]=a0
        output[6,start+row]=np.float32(np.float32(np.float32(np.float32(output[4,start+row]+a0)+a1)+a2)+a3)


@njit(cache=True, fastmath=False, parallel=True)
@_bind_batch_cache
def _batch(sh, vs, vb, heights, coefficients, factor, altitudes, indices,
           group_offsets, group_columns,
           lum, solid, cosine, surface_sun, surface_sh, total, capacity,
           width, output):
    for block in prange((total + capacity - 1) // capacity):
        _block(block, sh, vs, vb, heights, coefficients, factor, altitudes, indices,
            group_offsets, group_columns,
            lum, solid, cosine, surface_sun, surface_sh, total, capacity,
            width, output)


@njit(cache=True, fastmath=False)
@_bind_batch_cache
def _batch_serial(sh, vs, vb, heights, coefficients, factor, altitudes, indices,
           group_offsets, group_columns,
           lum, solid, cosine, surface_sun, surface_sh, total, capacity,
           width, output):
    for block in range((total + capacity - 1) // capacity):
        _block(block, sh, vs, vb, heights, coefficients, factor, altitudes, indices,
            group_offsets, group_columns,
            lum, solid, cosine, surface_sun, surface_sh, total, capacity,
            width, output)


@njit(cache=True, fastmath=False)
@bind_cache_identity
def _finite_output(output):
    """No-allocation check before accepting moved NumPy addition results."""
    for component in range(output.shape[0]):
        for pixel in range(output.shape[1]):
            if not np.isfinite(output[component,pixel]):
                return False
    return True


def execute(values, geometry, prepared, lum, surface_sun, surface_sh, capacity, output, parallel=True):
    """Private structurally validated path; None leaves legacy loop active."""
    from solweig_light.geometry.visibility import LazyDiffVisibility
    from solweig_light.geometry.visibility_compiled import _descriptor
    from solweig_light.radiation.static_geometry import owned_tangent
    from .direct_aosoa import _leased
    from .lw_stream import _admitted_channels
    channels = tuple(values[k] for k in ('shmat','vegshmat','vbshvegshmat'))
    diffuse = values['diffsh']
    field = np.asarray(values['asvf']).reshape(-1)
    if (capacity < 8 or capacity % 8 or prepared is None or
        type(diffuse) is not LazyDiffVisibility or diffuse.shadow is not channels[0]
        or diffuse.vegetation is not channels[1] or not _admitted_channels(channels)
        or (owned_tangent(values['asvf']) is None and
            not bool((np.isfinite(field)&(np.abs(field)<np.float32(125))).all()))):
        return None
    total = output.shape[1]
    indices, coefficients, factor = prepared
    with _leased(channels,0,total,geometry.altitude.size):
        sh, vs, vb = (_descriptor(channel) for channel in channels)
        try:
            _preflight_blocks(sh,vs,vb,total,capacity,geometry.altitude.size)
        except IndexError:
            # A later block's reserved payload must not precede an earlier
            # block's NumPy assembly warning/error. Decline before launch
            # so the retained block loop owns the original first event.
            return None
        from solweig_light.radiation.static_geometry import classification_heights
        heights = classification_heights(values['asvf'])
        # Construct after the existing preflight/tangent evaluation so their
        # errors keep their ordering. Only ordinary float32 profiles with
        # distinct ascending targets can change the classifier's write order.
        groups = None
        if (field.dtype == np.float32 and geometry.altitude.dtype == np.float32
                and type(indices) is np.ndarray and indices.ndim == 1
                and indices.dtype == np.int64 and indices.size == coefficients.size
                and (not indices.size or (indices[0] >= 0
                     and indices[-1] < geometry.altitude.size))
                and (indices.size < 2 or bool((indices[1:] > indices[:-1]).all()))):
            groups = _coefficient_bit_groups(coefficients)
        group_offsets, group_columns = ((np.empty(0, np.int64), np.empty(0, np.int64))
                                         if groups is None else groups)
        kernel = _batch if parallel else _batch_serial
        kernel(sh,vs,vb,heights,coefficients,np.asarray(factor,dtype=field.dtype)[()],
               geometry.altitude[indices],indices,group_offsets,group_columns,lum,geometry.solid_angle,
               geometry.cosine,surface_sun,surface_sh,total,capacity,8,output)
    # The retained caller overwrites only the candidate-owned components
    # 5 and 6; direct/Kup fields 0..4 were never modified by the kernel.
    # Replaying a nonfinite result restores NumPy warning/raise behavior
    # and exact NaN payload propagation, including under errstate(ignore).
    return output if _finite_output(output) else None
