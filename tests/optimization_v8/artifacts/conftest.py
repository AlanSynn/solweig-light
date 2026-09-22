#SOLWEIG-GPU: GPU-accelerated SOLWEIG model for urban thermal comfort simulation
#Copyright (C) 2022–2025 Harsh Kamath and Naveen Sudharsan

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
"""N8-21 installed-artifact loader test bootstrap.

Puts the experiments dirs on sys.path (the artifacts module under test +
the N8-20 packaging driver + the N8-10 loader it reuses) and provides
fake INSTALLED package trees in tmp: the staged proof generation is
copied into ``<tmp>/<pkg>/backends/native_generated/<gen>/`` so
resolution goes through the real importlib.resources machinery, never
through env vars.  The staged original is never mutated (session-end
integrity assert in the test module).

Skip labels (never fake-pass):
  [no-staged-artifact] -- the N8-20 proof generation is not present under
                          experiments/.../packaging/stage
"""
import importlib
import sys
import uuid
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
_ARTIFACTS = REPO / 'experiments' / 'optimization_v8' / 'artifacts'
_PACKAGING = REPO / 'experiments' / 'optimization_v8' / 'packaging'
_LOADER = REPO / 'experiments' / 'optimization_v8' / 'loader'

for _p in (str(_ARTIFACTS), str(_PACKAGING), str(_LOADER)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import installed_loader  # noqa: E402  (module under test)

STAGE_DIR = _PACKAGING / 'stage'


@pytest.fixture(autouse=True)
def _fresh_loader_state():
    """Fresh loader + handle registries per test."""
    installed_loader.reset_for_tests()
    yield
    installed_loader.reset_for_tests()


@pytest.fixture(scope='session')
def staged_generation() -> Path:
    """The REAL N8-20 proof generation (read-only source for copies)."""
    manifests = sorted(STAGE_DIR.glob('*/manifest.json'))
    if not manifests:
        pytest.skip('[no-staged-artifact] run build_native.py on the B7 '
                    'kernel to produce experiments/optimization_v8/'
                    'packaging/stage/<gen>')
    return manifests[-1].parent


@pytest.fixture(scope='session')
def staged_integrity(staged_generation) -> dict:
    """Digests of the staged original, captured once; the final test
    asserts the suite never mutated it."""
    import hashlib

    def sha(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    return {p.name: sha(p) for p in sorted(staged_generation.iterdir())
            if p.is_file()}


@pytest.fixture()
def make_package(tmp_path):
    """Factory: build a fake installed package and return (name, root).

    The package is importable (real __init__.py on sys.path) so the
    loader's importlib.resources resolution exercises the genuine
    installed-package path; teardown removes it from sys.path/modules.
    """
    made: list[tuple[str, str]] = []

    def _make(setup=None) -> tuple[str, Path]:
        name = f'fake_native_pkg_{uuid.uuid4().hex[:10]}'
        root = tmp_path / name
        ng = root / 'backends' / 'native_generated'
        ng.mkdir(parents=True)
        (root / '__init__.py').write_text('')
        if setup is not None:
            setup(ng)
        sys.path.insert(0, str(tmp_path))
        importlib.import_module(name)
        made.append((name, str(tmp_path)))
        return name, root

    yield _make
    for name, path in made:
        sys.modules.pop(name, None)
    for _, path in set(made):
        while path in sys.path:
            sys.path.remove(path)
