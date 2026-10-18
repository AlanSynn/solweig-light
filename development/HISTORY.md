# solweig-light — consolidated development record (final, 2026-10-17)

Status: **closed**. Every campaign is terminal, every registered item is
resolved or explicitly rejected, and nothing is in progress. No further
campaign is planned.

This record is organized **by theme, not campaign chronology**: what the
vanilla upstream model is and what this package changes (§1), how
correctness is defined and verified today (§2), what performance was
achieved and what is off the table (§3), and where everything lives (§4).
The earlier campaign-by-campaign narrative (eras 1–7) is preserved at git
`d3706ad7` (no history rewriting was ever performed, by policy) and as
Dropbox `repo_closure_20261017/HISTORY_pre_consolidation_d3706ad7.md`
(sha256 `68a749ebbb6c6605f5c3b5179b5ac400256e3e6bc06864e30a1cb356830f9056`).
Where this narrative and the archive index
(`development/docs/evidence_storage.md`) could disagree, the index governs
archive locations and hashes.

## 1. The upstream model and this port

### 1.1 Vanilla SOLWEIG-GPU (the behavioral reference)

- `nvnsudharsan/SOLWEIG-GPU` @ `0d7fe742abeeddd890dd58fc76ed7f78bd47faec`
  (recorded in `docs/provenance.md`): a Torch/GPU-oriented SOLWEIG
  reimplementation. Source files carry GPL-3.0-or-later notices while setup
  metadata says GPL-3.0-only — the discrepancy is documented, not silently
  resolved; original notices are preserved in translated files.
- The behavioral reference checkout is `.upstream/SOLWEIG-GPU` (gitignored;
  a fresh clone at the pinned rev restores it). It runs in an isolated
  Python 3.11 venv (`.venv-oracle`) and **never imports candidate code**.
- Characterization host: macOS ARM64 — CUDA unavailable, so CUDA equivalence
  was never passed; upstream correctness was established against its CPU
  execution. A P0 finding: upstream imports Numba without declaring it.

### 1.2 What solweig-light is

A CPU-native reimplementation of that upstream with identical model
behavior: the Torch/GPU stack replaced by NumPy + Numba, packaged as
`solweig_light` (wheel built from `src/`, console script `solweig-light`,
public API `thermal_comfort`). User-facing contracts live in `docs/`
(numerical contract, compatibility, model deviations, runtime, cache
policy, portable math profile).

### 1.3 The port milestones (P0–P8, each gated by original-CPU oracle comparisons)

| phase | content | installed-gate result |
|---|---|---|
| P0 | upstream characterization: 113-file source manifest, contract snapshot (7 signatures, 27 CLI declarations), static call graph (14 files, 202 functions, 3,776 call sites), deterministic fixture, frozen comparison/benchmark protocols, Numba-gap finding | — |
| P1 | serial NumPy geometry/radiation + chronological driver; first prepared-TIFF 24-step run within frozen budgets (largest TMRT error ~6.1e-05 °C) | 245 passed |
| P2 | compiled wall/aspect/UTCI kernels (Numba); 28 frozen kernel configurations; pinned NumPy signed-zero maximum behavior vs a Numba divergence | 515 passed |
| P3 | compiled shadows/SVF + lossless packed visibility (uint8 NPY, checksummed manifest, mmap); 43 benchmark configurations | 2,038 passed |
| P4 | compiled ground-view + patch radiation + delay chronology; measured compact-patch regressions at the frozen block (≈11.1× shortwave / 3.4× longwave vs best upstream warm configs) — the mandatory P6/P7 performance mandate | 2,879 passed |
| P5 | all seven public optional workflows (ERA5/UHI/WRF/roughness wind/input builders) as lazy extras; WRF via the reviewed upstream timestamp-repair patch v1 | 2,881/58/34 |
| P6 | runtime: native cache + identity guards, transactional output writer, state recovery, cgroup-aware memory admission, worker pools, cancellation | 3,029/78/34 |
| P7 | performance harness: paired-matrix measurement + repair discipline; two real compatibility defects found and repaired en route (f32 angular promotion in ground-view; scalar annulus arithmetic in Kdown), repair-only baselines kept separate | — |
| P8 | independent scientific checks + release qualification (see §4.3: four checks remained failed → approved exception; MKL declined; portable SLEEF profile admitted; full release qualification never completed) | — |

