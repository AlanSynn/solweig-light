"""Bound-only classifier refinement versus the frozen pre-refinement loop.

Oracle copied verbatim (function body, renamed only) from:
  de54d4485ab4f7a9b96441b5d4a97b3f51e798ff
  src/solweig_light/_native_dispatch/direct_aosoa.py
  _classes_table_masked_aosoa
Original function-source SHA256: 876c0a56c8be4c734d87498d50d674923952347378b38921e4c3e6d8bd4528bd
Only the test compilation decorator differs: no persistent cache or identity.
"""
import numpy as np
from numba import njit
import pytest

from solweig_light._native_dispatch.direct_aosoa import _classes_table_masked_aosoa
from solweig_light.radiation._sleef_classifier import atan_fma


@njit(cache=False, fastmath=False, error_model='numpy')
def _frozen_masked_aosoa(heights, coefficients, radians_to_degrees, altitudes,
                                indices, sun, shade, rows):
    """Masked-column form, mirroring _classes_table_masked's indirection."""
    for gang in range(sun.shape[0]):
        for column in range(coefficients.shape[0]):
            altitude = altitudes[column]
            coefficient = coefficients[column]
            target = indices[column]
            for lane in range(sun.shape[2]):
                row = gang * sun.shape[2] + lane
                if row >= rows:
                    break
                delta = np.float32(heights[row] + coefficient)
                degrees = np.float32(atan_fma(delta) * radians_to_degrees)
                sun[gang, target, lane] = degrees < altitude
                shade[gang, target, lane] = degrees > altitude


@pytest.mark.parametrize('width', [4, 8])
@pytest.mark.parametrize('rows', [0, 1, 3, 4, 7, 8, 9, 27, 128, 129])
@pytest.mark.parametrize('targets', ['canonical', 'sparse', 'negative_alias', 'duplicate', 'unsorted'])
@pytest.mark.parametrize('profile', ['f32', 'factor_f64', 'factor_python', 'mixed_f64'])
def test_valid_lane_bound_preserves_frozen_masks(width, rows, targets, profile):
    bits = np.array([0, 0x80000000, 0x7fc12345, 0x7fc54321, 0x3f800000,
                     0x3f800001, 0, 0x80000000, 0x7fa12345, 0x3f800001], np.uint32)
    coefficients = bits.view(np.float32)
    indices = np.arange(bits.size, dtype=np.int64)
    patches = 21 if targets == 'sparse' else 12
    if targets == 'sparse':
        indices *= 2
    elif targets == 'negative_alias':
        indices[0], indices[-1] = -1, patches - 1
    elif targets == 'duplicate':
        indices[2] = indices[1]
    elif targets == 'unsorted':
        indices = indices[::-1].copy()
    heights = np.resize(np.array([0, -0., .25, -1, 1, np.inf, -np.inf,
                                 np.nan], np.float32), rows)
    factor = np.float32(180 / np.pi)
    altitudes = np.array([0, -1, 30, 50, 45, 45, 1, 2, 75, 46], np.float32)
    if profile == 'factor_f64':
        factor = np.float64(180 / np.pi)
    elif profile == 'factor_python':
        factor = float(180 / np.pi)
    elif profile == 'mixed_f64':
        heights = heights.astype(np.float64)
        with np.errstate(invalid='ignore'):
            coefficients = coefficients.astype(np.float64)
        altitudes = altitudes.astype(np.float64)
        factor = np.float64(180 / np.pi)
    shape = ((rows + width - 1) // width, patches, width)
    expected = tuple(np.ones(shape, np.bool_) for _ in range(2))
    actual = tuple(np.ones(shape, np.bool_) for _ in range(2))
    snapshots = [value.tobytes() for value in (heights, coefficients, altitudes, indices)]
    _frozen_masked_aosoa(heights, coefficients, factor, altitudes, indices,
                         *expected, rows)
    _classes_table_masked_aosoa(heights, coefficients, factor, altitudes, indices,
                                *actual, rows)
    for got, want in zip(actual, expected):
        assert np.array_equal(got, want)
        assert got.transpose(0, 2, 1).reshape(-1, patches)[rows:].all()
        inactive = sorted(set(range(patches)) - set(indices % patches))
        assert got[:, inactive, :].all()
    assert [value.tobytes() for value in (heights, coefficients, altitudes, indices)] == snapshots
