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
"""N8-14 cancellation ownership: first-error-in-canonical-order, type
preservation, no starts after cancel, no silent partial results."""
import threading

import numpy as np
import pytest

from region import (ExecutionMode, RegionPool, execute_regions,
                    execute_serial, plan_regions)
from region_case import ProbeConsumer, fresh_output


def failure(exc):
    return getattr(exc, '_solweig_region_failure', {})


def test_produce_error_cancels_region_and_propagates_type():
    plan = plan_regions(16 * 8, block_pixels=8)      # 16 blocks
    boom = KeyError('block-5-payload')
    consumer = ProbeConsumer(fail_produce={5: boom})
    pool = RegionPool(3)
    try:
        out = fresh_output(16 * 8)
        with pytest.raises(KeyError) as caught:
            execute_regions(plan, consumer, out, pool=pool)
        assert caught.value is boom             # same object, type intact
        facts = failure(boom)
        assert facts['first_failing_block'] == 5
        assert facts['started_after_cancel'] == 0
        assert max(facts['blocks_started']) <= 15
    finally:
        pool.close()


def test_consume_error_cancels_region():
    plan = plan_regions(16 * 8, block_pixels=8)
    boom = RuntimeError('native entry failed after launch')
    consumer = ProbeConsumer(fail_consume={9: boom})
    pool = RegionPool(2)
    try:
        with pytest.raises(RuntimeError) as caught:
            execute_regions(plan, consumer, fresh_output(16 * 8), pool=pool)
        assert caught.value is boom
        assert failure(boom)['started_after_cancel'] == 0
    finally:
        pool.close()


def test_first_error_is_canonical_not_wallclock():
    """Block 7 fails immediately; block 2 fails LATER in wall time (it
    sleeps first). The caller must still see block 2's error: canonical
    order = ascending block index, the error a serial loop hits first."""
    plan = plan_regions(16 * 8, block_pixels=8)
    early = ValueError('high-index fast failure')
    late = ValueError('low-index slow failure')

    class Inverted(ProbeConsumer):
        def produce(self, ctx):
            if ctx.index == 7:
                raise early
            if ctx.index == 2:
                import time
                time.sleep(0.25)        # fail well AFTER block 7 cancelled
                raise late
            return super().produce(ctx)

    pool = RegionPool(4)
    try:
        with pytest.raises(ValueError) as caught:
            execute_regions(plan, Inverted(),
                            fresh_output(16 * 8), pool=pool)
        assert caught.value is late
        assert failure(late)['first_failing_block'] == 2
        assert set(failure(late)['failing_blocks']) == {2, 7}
    finally:
        pool.close()


def test_unsupported_input_passes_through_unchanged():
    """UnsupportedInput must keep its TYPE (a TypeError) so the real
    dispatcher's per-block fallback decision is unchanged."""
    from lw_b_control import UnsupportedInput
    boom = UnsupportedInput('sh: gang mismatch')
    plan = plan_regions(8 * 4, block_pixels=8)
    pool = RegionPool(2)
    try:
        with pytest.raises(UnsupportedInput) as caught:
            execute_regions(plan, ProbeConsumer(fail_produce={1: boom}),
                            fresh_output(8 * 4), pool=pool)
        assert caught.value is boom
        assert isinstance(boom, TypeError)
    finally:
        pool.close()


def test_native_loud_error_never_becomes_fallback():
    from loader.native_handle import NativeExecutionError
    boom = NativeExecutionError('admitted native invocation failed')
    plan = plan_regions(8 * 4, block_pixels=8)
    pool = RegionPool(2)
    try:
        with pytest.raises(NativeExecutionError) as caught:
            execute_regions(plan, ProbeConsumer(fail_consume={2: boom}),
                            fresh_output(8 * 4), pool=pool)
        assert caught.value is boom     # loud, not swallowed, not converted
    finally:
        pool.close()


