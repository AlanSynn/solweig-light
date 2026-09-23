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
"""N9-F1S bounded stream tests.

The stream must be BITWISE-identical to the measured whole-scene
consumers it replaces (uint32 views -- NaN/signed-zero exact), preserve
the frozen per-block order and canonical first-error contract, reuse its
bounded slots poison-safe, and never allocate a whole-scene ``14*N*P``
decoded cube.

Skip labels (never fake-pass):
  [no-staged-artifact] -- row C needs the genuine N8-13 generation under
                          experiments/optimization_v8/native/stage.
"""
import json
import shutil
import sys
import tracemalloc
from pathlib import Path

import numpy as np
import pytest

import stream_test_helpers as h
from stream_test_helpers import (NAMES, REPO, build_channel, make_case,
                                 outputs_bitwise, staged_generation,
                                 stream_plan, whole_scene_args)

from solweig_light._native_dispatch import direct_aosoa as da
from solweig_light._native_dispatch import lw_stream
from solweig_light._native_dispatch.region import (ExecutionMode,
                                                   RegionPool,
                                                   execute_regions,
                                                   execute_serial,
                                                   plan_regions)
from solweig_light._native_dispatch.region.consumers import AosoaBConsumer
from solweig_light.radiation import _lw_dispatch as dispatch


#: rows x patches grid: lane multiples, non-multiples (tail gang), both
#: frozen patch counts (P small and P=153), block sizes below and above
#: the scene (single-block and many-block) plus a capacity > scene case.
BITWISE_GRID = [
    (8, 5, 128), (16, 153, 128), (37, 153, 16), (128, 153, 128),
    (131, 153, 128), (131, 5, 1024), (300, 9, 16),
]


def _run_stream(case, rows, row, block_pixels, pool_budget=None, width=8):
    """One routed stream call; returns (output, consumer, report)."""
    stream = stream_plan(case, rows, row=row, block_pixels=block_pixels,
                         width=width)
    assert stream is not None
    try:
        output = np.empty((7, rows), dtype=np.float32)
        if row == 'B':
            consumer = lw_stream.AosoaBStreamConsumer(stream)
        else:
            consumer = lw_stream.AosoaCStreamConsumer(stream)
        plan = plan_regions(rows, block_pixels=block_pixels)
        if pool_budget is None:
            report = execute_serial(plan, consumer, output)
        else:
            pool = RegionPool(pool_budget)
            try:
                report = execute_regions(plan, consumer, output, pool=pool)
            finally:
                pool.close()
        return output, consumer, report
    finally:
        stream.close()


def _run_whole_scene(case, rows, row, block_pixels, width=8):
    """The OLD whole-scene consumer over identical inputs (serial)."""
    args = whole_scene_args(case, rows, width=width)
    output = np.empty((7, rows), dtype=np.float32)
    plan = plan_regions(rows, block_pixels=block_pixels)
    if row == 'B':
        consumer = AosoaBConsumer(args, width=width)
    else:
        consumer = dispatch.AosoaNativeCConsumer(args, width=width)
    execute_serial(plan, consumer, output)
    return output


# ---------------------------------------------------------------------------
# Bitwise parity with the measured whole-scene consumers
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('rows, patches, block_pixels', BITWISE_GRID)
def test_stream_b_bitwise_matches_whole_scene_consumer(rows, patches,
                                                       block_pixels):
    """B stream == old whole-scene B consumer, bits exact, serial."""
    case = make_case(rows, patches, seed=rows * 31 + patches)
    stream_out, _, _ = _run_stream(case, rows, 'B', block_pixels)
    whole_out = _run_whole_scene(case, rows, 'B', block_pixels)
    assert outputs_bitwise(stream_out, whole_out)


@pytest.mark.skipif(staged_generation() is None,
                    reason='[no-staged-artifact] run build_aosoa.py to '
                           f'produce {h.STAGE}/<gen>')
@pytest.mark.parametrize('rows, patches, block_pixels', BITWISE_GRID)
def test_stream_c_bitwise_matches_whole_scene_consumer(rows, patches,
                                                       block_pixels):
    """C stream == old whole-scene C consumer, with the REAL artifact."""
    case = make_case(rows, patches, seed=rows * 17 + patches)
    stream_out, consumer, report = _run_stream(case, rows, 'C',
                                               block_pixels, pool_budget=2)
    whole_out = _run_whole_scene(case, rows, 'C', block_pixels)
    assert outputs_bitwise(stream_out, whole_out)
    assert report.mode == 'block_fanout'
    assert isinstance(consumer, dispatch.AosoaNativeCConsumer)


