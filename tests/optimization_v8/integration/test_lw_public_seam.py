#SOLWEIG-GPU: GPU-accelerated SOLWEIG model for urban thermal comfort simulation
#Copyright (C) 2022–2025 Harsh Kamath and Naveen Sudharsan

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
"""N9 integration: the PUBLIC wrapper seam and the structural LW route.

The public pipeline call site (engine.Solweig_2022a_calc, the cylinder-
longwave call the pipeline drives under PIPELINE_CYLINDERS_ANISOTROPIC
demand) keeps the N8-40b TRI-STATE load-bearing (N9 F4): H>1 is an
explicit parallel demand (``parallel=True``); H<=1 is no explicit
demand (``parallel=None``), so the single
``cylinder_longwave._lw_region_route`` consult fires at the shipped
default and an admitted invocation takes the bounded Numba stream at
its pinned budget 1 (zero background pool threads; the leaf's prange
owns numba's threads). Driver-level ``parallel=False`` remains the only
serial demand and never dispatches. There is no registry consult
anywhere in the path (F4 removed the selector).

Every routed result is compared BITWISE (uint32 views -- NaN/signed-zero
exact) against the same public call with ``_lw_region_route`` forced to
None over IDENTICAL inputs loaded fresh from the small reference scene
(day event: solar altitude > 0).

Skip labels (never fake-pass): none -- the stream is a python module.
"""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

from solweig_light.radiation import cylinder_longwave as cyl
from solweig_light.radiation import engine
from solweig_light.runtime import runtime_options

# The v6 cylinder family's conftest, loaded by file path under a UNIQUE
# module name: a bare `import conftest` is shadowed by sibling suites in
# one pytest session (and the driver args are only needed for the
# driver-level tri-state test below).
_V6_CONFTEST = (Path(__file__).resolve().parents[2] / 'optimization_v6'
                / 'cylinder_lw' / 'conftest.py')
_spec = importlib.util.spec_from_file_location('_n840b_v6_conftest',
                                               str(_V6_CONFTEST))
_v6 = importlib.util.module_from_spec(_spec)
sys.modules['_n840b_v6_conftest'] = _v6
_spec.loader.exec_module(_v6)
lcyl_arguments = _v6.lcyl_arguments
packed = _v6.packed

# The first DAY input event of the small reference scene: the cylinder
# longwave site only runs on the day branch (solar altitude > 0).
_BOUNDARIES = (Path(__file__).resolve().parents[2]
               / 'reference' / 'small_original_cpu' / 'boundaries')
_DAY_EVENT_TIMESTEP = 7

_ROWS, _COLS, _PATCHES = 37, 53, 153  # driver-level test geometry


class _SeamStop(Exception):
    """Abort the public calc exactly at the seam, after capture."""


@pytest.fixture(autouse=True)
def _seam_shipped_env(monkeypatch):
    """Every test starts from the shipped no-env state; any pools a
    previous test created are torn down."""
    monkeypatch.delenv('SOLWEIG_LIGHT_LW_BACKEND', raising=False)
    yield
    import solweig_light._native_dispatch.region.region_pool as rp
    rp.reset_pools_for_tests()


@pytest.fixture()
def region_spy(monkeypatch):
    """Record every execute_regions call, then run the real executor."""
    import solweig_light._native_dispatch.region.region_pool as rp
    calls = []
    real = rp.execute_regions

    def spy(plan, consumer, output, **kwargs):
        report = real(plan, consumer, output, **kwargs)
        calls.append((plan, consumer, output, report))
        return report

    monkeypatch.setattr(rp, 'execute_regions', spy)
    return calls


# ---------------------------------------------------------------------------
# Helpers (uniquely named; no bare conftest imports)
# ---------------------------------------------------------------------------

