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
"""N8-22: disabled-by-default qualification policy selector for the
longwave-primary backend rows (dossier 06_default_dispatch.md).

This module PREPARES selection; it is not wired into ``src/`` and enables
nothing.  ``resolve_lw_backend()`` maps three inputs -- legacy env override,
installed-artifact state (the N8-21 ``LoadOutcome``), and qualification
records -- onto one of three rows:

* ``A``  legacy Numba dense kernels
  (``solweig_light.radiation.cylinder_longwave._longwave_primary`` /
  ``..._serial``) -- the shipped default and the FAIL-CLOSED target;
* ``B``  Numba AoSoA consumer
  (``experiments/optimization_v8/numba/lw_b_control.lw_primary_b``);
* ``C``  native AoSoA consumer
  (``experiments/optimization_v8/native/lw_native_aosoa.primary_aosoa``).

THE LAW (packet gate): every non-legacy row ships DISABLED.  B/C activate
only on an explicit qualification record whose referenced evidence still
validates end-to-end at resolve time.  Absent, stale, malformed or
not-yet-qualified records -- and every error path in this module -- fail
CLOSED to row A, never to B/C.  The shipped registry
(``qualification_registry.json`` next to this module) is EMPTY: with it,
the auto path provably resolves to A today even when a fully qualified
native artifact is installed (dossier: "The repository must not ship
example rows with placeholder success").

DECISION ORDER (dossier 06 "Decision hierarchy", steps 1-2 and 5):

1. Legacy explicit override first, byte-compatibly with the live
   dispatcher ``cylinder_longwave._lw_kernel``: the value of
   ``SOLWEIG_LIGHT_LW_BACKEND`` is normalized exactly as there
   (``get(env, '').strip().lower()``).  ``native``/``ispc`` are the ONLY
   recognized expert values; any other NON-EMPTY string retains the
   historical silent-Numba behavior and NEVER becomes auto (DX_CONTRACT:
   "Unknown legacy strings retain historical Numba behavior rather than
   becoming auto by accident").  Unset/empty means auto.
2. Expert path (``native``/``ispc``): an explicit request is never
   downgraded to silent A.  It resolves through the N8-21 installed
   loader's explicit semantics: loaded artifact -> row C executes; any
   decline -> the selection carries the taxonomy error
   (``MissingNativeArtifact`` / ``CorruptNativeArtifact`` /
   ``UnsupportedNativeISA``) which the caller MUST raise (loud), exactly as
   ``installed_loader.load_explicit`` defines.  Qualification records are
   NOT consulted for an explicit request: expert forcing is deliberate
   user intent and overrides promotion policy (dossier step 1).
3. Auto path: records for row C are evaluated before row B (the promotion
   gates already require C to beat B1 in every qualified cell, so a
   qualified C dominates); within a row, records evaluate in registry
   order and the first fully valid one wins.

NO NEW DX: this module reads exactly one environment variable -- the
legacy public ``SOLWEIG_LIGHT_LW_BACKEND`` -- adds no env var, no output,
no file, and performs no IO at import (registry/artifact/evidence access
is lazy, bounded and quiet; declines are recorded only in the private
in-memory ``policy_reasons()`` log, never printed).  No network, no
subprocess, no writes, ever.

QUALIFICATION RECORD SCHEMA (``sw8-lw-default-row-record-v1``) -- the
authoritative shape N8-31/N8-32 transcribe measured results into and N8-40
wires; a pending, never-activatable template ships under ``templates/``::

    {
      "schema": "sw8-lw-default-row-record-v1",
      "status": "qualified",              # ONLY 'qualified' can activate;
                                          # the shipped template says 'pending'
      "row": "C",                         # 'B' or 'C'; a record naming 'A' is
                                          # malformed: A is the fail-closed
                                          # target and never carries records
      "host_class": "darwin-arm64",       # exact ``current_host_class()`` key;
                                          # capability judgement itself lives in
                                          # the N8-21 loader (LoadOutcome status)
      "created_utc": "2026-09-22T00:00:00Z",
      "source_commit": "<40 lowercase hex>",   # commit of the qualified tree;
                                          # FORMAT-CHECKED ONLY, not anchored to
                                          # the current HEAD (the enforced
                                          # identity anchors are artifact/module
                                          # digests and evidence shas) -- N8-31/
                                          # N8-32 transcription must deliberately
                                          # pin the campaign commit, as with the
                                          # promotion record's own source_sha
      "artifact_identity": {              # what the row executes, pinned;
                                          # kind is BOUND to row (B1): row C
                                          # accepts only
        "kind": "installed-native-generation",   # this kind, row B only
        "generation": "<N8-20 generation id>",   # "python-module" (below);
        "kernel_sha256": "<64 hex>",             # cross-wires are malformed
        "dylib_sha256": "<64 hex>"
        # row B instead: {"kind": "python-module",
        #                "module_path": "experiments/optimization_v8/numba/lw_b_control.py",
        #                "module_sha256": "<64 hex>"}
      },
      "promotion_record": {               # PROMOTION_POLICY gates, re-verified
        "path": "<repo-relative .json>",  # at resolve time by
        "sha256": "<64 hex>",             # tools/.../promotion_gate.assess();
        "schema": "sw8-default-promotion-record-v1"
      },                                  # policy_data_passed is recomputed,
                                          # never trusted from this field
      "cells": ["<primary cell ids covered, subset of the promotion record>"],
      "independent_review": {             # dossier: policy provenance requires
        "path": "<repo-relative .json>",  # independent review; verdict must be
        "sha256": "<64 hex>"              # an APPROVE* string (repo convention,
      },                                  # e.g. 'APPROVE-WITH-NOTES')
      "notes": "optional free text"
    }

Staleness taxonomy (all fail closed to A, reason prefixed accordingly):
absent      no registry / empty records;
malformed   schema/shape/type violations, escape-y evidence paths;
stale       an identity anchor no longer matches at resolve time -- the
            installed artifact generation/kernel/dylib differ (row C), the
            consumer module digest differs (row B), or a referenced
            evidence file is missing or its sha256 changed after
            certification;
unqualified-host  record host_class != current host (ordinary, quiet);
not-qualified     status != 'qualified', promotion gates no longer assess
            as passed, or review verdict is not an approval.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform as _platform
import sys
import threading
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

# ---------------------------------------------------------------------------
# Public constants (no IO, no heavy imports at module scope on purpose)
# ---------------------------------------------------------------------------

# The ONE legacy public env var (byte-compat with cylinder_longwave's
# _LW_BACKEND_ENV; parity is pinned by tests, src is not touched here).
LW_BACKEND_ENV = 'SOLWEIG_LIGHT_LW_BACKEND'

ROW_A = 'A'
ROW_B = 'B'
ROW_C = 'C'

# Documentation references for N8-40 wiring (strings, never imports: the
# policy layer must stay import-light and must not pull numba/ctypes).
ROW_ENTRIES = {
    ROW_A: 'solweig_light.radiation.cylinder_longwave._longwave_primary'
           '(_serial)',
    ROW_B: 'experiments/optimization_v8/numba/lw_b_control.lw_primary_b',
    ROW_C: 'experiments/optimization_v8/native/lw_native_aosoa.primary_aosoa',
}

# Legacy recognized expert values (exact set _lw_kernel dispatches on,
# after strip().lower()).
EXPERT_VALUES = frozenset(('native', 'ispc'))

ROW_RECORD_SCHEMA = 'sw8-lw-default-row-record-v1'
REGISTRY_SCHEMA = 'sw8-lw-default-registry-v1'
PROMOTION_RECORD_SCHEMA = 'sw8-default-promotion-record-v1'
STATUS_QUALIFIED = 'qualified'

# Repo review convention (e.g. optimization_v7_backends/evidence/reviews/
# b7_30_ispc_review.json): verdicts are uppercase APPROVE[-WITH-NOTES].
_REVIEW_APPROVED_PREFIX = 'APPROVE'

# C before B: every qualified C cell already beat B1 by >= 1.05 (promotion
# gate), so a valid C record dominates a valid B record.
ROW_PRECEDENCE = (ROW_C, ROW_B)

MODULE_DIR = Path(__file__).resolve().parent
REPO_ROOT = MODULE_DIR.parents[2]
DEFAULT_REGISTRY_PATH = MODULE_DIR / 'qualification_registry.json'

STATUS_LOADED = 'loaded'  # mirrors installed_loader.STATUS_LOADED

_REASON_LOG_LIMIT = 64
_UNSET = object()


class PolicyRegistryError(ValueError):
    """Registry file present but unparseable/shape-invalid (fail closed)."""


# ---------------------------------------------------------------------------
# Selection result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Selection:
    """One resolved backend row plus why it was chosen.

    ``mode`` is one of:

    * ``'expert-explicit'``        env asked for native/ispc (loud path);
    * ``'legacy-unknown-value'``   unrecognized non-empty legacy env value
                                   keeps historical silent Numba behavior;
    * ``'auto-qualified'``         a record survived validation (future);
    * ``'auto-legacy'``            auto path failed closed to row A.
    """

    row: str
    mode: str
    reason: str
    expert: bool = False
    record: dict | None = None
    load_outcome: object | None = None
    expert_error: BaseException | None = None

    @property
    def entry(self) -> str:
        return ROW_ENTRIES[self.row]

    def expert_or_raise(self) -> 'Selection':
        """The loud expert contract (N8-10/N8-21): an explicit request that
        could not load RAISES the taxonomy error instead of returning a
        silent row-A fallback."""
        if self.expert_error is not None:
            raise self.expert_error
        return self


# ---------------------------------------------------------------------------
# Private diagnostics (bounded, in-memory, never printed)
# ---------------------------------------------------------------------------

_LOCK = threading.Lock()
_REASON_LOG: list[str] = []
_ASSESS_CACHE: dict[str, object] = {}


def policy_reasons() -> tuple[str, ...]:
    """Private diagnostics: recorded fail-closed / decline reasons."""
    with _LOCK:
        return tuple(_REASON_LOG)


def reset_for_tests() -> None:
    with _LOCK:
        _REASON_LOG.clear()
        _ASSESS_CACHE.clear()


def _log(reason: str) -> None:
    with _LOCK:
        _REASON_LOG.append(reason)
        del _REASON_LOG[:-_REASON_LOG_LIMIT]


# ---------------------------------------------------------------------------
# Host class (in-memory probe; capability judgement stays in N8-21)
# ---------------------------------------------------------------------------


def current_host_class() -> str:
    """Deterministic host-class key a record must match exactly.

    Pure ``sys.platform`` + normalized ``platform.machine()``; ISA feature
    probing (NEON etc.) belongs to the N8-21 loader, whose LoadOutcome this
    selector consumes.  No file IO.
    """
    machine = _platform.machine().lower()
    aliases = {'aarch64': 'arm64', 'amd64': 'x86_64', 'x64': 'x86_64'}
    return f'{sys.platform}-{aliases.get(machine, machine)}'


# ---------------------------------------------------------------------------
# Lazy helpers: registry file, promotion gate, installed loader
# ---------------------------------------------------------------------------


def _is_hex(value, length: int) -> bool:
    if not isinstance(value, str) or len(value) != length:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _repo_contained_path(repo_root: Path, rel) -> Path | None:
    """Repo-relative evidence path -> contained absolute Path (or None).

    Lexical checks first (absolute/traversal/NUL rejected), then resolved
    containment inside the repo root -- same discipline as the N8-21
    member gate, applied to the evidence references a record may carry.
    """
    if not isinstance(rel, str) or not rel or '\x00' in rel:
        return None
    pure = PurePosixPath(rel)
    if pure.is_absolute() or rel.startswith(('/', '\\')) \
            or len(pure.drive) or len(pure.root):
        return None
    parts = pure.parts
    if not parts or any(part in ('', '.', '..') for part in parts):
        return None
    candidate = repo_root.joinpath(*parts)
    if not candidate.resolve().is_relative_to(repo_root.resolve()):
        return None
    return candidate


def load_registry(path=None) -> dict:
    """Read and shape-check a registry file (lazy IO; raises
    PolicyRegistryError on malformed input -- the auto path catches it and
    fails closed)."""
    registry_path = Path(path) if path is not None else DEFAULT_REGISTRY_PATH
    try:
        parsed = json.loads(registry_path.read_text())
    except (OSError, ValueError) as exc:
        raise PolicyRegistryError(
            f'qualification registry {registry_path} unreadable/invalid '
            f'JSON ({exc!r})') from exc
    if not isinstance(parsed, dict) \
            or parsed.get('schema') != REGISTRY_SCHEMA \
            or not isinstance(parsed.get('records'), list):
        raise PolicyRegistryError(
            f'qualification registry {registry_path} is not a '
            f'{REGISTRY_SCHEMA} object with a "records" list')
    return parsed


def shipped_registry_records() -> tuple[dict, ...]:
    """The records in the SHIPPED registry (packet gate: must be empty)."""
    return tuple(load_registry()['records'])


def _assess_promotion(parsed_promotion: dict):
    """Re-verify PROMOTION_POLICY gate arithmetic through the packet tool
    (``optimization_v8_native_default/tools/promotion_gate.py``; pure
    computation, stdlib-only).  The record's say-so is never trusted."""
    key = hashlib.sha256(
        json.dumps(parsed_promotion, sort_keys=True).encode()).hexdigest()
    with _LOCK:
        if key in _ASSESS_CACHE:
            return _ASSESS_CACHE[key]
    tools = REPO_ROOT / 'optimization_v8_native_default' / 'tools'
    if str(tools) not in sys.path:
        sys.path.insert(0, str(tools))
    import promotion_gate  # noqa: E402  (lazy, stdlib-only)
    try:
        report = promotion_gate.assess(parsed_promotion)
    except Exception as exc:  # defensive tool boundary; reason is recorded
        report = {'policy_data_passed': False,
                  'errors': [f'promotion gate raised {exc!r}']}
    with _LOCK:
        _ASSESS_CACHE[key] = report
    return report


