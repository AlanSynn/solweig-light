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
"""N8-11 producer measurements (dossier 02_direct_aosoa controls).

Serial producer vs decode_block+transpose (the rejected adapter's cost) at
B=128/B=1024, P=153, binary/ternary/raw mixes, W in {8,4}; classification
as retained [B,P] + packing vs direct AoSoA production. Allocation cost is
reported as exact logical bytes per arm: decode_block allocates its output
inside the numba kernel where tracemalloc cannot see it, so measured peaks
would asymetrically under-report the legacy arms; logical bytes are exact
for every arm. The producer uses zero-copy per-patch descriptor views; the
_fused_descriptor flat-copy alternative is timed once per mix as an
informational line, never charged to the producer.

Usage: .venv/bin/python experiments/optimization_v8/layout/measure_direct_aosoa.py
Writes results/measure_direct_aosoa.json next to this file.
"""
from __future__ import annotations

import gc
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import direct_aosoa as da  # noqa: E402
from solweig_light.geometry.visibility import VisibilityBuilder  # noqa: E402
from solweig_light.geometry.visibility_compiled import (  # noqa: E402
    _descriptor, _fused_descriptor, decode_block)
from solweig_light.radiation.patch_radiation import (  # noqa: E402
    _class_coefficients, _classes, patch_geometry)

PIXELS = 1024          # one synthetic 32x32 tile
PATCHES = 153          # production vault size
MIXES = {
    'mix': ('binary', 'ternary', 'raw'),
    'all-binary': ('binary',),
    'all-raw': ('raw',),
}
RAW_POOL = np.array([0x00000000, 0x3F800000, 0x40000000, 0x40490FDB, 0x7FC00000,
                     0xFF800000, 0x3F7FFFFF, 0x4B7FFFFF], dtype=np.uint32)
LOGICAL_BYTES = {
    'decode': lambda rows, gangs, width, patches: rows * patches * 4,
    'decode+transpose': lambda rows, gangs, width, patches: rows * patches * 4
        + gangs * patches * width * 4,
    'produce-patchmajor': lambda rows, gangs, width, patches: gangs * patches * width * 4,
    'produce-blocked': lambda rows, gangs, width, patches: gangs * patches * width * 4,
    'decode-x3': lambda rows, gangs, width, patches: 3 * rows * patches * 4,
    'produce3-patchmajor': lambda rows, gangs, width, patches: 3 * gangs * patches * width * 4,
    'produce3-blocked': lambda rows, gangs, width, patches: 3 * gangs * patches * width * 4,
    'classes-retained': lambda rows, gangs, width, patches: 2 * rows * patches,
    'classes+pack': lambda rows, gangs, width, patches: 2 * rows * patches
        + 2 * gangs * patches * width,
    'classify-aosoa': lambda rows, gangs, width, patches: 2 * gangs * patches * width,
}


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


