"""B7-03: measure the actual longwave-primary island fraction on the real path.

Times the untouched pipeline on the 35x32 reference scene with transparent
delegation wrappers accumulating inclusive kernel time and inclusive
Lcyl-by-demand wrapper time. Dev-tier measurement on a possibly busy host:
used to size the island, not as an A/B/C benchmark.
"""
import json
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'src'))

import numpy as np  # noqa: E402

REPEATS = 3


def measure(config_name, overrides):
    from solweig_light.pipeline import files_by_key, run_tile
    from solweig_light.radiation import cylinder_longwave as cyl
    from solweig_light.runtime import runtime_options

    stats = {'kernel_calls': 0, 'kernel_time': 0.0, 'wrapper_calls': 0, 'wrapper_time': 0.0}

    original_parallel = cyl._longwave_primary
    original_serial = cyl._longwave_primary_serial

    def timed(original):
        def kernel(*args):
            start = time.perf_counter()
            result = original(*args)
            stats['kernel_time'] += time.perf_counter() - start
            stats['kernel_calls'] += 1
            return result
        return kernel

    cyl._longwave_primary = timed(original_parallel)
    cyl._longwave_primary_serial = timed(original_serial)

    # engine.py imports Lcyl_v2022a_by_demand inside the call body, so the
    # attribute is resolved from cylinder_longwave at call time.
    original_by_demand = cyl.Lcyl_v2022a_by_demand

    def timed_by_demand(*args, **kwargs):
        start = time.perf_counter()
        result = original_by_demand(*args, **kwargs)
        stats['wrapper_time'] += time.perf_counter() - start
        stats['wrapper_calls'] += 1
        return result

    cyl.Lcyl_v2022a_by_demand = timed_by_demand

    prepared = REPO / 'tests/reference/small_original_cpu/scene/processed_inputs'
    flags = {f'save_{name}': True for name in
             ('tmrt', 'kup', 'kdown', 'lup', 'ldown', 'shadow', 'wbgt', 'ta', 'wind')}
    paths = {name: files_by_key(prepared / name)['0_0'] for name in
             ('Building_DSM', 'Trees', 'DEM', 'walls', 'aspect', 'metfiles')}

    trials = []
    try:
        for repeat in range(REPEATS):
            with tempfile.TemporaryDirectory(prefix='v7_profile_') as scratch:
                start = time.perf_counter()
                with runtime_options(overrides):
                    run_tile(Path(scratch), prepared, '2020-07-18', '0_0', paths, flags)
                wall = time.perf_counter() - start
            trials.append(wall)
            stats[f'repeat_{repeat}_wall'] = wall
    finally:
        cyl._longwave_primary = original_parallel
        cyl._longwave_primary_serial = original_serial
        cyl.Lcyl_v2022a_by_demand = original_by_demand

    median = sorted(trials)[len(trials) // 2]
    return {
        'config': config_name,
        'overrides': overrides,
        'trials_wall_s': trials,
        'median_wall_s': median,
        'kernel_calls_per_run': stats['kernel_calls'] // REPEATS,
        'kernel_time_per_run_s': stats['kernel_time'] / REPEATS,
        'wrapper_calls_per_run': stats['wrapper_calls'] // REPEATS,
        'wrapper_time_per_run_s': stats['wrapper_time'] / REPEATS,
        'kernel_fraction_of_wall': stats['kernel_time'] / REPEATS / median,
        'wrapper_fraction_of_wall': stats['wrapper_time'] / REPEATS / median,
    }


def main():
    results = [
        measure('serial_default', {}),
        measure('parallel_tpw4_cpu4', {'threads_per_worker': 4, 'cpu_budget': 4}),
    ]
    report = {
        'schema': 'solweig-v7-island-profile-v1',
        'task': 'B7-03',
        'measurement_class': 'dev_tier_residual_profile',
        'scene': 'tests/reference/small_original_cpu/scene (35x32, 24 records)',
        'repeats': REPEATS,
        'results': results,
    }
    out = REPO / 'optimization_v7_backends/evidence/captures/b7_03_island_fraction.json'
    out.write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