Port checkpoint committed user-authorized at `8ca23d44` (2026-09-20), then
`14e88876` (local CPU optimization v1: GVF pixel parallelism, duplicate
visibility-decode removal, content-bound persistent JIT caches; paired
median 1.6268× at 4 threads, 256² warm, bootstrap CI [1.5934, 1.6490],
exact results).

### 1.4 What differs from vanilla — and what is preserved

**Differs:**

- **Platform**: CPU (NumPy + Numba) instead of Torch/GPU; CUDA equivalence
  is not claimed. GPU execution exists only as a user-authorized
  patched-upstream CUDA reference run (worker-limit patch, isolated
  checkout, 12 GiB cold admission on Cura) recorded as correctness
  evidence, not a speed claim.
- **Four inherited scientific deviations** (era-1/P8 findings, retained by
  user decision under the approved known-limitation exception
  `inherited-svf-umep-compatibility-v1`): 2× open-scene SVF unity and 2×
  UMEP ground-view variants remain failed independent checks — upstream
  behavior preserved and documented in `docs/model_deviations.md`; policy
  record `development/reports/scientific_release_exceptions.json`.
- **Portable math profile** `solweig-portable-sleef-5a1d179d-v1`: SLEEF-
  derived bounded-f32 helpers + NumPy-ufunc fallback, integrated after
  two-platform admission (M1 + Linux, 14,400 layout/thread cases each;
  large-scene 240-band gates pass); `docs/portable_math_profile.md`. MKL
  2024.2 passed everything but was **declined as a production dependency**
  (user decision).
- **Packaging**: installable wheel + console script + companion
  compatibility distribution; upstream stayed a research checkout.

**Preserved:** the model's mathematics and outputs — every output within
the frozen numerical contract (§2.1), and bitwise against the synthetic-
corpus goldens wherever measured (§3); upstream exception/failure behavior
(original failure frames reproduced or rejected identically); the CLI/API
surface.

### 1.5 The ground rules every change was held to

1. No timestep-level parallelism (the chronological driver's step order is
   contractual).
2. No altered scientific work — outputs must stay within the frozen
   numerical contract (and, from S10 on, bitwise against corpus goldens).
3. No new runtime dependencies.
4. The exact-optimization arithmetic lineages C5/C6/N8/N9 are frozen:
   later campaigns may add dispatch/scheduling around them but may not
   change their leaf-kernel arithmetic.

## 2. Exactness and verification

### 2.1 The numerical contract

- **Machine-readable authority**: `development/benchmarks/protocols/
  comparison_v1.json` — 96 named component return fields with per-family
  budgets (radiative fluxes atol 0.05 W/m² rtol 1e-5; TMRT/Tg 0.01 °C;
  UTCI/WBGT 0.02 °C; SVF 1e-6; control state exact). Budgets were never
  relaxed in response to a candidate failure. Cited by
  `docs/numerical_contract.md`.
- **Operative bar (established S10)**: the frozen comparison_v1 budgets are
  the acceptance standard — bit-equality vs the engine serial reference is
  NOT the bar (the shipped S-profile primary diverges 1–2 f32 ulp on real
  fractional-visibility inputs, documented and pre-existing). From S10
  onward, end-to-end campaign claims additionally require **bitwise**
  equality against the synthetic-corpus goldens (SVF and TMRT sha256).

### 2.2 The canonical test battery — current state: fully green

Command: `pytest tests/differential tests/integration tests/unit` on a
dedicated compute node (sbatch, cpu-small, 24 CPU/96G, detached git
worktree at the exact commit, shared warm `NUMBA_CACHE_DIR`). Verdicts are
**FAILED-set diffs** between arms, never absolute counts; login-node runs
are smoke only (cgroup admission caps numba threads at 4 there).

- **Current baseline: 3237 collected, 0 failed — FAILED set empty**
  (sbatch job 14143334, 2026-10-17, at the harness-removal commit). The
  canonical battery is fully green for the first time since the campaigns
  began.
- Other suites: `tests/optimization_v7` 12 collected / 0 errors;
  `tests/optimization_v8` 2020 collected + 2 documented login-node
  environmental errors; `tests/optional` 4 collection errors (missing
  optional extras in the dev venv).