def _default_attempt_load():
    """Lazily resolve the installed artifact state through N8-21.

    Only reached when a C record is actually a candidate (or the expert
    path needs the outcome); with the shipped empty registry the auto path
    never touches the filesystem beyond reading the registry itself."""
    artifacts = REPO_ROOT / 'experiments' / 'optimization_v8' / 'artifacts'
    if str(artifacts) not in sys.path:
        sys.path.insert(0, str(artifacts))
    import installed_loader  # noqa: E402  (lazy; N8-21)
    return installed_loader.attempt_load()


def _outcome_or_default(load_outcome):
    if load_outcome is _UNSET or load_outcome is None:
        outcome = _default_attempt_load()
        return outcome
    return load_outcome


def _outcome_identity(outcome) -> dict:
    """(generation, kernel_sha256, dylib_sha256) of a loaded outcome,
    taken from the N8-10 handle's no-IO ``identity()`` fingerprint."""
    handle = getattr(outcome, 'handle', None)
    ident = handle.identity() if handle is not None else {}
    stamp = ident.get('stamp') or {}
    return {
        'generation': getattr(outcome, 'generation', None),
        'kernel_sha256': ident.get('kernel_sha256'),
        'dylib_sha256': stamp.get('dylib_sha256'),
    }


# ---------------------------------------------------------------------------
# Record validation (fail closed; every miss returns (False, reason))
# ---------------------------------------------------------------------------


