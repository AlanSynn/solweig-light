"""R01a guarded absorption early-exit: candidate versus pristine original trace.

Evidence class: L0/L1 actual-kernel differential. _trace_pixel_reference below
is the pre-edit _trace_pixel algorithm copied verbatim from
src/solweig_light/geometry/sky_compiled.py at base
bfd9915e411e28bfe498d547e3c820a4de863ee2 and compiled with cache=False; it is
the untouched original algorithm, not candidate-generated goldens. All three
returned masks are compared bitwise (uint32 views), which covers NaN payloads
and signed zeros; the NaN-position check is kept as explicit documentation.
The positive-bush fallback is checked as a route-identity test against the
untouched step-major public entry, not reimplemented here.

Implementer model route: GLM (Z.ai); no Opus route was available for this
worker. Run with the thread cap:

    NUMBA_NUM_THREADS=2 uv run --extra test pytest tests/optimization_v5/rays -q
"""
import os
os.environ.setdefault('NUMBA_NUM_THREADS','2')

import numba
import numpy as np
from numba import njit
import pytest
from solweig_light.geometry.sky_compiled import (ray_schedule, shadow_pixel_parallel,
                                                shadow_pixel_serial, shadow_serial)


# ---------------------------------------------------------------------------
# Pristine reference: original _trace_pixel and _maximum at base bfd9915e.
# Byte-for-byte copies of the pre-edit algorithm; cache=False keeps this
# compiled object disjoint from the cached candidate kernels.
# ---------------------------------------------------------------------------
@njit(inline='always',fastmath=False,cache=False)
def _maximum_reference(left,right):
    if np.isnan(left):return left
    if np.isnan(right):return right
    if left>right:return left
    return right


@njit(cache=False,fastmath=False)
def _trace_pixel_reference(row,col,a,canopy,trunk,bush,bounds,da,dv,dt,first_heights):
    height=a[row,col]
    f=height
    sh=np.float32(0)
    vs=np.float32(bush[row,col]>1)
    vb=np.float32(0)
    for step in range(len(bounds)):
        xc1,xc2,yc1,yc2,xp1,xp2,yp1,yp2=bounds[step]
        building=np.float32(0)
        vegetation=np.float32(0)
        trunk_value=np.float32(0)
        if xp1<=row<xp2 and yp1<=col<yp2:
            source_row=xc1+row-xp1
            source_col=yc1+col-yp1
            building=np.float32(a[source_row,source_col]-da[step])
            vegetation=np.float32(canopy[source_row,source_col]-dv[step])
            trunk_value=np.float32(trunk[source_row,source_col]-dt[step])
        f=_maximum_reference(f,building)
        if f>height:
            sh=np.float32(1)
        elif f<=height:
            sh=np.float32(0)
        vs=_maximum_reference(vs,np.float32(vegetation>height)-np.float32(trunk_value>height))
        if vs*sh>0:
            vs=np.float32(0)
        vb=np.float32(vb+vs)
        if step==0:
            first_vegetation=np.float32(vegetation-building)
            if first_vegetation<=0:
                first_vegetation=np.float32(1000)
            if first_vegetation<first_heights[step]:
                vs=np.float32(1)
            vs=np.float32(vs*np.float32(trunk[row,col]>height))
            vb=np.float32(0)
    if vb>0:vb=np.float32(1)
    vb=np.float32(vb-vs)
    if vs>0:vs=np.float32(1)
    return np.float32(1)-sh,np.float32(1)-vs,np.float32(1)-vb


@njit(cache=False,fastmath=False)
def _pixel_reference(a,canopy,trunk,bush,bounds,da,dv,dt,first_heights,sh,vs,vb):
    for row in range(a.shape[0]):
        for col in range(a.shape[1]):
            sh[row,col],vs[row,col],vb[row,col]=_trace_pixel_reference(row,col,a,canopy,trunk,bush,bounds,da,dv,dt,first_heights)


