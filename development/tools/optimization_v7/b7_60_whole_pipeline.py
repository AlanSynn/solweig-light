#!/usr/bin/env python3
"""B7-60 whole-pipeline paired campaign: numba default (A) vs C_native at
4 synthetic 1024^2 tiles, 24 timesteps, T4 (user-directed).

Reuses the committed C6-101r child verbatim
(optimization_v6_continue/evidence/campaign_synthetic/tools/campaign_child.py):
fresh child process per slot, thread limits before numerical import, public
three-stage workflow, per-tile output digests. The ONLY difference between
the two arms is SOLWEIG_LIGHT_LW_BACKEND in the child environment (default
arm: var removed) — same tree, same interpreter, same RuntimeOptions.

Execution proof for the native arm: slot r0-native targets a FRESH scratch
native cache (SOLWEIG_LIGHT_NATIVE_CACHE) that only an in-campaign worker
child can populate; the build stamp appearing there after the slot is
filesystem evidence the native path executed inside the worker transport.
Build cost lands in r0-native (conservative direction for the native median).

Slots (frozen before the first run): cold default, then warm pairs
alternating — r0 default->native, r1 native->default, r2 default->native.
Warm medians per arm; per-tile digests must be IDENTICAL across all slots
(bitwise parity A vs native at 1024^2 x 24 records).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
B7_60 = REPO / 'optimization_v7_backends' / 'evidence' / 'trials' / 'b7_60'
CAMP = REPO / 'optimization_v6_continue' / 'evidence' / 'campaign_synthetic'
CHILD = CAMP / 'tools' / 'campaign_child.py'
sys.path.insert(0, str(CAMP / 'tools'))
from thread_limits import child_environment  # noqa: E402

PYTHON = str(REPO / '.venv' / 'bin' / 'python')
SITE = str(REPO / 'src')
SCENE = B7_60 / 'scenes' / 'scene_t1024'
RUN_ROOT = B7_60 / 'runs' / 't1024_T4'
NATIVE_CACHE_SCRATCH = B7_60 / 'native_cache_scratch'
RECORDS = B7_60 / 'records'
TIMEOUT_S = 5400
THREADS = 4

# (slot, temp, backend) — backend None = unset (numba default)
SLOTS = [
    ('cold_default', 'cold',      None),
    ('r0_default',   'warm_full', None),
    ('r0_native',    'warm_full', 'native'),
    ('r1_native',    'warm_full', 'native'),
    ('r1_default',   'warm_full', None),
    ('r2_default',   'warm_full', None),
    ('r2_native',    'warm_full', 'native'),
]


def run_slot(slot: str, temp: str, backend: str | None) -> dict:
    env = child_environment(THREADS, str(RUN_ROOT / 'numba_cache'))
    env.pop('SOLWEIG_LIGHT_LW_BACKEND', None)
    if backend == 'native':
        env['SOLWEIG_LIGHT_LW_BACKEND'] = backend
        env['SOLWEIG_LIGHT_NATIVE_CACHE'] = str(NATIVE_CACHE_SCRATCH)
    load_before = list(__import__('os').getloadavg())
    out = RECORDS / f'{slot}.json'
    t0 = time.monotonic()
    proc = subprocess.run(
        [PYTHON, str(CHILD),
         '--site', SITE, '--scene-src', str(SCENE),
         '--run-root', str(RUN_ROOT), '--temp', temp,
         '--workers', '1', '--threads', str(THREADS),
         '--cpu-budget', '4', '--memory-budget-gib', '12',
         '--block-pixels', '1024', '--out', str(out)],
        capture_output=True, text=True, timeout=TIMEOUT_S, env=env)
    wall_s = round(time.monotonic() - t0, 3)
    entry = {'slot': slot, 'temp': temp, 'backend': backend or 'default',
             'wall_s': wall_s, 'returncode': proc.returncode,
             'loadavg_before': [round(x, 2) for x in load_before],
             'loadavg_after': [round(x, 2) for x in __import__('os').getloadavg()],
             'stderr_tail': proc.stderr[-1500:] if proc.returncode else ''}
    if proc.returncode == 0:
        rec = json.loads(out.read_text())
        entry['stages_s'] = rec['stage_splits_s']
        entry['digest_per_tile'] = rec['output_manifest']['simulation_tiff_digest_per_tile']
        entry['module_origin'] = rec['module_origin']
    if backend == 'native':
        stamp = NATIVE_CACHE_SCRATCH / 'build_stamp.json'
        dylib = sorted(p.name for p in NATIVE_CACHE_SCRATCH.glob('*.dylib')) \
            if NATIVE_CACHE_SCRATCH.is_dir() else []
        entry['scratch_native_cache'] = {
            'build_stamp_present': stamp.exists(),
            'dylibs': dylib,
            'note': 'fresh at campaign start; only in-campaign worker children '
                    'could populate it under SOLWEIG_LIGHT_NATIVE_CACHE'}
    return entry


def main() -> int:
    B7_60.mkdir(parents=True, exist_ok=True)
    RECORDS.mkdir(parents=True, exist_ok=True)
    # proof freshness: the scratch native cache must be empty at campaign
    # start so a build stamp appearing later can only come from an
    # in-campaign worker child
    if NATIVE_CACHE_SCRATCH.exists():
        shutil.rmtree(NATIVE_CACHE_SCRATCH)
    manifest = json.loads((SCENE / 'scene_manifest.json').read_text())
    started = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    slots = []
    for slot, temp, backend in SLOTS:
        entry = run_slot(slot, temp, backend)
        status = 'OK' if entry['returncode'] == 0 else 'FAIL'
        sim = entry.get('stages_s', {}).get('simulation_total')
        print(f"{slot:<12} {status:<4} wall={entry['wall_s']:>8.1f}s "
              f"sim={sim if sim is not None else '—'}", flush=True)
        if entry['returncode'] != 0:
            print(entry['stderr_tail'][-800:], flush=True)
            slots.append(entry)
            break  # do not continue a broken campaign
        slots.append(entry)
        time.sleep(1.0)
    # analysis
    warm = [s for s in slots if s.get('stages_s')]
    arms = {}
    for s in warm:
        if s['temp'] != 'warm_full':
            continue
        arms.setdefault(s['backend'], []).append(s)

    def med(values):
        vs = sorted(values)
        n = len(vs)
        return vs[n // 2] if n % 2 else (vs[n // 2 - 1] + vs[n // 2]) / 2

    summary = {}
    for arm, entries in arms.items():
        summary[arm] = {
            'n': len(entries),
            'warm_total_med_s': round(med([e['stages_s']['total_measured'] for e in entries]), 2),
            'warm_sim_med_s': round(med([e['stages_s']['simulation_total'] for e in entries]),
                                    2),
            'warm_total_all': [e['stages_s']['total_measured'] for e in entries],
            'warm_sim_all': [e['stages_s']['simulation_total'] for e in entries],
        }
    ratio = None
    if 'default' in summary and 'native' in summary:
        ratio = {'total_native_over_default':
                 round(summary['default']['warm_total_med_s'] /
                       summary['native']['warm_total_med_s'], 4),
                 'sim_native_over_default':
                 round(summary['default']['warm_sim_med_s'] /
                       summary['native']['warm_sim_med_s'], 4)}
    # per-tile digest equality across ALL successful slots
    parity = {}
    for s in warm:
        for tile, info in s.get('digest_per_tile', {}).items():
            parity.setdefault(tile, {}).setdefault(info['digest'], []).append(s['slot'])
    parity_verdict = {tile: (len(digests) == 1)
                      for tile, digests in parity.items()}
    proof = next((s.get('scratch_native_cache') for s in slots
                  if s.get('scratch_native_cache')), None)
    cold = next((s for s in slots if s['temp'] == 'cold' and s.get('stages_s')), None)
    record = {
        'schema': 'sw7-b7-60-whole-pipeline-v1',
        'task': 'B7-60 user-directed whole-pipeline A(numba default) vs C_native, '
                '4 synthetic 1024^2 tiles x 24 records, T4 workers=1 block_pixels=1024',
        'started_utc': started,
        'scene_manifest': {'dir': manifest['dir'],
                           'met_source': manifest['met_source'],
                           'met_note': manifest['met_source_note'],
                           'sha256_inputs': manifest['sha256']},
        'protocol': {'child': str(CHILD), 'child_reused_verbatim': True,
                     'interpreter': PYTHON, 'site': SITE,
                     'threads_per_worker': THREADS, 'slots': [list(s) for s in SLOTS],
                     'timeout_s': TIMEOUT_S,
                     'label': 'SYNTHETIC dev-tier single-lease; no statistical or '
                              'actual-target claims'},
        'slots': slots,
        'warm_summary': summary,
        'warm_ratio_native_over_default': ratio,
        'per_tile_digest_parity': {'verdict': parity_verdict,
                                   'digests': {t: list(d) for t, d in parity.items()},
                                   'note': 'one digest per tile across all warm slots = '
                                           'bitwise parity between arms'},
        'native_execution_proof': proof,
        'cold_reference': ({'slot': cold['slot'],
                            'total_measured_s': cold['stages_s']['total_measured'],
                            'sim_s': cold['stages_s']['simulation_total']} if cold else None),
    }
    (B7_60 / 'b7_60_whole_pipeline.json').write_text(json.dumps(record, indent=1) + '\n')
    print('written', B7_60 / 'b7_60_whole_pipeline.json', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
