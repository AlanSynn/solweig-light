"""C6-31 parity harness: generates parity_table.md from live runs.

Runs the untouched ground_view._postprocess_block, the statement-by-statement
NumPy replica, the compiled serial kernel, the compiled debug kernel and the
prange variant against the adversarial case suite, and records per-node and
end-to-end bitwise parity plus warning/error parity. Exit code 0 only when
every row is a pass. Timing is NOT claimed here (contended development tier;
see bench_postprocess.py raw records).
"""
import hashlib
import subprocess
import sys
import warnings
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'src'))
sys.path.insert(0, str(REPO / 'tests' / 'optimization_v6' / 'gvf_postprocess'))

import _cases as cases  # noqa: E402
from solweig_light.radiation.ground_view import _postprocess_block  # noqa: E402
from solweig_light.radiation.gvf_postprocess import (  # noqa: E402
    DEBUG_NODES, _postprocess_block_debug, _step_scalar, gvf_postprocess_block)

SIZES = (16, 64, 128)
BUILDERS = cases.ALL_CASES


def run_original(case):
    block = case['block'].copy()
    planes = tuple(block[index] for index in range(16))
    return block, _postprocess_block(planes, case['buildings'], case['facesh'],
                                     case['lup_term'], case['alb_term'], case['nosh_term'],
                                     case['first'], case['second'])


def run_candidate(case, parallel=False):
    block = case['block'].copy()
    return block, gvf_postprocess_block(block, case['buildings'], case['facesh'],
                                        case['lup_term'], case['alb_term'], case['nosh_term'],
                                        case['first'], case['second'], parallel=parallel)


