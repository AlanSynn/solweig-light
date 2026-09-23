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
"""N8-14 fork policy (the routed fork-while-locked decision).

Real os.fork probes: the child's inherited pools are poisoned by the
lock-free at-fork hook, use raises ForkedRegionPool, and the child
RE-PREPARES (fresh pool through the cleared table) and reproduces the
parent's bits. One probe forks while a session is ACTIVE -- the exact
fork-while-locked edge from review note N4 -- and must neither deadlock
the child nor disturb the parent's session.

The child is deliberately minimal (pure-Python/numpy consumer, no numba
kernel calls, os._exit) because forked children of a threaded, JIT-loaded
process must not re-enter those runtimes.
"""
import os
import sys
import threading

import numpy as np
import pytest

from solweig_light._native_dispatch.region import (ForkedRegionPool, RegionPool, execute_regions,
                    execute_serial, plan_regions, shared_pool)
from region_case import ProbeConsumer, fresh_output, outputs_bitwise_equal

pytestmark = pytest.mark.skipif(
    not hasattr(os, 'fork'), reason='os.fork unavailable on this platform')


def _probe_consumer():
    return ProbeConsumer()


def test_fork_poisons_and_child_reprepares():
    plan = plan_regions(8 * 8, block_pixels=8)
    pool = RegionPool(2)
    try:
        # give the pool live workers + used scratch before forking
        parent_out = fresh_output(8 * 8)
        execute_regions(plan, _probe_consumer(), parent_out, pool=pool)
        read_fd, write_fd = os.pipe()
        pid = os.fork()
        if pid == 0:
            # ---- child ----
            status = 1
            try:
                try:
                    execute_regions(plan, _probe_consumer(),
                                    fresh_output(8 * 8), pool=pool)
                except ForkedRegionPool:
                    pass
                else:
                    os.write(write_fd, b'NOT-POISONED')
                    os._exit(3)
                fresh = shared_pool(2)          # re-prepare in the child
                child_out = fresh_output(8 * 8)
                execute_regions(plan, _probe_consumer(), child_out,
                                pool=fresh)
                os.write(write_fd, child_out.tobytes())
                status = 0
            finally:
                os._exit(status)
        # ---- parent ----
        os.close(write_fd)
        payload = b''
        while True:
            chunk = os.read(read_fd, 1 << 16)
            if not chunk:
                break
            payload += chunk
        os.close(read_fd)
        _, status = os.waitpid(pid, 0)
        assert os.waitstatus_to_exitcode(status) == 0
        assert payload != b'NOT-POISONED'
        child_out = np.frombuffer(payload, dtype=np.float32).reshape(7, 64)
        assert outputs_bitwise_equal(parent_out, child_out)
        # the parent's pool was NOT poisoned (child edits its own copy)
        assert not pool.poisoned
        again = fresh_output(8 * 8)
        execute_regions(plan, _probe_consumer(), again, pool=pool)
        assert outputs_bitwise_equal(parent_out, again)
    finally:
        pool.close()


def test_fork_while_session_active_neither_deadlocks_nor_disturbs():
    """The N4 edge: fork while a fanout session holds blocks in flight.
    The lock-free child hook must not hang; the parent session completes
    bitwise-correctly."""
    plan = plan_regions(6 * 8, block_pixels=8)
    pool = RegionPool(2)
    entered = threading.Event()
    release = threading.Event()

    class Held(ProbeConsumer):
        def consume(self, payload, ctx):
            if ctx.index == 0:
                entered.set()
                release.wait(timeout=30)    # hold block 0 in flight
            return super().consume(payload, ctx)

    result = {}
    session_done = threading.Event()

    def run_session():
        try:
            out = fresh_output(6 * 8)
            execute_regions(plan, Held(), out, pool=pool)
            result['out'] = out
        except BaseException as exc:      # pragma: no cover - fail loudly
            result['error'] = exc
        finally:
            session_done.set()

    thread = threading.Thread(target=run_session)
    thread.start()
    try:
        assert entered.wait(timeout=30)
        read_fd, write_fd = os.pipe()
        pid = os.fork()
        if pid == 0:
            # ---- child: mid-session fork; STRICTLY lock-free reads of
            # inherited state (the parent's threads may hold the pool
            # lock at the fork instant -- acquiring it here is the
            # deadlock the policy forbids), then a FRESH owner ----
            status = 1
            try:
                if not pool.poisoned:            # plain attribute read
                    os.write(write_fd, b'NOT-POISONED')
                    os._exit(3)
                fresh = RegionPool(2)            # new locks, no registry
                child_out = fresh_output(6 * 8)
                execute_regions(plan, _probe_consumer(), child_out,
                                pool=fresh)
                os.write(write_fd, b'CHILD-CLEAN')
                status = 0
            finally:
                os._exit(status)
        os.close(write_fd)
        payload = b''
        while True:
            chunk = os.read(read_fd, 1 << 16)
            if not chunk:
                break
            payload += chunk
        os.close(read_fd)
        _, status = os.waitpid(pid, 0)
        assert os.waitstatus_to_exitcode(status) == 0
        assert payload == b'CHILD-CLEAN'
        # parent session unaffected: release and check the composition
        release.set()
        assert session_done.wait(timeout=30)
        assert 'error' not in result
        serial = fresh_output(6 * 8)
        execute_serial(plan, ProbeConsumer(), serial)
        assert outputs_bitwise_equal(serial, result['out'])
    finally:
        release.set()
        thread.join(timeout=30)
        pool.close()


def test_child_shared_pool_is_fresh_not_inherited():
    """shared_pool() in the child returns a FRESH owner (table cleared by
    the fork hook) whose fork generation advanced."""
    plan = plan_regions(4 * 8, block_pixels=8)
    pool = RegionPool(2)
    try:
        execute_regions(plan, _probe_consumer(), fresh_output(4 * 8),
                        pool=pool)
        read_fd, write_fd = os.pipe()
        pid = os.fork()
        if pid == 0:
            status = 1
            try:
                fresh = shared_pool(2)
                os.write(write_fd, b'FRESH' if fresh is not pool else
                         b'INHERITED')
                os.write(write_fd, b'|GEN'
                         if fresh.fork_generation != pool.fork_generation
                         else b'|SAMEGEN')
                status = 0
            finally:
                os._exit(status)
        os.close(write_fd)
        payload = b''
        while True:
            chunk = os.read(read_fd, 1 << 16)
            if not chunk:
                break
            payload += chunk
        os.close(read_fd)
        _, status = os.waitpid(pid, 0)
        assert os.waitstatus_to_exitcode(status) == 0
        assert payload == b'FRESH|GEN'
    finally:
        pool.close()
