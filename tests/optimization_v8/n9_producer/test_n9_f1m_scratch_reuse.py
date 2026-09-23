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
"""N9 F1M direct-mask scratch-reuse tests.

With supplied ``sun_out``/``shade_out`` every valid lane (row < rows, all
columns) must be fully written: inactive valid columns cleared, not stale.
Padding lanes stay untouched, ``shade != not sun`` at equality/NaN holds,
and supplied buffers are validated (dtype/shape/contiguity/writeability)
with in/out span overlap rejected loudly BEFORE any write.
"""
import numpy as np
import pytest

from solweig_light._native_dispatch import direct_aosoa as da
from solweig_light.radiation.patch_radiation import (_class_coefficients,
                                                     _classes, patch_geometry)

from n9_producer_ref import (n9_masks_rows, n9_tensor32, n9_vault)


@pytest.fixture(params=[153, 7])
def geometry(request):
    return patch_geometry(n9_vault(request.param))


def asvf_pair(pixels):
    """Two clearly different daytime/nighttime-ish fields."""
    rng = np.random.default_rng(2026)
    day = rng.uniform(0.02, 0.35, size=pixels).astype(np.float32)
    night = rng.uniform(0.6, 1.0, size=pixels).astype(np.float32)
    return day, night


def _fresh(geometry, field, start, stop, active=None):
    return da.classify_block_aosoa(n9_tensor32(35.0), n9_tensor32(140.0),
                                   geometry, field, start, stop, active=active)


def _reused(geometry, field, start, stop, sun, shade, active=None, prepared=None):
    return da.classify_block_aosoa(n9_tensor32(35.0), n9_tensor32(140.0),
                                   geometry, field, start, stop, active=active,
                                   prepared=prepared, sun_out=sun, shade_out=shade)


