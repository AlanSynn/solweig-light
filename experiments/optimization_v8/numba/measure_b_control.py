#SOLWEIG-GPU: GPU-accelerated SOLWEIG model for urban thermal comfort simulation
#Copyright (C) 2022–2025 Harsh Kamth and Naveen Sudharsan

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
"""N8-12 B-control leaf timing -- INFORMATIONAL, NON-PROMOTION.

Protocol cells belong to N8-31; nothing here promotes anything. These are
small quick spot measurements (no sweeps) at B in {128, 1024}, P=153, W=8,
min-of-N, so the integrator can see the adapter-counted end-to-end shape of
the two arms on identical data:

  A-end-to-end: decode_block x3 + _classes + frozen _longwave_primary
  B-end-to-end: produce_blocks_aosoa + classify_block_aosoa + lw_primary_b
                (adapter admission + zero-copy views + kernel inside the call)

plus kernel-only leaves (frozen kernel on dense; B row-major serial and
parallel on pre-produced AoSoA; experimental lanes formulation) and BOTH
producer+classifier leaves (A-side decode-x3 + _classes vs B-side
produce_blocks_aosoa + classify_block_aosoa) so the producer cost is
accounted PER SIZE: per review note N1 (n8_30_review_n8_11_layout.md), the
direct producer's win over decode is B=1024-only and REVERSES at the
production block size 128 in 3 of 6 cells -- the per-block rows below are
the regime that matters and must not be read off the B=1024 rows. Every
timed configuration is cross-checked bitwise (A vs B outputs) so the
numbers describe CORRECT artifacts. Ambient loadavg is recorded around
every block; do NOT run this during a coordinated quiet window.

Usage: .venv/bin/python experiments/optimization_v8/numba/measure_b_control.py
Writes results/measure_b_control.json next to this file.
"""
from __future__ import annotations

import gc
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import numba

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'layout'))

import direct_aosoa as da  # noqa: E402
import lw_b_control as bc  # noqa: E402
from solweig_light.geometry.visibility import VisibilityBuilder  # noqa: E402
from solweig_light.geometry.visibility_compiled import (  # noqa: E402
    _descriptor, decode_block)
from solweig_light.radiation.cylinder_longwave import _longwave_primary  # noqa: E402
from solweig_light.radiation.patch_radiation import (  # noqa: E402
    _class_coefficients, _classes, patch_geometry)

PIXELS = 1024          # one synthetic 32x32 tile
PATCHES = 153          # production vault size
WIDTH = 8
THREADS = max(1, min(4, numba.config.NUMBA_NUM_THREADS))
numba.set_num_threads(THREADS)
MIXES = {
    'mix': ('binary', 'ternary', 'raw'),
    'all-binary': ('binary',),
    'all-raw': ('raw',),
}
RAW_POOL = np.array([0x00000000, 0x3F800000, 0x40000000, 0x40490FDB, 0x7FC00000,
                     0xFF800000, 0x3F7FFFFF, 0x4B7FFFFF], dtype=np.uint32)


def timed(fn, repeats, warmup=3):
    for _ in range(warmup):
        fn()
    gc.collect()
    gc.disable()
    try:
        samples = []
        for _ in range(repeats):
            begin = time.perf_counter()
            fn()
            samples.append(time.perf_counter() - begin)
    finally:
        gc.enable()
    return {'min_s': min(samples), 'median_s': float(np.median(samples)),
            'repeats': repeats}


def build_channel(mix, seed):
    rng = np.random.default_rng(seed)
    builder = VisibilityBuilder((32, 32, PATCHES))
    for patch in range(PATCHES):
        mode = MIXES[mix][patch % len(MIXES[mix])]
        if mode == 'raw':
            plane = rng.choice(RAW_POOL, size=(32, 32)).view(np.float32)
        else:
            high = 3 if mode == 'ternary' else 2
            plane = rng.integers(0, high, size=(32, 32)).astype(np.float32)
        builder.append(np.ascontiguousarray(plane))
    return builder.finish()


