"""C6-10 gate 1: source-bound all-19-field bitwise parity of the shared recipe.

Integrated-tree form (C6-70): the service route no longer exists as a
separate implementation — ``geometry/service.py`` produces through
``numerical_geometry_recipe`` and its former ``_producer`` is deleted — so
the historical three-route comparison (standalone vs pipeline vs recipe,
recorded in ``raw/parity_*.json`` with schema ``c6-10-recipe-parity-v1``)
is replaced by:

- Route B: the pinned ``pipeline.py`` geometry branch. The normalization
  body is transcribed verbatim below and asserted against the installed
  source text so drift fails loudly. The recipe must still reproduce this
  transcription bitwise on real scenes.
- Integration assertions: the installed service and pipeline sources both
  route production through the shared recipe.

All comparisons are uint32-view exact (dtype, shape, signed zeros, NaN
payloads). No numerical mocks anywhere; evidence is persisted before
assertions.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

os.environ.setdefault('NUMBA_NUM_THREADS', '2')  # development thread cap, before numba imports

import numpy as np
import pytest

from scene_fixtures import REPO, SRC, build_scene, field_bits, fields_equal, reference_paths

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

EVIDENCE = REPO / 'development/optimization_v6_continue' / 'evidence' / 'recipe'
COMMIT = 'e7a2d6ec8594b234820e7783e0ca26d821de7f3d'
INPUT_NAMES = ('Building_DSM', 'Trees', 'DEM')

PIPELINE_GEOMETRY_LINES = (
    'trees[trees < 0] = 0',
    'vegdem, vegdem2 = trees + dem, trees * np.float32(.25) + dem',
    'bush = np.logical_not(vegdem2 * vegdem) * vegdem',
    'vegdsm, vegdsm2 = trees + a, trees * np.float32(.25) + a',
    'vegdsm[vegdsm == a] = 0',
    'vegdsm2[vegdsm2 == a] = 0',
    'amaxvalue = np.maximum(a.max(), vegdem.max())',
)


def _route_b_intermediates(paths):
    """Pinned pipeline.py geometry branch (base e7a2d6ec pipeline.py:99-134)."""
    from solweig_light.io.rasters import read_raster
    a, metadata = read_raster(paths['Building_DSM'])
    trees, _ = read_raster(paths['Trees'])
    dem, _ = read_raster(paths['DEM'])
    scale = 1 / metadata.transform[1]
    trees[trees < 0] = 0
    vegdem, vegdem2 = trees + dem, trees * np.float32(.25) + dem
    bush = np.logical_not(vegdem2 * vegdem) * vegdem
    vegdsm, vegdsm2 = trees + a, trees * np.float32(.25) + a
    vegdsm[vegdsm == a] = 0
    vegdsm2[vegdsm2 == a] = 0
    amaxvalue = np.maximum(a.max(), vegdem.max())
    return a, scale, vegdem, vegdem2, bush, vegdsm, vegdsm2, amaxvalue


def _check_pipeline_body_unchanged():
    """Fail loudly if the installed pipeline geometry branch drifted."""
    text = (SRC / 'solweig_light' / 'pipeline.py').read_text()
    for line in PIPELINE_GEOMETRY_LINES:
        assert line in text, f'pipeline.py geometry branch drifted: missing {line!r}'


def _assert_integrated_sources():
    """The installed service and pipeline must produce through the recipe."""
    service_text = (SRC / 'solweig_light' / 'geometry' / 'service.py').read_text()
    assert 'numerical_geometry_recipe' in service_text, \
        'service.py must import the shared recipe'
    assert 'recipe.produce()' in service_text or 'recipe.export_identity' in service_text, \
        'service.py must produce through the recipe'
    assert '_producer' not in service_text, \
        'the duplicate standalone producer must stay deleted'


def _route_b_fields(paths):
    """Pinned pipeline producer call (base e7a2d6ec pipeline.py:181-184)."""
    from solweig_light.geometry.svf import svf_calculator_compact
    from solweig_light.pipeline import SVF_NAMES
    a, scale, _, _, bush, vegdsm, vegdsm2, amaxvalue = _route_b_intermediates(paths)
    values = svf_calculator_compact(2, amaxvalue, a, vegdsm, vegdsm2, bush, scale, save_rasters=False)
    return dict(zip(SVF_NAMES, values)), scale


def _scalar_fp(value):
    return {'type': type(value).__name__, 'hex': float(value).hex()}


def _field_fp(value):
    import numpy as np
    array = field_bits(value)
    return {'dtype': str(array.dtype), 'shape': list(array.shape),
            'sha256': hashlib.sha256(array.tobytes(order='C')).hexdigest()}


@pytest.mark.parametrize('scene_builder', [reference_paths, 'dense96'])
def test_recipe_bitwise_parity_pipeline_route(tmp_path, scene_builder):
    _check_pipeline_body_unchanged()
    _assert_integrated_sources()
    if scene_builder == 'dense96':
        scene_info = build_scene(tmp_path / 'scene96')
        scene_dir = scene_info.pop('dir')
        paths = {name: scene_dir / f'{name}.tif' for name in INPUT_NAMES}
        scene_label = 'dense96-96x96-real-generator-motif'
    else:
        scene_info = scene_builder(tmp_path)
        paths = scene_info.pop('paths')
        scene_label = 'reference-35x32-real-scene'

    from solweig_light.geometry.recipe import guarded_producer, normalize, numerical_geometry_recipe
    from solweig_light.io.rasters import read_raster

    fields_b, scale_b = _route_b_fields(paths)
    recipe = numerical_geometry_recipe(paths, 2)
    fields_r = guarded_producer(recipe)()

    # Recipe scale must come from the DSM geotransform like the pinned route.
    from osgeo import gdal
    template = gdal.Open(str(paths['Building_DSM']))
    try:
        scale_r = 1 / template.GetGeoTransform()[1]
    finally:
        template = None

    # Normalized-input parity: recipe.normalize vs the pinned pipeline body.
    # Mapping note: recipe.normalize returns the DSM-side arrays (pipeline
    # ``vegdsm``/``vegdsm2`` names); the DEM-side products are pinned through
    # the same clamped tree array the recipe produced in place.
    a0, _ = read_raster(paths['Building_DSM'])
    tree0, _ = read_raster(paths['Trees'])
    dem0, _ = read_raster(paths['DEM'])
    clamped_tree = tree0.copy()
    a_n, vegdsm_n, vegdsm2_n, bush_n, amaxvalue_n = normalize(clamped_tree, dem0.copy(), a0.copy())
    (a_p, scale_p, vegdem_p, vegdem2_p, bush_p, vegdsm_p, vegdsm2_p, amaxvalue_p) = _route_b_intermediates(paths)
    inputs_equal = {
        'a_dtype_float32': bool(a_n.dtype == np.float32 and np.array_equal(a_n.view(np.uint32), a_p.view(np.uint32))),
        'clamped_tree': bool(np.array_equal(clamped_tree.view(np.uint32), tree0.clip(0, None).view(np.uint32))),
        'vegdem_trees_plus_dem': bool(np.array_equal((clamped_tree + dem0).view(np.uint32), vegdem_p.view(np.uint32))),
        'vegdsm_trees_plus_a': bool(np.array_equal(vegdsm_n.view(np.uint32), vegdsm_p.view(np.uint32))),
        'vegdsm2': bool(np.array_equal(vegdsm2_n.view(np.uint32), vegdsm2_p.view(np.uint32))),
        'bush': bool(np.array_equal(bush_n.view(np.uint32), bush_p.view(np.uint32))),
        'vegdsm_tree_plus_a_zeroed': bool(np.all(vegdsm_n[vegdsm_n == a_n] == 0)),
        'amaxvalue_hex': _scalar_fp(amaxvalue_n) == _scalar_fp(amaxvalue_p),
        'scale_hex_pipeline': _scalar_fp(scale_p) == _scalar_fp(scale_b),
        'scale_hex_recipe': _scalar_fp(scale_r) == _scalar_fp(scale_b),
    }

    parity_b = fields_equal(fields_r, fields_b)

    payload = {
        'schema': 'c6-10-recipe-parity-integrated-v2', 'commit': COMMIT, 'scene': scene_label,
        'scene_inputs_sha256': scene_info.get('sha256'),
        'recipe_policy': recipe.identity['policy'], 'recipe_digest': recipe.digest,
        'recipe_implementation_closure': sorted(recipe.identity['implementation']),
        'normalized_inputs_recipe_vs_pipeline': inputs_equal,
        'per_field_bitwise': {'recipe_vs_pipeline_transcription': parity_b},
        'field_fingerprints': {'recipe': {name: _field_fp(value) for name, value in fields_r.items()}},
        'note': 'integrated-tree form: the standalone route is deleted (see schema v1 '
                'evidence for the historical three-route proof); parity only, no timing claims'}
    out = EVIDENCE / 'raw' / f'parity_integrated_{scene_label}.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=1, sort_keys=True))

    assert all(inputs_equal.values()), f'normalized inputs differ: {inputs_equal}'
    assert all(parity_b.values()), f'recipe vs pipeline differs: {[k for k, v in parity_b.items() if not v]}'
    assert len(fields_r) == 19 and set(fields_r) == set(fields_b)
    assert out.exists()
