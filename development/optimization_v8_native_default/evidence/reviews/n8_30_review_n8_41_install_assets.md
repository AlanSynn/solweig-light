# n841-3 install_assets Review — APPROVE-WITH-NOTES

- **Reviewer**: n8-rev-n8-41 (independent; did not author; vendoring reviewed separately)
- **Reviewed**: uncommitted working tree of `/Users/alansynn/Workspace/solweig-v8-native` @ HEAD `194cb973` — pyproject.toml, `_native_dispatch/__init__.py`, `test_installed_wheel_gates.py`, suite-rewritten `installed_gates.json`, plus the untracked author draft
- **Companion record**: `n8_30_review_n8_41_install_assets.json` (full executed evidence)
- **Scope honored**: no commits, no timed work, writes only under `evidence/reviews/`; loadavg ≥ 2.5 before every execution (6.10 / 4.69 / 3.80)

## Verdict: APPROVE-WITH-NOTES

All 8 commissioned claims **PASS**. No blocking defects, no required repairs.

## Per-claim results

| # | Claim | Result | Key evidence |
|---|-------|--------|--------------|
| 1 | pyproject: one glob, only the registry matches | PASS | one-line diff; recursive find: `qualification_registry.json` is the only `.json` under `_native_dispatch` |
| 2 | `__init__.py` docstring-only | PASS | single +15/−0 hunk entirely inside the module docstring; zero code |
| 3 | +2 tests non-vacuous on pre-existing fixtures | PASS | json/zipfile/`GATE_RECORD`/`REPO_ROOT`/`_run`/`built_wheel`/`wheel_venv` all pre-exist at HEAD (7→9 tests); membership+byte-identity+`records==[]` asserted; probe asserts row A / auto-legacy / expert False / record None, registry under site-packages, reason `[absent]`, `[malformed]`/`unreadable/invalid` banned; non-vacuous structurally (no MANIFEST.in, no include-package-data, no SCM plugin — without the glob the wheel cannot contain the file, the recorded D4 accident) |
| 4 | Gates diff honest re-record + one additive section | PASS | statuses 3→4 (only addition `registry_gate: passed`); both no-env gates still `blocked:host-memory-pressure`; surface still passed; deferred list parsed-JSON identical; file reflects the coordinator's pytest-861 rerun via the suite's own sessionfinish writer |
| 5 | Suites | PASS | installed 13/6 taken as coordinator-given; **full tree rerun: 1967 passed / 6 skipped / 0 failed in 200.87s** = baseline + exactly 2 tests; same 6-skip decomposition; 4 warnings are the pre-existing set |
| 6 | Promotion-gate disposition | PASS | single `_assess_promotion` call site inside `validate_row_record`, which the auto path never reaches (returns at `[absent]` before validation; expert path never consults records); `import promotion_gate` outside the defensive try → ModuleNotFoundError propagates (loud, never mis-qualifies); the vendoring draft's "FileNotFoundError on import" wording confirmed inaccurate and the correction exact |
| 7 | Repo-tree shipped-state invariance | PASS | no src selection code in the diff; `test_explicit_expert_env_stays_with_legacy_route` untouched, integration+dx segment 16 passed |
| 8 | dx cosmetic | PASS | `branch_surface.json` does list the stale pre-glob `package_data`; `_asserted_leaves` does not assert `package_data`; dx gates green |

## Notes (none blocking)

1. **N1**: the glob `_native_dispatch/*.json` is non-recursive — a future JSON under `_native_dispatch/region/` would not ship. No such file today.
2. **N2**: `registry_gate` carries absolute run-scoped paths — consistent with the file's existing convention.
3. **N3**: the draft's `guard_property_for_future_work` states the right invariant (missing tool never lets a record qualify; shipped-empty registry keeps the path unreachable) — keep it if the wheel story is revisited.
4. **N4**: the committed gates file will be the coordinator's run (pytest-861), not the author's (pytest-858); both were 13/6 — the commit message should not attribute the file to the author's run.
5. **N5**: membership-test non-vacuity rests on deterministic setuptools ship mechanics plus the D4-era accident record, not on a re-executed pre-diff build (a second build was out of scope); judged sufficient.

## Bottom line

The change does exactly what it claims and nothing more: the wheel now ships the byte-identical empty registry (designed `[absent]` fail-closed instead of the missing-file accident), repo-tree behavior is untouched, the promotion tool deliberately stays maintainer-tree-only with a loud, mis-qualification-proof failure mode, and the evidence trail is an honest suite-written re-record with one additive gate. Ready to commit.