def run_candidate_quiet(case):
    """Candidate with numpy warning state captured inside the module boundary."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        block, outputs = run_candidate(case)
    return block, outputs, caught


def collect_warnings(call):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        call()
    return sorted((type(item).__name__, str(item.message)) for item in caught)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    rows = []
    failures = 0

    for builder in BUILDERS:
        for n in SIZES:
            case = builder(n)
            name = f'{builder.__name__}-{n}'
            original_block, original = run_original(case)
            planes_copy = tuple(case['block'][index].copy() for index in range(16))
            replica, nodes = cases.replica_postprocess(
                planes_copy, case['buildings'], case['facesh'], case['lup_term'],
                case['alb_term'], case['nosh_term'], case['first'], case['second'])

            cand_block, candidate, cand_warnings = run_candidate_quiet(case)
            orig_warnings = collect_warnings(lambda: run_original(case))

            row = {'case': name, 'nodes': {}, 'checks': {}}

            # End-to-end bitwise parity of the five returned fields.
            e2e = all(cases.bits_equal(a, b) for a, b in zip(original, candidate))
            row['checks']['outputs_bitwise'] = e2e
            # All 16 receiver planes after the call (mutations + non-mutation).
            row['checks']['planes16_bitwise'] = all(
                cases.bits_equal(original_block[i], cand_block[i]) for i in range(16))
            row['checks']['planes1_3_5_untouched_elsewhere'] = all(
                cases.bits_equal(cand_block[i], case['block'][i])
                for i in range(16) if i not in cases.MUTATED_PLANES)
            # Replica inventory validity (outputs + mutated planes).
            row['checks']['replica_outputs'] = all(
                cases.bits_equal(a, b) for a, b in zip(original, replica))
            row['checks']['replica_planes'] = all(
                cases.bits_equal(original_block[i], planes_copy[i]) for i in range(16))
            # Warning contract at the module boundary.
            row['checks']['warnings_equal'] = (
                sorted((type(w).__name__, str(w.message)) for w in cand_warnings)
                == orig_warnings)
            expected_warn = case.get('warns')
            if expected_warn == 'none':
                row['checks']['warnings_expected_silent'] = len(cand_warnings) == 0
            elif expected_warn is not None:
                row['checks']['warnings_expected_silent'] = len(cand_warnings) > 0
            else:
                row['checks']['warnings_expected_silent'] = True

            # Per-node parity via the debug kernel (clean steps only; the
            # flagged cases route to the reference and cannot expose kernel
            # internals, but their end-to-end parity is covered above).
            if _step_scalar(case['first']) is not None and _step_scalar(case['second']) is not None:
                kernel_block = case['block'].copy()
                debug = _postprocess_block_debug(
                    kernel_block, case['buildings'], case['facesh'], case['lup_term'],
                    case['alb_term'], case['nosh_term'],
                    float(case['first']), float(case['second']))
                debug_outputs, exported = debug[:5], debug[6]
                row['checks']['debug_outputs_bitwise'] = all(
                    cases.bits_equal(a, b) for a, b in zip(original, debug_outputs))
                for plane, (node, value) in enumerate(zip(DEBUG_NODES, nodes.values())):
                    if node in ('eq_second', 'wallsuninfluence_first', 'wallinfluence_first',
                                'wallsuninfluence_second', 'wallinfluence_second',
                                'keep_mask', 'gvf2_clamp_mask'):
                        expected = value.astype(np.float32)
                    else:
                        expected = np.asarray(value, dtype=np.float32)
                    row['nodes'][node] = cases.bits_equal(exported[plane], expected)
            else:
                row['checks']['debug_outputs_bitwise'] = None
                for node in DEBUG_NODES:
                    row['nodes'][node] = None

            if not all(v for v in row['checks'].values() if v is not None) or \
                    not all(v for v in row['nodes'].values() if v is not None):
                failures += 1
            rows.append(row)

    # Parallel variant bitwise parity.
    par_failures = 0
    for builder in BUILDERS:
        for n in SIZES:
            case = builder(n)
            ob, original = run_original(case)
            cb, candidate = run_candidate(case, parallel=True)
            ok = all(cases.bits_equal(a, b) for a, b in zip(original, candidate)) and \
                all(cases.bits_equal(ob[i], cb[i]) for i in range(16))
            if not ok:
                par_failures += 1

    lines = ['# C6-31 parity table (generated by parity_harness.py)', '',
             'Environment: see commands.txt; all comparisons bitwise via uint32 views',
             '(NaN payloads and signed zeros included).', '',
             '## End-to-end and contract checks per case', '',
             '| case | outputs | planes16 | planes!=1/3/5 pristine | replica out | replica planes | warnings equal | warning expectation | debug outputs |',
             '|---|---|---|---|---|---|---|---|---|']
    for row in rows:
        c = row['checks']
        lines.append('| {case} | {a} | {b} | {c} | {d} | {e} | {f} | {g} | {h} |'.format(
            case=row['case'],
            a=c['outputs_bitwise'], b=c['planes16_bitwise'],
            c=c['planes1_3_5_untouched_elsewhere'], d=c['replica_outputs'],
            e=c['replica_planes'], f=c['warnings_equal'],
            g=c['warnings_expected_silent'], h=c['debug_outputs_bitwise']))

    lines += ['', '## Node-level parity (debug kernel vs NumPy replica, TRUE = bitwise-identical)', '']
    header = '| case | ' + ' | '.join(DEBUG_NODES) + ' |'
    lines += ['|' + '---|' * (len(DEBUG_NODES) + 1), header]
    for row in rows:
        cells = ' | '.join('n/a' if v is None else ('TRUE' if v else 'FALSE')
                           for v in row['nodes'].values())
        lines.append(f"| {row['case']} | {cells} |")

    lines += ['', '## Parallel (prange) variant', '',
              f'Bitwise parity vs original on all {len(BUILDERS) * len(SIZES)} cases: '
              + ('PASS' if par_failures == 0 else f'FAIL ({par_failures})'), '']
    if failures == 0 and par_failures == 0:
        lines += ['**Overall: PASS** (all rows bitwise-equal, warning contract equal)']
    else:
        lines += [f'**Overall: FAIL** end-to-end/node failures={failures} parallel={par_failures}']

    out = Path(__file__).parent / 'parity_table.md'
    out.write_text('\n'.join(lines) + '\n')
    print(f'wrote {out}')
    return 0 if failures == 0 and par_failures == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
