#!/usr/bin/env python
"""C6-21 L1 evidence runner: cylinder-longwave primary-output reduction.

Runs the full-vs-primary parity matrix on real patch geometry with
adversarial schedules and degenerate inputs, records per-case bitwise
results and contended-tier warm timings, and writes JSON.

Run:  PYTHONPATH=<worktree>/src:<worktree>/tests/optimization_v6/cylinder_lw \
      python run_L1.py <output_json>
"""
import hashlib
import json
import sys
import time

import numpy as np

from conftest import bitwise_equal, lcyl_arguments, lcyl_patches, lw_blocks, lw_coefficients, packed
from solweig_light.radiation import cylinder_longwave as cyl
from solweig_light.radiation import patch_radiation as compiled


def run_case(name, rows, cols, parallel, override, block_pixels=128):
    rng = np.random.default_rng(20260921)
    args = lcyl_arguments(rng, rows=rows, cols=cols, **override)
    full = compiled.Lcyl_v2022a(**args, block_pixels=block_pixels, parallel=parallel)
    primary = cyl.Lcyl_v2022a_primary(**args, block_pixels=block_pixels, parallel=parallel)
    ldown = bitwise_equal(full[0], primary[0])
    lside = bitwise_equal(full[1], primary[1])
    markers = all(marker is cyl.NOT_REQUESTED for marker in primary[2:])
    return dict(case=name, rows=rows, cols=cols, parallel=parallel,
                block_pixels=block_pixels, Ldown_bitwise=bool(ldown),
                Lside_bitwise=bool(lside), cardinals_not_requested=bool(markers))


def kernel_case(name, rows, cols, parallel):
    rng = np.random.default_rng(20260921)
    pixels, patches = rows*cols, 153
    sh, vs, vb = lw_blocks(rng, pixels, patches)
    coefficients = lw_coefficients(rng, patches, pixels)
    coefficients['sun'] = rng.random((pixels, patches)) < .5
    coefficients['shade'] = rng.random((pixels, patches)) < .5
    def run(kernel):
        return kernel(sh, vs, vb, coefficients['sun'], coefficients['shade'],
                      coefficients['solid'], coefficients['sine'], coefficients['cosine'],
                      coefficients['directions'], coefficients['gate'], coefficients['solar_gate'],
                      coefficients['sky_down'], coefficients['sky_side'],
                      coefficients['sun_surface'], coefficients['shade_surface'],
                      coefficients['lup'], coefficients['factor'])
    full_kernel = compiled._longwave if parallel else compiled._longwave_serial
    primary_kernel = cyl._longwave_primary if parallel else cyl._longwave_primary_serial
    full = run(full_kernel)
    primary = run(primary_kernel)
    columns = [bool(bitwise_equal(full[:, c], primary[:, c])) for c in range(7)]
    return dict(case=name, rows=rows, cols=cols, parallel=parallel,
                columns_0_6_bitwise=columns)


def fused_case(name, rows, cols, parallel):
    import os
    previous = os.environ.get('SOLWEIG_LIGHT_FUSED_RAD')
    os.environ['SOLWEIG_LIGHT_FUSED_RAD'] = '1'
    try:
        return _fused_case(name, rows, cols, parallel)
    finally:
        if previous is None:
            os.environ.pop('SOLWEIG_LIGHT_FUSED_RAD', None)
        else:
            os.environ['SOLWEIG_LIGHT_FUSED_RAD'] = previous


def _fused_case(name, rows, cols, parallel):
    rng = np.random.default_rng(20260921)
    pixels = rows*cols
    patches = 153
    sh = packed(rng, rows, cols, patches, ('binary', 'ternary', 'raw'))
    vs = packed(rng, rows, cols, patches, ('ternary', 'raw', 'binary'))
    vb = packed(rng, rows, cols, patches, ('raw', 'signed_zero', 'nonfinite'))
    coefficients = lw_coefficients(rng, patches, pixels)
    coefficients['sun'] = rng.random((pixels, patches)) < .5
    coefficients['shade'] = rng.random((pixels, patches)) < .5
    full = compiled._longwave_fused_block(
        sh, vs, vb, 0, pixels, patches, coefficients['sun'], coefficients['shade'],
        coefficients['solid'], coefficients['sine'], coefficients['cosine'],
        coefficients['directions'], coefficients['gate'], coefficients['solar_gate'],
        coefficients['sky_down'], coefficients['sky_side'], coefficients['sun_surface'],
        coefficients['shade_surface'], coefficients['lup'], coefficients['factor'], parallel)
    primary = cyl._longwave_fused_primary_block(
        sh, vs, vb, 0, pixels, patches, coefficients['sun'], coefficients['shade'],
        coefficients['solid'], coefficients['sine'], coefficients['cosine'],
        coefficients['directions'], coefficients['gate'], coefficients['solar_gate'],
        coefficients['sky_down'], coefficients['sky_side'], coefficients['sun_surface'],
        coefficients['shade_surface'], coefficients['lup'], coefficients['factor'], parallel)
    columns = [bool(bitwise_equal(full[:, c], primary[:, c])) for c in range(7)]
    return dict(case=name, rows=rows, cols=cols, parallel=parallel,
                columns_0_6_bitwise=columns)


