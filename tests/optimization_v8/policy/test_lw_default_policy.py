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
"""N8-22 policy-selector tests: fail-closed law, activation mechanics,
expert loudness, quiet-ness.

The fail-closed law under test: every way a qualification record can be
absent, stale, malformed, not-qualified or host-mismatched must resolve
the AUTO path to legacy row A -- never to B/C -- while recording the
reason privately.  Fabricated evidence (conftest) exercises the mechanics
exactly as PROMOTION_POLICY.md sanctions for packet unit tests; the
shipped registry stays empty and a separate gate test enforces that.
"""
import json

import pytest

from policy_test_helpers import (make_declined_outcome, make_loaded_outcome,
                                 make_promotion_record, write_json)

from solweig_light._native_dispatch import lw_default_policy as policy


# ---------------------------------------------------------------------------
# Today's observable behavior: auto -> A, always
# ---------------------------------------------------------------------------


def test_auto_resolves_to_legacy_a_today():
    selection = policy.resolve_lw_backend(env={})
    assert selection.row == policy.ROW_A
    assert selection.mode == 'auto-legacy'
    assert selection.expert is False
    assert selection.record is None
    assert selection.reason.startswith('[absent]')
    assert selection.entry == policy.ROW_ENTRIES[policy.ROW_A]


def test_auto_quiet_no_stdout(capsys):
    policy.resolve_lw_backend(env={})
    policy.resolve_lw_backend(env={'SOLWEIG_LIGHT_LW_BACKEND': 'native'})
    out, err = capsys.readouterr()
    assert out == '' and err == ''


def test_shipped_registry_is_empty():
    records = policy.shipped_registry_records()
    assert records == ()
    shipped = json.loads(policy.DEFAULT_REGISTRY_PATH.read_text())
    assert shipped['schema'] == policy.REGISTRY_SCHEMA
    assert shipped['records'] == []


def test_auto_stays_a_with_genuine_loaded_artifact(genuine_loaded_outcome):
    """A REAL qualified artifact loaded through the REAL N8-21 loader still
    does not activate anything: without records the auto path is A."""
    selection = policy.resolve_lw_backend(
        env={}, load_outcome=genuine_loaded_outcome)
    assert selection.row == policy.ROW_A
    assert selection.mode == 'auto-legacy'
    assert selection.reason.startswith('[absent]')


# ---------------------------------------------------------------------------
# Activation mechanics (fabricated records, valid end-to-end)
# ---------------------------------------------------------------------------


def test_qualified_c_record_activates_row_c(evidence, genuine_loaded_outcome,
                                            staged_identity):
    record = evidence.row_record(artifact_identity={
        'kind': 'installed-native-generation',
        'generation': staged_identity['generation'],
        'kernel_sha256': staged_identity['kernel_sha256'],
        'dylib_sha256': staged_identity['dylib_sha256'],
    })
    selection = policy.resolve_lw_backend(
        env={}, registry=evidence.registry(record),
        load_outcome=genuine_loaded_outcome, repo_root=evidence.root)
    assert selection.row == policy.ROW_C
    assert selection.mode == 'auto-qualified'
    assert selection.record is record
    assert selection.expert is False
    assert 'primary_aosoa' in selection.entry
    assert selection.load_outcome is genuine_loaded_outcome


def test_qualified_b_record_activates_row_b(evidence, tmp_path):
    """Row B pins the consumer module digest: a byte-identical copy of the
    real module under the evidence root satisfies the anchor."""
    import hashlib
    module_rel = 'src/solweig_light/_native_dispatch/lw_b_control.py'
    real = policy.REPO_ROOT / module_rel
    module_copy = tmp_path / module_rel
    module_copy.parent.mkdir(parents=True)
    module_copy.write_bytes(real.read_bytes())
    record = evidence.row_record(row='B', artifact_identity={
        'kind': 'python-module',
        'module_path': module_rel,
        'module_sha256': hashlib.sha256(real.read_bytes()).hexdigest(),
    })
    selection = policy.resolve_lw_backend(
        env={}, registry=evidence.registry(record), repo_root=evidence.root)
    assert selection.row == policy.ROW_B
    assert selection.mode == 'auto-qualified'
    assert 'lw_primary_b' in selection.entry


