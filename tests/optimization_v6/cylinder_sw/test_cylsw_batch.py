"""Compiled invocation scheduling preserves the retained cylinder graph."""
import numpy as np
import pytest
from solweig_light.geometry.visibility import PackedVisibility, LazyDiffVisibility
from solweig_light.radiation import cylinder_shortwave as sw
from test_cylsw_parity import synthetic_values, assert_bitwise


@pytest.mark.parametrize('shape,capacity', [((1,8),128),((7,19),16),((17,19),128)])
@pytest.mark.parametrize('surface_dtype',[np.float32,np.float64])
def test_batch_shared_lazy_bitwise(shape,capacity,surface_dtype,admitted_profile,monkeypatch):
    values=synthetic_values(*shape,seed=9)
    for name in ('shmat','vegshmat','vbshvegshmat'):
        dense=values[name]
        # Include ternary and raw patterns; masks still perform numeric
        # multiplication, including zero times infinity.
        dense.reshape(-1,dense.shape[2])[0,0]=np.float32(2)
        dense.reshape(-1,dense.shape[2])[-1,1]=np.float32(-0.)
        values[name]=PackedVisibility.from_dense(dense)
    values['diffsh']=LazyDiffVisibility(values['shmat'],values['vegshmat'])
    for name in ('radI','radD','albedo'):
        values[name]=surface_dtype(values[name])
    from solweig_light._native_dispatch import sw_batch
    real_execute=sw_batch.execute
    admitted=[]
    def tracked(*args,**kwargs):
        result=real_execute(*args,**kwargs)
        admitted.append(result is not None)
        return result
    monkeypatch.setattr(sw_batch,'execute',tracked)
    with np.errstate(all='ignore'):
        with monkeypatch.context() as patch:
            patch.setattr(sw_batch,'execute',lambda *a,**k:None)
            expected=sw.kside_cylinder_anisotropic(values,block_pixels=capacity,parallel=False)
        for parallel in (False,True):
            actual=sw.kside_cylinder_anisotropic(values,block_pixels=capacity,parallel=parallel)
            assert_bitwise(actual,expected,'batch')
    assert_bitwise(actual,expected,'batch')
    assert admitted == [True,True]


def _assembly_values(pixels=8):
    values=synthetic_values(1,pixels)
    values.update(radI=np.float32(3e38),radD=np.float32(1e38),altitude=np.float32(0))
    values['shadow'][:]=1
    values['lv'][:,0]=45
    values['lv'][:,1]=np.arange(6)*60
    values['lv'][:,2]=.1
    for name in ('shmat','vegshmat','vbshvegshmat'):
        values[name]=PackedVisibility.from_dense(np.ones((1,pixels,6),np.float32))
    values['diffsh']=LazyDiffVisibility(values['shmat'],values['vegshmat'])
    return values


def _assembly_outcome(values,regime,retained,monkeypatch):
    import warnings
    from solweig_light._native_dispatch import sw_batch
    with monkeypatch.context() as patch:
        if retained:patch.setattr(sw_batch,'execute',lambda *a,**k:None)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always',RuntimeWarning)
            with np.errstate(divide='ignore',invalid='ignore',over=regime,under='ignore'):
                try:
                    result=sw.kside_cylinder_anisotropic(values,block_pixels=8,parallel=False)
                    error=None
                except (FloatingPointError,IndexError) as exc:
                    result=None;error=(type(exc),str(exc))
    return result,error,[(item.category,str(item.message)) for item in caught]


@pytest.mark.parametrize('regime',['warn','raise','ignore'])
def test_batch_assembly_overflow_replays_numpy(regime,admitted_profile,monkeypatch):
    values=_assembly_values()
    expected,error,expected_warnings=_assembly_outcome(values,regime,True,monkeypatch)
    actual,actual_error,actual_warnings=_assembly_outcome(values,regime,False,monkeypatch)
    assert actual_error==error
    assert actual_warnings==expected_warnings
    if regime=='warn':assert expected_warnings==[(RuntimeWarning,'overflow encountered in add')]
    if regime=='raise':assert error==(FloatingPointError,'overflow encountered in add')
    else:assert_bitwise(actual,expected,'assembly overflow')


@pytest.mark.parametrize('regime',['warn','raise','ignore'])
def test_batch_earlier_assembly_event_precedes_later_reserved_code(regime,admitted_profile,monkeypatch):
    from solweig_light.geometry.visibility import _EncodedPatch
    values=_assembly_values(16)
    patches=list(values['shmat']._patches)
    patches[0]=_EncodedPatch('ternary',b'\x55\x55\x57\x55')
    values['shmat']=PackedVisibility((1,16,6),tuple(patches))
    values['diffsh']=LazyDiffVisibility(values['shmat'],values['vegshmat'])
    _,expected_error,expected_warnings=_assembly_outcome(values,regime,True,monkeypatch)
    _,actual_error,actual_warnings=_assembly_outcome(values,regime,False,monkeypatch)
    assert actual_error==expected_error
    assert actual_warnings==expected_warnings
    assert expected_error[0] is (FloatingPointError if regime=='raise' else IndexError)


@pytest.mark.parametrize('case',['direct','visibility'])
def test_batch_nonfinite_ignore_replays_exact_nan_payloads(case,admitted_profile,monkeypatch):
    values=_assembly_values()
    values['radI']=np.float32(650)
    values['radD']=np.float32(120)
    first=np.array(0x7fc11111,np.uint32).view(np.float32)
    second=np.array(0x7fc22222,np.uint32).view(np.float32)
    if case=='direct':
        values['shadow'][:]=first
        values['lv'][0,2]=second
    else:
        shadow=np.ones((1,8,6),np.float32);shadow[:,:,0]=first
        vegetation=np.ones((1,8,6),np.float32);vegetation[:,:,0]=second
        values['shmat']=PackedVisibility.from_dense(shadow)
        values['vegshmat']=PackedVisibility.from_dense(vegetation)
        values['diffsh']=LazyDiffVisibility(values['shmat'],values['vegshmat'])
    expected,error,_=_assembly_outcome(values,'ignore',True,monkeypatch)
    actual,actual_error,_=_assembly_outcome(values,'ignore',False,monkeypatch)
    assert error is actual_error is None
    assert_bitwise(actual,expected,'nonfinite assembly payload')
