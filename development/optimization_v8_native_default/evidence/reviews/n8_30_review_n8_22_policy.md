# N8-30 review of N8-22 (policy selector) — APPROVE (resubmission)

Review: `optimization_v8_native_default/evidence/reviews/n8_30_review_n8_22_policy.json` (authoritative, per-obligation detail).
Target: `experiments/optimization_v8/policy/` + `tests/optimization_v8/policy/` @ 16cdc56c. Reviewer did not author N8-22.

## Verdict: APPROVE — B1 repaired and independently re-verified (initial verdict: REJECT)

### Resubmission recheck (2026-09-22)

**B1 repair verified.** `_validate_artifact_identity` now derives `required_kind` from `record['row']` (row C ⇔ `installed-native-generation`, row B ⇔ `python-module`) and declines `[malformed] … (row/identity cross-wire)` **before** either staleness anchor runs. The original adversarial records were re-run verbatim by the reviewer against the repaired selector:

| Probe | Initial result | Repaired result |
|---|---|---|
| ADV1: row B + native identity matching the loaded outcome, consumer module tampered | **B auto-qualified** | A, `[malformed]` cross-wire |
| ADV2: row C + python-module identity, correct digest, artifact absent | **C auto-qualified** | A, `[malformed]` cross-wire |
| Sanity: correctly-wired row C + loaded outcome | C auto-qualified | C auto-qualified (no over-block) |
| Sanity: correctly-wired row B + consistent digest | B auto-qualified | B auto-qualified (no over-block) |

