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
"""N8-14 common-boundary tests: the planner/pool never special-case a
backend (A/B/C all run through one contract), per-block admission stays
inside the arm, and region execution adds ZERO growth to the N8-10
handle registry (the routed registry-bound note)."""
import numpy as np
import pytest
from test_typed_graph_identity import adversarial_inputs

from region_test_helpers import LW_TEST_THREADS
from region import (ExecutionMode, RegionPool, execute_regions, execute_serial,
                    plan_regions)
from region.consumers import (AosoaBConsumer, DenseKernelConsumer,
                              dense_to_aosoa)
from region_case import (aosoa_case, b_consumer, fresh_output,
                         oracle_consumer, outputs_bitwise_equal)


class AddTwoArrays:
    """A deliberately non-SOLWEIG consumer: proves the boundary accepts
    ANY produce/consume pair (no backend knowledge anywhere)."""

    mode = ExecutionMode.BLOCK_FANOUT

    def __init__(self, source):
        self.source = source

    def produce(self, ctx):
        return self.source[ctx.start:ctx.stop]

    def consume(self, payload, ctx):
        ctx.output[:, ctx.start:ctx.stop] = (payload + payload).T \
            .astype(np.float32)


def test_arbitrary_consumer_through_the_boundary():
    source = np.arange(7 * 40, dtype=np.float32).reshape(40, 7)
    plan = plan_regions(40, block_pixels=8, region_blocks=2)
    out = fresh_output(40)
    pool = RegionPool(2)
    try:
        report = execute_regions(plan, AddTwoArrays(source), out, pool=pool)
        assert np.array_equal(out, (source + source).T)
        assert report.mode == 'block_fanout'
    finally:
        pool.close()


def test_consumer_contract_is_enforced():
    plan = plan_regions(16, block_pixels=8)
    pool = RegionPool(1)
    try:
        with pytest.raises(TypeError):
            execute_regions(plan, object(), fresh_output(16), pool=pool)

        class NoConsume:
            mode = ExecutionMode.BLOCK_FANOUT
            produce = staticmethod(lambda ctx: None)

        with pytest.raises(TypeError):
            execute_regions(plan, NoConsume(), fresh_output(16), pool=pool)

        class BadMode:
            mode = 'block_fanout'          # not an ExecutionMode
            produce = staticmethod(lambda ctx: None)
            consume = staticmethod(lambda payload, ctx: None)

        with pytest.raises(TypeError):
            execute_regions(plan, BadMode(), fresh_output(16), pool=pool)
    finally:
        pool.close()


def test_b_admission_parity_between_serial_and_parallel():
    """A block size that is not lane-aligned is rejected by the B arm's
    OWN admission with the SAME error, serial or parallel -- the
    executor adds nothing and hides nothing."""
    n = 100
    dense, aosoa = aosoa_case(n, 29, 0)
    plan = plan_regions(n, block_pixels=5, region_blocks=4)  # misaligned
    pool = RegionPool(2)
    try:
        with pytest.raises(Exception) as serial_exc:
            execute_serial(plan, b_consumer(aosoa),
                           fresh_output(n))
        with pytest.raises(Exception) as parallel_exc:
            execute_regions(plan, b_consumer(aosoa), fresh_output(n),
                            pool=pool)
        assert type(serial_exc.value) is type(parallel_exc.value)
        assert serial_exc.value.args == parallel_exc.value.args
    finally:
        pool.close()


def test_mode_is_a_parallelism_class_not_a_backend_id():
    """Same MATH, both scheduling classes: the B kernel's single-threaded
    variant (parallel=False) under BLOCK_FANOUT produces the same bits as
    the parallel=True kernel under SELF_PARALLEL -- the declared mode
    changes ONLY how the owner schedules, never the result.

    (An internally-parallel kernel declared BLOCK_FANOUT would violate
    the thread-budget rule -- that misdeclaration is a consumer-contract
    violation the owner cannot detect, like lying about thread safety
    anywhere else. The B arm therefore declares SELF_PARALLEL.)"""
    from region.consumers import _ORDERED
    n = 256
    dense, aosoa = aosoa_case(n, 61, 1)
    plan = plan_regions(n, block_pixels=128, region_blocks=2)

    class FanoutSerialB(AosoaBConsumer):
        mode = ExecutionMode.BLOCK_FANOUT

        def consume(self, payload, ctx):
            rows = payload['rows']
            frame = ctx.slot.buffer('frame', (ctx.block_capacity, 7),
                                    np.float32)[:rows]
            self._lw_primary_b(
                *(payload[name] for name in _ORDERED),
                rows, parallel=False, out=frame)
            ctx.output[:, ctx.start:ctx.stop] = frame.T

    self_parallel = fresh_output(n)
    execute_serial(plan, b_consumer(aosoa), self_parallel)
    pool = RegionPool(4)
    try:
        fanout = fresh_output(n)
        report = execute_regions(plan, FanoutSerialB(aosoa), fanout,
                                 pool=pool)
        assert outputs_bitwise_equal(self_parallel, fanout)
        assert report.mode == 'block_fanout'
    finally:
        pool.close()


def _native_ready():
    from loader.native_handle import (NativeHandleError,
                                      prepare_native_handle)
    try:
        prepare_native_handle()
        return True
    except NativeHandleError:
        return False


@pytest.mark.skipif(not _native_ready(),
                    reason='native artifact unavailable (auto-decline is '
                           'the sanctioned planner behavior)')
def test_region_execution_adds_no_handle_registry_growth():
    """Routed registry-bound note: workers are threads sharing one pid
    and NativeHandle.execute writes no registry entries, so fanout over
    many blocks/regions leaves the N8-10 registry size unchanged."""
    from loader.native_handle import prepare_native_handle, registry_snapshot
    from region.consumers import DenseKernelConsumer, native_handle_reduce
    reduce_block = native_handle_reduce()
    args = adversarial_inputs(512, 61, 6)
    plan = plan_regions(512, block_pixels=128, region_blocks=2)
    before = registry_snapshot()
    pool = RegionPool(4)
    try:
        for _ in range(2):        # two full workflows' worth of regions
            execute_regions(plan, DenseKernelConsumer(reduce_block, args),
                            fresh_output(512), pool=pool)
        assert registry_snapshot() == before
    finally:
        pool.close()


@pytest.mark.skipif(not _native_ready(),
                    reason='native artifact unavailable')
def test_native_execution_error_propagates_through_region():
    """An ADMITTED native failure after launch (NativeExecutionError) is
    never hidden or converted by the region owner."""
    from loader.native_handle import NativeExecutionError
    from region.consumers import DenseKernelConsumer, native_handle_reduce

    class FailingHandle:
        def __init__(self, inner, fail_at):
            self.inner = inner
            self.fail_at = fail_at
            self.calls = 0

        def execute(self, *args, **kwargs):
            self.calls += 1
            if self.calls > self.fail_at:
                raise NativeExecutionError('synthetic post-launch failure')
            return self.inner.execute(*args, **kwargs)

    reduce_block = native_handle_reduce()
    reduce_block._handle = FailingHandle(reduce_block._handle, fail_at=1)
    args = adversarial_inputs(64, 29, 2)
    plan = plan_regions(64, block_pixels=16)
    pool = RegionPool(2)
    try:
        with pytest.raises(NativeExecutionError):
            execute_regions(plan, DenseKernelConsumer(reduce_block, args),
                            fresh_output(64), pool=pool)
    finally:
        pool.close()
