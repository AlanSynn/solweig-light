#!/usr/bin/env python3
"""Read-only worktree audit. Never switches, resets, creates or moves a branch."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

BRANCH = 'perf/claude-glm53-cpu-v5'


def git(repo: Path, *args: str) -> str:
    p = subprocess.run(['git', '-C', str(repo), *args], text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if p.returncode:
        raise ValueError(f'git {args[0]} failed: {p.stderr.strip()}')
    return p.stdout.strip()


def audit(repo: Path, role: str = 'integration', base: str | None = None) -> dict:
    repo = repo.resolve()
    top = Path(git(repo, 'rev-parse', '--show-toplevel')).resolve()
    head = git(top, 'rev-parse', 'HEAD')
    branch = git(top, 'branch', '--show-current')
    if role == 'integration' and branch != BRANCH:
        raise ValueError(f'Expected existing branch {BRANCH}; found {branch or "DETACHED"}. No refs changed.')
    if role == 'worker':
        if branch:
            raise ValueError('Worker must use an assigned detached worktree, not a named branch.')
        if not base:
            raise ValueError('Worker requires an explicit immutable --base commit.')
        wanted = git(top, 'rev-parse', '--verify', f'{base}^{{commit}}')
        p = subprocess.run(['git', '-C', str(top), 'merge-base', '--is-ancestor', wanted, head],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if p.returncode != 0:
            raise ValueError('Worker HEAD does not descend from the explicit assigned base.')
    elif role != 'integration':
        raise ValueError('Unknown role')
    status = git(top, 'status', '--porcelain=v1', '--untracked-files=normal')
    paths = ['src/solweig_light/' + s for s in (
        'api.py','pipeline.py','identities.py','runtime.py','cache/geometry.py',
        'cache/legacy.py','geometry/service.py','radiation/engine.py',
        'radiation/ground_view.py','radiation/patch_radiation.py')]
    hashes = {}
    for name in paths:
        p = top / name
        if p.is_file():
            hashes[name] = hashlib.sha256(p.read_bytes()).hexdigest()
    return {'schema':'sw6-read-only-branch-audit-v1','role':role,'repository':str(top),
            'head':head,'branch':branch or None,'dirty_status':status.splitlines(),
            'selected_source_sha256':hashes,'git_state_changed_by_tool':False,
            'note':'Status may include user-owned paths. Do not stash/reset/overwrite them.'}


def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo', type=Path, default=Path.cwd())
    ap.add_argument('--role', choices=['integration','worker'], default='integration')
    ap.add_argument('--base')
    ap.add_argument('--out', type=Path)
    a=ap.parse_args()
    try:
        result=audit(a.repo,a.role,a.base)
    except (ValueError,OSError) as e:
        ap.exit(2,str(e)+'\n')
    text=json.dumps(result,indent=2)+'\n'
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(text)
    else: print(text,end='')

if __name__=='__main__': main()
