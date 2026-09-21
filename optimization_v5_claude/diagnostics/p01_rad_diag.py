"""DIAGNOSTIC ONLY (not a benchmark claim): fused vs retained decode+reduce cost.

Synthetic 128x128 x 153-patch packed channel, threads capped at 2.
Measures, over one full production-shaped block loop (block_pixels=128):
  decode-only  - the retained decode_block materializing route (4 channels)
  old route    - decode_block + original _shortwave kernel
  fused route  - _shortwave_fused_block (ordered decode+accumulate, no decoded block)
"""
import time

import numba
import numpy as np

from solweig_light.geometry.visibility import LazyDiffVisibility, PackedVisibility
from solweig_light.geometry.visibility_compiled import decode_block
from solweig_light.radiation import patch_radiation as pr

numba.set_num_threads(2)
rng = np.random.default_rng(3)
rows = cols = 128
patches = 153
pixels = rows*cols
block_pixels = 128


def channel(kind):
    planes = []
    for patch in range(patches):
        if kind == 0:
            plane = rng.integers(0, 2, pixels).astype(np.float32)
        elif kind == 1:
            plane = rng.integers(0, 3, pixels).astype(np.float32)
        else:
            bits = rng.integers(0, 2**32, pixels, dtype=np.uint64).astype(np.uint32)
            bits[0] = 0x40600000
            plane = bits.view(np.float32)
        planes.append(plane.reshape(rows, cols))
    return PackedVisibility.from_dense(np.stack(planes, axis=2))


sh, vs, vb = channel(0), channel(1), channel(2)
diff = LazyDiffVisibility(sh, vs)
lum = rng.random(patches).astype(np.float32)
solid = rng.random(patches).astype(np.float32)+.01
cosine = rng.random(patches).astype(np.float32)
directions = rng.random((patches, 4)).astype(np.float32)
diff_gate = rng.random((patches, 4)) < .5
ref_gate = rng.random((patches, 4)) < .5
box_gate = rng.random(patches) < .5
sun = rng.integers(0, 2, (pixels, patches)).astype(np.bool_)
shade = rng.integers(0, 2, (pixels, patches)).astype(np.bool_)


def blocks():
    return ((start, min(start+block_pixels, pixels))
            for start in range(0, pixels, block_pixels))


def decode_only():
    for start, stop in blocks():
        decode_block(sh, start, stop, patches)
        decode_block(vs, start, stop, patches)
        decode_block(vb, start, stop, patches)
        decode_block(diff, start, stop, patches)


def old_route():
    for start, stop in blocks():
        decoded = pr._shortwave_visibility_blocks(sh, vs, vb, diff, start, stop, patches)
        pr._shortwave(*decoded, sun[start:stop], shade[start:stop], lum, solid, cosine,
                      directions, diff_gate, ref_gate, box_gate, np.float32(.37),
                      np.float32(.11), False)


def fused_route():
    for start, stop in blocks():
        pr._shortwave_fused_block(sh, vs, vb, diff, start, stop, patches,
                                  sun[start:stop], shade[start:stop], lum, solid, cosine,
                                  directions, diff_gate, ref_gate, box_gate, np.float32(.37),
                                  np.float32(.11), False, True)


def measure(function, repeats=3):
    function()  # warm JIT and caches
    samples = []
    for _ in range(repeats):
        begin = time.perf_counter()
        function()
        samples.append(time.perf_counter()-begin)
    return min(samples)


if __name__ == '__main__':
    decode = measure(decode_only)
    old = measure(old_route)
    fused = measure(fused_route)
    print(f'threads={numba.get_num_threads()} pixels={pixels} patches={patches} '
          f'block_pixels={block_pixels}')
    print(f'decode-only (4 channels): {decode*1e3:8.1f} ms/scene')
    print(f'old route (decode+reduce): {old*1e3:8.1f} ms/scene')
    print(f'fused route              : {fused*1e3:8.1f} ms/scene')
    print(f'fused/old ratio          : {fused/old:8.3f}')