def transpose_adapter(channel, start, stop, width):
    """The rejected adapter: legacy dense decode, then transpose to [G,P,W]."""
    dense = decode_block(channel, start, stop, PATCHES)
    rows = stop - start
    gangs = -(-rows // width)
    if rows != gangs * width:
        padded = np.zeros((gangs * width, PATCHES), dtype=np.float32)
        padded[:rows] = dense
        dense = padded
    return dense.view(np.uint32).reshape(gangs, width, PATCHES).transpose(0, 2, 1).copy()


def seed_of(text):
    return sum(text.encode())


def main():
    geometry = patch_geometry(vault_table())
    rng = np.random.default_rng(2026)
    asvf = rng.uniform(0.02, 1.0, size=PIXELS).astype(np.float32)
    altitude = np.array(np.float32(35.0))
    azimuth = np.array(np.float32(140.0))
    difference = np.abs(azimuth - geometry.azimuth)
    active = (difference > 90) & (difference < 270)
    prepared = _class_coefficients(altitude, azimuth, geometry, asvf, active)
    assert prepared is not None

    report = {
        'provenance': {
            'timestamp_utc': datetime.now(timezone.utc).isoformat(),
            'git_head': subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=HERE,
                                       capture_output=True, text=True).stdout.strip(),
            'branch': subprocess.run(['git', 'branch', '--show-current'], cwd=HERE,
                                     capture_output=True, text=True).stdout.strip(),
            'platform': platform.platform(),
            'python': platform.python_version(),
            'numpy': np.__version__,
            'threads': 1,
            'note': 'all producer/classification kernels serial (no prange); '
                    'descriptor views cached per channel before timing; allocation '
                    'cost is exact logical bytes (tracemalloc cannot see numba-'
                    'internal allocations, so measured peaks would favor the '
                    'producer unfairly)',
        },
        'descriptor_first_build_s': {},
        'flat_copy_build_s_informational': {},
        'blocks': [],
        'classification': [],
    }

    for mix in MIXES:
        # Each repeat needs a fresh channel (both descriptors cache per
        # channel), but channel construction must stay OUTSIDE the timed
        # call -- only the descriptor build itself is measured.
        def build_descriptor(fresh, mix=mix):
            return lambda: _descriptor(fresh.pop())

        def build_flat(fresh, mix=mix):
            return lambda: _fused_descriptor(fresh.pop())

        fresh = [build_channel(mix, seed_of(mix)) for _ in range(6)]
        report['descriptor_first_build_s'][mix] = timed(build_descriptor(fresh), 5,
                                                         warmup=1)['min_s']
        fresh = [build_channel(mix, seed_of(mix)) for _ in range(6)]
        report['flat_copy_build_s_informational'][mix] = timed(build_flat(fresh), 5,
                                                                warmup=1)['min_s']

    for block_pixels in (128, 1024):
        start, stop = PIXELS - block_pixels, PIXELS
        for width in da.WIDTHS:
            for mix in MIXES:
                channel = build_channel(mix, seed_of(mix))
                _descriptor(channel)  # warm the per-channel descriptor cache
                rows, gangs = stop - start, -(-(stop - start) // width)
                arms = {
                    'decode': lambda: decode_block(channel, start, stop, PATCHES),
                    'decode+transpose': lambda: transpose_adapter(channel, start, stop, width),
                    'produce-patchmajor': lambda: da.produce_block_aosoa(
                        channel, start, stop, PATCHES, width=width, order='patchmajor'),
                    'produce-blocked': lambda: da.produce_block_aosoa(
                        channel, start, stop, PATCHES, width=width, order='blocked'),
                    'decode-x3': lambda: tuple(decode_block(channel, start, stop, PATCHES)
                                               for _ in range(3)),
                    'produce3-patchmajor': lambda: da.produce_blocks_aosoa(
                        channel, channel, channel, start, stop, PATCHES,
                        width=width, order='patchmajor'),
                    'produce3-blocked': lambda: da.produce_blocks_aosoa(
                        channel, channel, channel, start, stop, PATCHES,
                        width=width, order='blocked'),
                }
                repeats = 200 if block_pixels == 128 else 40
                entry = {'block_pixels': block_pixels, 'width': width, 'mix': mix,
                         'start': start, 'stop': stop, 'gangs': gangs, 'arms': {}}
                for name, fn in arms.items():
                    entry['arms'][name] = {
                        **timed(fn, repeats),
                        'logical_bytes': LOGICAL_BYTES[name](rows, gangs, width, PATCHES)}
                report['blocks'].append(entry)

        for width in da.WIDTHS:
            def classes_then_pack():
                retained = _classes(altitude, azimuth, geometry, asvf, start, stop,
                                    active=active, prepared=prepared)
                return da.pack_masks_aosoa(*retained, width=width)

            arms = {
                'classes-retained': lambda: _classes(altitude, azimuth, geometry, asvf,
                                                     start, stop, active=active,
                                                     prepared=prepared),
                'classes+pack': classes_then_pack,
                'classify-aosoa': lambda: da.classify_block_aosoa(
                    altitude, azimuth, geometry, asvf, start, stop, active=active,
                    prepared=prepared, width=width),
            }
            repeats = 100 if block_pixels == 128 else 25
            rows, gangs = stop - start, -(-(stop - start) // width)
            entry = {'block_pixels': block_pixels, 'width': width, 'arms': {}}
            for name, fn in arms.items():
                entry['arms'][name] = {
                    **timed(fn, repeats),
                    'logical_bytes': LOGICAL_BYTES[name](rows, gangs, width, PATCHES)}
            report['classification'].append(entry)

    # Cross-checks so the timed numbers describe CORRECT artifacts.
    checks = []
    channel = build_channel('mix', seed_of('mix'))
    reference = decode_block(channel, 0, 128, PATCHES).view(np.uint32)
    for width in da.WIDTHS:
        for order in ('patchmajor', 'blocked'):
            produced = da.produce_block_aosoa(channel, 0, 128, PATCHES,
                                              width=width, order=order)
            rows = produced.transpose(0, 2, 1).reshape(-1, PATCHES)[:128]
            checks.append({'width': width, 'order': order,
                           'bitwise_equal_decode': bool(np.array_equal(rows, reference))})
        adapter = transpose_adapter(channel, 0, 128, width)
        rows = adapter.transpose(0, 2, 1).reshape(-1, PATCHES)[:128]
        checks.append({'width': width, 'order': 'adapter',
                       'bitwise_equal_decode': bool(np.array_equal(rows, reference))})
    masks_ref = _classes(altitude, azimuth, geometry, asvf, 0, 128, active=active,
                         prepared=prepared)
    masks_direct = da.classify_block_aosoa(altitude, azimuth, geometry, asvf, 0, 128,
                                           active=active, prepared=prepared)
    scattered = [mask.transpose(0, 2, 1).reshape(-1, PATCHES)[:128] for mask in masks_direct]
    checks.append({'width': 8, 'order': 'classify',
                   'bitwise_equal_classes': bool(
                       np.array_equal(scattered[0], masks_ref[0])
                       and np.array_equal(scattered[1], masks_ref[1]))})
    report['correctness_checks'] = checks

    target = HERE / 'results' / 'measure_direct_aosoa.json'
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(report, indent=1))
    print_table(report)
    print(f'\nwrote {target}')


def print_table(report):
    print('N8-11 direct AoSoA producer measurements (serial kernels, 1 thread)')
    print(f"provenance: {report['provenance']['git_head']} "
          f"({report['provenance']['branch']}), numpy {report['provenance']['numpy']}")
    print('descriptor first build (min s):', report['descriptor_first_build_s'])
    print('flat-copy first build, informational (min s):',
          report['flat_copy_build_s_informational'])
    for entry in report['blocks']:
        print(f"B={entry['block_pixels']:4d} W={entry['width']} {entry['mix']:<10s} "
              f"gangs={entry['gangs']}")
        for name, arm in entry['arms'].items():
            print(f"  {name:<22s} min {arm['min_s']*1e3:8.3f} ms  "
                  f"median {arm['median_s']*1e3:8.3f} ms  "
                  f"bytes {arm['logical_bytes']/1024:8.1f} KiB")
    for entry in report['classification']:
        print(f"classification B={entry['block_pixels']:4d} W={entry['width']}")
        for name, arm in entry['arms'].items():
            print(f"  {name:<22s} min {arm['min_s']*1e3:8.3f} ms  "
                  f"median {arm['median_s']*1e3:8.3f} ms  "
                  f"bytes {arm['logical_bytes']/1024:8.1f} KiB")
    print('correctness checks:', report['correctness_checks'])


if __name__ == '__main__':
    main()