def vault_table(patches=PATCHES):
    bands = 15
    per_band = -(-patches // bands)
    return np.column_stack((np.repeat(np.linspace(6.0, 84.0, bands).astype(np.float32), per_band),
                            np.tile(np.linspace(0.0, 350.0, per_band).astype(np.float32),
                                    bands)))[:patches].astype(np.float32)


def seed_of(text):
    return sum(text.encode())


def main():
    geometry = patch_geometry(vault_table())
    rng = np.random.default_rng(2027)
    asvf = rng.uniform(0.02, 1.0, size=PIXELS).astype(np.float32)
    altitude = np.array(np.float32(35.0))
    azimuth = np.array(np.float32(140.0))
    difference = np.abs(azimuth - geometry.azimuth)
    active = (difference > 90) & (difference < 270)
    prepared = _class_coefficients(altitude, azimuth, geometry, asvf, active)
    assert prepared is not None
    solid = rng.uniform(0.001, 0.05, PATCHES).astype(np.float32)
    sine = rng.uniform(-1, 1, PATCHES).astype(np.float32)
    cosine = rng.uniform(-1, 1, PATCHES).astype(np.float32)
    directions = np.zeros((PATCHES, 4), np.float32)
    gate = np.zeros((PATCHES, 4), np.bool_)
    sky_down = rng.uniform(300, 500, PATCHES).astype(np.float32)
    sky_side = rng.uniform(300, 500, PATCHES).astype(np.float32)
    lup = rng.uniform(380, 420, PIXELS).astype(np.float32)
    factor = np.float32(0.3)
    surface_sun, surface_sh = 350.0, 320.0     # f64 profile (real pipeline)

    report = {
        'label': 'INFORMATIONAL, NON-PROMOTION -- protocol cells belong to N8-31',
        'provenance': {
            'timestamp_utc': datetime.now(timezone.utc).isoformat(),
            'git_head': subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=HERE,
                                       capture_output=True, text=True).stdout.strip(),
            'branch': subprocess.run(['git', 'branch', '--show-current'], cwd=HERE,
                                     capture_output=True, text=True).stdout.strip(),
            'platform': platform.platform(),
            'python': platform.python_version(),
            'numpy': np.__version__,
            'numba_threads': THREADS,
            'loadavg_start': os.getloadavg(),
        },
        'blocks': [],
    }

    for block_pixels in (128, 1024):
        start, stop = PIXELS - block_pixels, PIXELS
        rows = stop - start
        for mix in MIXES:
            channels = tuple(build_channel(mix, seed_of(mix) + k) for k in range(3))
            for channel in channels:
                _descriptor(channel)          # warm per-channel descriptor cache
            lup_block = lup[start:stop]

            def arm_a():
                dense = tuple(decode_block(channel, start, stop, PATCHES)
                              for channel in channels)
                sun, shade = _classes(altitude, azimuth, geometry, asvf, start,
                                      stop, active=active, prepared=prepared)
                return _longwave_primary(dense[0], dense[1], dense[2], sun, shade,
                                         solid, sine, cosine, directions, gate,
                                         active, sky_down, sky_side, surface_sun,
                                         surface_sh, lup_block, factor)

            def arm_b():
                blocks = da.produce_blocks_aosoa(*channels, start, stop, PATCHES,
                                                 width=WIDTH)
                sun, shade = da.classify_block_aosoa(altitude, azimuth, geometry,
                                                     asvf, start, stop,
                                                     active=active,
                                                     prepared=prepared, width=WIDTH)
                return bc.lw_primary_b(*blocks, sun=sun, shade=shade, solid=solid,
                                       sine=sine, cosine=cosine, directions=directions,
                                       gate=gate, solar_gate=active, sky_down=sky_down,
                                       sky_side=sky_side, surface_sun=surface_sun,
                                       surface_sh=surface_sh, lup=lup_block,
                                       reflection_factor=factor, rows=rows,
                                       parallel=True)

            # Pre-produced/pre-decoded fixtures for the kernel-only leaves.
            blocks = da.produce_blocks_aosoa(*channels, start, stop, PATCHES,
                                             width=WIDTH)
            b_sun, b_shade = da.classify_block_aosoa(altitude, azimuth, geometry,
                                                     asvf, start, stop,
                                                     active=active,
                                                     prepared=prepared, width=WIDTH)
            dense = tuple(decode_block(channel, start, stop, PATCHES)
                          for channel in channels)
            a_sun, a_shade = _classes(altitude, azimuth, geometry, asvf, start, stop,
                                      active=active, prepared=prepared)
            sh32 = blocks[0].view(np.float32)
            vs32 = blocks[1].view(np.float32)
            vb32 = blocks[2].view(np.float32)
            b_out = np.zeros((rows, 7), np.float32)
            row_out = np.zeros((rows, 7), np.float32)

            def leaf_a_kernel():
                return _longwave_primary(dense[0], dense[1], dense[2], a_sun, a_shade,
                                         solid, sine, cosine, directions, gate,
                                         active, sky_down, sky_side, surface_sun,
                                         surface_sh, lup_block, factor)

            def leaf_b_row_raw():
                return bc.lw_primary_b_parallel(sh32, vs32, vb32, b_sun, b_shade,
                                                solid, sine, cosine, directions, gate,
                                                active, sky_down, sky_side,
                                                surface_sun, surface_sh, lup_block,
                                                factor, rows, row_out)

            def leaf_b_row_parallel():
                return bc.lw_primary_b(*blocks, sun=b_sun, shade=b_shade, solid=solid,
                                       sine=sine, cosine=cosine, directions=directions,
                                       gate=gate, solar_gate=active, sky_down=sky_down,
                                       sky_side=sky_side, surface_sun=surface_sun,
                                       surface_sh=surface_sh, lup=lup_block,
                                       reflection_factor=factor, rows=rows,
                                       parallel=True)

            def leaf_b_lanes():
                return bc.lw_primary_b_lanes_serial(sh32, vs32, vb32, b_sun, b_shade,
                                                    solid, sine, cosine, directions,
                                                    gate, active, sky_down, sky_side,
                                                    surface_sun, surface_sh, lup_block,
                                                    factor, rows, b_out)

            def leaf_a_producer():
                tuple(decode_block(channel, start, stop, PATCHES)
                      for channel in channels)
                return _classes(altitude, azimuth, geometry, asvf, start, stop,
                                active=active, prepared=prepared)

            def leaf_b_producer():
                da.produce_blocks_aosoa(*channels, start, stop, PATCHES, width=WIDTH)
                return da.classify_block_aosoa(altitude, azimuth, geometry, asvf,
                                               start, stop, active=active,
                                               prepared=prepared, width=WIDTH)

            repeats = 100 if block_pixels == 128 else 25
            arms = {
                'A-end-to-end': arm_a,
                'B-end-to-end': arm_b,
                'leaf-A-producer+classify': leaf_a_producer,
                'leaf-B-producer+classify': leaf_b_producer,
                'leaf-A-frozen-kernel': leaf_a_kernel,
                'leaf-B-row-parallel-adapter': leaf_b_row_parallel,
                'leaf-B-row-parallel-raw': leaf_b_row_raw,
                'leaf-B-lanes-raw': leaf_b_lanes,
            }
            entry = {'block_pixels': block_pixels, 'mix': mix, 'rows': rows,
                     'width': WIDTH, 'loadavg': os.getloadavg(), 'arms': {}}
            for name, fn in arms.items():
                entry['arms'][name] = timed(fn, repeats)

            # Correctness cross-check on the exact timed artifacts.
            out_a = arm_a()
            out_b = arm_b()
            entry['bitwise_equal_A_vs_B'] = bool(
                np.array_equal(out_a.view(np.uint32), out_b.view(np.uint32)))
            report['blocks'].append(entry)

    report['provenance']['loadavg_end'] = os.getloadavg()
    target = HERE / 'results' / 'measure_b_control.json'
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(report, indent=1))
    print_table(report)
    print(f'\nwrote {target}')


