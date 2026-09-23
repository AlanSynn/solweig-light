"""B7-31 campaign orchestrator: run the frozen b7_03 config set and analyze.

Runs the nine frozen configurations (kernel_only triage + adapter_total gates
+ warm small-batch gates) through abc_trial_runner's parent, then merges
per-config trial JSONs into one evidence record with:

* cross-variant bitwise digest equality per config/round (mandatory),
* paired warm medians (samples[1:] per child; sample 0 = process-cold guard),
* speed ratios for the frozen gates at 1T equal-budget (C vs B adapter_total
  >= 1.10x on held-out; warm total >= 1.05x over BOTH A and B),
* 4T configs labeled as A/B comparisons (C is single-thread by design and is
  recorded as a different-budget reference, never gated),
* ambient host load sampled before and after the campaign.

Alternating seeded order: rotation of [A, B, C_native] by round index.
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
EVID = REPO / 'optimization_v7_backends' / 'evidence' / 'trials'
RUNNER = HERE / 'abc_trial_runner.py'
PYTHON = str(REPO / '.venv' / 'bin' / 'python')

VARIANTS = ['A', 'B', 'C_native']
ADAPTERS = {
    'A': str(HERE / 'adapter_a.py'),
    'B': str(HERE / 'adapter_b.py'),
    'C_native': str(HERE / 'adapter_c_native.py'),
}

CONFIGS = [
    # (label, fixture, boundary, schedule, numba_threads, held_out)
    ('kernel_adv4096_serial_1T',    'adv4096',  'kernel_only',   'serial',   '1', False),
    ('kernel_adv4096_parallel_4T',  'adv4096',  'kernel_only',   'parallel', '4', False),
    ('kernel_adv16384_serial_1T',   'adv16384', 'kernel_only',   'serial',   '1', True),
    ('kernel_adv65536_serial_1T',   'adv65536', 'kernel_only',   'serial',   '1', True),
    ('adapter_adv16384_serial_1T',  'adv16384', 'adapter_total', 'serial',   '1', True),
    ('adapter_adv65536_serial_1T',  'adv65536', 'adapter_total', 'serial',   '1', True),
    ('adapter_adv16384_parallel_4T', 'adv16384', 'adapter_total', 'parallel', '4', True),
    ('warm_serial_1T',              'warm_serial',   'adapter_total', None, '1', True),
    ('warm_parallel_4T',            'warm_parallel', 'adapter_total', None, '4', True),
]

ROUNDS = 3
REPS = 4  # sample 0 = process-cold guard; samples 1..3 = the 3 paired warm reps


def ambient_load():
    try:
        return round(os.getloadavg()[0], 2)
    except OSError:
        return None


def median(xs):
    ys = sorted(xs)
    n = len(ys)
    return ys[n // 2] if n % 2 else (ys[n // 2 - 1] + ys[n // 2]) / 2


def run_config(label, fixture, boundary, schedule, threads, held_out):
    out = EVID / 'b7_31' / label
    out.mkdir(parents=True, exist_ok=True)
    config = {
        'rounds': 1,
        'reps': REPS,
        'adapters': ADAPTERS,
        'spec': {'fixture': fixture, 'boundary': boundary,
                 'schedule': schedule, 'label': label},
        'env': {'NUMBA_NUM_THREADS': threads},
        'out': str(out),
        'label': label,
    }
    # frozen alternating order: rotate the variant list by round
    orders = [[VARIANTS[(r + s) % 3] for s in range(3)] for r in range(ROUNDS)]
    trials = []
    for r, order in enumerate(orders):
        config['order'] = order
        cfg_path = out / f'config_r{r}.json'
        cfg_path.write_text(json.dumps(config))
        result = subprocess.run(
            [PYTHON, str(RUNNER), '--config', str(cfg_path), '--out', str(out)],
            capture_output=True, text=True)
        if result.returncode != 0:
            trials.append({'round': r, 'error': result.stderr[-2000:]})
            continue
        raw = json.loads((out / f'trials_{label}.json').read_text())
        for t in raw['trials']:
            t['round'] = r
            trials.append(t)
        time.sleep(1.0)  # settle between rounds
    return trials, held_out


def analyze(label, trials, boundary, threads, held_out):
    analysis = {'config': label, 'boundary': boundary,
                'numba_threads': threads, 'held_out': held_out,
                'variants': {}, 'digests_equal': None, 'errors': []}
    per_variant = {}
    for t in trials:
        if 'error' in t:
            analysis['errors'].append({'round': t['round'],
                                       'stderr_tail': t['error'][-400:]})
            continue
        v = t['variant']
        slot = per_variant.setdefault(v, {'warm': [], 'cold': [], 'digests': [],
                                          'identity': t.get('identity')})
        if t.get('rejected_reason'):
            slot['rejected_reason'] = t['rejected_reason']
            continue
        samples = t.get('samples_s') or []
        if samples:
            slot['cold'].append(samples[0])
            slot['warm'].extend(samples[1:])
        if t.get('output_bits_sha256'):
            slot['digests'].append(t['output_bits_sha256'])
    all_digests = {d for s in per_variant.values() for d in s['digests']}
    analysis['digests_equal'] = (len(all_digests) == 1 and len(all_digests) == 1
                                 and all(len(s['digests']) >= 1
                                         for s in per_variant.values()))
    for v, s in per_variant.items():
        entry = {'warm_samples_s': s['warm'], 'cold_guard_s': s['cold'],
                 'warm_median_s': median(s['warm']) if s['warm'] else None,
                 'digest_count': len(s['digests']),
                 'rejected_reason': s.get('rejected_reason'),
                 'identity': s['identity']}
        analysis['variants'][v] = entry
    # gate ratios at equal 1T budget only
    if threads == '1':
        wA = analysis['variants'].get('A', {}).get('warm_median_s')
        wB = analysis['variants'].get('B', {}).get('warm_median_s')
        wC = analysis['variants'].get('C_native', {}).get('warm_median_s')
        if wB and wC:
            analysis['ratio_C_over_B'] = round(wB / wC, 4)
        if wA and wC:
            analysis['ratio_C_over_A'] = round(wA / wC, 4)
        if wA and wB:
            analysis['ratio_B_over_A'] = round(wA / wB, 4)
    return analysis


def main():
    started = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    load_before = ambient_load()
    analyses = []
    for label, fixture, boundary, schedule, threads, held_out in CONFIGS:
        t0 = time.time()
        trials, held = run_config(label, fixture, boundary, schedule, threads, held_out)
        a = analyze(label, trials, boundary, threads, held)
        a['wall_s'] = round(time.time() - t0, 1)
        analyses.append(a)
        status = 'OK' if (a['digests_equal'] and not a['errors']) else 'CHECK'
        print(f"{label:<34} {status:<5} {a['wall_s']:>6}s "
              f"digests_equal={a['digests_equal']} "
              + ' '.join(f"{v}={d['warm_median_s']*1000:.2f}ms"
                         for v, d in a['variants'].items()
                         if d['warm_median_s']), flush=True)
    record = {
        'schema': 'solweig-v7-b7-31-trials-v1',
        'task': 'B7-31 clean A/B/C trials per frozen b7_03 protocol',
        'started_utc': started,
        'finished_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'host': {'machine': 'Apple M1 Pro', 'load_before': load_before,
                 'load_after': ambient_load(),
                 'lease': 'exclusive agent lease requested; ambient user apps '
                          'present and recorded, no other agent measured'},
        'protocol': 'benchmarks/protocols/optimization_v7/b7_03_protocol.json',
        'reps_note': 'per child: sample 0 = process-cold guard (disk cache may '
                     'be warm), samples 1..3 = 3 paired warm reps',
        'order_note': 'frozen alternating rotation [A,B,C]/[B,C,A]/[C,A,B]',
        'budget_note': '4T configs are A/B comparisons; C_native is '
                       'single-thread by design and recorded as a '
                       'different-budget reference, never gated',
        'analyses': analyses,
    }
    EVID.mkdir(parents=True, exist_ok=True)
    out_path = EVID / 'b7_31_trials.json'
    out_path.write_text(json.dumps(record, indent=1))
    print('written', out_path)


if __name__ == '__main__':
    main()
