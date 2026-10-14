#!/usr/bin/env python3
"""Classify tracked files into external-archive vs keep sets and build tar.gz bundles.

Move policy (user decision 2026-10-13): raw campaign measurement evidence moves to
Dropbox; the repository keeps manifests/provenance/docs and every path referenced
by tests. See development/docs/evidence_storage.md after the migration.
"""
import hashlib
import fnmatch
import json
import os
import subprocess
import tarfile

REPO = '/storage/scratch1/1/dsynn6/solweig-light'
STAGE = '/storage/scratch1/1/dsynn6/solweig-light-archive-staging'

CHAR_BULK = [
    'p7_pairs_v4', 'p7_pairs_v3', 'local_cpu_optimization_v1',
    'p8_portable_profile_v1', 'p7_angular_moment_experiment',
    'p8_portable_math_review', 'p7_persistent_jit_serial_variant',
    'p7_persistent_jit_experiment', 'p7_persistent_jit_wall_variant',
    'p7_persistent_jit_distinct_variant', 'p8_asvf_parity_review',
    'p7_full_profile_repeated256', 'p7_full_profile_repeated256_v2',
    'p6_runtime_v1_retry2_psutil', 'p4_radiation_v1',
    'p7_repaired_v2_component_matrix',
]
MOVED_ROOTS = tuple(
    [f'development/reports/characterization/{d}/' for d in CHAR_BULK]
    + [
        'development/reports/p7_profile_repeated256_warmed_v1/',
        'development/reports/p7_profile_repeated256_warmed_v2/',
        'development/reports/p7_profile_small_warmed_v1/',
        'development/reports/p7_profile_small_warmed_v2/',
        'development/reports/cura_p8_20260919T1215Z_a7c3/',
        'development/optimization_v5_claude/evidence/',
        'development/optimization_v6_continue/evidence/',
        'development/optimization_v7_backends/evidence/',
        'development/optimization_n9_final/evidence/',
        'development/optimization_v8_native_default/evidence/',
    ]
)
# Test-referenced evidence that must stay in git (do not archive).
PROTECTED = (
    'development/optimization_v8_native_default/evidence/installed/',
    'development/optimization_v8_native_default/evidence/dx_baseline/',
)
KEEP_BASENAMES = ('README*', '*.md', 'provenance*.json', '*manifest*.json',
                  '*.sha256', 'selection.json', 'final_artifacts.json')
GROUPS = {
    'characterization_pairs_localcpu': lambda p: p.startswith(
        ('development/reports/characterization/p7_pairs_v4/',
         'development/reports/characterization/p7_pairs_v3/',
         'development/reports/characterization/local_cpu_optimization_v1/')),
    'characterization_profiles_math': lambda p: p.startswith(
        ('development/reports/characterization/p8_portable_profile_v1/',
         'development/reports/characterization/p7_angular_moment_experiment/',
         'development/reports/characterization/p8_portable_math_review/',
         'development/reports/characterization/p7_persistent_jit_',
         'development/reports/characterization/p8_asvf_parity_review/',
         'development/reports/characterization/p7_full_profile_',
         'development/reports/characterization/p6_runtime_v1_retry2_psutil/',
         'development/reports/characterization/p4_radiation_v1/',
         'development/reports/characterization/p7_repaired_v2_component_matrix/')),
    'reports_profiles_cura': lambda p: p.startswith(
        ('development/reports/p7_profile_',
         'development/reports/cura_p8_20260919T1215Z_a7c3/')),
    'optimization_evidence': lambda p: p.startswith(
        ('development/optimization_v5_claude/evidence/',
         'development/optimization_v6_continue/evidence/',
         'development/optimization_v7_backends/evidence/',
         'development/optimization_n9_final/evidence/',
         'development/optimization_v8_native_default/evidence/')),
}


def is_kept(path):
    if path.startswith(PROTECTED):
        return True
    base = os.path.basename(path)
    return any(fnmatch.fnmatch(base, pat) for pat in KEEP_BASENAMES)


def main():
    tracked = subprocess.run(['git', '-C', REPO, 'ls-files'], check=True,
                             capture_output=True, text=True).stdout.splitlines()
    archive, keepers = [], []
    for p in tracked:
        if p.startswith(MOVED_ROOTS) and not is_kept(p):
            archive.append(p)
        elif p.startswith(MOVED_ROOTS):
            keepers.append(p)
    assert archive and keepers
    # Guard: test-referenced snapshots must never be archived.
    forbidden = ('development/reports/characterization/p8_umep_source/',
                 'development/reports/characterization/p8_utci_official_source/',
                 'development/reports/characterization/p7_p6_baseline/',
                 'development/reports/characterization/p7_repaired_p6_baseline',
                 'development/reports/contract_snapshot.json')
    for p in archive:
        if p.startswith(forbidden):
            raise SystemExit(f'FATAL: protected path in archive set: {p}')

    with open(os.path.join(STAGE, 'manifests', 'archive_list.txt'), 'w') as f:
        f.write('\n'.join(archive) + '\n')
    with open(os.path.join(STAGE, 'manifests', 'kept_in_repo.txt'), 'w') as f:
        f.write('\n'.join(keepers) + '\n')

    # sha256 manifest of every archived file (relative to repo root).
    sums_path = os.path.join(STAGE, 'manifests', 'repo_evidence_manifest.sha256')
    total = 0
    with open(sums_path, 'w') as f:
        for i, p in enumerate(archive):
            h = hashlib.sha256()
            with open(os.path.join(REPO, p), 'rb') as src:
                for chunk in iter(lambda: src.read(1 << 20), b''):
                    h.update(chunk)
            f.write(f'{h.hexdigest()}  {p}\n')
            total += 1
            if i % 5000 == 0:
                print(f'hashed {i}/{len(archive)}', flush=True)
    print(f'hashed {total} files', flush=True)

    # Bundles: one tar.gz per group, archive-rooted at repo root.
    summary = {}
    for gname, pred in GROUPS.items():
        members = [p for p in archive if pred(p)]
        assert members, gname
        listfile = os.path.join(STAGE, 'manifests', f'bundle_{gname}.txt')
        with open(listfile, 'w') as f:
            f.write('\n'.join(members) + '\n')
        bundle = os.path.join(STAGE, 'bundles', f'{gname}.tar.gz')
        with tarfile.open(bundle, 'w:gz') as tf:
            for p in members:
                tf.add(os.path.join(REPO, p), arcname=p, recursive=False)
        h = hashlib.sha256()
        with open(bundle, 'rb') as src:
            for chunk in iter(lambda: src.read(1 << 20), b''):
                h.update(chunk)
        summary[gname] = {'files': len(members), 'sha256': h.hexdigest(),
                          'bytes': os.path.getsize(bundle)}
        print(gname, summary[gname], flush=True)

    assert sum(v['files'] for v in summary.values()) == len(archive)
    with open(os.path.join(STAGE, 'manifests', 'bundle_summary.json'), 'w') as f:
        json.dump(summary, f, indent=1)
    print('DONE', len(archive), 'archived,', len(keepers), 'kept')


if __name__ == '__main__':
    main()
