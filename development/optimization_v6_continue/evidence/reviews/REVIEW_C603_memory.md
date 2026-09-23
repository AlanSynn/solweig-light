# REVIEW_C603 — Independent review of C6-03 memory evidence

- **Reviewer**: C6-60 (service instance). Independent GLM review; Opus unavailable (routing: GLM via Z.ai).
- **Date**: 2026-09-21
- **Review worktree**: `/Users/alansynn/Workspace/solweig-light-v6-rev603`, detached at `5e1fab46`.
- **Evidence commit**: `e7a2d6ec8594b234820e7783e0ca26d821de7f3d`. Verified `e7a2d6ec` is an ancestor of `5e1fab46` and `git diff --stat e7a2d6ec 5e1fab46 -- src/` is empty, so every `path:line` citation in m1-m3 resolves identically in this worktree.
- **Evidence under review**: `optimization_v6_continue/evidence/memory/{m1_stage_live_array_inventory.md, m2_worst_case_memory_model.md, m3_publication_failure_semantics.md, m4_instrumented_run.json, m4_notes.md}` (+ `m4_run.py`).
- **Contract**: DESIGN_AUTHORITY.md; dossiers/04_phase_pool_and_memory.md (D04); VALIDATION_POLICY.md; TASKS_CLAUDE.yaml C6-03 (`requires_independent_review: true`; gate: "raw/native/parent overlap budgeted", "sorted partial-publication behavior mapped").

## Method

I recomputed the budget arithmetic from the source constants myself (not by re-reading m2), spot-checked every load-bearing source citation listed in the review scope at `5e1fab46`, and ran one additional concurrency configuration (3x1) through the admission logic. Read-only checks with `/Users/alansynn/Workspace/solweig-light/.venv-light/bin/python`. No workloads rerun.

## Findings

### 1. Worst-case total 3.4742 GiB (m2 §2) — CONFIRMED, reproduced exactly

Claim: model total at 1024x1024/P153/w12/block1024 = 3.4742 GiB (3,730,374,656 B); block128 variant 3.4660 GiB; matches D04's "~3.474 GiB".

My recomputation from `estimate_memory` (`src/solweig_light/runtime.py:457-502`) and constants (`:279-286`: fraction 0.50, windchannels 12, LIVE=192, DTYPE64=32):

| Term | My value | Source |
|---|---|---|
| raw_visibility = 3*1048576*153*4 | 1,925,185,536 B = 1.7930 GiB | runtime.py:478 |
| live_arrays = (192+32+12)*1048576*4 | 989,855,744 B = 0.9219 GiB | runtime.py:482-486 |
| decoded block1024 = 1024*153*16*4 | 10,027,008 B = 9.5625 MiB | runtime.py:487 |
| decoded block128 | 1,253,376 B = 1.1953 MiB | runtime.py:487 |
| native = 256 MiB + 64 MiB*min(8,12) | 805,306,368 B = 0.750 GiB | runtime.py:489 |
| **total block1024** | **3,730,374,656 B = 3.4742 GiB** | runtime.py:490 |
| total block128 | 3,721,601,024 B = 3.4660 GiB | |

Byte-exact match with m2 and with D04's "~3.474 GiB at 1024/P153/default wind reserve/block1024". Verdict: correct.

### 2. DTYPE64 float64 undercount = 128 MiB (m2 §3) — CONFIRMED

Claim: the 32 `DTYPE64_RESERVED_PLANES` are multiplied by float32 (4 B/px) inside the `live_arrays` term, not 8; undercharge at 1024 = 128 MiB.

Verified: the entire `live_arrays` term is `* pixels * float32` (`runtime.py:482-486`); there is no 8-byte path for the reserve. Undercharge = 32 * 1,048,576 * 4 = 134,217,728 B = 128 MiB exactly. This is precisely the defect D04 warns about ("Correct float64 accounting means eight-byte arrays, not just a label on four-byte planes"). Verdict: correct.

### 3. GDAL_CACHEMAX not set in child environments (m2 §5, miss a) — CONFIRMED

