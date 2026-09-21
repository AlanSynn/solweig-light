"""C6-30 differentials: per-step prepared GVF expressions vs the accepted
fused baseline and the true original engine body.

Baselines (all oracles run on independent scene snapshots):
- ground_view._gvf_fused: the accepted v5 G03 route (parallel dispatch target)
  whose hoisted-snapshot behavior this module must not regress;
- engine.gvf_2018a_numpy: the verbatim original engine implementation, i.e.
  the ultimate source of truth for water pre/post mutation semantics.

All comparisons are bitwise (uint32/uint64 views catch NaN payloads, signed
zeros and dtype drift). Tg is a caller-visible mutated output and is compared
after every call. Prepared calls run with parallel=True/block_rows=32 unless
a variant is the point of the test.
"""
import numpy as np
import pytest

from gvf_prepare_cases import (
    assert_exact, assert_gvf_outputs, build_scene, call_fused, call_original,
    call_prepared, snapshots,
)


def outcome(make_call, scene, **kwargs):
    """Run one route on a fresh scene snapshot; capture raise-parity too."""
    try:
        outputs, Tg = make_call(scene, **kwargs)
        return ('ok', outputs, Tg)
    except (UnboundLocalError, RuntimeError, ValueError) as error:
        return ('raise', type(error))


@pytest.mark.parametrize('rows,cols', [(16, 16), (33, 21), (64, 64), (128, 128)])
@pytest.mark.parametrize('water', [False, True], ids=['nowater', 'water'])
@pytest.mark.parametrize('with_buildings', [False, True], ids=['open', 'built'])
@pytest.mark.parametrize('parallel', [False, True], ids=['serial', 'parallel'])
def test_prepared_matches_fused_and_original(rows, cols, water, with_buildings, parallel):
    scene = build_scene(rows, cols, seed=3 + water + 2 * with_buildings,
                        water=water, with_buildings=with_buildings)
    expected, expected_Tg = call_fused(scene)
    oracle, oracle_Tg = call_original(scene)
    actual, actual_Tg = call_prepared(scene, parallel=parallel)
    assert_exact(oracle_Tg, expected_Tg, 'original Tg after (baseline control)')
    assert_exact(actual_Tg, expected_Tg, 'Tg after the call')
    assert_gvf_outputs(actual, expected)
    assert_gvf_outputs(actual, oracle)


def test_water_mutation_and_first_direction_split_controls():
    # Negative controls making the water differentials non-vacuous: the
    # mutation really changes caller-visible Tg, and the gather Lup that
    # feeds direction 1 really differs from the one serving directions
    # 2..18 once the scatter has landed.
    scene = build_scene(24, 24, seed=101, water=True)
    pristine = snapshots(scene)['Tg']
    _, Tg = call_prepared(scene)
    assert not np.array_equal(Tg, pristine), 'water mutation control is vacuous'
    from solweig_light.radiation.ground_view import _lup_expression
    mutated = snapshots(scene)['Tg']
    mutated[scene['lc_grid'] == 3] = np.float32(scene['Twater'] - scene['Ta'])
    with np.errstate(invalid='ignore', divide='ignore'):
        lup_first = _lup_expression(scene['SBC'], scene['emis_grid'], pristine,
                                    scene['shadow'], scene['Ta'])
        lup_rest = _lup_expression(scene['SBC'], scene['emis_grid'], mutated,
                                   scene['shadow'], scene['Ta'])
    assert not np.array_equal(lup_first, lup_rest), 'first/later split control is vacuous'


def test_nonfinite_and_signed_zero_inputs_bitwise():
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
    expected, expected_Tg = call_fused(scene)
    actual, actual_Tg = call_prepared(scene)
    assert_exact(actual_Tg, expected_Tg, 'Tg after the call')
    assert_gvf_outputs(actual, expected)


def test_overflowing_tg_bitwise_nonfinite_masks():
    # Huge Tg drives the ^4 powers to inf and the Lup subtraction to NaN;
    # masks and payloads must survive preparation bit-exactly.
    scene = build_scene(19, 23, seed=5, water=True)
    scene['Tg'] = (scene['Tg'] * np.float32(1e33)).astype(np.float32)
    expected, expected_Tg = call_fused(scene)
    actual, actual_Tg = call_prepared(scene)
    assert_exact(actual_Tg, expected_Tg, 'Tg after the call')
    assert_gvf_outputs(actual, expected)


