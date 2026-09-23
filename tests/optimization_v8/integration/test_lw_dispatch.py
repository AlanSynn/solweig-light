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
"""N8-40 integration: the driver's policy-selected region dispatch.

Every routed result is compared BITWISE (uint32 views -- NaN/signed-zero
exact) against the same driver run with ``_lw_region_route`` forced to
None, over IDENTICAL inputs. The shipped-state test exercises the REAL
shipped registry file (no injection): empty records must resolve auto ->
A without touching any machinery.

Skip labels (never fake-pass):
  [no-staged-artifact] -- no lw-g8-* generation under
                          experiments/optimization_v8/native/stage (row C
                          tests need the genuine N8-13 artifact).
"""
import hashlib
import importlib.util
import json
import shutil
import sys
import uuid
from pathlib import Path

import numpy as np
import pytest

from solweig_light.radiation import cylinder_longwave as cyl
from solweig_light.radiation import _lw_dispatch as dispatch

# The v6 cylinder family's conftest, loaded by file path: a bare
# `import conftest` is shadowed by sibling suites in one pytest session.
_V6_CONFTEST = (Path(__file__).resolve().parents[2] / 'optimization_v6'
                / 'cylinder_lw' / 'conftest.py')
_spec = importlib.util.spec_from_file_location('_n840_v6_conftest',
                                               str(_V6_CONFTEST))
_v6 = importlib.util.module_from_spec(_spec)
sys.modules['_n840_v6_conftest'] = _v6
_spec.loader.exec_module(_v6)
lcyl_arguments = _v6.lcyl_arguments
lcyl_patches = _v6.lcyl_patches
packed = _v6.packed

# N8-41 vendoring: the machinery and the policy module ship in the
# package -- the SAME module identity the dispatch itself binds.
_HELPERS = Path(__file__).resolve().parent.parent / 'policy'
if str(_HELPERS) not in sys.path:
    sys.path.insert(0, str(_HELPERS))
from solweig_light._native_dispatch import lw_default_policy as policy  # noqa: E402
from policy_test_helpers import COMMIT, make_promotion_record, write_json  # noqa: E402
from solweig_light._native_dispatch import installed_loader  # noqa: E402  (N8-21; genuine loaded outcome)

_REPO = Path(__file__).resolve().parents[3]
_STAGE = _REPO / 'experiments' / 'optimization_v8' / 'native' / 'stage'

_ROWS, _COLS, _PATCHES = 37, 53, 153  # tail block + tail gang coverage


@pytest.fixture(autouse=True)
def _shipped_env(monkeypatch):
    """Every test starts from the shipped no-env state; policy state and
    any pools a previous test created are torn down (the production
    per-tile teardown does the same)."""
    monkeypatch.delenv('SOLWEIG_LIGHT_LW_BACKEND', raising=False)
    policy.reset_for_tests()
    yield
    import solweig_light._native_dispatch.region.region_pool as rp
    rp.reset_pools_for_tests()  # the region suite's own teardown hygiene
    policy.reset_for_tests()


@pytest.fixture()
def rng():
    return np.random.default_rng(20260922)


@pytest.fixture(scope='module')
def channels():
    """Adversarial packed visibility channels (binary/ternary/raw mixes),
    built once -- every test reuses the identical inputs."""
    gen = np.random.default_rng(20260922)
    return (packed(gen, _ROWS, _COLS, _PATCHES, ('binary', 'ternary', 'raw')),
            packed(gen, _ROWS, _COLS, _PATCHES, ('ternary', 'raw', 'binary')),
            packed(gen, _ROWS, _COLS, _PATCHES, ('raw', 'binary', 'ternary')))


@pytest.fixture()
def args(rng, channels):
    """Driver arguments whose visibility mats are the packed channels."""
    return lcyl_arguments(rng, rows=_ROWS, cols=_COLS,
                          shmat=channels[0], vegshmat=channels[1],
                          vbshvegshmat=channels[2])


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
# Helpers
# ---------------------------------------------------------------------------

def _bitwise(first, second):
    """The two primary fields, exact bits (slots 2..5 are NOT_REQUESTED)."""
    return all(np.array_equal(a.view(np.uint32), b.view(np.uint32))
               for a, b in zip(first[:2], second[:2]))


def _run_pair(**args):
    """(legacy, dispatched) primary results over identical inputs."""
    real_route = cyl._lw_region_route
    cyl._lw_region_route = lambda *a, **k: None
    try:
        legacy = cyl.Lcyl_v2022a_primary(**args)
    finally:
        cyl._lw_region_route = real_route
    routed = cyl.Lcyl_v2022a_primary(**args)
    return legacy, routed


