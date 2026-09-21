"""C6-21 L1 differential: cylinder-longwave primary-output reduction.

Gate: the reduced primary kernels must reproduce the full kernel's primary
channels (output columns 0..6, i.e. ordered accumulators 0..9) bitwise per
call/timestep on real small inputs, adversarial schedules and degenerate
inputs; the FULL_DIAGNOSTICS profile must keep the untouched full path; guard
failures must fall back to the original serial reference in both profiles.
"""
import importlib.util as _ilu
import sys as _sys
import warnings
from pathlib import Path as _Path

import numpy as np
import pytest

# Load THIS family's conftest by file path: bare `import conftest` is
# shadowed by sibling families' conftest modules when several directories
# are collected in one pytest invocation.
_conftest_path = _Path(__file__).resolve().parent / 'conftest.py'
_spec = _ilu.spec_from_file_location('_cylinderlw_conftest', str(_conftest_path))
_conftest = _ilu.module_from_spec(_spec)
_sys.modules['_cylinderlw_conftest'] = _conftest
_spec.loader.exec_module(_conftest)
bitwise_equal = _conftest.bitwise_equal
lcyl_arguments = _conftest.lcyl_arguments
lcyl_patches = _conftest.lcyl_patches
lw_blocks = _conftest.lw_blocks
lw_coefficients = _conftest.lw_coefficients
packed = _conftest.packed

from solweig_light.radiation import cylinder_longwave as cyl
from solweig_light.radiation import patch_radiation as compiled
from solweig_light.radiation.engine import _serial_Lcyl_v2022a as serial_reference

SHAPES = ((16, 16), (37, 53), (64, 64), (128, 128))


def _run_kernel(kernel, sh, vs, vb, coefficients, start, stop):
    return kernel(sh, vs, vb, coefficients['sun'][start:stop], coefficients['shade'][start:stop],
                  coefficients['solid'], coefficients['sine'], coefficients['cosine'],
                  coefficients['directions'], coefficients['gate'], coefficients['solar_gate'],
                  coefficients['sky_down'], coefficients['sky_side'],
                  coefficients['sun_surface'], coefficients['shade_surface'],
                  coefficients['lup'][start:stop], coefficients['factor'])


@pytest.mark.parametrize('rows,cols', SHAPES)
@pytest.mark.parametrize('parallel', (False, True))
def test_kernel_primary_columns_bitwise_full(rng, rows, cols, parallel):
    """Primary output columns 0..6 are bitwise-equal to the full kernel's."""
    pixels, patches = rows*cols, 153
    sh, vs, vb = lw_blocks(rng, pixels, patches)
    coefficients = lw_coefficients(rng, patches, pixels)
    coefficients['sun'] = rng.random((pixels, patches)) < .5
    coefficients['shade'] = rng.random((pixels, patches)) < .5
    full_kernel = compiled._longwave if parallel else compiled._longwave_serial
    primary_kernel = cyl._longwave_primary if parallel else cyl._longwave_primary_serial
    full = _run_kernel(full_kernel, sh, vs, vb, coefficients, 0, pixels)
    primary = _run_kernel(primary_kernel, sh, vs, vb, coefficients, 0, pixels)
    assert primary.shape == (pixels, 7)
    for column in range(7):
        assert bitwise_equal(full[:, column], primary[:, column]), column


def test_kernel_primary_matches_full_route_invariance(rng):
    """Full parallel vs serial kernels agree; primary agrees across both."""
    rows, cols = 32, 32
    pixels, patches = rows*cols, 153
    sh, vs, vb = lw_blocks(rng, pixels, patches)
    coefficients = lw_coefficients(rng, patches, pixels)
    coefficients['sun'] = rng.random((pixels, patches)) < .5
    coefficients['shade'] = rng.random((pixels, patches)) < .5
    full_parallel = _run_kernel(compiled._longwave, sh, vs, vb, coefficients, 0, pixels)
    full_serial = _run_kernel(compiled._longwave_serial, sh, vs, vb, coefficients, 0, pixels)
    for column in range(11):
        assert bitwise_equal(full_parallel[:, column], full_serial[:, column]), column
    primary_parallel = _run_kernel(cyl._longwave_primary, sh, vs, vb, coefficients, 0, pixels)
    primary_serial = _run_kernel(cyl._longwave_primary_serial, sh, vs, vb, coefficients, 0, pixels)
    for column in range(7):
        assert bitwise_equal(primary_parallel[:, column], primary_serial[:, column]), column
        assert bitwise_equal(full_parallel[:, column], primary_parallel[:, column]), column