def test_stream_b_parallel_matches_serial_composition():
    """BLOCK composition equality for B under a real multiworker pool."""
    rows, patches, block_pixels = 300, 9, 16
    case = make_case(rows, patches, seed=5)
    serial, _, _ = _run_stream(case, rows, 'B', block_pixels)
    parallel, _, report = _run_stream(case, rows, 'B', block_pixels,
                                      pool_budget=4)
    assert outputs_bitwise(serial, parallel)
    assert report.max_in_flight <= 4


# ---------------------------------------------------------------------------
# Slot reuse: poison-safe across blocks and across mask regimes
# ---------------------------------------------------------------------------

class _PoisoningB(lw_stream.AosoaBStreamConsumer):
    """Poisons every slot buffer at each produce entry: any stale lane a
    consumer failed to overwrite or clear becomes visible garbage."""

    def produce(self, ctx):
        slot = self._slot(ctx)
        for name in ('sh', 'vs', 'vb'):
            getattr(slot, name)[...] = h.POISON_U32
        slot.sun[...] = True
        slot.shade[...] = True
        slot.frame[...] = np.float32('nan')
        return super().produce(ctx)


def test_slot_reuse_poison_safe_alternating_blocks():
    """Binary block then raw block through the SAME slot: every valid
    lane is rewritten, every inactive mask lane cleared, the frame fully
    written -- poisoning changes nothing."""
    rows, patches, block_pixels = 300, 9, 16   # 19 blocks, one shared slot
    case = make_case(rows, patches, seed=11)
    stream = stream_plan(case, rows, row='B', block_pixels=block_pixels)
    try:
        clean = np.empty((7, rows), dtype=np.float32)
        execute_serial(plan_regions(rows, block_pixels=block_pixels),
                       lw_stream.AosoaBStreamConsumer(stream), clean)
        poisoned = np.empty((7, rows), dtype=np.float32)
        execute_serial(plan_regions(rows, block_pixels=block_pixels),
                       _PoisoningB(stream), poisoned)
        assert outputs_bitwise(clean, poisoned)
    finally:
        stream.close()


@pytest.mark.parametrize('gate', ['all', 'none', 'sun'])
def test_mask_clearing_alternating_gate_regimes(gate):
    """Active/inactive classification columns alternate cleanly across
    invocations: slots (fresh per consumer here) must match the
    whole-scene masks for EVERY gate regime, including all-inactive."""
    rows, patches, block_pixels = 70, 6, 16
    case = make_case(rows, patches, seed=13, gate=gate)
    stream_out, _, _ = _run_stream(case, rows, 'B', block_pixels)
    whole_out = _run_whole_scene(case, rows, 'B', block_pixels)
    assert outputs_bitwise(stream_out, whole_out)


# ---------------------------------------------------------------------------
# Ordering + canonical first-error contract
# ---------------------------------------------------------------------------