def test_c_precedes_b_when_both_qualified(evidence, tmp_path):
    import hashlib
    module_rel = 'src/solweig_light/_native_dispatch/lw_b_control.py'
    real = policy.REPO_ROOT / module_rel
    module_copy = tmp_path / module_rel
    module_copy.parent.mkdir(parents=True)
    module_copy.write_bytes(real.read_bytes())
    outcome = make_loaded_outcome()
    b_record = evidence.row_record(row='B', artifact_identity={
        'kind': 'python-module', 'module_path': module_rel,
        'module_sha256': hashlib.sha256(real.read_bytes()).hexdigest(),
    })
    c_record = evidence.row_record()
    selection = policy.resolve_lw_backend(
        env={}, registry=evidence.registry(b_record, c_record),
        load_outcome=outcome, repo_root=evidence.root)
    assert selection.row == policy.ROW_C
    assert selection.record is c_record


def test_resolve_is_deterministic(evidence):
    outcome = make_loaded_outcome()
    registry = evidence.registry(evidence.row_record())
    first = policy.resolve_lw_backend(
        env={}, registry=registry, load_outcome=outcome,
        repo_root=evidence.root)
    second = policy.resolve_lw_backend(
        env={}, registry=registry, load_outcome=outcome,
        repo_root=evidence.root)
    assert first == second


# ---------------------------------------------------------------------------
# Fail-closed matrix: every defect resolves auto -> A with a classified
# reason (absent / malformed / stale / unqualified-host / not-qualified)
# ---------------------------------------------------------------------------


def _declines_to_a(evidence, record, outcome=None, **kwargs):
    selection = policy.resolve_lw_backend(
        env={}, registry=evidence.registry(record),
        load_outcome=outcome if outcome is not None
        else make_declined_outcome(),
        repo_root=evidence.root, **kwargs)
    assert selection.row == policy.ROW_A
    assert selection.mode == 'auto-legacy'
    return selection.reason


def test_empty_registry_absent(evidence):
    selection = policy.resolve_lw_backend(
        env={}, registry=evidence.registry(), load_outcome=make_loaded_outcome(),
        repo_root=evidence.root)
    assert (selection.row, selection.mode) == (policy.ROW_A, 'auto-legacy')
    assert selection.reason.startswith('[absent]')


@pytest.mark.parametrize('mutate,prefix', [
    (lambda r: r.update(schema='sw8-other-v9'), '[malformed]'),
    (lambda r: r.update(status='pending'), '[not-qualified]'),
    (lambda r: r.update(row='A'), '[malformed]'),
    (lambda r: r.update(row=None), '[malformed]'),
    (lambda r: r.update(host_class='vax-9000'), '[unqualified-host]'),
    (lambda r: r.update(source_commit='nothex'), '[malformed]'),
    (lambda r: r.update(source_commit=None), '[malformed]'),
    (lambda r: r['artifact_identity'].update(kernel_sha256='4' * 64),
     '[stale]'),
    (lambda r: r['artifact_identity'].update(dylib_sha256='4' * 64),
     '[stale]'),
    (lambda r: r['artifact_identity'].update(generation='gen-other'),
     '[stale]'),
    (lambda r: r['artifact_identity'].update(kind='python-module'),
     '[malformed]'),
    (lambda r: r['artifact_identity'].update(generation=None),
     '[malformed]'),
    (lambda r: r['promotion_record'].update(sha256='0' * 64), '[stale]'),
    (lambda r: r['promotion_record'].update(path='../../etc/passwd'),
     '[malformed]'),
    (lambda r: r['promotion_record'].update(path='/etc/passwd'),
     '[malformed]'),
    (lambda r: r['promotion_record'].update(path='evidence/missing.json'),
     '[stale]'),
    (lambda r: r.update(cells=['primary-0', 'guard-default']), '[malformed]'),
    (lambda r: r.update(cells=[]), '[malformed]'),
    (lambda r: r.update(cells=['not-a-cell']), '[malformed]'),
    (lambda r: r['independent_review'].update(sha256='0' * 64), '[stale]'),
    (lambda r: r.update(independent_review=None), '[malformed]'),
])
def test_record_defects_fail_closed(evidence, mutate, prefix):
    record = evidence.row_record()
    mutate(record)
    reason = _declines_to_a(evidence, record, outcome=make_loaded_outcome())
    assert reason.startswith(prefix), reason


