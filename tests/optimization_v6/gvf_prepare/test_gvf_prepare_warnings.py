"""C6-30 warning/np.seterr contract.

Hoisting moves WHEN an invariant expression is evaluated (once per call, at
preparation) and therefore how many times numpy emits its warnings. The
contract under test:

- a hoisted expression's warning fires exactly once per prepared evaluation
  instead of once per direction: with Tg ~ 1e33 the float32 ^4 power in the
  Lup expression overflows once per _lup_expression evaluation, giving
  exactly 36 warnings on the fused route (18 gather + 18 lup_term) and
  exactly 2 on the prepared route (pre- and post-mutation);
- the first evaluation happens at the same input state, so np.seterr(raise)
  aborts both routes on the same first offending evaluation, before any
  caller-visible mutation;
- warnings OUTSIDE the hoisted closure keep their exact timing. The
  divide-by-zero-in-log warning at engine.py:1370 (svfalfaE =
  arcsin(exp(log(1 - svfE)/2)) in Lside_veg_v2022a, firing whenever a SVF
  equals 1) is per-Lside-call, i.e. per timestep, and must be neither
  absorbed nor duplicated by gvf preparation;
- sunwall's walls-zero divide warning is once-per-call in the fused route
  already (loop-external there): count parity between routes.
"""
import warnings

import numpy as np

from gvf_prepare_cases import (
    assert_gvf_outputs, build_scene, call_fused, call_prepared, snapshots,
)


def count_runtime_warnings(route, scene):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always', RuntimeWarning)
        with np.errstate(invalid='ignore', divide='ignore', over='warn'):
            route(scene)
    return sum(1 for item in caught if issubclass(item.category, RuntimeWarning))


def assert_exact_local(actual, expected):
    view = np.uint32 if actual.dtype == np.float32 else np.uint64
    np.testing.assert_array_equal(np.ascontiguousarray(actual).view(view),
                                  np.ascontiguousarray(expected).view(view))


def overflowing_scene(rows, cols, seed):
    scene = build_scene(rows, cols, seed=seed, water=True)
    # ~2.9e35 stays inside float32; the ^4 power overflows to inf, and the
    # Lup subtraction then produces NaN (invalid: suppressed by the routes'
    # errstate so only overflow warnings are counted).
    scene['Tg'] = (scene['Tg'] * np.float32(1e33)).astype(np.float32)
    return scene


def test_overflow_warning_count_contract():
    # One overflow warning per _lup_expression evaluation (the Tg-side
    # ^4 power): fused 18 gather + 18 lup_term = 36, prepared 2. The sky
    # term's power reads Ta only and does not overflow.
    scene = overflowing_scene(32, 32, seed=71)
    fused_count = count_runtime_warnings(call_fused, scene)
    prepared_count = count_runtime_warnings(call_prepared, scene)
    assert fused_count == 36, fused_count
    assert prepared_count == 2, prepared_count


def test_overflow_nonfinite_parity_despite_warning_counts():
    # The warning-count reduction must not change the arithmetic: inf/NaN
    # masks stay bitwise identical (differential at the same scene).
    scene = overflowing_scene(32, 32, seed=71)
    expected, expected_Tg = call_fused(scene)
    actual, actual_Tg = call_prepared(scene)
    assert_exact_local(actual_Tg, expected_Tg)
    assert_gvf_outputs(actual, expected)


def test_errstate_raise_aborts_prepared_route_like_baseline():
    # With overflow raised, both routes abort on the FIRST offending
    # evaluation; Tg is left unmutated in both (direction 1's Lup is
    # evaluated before the water scatter on both routes).
    scene = overflowing_scene(24, 24, seed=73)

    def run(route):
        local = snapshots(scene)
        with np.errstate(invalid='ignore', divide='ignore', over='raise'):
            try:
                route(local)
                return ('ok', local['Tg'])
            except FloatingPointError as error:
                return ('raise', type(error), local['Tg'])

    from solweig_light.radiation import gvf_prepared, ground_view
    fused = run(lambda local: ground_view._gvf_fused(**local, parallel=True, block_rows=32))
    prepared = run(lambda local: gvf_prepared.prepared_gvf_step(**local, parallel=True, block_rows=32))
    assert fused[0] == 'raise', fused[0]
    assert prepared[0] == 'raise'
    assert prepared[1] is fused[1]
    assert np.array_equal(fused[2], prepared[2]), 'Tg must be untouched on both abort paths'