def _reference_pixel_trace(amaxvalue,a,canopy,trunk,bush,azimuth,altitude,scale):
    # Host prep mirrors _shadow_pixel's no-bush branch line for line.
    bounds,heights=ray_schedule(a.shape,amaxvalue,azimuth,altitude,scale)
    da=np.asarray(heights,dtype=a.dtype)
    dv=np.asarray(heights,dtype=canopy.dtype)
    dt=np.asarray(heights,dtype=trunk.dtype)
    first_heights=np.asarray(heights,dtype=np.float32)
    outputs=tuple(np.empty(a.shape,dtype=np.float32) for _ in range(3))
    _pixel_reference(a,canopy,trunk,bush,bounds,da,dv,dt,first_heights,*outputs)
    return outputs


# ---------------------------------------------------------------------------
# Harness
# ---------------------------------------------------------------------------
def _bitwise(candidate,reference,label):
    for name,got,want in zip(('sh','vs','vb'),candidate,reference,strict=True):
        assert got.dtype==want.dtype==np.float32,(label,name,got.dtype,want.dtype)
        assert got.shape==want.shape,(label,name)
        assert np.array_equal(got.view(np.uint32),want.view(np.uint32)),f'{label}: {name} differs bitwise'
        assert np.array_equal(np.isnan(got),np.isnan(want)),f'{label}: {name} NaN positions differ'


def _run(amaxvalue,a,canopy,trunk,bush,azimuth,altitude,scale,label):
    a,canopy,trunk,bush=(np.ascontiguousarray(np.asarray(x)) for x in (a,canopy,trunk,bush))
    # Pixel-route precondition for this harness: the global bush predicate
    # must be false without NaN poisoning (NaN bush routes to the fallback).
    assert bush.max()<=0,(label,'bush must not be positive here')
    reference=_reference_pixel_trace(amaxvalue,a,canopy,trunk,bush,azimuth,altitude,scale)
    serial=shadow_pixel_serial(amaxvalue,a,canopy,trunk,bush,azimuth,altitude,scale)
    parallel=shadow_pixel_parallel(amaxvalue,a,canopy,trunk,bush,azimuth,altitude,scale)
    _bitwise(serial,reference,label+' serial')
    _bitwise(parallel,reference,label+' parallel')
    return serial


def _steps(shape,amaxvalue,azimuth,altitude,scale):
    bounds,_=ray_schedule(shape,amaxvalue,azimuth,altitude,scale)
    return len(bounds)


# ---------------------------------------------------------------------------
# Schedule-length anchors (document the L0 structure of the crafted cases)
# ---------------------------------------------------------------------------
def test_schedule_length_anchors():
    # The schedule loop appends the first bound-violating step, so a full
    # sweep retains max(shape) steps and the maximum length is max(shape).
    assert _steps((5,5),-1.0,0,10,1)==0
    assert _steps((1,1),5.0,0,10,1)==1
    assert _steps((3,3),0.5,0,45,1)==1
    assert _steps((3,3),1.0,0,45,1)==2
    assert _steps((2,2),1.0,0,0,1)==2
    assert _steps((5,5),4.0,0,0,1)==5
    assert _steps((5,5),4.0,0,45,1)==5
    assert _steps((5,5),10.0,90,0,1)==5
    assert _steps((17,33),40.0,0,0,1)==17
    assert _steps((17,33),40.0,90,0,1)==33
    assert _steps((17,160),500.0,90,0,1)==160
    assert _steps((32,32),500.0,0,0,1)==32


# ---------------------------------------------------------------------------
# Degenerate schedules
# ---------------------------------------------------------------------------
def test_empty_schedule():
    for shape in ((5,5),(1,1)):
        a=np.zeros(shape,np.float32)
        canopy=np.zeros(shape,np.float32)
        trunk=np.zeros(shape,np.float32)
        bush=np.zeros(shape,np.float32)
        _run(-1.0,a,canopy,trunk,bush,0,10,1,f'empty-{shape}')
        _run(5.0,a,canopy,trunk,bush,0,10,1,f'single-cell-{shape}')


