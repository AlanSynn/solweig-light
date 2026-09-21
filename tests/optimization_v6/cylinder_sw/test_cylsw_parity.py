"""L1 parity: narrow cylinder scratch vs the retained original production
route (bitwise) and vs the untouched serial reference (original budget).

Bitwise binds the specialization to the compiled wrapper route it
specializes: at base 5e1fab46 that route already differs from the serial
translation on KsideD/Kside by a pre-existing float32/float64 degree-radian
profile in the cached geometry, so no specialization of the route can be
bitwise vs serial. Serial comparisons therefore retain the untouched
comparison_v1 budget (atol 0.05, rtol 1e-5), unchanged from upstream.
"""
import importlib.util as _ilu
import sys as _sys
from pathlib import Path as _Path

import numpy as np
import pytest

from solweig_light.radiation import cylinder_shortwave

# Load THIS family's conftest by file path: bare `import conftest` is
# shadowed by sibling families' conftest modules when several directories
# are collected in one pytest invocation.
_conftest_path = _Path(__file__).resolve().parent / 'conftest.py'
_spec = _ilu.spec_from_file_location('_cylindersw_conftest', str(_conftest_path))
_conftest = _ilu.module_from_spec(_spec)
_sys.modules['_cylindersw_conftest'] = _conftest
_spec.loader.exec_module(_conftest)
assert_bitwise = _conftest.assert_bitwise
assert_within_original_budget = _conftest.assert_within_original_budget
load_packet_values = _conftest.load_packet_values
packet_cases = _conftest.packet_cases
serial_reference = _conftest.serial_reference
synthetic_values = _conftest.synthetic_values
wrapper_route = _conftest.wrapper_route

CYLINDER_CASES = [case for case in packet_cases()
                  if np.asarray(load_packet_values(case)['cyl']).reshape(()) in (1, True)]


@pytest.mark.parametrize('case', CYLINDER_CASES, ids=lambda case: case['label'])
@pytest.mark.parametrize('parallel', [False, True])
def test_real_packet_bitwise_vs_retained_route(case, parallel, admitted_profile):
    values = load_packet_values(case)
    expected = wrapper_route(values, block_pixels=17, parallel=parallel)
    actual = cylinder_shortwave.kside_cylinder_anisotropic(values, block_pixels=17, parallel=parallel)
    assert actual is not None
    assert_bitwise(actual, expected, f"packet/{case['label']}/parallel={parallel}")


@pytest.mark.parametrize('case', CYLINDER_CASES, ids=lambda case: case['label'])
def test_real_packet_serial_reference_within_original_budget(case, admitted_profile):
    values = load_packet_values(case)
    expected = serial_reference(values)
    actual = cylinder_shortwave.kside_cylinder_anisotropic(values, block_pixels=17, parallel=False)
    assert actual is not None
    assert_within_original_budget(actual, expected, f"serial-budget/{case['label']}")


@pytest.mark.parametrize('size', [16, 32, 64, 128])
@pytest.mark.parametrize('mode', ['baseline', 'zero-sentinel', 'extreme-sun', 'vegetated'])
def test_adversarial_sizes_bitwise(size, mode, admitted_profile):
    values = synthetic_values(size, size, mode=mode)
    expected = wrapper_route(values, block_pixels=64, parallel=True)
    actual = cylinder_shortwave.kside_cylinder_anisotropic(values, block_pixels=64, parallel=True)
    assert actual is not None
    assert_bitwise(actual, expected, f'{mode}/{size}')
    assert_within_original_budget(actual, serial_reference(values), f'{mode}/{size}/serial-budget')


def test_day_arc_per_timestep_bitwise(admitted_profile):
    """A 24-step solar arc, compared at every timestep like the chronology does."""
    for step in range(24):
        altitude = 62.0 - 5.0 * step
        azimuth = 70.0 + 9.2 * step
        values = synthetic_values(32, 24, mode='baseline', altitude=altitude, azimuth=azimuth, seed=100 + step)
        expected = wrapper_route(values, block_pixels=32, parallel=True)
        actual = cylinder_shortwave.kside_cylinder_anisotropic(values, block_pixels=32, parallel=True)
        assert actual is not None
        assert_bitwise(actual, expected, f'day-arc/step-{step}')
        assert_within_original_budget(actual, serial_reference(values), f'day-arc/step-{step}/serial-budget')


def test_entry_does_not_mutate_bound_values(admitted_profile):
    values = synthetic_values(16, 16)
    snapshot = {name: np.array(value, copy=True) if isinstance(value, np.ndarray) else value
                for name, value in values.items()}
    cylinder_shortwave.kside_cylinder_anisotropic(values, block_pixels=16, parallel=False)
    for name, value in values.items():
        if isinstance(value, np.ndarray):
            assert np.array_equal(value.view(np.uint8), snapshot[name].view(np.uint8)), name
        else:
            assert value == snapshot[name], name
