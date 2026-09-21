"""G02 differentials: hoisted direction-invariant source snapshots vs baseline.

The baseline is the verbatim pre-edit module in _reference_ground_view.py
(extracted from bfd9915e by script; see its docstring). Reference label: copied
pre-edit implementation with its own numba kernels compiled cache=False. All
comparisons are bitwise (uint32 views catch NaN payloads and signed zeros);
Tg is a caller-visible mutated output and is compared bitwise after every call.
"""
import numpy as np
import pytest
from solweig_light.radiation import engine, ground_view

import _reference_ground_view as reference

SBC = 5.67051e-08


def build_scene(rows, cols, seed=0, water=False, with_buildings=True,
                dtype=np.float32, first=2.0, second=6.0, scale=1.0):
    rng = np.random.default_rng(seed)
    float_dtype = np.dtype(dtype)
    walls = rng.integers(0, 4, size=(rows, cols)).astype(float_dtype)
    wallsun = np.where(rng.random((rows, cols)) < 0.4, walls, 0).astype(float_dtype)
    if with_buildings:
        buildings = (rng.random((rows, cols)) < 0.3).astype(float_dtype)
    else:
        buildings = np.zeros((rows, cols), float_dtype)
    shadow = (rng.random((rows, cols)) < 0.6).astype(float_dtype)
    dirwalls = (rng.random((rows, cols)) * 360.0).astype(float_dtype)
    Tg = (273.0 + 20.0 * rng.random((rows, cols))).astype(float_dtype)
    lc_grid = np.zeros((rows, cols), np.int32)
    if water:
        lc_grid[rows // 3:max(rows // 3 + 2, rows // 2), cols // 4:cols // 2] = 3
    emis_grid = np.full((rows, cols), 0.92, float_dtype)
    emis_grid[rng.random((rows, cols)) < 0.2] = 0.85
    alb_grid = np.full((rows, cols), 0.18, float_dtype)
    alb_grid[rng.random((rows, cols)) < 0.15] = 0.35
    Tgwall = (np.asarray(21.0, dtype=float_dtype) * np.ones((rows, cols), float_dtype)
              if seed % 2 else np.asarray(21.0, dtype=float_dtype))
    return dict(
        wallsun=wallsun, walls=walls, buildings=buildings, scale=np.float32(scale),
        shadow=shadow, first=np.array(first, dtype=np.float32),
        second=np.array(second, dtype=np.float32), dirwalls=dirwalls, Tg=Tg,
        Tgwall=Tgwall, Ta=21.0, emis_grid=emis_grid, ewall=0.88, alb_grid=alb_grid,
        SBC=np.float32(SBC), albedo_b=0.15, Twater=295.0, lc_grid=lc_grid,
        landcover=1 if water else 0, rows=rows, cols=cols,
    )


def as_bits(value):
    return np.ascontiguousarray(value).view(np.uint32)


def assert_exact(actual, expected, label):
    assert actual.dtype == expected.dtype, label
    assert actual.shape == expected.shape, label
    np.testing.assert_array_equal(as_bits(actual), as_bits(expected), err_msg=label)


def assert_gvf_outputs(actual, expected):
    assert len(actual) == len(expected) == 17
    names = ['gvfLup', 'gvfalb', 'gvfalbnosh', 'gvfLupE', 'gvfalbE', 'gvfalbnoshE',
             'gvfLupS', 'gvfalbS', 'gvfalbnoshS', 'gvfLupW', 'gvfalbW', 'gvfalbnoshW',
             'gvfLupN', 'gvfalbN', 'gvfalbnoshN', 'gvfSum', 'gvfNorm']
    for index, name in enumerate(names):
        assert_exact(actual[index], expected[index], name)


def snapshots(scene):
    return {key: (value.copy() if isinstance(value, np.ndarray) and value.ndim else value)
            for key, value in scene.items()}


def run_both_gvf(scene, parallel):
    pristine = snapshots(scene)
    ref_scene = snapshots(scene)
    new_scene = snapshots(scene)
    with np.errstate(invalid='ignore', divide='ignore'):
        expected = reference._gvf(**ref_scene, parallel=parallel)
        actual = ground_view._gvf(**new_scene, parallel=parallel)
    assert_exact(ref_scene['Tg'], new_scene['Tg'], 'Tg after the call')
    if scene['landcover'] == 1:
        # Control: the water mutation must actually be visible to the caller.
        assert not np.array_equal(as_bits(ref_scene['Tg']), as_bits(pristine['Tg'])), \
            'water Tg mutation control is vacuous'
    assert_gvf_outputs(actual, expected)
    return actual


@pytest.mark.parametrize('rows,cols', [(16, 16), (33, 21), (64, 64)])
@pytest.mark.parametrize('water', [False, True], ids=['nowater', 'water'])
@pytest.mark.parametrize('with_buildings', [False, True], ids=['open', 'built'])
@pytest.mark.parametrize('parallel', [False, True], ids=['serial', 'parallel'])
def test_gvf_differential_matches_baseline(rows, cols, water, with_buildings, parallel):
    scene = build_scene(rows, cols, seed=3 + water + 2 * with_buildings,
                        water=water, with_buildings=with_buildings)
    run_both_gvf(scene, parallel)


def test_gvf_nan_inf_signed_zero_inputs():
    scene = build_scene(24, 17, seed=11, water=True)
    scene['shadow'] = scene['shadow'].copy()
    scene['shadow'][2, 3] = np.float32(np.nan)
    scene['shadow'][4, 5] = np.float32(np.inf)
    scene['shadow'][6, 7] = np.float32(-0.0)
    scene['buildings'] = scene['buildings'].copy()
    scene['buildings'][8, 9] = np.float32(np.nan)
    scene['alb_grid'] = scene['alb_grid'].copy()
    scene['alb_grid'][10, 1] = np.float32(-0.0)
    scene['Tg'] = scene['Tg'].copy()
    scene['Tg'][12, 13] = np.float32(-np.inf)
    scene['Tg'][0, 0] = np.float32(-0.0)
    run_both_gvf(scene, parallel=False)


def test_gvf_float64_derived_lup_conversion_is_preserved():
    # SBC as a float64 array stays outside the float32 guard, so Lup/Lwall are
    # float64 and the snapshot conversion rounds: the value-changing conversion
    # must run once per state and match the per-direction baseline bitwise.
    scene = build_scene(20, 26, seed=5, water=True)
    scene['SBC'] = np.array([SBC])  # shape (1,) broadcasts to a float64 Lup
    run_both_gvf(scene, parallel=False)


def test_gvf_scalar_float64_tgwall_broadcast_conversion():
    scene = build_scene(18, 19, seed=7, water=True)
    scene['Tgwall'] = np.float64(21.5)  # scalar float64: Lwall broadcasts down
    run_both_gvf(scene, parallel=True)


@pytest.mark.parametrize('alias_key', ['shadow', 'buildings', 'alb_grid'])
def test_gvf_aliased_tg_keeps_exact_per_direction_route(alias_key):
    # Tg sharing memory with a snapshotted input must keep the legacy
    # per-direction copies: the water mutation rewrites the shared buffer after
    # the first direction's Lup evaluation but before its gather copies. The
    # alias must survive scene preparation, so both keys rebind to one copy.
    scene = build_scene(22, 18, seed=13, water=True)
    scene[alias_key] = scene[alias_key].copy()
    scene['Tg'] = scene[alias_key]

    def aliased_scene():
        local = snapshots(scene)
        shared = scene[alias_key].copy()
        local[alias_key] = shared
        local['Tg'] = shared
        return local

    pristine = snapshots(scene)
    ref_scene = aliased_scene()
    new_scene = aliased_scene()
    with np.errstate(invalid='ignore', divide='ignore'):
        expected = reference._gvf(**ref_scene, parallel=False)
        actual = ground_view._gvf(**new_scene, parallel=False)
    assert_exact(ref_scene['Tg'], new_scene['Tg'], 'Tg after the call')
    assert ref_scene['Tg'] is ref_scene[alias_key]
    assert not np.array_equal(as_bits(ref_scene['Tg']), as_bits(pristine['Tg'])), \
        'aliased mutation control is vacuous'
    assert_gvf_outputs(actual, expected)


def test_sun_water_trap_first_direction_differs():
    # Direction 0 evaluates Lup before Tg[lc_grid == 3] is rewritten; direction 1
    # inherits the mutated Tg. Both implementations must reproduce the split.
    scene = build_scene(20, 20, seed=17, water=True)
    common = dict(scale=scene['scale'], buildings=scene['buildings'], shadow=scene['shadow'],
                  first=scene['first'], second=scene['second'],
                  aspect=engine._divide(engine._operate(np.multiply, scene['dirwalls'], np.pi), 180),
                  walls=scene['walls'], Tgwall=scene['Tgwall'], Ta=scene['Ta'],
                  emis_grid=scene['emis_grid'], ewall=scene['ewall'], alb_grid=scene['alb_grid'],
                  SBC=scene['SBC'], albedo_b=scene['albedo_b'], Twater=scene['Twater'],
                  lc_grid=scene['lc_grid'], landcover=scene['landcover'])
    azimuths = np.arange(5, 359, 20, dtype=np.float32)
    ref_outputs = None
    for module in (reference, ground_view):
        Tg = scene['Tg'].copy()
        first_call = module._sun(azimuths[0], sunwall=np.zeros_like(scene['buildings']),
                                 Tg=Tg, parallel=False, **common)
        first_Tg = Tg.copy()
        second_call = module._sun(azimuths[1], sunwall=np.zeros_like(scene['buildings']),
                                  Tg=Tg, parallel=False, **common)
        # gvfLup combines the direction's gather Lup snapshot with the
        # re-evaluated mutated-Tg term, so the first/later split is observable.
        assert not np.array_equal(first_call[1], second_call[1]), module.__name__
        assert_exact(first_Tg, Tg, 'mutated water cells must persist between directions')
        if module is reference:
            ref_outputs = (first_call, second_call, Tg.copy())
        else:
            assert_exact(first_call[0], ref_outputs[0][0], 'gvf first call')
            assert_exact(first_call[1], ref_outputs[0][1], 'gvfLup first call')
            assert_exact(second_call[1], ref_outputs[1][1], 'gvfLup second call')
            assert_exact(Tg, ref_outputs[2], 'Tg after both calls')


def test_gather_snapshot_mode_direct():
    scene = build_scene(21, 29, seed=19, water=True)
    buildings = np.array(scene['buildings'], dtype=np.float32, copy=True)
    shadow = np.array(scene['shadow'], dtype=np.float32, copy=True)
    with np.errstate(invalid='ignore', divide='ignore'):
        sunwall = (engine._operate(np.multiply, engine._divide(scene['wallsun'], scene['walls']),
                                   buildings) == 1).astype(np.float32)
    lup = (273.0 + scene['Tg'] * scene['shadow']).astype(np.float32)
    albshadow = (scene['alb_grid'] * shadow).astype(np.float32)
    alb = np.array(scene['alb_grid'], dtype=np.float32, copy=True)
    # Snapshot contract: lwall already broadcast+converted, as _gather_sources
    # prepares it from _sun's scalar or raster Lwall.
    lwall = np.array(np.broadcast_to(np.array(310.0, dtype=np.float32), buildings.shape),
                     dtype=np.float32, copy=True)
    azimuth = np.float32(85.0)
    for parallel in (False, True):
        with np.errstate(invalid='ignore', divide='ignore'):
            expected = reference._gather(azimuth, scene['scale'], np.float32(2.0), np.float32(6.0),
                                         buildings, shadow, sunwall, lup, albshadow, alb, lwall,
                                         scene['albedo_b'], parallel)
            actual = ground_view._gather(azimuth, scene['scale'], np.float32(2.0), np.float32(6.0),
                                         buildings, shadow, sunwall, lup, albshadow, alb, lwall,
                                         scene['albedo_b'], parallel, snapshot=True)
        assert len(actual) == len(expected) == 16
        for index, (left, right) in enumerate(zip(actual, expected)):
            assert_exact(left, right, f'plane {index} parallel={parallel}')


def test_gather_persistent_outside_slice_samples():
    # Narrow scene: later ray steps leave the raster entirely, so bu/sh/lu/al/
    # an/sw must persist from the last in-slice step; first < second exercises
    # the unnormalized first-prefix snapshots.
    scene = build_scene(5, 23, seed=23, water=True, first=1.0, second=6.0)
    lup = (scene['Tg'] * scene['shadow']).astype(np.float32)
    albshadow = (scene['alb_grid'] * scene['shadow']).astype(np.float32)
    sunwall = np.zeros_like(lup)
    lwall = np.array(np.broadcast_to(np.array(305.0, dtype=np.float32), lup.shape),
                     dtype=np.float32, copy=True)
    for parallel in (False, True):
        with np.errstate(invalid='ignore', divide='ignore'):
            expected = reference._gather(np.float32(45.0), scene['scale'], np.float32(1.0),
                                         np.float32(6.0), scene['buildings'], scene['shadow'],
                                         sunwall, lup, albshadow, scene['alb_grid'],
                                         lwall, scene['albedo_b'], parallel)
            actual = ground_view._gather(np.float32(45.0), scene['scale'], np.float32(1.0),
                                         np.float32(6.0), scene['buildings'], scene['shadow'],
                                         sunwall, lup, albshadow, scene['alb_grid'],
                                         lwall, scene['albedo_b'], parallel, snapshot=True)
        for index, (left, right) in enumerate(zip(actual, expected)):
            assert_exact(left, right, f'persistent plane {index} parallel={parallel}')


def test_direction_order_accumulation_is_chronological():
    # The returned gvfSum must equal the float32 accumulation of per-direction
    # gvf2 in original azimuth order; a reversed order must differ somewhere
    # (negative control proving order is load-bearing and preserved).
    scene = build_scene(32, 24, seed=29, water=True)
    with np.errstate(invalid='ignore', divide='ignore'):
        outputs = ground_view._gvf(**snapshots(scene), parallel=False)
        azimuths = np.arange(5, 359, 20, dtype=np.float32)
        Tg = scene['Tg'].copy()
        sunwall = (engine._operate(np.multiply, engine._divide(scene['wallsun'], scene['walls']),
                                   scene['buildings']) == 1).astype(np.float32)
        forward = np.zeros_like(scene['buildings'])
        reverse = np.zeros_like(scene['buildings'])
        pieces = []
        for azimuth in azimuths:
            _, _, _, _, gvf2 = ground_view._sun(
                azimuth, scene['scale'], scene['buildings'], scene['shadow'],
                np.array(sunwall, dtype=np.float32, copy=True), scene['first'], scene['second'],
                engine._divide(engine._operate(np.multiply, scene['dirwalls'], np.pi), 180),
                scene['walls'], Tg, scene['Tgwall'], scene['Ta'], scene['emis_grid'],
                scene['ewall'], scene['alb_grid'], scene['SBC'], scene['albedo_b'],
                scene['Twater'], scene['lc_grid'], scene['landcover'], parallel=False)
            pieces.append(gvf2)
        for gvf2 in pieces:
            forward += gvf2
        for gvf2 in reversed(pieces):
            reverse += gvf2
    assert_exact(forward, outputs[15], 'gvfSum chronological order')
    assert not np.array_equal(as_bits(forward), as_bits(reverse)), 'order control is vacuous'


def test_nonfloat32_rasters_take_identical_fallback():
    scene = build_scene(14, 15, seed=31, water=True)
    scene['buildings'] = scene['buildings'].astype(np.float64)
    with np.errstate(invalid='ignore', divide='ignore'):
        expected = reference._gvf(**snapshots(scene), parallel=False)
        oracle = engine.gvf_2018a_numpy(**snapshots(scene))
        actual = ground_view._gvf(**snapshots(scene), parallel=False)
    assert_gvf_outputs(actual, expected)
    assert_gvf_outputs(actual, oracle)


def test_public_entries_match_internal_and_baseline():
    scene = build_scene(19, 23, seed=37, water=True)
    with np.errstate(invalid='ignore', divide='ignore'):
        expected = reference._gvf(**snapshots(scene), parallel=False)
        serial = ground_view.gvf_2018a(**snapshots(scene))
        parallel = ground_view.gvf_2018a_parallel(**snapshots(scene))
    assert_gvf_outputs(serial, expected)
    assert_gvf_outputs(parallel, expected)


@pytest.mark.parametrize('rows,cols', [(7, 5), (16, 16), (33, 21), (64, 64)])
@pytest.mark.parametrize('water', [False, True], ids=['nowater', 'water'])
@pytest.mark.parametrize('with_buildings', [False, True], ids=['open', 'built'])
@pytest.mark.parametrize('parallel', [False, True], ids=['serial', 'parallel'])
def test_gvf_fused_matches_full_and_baseline(rows, cols, water, with_buildings, parallel):
    # G03: the fused route must reproduce the full route (which materializes
    # all 16 per-direction planes) and the verbatim baseline bitwise.
    scene = build_scene(rows, cols, seed=43 + water + 2 * with_buildings,
                        water=water, with_buildings=with_buildings)
    ref_scene = snapshots(scene)
    full_scene = snapshots(scene)
    fused_scene = snapshots(scene)
    with np.errstate(invalid='ignore', divide='ignore'):
        expected = reference._gvf(**ref_scene, parallel=parallel)
        full = ground_view._gvf(**full_scene, parallel=parallel)
        fused = ground_view._gvf_fused(**fused_scene, parallel=parallel)
    assert_exact(ref_scene['Tg'], full_scene['Tg'], 'full Tg after')
    assert_exact(ref_scene['Tg'], fused_scene['Tg'], 'fused Tg after')
    assert_gvf_outputs(full, expected)
    assert_gvf_outputs(fused, expected)


def test_gvf_fused_block_row_variants():
    scene = build_scene(23, 19, seed=41, water=True)
    expected = None
    with np.errstate(invalid='ignore', divide='ignore'):
        expected = reference._gvf(**snapshots(scene), parallel=False)
        for block_rows in (1, 3, 32, 10_000):
            fused = ground_view._gvf_fused(**snapshots(scene), parallel=False, block_rows=block_rows)
            assert_gvf_outputs(fused, expected)


def test_gvf_fused_aliased_tg_route():
    # With Tg aliasing a snapshotted input the fused route keeps per-direction
    # conversion over the live arrays, read at the same chronological point as
    # the legacy gather copies; results must stay bitwise identical.
    scene = build_scene(22, 18, seed=47, water=True)
    scene['shadow'] = scene['shadow'].copy()
    scene['Tg'] = scene['shadow']

    def aliased():
        local = snapshots(scene)
        shared = scene['shadow'].copy()
        local['shadow'] = shared
        local['Tg'] = shared
        return local

    ref_scene = aliased()
    fused_scene = aliased()
    with np.errstate(invalid='ignore', divide='ignore'):
        expected = reference._gvf(**ref_scene, parallel=False)
        fused = ground_view._gvf_fused(**fused_scene, parallel=False)
    assert_exact(ref_scene['Tg'], fused_scene['Tg'], 'aliased Tg after')
    assert_gvf_outputs(fused, expected)


def test_gvf_fused_delegates_sun_level_guards():
    # Inputs _gvf accepts but _sun falls back on (nonfinite first, nonpositive
    # second*scale): the fused route must delegate to the full route, which
    # runs the exact per-direction fallback. That fallback is the original
    # engine body, whose documented upstream failure disposition for these
    # inputs is UnboundLocalError/RuntimeError, so identical failing behavior
    # across all three routes is the exactness contract here.
    def outcome(function, scene):
        try:
            with np.errstate(invalid='ignore', divide='ignore'):
                return ('ok', function(**snapshots(scene)))
        except (UnboundLocalError, RuntimeError) as error:
            return ('raise', type(error))

    scene = build_scene(15, 17, seed=53, water=True)
    scene['first'] = np.array(np.nan, dtype=np.float32)
    expected = outcome(reference._gvf, scene)
    assert expected[0] == 'raise', 'NaN-first control is vacuous'
    assert outcome(ground_view._gvf, scene)[0] == expected[0]
    assert outcome(ground_view._gvf_fused, scene)[0] == expected[0]
    scene = build_scene(15, 17, seed=53, water=True)
    scene['second'] = np.array(0.0, dtype=np.float32)
    expected = outcome(reference._gvf, scene)
    assert outcome(ground_view._gvf, scene)[0] == expected[0]
    assert outcome(ground_view._gvf_fused, scene)[0] == expected[0]
    if expected[0] == 'ok':
        for actual in (outcome(ground_view._gvf, scene), outcome(ground_view._gvf_fused, scene)):
            assert_gvf_outputs(actual[1], expected[1])


def test_gvf_fused_float64_rasters_delegate():
    scene = build_scene(14, 15, seed=59, water=True)
    scene['buildings'] = scene['buildings'].astype(np.float64)
    with np.errstate(invalid='ignore', divide='ignore'):
        expected = reference._gvf(**snapshots(scene), parallel=False)
        fused = ground_view._gvf_fused(**snapshots(scene), parallel=False)
    assert_gvf_outputs(fused, expected)


def test_public_entries_stay_on_full_route():
    scene = build_scene(19, 23, seed=61, water=True)
    with np.errstate(invalid='ignore', divide='ignore'):
        expected = ground_view._gvf(**snapshots(scene), parallel=False)
        serial = ground_view.gvf_2018a(**snapshots(scene))
    assert_gvf_outputs(serial, expected)