@pytest.mark.parametrize('parallel', (False, True))
def test_fused_primary_columns_bitwise_full(rng, monkeypatch, parallel):
    """Fused primary block is bitwise-equal to the full fused block (cols 0..6)."""
    monkeypatch.setenv('SOLWEIG_LIGHT_FUSED_RAD', '1')
    rows, cols = 16, 16
    pixels = rows*cols
    patches = 153
    sh = packed(rng, rows, cols, patches, ('binary', 'ternary', 'raw'))
    vs = packed(rng, rows, cols, patches, ('ternary', 'raw', 'binary'))
    vb = packed(rng, rows, cols, patches, ('raw', 'signed_zero', 'nonfinite'))
    coefficients = lw_coefficients(rng, patches, pixels)
    coefficients['sun'] = rng.random((pixels, patches)) < .5
    coefficients['shade'] = rng.random((pixels, patches)) < .5
    start, stop = 0, pixels
    sh_block, vs_block, vb_block = (compiled._block(channel, start, stop, patches)
                                    for channel in (sh, vs, vb))
    full_kernel = compiled._longwave if parallel else compiled._longwave_serial
    expected = _run_kernel(full_kernel, sh_block, vs_block, vb_block, coefficients, start, stop)
    observed = cyl._longwave_fused_primary_block(
        sh, vs, vb, start, stop, patches, coefficients['sun'][start:stop],
        coefficients['shade'][start:stop], coefficients['solid'], coefficients['sine'],
        coefficients['cosine'], coefficients['directions'], coefficients['gate'],
        coefficients['solar_gate'], coefficients['sky_down'], coefficients['sky_side'],
        coefficients['sun_surface'], coefficients['shade_surface'],
        coefficients['lup'][start:stop], coefficients['factor'], parallel)
    for column in range(7):
        assert bitwise_equal(expected[:, column], observed[:, column]), column


def test_fused_primary_block_schedule(rng, monkeypatch):
    """Adversarial block intervals: single pixel and mid-block boundaries."""
    monkeypatch.setenv('SOLWEIG_LIGHT_FUSED_RAD', '1')
    rows, cols = 16, 16
    pixels = rows*cols
    patches = 153
    sh = packed(rng, rows, cols, patches, ('binary', 'ternary', 'raw'))
    vs = packed(rng, rows, cols, patches, ('binary', 'ternary', 'raw'))
    vb = packed(rng, rows, cols, patches, ('binary', 'ternary', 'raw'))
    coefficients = lw_coefficients(rng, patches, pixels)
    coefficients['sun'] = rng.random((pixels, patches)) < .5
    coefficients['shade'] = rng.random((pixels, patches)) < .5
    for start, stop in ((0, 1), (5, 6), (37, 100), (0, pixels)):
        sh_block, vs_block, vb_block = (compiled._block(channel, start, stop, patches)
                                        for channel in (sh, vs, vb))
        expected = _run_kernel(compiled._longwave, sh_block, vs_block, vb_block,
                               coefficients, start, stop)
        observed = cyl._longwave_fused_primary_block(
            sh, vs, vb, start, stop, patches, coefficients['sun'][start:stop],
            coefficients['shade'][start:stop], coefficients['solid'], coefficients['sine'],
            coefficients['cosine'], coefficients['directions'], coefficients['gate'],
            coefficients['solar_gate'], coefficients['sky_down'], coefficients['sky_side'],
            coefficients['sun_surface'], coefficients['shade_surface'],
            coefficients['lup'][start:stop], coefficients['factor'], True)
        for column in range(7):
            assert bitwise_equal(expected[:, column], observed[:, column]), (start, stop, column)


