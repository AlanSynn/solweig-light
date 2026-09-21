"""C6-10 gate 2 end-to-end: one geometry production per cold tile in a real
public ``thermal_comfort`` run when cache is enabled.

``service.py`` is integrator-owned, so the service half of the integration
is simulated by loading the DIFF POST-IMAGE of ``geometry/service.py``: the
owned proposal ``integration_patch_C6-10.diff`` is applied with ``git apply``
to a private copy of the installed base service module, which is then used
in place of ``prepare_geometry_exports`` (labeled service-path patch; every
numerical kernel inside it is the real code). The pipeline half is simulated
in the tile-worker child by ``recipe_probe`` (identity-only patch; the
child's producer is the unmodified ``pipeline.py`` producer whose fields the
parity test proves bitwise identical to the recipe producer's).

Stages on real 96x96 scenes (dense_urban motif, reference met file):

1. ``baseline-cold``: unmodified source — reproduces census C6-02: two
   productions under two keys.
2. ``recipe-cold``: integration simulation — exactly ONE production, shared
   key for both routes.
3. ``recipe-warm``: faithful warm repeat — zero productions.

Final simulation outputs and standalone export artifacts are then compared
bitwise between the baseline and recipe runs.

Instrumentation is the committed C6-02 census probe (call-through wrappers
on ``svf_calculator_compact``, ``GeometryStore.get_or_create``,
``key_for``); children are instrumented through a generated
``sitecustomize`` exactly as in the census. Evidence is persisted before
assertions.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

os.environ.setdefault('NUMBA_NUM_THREADS', '2')  # development thread cap, before numba imports

import numpy as np
import pytest

import scene_fixtures
from scene_fixtures import DATE, REPO, SRC, build_scene, field_bits

PROBE_DIR = Path(__file__).resolve().parent
CENSUS_DIR = REPO / 'tests' / 'optimization_v6' / 'geometry_census'
EVIDENCE = REPO / 'optimization_v6_continue' / 'evidence' / 'recipe'
DIFF = EVIDENCE / 'integration_patch_C6-10.diff'
COMMIT = 'e7a2d6ec8594b234820e7783e0ca26d821de7f3d'

for entry in (str(SRC), str(CENSUS_DIR)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

import census_probe  # noqa: E402  (committed C6-02 instrumentation, reused unmodified)
import recipe_probe  # noqa: E402  (local integration-simulation patch)


def collect_events(record_dir):
    events = []
    for path in sorted(Path(record_dir).glob('*.jsonl')):
        for line in path.read_text(encoding='utf8').splitlines():
            if line.strip():
                events.append(json.loads(line))
    return events


def arm_children(record_dir, tmp_path):
    site_dir = Path(tmp_path) / 'sitecustomize_gen'
    site_dir.mkdir(exist_ok=True)
    (site_dir / 'sitecustomize.py').write_text(
        'import os, sys\n'
        'try:\n'
        '    for probe_dir in ("SOLWEIG_CENSUS_PROBE_DIR", "SOLWEIG_RECIPE_PROBE_DIR"):\n'
        '        where = os.environ.get(probe_dir)\n'
        '        if where and where not in sys.path:\n'
        '            sys.path.insert(0, where)\n'
        '    import census_probe\n'
        '    census_probe.autostart()\n'
        '    if os.environ.get("SOLWEIG_RECIPE_PROBE_DIR"):\n'
        '        import recipe_probe\n'
        '        recipe_probe.install()\n'
        'except Exception:\n'
        '    import traceback\n'
        '    traceback.print_exc(file=sys.stderr)\n', encoding='utf8')
    existing = os.environ.get('PYTHONPATH', '')
    parts = [str(site_dir), str(PROBE_DIR), str(CENSUS_DIR), str(SRC)]
    parts += [part for part in existing.split(os.pathsep) if part]
    os.environ['PYTHONPATH'] = os.pathsep.join(parts)
    os.environ['SOLWEIG_CENSUS_PROBE_DIR'] = str(CENSUS_DIR)
    os.environ['SOLWEIG_RECIPE_PROBE_DIR'] = str(PROBE_DIR)
    os.environ['SOLWEIG_CENSUS_RECORD_DIR'] = str(record_dir)
    os.environ['SOLWEIG_CENSUS_ROLE'] = 'child'


def begin_stage(base_record_dir, stage, tmp_path, integrate_child):
    stage_dir = Path(base_record_dir) / stage
    if stage_dir.exists():
        shutil.rmtree(stage_dir)
    stage_dir.mkdir(parents=True)
    arm_children(stage_dir, tmp_path)
    if not integrate_child:
        # Baseline children must NOT see the integration-simulation patch.
        os.environ.pop('SOLWEIG_RECIPE_PROBE_DIR', None)
    census_probe.rearm(stage_dir, 'parent')
    return stage_dir


def load_patched_service_module(tmp_path):
    """Apply the owned integration diff to a private copy of service.py.

    ``git apply --directory`` rewrites each file path BEFORE ``--include``
    matching and refuses targets outside the worktree, so the private copy is
    staged (relative) inside the owned tests directory and removed afterwards.
    A silent no-op is impossible here: the applied file must differ.
    """
    root = PROBE_DIR / '_patched_stage'
    if root.exists():
        shutil.rmtree(root)
    target_dir = root / 'src' / 'solweig_light' / 'geometry'
    target_dir.mkdir(parents=True)
    shutil.copyfile(SRC / 'solweig_light' / 'geometry' / 'service.py', target_dir / 'service.py')
    subprocess.run(['git', 'apply', '--directory', str(root.relative_to(REPO)),
                    '--include', '*src/solweig_light/geometry/service.py', str(DIFF)],
                   check=True, cwd=str(REPO))
    applied = (target_dir / 'service.py').read_text()
    assert applied != (SRC / 'solweig_light' / 'geometry' / 'service.py').read_text(), \
        'git apply silently skipped the service patch'
    assert 'numerical_geometry_recipe' in applied, 'post-image must use the shared recipe'
    name = 'solweig_light.geometry._service_c610_patched'
    spec = importlib.util.spec_from_file_location(name, target_dir / 'service.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    # The staged file must stay on disk: the post-image fingerprints its own
    # __file__ for the export identity, so cleanup happens at test end.
    return module


def thermal_comfort(scene):
    from solweig_light import thermal_comfort as run
    run(str(scene), DATE, own_met_file=str(scene / 'met.txt'), ERA_5_z0_find=False)


def summarize(stage, events, wall_s):
    svf = [e for e in events if e.get('event') == 'svf_call']
    store_calls = [e for e in events if e.get('event') == 'get_or_create']
    return {'stage': stage, 'wall_s': wall_s,
            'svf_calls': len(svf),
            'svf_by_route': {route: sum(1 for call in svf if call.get('route') == route)
                             for route in ('standalone', 'pipeline', 'unknown')
                             if any(call.get('route') == route for call in svf)},
            'store_calls': [{'route': call.get('route'), 'key': call.get('key'),
                             'hit': call.get('hit'), 'producer_calls': call.get('producer_calls'),
                             'identity_fields': sorted((call.get('identity') or {}).get('identity', call.get('identity') or {}))
                             if isinstance(call.get('identity'), dict) else None}
                            for call in store_calls],
            'keys': sorted({call.get('key') for call in store_calls if call.get('key')})}


def _tiff_pixels(path):
    from osgeo import gdal
    dataset = gdal.Open(str(path))
    try:
        return dataset.ReadAsArray().astype(np.float32).view(np.uint32)
    finally:
        dataset = None


def _zip_members(path):
    import zipfile
    with zipfile.ZipFile(path) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def _visibility_channels(path):
    from solweig_light.geometry.visibility import import_visibility_npz
    channels = import_visibility_npz(path)
    return {name: value.to_dense().view(np.uint32) for name, value in channels.items()}


def compare_outputs(left_scene, right_scene):
    """Bitwise comparison of all published artifacts between two runs."""
    report = {'output_files_left': sorted(str(p.name) for p in (left_scene / 'output_folder' / '0_0').glob('*')),
               'output_files_right': sorted(str(p.name) for p in (right_scene / 'output_folder' / '0_0').glob('*')),
               'outputs_pixel_bitwise_equal': {}, 'outputs_bytes_equal': {},
               'svf_exports_pixel_bitwise_equal': {}, 'visibility_channels_bitwise_equal': {}}
    left_outputs = sorted((left_scene / 'output_folder' / '0_0').glob('*'))
    right_outputs = sorted((right_scene / 'output_folder' / '0_0').glob('*'))
    assert [p.name for p in left_outputs] == [p.name for p in right_outputs] and left_outputs, 'output sets differ'
    for left, right in zip(left_outputs, right_outputs):
        report['outputs_pixel_bitwise_equal'][left.name] = bool(np.array_equal(_tiff_pixels(left), _tiff_pixels(right)))
        report['outputs_bytes_equal'][left.name] = left.read_bytes() == right.read_bytes()
    svf_left = left_scene / 'processed_inputs' / 'SVF'
    svf_right = right_scene / 'processed_inputs' / 'SVF'
    report['svf_exports_pixel_bitwise_equal']['SkyViewFactor_0_0.tif'] = bool(
        np.array_equal(_tiff_pixels(svf_left / 'SkyViewFactor_0_0.tif'),
                       _tiff_pixels(svf_right / 'SkyViewFactor_0_0.tif')))
    left_zip, right_zip = _zip_members(svf_left / 'svfs_0_0.zip'), _zip_members(svf_right / 'svfs_0_0.zip')
    assert set(left_zip) == set(right_zip) and left_zip, 'svfs zip members differ'
    report['svf_exports_pixel_bitwise_equal']['svfs_zip_members'] = all(
        left_zip[name] == right_zip[name] for name in left_zip)
    left_channels = _visibility_channels(svf_left / 'shadowmats_0_0.npz')
    right_channels = _visibility_channels(svf_right / 'shadowmats_0_0.npz')
    assert set(left_channels) == set(right_channels), 'visibility channel sets differ'
    for name, left in left_channels.items():
        report['visibility_channels_bitwise_equal'][name] = bool(np.array_equal(left, right_channels[name]))
    return report


def test_end_to_end_single_production_per_cold_tile(tmp_path):
    record_dir = EVIDENCE / 'raw' / 'end-to-end'
    if record_dir.exists():
        shutil.rmtree(record_dir)
    record_dir.mkdir(parents=True)

    # --- Stage 1: baseline cold public workflow on unmodified source. ---
    scene_base = build_scene(tmp_path / 'scene-base')
    stage = begin_stage(record_dir, 'baseline-cold', tmp_path, integrate_child=False)
    start = time.perf_counter()
    thermal_comfort(scene_base['dir'])
    base = summarize('baseline-cold', collect_events(stage), time.perf_counter() - start)

    # --- Stage 2: integration simulation on a fresh identical scene. ---
    scene_recipe = build_scene(tmp_path / 'scene-recipe')
    stage = begin_stage(record_dir, 'recipe-cold', tmp_path, integrate_child=True)
    from solweig_light.geometry import service as service_module
    from solweig_light import identities as identities_module
    patched = load_patched_service_module(tmp_path)
    saved_service = service_module.prepare_geometry_exports
    saved_identity = identities_module.geometry_identity
    service_module.prepare_geometry_exports = patched.prepare_geometry_exports
    identities_module.geometry_identity = recipe_probe.unified_geometry_identity
    try:
        start = time.perf_counter()
        thermal_comfort(scene_recipe['dir'])
        cold = summarize('recipe-cold', collect_events(stage), time.perf_counter() - start)

        # --- Stage 3: warm faithful repeat, still patched. ---
        stage = begin_stage(record_dir, 'recipe-warm', tmp_path, integrate_child=True)
        start = time.perf_counter()
        thermal_comfort(scene_recipe['dir'])
        warm = summarize('recipe-warm', collect_events(stage), time.perf_counter() - start)
    finally:
        service_module.prepare_geometry_exports = saved_service
        identities_module.geometry_identity = saved_identity
        shutil.rmtree(PROBE_DIR / '_patched_stage', ignore_errors=True)

    parity = compare_outputs(scene_base['dir'], scene_recipe['dir'])
    payload = {'schema': 'c6-10-end-to-end-v1', 'commit': COMMIT,
               'simulation': 'service half = diff post-image via git apply; child half = identity-only patch',
               'scene_sha256': {'baseline': scene_base['sha256'], 'recipe': scene_recipe['sha256']},
               'stages': [base, cold, warm], 'output_parity': parity,
               'note': 'development-tier contended host; wall times recorded, no benchmark claims'}
    out = EVIDENCE / 'raw' / 'end_to_end_summary.json'
    out.write_text(json.dumps(payload, indent=1, sort_keys=True))

    # Baseline reproduces the census on this base commit.
    assert base['svf_calls'] == 2, f'baseline must construct twice: {base}'
    assert base['svf_by_route'].get('standalone') == 1 and base['svf_by_route'].get('pipeline') == 1
    assert len(base['keys']) == 2, f'baseline keys must differ: {base["keys"]}'
    # Integration simulation: exactly one production, one shared key.
    assert cold['svf_calls'] == 1, f'recipe cold run must produce exactly once: {cold}'
    hits = sorted(call['hit'] for call in cold['store_calls'])
    producers = sorted(call['producer_calls'] for call in cold['store_calls'])
    assert len(cold['store_calls']) == 2, f'both routes must consult the store: {cold}'
    assert hits == [False, True] and producers == [0, 1], f'exactly one production expected: {cold}'
    assert len(cold['keys']) == 1, f'both routes must share one native key: {cold["keys"]}'
    assert cold['keys'][0] not in base['keys'], 'recipe key is a new third generation'
    # Warm repeat: zero productions; the child store consult still happens.
    assert warm['svf_calls'] == 0, f'warm repeat must not produce: {warm}'
    assert len(warm['store_calls']) == 1 and warm['store_calls'][0]['hit'] is True, f'{warm}'
    assert warm['keys'] == cold['keys'], 'warm key must equal the shared cold key'
    # Outputs identical in every published artifact.
    assert all(parity['outputs_pixel_bitwise_equal'].values()), f'{parity["outputs_pixel_bitwise_equal"]}'
    assert all(parity['svf_exports_pixel_bitwise_equal'].values()), f'{parity}'
    assert all(parity['visibility_channels_bitwise_equal'].values()), f'{parity}'
    assert out.exists()