def test_one_step_schedule():
    a=np.zeros((3,3),np.float32); a[0,1]=3.0
    canopy=np.zeros((3,3),np.float32); canopy[0,1]=0.5
    trunk=np.zeros((3,3),np.float32); trunk[1,1]=2.0
    bush=np.zeros((3,3),np.float32)
    assert _steps((3,3),0.5,0,45,1)==1
    _run(0.5,a,canopy,trunk,bush,0,45,1,'one-step')


def test_two_step_schedule():
    # Receiver (2,1) sees building a[0,1]=3 only at the second step.
    a=np.zeros((3,3),np.float32); a[0,1]=3.0
    canopy=np.zeros((3,3),np.float32); canopy[0,2]=4.0
    trunk=np.zeros((3,3),np.float32); trunk[2,1]=2.0
    bush=np.zeros((3,3),np.float32)
    assert _steps((3,3),1.0,0,45,1)==2
    _run(1.0,a,canopy,trunk,bush,0,45,1,'two-step')


# ---------------------------------------------------------------------------
# Absorption position: the break must fire exactly one step too late, never
# on the first step.
# ---------------------------------------------------------------------------
def test_first_step_hit_must_not_break():
    # Receiver (2,2) is absorbed by its first sample a[1,2]=10. The first-step
    # block then leaves vs=1 (canopy-building=0.5 < first height 1, trunk at
    # the receiver above height), so the second step must still run to zero vs
    # via the reset before any exit is allowed.
    a=np.zeros((5,5),np.float32); a[1,2]=10.0
    canopy=np.zeros((5,5),np.float32); canopy[1,2]=10.5; canopy[0,2]=6.0
    trunk=np.zeros((5,5),np.float32); trunk[2,2]=5.0
    bush=np.zeros((5,5),np.float32)
    assert _steps((5,5),4.0,0,45,1)==5
    out=_run(4.0,a,canopy,trunk,bush,0,45,1,'first-step-hit')
    # Negative control: a wrong break on the first step would leave vs=1 and
    # return 0 in the vegetation mask; the guarded exit must return 1.
    assert out[0][2,2]==np.float32(0)
    assert out[1][2,2]==np.float32(1)
    assert out[2][2,2]==np.float32(1)


def test_second_step_hit():
    # Receiver (2,2) sees building a[0,2]=10 only at the second step.
    a=np.zeros((5,5),np.float32); a[0,2]=10.0
    canopy=np.zeros((5,5),np.float32); canopy[1,2]=1.0
    trunk=np.zeros((5,5),np.float32); trunk[1,2]=0.5
    bush=np.zeros((5,5),np.float32)
    assert _steps((5,5),4.0,0,0,1)==5
    out=_run(4.0,a,canopy,trunk,bush,0,0,1,'second-step-hit')
    assert out[0][2,2]==np.float32(0)
    assert out[1][2,2]==np.float32(1)
    assert out[2][2,2]==np.float32(1)


def test_no_hit_open_ray():
    a=np.zeros((6,6),np.float32)
    canopy=np.zeros((6,6),np.float32); canopy[:,1::2]=3.0
    trunk=np.zeros((6,6),np.float32); trunk[:,1::2]=3.0
    bush=np.zeros((6,6),np.float32)
    _run(5.0,a,canopy,trunk,bush,0,0,1,'no-hit')


def test_late_hit_non_square():
    # Tower row 0 on a 17x33 scene: receivers absorb at their row index, the
    # last one at step 16; columns away from the tower never absorb.
    shape=(17,33)
    a=np.zeros(shape,np.float32); a[0,7]=50.0; a[0,25]=30.0
    canopy=np.zeros(shape,np.float32); canopy[0,7]=10.0
    trunk=np.zeros(shape,np.float32); trunk[0,25]=10.0
    bush=np.zeros(shape,np.float32)
    assert _steps(shape,40.0,0,0,1)==17
    _run(40.0,a,canopy,trunk,bush,0,0,1,'late-hit')


