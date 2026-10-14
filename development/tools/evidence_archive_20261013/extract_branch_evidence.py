#!/usr/bin/env python3
"""Extract branch-only blobs from the three campaign branches.

Writes files under staging/branch_evidence/<branch>/ preserving repo-relative
paths, plus a per-branch manifest recording sha256 of every extracted blob.
Blobs shared between branches are written once; later branches record a
shared_with reference instead of duplicating bytes.
"""
import hashlib
import json
import os
import subprocess

REPO = '/storage/scratch1/1/dsynn6/solweig-light'
STAGE = '/storage/scratch1/1/dsynn6/solweig-light-archive-staging'
BRANCHES = [
    ('handover_campaign-line', 'origin/handover/campaign-line'),
    ('perf_cpu-optimization', 'origin/perf/cpu-optimization'),
    ('perf_native-optimization', 'origin/perf/native-optimization'),
]


def run(args, inp=None):
    return subprocess.run(args, check=True, capture_output=True, input=inp).stdout


seen = {}  # blob sha1 -> (branch_name, path) of first extraction
summary = {}
for name, ref in BRANCHES:
    listing = run(['git', '-C', REPO, 'rev-list', '--objects', ref, '--not', 'main']).decode()
    cands = []
    for line in listing.splitlines():
        sha, _, path = line.partition(' ')
        if path:
            cands.append((sha, path))
    # Keep blobs only (rev-list --objects also lists trees with paths).
    out = run(['git', '-C', REPO, 'cat-file', '--batch-check=%(objectname) %(objecttype)'],
              inp='\n'.join(s for s, _ in cands).encode()).decode()
    types = {}
    for l in out.splitlines():
        sha, typ = l.split()
        types[sha] = typ
    blobs = [(s, p) for s, p in cands if types.get(s) == 'blob']

    base = os.path.join(STAGE, 'branch_evidence', name)
    records = []
    # Stream blob contents in one batch request.
    proc = subprocess.Popen(
        ['git', '-C', REPO, 'cat-file', '--batch'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    pending = [(s, p) for s, p in blobs if s not in seen]
    shared_records = []
    for s, p in blobs:
        if s in seen:
            shared_records.append({'path': p, 'git_blob_sha1': s,
                                   'shared_with': f'{seen[s][0]}:{seen[s][1]}'})
    try:
        # Interleave request/read per object; pre-writing all requests can
        # deadlock when git's stdout pipe fills while we are still writing.
        for s, p in pending:
            proc.stdin.write((s + '\n').encode())
            proc.stdin.flush()
            header = proc.stdout.readline().decode().split()
            if len(header) != 3 or header[1] != 'blob':
                raise SystemExit(f'unexpected cat-file header for {s}: {header}')
            size = int(header[2])
            data = proc.stdout.read(size)
            proc.stdout.read(1)  # trailing newline after each object
            safe = os.path.normpath(p)
            if safe.startswith(('..', '/')):
                raise SystemExit(f'unsafe path {p}')
            dest = os.path.join(base, safe)
            # The same path can hold different content at different history
            # points; never overwrite — keep each blob under its own name.
            if os.path.exists(dest):
                dest = f'{dest}.blob-{s[:12]}'
                archived = os.path.relpath(dest, base)
            else:
                archived = safe
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, 'wb') as f:
                f.write(data)
            seen[s] = (name, p)
            records.append({'path': p, 'archived_path': archived,
                            'git_blob_sha1': s,
                            'sha256': hashlib.sha256(data).hexdigest(),
                            'size': len(data)})
    finally:
        try:
            proc.stdin.close()
        except BrokenPipeError:
            pass
        proc.wait()
    records.extend(shared_records)
    manifest = {'branch': ref, 'blob_count': len(blobs),
                'written': len(records) - len(shared_records),
                'shared_skipped': len(shared_records), 'records': records}
    # Full verification pass: every written record must match its file.
    bad = []
    for r in records:
        if not r.get('sha256'):
            continue
        fp = os.path.join(base, r['archived_path'])
        with open(fp, 'rb') as f:
            if hashlib.sha256(f.read()).hexdigest() != r['sha256']:
                bad.append(r['archived_path'])
    if bad:
        raise SystemExit(f'FATAL: {len(bad)} extracted files failed sha256 verification')

    with open(os.path.join(STAGE, 'manifests', f'branch_{name}_manifest.json'), 'w') as f:
        json.dump(manifest, f, indent=1)
    summary[name] = {'blobs': len(blobs), 'written': manifest['written'],
                     'shared_skipped': manifest['shared_skipped']}
    print(name, summary[name], flush=True)

with open(os.path.join(STAGE, 'manifests', 'branch_extraction_summary.json'), 'w') as f:
    json.dump(summary, f, indent=1)
print('DONE')
