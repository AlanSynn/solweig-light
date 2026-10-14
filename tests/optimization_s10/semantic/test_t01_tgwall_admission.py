"""T01: singleton-array (U) Tgwall admission into the typed longwave primaries.

Covers the dossier-01 "tests that matter" subset for the admission change:
U32/U64 shapes (1,)/(1,1); multiple wall rows and true fields rejected;
scalar/singleton route agreement; guard and error order preserved; route
counters. Acceptance vs the serial reference uses the frozen comparison_v1
budgets (the standard every shipped compiled kernel is qualified against);
bit-equality is asserted only where the contract is bit-level (fallbacks and
S/U route agreement).
"""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from solweig_light.radiation import engine, patch_radiation

_SPEC = importlib.util.spec_from_file_location(
    'v6_cylinder_lw_conftest',
    Path(__file__).resolve().parents[3] / 'tests/optimization_v6/cylinder_lw/conftest.py')
_V6 = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_V6)
_lcyl_arguments = _V6.lcyl_arguments
_bitwise_equal = _V6.bitwise_equal

LCYL_FIELDS = ('Ldown', 'Lside', 'Least_', 'Lwest_', 'Lnorth_', 'Lsouth_')
# Lcyl_v2022a returns dpc columns (0,1,7,8,9,10).
DPC_FIELD_INDEX = {'Ldown': 0, 'Lside': 1, 'Least': 7, 'Lwest': 8, 'Lnorth': 9, 'Lsouth': 10}

PROTOCOL = json.loads((Path(__file__).resolve().parents[3] /
                       'development/benchmarks/protocols/comparison_v1.json').read_text())


def within_budget(function_field, actual, expected):
    """Frozen comparison_v1 budget for one function/field pair."""
    rule = PROTOCOL['field_rules'][function_field]
    actual, expected = np.asarray(actual), np.asarray(expected)
    for mask in (np.isnan, np.isposinf, np.isneginf):
        np.testing.assert_array_equal(mask(actual), mask(expected))
    np.testing.assert_allclose(actual, expected, atol=rule.get('atol', rule.get('max_abs', 0)),
                               rtol=rule.get('rtol', 0), err_msg=function_field)


def counters():
    return dict(patch_radiation.ROUTE_COUNTS)


def dpc_arguments(rng, tgwall):
    """Engine-order dpc argument bundle with fabricated sky tables."""
    base = _lcyl_arguments(rng, Tgwall=tgwall)
    table = base['sky_patches']
    sky = np.zeros((table.shape[0], 3), dtype=np.float32)
    sky[:, 2] = 420.0
    lnormal = sky.copy()
    lnormal[:, 2] = 0.8
    return (base['solar_altitude'], base['solar_azimuth'],
            table[:, 0].copy(), table[:, 1].copy(), table[:, 2].copy(),
            base['asvf'], base['shmat'], base['vegshmat'], base['vbshvegshmat'],
            sky, sky.copy(), lnormal, base['Lup'], base['Ta'], tgwall,
            base['ewall'], base['rows'], base['cols'])


def check_lcyl_route(arguments, expected_route, budget_fields=True):
    reference = patch_radiation._reference('Lcyl_v2022a')(**arguments)
    before = counters()
    output = patch_radiation.Lcyl_v2022a(**arguments)
    after = counters()
    assert after['Lcyl_v2022a_primary'] - before['Lcyl_v2022a_primary'] == (1 if expected_route == 'primary' else 0)
    assert after['Lcyl_v2022a_reference'] - before['Lcyl_v2022a_reference'] == (1 if expected_route == 'reference' else 0)
    for name, field in zip(LCYL_FIELDS, output):
        if budget_fields:
            within_budget(f'Lcyl_v2022a/{name}', field, reference[LCYL_FIELDS.index(name)])
        else:
            assert np.array_equal(np.asarray(field), np.asarray(reference[LCYL_FIELDS.index(name)]))
    return output, reference


@pytest.mark.parametrize('shape', [(1,), (1, 1)])
@pytest.mark.parametrize('dtype', [np.float32, np.float64])
def test_u_profiles_admitted_within_budget(rng, shape, dtype):
    """U32/U64 singleton arrays take the primary and stay inside frozen budgets."""
    arguments = _lcyl_arguments(rng, Tgwall=np.array(15.0, dtype=dtype).reshape(shape))
    check_lcyl_route(arguments, 'primary')


