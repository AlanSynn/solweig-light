#!/usr/bin/env python3
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
"""N8-13 quiet-window A/B/C comparison harness (DO NOT TIME until the
coordinator sends an explicit GO).

Binding protocol (team-lead + n8_30_review_n8_11_layout.md notes):
* report BOTH B=128 AND B=1024 with per-size producer/feed accounting --
  the producer-vs-dense penalty at b128 must be visible, not averaged away
  (N8-11 review note N1);
* mixes: all-binary / mix(P=153) / all-raw per size;
* A arm = frozen _longwave_primary (parallel and serial labels) on the
  dense decode path;
* B arm = N8-12's lw_primary_b adapter (dispatches row-major bodies and
  counts the zero-copy uint32->f32 view); the `lanes` variant is
  experimental and NOT the control. Pure kernel-leaf rows use
  lw_primary_b_parallel directly;
* C arm = N8-13 native AoSoA consumer (this task); kernel-leaf row calls
  the loaded dylib entry directly, bypassing the Python guards;
* bitwise A == B == C asserted on EVERY config before any timing;
* same AoSoA buffer feeds B and C (float32-view convention, note N6);
* min-of-N reported (median recorded alongside);
* INFORMATIONAL / NON-PROMOTION: N8-31 owns the protocol cells.

Usage:
  python quiet_window_abc.py --check-only      # parity smoke, no timing
  python quiet_window_abc.py                   # TIMED: GO window ONLY
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_MODULE_DIR = Path(__file__).resolve().parent
for _p in (str(_MODULE_DIR),
           str(_MODULE_DIR.parents[2] / 'tests' / 'optimization_v8' / 'native'),
           str(_MODULE_DIR.parent / 'layout')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from native_test_helpers import adversarial_inputs, pack_mask  # noqa: E402
from lw_reference_oracle import kernel_pair  # noqa: E402
import direct_aosoa as da  # noqa: E402
import lw_native_aosoa  # noqa: E402
from solweig_light.geometry.visibility import PackedVisibility, _EncodedPatch
from solweig_light.geometry.visibility_compiled import decode_block

F32 = np.float32
BLOCK_SIZES = (128, 1024)
MIXES = ('all-binary', 'mix', 'all-raw')
P_PATCHES = 153
REPS = 9


def _find_b_consumer():
    """N8-12's landed control: experiments/optimization_v8/numba/..."""
    directory = _MODULE_DIR.parent / 'numba'
    if not directory.is_dir():
        return None, None, None
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))
    py = directory / 'lw_b_control.py'
    if not py.is_file():
        return None, None, None
    # Load under the real module stem: numba's cache unpickles the kernel
    # environment by module name, so an alias breaks cache reuse.
    spec = importlib.util.spec_from_file_location(py.stem, py)
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(py.stem, mod)
    spec.loader.exec_module(mod)
    return (f'{py.name}:lw_primary_b', mod.lw_primary_b,
            mod.lw_primary_b_parallel)