def test_n9_f1m_alternating_day_night_reuse(geometry):
    """Alternating forcings through the SAME scratch always equal fresh."""
    pixels = 128
    day, night = asvf_pair(pixels)
    rows, patches = pixels, geometry.altitude.size
    gangs = -(-rows // 8)
    sun = np.empty((gangs, patches, 8), dtype=np.bool_)
    shade = np.empty_like(sun)
    for field in (day, night, day, night):
        reused = _reused(geometry, field, 0, rows, sun, shade)
        fresh = _fresh(geometry, field, 0, rows)
        assert reused[0] is sun and reused[1] is shade
        assert np.array_equal(sun, fresh[0]) and np.array_equal(shade, fresh[1])


def test_n9_f1m_changing_active_patch_sets_across_reuse(geometry):
    """A narrower active set must CLEAR columns the previous wider set wrote."""
    pixels = 128
    day, night = asvf_pair(pixels)
    rows, patches = pixels, geometry.altitude.size
    gangs = -(-rows // 8)
    difference = np.abs(n9_tensor32(140.0) - geometry.azimuth)
    wide = (difference > 90) & (difference < 270)
    narrow = wide & (np.arange(patches) % 3 == 0)
    assert narrow.sum() < wide.sum()
    sun = np.empty((gangs, patches, 8), dtype=np.bool_)
    shade = np.empty_like(sun)
    _reused(geometry, day, 0, rows, sun, shade, active=wide)
    reused = _reused(geometry, night, 0, rows, sun, shade, active=narrow)
    fresh = _fresh(geometry, night, 0, rows, active=narrow)
    assert np.array_equal(sun, fresh[0]) and np.array_equal(shade, fresh[1])
    # The cleared columns really were written by the previous call: with
    # poison True scratch and the narrow set, inactive columns end False.
    stale_probe = np.ones((gangs, patches, 8), dtype=np.bool_)
    _reused(geometry, day, 0, rows, stale_probe, stale_probe.copy(), active=narrow)
    inactive = ~narrow
    assert not n9_masks_rows(stale_probe)[:rows][:, inactive].any()


@pytest.mark.parametrize('rows', [5, 13, 97])
def test_n9_f1m_repeated_partial_last_blocks(geometry, rows):
    """Tail gangs: repeated partial-block reuse stays exact; padding keeps
    its poison."""
    day, night = asvf_pair(128)
    patches = geometry.altitude.size
    gangs = -(-rows // 8)
    sun = np.ones((gangs, patches, 8), dtype=np.bool_)
    shade = np.ones_like(sun)
    for field in (day, night, day):
        _reused(geometry, field, 0, rows, sun, shade)
        fresh = _fresh(geometry, field, 0, rows)
        assert np.array_equal(n9_masks_rows(sun)[:rows], n9_masks_rows(fresh[0])[:rows])
        assert np.array_equal(n9_masks_rows(shade)[:rows], n9_masks_rows(fresh[1])[:rows])
    assert n9_masks_rows(sun)[rows:].all() and n9_masks_rows(shade)[rows:].all()


def test_n9_f1m_all_false_active_set(geometry):
    """No active patches: every valid lane False, padding untouched."""
    rows, patches = 128, geometry.altitude.size
    gangs = -(-rows // 8)
    field = asvf_pair(128)[0]
    sun = np.ones((gangs, patches, 8), dtype=np.bool_)
    shade = np.ones_like(sun)
    produced = _reused(geometry, field, 0, rows, sun, shade,
                       active=np.zeros(patches, dtype=bool))
    assert produced is not None
    assert not n9_masks_rows(sun)[:rows].any()
    assert not n9_masks_rows(shade)[:rows].any()
    assert n9_masks_rows(sun)[rows:].all() and n9_masks_rows(shade)[rows:].all()


def test_n9_f1m_stale_scratch_poisoned(geometry):
    """Pre-filled True scratch: valid extent fully rewritten (inactive
    columns cleared too), padding lanes untouched."""
    rows, patches = 131, geometry.altitude.size
    gangs = -(-rows // 8)
    field = asvf_pair(160)[0][:rows]
    difference = np.abs(n9_tensor32(140.0) - geometry.azimuth)
    narrow = (difference > 90) & (np.arange(patches) % 2 == 0)
    sun = np.ones((gangs, patches, 8), dtype=np.bool_)
    shade = np.ones_like(sun)
    _reused(geometry, field, 0, rows, sun, shade, active=narrow)
    fresh = _fresh(geometry, field, 0, rows, active=narrow)
    assert np.array_equal(n9_masks_rows(sun)[:rows], n9_masks_rows(fresh[0])[:rows])
    assert np.array_equal(n9_masks_rows(shade)[:rows], n9_masks_rows(fresh[1])[:rows])
    assert n9_masks_rows(sun)[rows:].all() and n9_masks_rows(shade)[rows:].all()


@pytest.mark.parametrize('exact_tables', ['0', '1'])
def test_n9_f1m_parity_dense_classify_then_pack(geometry, exact_tables, monkeypatch):
    """Full parity vs the OLD path: dense _classes + pack_masks_aosoa, fresh
    AND reused direct production, whole-vault and solar-gate subsets."""
    monkeypatch.setenv('SOLWEIG_LIGHT_PATCH_CLASS_TABLES', exact_tables)
    pixels = 131
    rng = np.random.default_rng(int(exact_tables) * 41 + 7)
    field = rng.uniform(0.02, 1.0, size=pixels).astype(np.float32)
    altitude, azimuth = n9_tensor32(35.0), n9_tensor32(140.0)
    difference = np.abs(azimuth - geometry.azimuth)
    active = (difference > 90) & (difference < 270)
    for start, stop in ((0, 128), (5, 125), (3, 131), (0, 13)):
        rows = stop - start
        reference = _classes(altitude, azimuth, geometry, field, start, stop,
                             active=active)
        packed = da.pack_masks_aosoa(*reference, width=8)
        fresh = _fresh(geometry, field, start, stop, active=active)
        assert np.array_equal(n9_masks_rows(fresh[0])[:rows],
                              n9_masks_rows(packed[0])[:rows])
        assert np.array_equal(n9_masks_rows(fresh[1])[:rows],
                              n9_masks_rows(packed[1])[:rows])
        gangs = -(-rows // 8)
        sun = np.full((gangs, geometry.altitude.size, 8), True, dtype=np.bool_)
        shade = np.ones_like(sun)
        _reused(geometry, field, start, stop, sun, shade, active=active)
        assert np.array_equal(n9_masks_rows(sun)[:rows], n9_masks_rows(packed[0])[:rows])
        assert np.array_equal(n9_masks_rows(shade)[:rows], n9_masks_rows(packed[1])[:rows])


def test_n9_f1m_equality_and_nan_boundaries(geometry):
    """NaN/Inf field rows keep BOTH bits false through scratch reuse, and
    shade is not reduced to not-sun."""
    pixels = 128
    field = asvf_pair(pixels)[0]
    field[3] = np.float32('nan')
    field[17] = np.float32('inf')
    field[42] = np.float32(-np.inf)
    altitude, azimuth = n9_tensor32(20.0), n9_tensor32(10.0)
    gangs, patches = 16, geometry.altitude.size
    with np.errstate(invalid='ignore'):
        reference = _classes(altitude, azimuth, geometry, field, 0, 128)
        sun = np.ones((gangs, patches, 8), dtype=np.bool_)
        shade = np.ones_like(sun)
        da.classify_block_aosoa(altitude, azimuth, geometry, field, 0, 128,
                                sun_out=sun, shade_out=shade)
    scattered = n9_masks_rows(sun)[:128], n9_masks_rows(shade)[:128]
    assert np.array_equal(scattered[0], reference[0])
    assert np.array_equal(scattered[1], reference[1])
    both_false = ~(reference[0] | reference[1])
    assert both_false[3].all() and both_false[17].all() and both_false[42].all()
    assert not np.array_equal(scattered[1], ~scattered[0])


# ---------------------------------------------------------------------------
# Supplied-buffer validation and overlap rejection (before any write).
# ---------------------------------------------------------------------------

@pytest.fixture
def small_call(geometry):
    rows = 16
    field = asvf_pair(64)[0][:rows]

    def call(sun_out=None, shade_out=None, geometry_=None):
        return da.classify_block_aosoa(n9_tensor32(35.0), n9_tensor32(140.0),
                                       geometry_ or geometry, field, 0, rows,
                                       sun_out=sun_out, shade_out=shade_out)
    return call, rows, geometry.altitude.size


def test_n9_f1m_rejects_bad_buffers(small_call):
    call, rows, patches = small_call
    gangs = -(-rows // 8)
    shape = (gangs, patches, 8)
    with pytest.raises(ValueError, match='sun_out'):
        call(sun_out=np.zeros(shape, dtype=np.uint8))          # dtype
    with pytest.raises(ValueError, match='sun_out'):
        call(sun_out=np.zeros((gangs + 1, patches, 8), dtype=np.bool_))  # shape
    with pytest.raises(ValueError, match='sun_out'):
        call(sun_out=np.zeros(shape[::-1], dtype=np.bool_).transpose())  # strides
    readonly = np.zeros(shape, dtype=np.bool_)
    readonly.setflags(write=False)
    with pytest.raises(ValueError, match='sun_out'):
        call(sun_out=readonly)
    with pytest.raises(ValueError, match='shade_out'):
        call(shade_out=np.zeros(shape, dtype=np.float32))
    with pytest.raises(ValueError, match='sun_out'):
        call(sun_out=np.zeros((gangs, patches, 8), dtype=np.bool_).tolist())


def test_n9_f1m_rejects_overlapping_scratch_before_writes(small_call, geometry):
    """sun/shade sharing storage (or sharing storage with an input) is
    rejected loudly BEFORE any write -- the poison fill proves it."""
    call, rows, patches = small_call
    gangs = -(-rows // 8)
    # sun/shade overlapping each other.
    backing = np.zeros(gangs * patches * 8 + 8, dtype=np.bool_)
    sun = backing[:gangs * patches * 8].reshape(gangs, patches, 8)
    shade = backing[8:8 + gangs * patches * 8].reshape(gangs, patches, 8)
    with pytest.raises(ValueError, match='overlap'):
        call(sun_out=sun, shade_out=sun)
    with pytest.raises(ValueError, match='overlap'):
        call(sun_out=sun, shade_out=shade)
    # out overlapping the asvf input storage: one root buffer backs both, at
    # genuinely overlapping byte offsets.
    root = np.empty(0x8000, dtype=np.uint8)
    field = root[:4 * 16].view(np.float32)
    assert field.shape == (16,)
    sun = root[0x20:0x20 + gangs * patches * 8].view(np.bool_).reshape(gangs, patches, 8)
    with pytest.raises(ValueError, match='overlap'):
        da.classify_block_aosoa(n9_tensor32(35.0), n9_tensor32(140.0),
                                geometry, field, 0, rows, sun_out=sun, shade_out=None)
    with pytest.raises(ValueError, match='overlap'):
        da.classify_block_aosoa(n9_tensor32(35.0), n9_tensor32(140.0),
                                geometry, field, 0, rows, sun_out=None, shade_out=sun)
    # Genuine disjoint arena slices stay admissible (slot-style reuse).
    far = root[0x4000:0x4000 + gangs * patches * 8].view(np.bool_).reshape(
        gangs, patches, 8)
    call(sun_out=far, shade_out=root[0x6000:0x6000 + gangs * patches * 8]
         .view(np.bool_).reshape(gangs, patches, 8))


def test_n9_f1m_rejects_overlap_with_prepared_coefficients(small_call, geometry):
    """Caller-supplied prepared arrays are inputs too."""
    call, rows, patches = small_call
    gangs = -(-rows // 8)
    root = np.empty(0x8000, dtype=np.uint8)
    coefficients = root[0x40:0x40 + 4 * patches].view(np.float32)
    prepared = (np.arange(patches), coefficients,
                _class_coefficients(n9_tensor32(35.0), n9_tensor32(140.0),
                                    geometry, asvf_pair(64)[0][:64])[2])
    sun = root[0x50:0x50 + gangs * patches * 8].view(np.bool_).reshape(gangs, patches, 8)
    with pytest.raises(ValueError, match='prepared coefficients'):
        da.classify_block_aosoa(n9_tensor32(35.0), n9_tensor32(140.0), geometry,
                                asvf_pair(64)[0][:64], 0, rows, prepared=prepared,
                                sun_out=sun, shade_out=None)
    # Disjoint prepared coefficients are fine.
    far = root[0x4000:0x4000 + 4 * patches].view(np.float32)
    prepared = (np.arange(patches), far, prepared[2])
    out = da.classify_block_aosoa(n9_tensor32(35.0), n9_tensor32(140.0), geometry,
                                  asvf_pair(64)[0][:64], 0, rows, prepared=prepared,
                                  sun_out=sun, shade_out=None)
    assert out is not None


def test_n9_f1m_valid_supplied_buffers_accepted(small_call, geometry):
    """The happy path: exact-shape C-contiguous writeable bool scratch, and
    rows == 0 with empty buffers."""
    call, rows, patches = small_call
    gangs = -(-rows // 8)
    sun = np.zeros((gangs, patches, 8), dtype=np.bool_)
    shade = np.zeros_like(sun)
    out = call(sun_out=sun, shade_out=shade)
    assert out[0] is sun and out[1] is shade
    empty = np.zeros((0, patches, 8), dtype=np.bool_)
    out0 = da.classify_block_aosoa(n9_tensor32(35.0), n9_tensor32(140.0),
                                   geometry, asvf_pair(8)[0], 0, 0,
                                   sun_out=empty, shade_out=empty.copy())
    assert out0 is not None and out0[0].shape == (0, patches, 8)