def print_table(report):
    print('N8-12 B-control leaf timing (INFORMATIONAL, NON-PROMOTION)')
    print(f"provenance: {report['provenance']['git_head']} "
          f"({report['provenance']['branch']}), threads "
          f"{report['provenance']['numba_threads']}, loadavg "
          f"{[round(x, 2) for x in report['provenance']['loadavg_start']]}")
    for entry in report['blocks']:
        print(f"B={entry['block_pixels']:4d} W={entry['width']} {entry['mix']:<10s} "
              f"(loadavg {[round(x, 2) for x in entry['loadavg']]})")
        for name, arm in entry['arms'].items():
            print(f"  {name:<28s} min {arm['min_s']*1e3:8.3f} ms  "
                  f"median {arm['median_s']*1e3:8.3f} ms")
        a_prod = entry['arms']['leaf-A-producer+classify']['min_s'] * 1e3
        b_prod = entry['arms']['leaf-B-producer+classify']['min_s'] * 1e3
        regime = ('PRODUCTION BLOCK SIZE -- note N1 regime: do not read the '
                  'B=1024 rows here' if entry['block_pixels'] == 128 else
                  'full-tile regime')
        print(f"  producer+classify A {a_prod:7.3f} ms vs B {b_prod:7.3f} ms "
              f"-> {'B ahead' if b_prod < a_prod else 'A ahead'}  [{regime}]")
        print(f"  bitwise A==B: {entry['bitwise_equal_A_vs_B']}")


if __name__ == '__main__':
    main()
