#SOLWEIG-GPU: GPU-accelerated SOLWEIG model for urban thermal comfort simulation
#Copyright (C) 2022–2025 Harsh Kamath and Naveen Sudharsan

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
"""N8-10 'Compare and stop' leaf benchmark: C0 (shipped native call, with
per-call _ensure_loaded) vs H (handle-only execute) vs A (Numba kernel) on
real-profile f64 scalar inputs at B in {128, 1024}, P=153.

Uninstrumented paired-rep timing (dossier 01 final section; windows kept to
seconds).  Provenance of inputs: SYNTHETIC leaf-level, seeded rng, with
shapes/strides/scalar provenance mirroring the real packed pipeline measured
in n8_02 (P=153 patches, float64 surface scalars -> f64 entry, np.float32
reflection factor, stride-12 column-view sky tables, bool sun/shade/gate);
values are regular-range (no adversarial nonfinites), which matches the real
pipeline's admission rate (432/432 admitted in n8_02).

Run:  .venv/bin/python experiments/optimization_v8/loader/bench_leaf_compare.py
"""
from __future__ import annotations

import os
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import numba

THREADS = max(1, min(4, numba.config.NUMBA_NUM_THREADS))
numba.set_num_threads(THREADS)

from solweig_light.radiation import cylinder_longwave as cyl
from solweig_light.backends import native_lw
import native_handle as nh

F32 = np.float32
P = 153


def realistic_args(B: int, seed: int) -> dict:
    """Real-profile leaf inputs (see module docstring for provenance)."""
    rng = np.random.default_rng(seed)
    sh = rng.random((B, P)).astype(F32)
    vs = rng.random((B, P)).astype(F32)
    vb = rng.random((B, P)).astype(F32)
    sun = rng.random((B, P)) < 0.5
    shade = rng.random((B, P)) < 0.5
    solid = rng.random(P).astype(F32)
    sine = rng.random(P).astype(F32)
    cosine = np.sqrt(np.maximum(0.0, 1.0 - sine.astype(np.float64)
                                ** 2)).astype(F32)
    solar_gate = (np.arange(P) % 3 != 0)
    sky_table_down = rng.random((P, 3)).astype(F32) * 400.0   # W m-2 scale
    sky_table_side = rng.random((P, 3)).astype(F32) * 350.0
    lup = (rng.random(B).astype(F32) * 60.0) + 340.0
    return dict(
        sh=sh, vs=vs, vb=vb, sun=sun, shade=shade,
        solid=solid, sine=sine, cosine=cosine,
        directions=np.zeros((P, 4), F32), gate=np.zeros((P, 4), np.bool_),
        solar_gate=solar_gate,
        sky_down=sky_table_down[:, 2],    # stride-12 column view (real path)
        sky_side=sky_table_side[:, 2],
        surface_sun=0.95,                 # Python float -> f64 entry (real)
        surface_sh=0.90,
        lup=lup, reflection_factor=F32(0.35),
    )


