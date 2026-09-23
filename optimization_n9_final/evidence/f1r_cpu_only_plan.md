# F1R: CPU-only closure plan (applied only if native loses F3)

Release-owner plan for packet optimization_n9_final. Preconditions: F3 selects
`closed_cpu_only` (or native cannot be qualified). Applies to source branched
from `perf/native-optimization` @ 7abe526a (or the F3-qualified forward commit);
target main 14e88876. Inventory basis: `evidence/f0_inventory.json`.

Principle (MERGE_SCOPE): default is the best VERIFIED CPU/Numba route; the N8
no-op selector is not shipped to demonstrate effort; all evidence and the B7-32
expert route are preserved; native non-selection is recorded as
`not_selected_for_this_release`.

## 1. Exact removal list (installed path)

Each entry states what it is, why it exists (dependency), and what breaks.

| # | Target | What / dependency | Breaks if removed |
|---|--------|-------------------|-------------------|
| R1 | `src/solweig_light/radiation/cylinder_longwave.py:181-197` `_lw_region_route` | N8-40 seam; sole src caller of `_lw_dispatch.region_route`; exists only to reach dormant rows B/C | Nothing on the default path: today it returns None after the selector. Tests that drive the region route become archived-feature tests (T3). The call site :396-399 collapses to the unconditional legacy loop. |
| R2 | `src/solweig_light/radiation/_lw_dispatch.py` (whole file, 196 lines) | N8-40 dispatch; only caller is R1; `_execute_row` is the whole-scene AoSoA materializer (`produce_blocks_aosoa(...,0,total,...)`) never reachable shipped | Only the archived region tests. No default or expert behavior touches it once R1 lands. |
| R3 | `src/solweig_light/_native_dispatch/` — entire subpackage becomes repo-only research: `lw_default_policy.py`, `qualification_registry.json`, `direct_aosoa.py`, `lw_b_control.py`, `lw_native_aosoa.py`, `native_handle.py`, `installed_loader.py`, `build_native.py`, `region/*` | N8-22 selector, N8-11/12/13 consumers, N8-10/20/21 loader/build, N8-14 pool. Reachable only via R1/R2 or the loader paths the selector gates | Nothing installed: with R1 gone no default import reaches the package (`import solweig_light` already never imports it — pinned by `tests/optimization_v8/policy/test_legacy_env_parity.py`, which stays active and becomes trivially stronger). Move under an explicit non-installed research location (e.g. `experiments/optimization_v8/vendored_dispatch/`) or keep in place with packaging exclusion (§5); keep the immutable historical copies per MERGE_SCOPE. |
| R4 | `src/solweig_light/pipeline.py:312-318` — region `shutdown_all_pools` consult in the per-timestep finally | N8-40 teardown; exists only because the region owner could exist | Nothing: the import-and-call is a no-op in every CPU-only run. This also removes the heaviest dormant import (region_plan+region_pool) from every default tile run. |
| R5 | `engine.py:1653-1662` tri-state argument — `parallel=True if threads_per_worker > 1 else None` | N8-40b: `None` exists solely so the R1 consult fires at H<=1 | Nothing: restore plain boolean `parallel=threads_per_worker > 1` (§2). |
| R6 | `pyproject.toml` package-data delta: `backends/native/*.ispc`, `*.sh`, `_native_dispatch/*.json`, `backends/native_generated/**` | N8-41 wheel content for a product that never qualified | Nothing user-facing: the shipped registry was always empty (row A). MERGE_SCOPE explicitly forbids shipping maintainer build/verification programs as runtime deps just because the empty registry made them unreachable. `backends/native/*.py` disposition in §5. |
| R7 | `setup.py` (N8-41 native-wheel shim) | Build shim for a native wheel product that is `not_selected_for_this_release`; self-described "deletable" | Returns the project to the pre-N8-41 pure build. The pure-tree purity guard dies with it, but without the shim nothing can be staged, so nothing can leak. Delete or leave inert — deletion recommended for honesty; history preserves it. |

NOT removed (explicitly): `cylinder_longwave.py` / `cylinder_shortwave.py` as
files (they are branch additions carrying ACCEPTED v5/v6 demand-specialized
work — D03 primary-output reduction, demand scopes, fused kernels; only the N8
seam portion is removed), `_lw_kernel` (:203-223, B7-32 expert dispatch — §3),
`Lcyl_v2022a_by_demand` demand machinery, `pipeline.py:258-266/:306-307` demand
setup/restore, all v5/v6/v7 runtime/geometry/GVF work.

