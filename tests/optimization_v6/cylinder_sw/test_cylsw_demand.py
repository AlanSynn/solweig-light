import importlib.util as _ilu
from pathlib import Path as _Path
_conftest_path = _Path(__file__).resolve().parent / 'conftest.py'
_spec = _ilu.spec_from_file_location('_cylindersw_conftest', str(_conftest_path))
_conftest = _ilu.module_from_spec(_spec)
import sys as _sys
_sys.modules['_spec_name'] = _conftest
_spec.loader.exec_module(_conftest)
synthetic_values = _conftest.synthetic_values
"""Private demand-profile contract: PIPELINE_CYLINDER_ANISOTROPIC vs FULL_DIAGNOSTICS.The public diagnostic entry stays on the generic full path; the narrow route
exists only when the pipeline explicitly opts in. Missing diagnostics are
simply not requested — never zeros.
"""
import numpy as np
import pytest
from solweig_light.radiation import cylinder_shortwave



def test_default_profile_is_full_diagnostics():
    assert cylinder_shortwave.demand_profile() == cylinder_shortwave.FULL_DIAGNOSTICS


def test_entry_declines_without_pipeline_opt_in():
    values = synthetic_values(16, 16)
    assert cylinder_shortwave.kside_cylinder_anisotropic(values, block_pixels=16, parallel=True) is None


def test_profile_setter_round_trip(admitted_profile):
    assert cylinder_shortwave.demand_profile() == cylinder_shortwave.PIPELINE_CYLINDER_ANISOTROPIC
    cylinder_shortwave.set_demand_profile(cylinder_shortwave.FULL_DIAGNOSTICS)
    assert cylinder_shortwave.demand_profile() == cylinder_shortwave.FULL_DIAGNOSTICS


@pytest.mark.parametrize('bogus', ['cylinder_anisotropic', 'PIPELINE_CYLINDER_ANISOTROPIC ', None, 1])
def test_profile_setter_rejects_unknown(bogus):
    before = cylinder_shortwave.demand_profile()
    with pytest.raises(ValueError):
        cylinder_shortwave.set_demand_profile(bogus)
    assert cylinder_shortwave.demand_profile() == before


def test_box_mode_never_enters_narrow_route(admitted_profile):
    """cyl!=1 stays on the generic path even with the pipeline profile set."""
    values = synthetic_values(16, 16)
    values['cyl'] = np.float32(0)
    assert cylinder_shortwave.kside_cylinder_anisotropic(values, block_pixels=16, parallel=True) is None


def test_isotropic_diffuse_never_enters_narrow_route(admitted_profile):
    values = synthetic_values(16, 16)
    values['anisotropic_diffuse'] = 0
    assert cylinder_shortwave.kside_cylinder_anisotropic(values, block_pixels=16, parallel=True) is None
