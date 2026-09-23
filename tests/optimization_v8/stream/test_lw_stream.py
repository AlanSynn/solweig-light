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
"""N9 bounded stream tests (the shipped default route, row B only).

The stream must be BITWISE-identical to the whole-scene consumer it
replaces (uint32 views -- NaN/signed-zero exact), preserve the frozen
per-block order and canonical first-error contract, reuse its bounded
slots poison-safe, never allocate a whole-scene ``14*N*P`` decoded cube,
and decline structurally exactly where the measured stream-loss class
(all-raw payloads, N9-F3) or the producer's own admission declines.
"""
import importlib.util
import sys
import tracemalloc
from pathlib import Path

import numpy as np
import pytest

import stream_test_helpers as h
from stream_test_helpers import (build_channel, make_case, outputs_bitwise,
                                 stream_plan, whole_scene_args)

from solweig_light._native_dispatch import direct_aosoa as da
from solweig_light._native_dispatch import lw_stream
from solweig_light._native_dispatch.region import (ExecutionMode,
                                                   RegionPool,
                                                   execute_regions,
                                                   execute_serial,
                                                   plan_regions)
from solweig_light._native_dispatch.region.consumers import AosoaBConsumer


#: rows x patches grid: lane multiples, non-multiples (tail gang), both
#: frozen patch counts (P small and P=153), block sizes below and above
#: the scene (single-block and many-block) plus a capacity > scene case.
BITWISE_GRID = [
    (8, 5, 128), (16, 153, 128), (37, 153, 16), (128, 153, 128),
    (131, 153, 128), (131, 5, 1024), (300, 9, 16),
]


def _run_stream(case, rows, block_pixels, pool_budget=None, width=8):
    """One routed stream call; returns (output, consumer, report)."""
    stream = stream_plan(case, rows, row='B', block_pixels=block_pixels,
                         width=width)
    assert stream is not None
    try:
        output = np.empty((7, rows), dtype=np.float32)
        consumer = lw_stream.AosoaBStreamConsumer(stream)
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


def _run_whole_scene(case, rows, block_pixels, width=8):
    """The whole-scene consumer over identical inputs (serial)."""
    args = whole_scene_args(case, rows, width=width)
    output = np.empty((7, rows), dtype=np.float32)
    plan = plan_regions(rows, block_pixels=block_pixels)
    execute_serial(plan, AosoaBConsumer(args, width=width), output)
    return output


# ---------------------------------------------------------------------------
# Bitwise parity with the whole-scene consumer
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('rows, patches, block_pixels', BITWISE_GRID)
def test_stream_b_bitwise_matches_whole_scene_consumer(rows, patches,
                                                       block_pixels):
    """B stream == whole-scene B consumer, bits exact, serial."""
    case = make_case(rows, patches, seed=rows * 31 + patches)
    stream_out, _, _ = _run_stream(case, rows, block_pixels)
    whole_out = _run_whole_scene(case, rows, block_pixels)
    assert outputs_bitwise(stream_out, whole_out)


