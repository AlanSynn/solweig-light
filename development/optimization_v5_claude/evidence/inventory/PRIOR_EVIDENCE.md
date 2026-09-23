# C5-02 PRIOR_EVIDENCE — retained evidence mapped by identity

Worktree HEAD `6682b23e`. Paths are worktree-relative unless prefixed absolute.
`reports/` IS git-tracked in this repo (`git ls-files reports/ | wc -l` = 27841), so every
reports/ path below exists identically in the main checkout and this worktree.

## 1. Frozen protocols — `benchmarks/protocols/`

### `local_cpu_optimization_v1/{development,promotion,combined_development}.json`
- All three freeze `baseline_commit: 8ca23d444a3b05bdeb76655329c0a09c3dc4d6e8` and bindings
  `harness sha256 b7f52b0c…c0a80d`, `helpers sha256 d688ae60…c12720d5`.
- Shared acceptance core (all three): numerical = "Exact finite bits including signed zero,
  special masks, all artifacts and carried state; frozen original-reference gates unchanged.
  No fastmath, physics reduction, or chronological parallelism."; memory = 12 GiB process-tree
  RSS cap sampled at 20 ms, 10 GiB disk reserve; holdout = "Dense1024 and vegetation1024
  original SLEEF fixtures remain correctness holdouts and require final candidate
  requalification"; retention = never remove historical evidence or original goldens.
- `development.json` — diagnostic, 3 pairs/cell; advance candidates with median
  baseline/candidate >= 1.03 in >=1 cell subject to exactness.
- `promotion.json` — final method: exactly 5 pairs per cell, ALL 10 cells must pass; primary
  cell `repeated_block_256`, `budget 4`, `baseline_block_pixels 128 → candidate 1024`,
  `geometry_warm`, requires median baseline/candidate >= 1.05 AND paired geometric-mean
  bootstrap 95% lower bound > 1.0; guard cells (small/single-thread/warm) require
  candidate/baseline median <= 1.03; first-use median <= 1.10; RSS <= 1.10*baseline+64 MiB
  per cell.
- `combined_development.json` — combined_v1 cells (block 128 budget 1 … variant combined_v1),
  3 repetitions.

### `benchmarks/protocols/benchmark_v1.json` (frozen initial benchmark protocol)
- `status: "frozen_initial_benchmark_protocol_execution_incomplete"`,
  `source_commit: 0d7fe742abeeddd890dd58fc76ed7f78bd47faec`; hardware Apple M1 Pro, 10 logical
  CPUs, 16 GiB, macOS ARM64, no CUDA.
- Fixtures: `small` (manifest `reports/initial_fixture_manifest.json`, fixture sha256
  `475eff90…`, tile 64/0) and `medium256` (generator `tools/generate_benchmark_fixtures.py`,
  fixture sha256 `99eaeecc…`, tile 3600/20). `larger_sizes_required: [1024, 2048, 3600]`,
  status "pending execution, not omitted".
- Geometry family `repeated_blocks`: spacing 32 px, terrain 3 m, building height 10 m,
  rectangle [12,19,14,22], trees [[7,10,6,9,8],[22,25,25,28,6]].
- `physical_work`: resolution 1 m, patch_option 2, 153 patches, default 24 timesteps, all ten
  save flags + UTCI.
- `cache_regimes`: `first_use` (fresh process, empty candidate JIT+geometry caches, imports/
  JIT/IO included), `compiled_geometry_cold`, `geometry_warm`, `kernel_only`.
- Top keys also: `native_configs, selection, repetitions, resource_policy, statistics,
  numerical_prerequisite, predeclared_goals_not_measured, remaining_release_requirements,
  entrypoints`.

### `benchmarks/protocols/comparison_v1.json` (frozen comparison contract)
- `status: "frozen_P0_comparison_proposal_not_validated_candidate_contract"`, same
  source_commit + source_sha256 `1ac27bcd…`.
- `global_rules` (exactness rules): shapes/NaN/±Inf/sentinel locations match exactly BEFORE
  value comparison; input normalization, geometry categories, patch order, control state and
  artifact schemas exact; main state tested EVERY timestep; reported max errors + worst
  coordinates (no RMSE-only acceptance); no relaxation after failures.
- `field_rules` (key gates): `gvf_2018a/*` W m-2 fields (gvfLup, gvfLupE/S/W/N)
  `atol 0.05, rtol 1e-05`; dimensionless gvfalb*/gvfSum/gvfNorm `max_abs 1e-06`;
  `TsWaveDelay_2015a/Lup` first-five-calls-per-daytime flux `atol 0.05, rtol 1e-05`, sixth
  call `temperature_max_abs 0.01`.
