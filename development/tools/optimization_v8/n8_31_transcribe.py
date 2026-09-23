#!/usr/bin/env python3
"""N8-31 transcription tool: uniform-composition tables from timed A/B/C archives.

Exists because the R13-D1 delta finding: hand-transcribed end-to-end tables
mixed composition rules per row. This tool derives every number from the
archive under ONE stated rule, so a transcription is mechanically checkable:

    e2e(arm) = sum of component min_ms
      A0p = A_decode_block_x3 + A0_parallel_dense
      A0s = A_decode_block_x3 + A0_serial_dense
      B1  = BC_produce_blocks_aosoa + BC_pack_masks_x2 + B1_numba_adapter
      C1  = BC_produce_blocks_aosoa + BC_float32_views_x3
            + BC_pack_masks_x2 + C1_native_aosoa_adapter

    R-SEL-1: the timed B call receives PRE-PACKED sun_a/shade_a (call
    signature verified), so pack_masks sits OUTSIDE B1's timed kernel; the
    frozen harness comment charges adapters to B1/C1. The earlier
    "adapter inside kernel" B1 rule undercharged B1 by the pack cost.

Usage:
    python tools/optimization_v8/n8_31_transcribe.py <timed_archive.json>

Prints a JSON object: composition rule, per-mix end-to-end table, verdict
checks (C vs each arm), leaf ratios, producer accounting, parity/censor/
ambient extraction. Redirect to a file; paste verbatim into the trial record.
"""
import json
import sys


def _min(x):
    return x['min_ms']


def transcribe(archive):
    e2e, leaves, prod, checks = {}, {}, {}, {}
    parity, censored, ambient = [], 0, []
    for cell in archive['per_block']:
        mix = cell['mix']
        p, a, k = cell['producer_ms'], cell['adapter_ms'], cell['kernel_ms']
        row = {
            'A0p': _min(p['A_decode_block_x3']) + _min(k['A0_parallel_dense']),
            'A0s': _min(p['A_decode_block_x3']) + _min(k['A0_serial_dense']),
            'B1': (_min(p['BC_produce_blocks_aosoa']) + _min(a['BC_pack_masks_x2'])
                   + _min(k['B1_numba_adapter'])),
            'C1': (_min(p['BC_produce_blocks_aosoa']) + _min(a['BC_float32_views_x3'])
                   + _min(a['BC_pack_masks_x2']) + _min(k['C1_native_aosoa_adapter'])),
        }
        e2e[mix] = {arm: round(v, 4) for arm, v in row.items()}
        checks[mix] = {
            'C_beats_A0s': row['C1'] < row['A0s'],
            'C_beats_A0p': row['C1'] < row['A0p'],
            'C_beats_B1': row['C1'] < row['B1'],
            'C_vs_A0s_pct': round((row['C1'] / row['A0s'] - 1) * 100, 1),
        }
        leaves[mix] = {
            'C1k': _min(k['C1k_native_entry_leaf']),
            'B1k': _min(k['B1k_numba_parallel_leaf']),
            'A0s_leaf': _min(k['A0_serial_dense']),
            'A0p_leaf': _min(k['A0_parallel_dense']),
            'B1k_over_C1k': round(_min(k['B1k_numba_parallel_leaf'])
                                  / _min(k['C1k_native_entry_leaf']), 2),
        }
        prod[mix] = {
            'A_decode_x3': _min(p['A_decode_block_x3']),
            'BC_produce': _min(p['BC_produce_blocks_aosoa']),
            'delta': round(_min(p['BC_produce_blocks_aosoa'])
                           - _min(p['A_decode_block_x3']), 4),
            'pack_masks_min': _min(a['BC_pack_masks_x2']),
        }
        parity.append({mix: cell['parity']})
        if str(cell.get('parity', '')).find('pass') < 0:
            censored += 1
        ambient.append(cell.get('ambient_loadavg', None))
    return {
        'archive': archive.get('recorded_utc'),
        'block_sizes': archive.get('block_sizes'),
        'mixes': archive.get('mixes'),
        'reps': archive.get('reps'),
        'ambient_loadavg_start': archive.get('ambient_loadavg_start'),
        'ambient_loadavg_end': archive.get('ambient_loadavg_end'),
        'ambient_per_cell': ambient,
        'parity_all_pass': all('pass' in str(list(p.values())[0]) for p in parity),
        'parity': parity,
        'censored_cells': censored,
        'composition_rule': (
            'UNIFORM all-min: e2e = sum of component min_ms. '
            'A0x = A_decode_block_x3 + A0_{parallel,serial}_dense; '
            'B1 = BC_produce + pack_masks + B1_numba_adapter (canonical per '
            'review R-SEL-1: the timed B call receives pre-packed masks, so '
            'pack_masks is charged to B1); '
            'C1 = BC_produce + views + pack_masks + C1_native_aosoa_adapter.'),
        'end_to_end_min_ms': e2e,
        'verdict_checks': checks,
        'kernel_leaves_min_ms': leaves,
        'producer_accounting_min_ms': prod,
    }


def main(argv):
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 1
    with open(argv[1]) as fh:
        archive = json.load(fh)
    print(json.dumps(transcribe(archive), indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
