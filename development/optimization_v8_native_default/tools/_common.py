"""Local packet helpers. No network, project import, or automatic repository writes."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

BRANCH = 'perf/native-optimization'
PACKET = 'optimization_v8_native_default'


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(['git', '-C', str(repo), *args], text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode:
        raise ValueError(result.stderr.strip() or 'git command failed')
    return result.stdout.strip()


def repo_root(value: str | Path) -> Path:
    path = Path(value).expanduser().resolve()
    root = Path(git(path, 'rev-parse', '--show-toplevel')).resolve()
    if path != root:
        raise ValueError('--repo must be the repository root')
    return root


def require_branch(repo: Path) -> str:
    name = git(repo, 'symbolic-ref', '--quiet', '--short', 'HEAD')
    if name != BRANCH:
        raise ValueError(f'Expected {BRANCH}; got {name}. No automatic checkout/reset.')
    return name


def require_project(repo: Path) -> None:
    if not (repo / 'src/solweig_light/__init__.py').is_file():
        raise ValueError('SOLWEIG source marker missing; refusing to modify this repository')


def commit(repo: Path, ref: str) -> str:
    if not re.fullmatch(r'[0-9a-fA-F]{40}', ref):
        raise ValueError('Use an explicit full 40-character commit SHA')
    value = git(repo, 'rev-parse', '--verify', ref + '^{commit}')
    if not re.fullmatch(r'[0-9a-f]{40}', value):
        raise ValueError('Cannot resolve commit')
    return value


def no_symlink_ancestors(path: Path) -> None:
    # Check lexical components before resolving; resolving would hide symlinks.
    for value in [path, *path.parents]:
        if value.is_symlink():
            raise ValueError(f'Symlink path is not allowed: {value}')


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write(path: Path, data: str) -> None:
    no_symlink_ancestors(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.sw8-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        Path(tmp).unlink(missing_ok=True)


def emit(value: dict) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False))