def test_early_hit_long_suffix():
    # Azimuth 90 marches along columns on a 17x160 scene: absorption at the
    # first step for receiver (8,80) with 159 remaining steps to skip.
    shape=(17,160)
    a=np.zeros(shape,np.float32); a[8,79]=9.0
    canopy=np.zeros(shape,np.float32); canopy[8,78]=4.0
    trunk=np.zeros(shape,np.float32)
    bush=np.zeros(shape,np.float32)
    assert _steps(shape,500.0,90,0,1)>=150
    _run(500.0,a,canopy,trunk,bush,90,0,1,'early-hit-long-suffix')


# ---------------------------------------------------------------------------
# Domain edges
# ---------------------------------------------------------------------------
def test_receiver_below_zero():
    a=np.full((5,5),-5.0,np.float32); a[0,2]=3.0; a[4,4]=-0.5
    canopy=np.zeros((5,5),np.float32)
    trunk=np.zeros((5,5),np.float32)
    bush=np.zeros((5,5),np.float32)
    _run(4.0,a,canopy,trunk,bush,0,10,1,'below-zero')


def test_zero_padding_suffix():
    # Azimuth 90 marches along columns, so steps beyond half the width have
    # empty destination windows: pure out-of-domain zero padding suffixes.
    shape=(17,33)
    a=np.zeros(shape,np.float32); a[:,3]=8.0
    canopy=np.zeros(shape,np.float32); canopy[:,2]=5.0
    trunk=np.zeros(shape,np.float32); trunk[:,4]=1.0
    bush=np.zeros(shape,np.float32)
    assert _steps(shape,40.0,90,0,1)==33
    _run(40.0,a,canopy,trunk,bush,90,0,1,'zero-padding')


def test_canopy_trunk_gap_patterns():
    shape=(6,7)
    a=np.zeros(shape,np.float32); a[0,:]=4.0
    canopy=np.zeros(shape,np.float32); canopy[:,1::2]=6.0
    trunk=np.zeros(shape,np.float32); trunk[::2,0]=9.0; trunk[3,4]=6.5
    bush=np.full(shape,-2.0,np.float32)
    _run(6.0,a,canopy,trunk,bush,0,5,1,'gaps')


def test_signed_zeros():
    shape=(5,5)
    a=np.full(shape,-0.0,np.float32); a[1,2]=0.0; a[0,2]=2.0
    canopy=np.full(shape,-0.0,np.float32); canopy[0,2]=np.float32(2.0)
    trunk=np.full(shape,-0.0,np.float32); trunk[1,2]=np.float32(1.0)
    bush=np.full(shape,-0.0,np.float32)
    _run(4.0,a,canopy,trunk,bush,0,0,1,'signed-zeros')


# ---------------------------------------------------------------------------
# Nonfinite inputs: after absorption (NaN/Inf samples the break skips), on
# the transition step, and at the receiver itself.
# ---------------------------------------------------------------------------
def test_nonfinite_samples_after_absorption():
    a=np.zeros((5,5),np.float32); a[1,2]=10.0; a[0,2]=np.nan
    canopy=np.zeros((5,5),np.float32); canopy[0,2]=np.inf; canopy[1,2]=-np.inf
    trunk=np.zeros((5,5),np.float32); trunk[0,2]=np.nan; trunk[1,2]=np.inf
    bush=np.zeros((5,5),np.float32)
    _run(4.0,a,canopy,trunk,bush,0,0,1,'nonfinite-after-absorption')


def test_nonfinite_samples_random_scenes():
    rng=np.random.default_rng(42)
    shape=(11,13)
    a=rng.uniform(0.0,15.0,shape).astype(np.float32)
    canopy=rng.uniform(0.0,8.0,shape).astype(np.float32)
    trunk=rng.uniform(0.0,6.0,shape).astype(np.float32)
    a[2,3]=np.nan; a[5,5]=np.inf; a[7,2]=-np.inf
    canopy[3,4]=np.nan; canopy[6,1]=np.inf
    trunk[4,6]=np.nan; trunk[8,8]=-np.inf
    bush=np.zeros(shape,np.float32)
    _run(20.0,a,canopy,trunk,bush,15.0,25.0,1.0,'nonfinite-random')


