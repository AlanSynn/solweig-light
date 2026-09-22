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
"""N8-14 pool-budget gates: never more than N threads observed, one
owner, exclusive sessions, bounded registry, runtime-derived budget.

The concurrency assertions are functional (liveness + bound), NOT timed
benchmarks: the small sleeps only guarantee overlap so the bound is
actually exercised.
"""
import threading

import pytest
from solweig_light.runtime import RuntimeOptions, runtime_options

from region import (MAX_POOL_BUDGET_SLOTS, ExecutionMode, ForkedRegionPool,
                    PoolRegistryBound, PoolSessionConflict, RegionPool,
                    ClosedRegionPool, execute_regions, plan_regions,
                    reset_pools_for_tests, resolve_budget, shared_pool)
from region_case import ProbeConsumer, fresh_output


def plan_blocks(n_blocks, blocks_per_region=None):
    return plan_regions(n_blocks * 8, block_pixels=8,
                        region_blocks=blocks_per_region or n_blocks)


@pytest.mark.parametrize('budget', [1, 2, 4])
def test_max_in_flight_never_exceeds_budget(budget):
    """Fanout with overlapping blocks: concurrency observed <= N, and
    for N >= 2 parallelism actually happens (>= 2)."""
    plan = plan_blocks(16)
    consumer = ProbeConsumer(delay=0.01)
    pool = RegionPool(budget)
    try:
        report = execute_regions(plan, consumer, fresh_output(16 * 8),
                                 pool=pool)
        assert report.max_in_flight <= budget
        if budget >= 2:
            assert report.max_in_flight >= 2
        assert report.pool_workers == budget - 1
    finally:
        pool.close()


def test_thread_count_delta_bounded_by_budget_minus_one():
    """Live-thread census from inside the blocks: the owner adds at most
    N-1 threads beyond the submitting process's baseline."""
    plan = plan_blocks(12)
    baseline = [None]
    observed = []

    class Census(ProbeConsumer):
        def consume(self, payload, ctx):
            if baseline[0] is None:
                baseline[0] = threading.active_count()  # first block: 1 worker + caller
            observed.append(threading.active_count())
            return super().consume(payload, ctx)

    pool = RegionPool(3)
    try:
        execute_regions(plan, Census(delay=0.01), fresh_output(12 * 8),
                        pool=pool)
        assert max(observed) - min(observed) <= 3 - 1
        assert max(observed) <= baseline[0] + 3 - 1
    finally:
        pool.close()


def test_budget_one_spawns_no_threads():
    plan = plan_blocks(8)
    before = threading.active_count()
    pool = RegionPool(1)
    try:
        report = execute_regions(plan, ProbeConsumer(), fresh_output(8 * 8),
                                 pool=pool)
        assert report.pool_workers == 0
        assert threading.active_count() == before
        assert report.max_in_flight == 1
    finally:
        pool.close()


def test_self_parallel_owner_is_quiescent():
    """SELF_PARALLEL grants the budget to the consumer's own threading
    layer: the owner runs one block at a time and spawns no workers."""
    plan = plan_blocks(10)

    class Self(ProbeConsumer):
        mode = ExecutionMode.SELF_PARALLEL

    pool = RegionPool(4)
    try:
        report = execute_regions(plan, Self(), fresh_output(10 * 8),
                                 pool=pool)
        assert report.max_in_flight == 1
        assert report.pool_workers == 0
    finally:
        pool.close()


def test_nested_submission_from_inside_a_block_is_refused():
    plan = plan_blocks(8)
    pool = RegionPool(2)

    class Nested(ProbeConsumer):
        def consume(self, payload, ctx):
            if ctx.index == 0:
                inner = ProbeConsumer()
                with pytest.raises(PoolSessionConflict):
                    execute_regions(plan_blocks(2), inner, fresh_output(16),
                                    pool=pool)
            return super().consume(payload, ctx)

    try:
        execute_regions(plan, Nested(), fresh_output(8 * 8), pool=pool)
    finally:
        pool.close()


