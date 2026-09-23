#!/usr/bin/env python3
"""N8-03 smoke: one full default run of a generated scene through the REAL
public pipeline entry, WITHOUT backend env.

Public three-stage workflow (C6-101r campaign_child lineage):
  stage A walls_aspect : api.run_walls_aspect
  stage B svf_geometry : api.calculate_svf (patch_option=2, overwrite=False)
  stage C simulation   : api.run_utci_tiles, 10 save flags, 24 records

Deliberately UNCONFIGURED: ambient get_runtime_options() defaults (workers=1,
threads_per_worker=1, cpu_budget=1, block_pixels=128), no thread env caps,
SOLWEIG_LIGHT_LW_BACKEND explicitly removed — the main-compatible default
path. This is a correctness/entry smoke for the frozen fixtures, not a timed
benchmark; walls are recorded only to bound host time.

--memory-budget-gib N (default 0 = ambient) pins ONLY memory_budget_bytes via
runtime_options. Observed 2026-09-22: ambient admission = 0.50 x currently
AVAILABLE host memory, which under teammate load resolved to 1.72 GiB and
rejected the 128x128 x 24 simulation phase (~1.78 GiB reserved); quiet-host
ambient admission is required for the pure-default cells (frozen in
n8_03_protocol.json). Pinning the budget exercises admission, not the
backend/native path under test.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import platform
import shutil
import sys
import time
from pathlib import Path

PARSER = argparse.ArgumentParser(description=__doc__)
PARSER.add_argument('--scene', required=True)
PARSER.add_argument('--run-root', required=True)
PARSER.add_argument('--out', required=True)
PARSER.add_argument('--memory-budget-gib', type=int, default=0)
ARGS = PARSER.parse_args()

SCENE = Path(ARGS.scene).resolve()
RUN_ROOT = Path(ARGS.run_root).resolve()
RUN_DIR = RUN_ROOT / 'run_scene'
PREP = RUN_DIR / 'processed_inputs'

os.environ.pop('SOLWEIG_LIGHT_LW_BACKEND', None)
os.environ.pop('SOLWEIG_LIGHT_NATIVE_CACHE', None)
ENV_LW = os.environ.get('SOLWEIG_LIGHT_LW_BACKEND', '')

import numpy as np  # noqa: E402
import numba  # noqa: E402
import solweig_light  # noqa: E402
from solweig_light import api  # noqa: E402
from solweig_light.runtime import (default_memory_budget_bytes,  # noqa: E402
                                   get_runtime_options, runtime_options)

FLAGS = dict(save_tmrt=True, save_svf=True, save_kup=True, save_kdown=True,
             save_lup=True, save_ldown=True, save_shadow=True, save_wbgt=True,
             save_ta=True, save_wind=True)


def output_manifest(root: Path) -> dict:
    files = []
    for path in sorted(root.rglob('*')):
        rel = path.relative_to(root)
        if path.is_file() and not any(part.startswith('.solweig-light') for part in rel.parts):
            files.append({'path': str(rel), 'size': path.stat().st_size,
                          'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    simulation = [entry for entry in files if entry['path'].startswith('output_folder/')]
    return {'file_count': len(files),
            'simulation_tiff_count': len(simulation),
            'digest': hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()[:16],
            'simulation_tiff_digest': hashlib.sha256(
                json.dumps(simulation, sort_keys=True).encode()).hexdigest()[:16]}


def main() -> int:
    manifest = json.loads((SCENE / 'scene_manifest.json').read_text())
    if RUN_ROOT.exists():
        shutil.rmtree(RUN_ROOT)
    RUN_ROOT.mkdir(parents=True)
    shutil.copytree(SCENE, RUN_DIR)
    stale = RUN_DIR / 'output_folder'
    if stale.exists():
        shutil.rmtree(stale)

    options = get_runtime_options()  # ambient defaults, untouched
    ambient_budget = default_memory_budget_bytes()
    admission = {'ambient_default_budget_bytes': ambient_budget,
                 'ambient_budget_gib': round(ambient_budget / 1024**3, 3),
                 'pinned_memory_budget_gib': ARGS.memory_budget_gib or None}
    active = options
    if ARGS.memory_budget_gib:
        active = dataclasses.replace(options,
                                     memory_budget_bytes=ARGS.memory_budget_gib * 1024**3)
    splits = {}
    with runtime_options(active):
        t0 = time.monotonic()
        api.run_walls_aspect(str(PREP))
        splits['walls_aspect_s'] = round(time.monotonic() - t0, 3)

        t0 = time.monotonic()
        api.calculate_svf(str(PREP), patch_option=2, overwrite=False)
        splits['svf_geometry_s'] = round(time.monotonic() - t0, 3)

        t0 = time.monotonic()
        api.run_utci_tiles(base_path=str(RUN_DIR), preprocess_dir=str(PREP),
                           selected_date_str=manifest['selected_date'],
                           tile_keys=['0_0'], **FLAGS)
        splits['simulation_s'] = round(time.monotonic() - t0, 3)

    record = {
        'schema': 'sw8-n8-03-smoke-v1',
        'scene': str(SCENE),
        'scene_label': manifest['label'],
        'tile_size': manifest['tile_size'],
        'variant': manifest['variant'],
        'selected_date': manifest['selected_date'],
        'timesteps': manifest['met_records_including_header'] - 1,
        'env_lw_backend': ENV_LW,
        'admission': admission,
        'options_ambient_defaults': options.as_dict(),
        'options_active': active.as_dict(),
        'flags': sorted(FLAGS),
        'module_origin': {'solweig_light': Path(solweig_light.__file__).resolve().as_posix()},
        'stage_splits_s': splits,
        'output_manifest': output_manifest(RUN_DIR),
        'versions': {'python': platform.python_version(), 'numpy': np.__version__,
                     'numba': numba.__version__, 'machine': platform.machine()},
        'returncode': 0,
    }
    Path(ARGS.out).parent.mkdir(parents=True, exist_ok=True)
    Path(ARGS.out).write_text(json.dumps(record, indent=1) + '\n')
    print(json.dumps({'out': str(ARGS.out), 'splits': splits,
                      'digest': record['output_manifest']['digest'],
                      'simulation_tiffs': record['output_manifest']['simulation_tiff_count']}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
