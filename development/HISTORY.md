# solweig-light — consolidated history (final, 2026-10-17)

This is the single sequential record of how this repository came to be: the
port, the exactness contract, every optimization campaign, its terminal
state, and where the evidence lives. It supersedes the per-era process
documents that previously accumulated under `development/` (deleted at the
2026-10-17 documentation closure; recoverable from git history at the
pre-closure tip `07807fd8` and from the Dropbox archive — see the evidence
map below). The one other kept prose record is
`development/docs/evidence_storage.md`, the archive index required by the
repository evidence policy (see `CLAUDE.md`); where this narrative and that
index could disagree, the index governs archive locations and hashes.

Status: **closed**. All campaigns are terminal, all registered items are
resolved or explicitly rejected, and nothing is in progress. Performance
headroom analysis is complete for this node class; further work would be a
new campaign (none is planned).

## What this package is

solweig-light is a CPU-native reimplementation of the SOLWEIG-GPU model
(upstream pin `nvnsudharsan/SOLWEIG-GPU` @ `0d7fe742`, recorded in
`docs/provenance.md`): identical model behavior on CPU, with the Torch/GPU
stack replaced by NumPy + Numba, packaged as `solweig_light` (wheel from
`src/`, console script `solweig-light`, public API `thermal_comfort`). The
user-facing contracts live in `docs/` (numerical contract, compatibility,
model deviations, runtime, cache policy, portable math profile). The
behavioral reference checkout is `.upstream/SOLWEIG-GPU` (gitignored; a
fresh clone at the pinned rev restores it).

The development history below was constrained throughout by four ground
rules, treated as hard limits in every campaign:

1. No timestep-level parallelism (the chronological driver's step order is
   contractual).
2. No altered scientific work — outputs must stay within the frozen
   numerical contract (and, from S10 on, bitwise against corpus goldens).
3. No new runtime dependencies.
4. The exact-optimization arithmetic lineages C5/C6/N8/N9 (era 3) are
   frozen; later campaigns may add dispatch/scheduling around them but may
   not change their leaf-kernel arithmetic.

## Evidence map

- **Dropbox** `Alan Synn/Research/solweig-light/` (dbxcli; authenticated):
  - 2026-10-13 migration: `repo_evidence/`, `branch_evidence/`,
    `manifests/`, `logs/`, `EVIDENCE_ARCHIVE_README.md` — the 25,426 raw
    evidence files removed from git at `b3e5ca59`, plus 1,540 blobs unique
    to the deleted pre-handover campaign branches.
  - `s10/` — S10 raw records (trials, failsets, installed wheelhouse,
    synthdemo raw, sha256 sidecars).
  - `campaign_s11/phase0/`…`phase4/` — S11 raw records per phase, including
    the ~1.9 GB phase-0 SVF snapshot corpus and the S12 closure raw records
    (`phase4_s12_closure_raw_records.tar.gz`, sha256
    `3bbfcc16f2472ef9de02ea1377acd709618b13d0894d2d60a39476420ca6592b`) —
    plus `repo_closure_20261017/battery_closure_raw_records.tar.gz`
    (sha256 `581778a0f9c12db41f83f124227452759c7aa592cc7b5e4b26ec647f97bf0042`)
    for the documentation-closure battery and audit records.
  - `campaign_s11/repo_cleanup_20261016/` — `reports_bulk_20261016.tar.gz`
    (sha256 `41ca10c4…`) and `campaign_packets_20261016.tar.gz` (sha256
    `7beb2b35…`) — bulk `development/reports/` and the whole campaign
    packets (v4/v5/N9, S11, followon, `plans/`), removed at the S11 closure.
  - `repo_closure_20261017/development_closure_20261017.tar.gz` (sha256
    `0ef480844f4a7066a204c58834d50877056385a16715bea30709f80f7eea0305`) —
    everything removed by this documentation closure (508 files: campaign
    packet prose for v6/v7/v8/S10, `experiments/`, benchmark fixtures and
    superseded protocols, era tools, per-phase docs; members are
    repo-root-relative, a `MANIFEST.txt` inside carries per-file sha256s).