- **How it got green** (the 2026-10-17 baseline-hygiene closure; `src/`
  untouched throughout): the standing 176-failure baseline was
  heterogeneous, not environmental — 168 were fixed test-side (see §2.3
  for the cross-platform half; the radiation call recorder was re-seamed
  to the real C6 dispatch boundary `cylinder_longwave.Lcyl_v2022a_by_demand`
  with its 6 recorded intermediate-field comparisons restored; a stale
  4 GiB memory-budget pin was repriced to 8 GiB per the measured C6-42
  envelope; a geometry-guard mutation was moved to the real
  `svf_calculator_compact` seam; two cache-dependent tests moved to
  subprocess probes on per-run `NUMBA_CACHE_DIR`, eliminating the
  warm-cache battery artifact). The remaining 9 were platform-bound guards
  of the retired P7 measurement harness — archived characterization
  payloads, a gitignored reference wheel, untracked raw scene inputs, and
  one pre-restructure path citation; repair would have meant regenerating
  macOS-arm64 records or un-ignoring heavyweight binaries, and they never
  exercised `src/` — so they (and 63 passing tests of the same retired
  machinery, 72 tests total) were deleted by user decision. Details:
  `development/docs/evidence_storage.md` § "Baseline hygiene".

### 2.3 Cross-platform divergence policy (macOS captures vs Linux host)

The `tests/reference/` goldens labeled `original_upstream_cpu` were
captured on macOS-26.6.2-arm64 (Python 3.11.16/Clang 21, torch 2.14.0,
numba 0.67.0, numpy 2.4.6, scipy 1.17.1); the battery host is Linux
x86_64. Transcendental paths therefore diverge by tiny, deterministic
amounts on a small recorded cell set:

- **Aspect** (upstream's arctan fallback, a transcendental): recorded
  per-cell divergence table + absolute envelope
  (`tests/reference/walls_aspect_cross_platform_divergence.json`;
  envelope 3.0517578125e-05 degrees — five orders below the 1-degree
  winner granularity). Walls/dsm stay bitwise; NaN positions exact; any
  new divergent cell fails. Two rotation-boundary filter cells are pinned
  to observed values; any second differing cell fails.
- **svfalfa**: maxulp=1 (the in-file weight-table precedent); `svf`/
  `svfveg` stay bitwise.
- **Signed zero**: ±0 signs are numerically inert (IEEE −0.0 == +0.0);
  sign equality is asserted on nonzero magnitudes only where a reduction
  order legitimately differs.
- **Method note**: ULP distance explodes near zero (a ~1e-38 absolute
  difference at a 0-adjacent value reads as 5e8 ULP), so cross-platform
  bounds are recorded as **absolute envelopes + per-cell pins**, not
  maxulp.

## 3. Performance record

### 3.1 What shipped (the optimization inventory)

| change | what it is | measured effect | exactness |
|---|---|---|---|
| v1 (`14e88876`) | GVF pixel parallelism, duplicate visibility-decode removal, content-bound persistent JIT caches | 1.6268× paired median (4 threads, 256² warm) | exact |
| C5 (v5) | fused ordered packed-visibility decode (default **OFF** behind `SOLWEIG_LIGHT_FUSED_RAD`), GVF source hoisting + fused row-block gather, persistent bounded worker pool, checkpoint digest IO, guarded absorption exit | ~3.6× stage (gather, exact) | exact |
| C6 (v6) | common numerical geometry recipe, anisotropic Lside specialization, cylinder longwave/shortwave specializations, prepared GVF per-step sources, prepared multi-channel decoder (declined by default), phase-memory admission model (C6-42), patch-classification exact tables | — | exact |
| B7 (v7) | ISPC `C_native` longwave backend, opt-in via `SOLWEIG_LIGHT_LW_BACKEND=native` | — | bitwise, default untouched |
| N8 (v8) | native-default attempt — **not earned on measurement** (`numba_improvement_only`); row + qualification machinery landed inert, banned from wheels by gate | — | — |
| N9 (FINAL) | bounded Numba stream row B as the shipped longwave default (`thread_budget` pinned 1, all-raw structural decline, `aplus_decode` in both consumer seams) | carried geomean **1.60×**; cold PASS 0.9226 MARGINAL (causal-correction allowance consumed — no further F6 re-measurement is admissible) | bitwise 6/6 cells / 9 reps; superseded run-1 numbers (123×/5.14×/1.0843) are retained **invalidated** |
| S10 | T01 singleton-Tgwall typed longwave (1.659× stage); G01+G02 production dtype profile into prepared GVF at H=1 (1.738×; root cause: f64 Tg rejected by all-f32 guards — compiled GVF never engaged on land-cover scenes); R03 aniLum packed-stream ordered accumulation (cumulative ≈3.0× cell-level); Lside exact dispatch twin (bitwise, kill-switched); S03b GDAL cache charge from the container-correct memory view (ops fix) | held-out paired campaign geomean **1.314×** (gate ≥1.10 PASS), 100% route coverage, zero fallbacks | exact/bitwise; terminal `qualified_exact_cpu` |
| S11 X02 | SVF pixel-parallel twin at the default shape (static bush predicate routes serial vs parallel) | chain 6612.9 → 5636.2 s = 1.173× | bitwise 24/24 |
| S11 X01 | per-tile export loop as a concurrent spawn-pool stage (degree = runtime workers, gated on cache_enabled); documented contract amendment: publication order is completion order, failure truncates to the completed set | export stage 2.946×; chain → 3838.3 s = 1.723× | bitwise 24/24 |
| S11 X03 | measured-envelope admission recalibration (child RSS 0.72–0.77 GiB at 1024² vs the 9.17 GiB legacy reservation; table × margin 3, GDAL charge capped 256 MiB; slope form rejected by frozen no-go) | admits the 12×2 run shape → chain 1452.5935 s | bitwise 24/24; login-node refusal preserved; a 32×35 census cell in 6 GB now refuses (conservative direction) |
| S11 X05 | under-fill admission defect fix: `plan_phase_admission` clamps `requested = min(requested, len(jobs))` | 2048² 4×6 shape now admits and runs bitwise vs the 1×8 record | batteries byte-identical; adversarial review APPROVE |

S10-36 structural finding (steered S11): on the 24×1024² corpus the
small-cell ratios did not extrapolate (parity–1.034×) because the SVF
phase — 61.4% of the chain, dominated by the serial export loop — had
never been an S10 target; in-process warm tile spans 3.2363 → 1.0926 s =
2.96× (the cell-level improvement masked end-to-end until S11).

### 3.2 The verified chain (headline numbers)

Same synthetic corpus (24×1024² tiles, 24 steps), same node class
(cpu-small, 24 CPU), same cold-chain recipe; all end-to-end gates bitwise
against corpus goldens:

| configuration | chain | vs old main |
|---|---|---|
| old main `b3e5ca59`, 3×8 (direct baseline) | 6840.4 s | 1× |
| S10-optimized tree, 3×8 (S10-36 A-arm) | 6612.9 s | 1.034× |
| + X02 (SVF pixel-parallel twin) | 5636.2 s | 1.17× |
| + X01 (concurrent export loop) | 3838.3 s | 1.78× |
| + X03 (envelope recalibration, 12×2) | 1452.6 s | **4.71×** (4.552× vs S10-36) |
| merged main, same shape 3×8 (c24p headline) | 1483.90 s | **4.61×** |

Context: serial→parallel at 24 steps is **7.24×** (10744.3 → 1483.9 s,
60.3% worker efficiency; TMRT sha identical across serial/parallel/golden);
256² cross-config **6.90×**; warm start is **not** faster end-to-end
(+3.86%); 72-step 2954.05 s (~31 s/step marginal); 2-step 792.66 s (94%
fixed cost); 1-step is contract-unsupported (metfile >2 rows required).
Amdahl: residual serial fraction (walls + barrier) ≈26% bounds this tree
at ≈3.4× further ideal scaling; the measured ~4.7× vs old main is larger
because X01/X02 also removed serial phases old main still paid for.
Remaining headroom: the barrier seam (362 s serial read-back verify +
staged publication) and per-engine efficiency — both need more CPUs or a
protocol amendment.

### 3.3 Rejected directions (do not retry without new causal design)

Measured or gate-rejected across the campaigns: timestep parallelism (hard
limit); kernel-internal micro-optimization of the frozen C5/C6/N8/N9
lineages (exactness-frozen; post-census route counters showed 0 fallbacks —
the top stages are all on their compiled routes); ISPC/native default (not
earned; opt-in only); MKL as a production dependency (user declined);
portable math alternatives to the SLEEF profile — CORE-MATH, Intel IGC,
SVML, AOCL, OpenLibm (all fail the actual-invocation classification gate;
finite search, not proof of impossibility); UTCI Horner evaluation (error
0.031 °C > 0.02); six-moment angular-moment bundle (slower on every
median); single-translation horizon recurrence (wrong support); Python
quadtree hierarchical skip (7.2–7.4× slower); UTCI parallel dispatch;
InputGuard metadata shortcut; worker shapes >5 wide pre-X03; 2×12 and 5×4
shapes; slope-form memory envelope; 8×3 fallback shape (measured slower
than 12×2); cross-phase pipelining (held by user, ≤~14% ceiling);
Boolean-packed visibility channels (combined channel can equal 2 —
disproved at P0); interval changes to the delay mechanism (D08).

### 3.4 Recorded follow-ups never taken

No campaign is planned; these are recorded for completeness:
`NUMBA_CACHE_DIR` bounded default (would cut ~2.4–2.7 s per-process
compile on read-only installs; changes "cold" semantics, needs its own
gate record); installed no-env API/CLI product runs on admission-blocked
hosts; single-channel-raw compositions unmeasured.

## 4. Repository state and archives

### 4.1 Where everything lives

- **Dropbox** `Alan Synn/Research/solweig-light/` (dbxcli; authenticated) —
  the raw-evidence archive required by the evidence policy (`CLAUDE.md`):
  - 2026-10-13 migration: `repo_evidence/`, `branch_evidence/`,
    `manifests/`, `logs/`, `EVIDENCE_ARCHIVE_README.md` — the 25,426 raw
    evidence files removed from git at `b3e5ca59`, plus 1,540 blobs unique
    to the deleted pre-handover campaign branches.
  - `s10/` — S10 raw records; `campaign_s11/phase0/`…`phase4/` — S11/S12
    raw records per phase (incl. the ~1.9 GB phase-0 SVF snapshot corpus
    and `phase4_s12_closure_raw_records.tar.gz`, sha256 `3bbfcc16…`).
  - `campaign_s11/repo_cleanup_20261016/` — the S11 cut
    (`reports_bulk_20261016.tar.gz` sha256 `41ca10c4…`,
    `campaign_packets_20261016.tar.gz` sha256 `7beb2b35…`).
  - `repo_closure_20261017/` — the documentation + hygiene cuts:
    `development_closure_20261017.tar.gz` (sha256 `0ef48084…`, 508 files),
    `battery_closure_raw_records.tar.gz` (sha256 `581778a0…`),
    `battery_audit_raw_records.tar.gz` (sha256 `1a51a0da…`),
    `harness_removal_20261017.tar.gz` (sha256 `f78d007e…`, 141 members),
    `battery_hygiene_raw_records.tar.gz` (sha256 `806671a0…`), and
    `HISTORY_pre_consolidation_d3706ad7.md` (sha256 `68a749eb…`).
    Full index with expanded hashes: `development/docs/evidence_storage.md`.
- **Git history on main**: full history retained (no rewriting, by
  policy). Key anchors:

  | commit | date | event |
  |---|---|---|
  | `8ca23d44` | 2026-09-20 | first commit: P0–P8 port checkpoint + portable math profile + optimization strategy |
  | `14e88876` | 2026-09-20 | local CPU optimization v1 landed |
  | `90d72b50` | 2026-09-23 | campaign line close (v5–N9) + handover restructure (`development/` umbrella) |
  | `b3e5ca59` | 2026-10-13 | evidence-storage migration ("old main" tip; S10/S11 baseline) |
  | `cba707db` | 2026-10-16 | S11-8 closure tip; S10+S11 branches fast-forwarded here |
  | `05ecd6ae` | 2026-10-16 | S12 lean-repo cleanup (−3,128 files; archived) |
  | `12ff6d39` | 2026-10-17 | S12 direct old-main baseline (4.61×) + archive index |
  | `07807fd8` | 2026-10-17 | S12 docs consolidation; first push (b3e5ca59..07807fd8) |
  | `3ba286c3`–`d3706ad7` | 2026-10-17 | documentation closure, post-closure audit, baseline hygiene (168 fixes + harness removal), fully green battery |
  | *(this commit)* | 2026-10-17 | this record reorganized by theme; the era-by-era narrative preserved at `d3706ad7` + Dropbox |

- **Kept in the repo** (test-coupled or policy-required):
  `tests/reference/` goldens (incl. the recorded cross-platform divergence
  table); `development/benchmarks/protocols/comparison_v1.json` (read at
  module level by the differential/integration/s10/v6 suites) and
  `development/benchmarks/protocols/p7_persistent_jit_serial_variant/`
  (read by `tools/run_p7_serial_variant.py`, kept through the
  `run_exact_cpu_pairs` → `tests/unit/test_exact_cpu_pairs.py` chain);
  five `development/tools/` scripts (`run_exact_cpu_pairs`,
  `summarize_exact_cpu_pairs`, `capture_exact_pipeline`,
  `run_p7_serial_variant`, `characterize_inputs` — the last sha-pinned)
  plus `development/tools/evidence_archive_20261013/`;
  `development/reports/contract_snapshot.json`, the `p8_*`
  characterization subsets and `scientific_release_exceptions.json`;
  the `evidence/` trees of `optimization_v6_continue/`,
  `optimization_v7_backends/` (capture manifest + `b7_02_fixtures.npz`
  module-loaded by the v7 suite), `optimization_v8_native_default/`
  (installed + dx_baseline), `optimization_s10_semantic_systems/`;
  `development/experiments/optimization_v8/packaging/build_native.py`
  (collection-time import of `tests/optimization_v8/packaging/conftest.py`);
  `development/docs/evidence_storage.md`; this file and
  `development/README.md`. Product documents formerly under
  `development/docs/` moved to the root `docs/` at the documentation
  closure (`p5_optional.md`, `p6_memory_inventory.md`,
  `wind_memory_inventory.md`, `upstream_patches/wrf_timestamp_v1.patch` —
  the last is the location recorded by the reference manifests and the
  optional-test sha-pin). The P7 harness test modules,
  `tools/benchmark_p7_pipeline.py` and the `p7_*` characterization
  subsets were removed at the baseline-hygiene closure (§2.2; archive
  above).

### 4.2 How the repo got lean (closure timeline, compressed)

`b3e5ca59` (2026-10-13) moved raw evidence to Dropbox; `cba707db`
(2026-10-16) is the S10+S11 campaign tip; the S12 closure then removed the
campaign records and development tree bulk (`05ecd6ae`, −3,128 files),
consolidated the documentation (`07807fd8`, first push), passed a
post-closure audit (`a0f440ba`), and repaired the test baseline
(`08bb59db` + the harness-removal commit, ending in the fully green
battery). Records were retained as written (retain-don't-edit): paths in
older records cite the pre-restructure root layout (`reports/…`, `tools/…`
mean `development/reports/…`, `development/tools/…` today).

### 4.3 Known limitations and standing caveats

- **Synthetic corpus only.** `actual_target_status: unverified` — every
  headline number comes from the procedurally generated corpus; no
  real-scene target run was ever authorized. The four inherited scientific
  deviations (§1.4) remain documented failures under the approved
  exception.
- **Single node class.** All E2E claims are on cpu-small/24-CPU nodes with
  the measured admission envelope; other shapes/budgets are calibrated,
  not measured; above 2048² the legacy full-plane envelope applies
  unchanged.
- **Warm-cache behavior**: warm is not faster end-to-end (+3.86%). (The
  old warm-cache battery test artifact was eliminated at the baseline
  hygiene — §2.2.)
- **P8 release qualification was never completed** (release benchmark
  matrices, hosted CI runs, full-platform checks remain outstanding by
  decision; remote CI has never executed). Compatibility-release use
  outside the measured envelope carries the documented caveats only.
- **Host quirks for reproduction**: editable-install PYTHONPATH trap for
  worktree drivers; login-node cgroup admission (numba threads ≤4); GDAL
  libstdc++ shim (the 2 documented v8 collection errors). The canonical
  battery recipe is §2.2.
