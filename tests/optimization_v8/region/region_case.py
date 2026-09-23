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
"""Shared case builders for the N8-14 region tests.

Everything heavy is imported READ-ONLY: the frozen N8-04 oracle and its
adversarial input grid (``tests/optimization_v8/reference``), never
modified. Bitwise comparisons are uint32 views, matching the frozen
suite's convention.
"""
import threading
import time

import numpy as np

from lw_reference_oracle import lw_primary_reference
from test_typed_graph_identity import adversarial_inputs

from solweig_light._native_dispatch.region import ExecutionMode
from solweig_light._native_dispatch.region.consumers import DenseKernelConsumer, AosoaBConsumer, \
    dense_to_aosoa

F32 = np.float32


def oracle_reduce(payload, frame):
    """reduce_block adapter: the frozen oracle (arm A)."""
    return lw_primary_reference(
        payload['sh'], payload['vs'], payload['vb'],
        payload['sun'], payload['shade'],
        payload['solid'], payload['sine'], payload['cosine'],
        payload['directions'], payload['gate'], payload['solar_gate'],
        payload['sky_down'], payload['sky_side'],
        payload['surface_sun'], payload['surface_sh'],
        payload['lup'], payload['reflection_factor'])


def oracle_whole(args, n):
    """Whole-extent oracle call (the composition's bitwise target)."""
    with np.errstate(all='ignore'):
        return lw_primary_reference(
            args['sh'], args['vs'], args['vb'], args['sun'], args['shade'],
            args['solid'], args['sine'], args['cosine'],
            args['directions'], args['gate'], args['solar_gate'],
            args['sky_down'], args['sky_side'],
            args['surface_sun'], args['surface_sh'],
            args['lup'], args['reflection_factor'])


def oracle_consumer(args) -> DenseKernelConsumer:
    return DenseKernelConsumer(oracle_reduce, args)


def aosoa_case(n_rows, patches, seed, width=8):
    """(args_dense, args_aosoa) for the same underlying adversarial case.

    ``args_dense`` feeds arm A/C; ``args_aosoa`` repacks the identical
    float32 bits into the N8-11 lane layout and feeds arm B (padding
    lanes poisoned -- never read).
    """
    dense = adversarial_inputs(n_rows, patches, seed)
    aosoa = dict(dense)
    aosoa['sh'] = dense_to_aosoa(dense['sh'], width).view(np.uint32)
    aosoa['vs'] = dense_to_aosoa(dense['vs'], width).view(np.uint32)
    aosoa['vb'] = dense_to_aosoa(dense['vb'], width).view(np.uint32)
    aosoa['sun'] = dense_to_aosoa(dense['sun'], width)
    aosoa['shade'] = dense_to_aosoa(dense['shade'], width)
    return dense, aosoa


def b_consumer(aosoa_args, width=8) -> AosoaBConsumer:
    return AosoaBConsumer(aosoa_args, width=width)


def fresh_output(n_rows):
    return np.zeros((7, n_rows), dtype=np.float32)


def u32(frame):
    return np.ascontiguousarray(frame).view(np.uint32)


def outputs_bitwise_equal(a, b):
    return np.array_equal(u32(a), u32(b))


class ProbeConsumer:
    """Instrumented BLOCK_FANOUT consumer for mechanics tests.

    Records per-block facts (slot id, frame address, thread, order) and
    optionally sleeps in consume to force overlap, blocks on events to
    order wall-clock behavior, or raises at chosen block indices.
    ``reads_scratch`` turns on the read-before-write poison detector.
    """

    mode = ExecutionMode.BLOCK_FANOUT

    def __init__(self, *, fail_produce=None, fail_consume=None,
                 delay=0.0, barrier=None, release=None, compute=None):
        self.fail_produce = dict(fail_produce or {})
        self.fail_consume = dict(fail_consume or {})
        self.delay = delay
        self.barrier = barrier          # (event, count) -- block in consume
        self.release = release          # event that unblocks the barrier
        self.compute = compute or (lambda ctx: None)
        self.events = []                # (phase, index, slot_id, addr, tid)
        self.started = []
        self.scratch_reads = []

    def _note(self, phase, ctx, frame):
        self.events.append((phase, ctx.index, ctx.slot.id,
                            frame.ctypes.data, threading.get_ident()))

    def produce(self, ctx):
        self.started.append(ctx.index)
        if ctx.index in self.fail_produce:
            raise self.fail_produce[ctx.index]
        return None

    def consume(self, payload, ctx):
        frame = ctx.slot.buffer('frame', (ctx.block_capacity, 7), F32)
        self._note('consume', ctx, frame)
        if ctx.index in self.fail_consume:
            raise self.fail_consume[ctx.index]
        if self.delay:
            time.sleep(self.delay)
        if self.barrier is not None and ctx.index in self.barrier[1]:
            self.barrier[0].wait(timeout=30)
        self.compute(ctx)
        # deterministic per-block pattern write into OUR span only
        rng = np.random.default_rng(ctx.index)
        rows = ctx.stop - ctx.start
        frame[:rows] = rng.standard_normal((rows, 7)).astype(F32)
        ctx.output[:, ctx.start:ctx.stop] = frame[:rows].T
