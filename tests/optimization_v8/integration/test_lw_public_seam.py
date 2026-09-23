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
"""N8-40b integration: the PUBLIC wrapper seam reaches the LW route at H=1.

The public pipeline call site (engine.Solweig_2022a_calc, the cylinder-
longwave call the pipeline drives under PIPELINE_CYLINDERS_ANISOTROPIC
demand) passes ``parallel=None`` at threads_per_worker<=1 -- no explicit
demand, not a serial demand -- so the single
``cylinder_longwave._lw_region_route`` consult is reachable at the shipped
default. Driver-level ``parallel=False`` remains the only serial demand.

Every routed result is compared BITWISE (uint32 views -- NaN/signed-zero
exact) against the same public call with ``_lw_region_route`` forced to
None (= today's shipped behavior) over IDENTICAL inputs loaded fresh from
the small reference scene (day event: solar altitude > 0).

Skip labels (never fake-pass): none -- row B is a python-module row and
needs no staged native artifact.
"""
import hashlib
import importlib.util
import json
import shutil
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

# N8-41 vendoring: policy module ships in the package; the fabricated
# evidence builders are imported under their UNIQUE module name (never as
# ``conftest``).
_HELPERS = Path(__file__).resolve().parent.parent / 'policy'
if str(_HELPERS) not in sys.path:
    sys.path.insert(0, str(_HELPERS))
from solweig_light._native_dispatch import lw_default_policy as policy  # noqa: E402
from policy_test_helpers import COMMIT, make_promotion_record, write_json  # noqa: E402

_REPO = Path(__file__).resolve().parents[3]

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
    """Every test starts from the shipped no-env state; policy state and
    any pools a previous test created are torn down."""
    monkeypatch.delenv('SOLWEIG_LIGHT_LW_BACKEND', raising=False)
    policy.reset_for_tests()
    yield
    import solweig_light._native_dispatch.region.region_pool as rp
    rp.reset_pools_for_tests()
    policy.reset_for_tests()


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


def _seam_count_consults(monkeypatch):
    """Wrap the policy selector with a recording delegator (real decision
    preserved); returns the call list."""
    consults = []
    real = policy.resolve_lw_backend

    def counting(*args, **kwargs):
        consults.append(1)
        return real(*args, **kwargs)

    monkeypatch.setattr(policy, 'resolve_lw_backend', counting)
    return consults


def _seam_force_route_none(monkeypatch):
    monkeypatch.setattr(cyl, '_lw_region_route', lambda *a, **k: None)


def _seam_write_evidence(tmp_path):
    """Fabricated promotion + review tree; returns a row_record builder."""
    promotion_path, promotion_sha = write_json(
        tmp_path / 'evidence' / 'promotion.json', make_promotion_record())
    review_path, review_sha = write_json(
        tmp_path / 'evidence' / 'review.json',
        {'schema': 'sw8-lw-review-v1', 'task': 'N8-40b-public-seam',
         'verdict': 'APPROVE-WITH-NOTES'})

    def row_record(**overrides):
        record = {
            'schema': policy.ROW_RECORD_SCHEMA,
            'status': 'qualified',
            'row': 'C',
            'host_class': policy.current_host_class(),
            'created_utc': '2026-09-22T00:00:00Z',
            'source_commit': COMMIT,
            'artifact_identity': {
                'kind': 'installed-native-generation',
                'generation': 'gen-fabricated',
                'kernel_sha256': '2' * 64,
                'dylib_sha256': '3' * 64,
            },
            'promotion_record': {
                'path': 'evidence/promotion.json',
                'sha256': promotion_sha,
                'schema': policy.PROMOTION_RECORD_SCHEMA,
            },
            'cells': ['primary-0', 'primary-2'],
            'independent_review': {
                'path': 'evidence/review.json',
                'sha256': review_sha,
            },
        }
        record.update(overrides)
        return record

    return row_record


def _seam_inject_registry(monkeypatch, tmp_path, records):
    """Point the policy module's call-time globals at the tmp evidence
    (packet ``tools/`` mirrored for ``_assess_promotion``)."""
    path = tmp_path / 'registry.json'
    path.write_text(json.dumps(
        {'schema': policy.REGISTRY_SCHEMA, 'records': list(records)}))
    tools = _REPO / 'optimization_v8_native_default' / 'tools'
    mirrored = tmp_path / 'optimization_v8_native_default' / 'tools'
    if tools.is_dir() and not mirrored.is_dir():
        shutil.copytree(tools, mirrored)
    monkeypatch.setattr(policy, 'DEFAULT_REGISTRY_PATH', path)
    monkeypatch.setattr(policy, 'REPO_ROOT', tmp_path)


def _seam_row_b_record(tmp_path):
    """A qualified row B backed by the real lw_b_control module hash."""
    row_record = _seam_write_evidence(tmp_path)
    module_rel = 'src/solweig_light/_native_dispatch/lw_b_control.py'
    real = _REPO / module_rel
    module_copy = tmp_path / module_rel
    module_copy.parent.mkdir(parents=True)
    module_copy.write_bytes(real.read_bytes())
    return row_record(row='B', artifact_identity={
        'kind': 'python-module', 'module_path': module_rel,
        'module_sha256': hashlib.sha256(real.read_bytes()).hexdigest()})


