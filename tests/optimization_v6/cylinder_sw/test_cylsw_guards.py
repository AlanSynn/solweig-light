"""Guard and fallback-domain tests: the narrow route never changes observable
failure, warning or fallback semantics of the public paths.

Removed box-only work (direction cosines, box gate) can raise or emit
invalid-value warnings for nonfinite solar scalars; every such domain must
fall back to the untouched generic path, which keeps the original behaviour.

Slice nuance recorded here: with t=inf the compiled wrapper's removed
direction work raises/warns while the serial reference's cylinder slice never
reads t and stays silent. The wrapper is the production route whose
behaviour the specialization must preserve, so the wrapper contract is the
asserted oracle; the serial comparison is asserted only where both slices
share the domain.
"""
import inspect
import warnings

import numpy as np
import pytest
from solweig_light.radiation import cylinder_shortwave, engine, patch_radiation

from conftest import (assert_bitwise, assert_within_original_budget, load_packet_values,
                      packet_cases, serial_reference, synthetic_values)

CYLINDER_CASES = [case for case in packet_cases()
                  if np.asarray(load_packet_values(case)['cyl']).reshape(()) in (1, True)]
BASE_CASE = next(case for case in CYLINDER_CASES if 'option1-binary' in case['label'])

# (mutation, wrapper_warns_under_default_errstate, serial_shares_domain)
MUTATIONS = [
    ('azimuth_inf', True, True),
    ('t_inf', True, False),
    ('patch_azimuth_inf', True, True),
    ('azimuth_nan', False, True),
    ('azimuth_string', False, True),
]


def _base_values():
    values = load_packet_values(BASE_CASE)
    values['azimuth'] = float(np.asarray(values['azimuth']).reshape(()))
    values['t'] = float(np.asarray(values['t']).reshape(()))
    return values


def _mutate(values, mutation):
    if mutation == 'azimuth_inf':
        values['azimuth'] = float('inf')
    elif mutation == 'azimuth_nan':
        values['azimuth'] = float('nan')
    elif mutation == 'azimuth_string':
        values['azimuth'] = 'not-a-number'
    elif mutation == 't_inf':
        values['t'] = float('inf')
    elif mutation == 'patch_azimuth_inf':
        values['lv'] = values['lv'].copy()
        values['lv'][0, 1] = np.float32(np.inf)
    return values


def _probe(callable_, values):
    """Return (result, error_class_or_None, warned) under default errstate."""
    error, warned, result = None, False, None
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            result = callable_(values)
        warned = any(issubclass(item.category, RuntimeWarning) for item in caught)
    except Exception as exc:  # noqa: BLE001 - recording the domain's failure class
        error = type(exc)
    return result, error, warned


def test_block_pixels_zero_value_error(admitted_profile):
    values = _base_values()
    with pytest.raises(ValueError, match='block_pixels must be positive'):
        cylinder_shortwave.kside_cylinder_anisotropic(values, block_pixels=0, parallel=False)


def test_block_pixels_zero_value_error_matches_wrapper():
    values = _base_values()
    cylinder_shortwave.set_demand_profile(cylinder_shortwave.FULL_DIAGNOSTICS)
    with pytest.raises(ValueError, match='block_pixels must be positive'):
        patch_radiation.Kside_veg_v2022a(**values, block_pixels=0, parallel=False)


@pytest.mark.parametrize('serial_shares_domain,wrapper_warns,mutation',
                         [(shares, warns, name) for name, warns, shares in MUTATIONS],
                         ids=lambda value: str(value))
def test_removed_work_domains_fall_back(mutation, wrapper_warns, serial_shares_domain, admitted_profile):
    """Every input domain of the removed box-only evaluations declines the
    narrow route; the generic wrapper keeps its exact warning/failure class,
    and the serial reference agrees wherever its slice shares the domain."""
    values = _mutate(_base_values(), mutation)
    # The declining entry may still warm the shared patch-geometry cache; any
    # warning from that cold computation is exactly what the generic wrapper
    # emits at the same call point, so isolate it from the probes below.
    with warnings.catch_warnings(record=True):
        warnings.simplefilter('always')
        assert cylinder_shortwave.kside_cylinder_anisotropic(values, block_pixels=17, parallel=True) is None
    wrapper_result, wrapper_error, wrapper_flagged = _probe(
        lambda args: patch_radiation.Kside_veg_v2022a(**args, block_pixels=17, parallel=False), values)
    serial_result, serial_error, serial_flagged = _probe(serial_reference, values)
    assert wrapper_error == serial_error, (mutation, wrapper_error, serial_error)
    if serial_shares_domain:
        assert wrapper_flagged == serial_flagged, (mutation, wrapper_flagged, serial_flagged)
    assert wrapper_flagged == wrapper_warns, (mutation, wrapper_flagged)
    if wrapper_error is None:
        assert_within_original_budget(wrapper_result, serial_result, f'fallback-result/{mutation}')


@pytest.mark.parametrize('mutation', ['azimuth_inf', 't_inf'])
def test_wrapper_raises_under_seterr_raise(mutation, admitted_profile):
    """With np.seterr(all='raise') the original wrapper raises in the removed
    work's domain; the narrow route declines instead of skipping silently."""
    values = _mutate(_base_values(), mutation)
    assert cylinder_shortwave.kside_cylinder_anisotropic(values, block_pixels=17, parallel=True) is None
    with pytest.raises(FloatingPointError):
        with np.errstate(all='raise'):
            patch_radiation.Kside_veg_v2022a(**values, block_pixels=17, parallel=False)


def test_azimuth_inf_serial_raises_under_seterr_raise(admitted_profile):
    values = _mutate(_base_values(), 'azimuth_inf')
    with pytest.raises(FloatingPointError):
        with np.errstate(all='raise'):
            serial_reference(values)


def test_nonfloat32_profile_falls_back_exact(admitted_profile):
    """A non-admitted dtype profile declines the narrow route; the wrapper
    then delegates to the serial reference itself, so results are bitwise."""
    values = _base_values()
    values['shmat'] = values['shmat'].astype(np.float64)
    assert cylinder_shortwave.kside_cylinder_anisotropic(values, block_pixels=17, parallel=True) is None
    with np.errstate(all='ignore'):
        wrapper = patch_radiation.Kside_veg_v2022a(**values, block_pixels=17, parallel=False)
    expected = serial_reference(values)
    assert_bitwise(wrapper, expected, 'float64-fallback')


@pytest.mark.parametrize('case', CYLINDER_CASES, ids=lambda case: case['label'])
@pytest.mark.parametrize('profile', [cylinder_shortwave.FULL_DIAGNOSTICS, cylinder_shortwave.PIPELINE_CYLINDER_ANISOTROPIC])
def test_public_wrapper_full_route_untouched(case, profile):
    """Completion gate 3: the untouched public wrapper stays within the
    original upstream budget against the serial reference on all seven
    outputs under either demand profile (the generic route is not modified
    by this task; its serial delta is the pre-existing transcendental
    profile, not a specialization effect)."""
    cylinder_shortwave.set_demand_profile(profile)
    try:
        values = load_packet_values(case)
        expected = serial_reference(values)
        with np.errstate(all='ignore'):
            wrapper = patch_radiation.Kside_veg_v2022a(**values, block_pixels=17, parallel=False)
        assert_within_original_budget(wrapper, expected, f"public-full/{case['label']}/{profile}")
    finally:
        cylinder_shortwave.set_demand_profile(cylinder_shortwave.FULL_DIAGNOSTICS)
