"""S10 semantic-systems test fixtures.

Reuses the C6-21 cylinder-longwave builders (real engine patch table,
engine-profile argument bundle) by loading that conftest module directly; the
S10 acceptance budgets come from the frozen comparison_v1 protocol.
"""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

_SPEC = importlib.util.spec_from_file_location(
    'v6_cylinder_lw_conftest',
    Path(__file__).resolve().parents[2] / 'optimization_v6/cylinder_lw/conftest.py')
_v6 = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_v6)

lcyl_patches = _v6.lcyl_patches
lcyl_arguments = _v6.lcyl_arguments
bitwise_equal = _v6.bitwise_equal

PROTOCOL = json.loads((Path(__file__).resolve().parents[3] /
                       'tests/reference/contracts/comparison_v1.json').read_text())


def within_budget(function_field, actual, expected):
    """Frozen comparison_v1 budget for one function/field pair."""
    rule = PROTOCOL['field_rules'][function_field]
    actual, expected = np.asarray(actual), np.asarray(expected)
    for mask in (np.isnan, np.isposinf, np.isneginf):
        np.testing.assert_array_equal(mask(actual), mask(expected))
    np.testing.assert_allclose(actual, expected, atol=rule.get('atol', rule.get('max_abs', 0)),
                               rtol=rule.get('rtol', 0), err_msg=function_field)


@pytest.fixture
def rng():
    return np.random.default_rng(20261013)
