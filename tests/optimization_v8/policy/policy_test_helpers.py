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
"""Pure builders shared by the N8-22 policy tests.

Imported under its UNIQUE module name (never as ``conftest``: sibling v8
suites each have their own conftest.py and the bare name would collide
once several suites run in one session).

Everything here is FABRICATED evidence exercising selector mechanics only
(PROMOTION_POLICY.md: "Packet unit tests use fabricated examples solely to
test the tool, never runtime evidence").
"""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

COMMIT = '1' * 40


# ---------------------------------------------------------------------------
# Fake N8-21 LoadOutcome builders (duck-typed; the selector only reads
# .status/.reason/.error/.generation/.handle.identity())
# ---------------------------------------------------------------------------


def make_loaded_outcome(generation='gen-fabricated',
                        kernel_sha256='2' * 64, dylib_sha256='3' * 64):
    handle = SimpleNamespace(identity=lambda: {
        'kernel_sha256': kernel_sha256,
        'stamp': {'dylib_sha256': dylib_sha256},
    })
    return SimpleNamespace(
        status='loaded', reason='verified and loaded', error=None,
        generation=generation, handle=handle)


def make_declined_outcome(status='declined-absent', reason='no artifact',
                          error=None):
    return SimpleNamespace(
        status=status, reason=reason,
        error=error if error is not None else RuntimeError(reason),
        generation=None, handle=None)


# ---------------------------------------------------------------------------
# Fabricated promotion / review evidence (mechanics only, never runtime)
# ---------------------------------------------------------------------------


def _pairs(ratio, count=3):
    return [{'baseline_s': ratio, 'candidate_s': 1.0} for _ in range(count)]


def _primary_cell(index, ratio):
    return {
        'id': f'primary-{index}', 'kind': 'primary',
        'clean_complete': True, 'matched_budget': True,
        'thread_observed': True, 'default_env_unset': True,
        'main_defaults_covered': index == 0,
        'raw_evidence_paths': [f'evidence/raw/primary-{index}.json'],
        'pairs_current': _pairs(ratio), 'pairs_control': _pairs(1.08),
        'eligible_work': 1000, 'native_executed_work': 850,
    }


def make_promotion_record(ratios=(1.30, 1.25, 1.20, 1.15)):
    """A promotion record that passes promotion_gate.assess (4 primary
    cells with geomean ~1.22, one main-default primary, one guard)."""
    cells = [_primary_cell(i, ratio) for i, ratio in enumerate(ratios)]
    cells.append({
        'id': 'guard-default', 'kind': 'guard',
        'clean_complete': True, 'matched_budget': True,
        'thread_observed': True, 'default_env_unset': True,
        'raw_evidence_paths': ['evidence/raw/guard-default.json'],
        'pairs_current': _pairs(1.0),
    })
    return {
        'schema': 'sw8-default-promotion-record-v1',
        'status': 'observed',
        'branch': 'perf/native-optimization',
        'protocol_frozen_before_candidates': True,
        'source_sha': COMMIT,
        'protocol_sha256': 'b' * 64,
        'artifact_sha256': 'c' * 64,
        'qualification': {
            field: 'passed' for field in (
                'numeric', 'dx', 'installed_wheel', 'source_fallback',
                'independent_review', 'resources', 'cold_first_use')
        },
        'cells': cells,
        'actual_target_status': 'unverified',
    }


def write_json(path: Path, payload) -> tuple[Path, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    blob = json.dumps(payload, indent=2).encode()
    path.write_bytes(blob)
    return path, hashlib.sha256(blob).hexdigest()
