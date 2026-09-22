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
"""N8-14 scratch gates: microblock scratch independent from dispatch
size, bounded allocations, exclusive leases, no aliasing, poison-safe
reuse, fixed-shape arenas."""
import threading
import time

import numpy as np
import pytest
from test_typed_graph_identity import adversarial_inputs

from region import (RegionPool, ScratchShapeError, ScratchSlot,
                    execute_regions, execute_serial, plan_regions)
from region.consumers import DenseKernelConsumer
from region_case import (aosoa_case, b_consumer, fresh_output,
                         oracle_reduce, outputs_bitwise_equal)

B = 128


class _OverlappingDense(DenseKernelConsumer):
    """Oracle arm A with a small sleep in consume: releases the GIL so
    blocks genuinely overlap. Liveness forcing only, NOT timing."""

    def __init__(self, args, delay):
        super().__init__(oracle_reduce, args)
        self._delay = delay

    def consume(self, payload, ctx):
        if self._delay:
            time.sleep(self._delay)
        return super().consume(payload, ctx)


def run_once(n, region_blocks, budget, seed=5, delay=0.02):
    args = adversarial_inputs(n, 61, seed)
    plan = plan_regions(n, block_pixels=B, region_blocks=region_blocks)
    out = fresh_output(n)
    pool = RegionPool(budget)
    try:
        report = execute_regions(plan, _OverlappingDense(args, delay), out,
                                 pool=pool)
    finally:
        pool.close()
    return out, report


@pytest.mark.parametrize('region_blocks', [1, 2, 3, 7, 10 ** 6])
def test_scratch_independent_from_dispatch_size(region_blocks):
    """Same block size, dispatch granularities from one block per region
    to one giant region: identical bits, and scratch allocation counts
    that depend only on the budget and the blocks-per-region overlap
    actually available -- never on how many regions or total blocks run.

    The delay forces every lane of a region to overlap, so the count is
    deterministic: min(budget, blocks per region) x 1 buffer name."""
    n = 10 * B      # 10 blocks total
    reference, _ = run_once(n, None, 3)               # one giant region
    out, report = run_once(n, region_blocks, 3)
    assert outputs_bitwise_equal(reference, out)
    per_region = min(region_blocks, 10)               # 10**6 caps at 10
    assert report.slot_buffer_allocations == min(3, per_region)
    assert report.slot_buffer_allocations <= 3        # never above budget


def test_allocation_bounded_by_slots_not_blocks():
    """One buffer name per slot: with ONE region over 32 blocks the count
    is exactly budget x names, however many blocks execute."""
    n = 32 * B      # 32 blocks in a single region
    _, report = run_once(n, None, 4)
    assert report.slot_buffer_allocations == 4        # 4 slots x 1 name
    assert report.blocks == 32                        # many more blocks


def test_slots_are_exclusive_and_unaliased():
    """Two concurrently leased slots own disjoint memory; a slot's buffer
    is the same object across leases."""
    slot_a = ScratchSlot(0)
    slot_b = ScratchSlot(1)
    frame_a = slot_a.buffer('frame', (16, 7), np.float32)
    frame_b = slot_b.buffer('frame', (16, 7), np.float32)
    a0, a1 = frame_a.ctypes.data, frame_a.ctypes.data + frame_a.nbytes
    b0, b1 = frame_b.ctypes.data, frame_b.ctypes.data + frame_b.nbytes
    assert not (a0 < b1 and b0 < a1)                  # byte extents disjoint
    assert slot_a.buffer('frame', (16, 7), np.float32) is frame_a  # reuse


def test_concurrent_leases_hold_distinct_slots():
    from region_case import ProbeConsumer
    n_blocks = 8
    plan = plan_regions(n_blocks * 8, block_pixels=8)
    barrier = threading.Barrier(2, timeout=30)
    seen_leases = set()
    observed = threading.Event()

    class Pair(ProbeConsumer):
        def consume(self, payload, ctx):
            if ctx.index in (0, 1):
                seen_leases.add(ctx.slot.id)
                if len(seen_leases) == 2:
                    observed.set()
                barrier.wait()
            return super().consume(payload, ctx)

    pool = RegionPool(2)
    try:
        execute_regions(plan, Pair(), fresh_output(n_blocks * 8), pool=pool)
        assert observed.is_set()          # both were leased simultaneously
        assert len(seen_leases) == 2      # and they were distinct slots
    finally:
        pool.close()


def test_poisoned_scratch_does_not_change_results():
    """Arena reuse must be invisible: fill every slot's buffers with NaN
    between runs; a consumer that fully writes before reading produces
    identical bits (canary pinned by the B arm, which writes via out=)."""
    n = 512
    dense, aosoa = aosoa_case(n, 61, 7)
    plan = plan_regions(n, block_pixels=B, region_blocks=2)
    pool = RegionPool(3)
    try:
        first = fresh_output(n)
        execute_regions(plan, b_consumer(aosoa), first, pool=pool)
        for slot in pool._slots._all:
            for buf in slot._buffers.values():
                buf.fill(np.float32('nan'))
        second = fresh_output(n)
        execute_regions(plan, b_consumer(aosoa), second, pool=pool)
        assert outputs_bitwise_equal(first, second)
    finally:
        pool.close()


def test_read_before_write_would_see_poison():
    """Canary liveness: a consumer that READS the frame before writing
    would observe the poison -- proves the previous test has teeth."""
    from region import ExecutionMode
    from region_case import ProbeConsumer

    class ReadOnly(ProbeConsumer):
        mode = ExecutionMode.BLOCK_FANOUT

        def consume(self, payload, ctx):
            frame = ctx.slot.buffer('frame', (ctx.block_capacity, 7),
                                    np.float32)
            if np.isnan(frame[:ctx.stop - ctx.start]).any():
                raise AssertionError('poison visible to a reading consumer')
            return super().consume(payload, ctx)

    plan = plan_regions(4 * 8, block_pixels=8)
    pool = RegionPool(2)
    try:
        execute_regions(plan, ReadOnly(), fresh_output(4 * 8), pool=pool)
        for slot in pool._slots._all:
            for buf in slot._buffers.values():
                buf.fill(np.float32('nan'))
        with pytest.raises(AssertionError):
            execute_regions(plan, ReadOnly(), fresh_output(4 * 8), pool=pool)
    finally:
        pool.close()


def test_shape_rebinding_is_rejected():
    slot = ScratchSlot(0)
    slot.buffer('frame', (16, 7), np.float32)
    with pytest.raises(ScratchShapeError):
        slot.buffer('frame', (15, 7), np.float32)     # tail-shape misuse
    with pytest.raises(ScratchShapeError):
        slot.buffer('frame', (16, 7), np.float64)
    # a distinct name with a different shape is a NEW arena: fine
    slot.buffer('alt', (3,), np.float32)


def test_region_failure_on_shape_rebinding_keeps_type():
    """A consumer that misbinds a scratch shape fails that block with
    ScratchShapeError and the region cancels with the same error."""
    from region_case import ProbeConsumer

    class Misbind(ProbeConsumer):
        def consume(self, payload, ctx):
            ctx.slot.buffer('frame', (ctx.stop - ctx.start, 7), np.float32)
            return super().consume(payload, ctx)

    # 28 rows at b=8 -> blocks 8+8+8+4: the tail rebinds (8,7)->(4,7)
    plan = plan_regions(28, block_pixels=8)
    pool = RegionPool(2)
    try:
        with pytest.raises(ScratchShapeError):
            execute_regions(plan, Misbind(), fresh_output(28), pool=pool)
    finally:
        pool.close()
