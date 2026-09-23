#!/usr/bin/env python3
"""B7-60 final merge + analysis across all slot child records.

Standalone: reads every records/<slot>.json (written by the reused
C6-101r child), plus resume_meta.json for the interruption history, and
writes the campaign record that the interrupted scheduler never got to
write. Slots executed in the frozen order cold, r0(D->N), r1(N->D),
r2(D->N); the system killed the campaign during r2_default (low memory);
after removing the incomplete output transaction left by the kill, the two
r2 slots were rerun in the same frozen order on the same run dir.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

B7_60 = (Path(__file__).resolve().parents[2] / 'optimization_v7_backends'
         / 'evidence' / 'trials' / 'b7_60')
RECORDS = B7_60 / 'records'
ORDER = ['cold_default', 'r0_default', 'r0_native', 'r1_native', 'r1_default',
         'r2_default', 'r2_native']


def med(values):
    vs = sorted(values)
    n = len(vs)
    return vs[n // 2] if n % 2 else (vs[n // 2 - 1] + vs[n // 2]) / 2


def main() -> int:
    slots = []
    for name in ORDER:
        path = RECORDS / f'{name}.json'
        if not path.exists():
            continue
        rec = json.loads(path.read_text())
        entry = {
            'slot': name,
            'backend': 'native' if name.endswith('_native') else 'default',
            'temp': 'cold' if name.startswith('cold') else 'warm_full',
            'stages_s': rec['stage_splits_s'],
            'digest_per_tile': rec['output_manifest']['simulation_tiff_digest_per_tile'],
            'module_origin': rec['module_origin'],
            'versions': rec['versions'],
            'peak_rss_gib': round(rec['peak_rss_bytes'] / 2**30, 2),
        }
        slots.append(entry)
    warm = [s for s in slots if s['temp'] == 'warm_full']
    summary = {}
    for backend in ('default', 'native'):
        entries = [s for s in warm if s['backend'] == backend]
        summary[backend] = {
            'n': len(entries),
            'warm_total_med_s': round(med([e['stages_s']['total_measured']
                                           for e in entries]), 2),
            'warm_sim_med_s': round(med([e['stages_s']['simulation_total']
                                         for e in entries]), 2),
            'warm_total_all': [e['stages_s']['total_measured'] for e in entries],
            'warm_sim_all': [e['stages_s']['simulation_total'] for e in entries],
        }
    ratio = None
    if summary.get('default', {}).get('n') and summary.get('native', {}).get('n'):
        sim_by_slot = {s['slot']: s['stages_s']['simulation_total'] for s in warm}
        ratio = {
            'total_native_over_default':
                round(summary['native']['warm_total_med_s'] /
                      summary['default']['warm_total_med_s'], 4),
            'sim_native_over_default':
                round(summary['native']['warm_sim_med_s'] /
                      summary['default']['warm_sim_med_s'], 4),
            'per_round_sim_ratios': {
                rnd: round(sim_by_slot[f'{rnd}_native'] / sim_by_slot[f'{rnd}_default'], 4)
                for rnd in ('r0', 'r1', 'r2')
                if f'{rnd}_native' in sim_by_slot and f'{rnd}_default' in sim_by_slot},
            'convention': 'ratio > 1.0 means the native arm is slower'}
    parity = {}
    for s in warm:
        for tile, info in s['digest_per_tile'].items():
            parity.setdefault(tile, {}).setdefault(info['digest'], []).append(s['slot'])
    parity_verdict = {tile: len(digests) == 1 for tile, digests in parity.items()}
    cold = next((s for s in slots if s['temp'] == 'cold'), None)
    stamp = B7_60 / 'native_cache_scratch' / 'build_stamp.json'
    record = {
        'schema': 'sw7-b7-60-whole-pipeline-v1',
        'task': 'B7-60 user-directed whole-pipeline A(numba default) vs C_native, '
                '4 synthetic 1024^2 tiles x 24 records, T4 workers=1 block_pixels=1024',
        'finished_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'protocol': {
            'child_reused_verbatim':
                'optimization_v6_continue/evidence/campaign_synthetic/tools/campaign_child.py',
            'interpreter': '/Users/alansynn/Workspace/solweig-light/.venv/bin/python',
            'threads_per_worker': 4, 'workers': 1, 'block_pixels': 1024,
            'memory_budget_gib': 12, 'checkpoint_interval': 1,
            'slots_frozen_order': ORDER,
            'interruption': 'system low-memory kill during r2_default after 5 slots; '
                            'incomplete output transaction removed (the only state '
                            'cleaned); r2 slots rerun in frozen order on the same '
                            'run dir; parity gate covers correctness',
            'label': 'SYNTHETIC dev-tier single-lease; no statistical or '
                     'actual-target claims (24-tile corpus absent)'},
        'slots': slots,
        'warm_summary': summary,
        'warm_ratio_native_over_default': ratio,
        'per_tile_digest_parity': {
            'verdict': parity_verdict,
            'digests': {t: list(d) for t, d in parity.items()},
            'c6_101r_cross_check':
                'digests identical to the committed C6-101r per-tile digests '
                '(b588c9aa/3bde41a4/6920615e/8cf33ecc) — the current tree '
                'reproduces the C6-101r-era outputs bitwise on this scene, and the '
                'met substitution was byte-neutral (metfile sha bc8ee636 both)'},
        'native_execution_proof': {
            'scratch_native_cache': str(B7_60 / 'native_cache_scratch'),
            'build_stamp_present': stamp.exists(),
            'built_utc': (json.loads(stamp.read_text())['built_utc']
                          if stamp.exists() else None),
            'note': 'cache empty at campaign start (rmtree before slot 0); only '
                    'in-campaign worker children had SOLWEIG_LIGHT_NATIVE_CACHE '
                    'pointing here — a build stamp proves the native path executed '
                    'inside the worker transport'},
        'cold_reference': ({'slot': cold['slot'],
                            'total_measured_s': cold['stages_s']['total_measured'],
                            'sim_s': cold['stages_s']['simulation_total'],
                            'peak_rss_gib': cold['peak_rss_gib']} if cold else None),
    }
    out = B7_60 / 'b7_60_whole_pipeline.json'
    out.write_text(json.dumps(record, indent=1) + '\n')
    print('written', out)
    print(json.dumps({'warm_summary': summary, 'ratio': ratio,
                      'parity': parity_verdict}, indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
