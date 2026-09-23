# N9 F5 — installed no-env verification + main delta safety (independent reviewer record)

Reviewer: n9-reviewer. Worktree `/Users/alansynn/Workspace/solweig-v8-native`, HEAD `2c4ba021`
(N9 F4 removal/packaging + records). Runner: worktree `.venv` python 3.12.13 (pytest only; the
installed-gate conftest builds its own `uv`-seeded build/wheel/source venvs offline from
`~/.cache/uv/archive-v0`). All runs: `NUMBA_NUM_THREADS=2`,
`NUMBA_CACHE_DIR=<worktree>/.numba_cache`.

## Verdict

**CONDITIONAL PASS — two F4-introduced defects found, corrected, and re-verified green.**

The F4 disposition itself (bounded Numba stream as the shipped longwave default, N8 native row
and qualification machinery archived repo-only) is correctly realized in `src/` and in the
packaging configuration. The defects were both in the *realization of the removal*, not in the
design: (1) a collection-blocking SyntaxError in the archived gate module, (2) a stale in-tree
`build/` directory that silently resurrected the archived machinery into built wheels. After the
two corrections below, every non-environmental installed gate passes from a clean build.

## Correction set (2)

### C1 — `test_native_wheel_gates.py` was uncollectable (SyntaxError)

The F4 archive edit (`08d05cef`, fixup `a7c03171`) inserted `import pytest` +
`pytest.skip(..., allow_module_level=True)` at lines 3-8, *before* the module's
`from __future__ import annotations` (formerly line 50). Python forbids `__future__` imports
after any statement, so `pytest tests/optimization_v8/installed` died in collection with
"from __future__ imports must occur at the beginning of the file" and NO gate in this directory
could run. Correction: moved `from __future__ import annotations` to the top (after the GPL
comment block, which may legally precede it) and removed the now-duplicate old line. The
archive semantics are unchanged: the module-level skip still fires at import time, labelled
with the F3 NATIVE_LOSS / F4 closed_cpu_only reason.

Note: the F4 gate-run numbers reported for this worktree therefore cannot have included a
successful collection of `tests/optimization_v8/installed` at HEAD `2c4ba021`/`a7c03171`.

Update during verification: the integrator landed `22876fb6` ("N9 F4 fixup 2: repair whole-tree
test collection") while F5 was running; it commits this reviewer's reorder verbatim (empty diff
against my working copy) plus same-class conftest repairs in `tests/optimization_v8/{artifacts,
loader,native}/conftest.py`. The fixup touches only `tests/`; `branch_surface.json` was
relabelled `--commit 22876fb6` with a byte-identical surface, confirming src-identity.

### C2 — stale `build/` resurrected the archived machinery into the wheel (gate CAUGHT it)

First suite run in this environment FAILED the two inverted F4 wheel gates:

- `test_wheel_ships_no_qualification_machinery` — the built wheel contained all six archived
  members: `solweig_light/_native_dispatch/{build_native.py, installed_loader.py,
  lw_default_policy.py, lw_native_aosoa.py, native_handle.py, qualification_registry.json}`.
- `test_installed_product_has_no_selector_module` — `import
  solweig_light._native_dispatch.lw_default_policy` in the installed venv printed `PRESENT`.

Root cause: `/Users/alansynn/Workspace/solweig-v8-native/build/` (mtime Sep 23 00:08 — hours
before the F4 removal commits at 12:23) still held the N8-era tree under `build/lib/` and
`build/lib.macosx-11.0-arm64-cpython-312/`. In-tree PEP 517 builds reuse `build/lib` without
deleting sources that vanished from `src/`, so `pip wheel .` re-packaged the archived modules
even though `src/solweig_light/_native_dispatch/` at HEAD contains only the live modules
(`aplus_decode.py`, `direct_aosoa.py`, `lw_b_control.py`, `lw_stream.py`, `region/`).

Tainted wheel preserved as evidence: `solweig_light-0.1.0.dev0-py3-none-any.whl`,
sha256 `c40ef6f504d3dc8fa3f49e5cbd9278b3a4c0a76d3ebf21a2cceb7da6a3e29d4a`, 85 members, 6
offenders — see `f5_tainted_wheel_namelist.json` (same directory).