def _validate_common_shape(record, host_class: str) -> str | None:
    """Schema/status/row/host/commit checks; a reason string when invalid."""
    if not isinstance(record, dict):
        return f'[malformed] record is not a JSON object ({record!r})'
    if record.get('schema') != ROW_RECORD_SCHEMA:
        return (f'[malformed] schema {record.get("schema")!r} != '
                f'{ROW_RECORD_SCHEMA!r}')
    if record.get('status') != STATUS_QUALIFIED:
        return (f'[not-qualified] record status {record.get("status")!r} '
                f'cannot activate (only {STATUS_QUALIFIED!r} can; shipped '
                f'templates stay pending)')
    row = record.get('row')
    if row not in (ROW_B, ROW_C):
        return (f'[malformed] row {row!r} must be {ROW_B!r} or {ROW_C!r}; '
                f'{ROW_A!r} is the fail-closed target and never carries '
                f'a record')
    if record.get('host_class') != host_class:
        return (f'[unqualified-host] record host class '
                f'{record.get("host_class")!r} != current {host_class!r} '
                f'(ordinary quiet decline; the row stays disabled here)')
    if not _is_hex(record.get('source_commit'), 40):
        return (f'[malformed] source_commit '
                f'{record.get("source_commit")!r} is not 40 lowercase hex')
    return None


