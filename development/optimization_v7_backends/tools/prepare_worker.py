#!/usr/bin/env python3
"""Dry-run by default; create only a detached worktree at an explicit reachable base."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys
from _common import git, require_branch


def prepare(repo: Path, base: str, destination: Path, *, apply: bool = False) -> dict:
    root, head = require_branch(repo)
    if not base or base.startswith('-'):
        raise ValueError('An explicit base commit is required')
    full = git(root, 'rev-parse', '--verify', base + '^{commit}')
    status = subprocess.run(['git','-C',str(root),'merge-base','--is-ancestor',full,head],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            timeout=20).returncode
    if status != 0:
        raise ValueError('Worker base must be an ancestor of the current integration HEAD')
    dest = destination.expanduser().absolute()
    if dest.exists() or dest.is_symlink():
        raise ValueError('Destination must not exist; nothing will be removed')
    dest = dest.resolve()
    if dest == root or root in dest.parents:
        raise ValueError('Detached worktree must be outside the integration worktree')
    if not dest.parent.is_dir():
        raise ValueError('Destination parent must already exist')
    command = ['git','-C',str(root),'worktree','add','--detach',str(dest),full]
    result = {'applied': False, 'command': command, 'base': full, 'integration_head': head,
              'note': 'No new branch, commits, pushes, resets or cleanup.'}
    if apply:
        git(root, 'worktree', 'add', '--detach', str(dest), full)
        if git(dest, 'rev-parse', 'HEAD') != full:
            raise RuntimeError('Created worktree HEAD did not match; left untouched for inspection')
        if require_branch(root)[1] != head:
            raise RuntimeError('Integration HEAD changed concurrently; worker left for inspection')
        result['applied'] = True
    return result


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--base',required=True)
    p.add_argument('--destination',type=Path,required=True)
    p.add_argument('--apply',action='store_true')
    a=p.parse_args()
    print(json.dumps(prepare(a.repo,a.base,a.destination,apply=a.apply),indent=2))
    return 0


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except (ValueError,OSError) as e:
        print(str(e),file=sys.stderr);raise SystemExit(2)