- **Git history on main**: full commit history is retained (no history
  rewriting was ever performed, by policy). Deleted documents and packets
  are recoverable at their era commits; `cba707db` is the last commit that
  carried every campaign record, and `07807fd8` the last that carried every
  development document. Key anchors:

  | commit | date | event |
  |---|---|---|
  | `8ca23d44` | 2026-09-20 | first commit: P0–P8 port checkpoint + portable math profile + optimization strategy |
  | `14e88876` | 2026-09-20 | local CPU optimization v1 landed |
  | `90d72b50` | 2026-09-23 | campaign line close (v5–N9) + handover restructure (`development/` umbrella) |
  | `b3e5ca59` | 2026-10-13 | evidence-storage migration ("old main" tip; S10/S11 baseline) |
  | `cba707db` | 2026-10-16 | S11-8 closure tip; S10+S11 branches fast-forwarded here |
  | `05ecd6ae` | 2026-10-16 | S12 lean-repo cleanup (−3,128 files: 3,115 under development/ + 13 followon; archived) |
  | `e3346e14` | 2026-10-16 | S12 fix: restore 2 test-coupled fixture packets |
  | `c620286b` | 2026-10-16 | S12 battery verdict record |
  | `12ff6d39` | 2026-10-17 | S12 direct old-main baseline (4.61×) + archive index |
  | `07807fd8` | 2026-10-17 | S12 docs consolidation; first push (b3e5ca59..07807fd8) |
  | *(this commit)* | 2026-10-17 | documentation closure: this file created, development prose/tools/packets deleted + archived |

- **Kept in the repo** (test-coupled or policy-required):
  `tests/reference/` goldens; `development/benchmarks/protocols/comparison_v1.json`
  (read at module level by the differential/integration/s10/v6 suites) and
  `development/benchmarks/protocols/p7_persistent_jit_serial_variant/`
  (harness protocol of `tests/unit/test_p7_serial_variant_harness.py`);
  six `development/tools/` scripts exercised by tests (`run_exact_cpu_pairs.py`,
  `summarize_exact_cpu_pairs.py`, `capture_exact_pipeline.py`,
  `benchmark_p7_pipeline.py`, `run_p7_serial_variant.py`,
  `characterize_inputs.py` — the last two sha-pinned by their harnesses)
  plus `development/tools/evidence_archive_20261013/` (named by the archive
  index); `development/reports/contract_snapshot.json` and the
  characterization subsets (`p7_p6_baseline`,
  `p7_repaired_p6_baseline{,_v2}`, `p8_umep_source`,
  `p8_utci_official_source`, `scientific_release_exceptions.json`);
  the `evidence/` trees of `optimization_v6_continue/`,
  `optimization_v7_backends/` (captures: capture manifest + the
  `b7_02_fixtures.npz` module-loaded by the v7 suite — restored from
  `90d72b50` at the post-closure audit; it had been untracked with the
  2026-10-13 evidence migration, which broke v7 collection),
  `optimization_v8_native_default/` (installed + dx_baseline),
  `optimization_s10_semantic_systems/`;
  `development/experiments/optimization_v8/packaging/build_native.py`
  (collection-time import of `tests/optimization_v8/packaging/conftest.py`;
  restored from `07807fd8` at the post-closure audit — the rest of
  `experiments/` stays deleted);
  `development/docs/evidence_storage.md`; this file and
  `development/README.md`. Product documents formerly under
  `development/docs/` moved to the root `docs/` at this closure
  (`p5_optional.md`, `p6_memory_inventory.md`,
  `wind_memory_inventory.md`, `upstream_patches/wrf_timestamp_v1.patch` —
  the last is the location recorded by the reference manifests and the
  optional-test sha-pin).

## Era 1 — P0–P8: the port (2026-09, macOS ARM64 + Cura)