def _patch(mode, rng, B):
    """One _EncodedPatch of ``mode`` covering B rows (N8-11 encodings)."""
    if mode == 'raw':
        bits = rng.integers(0, 2 ** 32, size=B, dtype=np.uint64
                            ).astype(np.uint32)
        return _EncodedPatch(mode, bits.astype('<u4').tobytes())
    if mode == 'ternary':
        codes = rng.integers(0, 3, size=B).astype(np.uint8)
        padded = np.zeros((B + 3) // 4 * 4, dtype=np.uint8)
        padded[:B] = codes
        payload = (padded[0::4] | (padded[1::4] << 2) | (padded[2::4] << 4)
                   | (padded[3::4] << 6)).tobytes()
        return _EncodedPatch(mode, payload)
    codes = rng.integers(0, 2, size=B).astype(np.uint8)
    return _EncodedPatch(mode, np.packbits(codes, bitorder='little').tobytes())


def _channels(mix, rng, B, P):
    """Three PackedVisibility channels under the requested encoding mix."""
    rotation = {'all-binary': ('binary',), 'all-raw': ('raw',),
                'mix': ('binary', 'raw', 'ternary')}[mix]
    channels = []
    for _ in range(3):
        patches = [_patch(rotation[i % len(rotation)], rng, B)
                   for i in range(P)]
        channels.append(PackedVisibility((1, B, P), tuple(patches)))
    return channels


def _timeit(reps, fn, *a, **k):
    fn(*a, **k)
    times = []
    for _ in range(reps):
        t0 = time.perf_counter()
        fn(*a, **k)
        times.append((time.perf_counter() - t0) * 1e3)
    return {'min_ms': min(times), 'median_ms': statistics.median(times)}


def _kernel_leaf_native(views, sun_a, shade_a, base, B, entry):
    """C kernel-leaf: the adapter's exact ctypes invocation, guards off.

    Mirrors lw_native_aosoa.primary_aosoa's entry call byte for byte
    (solar_gate is the ABI gate; ``directions`` is admitted-but-never-read
    and carries no ABI slot; sky columns pass element strides)."""
    _buf = lw_native_aosoa._buffer
    out = np.empty((B, 7), dtype=F32)
    entry(
        _buf(views[0]), _buf(views[1]), _buf(views[2]),
        _buf(sun_a.view(np.uint8)), _buf(shade_a.view(np.uint8)),
        _buf(base['solid']), _buf(base['sine']), _buf(base['cosine']),
        _buf(base['solar_gate'].view(np.uint8)),
        _buf(base['sky_down']), base['sky_down'].strides[0] // 4,
        _buf(base['sky_side']), base['sky_side'].strides[0] // 4,
        float(base['surface_sun']), float(base['surface_sh']),
        _buf(base['lup']),
        lw_native_aosoa._reflection_spec(base['reflection_factor']),
        B, P_PATCHES,
        _buf(out),
    )
    return out


def run(check_only: bool, block_sizes='128,1024', max_loadavg=None) -> int:
    sizes = tuple(int(s) for s in str(block_sizes).split(','))
    parallel, serial = kernel_pair()
    b_name, b_fn, b_kernel = _find_b_consumer()
    load_start = os.getloadavg()
    if max_loadavg is not None and load_start[0] > max_loadavg:
        # Tier gate: abort BEFORE any timed work; archive with the check
        # tag so a gate-refusal is never mistaken for a measurement.
        _archive({'recorded_utc': datetime.now(timezone.utc).strftime(
                      '%Y-%m-%dT%H:%M:%SZ'),
                  'status': ('INFORMATIONAL / NON-PROMOTION (N8-31 owns '
                             'protocol cells)'),
                  'mode': 'check-only (gate refused; no timing)',
                  'block_sizes': list(sizes), 'mixes': list(MIXES),
                  'patches': P_PATCHES, 'reps': 0,
                  'ambient_loadavg_start': load_start,
                  'gate': f'max_loadavg={max_loadavg} exceeded at start'},
                 check_only=True)
        print(f'[gate] 1-min loadavg {load_start[0]:.2f} > {max_loadavg}; '
              'aborting before any timed work', file=sys.stderr)
        return 2
    record = {
        'recorded_utc': datetime.now(timezone.utc).strftime(
            '%Y-%m-%dT%H:%M:%SZ'),
        'status': 'INFORMATIONAL / NON-PROMOTION (N8-31 owns protocol cells)',
        'mode': 'check-only (no timing)' if check_only else 'TIMED',
        'block_sizes': list(sizes),
        'mixes': list(MIXES),
        'patches': P_PATCHES,
        'reps': 0 if check_only else REPS,
        'stat': 'min_ms (median_ms recorded alongside)',
        'b_consumer': b_name,
        'ambient_loadavg_start': load_start,
        'per_block': [],
    }

    for B in sizes:
        for mix in MIXES:
            rng = np.random.default_rng(100_003 * B + 7919 * MIXES.index(mix))
            base = adversarial_inputs(B, P_PATCHES, seed=97 * B)
            sh_c, vs_c, vb_c = _channels(mix, rng, B, P_PATCHES)
            cell = {'B': B, 'mix': mix, 'parity': None, 'producer_ms': {},
                    'kernel_ms': {}, 'adapter_ms': {}}

            # -- producers (A decodes dense; B/C produce AoSoA) ----------
            dense = [decode_block(ch, 0, B, P_PATCHES)
                     for ch in (sh_c, vs_c, vb_c)]
            args_a = dict(base)
            args_a['sh'], args_a['vs'], args_a['vb'] = dense
            aosoa = da.produce_blocks_aosoa(sh_c, vs_c, vb_c, 0, B,
                                            P_PATCHES, width=8)
            assert aosoa is not None, 'producer declined admitted channel'
            views = [block.view(np.float32) for block in aosoa]
            sun_a = pack_mask(base['sun'], B)
            shade_a = pack_mask(base['shade'], B)

            # -- correctness first: A == C (== B when present) ------------
            out_a = parallel(**args_a)
            out_c = lw_native_aosoa.primary_aosoa(
                views[0], views[1], views[2], sun_a, shade_a,
                base['solid'], base['sine'], base['cosine'],
                base['directions'], base['gate'], base['solar_gate'],
                base['sky_down'], base['sky_side'], base['surface_sun'],
                base['surface_sh'], base['lup'], base['reflection_factor'],
                B)
            parity = np.array_equal(out_a.view(np.uint32),
                                    out_c.view(np.uint32))
            _, _entries = lw_native_aosoa.load_generation()
            _leaf = _kernel_leaf_native(views, sun_a, shade_a, base, B,
                                        _entries['f64'])
            parity = parity and np.array_equal(out_a.view(np.uint32),
                                               _leaf.view(np.uint32))
            out_bk = None
            if b_fn is not None:
                out_b = b_fn(aosoa[0], aosoa[1], aosoa[2], sun_a, shade_a,
                             base['solid'], base['sine'], base['cosine'],
                             base['directions'], base['gate'],
                             base['solar_gate'], base['sky_down'],
                             base['sky_side'], base['surface_sun'],
                             base['surface_sh'], base['lup'],
                             base['reflection_factor'], B)
                parity = parity and np.array_equal(out_a.view(np.uint32),
                                                   out_b.view(np.uint32))
                out_bk = b_kernel(views[0], views[1], views[2], sun_a,
                                  shade_a, base['solid'], base['sine'],
                                  base['cosine'], base['directions'],
                                  base['gate'], base['solar_gate'],
                                  base['sky_down'], base['sky_side'],
                                  base['surface_sun'], base['surface_sh'],
                                  base['lup'], base['reflection_factor'],
                                  B, out_b)
                parity = parity and np.array_equal(out_a.view(np.uint32),
                                                   out_bk.view(np.uint32))
            if not parity:
                cell['parity'] = 'FAIL'
                record['per_block'].append(cell)
                record['ambient_loadavg_end'] = os.getloadavg()
                _archive(record, check_only)
                return 1
            cell['parity'] = ('pass (A0==C1==C1k==B1==B1k)' if b_fn
                              else 'pass (A0==C1==C1k; B unavailable)')
            if check_only:
                record['per_block'].append(cell)
                continue

            # -- timed: producers ------------------------------------------
            cell['producer_ms']['A_decode_block_x3'] = _timeit(
                REPS, lambda: [decode_block(ch, 0, B, P_PATCHES)
                               for ch in (sh_c, vs_c, vb_c)])
            cell['producer_ms']['BC_produce_blocks_aosoa'] = _timeit(
                REPS, da.produce_blocks_aosoa, sh_c, vs_c, vb_c, 0, B,
                P_PATCHES, width=8)
            # -- timed: adapters (charged to B1/C1, not A0) ----------------
            cell['adapter_ms']['BC_float32_views_x3'] = _timeit(
                REPS, lambda: [b.view(np.float32) for b in aosoa])
            cell['adapter_ms']['BC_pack_masks_x2'] = _timeit(
                REPS, lambda: (pack_mask(base['sun'], B),
                               pack_mask(base['shade'], B)))
            # -- timed: kernels --------------------------------------------
            cell['kernel_ms']['A0_parallel_dense'] = _timeit(
                REPS, parallel, **args_a)
            cell['kernel_ms']['A0_serial_dense'] = _timeit(
                REPS, serial, **args_a)
            cell['kernel_ms']['C1_native_aosoa_adapter'] = _timeit(
                REPS, lw_native_aosoa.primary_aosoa,
                views[0], views[1], views[2], sun_a, shade_a,
                base['solid'], base['sine'], base['cosine'],
                base['directions'], base['gate'], base['solar_gate'],
                base['sky_down'], base['sky_side'], base['surface_sun'],
                base['surface_sh'], base['lup'], base['reflection_factor'],
                B)
            lib, entries = lw_native_aosoa.load_generation()
            cell['kernel_ms']['C1k_native_entry_leaf'] = _timeit(
                REPS, _kernel_leaf_native, views, sun_a, shade_a, base, B,
                entries['f64'])
            if b_fn is not None:
                cell['kernel_ms']['B1_numba_adapter'] = _timeit(
                    REPS, b_fn, aosoa[0], aosoa[1], aosoa[2], sun_a,
                    shade_a, base['solid'], base['sine'], base['cosine'],
                    base['directions'], base['gate'], base['solar_gate'],
                    base['sky_down'], base['sky_side'], base['surface_sun'],
                    base['surface_sh'], base['lup'],
                    base['reflection_factor'], B)
                cell['kernel_ms']['B1k_numba_parallel_leaf'] = _timeit(
                    REPS, b_kernel, views[0], views[1], views[2], sun_a,
                    shade_a, base['solid'], base['sine'], base['cosine'],
                    base['directions'], base['gate'], base['solar_gate'],
                    base['sky_down'], base['sky_side'], base['surface_sun'],
                    base['surface_sh'], base['lup'],
                    base['reflection_factor'], B, out_bk)
            record['per_block'].append(cell)
            print(f'  timed cell done: B={B} mix={mix} '
                  f'(loadavg {os.getloadavg()[0]:.1f})', file=sys.stderr)

    record['ambient_loadavg_end'] = os.getloadavg()
    record['n1_note'] = ('producer cost is reported per block size and mix; '
                         'the direct producer reverses vs decode+transpose '
                         'at B=128 in 3 of 6 N8-11 cells, so C1 end-to-end '
                         'totals at 128 must include that penalty honestly')
    _archive(record, check_only)
    return 0


def _archive(record, check_only):
    evidence = _MODULE_DIR / 'evidence'
    evidence.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    tag = 'check' if check_only else 'timed'
    path = evidence / f'abc_quiet_window_{tag}_{stamp}.json'
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
    print(json.dumps(record, indent=2, sort_keys=True))
    print(f'[archived] {path}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--check-only', action='store_true',
                    help='parity smoke only; no timing loops')
    ap.add_argument('--block-sizes', default='128,1024',
                    help='comma list of block sizes (default 128,1024 keeps '
                         'the frozen-harness invocation bit-identical)')
    ap.add_argument('--max-loadavg', type=float, default=None,
                    help='operational guard: abort before any timed work '
                         'when the 1-min loadavg exceeds this (tier gate; '
                         'per-cell loadavg still goes to stderr for the '
                         'censor threshold)')
    ns = ap.parse_args()
    sys.exit(run(ns.check_only, ns.block_sizes, ns.max_loadavg))
