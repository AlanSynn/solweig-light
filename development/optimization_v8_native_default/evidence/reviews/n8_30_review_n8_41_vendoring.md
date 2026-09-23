# N8-41 Vendoring Review — APPROVE-WITH-NOTES

- **Reviewer**: n8-rev-n8-41 (independent; did not author the vendoring)
- **Reviewed**: uncommitted working tree of `/Users/alansynn/Workspace/solweig-v8-native` @ HEAD `14a98188` (branch `perf/native-optimization`), i.e. the N8-41 early vendoring by n8-41-vendor per n841-7/n841-8
- **Companion record**: `n8_30_review_n8_41_vendoring.json` (full executed evidence)
- **Scope honored**: no commits, no builds, no timed benchmarking; writes only under `evidence/reviews/` and `/tmp`

## Verdict: APPROVE-WITH-NOTES

All nine commissioned claims **PASS** with executed evidence. No blocking defects, no required repairs.

## Per-claim results

| # | Claim | Result | Key evidence |
|---|-------|--------|----------------|
| 1 | Byte-identical R moves (region x3, direct_aosoa, lw_b_control) | PASS | sha256 HEAD-vs-worktree IDENTICAL x5 (`2f795cc2…`, `37d3de47…`, `ccd9aff9…`, `cb92a175…`, `95fab457…`); staged renames 0/0, so every deviation is an unstaged hunk — all read in full |
| 2 | `_lw_dispatch.py` rewrite | PASS | bootstrap machinery deleted; tables/decline paths context-only (unchanged); zero env reads; selector ImportError now propagates; no HEAD test ever asserted silent-None (n8-40 probe was manual), so nothing to update — integration stays 9 |
| 3 | D1 pipeline.py hunk | PASS | exactly one import line + comment; try/except semantics untouched; foreign-`region` hazard removed by the qualified path (n8-40 R3) |
| 4a | D3 deferred `_build_native` + PEP 562 | PASS | wheel simulation in `/tmp` (no experiments tree): import clean, `_BUILD_NATIVE==[]`, `build_native` absent from sys.modules, first use raises loud ImportError naming the anchor; gates compare identical values; absent-registry wheel fails closed to row A |
| 4b | D9 evidence-anchor repair | PASS | native suite 194 passed / **0 skipped** — the evidence-audit test ran via `experiments_dir('native','evidence')`; FileNotFoundError -> identical skip message |
| 5 | installed_gates.json honesty | PASS | 130-line diff is run-metadata only (paths/pids/timestamps/memory numbers/run-scoped digests/cache hashes); every `status` identical old-vs-new; no gate/requirement/threshold edits |
| 6 | Module identity + monkeypatch visibility | PASS | sys.modules identity True; patched `DEFAULT_REGISTRY_PATH` cited verbatim in the decline reason; HEAD's own monkeypatch tests (197/198/336) pass |
| 7 | Grep audits | PASS | zero bare machinery imports in src/tests; experiments-dir sys.path appends exactly 2: packaging/conftest (pre-existing suite) + artifacts/conftest:46 (the surfaced deliberate one); src-side 3 lazy documented repo anchors |
| 8 | Suites | PASS | integration 9; policy+dx 95; native 194/0 skipped; region+layout+numba+artifacts 1378; **full tree 1965 passed / 6 skipped / 0 failed in 199.51s** (one invocation, matches baseline). Skips = 4 unconditional deferred gates + 2 environmental host-memory-pressure. Loadavg checked before every run (8.34/4.99/8.76/8.22/6.07) |
| 9 | Shipped-state inertness + registry | PASS | fresh interpreter: resolve -> row A, sys.modules gains only `_native_dispatch(+__init__)` and `.lw_default_policy`; registry copy sha256-identical (`3d3911da…`), original empty-diff; shipped-registry integration test passed |

## Notes (numbered; none blocking)

1. **N1 — unnumbered deviation**: `experiments/optimization_v8/native/quiet_window_abc.py` is genuinely modified (vendored-package import rewiring + dead layout sys.path entry removed) but appears only under `not_vendored`, not as D1–D11. Change reviewed, correct; integrator should name this file in the commit message so draft inventory and diff stay 1:1.
2. **N2 — docstring precision**: "a broken selector module propagates its import error" covers module-import failure; a present selector fed an unreadable/malformed registry fails closed to row A (`[malformed] …` — executed). Intended fail-safe, but one clarifying clause at next touch would prevent misreading.
3. **N3 — env-surface accounting**: `native_handle.py:655` child-env passthrough (`{**os.environ, 'ISPC': ispc}`) and `lw_default_policy.py:580` pre-existing expert-value intercept moved into src verbatim with their files; DX gate green (95 passed). Recorded so the frozen-surface contract is understood to count override read sites (D2 dedup), not child-env construction or the pre-existing intercept.
4. **N4 — stale docstring (doc-only)**: `tests/optimization_v8/policy/test_legacy_env_parity.py:15` still says "The selector exists in experiments/ only".
5. **N5 — cosmetic**: one >88-col import line in `tests/optimization_v8/native/test_aosoa_native_admission.py`.
6. **N6 — commit mechanics**: staged index holds byte-identical renames; all deviations are unstaged. The commit must also include the untracked `src/solweig_light/_native_dispatch/__init__.py`, `qualification_registry.json`, and the two evidence drafts for self-consistency.
7. **N7 — digest pins**: lw_b_control "digests still match pinned records" verified transitively (worktree file sha256-identical to HEAD's reviewed file; sha256-pinned integration tests pass). Pinned evidence archives not re-hashed directly (time budget; chain sufficient for the vendoring claim).

## Bottom line

The vendoring is semantics-preserving exactly as claimed: shipped state still resolves row A through the records-blind selector, decline taxonomy and dispatch tables are untouched, the single override env-read site is preserved via the D2 dedup, the two caught defects (D3, D9) are real and repaired non-vacuously, and the full tree reproduces the baseline count bit-for-bit at the skip level. The integrator can commit; N1–N7 are notes, not repairs.