def test_svf_log_divide_warning_outside_closure_unchanged():
    # engine.py:1370 divides log(1 - svfE) by 2: with svfE == 1 the log is 0
    # and numpy warns divide-by-zero-in-log once per Lside_veg_v2022a call
    # (per timestep). A gvf preparation between two such calls must not
    # change the per-call warning count in either direction.
    from solweig_light.radiation import engine, gvf_prepared

    def lside_log_warning_count():
        # Only svfE carries the 1.0 cell, so exactly one of the four
        # cardinal log sites at engine.py:1370-1373 fires per call.
        svf = np.full((4, 4), 0.7, np.float32)
        svf_e = svf.copy()
        svf_e[0, 0] = 1.0
        args = dict(
            svfS=svf, svfW=svf, svfN=svf, svfE=svf_e,
            svfEveg=svf * 0.5, svfSveg=svf * 0.5, svfWveg=svf * 0.5, svfNveg=svf * 0.5,
            svfEaveg=svf * 0.8, svfSaveg=svf * 0.8, svfWaveg=svf * 0.8, svfNaveg=svf * 0.8,
            azimuth=-10.0, altitude=0.0, Ta=20.0, Tw=15.0,
            SBC=np.float32(5.67051e-08), ewall=0.88,
            Ldown=np.zeros((4, 4), np.float32), esky=0.9, t=0.0,
            F_sh=np.zeros((4, 4), np.float32), CI=np.float32(0.5),
            LupE=np.zeros((4, 4), np.float32), LupS=np.zeros((4, 4), np.float32),
            LupW=np.zeros((4, 4), np.float32), LupN=np.zeros((4, 4), np.float32),
            anisotropic_longwave=1,
        )
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always', RuntimeWarning)
            with np.errstate(invalid='ignore', divide='warn'):
                engine.Lside_veg_v2022a(**args)
        return sum(1 for item in caught
                   if issubclass(item.category, RuntimeWarning) and 'log' in str(item.message))

    before = lside_log_warning_count()
    scene = build_scene(16, 16, seed=75, water=True)
    with np.errstate(invalid='ignore', divide='ignore'):
        gvf_prepared.prepared_gvf_step(**snapshots(scene), parallel=True, block_rows=32)
    after = lside_log_warning_count()
    assert before == 1, before
    assert after == 1, after


def test_walls_zero_divide_warning_count_parity():
    # walls == 0 cells make sunwall's _divide warn once per call on both
    # routes: the sunwall expression is loop-external in the fused baseline,
    # so preparation must neither absorb nor duplicate the warning.
    scene = build_scene(20, 20, seed=77, water=True)
    scene['walls'] = np.zeros_like(scene['walls'])
    scene['wallsun'] = np.zeros_like(scene['wallsun'])

    def count_route(route, local_scene):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always', RuntimeWarning)
            with np.errstate(invalid='ignore', divide='warn'):
                route(local_scene)
        return sum(1 for item in caught if 'divide by zero' in str(item.message))

    from solweig_light.radiation import gvf_prepared, ground_view
    fused_count = count_route(lambda local: ground_view._gvf_fused(**local, parallel=True, block_rows=32),
                              snapshots(scene))
    prepared_count = count_route(lambda local: gvf_prepared.prepared_gvf_step(**local, parallel=True, block_rows=32),
                                 snapshots(scene))
    assert fused_count == prepared_count, (fused_count, prepared_count)
