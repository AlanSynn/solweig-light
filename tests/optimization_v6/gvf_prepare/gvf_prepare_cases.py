"""Shared scene builder and bitwise helpers for the C6-30 prepared-GVF tests.

The scene builder mirrors tests/optimization_v5/gvf/test_g02_source_hoisting
(build_scene) so fixtures stay comparable across the two suites; it is copied
rather than imported to keep the suites independently runnable.
"""
import numpy as np

SBC = 5.67051e-08


def build_scene(rows, cols, seed=0, water=False, with_buildings=True,
                first=2.0, second=6.0, scale=1.0):
    rng = np.random.default_rng(seed)
    walls = rng.integers(0, 4, size=(rows, cols)).astype(np.float32)
    wallsun = np.where(rng.random((rows, cols)) < 0.4, walls, 0).astype(np.float32)
    if with_buildings:
        buildings = (rng.random((rows, cols)) < 0.3).astype(np.float32)
    else:
        buildings = np.zeros((rows, cols), np.float32)
    shadow = (rng.random((rows, cols)) < 0.6).astype(np.float32)
    dirwalls = (rng.random((rows, cols)) * 360.0).astype(np.float32)
    Tg = (273.0 + 20.0 * rng.random((rows, cols))).astype(np.float32)
    lc_grid = np.zeros((rows, cols), np.int32)
    if water:
        lc_grid[rows // 3:max(rows // 3 + 2, rows // 2), cols // 4:cols // 2] = 3
    emis_grid = np.full((rows, cols), 0.92, np.float32)
    emis_grid[rng.random((rows, cols)) < 0.2] = 0.85
    alb_grid = np.full((rows, cols), 0.18, np.float32)
    alb_grid[rng.random((rows, cols)) < 0.15] = 0.35
    Tgwall = (np.asarray(21.0, dtype=np.float32) * np.ones((rows, cols), np.float32)
              if seed % 2 else np.asarray(21.0, dtype=np.float32))
    return dict(
        wallsun=wallsun, walls=walls, buildings=buildings, scale=np.float32(scale),
        shadow=shadow, first=np.array(first, dtype=np.float32),
        second=np.array(second, dtype=np.float32), dirwalls=dirwalls, Tg=Tg,
        Tgwall=Tgwall, Ta=21.0, emis_grid=emis_grid, ewall=0.88, alb_grid=alb_grid,
        SBC=np.float32(SBC), albedo_b=0.15, Twater=295.0, lc_grid=lc_grid,
        landcover=1 if water else 0, rows=rows, cols=cols,
    )


def snapshots(scene):
    return {key: (value.copy() if isinstance(value, np.ndarray) and value.ndim else value)
            for key, value in scene.items()}


def as_bits(value):
    if value.dtype == np.float32:
        return np.ascontiguousarray(value).view(np.uint32)
    if value.dtype == np.float64:
        return np.ascontiguousarray(value).view(np.uint64)
    return np.ascontiguousarray(value)


def assert_exact(actual, expected, label):
    assert actual.dtype == expected.dtype, label
    assert actual.shape == expected.shape, label
    np.testing.assert_array_equal(as_bits(actual), as_bits(expected), err_msg=label)


GVF_NAMES = ['gvfLup', 'gvfalb', 'gvfalbnosh', 'gvfLupE', 'gvfalbE', 'gvfalbnoshE',
             'gvfLupS', 'gvfalbS', 'gvfalbnoshS', 'gvfLupW', 'gvfalbW', 'gvfalbnoshW',
             'gvfLupN', 'gvfalbN', 'gvfalbnoshN', 'gvfSum', 'gvfNorm']


def assert_gvf_outputs(actual, expected):
    assert len(actual) == len(expected) == 17
    for index, name in enumerate(GVF_NAMES):
        assert_exact(actual[index], expected[index], name)


def call_prepared(scene, **kwargs):
    """prepared_gvf_step over a fresh snapshot of ``scene``; returns outputs
    and the post-call Tg for bitwise comparison of caller-visible state."""
    from solweig_light.radiation import gvf_prepared
    local = snapshots(scene)
    with np.errstate(invalid='ignore', divide='ignore'):
        outputs = gvf_prepared.prepared_gvf_step(**local, **kwargs)
    return outputs, local['Tg']


def call_fused(scene):
    from solweig_light.radiation import ground_view
    local = snapshots(scene)
    with np.errstate(invalid='ignore', divide='ignore'):
        outputs = ground_view._gvf_fused(**local, parallel=True, block_rows=32)
    return outputs, local['Tg']


def call_original(scene):
    """The true original engine body (pre-G02/G03 NumPy implementation)."""
    from solweig_light.radiation import engine
    local = snapshots(scene)
    with np.errstate(invalid='ignore', divide='ignore'):
        outputs = engine.gvf_2018a_numpy(**local)
    return outputs, local['Tg']