@pytest.mark.parametrize('mutation', ['zeros', 'ones', 'maxwalls'])
def test_degenerate_masks_and_walls(mutation):
    scene = build_scene(20, 26, seed=13, water=True)
    if mutation == 'zeros':
        scene['buildings'] = np.zeros_like(scene['buildings'])
    elif mutation == 'ones':
        scene['buildings'] = np.ones_like(scene['buildings'])
        scene['shadow'] = np.ones_like(scene['shadow'])
    else:
        scene['walls'] = np.full_like(scene['walls'], 3)
        scene['wallsun'] = scene['walls'].copy()
    expected, expected_Tg = call_fused(scene)
    actual, actual_Tg = call_prepared(scene)
    assert_exact(actual_Tg, expected_Tg, 'Tg after the call')
    assert_gvf_outputs(actual, expected)


@pytest.mark.parametrize('first,second', [(1.0, 1.0), (5.0, 2.0), (0.5, 6.0)])
def test_search_distance_corners(first, second):
    scene = build_scene(18, 19, seed=17, water=True, first=first, second=second)
    expected, expected_Tg = call_fused(scene)
    oracle, oracle_Tg = call_original(scene)
    actual, actual_Tg = call_prepared(scene)
    assert_exact(actual_Tg, expected_Tg, 'Tg after the call')
    assert_gvf_outputs(actual, expected)
    assert_gvf_outputs(actual, oracle)


def test_water_mask_without_water_cells_reuses_lup():
    # landcover == 1 but no lc_grid == 3 cell: the scatter lands nothing, so
    # one Lup evaluation must serve both states (stats say 1).
    from solweig_light.radiation import gvf_prepared
    scene = build_scene(20, 20, seed=19, water=False)
    scene['landcover'] = 1
    expected, expected_Tg = call_fused(scene)
    actual, actual_Tg = call_prepared(scene)
    assert_exact(actual_Tg, expected_Tg, 'Tg after the call')
    assert_gvf_outputs(actual, expected)
    step = gvf_prepared.prepare_gvf_step(**snapshots(scene))
    assert step is not None and step.lup_evaluations == 1


def test_preparation_stats_water_scene():
    from solweig_light.radiation import gvf_prepared
    scene = build_scene(20, 20, seed=23, water=True)
    step = gvf_prepared.prepare_gvf_step(**snapshots(scene))
    assert step is not None
    assert step.lup_evaluations == 2
    assert step.mutations == 1
    for name in ('aspect', 'lwall', 'albshadow', 'search_steps', 'postprocess_terms', 'sky_emis'):
        assert step.stats[name] == 1, name


@pytest.mark.parametrize('block_rows', [1, 3, 32, 10_000])
def test_block_row_variants(block_rows):
    scene = build_scene(23, 19, seed=29, water=True)
    expected, expected_Tg = call_fused(scene)
    actual, actual_Tg = call_prepared(scene, block_rows=block_rows)
    assert_exact(actual_Tg, expected_Tg, 'Tg after the call')
    assert_gvf_outputs(actual, expected)


def test_no_leakage_across_steps():
    # One prepared object per call: a second call with different inputs must
    # track the baseline, not any snapshot of the first call.
    scene_a = build_scene(21, 21, seed=31, water=True)
    scene_b = build_scene(21, 21, seed=32, water=True)
    scene_b['shadow'] = 1.0 - scene_b['shadow']
    scene_b['Tg'] = scene_b['Tg'] + np.float32(5.0)
    for scene in (scene_a, scene_b):
        expected, expected_Tg = call_fused(scene)
        actual, actual_Tg = call_prepared(scene)
        assert_exact(actual_Tg, expected_Tg, 'Tg after the call')
        assert_gvf_outputs(actual, expected)


def tg_alias_scenes(scene, alias_key, scalar_fill=None):
    """Builders rebinding ``alias_key`` and Tg onto one buffer.

    Raster keys share the whole array; scalar keys share a 0-d view of one
    water cell (filled with ``scalar_fill`` so the water mutation really
    moves the aliased value). Returns (builder, non-vacuity probe result).
    """
    row, col = np.argwhere(scene['lc_grid'] == 3)[0]
    scalar = np.asarray(scene[alias_key]).ndim == 0
    if scalar and scalar_fill is not None:
        scene['Tg'][:] = np.float32(scalar_fill)

    def aliased_scene():
        local = snapshots(scene)
        shared = local['Tg']
        if scalar:
            local[alias_key] = shared[row:row + 1, col:col + 1].reshape(())
        else:
            local[alias_key] = shared
        assert np.may_share_memory(np.asarray(local[alias_key]), local['Tg'])
        return local

    probe = aliased_scene()
    probe['Tg'][probe['lc_grid'] == 3] = np.float32(scene['Twater'] - scene['Ta'])
    aliased_value = np.asarray(probe[alias_key])
    non_vacuous = (aliased_value.ndim > 0 and
                   not np.array_equal(np.asarray(probe[alias_key]), np.asarray(snapshots(scene)[alias_key]))) \
        or (aliased_value.ndim == 0 and float(aliased_value) == float(np.float32(scene['Twater'] - scene['Ta'])))
    return aliased_scene, non_vacuous