def test_registry_file_malformed_fails_closed(tmp_path):
    bad = tmp_path / 'registry.json'
    bad.write_text('{not json')
    selection = policy.resolve_lw_backend(env={}, registry=bad)
    assert (selection.row, selection.mode) == (policy.ROW_A, 'auto-legacy')
    assert selection.reason.startswith('[malformed]')


@pytest.mark.parametrize('registry', [
    {'schema': 'other', 'records': []},
    {'records': []},
    {'schema': policy.REGISTRY_SCHEMA, 'records': {'not': 'a list'}},
    object(),
], ids=['wrong-schema', 'no-schema', 'records-not-list', 'wrong-type'])
def test_registry_argument_defects_fail_closed(registry):
    selection = policy.resolve_lw_backend(env={}, registry=registry)
    assert (selection.row, selection.mode) == (policy.ROW_A, 'auto-legacy')
    assert selection.reason.startswith('[malformed]')


def test_non_object_registry_entries_fail_closed(evidence):
    selection = policy.resolve_lw_backend(
        env={}, registry=evidence.registry('junk', 42),
        load_outcome=make_loaded_outcome(), repo_root=evidence.root)
    assert selection.row == policy.ROW_A
    assert any('[malformed] registry entry is not an object'
               in reason for reason in policy.policy_reasons())


def test_declined_artifact_record_is_stale(evidence):
    reason = _declines_to_a(evidence, evidence.row_record(),
                            outcome=make_declined_outcome(
                                status='declined-absent',
                                reason='no native_generated resources'))
    assert reason.startswith('[stale]')


def test_edited_promotion_evidence_is_stale(evidence):
    record = evidence.row_record()
    # Rewrite with different content: the certified sha256 no longer
    # matches the file on disk (evidence changed after certification).
    evidence.rewrite_promotion(make_promotion_record(
        ratios=(1.45, 1.40, 1.35, 1.30)))
    reason = _declines_to_a(evidence, record, outcome=make_loaded_outcome())
    assert reason.startswith('[stale]')


def test_promotion_gates_reverified_not_trusted(evidence):
    failing = make_promotion_record(ratios=(1.0, 1.0, 1.0, 1.0))
    evidence.rewrite_promotion(failing)
    record = evidence.row_record()  # picks up the new sha, says nothing else
    record['promotion_record']['policy_data_passed'] = True  # liar field
    reason = _declines_to_a(evidence, record, outcome=make_loaded_outcome())
    assert reason.startswith('[not-qualified]')
    assert 'promotion gates not satisfied' in reason


def test_review_rejected_fails_closed(evidence):
    path, sha = write_json(evidence.root / 'evidence' / 'review.json',
                           {'schema': 'sw8-lw-review-v1',
                            'verdict': 'REJECT'})
    record = evidence.row_record(independent_review={
        'path': 'evidence/review.json', 'sha256': sha})
    reason = _declines_to_a(evidence, record, outcome=make_loaded_outcome())
    assert reason.startswith('[not-qualified]')
    assert 'REJECT' in reason