def _seam_load_inputs(timestep=_DAY_EVENT_TIMESTEP):
    """Fresh public-calc inputs from the small reference scene, packed
    exactly as the pipeline profile (compact visibility)."""
    manifest = json.loads((_BOUNDARIES / 'manifest.json').read_text())
    event = next(item for item in manifest['events']
                 if item['boundary'] == 'input' and item['timestep'] == timestep)
    with np.load(_BOUNDARIES / event['path']) as archive:
        values = {}
        for name, spec in event['fields'].items():
            if '/' in name:
                continue
            kind = spec['kind']
            if kind == 'dict':
                values[name] = {key: archive[name + '/' + key].item()
                                for key in spec['keys']}
            elif kind == 'list':
                assert spec['length'] == 0
                values[name] = []
            elif kind == 'none':
                values[name] = None
            else:
                value = archive[name].copy()
                if name in {'altitude', 'azimuth', 'zen', 'dectime', 'altmax'}:
                    values[name] = value[()]
                elif kind == 'array' or value.dtype == np.float32 or name in {
                        'jday', 'Ta', 'RH', 'radG', 'radD', 'radI', 'P',
                        'amaxvalue'}:
                    values[name] = value
                else:
                    values[name] = value.item()
        from solweig_light.geometry.visibility import (LazyDiffVisibility,
                                                       PackedVisibility)
        for name in ('shmat', 'vegshmat', 'vbshvegshmat'):
            values[name] = PackedVisibility.from_dense(values[name])
        values['diffsh'] = LazyDiffVisibility(values['shmat'],
                                              values['vegshmat'])
    return values


def _seam_public_calc(timestep=_DAY_EVENT_TIMESTEP):
    """Run the public calc exactly as the pipeline drives it (private
    PIPELINE demand profile); return the seam's two primary fields."""
    with cyl.demand_scope(cyl.CylinderLongwaveDemand.PIPELINE_CYLINDERS_ANISOTROPIC):
        with np.errstate(all='ignore'):
            result = engine.Solweig_2022a_calc(**_seam_load_inputs(timestep))
    return result[3], result[32]  # Ldown, Lside


def _seam_bitwise(first, second):
    return np.array_equal(first.view(np.uint32), second.view(np.uint32))


def _seam_count_kernels(monkeypatch):
    """Wrap the four cylinder-longwave njit kernels with recording
    delegators; returns {name: call_count}."""
    counts = {name: 0 for name in ('_longwave_primary',
                                   '_longwave_primary_serial',
                                   '_longwave_fused_primary',
                                   '_longwave_fused_primary_serial')}
    for name in counts:
        real = getattr(cyl, name)

        def wrapper(*args, _real=real, _name=name, **kwargs):
            counts[_name] += 1
            return _real(*args, **kwargs)

        monkeypatch.setattr(cyl, name, wrapper)
    return counts


def _seam_count_route_consults(monkeypatch):
    """Wrap ``_lw_region_route`` with a recording delegator (real
    decision preserved); returns the call list."""
    consults = []
    real = cyl._lw_region_route

    def counting(*args, **kwargs):
        consults.append(real(*args, **kwargs))
        return consults[-1]

    monkeypatch.setattr(cyl, '_lw_region_route', counting)
    return consults


def _seam_force_route_none(monkeypatch):
    monkeypatch.setattr(cyl, '_lw_region_route', lambda *a, **k: None)


# ---------------------------------------------------------------------------
# (a) the engine call site keeps the tri-state load-bearing
# ---------------------------------------------------------------------------

def test_public_wrapper_h_value_follows_the_tri_state(monkeypatch):
    """The seam: the public wrapper passes ``parallel=True`` at H>1 and
    ``parallel=None`` at H<=1 (no explicit demand -- the route consult
    stays reachable at the shipped default) -- captured at the exact
    call site, the calc aborted there."""
    captured = []

    def spy(*args, **kwargs):
        captured.append(kwargs.get('parallel', 'MISSING'))
        raise _SeamStop

    monkeypatch.setattr(cyl, 'Lcyl_v2022a_by_demand', spy)
    for threads, expected in ((1, None), (2, True)):
        captured.clear()
        with pytest.raises(_SeamStop):
            with runtime_options(cpu_budget=threads,
                                 threads_per_worker=threads):
                _seam_public_calc()
        assert captured == [expected], threads


# ---------------------------------------------------------------------------
# (b) shipped state, public H=1 call: no explicit demand, stream runs
# ---------------------------------------------------------------------------