def _validate_artifact_identity(record, load_outcome, repo_root: Path
                                ) -> str | None:
    ident = record.get('artifact_identity')
    kind = ident.get('kind') if isinstance(ident, dict) else None
    # B1 (review n8_30_review_n8_22_policy): the identity KIND is bound to
    # the ROW -- row C executes an installed native generation, row B the
    # certified Python consumer module -- and the binding is enforced
    # BEFORE either row's staleness anchor runs. A cross-wired record
    # whose foreign-kind fields are individually fully valid (a row-B
    # record carrying a native identity that matches a loaded outcome; a
    # row-C record carrying a correct module digest) is malformed and
    # fails closed, so a row can never activate through the other row's
    # anchor (B with a tampered consumer module, or C with no artifact).
    required_kind = ('installed-native-generation'
                     if record.get('row') == ROW_C else 'python-module')
    if kind != required_kind:
        return (f'[malformed] row {record.get("row")!r} requires '
                f'artifact_identity.kind {required_kind!r}, got {kind!r} '
                f'(row/identity cross-wire)')
    if kind == 'installed-native-generation':
        if not (isinstance(ident.get('generation'), str) and ident['generation']
                and _is_hex(ident.get('kernel_sha256'), 64)
                and _is_hex(ident.get('dylib_sha256'), 64)):
            return (f'[malformed] row-C artifact_identity needs generation,'
                    f' kernel_sha256 and dylib_sha256 (got {ident!r})')
        outcome = _outcome_or_default(load_outcome)
        status = getattr(outcome, 'status', None)
        if status != STATUS_LOADED:
            return (f'[stale] record targets an installed native '
                    f'generation but no artifact is loaded here '
                    f'(status {status!r}: '
                    f'{getattr(outcome, "reason", "not attempted")})')
        actual = _outcome_identity(outcome)
        for field in ('generation', 'kernel_sha256', 'dylib_sha256'):
            if actual.get(field) != ident.get(field):
                return (f'[stale] artifact {field} {actual.get(field)!r} != '
                        f'certified {ident.get(field)!r}')
        return None
    if kind == 'python-module':
        module = _repo_contained_path(repo_root, ident.get('module_path'))
        if module is None or not _is_hex(ident.get('module_sha256'), 64):
            return (f'[malformed] row-B artifact_identity needs a contained'
                    f' module_path and 64-hex module_sha256 (got {ident!r})')
        try:
            digest = hashlib.sha256(module.read_bytes()).hexdigest()
        except OSError:
            return f'[stale] certified consumer module {module} is missing'
        if digest != ident.get('module_sha256'):
            return (f'[stale] consumer module {module} digest {digest} != '
                    f'certified {ident.get("module_sha256")}')
        return None
    return (f'[malformed] artifact_identity kind {kind!r} is not '
            f'"installed-native-generation" (row C) or "python-module"'
            f' (row B)')