The original upstream is a Torch/GPU-oriented SOLWEIG reimplementation. The
project began as a correctness-first characterization of that upstream on
CPU, then rebuilt it as a CPU-native package milestone by milestone, each
gated by original-CPU oracle comparisons (upstream installed in an isolated
Python 3.11 venv, never importing candidate code; its outputs packaged as
goldens under `tests/reference/`, which remain in the repo):

- **P0** — upstream characterization: 113-file source manifest, contract
  snapshot (7 signatures, 27 CLI declarations), static call graph (14 files,
  202 functions, 3,776 call sites), deterministic 32×35 24-hour fixture,
  same-host run repeatability, dependency-gap finding (upstream imports
  Numba undeclared). Froze the comparison/benchmark protocols.
- **P1** — serial NumPy geometry/radiation + chronological driver; first
  prepared-TIFF 24-step run within frozen budgets (largest TMRT error
  ~6.1e-05 °C); installed-wheel gate 245 passed; compatibility companion
  distribution introduced.
- **P2** — compiled wall/aspect/UTCI kernels (Numba), original fixture
  families, 28 frozen kernel configurations, installed gate 515 passed.
  Pinned NumPy signed-zero maximum behavior against a Numba divergence.
- **P3** — compiled shadows/SVF + lossless packed visibility (uint8 NPY,
  checksummed manifest, mmap); 43 benchmark configurations; installed gate
  2,038 passed.
- **P4** — compiled ground-view + patch radiation + delay chronology; 29
  frozen configurations; exception-compatibility fixes (original failure
  frames reproduced/rejected where upstream fails); installed gate 2,879
  passed. Measured compact-patch regressions at the frozen block (≈11.1×
  shortwave / 3.4× longwave vs best upstream warm configs) — recorded as
  the mandatory P6/P7 performance work.
- **P5** — all seven public optional workflows (ERA5/UHI/WRF/roughness
  wind/input builders) as lazy extras; WRF via the reviewed upstream
  timestamp-repair patch v1; gates 2,881/58/34.
- **P6** — runtime: native cache + identity guards, transactional output
  writer, state recovery, memory admission (cgroup-aware), worker pools,
  cancellation; two-generation raster ownership bound; gates 3,029/78/34.
- **P7** — performance: preserved P6 baseline, then measured, repaired, and
  gated. Found and repaired two real compatibility defects en route (f32
  angular promotion in ground-view; scalar annulus arithmetic in Kdown)
  with repair-only baselines kept separate (`p7_repaired_p6_baseline*`,
  still in the repo as test fixtures). Full 7-scene × 5-pair × 2-budget ×
  cold/warm paired matrix (v4 protocols) completed; persistent-JIT cache
  variant promoted after 40/40 pairs (distinct serial definitions to avoid
  dispatcher cache collisions). Rejected experiments (all recorded, none
  promoted): single-translation horizon recurrence, conservative quadtree
  skip (7.2–7.4× slower in Python), UTCI full-Horner (max error 0.031 °C
  > 0.02 gate), six-moment angular-moment bundle (all medians slower). P7
  formally remained `in_progress` at the log's end.
- **P8** — independent scientific checks + release qualification. Official
  UTCI/UMEP sources retrieved and hashed; isolated executions on the Cura
  host. Outcome: four named independent scientific checks (2× open-scene
  SVF unity, 2× UMEP ground-view variants) remained failed; the user
  approved retaining upstream behavior with a documented known-limitation
  exception (`inherited-svf-umep-compatibility-v1`; substance in
  `docs/model_deviations.md`, policy record kept at
  `development/reports/scientific_release_exceptions.json`). The
  dense-1024 TMRT incompatibility was localized to platform-dependent
  `acos`/tangent rounding before strict patch classification; standalone
  MKL 2024.2 passes everything but was **declined as a production
  dependency** (user decision). Instead the user authorized a separately
  versioned portable profile, **`solweig-portable-sleef-5a1d179d-v1`**
  (SLEEF-derived bounded-f32 helpers + NumPy-ufunc fallback), integrated
  after two-platform admission (M1 + Linux exact categories, 14,400
  layout/thread cases each; large-scene 240-band gates pass), documented in
  `docs/portable_math_profile.md`. A user-authorized patched-upstream CUDA
  reference (worker-limit patch, isolated checkout) passed the 12 GiB cold
  admission on Cura — recorded as patched-reference correctness, not a
  speed claim. Full release qualification (P8) was never completed; the
  mission pivoted to performance (era 2) with the port checkpoint committed.