@pytest.mark.parametrize('block_pixels', (1, 3, 128, 10**6))
@pytest.mark.parametrize('parallel', (False, True))
def test_wrapper_lcyl_primary_bitwise(rng, block_pixels, parallel):
    """Wrapper-level parity: Ldown/Lside bitwise, cardinals NOT_REQUESTED."""
    args = lcyl_arguments(rng, rows=16, cols=16)
    full = compiled.Lcyl_v2022a(**args, block_pixels=block_pixels, parallel=parallel)
    primary = cyl.Lcyl_v2022a_primary(**args, block_pixels=block_pixels, parallel=parallel)
    assert bitwise_equal(full[0], primary[0])
    assert bitwise_equal(full[1], primary[1])
    for marker in primary[2:]:
        assert marker is cyl.NOT_REQUESTED


@pytest.mark.parametrize('altitude,azimuth', ((35., 180.), (0.5, 0.), (89., 359.),
                                              (-10., 200.), (10., 90.), (1e-4, 359.999)))
def test_wrapper_schedules(rng, altitude, azimuth):
    """Solar schedules incl. night and gate boundaries, both profiles."""
    args = lcyl_arguments(rng, rows=16, cols=16,
                          solar_altitude=np.array(altitude, dtype=np.float32),
                          solar_azimuth=np.array(azimuth, dtype=np.float32))
    full = compiled.Lcyl_v2022a(**args)
    primary = cyl.Lcyl_v2022a_primary(**args)
    assert bitwise_equal(full[0], primary[0])
    assert bitwise_equal(full[1], primary[1])
    assert all(marker is cyl.NOT_REQUESTED for marker in primary[2:])


def test_wrapper_per_timestep_chronology(rng):
    """Six ordered timesteps (day-night-day) with per-step bitwise parity."""
    schedule = ((35., 90.), (12., 142.), (2., 200.), (-8., 250.), (0.1, 300.), (60., 15.))
    args = lcyl_arguments(rng, rows=16, cols=16)
    for step, (altitude, azimuth) in enumerate(schedule):
        args['solar_altitude'] = np.array(altitude, dtype=np.float32)
        args['solar_azimuth'] = np.array(azimuth, dtype=np.float32)
        full = compiled.Lcyl_v2022a(**args)
        primary = cyl.Lcyl_v2022a_primary(**args)
        assert bitwise_equal(full[0], primary[0]), step
        assert bitwise_equal(full[1], primary[1]), step
        assert all(marker is cyl.NOT_REQUESTED for marker in primary[2:]), step


@pytest.mark.parametrize('parallel', (False, True))
def test_degenerate_inputs(rng, parallel):
    """Zero emissivity, nonfinite Lup, extreme Ta, sentinel visibility mats."""
    cases = [
        ('zero_emissivity', dict(esky=np.array(0.0, dtype=np.float32))),
        ('lup_nonfinite', dict(Lup=_spiked(rng, 16*16, (16, 16)))),
        ('ta_hot', dict(Ta=np.array(1e30, dtype=np.float32))),
        ('ta_cold', dict(Ta=np.array(-1e30, dtype=np.float32))),
        ('ta_negative_zero', dict(Ta=np.array(-0.0, dtype=np.float32))),
        ('visibility_all_zero', dict(shmat=np.zeros((16, 16, 153), dtype=np.float32))),
        ('visibility_all_one', dict(shmat=np.ones((16, 16, 153), dtype=np.float32))),
        ('visibility_all_two', dict(shmat=np.full((16, 16, 153), 2.0, dtype=np.float32))),
        ('visibility_nonfinite', dict(shmat=_nonfinite_cube(rng, 16, 16, 153))),
        ('veg_nonfinite', dict(vegshmat=_nonfinite_cube(rng, 16, 16, 153))),
        ('vb_nonfinite', dict(vbshvegshmat=_nonfinite_cube(rng, 16, 16, 153))),
        ('asvf_nonfinite', dict(asvf=_spiked(rng, 16*16, (16, 16)))),
        ('ewall_zero', dict(ewall=np.array(0.0, dtype=np.float32))),
        ('ewall_one', dict(ewall=np.array(1.0, dtype=np.float32))),
    ]
    for name, override in cases:
        args = lcyl_arguments(rng, rows=16, cols=16, **override)
        full = compiled.Lcyl_v2022a(**args, parallel=parallel)
        primary = cyl.Lcyl_v2022a_primary(**args, parallel=parallel)
        assert bitwise_equal(full[0], primary[0]), name
        assert bitwise_equal(full[1], primary[1]), name
        assert all(marker is cyl.NOT_REQUESTED for marker in primary[2:]), name


