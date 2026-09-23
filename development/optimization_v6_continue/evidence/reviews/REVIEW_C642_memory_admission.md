# REVIEW_C642 — Independent review of C6-42 private phase memory admission

- **Reviewer**: C6-60 (service instance). Independent GLM review; Opus unavailable (routing: GLM via Z.ai).
- **Date**: 2026-09-21
- **Review worktree**: `/Users/alansynn/Workspace/solweig-light-v6-rev642`, detached at `41bfcaf4` (carries REVIEW_C603_memory.md; `git diff --stat 5e1fab46 41bfcaf4 -- src/` is empty, so all `path:line` citations below resolve identically at the candidate base `5e1fab46`).
- **Candidate under review**: worker v6-memadm, worktree `/Users/alansynn/Workspace/solweig-light-v6-memadm` (detached at `5e1fab46`): `src/solweig_light/runtime_memory.py` (NEW, inert), `tests/optimization_v6/memory/test_phase_memory_admission.py` (24 functions / 29 collected), `optimization_v6_continue/evidence/mem_adm/{m5..m7}`.
- **State certified**: evidence "revision 2" (self-declared in `m5_commands_and_hashes.txt`), sha256 re-verified against the tree during this review: module `f65384af…`, tests `adc6a809…`, probe `2613aa7c…`, decision JSON `798ce48d…`, m5 `97e37d1f…`, m7 recipe `f57a14e9…`, m7 patch `9ba72a54…`.
- **Contract**: DESIGN_AUTHORITY.md; dossiers/04 (D04), dossiers/09 (integrator-owned files); VALIDATION_POLICY.md; the relayed C6-03 review corrections (a)-(e) from REVIEW_C603_memory.md.

## Method

I read `runtime_memory.py` in full (all 953 lines) and every evidence file; recomputed all headline arithmetic myself from source constants (not from m5); ran the full test suite, re-executed all 12 decision-table cells independently in memory and diffed against the committed JSON (byte-for-byte, including reject reason strings), and ran the legacy-anchor assertion against `runtime.estimate_memory` myself. Spot-checked every load-bearing source citation new since C6-03 (`io/rasters.py:24,31-37`, `persistence.py:84-104,456-468`, `walls.py:181`, `walls_compiled.py:39,49`, `runtime.py:170,279-286,457-502,532-592,663-677`, `api.py:17-46,150-161,208-210`, `geometry/service.py:265-286`). Attempted `git apply --check` of the proposed wiring patch. Read-only checks with `/Users/alansynn/Workspace/solweig-light/.venv-light/bin/python`; no numerical runs; nothing edited in the candidate worktree.

**Process incident recorded up front (finding 1)**: the candidate tree mutated during this review. My first full read of `runtime_memory.py` returned the pre-correction state (walls/aspects inventory row still `float64`/8 B); the file was rewritten ~2 minutes later (mtime 11:42:25) with the relayed F7 correction, and tests/m5/m6/m7 followed through 11:45:23. The dispatch brief said "worker finished, no further writes" — empirically false at dispatch time. I waited for quiescence (no writes after 11:45:30, re-checked at 11:48) and this review certifies the post-quiescence hash set only. All findings below are against that final state.

## Findings

### 1. Mid-review mutation of the candidate tree — PROCESS FINDING (no code defect)

Claim (dispatch): worker finished, no further writes.
Verification: mtimes show `runtime_memory.py` 11:42:25, tests 11:43:07, probe 11:43:40, m5 11:44:53, m7 recipe 11:45:00, JSON/probe log 11:45:10, hashes file 11:45:23 — all after my review opened; the originally recorded 11:37 hash set mismatched the tree for every deliverable until the worker re-recorded it as "revision 2". After quiescence all 7 hashes match revision 2 and my independent runs (below) all pass.
Verdict: not verdict-changing (final state is coherent and independently re-verified), but the coordinator should not mark a worker finished while it is still applying corrections; evidence timestamps must precede reviewer dispatch.

### 2. Legacy anchor reproduction — CONFIRMED byte-exact

Claim: `legacy_estimate_total_bytes(1024,1024,153,12,1024)` = 3,730,374,656 B, asserted equal to `runtime.estimate_memory(...).total_bytes`.
Verification: recomputed from `estimate_memory` source (`runtime.py:457-502`: raw 3·pixels·153·4 + live (192+32+12)·pixels·4 + decoded 1024·153·16·4 + native 768 MiB) — identical terms, identical total. Ran the module's function and `estimate_memory` in one process: equal, = 3,730,374,656. Suite test `test_legacy_worst_case_reproduced_from_first_principles` passes (29/29 passed in my own run, 0.74 s).
Verdict: correct.

