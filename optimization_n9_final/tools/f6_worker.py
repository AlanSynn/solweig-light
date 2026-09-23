#SOLWEIG-GPU: GPU-accelerated SOLWEIG model for urban thermal comfort simulation
#Copyright (C) 2022–2025 Harsh Kamath and Naveen Sudharsan

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
"""N9-F6 per-tree measurement worker (spawned by f6_final_vs_main.py).

The FINAL tree and the pinned main reference share the package name
``solweig_light``, so one worker process imports EXACTLY ONE source tree
(``--root`` is inserted at sys.path[0] and asserted via
``solweig_light.__file__``) and runs the compact cell set through that
tree's own production longwave seam:

* FINAL: ``cylinder_longwave.set_demand(PIPELINE_CYLINDERS_ANISOTROPIC)``
  then ``Lcyl_v2022a_by_demand(..., parallel=None at tw=1)`` -- the exact
  call form of the engine's shipped default route (the route consult
  fires; admitted cells take the bounded stream at its pinned budget 1).
* MAIN: ``radiation.engine.Lcyl_v2022a(...)`` -- main's production seam
  (engine.py:1761 wrapper), which reads block_pixels and
  ``parallel = threads_per_worker > 1`` (False at the shipped default)
  from the runtime options context.

Thread budget: ONE budget N for the whole session (both trees get the
identical environment: numba threads = N; the FINAL stream leaf's prange
owns those threads, MAIN's serial kernels use one). Env pins land BEFORE
any numerical import. threads_per_worker stays at its shipped default 1
in both trees (asserted) -- the F6 comparison is product-default vs
product-default.

Modes:
  check  fixtures + fast-path guards + route audit + untimed calls +
         digests (no timing anywhere)
  cold   fresh JIT cache (--cache-dir must be empty); ONE timed cold call
         on the primary cell, then an untimed full sweep, then one warm
         re-timing of the primary cell (cold/warm diagnostic)
  warm   per cell: one untimed call, then ONE timed call (single clock)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_WORKTREE = Path(__file__).resolve().parents[2]


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--tree', choices=('final', 'main'), required=True)
    ap.add_argument('--root', required=True,
                    help='the source tree to import (its src/ directory)')
    ap.add_argument('--cache-dir', required=True,
                    help='NUMBA_CACHE_DIR private to this tree')
    ap.add_argument('--mode', choices=('check', 'cold', 'warm'),
                    required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--threads', type=int, default=4)
    ap.add_argument('--sha', default='')
    ap.add_argument('--fixture-data',
                    help='npz with the adversarial lup pools (required for '
                         'check/cold/warm; tree-independent data, generated '
                         'once under the FINAL tree)')
    ap.add_argument('--dump-fixture-data', dest='dump_fixture_data',
                    help='generate the fixture npz and exit (requires a '
                         'tree whose radiation.cylinder_longwave imports, '
                         'i.e. the FINAL tree)')
    args = ap.parse_args()

    # --- thread budget + cache/env pinning BEFORE any numerical import ---
    for _name in ('BLIS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMBA_NUM_THREADS',
                  'NUMEXPR_NUM_THREADS', 'OMP_NUM_THREADS',
                  'OPENBLAS_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
        os.environ[_name] = str(args.threads)
    os.environ['NUMBA_CACHE_DIR'] = os.path.abspath(args.cache_dir)
    # The shipped default route must be measured AT the defaults:
    for _name in ('SOLWEIG_LIGHT_FUSED_RAD', 'SOLWEIG_LIGHT_PATCH_CLASS_TABLES',
                  'SOLWEIG_LIGHT_LW_BACKEND'):
        os.environ.pop(_name, None)
    root = os.path.abspath(args.root)
    sys.path.insert(0, root)

    record: dict = {'tree': args.tree, 'root': root, 'sha': args.sha,
                    'mode': args.mode, 'utc': _now_utc(),
                    'threads': args.threads,
                    'numba_cache_dir': os.environ['NUMBA_CACHE_DIR'],
                    'errors': []}

    import numpy as np
    import numba
    numba.set_num_threads(args.threads)

    import solweig_light
    live = os.path.abspath(solweig_light.__file__)
    assert live.startswith(root + os.sep), \
        f'imported {live} not under {root}'
    record['imported_from'] = live

    # --- fixture data prep mode (tree-independent pools, generated once) --
    if args.dump_fixture_data:
        import importlib.util
        ref = _WORKTREE / 'tests' / 'optimization_v8' / 'reference'
        if str(ref) not in sys.path:
            sys.path.insert(0, str(ref))
        spec = importlib.util.spec_from_file_location(
            'lw_identity_grid', ref / 'test_typed_graph_identity.py')
        module = importlib.util.module_from_spec(spec)
        sys.modules['lw_identity_grid'] = module
        spec.loader.exec_module(module)
        pools = {}
        for B in (1024, 128):
            base = module.adversarial_inputs(B, 153, seed=97 * B)
            pools[f'lup_{B}'] = np.asarray(base['lup'], dtype=np.float32)
        Path(args.dump_fixture_data).write_bytes(b'')  # ensure writable
        np.savez(str(args.dump_fixture_data), **pools)
        print(json.dumps({'dumped': str(args.dump_fixture_data),
                          'keys': sorted(pools)}))
        return 0

    if not args.fixture_data:
        ap.error('--fixture-data is required for check/cold/warm modes')

    # --- fixtures (F3 quiet_window_abc construction at the PUBLIC seam) --
    P_PATCHES = 153
    CELLS = ((1024, 'all-binary'), (1024, 'mix'), (1024, 'all-raw'),
             (128, 'all-binary'), (128, 'mix'), (128, 'all-raw'))
    PRIMARY = (1024, 'mix')          # the cold-metric composition
    ESKY, TA, TGWALL, EWALL = 0.85, 25.0, 2.0, 0.9   # recorded constants

    lup_pools = np.load(args.fixture_data)

    from solweig_light.geometry.shadows import create_patches
    from osgeo import gdal

    def _real_asvf(rows: int) -> np.ndarray:
        dataset = gdal.Open(str(_WORKTREE / 'tests' / 'reference'
                                / 'state_sequence_original_cpu' / 'scene'
                                / 'processed_inputs' / 'SVF'
                                / 'SkyViewFactor_0_0.tif'))
        raster = np.asarray(dataset.GetRasterBand(1).ReadAsArray(),
                            dtype=np.float32)
        del dataset
        return np.resize(raster.reshape(-1), rows).astype(np.float32)

    def build_inputs(B: int, mix: str) -> dict:
        from solweig_light.geometry.visibility import (PackedVisibility,
                                                       _EncodedPatch)

        def _patch(mode, rng):
            if mode == 'raw':
                bits = rng.integers(0, 2 ** 32, size=B, dtype=np.uint64
                                    ).astype(np.uint32)
                return _EncodedPatch(mode, bits.astype('<u4').tobytes())
            if mode == 'ternary':
                codes = rng.integers(0, 3, size=B).astype(np.uint8)
                padded = np.zeros((B + 3) // 4 * 4, dtype=np.uint8)
                padded[:B] = codes
                payload = (padded[0::4] | (padded[1::4] << 2)
                           | (padded[2::4] << 4) | (padded[3::4] << 6)
                           ).tobytes()
                return _EncodedPatch(mode, payload)
            codes = rng.integers(0, 2, size=B).astype(np.uint8)
            return _EncodedPatch(mode, np.packbits(codes, bitorder='little')
                                 .tobytes())

        rotation = {'all-binary': ('binary',), 'all-raw': ('raw',),
                    'mix': ('binary', 'raw', 'ternary')}[mix]
        rng = np.random.default_rng(100_003 * B + 7919
                                    * ('all-binary', 'mix', 'all-raw'
                                       ).index(mix))
        channels = []
        for _ in range(3):
            patches = [_patch(rotation[i % len(rotation)], rng)
                       for i in range(P_PATCHES)]
            channels.append(PackedVisibility((1, B, P_PATCHES), tuple(patches)))

        base = lup_pools[f'lup_{B}']
        patch_alt, patch_azi = create_patches(2)[0], create_patches(2)[1]
        assert patch_alt.size == P_PATCHES
        sky_patches = np.column_stack(
            (patch_alt, patch_azi,
             np.full(P_PATCHES, EWALL, dtype=np.float32)))
        return {'B': B, 'mix': mix,
                'esky': ESKY, 'Ta': TA, 'Tgwall': TGWALL, 'ewall': EWALL,
                'sky_patches': sky_patches,
                'Lup': base.reshape(1, B),
                'shmat': channels[0], 'vegshmat': channels[1],
                'vbshvegshmat': channels[2],
                'solar_altitude': np.array(52.0),
                'solar_azimuth': np.array(173.0),
                'rows': 1, 'cols': B,
                'asvf': _real_asvf(B)}

    from solweig_light import runtime
    from solweig_light.radiation.patch_radiation import _supported
    assert runtime.get_runtime_options().threads_per_worker == 1, \
        'the shipped threads_per_worker default must be 1 in both trees'

    cells = {}
    for B, mix in CELLS:
        inp = build_inputs(B, mix)
        assert _supported([inp['sky_patches'], inp['Lup'], inp['asvf']],
                          [inp['shmat'], inp['vegshmat'],
                           inp['vbshvegshmat']]), \
            f'fast-path guard rejected the fixture: B={B} {mix}'
        cells[(B, mix)] = inp
    record['fast_path_guards'] = 'passed (all 6 cells)'

    # --- the production seam of THIS tree --------------------------------
    if args.tree == 'final':
        from solweig_light.radiation import cylinder_longwave as cyl
        _previous = cyl.set_demand(
            cyl.CylinderLongwaveDemand.PIPELINE_CYLINDERS_ANISOTROPIC)
        assert cyl.current_demand() == \
            cyl.CylinderLongwaveDemand.PIPELINE_CYLINDERS_ANISOTROPIC

        def run_seam(inp):
            # Exact engine call form (engine.py shipped default route):
            # block_pixels is read from the runtime context INSIDE the
            # call and passed down explicitly, as the engine does.
            with runtime.runtime_options(block_pixels=inp['B']):
                return cyl.Lcyl_v2022a_by_demand(
                    inp['esky'], inp['sky_patches'], inp['Ta'],
                    inp['Tgwall'], inp['ewall'], inp['Lup'], inp['shmat'],
                    inp['vegshmat'], inp['vbshvegshmat'],
                    inp['solar_altitude'], inp['solar_azimuth'],
                    inp['rows'], inp['cols'], inp['asvf'],
                    block_pixels=runtime.get_runtime_options().block_pixels,
                    parallel=True if runtime.get_runtime_options()
                    .threads_per_worker > 1 else None)

        def audit_routes():
            """UNTIMED: which cells the structural route admits."""
            found: dict[int, list[bool]] = {}
            orig = cyl._lw_region_route

            def probe(values, geometry, solar_gate, prepared, total,
                      block_pixels, *rest):
                routed = orig(values, geometry, solar_gate, prepared, total,
                              block_pixels, *rest)
                found.setdefault(int(block_pixels), []).append(routed
                                                               is not None)
                return routed

            cyl._lw_region_route = probe
            try:
                for key in CELLS:
                    run_seam(cells[key])
            finally:
                cyl._lw_region_route = orig
            return {f'B={B} {mix}': found[B][i]
                    for B, mix in CELLS
                    for i, m in enumerate(['all-binary', 'mix', 'all-raw'])
                    if m == mix}
    else:
        from solweig_light.radiation import engine as rad_engine

        def run_seam(inp):
            # Exact production seam: main's engine wrapper reads
            # block_pixels and parallel = tw > 1 from the runtime context.
            with runtime.runtime_options(block_pixels=inp['B']):
                return rad_engine.Lcyl_v2022a(
                    inp['esky'], inp['sky_patches'], inp['Ta'],
                    inp['Tgwall'], inp['ewall'], inp['Lup'], inp['shmat'],
                    inp['vegshmat'], inp['vbshvegshmat'],
                    inp['solar_altitude'], inp['solar_azimuth'],
                    inp['rows'], inp['cols'], inp['asvf'])

        def audit_routes():
            # MAIN has no route seam; the audit pass still calls the seam
            # once per cell so every tree gets the identical untimed
            # warm-up before any timed call (run-1 lesson: MAIN's first
            # timed cell otherwise pays JIT cache load inside the clock).
            for key in CELLS:
                run_seam(cells[key])
            return {f'B={B} {mix}': None for B, mix in CELLS}

    def digest(out) -> str:
        h = hashlib.sha256()
        for field in out[:2]:            # Ldown, Lside (primary outputs)
            h.update(np.ascontiguousarray(field, dtype=np.float32)
                     .view(np.uint32).tobytes())
        return h.hexdigest()

    def loadavg() -> list:
        return [float(v) for v in os.getloadavg()]

    results: dict = {}
    if args.mode in ('check', 'warm'):
        # Untimed first pass: doubles as the JIT warm-up and the route
        # audit (which cells the structural route admits). In warm mode
        # every timed call below is therefore a fully warmed second call.
        record['route_audit'] = audit_routes()
        for key in CELLS:
            inp = cells[key]
            if args.mode == 'warm':
                t0 = time.perf_counter()
                out = run_seam(inp)
                ms = (time.perf_counter() - t0) * 1e3
            else:
                out = run_seam(inp)
                ms = None
            results[f'B={key[0]} {key[1]}'] = {
                'ms': round(ms, 4) if args.mode == 'warm' else None,
                'digest': digest(out),
                'loadavg_1m_after': round(loadavg()[0], 2)}
        if args.mode == 'warm':
            record['timed_first_call_only'] = \
                'ONE clock per cell (second call; first pass was untimed)'
    elif args.mode == 'cold':
        # Importing the tree creates the numba cache SUBDIRECTORY skeleton
        # (decoration-time locator), so freshness means: no compiled
        # cache entries yet, not an empty directory.
        assert not list(Path(args.cache_dir).rglob('*.nbi')), \
            'cold mode requires a FRESH cache dir (no compiled entries)'
        inp = cells[PRIMARY]
        t0 = time.perf_counter()
        out = run_seam(inp)
        cold_ms = (time.perf_counter() - t0) * 1e3
        for key in CELLS:                      # untimed sweep: JIT the rest
            run_seam(cells[key])
        t0 = time.perf_counter()
        out_warm = run_seam(inp)
        warm_ms = (time.perf_counter() - t0) * 1e3
        d_final = digest(out)
        d_warm = digest(out_warm)
        assert d_final == d_warm, 'cold vs warm digest divergence'
        results[f'B={PRIMARY[0]} {PRIMARY[1]}'] = {
            'cold_ms': round(cold_ms, 4), 'warm_ms': round(warm_ms, 4),
            'digest': d_final,
            'loadavg_1m_after': round(loadavg()[0], 2)}
        record['cold_cell'] = f'B={PRIMARY[0]} {PRIMARY[1]}'

    record['results'] = results
    if args.mode == 'check':
        record['route_audit'] = audit_routes()
    with open(args.out, 'w') as f:
        json.dump(record, f, indent=1, sort_keys=True)
    print(json.dumps({'tree': args.tree, 'mode': args.mode,
                      'ok': True, 'out': args.out}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
