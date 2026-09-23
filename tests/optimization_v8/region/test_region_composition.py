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
"""N8-14 composition exactness: parallel region execution == serial
composition, bitwise, across region shapes (single-block, tail,
multi-region), budgets and all three consumer arms (A oracle, B Numba,
C native handle). Comparisons are uint32 views (frozen-suite
convention). No timing is taken here.
"""
import numpy as np
import pytest
from test_typed_graph_identity import adversarial_inputs

from region_test_helpers import LW_TEST_THREADS
from solweig_light._native_dispatch.region import RegionPool, execute_regions, execute_serial, plan_regions
from region_case import (aosoa_case, b_consumer, fresh_output,
                         oracle_consumer, oracle_whole, outputs_bitwise_equal)

B = 128  # the public default execution block


@pytest.mark.parametrize('n,region_blocks', [
    (1, 1), (127, 1), (128, 1),                    # single block
    (129, 1), (300, 1), (300, 2), (300, 3),        # tail in an owning region
    (512, 1), (512, 2), (512, 3), (512, 99),       # multi-region, oversized R
])
@pytest.mark.parametrize('budget', [1, 2, 4])
@pytest.mark.parametrize('seed', [0, 1])
def test_parallel_equals_serial_and_whole_call(n, region_blocks, budget,
                                               seed):
    """A-arm gate: fanout composition == serial composition == one
    whole-extent oracle call, bitwise, for every shape."""
    args = adversarial_inputs(n, 61, seed)
    plan = plan_regions(n, block_pixels=B, region_blocks=region_blocks)
    serial_out = fresh_output(n)
    execute_serial(plan, oracle_consumer(args), serial_out)
    pool = RegionPool(budget)
    try:
        parallel_out = fresh_output(n)
        report = execute_regions(plan, oracle_consumer(args), parallel_out,
                                 pool=pool)
        assert outputs_bitwise_equal(serial_out, parallel_out)
        assert outputs_bitwise_equal(parallel_out,
                                     oracle_whole(args, n).T)
        assert report.blocks == plan.total_blocks
        assert report.blocks_started == plan.total_blocks
        assert report.max_in_flight <= budget
    finally:
        pool.close()


@pytest.mark.parametrize('n,region_blocks', [(512, 1), (512, 2), (300, 1)])
@pytest.mark.parametrize('seed', [0, 3])
def test_b_self_parallel_composition(n, region_blocks, seed):
    """B-arm gate: SELF_PARALLEL region execution == serial composition ==
    one whole lw_primary_b call, bitwise (W-aligned blocks)."""
    from solweig_light._native_dispatch.lw_b_control import lw_primary_b
    dense, aosoa = aosoa_case(n, 61, seed)
    plan = plan_regions(n, block_pixels=B, region_blocks=region_blocks)
    serial_out = fresh_output(n)
    execute_serial(plan, b_consumer(aosoa), serial_out)
    pool = RegionPool(LW_TEST_THREADS)
    try:
        parallel_out = fresh_output(n)
        report = execute_regions(plan, b_consumer(aosoa), parallel_out,
                                 pool=pool)
        assert outputs_bitwise_equal(serial_out, parallel_out)
        # whole-extent single call over the same global AoSoA payload
        whole = np.zeros((n, 7), dtype=np.float32)
        lw_primary_b(aosoa['sh'], aosoa['vs'], aosoa['vb'],
                     aosoa['sun'], aosoa['shade'],
                     aosoa['solid'], aosoa['sine'], aosoa['cosine'],
                     aosoa['directions'], aosoa['gate'],
                     aosoa['solar_gate'], aosoa['sky_down'],
                     aosoa['sky_side'], aosoa['surface_sun'],
                     aosoa['surface_sh'], aosoa['lup'],
                     aosoa['reflection_factor'], n, parallel=True,
                     out=whole)
        assert outputs_bitwise_equal(parallel_out, whole.T)
        assert report.mode == 'self_parallel'
        assert report.max_in_flight == 1     # owner quiesced; kernel owns it
    finally:
        pool.close()


def native_available():
    from solweig_light._native_dispatch.native_handle import prepare_native_handle, \
        NativeHandleError
    try:
        prepare_native_handle()
        return True
    except NativeHandleError:
        return False


@pytest.mark.parametrize('n,region_blocks', [(300, 1), (300, 2), (257, 3)])
def test_c_native_fanout_composition(n, region_blocks):
    """C-arm gate: BLOCK_FANOUT over the N8-10 native handle == serial
    composition == one whole handle call, bitwise."""
    if not native_available():
        pytest.skip('native artifact unavailable in this environment '
                    '(auto-decline is the sanctioned planner behavior)')
    from solweig_light._native_dispatch.region.consumers import native_handle_reduce, DenseKernelConsumer
    from test_typed_graph_identity import adversarial_inputs
    reduce_block = native_handle_reduce()
    args = adversarial_inputs(n, 61, 2)
    consumer = DenseKernelConsumer(reduce_block, args)
    plan = plan_regions(n, block_pixels=B, region_blocks=region_blocks)
    serial_out = fresh_output(n)
    execute_serial(plan, consumer, serial_out)
    pool = RegionPool(4)
    try:
        parallel_out = fresh_output(n)
        report = execute_regions(plan, DenseKernelConsumer(reduce_block,
                                                           args),
                                 parallel_out, pool=pool)
        assert outputs_bitwise_equal(serial_out, parallel_out)
        whole = reduce_block.handle.execute(
            args['sh'], args['vs'], args['vb'], args['sun'], args['shade'],
            args['solid'], args['sine'], args['cosine'],
            args['directions'], args['gate'], args['solar_gate'],
            args['sky_down'], args['sky_side'],
            args['surface_sun'], args['surface_sh'], args['lup'],
            args['reflection_factor'])
        assert outputs_bitwise_equal(parallel_out, whole.T)
        assert report.mode == 'block_fanout'
    finally:
        pool.close()


@pytest.mark.parametrize('seed', [0])
def test_all_three_arms_agree_bitwise(seed):
    """Cross-arm: A (oracle) == B (Numba) == C (native) through the same
    region boundary on the same adversarial case."""
    n = 256
    dense, aosoa = aosoa_case(n, 61, seed)
    plan = plan_regions(n, block_pixels=B, region_blocks=2)
    outs = {}
    outs['A'] = fresh_output(n)
    execute_serial(plan, oracle_consumer(dense), outs['A'])
    outs['B'] = fresh_output(n)
    execute_serial(plan, b_consumer(aosoa), outs['B'])
    assert outputs_bitwise_equal(outs['A'], outs['B'])
    if native_available():
        from solweig_light._native_dispatch.region.consumers import native_handle_reduce, \
            DenseKernelConsumer
        reduce_block = native_handle_reduce()
        outs['C'] = fresh_output(n)
        execute_serial(plan, DenseKernelConsumer(reduce_block, dense),
                       outs['C'])
        assert outputs_bitwise_equal(outs['A'], outs['C'])


def test_repeated_executions_on_one_pool_are_stable():
    """One shared owner, many region calls: scratch reuse across regions
    and timesteps never leaks bits between spans."""
    args = adversarial_inputs(512, 61, 4)
    plan = plan_regions(512, block_pixels=B, region_blocks=2)
    pool = RegionPool(3)
    try:
        first = fresh_output(512)
        execute_regions(plan, oracle_consumer(args), first, pool=pool)
        for _ in range(3):
            again = fresh_output(512)
            execute_regions(plan, oracle_consumer(args), again, pool=pool)
            assert outputs_bitwise_equal(first, again)
    finally:
        pool.close()