GATED_ALIASES = {
    # raster keys: the water mutation travels through the shared buffer
    'buildings': None, 'shadow': None, 'alb_grid': None, 'walls': None,
    'lc_grid': 3.0, 'dirwalls': 3.0,
    # scalar keys aliased to a water cell whose fill the mutation overwrites
    'scale': 3.0, 'ewall': 3.0, 'albedo_b': 3.0, 'landcover': 1.0, 'Twater': 10.0,
}


@pytest.mark.parametrize('alias_key', sorted(GATED_ALIASES))
def test_gated_tg_aliases_delegate_to_fused(alias_key):
    # Every alias that defeats a once-per-call snapshot must leave Tg and
    # all outputs (or the raised exception type) identical to both
    # baselines; the delegate spy pins that the prepared entry hands the
    # untouched scene to the fused route.
    from solweig_light.radiation import engine, gvf_prepared, ground_view
    scene = build_scene(22, 18, seed=37, water=True)
    aliased_scene, non_vacuous = tg_alias_scenes(scene, alias_key, GATED_ALIASES[alias_key])
    ref_scene = aliased_scene()
    new_scene = aliased_scene()
    oracle_scene = aliased_scene()
    delegated = []

    def spy(*args, **kwargs):
        delegated.append(1)
        with np.errstate(invalid='ignore', divide='ignore'):
            return ground_view._gvf_fused(*args, **kwargs)

    with np.errstate(invalid='ignore', divide='ignore'):
        actual = outcome(lambda s: gvf_prepared.prepared_gvf_step(
            **{**s, 'parallel': True, 'block_rows': 32, 'delegate': spy}), new_scene)
        expected = outcome(lambda s: ground_view._gvf_fused(**s, parallel=True, block_rows=32), ref_scene)
        oracle = outcome(lambda s: engine.gvf_2018a_numpy(**s), oracle_scene)
    assert delegated, f'{alias_key} alias must delegate to the fused route'
    assert actual[0] == expected[0], alias_key
    assert oracle[0] == expected[0], f'baseline control ({alias_key}): {oracle[0]} vs {expected[0]}'
    if alias_key == 'Twater':
        assert non_vacuous, 'Twater alias control is vacuous'
    if expected[0] == 'ok':
        assert_exact(new_scene['Tg'], ref_scene['Tg'], 'aliased Tg after the call')
        assert_exact(oracle_scene['Tg'], ref_scene['Tg'], 'original aliased Tg after the call')
        assert_gvf_outputs(actual[1], expected[1])
        assert_gvf_outputs(actual[1], oracle[1])


POSITION_FAITHFUL_ALIASES = {
    # Read at the same pre/post-mutation points by both routes: exact with
    # the prepared snapshot, no delegation needed.
    'Tgwall': None,      # raster alias: Lwall is evaluated post-mutation
    'emis_grid': None,   # raster alias: Lup/sky terms are evaluated per state
    'first': 'view',     # 0-d view of a NON-water Tg cell
    'second': 'view',
}


def non_water_view_scenes(scene, key):
    """Builders rebinding a scalar scene entry to a 0-d view of one
    non-water Tg cell (the mutation cannot rewrite it, but every read still
    goes through the alias). The cell choice is deterministic per builder so
    every aliased scene aliases the SAME cell with the same value."""
    def aliased_scene():
        rng = np.random.default_rng(7)
        local = snapshots(scene)
        shared = local['Tg']
        while True:
            r, c = int(rng.integers(0, shared.shape[0])), int(rng.integers(0, shared.shape[1]))
            if local['lc_grid'][r, c] != 3:
                break
        local[key] = shared[r:r + 1, c:c + 1].reshape(())
        # Pin a sane step value into the shared cell: a raw Tg value (~287)
        # as a search distance trips the ray-schedule RuntimeError guard on
        # BOTH routes, which would test raise-parity instead of the prepared
        # read path. Writing the cell writes the alias (they share memory).
        shared[r, c] = np.float32(2.0 if key == 'first' else 6.0)
        assert np.may_share_memory(np.asarray(local[key]), local['Tg'])
        return local

    return aliased_scene