Claim: `_child_environment` (`runtime.py:663-676`) sets only the seven thread-limit variables; `GDAL_CACHEMAX` is absent, so each worker process can accumulate the GDAL default (~5% of physical RAM) uncounted.

Verified: `runtime.py:663-676` sets OMP/OPENBLAS/MKL/NUMEXPR/VECLIB/BLIS/NUMBA only. `io/rasters.py:66-78` (`StreamingOutputs.write`) does WriteArray + FlushCache per band (flushes dirty blocks only). The per-process ~5% default and the W x 1.6 GiB (32 GiB host) multiplier are standard GDAL defaults; the magnitude claim is plausible and correctly flagged as the largest uncounted term. Verdict: correct.

### 4. Preprocess phase over-admission (m2 §6 miss g) — CONFIRMED, with in-source corroboration

Claim: `run_walls_aspect` (`api.py:17-47`) charges the full 3.47 GiB per-file estimate for a ~0.2 GiB float64 phase, blocking up to 6-7 workers unnecessarily.

Verified: `api.py:33` calls `plan_admission([{'paths': {'Building_DSM': ...}}], runtime)` per file; `_job_estimate` (`runtime.py:532-563`) resolves dimensions from the DSM and falls through to `estimate_tile_memory(rows, cols, DEFAULT_PATCHES=153, DEFAULT_WIND_CHANNELS=12, ...)` — the full simulation estimate. The phase itself allocates ~8-10 float64 planes (`walls.py:181` `y = np.zeros(a.shape)` defaults to f64; `walls_compiled.py:39,49` both `np.zeros((rows,cols), dtype=np.float64)`) plus f32 DSM ≈ 0.1-0.2 GiB. The source itself concedes this at `geometry/service.py:272-274`: "The full pipeline inventory conservatively overestimates geometry-only work". Verdict: correct.

### 5. plan_admission structure (m2 §1) — CONFIRMED with one trivial imprecision

Verified: `plan_admission` (`runtime.py:566-592`) does a per-job single-tile check (`:571-577`) and a K-largest-descending cumulative check (`:584-589`); static sum, no phase dimension — matches m2. Imprecision: m2 says "(a) each *active* job's individual estimate must be ≤ budget"; the per-job check applies to **all** jobs, not only active ones. No consequence. Verdict: correct as described for the K-largest rule; note the wording.

### 6. Concurrency boundary 2x2-safe / 4x1-unsafe at a 12 GiB tree cap (m2 §7) — CONFIRMED, with two refinements

Reproduced (parent footprint p, pulses 0.2, GDAL 1.6 GiB/worker on 32 GiB host):

- 2x2 admitted: 2 * 3.4742 = 6.9484 GiB; + p=0.3 ⇒ 7.248 GiB; headroom 4.75 GiB — matches m2.
- 2x2 raw worst: 3.2 + 6.9484 + 0.3 + 0.2 = **10.65 GiB**, not m2's "≈ 10.75". m2's own printed terms (parent 0.3) sum to 10.65; 10.75 requires parent = 0.4 (top of its stated 0.2-0.4 range). Either way < 12 GiB with 1.25-1.35 GiB headroom — conclusion unchanged, but the line is internally inconsistent by 0.1 GiB.
- 4x1 at default budget (32 GiB host ⇒ 16 GiB budget): 4 * 3.4742 = 13.897 ≤ 16 ⇒ admitted by plan_admission; raw ≈ 20.5-20.9 GiB > 12 GiB cap ⇒ breach — matches m2. (At an explicit 12 GiB budget, 4x1 is refused outright: 13.897 > 12.)
- **Additional configuration 3x1 (my check)**: at a 12 GiB budget the K-check admits 3 workers (10.423 ≤ 12; `plan_admission` K-loop confirms active=3), but raw worst = 3*(3.4742+1.6) + 0.3 + 0.2 = **15.72 GiB > 12 GiB cap**. So in raw terms the 12 GiB-safe worker count is 2, and 3x1 at the default 16 GiB budget also breaches a hard 12 GiB tree cap. m2 never claims 3x1 is safe, and its verdict sentence is written as a 2x2-vs-4x1 contrast (the D04 comparison pair), but the phrase "that configuration ... is the one that can breach" reads as if 4x1 were the unique breach configuration; it is the breach *boundary at best*, with 3 workers already raw-unsafe.