### 3. Reservation table matches the corrected inventory — CONFIRMED

Claim: f32 walls/aspects, GDAL cache 1,717,986,918 B/process, DTYPE64 at 8 B/value, parent 429,496,730 B.
Verification: (a) walls/aspects inventory row is now `float32`/4 B with the corrected source chain (`read_raster` astype f32 at `io/rasters.py:24`; `write_single` GDT_Float32 at `:31-37`; `GeometryCache` passthrough `pipeline.py:202`) — matches the relayed correction (a), and the 32-plane DTYPE64 repricing is re-justified as promotion-reserve pricing consistent with the `runtime.py:479-481` comment, not as a resident f64 family. (b) `DEFAULT_GDAL_CACHE_RATIO=(5,100)`, `_physical_memory_bytes()` sysconf/sysctl probe; 5% of 32 GiB floored = 1,717,986,918 exactly (asserted in `test_default_gdal_cache_derivation`). (c) `simulation_reservation` prices the 32-plane reserve at 8 B/value (`runtime_memory.py:633`); delta vs legacy = 134,217,728 B (asserted). (d) parent = ceil(0.4 GiB) = 429,496,730, charged once per tree, infeasibility/K-checks all subtract it before reservations.
Arithmetic cross-check (my own sums @1024/P153/block1024/raw): preprocess 2,674,288,230; geometry 4,758,857,318; simulation 5,741,962,854; 2·sim+parent = 11,913,422,438 ≤ 12 GiB; 3·sim+parent = 17,655,385,292 > 12 GiB; geo+sim+parent = 10,930,316,902; 4·pre+parent = 11,126,649,650 — all match m5 §5 and the committed JSON.
Verdict: correct.

### 4. Decision table: all 12 cells reproduce; the 3×1 raw-worst boundary IS asserted (correction c satisfied)

Claim: `m6_admission_decision_table.json` cells are programmatic outputs of the calculator at the recorded state.
Verification: I re-implemented the probe's cell runner in a throwaway process (imports from the candidate `src`, no files written) and diffed every field (outcome, admissible/deferred, native_threads, tree bytes) plus the full reject reason strings against the committed JSON — byte-identical, 12/12 cells. The table contains two explicit 3×1 cells tagged "(C6-60 F6)": `12GiB sim x3 queue` → queued, admissible=2, deferred=1; `12GiB sim x3 reject` → rejected naming "only 2 fit" and "17,225,888,562" (the 3-largest sum). The mixed geo+sim 2x2 and x4 cells pin K=2 at 12 GiB from both sides. Additionally `test_three_worker_boundary_raw_worst_and_legacy_gap` asserts the legacy gap itself: legacy `plan_admission` admits 3 workers at a 12 GiB budget (I reproduced: `active_workers == 3`) while the corrected model refuses width 3 — exactly the boundary correction (c) required, with 4×1 no longer presented as the unique breach configuration.
Verdict: correct; the critical concern from the C6-03 relay is properly closed, in both the probe artifacts and the test suite.

### 5. Oversubscription and failure semantics — CONFIRMED