## 2. Boolean-semantics restoration (N8-40b tri-state)

N8 introduced `parallel=None` ("no explicit demand — the route-eligible value")
on `define_patch_characteristics_primary` / `Lcyl_v2022a_primary` /
`Lcyl_v2022a_by_demand` solely so the region-route consult could fire at H<=1.
With R1 applied the tri-state has no reason to exist. Restoration:

- `define_patch_characteristics_primary(..., parallel: bool = True)`: remove the
  `parallel is not False` gate (:396) and the `_lw_region_route` call (:397-399);
  the docstring reverts from the True/False/None contract to boolean
  parallel/serial kernel choice. The route gate `if parallel is not False and
  rows*cols:` disappears — the legacy block loop runs for both `True` and
  `False` values, exactly the pre-N8 observable.
- `Lcyl_v2022a_primary` / `Lcyl_v2022a_by_demand`: drop the "N8-40b tri-state"
  docstring paragraphs; `Lcyl_v2022a_by_demand` passes `parallel=bool(parallel)`
  to the full path unconditionally (currently only in the FULL_DIAGNOSTICS arm)
  and forwards a plain bool to the primary arm.
- `engine.py:1662`: `parallel=threads_per_worker > 1` (plain bool; H=1 becomes
  an explicit serial demand again, matching main's observable).
- `_lw_kernel(parallel)` keeps its boolean domain (`kernel=_longwave_primary if
  parallel else _longwave_primary_serial`) — unchanged; only its docstring's
  tri-state references go.

Surface tests that prove the restoration (must pass on the cleaned tree):

- `tests/optimization_v6/cylinder_lw/` — demand-specialized vs reference
  equivalence for both parallel and serial demands (numerical identity).
- `tests/optimization_v8/dx/` + `tests/optimization_v8/policy/
  test_legacy_env_parity.py` — env unset/unknown value keeps silent Numba
  behavior; no env var added; `import solweig_light` imports none of
  `_native_dispatch`.
- `tests/optimization_v8/installed/` — repointed: installed wheel contains no
  `_native_dispatch`, no registry, no native package-data; imports/CLI work
  read-only with no repo (F4/F5 verify).
- Existing differential/identity small chronology (inherited gates) — H=1 and
  H>1 runs bitwise vs A-endpoint.

## 3. Preserve list (nothing deleted)

- **B7-32 expert route**: `SOLWEIG_LIGHT_LW_BACKEND=native|ispc` via
  `cylinder_longwave._lw_kernel` -> `solweig_light.backends.native_lw`
  (+ `backends/__init__.py`, `backends/native/lw_native.py`,
  `backends/native/lw_primary.ispc`, `backends/native/build.sh` in the REPO).
  This predates N8, is part of the branch's agreed compatibility contract
  (MERGE_SCOPE: "No surprise removal of an already offered override"), and does
  not justify any default-native claim. In a wheel, the expert route degrades
  to its documented loud dev-build failure (no ispc/no sources) — that behavior
  is tested and documented, not a regression.
- **Research evidence**: `optimization_v5_claude/`, `optimization_v6_continue/`,
  `optimization_v7_backends/`, `optimization_v8_native_default/` (incl.
  `evidence/trials/n8_31_tierA/B_record.json`,
  `evidence/selection/n8_32_selection_record.json`
  (`numba_improvement_only_native_goal_open`),
  `evidence/freeze/n8_50_freeze_record.json`, `evidence/promotion/`,
  `evidence/reviews/n8_30_*`), `experiments/optimization_v8/` — all preserved
  as immutable history. Tier-B record keeps its SUM-OF-MINIMA diagnostic label;
  it is never relabeled as a continuous pipeline measurement (MEASUREMENT.md).
- **Failing fixtures**: any fixture inside `tests/optimization_v8/**` that
  documents a failure or decline taxonomy (loader/corrupt-artifact/ISA cases)
  is kept with its test in archived disposition — never deleted because the
  feature it exercised is gone.
- **N8-13-era harness**: `experiments/optimization_v8/native/
  quiet_window_abc.py` stays as the historical tier harness; the residual
  N13-7 `--block-sizes 0` acceptance is fixed in place per F0
  (`f0_inventory.json -> harness_zero_blocksize`, lines 173/350) as a small
  audit delta, or recorded as a known-historical-limit if the harness owner
  declines.
- **Maintainer tools**: `tools/optimization_v7/`, `tools/optimization_v8/`,
  `benchmarks/fixtures/optimization_v8/`, `benchmarks/protocols/`.

## 4. Test disposition

- **Archived-feature tests** (skipped with an explicit reason string naming
  this packet and the F3 outcome; never weakened, never edited to pass):
  `tests/optimization_v8/region/` (region owner/plan/pool),
  `tests/optimization_v8/policy/` selector-activation cases (rows B/C via
  records — the parity/DX cases stay active below),
  `tests/optimization_v8/layout/`, `tests/optimization_v8/numba/` (row-B
  consumer), `tests/optimization_v8/native/`, `tests/optimization_v8/loader/`,
  `tests/optimization_v8/artifacts/`, `tests/optimization_v8/packaging/`
  (native wheel assembly), and the R1-route cases inside
  `tests/optimization_v6/cylinder_lw/` if any drive the region route directly.
- **Stay active** (safety for the retained product): all
  `tests/optimization_v5/`, `tests/optimization_v6/` (decoder, gvf_prepare,
  gvf_postprocess, geometry_recipe, cylinder_sw, cylinder_lw, lside,
  patchclasses), `tests/unit/` (+1 new), `tests/optimization_v8/dx/`,
  `tests/optimization_v8/policy/test_legacy_env_parity.py`,
  `tests/optimization_v8/installed/` (repointed to CPU-only expectations),
  `tests/optimization_v8/reference/`, `tests/optimization_v8/integration/`
  (repointed where they assumed vendored machinery in the wheel).
- Mechanism: module-level `pytest.skip('archived feature: N8 default LW
  dispatch not selected for this release (n8_32 -> N9 F3 closed_cpu_only)',
  allow_module_level=True)` — the reason travels with the suite; fixtures stay.

## 5. Wheel/sdist exclusion candidates

Everything below is already OUTSIDE `packages.find where=["src"]` (src-layout;
no MANIFEST.in in the diff), so these are confirmations plus the src-tree
package-data deltas — no bulk deletion, no history rewrite:

- Confirm excluded from wheel AND sdist (repo-only, by design):
  `optimization_v5_claude/` (105 files), `optimization_v6_continue/` (375),
  `optimization_v7_backends/` (194), `optimization_v8_native_default/` (166),
  `experiments/` (43), `tools/` (29), `benchmarks/` (31), `tests/` (111),
  `optimization_n9_final/`. Rationale: campaign records, maintainer tools and
  fixtures are qualification-time artifacts; MERGE_SCOPE says exclude large
  historical experiment folders and link compact release notes to the
  immutable evidence.
- Remove from `[tool.setuptools.package-data]`: `backends/native/*.ispc`,
  `backends/native/*.sh`, `_native_dispatch/*.json` (registry), and the two
  `backends/native_generated/**` patterns (R6).
- `backends/native/*.py` (`lw_native.py`): two options — (a) keep shipping so
  the installed expert route can at least import up to its loud dev-build
  error, or (b) exclude it for a strictly CPU wheel. Recommendation: (b) with
  the expert route documented as repo-checkout-only, because MERGE_SCOPE
  forbids shipping maintainer build programs as runtime deps; decide finally
  in F4 with the DX owner (the env-parity test must then assert the loud
  failure on the installed product).
- `setup.py`: delete (R7).

## 6. Sequencing (forward commits on the same branch)

1. Commit A: R1+R2+R4+R5 + boolean restoration (§2) + active tests green
   (this is the only commit touching default behavior).
2. Commit B: R3 research relocation/exclusion + archived-feature skips (§4)
   + R6/R7 packaging (§5) + tier/freeze record addendum pointing at the N9
   selection record.
3. Commit C: F0 audit delta (zero-blocksize harness validation proposal or its
   applied one-line fix, if the harness owner approves).
Each commit keeps the installed import/API/CLI surface and the small frozen
chronology green; F4/F5 re-verify the no-env installed product after Commit B.
