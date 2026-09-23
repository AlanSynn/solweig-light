#SOLWEIG-GPU: GPU-accelerated SOLWEIG model for urban thermal comfort simulation
#Copyright (C) 2022–2025 Harsh Kamath and Naveen Sudharsan

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful, but
#WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#General Public License for more details.
"""N8-22 policy-selector test bootstrap.

N8-41 vendoring: the policy module under test and the N8-21 loader it can
consult lazily are imported from the package (same module identity the
dispatch binds). Provides the fabricated
evidence tree / genuine staged-artifact fixtures.  Pure builders live in
``policy_test_helpers`` (unique module name; a bare ``conftest`` import
would collide with sibling suites in one pytest session).

The genuine staged N8-20 generation is reused read-only (copied into a
fake installed package, same pattern as tests/optimization_v8/artifacts/)
for the "qualified artifact present yet still fail-closed" proof.

Skip labels (never fake-pass):
  [no-staged-artifact] -- the N8-20 proof generation is not present under
                          experiments/.../packaging/stage
"""
import importlib
import json
import shutil
import sys
import uuid
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
# N8-41 vendoring: lw_default_policy / installed_loader are imported
# from the package (same module identity the dispatch binds). Only the
# suite's own directory stays on sys.path (the uniquely-named helpers
# module) plus the packaging PATH constant for the staged proof
# generation (a file path, not an import route).
_PACKAGING = REPO / 'experiments' / 'optimization_v8' / 'packaging'

for _p in (Path(__file__).resolve().parent,):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from solweig_light._native_dispatch import lw_default_policy as policy  # noqa: E402  (module under test)
from policy_test_helpers import (  # noqa: E402  (fabricated builders)
    COMMIT, make_promotion_record, write_json)

STAGE_DIR = _PACKAGING / 'stage'


@pytest.fixture(autouse=True)
def _fresh_policy_state():
    """Fresh reason log / assess cache per test."""
    policy.reset_for_tests()
    yield
    policy.reset_for_tests()


# ---------------------------------------------------------------------------
# Fabricated evidence tree (promotion record + independent review)
# ---------------------------------------------------------------------------


@pytest.fixture()
def evidence(tmp_path):
    """Fabricated evidence tree under tmp: promotion record (passing
    promotion_gate.assess) + independent review (APPROVE-WITH-NOTES);
    returns helpers to rebuild variants and to assemble row records
    against them."""
    class Evidence:
        root = tmp_path
        promotion_path, promotion_sha = write_json(
            tmp_path / 'evidence' / 'promotion.json',
            make_promotion_record())
        review_path, review_sha = write_json(
            tmp_path / 'evidence' / 'review.json',
            {'schema': 'sw8-lw-review-v1', 'task': 'N8-22-tests',
             'verdict': 'APPROVE-WITH-NOTES'})

        def rewrite_promotion(self, record):
            self.promotion_path, self.promotion_sha = write_json(
                self.promotion_path, record)

        def row_record(self, **overrides):
            record = {
                'schema': policy.ROW_RECORD_SCHEMA,
                'status': 'qualified',
                'row': 'C',
                'host_class': policy.current_host_class(),
                'created_utc': '2026-09-22T00:00:00Z',
                'source_commit': COMMIT,
                'artifact_identity': {
                    'kind': 'installed-native-generation',
                    'generation': 'gen-fabricated',
                    'kernel_sha256': '2' * 64,
                    'dylib_sha256': '3' * 64,
                },
                'promotion_record': {
                    'path': 'evidence/promotion.json',
                    'sha256': self.promotion_sha,
                    'schema': policy.PROMOTION_RECORD_SCHEMA,
                },
                'cells': ['primary-0', 'primary-2'],
                'independent_review': {
                    'path': 'evidence/review.json',
                    'sha256': self.review_sha,
                },
            }
            record.update(overrides)
            return record

        def registry(self, *records):
            return {'schema': policy.REGISTRY_SCHEMA, 'records':
                    list(records)}
    return Evidence()


# ---------------------------------------------------------------------------
# Genuine staged N8-20 generation (read-only source for copies)
# ---------------------------------------------------------------------------


@pytest.fixture(scope='session')
def staged_generation() -> Path:
    manifests = sorted(STAGE_DIR.glob('*/manifest.json'))
    if not manifests:
        pytest.skip('[no-staged-artifact] run build_native.py on the B7 '
                    'kernel to produce experiments/optimization_v8/'
                    'packaging/stage/<gen>')
    return manifests[-1].parent


@pytest.fixture(scope='session')
def staged_manifest(staged_generation) -> dict:
    return json.loads((staged_generation / 'manifest.json').read_text())


@pytest.fixture(scope='session')
def staged_identity(staged_manifest) -> dict:
    """(generation, kernel_sha256, dylib_sha256) of the staged original,
    read from the manifest exactly like installed_loader._instantiate."""
    return {
        'generation': staged_manifest['generation'],
        'kernel_sha256': staged_manifest['kernel']['sha256'],
        'dylib_sha256': staged_manifest['artifacts'][0]['sha256'],
    }


@pytest.fixture()
def make_package(tmp_path, staged_generation):
    """Fake installed package factory (same pattern as the N8-21 suite):
    a real importable package whose backends/native_generated holds a copy
    of the staged generation, so installed_loader.attempt_load(<name>)
    exercises the genuine resolution/gating path."""
    made: list[tuple[str, str]] = []

    def _make() -> tuple[str, Path]:
        name = f'fake_native_pkg_{uuid.uuid4().hex[:10]}'
        root = tmp_path / name
        ng = root / 'backends' / 'native_generated'
        ng.mkdir(parents=True)
        (root / '__init__.py').write_text('')
        shutil.copytree(staged_generation, ng / staged_generation.name)
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


@pytest.fixture()
def genuine_loaded_outcome(make_package, staged_identity):
    """A GENUINE N8-21 LoadOutcome for the staged artifact (loaded through
    the real loader's resolution + gating, in a fake installed package)."""
    from solweig_light._native_dispatch import installed_loader  # noqa: E402  (N8-21)
    installed_loader.reset_for_tests()
    name, _ = make_package()
    outcome = installed_loader.attempt_load(name)
    installed_loader.reset_for_tests()
    assert outcome.status == 'loaded', outcome.reason
    assert outcome.generation == staged_identity['generation']
    return outcome