Verification (code + tests, all re-run):
- In-process only / class identity: `plan_phase_admission` raises `ResourceAdmissionError` imported from `.runtime`; `test_reject_policy_raises_in_process_runtime_error_identity` asserts both `type(excinfo.value) is ResourceAdmissionError` (runtime's class object) and `rm.ResourceAdmissionError is ResourceAdmissionError` — real identity assertions, and I confirmed the identity independently. Nothing in the module pickles, serializes, or string-rebuilds the error; the JSON-safe dataclasses (`PhaseJob`/`Reservation`/`PhaseAdmissionPlan`) carry data only, never the exception.
- Queue defers only individually-fitting jobs: the per-job infeasibility scan (`total_bytes > base`) runs before any policy branch (`runtime_memory.py:894-908`), so an impossible job raises under both policies — asserted verbatim by `test_individually_infeasible_job_raises_in_both_policies` ("queueing cannot make this phase fit") at a 5.5 GiB budget.
- The K-greedy is the same K-largest-prefix rule as `runtime.plan_admission` (`runtime.py:584-589` vs `runtime_memory.py:913-923`); since any-K-fits ⟺ K-largest-fit, `admissible_workers` is a safe concurrency bound for arbitrary scheduler subsets. `plan_phase_admission` correctly applies the infeasibility check to all jobs (consistent with legacy behavior and with m5 §9's F5 note).
- Missing shape data raises everywhere: `PhaseJob` requires rows/cols positionally (TypeError if absent), validates all dimensions and modes eagerly; `shape_from_building_dsm` raises `ResourceAdmissionError` naming the path on missing key, missing file, or unreadable raster; no zero-byte reservation path exists anywhere in the module. All covered by tests (6 malformed params + missing-args + nonexistent-file cases) and all pass.
- Tree-overhead exhaustion raises before reservation arithmetic (`test_tree_overheads_exhausting_budget_raise_before_reservations`); no negative intermediates (`test_no_negative_budget_arithmetic` iterates every inventory field of every phase ≥ 0).
Verdict: correct.

### 6. Inertness — CONFIRMED

Verification: `grep -rln runtime_memory src/` (excluding the module itself) returns nothing. Module imports are exactly `dataclasses`, `os`, `typing`, and `.runtime` — no numpy, no numba, no osgeo at module scope. GDAL appears only as a lazy `from osgeo import gdal` inside `shape_from_building_dsm`, opening `GA_ReadOnly` and reading `RasterYSize/RasterXSize` only — verified side-by-side to mirror `runtime._job_estimate`'s probe (`runtime.py:548-556`) exactly. `test_module_is_inert_until_wired` additionally proves in a subprocess that importing `runtime_memory` after `runtime` adds no numba/osgeo top-level module (correctly attributing baseline imports to `runtime`).
Verdict: correct; the module is inert until wired.

### 7. Proposed wiring patch is CORRUPT — artifact defect (must regenerate before integrator use)

Claim: `m7_phase_admission_wiring.proposed.patch` is the integrator-consumable diff proposal at base `5e1fab46`.
Verification: `git apply --check` (run in my worktree, whose `src/` is byte-identical to `5e1fab46`) fails: `error: corrupt patch at …:37`. Every hunk's declared counts mismatch its body — api.py hunk declares 6 old/27 new context+change lines but its body yields 5/28; service.py 6/22 vs 6/27; runtime.py 6/13 vs 3/9. The envelopes were evidently edited after generation (leading context lines dropped from the bodies).
Mitigations: the three intended anchors are all real at base — `plan_admission(jobs, runtime)` at `api.py:157`, `plan_admission([{'tile': …` at `geometry/service.py:275`, `_child_environment` thread-var block at `runtime.py:663-677` — and the intended insertions are semantically coherent (parent-side, policy='reject', `active_workers=min(workers, max(1, cpu_budget // threads_per_worker))` matching both `plan_admission` and `admission_inputs_from_options`; W3's `GDAL_CACHEMAX` value floors to 1,717,659,648 B ≤ the 1,717,986,918 B charged — cap slightly below charge, conservative).
Verdict: recipe analysis sound, artifact broken. Not verdict-changing (patch is explicitly NOT APPLIED; module is inert), but regeneration via `git diff` (and a `git apply --check` in the evidence commands) is mandatory before any integrator consumes it.

### 8. m7 §3 sign-off interval: lower bound wrong by the parent term — ANALYSIS ERROR (minor)

Claim: "budgets between ~3.88 GiB (3.4742 + 0.4 GiB parent) and ~4.83 GiB (4.432 + 0.4) that today admit a cold worst-case geometry job would newly raise."
Verification (numerical, my own run): the legacy per-job check admits a single job iff estimate ≤ budget — it charges no parent term — so its boundary is 3.4742 GiB. The corrected single-job geometry check admits iff 4,758,857,318 ≤ budget − 429,496,730, boundary 4.8320 GiB. I stepped budgets 3.6/3.7/3.88/4.0/4.7/4.83/4.9 GiB through both checks: 3.6 and 3.7 GiB **newly raise** yet fall outside the recipe's claimed interval. The correct newly-raising interval is **[3.4742, 4.8320) GiB**; the recipe's "~3.88" adds the parent to the legacy side of the comparison, where the legacy check never charged it.
Verdict: upper bound and the "stricter boundary, needs sign-off" framing are correct; the lower bound understates the behavior change by 0.4 GiB in the very section whose purpose is to delimit it. Fix the interval before integrator sign-off.

### 9. m7 §3 closing sentence overstates model agreement at 12 GiB — WORDING (minor)

Claim: "At the 12 GiB budget the two models agree (both admit), so W1 changes nothing for compliant configurations."
Verification: true for the single-job W2 comparison (3.4742 and 4.8320 GiB are both ≤ 12 GiB). False as a W1 statement: at a 12 GiB budget, legacy `plan_admission` admits width 3 (the worker's own test asserts `active_workers == 3`) while the corrected model caps width at 2 — a currently-admitted 3-tile 12 GiB run changes behavior under W1. That is precisely the intended F6 correction, but "the two models agree" contradicts the evidence's own headline boundary.
Verdict: reword (e.g., "single-job geometry admissions agree at 12 GiB; multi-worker width narrows from 3 to 2 by design — see the 3×1 F6 boundary").

### 10. `plan_phase_admission` silently ignores `PhaseJob.visibility_mode` and `PhaseJob.export_overlap` — API gap (minor, conservative direction)

Verification: the plan builder passes only `gdal_cache_bytes`/`native_bytes` (plus `dense_fallback` for geometry) to the reservation builders, so every job is reserved at the builders' defaults `unknown_cold` + `export_overlap=True` regardless of the descriptor fields. This can only over-charge, never under-charge: binary/ternary declarations pay the raw-fallback payload (60,017,664 → 1,925,185,536 B at worst shape), `native_cache` pays the same magnitude as heap raw (asserted by `test_native_cache_mode_charges_resident_mapped_pages`), and the export stream is always included. But a caller setting `visibility_mode=VISIBILITY_BINARY` gets no error and no smaller reservation — the validated, JSON-round-tripped fields are dead inputs on the admission path.
Verdict: acceptable for the worst-case public wiring (m7 uses only the defaults), but thread the fields through or reject non-default declarations explicitly before the phase adapter relies on them.

### 11. Wiring patch omits the configured `block_pixels` — parity nit (minor)

Verification: `_job_estimate` prices the decoded block at `options.block_pixels` (`runtime.py:563`); the patch's `shape_from_building_dsm(job['paths'])` / `shape_from_building_dsm(paths, patches=patch_count)` calls omit `block_pixels`, which then defaults to 128. At `block_pixels=1024` the corrected check would charge 1,253,376 B instead of 10,027,008 B for the decoded-block term — an ~8.8 MiB/worker undercharge relative to the legacy path it mirrors ("mirroring runtime._job_estimate"). Every committed test/boundary number uses block1024 explicitly, so the evidence arithmetic itself is unaffected; only the proposed wiring inherits the default.
Verdict: pass `block_pixels=runtime.block_pixels` through W1/W2 when regenerating the patch (finding 7).

### 12. Parent-side GDAL caching is an unmodeled term — observation, currently safe

Verification: the parent phases do GDAL I/O in-process (`run_walls_aspect` at `api.py:24-46`: serial per-tile `read_raster`/`write_single`, datasets closed per tile; `_calculate_svf` → `prepare_geometry_exports` likewise parent-side). Because every dataset is short-lived, no persistent parent block cache accrues under current code, so the flat 429,496,730 B parent term (M4-corroborated 0.214-0.251 GiB interpreter baseline) is not missing a large resident component today. However, W3 caps `GDAL_CACHEMAX` only in child environments; nothing enforces the parent-side invariant the model silently relies on.
Verdict: note for the integrator — either set `GDAL_CACHEMAX` in-process for the parent phases too, or state the short-lived-dataset invariant in m7 §1 (W3 row). Not verdict-changing.

### 13. Stale self-description numbers in m5/m7 — cosmetic

Verification: m5 §1 says "28 L0 tests" and §7 "tests ran in 0.43 s wall"; m7 §5 gate 1 says "28 at base". Revision-2 reality: 29 collected (24 functions, 6 parametrized), 0.60 s recorded / 0.74 s in my run. The commands file (revision 2) is correct; the prose was not updated in step.
Verdict: update the three numbers. Honesty audit otherwise passes: reservations are declared accounting (not RSS bounds) with the model-only status of pulses/stream terms explicitly restated per F10; synthetic fixtures are labeled throughout; no performance claims; the m2 errata (10.75/20.5) are explicitly not carried and replaced by byte-exact first-principles figures (17,655,385,292; 22,222,943,026 = 20.698 GiB — both independently reproduced).

## Honesty audit

No claim in the certified state exceeds its evidence. The one material process blemish is finding 1 (evidence briefly stale against the tree during active writes; resolved by the revision-2 re-record, which I verified hash-for-hash). Corrections relayed from C6-03 are all genuinely applied and traceable in m5 §9: (a) walls/aspects f32 tile-resident with corrected source chain; (b) the 10.65-vs-10.75 slip replaced by byte-exact arithmetic; (c) 3×1 asserted as a breach configuration with the legacy gap pinned by test; (d) m3 citations replaced by section references plus the corrected line numbers; (e) m4 phase attribution disclosed as absent with model-only transients restated in m5 §7.

## Verdict

**APPROVE-WITH-NOTES.**

The candidate module — the actual deliverable — is correct, inert, pure-integer, and satisfies the C6-42 gate: every relayed C6-03 correction is applied and test-enforced, the 12-cell decision table reproduces byte-for-byte, the legacy anchor is exact against `runtime.estimate_memory`, and the raw-worst boundary (raw-safe width 2 at 12 GiB; 3×1 and 4×1 both refused; legacy still admits 3) is asserted in both probe and tests. Required before integrator consumption (none verdict-changing, none in the module's arithmetic):

1. **F7/F11 (artifact)**: regenerate `m7_phase_admission_wiring.proposed.patch` (it fails `git apply --check` in all three hunks) and thread `block_pixels=runtime.block_pixels` through `shape_from_building_dsm` at W1/W2; add `git apply --check` to the recorded commands.
2. **F8 (analysis)**: correct m7 §3's newly-raising interval to [3.4742, 4.8320) GiB — the legacy check charges no parent term.
3. **F9 (wording)**: restate the m7 §3 "models agree at 12 GiB" sentence per the 3→2 width narrowing under W1.
4. **F10/F12 (design notes for the phase adapter)**: thread or reject `visibility_mode`/`export_overlap` descriptors in `plan_phase_admission`; document (or enforce parent-side) the short-lived-GDAL-dataset invariant behind the flat parent term.
5. **F13 (cosmetic)**: m5 §1/§7 and m7 §5 stale counts/timing → 29 tests, 0.60 s.
6. **F1 (process)**: coordinator protocol — dispatch reviewers only after worker writes have ceased and hashes are recorded.

Byte-exact core certified by this review: legacy 3,730,374,656 B; corrected preprocess 2,674,288,230 / geometry 4,758,857,318 / simulation 5,741,962,854 B; 12 GiB tree at width 2 = 11,913,422,438 B; 3×1 raw-worst tree = 17,655,385,292 B; geometry single-job boundary 5,188,354,048 B (4.8320 GiB).

## Addendum (2026-09-21 12:05, post-race-notice re-verification)

The coordinator's race notice arrived after this review was committed. Re-verification results:

- **Tree unchanged since certification.** All 7 deliverable sha256s re-hashed at 12:02 and identical to the revision-2 set listed in the header; mtimes still pre-11:46. This review's verdict applies to the current tree as-is.
- **Scope correction to finding 4.** My 12-cell diff compared the fields the *pre-revision* probe emitted; the committed decision-table cells additionally carry a per-cell `legacy_would_admit` annotation that a key-scoped diff does not flag. I have now read the revision-2 probe source (`m6_decision_probe.py`, sha `2613aa7c…`) in full and verified the annotation separately: all 12 values (3,3,3,3,2,3,3,4,4,3,2,1) are correct under the documented composition (max k ≤ requested width with k × 3,730,374,656 ≤ budget), and the source emits the field in both the success and rejection branches, so source and committed JSON are consistent (12/12 cells annotated, both 3×1 F6 cells present). Finding 4's conclusion is unchanged and now complete.
- **Two characterization notes on the annotation** (neither an error): (a) `legacy_would_admit` is a uniform-estimate simplification of `runtime.plan_admission` — exact for these cells because every job in a cell shares one shape, and the load-bearing 3×1 case is additionally asserted against the *real* `plan_admission` by `test_three_worker_boundary_raw_worst_and_legacy_gap`; (b) in the writer-queue cell the annotation answers "would legacy admit at this budget" with the writer queue not subtracted — correct as stated, since the legacy model has no writer-queue term, but integrators comparing the columns should read it as estimate-sum-only parallelism.
- **Race-notice claims 1-4: all verified.** (1) 3×1 cells + annotations ✓ (above); 17,655,385,292 B = 16.443 GiB and legacy 3 × 3,730,374,656 = 11,191,123,968 ≤ 12 GiB both recomputed. (2) F7 relabel with unchanged byte totals — confirmed previously (finding 3); the envelope-covered row was never separately priced, so no boundary moved. (3) Errata figures — m2's 10.65-vs-10.75 slip recorded in m5 §5; 16 GiB legacy raw tree 14,921,498,624 + 6,871,947,672 + 429,496,730 = 22,222,943,026 B = 20.698 GiB reproduced. (4) 29/29 tests re-run by me at 11:47 (0.74 s) and again reflected in the revision-2 record (0.60 s); the m5/m7 stale "28"/"0.43 s" prose remains finding 13.