# ---------------------------------------------------------------------------
# (a) shipped state, public H=1 call
# ---------------------------------------------------------------------------

def test_public_wrapper_h_value_is_no_serial_demand_at_h1(monkeypatch):
    """The seam: the public wrapper passes parallel=None at H=1 (no
    explicit demand) and parallel=True at H=2 -- captured at the exact
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


def test_shipped_h1_public_call_consults_once_and_stays_serial(monkeypatch,
                                                               region_spy):
    """Shipped empty registry, public H=1 call under the pipeline demand:
    exactly ONE selector consult, the region machinery untouched, only the
    serial legacy kernels run, and Ldown/Lside are bitwise-identical to
    the same call with the route forced to None (= today)."""
    consults = _seam_count_consults(monkeypatch)
    counts = _seam_count_kernels(monkeypatch)
    with runtime_options(threads_per_worker=1):
        routed = _seam_public_calc()
    assert len(consults) == 1, 'exactly one selector read per public LW call'
    assert policy.policy_reasons(), 'selector must have run'
    assert any('[absent]' in reason for reason in policy.policy_reasons())

    _seam_force_route_none(monkeypatch)
    with runtime_options(threads_per_worker=1):
        legacy = _seam_public_calc()

    assert _seam_bitwise(routed[0], legacy[0]) and _seam_bitwise(routed[1], legacy[1])
    assert region_spy == []
    assert counts['_longwave_primary'] == 0
    assert counts['_longwave_fused_primary'] == 0
    assert (counts['_longwave_primary_serial']
            + counts['_longwave_fused_primary_serial']) >= 1


# ---------------------------------------------------------------------------
# (b) shipped state, public H=2 call: identical to today
# ---------------------------------------------------------------------------

def test_shipped_h2_public_call_identical_to_today(monkeypatch, region_spy):
    """H=2 keeps the explicit parallel demand: one consult (as N8-40
    shipped), parallel legacy kernels, region machinery untouched,
    Ldown/Lside bitwise vs the route-forced-None run."""
    consults = _seam_count_consults(monkeypatch)
    counts = _seam_count_kernels(monkeypatch)
    with runtime_options(cpu_budget=2, threads_per_worker=2):
        routed = _seam_public_calc()

    _seam_force_route_none(monkeypatch)
    with runtime_options(cpu_budget=2, threads_per_worker=2):
        legacy = _seam_public_calc()

    assert _seam_bitwise(routed[0], legacy[0]) and _seam_bitwise(routed[1], legacy[1])
    assert len(consults) == 1  # only the routed (first) run consults
    assert region_spy == []
    assert counts['_longwave_primary_serial'] == 0
    assert counts['_longwave_fused_primary_serial'] == 0
    assert (counts['_longwave_primary']
            + counts['_longwave_fused_primary']) >= 1


# ---------------------------------------------------------------------------
# (c) injected qualified row, public H=1 call: region dispatch fires
# ---------------------------------------------------------------------------

def test_qualified_row_h1_public_call_dispatches_region(monkeypatch, tmp_path,
                                                        region_spy):
    """A qualified row at H=1 through the PUBLIC wrapper dispatches the
    region path (its own bounded threading) and stays bitwise-faithful to
    the legacy run; the numba kernel families are never entered."""
    _seam_inject_registry(monkeypatch, tmp_path, [_seam_row_b_record(tmp_path)])
    counts = _seam_count_kernels(monkeypatch)
    with runtime_options(threads_per_worker=1):
        routed = _seam_public_calc()
    assert len(region_spy) == 1
    plan, consumer, output, report = region_spy[0]
    assert consumer.mode.value == 'self_parallel'
    assert report.blocks == plan.total_blocks
    assert all(count == 0 for count in counts.values())
    assert policy.resolve_lw_backend().row == 'B'

    _seam_force_route_none(monkeypatch)
    with runtime_options(threads_per_worker=1):
        legacy = _seam_public_calc()
    assert _seam_bitwise(routed[0], legacy[0]) and _seam_bitwise(routed[1], legacy[1])


# ---------------------------------------------------------------------------
# (d) driver-level explicit serial demand: still never dispatches
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


def test_driver_explicit_serial_demand_never_dispatches_qualified(
        monkeypatch, tmp_path, region_spy, driver_args):
    """Under an INJECTED qualified row the driver-level tri-state holds:
    parallel=False consults nothing and never dispatches, while
    parallel=None (the wrapper's H=1 value) dispatches. False alone is
    the serial demand."""
    _seam_inject_registry(monkeypatch, tmp_path, [_seam_row_b_record(tmp_path)])
    consults = _seam_count_consults(monkeypatch)

    serial = cyl.Lcyl_v2022a_primary(**driver_args, parallel=False)
    assert consults == []
    assert region_spy == []

    routed = cyl.Lcyl_v2022a_primary(**driver_args, parallel=None)
    assert len(region_spy) == 1
    assert all(np.array_equal(a.view(np.uint32), b.view(np.uint32))
               for a, b in zip(serial[:2], routed[:2]))