- `other_outputs`: `SVF_all_15_fields max_abs 1e-06`; `UTCI max_abs 0.02 degC`; `WBGT
  max_abs 0.02 degC`; `Ta` "match float32 operation order; exact on frozen forcing"; `Wind`
  exact selection/clamp; `wall_stencil` "exact float32".
- Scope: pinned CPU profile on macOS ARM64; no gate weakening.

## 2. Fixtures (all present in worktree)

- `tests/fixtures/generated/p7/dense_urban_256`, `tests/fixtures/generated/p7/vegetation_rich_256`
- `tests/fixtures/generated/p7_real/{dense_urban,sparse,vegetation_rich,selection_inventory.json}`
- `tests/fixtures/generated/benchmarks/repeated_block_256`
- `tests/fixtures/generated/own_met_small/{Building_DSM,DEM,Trees}.tif + met.txt + manifest.json`
- `tests/fixtures/generated/small_prepared/{*.tif, met.txt, manifest.json, processed_inputs/}`
- `tests/reference/small_original_cpu/` (32x35 reference scene): layout
  `{scene/, boundaries/, environment.json, fixture_hashes.json, harness/, kwargs.json,
  outcome.json, reference_manifest.json}`.
- 1024 holdouts (absolute, and confirmed present in the worktree because reports/ is
  git-tracked):
  - `/Users/alansynn/Workspace/solweig-light-claude-v5/reports/characterization/local_cpu_optimization_v1/qualification/final_combined_v1/large_harness/fixtures/dense1024`
  - `…/large_harness/fixtures/vegetation1024`
  Manifest binding: `large_runs_v1/dense1024/candidate_manifest.json` records
  `fixture_manifest_sha256 51e5aac79281644d…`, `elapsed_diagnostic_seconds 400.827`,
  installed-wheel module origins under `…/qualification/final_combined_v1/site-packages/`, and
  sha256 for every 100,899,822-byte output TIFF (Kdown/Kup/Ldown/Lup/Shadow/TMRT/Ta/Wind/UTCI
  under `scene/output_folder/0_0/`). vegetation1024 analog records 341.365 s (also cited in
  `optimization_v4/THROUGHPUT.md:22`, main checkout).

## 3. Differential / reference test suite layout

- `tests/reference/<domain>_original_cpu/` — golden npz pairs + `reference_manifest.json`
  per domain: `geometry_original_cpu` (characterize_geometry.py + float32_block_*_inputs/
  outputs.npz), `delay_original_cpu`, `ground_view_original_cpu`, `patch_radiation_original_cpu`,
  `svf_original_cpu`, `wall_shadows_original_cpu`, `walls_original_cpu`,
  `walls_expanded_original_cpu`, `utci_original_cpu`, `state_sequence_original_cpu`,
  `forcing_original_cpu`, `inputs_original_cpu`, `public_forcing_original_cpu`,
  `public_roughness_original_cpu`, `wind_original_cpu`, `wrf_patched_cpu`,
  `p7_ground_view_angular_original_cpu`, `p7_svf_annulus_original_cpu`,
  `p4_benchmark_inputs`, `optional_original_cpu`, `small_original_cpu`.
- Harness pattern (canonical example `tests/differential/test_sky_compiled.py`):
  loads `REFERENCE=tests/reference/geometry_original_cpu`, asserts
  `evidence_class=='original_upstream_cpu'` and `source_commit=='0d7fe742…'`, verifies each
  case npz sha256, runs kernel under `numba.set_num_threads` variants
  `[None,1,4,10]` × variants `[step,pixel]`, and enforces `assert_exact`:
  dtype equal, shape equal, `np.testing.assert_array_equal`, NaN/+Inf/-Inf mask equality, and
  `signbit` equality on finite positions. This bit-exact-with-sign rule is the reusable
  baseline-vs-candidate kernel comparator; it is defined per test file (not a shared helper
  module).
- `tests/differential/` inventory (19 files): comfort/delay/geometry/preprocessor/pipeline/
  radiation/state_sequence references, `test_sky_compiled.py`, `test_wall_shadows_compiled.py`,
  `test_walls_compiled.py`, `test_ground_view_compiled.py`,
  `test_ground_view_dispatch_exact.py`, `test_patch_radiation.py`, `test_utci_compiled.py`,
  `test_p7_ground_view_angular.py`, `test_p7_svf_annulus.py`, `test_svf_concurrency.py`,
  `test_svf_options.py`, `test_state_resume.py`.
- `tests/helpers/`: `exact_persistent_jit_cache_probe.py` (asserts module origins + jit_cache
  identity for `_jit_cache`/`_sleef_*`), `installed_wheel_guard.py`,
  `persistent_jit_cache_probe.py`, `promotion_tiff_probe.py`.
