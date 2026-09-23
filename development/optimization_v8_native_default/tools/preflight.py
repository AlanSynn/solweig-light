"""Read-only Git/source inventory. Never initializes SOLWEIG/native libraries."""
from __future__ import annotations
import argparse
from pathlib import Path
from _common import BRANCH, emit, git, repo_root, sha256_file

PATHS = ('pyproject.toml', 'src/solweig_light/api.py', 'src/solweig_light/cli.py',
         'src/solweig_light/runtime.py', 'src/solweig_light/backends/native_lw.py',
         'src/solweig_light/radiation/cylinder_longwave.py')


def inspect_repo(repo: Path) -> dict:
    try:
        branch = git(repo, 'symbolic-ref', '--quiet', '--short', 'HEAD')
    except ValueError:
        branch = 'DETACHED'
    files = {}
    for relative in PATHS:
        path = repo / relative
        if path.is_file() and not path.is_symlink():
            files[relative] = {'sha256': sha256_file(path), 'bytes': path.stat().st_size}
    return {'schema': 'sw8-preflight-v1', 'read_only': True,
            'repository': str(repo), 'branch': branch,
            'same_branch': branch == BRANCH, 'head': git(repo, 'rev-parse', 'HEAD'),
            'dirty_porcelain': git(repo, 'status', '--porcelain=v1'),
            'files': files, 'numerical_execution': False,
            'native_qualification': 'not_tested',
            'note': 'No environment/credentials dumped. Local file hashes are not runtime proof.'}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--repo', default='.')
    a = p.parse_args()
    try:
        report = inspect_repo(repo_root(a.repo)); emit(report)
        return 0 if report['same_branch'] else 2
    except (ValueError, OSError) as exc:
        emit({'error': str(exc), 'read_only': True}); return 2

if __name__ == '__main__':
    raise SystemExit(main())
