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
"""N9 integration: the driver's STRUCTURAL region dispatch.

There is no selection policy and no registry anywhere in this path (N9
F4): the route declines structurally -- degenerate extent, a lane-
misaligned block size, non-admitted channels, the all-raw payload class
(N9-F3 measured stream loss) -- and otherwise runs the bounded Numba
stream. An explicit expert request (``SOLWEIG_LIGHT_LW_BACKEND=
native|ispc``) stands down to the legacy B7-32 route at the seam, and a
driver-level ``parallel=False`` serial demand never consults the route.

Every routed result is compared BITWISE (uint32 views -- NaN/signed-zero
exact) against the same driver run with ``_lw_region_route`` forced to
None, over IDENTICAL inputs.
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

from solweig_light.radiation import cylinder_longwave as cyl

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
packed = _v6.packed

_ROWS, _COLS, _PATCHES = 37, 53, 153  # tail block + tail gang coverage


@pytest.fixture(autouse=True)
def _shipped_env(monkeypatch):
    """Every test starts from the shipped no-env state; any pools a
    previous test created are torn down (the production per-tile
    teardown does the same)."""
    monkeypatch.delenv('SOLWEIG_LIGHT_LW_BACKEND', raising=False)
    sys.modules.pop('solweig_light._native_dispatch.lw_default_policy',
                    None)
    yield
    import solweig_light._native_dispatch.region.region_pool as rp
    rp.reset_pools_for_tests()  # the region suite's own teardown hygiene


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


def _policy_gone():
    """The qualification selector is gone from the package (N9 F4) and
    no routed call imported a stale copy."""
    import importlib
    assert importlib.util.find_spec(
        'solweig_light._native_dispatch.lw_default_policy') is None
    assert 'solweig_light._native_dispatch.lw_default_policy' \
        not in sys.modules


# ---------------------------------------------------------------------------
# The structural default: the bounded Numba stream
# ---------------------------------------------------------------------------

def test_structural_default_routes_stream_bitwise(args, region_spy):
    """No env, admitted packed channels: the stream executes, bitwise-
    identical to the legacy loop, with no selection policy anywhere in
    the path."""
    legacy, routed = _run_pair(**args)
    assert _bitwise(legacy, routed)
    assert len(region_spy) == 1
    plan, consumer, output, report = region_spy[0]
    assert consumer.mode.value == 'self_parallel'
    assert plan.block_pixels == 128
    assert report.blocks == plan.total_blocks
    _policy_gone()


def test_unknown_legacy_env_value_takes_structural_default(args, region_spy,
                                                           monkeypatch):
    """A non-expert env value ('numba') is not the expert stand-down: the
    structural default applies exactly as with no env at all."""
    monkeypatch.setenv('SOLWEIG_LIGHT_LW_BACKEND', 'numba')
    legacy, routed = _run_pair(**args)
    assert _bitwise(legacy, routed)
    assert len(region_spy) == 1
    _policy_gone()


def test_explicit_expert_env_stands_down_to_b7_32(args, region_spy,
                                                  monkeypatch):
    """Established expert compatibility: env=native/ispc is served by the
    legacy B7-32 route, so the stream route returns None at the seam
    (the region machinery is never touched)."""
    for value in ('native', 'ispc'):
        monkeypatch.setenv('SOLWEIG_LIGHT_LW_BACKEND', value)
        legacy, routed = _run_pair(**args)
        assert _bitwise(legacy, routed)
    assert region_spy == []


def test_serial_demand_never_dispatches(args, region_spy):
    """parallel=False keeps the legacy serial kernel in both runs: the
    route gate stays shut, the route is never consulted."""
    legacy, routed = _run_pair(**args, parallel=False)
    assert _bitwise(legacy, routed)
    assert region_spy == []


def test_lane_misaligned_block_pixels_decline(args, region_spy):
    """A lane-misaligned block size is a STRUCTURAL pre-launch decline:
    the trusted legacy loop serves the call, machinery untouched."""
    legacy, routed = _run_pair(**args, block_pixels=100)
    assert _bitwise(legacy, routed)
    assert region_spy == []


def test_dense_channel_declines_before_launch(rng, region_spy):
    """A NON-admitted (dense) visibility channel is a pre-launch producer
    decline: trusted legacy loop, machinery untouched -- fallback outside
    the admitted domain is the unchanged B7-32 contract."""
    args = lcyl_arguments(rng, rows=_ROWS, cols=_COLS)  # dense mats
    legacy, routed = _run_pair(**args)
    assert _bitwise(legacy, routed)
    assert region_spy == []


def test_all_raw_payload_class_declines(region_spy, rng):
    """The one measured stream loss (N9-F3): ALL-raw packed payloads
    decline pre-launch and the legacy loop serves the call."""
    gen = np.random.default_rng(20260922)
    raw = tuple(packed(gen, _ROWS, _COLS, _PATCHES, ('raw', 'raw', 'raw'))
                for _ in range(3))
    args = lcyl_arguments(rng, rows=_ROWS, cols=_COLS,
                          shmat=raw[0], vegshmat=raw[1],
                          vbshvegshmat=raw[2])
    legacy, routed = _run_pair(**args)
    assert _bitwise(legacy, routed)
    assert region_spy == []


def test_all_raw_decline_parity_same_process_with_guard_alternation(
        args, rng, region_spy):
    """Release-owner REQUIRED (f4_release_disposition.md section 2): an
    all-raw tile through the driver is bitwise == the legacy A8 result
    computed in the SAME process, and a raw -> packed -> raw alternation
    exercises slot reuse across the raw-guard boundary -- the trailing
    raw tile must still match A8 exactly (no stream-state leakage)."""
    gen = np.random.default_rng(20260923)
    channels = tuple(packed(gen, _ROWS, _COLS, _PATCHES,
                            ('raw', 'raw', 'raw')) for _ in range(3))
    raw_args = lcyl_arguments(rng, rows=_ROWS, cols=_COLS,
                              shmat=channels[0], vegshmat=channels[1],
                              vbshvegshmat=channels[2])

    # The A8 references: identical inputs, route forced off, same process.
    real_route = cyl._lw_region_route
    cyl._lw_region_route = lambda *a, **k: None
    try:
        legacy_raw = cyl.Lcyl_v2022a_primary(**raw_args)
        legacy_mixed = cyl.Lcyl_v2022a_primary(**args)
    finally:
        cyl._lw_region_route = real_route

    # Alternation raw -> packed -> raw: the middle (admitted) tile takes
    # the stream and reuses its bounded slots; both raw tiles decline
    # pre-launch at the guard.
    first = cyl.Lcyl_v2022a_primary(**raw_args)
    middle = cyl.Lcyl_v2022a_primary(**args)
    last = cyl.Lcyl_v2022a_primary(**raw_args)

    assert _bitwise(first, legacy_raw)
    assert _bitwise(middle, legacy_mixed)
    assert _bitwise(last, legacy_raw)
    assert len(region_spy) == 1  # only the admitted middle tile dispatched


def test_routed_call_pins_budget_one_and_pool_has_zero_workers(args,
                                                               monkeypatch):
    """Release-owner REQUIRED: the default route executes on the shared
    pool keyed (pid, 1) with ZERO background workers, and the driver
    passes ``budget=1`` (the plan's pinned B1 arm) -- never the wider
    runtime default (threads_per_worker)."""
    import os
    import solweig_light._native_dispatch.region.region_pool as rp
    received = {}
    real = rp.execute_regions

    def spy(plan, consumer, output, **kwargs):
        received['budget'] = kwargs.get('budget')
        return real(plan, consumer, output, **kwargs)

    monkeypatch.setattr(rp, 'execute_regions', spy)
    routed = cyl.Lcyl_v2022a_primary(**args)
    assert routed is not None
    assert received['budget'] == 1
    pool = rp._POOLS.get((os.getpid(), 1))
    assert pool is not None, 'the (pid, 1) shared owner was not created'
    assert pool.worker_count == 0
    # teardown hygiene is the autouse fixture's reset_pools_for_tests()


# ---------------------------------------------------------------------------
# Pool lifecycle (n840-1/n840-4): one shared owner per budget, reuse, and
# explicit teardown
# ---------------------------------------------------------------------------

def test_region_pool_reuse_and_shutdown(args):
    """Two routed calls share ONE pool per budget (registry growth bound),
    and shutdown_all_pools empties the live set."""
    import solweig_light._native_dispatch.region.region_pool as rp

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