def _spiked(rng, count, shape):
    values = rng.random(count).astype(np.float32)
    values[1::11] = np.float32('nan')
    values[2::11] = np.float32('inf')
    values[3::11] = np.float32('-inf')
    values[5::11] = np.float32(-0.0)
    return values.reshape(shape)


def _nonfinite_cube(rng, rows, cols, patches):
    cube = (rng.random((rows, cols, patches)) > .4).astype(np.float32)
    cube[0, 0, ::7] = np.float32('nan')
    cube[0, 1, ::11] = np.float32('inf')
    cube[1, 0, ::13] = np.float32('-inf')
    cube[1, 1, ::17] = np.float32(-0.0)
    return cube


def test_zero_pixel_domain(rng):
    """rows=cols=0 keeps the empty contract identical in both profiles."""
    args = lcyl_arguments(rng, rows=0, cols=0)
    full = compiled.Lcyl_v2022a(**args)
    primary = cyl.Lcyl_v2022a_primary(**args)
    assert full[0].shape == (0, 0) and primary[0].shape == (0, 0)
    assert bitwise_equal(full[0], primary[0])
    assert bitwise_equal(full[1], primary[1])
    assert all(marker is cyl.NOT_REQUESTED for marker in primary[2:])


def test_by_demand_dispatch_full_default(rng):
    """Default demand and explicit FULL_DIAGNOSTICS keep the untouched full path."""
    assert cyl.current_demand() is cyl.CylinderLongwaveDemand.FULL_DIAGNOSTICS
    args = lcyl_arguments(rng, rows=16, cols=16)
    direct = compiled.Lcyl_v2022a(**args)
    dispatched = cyl.Lcyl_v2022a_by_demand(**args)
    for a, b in zip(direct, dispatched):
        assert bitwise_equal(a, b)
    assert cyl.current_demand() is cyl.CylinderLongwaveDemand.FULL_DIAGNOSTICS
    with cyl.demand_scope(cyl.CylinderLongwaveDemand.FULL_DIAGNOSTICS):
        dispatched = cyl.Lcyl_v2022a_by_demand(**args)
    for a, b in zip(direct, dispatched):
        assert bitwise_equal(a, b)


def test_by_demand_dispatch_pipeline(rng):
    """PIPELINE_CYLINDERS_ANISOTROPIC dispatches the primary reduction."""
    args = lcyl_arguments(rng, rows=16, cols=16)
    full = compiled.Lcyl_v2022a(**args)
    with cyl.demand_scope(cyl.CylinderLongwaveDemand.PIPELINE_CYLINDERS_ANISOTROPIC):
        dispatched = cyl.Lcyl_v2022a_by_demand(**args)
        assert cyl.current_demand() is cyl.CylinderLongwaveDemand.PIPELINE_CYLINDERS_ANISOTROPIC
    assert bitwise_equal(full[0], dispatched[0])
    assert bitwise_equal(full[1], dispatched[1])
    assert all(marker is cyl.NOT_REQUESTED for marker in dispatched[2:])
    assert cyl.current_demand() is cyl.CylinderLongwaveDemand.FULL_DIAGNOSTICS


def test_demand_scope_restores_on_error(rng):
    """The demand scope restores the previous profile even on exception."""
    args = lcyl_arguments(rng, rows=16, cols=16)
    with pytest.raises(RuntimeError), cyl.demand_scope(cyl.CylinderLongwaveDemand.PIPELINE_CYLINDERS_ANISOTROPIC):
        raise RuntimeError('boom')
    assert cyl.current_demand() is cyl.CylinderLongwaveDemand.FULL_DIAGNOSTICS
    direct = compiled.Lcyl_v2022a(**args)
    dispatched = cyl.Lcyl_v2022a_by_demand(**args)
    for a, b in zip(direct, dispatched):
        assert bitwise_equal(a, b)


