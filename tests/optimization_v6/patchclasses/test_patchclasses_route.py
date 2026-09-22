"""Route-level differential tests for the exact classification tables.

The oracle is the retained ungated route on the same inputs: the per-patch
scalar coefficient loop (``_class_coefficients`` with the gate off) and the
per-block NumPy tan/atan sequence in ``_classes``. Parity is bitwise; the
engine's ``shaded_or_sunlit`` chain is used as an independent spot oracle.
"""
import importlib.util as _ilu
import os
import sys as _sys
from pathlib import Path as _Path

import numpy as np
import pytest

from solweig_light.radiation import engine as e, patch_radiation as p

# Load THIS family's conftest by file path: bare `import conftest` is
# shadowed by sibling families' conftest modules when several directories
# are collected in one pytest invocation.
_conftest_path = _Path(__file__).resolve().parent / 'conftest.py'
_spec = _ilu.spec_from_file_location('_patchclasses_conftest', str(_conftest_path))
_conftest = _ilu.module_from_spec(_spec)
_sys.modules['_patchclasses_conftest'] = _conftest
_spec.loader.exec_module(_conftest)
GATE_ENV = _conftest.GATE_ENV
asvf_field = _conftest.asvf_field
bitwise = _conftest.bitwise
crafted_vault = _conftest.crafted_vault
real_vault = _conftest.real_vault

SOLAR_STATES = [float, np.float32, np.float64,
                lambda v: np.array(v, np.float32), lambda v: np.array(v, np.float64)]
# The route contract requires a tensor-origin solar altitude (0-d ndarray);
# the azimuth carries the wrapped-scalar promotion variety.
ALTITUDE_STATES = [lambda v: np.array(v, np.float32), lambda v: np.array(v, np.float64)]


def route_pair(altitude, azimuth, geometry, field, start, stop, active=None):
    """Run _classes/_class_coefficients with the gate off, then on."""
    saved = os.environ.pop(GATE_ENV, None)
    try:
        off_coeff = p._class_coefficients(altitude, azimuth, geometry, field, active)
        off = p._classes(altitude, azimuth, geometry, field, start, stop, active=active)
    finally:
        if saved is not None:
            os.environ[GATE_ENV] = saved
    os.environ[GATE_ENV] = '1'
    try:
        on_coeff = p._class_coefficients(altitude, azimuth, geometry, field, active)
        on = p._classes(altitude, azimuth, geometry, field, start, stop, active=active)
    finally:
        os.environ.pop(GATE_ENV, None)
        if saved is not None:
            os.environ[GATE_ENV] = saved
    return (off, off_coeff), (on, on_coeff)


@pytest.mark.parametrize('option', [1, 2, 3])
@pytest.mark.parametrize('asvf_mode', ['realistic', 'adversarial'])
@pytest.mark.parametrize('altitude_state', ALTITUDE_STATES)
@pytest.mark.parametrize('solar_state', SOLAR_STATES)
@pytest.mark.parametrize('active_kind', ['none', 'mask', 'empty'])
def test_route_bitwise_vs_retained_route(rng, option, asvf_mode, altitude_state, solar_state, active_kind):
    vault = real_vault(option)
    geometry = p.patch_geometry(vault)
    field = asvf_field(rng, 8, 8, asvf_mode)
    altitude = altitude_state(35.0)
    azimuth = solar_state(180.0)
    active = {'none': None,
              'mask': rng.random(vault.shape[0]) < 0.7,
              'empty': np.zeros(vault.shape[0], bool)}[active_kind]
    (off, off_coeff), (on, on_coeff) = route_pair(altitude, azimuth, geometry, field, 3, 61, active)
    assert np.array_equal(off_coeff[0], on_coeff[0]), 'indices differ'
    assert bitwise(off_coeff[1], on_coeff[1]), 'coefficient table bits differ'
    assert off_coeff[2].tobytes() == on_coeff[2].tobytes(), 'rad2deg bits differ'
    assert bitwise(off[0], on[0]), 'sun masks differ'
    assert bitwise(off[1], on[1]), 'shade masks differ'


def test_crafted_vault_source_state_classes(rng):
    """Repeated azimuths, signed zeros and NaN stay exact through the dedup."""
    geometry = p.patch_geometry(crafted_vault())
    field = rng.uniform(0.05, 1.5, (16, 16)).astype(np.float32)
    altitude = np.array(35.0, np.float32)
    (off, off_coeff), (on, on_coeff) = route_pair(altitude, 180.0, geometry, field, 0, 256)
    assert bitwise(off_coeff[1], on_coeff[1])
    assert bitwise(off[0], on[0]) and bitwise(off[1], on[1])
    # Patches sharing an azimuth source state share the stored coefficient bits.
    coefficients = on_coeff[1]
    assert bitwise(coefficients[0], coefficients[1]) and bitwise(coefficients[1], coefficients[2])
    assert bitwise(coefficients[3], coefficients[4]) and bitwise(coefficients[4], coefficients[5])
    # The NaN state stays a distinct class: where(yi>0, 0.0, yi) propagates NaN.
    assert np.isnan(coefficients[8])


