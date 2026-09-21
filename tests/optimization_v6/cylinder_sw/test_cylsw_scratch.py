"""Structural scratch gates: the admitted profile must not do box-only work.

Completion gate 2: no box-only allocation under the admitted profile, and the
narrow kernel scratch is exactly the four demanded reduction columns.
"""
import numpy as np
import pytest
from solweig_light.radiation import cylinder_shortwave, patch_radiation

from conftest import synthetic_values


def test_narrow_kernel_scratch_is_four_columns(admitted_profile):
    values = synthetic_values(16, 16, seed=5)
    pixels = 16 * 16
    sun = np.zeros((pixels, 6), dtype=np.bool_)
    shade = np.zeros_like(sun)
    sh = values['shmat'].reshape(pixels, 6)
    vs = values['vegshmat'].reshape(pixels, 6)
    vb = values['vbshvegshmat'].reshape(pixels, 6)
    diff = values['diffsh'].reshape(pixels, 6)
    lum = values['lv'][:, 2] * np.float32(120.0)
    solid = np.full(6, np.float32(0.01), dtype=np.float32)
    cosine = np.full(6, np.float32(0.7), dtype=np.float32)
    surface_sun = np.float32(12.5)
    surface_sh = np.float32(3.25)
    for parallel in (False, True):
        kernel = cylinder_shortwave._shortwave_cylinder if parallel else cylinder_shortwave._shortwave_cylinder_serial
        reduced = kernel(sh, vs, vb, diff, sun, shade, lum, solid, cosine, surface_sun, surface_sh)
        assert reduced.shape == (pixels, 4)
        original = patch_radiation._shortwave_serial(sh, vs, vb, diff, sun, shade, lum, solid, cosine,
                                                     np.zeros((6, 4), dtype=np.float32),
                                                     np.zeros((6, 4), dtype=np.bool_),
                                                     np.zeros((6, 4), dtype=np.bool_),
                                                     np.zeros(6, dtype=np.bool_),
                                                     surface_sun, surface_sh, False)
        assert original.shape == (pixels, 20)
        # Document the dead generic work: box-only columns stay at zero and
        # the demanded columns match the narrow scratch bit for bit.
        assert np.all(original[:, 4:].view(np.uint32) == 0)
        assert np.array_equal(reduced.view(np.uint32), original[:, :4].view(np.uint32))


class _RecordingNumpy:
    """Proxy over the module-level numpy namespace recording scratch requests."""

    def __init__(self, real):
        self._real = real
        self.requests = []

    def __getattr__(self, name):
        return getattr(self._real, name)

    def zeros(self, *args, **kwargs):
        self.requests.append(('zeros', args, kwargs))
        return self._real.zeros(*args, **kwargs)

    def empty(self, *args, **kwargs):
        self.requests.append(('empty', args, kwargs))
        return self._real.empty(*args, **kwargs)

    def ones(self, *args, **kwargs):
        self.requests.append(('ones', args, kwargs))
        return self._real.ones(*args, **kwargs)


def test_entry_allocates_no_box_only_scratch(monkeypatch, admitted_profile):
    """Python-level scratch of the narrow entry is exactly the demanded
    seven-field output plane plus the scalar radTot accumulator: no
    (pixels,20) reduction block and no (patches,4) direction cosine table."""
    values = synthetic_values(16, 16, seed=11)
    patches = values['lv'].shape[0]
    proxy = _RecordingNumpy(np)
    monkeypatch.setattr(cylinder_shortwave, 'np', proxy)
    actual = cylinder_shortwave.kside_cylinder_anisotropic(values, block_pixels=16, parallel=True)
    assert actual is not None
    shapes = [args[0] for name, args, _ in proxy.requests]
    assert (7, 256) in shapes  # the seven public fields only
    assert 1 in shapes or (1,) in shapes  # radTot scalar accumulator
    for shape in shapes:
        assert not (isinstance(shape, tuple) and len(shape) == 2 and shape[1] == 20), shape
        assert not (isinstance(shape, tuple) and tuple(shape) == (patches, 4)), shape


def test_fallback_profile_keeps_generic_wrapper_scratch():
    """Under FULL_DIAGNOSTICS the entry declines; the generic wrapper still
    produces its full 20-column route result on the same inputs, within the
    untouched upstream budget against the serial reference."""
    values = synthetic_values(16, 16, seed=11)
    assert cylinder_shortwave.kside_cylinder_anisotropic(values, block_pixels=16, parallel=True) is None
    from conftest import assert_within_original_budget, serial_reference
    wrapper = patch_radiation.Kside_veg_v2022a(**values, block_pixels=16, parallel=True)
    assert_within_original_budget(wrapper, serial_reference(values), 'fallback-generic-wrapper')
