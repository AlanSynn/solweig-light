"""Invocation-wide compiled scheduling parity on the frozen stream fixtures."""
import numpy as np
import pytest
from stream_test_helpers import make_case, stream_plan, outputs_bitwise
from test_lw_stream import _run_stream
from solweig_light._native_dispatch import lw_batch


@pytest.mark.parametrize('surface_dtype',[np.float32,np.float64])
@pytest.mark.parametrize('rows,patches,capacity', [(8,5,128),(37,153,16),(131,153,128),(300,9,16)])
def test_compiled_batch_matches_retained_stream(rows, patches, capacity, surface_dtype):
    case = make_case(rows, patches, seed=rows*31+patches)
    case['sun_surface']=surface_dtype(1+2**-25)
    case['shade_surface']=surface_dtype(1+2**-25)
    expected, _, _ = _run_stream(case, rows, capacity)
    plan = stream_plan(case, rows, row='B', block_pixels=capacity, width=8)
    try:
        actual = lw_batch.execute(plan)
        assert outputs_bitwise(actual, expected)
    finally:
        plan.close()


def test_batch_reserved_code_rejected_before_parallel_launch(monkeypatch):
    from solweig_light._native_dispatch import direct_aosoa as da
    from stream_test_helpers import build_channel
    rows,patches=131,5
    case=make_case(rows,patches,seed=13)
    codes=np.zeros(rows,np.uint8);codes[130]=3
    case['values']['vbshvegshmat']=build_channel(rows,['ternary']*patches,codes=codes)
    plan=stream_plan(case,rows,block_pixels=128)
    def forbidden(*args):
        raise AssertionError('parallel launch preceded reserved-code validation')
    monkeypatch.setattr(lw_batch,'_batch',forbidden)
    try:
        with pytest.raises(IndexError,match='Reserved visibility code'):
            lw_batch.execute(plan)
    finally:
        plan.close()