def main() -> None:
    print(f'host loadavg at start: {os.getloadavg()}')
    print(f'numba threads: {THREADS} (pinned like n8_02)')
    results = {}
    first_use = {}

    for B, n_calls in ((128, 300), (1024, 100)):
        args = realistic_args(B, seed=20260922 + B)

        # ---- first use, separately (before any warm loop) ----
        t0 = time.perf_counter()
        ref_a = cyl._longwave_primary(**args)
        first_use[('A', B)] = time.perf_counter() - t0

        t0 = time.perf_counter()
        ref_c0 = native_lw.native_longwave_primary(**args)
        first_use[('C0', B)] = time.perf_counter() - t0

        t0 = time.perf_counter()
        handle = nh.prepare_native_handle()
        first_use[('H_prepare', B)] = time.perf_counter() - t0
        t0 = time.perf_counter()
        ref_h = handle.execute(**args)
        first_use[('H_first_exec', B)] = time.perf_counter() - t0
        t0 = time.perf_counter()
        nh.prepare_native_handle()          # registry hit
        first_use[('H_prepare_cached', B)] = time.perf_counter() - t0

        assert np.array_equal(ref_a.view(np.uint32), ref_c0.view(np.uint32))
        assert np.array_equal(ref_a.view(np.uint32), ref_h.view(np.uint32))

        # sanity: same admission path (f64 entry) as the real pipeline
        assert isinstance(args['surface_sun'], float)

        arms = {
            'C0': lambda a=args: native_lw.native_longwave_primary(**a),
            'H': lambda a=args: handle.execute(**a),
            'A': lambda a=args: cyl._longwave_primary(**a),
        }
        # E: raw pre-marshaled ctypes entry (decomposes H into kernel vs
        # validation/marshal; diagnostic only, not a shipping arm)
        entry = handle._entries['f64']
        flat_down = np.ascontiguousarray(args['sky_down'])
        flat_side = np.ascontiguousarray(args['sky_side'])
        e_args = (args['sh'].ctypes.data, args['vs'].ctypes.data,
                  args['vb'].ctypes.data,
                  args['sun'].view(np.uint8).ctypes.data,
                  args['shade'].view(np.uint8).ctypes.data,
                  args['solid'].ctypes.data, args['sine'].ctypes.data,
                  args['cosine'].ctypes.data,
                  args['solar_gate'].view(np.uint8).ctypes.data,
                  flat_down.ctypes.data, 1, flat_side.ctypes.data, 1,
                  float(args['surface_sun']), float(args['surface_sh']),
                  args['lup'].ctypes.data, float(args['reflection_factor']),
                  B, P, (e_out := np.empty((B, 7), F32)).ctypes.data)
        arms['E'] = lambda: entry(*e_args)
        # one untimed warm block to level caches
        for fn in arms.values():
            for _ in range(n_calls // 10):
                fn()
        per_call = {k: [] for k in arms}
        for _rep in range(5):                      # interleaved paired reps
            for name, fn in arms.items():
                t0 = time.perf_counter()
                for _ in range(n_calls):
                    fn()
                per_call[name].append(
                    (time.perf_counter() - t0) / n_calls)
        results[B] = {k: statistics.median(v) for k, v in per_call.items()}
        print(f'\nB={B}  P={P}  n={n_calls} calls x 5 reps (median per call)')
        for k in ('A', 'C0', 'H', 'E'):
            us = results[B][k] * 1e6
            spread = (min(per_call[k]) * 1e6, max(per_call[k]) * 1e6)
            print(f'  {k:>2}: {us:8.1f} us/call   (rep min/max '
                  f'{spread[0]:.1f}/{spread[1]:.1f})')
        removed = (results[B]['C0'] - results[B]['H']) * 1e6
        print(f'  removed prep overhead (C0-H): {removed:8.1f} us/call')
        print(f'  A/H speedup of native handle vs Numba: '
              f'{results[B]["A"] / results[B]["H"]:.2f}x')

    # ---- island counterfactual reproduction (n8_02 blocks-per-run: 432/96)
    print('\nisland-level extrapolation (leaf medians x n8_02 call counts):')
    for B, calls in ((128, 432), (1024, 96)):
        a = results[B]['A'] * calls
        h = results[B]['H'] * calls
        c0 = results[B]['C0'] * calls
        print(f'  B={B}: A={a * 1e3:7.1f} ms  C0={c0 * 1e3:7.1f} ms  '
              f'H={h * 1e3:7.1f} ms  ->  A/H = {a / h:.2f}x'
              f'   (n8_02 counterfactual b128: 63.1 ms numba vs 39.0 ms'
              f' loader-fixed native = 1.62x)')
    print('\nfirst-use (same process, in order A -> C0 -> H):')
    for (k, B), t in first_use.items():
        print(f'  {k:>16} B={B:>4}: {t * 1e3:9.2f} ms')
    ident = handle.identity()
    print(f"\nhandle: generation={ident['generation'][:16]}... "
          f"kernel={ident['kernel_sha256'][:16]}... gang={ident['gang']} "
          f"pid={ident['pid']} threads={THREADS}")
    print(f'host loadavg at end: {os.getloadavg()}')
    print('ambient note: shared 10-core host; other optimization agents may '
          'be active; medians over interleaved paired reps reported')


if __name__ == '__main__':
    main()