def test_nonfinite_receivers():
    a=np.zeros((4,4),np.float32)
    a[1,1]=np.nan; a[2,2]=-np.inf; a[3,3]=np.inf; a[0,0]=-0.0
    canopy=np.zeros((4,4),np.float32); canopy[0,1]=7.0
    trunk=np.zeros((4,4),np.float32); trunk[1,2]=2.0
    bush=np.zeros((4,4),np.float32)
    _run(3.0,a,canopy,trunk,bush,0,0,1,'nonfinite-receivers')


# ---------------------------------------------------------------------------
# Seeded random scenes: vegetation and buildings, non-square shapes, long
# schedules. The schedule length is bounded by max(shape) (one index per
# step, plus the retained bound-violating step), so a 32x32 scene cannot
# exceed 32 steps; 150+ step schedules need a long dimension and are
# provided by the (17,160) and (160,17) configs.
# ---------------------------------------------------------------------------
RANDOM_CONFIGS=[
    (0,(17,33),0.0,0.0,1.0,40.0),
    (1,(17,33),90.0,20.0,1.0,40.0),
    (2,(8,12),225.0,45.0,2.0,30.0),
    (3,(32,32),45.0,0.0,1.0,500.0),
    (4,(32,32),135.0,60.0,0.5,500.0),
    (5,(17,160),90.0,0.0,1.0,500.0),
    (6,(160,17),180.0,10.0,1.0,500.0),
    (7,(160,17),350.0,80.0,2.0,500.0),
    (8,(5,5),0.0,-45.0,1.0,4.0),
    (9,(24,7),270.0,30.0,1.5,60.0),
    (10,(9,9),200.0,5.0,1.0,100.0),
    (11,(13,29),350.0,15.0,1.0,150.0),
]


def _random_scene(rng,shape,dtype=np.float32):
    a=rng.uniform(-2.0,20.0,shape).astype(dtype)
    canopy=rng.uniform(0.0,10.0,shape).astype(dtype)
    trunk=rng.uniform(0.0,8.0,shape).astype(dtype)
    canopy[rng.random(shape)<0.3]=0.0
    trunk[rng.random(shape)<0.3]=0.0
    bush=np.full(shape,-1.0,dtype)
    bush[rng.random(shape)<0.5]=0.0
    return a,canopy,trunk,bush


@pytest.mark.parametrize('seed,shape,azimuth,altitude,scale,amaxvalue',RANDOM_CONFIGS)
def test_random_scenes(seed,shape,azimuth,altitude,scale,amaxvalue):
    rng=np.random.default_rng(seed)
    a,canopy,trunk,bush=_random_scene(rng,shape)
    _run(amaxvalue,a,canopy,trunk,bush,azimuth,altitude,scale,f'random-{seed}')


def test_random_scene_float64():
    rng=np.random.default_rng(77)
    shape=(10,23)
    a,canopy,trunk,bush=_random_scene(rng,shape,np.float64)
    _run(60.0,a,canopy,trunk,bush,100.0,35.0,1.25,'random-float64')


# ---------------------------------------------------------------------------
# Positive-bush fallback: route identity with the untouched step-major entry.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize('parallel',[False,True],ids=['serial','parallel'])
def test_positive_bush_fallback_route_unchanged(parallel):
    rng=np.random.default_rng(11)
    shape=(9,9)
    a=rng.uniform(0.0,10.0,shape).astype(np.float32)
    canopy=rng.uniform(0.0,6.0,shape).astype(np.float32)
    trunk=rng.uniform(0.0,4.0,shape).astype(np.float32)
    bush=rng.uniform(0.0,3.0,shape).astype(np.float32)
    args=(20.0,a,canopy,trunk,bush,120.0,30.0,1.0)
    pixel=shadow_pixel_parallel(*args) if parallel else shadow_pixel_serial(*args)
    want=shadow_serial(*args)
    for got,expected in zip(pixel,want,strict=True):
        assert got.dtype==expected.dtype
        assert np.array_equal(got.view(np.uint32),expected.view(np.uint32))