Verdict: conclusions as stated (2x2 safe, 4x1 at default budget unsafe) are correct; refine the wording per above.

### 7. m1/m2 mislabel tile-resident `walls`/`aspects` as float64 — ERROR FOUND (small, conservative direction)

Claim (m1 Stage 0): "`walls`, `aspects` | P (tile) | full plane **f64** | GeometryCache via `pipeline.py:202` ... the only non-32-byte-per-pixel family at entry". Claim (m2 §3): walls/aspects "persist tile-long (M1 Stage 0)" as f64.

Verified: inside the simulation tile these arrays come from `read_raster` (`pipeline.py:100-101`), which does `ReadAsArray().astype(np.float32)` (`io/rasters.py:24`); the on-disk artifacts are themselves written as `GDT_Float32` by `write_single` (`api.py:41-42` → `io/rasters.py:31-35`); `GeometryCache` (`models.py:55-63`) stores them as passed (`pipeline.py:202`). Float64 walls/aspects exist **only** as preprocess in-memory intermediates (`walls.py:181`, `walls_compiled.py:39,49`) and are downcast before publication. The f32-promotion dispatch at `engine.py:1716-1727` (compiled `exact_13`/`exact_23` require all-f32 inputs) confirms the engine sees f32.

Impact: 2 planes x 4 MiB = 8 MiB overstatement at 1024 (~0.23% of the estimate), conservative direction; no arithmetic or concurrency conclusion changes. But m1 is the authoritative array inventory and this family's resident dtype is wrong; it also weakens m1/m2's stated *rationale* for the 32-plane DTYPE64 reserve (there is in fact no resident f64 family in-tile — the reserve is purely against hypothetical promotions, which is what `runtime.py:479-481`'s comment actually says, so the reserve semantics stand). m2 §3's "Actual f64 families in the pipeline" list should name preprocess intermediates only, with tile-resident walls/aspects as f32. Verdict: correct the inventory row and the m2 §3 sentence; nothing downstream breaks.

### 8. m3 publication-failure semantics — CONFIRMED (two citation slips)

Verified against source at `5e1fab46`:

- Transaction identity sha256 over sorted output paths: `persistence.py:268` — exact.
- `resume=False` refusal: `persistence.py:285-287` raises `PersistenceError("Incomplete output transaction exists; request resume=True explicitly")` — exact. Nothing-to-resume raise `:304-305` — exact.
- Digest verification: `:131` (state load), `:334` (previous-completion), `:591` (published-artifact check) — exact; `_recover` at `:389-429` with state verify `:403` — exact; checkpoint record with `state_sha256` + `band_hashes` at `:488` — exact.
- `complete()` (`persistence.py:540-595`): publication journal written first (`_atomic_json(publication_path)` at `:581`), per-artifact staged→final renames `:587-592`, completion manifest **last** (`:594`). Substance exactly as m3 states. Two citation slips: m3 cites ":577" for the renames (that line is journal-entry construction; renames are `:587-592`) and attaches "(:601 references the held-set)" to the manifest-last claim (the manifest-last write is `:594`; `:599-601` is the held-set check inside `_lock_extra_publication`). Cosmetic; the ordering claim itself is true.
- `ResourceAdmissionError` parent-side rebuild, not pickling: `runtime.py:618-660` — `_CHILD_BUILTIN_EXCEPTIONS` allowlist + `(module, name)` dispatch, `ResourceAdmissionError` at `:647-648`; failure payload is a schema-1 JSON mapping (`runtime_worker.py:50-61`). Exact.
- Scheduler: dispatch strictly `next_index`-ascending (`runtime.py:819`, `:901-903`, `:938-950`); failure raise on nonzero code or missing marker (`:871-874`, `:898`); reap-all with `terminate=True` (`:955-961`; early path `:868`). Exact.
- Phase orderings: `api.py:29` unsorted `os.listdir`; `api.py:81` lexicographic `sorted(set intersection)`; `api.py:151` numeric tuple sort; barriers as a sequential call chain at `api.py:208-210` (run_walls_aspect :208 → _calculate_svf :209 → run_utci_tiles :210). All exact. The lexicographic-vs-numeric example ("10_10" before "2_2" as strings, after numerically) is correct.
- Worker retirement: `gc.collect()` per job (`runtime_worker.py:85`), bounded retained resources (ray-schedule `lru_cache(36)` `ground_view.py:64`, ≤64 KiB per `:71` comment; `patch_geometry` `lru_cache(8)` `patch_radiation.py:54`). Exact.

Verdict: correct; fix the two line references.

### 9. m1 inventory citations — spot-checked, all resolve (one content error per finding 7)

Checked: `io/rasters.py:20-28` (f32 casts), `pipeline.py:128-138` (veg/building derivations), `:158-192` cold geometry path with `save_rasters=False` + `GeometryStore.get_or_create` (`:185`), `:193-200` (svfbuveg/asvf/LazyDiffVisibility/svfalfa), `:202` GeometryCache, `:216-223` wind coefficient planes (≤12, `DEFAULT_WIND_CHANNELS=12` at `runtime.py:281`), `:224-226` zero/ones/SimulationState, `:227-236` args dict, `:244-247` TransactionalOutputs, `:283` explicit `del result, fields, output, tmrt, utci, speed, temperature`, `:286-300` legacy SVF export while all persistent families live + `writer.complete(extra_artifacts=extra)` at `:300`; `geometry/svf.py:111` (15 f32 fields — exact), `:122-126` compact builders vs dense cube (`(sum(counts), rows, cols)` f32, 153-patch worst), `:132` per-patch `shadow(...)`; `geometry/visibility.py:90` (raw = pixels*4 ⇒ 32 b/px, exact), `:253-258` LazyDiffVisibility per-access decode; `engine.py:1563` (`aniLum += _operate(np.multiply, diffsh[:,:,idx], lv[idx,2])` — 2-plane decode per patch, exact), `:1676` return tuple (counted: **39 elements** — exact), `:1693-1707` `_operands` f32 guard, `:1738-1749` fused dispatch with `block_rows=32`; `ground_view.py:218` `output=np.empty((16,*shape))` (exact), `:413-428` (counted the `_zeros` block: **16 accumulator planes** — exact), `:240-263`/`:443-450` prepared copies, `:652-655` fused `(16, block_rows, cols)` block; `patch_radiation.py:544` `(7, pixels)` (exact), `:560-582` block loop, `:883` `(11, rows*cols)` (exact), `:903-932` Lcyl (patch-sized, ≤4 planes holds); `wall_shadows.py:77-105` `(5,sx,sy)` / `:140-200` `(8,sx,sy)` outputs; `service.py:258-327` with `plan_admission` at `:275`, `_destination_locks` `:29-59`, GDAL schema probe `:85-104`, bounded compare workspace `:172-188`, staged export with hard-link rollback `:212-255`; `cache/geometry.py:150-158` close, `:194-219` mmaps (`ARRAY_FIELDS = SVF_FIELDS + ('svftotal',)` ⇒ 16 mmap arrays + 3 visibility — exact); `visibility_native.py:63-119` MappedVisibility with explicit close, open at `:260-261`. Verdict: inventory is source-accurate except finding 7.

### 10. m4 instrumented run — supports what it claims; gaps disclosed, none hidden

Verified `m4_run.py` matches `m4_notes.md`: in-process `run_utci_tiles`, `memory_budget_bytes=4 GiB`, `cpu_budget=1`, `threads_per_worker=1`, `block_pixels=128`, tracemalloc + `ru_maxrss` + 20 ms sampler, temp-dir copy, numerics untouched. JSON internally consistent: tracemalloc_end 55.109 < peak 64.62 MiB (no-leak claim holds), top sites import machinery (22.7 MiB), rss_peak_sampled 219.4 / final 256.8 MiB.

- Parent/native-library footprint: measured 0.214-0.251 GiB vs m4_notes' "≈ 0.22-0.26 GiB" (slight up-rounding, immaterial) — corroborates m2 §6(f)'s 0.2-0.4 GiB parent term with actual data.
- **Phase attribution: m4 contains none.** The JSON has no per-phase breakdown (no geometry/preprocess/simulation split). Neither m1 nor m2 claims m4 provides phase attribution — m2's phase table (§2) is arithmetic from m1's inventory, labeled as such — so this is a gap in measurement coverage, not a misrepresentation. It does mean the P1' overlap-window and P2/P3 pulse magnitudes (~0.05-0.16 GiB transient terms) remain model-only, unvalidated at any scale.
- Scale honesty: m4 explicitly states it cannot validate 1024-scale peaks (35x32 ≈ 940x smaller; 1024²/(35·32) = 936 ✓) and invokes D04's "RSS sampling is supporting evidence, not a hard upper bound". This complies with VALIDATION_POLICY L17 ("No per-worker/per-commit 1024 admission"). Scope statements (1024 model in m2, 35x32 measurement in m4) are correctly separated throughout.
- Note for portability: `m4_run.py:27` divides `ru_maxrss` by 1024² assuming bytes (macOS); on Linux the same script would under-report RSS by 1024x (KB units). Correct for this host; flag if the run is ever reproduced on Linux.

Verdict: supported; measurement coverage gaps are disclosed rather than papered over.

### 11. Honesty audit — PASS with the finding-7 caveat

- No claim in m1-m3 is presented as measured; m1/m3 are declared source-derived inventories/contracts, m2 declared arithmetic. m4 is the only measurement and is honestly scoped.
- m2 §2 phase-table values (P0 ≈ 0.1-0.2, P1 ≈ 2.0-2.4, P2 ≈ 3.6, P3 ≈ 3.6-3.7) are internally consistent with my recomputation (P2: 3.4742 + 0.16 GVF-serial + 0.03 wall-shadow ≈ 3.66) and labeled approximations. Spot-checks of the underlying plane counts (16 GVF accumulators, 8/5-plane wall-shadow outputs, 15 SVF fields, 39-tuple) were exact.
- Exceptions: finding 7 (walls/aspects dtype), finding 6 (10.65-vs-10.75 sum), finding 8 (two line refs). None is an overclaim of evidence; the dtype error is the only factual inventory mistake and it errs conservative.

## Verdict

**APPROVE-WITH-NOTES.**

The deliverable satisfies the C6-03 gate: raw/native/parent overlap budgeted (m2 §4-§5, §7 — verified arithmetic), sorted partial-publication behavior mapped (m3 — verified against source). The headline numbers reproduce byte-exactly (3,730,374,656 B; 128 MiB undercharge), and every admission-miss claim (GDAL_CACHEMAX, DTYPE64 charging, parent footprint, phase over-admission) is real and correctly cited. Required corrections before this inventory feeds C6-42 (phase memory admission) — all small, none verdict-changing:

1. **F7 (content)**: correct m1 Stage 0 walls/aspects to float32 tile-resident (f64 is preprocess-intermediate only; on-disk artifacts are GDT_Float32) and the matching sentence in m2 §3. Re-check whether any DTYPE64-rationale text needs rewording.
2. **F6 (arithmetic)**: fix the 2x2 raw-worst sum (≈10.65 at parent 0.3, or state parent=0.4 explicitly); add the 3x1 raw-unsafety boundary note so "the one that can breach" is not read as unique.
3. **F8 (citations)**: m3 ":577" → ":587-592"; ":601" → ":594".
4. **F5 (wording)**: m2 §1 "(a) each active job's" → "(a) each job's".

Unvalidated-by-measurement residual (accepted, disclosed): P1' export-overlap stream cost and the P2/P3 transient pulses are model-only; m4 provides baseline-overhead and no-leak evidence at 35x32 only, and contains no phase attribution.