def test_u_route_bitwise_equals_scalar_route(rng):
    """The U route is the shipped S route: extraction adds no arithmetic."""
    scalar = _lcyl_arguments(rng, Tgwall=np.array(15.0, dtype=np.float64))
    singleton = dict(scalar, Tgwall=scalar['Tgwall'].reshape(1, 1))
    for left, right in zip(patch_radiation.Lcyl_v2022a(**scalar),
                           patch_radiation.Lcyl_v2022a(**singleton)):
        assert _bitwise_equal(left, right)


def test_multiple_wall_rows_rejected(rng):
    """Multiple wall rows stay on the reference route: guard rejects, then the
    reference raises the original broadcast error."""
    arguments = _lcyl_arguments(rng, Tgwall=np.array([[15.0], [16.0]]))
    with pytest.raises(ValueError):
        patch_radiation._reference('Lcyl_v2022a')(**arguments)
    before = counters()
    with pytest.raises(ValueError):
        patch_radiation.Lcyl_v2022a(**arguments)
    after = counters()
    assert after['Lcyl_v2022a_reference'] - before['Lcyl_v2022a_reference'] == 1
    assert after['Lcyl_v2022a_primary'] == before['Lcyl_v2022a_primary']


def test_true_field_rejected(rng):
    """A spatially varying Tgwall field stays on the reference route, bitwise."""
    arguments = _lcyl_arguments(rng, Tgwall=(rng.random((16, 16)) * 4 + 13).astype(np.float64))
    check_lcyl_route(arguments, 'reference', budget_fields=False)


def test_size_two_singleton_rejected(rng):
    """A size-2 array is not U: guard rejects, then the reference raises the
    original broadcast error."""
    arguments = _lcyl_arguments(rng, Tgwall=np.array([15.0, 15.0]))
    with pytest.raises(ValueError):
        patch_radiation._reference('Lcyl_v2022a')(**arguments)
    before = counters()
    with pytest.raises(ValueError):
        patch_radiation.Lcyl_v2022a(**arguments)
    after = counters()
    assert after['Lcyl_v2022a_reference'] - before['Lcyl_v2022a_reference'] == 1
    assert after['Lcyl_v2022a_primary'] == before['Lcyl_v2022a_primary']


def test_nonarray_solar_altitude_raises_original_error(rng):
    """Guard order: scalar altitude still routes to the reference's TypeError."""
    arguments = _lcyl_arguments(rng, Tgwall=np.array([[15.0]]), solar_altitude=35.0)
    with pytest.raises(TypeError):
        patch_radiation._reference('Lcyl_v2022a')(**arguments)
    with pytest.raises(TypeError):
        patch_radiation.Lcyl_v2022a(**arguments)


def test_block_pixels_validation_preserved(rng):
    """block_pixels<1 raises ValueError after admission, position unchanged."""
    arguments = _lcyl_arguments(rng, Tgwall=np.array([[15.0]]))
    with pytest.raises(ValueError, match='block_pixels must be positive'):
        patch_radiation.Lcyl_v2022a(**arguments, block_pixels=0)


@pytest.mark.parametrize('shape', [(1,), (1, 1)])
def test_night_u_profile_admitted(rng, shape):
    """Night (altitude<0) with a U profile also takes the primary, in budget."""
    arguments = _lcyl_arguments(rng, Tgwall=np.array(0.0, dtype=np.float64).reshape(shape),
                                solar_altitude=np.array(-24.7, dtype=np.float64))
    check_lcyl_route(arguments, 'primary')


def test_dpc_u_profile_admitted_within_budget(rng):
    """The dpc entry admits U directly with protocol budgets on its fields."""
    arguments = dpc_arguments(rng, np.array([[12.7]], dtype=np.float64))
    before = counters()
    output = patch_radiation.define_patch_characteristics(*arguments)
    after = counters()
    assert after['define_patch_characteristics_primary'] - before['define_patch_characteristics_primary'] == 1
    reference = patch_radiation._reference('define_patch_characteristics')(*arguments)
    for name, index in DPC_FIELD_INDEX.items():
        within_budget(f'define_patch_characteristics/{name}', output[index], reference[index])


def test_dpc_reference_rank_invariance(rng):
    """Reference outputs are bit-identical for scalar vs (1,1) Tgwall inputs."""
    arguments = list(dpc_arguments(rng, np.float64(12.7)))
    left = patch_radiation._reference('define_patch_characteristics')(*arguments)
    singleton = list(arguments)
    singleton[14] = np.array([[12.7]])
    right = patch_radiation._reference('define_patch_characteristics')(*singleton)
    for a, b in zip(left, right):
        assert np.array_equal(np.asarray(a), np.asarray(b))
