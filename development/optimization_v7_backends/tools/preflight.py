#!/usr/bin/env python3
"""Read-only branch/tool inventory. Does not import numerical backends or call APIs."""
from __future__ import annotations
import argparse
import importlib.metadata
import json
from pathlib import Path
import platform
import shutil
import sys
from _common import git, require_branch, sha256_file, write_new_json

FILES = ('src/solweig_light/radiation/cylinder_longwave.py',
         'src/solweig_light/radiation/_math_profile.py',
         'src/solweig_light/radiation/_sleef_classifier.py',
         'src/solweig_light/geometry/visibility_compiled.py',
         'src/solweig_light/pipeline.py', 'src/solweig_light/runtime.py',
         'src/solweig_light/identities.py', 'pyproject.toml')


def inspect(repo: Path) -> dict:
    root, head = require_branch(repo)
    versions = {}
    for name in ('numpy', 'numba', 'llvmlite', 'GDAL', 'drjit', 'pyopencl', 'mlx', 'nanobind'):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    paths = {}
    for relative in FILES:
        path = root / relative
        paths[relative] = sha256_file(path) if path.is_file() else None
    return {'schema': 'solweig-backend-readonly-preflight-v1',
            'repository': str(root), 'branch': 'perf/cpu-optimization', 'head': head,
            'dirty_status': git(root, 'status', '--porcelain=v1'),
            'python': {'executable': sys.executable, 'version': platform.python_version()},
            'host': {'system': platform.system(), 'machine': platform.machine()},
            'file_sha256': paths, 'installed_distribution_versions': versions,
            'tool_paths': {name: shutil.which(name) for name in ('git','claude','ispc','clang++','g++','cmake','clinfo')},
            'provider_verified': False, 'device_verified': False, 'kernel_executed': False,
            'note': 'Package metadata/tool presence is not backend capability or actual model routing. No numerical import, network access or secret environment dump performed.'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    result = inspect(args.repo)
    if args.out:
        write_new_json(args.out, result)
    else:
        print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
