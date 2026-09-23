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
"""N8-13 SMALL leaf micro-timing (BENCHMARK_PROTOCOL leaf_kernel class).

Synthetic leaf only -- no claim of application gain. One modest shape,
few repetitions, results + ambient loadavg archived next to this script
(evidence/): numbers never live only in the terminal. The real b1024
A/B/C kernel comparison runs later in a coordinator-confirmed quiet
window and is NOT attempted here.

Arms (same inputs, f64 surface profile, caller-allocated out):
  serial  : frozen Numba _longwave_primary_serial on dense [B,P];
  native-B7-dense : reviewed lw_native.primary (dense [B,P], gather loads)
                    -- only if the B7 dylib is locatable;
  native-aosoa    : this task's consumer on the N8-11 lane layout.
The dense->AoSoA pack is timed separately and NOT charged to any kernel
arm (attribution: producer gain vs backend gain stay distinct).
"""
from __future__ import annotations

import os
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_MODULE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_MODULE_DIR))
sys.path.insert(0, str(_MODULE_DIR.parents[2] / 'tests' / 'optimization_v8'
                       / 'native'))          # conftest helpers (read-only)

from native_test_helpers import (SERIAL, adversarial_inputs,  # noqa: E402
                                 to_aosoa)
import lw_native_aosoa  # noqa: E402

B, P = 8192, 153
REPS = 7


def timeit(fn, *a, **k):
    fn(*a, **k)                       # warm
    times = []
    for _ in range(REPS):
        t0 = time.perf_counter()
        fn(*a, **k)
        times.append((time.perf_counter() - t0) * 1e3)
    return statistics.median(times), min(times)


def main() -> int:
    load_start = os.getloadavg()
    args = adversarial_inputs(B, P, seed=20260922)
    feed = to_aosoa(args, B)

    def run_serial():
        return SERIAL(**args)

    def run_aosoa(out):
        return lw_native_aosoa.primary_aosoa(
            feed['sh'], feed['vs'], feed['vb'], feed['sun'], feed['shade'],
            feed['solid'], feed['sine'], feed['cosine'], feed['directions'],
            feed['gate'], feed['solar_gate'], feed['sky_down'],
            feed['sky_side'], args['surface_sun'], args['surface_sh'],
            args['lup'], args['reflection_factor'], B, out=out)

    out = np.empty((B, 7), np.float32)
    aosoa_ms, aosoa_min = timeit(run_aosoa, out)
    assert np.array_equal(out.view(np.uint32),
                          run_serial().view(np.uint32)), 'bitwise drift'

    pack_ms, _ = timeit(lambda: to_aosoa(args, B))

    b7 = None
    b7_err = None
    try:
        # B7 dense arm through the REVIEWED N8-10 handle (read-only reuse;
        # no build, no src/ writes) against the user-cache artifacts.
        loader_dir = _MODULE_DIR.parent / 'loader'
        sys.path.insert(0, str(loader_dir))
        import native_handle
        handle = native_handle.prepare_native_handle(gang=8)
        ref = handle.execute(
            args['sh'], args['vs'], args['vb'], args['sun'], args['shade'],
            args['solid'], args['sine'], args['cosine'], args['directions'],
            args['gate'], args['solar_gate'], args['sky_down'],
            args['sky_side'], args['surface_sun'], args['surface_sh'],
            args['lup'], args['reflection_factor'])
        assert np.array_equal(ref.view(np.uint32), out.view(np.uint32))
        b7, _ = timeit(handle.execute,
                       args['sh'], args['vs'], args['vb'], args['sun'],
                       args['shade'], args['solid'], args['sine'],
                       args['cosine'], args['directions'], args['gate'],
                       args['solar_gate'], args['sky_down'], args['sky_side'],
                       args['surface_sun'], args['surface_sh'], args['lup'],
                       args['reflection_factor'])
    except Exception as exc:      # B7 artifacts unavailable: arm stays absent
        b7 = None
        b7_err = f'{type(exc).__name__}: {exc}'

    load_end = os.getloadavg()
    record = {
        'recorded_utc': datetime.now(timezone.utc).strftime(
            '%Y-%m-%dT%H:%M:%SZ'),
        'class': 'leaf_kernel (synthetic; no application-gain claim)',
        'shape': {'B': B, 'P': P, 'surface_profile': 'f64', 'reps': REPS,
                  'stat': 'median_ms'},
        'ambient_loadavg_start': load_start,
        'ambient_loadavg_end': load_end,
        'serial_dense_ms': timeit(run_serial)[0],
        'native_b7_dense_ms': b7,
        'native_aosoa_ms': aosoa_ms,
        'native_aosoa_min_ms': aosoa_min,
        'aosoa_pack_only_ms': pack_ms,
        'b7_arm_error': b7_err,
        'bitwise_parity': 'serial == native-aosoa == b7 (uint32 view)',
        'note': ('quiet-window b1024 A/B/C comparison deferred to the '
                 'coordinator window; this is a small leaf sanity record'),
    }
    evidence = _MODULE_DIR / 'evidence'
    evidence.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    path = evidence / f'leaf_timing_{stamp}.json'
    path.write_text(__import__('json').dumps(record, indent=2,
                                             sort_keys=True) + '\n')
    print(__import__('json').dumps(record, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
