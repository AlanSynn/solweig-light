"""Direction accumulation preserves NumPy's warning and exception contract."""
import warnings
import numpy as np
import pytest
from gvf_prepare_cases import build_scene, snapshots, assert_gvf_outputs
from solweig_light.radiation import gvf_batch, gvf_prepared


def prepared_step(extreme):
    scene=build_scene(12,12,with_buildings=False,water=False)
    scene['walls'][:]=1
    scene['shadow'][:]=1
    if extreme:
        scene['Tg']=np.full((12,12),1.5e11,np.float64)
    with np.errstate(all='ignore'):
        return gvf_prepared.prepare_gvf_step(**snapshots(scene))


def outcome(step,parallel,regime):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always',RuntimeWarning)
        with np.errstate(divide='ignore',invalid='ignore',over=regime,under='ignore'):
            try:
                result=gvf_prepared.run_prepared_gvf_step(step,12,12,parallel=parallel)
                error=None
            except FloatingPointError as exc:
                result=None;error=(type(exc),str(exc))
    return result,error,[(item.category,str(item.message)) for item in caught]


@pytest.mark.parametrize('regime',['warn','raise','ignore'])
def test_finite_direction_results_overflow_accumulator_like_numpy(regime):
    step=prepared_step(True)
    assert np.isfinite(step.lup_term).all()
    expected,error,warnings_expected=outcome(step,False,regime)
    actual,error_actual,warnings_actual=outcome(step,True,regime)
    assert error_actual==error
    assert warnings_actual==warnings_expected
    if regime=='warn':
        assert warnings_expected==[(RuntimeWarning,'overflow encountered in add')]*2
    if regime=='raise':
        assert error==(FloatingPointError,'overflow encountered in add')
    else:
        assert_gvf_outputs(actual,expected)
        assert np.isinf(actual[0]).all()


def test_normal_finite_accumulators_keep_compiled_route():
    step=prepared_step(False)
    with np.errstate(all='ignore'):
        accumulators=gvf_batch.run(step,12,12,32)
    assert accumulators is not None and np.isfinite(accumulators).all()
    actual,error,caught=outcome(step,True,'warn')
    expected,error_ref,caught_ref=outcome(step,False,'warn')
    assert error is error_ref is None and caught==caught_ref==[]
    assert_gvf_outputs(actual,expected)
