"""B7-03: island share versus pixel count - kernel vs full wrapper island.

Single-process dev-tier probe; each timing is the median of 3 calls after one
warmup. bare-kernel = _longwave_primary on a prepared block; island =
Lcyl_v2022a_primary end-to-end for the same domain (guards, classification,
packing, blocks, kernel). Establishes whether the nominated island grows or
shrinks with tile size, and gives the A baseline kernel throughput curve.
"""
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'src'))

import numpy as np  # noqa: E402

PATCHES = 153
SIZES = (4096, 16384, 65536)  # 64^2, 128^2, 256^2
REPEATS = 3


def time_call(call, repeats=REPEATS):
    call()  # warmup
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        call()
        samples.append(time.perf_counter() - start)
    return samples


def main():
    conftest_path = REPO / 'tests/optimization_v6/cylinder_lw/conftest.py'
    import importlib.util
    import types
    if 'pytest' not in sys.modules:
        try:
            import pytest  # noqa: F401
        except ImportError:
            stub = types.ModuleType('pytest')

            def _fixture(function=None, **_):
                return function if function is not None else (lambda inner: inner)
            stub.fixture = _fixture
            sys.modules['pytest'] = stub
    spec = importlib.util.spec_from_file_location('_v7_conftest', str(conftest_path))
    conftest = importlib.util.module_from_spec(spec)
    sys.modules['_v7_conftest'] = conftest
    spec.loader.exec_module(conftest)

    from solweig_light.radiation import cylinder_longwave as cyl
    from solweig_light.radiation import patch_radiation as compiled

    results = []
    for pixels in SIZES:
        side = int(pixels ** 0.5)
        rng = np.random.default_rng(20260922 + pixels)
        args = conftest.lcyl_arguments(rng, rows=side, cols=side)
        coefficients_sun = rng.random((pixels, PATCHES)) < .5
        coefficients_shade = rng.random((pixels, PATCHES)) < .5
        # Materialize blocks once; adapter/packing cost is a separate trial
        # boundary in the frozen A/B/C protocol, not part of bare-kernel time.
        sh, vs, vb = (compiled._block(args[name], 0, pixels, PATCHES)
                      for name in ('shmat', 'vegshmat', 'vbshvegshmat'))
        table = args['sky_patches']
        geometry = compiled.patch_geometry(table)
        from solweig_light.radiation import engine as e
        sbc = e._array(5.67051e-8)
        ewall = e._array(args['ewall'])
        sun_surface = e._divide(e._operate(np.multiply, e._operate(np.multiply, ewall, sbc),
                                           e._operate(np.power, e._operate(np.add, e._operate(
                                               np.add, args['Ta'], args['Tgwall']), 273.15), 4)),
                                e._array(np.pi))[()]
        shade_surface = e._divide(e._operate(np.multiply, e._operate(np.multiply, ewall, sbc),
                                             e._operate(np.power, e._operate(np.add, args['Ta'], 273.15), 4)),
                                  e._array(np.pi))[()]
        difference = np.asarray([np.abs(e._operate(np.subtract, args['solar_azimuth'], value))
                                 for value in geometry.azimuth])
        solar_gate = (difference > 90) & (difference < 270) & (args['solar_altitude'] > 0)
        factor = e._operate(np.subtract, 1, ewall)[()]
        lup_flat = args['Lup'].reshape(-1)

        def call_kernel():
            cyl._longwave_primary(sh, vs, vb, coefficients_sun, coefficients_shade,
                                  geometry.solid_angle, geometry.sine, geometry.cosine,
                                  geometry.longwave_cardinal_cosine, geometry.reflection_cardinal,
                                  solar_gate, table[:, 2], table[:, 2], sun_surface,
                                  shade_surface, lup_flat, factor)

        def call_wrapper():
            cyl.Lcyl_v2022a_primary(**args)

        kernel_samples = time_call(call_kernel)
        wrapper_samples = time_call(call_wrapper)
        results.append({
            'pixels': pixels,
            'side': side,
            'kernel_s': kernel_samples,
            'wrapper_s': wrapper_samples,
            'kernel_share_of_island_median': sorted(kernel_samples)[REPEATS // 2]
            / sorted(wrapper_samples)[REPEATS // 2],
        })
        print(json.dumps(results[-1]))

    report = {
        'schema': 'solweig-v7-island-scale-v1',
        'task': 'B7-03',
        'measurement_class': 'dev_tier_scale_probe',
        'patches': PATCHES,
        'repeats': REPEATS,
        'results': results,
    }
    out = REPO / 'optimization_v7_backends/evidence/captures/b7_03_island_scale.json'
    out.write_text(json.dumps(report, indent=1))
    print('written', out)


if __name__ == '__main__':
    main()
