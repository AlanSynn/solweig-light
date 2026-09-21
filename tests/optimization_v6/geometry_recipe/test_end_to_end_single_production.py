"""C6-10 gate 2 end-to-end: one geometry production per cold tile in a real
public ``thermal_comfort`` run when cache is enabled.

Integrated-tree form (C6-70): the service and pipeline halves are wired for
real (``integration_patch_C6-10.diff`` is applied to the installed source),
so the pre-integration simulation (loading the diff post-image of
``service.py`` over a private copy and identity-patching the child; recorded
in ``raw/end-to-end/`` with schema ``c6-10-end-to-end-v1``) is replaced by
runs against the actual integrated tree:

1. ``integrated-cold``: fresh scene — exactly ONE production under ONE
   shared key, consulted by both routes.
2. ``integrated-warm``: faithful warm repeat on the same scene — zero
   productions.
3. ``integrated-cold-2``: a second identical fresh scene — one production
   again, and every published artifact bitwise-equal to run 1 (determinism
   of the integrated tree across identical cold inputs).

Instrumentation is the committed C6-02 census probe (call-through wrappers
on ``svf_calculator_compact``, ``GeometryStore.get_or_create``,
``key_for``); children are instrumented through a generated
``sitecustomize`` exactly as in the census. Evidence is persisted before
assertions.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time
from pathlib import Path

os.environ.setdefault('NUMBA_NUM_THREADS', '2')  # development thread cap, before numba imports

import numpy as np
import pytest

import scene_fixtures
from scene_fixtures import DATE, REPO, SRC, build_scene

PROBE_DIR = Path(__file__).resolve().parent
CENSUS_DIR = REPO / 'tests' / 'optimization_v6' / 'geometry_census'
EVIDENCE = REPO / 'optimization_v6_continue' / 'evidence' / 'recipe'
COMMIT = 'e7a2d6ec8594b234820e7783e0ca26d821de7f3d'

for entry in (str(SRC), str(CENSUS_DIR)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

import census_probe  # noqa: E402  (committed C6-02 instrumentation, reused unmodified)


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
        '    for probe_dir in ("SOLWEIG_CENSUS_PROBE_DIR",):\n'
        '        where = os.environ.get(probe_dir)\n'
        '        if where and where not in sys.path:\n'
        '            sys.path.insert(0, where)\n'
        '    import census_probe\n'
        '    census_probe.autostart()\n'
        'except Exception:\n'
        '    import traceback\n'
        '    traceback.print_exc(file=sys.stderr)\n', encoding='utf8')
    existing = os.environ.get('PYTHONPATH', '')
    parts = [str(site_dir), str(CENSUS_DIR), str(SRC)]
    parts += [part for part in existing.split(os.pathsep) if part]
    os.environ['PYTHONPATH'] = os.pathsep.join(parts)
    os.environ['SOLWEIG_CENSUS_PROBE_DIR'] = str(CENSUS_DIR)
    os.environ['SOLWEIG_CENSUS_RECORD_DIR'] = str(record_dir)
    os.environ['SOLWEIG_CENSUS_ROLE'] = 'child'


def begin_stage(base_record_dir, stage, tmp_path):
    stage_dir = Path(base_record_dir) / stage
    if stage_dir.exists():
        shutil.rmtree(stage_dir)
    stage_dir.mkdir(parents=True)
    arm_children(stage_dir, tmp_path)
    census_probe.rearm(stage_dir, 'parent')
    return stage_dir


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
    record_dir = EVIDENCE / 'raw' / 'end-to-end-integrated'
    if record_dir.exists():
        shutil.rmtree(record_dir)
    record_dir.mkdir(parents=True)

    # --- Run 1: integrated cold public workflow on a fresh scene. ---
    scene_one = build_scene(tmp_path / 'scene-one')
    stage = begin_stage(record_dir, 'integrated-cold', tmp_path)
    start = time.perf_counter()
    thermal_comfort(scene_one['dir'])
    cold = summarize('integrated-cold', collect_events(stage), time.perf_counter() - start)

    # --- Run 2: warm faithful repeat on the same scene. ---
    stage = begin_stage(record_dir, 'integrated-warm', tmp_path)
    start = time.perf_counter()
    thermal_comfort(scene_one['dir'])
    warm = summarize('integrated-warm', collect_events(stage), time.perf_counter() - start)

    # --- Run 3: second identical fresh scene — cold again, outputs must
    #     match run 1 bitwise (integrated-tree determinism). ---
    scene_two = build_scene(tmp_path / 'scene-two')
    stage = begin_stage(record_dir, 'integrated-cold-2', tmp_path)
    start = time.perf_counter()
    thermal_comfort(scene_two['dir'])
    cold2 = summarize('integrated-cold-2', collect_events(stage), time.perf_counter() - start)

    parity = compare_outputs(scene_one['dir'], scene_two['dir'])
    payload = {'schema': 'c6-10-end-to-end-integrated-v2', 'commit': COMMIT,
               'simulation': 'none; runs execute the actual integrated source',
               'scene_sha256': {'run1': scene_one['sha256'], 'run3': scene_two['sha256']},
               'stages': [cold, warm, cold2], 'output_parity': parity,
               'note': 'development-tier contended host; wall times recorded, no benchmark claims'}
    out = EVIDENCE / 'raw' / 'end_to_end_integrated_summary.json'
    out.write_text(json.dumps(payload, indent=1, sort_keys=True))

    # Integrated cold run: exactly one production, one shared native key.
    assert cold['svf_calls'] == 1, f'integrated cold run must produce exactly once: {cold}'
    hits = sorted(call['hit'] for call in cold['store_calls'])
    producers = sorted(call['producer_calls'] for call in cold['store_calls'])
    assert len(cold['store_calls']) == 2, f'both routes must consult the store: {cold}'
    assert hits == [False, True] and producers == [0, 1], f'exactly one production expected: {cold}'
    assert len(cold['keys']) == 1, f'both routes must share one native key: {cold["keys"]}'
    # Warm repeat: zero productions; the store consult still happens.
    assert warm['svf_calls'] == 0, f'warm repeat must not produce: {warm}'
    assert len(warm['store_calls']) == 1 and warm['store_calls'][0]['hit'] is True, f'{warm}'
    assert warm['keys'] == cold['keys'], 'warm key must equal the shared cold key'
    # Second cold scene: one production, bitwise-equal outputs. The key is
    # allowed to differ across directories (pre-existing raster_fingerprint
    # path dependence, C6-10 review record): the key assertion is only made
    # within one scene directory (cold vs warm above).
    assert cold2['svf_calls'] == 1, f'second cold run must produce exactly once: {cold2}'
    assert len(cold2['keys']) == 1, f'second cold run must use one shared key: {cold2}'
    assert all(parity['outputs_pixel_bitwise_equal'].values()), f'{parity["outputs_pixel_bitwise_equal"]}'
    assert all(parity['svf_exports_pixel_bitwise_equal'].values()), f'{parity}'
    assert all(parity['visibility_channels_bitwise_equal'].values()), f'{parity}'
    assert out.exists()
