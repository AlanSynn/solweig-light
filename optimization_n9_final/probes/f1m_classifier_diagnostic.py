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
"""F1M classifier DIAGNOSTIC: FULL classification cost, both sides.

  old: dense _classes classification + pack_masks_aosoa transpose-pack
  new: direct AoSoA classify_block_aosoa INCLUDING supplied-scratch clearing

LABELED DIAGNOSTIC (variant-selection data for F2 review). This is NOT the
F3 verdict: small n, tuning inputs, per-cell loadavg annotated, no
inferential claims, never added into any protocol timer.
"""
import json
import os
import platform
import statistics
import sys
import time

import numpy as np

REPS = 15


def loadavg_triple():
    return tuple(round(v, 3) for v in os.getloadavg())


def vault(patches=153):
    bands = 15
    per_band = max(1, -(-patches // bands))
    altitudes = np.repeat(np.linspace(6.0, 84.0, bands).astype(np.float32), per_band)
    azimuths = np.tile(np.linspace(0.0, 350.0, per_band).astype(np.float32), bands)
    return np.column_stack((altitudes, azimuths))[:patches].astype(np.float32)


def time_ns(fn):
    t0 = time.perf_counter_ns()
    fn()
    return time.perf_counter_ns() - t0


def main():
    from solweig_light._native_dispatch import direct_aosoa as da
    from solweig_light.radiation.patch_radiation import _classes, patch_geometry

    geometry = patch_geometry(vault(153))
    patches = geometry.altitude.size
    altitude = np.array(np.float32(35.0))
    azimuth = np.array(np.float32(140.0))
    rng = np.random.default_rng(9)
    asvf_pool = rng.uniform(0.02, 1.0, size=1024).astype(np.float32)
    difference = np.abs(azimuth - geometry.azimuth)
    active_subset = (difference > 90) & (difference < 270)

    result = {
        'label': 'DIAGNOSTIC -- variant-selection data only, NOT the F3 verdict',
        'protocol': 'outside N9-CONT-v1 timers; component attribution only',
        'host': {'platform': platform.platform(), 'machine': platform.machine(),
                 'python': sys.version.split()[0], 'numba': __import__('numba').__version__,
                 'numpy': np.__version__},
        'numba_threads': os.environ.get('NUMBA_NUM_THREADS'),
        'patches': patches,
        'width': 8,
        'reps': REPS,
        'cells': [],
    }
    start_load = loadavg_triple()
    result['loadavg_start'] = start_load
    result['window_gate'] = (
        'MET' if start_load[0] < 5.0 else
        'NOT MET (1-min loadavg >= 5.0): numbers are noise-contaminated by '
        'concurrent host work; re-run in a quiet window before F2/F3 rely '
        'on any magnitude here. Directional parity observations only.')

    for block in (128, 1024):
        asvf = np.ascontiguousarray(np.resize(asvf_pool, block))
        gangs = -(-block // 8)
        sun_scratch = np.empty((gangs, patches, 8), dtype=np.bool_)
        shade_scratch = np.empty((gangs, patches, 8), dtype=np.bool_)
        for active_name, active in (('whole-vault active=None', None),
                                    ('solar-gate subset', active_subset)):
            def old_full():
                masks = _classes(altitude, azimuth, geometry, asvf, 0, block, active=active)
                return da.pack_masks_aosoa(*masks, width=8)

            def old_dense():
                return _classes(altitude, azimuth, geometry, asvf, 0, block, active=active)

            def new_full():
                return da.classify_block_aosoa(altitude, azimuth, geometry, asvf,
                                               0, block, active=active,
                                               sun_out=sun_scratch, shade_out=shade_scratch)

            # Warmup (JIT + caches), then interleaved measurement.
            for _ in range(3):
                old_full(); new_full()
            samples = {k: [] for k in ('old_full', 'old_dense', 'new_full_with_clearing')}
            for _ in range(REPS):
                samples['old_full'].append(time_ns(old_full))
                samples['new_full_with_clearing'].append(time_ns(new_full))
                samples['old_dense'].append(time_ns(old_dense))
            cell = {'block': block, 'active': active_name,
                    'loadavg_cell': loadavg_triple(), 'ms': {}}
            for name, values in samples.items():
                cell['ms'][name] = {
                    'raw_us': [round(v / 1000, 1) for v in values],
                    'median': round(statistics.median(values) / 1000, 1),
                    'min': round(min(values) / 1000, 1),
                    'mean': round(statistics.fmean(values) / 1000, 1),
                }
            # DERIVED attribution: pack cost alone = old_full - old_dense
            # (per-rep differences, labeled derivation, not a separate timer).
            derived = [f - dns for f, dns in zip(samples['old_full'], samples['old_dense'])]
            cell['ms']['pack_only_DERIVED'] = {
                'raw_us': [round(v / 1000, 1) for v in derived],
                'median': round(statistics.median(derived) / 1000, 1),
                'min': round(min(derived) / 1000, 1),
                'mean': round(statistics.fmean(derived) / 1000, 1),
            }
            result['cells'].append(cell)

    result['loadavg_end'] = loadavg_triple()
    out_path = sys.argv[1] if len(sys.argv) > 1 else \
        'optimization_n9_final/evidence/f1m_classifier_diagnostic.json'
    with open(out_path, 'w') as fh:
        json.dump(result, fh, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