def _validate_referenced_json(ref: object, repo_root: Path, what: str
                              ) -> tuple[dict | None, str | None]:
    """Shared path/sha/read/parse for referenced evidence files."""
    if not isinstance(ref, dict):
        return None, f'[malformed] {what} block is not an object ({ref!r})'
    path = _repo_contained_path(repo_root, ref.get('path'))
    if path is None:
        return None, (f'[malformed] {what} path {ref.get("path")!r} is not'
                      f' a contained repo-relative path')
    if not _is_hex(ref.get('sha256'), 64):
        return None, (f'[malformed] {what} sha256 {ref.get("sha256")!r} is'
                      f' not 64 hex')
    try:
        payload = path.read_bytes()
    except OSError:
        return None, f'[stale] {what} file {path} is missing'
    digest = hashlib.sha256(payload).hexdigest()
    if digest != ref.get('sha256'):
        return None, (f'[stale] {what} file {path} sha256 {digest} != '
                      f'certified {ref.get("sha256")} (evidence changed '
                      f'after certification)')
    try:
        parsed = json.loads(payload)
    except ValueError as exc:
        return None, f'[malformed] {what} file {path} is invalid JSON ({exc!r})'
    if not isinstance(parsed, dict):
        return None, f'[malformed] {what} file {path} is not a JSON object'
    return parsed, None


