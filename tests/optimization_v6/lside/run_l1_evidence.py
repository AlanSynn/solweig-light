"""C6-20 L1 evidence harness: per-timestep parity, admission, and timing.

Runs the untouched ``engine.Lside_veg_v2022a`` and the private demand-dispatched
candidate (``pipeline_demand.lside_veg_v2022a_demanded``) side by side on
adversarial 24-step schedules at 128 square plus the real processed SVF
fixture, records per-timestep/per-field bitwise parity and warning streams,
and times the original against the fast path and the full fallback.

Timing is a contended development-tier observation (eight sibling workers
share this host); it is recorded, never claimed.  Evidence is written to
``optimization_v6_continue/evidence/lside/`` before any failure exits.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
import time
import warnings

os.environ.setdefault('NUMBA_NUM_THREADS', '2')  # development thread cap

from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
SRC = REPO / 'src'
EVIDENCE = REPO / 'optimization_v6_continue' / 'evidence' / 'lside'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from solweig_light.radiation.engine import Lside_veg_v2022a  # noqa: E402
from solweig_light.radiation.pipeline_demand import (  # noqa: E402
    RadiationDemand,
    demand_identity,
    lside_veg_v2022a_demanded,
)

PARAM_ORDER = (
    'svfS', 'svfW', 'svfN', 'svfE', 'svfEveg', 'svfSveg', 'svfWveg', 'svfNveg',
    'svfEaveg', 'svfSaveg', 'svfWaveg', 'svfNaveg',
    'azimuth', 'altitude', 'Ta', 'Tw', 'SBC', 'ewall', 'Ldown', 'esky', 't',
    'F_sh', 'CI', 'LupE', 'LupS', 'LupW', 'LupN', 'anisotropic_longwave',
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_case(shape, dtype=np.float32, seed=20260920, svf_mode='clean'):
    rng = np.random.default_rng(seed)

    def svf():
        return (0.05 + 0.9 * rng.random(shape)).astype(dtype)

    case = dict(
        svfS=svf(), svfW=svf(), svfN=svf(), svfE=svf(),
        svfEveg=svf(), svfSveg=svf(), svfWveg=svf(), svfNveg=svf(),
        svfEaveg=svf(), svfSaveg=svf(), svfWaveg=svf(), svfNaveg=svf(),
        azimuth=137.5, altitude=32.0, Ta=21.5,
        Tw=(30.0 * rng.random(shape)).astype(dtype),
        SBC=5.67e-8, ewall=0.95,
        Ldown=(400.0 * rng.random(shape)).astype(dtype),
        esky=0.85, t=15,
        F_sh=rng.random(shape).astype(dtype),
        CI=0.72,
        LupE=(450.0 * rng.random(shape)).astype(dtype),
        LupS=(450.0 * rng.random(shape)).astype(dtype),
        LupW=(450.0 * rng.random(shape)).astype(dtype),
        LupN=(450.0 * rng.random(shape)).astype(dtype),
        anisotropic_longwave=1,
    )
    if svf_mode == 'real_like':
        case['svfE'] = np.full(shape, 1.0, dtype=dtype)  # real svfE rasters do this
    return case


def schedule_step(case, step):
    step_case = dict(case)
    step_case['altitude'] = -8.0 if step % 5 == 0 else (0.0 if step % 7 == 0 else 4.0 + 2.5 * step)
    azimuth = (122.0 + 15.0 * step) % 360.0
    if step % 11 == 3:
        azimuth = 361.0
    if step % 11 == 5:
        azimuth = -30.0
    step_case['azimuth'] = azimuth
    step_case['CI'] = (0.2, 0.72, 0.95, 1.0)[step % 4]
    if step > 0:
        for key in ('LupE', 'LupS', 'LupW', 'LupN'):
            step_case[key] = (step_case[key] + np.float32(0.25)).astype(np.float32)
    if step == 6:
        for key in ('LupE', 'LupS', 'LupW', 'LupN'):
            step_case[key] = np.zeros(step_case[key].shape, dtype=np.float32)
    if step == 9:
        step_case['LupE'] = np.full(step_case['LupE'].shape, np.nan, dtype=np.float32)
        step_case['LupS'] = step_case['LupS'].copy()
        step_case['LupS'][0, 0] = np.inf
    if step == 12:
        step_case['LupW'] = np.full(step_case['LupW'].shape, -0.0, dtype=np.float32)
        step_case['LupN'] = np.full(step_case['LupN'].shape, 1e-45, dtype=np.float32)
    return step_case


def run_pair(case, demand=RadiationDemand.PIPELINE_CYLINDER_ANISOTROPIC):
    """Return (candidate_outcome, reference_outcome, candidate_warnings)."""
    args = [case[name] for name in PARAM_ORDER]
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        try:
            got = ('ok', lside_veg_v2022a_demanded(*args, demand=demand))
        except Exception as exc:  # noqa: BLE001
            got = ('error', type(exc).__name__, str(exc))
    with warnings.catch_warnings(record=True):
        warnings.simplefilter('always')
        try:
            want = ('ok', Lside_veg_v2022a(*args))
        except Exception as exc:  # noqa: BLE001
            want = ('error', type(exc).__name__, str(exc))
    warned = [(w.category.__name__, str(w.message)) for w in caught]
    return got, want, warned


def compare(got, want, warned, warned_reference):
    fields = {}
    if got[0] != want[0]:
        return {'verdict': 'FAIL', 'candidate': got[0], 'reference': want[0]}
    if got[0] == 'error':
        fields['exception'] = {'verdict': 'OK', 'class': got[1], 'message': got[2]}
        return {'verdict': 'OK', 'outcome': 'error', 'fields': fields}
    names = ('Least', 'Lsouth', 'Lwest', 'Lnorth')
    for name, g, w in zip(names, got[1], want[1]):
        ok = g.dtype == w.dtype and g.shape == w.shape and g.tobytes() == w.tobytes()
        fields[name] = {
            'verdict': 'OK' if ok else 'FAIL',
            'dtype': str(g.dtype),
            'shape': list(g.shape),
            'bytes_sha256': hashlib.sha256(g.tobytes()).hexdigest()[:16],
        }
    verdict = 'OK' if all(f['verdict'] == 'OK' for f in fields.values()) else 'FAIL'
    return {'verdict': verdict, 'outcome': 'ok', 'fields': fields, 'warnings': warned}


def parity_block(label, case, steps=24):
    rows = []
    all_ok = True
    for step in range(steps):
        step_case = schedule_step(case, step)
        got, want, warned = run_pair(step_case)
        with warnings.catch_warnings(record=True) as ref_caught:
            warnings.simplefilter('always')
            try:
                Lside_veg_v2022a(*[step_case[name] for name in PARAM_ORDER])
            except Exception:  # noqa: BLE001
                pass
        warned_reference = [(w.category.__name__, str(w.message)) for w in ref_caught]
        record = compare(got, want, warned, warned_reference)
        record['warnings_match_reference'] = warned == warned_reference
        if record['verdict'] != 'OK' or not record['warnings_match_reference']:
            all_ok = False
        rows.append({'step': step, **record})
    return {'label': label, 'all_steps_bitwise_ok': all_ok, 'steps': rows}


def timed(label, runner, repeats=3):
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        runner()
        samples.append(time.perf_counter() - start)
    return {'label': label, 'samples_s': [round(s, 4) for s in samples], 'min_s': min(samples)}


def main():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    module = SRC / 'solweig_light' / 'radiation' / 'pipeline_demand.py'
    evidence = {
        'task': 'C6-20 anisotropic Lside private fast path',
        'reduction_rule': 'R-A',
        'worktree_head': os.popen('git -C %s rev-parse HEAD' % REPO).read().strip(),
        'module_sha256': sha256(module),
        'identity': demand_identity(),
        'environment': {
            'python': sys.version.split()[0],
            'numpy': np.__version__,
            'numba': __import__('numba').__version__,
            'machine': platform.machine(),
            'system': platform.system(),
            'numba_num_threads_env': os.environ.get('NUMBA_NUM_THREADS'),
            'tier': 'contended development host, 8 sibling workers; recorded, no claims',
        },
        'parity': [],
        'timing': [],
    }

    shape = (128, 128)
    evidence['parity'].append(parity_block('128_clean_svf', make_case(shape, svf_mode='clean')))
    evidence['parity'].append(parity_block('128_svfE_exact_one', make_case(shape, svf_mode='real_like')))

    fallback_case = make_case(shape)
    fallback_case['svfE'] = np.full(shape, np.float32(1.5), dtype=np.float32)
    block = parity_block('128_svfE_above_one_fallback_domain', fallback_case, steps=4)
    evidence['parity'].append(block)

    fixture_zip = REPO / 'tests' / 'reference' / 'small_original_cpu' / 'scene' / 'processed_inputs' / 'SVF' / 'svfs_0_0.zip'
    if fixture_zip.exists():
        import tempfile
        import zipfile

        from osgeo import gdal

        gdal.UseExceptions()
        fshape = (32, 35)
        case = make_case(fshape, svf_mode='clean')
        stats = {}
        with zipfile.ZipFile(fixture_zip) as bundle:
            names = {Path(n).name: n for n in bundle.namelist()}
            for key in ('svfS', 'svfW', 'svfN', 'svfE', 'svfEveg', 'svfSveg', 'svfWveg', 'svfNveg',
                        'svfEaveg', 'svfSaveg', 'svfWaveg', 'svfNaveg'):
                with tempfile.TemporaryDirectory() as tmp:
                    target = Path(tmp) / f'{key}.tif'
                    target.write_bytes(bundle.read(names[f'{key}.tif']))
                    dataset = gdal.Open(str(target))
                    raster = dataset.GetRasterBand(1).ReadAsArray()
                    dataset = None
                raster = np.ascontiguousarray(raster.astype(np.float32))
                case[key] = raster
                stats[key] = {'min': float(raster.min()), 'max': float(raster.max()),
                              'n_exact_one': int((raster == 1.0).sum())}
        evidence['fixture_svf_stats'] = stats
        evidence['parity'].append(parity_block('real_svf_fixture_32x35', case))

    # Timing cells: same process, alternating order, full warnings captured.
    a_case = make_case(shape, svf_mode='clean')
    b_case = make_case(shape, svf_mode='real_like')
    fb_case = make_case(shape)
    fb_case['svfE'] = np.full(shape, np.float32(1.5), dtype=np.float32)
    fb_args = [fb_case[name] for name in PARAM_ORDER]

    def orig_a():
        for step in range(24):
            Lside_veg_v2022a(*[schedule_step(a_case, step)[n] for n in PARAM_ORDER])

    def fast_a():
        for step in range(24):
            lside_veg_v2022a_demanded(*[schedule_step(a_case, step)[n] for n in PARAM_ORDER],
                                      demand=RadiationDemand.PIPELINE_CYLINDER_ANISOTROPIC)

    def orig_b():
        for step in range(24):
            Lside_veg_v2022a(*[schedule_step(b_case, step)[n] for n in PARAM_ORDER])

    def fast_b():
        for step in range(24):
            lside_veg_v2022a_demanded(*[schedule_step(b_case, step)[n] for n in PARAM_ORDER],
                                      demand=RadiationDemand.PIPELINE_CYLINDER_ANISOTROPIC)

    def full_b():
        for step in range(24):
            lside_veg_v2022a_demanded(*[schedule_step(b_case, step)[n] for n in PARAM_ORDER],
                                      demand=RadiationDemand.FULL_DIAGNOSTICS)

    def fallback_fb():
        lside_veg_v2022a_demanded(*fb_args, demand=RadiationDemand.PIPELINE_CYLINDER_ANISOTROPIC)

    orig_a(); fast_a(); orig_b(); fast_b(); full_b(); fallback_fb()  # warmup/JIT
    labels = {
        'orig_a': 'original 128 clean x24',
        'fast_a': 'dispatch 128 clean (tier A) x24',
        'orig_b': 'original 128 svfE=1 x24',
        'fast_b': 'dispatch 128 svfE=1 (tier B) x24',
        'full_b': 'FULL_DIAGNOSTICS 128 svfE=1 x24',
        'fallback_fb': 'dispatch fallback domain 128 x1',
    }
    for cell in (orig_a, fast_a, orig_b, fast_b, full_b, orig_a, fast_a, orig_b, fast_b, full_b, fallback_fb, fallback_fb):
        evidence['timing'].append(timed(labels[cell.__name__], cell))

    failures = [b['label'] for b in evidence['parity'] if not b['all_steps_bitwise_ok']]
    evidence['verdict'] = 'ALL_BITWISE_OK' if not failures else f'FAILED: {failures}'
    out = EVIDENCE / 'l1_parity_and_timing.json'
    out.write_text(json.dumps(evidence, indent=2))
    print(json.dumps({'verdict': evidence['verdict'], 'evidence': str(out),
                      'timing': [(t['label'], t['min_s']) for t in evidence['timing']]}, indent=2))
    return 0 if not failures else 1


if __name__ == '__main__':
    sys.exit(main())
