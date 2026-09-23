"""B7-02: capture untouched ``_longwave_primary`` arguments/outputs from real execution.

Runs the accepted baseline in the project environment without replacing any
numerical behavior: recording wrappers delegate to the original Numba
dispatchers, and all capture work happens outside any timed interval.

Phases:
  real_pipeline   - full ``run_tile`` chronology on the untouched small
                    upstream-CPU reference scene (35x32, 24 records), the
                    genuine TIFF path through PIPELINE_CYLINDERS_ANISOTROPIC.
  synthetic_edge  - wrapper/kernel-level edge domains: P=1, B=0, nonfinite
                    payloads, float64/Python scalar specializations.

Outputs (owned by B7-02):
  optimization_v7_backends/evidence/captures/b7_02_capture_manifest.json
  optimization_v7_backends/evidence/captures/b7_02_fixtures.npz
  optimization_v7_backends/evidence/captures/b7_02_typed_ir.txt
"""
import hashlib
import json
import os
import platform
import struct
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'src'))

import numpy as np  # noqa: E402

CAPTURE_DIR = REPO / 'optimization_v7_backends/evidence/captures'
ENV_FLAGS = ('SOLWEIG_LIGHT_FUSED_RAD', 'SOLWEIG_LIGHT_PATCH_CLASS_TABLES')

_kernel_labels = ('parallel', 'serial')


def _sha256_bytes(payload):
    return hashlib.sha256(payload).hexdigest()


def describe_array(a):
    view = np.asarray(a)
    return {
        'kind': 'ndarray',
        'shape': list(view.shape),
        'strides': list(view.strides),
        'dtype': str(view.dtype),
        'c_contiguous': bool(view.flags.c_contiguous),
        'f_contiguous': bool(view.flags.f_contiguous),
        'writeable': bool(view.flags.writeable),
        'byte_hash': _sha256_bytes(np.ascontiguousarray(view).tobytes()),
        'itemsize': int(view.itemsize),
    }


def describe_scalar(v):
    if isinstance(v, np.generic):
        payload = np.asarray(v).tobytes()
        return {
            'kind': 'numpy_scalar',
            'python_type': type(v).__name__,
            'dtype': str(v.dtype),
            'hex': payload.hex(),
            'byte_hash': _sha256_bytes(payload),
        }
    if isinstance(v, float):
        f64 = struct.pack('>d', v)
        f32 = struct.pack('>f', np.float32(v))
        return {
            'kind': 'python_float',
            'python_type': 'float',
            'float64_hex_be': f64.hex(),
            'as_float32_hex_be': f32.hex(),
            'byte_hash': _sha256_bytes(f64),
        }
    if isinstance(v, (bool, np.bool_)):
        return {'kind': 'python_bool', 'value': bool(v)}
    if isinstance(v, int):
        return {'kind': 'python_int', 'value': int(v)}
    return {'kind': 'other', 'python_type': type(v).__name__, 'repr': repr(v)}


def describe_value(v):
    if isinstance(v, np.ndarray):
        return describe_array(v)
    return describe_scalar(v)


def install_capture():
    """Wrap the two primary dispatchers; delegation keeps execution untouched."""
    from solweig_light.radiation import cylinder_longwave as cyl

    originals = {'parallel': cyl._longwave_primary, 'serial': cyl._longwave_primary_serial}
    records = []

    def make(label, original):
        def kernel(*args):
            record = {
                'label': label,
                'call_index': len(records),
                'first_use': len(records) == 0,
                'args': [describe_value(a) for a in args],
                'kept': False,
            }
            output = original(*args)
            record['output'] = describe_value(output)
            record['arrays'] = (args, output)
            records.append(record)
            return output
        return kernel

    cyl._longwave_primary = make('parallel', originals['parallel'])
    cyl._longwave_primary_serial = make('serial', originals['serial'])
    return cyl, originals, records


