"""Exact stored-coefficient reuse, with the original masked kernel as oracle."""
import numpy as np
import numba
import pytest

from solweig_light._native_dispatch import direct_aosoa as da, sw_batch
from solweig_light.geometry.visibility import LazyDiffVisibility, PackedVisibility
from solweig_light.radiation.patch_radiation import patch_geometry
from solweig_light.radiation._sleef_classifier import atan_fma


def _groups(coefficients):
    result = da._coefficient_bit_groups(coefficients)
    assert result is not None
    return result


def test_groups_preserve_bits_and_first_member_order():
    bits = np.array([0, 0x80000000, 0x7fc12345, 0x7fc54321, 0x3f800000,
                     0x3f800001, 0, 0x80000000, 0x7fc12345, 0x3f800001], np.uint32)
    coefficients = bits.view(np.float32)
    offsets, columns = _groups(coefficients)
    assert offsets.tolist() == [0, 2, 4, 6, 7, 8, 10]
    assert columns.tolist() == [0, 6, 1, 7, 2, 8, 3, 4, 5, 9]
    for lo, hi in zip(offsets[:-1], offsets[1:]):
        assert np.all(bits[columns[lo:hi]] == bits[columns[lo]])
    assert np.array_equal(coefficients.view(np.uint32), bits)


@pytest.mark.parametrize('coefficients', [np.array([], np.float32),
    np.arange(8, dtype=np.float32), np.zeros(8, np.float64),
    np.zeros(8, np.float32)[::2], np.zeros((2, 2), np.float32)])
def test_unsupported_or_all_unique_uses_reference(coefficients):
    assert da._coefficient_bit_groups(coefficients) is None


