"""DIAGNOSTIC probe: full Kside wrapper time, fused vs retained, by channel backing.

Not a benchmark claim. Final arbiter is the integrator's portfolio protocol.
Compares packed in-RAM channels against MappedVisibility (the warm
GeometryStore path) with the pipeline's LazyDiff diffuse pairing, toggling
only SOLWEIG_LIGHT_FUSED_RAD between arms.
Run: uv run --extra test python tests/optimization_v5/radiation/probe_stage_context.py
"""
import os
import shutil
import time

import numba
import numpy as np

from conftest import kside_arguments
from solweig_light.geometry.visibility import LazyDiffVisibility, PackedVisibility
from solweig_light.geometry.visibility_native import (open_native_visibility,
                                                      save_native_visibility)
from solweig_light.radiation import patch_radiation as compiled

ROWS = COLS = 256
PATCHES = 153
BLOCK = 128
ENV = 'SOLWEIG_LIGHT_FUSED_RAD'


def packed_scene(seed):
    rng = np.random.default_rng(seed)
    values = kside_arguments(rng, ROWS, COLS, PATCHES, False)
    values['diffsh'] = (values['shmat']
                        - (np.float32(1) - values['vegshmat'])*np.float32(1-.03))
    packed_values = dict(values)
    for key in ('shmat', 'vegshmat', 'vbshvegshmat', 'diffsh'):
        packed_values[key] = PackedVisibility.from_dense(values[key])
    packed_values['diffsh'] = LazyDiffVisibility(packed_values['shmat'],
                                                 packed_values['vegshmat'])
    return packed_values


def mapped_scene(packed_values, root):
    paths = {}
    for key in ('shmat', 'vegshmat', 'vbshvegshmat'):
        path = os.path.join(root, key + '.vis')
        save_native_visibility(path, packed_values[key])
        paths[key] = path
    mapped = dict(packed_values)
    for key, path in paths.items():
        mapped[key] = open_native_visibility(path)
    mapped['diffsh'] = LazyDiffVisibility(mapped['shmat'], mapped['vegshmat'])
    return mapped, paths


def arm(values, enabled, repeats=3):
    if enabled:
        os.environ[ENV] = '1'
    else:
        os.environ.pop(ENV, None)
    def run():
        compiled.Kside_veg_v2022a(**values, block_pixels=BLOCK, parallel=True)
    run()
    samples = []
    for _ in range(repeats):
        begin = time.perf_counter()
        run()
        samples.append(time.perf_counter()-begin)
    return min(samples)


def report(label, values):
    disabled = arm(values, False)
    enabled = arm(values, True)
    print(f'{label:34s} old {disabled*1e3:8.1f} ms/scene   '
          f'fused {enabled*1e3:8.1f} ms/scene   ratio {enabled/disabled:.3f}')


if __name__ == '__main__':
    numba.set_num_threads(4)
    root = '/tmp/p01-stage-probe'
    shutil.rmtree(root, ignore_errors=True)
    os.makedirs(root)
    try:
        packed_values = packed_scene(11)
        report('packed + lazy diffuse', packed_values)
        mapped_values, paths = mapped_scene(packed_values, root)
        report('mapped + lazy diffuse', mapped_values)
        for channel in mapped_values.values():
            if hasattr(channel, 'close'):
                channel.close()
        del mapped_values
        # Fresh mmap per rep: the warm-store per-tile-open pattern.
        fresh_values = dict(packed_values)
        for key in ('shmat', 'vegshmat', 'vbshvegshmat'):
            fresh_values[key] = open_native_visibility(paths[key])
        fresh_values['diffsh'] = LazyDiffVisibility(fresh_values['shmat'],
                                                    fresh_values['vegshmat'])
        disabled = arm(fresh_values, False)
        enabled = arm(fresh_values, True)
        print(f'{"mapped fresh-open + lazy diffuse":34s} old {disabled*1e3:8.1f} ms/scene   '
              f'fused {enabled*1e3:8.1f} ms/scene   ratio {enabled/disabled:.3f}')
        for channel in fresh_values.values():
            if hasattr(channel, 'close'):
                channel.close()
    finally:
        shutil.rmtree(root, ignore_errors=True)
