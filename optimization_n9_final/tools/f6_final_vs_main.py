#SOLWEIG-GPU: GPU-accelerated SOLWEIG model for urban thermal comfort simulation
#Copyright (C) 2022–2025 Harsh Kamath and Naveen Sudharsan

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
"""N9-F6 FINAL vs pinned-main compact comparison (performance_owner).

Cells: the F3 frozen set (B=1024 primary, B=128 secondary x mixes
all-binary/mix/all-raw) driven through EACH tree's own production
longwave seam at the shipped defaults (threads_per_worker=1 asserted,
block_pixels bound per cell, env unset):

* FINAL tree (this worktree, F4-landed): pipeline demand -> primary
  reduction -> structural route consult -> bounded stream at pinned
  budget 1 (admitted) or the legacy serial kernels (declined).
* MAIN tree (/Users/alansynn/Workspace/n9-main-ref @ pinned SHA): the
  compiled public path with parallel = threads_per_worker > 1 (False at
  the default) -- the pre-N9 product behavior.

Because the trees share one package name, each sample comes from a
separate worker process (f6_worker.py); pairing is by rep: REPS=9
alternating tree order (interleaved per rep, never tree-major). ONE
clock per cell per rep, after an untimed warm pass inside the same
worker. Same budget: both trees get the identical thread environment
(numba threads N=4; the FINAL stream leaf's prange owns them, MAIN's
serial kernels use one -- each tree's shipped-default behavior).

Gates (recorded transparently; amendment-2 discipline):
* Launch at the FIRST 1-min loadavg reading < 10.0 with the memory view
  >= 92,000 pages; the actual start load is recorded prominently; any
  timed-rep annotation > 1.6x the actual start load invalidates the
  session (censored raw retained, no renegotiated window).
* Pre-committed threads_per_worker=1 rule (engine.py, recorded pre-F6):
  if the stream LOSES a stream-carried cell (FINAL median slower than
  MAIN median where the route admits), the plain-boolean engine
  restoration is triggered and the manifest records it.
* Declined cells (raw): FINAL/MAIN median <= 1.03 (inherited default
  regression bound; the declined path is the same serial kernel plus
  one consult).
* Cold-start (release-owner 4.5): FINAL cold / MAIN cold <= 1.03 on the
  primary cell, fresh JIT caches both sides.
* Parity: Ldown+Lside bitwise (uint32 sha256) FINAL == MAIN on every
  cell, every rep. A mismatch is reported, never silently accepted.
* Amendment-2 marginality: any winning margin within 2x the observed
  per-pair spread is labeled MARGINAL, not a clear pass.

Usage:
  f6_final_vs_main.py --check-only   # pre-flight: guards, route audit, parity
  f6_final_vs_main.py --timed        # gate -> cold phase -> 9 paired reps
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
N9_DIR = _REPO / 'optimization_n9_final'
EVIDENCE = N9_DIR / 'evidence'
TOOLS = N9_DIR / 'tools'
WORKER = TOOLS / 'f6_worker.py'
FINAL_SRC = _REPO / 'src'
MAIN_WORKTREE = Path('/Users/alansynn/Workspace/n9-main-ref')
MAIN_SRC = MAIN_WORKTREE / 'src'

REPS = 9
COLD_SAMPLES = 3                  # paired cold full-entry samples per tree
THREADS = 4                       # one budget for the whole session
LOAD_START_MAX = 10.0             # amendment-2 launch threshold
MIN_AVAIL_PAGES = 92_000
COLD_REGRESSION_BOUND = 1.03      # inherited <=3% (release-owner 4.5)
DECLINED_REGRESSION_BOUND = 1.03  # inherited default regression bound
CELLS = ((1024, 'all-binary'), (1024, 'mix'), (1024, 'all-raw'),
         (128, 'all-binary'), (128, 'mix'), (128, 'all-raw'))
PRIMARY = (1024, 'mix')


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def _git(*args: str, cwd: Path = _REPO) -> str:
    return subprocess.run(['git', *args], cwd=cwd, capture_output=True,
                          text=True, check=True).stdout.strip()


def loadavg() -> tuple[float, float, float]:
    return os.getloadavg()


def memory_view() -> dict:
    out = subprocess.run(['/usr/bin/vm_stat'], capture_output=True,
                         text=True).stdout
    pages: dict[str, int] = {}
    page_size = 16384
    for line in out.splitlines():
        if 'page size of' in line:
            page_size = int(line.split('page size of')[1].split()[0])
        if ':' in line:
            key, value = line.split(':', 1)
            value = value.strip().rstrip('.').strip()
            if value.isdigit():
                pages[key.strip()] = int(value)
    free = pages.get('Pages free', 0)
    inactive = pages.get('Pages inactive', 0)
    speculative = pages.get('Pages speculative', 0)
    return {'page_size': page_size, 'pages_available': free + inactive
            + speculative}


def admitted_processes() -> list[str]:
    out = subprocess.run(['/bin/ps', '-eo', 'pcpu,comm'], capture_output=True,
                         text=True).stdout.splitlines()[1:]
    return sorted({line.split(None, 1)[1].strip().rsplit('/', 1)[-1]
                   for line in out if line.strip()
                   and float(line.split(None, 1)[0] or 0) > 50.0})


def window_gate() -> tuple[bool, dict]:
    """Amendment-2 launch gate: first sub-10 reading, memory view, no wait."""
    snapshot = {'loadavg': list(loadavg()), 'memory': memory_view(),
                'at_utc': _now_utc()}
    ok = (snapshot['loadavg'][0] < LOAD_START_MAX
          and snapshot['memory']['pages_available'] >= MIN_AVAIL_PAGES)
    snapshot['gate'] = 'pass' if ok else 'FAIL'
    snapshot['rule'] = (f'1-min loadavg < {LOAD_START_MAX} (amendment-2) '
                        f'AND available >= {MIN_AVAIL_PAGES} pages')
    return ok, snapshot


FIXTURE_DATA = EVIDENCE / 'f6_fixture_data.npz'


def _prepare_fixture_data() -> Path:
    """Generate the adversarial lup pools ONCE under the FINAL tree.

    The provenance generator (tests/optimization_v8/reference) imports
    ``radiation.cylinder_longwave`` at module scope, which only exists in
    the FINAL tree -- so the pools are generated there, saved as pure
    numpy data, and loaded tree-independently by both workers.
    """
    if FIXTURE_DATA.exists():
        return FIXTURE_DATA
    env = dict(os.environ)
    env.pop('NUMBA_CACHE_DIR', None)
    env.pop('PYTHONPATH', None)
    cmd = [sys.executable, str(WORKER), '--tree', 'final',
           '--root', str(FINAL_SRC), '--cache-dir',
           str(_REPO / '.numba_cache' / 'f6prep'),
           '--mode', 'check', '--out', str(EVIDENCE / '_f6_prep_unused.json'),
           '--threads', str(THREADS), '--dump-fixture-data',
           str(FIXTURE_DATA)]
    proc = subprocess.run(cmd, env=env, cwd=str(_REPO), capture_output=True,
                          text=True, timeout=600)
    if proc.returncode != 0 or not FIXTURE_DATA.exists():
        fail = {'step': 'fixture-data prep', 'returncode': proc.returncode,
                'stderr': proc.stderr[-4000:], 'utc': _now_utc()}
        path = EVIDENCE / f'f6_prep_error_{_stamp()}.json'
        path.write_text(json.dumps(fail, indent=1))
        raise RuntimeError(f'fixture-data prep failed; archived {path}')
    return FIXTURE_DATA


def _spawn(tree: str, mode: str, cache_dir: Path, sha: str) -> dict:
    out = EVIDENCE / f'_f6_{tree}_{mode}_{_stamp()}.json.tmp'
    env = dict(os.environ)
    env.pop('NUMBA_CACHE_DIR', None)     # worker pins it from --cache-dir
    env.pop('PYTHONPATH', None)
    root = str(FINAL_SRC if tree == 'final' else MAIN_SRC)
    cmd = [sys.executable, str(WORKER), '--tree', tree, '--root', root,
           '--cache-dir', str(cache_dir), '--mode', mode,
           '--out', str(out), '--threads', str(THREADS), '--sha', sha,
           '--fixture-data', str(FIXTURE_DATA)]
    proc = subprocess.run(cmd, env=env, cwd=str(_REPO), capture_output=True,
                          text=True, timeout=1200)
    if proc.returncode != 0 or not out.exists():
        fail = {'tree': tree, 'mode': mode, 'cmd': cmd, 'returncode':
                proc.returncode, 'stderr': proc.stderr[-4000:],
                'stdout': proc.stdout[-2000:], 'utc': _now_utc()}
        path = EVIDENCE / f'f6_worker_error_{tree}_{mode}_{_stamp()}.json'
        path.write_text(json.dumps(fail, indent=1))
        raise RuntimeError(f'worker {tree}/{mode} failed; archived {path}')
    with open(out) as f:
        record = json.load(f)
    out.unlink()
    return record


def _archives(record: dict, kind: str) -> Path:
    path = EVIDENCE / f'f6_final_vs_main_{kind}_{_stamp()}.json'
    path.write_text(json.dumps(record, indent=1, sort_keys=True))
    return path


def run_check_only() -> int:
    fixture = _prepare_fixture_data()
    print(f'[F6] fixture data: {fixture}', file=sys.stderr)
    shas = {'final': _git('rev-parse', 'HEAD'),
            'main': _git('rev-parse', 'HEAD', cwd=MAIN_WORKTREE)}
    check_cache = _REPO / '.numba_cache' / 'f6check'
    records = {}
    for tree in ('final', 'main'):
        cache = check_cache / tree
        cache.mkdir(parents=True, exist_ok=True)
        records[tree] = _spawn(tree, 'check', cache, shas[tree])
    report = {'utc': _now_utc(), 'shas': shas,
              'guards': {t: records[t]['fast_path_guards']
                         for t in records},
              'route_audit_final': records['final'].get('route_audit'),
              'route_audit_main': records['main'].get('route_audit'),
              'parity': {}, 'digests': {}}
    ok = True
    for key in (f'B={b} {m}' for b, m in CELLS):
        df = records['final']['results'][key]['digest']
        dm = records['main']['results'][key]['digest']
        report['digests'][key] = {'final': df, 'main': dm}
        report['parity'][key] = (df == dm)
        ok = ok and df == dm
    report['parity_all_bitwise'] = ok
    path = EVIDENCE / f'f6_final_vs_main_check_{_stamp()}.json'
    path.write_text(json.dumps(report, indent=1, sort_keys=True))
    print(json.dumps(report, indent=1, sort_keys=True))
    print(f'[F6] check archive: {path}', file=sys.stderr)
    return 0 if ok else 3


def run_timed() -> int:
    _prepare_fixture_data()
    shas = {'final': _git('rev-parse', 'HEAD'),
            'main': _git('rev-parse', 'HEAD', cwd=MAIN_WORKTREE)}
    session: dict = {
        'record': 'N9-F6 FINAL vs pinned-main compact comparison',
        'protocol': ('amendment-2 launch discipline; per-pair ratios are '
                     'the verdict basis; marginality within 2x spread'),
        'utc': _now_utc(), 'shas': shas, 'reps': REPS, 'threads': THREADS,
        'cells': [f'B={b} {m}' for b, m in CELLS],
        'primary_cell': f'B={PRIMARY[0]} {PRIMARY[1]}',
        'measurement_notes': [
            'run 1 (f6_final_vs_main_timed_20260923T170156Z.json) is '
            'INVALID for the MAIN warm cells: its worker performed no '
            'untimed warm pass before the clock, so MAIN\'s first timed '
            'cell paid JIT disk-cache load inside the measurement. FINAL '
            'warm cells were unaffected (route audit doubled as warm-up). '
            'Run 1 raw retained; this record is authoritative.']}

    # ---- amendment-2 launch gate: FIRST sub-10 reading, no settle wait ---
    ok, start = window_gate()
    session['start_snapshot'] = start
    session['actual_start_loadavg_1m'] = start['loadavg'][0]
    if not ok:
        session['status'] = 'WINDOW_GATE_REFUSED (amendment-2; no re-window)'
        path = _archives(session, 'gaterefused')
        print(f'[F6] gate REFUSED {start}; archived {path}', file=sys.stderr)
        return 2
    censor_bound = round(1.6 * start['loadavg'][0], 3)
    session['censor_bound_1p6x_start'] = censor_bound
    print(f'[F6] gate pass: start load1={start["loadavg"][0]:.2f} '
          f'censor>{censor_bound} mem={start["memory"]["pages_available"]}p',
          file=sys.stderr)

    # ---- cold phase: COLD_SAMPLES fresh JIT caches per tree, paired -------
    # "cold full-entry guard within the 3% paired bound" (n8_03_protocol):
    # each sample is a genuine first use under a brand-new cache dir; tree
    # order alternates per sample so compile-time load trends hit both.
    stamp = _stamp()
    cold_cache_root = _REPO / '.numba_cache' / f'f6_{stamp}'
    cold_key = f'B={PRIMARY[0]} {PRIMARY[1]}'
    cold_ms: dict[str, list] = {'final': [], 'main': []}
    cold_diag: dict[str, dict] = {}
    cold_raw: list[dict] = []
    for sample in range(COLD_SAMPLES):
        order = ('final', 'main') if sample % 2 == 0 else ('main', 'final')
        for tree in order:
            cache = cold_cache_root / f'cold{sample}' / tree
            cache.mkdir(parents=True, exist_ok=True)
            rec = _spawn(tree, 'cold', cache, shas[tree])
            r = rec['results'][cold_key]
            cold_ms[tree].append(r['cold_ms'])
            cold_diag.setdefault(tree, r)
            cold_raw.append({'sample': sample, 'tree': tree,
                             'cold_ms': r['cold_ms'], 'warm_ms': r['warm_ms'],
                             'loadavg_1m_after': r['loadavg_1m_after']})
    session['cold_phase'] = {'samples': cold_raw, 'cell': cold_key}
    final_cold = {'cold_ms': statistics.median(cold_ms['final']),
                  'warm_ms': cold_diag['final']['warm_ms'],
                  'samples': cold_ms['final']}
    main_cold = {'cold_ms': statistics.median(cold_ms['main']),
                 'warm_ms': cold_diag['main']['warm_ms'],
                 'samples': cold_ms['main']}
    cold_ratio = final_cold['cold_ms'] / main_cold['cold_ms']
    cold_pairs = [f / m for f, m in zip(cold_ms['final'], cold_ms['main'])]
    session['cold_pair_ratios'] = [round(x, 4) for x in cold_pairs]
    session['cold_pair_spread'] = round(max(cold_pairs) - min(cold_pairs), 4)

    # ---- warm campaign: REPS paired alternating, never tree-major --------
    samples = {f'B={b} {m}': {'final': [], 'main': []} for b, m in CELLS}
    audits: dict[str, bool] = {}
    digest_pairs: list[dict] = []
    loads: list[dict] = []
    censored: list[dict] = []
    for rep in range(REPS):
        order = ('final', 'main') if rep % 2 == 0 else ('main', 'final')
        rep_records = {}
        for tree in order:
            rep_records[tree] = _spawn(
                tree, 'warm',
                cold_cache_root / f'cold{COLD_SAMPLES - 1}' / tree,
                shas[tree])
        pair_max = max(rep_records[t]['results']
                       [f'B={b} {m}']['loadavg_1m_after']
                       for t in rep_records for b, m in CELLS)
        entry = {'rep': rep, 'order': list(order), 'loadavg_1m_max': pair_max}
        loads.append(entry)
        if pair_max > censor_bound:
            censored.append(entry)
            print(f'[F6] rep {rep}: loadavg {pair_max} > {censor_bound} '
                  '-- SESSION CENSORED (amendment-2)', file=sys.stderr)
            break
        audit = rep_records['final'].get('route_audit')
        if rep == 0:
            for key in (f'B={b} {m}' for b, m in CELLS):
                audits[key] = audit.get(key)
        elif any(audits[key] != audit.get(key)
                 for key in audits):
            censored.append({'rep': rep, 'error': 'route audit drift'})
            break
        digest_pairs.append(
            {f'B={b} {m}': {
                'final': rep_records['final']['results']
                [f'B={b} {m}']['digest'],
                'main': rep_records['main']['results']
                [f'B={b} {m}']['digest']}
                for b, m in CELLS})
        for key in (f'B={b} {m}' for b, m in CELLS):
            for tree in ('final', 'main'):
                samples[key][tree].append(
                    rep_records[tree]['results'][key]['ms'])
        print(f'[F6] rep {rep + 1}/{REPS} done (load1 max {pair_max})',
              file=sys.stderr)

    session['rep_load_annotations'] = loads
    session['censored_records'] = censored
    session['end_snapshot'] = {
        'loadavg': list(loadavg()), 'memory': memory_view(),
        'admitted_busy_processes': admitted_processes(), 'at_utc': _now_utc()}

    session['samples_ms'] = samples
    session['route_audit_final'] = audits
    session['digest_pairs_by_rep'] = digest_pairs
    last = digest_pairs[-1] if digest_pairs else {}
    session['parity_per_cell'] = {
        key: {'final': pair['final'], 'main': pair['main'],
              'bitwise_equal': pair['final'] == pair['main'],
              'equal_all_reps': all(dp[key]['final'] == pair['final']
                                    and dp[key]['main'] == pair['main']
                                    for dp in digest_pairs)}
        for key, pair in last.items()}
    session['cold_ratio_final_over_main'] = round(cold_ratio, 4)

    session['verdict'] = _gate_math(session, samples, audits, cold_ratio,
                                    final_cold, main_cold, censored)
    raw_path = EVIDENCE / f'f6_final_vs_main_timed_{_stamp()}.json'
    raw_path.write_text(json.dumps(session, indent=1, sort_keys=True))
    verdict_path = EVIDENCE / 'f6_verdict.json'
    verdict_path.write_text(json.dumps(session['verdict'], indent=1,
                                       sort_keys=True))
    print(json.dumps(session['verdict'], indent=1, sort_keys=True))
    print(f'[F6] raw archive: {raw_path}\n[F6] verdict: {verdict_path}',
          file=sys.stderr)
    return 0


def _gate_math(session: dict, samples: dict, audits: dict, cold_ratio:
               float, final_cold: dict, main_cold: dict,
               censored: list) -> dict:
    verdict: dict = {'record': 'N9-F6 verdict: shipped FINAL default vs '
                     'pinned main at shipped defaults (tw=1)',
                     'recorded_utc': _now_utc(),
                     'shas': session['shas'],
                     'verdict_basis': 'per-pair ratios (median of paired '
                     'per-rep MAIN/FINAL ratios), median-of-times '
                     'ratios reported alongside'}
    if censored:
        verdict['terminal_label'] = 'UNQUALIFIED_BY_ENVIRONMENT'
        verdict['note'] = ('a timed-rep annotation exceeded 1.6x the actual '
                           'start load; censored raw retained (amendment-2 '
                           'is terminal, no renegotiated window)')
        return verdict
    parity_bad = [k for k, v in session['parity_per_cell'].items()
                  if not v['bitwise_equal']]
    verdict['parity'] = ('Ldown+Lside bitwise (uint32 sha256) FINAL == MAIN '
                         'on all 6 cells'
                         if not parity_bad else f'BITWISE MISMATCH: {parity_bad}')
    cells_out = {}
    triggered = []
    marginal = []
    declined_regression = 0.0
    geomean_carried = 1.0
    n_carried = 0
    for key, times in samples.items():
        f_ms, m_ms = times['final'], times['main']
        pairs = [m / f for m, f in zip(m_ms, f_ms)]
        med_ratio = statistics.median(pairs)
        spread = max(pairs) - min(pairs)
        med_of_times = (statistics.median(m_ms)
                        / statistics.median(f_ms))
        carried = audits.get(key) is True
        entry = {
            'final_median_ms': round(statistics.median(f_ms), 4),
            'main_median_ms': round(statistics.median(m_ms), 4),
            'speedup_main_over_final_median_of_times': round(med_of_times, 4),
            'per_pair_ratio_median': round(med_ratio, 4),
            'per_pair_spread': round(spread, 4),
            'stream_carried': carried,
            'min_pair': round(min(pairs), 4),
            'max_pair': round(max(pairs), 4),
        }
        if carried:
            if med_ratio < 1.0:
                triggered.append(key)
            else:
                margin = med_ratio - 1.0
                if margin <= 2 * spread:
                    marginal.append(key)
                geomean_carried *= med_of_times
                n_carried += 1
        else:
            # Declined cells: judged on the DECLARED verdict basis (per-pair
            # ratios, FINAL/MAIN), same as every other gate. The
            # median-of-times ratio is reported alongside for completeness
            # (on the short 128-raw cell the two statistics disagree in
            # sign; the spread dwarfs both).
            declined_pairs = [f / m for f, m in zip(f_ms, m_ms)]
            regression = statistics.median(declined_pairs)
            declined_regression = max(declined_regression, regression)
            entry['declined_regression_ratio_per_pair_median'] = round(
                regression, 4)
            entry['declined_regression_margin_vs_2x_spread'] = round(
                2 * spread - abs(regression - 1.0), 4)
        cells_out[key] = entry
    verdict['cells'] = cells_out
    cold_pairs = session.get('cold_pair_ratios', [round(cold_ratio, 4)])
    cold_spread = session.get('cold_pair_spread', 0.0)
    cold_med = statistics.median(cold_pairs)
    cold_ok = cold_med <= COLD_REGRESSION_BOUND
    cold_marginal = cold_ok and (COLD_REGRESSION_BOUND - cold_med) <= 2 * cold_spread
    verdict['cold'] = {
        'cell': f'B={PRIMARY[0]} {PRIMARY[1]}',
        'metric': 'cold full-entry (fresh JIT cache per sample), paired',
        'samples_final_ms': final_cold['samples'],
        'samples_main_ms': main_cold['samples'],
        'final_cold_median_ms': round(final_cold['cold_ms'], 4),
        'main_cold_median_ms': round(main_cold['cold_ms'], 4),
        'final_over_main_median': round(cold_med, 4),
        'per_sample_ratios': cold_pairs,
        'per_sample_spread': cold_spread,
        'bound': COLD_REGRESSION_BOUND,
        'label': 'MARGINAL' if cold_marginal else
                 ('PASS' if cold_ok else 'FAIL (> 3% paired bound)'),
        'final_cold_over_final_warm': round(
            final_cold['cold_ms'] / final_cold['warm_ms'], 4),
        'main_cold_over_main_warm': round(
            main_cold['cold_ms'] / main_cold['warm_ms'], 4)}
    if n_carried:
        verdict['geomean_speedup_carried_median_of_times'] = round(
            geomean_carried ** (1 / n_carried), 4)
    verdict['plain_boolean_restoration'] = (
        f'TRIGGERED on {sorted(triggered)} (pre-committed engine.py rule: '
        'stream loses its carried cell at threads_per_worker=1)'
        if triggered else
        'NOT_TRIGGERED (stream wins its carried cells at budget 1)')
    verdict['marginal_labels'] = ([f'{k}: winning margin within 2x per-pair '
                                   'spread -> MARGINAL, not a clear pass'
                                   for k in marginal] or 'none')
    verdict['declined_cells_max_regression_ratio'] = round(
        declined_regression, 4)
    declined_ok = declined_regression <= DECLINED_REGRESSION_BOUND
    verdict['gates'] = {
        'parity_bitwise_all_cells': not parity_bad,
        'cold_within_3pct': cold_ok,
        'cold_marginal': cold_marginal,
        'declined_within_3pct': declined_ok,
        'pre_committed_rule_triggered': bool(triggered),
    }
    if parity_bad:
        verdict['terminal_label'] = 'PARITY_FAILURE'
        verdict['note'] = ('bitwise FINAL vs MAIN divergence measured; do '
                           'not ship on this record; investigate before '
                           'any promotion claim')
    elif triggered:
        verdict['terminal_label'] = 'PLAIN_BOOLEAN_RESTORATION_TRIGGERED'
    elif cold_ok and declined_ok:
        verdict['terminal_label'] = 'SHIPPED_ROUTE_CONFIRMED'
    else:
        verdict['terminal_label'] = 'GATE_FAILURE'
        verdict['note'] = ('cold or declined-cell regression beyond the '
                           'inherited 3% bound; see gates')
    return verdict


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--check-only', action='store_true')
    ap.add_argument('--timed', action='store_true')
    ap.add_argument('--recompute', metavar='RAW_JSON',
                    help='replay gate math from a raw timed archive '
                         '(no measurement)')
    args = ap.parse_args()
    if args.check_only:
        return run_check_only()
    if args.timed:
        return run_timed()
    if args.recompute:
        with open(args.recompute) as f:
            session = json.load(f)
        cold_by_tree: dict[str, list] = {'final': [], 'main': []}
        warm_by_tree: dict[str, list] = {'final': [], 'main': []}
        for s in session['cold_phase']['samples']:
            cold_by_tree[s['tree']].append(s['cold_ms'])
            warm_by_tree[s['tree']].append(s['warm_ms'])
        cold_key = session['cold_phase']['cell']
        # warm diagnostic per tree: the sample-0 warm re-timing
        warm_diag = {t: warm_by_tree[t][0] for t in cold_by_tree}
        final_cold = {'cold_ms': statistics.median(cold_by_tree['final']),
                      'warm_ms': warm_diag['final'],
                      'samples': cold_by_tree['final']}
        main_cold = {'cold_ms': statistics.median(cold_by_tree['main']),
                     'warm_ms': warm_diag['main'],
                     'samples': cold_by_tree['main']}
        cold_ratio = final_cold['cold_ms'] / main_cold['cold_ms']
        verdict = _gate_math(session, session['samples_ms'],
                             session['route_audit_final'], cold_ratio,
                             final_cold, main_cold,
                             session['censored_records'])
        verdict['derivation'] = (
            f'gate math replayed from raw archive {args.recompute} without '
            're-measurement; declined-cell gate aligned to the declared '
            'per-pair verdict basis')
        verdict['measurement_notes'] = session.get('measurement_notes', [])
        Path(EVIDENCE / 'f6_verdict.json').write_text(
            json.dumps(verdict, indent=1, sort_keys=True))
        print(json.dumps(verdict, indent=1, sort_keys=True))
        return 0
    ap.error('one of --check-only / --timed / --recompute is required')


if __name__ == '__main__':
    raise SystemExit(main())
