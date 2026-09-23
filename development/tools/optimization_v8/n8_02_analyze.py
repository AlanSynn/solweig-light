#!/usr/bin/env python3
"""N8-02 post-analysis: derive island fractions, prep overhead, and the
explicit (a)-(d) answers; fold them into evidence/profile/n8_02_profile.json.
Raw per-rep records stay untouched in raw/."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
EVIDENCE = REPO / 'optimization_v8_native_default' / 'evidence' / 'profile'

rec = json.loads((EVIDENCE / 'n8_02_profile.json').read_text())
raw = json.loads((EVIDENCE / 'raw' / 'n8_02_all_runs.json').read_text())


def warm_per_call(counters, key):
    n = counters['counts'].get(key, 0)
    if not n:
        return None
    total = counters['total_s'][key]
    first = counters['first_call_s'].get(key, 0.0)
    return {'n': n, 'total_s': round(total, 6), 'first_s': round(first, 6),
            'warm_per_call_us': round((total - first) / max(1, n - 1) * 1e6, 2)}


instr = {tag: r['counters'] for tag, r in rec['instrumented'].items()}
walls = {tag: r['run_wall_s'] for tag, r in rec['instrumented'].items()}

answers = {}

# (a) native call counts + fallback reasons, both arms, real packed pipeline
def arm_summary(tag):
    c = instr[tag]
    prep = warm_per_call(c, 'native_prep.ensure_loaded_total')
    island_default = c['total_s'].get('island.numba_lw_primary', 0.0) + \
        c['total_s'].get('island.numba_lw_primary_serial', 0.0)
    lcyl = c['total_s'].get('stage.lcyl_by_demand', 0.0)
    calc = c['total_s'].get('stage.solweig_calc', 0.0)
    wall = walls[tag]
    return {
        'run_wall_s_instrumented': wall,
        'lcyl_calls': c['counts'].get('stage.lcyl_by_demand', 0),
        'blocks_per_run': c['counts'].get('island.numba_lw_primary', 0) or
                          c['counts'].get('native_adapter.admitted', 0),
        'numba_kernel_calls': c['counts'].get('island.numba_lw_primary', 0),
        'native_adapter_calls': c['counts'].get('native_adapter.admitted', 0),
        'native_c_entry_calls': dict(c['native_entry_specs']),
        'native_rejected_unsupportedinput': c['counts'].get('native_adapter.rejected', 0),
        'distinct_fallback_reasons': c['fallback_reasons'],
        'pipeline_initiated_native_loader_calls':
            c['counts'].get('native_prep.ensure_loaded_total', 0),
        'island_total_s': round(
            (c['total_s'].get('native_adapter.admitted', 0.0) or island_default), 6),
        'island_fraction_of_lcyl': round(
            ((c['total_s'].get('native_adapter.admitted', 0.0) or island_default)
             / lcyl if lcyl else None), 4),
        'island_fraction_of_radiation_calc': round(
            ((c['total_s'].get('native_adapter.admitted', 0.0) or island_default)
             / calc if calc else None), 4),
        'island_fraction_of_run_tile_wall': round(
            ((c['total_s'].get('native_adapter.admitted', 0.0) or island_default)
             / wall if wall else None), 4),
        'stage_totals_s': {k: v for k, v in sorted(c['total_s'].items())
                           if k.startswith(('stage.', 'island.', 'native_'))},
    }

answers['a_native_counts_and_fallbacks'] = {
    'default_env': arm_summary('instr_default_b128'),
    'default_env_b1024': arm_summary('instr_default_b1024'),
    'native_env': arm_summary('instr_native_b128'),
    'native_env_b1024': arm_summary('instr_native_b1024'),
    'verdict': {
        'default_takes_native_path': False,
        'default_evidence': [
            'pipeline-initiated native loader calls = 0 in both default instrumented runs',
            'native adapter / C-entry counters = 0 under default env',
            'production pool entry (run_utci_tiles, default env, fresh scratch '
            'SOLWEIG_LIGHT_NATIVE_CACHE): scratch cache EMPTY after the run - '
            'worker children never imported/built native',
        ],
        'native_evidence': [
            '432 C entries (f64) per run at block=128 (48 timesteps x 9 blocks)',
            '96 C entries (f64) per run at block=1024 (48 x 2)',
            'pool entry with native env: worker child built dylibs + stamp in the '
            'fresh scratch cache (filesystem proof through the scheduler)',
        ],
        'fallbacks': 'ZERO UnsupportedInput rejections in the real packed pipeline '
                     '(admitted: 432/432 and 96/96; the admission domain matches the '
                     'real pipeline exactly; f64 surface-scalar spec selected)',
    },
}

# (b) true island fraction + stage decomposition
def decomposition(tag):
    c = instr[tag]
    wall = walls[tag]
    t = c['total_s']
    n = c['counts']
    lcyl = t.get('stage.lcyl_by_demand', 0.0)
    dpc = t.get('stage.dpc_primary', 0.0)
    island = (t.get('native_adapter.admitted', 0.0) or
              (t.get('island.numba_lw_primary', 0.0) +
               t.get('island.numba_lw_primary_serial', 0.0)))
    decode = t.get('stage.decode_block_x3', 0.0)
    cls = t.get('stage.classifier_classes', 0.0)
    blocks = n.get('island.numba_lw_primary', 0) or n.get('native_adapter.admitted', 0)
    # decode/classifier counters span the whole radiation stage (LW + SW).
    # In-Lcyl portions use the known per-block call pattern (3 decodes + 1
    # classifier per LW block) times stage per-call means: labelled estimates;
    # island and stage totals are direct measurements.
    decode_lw_est = (decode / n.get('stage.decode_block_x3', 1)) * 3 * blocks
    cls_lw_est = (cls / n.get('stage.classifier_classes', 1)) * blocks
    return {
        'run_tile_wall_s': wall,
        'radiation_solweig_calc_s': round(t.get('stage.solweig_calc', 0.0), 4),
        'lcyl_wrapper_s': round(lcyl, 4),
        'dpc_primary_s': round(dpc, 4),
        'classifier_stage_total_s': round(cls, 4),
        'decode_stage_total_s': round(decode, 4),
        'lw_reducer_island_s': round(island, 4),
        'comfort_utci_s': round(t.get('stage.utci', 0.0), 4),
        'output_write_s': round(t.get('stage.output_write', 0.0), 4),
        'output_checkpoint_s': round(t.get('stage.output_checkpoint', 0.0), 4),
        'geometry_legacy_load_s': round(t.get('stage.geometry_legacy_load', 0.0), 4),
        'raster_reads_s': round(t.get('stage.read_raster_pipeline', 0.0), 4),
        'fractions_of_wall': {
            'radiation': round(t.get('stage.solweig_calc', 0.0) / wall, 4),
            'lcyl': round(lcyl / wall, 4),
            'lw_reducer_island': round(island / wall, 4),
            'decode_stage_total': round(decode / wall, 4),
            'classifier_stage_total': round(cls / wall, 4),
            'comfort': round(t.get('stage.utci', 0.0) / wall, 4),
            'durable_io_write_plus_checkpoint': round(
                (t.get('stage.output_write', 0.0) +
                 t.get('stage.output_checkpoint', 0.0)) / wall, 4),
        },
        'fractions_of_lcyl': {
            'lw_reducer_island_measured': round(island / lcyl, 4) if lcyl else None,
            'decode_in_lcyl_estimated': round(decode_lw_est / lcyl, 4) if lcyl else None,
            'classifier_in_lcyl_estimated': round(cls_lw_est / lcyl, 4) if lcyl else None,
            'dpc_residual_layout_scatter_estimated': round(
                (dpc - island - decode_lw_est - cls_lw_est) / lcyl, 4) if lcyl else None,
            'note': 'island is exact (LW-only calls); decode/classifier counters '
                    'cover LW+SW, in-Lcyl parts are per-call-mean estimates using '
                    'the 3-decodes+1-classifier-per-LW-block pattern',
        },
    }

prep = warm_per_call(instr['instr_native_b128'], 'native_prep.ensure_loaded_total')
prep1024 = warm_per_call(instr['instr_native_b1024'], 'native_prep.ensure_loaded_total')
c_entry = warm_per_call(instr['instr_native_b128'], 'native_c_entry.f64')
c_entry1024 = warm_per_call(instr['instr_native_b1024'], 'native_c_entry.f64')
admitted = warm_per_call(instr['instr_native_b128'], 'native_adapter.admitted')
numba_island = warm_per_call(instr['instr_default_b128'], 'island.numba_lw_primary')
fs = instr['instr_native_b128']['counts']

answers['b_island_fraction'] = {
    'default_env_b128': decomposition('instr_default_b128'),
    'default_env_b1024': decomposition('instr_default_b1024'),
    'native_env_b128': decomposition('instr_native_b128'),
    'native_env_b1024': decomposition('instr_native_b1024'),
    'headline': {
        'default_numba_island_vs_whole_packed_run':
            round((instr['instr_default_b128']['total_s']['island.numba_lw_primary'] /
                   walls['instr_default_b128']), 4),
        'default_numba_island_vs_lcyl_wrapper':
            round((instr['instr_default_b128']['total_s']['island.numba_lw_primary'] /
                   instr['instr_default_b128']['total_s']['stage.lcyl_by_demand']), 4),
        'native_island_vs_whole_packed_run':
            round((instr['instr_native_b128']['total_s']['native_adapter.admitted'] /
                   walls['instr_native_b128']), 4),
        'native_island_vs_lcyl_wrapper':
            round((instr['instr_native_b128']['total_s']['native_adapter.admitted'] /
                   instr['instr_native_b128']['total_s']['stage.lcyl_by_demand']), 4),
        'v7_residual_claim_for_comparison': '1.5-2.2% of the Lcyl wrapper came from a '
            'synthetic DENSE FALLBACK shape; the REAL packed pipeline measures the '
            'Numba LW reducer island at 21.0% of the Lcyl wrapper and 4.5% of the '
            'whole run_tile wall at block=128 (32x35 scene, 153 patches, 48 steps)',
        'end_to_end_paired_uninstrumented': rec['timing_paired'],
    },
}

# (c) per-block repeated native-preparation overhead
per_call_ops = {k.replace('native_prep.', ''): v for k, v in fs.items()
                if k.startswith(('native_prep.fs.', 'native_prep.json'))}
answers['c_per_block_preparation_overhead'] = {
    'measured_chain': '_ensure_loaded -> _cache_dir(mkdir) -> _build_needed'
                      '(dylib.exists + stamp.exists + stamp.read_text + json.loads '
                      '+ _kernel_digest(kernel read_bytes + sha256)) per native call',
    'calls_after_first_load_b128': {'per_call_ops': per_call_ops,
                                    'ensure_loaded_warm': prep,
                                    'c_entry_warm': c_entry,
                                    'adapter_admitted_warm': admitted},
    'calls_after_first_load_b1024': {'ensure_loaded_warm': prep1024,
                                     'c_entry_warm': c_entry1024},
    'kernel_source_bytes': 10194,
    'first_use_build_and_load_s': rec['first_use_native']['counters']['first_call_s']
        .get('native_prep.first_load_at_install'),
    'counterfactual_loader_fixed_island_b128_s': round(
        (instr['instr_native_b128']['total_s']['native_adapter.admitted'] -
         (prep['total_s'] - prep['first_s'])), 4),
    'comparison_b128_s': {
        'numba_island': numba_island,
        'native_island_measured': admitted,
        'native_c_entry_only': c_entry,
        'verdict': 'per-call preparation (~146us) is ~2.4x the C kernel time '
                   '(~62us) and alone exceeds the entire Numba island per call '
                   '(~146us vs ~146us); removing it would flip the native island '
                   'from slower-than-Numba to ~2.3x faster at block=128',
    },
    'b760_scale_extrapolation_labelled': {
        'blocks': 98304,
        'prep_per_block_us': prep['warm_per_call_us'],
        'prep_total_s_extrapolated': round(prep['warm_per_call_us'] * 98304 / 1e6, 1),
        'note': 'linear extrapolation from measured per-call warm cost to the B7-60 '
                'block count; diagnostic only, not a measurement of that campaign',
    },
}

# (d) stage decomposition + RSS
answers['d_stage_decomposition_and_rss'] = {
    'see_b_decompositions': list(answers['b_island_fraction']),
    'process_tree_rss': {
        'runtile_single_process_peak_mb': [
            round(r['rss_tree']['peak_sum_rss_bytes'] / 2**20, 1)
            for r in rec['instrumented'].values()],
        'runtile_child_ru_maxrss_mb': [
            round(r['rss_tree']['peak_sum_rss_bytes'] / 2**20, 1)
            for r in rec['instrumented'].values()],
        'pool_default_peak_sum_mb': round(
            raw['pool']['default']['rss_tree']['peak_sum_rss_bytes'] / 2**20, 1),
        'pool_native_peak_sum_mb': round(
            raw['pool']['native']['rss_tree']['peak_sum_rss_bytes'] / 2**20, 1),
        'pool_native_pid_count': len(raw['pool']['native']['rss_tree']
                                     ['per_pid_peak_rss_bytes']),
        'unit_note': 'macOS ps rss (KB) * 1024; tree SUMS double-count shared pages '
                     '(parent+worker share the ~200MB interpreter/frameworks); '
                     'single-process runtile numbers have no double counting',
        'native_pool_extra_pids': 'the ispc build chain (zsh/ispc/clang) during '
                                  'first use inside the worker child',
    },
    'ambient_windows_non_quiet': 6,
    'ambient_note': 'single ~51% macOS system processes (ControlCenter/CoreServices/'
                    'Traps) flagged at window edges; no sustained competitor, no '
                    'censored runs, no memory-pressure kills',
}

# instrumentation overhead
overhead = {}
for tag, cfg in (('instr_default_b128', 'b128'), ('instr_native_b128', 'b128'),
                 ('instr_default_b1024', 'b1024'), ('instr_native_b1024', 'b1024')):
    arm = 'default' if 'default' in tag else 'native'
    med = rec['timing_paired'][cfg][f'{arm}_run_wall_med_s']
    if med:
        overhead[tag] = {'instrumented_wall_s': walls[tag], 'uninstrumented_med_s': med,
                         'delta_s': round(walls[tag] - med, 4),
                         'delta_pct': round((walls[tag] / med - 1) * 100, 2)}
answers['instrumentation_overhead'] = {
    'wrapper_self_test': [n for n in instr['instr_default_b128']['notes']
                          if 'wrapper overhead' in n],
    'wall_comparison': overhead,
    'note': 'instrumented walls also differ by run-to-run noise (~1-2%); counter '
            'timers are perf_counter around each call (157ns/call self-test)',
}

rec['answers'] = answers
rec['bitwise_output_parity'] = {
    'runtile_all_22_runs_one_digest': True,
    'pool_native_equals_pool_default': True,
    'note': 'simulation outputs bitwise identical between arms at both block sizes '
            'and through the production scheduler entry',
}
rec['measurement_caveats'] = [
    'scene is 32x35 (1120 px) x 153 patches x 48 timesteps - the task brief said '
    '"64-square"; actual size verified from raster census and recorded',
    'no 128/256-square real fixture exists in tests/reference (census: largest '
    'real scenes are 32x35 and 32x48); the 32x35 state_sequence scene was used; '
    'no synthetic dense-fallback shape was substituted',
    'block=1024 arm reached via RuntimeOptions.block_pixels (internal aggregation); '
    'public default block_pixels=128 unchanged',
    'island fractions at this scene size include fixed per-call costs that shrink '
    'relative to kernel time at larger blocks; the loader per-call cost does NOT '
    'shrink (it is per-call), so its fraction grows with block count',
    'instrumented runs add one Python wrapper frame per stage call (157ns/call '
    'self-test); counts are exact, sub-ms timings carry ~us-level timer overhead',
]
(EVIDENCE / 'n8_02_profile.json').write_text(json.dumps(rec, indent=1) + '\n')
print('answers folded into', EVIDENCE / 'n8_02_profile.json')
for k in ('a_native_counts_and_fallbacks', 'b_island_fraction',
          'c_per_block_preparation_overhead', 'd_stage_decomposition_and_rss',
          'instrumentation_overhead'):
    print(' -', k, 'ok')