def test_h1_public_call_routes_the_stream_at_pinned_budget_1(monkeypatch,
                                                             region_spy):
    """H=1 sends parallel=None (no explicit demand): exactly one route
    consult, the admitted scene takes the bounded stream at budget 1
    (zero background pool threads), no njit kernel family of the legacy
    loop is ever entered, and Ldown/Lside are bitwise-identical to the
    same call with the route forced to None (= the serial legacy
    kernels)."""
    consults = _seam_count_route_consults(monkeypatch)
    counts = _seam_count_kernels(monkeypatch)
    with runtime_options(threads_per_worker=1):
        routed = _seam_public_calc()
    assert len(consults) == 1, 'exactly one route consult per public LW call'
    assert len(region_spy) == 1
    plan, consumer, output, report = region_spy[0]
    assert consumer.mode.value == 'self_parallel'
    assert report.pool_workers == 0
    assert report.blocks == plan.total_blocks
    assert all(count == 0 for count in counts.values())

    _seam_force_route_none(monkeypatch)
    with runtime_options(threads_per_worker=1):
        legacy = _seam_public_calc()

    assert _seam_bitwise(routed[0], legacy[0]) and _seam_bitwise(routed[1], legacy[1])
    assert (counts['_longwave_primary_serial']
            + counts['_longwave_fused_primary_serial']) >= 1


# ---------------------------------------------------------------------------
# (c) shipped state, public H=2 call: explicit parallel demand, stream too
# ---------------------------------------------------------------------------

def test_h2_public_call_routes_the_stream_bitwise(monkeypatch, region_spy):
    """H=2 keeps the explicit parallel demand: the route consult fires,
    the real scene's channels are admitted (mixed binary storage), the
    bounded Numba stream executes, and Ldown/Lside are bitwise-identical
    to the same call with the route forced to None (= the parallel
    legacy kernels)."""
    consults = _seam_count_route_consults(monkeypatch)
    counts = _seam_count_kernels(monkeypatch)
    with runtime_options(cpu_budget=2, threads_per_worker=2):
        routed = _seam_public_calc()

    assert len(consults) == 1, 'exactly one route consult per public LW call'
    assert len(region_spy) == 1
    plan, consumer, output, report = region_spy[0]
    assert consumer.mode.value == 'self_parallel'
    assert report.blocks == plan.total_blocks
    assert all(count == 0 for count in counts.values())

    _seam_force_route_none(monkeypatch)
    with runtime_options(cpu_budget=2, threads_per_worker=2):
        legacy = _seam_public_calc()

    assert _seam_bitwise(routed[0], legacy[0]) and _seam_bitwise(routed[1], legacy[1])
    assert (counts['_longwave_primary']
            + counts['_longwave_fused_primary']) >= 1
    assert counts['_longwave_primary_serial'] == 0
    assert counts['_longwave_fused_primary_serial'] == 0


# ---------------------------------------------------------------------------
# (d) driver-level tri-state: serial demand never dispatches; the
#     no-demand value consults and dispatches
# ---------------------------------------------------------------------------

@pytest.fixture()
def driver_args(rng):
    """Driver arguments over adversarial packed channels (37x53, tail
    block + tail gang coverage)."""
    gen = np.random.default_rng(20260922)
    return lcyl_arguments(rng, rows=_ROWS, cols=_COLS,
                          shmat=packed(gen, _ROWS, _COLS, _PATCHES,
                                       ('binary', 'ternary', 'raw')),
                          vegshmat=packed(gen, _ROWS, _COLS, _PATCHES,
                                          ('ternary', 'raw', 'binary')),
                          vbshvegshmat=packed(gen, _ROWS, _COLS, _PATCHES,
                                              ('raw', 'binary', 'ternary')))


@pytest.fixture()
def rng():
    return np.random.default_rng(20260922)


def test_driver_serial_demand_never_consults_and_none_dispatches(
        monkeypatch, region_spy, driver_args):
    """The driver-level tri-state holds with NO registry behind it:
    parallel=False consults nothing and never dispatches, while
    parallel=None (the no-explicit-demand value) consults once and takes
    the stream. False alone is the serial demand."""
    consults = _seam_count_route_consults(monkeypatch)

    serial = cyl.Lcyl_v2022a_primary(**driver_args, parallel=False)
    assert consults == []
    assert region_spy == []

    routed = cyl.Lcyl_v2022a_primary(**driver_args, parallel=None)
    assert len(consults) == 1
    assert len(region_spy) == 1
    assert all(np.array_equal(a.view(np.uint32), b.view(np.uint32))
               for a, b in zip(serial[:2], routed[:2]))