def _write_evidence(tmp_path):
    """Fabricated promotion + review tree; returns a row_record builder."""
    promotion_path, promotion_sha = write_json(
        tmp_path / 'evidence' / 'promotion.json', make_promotion_record())
    review_path, review_sha = write_json(
        tmp_path / 'evidence' / 'review.json',
        {'schema': 'sw8-lw-review-v1', 'task': 'N8-40-integration',
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


def _inject_registry(monkeypatch, tmp_path, records):
    """Point the policy module's call-time globals at the tmp evidence.

    REPO_ROOT moves so record evidence paths resolve under tmp; the packet
    ``tools/`` tree (real promotion-gate code) is mirrored into the fake
    root because ``_assess_promotion`` imports it relative to REPO_ROOT.
    """
    path = tmp_path / 'registry.json'
    path.write_text(json.dumps(
        {'schema': policy.REGISTRY_SCHEMA, 'records': list(records)}))
    tools = _REPO / 'optimization_v8_native_default' / 'tools'
    mirrored = tmp_path / 'optimization_v8_native_default' / 'tools'
    if tools.is_dir() and not mirrored.is_dir():
        shutil.copytree(tools, mirrored)
    monkeypatch.setattr(policy, 'DEFAULT_REGISTRY_PATH', path)
    monkeypatch.setattr(policy, 'REPO_ROOT', tmp_path)


def _staged_generation():
    manifests = sorted(_STAGE.glob('*/manifest.json'))
    if not manifests:
        pytest.skip('[no-staged-artifact] run build_aosoa.py to produce '
                    f'{_STAGE}/<gen>')
    return manifests[-1].parent


def _genuine_outcome(tmp_path, staged):
    """A REAL N8-21 LoadOutcome for a copy of the staged N8-13 generation
    (fake installed package, policy-suite pattern)."""
    name = f'fake_native_pkg_{uuid.uuid4().hex[:10]}'
    root = tmp_path / name
    generated = root / 'backends' / 'native_generated'
    generated.mkdir(parents=True)
    (root / '__init__.py').write_text('')
    shutil.copytree(staged, generated / staged.name)
    sys.path.insert(0, str(tmp_path))
    try:
        importlib.import_module(name)
        installed_loader.reset_for_tests()
        outcome = installed_loader.attempt_load(name)
    finally:
        sys.modules.pop(name, None)
        while str(tmp_path) in sys.path:
            sys.path.remove(str(tmp_path))
    installed_loader.reset_for_tests()
    assert outcome.status == 'loaded', outcome.reason
    return outcome


# ---------------------------------------------------------------------------
# Shipped state: the wiring is inert byte-for-byte
# ---------------------------------------------------------------------------

def test_shipped_registry_routes_legacy_bitwise(args, region_spy):
    """Real shipped registry (no injection): [absent] -> row A -> the
    legacy loop, and the region machinery is never touched."""
    legacy, routed = _run_pair(**args)
    assert _bitwise(legacy, routed)
    assert region_spy == []
    assert any('[absent]' in reason for reason in policy.policy_reasons())


def test_explicit_expert_env_stays_with_legacy_route(args, region_spy,
                                                     monkeypatch):
    """Staged expert migration (n840-6): env=native/ispc is served by the
    legacy B7-32 route; the policy selector is never consulted."""
    called = []
    monkeypatch.setattr(policy, 'resolve_lw_backend',
                        lambda *a, **k: called.append(1))
    for value in ('native', 'ispc'):
        monkeypatch.setenv('SOLWEIG_LIGHT_LW_BACKEND', value)
        legacy, routed = _run_pair(**args)
        assert _bitwise(legacy, routed)
    assert called == []
    assert region_spy == []


def test_unknown_legacy_env_value_routes_legacy(args, region_spy,
                                                monkeypatch):
    monkeypatch.setenv('SOLWEIG_LIGHT_LW_BACKEND', 'numba')
    legacy, routed = _run_pair(**args)
    assert _bitwise(legacy, routed)
    assert region_spy == []


def test_serial_demand_never_dispatches(args, region_spy):
    """parallel=False keeps the legacy serial kernel in both runs."""
    legacy, routed = _run_pair(**args, parallel=False)
    assert _bitwise(legacy, routed)
    assert region_spy == []


def test_lane_misaligned_block_pixels_decline(args, region_spy,
                                              monkeypatch, tmp_path):
    """A qualified row still declines (pre-launch) when the driver's block
    size is not lane-aligned; the trusted legacy loop serves the call."""
    row_record = _write_evidence(tmp_path)
    module_rel = 'src/solweig_light/_native_dispatch/lw_b_control.py'
    real = _REPO / module_rel
    module_copy = tmp_path / module_rel
    module_copy.parent.mkdir(parents=True)
    module_copy.write_bytes(real.read_bytes())
    record = row_record(row='B', artifact_identity={
        'kind': 'python-module', 'module_path': module_rel,
        'module_sha256': hashlib.sha256(real.read_bytes()).hexdigest()})
    _inject_registry(monkeypatch, tmp_path, [record])
    legacy, routed = _run_pair(**args, block_pixels=100)
    assert _bitwise(legacy, routed)
    assert region_spy == []


# ---------------------------------------------------------------------------
# Qualified rows: the region path executes and stays bitwise-faithful
# ---------------------------------------------------------------------------

def test_row_b_qualified_record_routes_region(args, region_spy, monkeypatch,
                                              tmp_path):
    row_record = _write_evidence(tmp_path)
    module_rel = 'src/solweig_light/_native_dispatch/lw_b_control.py'
    real = _REPO / module_rel
    module_copy = tmp_path / module_rel
    module_copy.parent.mkdir(parents=True)
    module_copy.write_bytes(real.read_bytes())
    record = row_record(row='B', artifact_identity={
        'kind': 'python-module', 'module_path': module_rel,
        'module_sha256': hashlib.sha256(real.read_bytes()).hexdigest()})
    _inject_registry(monkeypatch, tmp_path, [record])

    legacy, routed = _run_pair(**args)
    assert _bitwise(legacy, routed)
    assert len(region_spy) == 1
    plan, consumer, output, report = region_spy[0]
    assert consumer.mode.value == 'self_parallel'
    assert plan.block_pixels == 128
    assert report.blocks == plan.total_blocks
    # The success path returns without logging; assert the selector itself
    # reached the qualified row under this exact injected state.
    selection = policy.resolve_lw_backend()
    assert selection.row == 'B' and selection.mode == 'auto-qualified'


def test_row_c_qualified_record_routes_native(args, region_spy, monkeypatch,
                                              tmp_path):
    staged = _staged_generation()
    outcome = _genuine_outcome(tmp_path, staged)
    manifest = json.loads((staged / 'manifest.json').read_text())
    row_record = _write_evidence(tmp_path)
    record = row_record(row='C', artifact_identity={
        'kind': 'installed-native-generation',
        'generation': manifest['generation'],
        'kernel_sha256': manifest['kernel']['sha256'],
        'dylib_sha256': manifest['artifacts'][0]['sha256']})
    _inject_registry(monkeypatch, tmp_path, [record])
    monkeypatch.setattr(policy, '_default_attempt_load', lambda: outcome)

    legacy, routed = _run_pair(**args)
    assert _bitwise(legacy, routed)
    assert len(region_spy) == 1
    plan, consumer, output, report = region_spy[0]
    assert isinstance(consumer, dispatch.AosoaNativeCConsumer)
    assert consumer.mode.value == 'block_fanout'
    assert report.blocks == plan.total_blocks


def test_dense_channel_declines_before_launch(monkeypatch, tmp_path, rng,
                                              region_spy):
    """A qualified row over a NON-admitted (dense) visibility channel is a
    pre-launch producer decline: trusted legacy loop, machinery untouched.
    The shipped B7-32 contract already establishes fallback outside the
    admitted domain."""
    args = lcyl_arguments(rng, rows=_ROWS, cols=_COLS)  # dense mats
    record = _write_evidence(tmp_path)(row='B', artifact_identity={
        'kind': 'python-module',
        'module_path': 'src/solweig_light/_native_dispatch/lw_b_control.py',
        'module_sha256': hashlib.sha256(
            (_REPO / 'src/solweig_light/_native_dispatch/lw_b_control.py')
            .read_bytes()).hexdigest()})
    _inject_registry(monkeypatch, tmp_path, [record])
    legacy, routed = _run_pair(**args)
    assert _bitwise(legacy, routed)
    assert region_spy == []


# ---------------------------------------------------------------------------
# Pool lifecycle (n840-1/n840-4): one shared owner per budget, reuse, and
# explicit teardown
# ---------------------------------------------------------------------------

def test_region_pool_reuse_and_shutdown(args, monkeypatch, tmp_path):
    """Two routed calls share ONE pool per budget (registry growth bound),
    and shutdown_all_pools empties the live set."""
    import solweig_light._native_dispatch.region.region_pool as rp
    row_record = _write_evidence(tmp_path)
    module_rel = 'src/solweig_light/_native_dispatch/lw_b_control.py'
    real = _REPO / module_rel
    module_copy = tmp_path / module_rel
    module_copy.parent.mkdir(parents=True)
    module_copy.write_bytes(real.read_bytes())
    record = row_record(row='B', artifact_identity={
        'kind': 'python-module', 'module_path': module_rel,
        'module_sha256': hashlib.sha256(real.read_bytes()).hexdigest()})
    _inject_registry(monkeypatch, tmp_path, [record])
    def _live_pools():
        # LIVE filter: post n8-14 repair, close() always untracks, so this
        # is a pure safety net (delta review R-D1/N-D1); the reuse/growth
        # invariant is asserted over the pool TABLE's live entries.
        return {id(p) for p in rp._LIVE_POOLS
                if not p.closed and not p.poisoned}

    try:
        cyl.Lcyl_v2022a_primary(**args)
        after_first = _live_pools()
        assert len(after_first) == 1
        cyl.Lcyl_v2022a_primary(**args)
        assert _live_pools() == after_first
    finally:
        rp.reset_pools_for_tests()
    assert len(list(rp._LIVE_POOLS)) == 0