def test_concurrent_second_submission_is_refused():
    plan = plan_blocks(8)
    pool = RegionPool(2)
    entered = threading.Barrier(2, timeout=30)
    release = threading.Event()
    conflicts = []

    class Held(ProbeConsumer):
        def consume(self, payload, ctx):
            if ctx.index == 0:
                entered.wait()          # sync with the second submitter
                release.wait(timeout=30)  # keep the session ACTIVE
            return super().consume(payload, ctx)

    def second():
        try:
            entered.wait(timeout=30)
            execute_regions(plan_blocks(2), ProbeConsumer(),
                            fresh_output(16), pool=pool)
        except PoolSessionConflict as exc:
            conflicts.append(exc)

    thread = threading.Thread(target=second)
    thread.start()
    try:
        execute_regions(plan, Held(), fresh_output(8 * 8), pool=pool)
        release.set()
        thread.join(timeout=30)
        assert len(conflicts) == 1
    finally:
        release.set()
        thread.join(timeout=30)
        pool.close()


def test_shared_pool_identity_and_replacement():
    reset_pools_for_tests()
    a = shared_pool(2)
    b = shared_pool(2)
    assert a is b                      # ONE owner per (pid, budget)
    a.close()
    c = shared_pool(2)
    assert c is not a and c.budget == 2
    c.close()
    with pytest.raises(ClosedRegionPool):
        a.execute_regions(plan_blocks(2), ProbeConsumer(),
                          fresh_output(16))
    reset_pools_for_tests()


def test_registry_bound_is_loud():
    reset_pools_for_tests()
    pools = []
    try:
        for budget in range(1, MAX_POOL_BUDGET_SLOTS + 1):
            pools.append(shared_pool(budget))
        with pytest.raises(PoolRegistryBound):
            shared_pool(MAX_POOL_BUDGET_SLOTS + 1)
        # the existing budgets still work; the bound caps DISTINCT live
        # budgets, not reuse
        assert shared_pool(2) is pools[1]
    finally:
        reset_pools_for_tests()


def _live_tracked():
    import region.region_pool as rp
    with rp._POOLS_LOCK:
        return list(rp._LIVE_POOLS)


def test_live_pool_tracked_exactly_once():
    """One creation, ONE entry: the constructor's dedup-guarded
    _track_pool is the single registration point (regression: shared_pool
    used to append again, leaving a duplicate)."""
    reset_pools_for_tests()
    try:
        pool = shared_pool(2)
        tracked = _live_tracked()
        assert tracked.count(pool) == 1
        assert sum(p is pool for p in tracked) == 1
    finally:
        reset_pools_for_tests()


def test_closed_pools_leave_the_live_list():
    """close() untracks; _LIVE_POOLS holds LIVE pools only, and repeated
    create/close/shutdown cycles never grow it (regression: a duplicated
    entry survived close and accumulated across shutdown cycles)."""
    reset_pools_for_tests()
    try:
        for _cycle in range(5):
            pool = shared_pool(2)
            pool.close()
            assert all(p is not pool for p in _live_tracked())
            from region import shutdown_all_pools
            shutdown_all_pools()
            tracked = _live_tracked()
            assert not tracked            # everything closed -> empty
            assert all(not p.closed and not p.poisoned for p in tracked)
    finally:
        reset_pools_for_tests()


def test_resolve_budget_rules():
    assert resolve_budget(1) == 1
    assert resolve_budget(4) == 4
    for bad in (0, -1, True, 1.5, '4'):
        with pytest.raises(ValueError):
            resolve_budget(bad)
    with pytest.raises(ValueError):
        resolve_budget(10 ** 6)          # exceeds total CPUs
    # default = the existing runtime thread budget
    with runtime_options(RuntimeOptions(cpu_budget=4, threads_per_worker=3)):
        assert resolve_budget() == 3
    with runtime_options(RuntimeOptions(cpu_budget=2, threads_per_worker=2)):
        assert shared_pool() is shared_pool(2)
    reset_pools_for_tests()


def test_forked_pool_object_is_refused_without_os_fork():
    """Direct poisoning (what the fork hook does) refuses service."""
    pool = RegionPool(2)
    pool._poisoned = True
    with pytest.raises(ForkedRegionPool):
        pool.execute_regions(plan_blocks(2), ProbeConsumer(),
                             fresh_output(16))