End state of the era: commit `8ca23d44` (checkpoint of the whole port +
records, user-authorized 2026-09-20), then `14e88876` (local CPU
optimization v1: GVF pixel parallelism, duplicate visibility-decode removal,
content-bound persistent JIT caches; paired median 1.6268× at 4 threads,
256² warm, bootstrap CI [1.5934, 1.6490], exact results).

## Era 2 — exactness contract and verification regime

These are the rules every later campaign measured against:

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
- **Test battery**: `pytest tests/differential tests/integration tests/unit`
  on a dedicated compute node (sbatch, cpu-small, 24 CPU/96G, detached git
  worktree at the exact commit, shared NUMBA_CACHE_DIR). Clean baseline:
  **176 failed / 3133 passed** — a stable, byte-identical FAILED set of
  pre-existing environmental failures (missing `.upstream` tree pieces,
  login-cgroup thread limits, and similar), identical across arms; verdicts
  are FAILED-set diffs, never absolute counts. Login-node batteries are
  smoke only. Post-merge, the battery collects **3309** tests (the old
  `--ignore=tests/unit/test_exact_cpu_pairs.py` workaround became obsolete —
  era 7).
  - Three of the 176 baseline failures belong to
    `tests/unit/test_p7_serial_variant_harness.py`: their frozen protocol
    references characterization evidence (`p7_persistent_jit_distinct_variant`,
    `p7_pairs_v4`) that was removed with the bulk `development/reports/` at
    the S11 closure (raw-evidence class — archived, deliberately NOT
    restored). The harness, its tool and its protocol stay in the repo, so
    the collection count is unchanged; the three failures are a permanent,
    understood part of the baseline.
- **Known battery artifact** (documented so nobody re-diagnoses it):
  `test_compiled_patch_parallel_diagnostics` fails on a WARM numba cache
  and passes on a fresh one — `parallel_diagnostics()` metadata exists only
  on fresh in-process compiles (cache-hit dispatchers carry
  `ol.metadata is None`). Verified by fresh-cache discrimination (single +
  full-file 635/635 PASS). Not a product regression.

## Era 3 — the v4–N9 campaign line (2026-09; merged at handover)

Packetized optimization campaigns on dedicated branches, fast-forward merged
into main at handover (`90d72b50`). Terminal selection:
**`closed_cpu_only`** — no native/GPU backend earned its default.

- **v4** — operational/validation discipline only (strategy catalog, L0–L4
  test discipline); no src change.
- **v5 (C5)** — fused ordered packed-visibility decode (default OFF behind
  `SOLWEIG_LIGHT_FUSED_RAD`), GVF source hoisting + fused row-block gather
  (~3.6× stage, exact), persistent bounded worker pool, checkpoint digest
  IO, guarded absorption exit.
- **v6 (C6)** — common numerical geometry recipe, anisotropic Lside
  specialization, cylinder longwave/shortwave specializations, prepared GVF
  per-step sources, prepared multi-channel visibility decoder (later
  declined by default), phase memory admission (C6-42: the admission model
  that later shaped all S11 scheduling), patch-classification exact tables.
- **v7 (B7)** — ISPC `C_native` longwave backend as an opt-in expert backend
  (`SOLWEIG_LIGHT_LW_BACKEND=native`), bitwise-identical, default untouched;
  drjit explored, not selected.
