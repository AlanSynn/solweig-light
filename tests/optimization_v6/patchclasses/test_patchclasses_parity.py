"""Wrapper-level parity: the exact-table route against the retained route.

Both sides run the full public wrappers with the same bound arguments; the
gate is the only difference. Parity is bitwise over every exported field, so
the gate binds to the retained wrapper route as the selection requires.
"""
import importlib.util as _ilu
import os
import sys as _sys
from pathlib import Path as _Path

import numpy as np
import pytest

from solweig_light.radiation import patch_radiation as p

_conftest_path = _Path(__file__).resolve().parent / 'conftest.py'
_spec = _ilu.spec_from_file_location('_patchclasses_conftest', str(_conftest_path))
_conftest = _ilu.module_from_spec(_spec)
_sys.modules['_patchclasses_conftest'] = _conftest
_spec.loader.exec_module(_conftest)
GATE_ENV = _conftest.GATE_ENV
assert_fields_bitwise = _conftest.assert_fields_bitwise
crafted_vault = _conftest.crafted_vault
kside_values = _conftest.kside_values
lcyl_arguments = _conftest.lcyl_arguments
real_vault = _conftest.real_vault

FIELD_NAMES = _conftest.FIELD_NAMES
# Lcyl_v2022a exports define_patch_characteristics rows (0,1,7,8,9,10);
# the cylinder_lw family compares these positionally, so the labels stay positional.
LONGWAVE_NAMES = ('out0', 'out1', 'out7', 'out8', 'out9', 'out10')


def _clone(values):
    return {name: np.array(value, copy=True) if isinstance(value, np.ndarray) else value
            for name, value in values.items()}


def kside_pair(values, block_pixels=64):
    saved = os.environ.pop(GATE_ENV, None)
    try:
        expected = p.Kside_veg_v2022a(**_clone(values), block_pixels=block_pixels)
    finally:
        if saved is not None:
            os.environ[GATE_ENV] = saved
    os.environ[GATE_ENV] = '1'
    try:
        actual = p.Kside_veg_v2022a(**_clone(values), block_pixels=block_pixels)
    finally:
        os.environ.pop(GATE_ENV, None)
        if saved is not None:
            os.environ[GATE_ENV] = saved
    return actual, expected


def lcyl_pair(values, block_pixels=64):
    saved = os.environ.pop(GATE_ENV, None)
    try:
        expected = p.Lcyl_v2022a(**_clone(values), block_pixels=block_pixels)
    finally:
        if saved is not None:
            os.environ[GATE_ENV] = saved
    os.environ[GATE_ENV] = '1'
    try:
        actual = p.Lcyl_v2022a(**_clone(values), block_pixels=block_pixels)
    finally:
        os.environ.pop(GATE_ENV, None)
        if saved is not None:
            os.environ[GATE_ENV] = saved
    return actual, expected


@pytest.mark.parametrize('altitude,azimuth', [(35.0, 180.0), (89.5, 359.9)])
@pytest.mark.parametrize('box', [False, True])
def test_kside_bitwise_vs_retained_route(rng, box, altitude, azimuth):
    """box=False drives the Kside body; box=True admits it via tensor t."""
    values = kside_values(rng, rows=64, cols=64, cyl=2.0 if box else 1.0,
                          altitude=altitude, azimuth=azimuth,
                          t=np.array(0.0, np.float32) if box else 0.0)
    actual, expected = kside_pair(values)
    assert_fields_bitwise(actual, expected, FIELD_NAMES,
                          f'kside/box={box}/{altitude}/{azimuth}')


@pytest.mark.parametrize('step', range(4))
def test_kside_day_arc_bitwise(rng, step):
    altitude = 62.0 - 5.0 * step
    azimuth = 70.0 + 9.2 * step
    values = kside_values(rng, rows=32, cols=32, vault=real_vault(1), cyl=1.0,
                          altitude=altitude, azimuth=azimuth, seed=100 + step)
    actual, expected = kside_pair(values, block_pixels=32)
    assert_fields_bitwise(actual, expected, FIELD_NAMES, f'day-arc/step-{step}')


@pytest.mark.parametrize('esky', [0.85, 0.95])
def test_lcyl_bitwise_vs_retained_route(rng, esky):
    values = lcyl_arguments(rng, rows=16, cols=16, vault=real_vault(2), esky=esky)
    actual, expected = lcyl_pair(values)
    assert_fields_bitwise(actual, expected, LONGWAVE_NAMES, f'lcyl/esky={esky}')


def test_lcyl_crafted_vault_and_night_bitwise(rng):
    """Degenerate vault plus a night step with an empty solar-gate state set."""
    values = lcyl_arguments(rng, rows=16, cols=16, vault=crafted_vault())
    actual, expected = lcyl_pair(values)
    assert_fields_bitwise(actual, expected, LONGWAVE_NAMES, 'lcyl/crafted')
    night = lcyl_arguments(rng, rows=16, cols=16, vault=real_vault(1),
                           solar_altitude=-10.0)
    actual, expected = lcyl_pair(night)
    assert_fields_bitwise(actual, expected, LONGWAVE_NAMES, 'lcyl/night')


def test_wrappers_do_not_mutate_bound_values(rng, gate_on):
    """The gated route stays read-only over its boundary bundle."""
    values = kside_values(rng, rows=16, cols=16)
    snapshot = {name: np.array(value, copy=True) if isinstance(value, np.ndarray) else value
                for name, value in values.items()}
    p.Kside_veg_v2022a(**values, block_pixels=16, parallel=False)
    for name, value in values.items():
        if isinstance(value, np.ndarray):
            assert np.array_equal(value.view(np.uint8), snapshot[name].view(np.uint8)), name
        else:
            assert value == snapshot[name], name