def test_review_pending_fails_closed(evidence):
    path, sha = write_json(evidence.root / 'evidence' / 'review.json',
                           {'schema': 'sw8-lw-review-v1',
                            'verdict': 'OPEN'})
    record = evidence.row_record(independent_review={
        'path': 'evidence/review.json', 'sha256': sha})
    reason = _declines_to_a(evidence, record, outcome=make_loaded_outcome())
    assert reason.startswith('[not-qualified]')


@pytest.mark.parametrize('verdict', ['approve', 'Approve'])
def test_review_verdict_matching_is_case_sensitive(evidence, verdict):
    """N2 (review n8_30_review_n8_22_policy): the approval prefix match is
    deliberately CASE-SENSITIVE -- the repo convention is uppercase
    APPROVE; lowercase variants must decline, not pass by accident."""
    path, sha = write_json(evidence.root / 'evidence' / 'review.json',
                           {'schema': 'sw8-lw-review-v1',
                            'verdict': verdict})
    record = evidence.row_record(independent_review={
        'path': 'evidence/review.json', 'sha256': sha})
    reason = _declines_to_a(evidence, record, outcome=make_loaded_outcome())
    assert reason.startswith('[not-qualified]')
    assert verdict in reason


# ---------------------------------------------------------------------------
# B1 regression (review n8_30_review_n8_22_policy): row/identity binding.
# The foreign-kind fields are FULLY populated and individually VALID, so
# only the row/kind rule can produce the decline -- each construction must
# land in [malformed], never activate the wrong row through the other
# row's anchor.
# ---------------------------------------------------------------------------


def test_b1_adv1_row_b_with_fully_valid_native_identity_declines(evidence):
    """Adversarial ADV1: row B carrying an installed-native-generation
    identity that MATCHES a loaded outcome. Before the binding, this
    ACTIVATED row B while the certified consumer module had been tampered
    with after certification (the module-digest anchor never ran)."""
    record = evidence.row_record(row='B', artifact_identity={
        'kind': 'installed-native-generation',
        'generation': 'gen-fabricated',
        'kernel_sha256': '2' * 64,
        'dylib_sha256': '3' * 64,
    })
    # The native identity matches this loaded outcome exactly, so the
    # foreign anchor would pass; the decline must come from the binding.
    reason = _declines_to_a(evidence, record, outcome=make_loaded_outcome())
    assert reason.startswith('[malformed]')
    assert 'cross-wire' in reason


def test_b1_adv2_row_c_with_fully_valid_module_identity_declines(evidence):
    """Adversarial ADV2: row C carrying a python-module identity with the
    REAL module and its CORRECT digest, with the native artifact ABSENT.
    Before the binding, this ACTIVATED row C with handle=None (a native
    row with zero verified artifact)."""
    import hashlib
    module_rel = 'src/solweig_light/_native_dispatch/lw_b_control.py'
    real = policy.REPO_ROOT / module_rel
    module_copy = evidence.root / module_rel
    module_copy.parent.mkdir(parents=True, exist_ok=True)
    module_copy.write_bytes(real.read_bytes())
    record = evidence.row_record(artifact_identity={  # row stays 'C'
        'kind': 'python-module',
        'module_path': module_rel,
        'module_sha256': hashlib.sha256(real.read_bytes()).hexdigest(),
    })
    reason = _declines_to_a(
        evidence, record,
        outcome=make_declined_outcome(status='declined-absent',
                                      reason='no native_generated resources'))
    assert reason.startswith('[malformed]')
    assert 'cross-wire' in reason


def test_fail_closed_reasons_are_private_not_printed(evidence, capsys):
    _declines_to_a(evidence, evidence.row_record())
    out, err = capsys.readouterr()
    assert out == '' and err == ''
    assert policy.policy_reasons()  # recorded privately instead


# ---------------------------------------------------------------------------
# Legacy unknown values never become auto
# ---------------------------------------------------------------------------


@pytest.mark.parametrize('value', ['numba', 'NUMBA', 'bogus', 'auto', '0',
                                   ' native-ish', 'nat'])