@pytest.mark.parametrize('demand', list(cyl.CylinderLongwaveDemand))
def test_fallback_guard_order_preserved(rng, demand):
    """Unsupported profiles fall back to the serial reference in both profiles.

    The scalar-altitude case preserves the original failure: the reference
    itself raises TypeError, identically under both demand profiles.
    """
    cases = [
        ('float64_cube', lcyl_arguments(rng, rows=16, cols=16,
                                        shmat=np.zeros((16, 16, 153), dtype=np.float64)), 'result'),
        ('scalar_altitude', lcyl_arguments(rng, rows=16, cols=16,
                                           solar_altitude=np.float32(35.0)), 'TypeError'),
        ('oversized_patches', lcyl_arguments(rng, rows=16, cols=16,
                                             sky_patches=np.tile(lcyl_patches(2), (5, 1))[:610]), 'result'),
    ]
    for name, args, outcome in cases:
        if outcome == 'TypeError':
            with pytest.raises(TypeError), cyl.demand_scope(demand):
                cyl.Lcyl_v2022a_by_demand(**args)
            with pytest.raises(TypeError):
                serial_reference(**args)
            continue
        reference = serial_reference(**args)
        with cyl.demand_scope(demand):
            observed = cyl.Lcyl_v2022a_by_demand(**args)
        # Guard-failure fallback restores the complete original contract: the
        # serial reference's full six-field result, real arrays included.
        for index in range(6):
            assert bitwise_equal(reference[index], observed[index]), (name, index)
        if demand is cyl.CylinderLongwaveDemand.FULL_DIAGNOSTICS:
            # Unsupported fast-path guards also fall back inside the public path.
            expected = compiled.Lcyl_v2022a(**args)
            for index in range(6):
                assert bitwise_equal(expected[index], observed[index]), (name, index)


@pytest.mark.parametrize('demand', list(cyl.CylinderLongwaveDemand))
def test_seterr_overflow_parity(rng, demand):
    """Wrapper-level np.seterr behavior is identical in both profiles."""
    args = lcyl_arguments(rng, rows=16, cols=16, Ta=np.array(1e30, dtype=np.float32))
    with np.errstate(all='raise'), cyl.demand_scope(demand):
        with pytest.raises(FloatingPointError):
            cyl.Lcyl_v2022a_by_demand(**args)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        with np.errstate(all='warn'), cyl.demand_scope(demand):
            observed = cyl.Lcyl_v2022a_by_demand(**args)
            expected = compiled.Lcyl_v2022a(**args)
    if demand is cyl.CylinderLongwaveDemand.FULL_DIAGNOSTICS:
        for a, b in zip(expected, observed):
            assert bitwise_equal(a, b)
    else:
        assert bitwise_equal(expected[0], observed[0])
        assert bitwise_equal(expected[1], observed[1])
        assert all(marker is cyl.NOT_REQUESTED for marker in observed[2:])


def test_not_requested_is_not_zero(rng):
    """The omitted diagnostics are an explicit marker, never fake zeros."""
    args = lcyl_arguments(rng, rows=16, cols=16)
    primary = cyl.Lcyl_v2022a_primary(**args)
    for marker in primary[2:]:
        assert not isinstance(marker, np.ndarray)
        assert marker is cyl.NOT_REQUESTED


def test_kernel_primary_output_width_and_mapping(rng):
    """Primary kernel exposes the documented 7-column primary contract."""
    rows, cols = 16, 16
    pixels, patches = rows*cols, 153
    sh, vs, vb = lw_blocks(rng, pixels, patches)
    coefficients = lw_coefficients(rng, patches, pixels)
    coefficients['sun'] = rng.random((pixels, patches)) < .5
    coefficients['shade'] = rng.random((pixels, patches)) < .5
    full = _run_kernel(compiled._longwave, sh, vs, vb, coefficients, 0, pixels)
    primary = _run_kernel(cyl._longwave_primary, sh, vs, vb, coefficients, 0, pixels)
    # columns 2..6 are accumulators 5..9 individually; 0/1 are the ordered totals
    for accumulator, column in zip(range(5, 10), range(2, 7)):
        assert bitwise_equal(full[:, column], primary[:, column])
        assert bitwise_equal(full[:, column], primary[:, accumulator-3]), accumulator
    assert primary.shape[1] == 7 and full.shape[1] == 11