def test_no_block_starts_after_cancel():
    """With a barrier holding two blocks in flight, a third failing block
    cancels the region; every later block must be skipped, never run."""
    n_blocks = 12
    plan = plan_regions(n_blocks * 8, block_pixels=8, region_blocks=12)
    barrier = threading.Barrier(3, timeout=30)   # blocks 0,1 + releaser
    boom = OSError('boom')

    class Held(ProbeConsumer):
        def consume(self, payload, ctx):
            if ctx.index in (0, 1):
                barrier.wait()
            return super().consume(payload, ctx)

    consumer = Held(fail_produce={6: boom})
    pool = RegionPool(2)
    released = threading.Event()

    def releaser():
        barrier.wait(timeout=30)     # third party opens the barrier
        released.set()

    thread = threading.Thread(target=releaser)
    thread.start()
    try:
        with pytest.raises(OSError):
            execute_regions(plan, consumer, fresh_output(n_blocks * 8),
                            pool=pool)
        # join BEFORE asserting: the barrier synchronizes the blocks, but
        # the releaser's event set races the main thread's wakeup
        thread.join(timeout=30)
        assert released.is_set()
        facts = failure(boom)
        started = set(facts['blocks_started'])
        assert facts['started_after_cancel'] == 0
        # blocks 2..5 may legitimately have run while 0,1 were held at the
        # barrier and before block 6's failure was recorded; but nothing
        # past the failing block ever starts
        assert 6 in started
        assert not any(index > 6 for index in started)
    finally:
        thread.join()
        pool.close()


def test_serial_and_parallel_raise_identically():
    plan = plan_regions(8 * 6, block_pixels=8)
    boom = ZeroDivisionError('divide by stored pi')
    serial = ProbeConsumer(fail_consume={3: boom})
    parallel = ProbeConsumer(fail_consume={3: boom})
    with pytest.raises(ZeroDivisionError) as serial_exc:
        execute_serial(plan, serial, fresh_output(8 * 6))
    pool = RegionPool(4)
    try:
        with pytest.raises(ZeroDivisionError) as parallel_exc:
            execute_regions(plan, parallel, fresh_output(8 * 6), pool=pool)
        assert type(serial_exc.value) is type(parallel_exc.value)
        assert serial_exc.value.args == parallel_exc.value.args
    finally:
        pool.close()


def test_self_parallel_cancellation_stops_dispatch():
    class SelfParallel(ProbeConsumer):
        mode = ExecutionMode.SELF_PARALLEL

    boom = ValueError('numba arm failed mid-region')
    plan = plan_regions(8 * 8, block_pixels=8)
    consumer = SelfParallel(fail_produce={4: boom})
    pool = RegionPool(3)
    try:
        with pytest.raises(ValueError) as caught:
            execute_regions(plan, consumer, fresh_output(8 * 8), pool=pool)
        assert caught.value is boom
        assert failure(boom)['first_failing_block'] == 4
        # serial semantics: blocks 5.. never started
        assert failure(boom)['blocks_started'] == (0, 1, 2, 3, 4)
    finally:
        pool.close()


def test_structural_failure_before_any_block():
    plan = plan_regions(64, block_pixels=16)
    consumer = ProbeConsumer()
    pool = RegionPool(2)
    try:
        with pytest.raises(ValueError):
            execute_regions(plan, consumer,
                            np.zeros((7, 63), dtype=np.float32), pool=pool)
        assert consumer.started == []       # nothing dispatched
        with pytest.raises(TypeError):
            execute_regions(plan, consumer, 'not-an-array', pool=pool)
        assert consumer.started == []
        with pytest.raises(ValueError):
            execute_regions(plan, consumer,
                            np.zeros((6, 64), dtype=np.float32), pool=pool)
        assert consumer.started == []
    finally:
        pool.close()


def test_close_during_active_session_is_refused():
    plan = plan_regions(8 * 4, block_pixels=8)
    pool = RegionPool(2)
    from region import RegionExecutorError

    class Closer(ProbeConsumer):
        def consume(self, payload, ctx):
            if ctx.index == 0:
                with pytest.raises(RegionExecutorError):
                    self.pool.close()
            return super().consume(payload, ctx)

    closer = Closer()
    closer.pool = pool
    try:
        execute_regions(plan, closer, fresh_output(8 * 4), pool=pool)
        assert 0 in closer.started
    finally:
        pool.close()