def _inject_reserved(values, channel_name, pixel):
    """Rewrite one channel as ternary with a code 3 at ``pixel``; the
    first reserved position in patch-major order is then (patch 0,
    pixel), so the failing block is the one covering ``pixel``."""
    from solweig_light.geometry.visibility import PackedVisibility, \
        _EncodedPatch
    codes = np.random.default_rng(pixel).integers(0, 3, size=pixel + 1)
    codes = np.concatenate([codes.astype(np.uint8),
                            np.zeros(300 - pixel - 1, dtype=np.uint8)])
    codes[pixel] = 3
    padded = np.zeros((300 + 3) // 4 * 4, dtype=np.uint8)
    padded[:300] = codes
    payload = (padded[0::4] | (padded[1::4] << 2) | (padded[2::4] << 4)
               | (padded[3::4] << 6)).tobytes()
    channel = values[channel_name]
    replaced = [_EncodedPatch('ternary', payload)
                for _ in channel._patches]
    values[channel_name] = PackedVisibility(channel.shape, tuple(replaced))


def _serial_reference_error(case, rows, block_pixels, width=8):
    """A plain serial loop in the frozen per-block order (classify, then
    sh/vs/vb decode) -- the error the stream must reproduce exactly."""
    values = case['values']
    geometry = case['geometry']
    patches = geometry.altitude.size
    with da._leased((values['shmat'], values['vegshmat'],
                     values['vbshvegshmat']), 0, rows, patches):
        for start in range(0, rows, block_pixels):
            stop = min(start + block_pixels, rows)
            da.classify_block_aosoa(
                values['solar_altitude'], values['solar_azimuth'], geometry,
                values['asvf'], start, stop, active=case['solar_gate'],
                prepared=case['prepared'], width=width)
            for name in ('shmat', 'vegshmat', 'vbshvegshmat'):
                da.produce_block_aosoa(values[name], start, stop, patches,
                                       width=width)


@pytest.mark.parametrize('channel, pixel, failing_block', [
    ('shmat', 200, 1), ('vegshmat', 200, 1), ('vbshvegshmat', 40, 0),
    ('shmat', 260, 2),
])
def test_reserved_code_canonical_first_error(channel, pixel, failing_block):
    """A reserved code in a MIDDLE block: the parallel stream raises the
    SAME error object identity (type + args) as the serial stream and a
    plain serial loop, at the LOWEST failing block (produce-before-
    consume), never a later block's error and never a fallback."""
    rows, patches, block_pixels = 300, 4, 128
    case = make_case(rows, patches, seed=21)
    _inject_reserved(case['values'], channel, pixel)

    with pytest.raises(IndexError) as serial:
        _run_stream(case, rows, 'B', block_pixels)
    with pytest.raises(IndexError) as parallel:
        _run_stream(case, rows, 'B', block_pixels, pool_budget=3)
    assert serial.value.args == parallel.value.args == (
        'Reserved visibility code',)
    assert type(serial.value) is type(parallel.value) is IndexError
    assert parallel.value._solweig_region_failure[
        'first_failing_block'] == failing_block
    with pytest.raises(IndexError) as reference:
        _serial_reference_error(case, rows, block_pixels)
    assert reference.value.args == serial.value.args


# ---------------------------------------------------------------------------
# Admission: pre-launch decline parity with the plural producer
# ---------------------------------------------------------------------------

def _decline_spy(monkeypatch):
    import solweig_light._native_dispatch.region.region_pool as rp
    calls = []
    monkeypatch.setattr(rp, 'execute_regions',
                        lambda *a, **k: calls.append(1))
    return calls


def test_plan_admission_mirrors_producer_exactly(monkeypatch, tmp_path):
    """plan_invocation declines EXACTLY when produce_blocks_aosoa
    declines (same predicate, same channels) -- and a decline happens
    before any region machinery runs, so a mid-stream producer decline
    cannot exist."""
    from solweig_light.geometry.visibility import LazyDiffVisibility
    calls = _decline_spy(monkeypatch)
    rows, patches = 32, 3
    modes = ('binary', 'ternary', 'raw')
    packed = build_channel(rows, modes, seed=1)
    dense = np.zeros((1, rows, patches), dtype=np.float32)
    lazy = LazyDiffVisibility(np.zeros((1, rows, patches), dtype=np.float32),
                              np.zeros((1, rows, patches), dtype=np.float32))
    manifest = tmp_path / 'mapped' / 'manifest.json'
    from solweig_light.geometry.visibility_native import (
        open_native_visibility, save_native_visibility)
    save_native_visibility(manifest, packed)
    mapped = open_native_visibility(manifest)

    triples = [(packed, packed, packed),
               (mapped, mapped, mapped),
               (dense, dense, dense),
               (packed, dense, packed),
               (lazy, packed, packed)]
    for triple in triples:
        case = make_case(rows, patches, seed=2)
        case['values']['shmat'], case['values']['vegshmat'], \
            case['values']['vbshvegshmat'] = triple
        producer = da.produce_blocks_aosoa(*triple, 0, rows, patches)
        plan = stream_plan(case, rows, row='B', block_pixels=128)
        assert (plan is None) == (producer is None), triple
        if plan is not None:
            plan.close()
    assert calls == []          # no decline ever touched the machinery


def test_plan_is_frozen_and_private():
    """The frozen records are immutable after mint and never exposed
    through any public namespace (forgeable by no public call)."""
    import dataclasses
    import solweig_light
    import solweig_light.radiation as radiation
    case = make_case(32, 3, seed=3)
    plan = stream_plan(case, 32, row='B', block_pixels=128)
    assert plan is not None
    try:
        assert dataclasses.is_dataclass(plan)
        with pytest.raises(dataclasses.FrozenInstanceError):
            plan.total = 12345
        for namespace in (solweig_light, radiation):
            for record in ('InvocationPlan', 'BorrowedVisibility',
                           'BlockSlot'):
                assert not hasattr(namespace, record)
    finally:
        plan.close()


# ---------------------------------------------------------------------------
# Thread budgets: H=1 with zero background threads, H=4 disjoint slots
# ---------------------------------------------------------------------------

class _SlowC(lw_stream.AosoaCStreamConsumer):
    """Adds a real sleep per block so BLOCK_FANOUT genuinely overlaps
    (liveness forcing only, never timing)."""

    def consume(self, payload, ctx):
        import time
        time.sleep(0.02)
        super().consume(payload, ctx)


@pytest.mark.skipif(staged_generation() is None,
                    reason='[no-staged-artifact] run build_aosoa.py to '
                           f'produce {h.STAGE}/<gen>')
@pytest.mark.parametrize('budget', [1, 4])
def test_stream_c_h1_and_h4_budgets(budget):
    """H slots follow the granted budget: budget=1 runs with ZERO
    background threads (no background-thread assumption), budget=4 fans
    out over four DISJOINT slots (>= 2 blocks genuinely in flight) and
    matches the serial stream bitwise. The passing fanout is also the
    no-deadlock proof: workers run produce on pinned descriptors while
    the submitting thread holds the leaf lease."""
    rows, patches, block_pixels = 256, 9, 16
    case = make_case(rows, patches, seed=7)
    serial, _, _ = _run_stream(case, rows, 'C', block_pixels)
    stream = stream_plan(case, rows, row='C', block_pixels=block_pixels)
    try:
        output = np.empty((7, rows), dtype=np.float32)
        consumer = _SlowC(stream)
        plan = plan_regions(rows, block_pixels=block_pixels)
        pool = RegionPool(budget)
        try:
            report = execute_regions(plan, consumer, output, pool=pool)
        finally:
            pool.close()
        assert outputs_bitwise(serial, output)
        assert report.max_in_flight <= budget
        assert len(consumer._slots) <= budget
        if budget == 1:
            assert report.pool_workers == 0
        else:
            assert report.max_in_flight >= 2
    finally:
        stream.close()


def test_stream_b_budget_1_zero_background_threads():
    """B (SELF_PARALLEL) at budget 1: the owner spawns no worker and the
    granted budget executes the block in the calling thread."""
    rows, patches, block_pixels = 64, 5, 16
    case = make_case(rows, patches, seed=9)
    stream_out, _, report = _run_stream(case, rows, 'B', block_pixels,
                                        pool_budget=1)
    whole_out = _run_whole_scene(case, rows, 'B', block_pixels)
    assert outputs_bitwise(stream_out, whole_out)
    assert report.pool_workers == 0
    assert report.mode == 'self_parallel'


# ---------------------------------------------------------------------------
# Readonly inputs / no input mutation
# ---------------------------------------------------------------------------

def test_readonly_input_leaves_and_no_mutation():
    """Pinned descriptors are readonly, the driver's arrays stay
    readonly and unmutated, and the result is unchanged."""
    rows, patches, block_pixels = 96, 6, 16
    case = make_case(rows, patches, seed=13)
    values = case['values']
    digests = {name: h.payload_digest(values[name])
               for name in ('shmat', 'vegshmat', 'vbshvegshmat')}
    for name in ('Lup', 'Lsky_down', 'Lsky_side'):
        values[name].setflags(write=False)
    stream = stream_plan(case, rows, row='B', block_pixels=block_pixels)
    try:
        for channel in (stream.borrowed.sh, stream.borrowed.vs,
                        stream.borrowed.vb):
            payloads = channel[0]
            for index in range(len(payloads)):
                assert not payloads[index].flags.writeable
        output = np.empty((7, rows), dtype=np.float32)
        execute_serial(plan_regions(rows, block_pixels=block_pixels),
                       lw_stream.AosoaBStreamConsumer(stream), output)
    finally:
        stream.close()
    whole_out = _run_whole_scene(case, rows, 'B', block_pixels)
    assert outputs_bitwise(output, whole_out)
    for name in ('shmat', 'vegshmat', 'vbshvegshmat'):
        assert h.payload_digest(values[name]) == digests[name]


# ---------------------------------------------------------------------------
# Degenerate sizes: total 0 declines, total 1 is exact
# ---------------------------------------------------------------------------

def test_total_zero_declines_and_total_one_is_exact():
    rows, patches, block_pixels = 1, 3, 128
    case = make_case(rows, patches, seed=15)
    assert stream_plan(case, rows, row='B', block_pixels=block_pixels)
    assert stream_plan(case, 0, row='B', block_pixels=block_pixels) is None
    # total=0 through the public seam: decline before the machinery.
    from solweig_light.radiation._lw_dispatch import region_route
    assert region_route(case['values'], case['geometry'],
                        case['solar_gate'], case['prepared'], 0,
                        block_pixels, case['factor'], case['sun_surface'],
                        case['shade_surface']) is None
    stream_out, _, _ = _run_stream(case, rows, 'B', block_pixels)
    whole_out = _run_whole_scene(case, rows, 'B', block_pixels)
    assert stream_out.shape == whole_out.shape == (7, 1)
    assert outputs_bitwise(stream_out, whole_out)


def test_lane_misaligned_block_declines():
    rows, patches = 32, 3
    case = make_case(rows, patches, seed=17)
    assert stream_plan(case, rows, row='B', block_pixels=100) is None
    assert stream_plan(case, rows, row='B', block_pixels=4) is None


# ---------------------------------------------------------------------------
# The bounded-memory proof: no 14*N*P cube anywhere in the routed path
# ---------------------------------------------------------------------------

def test_slot_payload_is_block_bounded_not_scene_bounded():
    """Owned slot payload is ~14*B*P per slot, independent of the scene
    extent, and the WHOLE-SCENE prologue is never called on the routed
    path (produce_blocks_aosoa(0,total) would raise)."""
    rows, patches, block_pixels = 4096, 153, 1024
    case = make_case(rows, patches, seed=19)
    stream = stream_plan(case, rows, row='B', block_pixels=block_pixels)
    try:
        output = np.empty((7, rows), dtype=np.float32)
        consumer = lw_stream.AosoaBStreamConsumer(stream)

        def bomb(*args, **kwargs):
            raise AssertionError('whole-scene producer ran on the stream')

        real = da.produce_blocks_aosoa
        da.produce_blocks_aosoa = bomb
        try:
            execute_serial(plan_regions(rows, block_pixels=block_pixels),
                           consumer, output)
        finally:
            da.produce_blocks_aosoa = real
        bound = stream.thread_budget * (14 * block_pixels * patches)
        assert consumer.slot_bytes() <= bound
        assert bound < 14 * rows * patches  # the whole-scene cube
    finally:
        stream.close()


def test_routed_peak_memory_independent_of_scene_extent():
    """Warm routed-call peak (tracemalloc, H-slot allocation included)
    stays flat as the scene grows: 4x the extent must NOT grow the peak,
    and the peak is the slots, a small fraction of the whole-scene cube
    the old path materialized."""
    block_pixels, patches = 1024, 153
    peaks = {}
    for rows in (4096, 16384):
        case = make_case(rows, patches, seed=rows)
        stream = stream_plan(case, rows, row='B',
                             block_pixels=block_pixels)
        try:
            plan = plan_regions(rows, block_pixels=block_pixels)
            warm = np.empty((7, rows), dtype=np.float32)
            # Warm the process: JIT, caches, the first consumer's slots.
            execute_serial(plan, lw_stream.AosoaBStreamConsumer(stream),
                           warm)
            tracemalloc.start()
            consumer = lw_stream.AosoaBStreamConsumer(stream)  # H slots
            measured = np.empty((7, rows), dtype=np.float32)
            execute_serial(plan, consumer, measured)
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            assert outputs_bitwise(warm, measured)
            peaks[rows] = peak
        finally:
            stream.close()
    whole_small = 14 * 4096 * patches
    whole_large = 14 * 16384 * patches
    # Flat in the extent (4x scene -> < 2x peak) and far under the cube.
    assert peaks[16384] < 2 * peaks[4096] + (1 << 20)
    assert peaks[4096] < whole_small
    assert peaks[16384] < whole_large // 2


# ---------------------------------------------------------------------------
# The public seam still routes through the stream (driver-level, row B)
# ---------------------------------------------------------------------------

def test_driver_seam_routes_stream_row_b(monkeypatch, tmp_path):
    """A qualified B record drives the FULL driver through the rewired
    _execute_row: one region submission, the stream B consumer, bitwise
    equal to the legacy loop over identical inputs."""
    import hashlib
    from policy_test_helpers import COMMIT, make_promotion_record, write_json
    from solweig_light._native_dispatch import lw_default_policy as policy

    import importlib.util
    _V6_CONFTEST = (Path(__file__).resolve().parents[2] / 'optimization_v6'
                    / 'cylinder_lw' / 'conftest.py')
    spec = importlib.util.spec_from_file_location('_n9s_v6_conftest',
                                                  str(_V6_CONFTEST))
    v6 = importlib.util.module_from_spec(spec)
    sys.modules['_n9s_v6_conftest'] = v6
    spec.loader.exec_module(v6)

    rng = np.random.default_rng(20260923)
    rows, cols, patches = 37, 53, 153
    # Adversarial PACKED channels (dense mats are a pre-launch decline).
    channels = tuple(v6.packed(rng, rows, cols, patches,
                               ('binary', 'ternary', 'raw'))
                     for _ in range(3))
    args = v6.lcyl_arguments(rng, rows=rows, cols=cols, shmat=channels[0],
                             vegshmat=channels[1],
                             vbshvegshmat=channels[2])

    promotion_path, promotion_sha = write_json(
        tmp_path / 'evidence' / 'promotion.json', make_promotion_record())
    review_path, review_sha = write_json(
        tmp_path / 'evidence' / 'review.json',
        {'schema': 'sw8-lw-review-v1', 'task': 'N9-F1S-stream',
         'verdict': 'APPROVE-WITH-NOTES'})
    module_rel = 'src/solweig_light/_native_dispatch/lw_b_control.py'
    real = REPO / module_rel
    # The certified module resolves under the fake REPO_ROOT: mirror it.
    module_copy = tmp_path / module_rel
    module_copy.parent.mkdir(parents=True)
    module_copy.write_bytes(real.read_bytes())
    record = {
        'schema': policy.ROW_RECORD_SCHEMA, 'status': 'qualified',
        'row': 'B', 'host_class': policy.current_host_class(),
        'created_utc': '2026-09-23T00:00:00Z', 'source_commit': COMMIT,
        'artifact_identity': {
            'kind': 'python-module', 'module_path': module_rel,
            'module_sha256': hashlib.sha256(real.read_bytes()).hexdigest()},
        'promotion_record': {'path': 'evidence/promotion.json',
                             'sha256': promotion_sha,
                             'schema': policy.PROMOTION_RECORD_SCHEMA},
        'cells': ['primary-0', 'primary-2'],
        'independent_review': {'path': 'evidence/review.json',
                               'sha256': review_sha},
    }
    registry = tmp_path / 'registry.json'
    registry.write_text(json.dumps(
        {'schema': policy.REGISTRY_SCHEMA, 'records': [record]}))
    tools = REPO / 'optimization_v8_native_default' / 'tools'
    mirrored = tmp_path / 'optimization_v8_native_default' / 'tools'
    if tools.is_dir() and not mirrored.is_dir():
        shutil.copytree(tools, mirrored)
    monkeypatch.setattr(policy, 'DEFAULT_REGISTRY_PATH', registry)
    monkeypatch.setattr(policy, 'REPO_ROOT', tmp_path)
    monkeypatch.delenv('SOLWEIG_LIGHT_LW_BACKEND', raising=False)

    import solweig_light._native_dispatch.region.region_pool as rp
    import solweig_light.radiation.cylinder_longwave as cyl
    calls = []
    real_exec = rp.execute_regions

    def spy(plan_, consumer, output, **kwargs):
        report = real_exec(plan_, consumer, output, **kwargs)
        calls.append(consumer)
        return report

    monkeypatch.setattr(rp, 'execute_regions', spy)

    real_route = cyl._lw_region_route
    cyl._lw_region_route = lambda *a, **k: None
    try:
        legacy = cyl.Lcyl_v2022a_primary(**args)
    finally:
        cyl._lw_region_route = real_route
    try:
        routed = cyl.Lcyl_v2022a_primary(**args)
    finally:
        rp.reset_pools_for_tests()

    assert all(np.array_equal(a.view(np.uint32), b.view(np.uint32))
               for a, b in zip(legacy[:2], routed[:2]))
    assert len(calls) == 1
    assert isinstance(calls[0], lw_stream.AosoaBStreamConsumer)
    assert calls[0].mode is ExecutionMode.SELF_PARALLEL