def run_real_pipeline(records, cyl):
    """Drive the untouched pipeline in its two accepted runtime configurations.

    Default options (threads_per_worker=1) reach the serial kernel; a
    threads_per_worker=4 scope reaches the parallel kernel. Both are real
    TIFF-path executions under PIPELINE_CYLINDERS_ANISOTROPIC demand.
    """
    from solweig_light.pipeline import files_by_key, run_tile
    from solweig_light.runtime import runtime_options

    prepared = REPO / 'tests/reference/small_original_cpu/scene/processed_inputs'
    flags = {f'save_{name}': True for name in
             ('tmrt', 'kup', 'kdown', 'lup', 'ldown', 'shadow', 'wbgt', 'ta', 'wind')}
    paths = {name: files_by_key(prepared / name)['0_0'] for name in
             ('Building_DSM', 'Trees', 'DEM', 'walls', 'aspect', 'metfiles')}
    with tempfile.TemporaryDirectory(prefix='v7_capture_') as scratch:
        for label, overrides in (('pipeline_serial_default', {}),
                                 ('pipeline_parallel_tpw4',
                                  {'threads_per_worker': 4, 'cpu_budget': 4})):
            mark = len(records)
            with runtime_options(overrides):
                run_tile(Path(scratch) / label, prepared, '2020-07-18', '0_0', paths, flags)
            for record in records[mark:]:
                record['case'] = label
    return 'real_pipeline'


def synthetic_edges(records, cyl):
    """Wrapper/kernel edge domains beyond the real pipeline shapes."""
    conftest_path = REPO / 'tests/optimization_v6/cylinder_lw/conftest.py'
    import importlib.util
    import types

    # The v6 conftest imports pytest only for its fixture decorators; the
    # argument builders are pure NumPy. A stub keeps this capture inside the
    # untouched baseline environment (pytest is not installed there).
    if 'pytest' not in sys.modules:
        try:
            import pytest  # noqa: F401
        except ImportError:
            stub = types.ModuleType('pytest')

            def _fixture(function=None, **_kwargs):
                return function if function is not None else (lambda inner: inner)

            stub.fixture = _fixture
            sys.modules['pytest'] = stub

    spec = importlib.util.spec_from_file_location('_v7_conftest', str(conftest_path))
    conftest = importlib.util.module_from_spec(spec)
    sys.modules['_v7_conftest'] = conftest
    spec.loader.exec_module(conftest)

    rng = np.random.default_rng(20260922)
    cases = []
    # P=1 single-patch domain.
    single = np.array([[45.0, 180.0, 0.0]], dtype=np.float32)
    cases.append(('P1_default', conftest.lcyl_arguments(rng, rows=16, cols=16, sky_patches=single)))
    # Adversarial payloads at the default 153-patch table.
    cases.append(('adversarial_16', conftest.lcyl_arguments(rng, rows=16, cols=16)))
    cases.append(('adversarial_64', conftest.lcyl_arguments(rng, rows=64, cols=64)))
    # Degenerate visibilities and nonfinite payloads.
    cases.append(('vis_all_zero', conftest.lcyl_arguments(
        rng, rows=16, cols=16, shmat=np.zeros((16, 16, 153), dtype=np.float32))))
    cases.append(('vis_all_two', conftest.lcyl_arguments(
        rng, rows=16, cols=16, shmat=np.full((16, 16, 153), 2.0, dtype=np.float32))))
    cases.append(('lup_nonfinite', conftest.lcyl_arguments(
        rng, rows=16, cols=16,
        Lup=(lambda v: _spiked(v, 16 * 16, (16, 16)))(rng.random(16 * 16)))))
    # Empty domain.
    cases.append(('B0_empty', conftest.lcyl_arguments(rng, rows=0, cols=0)))

    for name, args in cases:
        with_records = len(records)
        cyl.Lcyl_v2022a_primary(**args, parallel=True)
        cyl.Lcyl_v2022a_primary(**args, parallel=False)
        for record in records[with_records:]:
            record['case'] = name

    # Scalar-provenance specializations at the raw kernel level: float64 and
    # Python-float surface/factor scalars in an otherwise float32 call.
    pixels, patches = 64, 153
    sh, vs, vb = conftest.lw_blocks(rng, pixels, patches)
    coefficients = conftest.lw_coefficients(rng, patches, pixels)
    coefficients['sun'] = rng.random((pixels, patches)) < .5
    coefficients['shade'] = rng.random((pixels, patches)) < .5
    base = (sh, vs, vb, coefficients['sun'], coefficients['shade'],
            coefficients['solid'], coefficients['sine'], coefficients['cosine'],
            coefficients['directions'], coefficients['gate'], coefficients['solar_gate'],
            coefficients['sky_down'], coefficients['sky_side'])
    tail = (coefficients['lup'], coefficients['factor'])
    variants = (
        ('scalar_f64', np.float64(coefficients['sun_surface']), np.float64(coefficients['shade_surface'])),
        ('python_float', float(coefficients['sun_surface']), float(coefficients['shade_surface'])),
    )
    for name, sun_surface, shade_surface in variants:
        with_records = len(records)
        cyl._longwave_primary(*base, sun_surface, shade_surface, *tail)
        cyl._longwave_primary_serial(*base, sun_surface, shade_surface, *tail)
        for record in records[with_records:]:
            record['case'] = f'direct_{name}'
    return 'synthetic_edge'