@pytest.mark.parametrize('alias_key', sorted(POSITION_FAITHFUL_ALIASES))
def test_position_faithful_aliases_stay_prepared_and_exact(alias_key):
    from solweig_light.radiation import engine, gvf_prepared, ground_view
    scene = build_scene(22, 18, seed=41, water=True)
    if POSITION_FAITHFUL_ALIASES[alias_key] == 'view':
        aliased_scene = non_water_view_scenes(scene, alias_key)
    else:
        aliased_scene, _ = tg_alias_scenes(scene, alias_key)
    ref_scene = aliased_scene()
    new_scene = aliased_scene()
    oracle_scene = aliased_scene()
    delegated = []

    def spy(*args, **kwargs):
        delegated.append(1)
        with np.errstate(invalid='ignore', divide='ignore'):
            return ground_view._gvf_fused(*args, **kwargs)

    with np.errstate(invalid='ignore', divide='ignore'):
        actual = gvf_prepared.prepared_gvf_step(**new_scene, parallel=True, block_rows=32, delegate=spy)
        expected = ground_view._gvf_fused(**ref_scene, parallel=True, block_rows=32)
        oracle = engine.gvf_2018a_numpy(**oracle_scene)
    assert not delegated, f'{alias_key} alias must stay on the prepared route'
    assert_exact(new_scene['Tg'], ref_scene['Tg'], 'aliased Tg after the call')
    assert_exact(oracle_scene['Tg'], ref_scene['Tg'], 'original aliased Tg after the call')
    assert_gvf_outputs(actual, expected)
    assert_gvf_outputs(actual, oracle)


def test_float64_derived_lup_conversion_preserved():
    # SBC as a float64 array makes Lup/Lwall float64; the value-changing
    # float32 snapshot conversion must run once per state and the raw
    # float64 lup_term must reach _postprocess_block exactly as the
    # baseline's inline expression does.
    scene = build_scene(20, 26, seed=45, water=True)
    scene['SBC'] = np.array([5.67051e-08])
    expected, expected_Tg = call_fused(scene)
    actual, actual_Tg = call_prepared(scene)
    assert_exact(actual_Tg, expected_Tg, 'Tg after the call')
    assert_gvf_outputs(actual, expected)


def test_scalar_float64_tgwall_broadcast():
    scene = build_scene(18, 19, seed=47, water=True)
    scene['Tgwall'] = np.float64(21.5)
    expected, expected_Tg = call_fused(scene)
    actual, actual_Tg = call_prepared(scene)
    assert_exact(actual_Tg, expected_Tg, 'Tg after the call')
    assert_gvf_outputs(actual, expected)


def test_float64_rasters_take_identical_fallback():
    scene = build_scene(14, 15, seed=49, water=True)
    scene['buildings'] = scene['buildings'].astype(np.float64)
    expected, expected_Tg = call_fused(scene)
    oracle, oracle_Tg = call_original(scene)
    actual, actual_Tg = call_prepared(scene)
    assert_exact(actual_Tg, expected_Tg, 'fallback Tg after the call')
    assert_gvf_outputs(actual, expected)
    assert_gvf_outputs(actual, oracle)


def test_unsupported_step_inputs_raise_identically():
    # Inputs _gvf_fused's guards reject: the prepared entry must delegate
    # BEFORE touching Tg, so the failing behavior is the baseline's.
    scene = build_scene(15, 17, seed=51, water=True)
    scene['first'] = np.array(np.nan, dtype=np.float32)
    expected = outcome(call_fused, scene)
    assert expected[0] == 'raise', 'NaN-first control is vacuous'
    actual = outcome(call_prepared, scene)
    assert actual[0] == expected[0] and actual[1] == expected[1]

    scene = build_scene(15, 17, seed=51, water=True)
    scene['second'] = np.array(0.0, dtype=np.float32)
    expected = outcome(call_fused, scene)
    actual = outcome(call_prepared, scene)
    assert actual[0] == expected[0] and actual[1] == expected[1]


def test_toggle_routes_everything_to_fused(monkeypatch):
    from solweig_light.radiation import gvf_prepared, ground_view
    scene = build_scene(19, 23, seed=53, water=True)
    delegated = []

    def spy(*args, **kwargs):
        delegated.append(1)
        with np.errstate(invalid='ignore', divide='ignore'):
            return ground_view._gvf_fused(*args, **kwargs)

    monkeypatch.setenv('SOLWEIG_LIGHT_GVF_PREPARE', '0')
    try:
        actual = gvf_prepared.prepared_gvf_step(**snapshots(scene), parallel=True, block_rows=32, delegate=spy)
    finally:
        monkeypatch.undo()
    expected, expected_Tg = call_fused(scene)
    assert delegated, 'kill switch must delegate without preparing anything'
    assert_gvf_outputs(actual, expected)


def test_dispatch_shape_parity():
    # The integration recipe calls prepared_gvf_step with the dispatch's
    # argument list; pin that this equals the dispatched fused result.
    scene = build_scene(64, 64, seed=57, water=True)
    expected, expected_Tg = call_fused(scene)
    actual, actual_Tg = call_prepared(scene, parallel=True, block_rows=32)
    assert_exact(actual_Tg, expected_Tg, 'Tg after the call')
    assert_gvf_outputs(actual, expected)
