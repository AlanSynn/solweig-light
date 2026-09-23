"""Small stdlib helpers. No network, framework initialization or secrets logging."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import subprocess
from typing import Any

BRANCH = 'perf/cpu-optimization'


def git(repo: Path, *args: str) -> str:
    completed = subprocess.run(['git', '-C', str(repo), *args], check=False,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, timeout=20)
    if completed.returncode:
        # No full subprocess environment or credential-containing URL is printed.
        raise ValueError(f'git operation failed: {args[0] if args else "unknown"} (exit {completed.returncode})')
    return completed.stdout.strip()


def require_branch(repo: Path) -> tuple[Path, str]:
    root = Path(git(repo, 'rev-parse', '--show-toplevel')).resolve()
    name = git(root, 'symbolic-ref', '--quiet', '--short', 'HEAD')
    if name != BRANCH:
        raise ValueError(f'Expected existing integration branch {BRANCH}; no checkout was changed')
    return root, git(root, 'rev-parse', 'HEAD')


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def positive_int(value: Any, name: str, *, zero: bool = False) -> int:
    if type(value) is not int or value < (0 if zero else 1):
        raise ValueError(f'{name} must be {"nonnegative" if zero else "positive"} integer')
    return value


def number(value: Any, name: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError(f'{name} must be a finite number')
    result = float(value)
    if not math.isfinite(result) or result < 0 or (positive and result == 0):
        raise ValueError(f'{name} must be finite and {"positive" if positive else "nonnegative"}')
    return result


def write_new_json(path: Path, value: Any) -> None:
    """Never overwrite a previous evidence record."""
    payload = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        stream.write(payload)
