#!/usr/bin/env python3
"""N8-02 fresh-process child: one packed-pipeline run over the real scene.

b7-50 pattern (pipeline.run_tile in-process, PIPELINE_CYLINDERS_ANISOTROPIC
demand set by run_tile itself), thread caps before numerical import, Numba
thread pool verified, optional worker-local instrumentation
(n8_02_instrument), per-run bounded JSON record.

Arms (--backend): default (LW env removed) or native
(SOLWEIG_LIGHT_LW_BACKEND=native). --block-pixels reaches the engine through
RuntimeOptions.block_pixels (internal aggregation; public default unchanged).
--entry pool switches to the production scheduler entry api.run_utci_tiles
(uninstrumented; filesystem proof of the native path inside worker children).
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import platform
import resource
import shutil
import sys
import time
from pathlib import Path

PARSER = argparse.ArgumentParser(description=__doc__)
PARSER.add_argument('--site', required=True)
PARSER.add_argument('--prepared', required=True)
PARSER.add_argument('--date', default='2020-07-18')
PARSER.add_argument('--backend', choices=('default', 'native'), default='default')
PARSER.add_argument('--block-pixels', type=int, default=128)
PARSER.add_argument('--threads', type=int, default=4)
PARSER.add_argument('--cpu-budget', type=int, default=4)
PARSER.add_argument('--memory-budget-gib', type=int, default=12)
PARSER.add_argument('--instrument', type=int, default=0)
PARSER.add_argument('--entry', choices=('runtile', 'pool'), default='runtile')
PARSER.add_argument('--run-root', required=True)
PARSER.add_argument('--out', required=True)
ARGS = PARSER.parse_args()

T_START = time.monotonic()
SITE = str(Path(ARGS.site).resolve())
sys.path.insert(0, SITE)
_path = os.environ.get('PYTHONPATH')
os.environ['PYTHONPATH'] = SITE if not _path else SITE + os.pathsep + _path

THREAD_VARS = ('BLIS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMBA_NUM_THREADS',
               'NUMEXPR_NUM_THREADS', 'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
               'VECLIB_MAXIMUM_THREADS')
for _name in THREAD_VARS:
    os.environ[_name] = str(ARGS.threads)

if ARGS.backend == 'default':
    os.environ.pop('SOLWEIG_LIGHT_LW_BACKEND', None)
else:
    os.environ['SOLWEIG_LIGHT_LW_BACKEND'] = ARGS.backend
ENV_AT_START = {name: os.environ.get(name) for name in THREAD_VARS}
ENV_LW = os.environ.get('SOLWEIG_LIGHT_LW_BACKEND', '')

import numpy as np  # noqa: E402
import numba  # noqa: E402

CONFIG_THREADS = int(numba.config.NUMBA_NUM_THREADS)
if CONFIG_THREADS == ARGS.threads:
    numba.set_num_threads(ARGS.threads)
THREAD_SET_OK = numba.get_num_threads() == ARGS.threads

T_IMPORT_START = time.monotonic()
import solweig_light  # noqa: E402
from solweig_light import api, pipeline  # noqa: E402
from solweig_light.runtime import (get_runtime_options, plan_admission,  # noqa: E402
                                   runtime_options)
T_IMPORT_S = time.monotonic() - T_IMPORT_START

PREPARED = Path(ARGS.prepared).resolve()
FLAGS = {f'save_{name}': True for name in
         ('tmrt', 'kup', 'kdown', 'lup', 'ldown', 'shadow', 'wbgt', 'ta', 'wind',
          'svf')}


def output_digest(root: Path) -> dict:
    files = []
    for path in sorted(root.rglob('*')):
        rel = path.relative_to(root)
        if path.is_file() and not any(part.startswith('.solweig-light') for part in rel.parts):
            files.append({'path': str(rel), 'size': path.stat().st_size,
                         'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    return {'file_count': len(files),
            'digest': hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()[:16],
            'files': files}


def main() -> int:
    if ARGS.block_pixels < 1:
        raise SystemExit(f'--block-pixels must be >= 1, got {ARGS.block_pixels}'
                         ' (N13-7: non-positive values parsed as vacuous passes)')
    run_dir = Path(ARGS.run_root) / 'run'
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True)

    options = dataclasses.replace(
        get_runtime_options(),
        memory_budget_bytes=ARGS.memory_budget_gib * 1024**3,
        cpu_budget=ARGS.cpu_budget,
        workers=1,
        threads_per_worker=ARGS.threads,
        block_pixels=ARGS.block_pixels,
        checkpoint_interval=1,
        cache_enabled=True,
        legacy_cache_policy='trust',
        cache_dir=None,
    )

    counters = None
    counters_path = None
    if ARGS.instrument:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        os.environ['N8_02_COUNTERS_OUT'] = str(Path(ARGS.out).with_suffix('.counters.json'))
        import n8_02_instrument
        n8_02_instrument.install()
        counters_path = os.environ['N8_02_COUNTERS_OUT']

    stage_splits = {}
    t_run_start = time.monotonic()
    if ARGS.entry == 'runtile':
        paths = {name: pipeline.files_by_key(PREPARED / name)['0_0'] for name in
                 ('Building_DSM', 'Trees', 'DEM', 'walls', 'aspect', 'metfiles')}
        with runtime_options(options):
            pipeline.run_tile(run_dir, PREPARED, ARGS.date, '0_0', paths, FLAGS)
    else:
        # production scheduler entry: worker children in a bounded pool run
        # the same run_tile; env (incl. LW backend + native cache) propagates
        # through _child_environment(os.environ.copy()).
        with runtime_options(options):
            api.run_utci_tiles(base_path=str(run_dir), preprocess_dir=str(PREPARED),
                               selected_date_str=ARGS.date, tile_keys=['0_0'], **FLAGS)
    run_s = time.monotonic() - t_run_start

    try:
        layer = numba.threading_layer()
    except Exception as error:
        layer = f'error: {error}'

    record = {
        'schema': 'sw8-n8-02-child-v1',
        'requested': {'backend': ARGS.backend, 'block_pixels': ARGS.block_pixels,
                      'threads': ARGS.threads, 'cpu_budget': ARGS.cpu_budget,
                      'instrument': bool(ARGS.instrument), 'entry': ARGS.entry},
        'env': {'threads_at_import': ENV_AT_START, 'lw_backend': ENV_LW,
                'native_cache': os.environ.get('SOLWEIG_LIGHT_NATIVE_CACHE', ''),
                'numba_cache_dir': os.environ.get('NUMBA_CACHE_DIR', '')},
        'numba': {'config_NUMBA_NUM_THREADS': CONFIG_THREADS,
                  'thread_set_ok': THREAD_SET_OK,
                  'final_get_num_threads': int(numba.get_num_threads()),
                  'threading_layer': layer, 'version': numba.__version__},
        'options': options.as_dict(),
        'module_origin': {'solweig_light': Path(solweig_light.__file__).resolve().as_posix()},
        'run_wall_s': round(run_s, 4),
        'import_s': round(T_IMPORT_S, 3),
        'child_total_s': round(time.monotonic() - T_START, 3),
        'peak_rss_self_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'peak_rss_children_bytes': resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
        'counters_path': counters_path,
        'output_manifest': output_digest(run_dir),
        'versions': {'python': platform.python_version(), 'numpy': np.__version__,
                     'numba': numba.__version__, 'machine': platform.machine()},
        'pid': os.getpid(),
    }
    Path(ARGS.out).parent.mkdir(parents=True, exist_ok=True)
    Path(ARGS.out).write_text(json.dumps(record, indent=1) + '\n')
    print(json.dumps({'out': str(ARGS.out), 'run_wall_s': record['run_wall_s'],
                      'digest': record['output_manifest']['digest']}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
