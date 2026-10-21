"""Bitwise comparisons to the preceding ordered NumPy SVF accumulation.

This is candidate-before/candidate-after evidence; original upstream coverage
remains in test_svf_options.py. The reference deliberately retains each annulus
array expression rather than aggregating the weights algebraically.
"""
import numba
import numpy as np
import pytest

from solweig_light.geometry import svf, shadows


def _legacy_accumulation(fields, masks, weights, directional_weights, directions):
    fields = list(fields)
    for wt, wd in zip(weights, directional_weights):
        for channel, mask in enumerate(masks):
            offset = channel * 5
            fields[offset] += wt * mask
            for direction, active in enumerate(directions):
                if active:
                    fields[offset + direction + 1] += wd * mask


def _scene(kind, dtype=np.float32):
    a = np.zeros((6, 7), dtype=dtype)
    a[2:4, 2:5] = 3.25
    canopy = np.zeros_like(a)
    canopy[1:5, 1:6] = 7.5
    trunk = np.zeros_like(a)
    trunk[1:5, 1:6] = 1.5
    bush = np.zeros_like(a)
    if kind == 'positive_bush':
        bush[1:3, 1:4] = 1.00001
    elif kind == 'nan_bush':
        bush[1, 2] = np.nan
        bush[2, 3] = 3
    elif kind == 'nonfinite_inputs':
        a[1, 3] = np.nan
        canopy[2, 5] = np.nan
        bush[3, 3] = np.inf
    elif kind == 'strided':
        a, canopy, trunk, bush = (value[::-1, ::-1] for value in (a, canopy, trunk, bush))
    elif kind == 'negative_short_ray':
        a.fill(-2)
        a[2:4, 2:5] = -1
        canopy.fill(0)
        trunk.fill(0)
    return dict(amaxvalue=1. if kind == 'negative_short_ray' else 8.,
                a=a, vegdem=canopy, vegdem2=trunk, bush=bush, scale=1.)


def _assert_all_outputs_bitwise(actual, expected):
    assert len(actual) == len(expected) == 19
    for index, (value, reference) in enumerate(zip(actual, expected, strict=True)):
        if hasattr(value, 'to_dense'):
            value = value.to_dense()
        assert value.shape == reference.shape
        assert value.dtype == reference.dtype
        np.testing.assert_array_equal(value.view(np.uint32), reference.view(np.uint32),
                                      err_msg=f'SVF output {index}')


@pytest.mark.parametrize('option', [1, 2, 3])
@pytest.mark.parametrize('kind', ['clear', 'positive_bush', 'nan_bush', 'nonfinite_inputs', 'strided', 'negative_short_ray'])
@pytest.mark.parametrize('threads', [1, 4, 8])
@pytest.mark.parametrize('compact', [False, True])
def test_full_svf_bitwise_preceding_array_order(monkeypatch, option, kind, threads, compact):
    inputs = _scene(kind)
    previous = numba.get_num_threads()
    try:
        numba.set_num_threads(threads)
        with np.errstate(invalid='ignore'):
            calculate = svf.svf_calculator_compact if compact else svf.svf_calculator
            actual = calculate(option, **inputs)
            if compact and kind == 'negative_short_ray':
                assert any('ternary' in value.modes for value in actual
                           if hasattr(value, 'modes'))
            monkeypatch.setattr(svf, '_accumulate_patch_f32', _legacy_accumulation)
            # Exercise the old per-patch bush dispatch alongside the old
            # accumulator so the whole 19-field comparison covers hoisting.
            monkeypatch.setattr(svf, 'prepare_shadow', lambda a, v, t, b:
                                lambda maximum, azi, alt, scale:
                                shadows.shadow(maximum, a, v, t, b, azi, alt, scale))
            expected = svf.svf_calculator(option, **inputs)
        _assert_all_outputs_bitwise(actual, expected)
    finally:
        numba.set_num_threads(previous)


@pytest.mark.parametrize('kind', ['clear', 'positive_bush', 'nonfinite_inputs'])
@pytest.mark.parametrize('precision', ['float64', 'mixed_bush'])
def test_float64_low_level_keeps_numpy_accumulation(monkeypatch, kind, precision):
    inputs = _scene(kind, np.float64 if precision == 'float64' else np.float32)
    if precision == 'mixed_bush':
        inputs['bush'] = inputs['bush'].astype(np.float64)
    calls = []
    reference = svf._accumulate_patch_numpy

    def numpy_only(*args):
        calls.append(True)
        return reference(*args)

    def forbidden(*args):
        raise AssertionError('float64 input reached the float32-only kernel')

    monkeypatch.setattr(svf, '_accumulate_patch_numpy', numpy_only)
    monkeypatch.setattr(svf, '_accumulate_patch_f32', forbidden)
    previous = numba.get_num_threads()
    try:
        numba.set_num_threads(1)
        with np.errstate(invalid='ignore'):
            actual = svf.svf_calculator(2, **inputs)
            monkeypatch.setattr(svf, '_accumulate_patch_numpy', _legacy_accumulation)
            expected = svf.svf_calculator(2, **inputs)
        assert len(calls) == 153
        _assert_all_outputs_bitwise(actual, expected)
    finally:
        numba.set_num_threads(previous)


def test_nonbinary_masks_keep_each_product_rounding():
    rng = np.random.default_rng(148)
    masks = tuple(rng.uniform(-1, 2, (5, 7)).astype(np.float32) for _ in range(3))
    masks[1][0, 0] = np.nan
    masks[2][0, 0] = -0.
    fields = tuple(rng.uniform(0, 1, (5, 7)).astype(np.float32) for _ in range(15))
    expected = [field.copy() for field in fields]
    weights = rng.uniform(0, .02, 12).astype(np.float32)
    directional = rng.uniform(0, .04, 12).astype(np.float32)
    directions = np.array([True, False, False, True])
    _legacy_accumulation(expected, masks, weights, directional, directions)
    svf._accumulate_patch_f32(fields, masks, weights, directional, directions)
    for actual, reference in zip(fields, expected, strict=True):
        np.testing.assert_array_equal(actual.view(np.uint32), reference.view(np.uint32))