def validate_row_record(record, *, host_class=None, load_outcome=_UNSET,
                        repo_root=None) -> tuple[bool, str]:
    """Full fail-closed validation of one qualification record.

    Returns ``(True, 'qualified')`` only when every anchor holds RIGHT
    NOW: shape, status, host class, artifact identity against the loaded
    N8-21 outcome (row C) or the consumer module digest (row B), the
    referenced promotion record still passing ``promotion_gate.assess``
    with the declared cells among its primary cells, and the referenced
    independent review still carrying an APPROVE verdict.
    """
    host = current_host_class() if host_class is None else host_class
    root = Path(repo_root) if repo_root is not None else REPO_ROOT

    reason = _validate_common_shape(record, host)
    if reason is not None:
        return False, reason
    reason = _validate_artifact_identity(record, load_outcome, root)
    if reason is not None:
        return False, reason

    promotion, reason = _validate_referenced_json(
        record.get('promotion_record'), root, 'promotion_record')
    if reason is not None:
        return False, reason
    if promotion.get('schema') != PROMOTION_RECORD_SCHEMA:
        return False, (f'[malformed] promotion record schema '
                       f'{promotion.get("schema")!r} != '
                       f'{PROMOTION_RECORD_SCHEMA!r}')
    report = _assess_promotion(promotion)
    if not report.get('policy_data_passed'):
        errors = report.get('errors') or ['unknown gate failure']
        return False, (f'[not-qualified] promotion gates not satisfied: '
                       f'{"; ".join(errors[:3])}')
    primary_ids = {cell.get('id') for cell in promotion.get('cells') or []
                   if isinstance(cell, dict)
                   and cell.get('kind') == 'primary'}
    cells = record.get('cells')
    if not isinstance(cells, list) or not cells \
            or not all(isinstance(cell, str) for cell in cells) \
            or not set(cells) <= primary_ids:
        return False, (f'[malformed] cells {cells!r} must be a non-empty '
                       f'subset of the promotion record primary cells '
                       f'{sorted(primary_ids)}')

    review, reason = _validate_referenced_json(
        record.get('independent_review'), root, 'independent_review')
    if reason is not None:
        return False, reason
    verdict = review.get('verdict')
    if not isinstance(verdict, str) \
            or not verdict.startswith(_REVIEW_APPROVED_PREFIX):
        return False, (f'[not-qualified] independent review verdict '
                       f'{verdict!r} is not an approval '
                       f'({_REVIEW_APPROVED_PREFIX}*)')

    return True, 'qualified'


# ---------------------------------------------------------------------------
# The selector
# ---------------------------------------------------------------------------


def _explicit_value(env) -> str:
    """Legacy env normalization, byte-identical to _lw_kernel.

    A non-str value from a PROGRAMMATIC env mapping coerces to '' (auto);
    unreachable through os.environ, whose values are always str (review
    note N1 of n8_30_review_n8_22_policy: documented coercion)."""
    mapping = os.environ if env is None else env
    raw = mapping.get(LW_BACKEND_ENV, '')
    return raw.strip().lower() if isinstance(raw, str) else ''