Correction: purged `build/` and `src/solweig_light.egg-info/` (both gitignored; nothing tracked
touched). Clean re-run: **13 passed, 7 skipped, 0 failed** in 153s; new wheel sha256
`7d78a93f2d7ac17c…`; the banned-substring gate and the installed-venv ABSENT probe both pass.

Handover note this proves: **wheels must be built with a purged `build/`; the F4 inverted gates
are the enforcement and they work** — this defect was found by the gate, not by inspection.

## Wheel / archive disposition (obligation 2) — VERIFIED

- `src/solweig_light/_native_dispatch/` ships only the live default-route modules; the six
  archived modules + `region_native_reduce.py` live only under
  `experiments/optimization_v8/native_dispatch/` (repo-only research archive).
- `[tool.setuptools.packages.find] where = ["src"]` — `experiments/` (outside `src/`) can never
  be packaged. `[tool.setuptools.package-data]` whitelist has no `_native_dispatch/*.json` and
  no `native_generated/**`; `backends/native/*` retained for the B7-32 expert route.
- Stale `__pycache__/*.pyc` for the archived modules exist in the worktree `src/` tree but do
  not ship (clean wheel verified) and cannot import without sources (PEP 3147).

## branch_surface.json regeneration (obligation 4 — recorded)

Regenerated with `dx_snapshot.py capture --tree <worktree> --commit 2c4ba021 --out …/dx_baseline/branch_surface.json`
(replaces the stale N8-era record at commit `16cdc56c`). Findings:

- `surface_divergences(main_surface@14e88876, branch_surface@2c4ba021, skip={companion_distribution.console_scripts})`
  = **0 paths**. Every DX asserted leaf (distribution metadata, package.all, workflows,
  runtime_options.fields, cli.*, …) is main-identical. Consequently the installed-runtime
  surface gate passes with allowlist `{}` — no entry needs the branch cross-check.
- The intentional F4 divergences are all BELOW asserted-leaf granularity: the structural
  default route lives inside radiation internals; the policy module's removal never touches
  `package.all` (it is subpackage-inventory, not asserted); and the env surface is recorded but
  NOT asserted.
- **Honesty note (capture blind spot):** `SOLWEIG_LIGHT_LW_BACKEND` is read at
  `radiation/cylinder_longwave.py` (`os.environ.get(_LW_BACKEND_ENV, …)` via a module-level
  constant), which the AST env-read capture does not see (it only matches literal args). The
  seam read is real and intentional (expert stand-down KEPT: `native|ispc` -> return None ->
  trusted legacy loop); the dispatch path itself (`radiation/_lw_dispatch.py`,
  `_native_dispatch/lw_stream.py`) reads NO environment variables, exactly as claimed.
  `env_vars_read` main-vs-branch differs (branch additionally reads
  `SOLWEIG_LIGHT_NATIVE_CACHE`, `SOLWEIG_LIGHT_PREPARED_VIS`, `SOLWEIG_LIGHT_FUSED_RAD`,
  `SOLWEIG_LIGHT_PATCH_CLASS_TABLES`, `GDAL_CACHEMAX`, `SOLWEIG_LIGHT_WORKER_POOL`; main reads
  only `EE_PROJECT`) — none of these are in the frozen assert set, but the difference is now on
  record in the regenerated `branch_surface.json`.

## Small chronology evidence (obligation 3) — VERIFIED, within frozen protocol

`optimization_n9_final/evidence/f4_small_chronology_default/` holds the tmp-run copies of
`tests/differential/test_pipeline_reference.py::test_chronological_tiff_pipeline[small-*]`
(warm `pipeli0` + cold `pipeli1`), each a genuine chronological TIFF-to-TIFF run at 35x32 with
**24** bands per output (the brief's "24/48-step" reads as the two 24-record runs; there is no
48-band artifact here). Each `comparison.json` records max-abs vs the frozen original-CPU
reference under `benchmarks/protocols/comparison_v1.json`:

| field | max_abs | protocol bound |
|---|---|---|
| TMRT | 6.1e-5 | 0.01 |
| UTCI | 6.9e-5 | 0.02 |
| WBGT | 5.7e-5 | 0.02 |
| Kdown / Kup / Ldown / Lup | <= 4.6e-4 | flux atol 0.05 |
| Ta, Wind, Shadow | exactly 0.0 | exact |

Both runs identical; cold (SVF-regenerating) path equals warm. Real evidence, honest bounds.

## Installed-gate suite results (this environment)

| run | build/ state | result |
|---|---|---|
| 1 | stale (N8-era) | 2 failed (banned-members, selector PRESENT), 11 passed, 7 skipped |
| 2 (after C1+C2) | purged | 13 passed, 7 skipped, 0 failed (153s) |
| 3 (no-env-only retry) | purged | 1 passed, 2 skipped — both product runs `[host-memory-pressure]` |
| 4 (retry after 3-min pause) | purged | 1 passed, 2 skipped — unchanged `[host-memory-pressure]` |
| 5 (+ release-owner gates R1/R2) | purged | **15 passed, 7 skipped, 0 failed** (155s) |
| 6 (noenv-only, + remedy diagnostic) | purged | 1 passed, 2 skipped — remedy refused identically (deficit ~1.15 GB) |
| 7 (FINAL full suite, single build `aa184a71…`) | purged | **15 passed, 7 skipped, 0 failed** (159s); product runs blocked with 4 labelled attempts each — RECORD OF NOTE |

Run 7 is the committed record: one build (`solweig_light-0.1.0.dev0-py3-none-any.whl`, sha256
`aa184a71bc16d015…`) carries the passing surface gate (zero unexpected divergences), both
release-owner gates R1/R2 green, and api/cli gate records with FOUR attempts each — three
pinned no-env attempts plus the labelled `gdal-cachemax-64-diagnostic`, all
`blocked:host-memory-pressure`. The CLI fixture's inline retry loop was given the same
remedy-diagnostic attempt as the API pipeline (parity fix), and both fixtures now compute
status from the PINNED attempts only (`remedy_note` discloses a remedy-assisted pass if one
ever lands). Per release-owner instruction: no further retries; the block is recorded as a
measured environmental limitation.

Skip labels (never fake passes): 1 archive skip (`test_native_wheel_gates.py`, F4 reason),
4 deferred N8-41/42 skips, 2 `[host-memory-pressure]` skips of the API/CLI no-env product runs.

