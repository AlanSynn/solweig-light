"""Small NumPy semantic probes, NOT a SOLWEIG or performance benchmark.

The wall-index expression and promotion helpers are transcribed from main
90d72b50e6396bb0182db41598c9bd535dd9c487. The radiation example is one
multiply chain, not the full longwave model. No project imports, Torch,
GDAL, native backend, or target-M4 execution is involved.
"""
from pathlib import Path
import json, platform, sys
import numpy as np


def operands(a, b):
    aa, bb = np.asarray(a), np.asarray(b)
    if aa.dtype.kind == 'f' and aa.ndim > 0 and (bb.ndim == 0 or bb.dtype.kind in 'biu'):
        b = np.asarray(b, dtype=aa.dtype)
    elif bb.dtype.kind == 'f' and bb.ndim > 0 and (aa.ndim == 0 or aa.dtype.kind in 'biu'):
        a = np.asarray(a, dtype=bb.dtype)
    return a, b


def operate(op, a, b):
    a, b = operands(a, b)
    return op(a, b)


def contribution(surface, sun, solid, cosine, building):
    value = operate(np.multiply, surface, sun)
    value = operate(np.multiply, value, solid)
    value = operate(np.multiply, value, cosine)
    return operate(np.multiply, value, building)


def run():
    table = np.asarray([
        [2, .18, .95, .58, -9.78, 15.],
        [1, .18, .95, .58, -9.78, 15.],
        [0, .20, .95, .37, -3.41, 15.],
        [7, .05, .98, .00, .00, 12.],
        [5, .16, .94, .21, -3.38, 14.],
        [6, .25, .94, .33, -3.01, 14.],
        [99, .20, .90, .58, -3.41, 15.],
    ], dtype=np.float64)
    wall_pos = np.where(table[:, 0] == 99)
    wall_fields = {name: np.asarray(table[wall_pos, col], dtype=np.float32)
                   for name, col in [('TgK_wall', 3), ('Tstart_wall', 4), ('TmaxLST_wall', 5)]}
    assert all(x.shape == (1, 1) and x.size == 1 for x in wall_fields.values())
    shape_results = {k: {'shape': list(v.shape), 'dtype': str(v.dtype),
                          'values': v.tolist()} for k, v in wall_fields.items()}

    air = np.float64(25.123456789)
    wall = np.array([[12.345678]], dtype=np.float32)
    array_result = operate(np.add, air, wall)
    scalar_result = operate(np.add, air, wall[0, 0])
    assert array_result.dtype == np.float32 and scalar_result.dtype == np.float64
    promotion = {'singleton_array_result': float(array_result[0, 0]),
                 'singleton_array_dtype': str(array_result.dtype),
                 'scalar_result': float(scalar_result),
                 'scalar_dtype': str(scalar_result.dtype)}

    # Preserve the original expression at every intermediate. Lookup values
    # retain the contribution dtype. Each independent accumulator still sees
    # all patches in original order and rounds to float32 after each add.
    rng = np.random.default_rng(20261013)
    shape, patches = (8, 9), 153
    profiles = {
        'surface_singleton_f32': np.array([[123.45678]], dtype=np.float32),
        'surface_singleton_f64': np.array([[123.4567890123]], dtype=np.float64),
        'surface_scalar_f32': np.float32(123.45678),
        'surface_scalar_f64': np.float64(123.4567890123),
    }
    results = []
    total_values = 0
    for name, surface in profiles.items():
        reference = np.zeros(shape, dtype=np.float32)
        candidate = np.zeros(shape, dtype=np.float32)
        dtypes = set()
        for patch in range(patches):
            sun = rng.random(shape) > .5
            building = rng.random(shape) > .5
            solid = np.float32(rng.uniform(.0001, .2))
            cosine = np.float32(rng.uniform(-1, 1))
            if patch % 29 == 0:
                cosine = np.float32(-0.)
            c = contribution(surface, sun, solid, cosine, building)
            lut = np.empty((2, 2), dtype=c.dtype)
            for s in range(2):
                for b in range(2):
                    lut[s, b] = contribution(surface,
                        np.array([[bool(s)]], dtype=np.bool_), solid, cosine,
                        np.array([[bool(b)]], dtype=np.bool_))[0, 0]
            observed = lut[sun.astype(np.intp), building.astype(np.intp)]
            assert observed.dtype == c.dtype
            uint = np.uint32 if c.dtype == np.float32 else np.uint64
            assert np.array_equal(c.view(uint), observed.view(uint))
            reference += c
            candidate += observed
            assert np.array_equal(reference.view(np.uint32), candidate.view(np.uint32))
            total_values += c.size
            dtypes.add(str(c.dtype))
        results.append({'profile': name, 'patches': patches,
                        'pixels': reference.size,
                        'contribution_dtypes': sorted(dtypes),
                        'each_contribution_bits_equal': True,
                        'all_ordered_prefix_accumulator_bits_equal': True})
    return {'evidence_class': 'standalone_semantic_probe_not_project_validation',
            'source_reference': '90d72b50e6396bb0182db41598c9bd535dd9c487',
            'environment': {'python': sys.version, 'numpy': np.__version__,
                            'platform': platform.platform()},
            'wall_indexing': shape_results,
            'premature_scalarization_changes_promotion': promotion,
            'finite_contribution_values_checked': total_values,
            'profiles': results,
            'performance_measured': False,
            'full_model_executed': False,
            'limits': ['finite multiply-chain probe only; no transcendental parity',
                       'not the target M4 environment or project-pinned NumPy',
                       'no installed-wheel, TIFF, chronology or full radiation check',
                       'runtime warnings, exception order and all nonfinite cases not covered']}


if __name__ == '__main__':
    output = run()
    path = Path(__file__).with_name('results.json')
    path.write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps(output, indent=2))