@pytest.mark.parametrize('blocks', [(0, 1), (0, 7), (5, 6), (0, 63), (17, 64)])
def test_block_slices_bitwise(rng, blocks):
    geometry = p.patch_geometry(real_vault(1))
    field = asvf_field(rng, 8, 8, 'adversarial')
    altitude = np.array(35.0, np.float32)
    start, stop = blocks
    (off, _), (on, _) = route_pair(altitude, 200.0, geometry, field, start, stop)
    assert bitwise(off[0], on[0]) and bitwise(off[1], on[1])


def test_engine_scalar_oracle(rng):
    """Independent oracle: active columns equal shaded_or_sunlit exactly."""
    geometry = p.patch_geometry(crafted_vault())
    field = rng.uniform(0.0, 1.57, (16, 16)).astype(np.float32)
    altitude = np.array(35.0, np.float32)
    (_, _), (on, _) = route_pair(altitude, 200.0, geometry, field, 0, 256)
    for patch in range(geometry.altitude.size):
        sun, shade = e.shaded_or_sunlit(altitude, 200.0, geometry.altitude[patch],
                                        geometry.azimuth[patch], field.reshape(-1, 1))
        assert np.array_equal(on[0][:, patch], sun[:, 0]), patch
        assert np.array_equal(on[1][:, patch], shade[:, 0]), patch


def test_inactive_patches_stay_false_and_kernel_skipped(rng, gate_on, monkeypatch):
    geometry = p.patch_geometry(crafted_vault())
    field = rng.uniform(0.05, 1.5, (8, 8)).astype(np.float32)
    altitude = np.array(35.0, np.float32)
    active = np.zeros(geometry.altitude.size, bool)

    def fail(*args, **kwargs):
        raise AssertionError('compiled classification ran for an empty state set')
    monkeypatch.setattr(p, '_classes_table', fail)
    sun, shade = p._classes(altitude, 180.0, geometry, field, 0, 64, active=active)
    assert not sun.any() and not shade.any()
    prepared = p._class_coefficients(altitude, 180.0, geometry, field, active)
    assert prepared[1].size == 0


def test_type_error_contract(rng, gate_off):
    """A non-tensor solar altitude raises exactly as the retained route's."""
    geometry = p.patch_geometry(crafted_vault())
    field = rng.uniform(0.05, 1.5, (8, 8)).astype(np.float32)
    with pytest.raises(TypeError, match='tensor-origin'):
        p._classes(20.0, 0.0, geometry, field, 0, 64)
    with pytest.raises(TypeError, match='tensor-origin'):
        p._classes(np.float32(20.0), 0.0, geometry, field, 0, 64)


def test_tensor_altitude_runs_gate_on(rng, gate_on):
    """The 0-d ndarray altitude is the admitted tensor-origin form."""
    geometry = p.patch_geometry(crafted_vault())
    field = rng.uniform(0.05, 1.5, (8, 8)).astype(np.float32)
    sun, shade = p._classes(np.array(20.0, np.float32), 0.0, geometry, field, 0, 64)
    assert sun.shape == (64, geometry.altitude.size)


def test_type_error_contract_gate_on(rng, gate_on):
    geometry = p.patch_geometry(crafted_vault())
    field = rng.uniform(0.05, 1.5, (8, 8)).astype(np.float32)
    with pytest.raises(TypeError, match='tensor-origin'):
        p._classes(20.0, 0.0, geometry, field, 0, 64)


def test_empty_active_never_raises_gate_on(rng, gate_on):
    """With no active patches the retained route never raises; gate follows."""
    geometry = p.patch_geometry(crafted_vault())
    field = rng.uniform(0.05, 1.5, (8, 8)).astype(np.float32)
    active = np.zeros(geometry.altitude.size, bool)
    sun, shade = p._classes(20.0, 0.0, geometry, field, 0, 64, active=active)
    assert not sun.any() and not shade.any()


def test_gate_parsing_is_strict():
    saved = os.environ.pop(GATE_ENV, None)
    try:
        for value in (None, '', '0', 'true', 'on', '1 '):
            if value is None:
                os.environ.pop(GATE_ENV, None)
            else:
                os.environ[GATE_ENV] = value
            assert p._classes_exact_enabled() is (value == '1'), repr(value)
    finally:
        if saved is not None:
            os.environ[GATE_ENV] = saved
        else:
            os.environ.pop(GATE_ENV, None)