- `tests/scientific/`: analytic/independent checks incl.
  `test_umep_delay_independent.py` / `test_umep_ground_view_independent.py` (verify against
  UMEP sources captured under `reports/characterization/p8_umep_source/` with sha256) and
  `test_utci_independent.py` (official source under `reports/characterization/p8_utci_official_source`).

## 4. Prior candidate history — `reports/characterization/local_cpu_optimization_v1/candidates/`

- `baseline/` — source snapshot of commit 8ca23d44 (`source_manifest.json` + full `src/` copy);
  no behavior change.
- `e1/` — GVF dispatch experiment: `admission.json`, `gvf.junit.xml`,
  `test_gvf_dispatch.py`, source snapshot. (Ground-view dispatch change; performance gate
  evidence in admission.json.)
- `e2/` — "E2 duplicate visibility decode" (`report.json: experiment` field): reuse of shared
  decoded shadow/vegetation leaves for the diffsh channel instead of a second decode;
  `status: functional_candidate_complete_performance_not_run`; includes
  `candidate.patch`, `candidate-v2-unverified.patch`, `source_review_v2.json`,
  `test_e2_duplicate_decode.py`. This is the v4 code that survives at HEAD as
  `diff_from_shared_decoded`.
- `combined_v1/` — the promoted v4 combination (scheduling + decode reuse + JIT identity);
  source snapshot only; became commit 14e88876.
- Also present (earlier/auxiliary): `e4/`, `e4v2/`, `e4v3/`, plus `e0/`, `development_run_v1/`,
  `combined_development_run_v1/`, `promotion_run_v1/`, `integration/`, `reviews/`,
  `proposals/`, `qualification/`, and frozen statistics
  (`development_statistics_v1.json`, `combined_development_statistics_v1.json`,
  `promotion_statistics_v1.json`, `promotion_completion_v1.json`).

## 5. Known scientific failure dispositions (inherited, to be preserved)

- dense1024 / vegetation1024 large-run records:
  `reports/characterization/local_cpu_optimization_v1/qualification/final_combined_v1/large_harness/large_runs_v1/{dense1024,vegetation1024}/`
  (`candidate_manifest.json`, `kwargs_used.json`, `monitor.json`, `rss_samples.jsonl`,
  full `scene/` output tree). Reference times: 400.827 s / 341.365 s single four-thread
  one-worker admissions (`optimization_v4/THROUGHPUT.md:22`, main checkout; explicitly NOT a
  repeated batch distribution).
- The dense1024 TMRT Linux p8 gate failure is an inherited v4-era disposition; I could not
  locate its single canonical record inside this worktree in the timebox (grep over
  `optimization_v5_claude/` and v4 docs found only the THROUGHPUT.md references). It is
  referenced as a preserved disposition in `optimization_v4/VALIDATION_POLICY.md:67`
  ("Preserve all old scientific failure dispositions"). UNRESOLVED POINTER — v5 validation
  owners should locate the exact record in the main checkout's v4 evidence before citing it.
- Inherited SVF/UMEP exception behaviors (identified by code/test anchors; count matches
  "four" but the authoritative v4 list was not located — see caveat above):
  1. `geometry/shadows.py:30` — `UnboundLocalError("unsupported patch option: upstream has no
     patch table")` for patch_option not in 1-4.
  2. `geometry/svf.py:113-114` — patch option 4 reaches a floating range bound and raises
     `TypeError('only integer tensors of a single element can be converted to an index')`.
  3. `radiation/wall_shadows.py:66` — `UnboundLocalError('Pinned upstream leaves facesh
     unbound for this azimuth')`.
  4. Exact-zenith shadow failure, recorded (not skipped) per
     `tests/scientific/test_geometry_analytic.py:54`.

## 6. Prior large-run harness

- `reports/characterization/local_cpu_optimization_v1/qualification/final_combined_v1/large_harness/run_final_large.py`
  — "Monitored final installed-wheel admission for the two 1024 fixtures"; local to the
  qualification record, does not alter package/tests/protocol. Measures: wall time,
  process-tree RSS via psutil sampled at an interval (`tree_rss`, sums
  `memory_info().rss` over root + descendants, deduped by pid), disk free
  (`available_bytes`), sha256 digests of every output artifact; constants
  `LIMIT = 12 GiB`, `RESERVE = 10 GiB`, `REPO = /Users/alansynn/Workspace/solweig-light`,
  `CASES = ("dense1024", "vegetation1024")`. Results land in `large_runs_v1/<case>/`.
