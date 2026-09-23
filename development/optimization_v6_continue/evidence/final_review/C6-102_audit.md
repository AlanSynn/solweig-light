# C6-102 independent evidence audit

Date: 2026-09-21. Auditor: independent GLM audit (Opus unavailable; honest
label per DESIGN_AUTHORITY §16). Tree:
`/Users/alansynn/Workspace/solweig-light-claude-v5`, branch
`perf/claude-glm53-cpu-v5`.

## Verdict: CLEAN-WITH-NOTES

No blocking finding. Every audit-able headline number I recomputed from
committed raw data matches its claim exactly. The C6-101 blockage (absent
24-spatial-tile dataset) is recorded honestly in every claim-bearing
document; no spatial/band conflation, no unscoped timing claim, no oracle
fabrication was found. Four non-blocking notes below.

## Scope audited and lineage note (N1)

- Audit ran against HEAD **`7e0d8764`**. The task brief named `2f91d3e2`;
  that commit was amended to `7e0d8764` before the audit (same parent
  `ea2eed53`, same subject/timestamp; the amendment dropped ~1139 bulky
  binary run artifacts — numba caches, `processed_inputs` TIFFs,
  ~229k lines). `2f91d3e2` is referenced by no evidence file; the freeze
  content itself (src frozen at `ea2eed53`) is unaffected. Recorded as the
  actual lineage; nothing to fix.
- All evidence under `optimization_v6_continue/evidence/` plus the branch
  commit series `5e1fab46..7e0d8764` was swept. Benchmarks were not rerun;
  no src/tests state was modified (verified post-audit: zero tracked-file
  churn in `evidence/recipe`, `evidence/census`, `src/`, `tests/`).

## Findings