def test_stream_b_parallel_matches_serial_composition():
    """BLOCK composition equality for B under a real multiworker pool."""
    rows, patches, block_pixels = 300, 9, 16
    case = make_case(rows, patches, seed=5)
    serial, _, _ = _run_stream(case, rows, block_pixels)
    parallel, _, report = _run_stream(case, rows, block_pixels,
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
    stream_out, _, _ = _run_stream(case, rows, block_pixels)
    whole_out = _run_whole_scene(case, rows, block_pixels)
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
        _run_stream(case, rows, block_pixels)
    with pytest.raises(IndexError) as parallel:
        _run_stream(case, rows, block_pixels, pool_budget=3)
    assert serial.value.args == parallel.value.args == (
        'Reserved visibility code',)
    assert type(serial.value) is type(parallel.value) is IndexError
    assert parallel.value._solweig_region_failure[
        'first_failing_block'] == failing_block
    with pytest.raises(IndexError) as reference:
        _serial_reference_error(case, rows, block_pixels)
    assert reference.value.args == serial.value.args


# ---------------------------------------------------------------------------
# Admission: pre-launch decline parity + the all-raw stream-loss class
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
    cannot exist. (Channels here are mixed-mode, so the separate all-raw
    guard never fires and the pure producer parity is what is measured.)"""
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


def test_all_raw_declines_pre_launch_and_releases_the_lease(tmp_path):
    """The one measured stream-loss class (N9-F3): when EVERY patch of
    ALL THREE channels is raw (mode 4), the plan declines PRE-LAUNCH and
    the top-level leaf lease is RELEASED -- no lock survives the decline.
    MappedVisibility leaves are the genuine raw-storage leaves; their
    RLocks are reentrant per-thread, so the release proof acquires each
    lock NON-BLOCKING from a fresh thread (a same-thread check could
    never see a leak)."""
    import threading
    rows, patches = 32, 3

    # (a) packed leaves whose patches are all raw mode.
    case = make_case(rows, patches, seed=29, modes_cycle=('raw',))
    assert stream_plan(case, rows, row='B', block_pixels=128) is None

    # (b) mapped (mmap) leaves over all-raw payloads.
    from solweig_light.geometry.visibility_native import (
        open_native_visibility, save_native_visibility)
    channels = []
    for index in range(3):
        manifest = tmp_path / f'mapped_raw_{index}' / 'manifest.json'
        manifest.parent.mkdir(parents=True)
        save_native_visibility(
            manifest, build_channel(rows, ('raw',) * patches,
                                    seed=40 + index))
        channels.append(open_native_visibility(manifest))
    case = make_case(rows, patches, seed=43)
    (case['values']['shmat'], case['values']['vegshmat'],
     case['values']['vbshvegshmat']) = tuple(channels)
    # Sanity: the pinned mode bytes really are all raw.
    from solweig_light.geometry.visibility_compiled import _descriptor
    assert all(bool((_descriptor(ch)[1] == 4).all()) for ch in channels)
    assert stream_plan(case, rows, row='B', block_pixels=128) is None

    # The lease is gone: every leaf lock is freely acquirable elsewhere.
    for channel in channels:
        outcome = []

        def _grab(lock=channel._lock):
            acquired = lock.acquire(blocking=False)
            if acquired:
                lock.release()
            outcome.append(acquired)

        worker = threading.Thread(target=_grab)
        worker.start()
        worker.join(10)
        assert outcome == [True], 'a leaf lock survived the decline'


@pytest.mark.parametrize('modes_cycle', [
    ('binary', 'ternary', 'raw'),   # the classic mix
    ('binary',),                    # all-binary
    ('raw', 'binary', 'raw'),       # one non-raw patch keeps the stream
])
def test_non_all_raw_payloads_admit(modes_cycle):
    """Any binary/ternary patch in ANY channel keeps the stream: only the
    ALL-raw class declines."""
    rows, patches = 32, 3
    case = make_case(rows, patches, seed=31, modes_cycle=modes_cycle)
    plan = stream_plan(case, rows, row='B', block_pixels=128)
    assert plan is not None
    plan.close()


@pytest.mark.parametrize('row', ['A', 'C', 'D'])
def test_unknown_row_raises_value_error(row):
    """The shipped stream is row B only: any other row is a loud error at
    the very first check -- never a silent decline, never a mint."""
    case = make_case(32, 3, seed=33)
    with pytest.raises(ValueError, match='unknown stream row'):
        stream_plan(case, 32, row=row, block_pixels=128)


def test_single_slot_prealloc_self_parallel():
    """The shipped consumer is SELF_PARALLEL with ONE preallocated slot
    (slot id 0 -- the only id a serial owner ever leases): the table has
    exactly that key at construction and slot_bytes() is one BlockSlot's
    payload. The lazy growth path stays as the correctness valve for a
    future fanout owner, never as extra preallocation."""
    rows, patches, block_pixels = 64, 5, 16
    case = make_case(rows, patches, seed=35)
    stream = stream_plan(case, rows, row='B', block_pixels=block_pixels)
    try:
        consumer = lw_stream.AosoaBStreamConsumer(stream)
        assert list(consumer._slots) == [0]
        one = lw_stream.BlockSlot(stream.slot_gangs, stream.patches,
                                  stream.width, stream.block_capacity)
        assert consumer.slot_bytes() == one.payload_bytes
        assert consumer.mode is ExecutionMode.SELF_PARALLEL
        # And one slot suffices for a full execution in the calling thread.
        output = np.empty((7, rows), dtype=np.float32)
        execute_serial(plan_regions(rows, block_pixels=block_pixels),
                       consumer, output)
        assert list(consumer._slots) == [0]   # no growth, no aliasing
    finally:
        stream.close()


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
# Thread budget: the leaf's prange owns it; budget 1 = zero background
# ---------------------------------------------------------------------------

def test_stream_b_budget_1_zero_background_threads():
    """B (SELF_PARALLEL) at budget 1: the owner spawns no worker and the
    granted budget executes the block in the calling thread."""
    rows, patches, block_pixels = 64, 5, 16
    case = make_case(rows, patches, seed=9)
    stream_out, _, report = _run_stream(case, rows, block_pixels,
                                        pool_budget=1)
    whole_out = _run_whole_scene(case, rows, block_pixels)
    assert outputs_bitwise(stream_out, whole_out)
    assert report.pool_workers == 0
    assert report.mode == 'self_parallel'


def test_plan_thread_budget_pinned_to_one_regardless_of_runtime_threads():
    """N9 F4 REQUIRED: the shipped route is the measured B1 arm -- the
    plan's budget is PINNED to 1 whatever the runtime thread width says,
    so H>1 runtimes can never resurrect the B4 arm that lost every cell."""
    from solweig_light.runtime import runtime_options
    rows = 64
    case = make_case(rows, 153, seed=9)
    for threads in (1, 4):
        with runtime_options(cpu_budget=threads, threads_per_worker=threads):
            stream = stream_plan(case, rows, row='B', block_pixels=128)
            try:
                assert stream.thread_budget == 1, threads
            finally:
                stream.close()


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
    whole_out = _run_whole_scene(case, rows, block_pixels)
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
    stream_out, _, _ = _run_stream(case, rows, block_pixels)
    whole_out = _run_whole_scene(case, rows, block_pixels)
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
    """Warm routed-call peak (tracemalloc, slot allocation included)
    stays flat as the scene grows: 4x the extent must NOT grow the peak,
    and the peak is the slot, a small fraction of the whole-scene cube
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
            # Warm the process: JIT, caches, the first consumer's slot.
            execute_serial(plan, lw_stream.AosoaBStreamConsumer(stream),
                           warm)
            tracemalloc.start()
            consumer = lw_stream.AosoaBStreamConsumer(stream)  # the slot
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

def test_driver_seam_routes_stream_row_b(monkeypatch):
    """The structural default drives the FULL driver through the rewired
    _execute_row: one region submission, the stream B consumer, bitwise
    equal to the legacy loop over identical inputs -- and no selection
    policy exists anywhere in the path (the module is gone from the
    package and never imported by a routed call)."""
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
    monkeypatch.delenv('SOLWEIG_LIGHT_LW_BACKEND', raising=False)
    # Defensive: drop any copy an earlier test session may have leaked so
    # the post-run absence below can only be explained by THIS path.
    sys.modules.pop('solweig_light._native_dispatch.lw_default_policy',
                    None)

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
    # No selection policy anywhere in the path: the module is gone from
    # the package and a routed call never imported it.
    import importlib
    assert importlib.util.find_spec(
        'solweig_light._native_dispatch.lw_default_policy') is None
    assert 'solweig_light._native_dispatch.lw_default_policy' \
        not in sys.modules