Passing substance (run 2, from the conftest's `installed_gates.json`): wheel tags pure /
`py3-none-any`; no solweig_gpu collision; core deps canonical-match MAIN_SURFACE with no
forbidden accelerators; every installed module resolves inside site-packages (never repo src/);
`__version__` matches MAIN_SURFACE; DX surface by `capture_runtime_surface_subprocess` =
`runtime_introspection`, zero unexpected divergences, `check_divergences_allowed` clean; banned
machinery absent from the wheel; selector import ABSENT in the installed venv; source-fallback
install + tiny Numba-path API + console script green.

**Residual (environmental, labelled):** the no-env API/CLI product runs were refused by resource
admission across SIX runs total (initial + 2 retries + the release-owner-directed quiet-host
re-run + the remedy diagnostic), with attempts and full `ResourceAdmissionError` text recorded
in `installed_gates.json`. The release-owner remedy (cap `GDAL_CACHEMAX` per the error's own
hint) is now implemented in `_run_noenv_pipeline` as a permanently attached, distinctly-labelled
fourth attempt (`gdal-cachemax-64-diagnostic`) and was refused IDENTICALLY — by construction:
the admission charge is `default_gdal_cache_bytes()` = 5% of probed physical RAM
(`runtime_memory.py:485-494`), the planner never reads the env var, and the documented remedy
requires passing `gdal_cache_bytes` via RuntimeOptions, which the pinned no-env contract
forbids. The skip label carries this fact. Deficit history: 48 MB (initial window) then
~1.15 GB (quiet-host re-run — the shared host's available view slid from ~3.37 GB to ~3.18 GB
between readings; 28 users, loadavg 4.5-6.4). These gates are self-driving and must be re-run
in a genuinely quiet window (needs available-view >= ~4.3 GB for budget >= 2.15 GB); everything
else they assert — no-net guard, readonly site-packages, empty native cache, populated numba
cache, frozen CLI flags — is exercised by the passing gates around them. The fixture's
remedy-diagnostic attempt and the `mode_label`/`task` rewording (N8-23 -> N9 F4
closed_cpu_only) are uncommitted, ready for the F5 commit.

## Release-owner gates added during F5 (team-lead items 1 and 2)

Two positive gates appended to `tests/optimization_v8/installed/test_installed_wheel_gates.py`
(both green in run 5; uncommitted):

- **R1 `test_installed_lw_dispatch_env_surface_is_the_frozen_stand_down`** — AST-scans the
  INSTALLED package's LW dispatch region (`radiation/_lw_dispatch.py`,
  `radiation/cylinder_longwave.py`, everything under `_native_dispatch/`) and asserts the
  env-read map is EXACTLY `{cylinder_longwave.py: {196: SOLWEIG_LIGHT_LW_BACKEND,
  216: SOLWEIG_LIGHT_LW_BACKEND}}`. The scanner resolves module-constant indirection
  (`_LW_BACKEND_ENV`), records `<unresolved>`/`<subscript>` reads so they fail rather than
  escape, and the line numbers are pinned deliberately — moving the seam must fail the gate and
  force a conscious re-freeze. Dry-run negative control (whole-package scan) confirms the
  scanner still sees the legitimate out-of-region reads
  (`SOLWEIG_LIGHT_NATIVE_CACHE`, `SOLWEIG_LIGHT_PREPARED_VIS`, `EE_PROJECT`,
  `SOLWEIG_LIGHT_GVF_PREPARE`, `SOLWEIG_LIGHT_FUSED_RAD`, `SOLWEIG_LIGHT_PATCH_CLASS_TABLES`,
  `GDAL_CACHEMAX`, `SOLWEIG_LIGHT_WORKER_POOL`). Note this gate covers what the dx_snapshot
  env-read capture structurally cannot (constant-indirect reads are invisible to it — the blind
  spot recorded above).
- **R2 `test_installed_wheel_ships_and_wires_aplus_decode`** — the wheel must carry
  `solweig_light/_native_dispatch/aplus_decode.py`, and the installed product must bind its
  `_decode_at_plus` into BOTH consumer seams (module-identity probe: `cylinder_longwave.
  _decode_at is aplus_decode._decode_at_plus` and `patch_radiation._decode_at is
  aplus_decode._decode_at_plus`). Encodes "SHIPPED and WIRED, not banned" positively so a
  future archive pass cannot silently drop or orphan the module.

## Residual notes (non-blocking)

- `installed_gates.json` `mode_label`/`task` still carry N8-23 wording ("no packaged native
  artifact exists before N8-41"), stale relative to the F4 closed_cpu_only disposition.
  Cosmetic; the gate record is otherwise accurate.
- The stale-`build/` hazard is structural: ANY future module removal taints subsequent wheel
  builds in tree until purged. Recommend a purge step (or `pip wheel` from a pristine copy) be
  mandated in the F7 packaging/manifest instructions.

## Integrator addendum (team-lead, F7 close; post-review events)

- **Run 7 (pytest-951)** landed after this review's six-run history: a fresh full-suite
  run that verifies the conftest status-logic fix (`blocked:host-memory-pressure` now
  judged over the PINNED attempts only, not the labelled remedy attempt) and refreshes
  `installed_gates.json` on a rebuilt wheel (`aa184a71bc16d015` — same tree content,
  new zip entry timestamps). Outcome unchanged: api/cli product runs blocked at all
  4 labelled attempts each; surface + R1 + R2 + banned-members green. Environmental
  block confirmed terminal for this campaign.
- The `mode_label`/`task` staleness residual above is RESOLVED on disk as of run 7:
  the record now reads "N8-23; disposition N9 F4 closed_cpu_only" with the archived
  machinery wording (installed_test_helpers.py rewording, landed in the F5 evidence
  commit and re-recorded by run 7).
- The stale-`build/` purge recommendation is adopted verbatim in
  `optimization_n9_final/MERGE_MANIFEST.json` (packaging_handover.D2_wheel_taint)
  and FINAL_SELECTION.json commands.wheel_build_handover.
