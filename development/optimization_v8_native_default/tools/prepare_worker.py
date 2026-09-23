"""Dry-run by default; creates only an explicit-commit detached worktree."""
from __future__ import annotations
import argparse
from pathlib import Path
from _common import commit, emit, git, no_symlink_ancestors, repo_root, require_branch, require_project


def prepare(repo: Path, base: str, destination: Path, apply: bool = False) -> dict:
    require_branch(repo); require_project(repo)
    sha = commit(repo, base)
    destination = destination.expanduser().absolute()
    no_symlink_ancestors(destination)
    if destination.exists():
        raise ValueError('Destination already exists; nothing will be removed')
    if not destination.parent.is_dir():
        raise ValueError('Create the destination parent explicitly before applying')
    if destination == repo or repo in destination.parents:
        raise ValueError('Worker destination must be outside the integration checkout')
    command = ['git', '-C', str(repo), 'worktree', 'add', '--detach', str(destination), sha]
    if apply:
        git(repo, 'worktree', 'add', '--detach', str(destination), sha)
    return {'schema': 'sw8-worker-plan-v1', 'applied': apply, 'base_sha': sha,
            'destination': str(destination), 'command': command,
            'new_named_branch': False, 'cleanup_performed': False}


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', default='.');p.add_argument('--base', required=True)
    p.add_argument('--destination', required=True);p.add_argument('--apply', action='store_true')
    a=p.parse_args()
    try:
        emit(prepare(repo_root(a.repo),a.base,Path(a.destination),a.apply));return 0
    except (ValueError,OSError) as exc:
        emit({'error':str(exc),'applied':False});return 2

if __name__ == '__main__':
    raise SystemExit(main())
