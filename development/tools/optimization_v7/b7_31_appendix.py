"""B7-31 appendix: C_drjit trials at matched thread budgets.

Runs after the drjit B7-30 review. All variants execute under the drjit
worktree venv interpreter (identical python/numba/numpy versions to the
baseline; adds drjit 1.5.0), so A and C_native numbers are directly
comparable to the main campaign. C_drjit's Dr.Jit pool is pinned per config
via configure_runtime(threads) — 1T configs give an equal-budget comparison;
the 4T config compares A(numba 4T) vs C_drjit(4 threads) with C_native as a
labeled 1T reference (as in the main campaign).

Configs target the claimed performance split: pipeline block size (B=128,
both kernel-level and the real-scene warm sequence) and large held-out B.
"""
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from b7_31_run import analyze, ambient_load, median  # noqa: E402

REPO = HERE.parents[1]
EVID = REPO / 'optimization_v7_backends' / 'evidence' / 'trials'
RUNNER = HERE / 'abc_trial_runner.py'
PYTHON = '/Users/alansynn/Workspace/solweig-v7-drjit/.venv-v7/bin/python'

VARIANTS = ['A', 'C_native', 'C_drjit']
ADAPTERS = {
    'A': str(HERE / 'adapter_a.py'),
    'C_native': str(HERE / 'adapter_c_native.py'),
    'C_drjit': str(HERE / 'adapter_c_drjit.py'),
}

# (label, fixture, boundary, schedule, numba_threads, drjit_threads, held_out)
CONFIGS = [
    ('kernel_adv128_serial_1T',   'adv128',   'kernel_only',   'serial',   '1', 1, False),
    ('warm_serial_1T',            'warm_serial',   'adapter_total', None, '1', 1, True),
    ('warm_parallel_4T',          'warm_parallel', 'adapter_total', None, '4', 4, True),
    ('adapter_adv65536_serial_1T', 'adv65536', 'adapter_total', 'serial',   '1', 1, True),
]

ROUNDS = 3
REPS = 4


def run_config(label, fixture, boundary, schedule, nthreads, dthreads):
    out = EVID / 'b7_31_appendix' / label
    out.mkdir(parents=True, exist_ok=True)
    config = {
        'rounds': 1, 'reps': REPS, 'adapters': ADAPTERS,
        'spec': {'fixture': fixture, 'boundary': boundary, 'schedule': schedule,
                 'label': label, 'drjit_threads': dthreads},
        'env': {'NUMBA_NUM_THREADS': nthreads},
        'out': str(out), 'label': label,
    }
    orders = [[VARIANTS[(r + s) % 3] for s in range(3)] for r in range(ROUNDS)]
    trials = []
    for r, order in enumerate(orders):
        config['order'] = order
        cfg_path = out / f'config_r{r}.json'
        cfg_path.write_text(json.dumps(config))
        result = subprocess.run([PYTHON, str(RUNNER), '--config', str(cfg_path),
                                 '--out', str(out)], capture_output=True, text=True)
        if result.returncode != 0:
            trials.append({'round': r, 'error': result.stderr[-2000:]})
            continue
        raw = json.loads((out / f'trials_{label}.json').read_text())
        for t in raw['trials']:
            t['round'] = r
            trials.append(t)
        time.sleep(1.0)
    return trials


def main():
    started = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    load_before = ambient_load()
    analyses = []
    for label, fixture, boundary, schedule, nthreads, dthreads, held in CONFIGS:
        t0 = time.time()
        trials = run_config(label, fixture, boundary, schedule, nthreads, dthreads)
        a = analyze(label, trials, boundary, nthreads, held)
        a['drjit_threads'] = dthreads
        a['wall_s'] = round(time.time() - t0, 1)
        med = {v: d.get('warm_median_s') for v, d in a['variants'].items()}
        a['pairwise_speedups'] = {
            f'{x}_over_{y}': round(med[y] / med[x], 4)
            for x in med for y in med
            if x != y and med[x] and med[y]}
        analyses.append(a)
        status = 'OK' if (a['digests_equal'] and not a['errors']) else 'CHECK'
        print(f"{label:<30} {status:<5} {a['wall_s']:>6}s digests={a['digests_equal']} "
              + ' '.join(f"{v}={d['warm_median_s']*1000:.2f}ms"
                         for v, d in a['variants'].items() if d['warm_median_s']),
              flush=True)
    record = {
        'schema': 'solweig-v7-b7-31-appendix-drjit-v1',
        'task': 'B7-31 appendix: C_drjit at matched budgets (post B7-30 review)',
        'interpreter': PYTHON,
        'interpreter_note': 'identical python 3.12.13 / numba 0.67.0 / numpy '
                            '2.4.6 as the baseline venv; adds drjit 1.5.0',
        'started_utc': started,
        'host': {'load_before': load_before, 'load_after': ambient_load()},
        'reps_note': 'sample 0 = process-cold guard; samples 1..3 = 3 paired warm reps',
        'analyses': analyses,
    }
    out_path = EVID / 'b7_31_appendix_drjit.json'
    out_path.write_text(json.dumps(record, indent=1))
    print('written', out_path)


if __name__ == '__main__':
    main()
