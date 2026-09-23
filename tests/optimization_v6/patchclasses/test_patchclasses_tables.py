"""Exactness tests for the per-state coefficient table and gate inertness.

The construction oracle recomputes each patch's scalar chain externally from
the engine operations (the retained loop's statements), so the gated table is
checked against the chain itself, not only against the ungated route.
"""
import importlib.util as _ilu
import sys as _sys
from pathlib import Path as _Path

import numpy as np
import pytest

from solweig_light.radiation import engine as e, patch_radiation as p

_conftest_path = _Path(__file__).resolve().parent / 'conftest.py'
_spec = _ilu.spec_from_file_location('_patchclasses_conftest', str(_conftest_path))
_conftest = _ilu.module_from_spec(_spec)
_sys.modules['_patchclasses_conftest'] = _conftest
_spec.loader.exec_module(_conftest)
GATE_ENV = _conftest.GATE_ENV
bitwise = _conftest.bitwise
crafted_vault = _conftest.crafted_vault
real_vault = _conftest.real_vault


def external_chain(azimuth, altitude, patch_azimuth):
    """The retained per-patch coefficient chain, restated from the engine."""
    difference = np.abs(e._operate(np.subtract, azimuth, patch_azimuth))
    deg2rad = e._divide(np.pi, 180.0)
    xi = np.cos(e._operate(np.multiply, difference, deg2rad))
    if not isinstance(altitude, np.ndarray):
        raise TypeError('tan(): solar_altitude must be a tensor-origin array')
    yi = e._operate(np.multiply, e._operate(np.multiply, 2, xi),
                    np.tan(e._operate(np.multiply, altitude, deg2rad)))
    return np.where(yi > 0, 0.0, yi)


def external_table(azimuth, altitude, geometry, active=None):
    indices = np.flatnonzero(np.ones(geometry.altitude.size, dtype=bool) if active is None else active)
    coefficients = np.empty(indices.size, np.float32)
    for column, patch in enumerate(indices):
        coefficients[column] = external_chain(azimuth, altitude, geometry.azimuth[patch])
    return indices, coefficients


@pytest.mark.parametrize('option', [1, 2, 3])
@pytest.mark.parametrize('altitude_state', [lambda v: np.array(v, np.float32),
                                            lambda v: np.array(v, np.float64)])
@pytest.mark.parametrize('azimuth_state', [float, np.float32, np.float64,
                                           lambda v: np.array(v, np.float32),
                                           lambda v: np.array(v, np.float64)])
def test_table_matches_external_chain(option, altitude_state, azimuth_state, rng, gate_on):
    geometry = p.patch_geometry(real_vault(option))
    field = rng.uniform(0.05, 1.5, (4, 4)).astype(np.float32)
    active = rng.random(geometry.altitude.size) < 0.6
    altitude, azimuth = altitude_state(41.25), azimuth_state(213.7)
    indices, expected = external_table(azimuth, altitude, geometry, active)
    prepared = p._class_coefficients(altitude, azimuth, geometry, field, active)
    assert np.array_equal(prepared[0], indices)
    assert bitwise(prepared[1], expected), 'gated table deviates from the chain'


@pytest.mark.parametrize('state', [
    dict(altitude=np.array(np.nan, np.float32)),
    dict(altitude=np.array(np.inf, np.float32)),
    dict(altitude=np.array(-10.0, np.float32)),
    dict(altitude=np.array(np.nan, np.float64)),
])
def test_table_nonfinite_solar_states(state, rng, gate_on):
    """NaN/inf/negative solar altitude keep the retained where() semantics."""
    geometry = p.patch_geometry(crafted_vault())
    field = rng.uniform(0.05, 1.5, (4, 4)).astype(np.float32)
    altitude = state['altitude']
    indices, expected = external_table(180.0, altitude, geometry)
    prepared = p._class_coefficients(altitude, 180.0, geometry, field)
    assert bitwise(prepared[1], expected)


def test_table_single_state_vault_deduplicates(rng, gate_on):
    """One unique azimuth state: every member shares the same stored bits."""
    table = np.column_stack((np.arange(9, dtype=np.float32) * 9.0,
                             np.full(9, 123.0, np.float32),
                             np.zeros(9, np.float32)))
    geometry = p.patch_geometry(table)
    field = rng.uniform(0.05, 1.5, (4, 4)).astype(np.float32)
    altitude = np.array(35.0, np.float32)
    prepared = p._class_coefficients(altitude, 180.0, geometry, field)
    assert bitwise(prepared[1], np.full(9, prepared[1][0], np.float32))
    indices, expected = external_table(180.0, altitude, geometry)
    assert bitwise(prepared[1], expected)


def test_gate_off_route_is_inert(rng, gate_off, monkeypatch):
    """With the gate off the compiled kernel never runs and nothing changes."""
    geometry = p.patch_geometry(crafted_vault())
    field = rng.uniform(0.05, 1.5, (16, 16)).astype(np.float32)
    altitude = np.array(35.0, np.float32)

    def fail(*args, **kwargs):
        raise AssertionError('compiled classification ran with the gate off')
    monkeypatch.setattr(p, '_classes_table', fail)
    assert not p._classes_exact_enabled()
    prepared = p._class_coefficients(altitude, 180.0, geometry, field)
    indices, expected = external_table(180.0, altitude, geometry)
    assert np.array_equal(prepared[0], indices)
    assert bitwise(prepared[1], expected)
    sun, shade = p._classes(altitude, 180.0, geometry, field, 0, 256, prepared=prepared)
    reference = p._classes(altitude, 180.0, geometry, field, 0, 256)
    assert np.array_equal(sun, reference[0]) and np.array_equal(shade, reference[1])


def test_gate_off_ignores_stray_env_shapes(rng, gate_off):
    """Only the exact '1' value arms the route; others keep the loop path."""
    import os
    for value in ('1 ', '1x', 'TRUE'):
        os.environ[GATE_ENV] = value
        try:
            assert not p._classes_exact_enabled()
        finally:
            os.environ.pop(GATE_ENV, None)
