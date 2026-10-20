"""Allocation bounds added above frozen pre-batch admission calibrations."""
import pytest

from solweig_light import runtime_memory as rm


@pytest.mark.parametrize('rows,cols,patches,block,threads', [
    (600, 600, 153, 128, 1), (600, 600, 609, 128, 8),
    (7, 11, 7, 13, 8), (1, 1, 1, 1, 128),
    (1024, 1024, 153, 32768, 4),
])
def test_full_allocation_bound(rows, cols, patches, block, threads):
    shape = rm.TileShapeDescriptor(rows, cols, patches, 12, block)
    size = min(block, rows * cols)
    active = min(threads, (rows * cols + block - 1) // block)
    # Three uint32 payloads, two uint8/bool masks, seven-f32 frame,
    # ten-f32 reducer accumulator. Width-eight rounding bounds LW and SW.
    lw = active * (14 * ((size+7)//8*8) * patches + 28*size + 40)
    gvf = min(threads, (rows+31)//32) * 96 * min(rows, 32) * cols
    finishing = 16*4*rows*cols
    assert rm.execution_overhead(shape, threads) == (
        56*rows*cols + max(lw, gvf, finishing) + 17*patches + 8)


def test_threads_change_only_new_scratch_above_same_frozen_base():
    shape = rm.TileShapeDescriptor(1024, 1024, 153, 12, 128)
    one = rm.simulation_reservation(shape, threads_per_worker=1, gdal_cache_bytes=0)
    eight = rm.simulation_reservation(shape, threads_per_worker=8, gdal_cache_bytes=0)
    assert one.live_array_bytes == eight.live_array_bytes == 3*826_736_640 + 56*shape.pixels
    assert one.total_bytes - rm.execution_overhead(shape, 1) == (
        eight.total_bytes - rm.execution_overhead(shape, 8))
    assert eight.total_bytes >= one.total_bytes
    assert eight.decoded_block_bytes - one.decoded_block_bytes == (
        rm.execution_overhead(shape, 8) - rm.execution_overhead(shape, 1))


def test_monotone_threads_and_bounded_owner_count():
    shape = rm.TileShapeDescriptor(65, 64, 153, 12, 128)
    totals = [rm.execution_overhead(shape, h) for h in (1, 2, 4, 8, 32, 128)]
    assert totals == sorted(totals)
    assert rm.execution_overhead(shape, 128) == rm.execution_overhead(shape, 100_000)


def test_finishing_overlap_is_charged_when_larger_than_worker_scratch():
    shape = rm.TileShapeDescriptor(600, 600, 153, 12, 128)
    assert rm._execution_overhead_components(shape, 1) == (56*600*600, 64*600*600 + 17*153 + 8)
    assert rm._execution_overhead_components(shape, 8) == (56*600*600, 64*600*600 + 17*153 + 8)


def test_phase_planner_prices_requested_native_threads():
    job = rm.PhaseJob(rm.PHASE_SIMULATION, 600, 600)
    plan = rm.plan_phase_admission([job], budget_bytes=10*1024**3,
                                   gdal_cache_bytes=0, threads_per_worker=8)
    direct = rm.simulation_reservation(job.shape, gdal_cache_bytes=0, threads_per_worker=8)
    assert plan.reservations == (direct,)
    assert plan.native_threads == 8


def test_large_block_and_thread_scratch_rejects_before_execution():
    job = rm.PhaseJob(rm.PHASE_SIMULATION, 1024, 1024, block_pixels=32768)
    one = rm.simulation_reservation(job.shape, threads_per_worker=1, gdal_cache_bytes=0)
    eight = rm.simulation_reservation(job.shape, threads_per_worker=8, gdal_cache_bytes=0)
    assert eight.total_bytes > one.total_bytes
    with pytest.raises(rm.ResourceAdmissionError, match='queueing cannot make'):
        rm.plan_phase_admission([job], budget_bytes=one.total_bytes,
                                parent_footprint_bytes=0, gdal_cache_bytes=0,
                                threads_per_worker=8, policy='queue')


@pytest.mark.parametrize('threads', [0, -1, True, 1.5])
def test_invalid_native_thread_counts_refuse(threads):
    shape = rm.TileShapeDescriptor(600, 600)
    with pytest.raises(ValueError, match='threads_per_worker'):
        rm.execution_overhead(shape, threads)
    with pytest.raises(ValueError, match='threads_per_worker'):
        rm.simulation_reservation(shape, threads_per_worker=threads)


@pytest.mark.parametrize('patches', [1, 153, 609])
@pytest.mark.parametrize('threads', [1, 2, 8])
def test_group_builder_peak_is_charged_once_and_covers_small_block(patches, threads):
    shape = rm.TileShapeDescriptor(1, 8, patches, 12, 8)
    # Only one execution block exists: shared metadata must not acquire a
    # threads multiplier. Even all-unique coefficients allocate build arrays.
    group_peak = 8*(patches + 1) + 8*patches + patches
    old_peak = max(14*8*patches + 28*8 + 40, 96*8, 64*8)
    assert rm.execution_overhead(shape, threads) == 56*8 + old_peak + group_peak
    grouped_sw_live = 14*8*patches + 32 + 16*patches + 8
    assert rm._execution_overhead_components(shape, threads)[1] >= grouped_sw_live


def test_group_charge_does_not_reduce_preexisting_reserves():
    shape = rm.TileShapeDescriptor(1, 8, 609, 12, 8)
    reserve = rm.simulation_reservation(shape, threads_per_worker=1, gdal_cache_bytes=0)
    assert reserve.decoded_block_bytes == 14*8*609 + 28*8 + 40 + 17*609 + 8
    # Previously uncharged numerical build peak is exactly 10,361 B at P609.
    assert 17*609 + 8 == 10_361