- **v8 (N8)** — native-default attempt: **NOT earned on measurement**
  (selection `numba_improvement_only`); the native row + qualification
  machinery landed inert, archived repo-only under
  `development/experiments/optimization_v8/` (removed at this closure),
  banned from wheels by gate.
- **N9 (FINAL)** — bounded Numba stream row B as the shipped longwave
  default (`thread_budget` pinned 1, all-raw structural decline),
  mode-specialized packed decode + A-plus comparator; F6 terminal
  comparison vs main: bitwise parity on all 6 cells / 9 reps, carried
  geomean **1.60×** median-of-times, cold PASS 0.9226 MARGINAL; the
  causal-correction allowance was consumed (Amendment 1) — no further F6
  re-measurement is admissible. Superseded run-1 records (citing
  123×/5.14×/1.0843) are retained invalidated; any such number is the
  invalidated run.
- **Shipped default longwave state after N9**: bounded stream row B at
  `thread_budget` 1; engine `parallel=True` only when
  `threads_per_worker > 1`; all-raw inputs decline structurally to the
  legacy route; `aplus_decode` shipped in both consumer seams.

## Era 4 — handover restructure and evidence policy (2026-09-23 → 10-13)

- `90d72b50` moved everything not needed to *use* the package under
  `development/` (reports, docs, benchmarks, tools, experiments, campaign
  packets). Old absolute-era paths in tests' docstrings refer to the
  pre-restructure layout.
- `b3e5ca59` (2026-10-13, user decision) migrated raw evidence to Dropbox
  and kept the repo lean (manifests/provenance stay in git). This commit is
  the "old main" tip — the baseline for all later performance claims. One
  latent defect of this era (fixed by the campaign line): old main's
  `tests/unit/test_exact_cpu_pairs.py` resolved its tools path
  pre-restructure (`parents[2]/"tools"`), so those 8 tests were ignored in
  batteries until the fix landed on the campaign branch (`a405fc28`).

## Era 5 — S10 semantic-systems campaign (2026-10-13 → 15; terminal
`qualified_exact_cpu`)

Baseline: old main `b3e5ca59`. (The S10 REGISTER and packet prose were
archived at the 2026-10-17 closure — Dropbox `repo_closure_20261017/` — the
terminal record lives here; the packet's `evidence/` tree stays, read by
`tests/optimization_s10/`.) Accepted (each L2-paired, review-gated, exact):

- T01 — singleton-array Tgwall typed longwave path (1.659× stage geomean).
- G01+G02 — production dtype profile into the prepared GVF route at H=1
  (1.738×; root cause: production f64 Tg had been rejected by all-f32
  guards, so compiled GVF never engaged on land-cover scenes).
- R03 — aniLum packed-stream ordered-accumulation kernel (cumulative ≈3.0×
  vs main at cell level).
- Lside exact dispatch twin (all production calls aniso==1 → exactly
  `Lup*0.5`; bitwise, kill-switched, independently reviewed).
- S03b — GDAL cache charge derived from the container-correct memory view
  (ops fix, not speed; unblocks container-limited hosts).
- Held-out paired campaign (47 raw records): geomean paired-median **1.314×**
  (gate ≥1.10 PASS), 100% route coverage, zero reference fallbacks.
  Terminal state `qualified_exact_cpu`; wheel/DX gates clean (pure
  py3-none-any wheel, top-level package exactly `{solweig_light}`).
- S10-36 synthetic-scale demonstration (24×1024² corpus, 3×8): the
  small-cell ratios did **not** extrapolate — measured parity-to-1.034× —
  and exposed the structural finding that steered S11: **the SVF phase
  (61.4% of the chain, dominated by the serial export loop) had never been
  an S10 target**. In-process warm tile spans: 3.2363 → 1.0926 s = 2.96×.
- `actual_target_status: unverified` from S10 onward: all measurements are
  on the procedurally generated synthetic corpus; no real-target run was
  ever authorized.

## Era 6 — S11 envelope-headroom campaign (2026-10-15/16; terminal)

