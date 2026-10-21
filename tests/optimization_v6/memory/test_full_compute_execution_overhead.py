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
    # Three uint32 payloads, two bool masks, seven-f32 frame, and either
    # ten scalar accumulators or eleven rows of 32 for private LW gangs.
    accumulator = 11*32*4 if rows*cols >= block and block % 32 == 0 else 40
    lw = active * (14 * ((size+7)//8*8) * patches + 28*size + accumulator)
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


@pytest.mark.parametrize('resident_lw_masks', [False, True])
def test_phase_planner_prices_requested_native_threads(resident_lw_masks):
    job = rm.PhaseJob(rm.PHASE_SIMULATION, 600, 600)
    plan = rm.plan_phase_admission([job], budget_bytes=10*1024**3,
                                   gdal_cache_bytes=0, threads_per_worker=8,
                                   resident_lw_masks=resident_lw_masks)
    direct = rm.simulation_reservation(job.shape, gdal_cache_bytes=0, threads_per_worker=8,
                                       resident_lw_masks=resident_lw_masks)
    assert plan.reservations == (direct,)
    assert plan.native_threads == 8


@pytest.mark.parametrize('rows,cols,mask_bytes', [
    (1, 33, 9_792), (600, 600, 55_080_000), (4096, 4096, 2_566_914_048),
])
def test_resident_masks_add_one_live_owner_without_reducing_scratch(rows, cols, mask_bytes):
    job = rm.PhaseJob(rm.PHASE_SIMULATION, rows, cols)
    for threads in (1, 8):
        base = rm.simulation_reservation(job.shape, gdal_cache_bytes=0,
                                         threads_per_worker=threads)
        resident = rm.simulation_reservation(job.shape, gdal_cache_bytes=0,
                                             threads_per_worker=threads, resident_lw_masks=True)
        assert resident.live_array_bytes == base.live_array_bytes + mask_bytes
        assert resident.decoded_block_bytes == base.decoded_block_bytes
        assert resident.total_bytes == base.total_bytes + mask_bytes
        with pytest.raises(rm.ResourceAdmissionError, match='queueing cannot make'):
            rm.plan_phase_admission([job], budget_bytes=base.total_bytes,
                                    parent_footprint_bytes=0, gdal_cache_bytes=0,
                                    threads_per_worker=threads, resident_lw_masks=True)


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


@pytest.mark.parametrize('pixels,block,accumulator', [
    (8,8,40), (33,128,40), (128,127,40), (128,128,1408), (129,128,1408),
])
def test_group_charge_does_not_reduce_preexisting_reserves(pixels, block, accumulator):
    shape = rm.TileShapeDescriptor(1, pixels, 609, 12, block)
    reserve = rm.simulation_reservation(shape, threads_per_worker=1, gdal_cache_bytes=0)
    size = min(pixels, block)
    scratch = 14*((size+7)//8*8)*609 + 28*size + accumulator
    assert scratch > max(96*pixels, 64*pixels)
    # Retain the excess decode reserve above the calibrated block128/P153.
    previous_decode = max(0, (block*609 - 128*153)*16*4)
    assert reserve.decoded_block_bytes == previous_decode + scratch + 17*609 + 8
    # Previously uncharged numerical build peak is exactly 10,361 B at P609.
    assert 17*609 + 8 == 10_361
