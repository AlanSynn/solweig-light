"""C6-10 gates 2+3 at the recipe/store level: one production, rejection of
corrupted or stale cached inputs.

Gate 2 (recipe-level guarantee): when both routes request geometry through
the shared recipe against one store root, exactly one full numerical
production runs cold and zero run warm. The genuine end-to-end
``thermal_comfort`` demonstration (including the service-side wiring) lives
in ``test_end_to_end_single_production.py`` because ``service.py`` is
integrator-owned; this module proves the recipe-level property the
integration relies on.

Gate 3: corrupted array payloads, corrupted visibility payloads, forged
manifests and changed source rasters are all rejected and rebuilt from the
real producer — the store's producer is the only oracle, and the recipe
never serves stale bytes.

No numerical mocks: the SVF producer is only wrapped call-through to count
invocations. Evidence is persisted before assertions.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

os.environ.setdefault('NUMBA_NUM_THREADS', '2')  # development thread cap, before numba imports

import numpy as np
import pytest

from scene_fixtures import EPSG, REPO, SRC, SIZE, TRANSFORM, build_scene, fields_equal

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from solweig_light.cache import GeometryStore  # noqa: E402
from solweig_light.geometry.recipe import guarded_producer, numerical_geometry_recipe  # noqa: E402

EVIDENCE = REPO / 'development/optimization_v6_continue' / 'evidence' / 'recipe'
COMMIT = 'e7a2d6ec8594b234820e7783e0ca26d821de7f3d'


class _SvfCounter:
    """Call-through counting wrapper around the real svf_calculator_compact."""

    def __init__(self):
        self.calls = 0

    def install(self):
        import solweig_light.geometry.svf as svf_module
        self._original = svf_module.svf_calculator_compact
        counter = self

        def wrapper(*args, **kwargs):
            counter.calls += 1
            return counter._original(*args, **kwargs)

        svf_module.svf_calculator_compact = wrapper
        return self

    def remove(self):
        import solweig_light.geometry.svf as svf_module
        svf_module.svf_calculator_compact = self._original


def _scene(tmp_path):
    info = build_scene(tmp_path / 'scene96')
    scene_dir = info.pop('dir')
    paths = {name: scene_dir / f'{name}.tif' for name in ('Building_DSM', 'Trees', 'DEM')}
    return paths, info


def _dense(handle):
    """Materialize every field before the handle (and its memmaps) closes."""
    out = {}
    for name, value in handle.fields.items():
        if hasattr(value, 'to_dense'):
            out[name] = np.ascontiguousarray(value.to_dense())
        else:
            out[name] = np.array(value, copy=True)
    return out


def _corrupt_bytes(path, offset):
    """Flip one byte of a published (0o444) cache payload after chmod."""
    path.chmod(path.stat().st_mode | 0o200)
    data = bytearray(path.read_bytes())
    data[offset] ^= 0xFF
    path.write_bytes(bytes(data))
    path.chmod(path.stat().st_mode & ~0o200)


def _generations(store_root, key):
    directory = store_root / key
    return sorted(path.name for path in directory.glob('generation-*')) if directory.is_dir() else []


def _first_generation(store_root, key):
    return store_root / key / _generations(store_root, key)[0]


def test_two_routes_one_shared_recipe_single_cold_production(tmp_path):
    paths, scene_info = _scene(tmp_path)
    store_root = tmp_path / 'store'
    store = GeometryStore(store_root)
    counter = _SvfCounter().install()
    export_identity = None
    try:
        # Route 1 (pipeline-shaped): recipe + guarded producer through the store.
        recipe_pipeline = numerical_geometry_recipe(paths, 2)
        handle_1 = store.get_or_create(recipe_pipeline.identity, guarded_producer(recipe_pipeline))
        fields_1 = _dense(handle_1)
        record_pipeline = {'hit': handle_1.hit, 'key': handle_1.key,
                           'digest': recipe_pipeline.digest}
        handle_1.close()

        # Route 2 (standalone-shaped): fresh recipe object, same sources; its
        # export identity is separate and never enters the native key.
        recipe_standalone = numerical_geometry_recipe(paths, 2)
        export_identity = recipe_standalone.export_identity(
            construction='standalone-svf-v1',
            exporter_implementation={'size_bytes': 1, 'sha256': 'standalone-wrapper-placeholder'})
        handle_2 = store.get_or_create(recipe_standalone.identity, guarded_producer(recipe_standalone))
        fields_2 = _dense(handle_2)
        record_standalone = {'hit': handle_2.hit, 'key': handle_2.key,
                             'digest': recipe_standalone.digest,
                             'export_identity': export_identity}
        handle_2.close()

        # Warm repeat through either route: zero productions.
        recipe_warm = numerical_geometry_recipe(paths, 2)
        handle_3 = store.get_or_create(recipe_warm.identity, guarded_producer(recipe_warm))
        record_warm = {'hit': handle_3.hit, 'key': handle_3.key}
        fields_warm = _dense(handle_3)
        handle_3.close()
    finally:
        counter.remove()

    parity = fields_equal(fields_2, fields_1)
    payload = {'schema': 'c6-10-recipe-single-production-v1', 'commit': COMMIT,
               'scene_inputs_sha256': scene_info.get('sha256'),
               'svf_producer_calls_total': counter.calls,
               'records': {'route_pipeline': record_pipeline,
                           'route_standalone': record_standalone,
                           'warm_repeat': record_warm},
               'cached_fields_bitwise_equal_cold': parity,
               'generations_for_key': _generations(store_root, record_pipeline['key'])}
    out = EVIDENCE / 'raw' / 'recipe_single_production.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=1, sort_keys=True))

    assert counter.calls == 1, f'expected exactly ONE production for both routes, got {counter.calls}'
    assert record_pipeline['hit'] is False, 'cold route must miss and produce'
    assert record_standalone['hit'] is True, 'second route must hit the shared generation'
    assert record_warm['hit'] is True
    assert record_pipeline['key'] == record_standalone['key'] == record_warm['key']
    assert record_pipeline['digest'] == record_standalone['digest']
    assert export_identity['construction'] == 'standalone-svf-v1'
    assert all(parity.values()), 'cached generation must be bitwise identical to cold fields'
    assert all(fields_equal(fields_warm, fields_1).values()), 'warm fields must match cold fields bitwise'
    assert len(_generations(store_root, record_pipeline['key'])) == 1
    assert out.exists()


@pytest.mark.parametrize('corruption', ['array_payload', 'visibility_payload', 'forged_manifest'])
def test_corrupted_cache_rejected_and_rebuilt(tmp_path, corruption):
    paths, _ = _scene(tmp_path)
    store_root = tmp_path / 'store'
    store = GeometryStore(store_root)
    counter = _SvfCounter().install()
    try:
        recipe = numerical_geometry_recipe(paths, 2)
        handle = store.get_or_create(recipe.identity, guarded_producer(recipe))
        key = handle.key
        reference = _dense(handle)
        handle.close()
        assert counter.calls == 1
        counter.calls = 0

        generation = _first_generation(store_root, key)
        if corruption == 'array_payload':
            _corrupt_bytes(generation / 'svf.npy', offset=512)
        elif corruption == 'visibility_payload':
            channel_manifest = json.loads((generation / 'shmat.json').read_text())
            _corrupt_bytes(generation / channel_manifest['payload']['name'], offset=256)
        else:
            manifest_path = store_root / key / 'manifest.json'
            manifest = json.loads(manifest_path.read_text())
            manifest['identity']['patch_option'] = 999
            # Forge a self-consistent digest so only the identity check can
            # reject it: the store must still refuse to serve the payload.
            digest = hashlib.sha256(json.dumps(
                {k: v for k, v in manifest.items() if k != 'manifest_sha256'},
                sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            manifest['manifest_sha256'] = digest
            manifest_path.chmod(manifest_path.stat().st_mode | 0o200)
            manifest_path.write_text(json.dumps(manifest, sort_keys=True, separators=(',', ':')))
            manifest_path.chmod(manifest_path.stat().st_mode & ~0o200)

        recipe_after = numerical_geometry_recipe(paths, 2)
        handle = store.get_or_create(recipe_after.identity, guarded_producer(recipe_after))
        rebuilt = _dense(handle)
        payload = {'schema': 'c6-10-recipe-corruption-v1', 'commit': COMMIT, 'corruption': corruption,
                   'rebuild_hit': handle.hit, 'svf_producer_calls_after_corruption': counter.calls,
                   'generations_after': _generations(store_root, key),
                   'rebuilt_fields_bitwise_equal_reference': fields_equal(rebuilt, reference)}
        handle.close()
    finally:
        counter.remove()
    out = EVIDENCE / 'raw' / f'corruption_{corruption}.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=1, sort_keys=True))

    assert payload['rebuild_hit'] is False, 'corrupt cache must not be served as a hit'
    assert payload['svf_producer_calls_after_corruption'] == 1, 'producer must rebuild corrupted cache'
    assert all(payload['rebuilt_fields_bitwise_equal_reference'].values())
    assert out.exists()


def test_stale_source_raster_rekeyed_and_reproduced(tmp_path):
    paths, _ = _scene(tmp_path)
    store_root = tmp_path / 'store'
    store = GeometryStore(store_root)
    counter = _SvfCounter().install()
    try:
        recipe_old = numerical_geometry_recipe(paths, 2)
        handle_old = store.get_or_create(recipe_old.identity, guarded_producer(recipe_old))
        key_old = handle_old.key
        fields_old = _dense(handle_old)
        handle_old.close()
        assert counter.calls == 1
        counter.calls = 0

        # Mutate real source content: taller trees on one motif block, same
        # geometry metadata (write-then-replace keeps the TIFF consistent).
        from osgeo import gdal, osr
        path = paths['Trees']
        dataset = gdal.Open(str(path))
        values = dataset.GetRasterBand(1).ReadAsArray()
        dataset = None
        values[4:28, 4:28] = np.float32(11.0)
        staged = path.with_suffix('.staged.tif')
        driver = gdal.GetDriverByName('GTiff')
        updated = driver.Create(str(staged), values.shape[1], values.shape[0], 1, gdal.GDT_Float32)
        updated.SetGeoTransform(TRANSFORM)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(EPSG)
        updated.SetProjection(srs.ExportToWkt())
        updated.GetRasterBand(1).WriteArray(values)
        updated = None
        staged.replace(path)

        recipe_new = numerical_geometry_recipe(paths, 2)
        handle_new = store.get_or_create(recipe_new.identity, guarded_producer(recipe_new))
        key_new = handle_new.key
        fields_new = _dense(handle_new)
        changed = {name: not same for name, same in fields_equal(fields_old, fields_new).items()}
        payload = {'schema': 'c6-10-recipe-stale-input-v1', 'commit': COMMIT,
                   'key_old': key_old, 'key_new': key_new,
                   'stale_hit': handle_new.hit,
                   'svf_producer_calls_after_source_change': counter.calls,
                   'old_generation_preserved': _generations(store_root, key_old),
                   'fields_changed': {name: changed[name] for name in sorted(changed) if changed[name]},
                   'fields_changed_somewhere': any(changed.values())}
        handle_new.close()
    finally:
        counter.remove()
    out = EVIDENCE / 'raw' / 'stale_input.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=1, sort_keys=True))

    assert key_new != key_old, 'changed source must rekey'
    assert payload['stale_hit'] is False, 'changed source must not be served from the old generation'
    assert payload['svf_producer_calls_after_source_change'] == 1
    assert payload['old_generation_preserved'], 'old generations are immutable and remain on disk'
    assert payload['fields_changed_somewhere'], 'sanity: changed trees must change svf'
    assert out.exists()