def _spiked(values, count, shape):
    values = values.astype(np.float32)
    values[1::11] = np.float32('nan')
    values[2::11] = np.float32('inf')
    values[3::11] = np.float32('-inf')
    values[5::11] = np.float32(-0.0)
    return values.reshape(shape)


def keep_and_write(records, originals, phases):
    """Select stored fixtures, write manifest/npz/typed-IR, return manifest."""
    from solweig_light.radiation import cylinder_longwave as cyl

    # Keep the first call per (label, signature-shape) plus every edge case.
    seen_signatures = set()
    arrays = {}

    def _sig_item(a):
        if a['kind'] == 'ndarray':
            return (tuple(a['shape']), a['dtype'])
        return (a['kind'], a.get('dtype', a.get('python_type', '')))

    for record in records:
        signature = tuple(_sig_item(a) for a in record['args'])
        key = (record['label'], signature)
        keep = record.get('case') is not None or key not in seen_signatures
        if keep and key not in seen_signatures:
            seen_signatures.add(key)
        record['kept'] = bool(keep)
        if keep:
            args, output = record.pop('arrays')
            for index, value in enumerate(args):
                if isinstance(value, np.ndarray):
                    arrays[f'call{record["call_index"]:04d}_arg{index:02d}'] = value
                else:
                    arrays[f'call{record["call_index"]:04d}_arg{index:02d}'] = np.array(value)
            arrays[f'call{record["call_index"]:04d}_output'] = output
        else:
            record.pop('arrays', None)

    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CAPTURE_DIR / 'b7_02_fixtures.npz', **arrays)

    signatures = {
        'parallel': [str(sig) for sig in originals['parallel'].signatures],
        'serial': [str(sig) for sig in originals['serial'].signatures],
    }
    with open(CAPTURE_DIR / 'b7_02_typed_ir.txt', 'w') as handle:
        for label in _kernel_labels:
            handle.write(f'===== {label} =====\n')
            originals[label].inspect_types(file=handle)
            handle.write('\n')

    from solweig_light.runtime import get_runtime_options
    options = get_runtime_options()
    manifest = {
        'schema': 'solweig-v7-capture-v1',
        'task': 'B7-02',
        'phases': phases,
        'call_count': len(records),
        'kept_calls': sum(1 for record in records if record['kept']),
        'environment': {
            'python': sys.version.split()[0],
            'numpy': np.__version__,
            'numba': __import__('numba').__version__,
            'platform': platform.platform(),
            'machine': platform.machine(),
        },
        'source_identity': {
            'branch': 'perf/cpu-optimization',
            'head': os.popen('git rev-parse HEAD').read().strip(),
            'reducer_blob': '27ba6ce48454399c7b97285c8408511d050a32da',
        },
        'env_flags': {flag: os.environ.get(flag) for flag in ENV_FLAGS},
        'runtime_options': {
            'block_pixels': options.block_pixels,
            'threads_per_worker': options.threads_per_worker,
            'cpu_budget': options.cpu_budget,
            'workers': options.workers,
        },
        'numba_signatures': signatures,
        'calls': [{key: value for key, value in record.items() if key != 'arrays'}
                  for record in records],
    }
    manifest_path = CAPTURE_DIR / 'b7_02_capture_manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=1))
    return manifest


def main():
    phases = []
    cyl, originals, records = install_capture()
    phases.append(run_real_pipeline(records, cyl))
    phases.append(synthetic_edges(records, cyl))
    manifest = keep_and_write(records, originals, phases)
    print(json.dumps({
        'calls': manifest['call_count'],
        'kept': manifest['kept_calls'],
        'signatures': manifest['numba_signatures'],
        'manifest': str(CAPTURE_DIR / 'b7_02_capture_manifest.json'),
    }, indent=1))


if __name__ == '__main__':
    main()
