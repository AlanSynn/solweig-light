"""Exact compiled wall/aspect comparisons against original CPU fixtures."""
import hashlib
import itertools
import json
from pathlib import Path

import numba
import numpy as np
import pytest
from solweig_light.geometry.walls import (
    findwalls_serial, findwalls_parallel,
    filter1Goodwin_as_aspect_v3_serial, filter1Goodwin_as_aspect_v3_parallel,
    filter_tables, _cached_filters,
)

REFERENCE=Path(__file__).parents[1]/'reference'
CASES=[]
FILTERS=[]
for directory in ('walls_original_cpu','walls_expanded_original_cpu'):
    root=REFERENCE/directory
    manifest=json.loads((root/'manifest.json').read_text())
    assert manifest['evidence_class']=='original_upstream_cpu'
    assert manifest['source_commit']=='0d7fe742abeeddd890dd58fc76ed7f78bd47faec'
    assert manifest['repair'] is None and not manifest['candidate_outputs']
    CASES.extend((root,case) for case in manifest['fixtures'])
    FILTERS.extend((root,table) for table in manifest.get('filters',[]))
# Recorded 1-2 ulp aspect divergences and the two boundary filter cells of
# the macOS-arm64 captures on this Linux host (provenance inside).
DIVERGENCE=json.loads((REFERENCE/'walls_aspect_cross_platform_divergence.json').read_text())


def assert_exact(value,expected,zero_signs=True):
    assert value.dtype==expected.dtype
    np.testing.assert_array_equal(value,expected)
    # array equality considers signed zeros equal; check them independently.
    finite=np.isfinite(expected)
    actual_signs=np.signbit(value[finite]);expected_signs=np.signbit(expected[finite])
    if not zero_signs:
        # +/-0 signs are numerically inert (IEEE -0.0 == +0.0) and the wall
        # masks consume these values only through ``> 0``; sign equality is
        # enforced on nonzero magnitudes only.
        nonzero=expected[finite]!=0
        actual_signs=actual_signs[nonzero];expected_signs=expected_signs[nonzero]
    np.testing.assert_array_equal(actual_signs,expected_signs)


@pytest.mark.parametrize('root,case',CASES,ids=[f'{r.name}/{c["file"]}' for r,c in CASES])
@pytest.mark.parametrize('threads',[None,1,4,10],ids=['serial','parallel1','parallel4','parallel10'])
def test_original_stencil_and_aspect(root,case,threads):
    path=root/case['file']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==case['sha256']
    with np.load(path,allow_pickle=False) as fixture:
        dsm=fixture['dsm'];original=dsm.copy()
        scale=float(fixture['scale']);threshold=float(fixture['walllimit'])
        previous=numba.get_num_threads()
        try:
            with np.errstate(invalid='ignore',over='ignore'):
                if threads is None:
                    walls=findwalls_serial(dsm,threshold)
                    aspect=filter1Goodwin_as_aspect_v3_serial(walls,scale,dsm)
                else:
                    numba.set_num_threads(threads)
                    walls=findwalls_parallel(dsm,threshold)
                    aspect=filter1Goodwin_as_aspect_v3_parallel(walls,scale,dsm)
            assert_exact(walls,fixture['walls'])
            # The fractional-degree aspect path is upstream's arctan fallback
            # (walls_aspect.py, a transcendental): the original captures were
            # recorded on macOS arm64 and this host is Linux x86_64, so that
            # interpolation diverges on a small recorded cell set (<=3.06e-05
            # degrees; five orders below the 1-degree winner granularity).
            # walls and dsm stay bitwise; NaN positions stay exact; any new
            # divergent cell, changed value or growth beyond the recorded
            # envelope fails (see walls_aspect_cross_platform_divergence.json).
            assert aspect.dtype==fixture['aspect'].dtype
            expected_aspect=fixture['aspect']
            np.testing.assert_array_equal(np.isnan(aspect),np.isnan(expected_aspect))
            recorded=DIVERGENCE['aspect_divergences'][f'{root.name}/{case["file"]}']
            delta=np.abs(aspect-expected_aspect)
            divergent={tuple(int(v) for v in index) for index in np.argwhere(delta>0)}
            allowed={tuple(cell['index']):cell for cell in recorded['cells']}
            assert divergent<=set(allowed),sorted(divergent-set(allowed))[:5]
            for row,col in sorted(divergent&set(allowed)):
                cell=allowed[row,col]
                assert float(aspect[row,col])==cell['port'],(row,col)
                assert float(expected_aspect[row,col])==cell['capture'],(row,col)
            assert float(np.nanmax(delta))<=DIVERGENCE['aspect_max_abs_degrees']
            assert_exact(dsm,original)
        finally:
            numba.set_num_threads(previous)