Branch `perf/s11-envelope-headroom` (cut from S10's tip), fast-forward
merged at `cba707db`; the REGISTER is archived in
`campaign_s11/repo_cleanup_20261016/campaign_packets_20261016.tar.gz`, its
findings indexed in `development/docs/evidence_storage.md`. Anchor: the
S10-36 A-arm chain (walls 20.0 + svf 4063.1 + run 2529.7; the recorded
total is 6612.9 s — the phase sum is 6612.8, a 0.1 s discrepancy present
in the source records themselves),
24×1024² tiles, 24 steps, 3×8.

- **Phase 0 attribution** (M1–M6 measured, product untouched): the serial
  parent export loop is 66.7% of the SVF phase and 41.2% of the whole
  chain; admission caps workers at 5; run phase is engine-dominated (95%)
  with a 4.2× day/night bimodal; UTCI immaterial (1.3%); guard at the
  hashing floor.
- **X02 ACCEPTED** — SVF pixel-parallel twin at the default shape (static
  bush predicate routes serial vs `shadow_pixel_parallel`): svf phase
  1.331×, chain 6612.9 → 5636.2 s = **1.173×**; bitwise 24/24.
- **X01 ACCEPTED** — per-tile export loop as a concurrent spawn-pool stage
  (degree = runtime workers, gated on cache_enabled): export stage 2708.2 →
  919.5 s = 2.946×; chain → 3838.3 s = **1.723×** (projection matched to
  +0.2%); bitwise 24/24. Documented contract amendment: publication order
  is completion order; failure truncates to the completed set.
- **X03 ACCEPTED** — measured-envelope admission recalibration. Child peak
  RSS measured 0.72–0.77 GiB at 1024² (vs the 9.17 GiB legacy reservation,
  >11× conservative); envelope table measured at 1024² and 2048² (slope
  form REJECTED by the frozen no-go, R-ratio 4.66); `simulation_reservation`
  repriced to table × margin 3 with GDAL charge capped at 256 MiB;
  post-E2E hardening charges decode scratch beyond the measured config.
  Result: 12×2 run shape admitted — chain **1452.5935 s = 4.552×** vs
  S10-36 (walls 21.0 + svf 599.3 + run 832.3); run +0.16% off projection;
  bitwise 24/24; login-node refusal preserved; user-visible consequence
  documented (a 32×35 census cell in 6 GB now refuses — conservative
  direction).
- **S11-7 corner matrix** (pure measurement, zero product change): steps
  2/24/72 × 256²/1024²/2048² × cold/warm × serial/parallel. Headlines:
  serial c24s 10744.28 s vs parallel c24p 1483.90 s = **7.24×** (60.3%
  worker efficiency; TMRT sha IDENTICAL across serial/parallel/golden);
  256² pair 6.90× cross-config bitwise; warm **not** faster (+3.86%:
  geometry verify-only saves 327.7 s but run pays +385.9 s); 72-step
  2954.05 s (~31 s/step marginal); 2-step 792.66 s (94% fixed cost);
  1-step is contract-unsupported (metfile >2 rows required). Discovered
  the pre-existing **under-fill admission defect** (below).
- **X05 ACCEPTED** (user-approved) — the under-fill defect fixed end-to-end:
  `plan_phase_admission` now clamps `requested = min(requested, len(jobs))`
  — scenes with fewer tiles than the requested worker width admit at the
  job count instead of refusing with a misleading "only N fit". One-line
  fix + 4 behavior pins; adversarial review APPROVE (0 MAJOR, pins proven
  discriminating on a pre-fix archive); batteries byte-identical (176/3133
  both arms); E2E at the previously-refusing 2048² 4×6 shape bitwise vs the
  1×8 record.
- **Amdahl ceiling at this node class (24 CPUs)**: serial fraction (walls +
  barrier) ≈26%; run engines saturate 12×2 = 24 threads; 16-wide admission
  fits memory but has no spare CPUs. Remaining headroom: the barrier seam
  (362 s serial read-back verify + staged publication) and per-engine
  efficiency — both need more CPUs or a protocol amendment.
- **REJECTED in S11** (measured; do not retry): UTCI parallel dispatch
  (≤1.013× bound), InputGuard optimization (at raw-sha floor), worker
  shapes >5 wide under the old admission (refused), 2×12 (dominated), 5×4
  SVF twin shape (admission-refused and dominated), slope-form memory
  envelope (no-go), alternatives B/C/D of the Stage-B protocol (arithmetic
  frozen in protocol), 8×3 (measured slower than 12×2: 1138 vs 831 s
  makespan), cross-phase pipelining (held by user decision; ≤~14% ceiling).

## Era 7 — S12 closure (2026-10-16/17)

- The S11 line was fast-forward merged to main at `cba707db` (branches
  deleted; commits reachable from main).
- **Merge-safety battery**: job 14126143 on main @ `e3346e14`, 3309 tests
  collected (the old-main `--ignore` workaround is obsolete post-merge):
  FAILED set == the campaign baseline 176 + exactly one deviation — the
  numba cache-state artifact documented in era 2 (root-caused by
  fresh-cache discrimination, job 14126396). No product regression.
- **Lean-repo cleanup** (`05ecd6ae`, then `e3346e14`): campaign packets and
  bulk reports removed from git and archived to Dropbox; the first cut
  accidentally dropped two test-coupled fixture packets
  (`p7_repaired_p6_baseline{,_v2}` — bare-name parametrization evaded the
  literal-path audit; post-cleanup battery caught 35 deterministic setup
  errors); restored from `cba707db`, audit re-run mechanically. Lesson
  recorded: deletion boundaries must resolve parametrized/bare-name test
  references, not just path literals.
- **Direct old-main baseline** (`12ff6d39`, job 14125735): the pre-merge
  main (`b3e5ca59`) chain at the SAME cold recipe (1024² corpus, 3×8 = 24
  tiles, 24 steps, walls→SVF→run) = **6840.3854 s** (walls 24.11 + svf
  4067.41 + run 2748.87), TMRT 24 bands **bitwise == corpus golden
  c361f819…** — old main and merged main produce identical outputs; only
  speed differs. (First attempt 14125089 died on a measurement-driver
  defect — editable-install hijacking child imports; fixed with PYTHONPATH
  + child-origin assert; that attempt contributed no timing.)
- All five closure commits pushed (`b3e5ca59..07807fd8`).
- **Post-closure audit** (2026-10-17, user-directed, seven independent
  auditors: structure, repo machinery, doc cross-references, this file's
  factual accuracy, independent test-coupling re-derivation, packaging/wheel
  build+install, git/archive integrity): the closure tree, wheel, git
  delta, and archive bundles verified clean; found and fixed — (a) the
  closure missed ONE collection-time import
  (`tests/optimization_v8/packaging/conftest.py` imports
  `experiments/.../build_native.py`; conftest is collection-time code —
  the S12 bare-name lesson one level deeper), (b) a PRE-EXISTING defect
  since the 2026-10-13 evidence migration: the v7 suite module-loads
  `b7_02_fixtures.npz`, untracked then, breaking v7 collection outside the
  canonical battery — both files restored from git history, (c) three
  wording corrections in this file (this section's cleanup-commit label,
  the S10-36 anchor phase-sum note, the Amdahl-ceiling sentence), (d) the
  CI workflow's one version-pinned wheel filename → glob. The
  `development/README.md` map and `docs/` annotations were adjusted to
  match; canonical collection stays 3309 (`git diff 07807fd8..HEAD --
  tests/` is empty — no test logic changed at any point of the closure).
- **Documentation closure** (this commit, 2026-10-17, user-directed): the
  accumulated development documents (per-phase docs, packet prose, era
  tools, benchmark fixtures/superseded protocols, `experiments/`) were
  deleted and archived to Dropbox `repo_closure_20261017/`; this file is
  the single surviving narrative. In the same change: the four
  product documents listed under "Kept in the repo" moved from
  `development/docs/` to the root `docs/` (repairing citations from
  `src/` and `docs/` that already pointed at the root locations);
  `development/reports/scientific_release_exceptions.json` was restored
  from `cba707db` (a 2.7 KB policy-provenance record cited by
  `docs/compatibility.md` and `docs/model_deviations.md`); the root
  `README.md` status section was refreshed to the closed state;
  `AGENTS.md` and the user-facing docs received archive annotations for
  their removed-evidence references; `development/README.md` shrank to a
  map. A pre-existing docs-side condition is annotated rather than
  repaired: many P0-era evidence records under `development/reports/` had
  already been removed at the S11 closure (2026-10-16); those references
  now carry explicit archive notes instead of dangling links.

## Performance summary (verified chain)

Same synthetic corpus (24×1024² tiles, 24 steps), same node class
(cpu-small, 24 CPU), same cold chain recipe; all end-to-end gates bitwise
against corpus goldens unless noted:

| configuration | chain | vs old main |
|---|---|---|
| old main `b3e5ca59`, 3×8 (direct baseline) | 6840.4 s | 1× |
| S10-optimized tree, 3×8 (S10-36 A-arm) | 6612.9 s | 1.034× |
| + X02 (SVF pixel-parallel twin) | 5636.2 s | 1.17× |
| + X01 (concurrent export loop) | 3838.3 s | 1.78× |
| + X03 (envelope recalibration, 12×2) | 1452.6 s | **4.71×** (4.552× vs S10-36) |
| merged main, same shape 3×8 (c24p headline) | 1483.90 s | **4.61×** |

Context numbers: serial→parallel at 24 steps is **7.24×** (10744.3 →
1483.9 s); 256² cross-config **6.90×**; cell-level compute improvement from
S10 ≈2.96× (visible in the run phase; masked in E2E until S11 removed the
SVF-phase bottleneck); warm start is **not** faster end-to-end (+3.86%).
Layered efficiency: X03 12×2 = 60.3% of ideal 24-way worker efficiency.
The residual serial fraction (≈26%: walls + barrier) bounds ideal parallel
scaling of THIS tree at ≈3.4× further; the measured ~4.7× vs old main is
larger because X01/X02 also removed serial phases the old-main baseline
still paid for.

## Known limitations and standing caveats

- **Synthetic corpus only.** `actual_target_status: unverified` — every
  headline number comes from the procedurally generated corpus; no
  real-scene target run was ever authorized. Physically, the model's four
  inherited scientific deviations (era 1, P8) remain documented failures
  under an approved known-limitation exception (`docs/model_deviations.md`;
  policy record `development/reports/scientific_release_exceptions.json`).
- **Single node class.** All E2E claims are on cpu-small/24-CPU nodes with
  the measured admission envelope; other shapes/budgets are calibrated, not
  measured; above 2048² the legacy full-plane envelope applies unchanged.
- **Warm-cache behavior**: warm is not faster end-to-end (+3.86%); JIT
  cache state changes one battery test's outcome (era 2 artifact).
- **P8 release qualification was never completed** (release benchmark
  matrices, hosted CI runs, full-platform checks remain outstanding by
  decision; remote CI has never executed). Compatibility-release use
  outside the measured envelope carries the documented caveats only.
- **Post-campaign follow-ups recorded, never taken** (no campaign is
  planned): `NUMBA_CACHE_DIR` bounded default (would cut ~2.4–2.7 s
  per-process compile on read-only installs; changes "cold" semantics and
  needs its own gate record); installed no-env API/CLI product runs on
  admission-blocked hosts; single-channel-raw compositions unmeasured.
- The host has known environment quirks for reproduction (editable-install
  PYTHONPATH trap for worktree drivers; numba cache-state test artifact;
  login-node cgroup admission; GDAL libstdc++ shim). The canonical battery
  recipe is sbatch + detached worktree + shared NUMBA_CACHE_DIR.

## Rejected directions (cumulative — do not retry without new causal design)

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
