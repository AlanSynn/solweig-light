"""C6-30 completion gate 2: actual repeated-expression evaluation counts.

Counts real evaluations by wrapping the exact functions the routes call:
ground_view._lup_expression (module-global lookup inside _gvf_fused, so the
wrapper is seen) and engine._operate/_divide (function-level imports inside
the routes, resolved from the engine module at call time). No timing.
"""
import numpy as np
import pytest

from gvf_prepare_cases import build_scene, snapshots


class Counting:
    def __init__(self, target, attribute, owner):
        self.owner = owner
        self.attribute = attribute
        self.target = target
        self.count = 0

    def __call__(self, *args, **kwargs):
        self.count += 1
        return self.target(*args, **kwargs)

    def __enter__(self):
        setattr(self.owner, self.attribute, self)
        return self

    def __exit__(self, *exc):
        setattr(self.owner, self.attribute, self.target)
        return False


def test_lup_expression_evaluations_reduction():
    # Baseline _gvf_fused evaluates the Lup expression twice per direction
    # (gather + postprocessed lup_term) = 36 evaluations per call. The
    # prepared route evaluates it once pre-mutation (direction 1's gather)
    # and once post-mutation (directions 2..18 + lup_term).
    from solweig_light.radiation import engine, gvf_prepared, ground_view
    scene = build_scene(64, 64, seed=61, water=True)
    with Counting(ground_view._lup_expression, '_lup_expression', ground_view):
        with np.errstate(invalid='ignore', divide='ignore'):
            ground_view._gvf_fused(**snapshots(scene), parallel=True, block_rows=32)
        fused_count = ground_view._lup_expression.count
    with Counting(ground_view._lup_expression, '_lup_expression', ground_view):
        with np.errstate(invalid='ignore', divide='ignore'):
            gvf_prepared.prepared_gvf_step(**snapshots(scene), parallel=True, block_rows=32)
        prepared_count = ground_view._lup_expression.count
    assert fused_count == 36, fused_count
    assert prepared_count == 2, prepared_count


def test_lup_expression_single_evaluation_without_water():
    from solweig_light.radiation import engine, gvf_prepared, ground_view
    scene = build_scene(64, 64, seed=63, water=False)
    with Counting(ground_view._lup_expression, '_lup_expression', ground_view):
        with np.errstate(invalid='ignore', divide='ignore'):
            ground_view._gvf_fused(**snapshots(scene), parallel=True, block_rows=32)
        fused_count = ground_view._lup_expression.count
    with Counting(ground_view._lup_expression, '_lup_expression', ground_view):
        with np.errstate(invalid='ignore', divide='ignore'):
            gvf_prepared.prepared_gvf_step(**snapshots(scene), parallel=True, block_rows=32)
        prepared_count = ground_view._lup_expression.count
    assert fused_count == 36, fused_count
    assert prepared_count == 1, prepared_count


def test_operate_call_reduction():
    # Aggregate repeated arithmetic: every numpy elementwise op in both
    # routes flows through engine._operate. The prepared route removes the
    # 17 once-per-direction expression trees; direction-dependent trees
    # (azilow/azihigh/facesh) and the block postprocess remain per direction
    # in both routes.
    from solweig_light.radiation import engine, gvf_prepared, ground_view
    scene = build_scene(64, 64, seed=65, water=True)
    counts = {}
    for name in ('fused', 'prepared'):
        wrapper = Counting(engine._operate, '_operate', engine)
        with wrapper:
            with np.errstate(invalid='ignore', divide='ignore'):
                if name == 'fused':
                    ground_view._gvf_fused(**snapshots(scene), parallel=True, block_rows=32)
                else:
                    gvf_prepared.prepared_gvf_step(**snapshots(scene), parallel=True, block_rows=32)
        counts[name] = wrapper.count
    assert counts['prepared'] < counts['fused'], counts
    # The reduction spans the once-per-direction trees the preparation
    # removes (Lup ~10 ops x36 evals, lup_term wrapper tree, Lwall ~9,
    # albshadow, aspect, first/second, alb/nosh terms, post-loop sky x5),
    # minus the once-per-call prepared evaluations. The precise Lup-tree
    # reduction is pinned by the _lup_expression tests above; this floor
    # stays far below the measured gap so only a real regression trips it.
    assert counts['fused'] - counts['prepared'] >= 600, counts


def test_per_direction_expressions_survive_for_direction_dependent_work():
    # The route must NOT skip the direction-dependent trees: azilow/azihigh
    # and facesh stay per direction, and ray schedules stay per direction.
    from solweig_light.radiation import engine, gvf_prepared, ground_view
    scene = build_scene(32, 32, seed=67, water=True)
    schedules = Counting(ground_view.ray_schedule, 'ray_schedule', ground_view)
    with schedules:
        with np.errstate(invalid='ignore', divide='ignore'):
            gvf_prepared.prepared_gvf_step(**snapshots(scene), parallel=True, block_rows=32)
    assert schedules.count == 18