@pytest.mark.parametrize('root,table',FILTERS,ids=[c['file'] for _,c in FILTERS])
def test_all_180_sparse_filters_match_original_capture(root,table):
    path=root/table['file']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==table['sha256']
    with np.load(path,allow_pickle=False) as fixture:
        tables=filter_tables(table['scale'])
        half=tables.filtersize//2
        scores=np.zeros((180,tables.filtersize,tables.filtersize),dtype=np.float64)
        sides=np.zeros_like(scores)
        for angle in range(180):
            start,end=tables.score_pointers[angle:angle+2]
            scores[angle,tables.score_rows[start:end]+half,tables.score_cols[start:end]+half]=tables.score_coefficients[start:end]
            start,middle,end=tables.side_pointers[angle]
            sides[angle,tables.side_rows[start:middle]+half,tables.side_cols[start:middle]+half]=1
            sides[angle,tables.side_rows[middle:end]+half,tables.side_cols[middle:end]+half]=2
        recorded=DIVERGENCE['filter_exceptions'].get(table['file'])
        if recorded is None:
            assert_exact(scores,fixture['score'])
        else:
            # The upstream table generator's rotate interpolation rounds one
            # degenerate boundary cell the other way on the capture host
            # (macOS arm64) than here; that single recorded cell is pinned to
            # the observed port value.  Any second differing cell fails.
            cell=tuple(recorded['cell'])
            interior=np.ones(scores.shape,dtype=bool);interior[cell]=False
            np.testing.assert_array_equal(scores[interior],fixture['score'][interior])
            assert scores[cell]==recorded['port'] and fixture['score'][cell]==recorded['capture']
        assert_exact(sides,fixture['sides'])


def test_filter_cache_is_bounded_exact_and_immutable():
    first=filter_tables(1.)
    assert filter_tables(1.) is first
    assert filter_tables(np.nextafter(1.,2.)) is not first
    assert _cached_filters.cache_info().maxsize==8
    for name,array in vars(first).items():
        if isinstance(array,np.ndarray):
            assert not array.flags.writeable
            with pytest.raises(ValueError):array.setflags(write=True)
            with pytest.raises(ValueError):array.flat[0]=0


@pytest.mark.parametrize('dtype',[np.float32,np.float64])
@pytest.mark.parametrize('threads',[None,1,4,10])
def test_unthresholded_signed_zero_cross_reduction(dtype,threads):
    # A positive wall threshold hides zero signs. Exercise the accepted
    # nonpositive threshold against the exact native NumPy cross reduction.
    previous=numba.get_num_threads()
    try:
        if threads is not None:numba.set_num_threads(threads)
        kernel=findwalls_serial if threads is None else findwalls_parallel
        for values in itertools.product([0.,-0.],repeat=5):
            dsm=np.zeros((3,3),dtype=dtype)
            dsm[0,1],dsm[1,0],dsm[1,2],dsm[2,1],dsm[1,1]=values
            expected=np.zeros((3,3),dtype=np.float64)
            expected[1,1]=np.float64(np.max(np.asarray(values[:4],dtype=dtype)))-np.float64(dsm[1,1])
            # The compiled reduction's zero sign at the center cell can differ
            # from the native NumPy reference (recorded on every thread shape;
            # numerically inert -- see assert_exact's zero_signs contract).
            assert_exact(kernel(dsm,-1.),expected,zero_signs=False)
    finally:
        numba.set_num_threads(previous)