@pytest.mark.parametrize('width', [4, 8])
@pytest.mark.parametrize('rows', [0, 1, 7, 8, 9, 27])
@pytest.mark.parametrize('sparse', [False, True])
def test_grouped_masks_exact_with_boundaries_and_padding(width, rows, sparse):
    bits = np.array([0, 0x80000000, 0x7fc12345, 0x7fc54321, 0x3f800000,
                     0x3f800001, 0, 0x80000000, 0x7fc12345, 0x3f800001], np.uint32)
    coefficients = bits.view(np.float32)
    offsets, columns = _groups(coefficients)
    indices = np.arange(coefficients.size, dtype=np.int64) * (2 if sparse else 1)
    patches = int(indices[-1]) + 2
    heights = np.resize(np.array([0, -0., .25, -1, 1, np.inf, -np.inf,
                                 np.nan], np.float32), rows)
    factor = np.float32(180 / np.pi)
    equality = np.float32(atan_fma(np.float32(0)) * factor)
    altitudes = np.array([equality, -1, 30, 50, 45, 45, 1, 2, 75, 46], np.float32)
    shape = ((rows + width - 1) // width, patches, width)
    expected = tuple(np.ones(shape, np.bool_) for _ in range(2))
    actual = tuple(np.ones(shape, np.bool_) for _ in range(2))
    da._classes_table_masked_aosoa(heights, coefficients, factor, altitudes,
                                  indices, *expected, rows)
    da._classes_table_grouped_aosoa(heights, coefficients, factor, altitudes,
                                   indices, offsets, columns, *actual, rows)
    for got, want in zip(actual, expected):
        assert np.array_equal(got, want)
        padding = got.transpose(0, 2, 1).reshape(-1, patches)[rows:]
        assert padding.all()
        assert got[:, -1, :].all()  # inactive columns keep their poison
    if rows:
        assert not actual[0][0, indices[0], 0]
        assert not actual[1][0, indices[0], 0]  # strict threshold equality
        assert actual[0][0, indices[6], 0]      # same coefficient, new altitude
        assert not actual[0][0, indices[2], 0]  # NaN coefficient
        assert not actual[1][0, indices[2], 0]
        assert not actual[0][0, indices[4], 0]
        assert not actual[1][0, indices[4], 0]  # atan(1) == 45 degrees
        assert actual[1][0, indices[5], 0]      # one-ULP coefficient > threshold


def _batch_case(rows=43, patches=13, unique=False):
    rng = np.random.default_rng(194)
    geometry = patch_geometry(np.column_stack((
        np.linspace(0, 85, patches, dtype=np.float32),
        np.linspace(0, 350, patches, dtype=np.float32))))
    channels = tuple(PackedVisibility.from_dense(
        rng.integers(0, 3, (1, rows, patches)).astype(np.float32)) for _ in range(3))
    values = dict(zip(('shmat', 'vegshmat', 'vbshvegshmat'), channels))
    values.update(diffsh=LazyDiffVisibility(*channels[:2]),
                  asvf=rng.uniform(0, 1, rows).astype(np.float32))
    indices = np.array([0, 2, 3, 5, 7, 9, 12], np.int64)
    coefficients = np.arange(indices.size, dtype=np.float32) if unique else np.array(
        [0, -0., 0, -.4, -.4, .2, 0], np.float32)
    prepared = (indices, coefficients, np.float64(180 / np.pi))
    return values, geometry, prepared, rng.random(patches).astype(np.float32)


@pytest.mark.parametrize('unique', [False, True])
@pytest.mark.parametrize('capacity', [8, 16, 32, 128])
@pytest.mark.parametrize('surface_dtype', [np.float32, np.float64])
def test_sw_batch_exact_at_one_and_several_threads(unique, capacity, surface_dtype, monkeypatch):
    rows = 192 if capacity == 128 else 43
    values, geometry, prepared, lum = _batch_case(rows=rows, unique=unique)
    original = numba.get_num_threads()
    real_groups = sw_batch._coefficient_bit_groups
    groups_seen = []
    def tracked(coefficients):
        groups = real_groups(coefficients)
        groups_seen.append(groups is not None)
        return groups
    monkeypatch.setattr(sw_batch, '_coefficient_bit_groups', tracked)
    def execute(parallel):
        initial = np.arange(7 * rows, dtype=np.float32).reshape(7, rows) / np.float32(8)
        return sw_batch.execute(values, geometry, prepared, lum, surface_dtype(2.75),
            surface_dtype(1.25), capacity, initial, parallel=parallel)
    try:
        with monkeypatch.context() as patch:
            patch.setattr(sw_batch, '_coefficient_bit_groups', lambda _: None)
            expected = execute(False)
        assert expected is not None
        for threads in sorted({1, min(2, numba.config.NUMBA_NUM_THREADS)}):
            numba.set_num_threads(threads)
            for parallel in (False, True):
                actual = execute(parallel)
                assert actual is not None
                assert np.array_equal(actual.view(np.uint32), expected.view(np.uint32))
    finally:
        numba.set_num_threads(original)
    assert groups_seen and all(value == (not unique) for value in groups_seen)


def test_duplicate_targets_retain_reference_write_order(monkeypatch):
    values, geometry, prepared, lum = _batch_case()
    prepared[0][1] = prepared[0][0]
    def fail(_):
        raise AssertionError('grouping must not reorder duplicate target writes')
    monkeypatch.setattr(sw_batch, '_coefficient_bit_groups', fail)
    result = sw_batch.execute(values, geometry, prepared, lum, np.float32(2.75),
        np.float32(1.25), 16, np.zeros((7, 43), np.float32), parallel=False)
    assert result is not None


@pytest.mark.parametrize('out_of_range', [False, True])
def test_noncanonical_targets_never_group_before_native_launch(out_of_range, monkeypatch):
    values, geometry, prepared, lum = _batch_case()
    if out_of_range:
        prepared[0][-1] = geometry.altitude.size
    else:
        # Strictly ascending, but -1 aliases the final positive target.
        prepared[0][0] = -1
    def fail(_):
        raise AssertionError('grouping must require canonical in-range targets')
    monkeypatch.setattr(sw_batch, '_coefficient_bit_groups', fail)
    launches = []
    def fake_kernel(*args):
        assert args[8].size == 0  # empty group_offsets selects the reference
        launches.append(True)
    monkeypatch.setattr(sw_batch, '_batch_serial', fake_kernel)
    def execute():
        return sw_batch.execute(values, geometry, prepared, lum, np.float32(2.75),
            np.float32(1.25), 16, np.zeros((7, 43), np.float32), parallel=False)
    if out_of_range:
        # The retained NumPy altitude indexing raises before a native write.
        with pytest.raises(IndexError):
            execute()
        assert not launches
    else:
        assert execute() is not None
        assert launches == [True]


@pytest.mark.parametrize('patches', [0, 1, 2, 7, 153, 609])
@pytest.mark.parametrize('regime', ['all_unique', 'all_zero', 'one_repeat', 'mixed_bits'])
@pytest.mark.parametrize('readonly', [False, True])
def test_fixed_builder_matches_original_bit_group_order(patches, regime, readonly):
    # Independent Python bit grouping is the pre-budget builder's semantics;
    # production must not retain its Python per-patch dict/list allocations.
    bits = np.arange(patches, dtype=np.uint32)
    if regime == 'all_zero':
        bits[:] = 0
    elif regime == 'one_repeat' and patches:
        bits[-1] = bits[0]
    elif regime == 'mixed_bits':
        states = np.array([0, 0x80000000, 0x7fc12345, 0x7fc54321,
                           0x7fa12345, 0x3f800000, 0x3f800001], np.uint32)
        bits = np.random.default_rng(20261020 + patches).choice(states, patches)
    expected = {}
    for column, state in enumerate(bits):
        expected.setdefault(int(state), []).append(column)
    before = bits.copy()
    if readonly:
        bits.setflags(write=False)
    result = da._coefficient_bit_groups(bits.view(np.float32))
    assert np.array_equal(bits, before)
    if len(expected) == patches:
        assert result is None
    else:
        offsets, columns = result
        assert offsets.dtype == columns.dtype == np.int64
        assert offsets.tolist() == [0] + list(np.cumsum([len(v) for v in expected.values()]))
        assert columns.tolist() == [column for members in expected.values() for column in members]
        assert offsets.nbytes + columns.nbytes <= 16 * patches + 8


def test_oversized_repeated_table_retains_masked_route(monkeypatch):
    from types import SimpleNamespace
    # Public geometry caps P at 609; exercise the private/custom caller here.
    geometry = SimpleNamespace(
        altitude=np.linspace(0, 85, 610, dtype=np.float32),
        azimuth=np.zeros(610, np.float32), solid_angle=np.full(610, .1, np.float32),
        cosine=np.linspace(1, .1, 610, dtype=np.float32))
    rng = np.random.default_rng(610)
    channels = tuple(PackedVisibility.from_dense(
        rng.integers(0, 3, (1, 43, 610)).astype(np.float32)) for _ in range(3))
    values = dict(zip(('shmat', 'vegshmat', 'vbshvegshmat'), channels))
    values.update(diffsh=LazyDiffVisibility(*channels[:2]), asvf=np.full(43, .6, np.float32))
    lum = np.full(610, .2, np.float32)
    prepared = (np.arange(610, dtype=np.int64), np.zeros(610, np.float32),
                np.float64(180 / np.pi))
    def forbidden(_):
        raise AssertionError('oversized tables must not launch the quadratic builder')
    monkeypatch.setattr(da, '_coefficient_bit_groups_f32', forbidden)
    assert da._coefficient_bit_groups(prepared[1]) is None
    def execute():
        return sw_batch.execute(values, geometry, prepared, lum, np.float32(2.75),
            np.float32(1.25), 16, np.zeros((7, 43), np.float32), parallel=False)
    with monkeypatch.context() as patch:
        patch.setattr(sw_batch, '_coefficient_bit_groups', lambda _: None)
        expected = execute()
    actual = execute()
    assert actual is not None and expected is not None
    assert np.array_equal(actual.view(np.uint32), expected.view(np.uint32))
