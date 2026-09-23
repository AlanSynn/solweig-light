# Review: N8-41 candidate native wheel (n8-41-wheel) — n8_30_review_n8_41_candidate_wheel

- schema: sw8-n8-30-review-v1 · verdict: **APPROVE** · 2026-09-23T04:49Z
- object: the uncommitted 5M+5N diff on HEAD `a19e22db`, against `evidence/wheels/n8_41_candidate_wheel_draft.json` incl. `integrator_adjudication`; author n8-41-wheel; reviewer independent.
- tree at review start: exactly the module_map paths (staged dylib gitignored; `installed_gates.json` clean = HEAD version).

## D1 — independent trace: CONFIRM (agree with ACCEPT)

- **Env reads**: exactly two literal reads in the vendored driver — `PATH` at `src/solweig_light/_native_dispatch/build_native.py:128` (`_build_env`), `SOLWEIG_LIGHT_ISPC` at `:169` (`discover_ispc`). No module-level reads.
- **Runtime unreachability**: `installed_loader.py` touches only constants (`:145/:147/:149/:151`) and `driver.verify_generation` (`:463`). `verify_generation` (`build_native.py:577-648`) is JSON + hashing + `macho_structure_error` (pure byte walk) + `fma_audit` (regex) — **no subprocess, no env, no `shutil.which`**. grep: zero src callers of `run_tool`/`discover_ispc`/`macho_facts`/`native_build_impl`/`_build_env`/`source_fallback_manifest`/`atomic_publish` outside build_native.py itself. native_handle dlopens by absolute path; lw_default_policy never calls any of them. Executed corroboration: the installed-origin probe ran `attempt_load()` in a fresh venv with `{HOME, PATH=/usr/bin:/bin, LANG}` and **no backend variables** → `loaded`; selection probe → row A.
- **Self-validation mechanics**: `dx_snapshot._env_vars_read_from_tree` (dx_snapshot.py:320-350) is AST-based over literal reads and returns **sorted** lists → the file scans to exactly `['PATH', 'SOLWEIG_LIGHT_ISPC']`; second/changed read, renamed/removed file, or moved key all fail the pop+equality. Frozen baseline contains **zero** `build_native`/`SOLWEIG_LIGHT_ISPC` occurrences (grep -c = 0) → the single pop is necessary and sufficient. Gate green in my runs.
- **Nuance (N1)**: the scanner is blind to dynamic reads (`_build_env`'s SDKROOT/DEVELOPER_DIR/MACOSX_DEPLOYMENT_TARGET loop, `:130-134`) — pre-existing semantics shared with the frozen baseline; the build-time-only property rests on the call graph, which is solid.

## D4 — reword accurate, no gate semantics changed

The conftest `deferred[0]` reword's four clauses all verified true (candidate ships the staged generation; qualification absent; registry empty → row A with artifact loaded — `test_installed_native_selection_stays_row_a`; the gate's real requirement "automatic native selection, actual native work counted" still unmet → skip stays correct). Pure string reword in one list element.

## Focus items — all PASS (executed)

1. **Staging purity**: full gate BEFORE staging (`setup.py:113`); copy2 + per-member sha256 proof (mismatch → rmtree + raise); `try/finally` unstage (`:115-118`) incl. emptied container; hard-kill leftover → next pure build **fails loud** in `assert_pure_package_tree` — never leaks into py3-none-any. Generation is flat (4 files) so the hash proof is exact.
2. **Gate directions executed**: pip-level bogus request → nonzero + "not a directory" + **zero wheels**; byte-flipped dylib → "hash" rejection; renamed dir → "name mismatch"; session pure wheel py3-none-any with zero native members (all green in my installed rerun).
3. **Installed-origin probe**: loaded from site-packages, generation dir + resolved vendored driver both inside site-packages, `repo_sys_path == []`, kernel/dylib sha vs staged manifest, ABI pins — green.
4. **Selection invariance**: registry-gate tests untouched (`git diff --stat` empty) and green; shipped registry byte-identical; A/auto-legacy/[absent] with the artifact present AND loaded. No src read of `SOLWEIG_LIGHT_PACKAGE_NATIVE` (docstring only).
5. **Vendored driver**: both sides sha256 `dd2467b3dcf8c46cfef69591339334d5a42d62ab788fa7fdf768757a15604d50` (== record); drift-alarm test byte-compares; `_build_native` repo-home-first keeps in-repo behavior unchanged, packaged fallback loud-fails naming both paths.
6. **setup.py inertness + delete-then-raise**: no-request path is pass-through + purity guard; on wheel violation ALL recent wheels are unlinked BEFORE raising, inside the single pip process — nothing mislabeled survives to upload. (Minor: the `started - 5` mtime window could sweep a <5 s-old unrelated wheel into deletion — maintainer-tree, fail-loud, N3.)
7. **installed_gates.json**: HEAD version at review start (no native_wheel keys — consistent with restore-before-commit); my rerun regenerated it, verified **additive** (native_wheel* GATE_RECORD keys, statuses passed; `-` lines are only the known tmp-dir/budget-figure churn). Restore before commit; not author drift.

## Reruns (load discipline held; load was HIGH throughout — no quiet window occupied)

- installed: **22 passed / 6 skipped** (166.36s) — matches author and coordinator; skip decomposition unchanged.
- full tree (one invocation): **1981 passed / 6 skipped / 0 failed** (213.23s) = 1972 baseline + exactly the 9 new tests; same 4 pre-existing warnings.

## Notes

- **N1**: D1 scanner-blindness nuance (above).
- **N2** (doc-only, reword at N8-50): `test_deferred_gates.py` module docstring still pins `@ 16cdc56c`; its skip reason's "no packaged native artifact exists on this branch yet" is now literally false in-suite. The skip itself remains correct.
- **N3**: bdist_wheel mtime-window deletion sweep (maintainer-tree only, fail-loud).
- **N4**: staging hash-proof is top-level-files-only — exact for the flat generation; extend if generations ever nest.
- **N5**: `installed_gates.json` regenerated by my runs — expected; restore before commit.
- **N6** (positive): run-scoped wheel sha honestly labeled — identity is pinned through content (dylib/manifest sha256); D2 (scan in assembly gate) preserves vendoring byte-identity and keeps subprocesses out of the runtime verify path; D3 (bare-basename install name, no post-hoc mutation) preserves content-derived identity, `@rpath` accepted at the N8-50 re-freeze.

## Conclusion

Ordinary pip stays the guarded pure fallback; the native request gates before staging, stages byte-identically, unstages in finally, and deletes-then-fails on any violation; the installed loader loads the PACKAGED generation with zero repo reach; selection stays auto → row A. D1 independently confirmed; D4 accurate; reruns match. **APPROVE.**
