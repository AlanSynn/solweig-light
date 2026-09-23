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
"""N8-14 planner invariants: dispatch size decoupled from the block grid."""
import pytest

from solweig_light._native_dispatch.region import plan_regions


def spans_of(total, block):
    return [(s, min(s + block, total)) for s in range(0, total, block)]


@pytest.mark.parametrize('total,block', [
    (0, 128), (1, 128), (127, 128), (128, 128), (129, 128),
    (1000, 128), (32 * 35, 128), (300, 7),  # b is a free parameter
])
def test_block_grid_is_the_original_serial_loop(total, block):
    plan = plan_regions(total, block_pixels=block)
    assert plan.block_spans() == tuple(spans_of(total, block))
    assert plan.total_blocks == len(spans_of(total, block))


@pytest.mark.parametrize('total,block,region_blocks', [
    (1000, 128, 1), (1000, 128, 3), (1000, 128, 8), (1000, 128, 100),
    (129, 128, 1), (129, 128, 5), (0, 128, 4), (5, 128, 2),
])
def test_regions_partition_the_block_grid_exactly(total, block,
                                                  region_blocks):
    """Regions are unions of whole blocks: ascending, gapless, exact."""
    plan = plan_regions(total, block_pixels=block, region_blocks=region_blocks)
    all_spans = plan.block_spans()
    collected = []
    boundaries = {0}
    for rng in plan.region_block_ranges():
        assert rng.start < rng.stop            # no empty regions
        assert rng.step == 1
        collected.extend(all_spans[i] for i in rng)
    assert collected == list(all_spans)        # exact partition, in order
    for first, last in plan.region_spans():
        boundaries.add(first)
    # every region edge is a block edge (alignment invariant; 0 is the
    # degenerate whole-extent edge for the empty plan)
    block_edges = {s for s, _ in all_spans}
    assert boundaries <= block_edges | {0}


def test_default_is_one_region_over_all_blocks():
    plan = plan_regions(1000)
    assert plan.region_count == 1
    assert plan.region_spans() == ((0, 1000),)


def test_region_pixels_snaps_down_to_whole_blocks():
    # 300 pixels at b=128 -> 2 blocks of 128 + tail; M=256 -> 2 blocks.
    plan = plan_regions(300, block_pixels=128, region_pixels=256)
    assert plan.region_blocks == 2
    assert plan.region_spans() == ((0, 256), (256, 300))
    # M smaller than one block still yields whole blocks (>=1).
    small = plan_regions(300, block_pixels=128, region_pixels=100)
    assert small.region_blocks == 1


def test_dispatch_size_is_decoupled_from_block_size():
    """Same block grid, wildly different dispatch granularities."""
    grid = plan_regions(512, block_pixels=128).block_spans()
    for region_blocks in (1, 2, 3, 4, 99):
        plan = plan_regions(512, block_pixels=128,
                            region_blocks=region_blocks)
        assert plan.block_spans() == grid
        assert plan.block_pixels == 128        # public default meaning kept


def test_tail_block_lives_in_the_owning_region():
    plan = plan_regions(300, block_pixels=128, region_blocks=2)
    assert plan.total_blocks == 3             # 128 + 128 + 44
    assert plan.region_block_ranges() == (range(0, 2), range(2, 3))
    assert plan.region_spans() == ((0, 256), (256, 300))


def test_zero_rows_plan_is_empty():
    plan = plan_regions(0)
    assert plan.total_blocks == 0
    assert plan.region_count == 0
    assert plan.block_spans() == ()
    assert plan.region_spans() == ()


def test_describe_matches_structure():
    plan = plan_regions(300, block_pixels=128, region_blocks=1)
    d = plan.describe()
    assert d['total_rows'] == 300 and d['block_pixels'] == 128
    assert d['total_blocks'] == 3 and d['region_count'] == 3
    assert d['block_spans'] == list(plan.block_spans())


@pytest.mark.parametrize('kwargs', [
    {'total_rows': -1},
    {'total_rows': 1.5},
    {'total_rows': True},
    {'total_rows': 10, 'block_pixels': 0},
    {'total_rows': 10, 'block_pixels': -5},
    {'total_rows': 10, 'region_blocks': 0},
    {'total_rows': 10, 'region_blocks': 1.0},
    {'total_rows': 10, 'region_pixels': 0},
])
def test_validation(kwargs):
    with pytest.raises(ValueError):
        plan_regions(**kwargs)


def test_both_granularities_rejected():
    with pytest.raises(ValueError):
        plan_regions(100, region_blocks=2, region_pixels=256)