def timing_kernel(rows, cols, parallel, repeats=5):
    """Contended development tier warm timing; no performance claim."""
    rng = np.random.default_rng(20260921)
    pixels, patches = rows*cols, 153
    sh, vs, vb = lw_blocks(rng, pixels, patches)
    coefficients = lw_coefficients(rng, patches, pixels)
    coefficients['sun'] = rng.random((pixels, patches)) < .5
    coefficients['shade'] = rng.random((pixels, patches)) < .5
    def run(kernel):
        return kernel(sh, vs, vb, coefficients['sun'], coefficients['shade'],
                      coefficients['solid'], coefficients['sine'], coefficients['cosine'],
                      coefficients['directions'], coefficients['gate'], coefficients['solar_gate'],
                      coefficients['sky_down'], coefficients['sky_side'],
                      coefficients['sun_surface'], coefficients['shade_surface'],
                      coefficients['lup'], coefficients['factor'])
    full_kernel = compiled._longwave if parallel else compiled._longwave_serial
    primary_kernel = cyl._longwave_primary if parallel else cyl._longwave_primary_serial
    run(full_kernel); run(primary_kernel)  # warm JIT
    samples = {}
    for label, kernel in (('full', full_kernel), ('primary', primary_kernel)):
        best = min(_one(run, kernel) for _ in range(repeats))
        samples[label] = best
    return dict(rows=rows, cols=cols, parallel=parallel, tier='contended_development',
                claim='none', full_warm_s=samples['full'], primary_warm_s=samples['primary'])


def _one(run, kernel):
    start = time.perf_counter()
    run(kernel)
    return time.perf_counter() - start


def main(out_path):
    results = {'wrapper': [], 'kernel': [], 'fused': [], 'timing': []}
    schedules = ((35., 180.), (0.5, 0.), (89., 359.), (-10., 200.), (10., 90.))
    degenerate = (
        ('zero_emissivity', dict(esky=np.array(0.0, dtype=np.float32))),
        ('ta_hot', dict(Ta=np.array(1e30, dtype=np.float32))),
        ('visibility_all_zero', dict(shmat=np.zeros((16, 16, 153), dtype=np.float32))),
    )
    for rows, cols in ((16, 16), (37, 53), (64, 64), (128, 128)):
        for parallel in (False, True):
            results['kernel'].append(kernel_case('lw_blocks_nonfinite', rows, cols, parallel))
    for index, (altitude, azimuth) in enumerate(schedules):
        for parallel in (False, True):
            results['wrapper'].append(run_case(
                f'schedule_{index}', 16, 16, parallel,
                dict(solar_altitude=np.array(altitude, dtype=np.float32),
                     solar_azimuth=np.array(azimuth, dtype=np.float32))))
    for name, override in degenerate:
        if override is None:
            continue
        for parallel in (False, True):
            results['wrapper'].append(run_case(name, 16, 16, parallel, override))
    for block_pixels in (1, 3, 128, 10**6):
        results['wrapper'].append(run_case('block_schedule', 16, 16, True, {}, block_pixels))
    rng = np.random.default_rng(20260921)
    spiked = rng.random(16*16).astype(np.float32)
    spiked[1::11] = np.float32('nan'); spiked[2::11] = np.float32('inf')
    spiked[3::11] = np.float32('-inf'); spiked[5::11] = np.float32(-0.0)
    for parallel in (False, True):
        results['wrapper'].append(run_case('lup_nonfinite', 16, 16, parallel, dict(Lup=spiked.reshape(16, 16))))
    for parallel in (False, True):
        results['fused'].append(fused_case('packed_adversarial', 16, 16, parallel))
    for rows, cols in ((64, 64), (128, 128)):
        for parallel in (False, True):
            results['timing'].append(timing_kernel(rows, cols, parallel))

    results['all_passed'] = all(
        case.get('Ldown_bitwise', True) and case.get('Lside_bitwise', True)
        and case.get('cardinals_not_requested', True) and all(case.get('columns_0_6_bitwise', [True]))
        for group in ('wrapper', 'kernel', 'fused') for case in results[group])
    module = 'src/solweig_light/radiation/cylinder_longwave.py'
    results['module_sha256'] = hashlib.sha256(open(module, 'rb').read()).hexdigest()
    with open(out_path, 'w') as handle:
        json.dump(results, handle, indent=2)
    print(json.dumps({'all_passed': results['all_passed'],
                      'cases': sum(len(results[k]) for k in ('wrapper', 'kernel', 'fused'))}))
    return 0 if results['all_passed'] else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else 'parity_results.json'))