def resolve_lw_backend(env=None, *, registry=_UNSET, load_outcome=_UNSET,
                       repo_root=None, host_class=None) -> Selection:
    """Resolve the LW-primary backend row (pure given its inputs; resolve
    once per workflow at the N8-40 call site, dossier step 1).

    ``env``          mapping or None for the real environment (only
                     ``SOLWEIG_LIGHT_LW_BACKEND`` is ever read);
    ``registry``     parsed registry dict, a path, or _UNSET for the
                     shipped default file;
    ``load_outcome`` an N8-21 ``LoadOutcome`` (or _UNSET to let this
                     module ask the installed loader, lazily, only when a
                     C record is a candidate or the expert path runs).
    """
    value = _explicit_value(env)

    # 1. Expert explicit request: never downgraded, never silent. --------
    if value in EXPERT_VALUES:
        outcome = _outcome_or_default(load_outcome)
        if getattr(outcome, 'status', None) == STATUS_LOADED:
            selection = Selection(
                ROW_C, 'expert-explicit',
                f'explicit SOLWEIG_LIGHT_LW_BACKEND={value!r}: installed '
                f'artifact loaded; qualification records are not consulted '
                f'for an explicit request (deliberate user intent overrides '
                f'promotion policy)', expert=True, load_outcome=outcome)
        else:
            selection = Selection(
                ROW_C, 'expert-explicit',
                f'explicit SOLWEIG_LIGHT_LW_BACKEND={value!r}: artifact '
                f'declined ({getattr(outcome, "reason", "not attempted")}) '
                f'-- the caller MUST raise the taxonomy error '
                f'(expert_or_raise); a silent downgrade to row A is '
                f'forbidden', expert=True, load_outcome=outcome,
                expert_error=getattr(outcome, 'error', None))
        return selection

    # 2. Unknown legacy value: historical silent Numba, never auto. -------
    if value != '':
        selection = Selection(
            ROW_A, 'legacy-unknown-value',
            f'unknown legacy {LW_BACKEND_ENV}={value!r} retains the '
            f'historical Numba behavior; it never becomes auto')
        _log(selection.reason)
        return selection

    # 3. Auto: fail closed to A unless a record survives validation. -----
    if registry is _UNSET:
        try:
            parsed_registry = load_registry()
        except PolicyRegistryError as exc:
            parsed_registry = None
            reason = f'[malformed] {exc}'
    elif isinstance(registry, (str, Path)):
        try:
            parsed_registry = load_registry(registry)
        except PolicyRegistryError as exc:
            parsed_registry = None
            reason = f'[malformed] {exc}'
    elif isinstance(registry, dict):
        parsed_registry = registry
        if parsed_registry.get('schema') != REGISTRY_SCHEMA:
            parsed_registry = None
            reason = (f'[malformed] registry schema '
                      f'{registry.get("schema")!r} != {REGISTRY_SCHEMA!r}')
        elif not isinstance(parsed_registry.get('records'), list):
            parsed_registry = None
            reason = '[malformed] registry records is not a list'
    else:
        parsed_registry = None
        reason = f'[malformed] registry argument {registry!r} not understood'

    if parsed_registry is None:
        selection = Selection(ROW_A, 'auto-legacy', reason)
        _log(selection.reason)
        return selection

    records = parsed_registry.get('records') or []
    if not records:
        selection = Selection(
            ROW_A, 'auto-legacy',
            '[absent] no qualification records in the registry (shipped '
            'state: every non-legacy row disabled; auto resolves to legacy '
            'A)')
        _log(selection.reason)
        return selection

    host = current_host_class() if host_class is None else host_class
    root = Path(repo_root) if repo_root is not None else REPO_ROOT
    # Pre-pass: shape-class declines are logged once, not once per row.
    entries: list[dict] = []
    first_why: str | None = None
    declines = 0

    def _decline(why: str, log_line: str | None = None) -> None:
        nonlocal first_why, declines
        _log(log_line if log_line is not None else why)
        if first_why is None:
            first_why = why
        declines += 1

    for record in records:
        if not isinstance(record, dict):
            _decline(f'[malformed] registry entry is not an object: '
                     f'{record!r}')
        elif record.get('row') not in (ROW_B, ROW_C):
            _decline(f'[malformed] registry entry row '
                     f'{record.get("row")!r} is not {ROW_B!r}/{ROW_C!r}; '
                     f'ignored (A never carries records)')
        else:
            entries.append(record)
    for row in ROW_PRECEDENCE:
        for record in entries:
            if record.get('row') != row:
                continue
            ok, why = validate_row_record(
                record, host_class=host, load_outcome=load_outcome,
                repo_root=root)
            if ok:
                selection = Selection(
                    row, 'auto-qualified',
                    f'row {row} activated by qualification record '
                    f'(source_commit {record.get("source_commit")}, host '
                    f'{host}, cells {record.get("cells")})',
                    record=record,
                    load_outcome=_outcome_or_default(load_outcome)
                    if row == ROW_C else None)
                return selection
            _decline(why, log_line=f'row {row} record declined: {why}')
    # Fail closed to A, surfacing the first classified decline privately.
    reason = first_why or ('[absent] no well-formed qualification records '
                           'in the registry')
    if declines > 1:
        reason += f' (and {declines - 1} more decline(s); see ' \
                  f'policy_reasons())'
    selection = Selection(ROW_A, 'auto-legacy', reason)
    _log(reason)
    return selection


__all__ = [
    'LW_BACKEND_ENV', 'ROW_A', 'ROW_B', 'ROW_C', 'ROW_ENTRIES',
    'EXPERT_VALUES', 'ROW_RECORD_SCHEMA', 'REGISTRY_SCHEMA',
    'PROMOTION_RECORD_SCHEMA', 'STATUS_QUALIFIED', 'ROW_PRECEDENCE',
    'DEFAULT_REGISTRY_PATH', 'PolicyRegistryError', 'Selection',
    'current_host_class', 'load_registry', 'shipped_registry_records',
    'validate_row_record', 'resolve_lw_backend', 'policy_reasons',
    'reset_for_tests',
]