New regressions are faithful (foreign-kind fields fully populated and individually valid — ADV1's native identity matches the loaded outcome exactly, so only the binding can decline): `test_b1_adv1_…` and `test_b1_adv2_…`, both asserting the `[malformed]` prefix and `cross-wire`. The old accidental matrix case now declines through the binding with the right reason.

**Notes discharged**: N2 — `test_review_verdict_matching_is_case_sensitive` pins `approve`/`Approve` → `[not-qualified]`; N3 — template notes document the kind⇔row binding and the format-checked-not-HEAD-anchored `source_commit`/`source_sha` semantics with explicit N8-31/N8-32 transcription guidance; N1 — `_explicit_value` docstring documents the non-str coercion.

**Post-repair runs (reviewer's)**: policy suite **88 passed** (84 + 2 B1 regressions + 2 case-sensitivity params); full tree `tests/optimization_v8/ -q` **1954 passed, 6 skipped, 0 failed** (193.68s). The previously-classified installed-suite conftest failure is also gone — the sibling author independently applied this review's recommended fix (`installed_test_helpers` unique-name import at `test_installed_wheel_gates.py:23`); not an N8-22 change. The author's 1832/117 session remained unreproduced across all four full-tree-condition runs of this review (1948/1, 1864/1, 1954/0, plus installed standalone).

---

## Initial review (superseded verdict: REJECT) — findings below as originally issued

**B1 (blocking) — `artifact_identity.kind` is not bound to `record.row`** (`lw_default_policy.py:416-455`). Two adversarial records, constructed and executed by the reviewer through the real `resolve_lw_backend`, ACTIVATE when the review charter requires a decline:

- **ADV1**: row `B` + `kind='installed-native-generation'` matching a loaded outcome → row **B activated** while the certified consumer module `lw_b_control.py` was tampered with after certification. The row-B staleness anchor the module's own law names ("the consumer module digest differs") never runs.
- **ADV2**: row `C` + `kind='python-module'` with a correct module digest and load outcome `declined-absent` → row **C activated with zero native artifact** (`load_outcome.handle=None`). A native-consumer row selected with no verified artifact is the exact scenario this chain exists to prevent.

The author's defect-matrix test intends cross-wire rejection (`kind='python-module'` on a row-C record → `[malformed]`) but passes only because the fabricated record lacks `module_path`; populate the foreign-kind fields and it activates. Schema `sw8-lw-default-row-record-v1` is declared authoritative for N8-31/N8-32/N8-40 — do not freeze a validator that mis-enforces its own documented row/identity binding.

**Repair**: bind kind to row in `_validate_artifact_identity` (C ⇔ `installed-native-generation`, B ⇔ `python-module`; else `[malformed]`) + two regression tests with fully-populated foreign-kind fields asserting the decline prefix. Small, local fix. **— REPAIRED AND REVERIFIED in resubmission (see above).**

Shipped state remains safe: registry empty, module unwired, never imported by `src/` — no observable DX change today. Repair-and-resubmit.

## Per-obligation

1. **Legacy parity — PASS.** Normalization byte-identical to `_lw_kernel` (`cylinder_longwave.py:195`); every value class pinned against the live dispatcher (unset/empty/whitespace/`numba`/bogus/`auto` → plain kernel identity asserts; `native`/`ispc`/case/whitespace variants → native wrapper closure asserts; classification cross-check test). Unknown non-empty values → row A silent, never auto; blank behaves as unset. Missing-ispc RuntimeError byte-pinned (verified against `native_lw.py:78-83`). `src/` has zero tracked modifications. Note N1: injected non-str env value coerces to `''` (unreachable via `os.environ`).
2. **Fail-closed — PASS after B1 repair (initial: FAIL, B1 only).** All five decline classes pinned by tests; genuine staged artifact through the real N8-21 loader still resolves A with empty registry; path escapes (`../..`, `/etc/...`) → `[malformed]`; sha drift → `[stale]`; wrong host → `[unqualified-host]`. Auto reaches B/C only inside the `if ok:` branch after full validation, C before B.
3. **Re-assessment — PASS.** `promotion_gate.assess` recomputed on the sha-verified parsed file; liar field `policy_data_passed=True` over ratios 1.0 → `[not-qualified]`; sha mismatch → `[stale]` — both pinned.
4. **Expert path — PASS.** Runs before registry parsing (records-blind, pinned incl. qualified-B case); declines carry the taxonomy error via `expert_or_raise`, never silent A. Note N4: expert resolves through the N8-21 installed loader, not the legacy dev-build path — N8-40 must make that routing decision explicitly per DX_CONTRACT.
5. **No-IO / no-surface — PASS.** Fresh-interpreter audit hook allows only the module's own files through import and a pure resolve; exactly one env var (AST-pinned, matches `src` constant); `import solweig_light` never leaks the module; src env surface equals the frozen N8-01 baseline; registry ships empty; template pending + inert.
6. **Interference — selector NOT implicated** (my runs below).
7. **Ownership — PASS.** Untracked additions only; no `src/` changes; no registry population; no timing.

## Independent failure classification

| Run | Result |
|---|---|
| `tests/optimization_v8/policy/ -q` | **84 passed** (3.01s) |
| `tests/optimization_v8/ -q` | **1 failed, 1948 passed, 6 skipped** (200.74s) |
| full tree `--ignore=.../policy` | **same 1 failure**, 1864 passed, 6 skipped (196.30s) |
| `tests/optimization_v8/installed/ -q` alone | 11 passed, 6 skipped (passes standalone) |

The one reproducible failure is `installed/test_installed_wheel_gates.py::test_surface_gate_recorded` — a bare `from conftest import GATE_RECORD` at test time resolving to `region/conftest.py` (no `__init__.py` anywhere under `tests/optimization_v8`; eleven sibling conftests contest the bare name; region is collected last). It is invariant to the policy suite's presence and its fix belongs to the installed suite (use a fixture or a uniquely named helper, the `policy_test_helpers` pattern). The author's 1832/117 report did **not** reproduce in any of my runs, and the author's own committed log (`policy/results/full_tree_run1_withall_tbline.log`) records the same 1948/1 outcome as mine — the 117-failure session was differently conditioned (consistent with their thread-cap/fork hypothesis); nothing implicates the selector module (no import side effects, policy green alone and in-session).

## Notes (non-blocking)

N1 non-str env coercion (theoretical) · N2 lowercase `approve` declines but unpinned — add a test · N3 `source_commit`/`source_sha` format-checked only, not HEAD-anchored (consistent with documented taxonomy; state it in N8-31 transcription guidance) · N4 N8-40 expert-path routing decision · N5 multi-decline surfaced reason is the C-row-first decline (deterministic; pointer to `policy_reasons()` present).