def test_unknown_legacy_values_stay_legacy_a_even_with_valid_records(
        evidence, value):
    record = evidence.row_record()
    selection = policy.resolve_lw_backend(
        env={'SOLWEIG_LIGHT_LW_BACKEND': value},
        registry=evidence.registry(record), load_outcome=make_loaded_outcome(),
        repo_root=evidence.root)
    assert (selection.row, selection.mode) == \
        (policy.ROW_A, 'legacy-unknown-value')
    assert 'historical Numba behavior' in selection.reason


@pytest.mark.parametrize('value', ['', '   '])
def test_blank_values_behave_like_unset_for_auto(evidence, value):
    """Legacy treats set-but-blank identically to unset (both normalize to
    ''); the auto policy applies to both."""
    record = evidence.row_record()
    selection = policy.resolve_lw_backend(
        env={'SOLWEIG_LIGHT_LW_BACKEND': value},
        registry=evidence.registry(record), load_outcome=make_loaded_outcome(),
        repo_root=evidence.root)
    assert selection.row == policy.ROW_C
    assert selection.mode == 'auto-qualified'


# ---------------------------------------------------------------------------
# Expert path: loud, never downgraded, records not consulted
# ---------------------------------------------------------------------------


@pytest.mark.parametrize('value', ['native', 'ispc', 'NATIVE', ' native\t'])
def test_expert_loaded_never_downgrades(evidence, value):
    record = evidence.row_record()  # would qualify C anyway; irrelevant
    outcome = make_loaded_outcome()
    selection = policy.resolve_lw_backend(
        env={'SOLWEIG_LIGHT_LW_BACKEND': value},
        registry=evidence.registry(record), load_outcome=outcome,
        repo_root=evidence.root)
    assert selection.row == policy.ROW_C
    assert selection.mode == 'expert-explicit'
    assert selection.expert is True
    assert selection.expert_error is None
    assert selection.expert_or_raise() is selection


def test_expert_declined_raises_taxonomy_loudly(evidence):
    error = RuntimeError('no qualified native artifact in this installation')
    outcome = make_declined_outcome(status='declined-absent',
                                    reason='no native_generated resources',
                                    error=error)
    selection = policy.resolve_lw_backend(
        env={'SOLWEIG_LIGHT_LW_BACKEND': 'native'},
        registry=evidence.registry(), load_outcome=outcome,
        repo_root=evidence.root)
    # Never row A, never silent: the selection CARRIES the error and the
    # caller must raise it.
    assert selection.row == policy.ROW_C
    assert selection.expert is True
    assert selection.expert_error is error
    with pytest.raises(RuntimeError, match='no qualified native artifact'):
        selection.expert_or_raise()
    assert 'MUST raise' in selection.reason


def test_expert_declined_even_with_qualified_b_records(evidence, tmp_path):
    """The selector never swaps an explicit expert request for a qualified
    B row (or silent A): expert resolution is records-blind."""
    module_rel = 'src/solweig_light/_native_dispatch/lw_b_control.py'
    real = policy.REPO_ROOT / module_rel
    import hashlib
    b_record = evidence.row_record(row='B', artifact_identity={
        'kind': 'python-module', 'module_path': module_rel,
        'module_sha256': hashlib.sha256(real.read_bytes()).hexdigest(),
    })
    outcome = make_declined_outcome(status='declined-corrupt',
                                    reason='packaging defect')
    selection = policy.resolve_lw_backend(
        env={'SOLWEIG_LIGHT_LW_BACKEND': 'ispc'},
        registry=evidence.registry(b_record), load_outcome=outcome,
        repo_root=policy.REPO_ROOT)
    assert selection.row == policy.ROW_C
    assert selection.expert is True
    assert selection.record is None


# ---------------------------------------------------------------------------
# Host class helper
# ---------------------------------------------------------------------------


def test_current_host_class_shape():
    host = policy.current_host_class()
    assert isinstance(host, str) and '-' in host
    platform_os, _, arch = host.partition('-')
    assert platform_os and arch