| # | Severity | Location | Finding |
|---|---|---|---|
| F1 | INFO | `evidence/mem_adm/m5_phase_inventory_and_calculator.md:108-110` | "4 × simulation + parent: reject policy raises `ResourceAdmissionError` naming 22,967,851,416 B" — the named byte total is exactly 4×simulation (4 × 5,741,962,854 = 22,967,851,416) **without** the parent term; the "+ parent" in the sentence describes the tree, not the named number. The number itself is exact; wording is loose. |
| F2 | INFO | `evidence/portfolio/README_C6-80.md:161`, `evidence/selection/C6-81_selection.md:19` | The decoder "+21–24%" headline uses display-rounded endpoints; exact best-of-30 deltas recompute to +20.7%, +20.7%, +22.0%, +23.4%. Already flagged as F2 (INFO) in `evidence/reviews/C6-81_review_decoder_decline.md:212`. Direction is conservative (overstates the declined decoder's loss). |
| F3 | INFO | `evidence/mem_adm/m5_phase_inventory_and_calculator.md:60,73` | The admission boundary tables size the GDAL cache term for a 32 GiB host (1,717,986,918 B = 5% of 32 GiB) while the measurement host has 16 GiB (`hw.memsize` = 17,179,869,184). The §5 header declares the sizing and `tests/optimization_v6/memory/test_phase_memory_admission.py:206-211` pins both host sizes, so it is a labeled model assumption — but a casual reader could take the tables as this-host numbers. |
| N1 | NOTE | branch tip | Lineage observation, see above: brief's HEAD `2f91d3e2` amended to `7e0d8764` before audit; freeze unaffected. |

## Checklist results

### 1. Scope conflation sweep — PASS

- No evidence file claims an actual-target, release, statistical, p95,
  reliability, or production timing result. C6-101 is recorded
  **BLOCKED-UNVERIFIED / dataset absent** in all five claim-bearing
  documents: `inventory/LEDGER_C6.md:65`, `freeze/FREEZE_C6-100.md`
  ("TARGET SCOPE", :167-195), `integration/C6-99_surface_confirmation.md`
  ("Remaining gap", :59-65), `selection/C6-81_selection.md` ("What this
  selection does NOT claim", :47-51), and
  `measurement/BASELINE_v6.md:86-94` ("Nothing here is final-target
  evidence").
- Every timing number carries its tier label: C6-80 numbers are
  "dev-tier single-lease observations" (`portfolio/README_C6-80.md:3-7`,
  repeated in freeze constraints item 2 and the selection record); census
  durations are "NOT benchmark" (`census/CENSUS_C6-02.md:28-30`); baseline
  paired timing is "triage only, L2 development tier"
  (`measurement/BASELINE_v6.md:63`).
- The 598.9 s scope correction is append-only and the historical record is
  untouched: `measurement/SCOPE_CORRECTION.md` states the correction and
  names the immutable original; `git diff 8e0b3877..HEAD --
  optimization_v5_claude/evidence/final_batch/CAMPAIGN_v1.md` is empty
  (file introduced once by `becb3841`, never edited on this branch). The
  correction states both directions honestly: the v5 record itself said
  "both scenes"; the error is only any later reuse of 598.9 s ≤ 1800 s as a
  24-tile pass. Every `1800` mention in evidence is correctly scoped
  (7 hits, all in target-definition/correction context).

### 2. W/H and thread telemetry — PASS

- Portfolio child records record the complete chain per run: all seven
  thread env vars at numerical import, `numba.config.NUMBA_NUM_THREADS`,
  `set_num_threads` error, `final_get_num_threads` (effective mask),
  threading layer, and the admission plan's native threads. All 64 slots:
  `native_mask` == requested config (S1/P2 = 1, T2 = 2), 0 mismatches,
  0 nonzero returncodes.
- Measured shapes are real, not just manifest labels: GDAL probe of the
  committed run scenes gives 128×128 (`runs/t128_S1/integrated/run_scene`)
  and 256×256 (`runs/t256_S1/...`); scene manifests record
  `tile_size [128,128]`/`[256,256]` with per-tile sha256; census fixture is
  96×96 (`scene96`), baseline workload is 256×256 (`scene_dense256`,
  GDAL-verified).
- The C6-01 defect demo is backed by raw records:
  `measurement/paired_runs/slot02_old_style_h4/record.json` shows
  `config=10`, `set_num_threads_called=false`, final mask 10 — exactly the
  voiding rationale in `BASELINE_v6.md:61-71`. H-matrix children show
  requested == configured == effective (1/2/4).
- Decoder probes record `native_threads: 2` and warm-JIT state.

### 3. Chain integrity — PASS

- All 28 ledger commit hashes exist on the branch with matching subjects
  (b2d23c6c … ea2eed53, incl. 41bfcaf4 C6-03 review commit).
- Review verdicts match the ledger row-for-row: C6-03/C6-10/C6-20/C6-21/
  C6-22/C6-30/C6-31/C6-42(rev3)/C6-50 = APPROVE-WITH-NOTES; C6-40 and
  C6-70 = APPROVE-WITH-CONDITIONS (conditions closed: `db5928fe` exists;
  `integration/C6-70_review_dispositions.md` documents all three closures);
  C6-81 = APPROVE.
- Freeze lineage: frozen rev `ea2eed53` (= C6-99 tip), exactly one commit
  after it (`7e0d8764`, evidence-only; `git diff ea2eed53..HEAD -- src/
  tests/` empty). Freeze src-delta table recomputes: `git diff --numstat
  8e0b3877..ea2eed53 -- src/` = 10 files, +1173/−86, every per-file count
  matching `FREEZE_C6-100.md:19-31`. Decoder-decline commit `46450c75` src
  delta confined to `geometry/visibility_prepared.py` +19/−1, as claimed.
- C6-90..94: zero commits anywhere on the branch (`git log --all |
  grep -c "C6-9[0-4]"` = 0), consistent with the selection record's
  NOT-SELECTED dispositions and the ledger's "not dispatched" status.

### 4. Numeric spot-recomputation — PASS (all exact)

Recomputed from committed raw JSONs (not rerun):

1. **Portfolio cells** (`portfolio_v1.json`, 64 slots, `total_measured`):
   all 12 cold/warm cell medians match the README table exactly (t128_S1
   21.35/22.80 cold, 9.99/9.87 warm; t256_S1 48.65/53.92, 31.06/31.18;
   t128_P2 19.31/18.66, 7.26/6.30; t256_P2 34.96/39.25, 18.01/17.20;
   t128_T2 19.71/20.99, 8.24/8.01; t256_T2 40.93/48.83, 21.64/22.32), and
   all 18 cold stage medians (walls/svf/sim) match the stage table exactly.
   Headline deltas recompute: −6.4%, −9.8% (S1 cold), −6.1%, −16.2% (T2
   cold), −10.9% (P2 t256 cold), +1.2%, −0.4% (S1 warm), +2.9%, −3.0%
   (T2 warm).
2. **Decoder probe** (4 cells): +20.7%, +20.7%, +22.0%, +23.4% prepared
   loss; reproduces the recorded 58.3 vs 72.0 ms cell and the README's
   displayed 55.4/66.8, 236.7/288.8, 222.7/268.7.
3. **Baseline paired timing** (`paired_runs/*/record.json`,
   `timing_s.run_tile_total`): H1 26.946/25.576/25.37 → min 25.37, median
   25.576; H4 → min 20.62, median 20.786; old-style → min 19.755, median
   20.238; routes H1 = `gvf_serial_full` ×14, H4/old-style =
   `gvf_fused_g03` ×14 — all identical to `BASELINE_v6.md`.
4. **Wheel gate**: recomputed sha256 of all 10 `output_folder/0_0` TIFFs
   in the committed `run_src` vs `run_wheel` roots — 10/10 bitwise
   identical. `svfs_0_0.zip`: 15/15 members content-identical, 15/15
   member timestamps differ — exactly the recorded verdict-4 caveat.
5. **Memory model**: legacy estimate 3,730,374,656 B (= 1,925,185,536 +
   989,855,744 + 10,027,008 + 805,306,368 = 3.4742 GiB); corrected
   reservations sim 5,741,962,854 / geo 4,758,857,318 / pre 2,674,288,230;
   12 GiB tree arithmetic (2×sim+parent = 11,913,422,438 fits with
   headroom 971,479,450; 3×1 = 17,655,385,292 breaches; preprocess-only
   4×1 = 11,126,649,650; mixed 2 = 10,930,316,902; 5.5 GiB infeasible base
   5,476,083,302 = 5.5 GiB − parent exactly); parent ceil(0.4 GiB) =
   429,496,730; 5% of 32 GiB floored = 1,717,986,918; raw-True numbers
   (budget 1,736,769,536 − parent 429,496,730 = 1,307,272,806 remaining)
   self-consistent.
6. **Census counts**: base 4 vs integrated 2 cache entries holds in every
   one of the 64 portfolio slots; integrated cold `productions=1,
   svf_calls=1` (shared key) and cache-disabled `productions=2` in both
   trees, matching `CENSUS_C6-02.md` and the integrated census JSON.

### 5. Negative-result preservation — PASS

- **Fused radiation OFF**: `patch_radiation.py:135-142` —
  `SOLWEIG_LIGHT_FUSED_RAD == '1'` opt-in, default OFF, docstring says so;
  C6-70e hook declines under fused (`patch_radiation.py:531-535`);
  `C6-99_surface_confirmation.md:56` records the v5 measured rejection as
  unchanged.
- **Prepared decoder default-declined**: `visibility_prepared.py:310-319`
  gate returns enabled only on `SOLWEIG_LIGHT_PREPARED_VIS == '1'`, and its
  docstring cites the C6-80 measured loss as the reason;
  `prepare_channels` returns `None` when declined (:332-333), documented as
  indistinguishable from unsupported inputs; `46450c75` + review APPROVE on
  record. Not softened anywhere.
- **Phase-route t128 caveat**: recorded in freeze constraint 4 and the
  selection dispositions (net negative at 128², pays at 256²; gate
  unchanged to avoid a sub-5% host-noise call).
- **Raw-True admission failure**: recorded verbatim in
  `freeze/gates_summary.json` + `freeze/gate_raw_true.full.txt`, classified
  honestly as an admission rejection *before any numerical comparison*,
  dispositioned in `freeze/C6-100_integrator_dispositions.md` as the
  sanctioned C6-42 stricter boundary with an environmental trigger — with
  the numerics covered bitwise by the wheel gate. Not hidden, not patched
  post-freeze.

### 6. No fabricated oracle — PASS

- `git diff 8e0b3877..HEAD -- src/` contains **zero** added lines matching
  `fastmath|seterr|errstate|rtol|atol|allclose`; net fastmath/seterr delta
  = 0. All `fastmath` occurrences at HEAD are the pre-existing
  `fastmath=False` declarations in `comfort/` (untouched by the range).
  `engine.py:333` `np.seterr(divide='ignore', invalid='ignore')` is
  pre-existing at base (`:330` at 8e0b3877), not touched.
- Public surface delta = the opt-in env var `SOLWEIG_LIGHT_PREPARED_VIS`
  + the `prepared_default_off` pytest marker (`pyproject.toml:40`) + the
  new private module `runtime_phases.py`. `api.py`'s only added top-level
  def is private (`_precompute_geometry_phase`); no `__all__`, signature,
  CLI, or workflow-contract change to the existing surface
  (`C6-99_surface_confirmation.md:25-29` matches the diff).

### 7. Guard/durability contracts — PASS

- Pre-spawn admission: `api.py:210-246` — `plan_admission` then C6-42
  `plan_phase_admission(..., policy='reject')` run parent-side and
  in-process **before** `execute_tiles` spawns anything; the comment block
  records the semantics, and the `if jobs:` guard carries the C6-60 F1
  disposition reference. The raw-True disposition's
  "rejects before any worker spawns" claim is consistent with this code.
- Decoder fallback: `prepare_channels` → `None` when gate off or admission
  fails → `decode_shortwave_block` returns `None` → `_shortwave_
  visibility_blocks` runs the original per-channel path verbatim (only an
  early-return on a non-None prepared result was added).
- Durability per reviews: L2 chronology differentials (both threads=1 and
  threads=2 GVF-inclusive closures) are recorded with raw NDJSON logs and
  output-hash JSONs present in `integration/l2-logs/`; C6-80 output
  integrity (one simulation-TIFF digest per shape across all 64 runs) is
  in the slot records.
- Live verification at HEAD: `tests/optimization_v6/decoder/
  test_prepared_default_off.py` — 2 passed (PYTHONPATH=src,
  NUMBA_NUM_THREADS=2, project venv). No tracked evidence file churned.

## Recomputed vs trusted

**Recomputed by this audit from committed raw data** (higher confidence):
portfolio slot table and stage medians + all headline deltas; decoder-probe
deltas (4 cells); baseline paired timing minima/medians/routes; wheel-gate
output TIFF sha256s and svfs ZIP member comparison; memory-model component
arithmetic and admission-boundary bytes; census cache-entry counts across
all 64 slots; freeze src-delta numstat; thread telemetry fields in 64 child
records + 12 measurement records; raster dimensions of the measured scenes;
review-verdict-to-ledger mapping; commit-existence for all 28 referenced
hashes; src-diff grep for oracle fabrication.

**Trusted on the record's own evidence** (review-verified; not re-executed
per audit mandate): the numerical bitwise differentials themselves (L2 event
hash streams, cylinder parity kernels, recipe/phase/memory suites), the
reviewers' internal recomputations inside the review files (e.g. 541+35
scoped tests at C6-70 closure), the wheel-gate identity-closure byte checks
beyond the sha256 recomputation I redid, and the C6-42 unit suite (31
tests).

## Carried items for C6-103 handover (unchanged, as recorded)

1. 24-spatial-tile dataset absent → C6-101 BLOCKED-UNVERIFIED; no
   actual-target or release timing claim may be derived from this tree.
2. Raw-True differential case is host-RAM-sensitive by construction
   (default-options public entry vs availability-sensitive auto budget);
   candidate future fix is a pinned `memory_budget_bytes` in the test
   (small reviewed commit + re-freeze).
3. Decoder remains available only via `SOLWEIG_LIGHT_PREPARED_VIS=1`
   (exactness/memory-profile adoption case only).
