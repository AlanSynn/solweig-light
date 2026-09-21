"""C6-02 cold producer/key census on a tiny real own-met TIFF workflow (L1).

Integrated-tree form (C6-70): the C6-10 recipe integration removed the
duplicate standalone production, so the historical D02 duplicate hypothesis
(two productions under two keys differing by exactly {construction,
standalone_implementation}; recorded in ``census_counts_cold-warm.json`` /
``census_counts_cache-disabled.json`` with schema ``c6-02-census-v1``) is
replaced by its fulfilled form: ONE production under ONE shared key
consulted by both routes.

The public ``thermal_comfort`` workflow runs once cold, then warm, then warm
after deleting only the legacy export artifacts, then once with
``cache_enabled=False`` on a fresh scene.  The real producers are wrapped, not
mocked: ``svf_calculator_compact``, ``GeometryStore.get_or_create``,
``GeometryStore.key_for`` and ``save_svf_zip_npz_outputs`` are call-through
counting/fingerprinting wrappers (see ``census_probe``).  The tile worker
child that the public workflow spawns for the simulation stage is instrumented
through a generated ``sitecustomize`` on its inherited PYTHONPATH, so the
production of one cold run is counted where it actually happens.

The fixture is a deterministic 96x96 dense_urban scene (explicit 32-pixel
motif, no RNG) following the pinned synthetic-input generator
``reports/p7_fixture_sources/00318d13e1441c4567b5baa6c7a0bd5bcf04ef5fbf577ff9d4e8f920475c7bf6.py``
with the reference own-met file copied byte-for-byte.  Run-scoped evidence
(counts, identities, keys, indicative durations) is persisted into the owned
evidence tree under new v2 names before any assertion, so a failing
census still records what actually happened and the v1 evidence stays
untouched.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path

os.environ.setdefault('NUMBA_NUM_THREADS', '2')  # census cap: at most two native threads in this process

import pytest

REPO = Path(__file__).resolve().parents[3]
SRC = REPO / 'src'
PROBE_DIR = Path(__file__).resolve().parent
EVIDENCE = REPO / 'optimization_v6_continue' / 'evidence' / 'census'
COMMIT = 'e7a2d6ec8594b234820e7783e0ca26d821de7f3d'
MET_SOURCE = REPO / 'tests' / 'reference' / 'small_original_cpu' / 'scene' / 'met.txt'
DATE = '2020-07-18'
SIZE = 96

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import census_probe  # noqa: E402  (local instrumentation module)


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def _dense_urban_motif(size):
    """Verbatim dense_urban branch of the pinned generator's geometry()."""
    import numpy as np
    dem = np.full((size, size), 3, dtype=np.float32)
    building = dem.copy()
    trees = np.zeros_like(dem)
    for row in range(0, size, 32):
        for col in range(0, size, 32):
            height = 16 + 8 * ((row // 32 + col // 32) % 3)
            building[row+4:row+28, col+4:col+28] += height
            building[row+12:row+20, col+12:col+20] = dem[row+12:row+20, col+12:col+20]
            trees[row+1:row+3, col+14:col+18] = 6
    return dem, building, trees


def build_scene(destination: Path) -> dict:
    import numpy as np
    from osgeo import gdal, osr
    gdal.UseExceptions()
    destination.mkdir(parents=True)
    dem, building, trees = _dense_urban_motif(SIZE)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(32618)
    transform = (583017.5 - SIZE / 2, 1., 0., 4506984. + SIZE / 2, 0., -1.)
    for name, values in (('DEM.tif', dem), ('Building_DSM.tif', building), ('Trees.tif', trees)):
        dataset = gdal.GetDriverByName('GTiff').Create(str(destination / name), SIZE, SIZE, 1, gdal.GDT_Float32)
        dataset.SetGeoTransform(transform)
        dataset.SetProjection(srs.ExportToWkt())
        dataset.GetRasterBand(1).WriteArray(values)
        dataset = None
        check = gdal.Open(str(destination / name))
        assert np.array_equal(check.ReadAsArray(), values), f'fixture read-back failed: {name}'
        check = None
    shutil.copyfile(MET_SOURCE, destination / 'met.txt')
    names = ('DEM.tif', 'Building_DSM.tif', 'Trees.tif', 'met.txt')
    return {'dir': destination, 'rows': SIZE, 'cols': SIZE, 'epsg': 32618,
            'transform': list(transform),
            'sha256': {name: _sha256(destination / name) for name in names},
            'generator_motif': 'dense_urban 32-pixel motif (pinned p7 generator 00318d13), no RNG',
            'met_source': 'tests/reference/small_original_cpu/scene/met.txt (byte-for-byte copy)'}


def arm_children(record_dir, tmp_path):
    """Make tile worker children import the probe through sitecustomize."""
    site_dir = Path(tmp_path) / 'sitecustomize_gen'
    site_dir.mkdir(exist_ok=True)
    (site_dir / 'sitecustomize.py').write_text(
        'import os, sys\n'
        'try:\n'
        '    probe = os.environ.get("SOLWEIG_CENSUS_PROBE_DIR")\n'
        '    if probe and probe not in sys.path:\n'
        '        sys.path.insert(0, probe)\n'
        '    import census_probe\n'
        '    census_probe.autostart()\n'
        'except Exception:\n'
        '    import traceback\n'
        '    traceback.print_exc(file=sys.stderr)\n', encoding='utf8')
    existing = os.environ.get('PYTHONPATH', '')
    parts = [str(site_dir), str(PROBE_DIR)] + ([existing] if existing else [])
    os.environ['PYTHONPATH'] = os.pathsep.join(parts)
    os.environ['SOLWEIG_CENSUS_PROBE_DIR'] = str(PROBE_DIR)
    os.environ['SOLWEIG_CENSUS_RECORD_DIR'] = str(record_dir)
    os.environ['SOLWEIG_CENSUS_ROLE'] = 'child'


def begin_stage(base_record_dir, stage, tmp_path):
    """One fresh record dir per stage so warm counts never see cold events."""
    stage_dir = Path(base_record_dir) / stage
    if stage_dir.exists():
        shutil.rmtree(stage_dir)
    stage_dir.mkdir(parents=True)
    arm_children(stage_dir, tmp_path)
    census_probe.rearm(stage_dir, 'parent')
    return stage_dir


def collect_events(record_dir):
    events = []
    for path in sorted(Path(record_dir).glob('*.jsonl')):
        for line in path.read_text(encoding='utf8').splitlines():
            if line.strip():
                events.append(json.loads(line))
    return events


def store_tree(scene):
    root = Path(scene) / 'processed_inputs' / '.solweig-light'
    entries = []
    if root.is_dir():
        for path in sorted(root.rglob('*')):
            entries.append({'path': str(path.relative_to(root)), 'dir': path.is_dir(),
                            'size': None if path.is_dir() else path.stat().st_size})
    return entries


def summarize(stage, scene_info, options_label, events, wall_s):
    svf = [e for e in events if e.get('event') == 'svf_call']
    store_calls = [e for e in events if e.get('event') == 'get_or_create']
    keys = [e for e in events if e.get('event') == 'key_for']
    exports = [e for e in events if e.get('event') == 'export']
    errors = [e for e in events if e.get('event') == 'census_error']
    identities = {call['route']: call['identity'] for call in store_calls if 'route' in call}
    identity_diff = {}
    if 'standalone' in identities and 'pipeline' in identities:
        only_standalone = sorted(set(identities['standalone']) - set(identities['pipeline']))
        only_pipeline = sorted(set(identities['pipeline']) - set(identities['standalone']))
        differing = sorted(name for name in set(identities['standalone']) & set(identities['pipeline'])
                           if identities['standalone'][name] != identities['pipeline'][name])
        identity_diff = {'only_in_standalone': only_standalone, 'only_in_pipeline': only_pipeline,
                         'differing_shared_fields': differing}
    equivalence = {}
    if len(svf) >= 2 and all(call.get('route') in ('standalone', 'pipeline') for call in svf[:2]):
        first, second = svf[0], svf[1]
        arrays = ('a', 'vegdem', 'vegdem2', 'bush')
        inputs_equal = all(first['inputs'][name] == second['inputs'][name] for name in arrays)
        scalars_equal = all(first['inputs'][name] == second['inputs'][name]
                            for name in ('patch_option', 'amaxvalue', 'scale'))
        outputs_equal = (first.get('outputs') is not None and first.get('outputs') == second.get('outputs'))
        equivalence = {'compared': [first.get('route'), second.get('route')],
                       'normalized_arrays_bitwise_equal': inputs_equal,
                       'scalars_equal': scalars_equal,
                       'outputs_bitwise_equal': outputs_equal,
                       'verdict': ('bitwise-identical-normalized-inputs-and-outputs'
                                   if inputs_equal and scalars_equal and outputs_equal else 'DIFFERS')}
    return {'schema': 'c6-02-census-run-v1', 'commit': COMMIT, 'stage': stage,
            'options': options_label,
            'scene': {name: (str(value) if isinstance(value, Path) else value)
                      for name, value in scene_info.items()},
            'counts': {'svf_calls': len(svf), 'get_or_create_calls': len(store_calls),
                       'key_for_calls': len(keys), 'export_calls': len(exports),
                       'productions': len(svf),
                       'by_route_svf': {route: sum(1 for call in svf if call.get('route') == route)
                                        for route in ('standalone', 'pipeline', 'unknown') if
                                        any(call.get('route') == route for call in svf)}},
            'store_calls': [{'route': call.get('route'), 'caller': call.get('caller'),
                             'key': call.get('key'), 'hit': call.get('hit'),
                             'producer_calls': call.get('producer_calls'),
                             'producer_duration_s': call.get('producer_duration_s'),
                             'duration_s': call.get('duration_s'),
                             'cache_root': call.get('cache_root')} for call in store_calls],
            'key_for': [{'route': call.get('route'), 'key': call.get('key')} for call in keys],
            'identities': identities, 'identity_diff': identity_diff,
            'equivalence': equivalence,
            'durations_s': {'total_stage_wall': wall_s,
                            'svf_calls': [{'route': call.get('route'),
                                           'duration_s': call.get('duration_s')} for call in svf],
                            'exports': [{'route': call.get('route'),
                                         'duration_s': call.get('duration_s')} for call in exports]},
            'store_tree': (scene_info or {}).pop('_store_tree', None),
            'events': events,
            'note': 'census durations, not benchmark: single small runs on a shared machine'}


def persist(payload, name):
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE / name
    path.write_text(json.dumps(payload, indent=1, sort_keys=True), encoding='utf8')
    return path


def thermal_comfort(scene):
    import dataclasses
    from solweig_light import RuntimeOptions, runtime_options, thermal_comfort as run
    from solweig_light.runtime import get_runtime_options
    # Explicit budget: the auto-resolved budget tracks transient available
    # host memory, which other local workers contend; these tests pin
    # production-counting behavior, not admission boundary sensitivity.
    # Merge with the ambient options so caller-set flags survive.
    merged = dataclasses.replace(get_runtime_options(),
                                 memory_budget_bytes=12 * 1024 ** 3)
    with runtime_options(merged):
        run(str(scene), DATE, own_met_file=str(scene / 'met.txt'), ERA_5_z0_find=False)


def test_cold_then_warm_producer_census(tmp_path):
    scene_info = build_scene(tmp_path / 'scene96')
    scene = scene_info['dir']
    record_dir = EVIDENCE / 'raw' / 'integrated-cold-warm'
    if record_dir.exists():
        shutil.rmtree(record_dir)
    record_dir.mkdir(parents=True)

    stages = []
    # Stage 1: cold full public workflow, default cache_enabled.
    stage_dir = begin_stage(record_dir, 'cold', tmp_path)
    start = time.perf_counter()
    thermal_comfort(scene)
    cold_wall = time.perf_counter() - start
    cold_events = collect_events(stage_dir)
    scene_info['_store_tree'] = store_tree(scene)
    stages.append(summarize('cold', dict(scene_info), 'defaults (cache_enabled=True)',
                            cold_events, cold_wall))

    # Stage 2: warm faithful repeat of the same public call on the same scene.
    stage_dir = begin_stage(record_dir, 'warm-faithful', tmp_path)
    start = time.perf_counter()
    thermal_comfort(scene)
    warm_a_wall = time.perf_counter() - start
    warm_a_events = collect_events(stage_dir)
    scene_info['_store_tree'] = store_tree(scene)
    stages.append(summarize('warm-faithful', dict(scene_info), 'defaults (cache_enabled=True)',
                            warm_a_events, warm_a_wall))

    # Stage 3: warm repeat after deleting only the legacy export artifacts and
    # the export manifest, so the routes must consult the native store again.
    svf_dir = scene / 'processed_inputs' / 'SVF'
    for name in ('svfs_0_0.zip', 'shadowmats_0_0.npz', 'SkyViewFactor_0_0.tif'):
        (svf_dir / name).unlink()
    (scene / 'processed_inputs' / '.solweig-light' / 'export-manifests' / 'geometry-exports_0_0.json').unlink()
    stage_dir = begin_stage(record_dir, 'warm-native-only', tmp_path)
    start = time.perf_counter()
    thermal_comfort(scene)
    warm_b_wall = time.perf_counter() - start
    warm_b_events = collect_events(stage_dir)
    scene_info['_store_tree'] = store_tree(scene)
    stages.append(summarize('warm-native-only', dict(scene_info), 'defaults (cache_enabled=True)',
                            warm_b_events, warm_b_wall))

    payload = {'schema': 'c6-02-census-integrated-v2', 'commit': COMMIT,
               'hypothesis': 'after the C6-10 recipe integration one cold public run '
                             'constructs geometry exactly once under one shared native key '
                             'consulted by both the standalone-export and pipeline routes.',
               'hypothesis_verdict': None, 'stages': stages}
    svf = stages[0]['counts']['by_route_svf']
    cold_keys = {call['key'] for call in stages[0]['store_calls'] if call.get('key')}
    if stages[0]['counts']['svf_calls'] == 1 and len(cold_keys) == 1:
        payload['hypothesis_verdict'] = ('CONFIRMED: one production, one shared key '
                                         '(historical duplicate confirmed separately in v1 evidence)')
    else:
        payload['hypothesis_verdict'] = 'REFUTED: more than one production or multiple keys (see counts)'
    path = persist(payload, 'census_counts_integrated_cold-warm.json')

    # Assertions run only after the evidence above is on disk.
    cold = stages[0]['counts']
    assert cold['svf_calls'] == 1, f'integrated cold run must produce exactly once, got {cold}'
    assert cold['get_or_create_calls'] == 2, f'both routes must consult the store cold: {cold}'
    cold_store = stages[0]['store_calls']
    hits = sorted(call['hit'] for call in cold_store)
    producers = sorted(call['producer_calls'] for call in cold_store)
    assert hits == [False, True] and producers == [0, 1], \
        f'exactly one cold production expected: {cold_store}'
    routes = {call['route']: call for call in cold_store}
    assert set(routes) == {'standalone', 'pipeline'}, f'unexpected routes: {sorted(routes)}'
    assert routes['standalone']['key'] == routes['pipeline']['key'], \
        f'both routes must share one native key: {cold_store}'
    assert routes['standalone']['cache_root'] == routes['pipeline']['cache_root'], 'same store root expected'

    warm_a = stages[1]['counts']
    assert warm_a['svf_calls'] == 0, f'warm faithful repeat must not produce: {warm_a}'
    assert warm_a['productions'] == 0, f'warm faithful repeat must not rebuild: {warm_a}'

    warm_b = stages[2]['counts']
    assert warm_b['svf_calls'] == 0, f'native warm repeat must not produce: {warm_b}'
    assert warm_b['get_or_create_calls'] == 2, f'both routes must consult the store warm: {warm_b}'
    assert all(call['hit'] is True and call['producer_calls'] == 0 for call in stages[2]['store_calls']), \
        f'native warm hits expected: {stages[2]["store_calls"]}'
    assert not stages[0]['events'] or not [e for e in stages[0]['events']
                                           if e.get('event') == 'census_error'], 'census errors recorded'
    assert path.exists()


def test_cache_disabled_producer_census(tmp_path):
    scene_info = build_scene(tmp_path / 'scene96')
    scene = scene_info['dir']
    record_dir = EVIDENCE / 'raw' / 'integrated-cache-disabled'
    if record_dir.exists():
        shutil.rmtree(record_dir)
    record_dir.mkdir(parents=True)
    stage_dir = begin_stage(record_dir, 'cache-disabled', tmp_path)

    from solweig_light import RuntimeOptions, runtime_options
    start = time.perf_counter()
    with runtime_options(RuntimeOptions(cache_enabled=False)):
        thermal_comfort(scene)
    wall = time.perf_counter() - start
    events = collect_events(stage_dir)
    scene_info['_store_tree'] = store_tree(scene)
    payload = {'schema': 'c6-02-census-integrated-v2', 'commit': COMMIT,
               'stages': [summarize('cache-disabled', dict(scene_info),
                                    'RuntimeOptions(cache_enabled=False)', events, wall)]}
    persist(payload, 'census_counts_integrated_cache-disabled.json')

    counts = payload['stages'][0]['counts']
    # Cache-disabled keeps the historical behavior: both routes produce
    # independently because the shared native key only deduplicates through
    # the store (the C6-10 saving is a cache-regime effect).
    assert counts['svf_calls'] == 2, f'cache-disabled must still produce twice: {counts}'
    assert counts['get_or_create_calls'] == 0 and counts['key_for_calls'] == 0, \
        f'no native store use allowed: {counts}'
    generations = [entry for entry in scene_info['_store_tree']
                   if entry['path'].startswith('cache') and not entry['dir']]
    assert not generations, f'nothing may be persisted to the native store: {generations}'


def teardown_function(function):
    os.environ.pop('SOLWEIG_CENSUS_RECORD_DIR', None)
    os.environ.pop('SOLWEIG_CENSUS_ROLE', None)
