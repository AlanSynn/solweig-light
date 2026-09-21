"""DIAGNOSTIC probe: radiation stage cost at pipeline shape (256x256, block 128).

Not a benchmark claim. Final arbiter is the integrator's portfolio protocol.
Run: uv run --extra test python tests/optimization_v5/radiation/probe_pipeline_shape.py
"""
import os
import time

import numba
import numpy as np

os.environ.setdefault('SOLWEIG_LIGHT_FUSED_RAD', '1')

from conftest import (lw_coefficients, packed, sw_coefficients, threads)  # noqa: E402
from solweig_light.geometry.visibility import LazyDiffVisibility  # noqa: E402
from solweig_light.radiation import patch_radiation as compiled  # noqa: E402

ROWS = COLS = 256
PATCHES = 153
PIXELS = ROWS*COLS
BLOCK = 128


def scene(seed, lazy_diff):
    rng = np.random.default_rng(seed)
    sh = packed(rng, ROWS, COLS, PATCHES, ('binary', 'ternary', 'raw'))
    vs = packed(rng, ROWS, COLS, PATCHES, ('binary', 'ternary', 'raw'))
    vb = packed(rng, ROWS, COLS, PATCHES, ('binary', 'ternary', 'raw'))
    diffuse = LazyDiffVisibility(sh, vs) if lazy_diff else packed(
        rng, ROWS, COLS, PATCHES, ('binary',))
    return rng, sh, vs, vb, diffuse


def sw_blocks(rng, sh, vs, vb, diffuse):
    coefficients = sw_coefficients(rng, PATCHES)
    sun = rng.integers(0, 2, (PIXELS, PATCHES)).astype(np.bool_)
    shade = rng.integers(0, 2, (PIXELS, PATCHES)).astype(np.bool_)
    return coefficients, sun, shade


def measure(function, repeats=3):
    function()
    samples = []
    for _ in range(repeats):
        begin = time.perf_counter()
        function()
        samples.append(time.perf_counter()-begin)
    return min(samples)


def old_sw(sh, vs, vb, diffuse, coefficients, sun, shade):
    for start in range(0, PIXELS, BLOCK):
        stop = min(start+BLOCK, PIXELS)
        decoded = compiled._shortwave_visibility_blocks(sh, vs, vb, diffuse, start, stop, PATCHES)
        compiled._shortwave(*decoded, sun[start:stop], shade[start:stop],
                            coefficients['lum'], coefficients['solid'], coefficients['cosine'],
                            coefficients['directions'], coefficients['diff_gate'],
                            coefficients['ref_gate'], coefficients['box_gate'],
                            coefficients['surface_sun'], coefficients['surface_sh'], False)


def fused_sw(sh, vs, vb, diffuse, coefficients, sun, shade):
    for start in range(0, PIXELS, BLOCK):
        stop = min(start+BLOCK, PIXELS)
        compiled._shortwave_fused_block(
            sh, vs, vb, diffuse, start, stop, PATCHES, sun[start:stop], shade[start:stop],
            coefficients['lum'], coefficients['solid'], coefficients['cosine'],
            coefficients['directions'], coefficients['diff_gate'], coefficients['ref_gate'],
            coefficients['box_gate'], coefficients['surface_sun'], coefficients['surface_sh'],
            False, True)


def old_lw(sh, vs, vb, lw, sun, shade):
    for start in range(0, PIXELS, BLOCK):
        stop = min(start+BLOCK, PIXELS)
        decoded = [compiled._block(channel, start, stop, PATCHES)
                   for channel in (sh, vs, vb)]
        compiled._longwave(*decoded, sun[start:stop], shade[start:stop], lw['solid'],
                           lw['sine'], lw['cosine'], lw['directions'], lw['gate'],
                           lw['solar_gate'], lw['sky_down'], lw['sky_side'], lw['sun_surface'],
                           lw['shade_surface'], lw['lup'][start:stop], lw['factor'])


def fused_lw(sh, vs, vb, lw, sun, shade):
    for start in range(0, PIXELS, BLOCK):
        stop = min(start+BLOCK, PIXELS)
        compiled._longwave_fused_block(
            sh, vs, vb, start, stop, PATCHES, sun[start:stop], shade[start:stop], lw['solid'],
            lw['sine'], lw['cosine'], lw['directions'], lw['gate'], lw['solar_gate'],
            lw['sky_down'], lw['sky_side'], lw['sun_surface'], lw['shade_surface'],
            lw['lup'][start:stop], lw['factor'], True)


if __name__ == '__main__':
    for lazy in (False, True):
        with threads(4):
            rng, sh, vs, vb, diffuse = scene(11, lazy)
            coefficients, sun, shade = sw_blocks(rng, sh, vs, vb, diffuse)
            lw = lw_coefficients(rng, PATCHES, PIXELS)
            kind = 'lazy-diff' if lazy else 'direct-diff'
            print(f'--- SW {kind}, threads={numba.get_num_threads()}, '
                  f'scene {ROWS}x{COLS}, block {BLOCK} ---')
            old = measure(lambda: old_sw(sh, vs, vb, diffuse, coefficients, sun, shade))
            fused = measure(lambda: fused_sw(sh, vs, vb, diffuse, coefficients, sun, shade))
            print(f'SW old   {old*1e3:9.1f} ms/scene')
            print(f'SW fused {fused*1e3:9.1f} ms/scene  ratio {fused/old:.3f}')
            if lazy:
                diffuse_direct = packed(
                    np.random.default_rng(13), ROWS, COLS, PATCHES, ('binary',))
                old = measure(lambda: old_lw(sh, vs, vb, lw, sun, shade))
                fused = measure(lambda: fused_lw(sh, vs, vb, lw, sun, shade))
                print(f'LW old   {old*1e3:9.1f} ms/scene')
                print(f'LW fused {fused*1e3:9.1f} ms/scene  ratio {fused/old:.3f}')
                del diffuse_direct
