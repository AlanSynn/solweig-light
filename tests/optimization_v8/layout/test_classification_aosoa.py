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
"""N8-11 AoSoA classification tests (dossier stage 2).

The AoSoA masks must be bitwise the retained _classes output scattered to
the lane layout, in both dispatch regimes (default route and R04+G06 exact
tables), for whole-vault and solar-gate-subset active sets, at every width
and tail. Boundary semantics -- both bits false at equality, shade is not
always not-sun -- are preserved because the arithmetic is reused, and the
tests pin actual both-false cells on record.
"""
import numpy as np
import pytest

from solweig_light._native_dispatch import direct_aosoa as da
from solweig_light.radiation.patch_radiation import _class_coefficients, _classes, patch_geometry


def vault(patches=153):
    """Deterministic Tregenza-like ordered patch table (<=609 patches)."""
    bands = 15
    per_band = max(1, -(-patches // bands))
    altitudes = np.repeat(np.linspace(6.0, 84.0, bands).astype(np.float32), per_band)
    azimuths = np.tile(np.linspace(0.0, 350.0, per_band).astype(np.float32), bands)
    return np.column_stack((altitudes, azimuths))[:patches].astype(np.float32)


def tensor32(value):
    return np.array(np.float32(value))


def masks_rows(mask):
    gangs, patches, width = mask.shape
    return mask.transpose(0, 2, 1).reshape(gangs * width, patches)


@pytest.fixture(params=[153, 609, 7])
def geometry(request):
    return patch_geometry(vault(request.param))


@pytest.mark.parametrize('exact_tables', ['0', '1'])
@pytest.mark.parametrize('width', da.WIDTHS)
@pytest.mark.parametrize('start,stop', [(0, 128), (5, 125), (0, 1), (0, 0), (3, 131)])
def test_masks_bitwise_equal_classes(geometry, width, start, stop, exact_tables, monkeypatch):
    monkeypatch.setenv('SOLWEIG_LIGHT_PATCH_CLASS_TABLES', exact_tables)
    pixels = 131
    rng = np.random.default_rng(int(exact_tables) * 100 + width)
    asvf = rng.uniform(0.02, 1.0, size=pixels).astype(np.float32)
    altitude = tensor32(35.0)
    azimuth = tensor32(140.0)
    difference = np.abs(azimuth - geometry.azimuth)
    active = (difference > 90) & (difference < 270)  # solar-gate subset form
    reference = _classes(altitude, azimuth, geometry, asvf, start, stop, active=active)
    produced = da.classify_block_aosoa(altitude, azimuth, geometry, asvf, start, stop,
                                       active=active, width=width)
    assert produced is not None
    sun, shade = produced
    rows = stop - start
    assert sun.shape == (-(-rows // width), geometry.altitude.size, width)
    assert sun.dtype == np.bool_ and shade.dtype == np.bool_
    assert np.array_equal(masks_rows(sun)[:rows], reference[0])
    assert np.array_equal(masks_rows(shade)[:rows], reference[1])


@pytest.mark.parametrize('width', da.WIDTHS)
def test_masks_padding_never_written(geometry, width):
    rng = np.random.default_rng(61)
    asvf = rng.uniform(0.02, 1.0, size=131).astype(np.float32)
    rows, patches = 97, geometry.altitude.size
    gangs = -(-rows // width)
    sun = np.ones((gangs, patches, width), dtype=np.bool_)
    shade = np.ones_like(sun)
    da.classify_block_aosoa(tensor32(35), tensor32(140), geometry, asvf, 0, rows,
                            sun_out=sun, shade_out=shade, width=width)
    # Padding lanes keep their poison True fill; valid lanes were overwritten.
    assert masks_rows(sun)[rows:].all() and masks_rows(shade)[rows:].all()
    assert not masks_rows(sun)[:rows].all()


def test_both_bits_false_boundary_is_preserved(geometry):
    """shade is not always not-sun: NaN-field rows carry both bits false."""
    rng = np.random.default_rng(67)
    asvf = rng.uniform(0.02, 1.0, size=128).astype(np.float32)
    asvf[3] = np.float32('nan')   # NaN delta -> NaN degrees -> both strict
    asvf[17] = np.float32('inf')  # tan(Inf) = NaN through the retained route
    asvf[42] = np.float32(-np.inf)
    altitude = tensor32(20.0)
    azimuth = tensor32(10.0)
    with np.errstate(invalid='ignore'):  # the retained route's own tan(Inf) warning
        reference = _classes(altitude, azimuth, geometry, asvf, 0, 128)
        both_false = ~(reference[0] | reference[1])
        assert both_false[3].all() and both_false[17].all() and both_false[42].all()
        produced = da.classify_block_aosoa(altitude, azimuth, geometry, asvf, 0, 128)
    scattered = masks_rows(produced[0])[:128], masks_rows(produced[1])[:128]
    assert np.array_equal(~(scattered[0] | scattered[1]), both_false)
    assert not np.array_equal(scattered[1], ~scattered[0]), 'shade must not be reduced to not-sun'


def test_prepared_tuple_reuse_matches_classes(geometry):
    rng = np.random.default_rng(71)
    asvf = rng.uniform(0.02, 1.0, size=128).astype(np.float32)
    altitude, azimuth = tensor32(41.0), tensor32(200.0)
    prepared = _class_coefficients(altitude, azimuth, geometry, asvf)
    assert prepared is not None
    reference = _classes(altitude, azimuth, geometry, asvf, 16, 96, prepared=prepared)
    produced = da.classify_block_aosoa(altitude, azimuth, geometry, asvf, 16, 96,
                                       prepared=prepared)
    assert np.array_equal(masks_rows(produced[0])[:80], reference[0])
    assert np.array_equal(masks_rows(produced[1])[:80], reference[1])


def test_float64_asvf_declines(geometry):
    asvf = np.full(128, 0.5, dtype=np.float64)
    assert da.classify_block_aosoa(tensor32(35), tensor32(140), geometry, asvf,
                                   0, 128) is None


def test_strided_asvf_matches(geometry):
    """Non-unit-stride field input keeps the retained route's semantics."""
    rng = np.random.default_rng(73)
    wide = rng.uniform(0.02, 1.0, size=(128, 4)).astype(np.float32)
    strided = wide[:, ::2]  # non-unit row stride into the field
    flat = np.ascontiguousarray(strided).reshape(-1)
    altitude, azimuth = tensor32(55.0), tensor32(300.0)
    reference = _classes(altitude, azimuth, geometry, flat, 8, 120)
    produced = da.classify_block_aosoa(altitude, azimuth, geometry, strided, 8, 120)
    assert produced is not None
    assert np.array_equal(masks_rows(produced[0])[:112], reference[0])
    assert np.array_equal(masks_rows(produced[1])[:112], reference[1])


def test_inputs_unchanged_and_pack_helper_matches(geometry):
    rng = np.random.default_rng(79)
    asvf = rng.uniform(0.02, 1.0, size=128).astype(np.float32)
    before = asvf.tobytes()
    altitude, azimuth = tensor32(35.0), tensor32(140.0)
    reference = _classes(altitude, azimuth, geometry, asvf, 0, 128)
    assert asvf.tobytes() == before
    packed = da.pack_masks_aosoa(*reference, width=8)
    direct = da.classify_block_aosoa(altitude, azimuth, geometry, asvf, 0, 128, width=8)
    assert np.array_equal(packed[0], direct[0])
    assert np.array_equal(packed[1], direct[1])
    # Tail packing pads with False rather than reading absent rows.
    tail_reference = _classes(altitude, azimuth, geometry, asvf, 0, 13)
    tail_packed = da.pack_masks_aosoa(*tail_reference, width=8)
    assert not masks_rows(tail_packed[0])[13:].any()
