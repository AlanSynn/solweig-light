#!/usr/bin/env python3
"""N8-02 orchestrator: paired packed-pipeline measurement campaign.

Sequence (fresh child process per run; exclusive benchmark windows):
  0. preflight: fixture identity/hashes, scene-size survey (answers the
     "128/256-square real fixture?" question), host facts, ambient load
  1. warmup default child (populates the shared NUMBA_CACHE_DIR)
  2. first-use native child (FRESH scratch native cache; build cost lands
     inside this run; instrumented) -> workflow_first_use evidence
  3. instrumented children {default, native} x {block 128, block 1024}
     -> counts, fallback reasons, stage decomposition, prep-op counts
  4. uninstrumented paired timing reps, alternating arms
     (block 128: 5 pairs; block 1024: 3 pairs) with process-tree RSS
     sampling (ps rss KB; shared pages double-count when summed - reported
     as such, never as admission)
  5. production-entry pool arms (run_utci_tiles), default + native, each
     against a FRESH scratch native cache: filesystem proof whether worker
     children touch the native path under each env

Writes evidence/profile/n8_02_profile.json (bounded terminal record) and
evidence/profile/raw/n8_02_*.json per run.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PYTHON = str(REPO / '.venv' / 'bin' / 'python')
CHILD = HERE / 'n8_02_child.py'
SITE = str(REPO / 'src')
EVIDENCE = REPO / 'optimization_v8_native_default' / 'evidence' / 'profile'
RAW = EVIDENCE / 'raw'
RUNS = EVIDENCE / 'runs'

SCENE = REPO / 'tests/reference/state_sequence_original_cpu/scene'
PREPARED = SCENE / 'processed_inputs'
WORK_ROOT = EVIDENCE / 'work'

THREADS = 4
CPU_BUDGET = 4
PAIRS_B128 = 5
PAIRS_B1024 = 3


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def ambient() -> dict:
    load = list(os.getloadavg())
    rows = subprocess.run(['ps', '-eo', 'pcpu,comm'], capture_output=True,
                          text=True, timeout=10).stdout.splitlines()[1:]
    heavy = []
    for row in rows:
        parts = row.strip().split(None, 1)
        if len(parts) == 2:
            try:
                pcpu = float(parts[0])
            except ValueError:
                continue
            if pcpu >= 50 and not any(k in parts[1] for k in
                                      ('Chrome', 'WindowServer', 'Google', 'Claude')):
                heavy.append({'pcpu': pcpu, 'comm': parts[1][:60]})
    return {'loadavg': [round(x, 2) for x in load], 'busy_non_browser': heavy[:6],
            'quiet': not heavy}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RSSTreeSampler(threading.Thread):
    """Sample child process-tree RSS via ps (KB -> bytes)."""

    def __init__(self, root_pid: int, interval_s: float = 0.15):
        super().__init__(daemon=True)
        self.root_pid = root_pid
        self.interval_s = interval_s
        self.stop_flag = threading.Event()
        self.samples = []
        self.per_pid_peak = {}
        self.errors = 0

    def _snapshot(self):
        rows = subprocess.run(['ps', '-eo', 'pid,ppid,rss,comm'],
                              capture_output=True, text=True, timeout=5).stdout
        table = {}
        for line in rows.splitlines()[1:]:
            parts = line.strip().split(None, 3)
            if len(parts) == 4:
                try:
                    table[int(parts[0])] = (int(parts[1]), int(parts[2]) * 1024,
                                            parts[3][:40])
                except ValueError:
                    continue
        if self.root_pid not in table:
            return
        stack, tree = [self.root_pid], []
        while stack:
            pid = stack.pop()
            if pid in tree:
                continue
            entry = table.get(pid)
            if entry is None:
                continue
            tree.append(pid)
            self.per_pid_peak[pid] = max(self.per_pid_peak.get(pid, 0), entry[1])
            stack.extend(child for child, (ppid, _, _) in table.items() if ppid == pid)
        total = sum(table[pid][1] for pid in tree)
        self.samples.append({'t': round(time.monotonic(), 3), 'n_proc': len(tree),
                             'sum_rss_bytes': total})

    def run(self):
        while not self.stop_flag.is_set():
            try:
                self._snapshot()
            except Exception:
                self.errors += 1
            self.stop_flag.wait(self.interval_s)

    def finish(self):
        self.stop_flag.set()
        self.join(timeout=2.0)
        sums = [s['sum_rss_bytes'] for s in self.samples] or [0]
        return {'sample_count': len(self.samples), 'errors': self.errors,
                'peak_sum_rss_bytes': max(sums),
                'mean_sum_rss_bytes': round(sum(sums) / len(sums)),
                'per_pid_peak_rss_bytes': {str(k): v for k, v in
                                           sorted(self.per_pid_peak.items())},
                'unit': 'bytes (macOS ps rss KB * 1024)',
                'double_count_note': 'sum over the process tree counts shared '
                                     'pages once per process; peak_sum is an '
                                     'upper bound, never an admission number'}


def run_child(tag: str, *, backend: str, block: int, instrument: bool,
              entry: str = 'runtile', native_cache: str | None = None,
              timeout_s: int = 1800) -> dict:
    out = RAW / f'n8_02_{tag}.json'
    run_root = RUNS / tag
    run_root.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    for name in ('BLIS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMBA_NUM_THREADS',
                 'NUMEXPR_NUM_THREADS', 'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
                 'VECLIB_MAXIMUM_THREADS'):
        env[name] = str(THREADS)
    env['NUMBA_CACHE_DIR'] = str(WORK_ROOT / 'numba_cache')
    env.pop('SOLWEIG_LIGHT_LW_BACKEND', None)
    env.pop('SOLWEIG_LIGHT_FUSED_RAD', None)
    env.pop('SOLWEIG_LIGHT_PATCH_CLASS_TABLES', None)
    env.pop('SOLWEIG_LIGHT_NATIVE_CACHE', None)
    if backend == 'native':
        env['SOLWEIG_LIGHT_LW_BACKEND'] = 'native'
    if native_cache:
        env['SOLWEIG_LIGHT_NATIVE_CACHE'] = native_cache
    cmd = [PYTHON, str(CHILD), '--site', SITE, '--prepared', str(PREPARED),
           '--backend', backend, '--block-pixels', str(block),
           '--threads', str(THREADS), '--cpu-budget', str(CPU_BUDGET),
           '--instrument', str(int(instrument)), '--entry', entry,
           '--run-root', str(run_root), '--out', str(out)]
    before = ambient()
    t0 = time.monotonic()
    proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True)
    sampler = RSSTreeSampler(proc.pid)
    sampler.start()
    stdout, stderr = proc.communicate(timeout=timeout_s)
    wall_s = time.monotonic() - t0
    rss = sampler.finish()
    after = ambient()
    entry_rec = {'tag': tag, 'backend': backend, 'block': block,
                 'instrument': instrument, 'entry': entry,
                 'returncode': proc.returncode, 'parent_wall_s': round(wall_s, 3),
                 'ambient_before': before, 'ambient_after': after,
                 'rss_tree': rss, 'native_cache_used': native_cache or 'default-user-cache',
                 'stdout_tail': stdout[-400:], 'stderr_tail': stderr[-1500:]}
    if proc.returncode == 0 and out.exists():
        entry_rec['child'] = json.loads(out.read_text())
        counters = Path(out).with_suffix('.counters.json')
        if counters.exists():
            entry_rec['counters'] = json.loads(counters.read_text())
    return entry_rec


def native_cache_state(cache: Path) -> dict:
    return {'exists': cache.exists(),
            'dylibs': sorted(p.name for p in cache.glob('*.dylib')) if cache.exists() else [],
            'build_stamp': json.loads((cache / 'build_stamp.json').read_text())
            if (cache / 'build_stamp.json').exists() else None}


def med(values):
    ordered = sorted(values)
    n = len(ordered)
    return ordered[n // 2] if n % 2 else (ordered[n // 2 - 1] + ordered[n // 2]) / 2


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    WORK_ROOT.mkdir(parents=True, exist_ok=True)

    started = now_utc()
    print(f'[{started}] preflight', flush=True)
    fixture_files = {}
    for name in ('Building_DSM.tif', 'DEM.tif', 'Trees.tif', 'met.txt', 'manifest.json'):
        path = SCENE / name
        fixture_files[name] = sha256_file(path)
    prepared_hashes = {}
    for folder in sorted(PREPARED.iterdir()):
        for path in sorted(folder.rglob('*')):
            if path.is_file():
                prepared_hashes[str(path.relative_to(PREPARED))] = sha256_file(path)

    host = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string', 'hw.memsize'],
                          capture_output=True, text=True).stdout.strip().split('\n')
    user_cache = Path.home() / '.cache' / 'solweig-light' / 'native'

    try:
        from osgeo import gdal as _gdal
        sizes = {}
        for path in sorted((REPO / 'tests/reference').rglob('*.tif')):
            rel = str(path.relative_to(REPO))
            if '.solweig-light' in rel or 'output_folder' in rel:
                continue
            dataset = _gdal.Open(str(path), _gdal.GA_ReadOnly)
            if dataset is None:
                continue
            key = (dataset.RasterYSize, dataset.RasterXSize)
            sizes.setdefault(key, []).append(rel)
            dataset = None
        largest = max(sizes, key=lambda k: min(k))
        survey = {
            'distinct_sizes': {f'{r}x{c}': len(v) for (r, c), v in sorted(sizes.items())},
            'largest_square_min_side': min(largest),
            'largest_examples': sizes[largest][:4],
            'exists_128_or_256_square_real_fixture': any(min(k) >= 128 for k in sizes),
            'note': 'census over real reference TIFFs only (no synthetic scenes)',
        }
    except Exception as error:
        survey = {'error': f'{type(error).__name__}: {error}'}

    protocol = {
        'host': {'cpu': host[0] if host else '', 'memsize_bytes': int(host[1]) if len(host) > 1 else None,
                 'python': PYTHON},
        'scene': {'dir': str(SCENE), 'fixture_files_sha256': fixture_files,
                  'prepared_files_sha256_count': len(prepared_hashes),
                  'prepared_digest': hashlib.sha256(json.dumps(
                      prepared_hashes, sort_keys=True).encode()).hexdigest()[:16]},
        'scene_survey': survey,
        'threads': THREADS, 'cpu_budget': CPU_BUDGET,
        'pairs_b128': PAIRS_B128, 'pairs_b1024': PAIRS_B1024,
        'user_native_cache_before': native_cache_state(user_cache),
    }
    (RAW / 'n8_02_preflight.json').write_text(json.dumps(protocol, indent=1))

    # 1. warmup (numba disk cache population, uninstrumented, default)
    print('[warmup] default b128 uninstrumented', flush=True)
    warmup = run_child('warmup_default_b128', backend='default', block=128, instrument=False)

    # 2. first-use native (fresh scratch cache, instrumented)
    print('[first-use] native fresh scratch cache', flush=True)
    scratch_first = WORK_ROOT / 'native_cache_firstuse'
    if scratch_first.exists():
        import shutil
        shutil.rmtree(scratch_first)
    first_use = run_child('firstuse_native_b128', backend='native', block=128,
                          instrument=True, native_cache=str(scratch_first))
    first_use['scratch_cache_after'] = native_cache_state(scratch_first)

    # 3. instrumented matrix
    instrumented = {}
    for backend in ('default', 'native'):
        for block in (128, 1024):
            tag = f'instr_{backend}_b{block}'
            print(f'[instrumented] {tag}', flush=True)
            instrumented[tag] = run_child(tag, backend=backend, block=block, instrument=True)

    # 4. uninstrumented paired timing reps
    timing = {}
    for block, pairs in ((128, PAIRS_B128), (1024, PAIRS_B1024)):
        reps = {'default': [], 'native': []}
        for pair in range(pairs):
            for backend in ('default', 'native'):  # A,C order each pair
                tag = f'time_b{block}_{backend}_p{pair}'
                print(f'[timing] {tag}', flush=True)
                rec = run_child(tag, backend=backend, block=block, instrument=False)
                reps[backend].append(rec)
                time.sleep(0.5)
        timing[f'b{block}'] = reps

    # 5. production-entry pool arms with fresh scratch native caches
    pool = {}
    for backend in ('default', 'native'):
        scratch = WORK_ROOT / f'native_cache_pool_{backend}'
        if scratch.exists():
            import shutil
            shutil.rmtree(scratch)
        tag = f'pool_{backend}_b128'
        print(f'[pool] {tag}', flush=True)
        rec = run_child(tag, backend=backend, block=128, instrument=False,
                        entry='pool', native_cache=str(scratch))
        rec['scratch_cache_after'] = native_cache_state(scratch)
        pool[backend] = rec

    finished = now_utc()

    # ---- aggregation ----
    def med_wall(records):
        return med([r['child']['run_wall_s'] for r in records
                    if r.get('returncode') == 0]) if records else None

    summary_timing = {}
    for key, reps in timing.items():
        d = med_wall(reps['default'])
        n = med_wall(reps['native'])
        summary_timing[key] = {
            'n_pairs': len(reps['default']),
            'default_run_wall_med_s': round(d, 4) if d else None,
            'native_run_wall_med_s': round(n, 4) if n else None,
            'native_over_default': round(n / d, 4) if d and n else None,
            'default_all': [r['child']['run_wall_s'] for r in reps['default']],
            'native_all': [r['child']['run_wall_s'] for r in reps['native']],
        }

    record = {
        'schema': 'sw8-n8-02-profile-v1',
        'task': 'N8-02 packed worker boundary + native entry measurement',
        'evidence_class': 'new_region_measurement',
        'started_utc': started, 'finished_utc': finished,
        'protocol': protocol,
        'warmup': {'returncode': warmup['returncode'],
                   'run_wall_s': warmup.get('child', {}).get('run_wall_s')},
        'first_use_native': {
            'returncode': first_use['returncode'],
            'run_wall_s': first_use.get('child', {}).get('run_wall_s'),
            'scratch_cache_after': first_use.get('scratch_cache_after'),
            'counters': first_use.get('counters'),
        },
        'instrumented': {tag: {'returncode': rec['returncode'],
                               'run_wall_s': rec.get('child', {}).get('run_wall_s'),
                               'counters': rec.get('counters'),
                               'rss_tree': rec['rss_tree']}
                         for tag, rec in instrumented.items()},
        'timing_paired': summary_timing,
        'pool_entry': {backend: {'returncode': rec['returncode'],
                                 'run_wall_s': rec.get('child', {}).get('run_wall_s'),
                                 'scratch_cache_after': rec.get('scratch_cache_after'),
                                 'rss_tree': rec['rss_tree']}
                       for backend, rec in pool.items()},
        'failures': [],
    }
    for tag, rec in ([('warmup', warmup), ('firstuse_native_b128', first_use)] +
                     list(instrumented.items()) +
                     [(f'pool_{b}', rec) for b, rec in pool.items()] +
                     [(f'time_{k}_{b}_p{i}', r) for k, reps in timing.items()
                      for b in ('default', 'native') for i, r in enumerate(reps[b])]):
        if rec['returncode'] != 0:
            record['failures'].append({'tag': tag, 'stderr_tail': rec['stderr_tail']})

    # raw per-rep records
    (RAW / 'n8_02_all_runs.json').write_text(json.dumps(
        {'warmup': warmup, 'first_use': first_use, 'instrumented': instrumented,
         'timing': {k: {b: [r for r in reps[b]] for b in reps} for k, reps in timing.items()},
         'pool': pool}, indent=1, default=str) + '\n')

    out = EVIDENCE / 'n8_02_profile.json'
    out.write_text(json.dumps(record, indent=1) + '\n')
    print('written', out, flush=True)
    print('failures:', len(record['failures']), flush=True)
    return 0 if not record['failures'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
