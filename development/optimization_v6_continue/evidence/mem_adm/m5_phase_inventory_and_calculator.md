# M5 — Derived phase lifetime inventory and the private admission calculator (C6-42)

Worker C6-42 (runtime_specialist).  Base: worktree
`/Users/alansynn/Workspace/solweig-light-v6-memadm`, detached at `5e1fab46`.
Specification input: C6-03 evidence at the same base
(`evidence/memory/m1..m4`), **as corrected by the C6-60 review
(REVIEW_C603_memory.md, APPROVE-WITH-NOTES; corrections F6/F7/F8/F10 applied
to this document and the module — see §9)**.  Served model identity per
INVENTORY routing: GLM via Z.ai.  All numbers below are reproduced by the
committed calculator and asserted by the committed tests; none is an RSS
claim (M4's own limitation note applies: RSS sampling is supporting
evidence, not a bound).

## 1. Deliverables

| Path | Content |
|---|---|
| `src/solweig_light/runtime_memory.py` | NEW private module: inventory data, per-phase reservations, `plan_phase_admission` (reject/queue), JSON-safe descriptors, `legacy_estimate_total_bytes` anchor. Inert: nothing in `src` imports it (tested). |
| `tests/optimization_v6/memory/test_phase_memory_admission.py` | 31 L0 tests, synthetic shape descriptors only, no numerical runs |
| `m6_decision_probe.py` + `m6_admission_decision_table.json` | Programmatic decision table across budget cells |
| `m7_integration_recipe.md` + `m7_phase_admission_wiring.proposed.patch` | Integrator-owned wiring recipe (NOT applied) |

## 2. Derived lifetime inventory (phase × array × dtype × shape × lifetime)

Transcribed from M1 stage tables into `INVENTORY_LINES` (authoritative copy
in the module; the JSON dump in `m6_admission_decision_table.json`
`inventory_lines` is generated from it).  Plane = one full-plane equivalent
of `(rows, cols)` values.  Reconciliation against the legacy accounting
envelope (asserted by `test_inventory_table_reconciles_with_legacy_envelope`):

- simulation persistent (scene 40 + SVF/derived 18 + walls/aspects 2
  [**float32 residents** — dtype corrected per review F7] + wind 12 +
  state 6) = **78 planes**
- simulation core transients (GVF serial 40 + wall-shadow 8 + Kside 7 +
  define_patch 11 + Lcyl 4 + dRad 2 + cylwedge 10 + outputs 10) = **92 planes**
- pulses (digest 10 + checkpoint 12) = **22 planes** → core total = **exactly
  192 planes** — the legacy envelope covers the enumerated families with zero
  slack before the fallback route; adding the fallback-only numpy route
  (30 planes) gives 222 ≤ 192 + 32 ✓
- packed visibility payloads are charged as a byte term, not planes:
  3 × 153 × 1024² × 4 = **1,925,185,536 B = 459 f32 plane equivalents**
  at 1024/P153 (`test_packed_mode_formulas_match_visibility_validation`
  checks the binary/ternary/raw formulas against
  `geometry/visibility.py:90-92`).

## 3. Legacy worst case reproduced from first principles

`legacy_estimate_total_bytes(TileShapeDescriptor(1024,1024,153,12,1024))` =
**3,730,374,656 B = 3.4742 GiB**, asserted equal to
`runtime.estimate_memory(...).total_bytes` (raw 1,925,185,536 + live
989,855,744 + decoded 10,027,008 + native 805,306,368).  Same number as M2
§2 and D04; no correction of the historical figure is needed — the
corrections below are additive charges the legacy model missed, plus one
repricing.

## 4. Corrections (each M2 §6 a-g, with the charged term)

| # | Miss | Charge in calculator | Bytes @1024 |
|---|---|---|---|
| a | GDAL block cache per process (`GDAL_CACHEMAX` unset ⇒ 5% of physical; children are separate processes) | `gdal_cache_bytes` = 5% of probed physical, explicit override supported; W3 proposal caps it in `_child_environment` | 1,717,986,918 (5% of 32 GiB) |
| b | 32-plane float64 reserve priced at float32 | repriced at 8 B/value — pricing the legacy promotion reserve at its denominated dtype (D04).  Per review F7 no resident f64 family exists in-tile (walls/aspects are f32 residents), so this is reserve pricing, not a resident-array claim | +134,217,728 |
| c | checkpoint transit pulse (6 state planes ×2) | `CHECKPOINT_PULSE_PLANES=12` | 50,331,648 |
| d | per-write digest copies | `DIGEST_PULSE_PLANES=10` | 41,943,040 |
| e | export-overlap stream buffers (bounded streaming, M2 §4 windows 1-2) | `DEFAULT_EXPORT_STREAM_BYTES` = 64 MiB, `export_overlap=False` only when the caller asserts no in-window publication | 67,108,864 |
| f | parent footprint (0.2-0.4 GiB M2 §6f; 0.22-0.26 GiB measured, M4) | `DEFAULT_PARENT_FOOTPRINT_BYTES` = ceil(0.4 GiB) = 429,496,730, charged once per tree | 429,496,730 |
| g | phase-shape over-admission | per-phase reservations: preprocess no payload/no envelope; geometry no simulation envelope; simulation unchanged envelope | see §5 |
| — | mmap is not free memory (D04; M2 §7) | `native_cache` mode charges the payload magnitude as `mapped_bytes`, heap payload 0 | 1,925,185,536 |

Writer queue (`writer_queue_bytes`, D04 `M_total` term) is a tree-level
charge; `test_writer_queue_shrinks_admissible_width` shows 1 GiB of bounded
staging queue drops the 12 GiB safe width from 2 to 1.

## 5. Corrected reservations and the 12 GiB boundary (1024/P153/block1024, raw fallback, GDAL 5% of 32 GiB)

Components (from `m6_admission_decision_table.json`
`corrected_component_inventories`):

| Component | preprocess | geometry | simulation |
|---|---|---|---|
| payload | 0 | 1,925,185,536 | 1,925,185,536 |
| live arrays | 83,886,080 (10 f64 planes) | 243,269,632 (58 f32 planes) | 1,124,073,472 (204 f32 + 32 f64 planes) |
| decoded block | 0 | 0 | 10,027,008 |
| native JIT/BLAS | 805,306,368 | 805,306,368 | 805,306,368 |
| GDAL cache | 1,717,986,918 | 1,717,986,918 | 1,717,986,918 |
| write pulses | 0 | 0 | 92,274,688 |
| export stream | 67,108,864 | 67,108,864 | 67,108,864 |
| mapped pages | 0 | 0 | 0 |
| **total** | **2,674,288,230 (2.4906 GiB)** | **4,758,857,318 (4.4320 GiB)** | **5,741,962,854 (5.3476 GiB)** |

Tree arithmetic at the 12 GiB budget (parent 429,496,730 B, writer queue 0):

- 2 × simulation + parent = **11,913,422,438 ≤ 12,884,901,888** ✓ (headroom
  971,479,450 B) — **2×2 geometry+simulation admitted**
  (`test_boundary_12gib_admits_two_workers_rejects_four`; mixed
  geometry+simulation tree = 10,930,316,902 ✓)
- **3×1 is also a breach configuration (review F6 — not unique to 4×1)**:
  the legacy public model budget-admits 3 workers
  (3 × 3,730,374,656 = 11,191,123,968 ≤ 12 GiB; asserted
  `plan_admission(...).active_workers == 3` in
  `test_three_worker_boundary_raw_worst_and_legacy_gap`), but the raw-worst
  tree is 3 × 5,741,962,854 + 429,496,730 = **17,655,385,292 B = 16.443 GiB
  > 12 GiB** (the review's own composition gives ≈15.72 GiB with m2's
  estimate-total + GDAL terms and parent 0.3 — same conclusion).  The
  corrected calculator charges every raw-worst component per worker, so
  budget-admission and raw-safety coincide: **3×1 is rejected**
  (`only 2 fit`; queue policy `admissible=2, deferred=1`).  **Raw-safe
  worker count at 12 GiB is 2**, which equals the budget-admitted count.
- 4 × simulation + parent: reject policy raises `ResourceAdmissionError`
  naming 22,967,851,416 B; queue policy returns
  `queued, admissible=2, deferred=2`
- geometry-only 4×1: admissible = 2; preprocess-only 4×1: **admissible = 4**
  (tree 11,126,649,650) — the phase-shape correction legitimately widens the
  preprocess phase that the legacy model blocked with the 3.4742 GiB
  simulation estimate (M2 §6g)
- at the 32 GiB-host default budget (50% ⇒ 16 GiB) 4×1 simulation is
  **still rejected** (base 15.6 GiB < 3 × 5.348 GiB + parent): the corrected
  model rejects before start the configuration M2 §7 flagged as the breach
  risk.  From first principles the legacy model at 16 GiB would have
  admitted 4 × 3,730,374,656 = 14,921,498,624 B (13.898 GiB) of estimates
  while the raw tree reached 14,921,498,624 + 4 × 1,717,986,918 (GDAL) +
  429,496,730 (parent) = 22,222,943,026 B = **20.698 GiB** — m2's "≈20.5"
  used parent 0.3 and rounding; its own 2×2 raw-worst line also printed
  terms summing to 10.65 GiB while stating ≈10.75 (10.75 needs parent 0.4);
  both are m2 errata per review F6 and are not carried into this document
- single infeasible job: 5.5 GiB budget ⇒ base 5,476,083,302 B < one
  simulation reservation ⇒ raises in **both** policies (queueing cannot fix
  an impossible job)

## 6. Failure semantics (C6-03 m3)

- `ResourceAdmissionError` is the existing `runtime` class, re-exported for
  type identity; raised **in-process only** (admission is a pre-dispatch,
  parent-side decision in the recipe).  Never pickled through workers;
  `test_reject_policy_raises_in_process_runtime_error_identity` pins the
  class identity.
- Missing shape data raises: malformed `PhaseJob` dimensions (6 bad-value
  cases), missing `PhaseJob(PHASE_SIMULATION)` args, unreadable
  Building_DSM in `shape_from_building_dsm`.  No zero-byte fallback exists.
- Pure-integer arithmetic; no `np.seterr` manipulation anywhere; no negative
  intermediate (`test_no_negative_budget_arithmetic`).
- Transactional publication (per-tile journal) is untouched — the module
  owns no publication path.

## 7. What is NOT claimed

- No behavioral change: the module is inert (nothing in `src` imports it;
  `test_module_is_inert_until_wired` also proves it pulls in no numba/gdal
  import of its own beyond the lazy, metadata-only GDAL open in
  `shape_from_building_dsm`, which mirrors the existing
  `runtime._job_estimate` behavior).
- The reservations are admission accounting derived from the M1 lifetime
  inventory, not measured RSS bounds.  **Per review finding 10, m4 contains
  no phase attribution**: the P1' export-overlap stream cost and the P2/P3
  transient pulse magnitudes charged here are model-only terms from the M1
  inventory, unvalidated by measurement at any scale.  m4 informs exactly
  one term of this model — the process-baseline/parent footprint (measured
  0.214-0.251 GiB at 35x32) — and nothing else.  No 1024 numerical run was
  made (none needed at unit level per task brief).
- Timing: the 31-test suite ran in 0.48-0.96 s wall across recorded rev-3
  runs under the contended development tier; recorded, no performance claims.
- The stricter geometry boundary interval and its sign-off requirement are
  in `m7_integration_recipe.md` §3.

## 8. Commands and hashes

See `m5_commands_and_hashes.txt` (commands, exit codes, sha256 of every
deliverable at the recorded tree state).

## 9. C6-60 review corrections applied (2026-09-21, REVIEW_C603_memory.md)

| Finding | Correction applied here |
|---|---|
| F7 (walls/aspects dtype) | Inventory row is float32/4 B with the corrected source chain (`read_raster` astype f32, `write_single` GDT_Float32, `GeometryCache` passthrough); f64 exists only as preprocess intermediates.  The 32-plane DTYPE64 repricing is retained and rejustified as promotion-reserve pricing (D04), no longer justified by resident arrays.  Plane counts, byte totals and every boundary result are unchanged (the row was always f32-priced inside the 192-plane envelope; only its label was wrong). |
| F6 (2x2 raw-worst sum slip; 3x1 boundary) | m2's 10.75/20.5 figures are not carried; all raw-worst arithmetic here is byte-exact from first principles.  New explicit 3×1 test and probe cells: legacy budget-admits 3×1 at 12 GiB (active=3 asserted) while raw-worst tree 17,655,385,292 B breaches; corrected calculator rejects 3×1.  Raw-safe worker count = 2 = budget-admitted count; 4×1 is not the unique breach config. |
| F8 (m3 citation slips) | This evidence cites m3 by section, not by `persistence.py` line; for the record the corrected references are renames `:587-592`, manifest-last `:594`. |
| F5 (plan_admission wording) | The per-job single-tile check applies to all jobs, not only active ones — consistent with how `plan_phase_admission` treats infeasible jobs (raises for any job that can never fit, in both policies). |
| F10 (m4 phase attribution) | §7 restated: transient magnitudes are model-only; m4 informs only the parent/baseline term. |

The verified byte-exact core (3,730,374,656 B block1024 / 3,721,601,024 B
block128) was confirmed by the reviewer's independent recomputation and
stands unchanged as this module's `legacy_estimate_total_bytes` anchor.

## 10. C6-42 review fixes applied (2026-09-21, rev 3)

APPROVE-WITH-NOTES (13 findings, none verdict-changing).  Applied:

| Review fix | Change |
|---|---|
| 1 | `m7_phase_admission_wiring.proposed.patch` regenerated with `git diff` over the three wiring edits; `git apply --check` passes (recorded in `m5_commands_and_hashes.txt`). |
| 2 | m7 §3 sign-off interval corrected to **[3.4742, 4.8320) GiB** — the legacy single-job check charges no parent term, so the lower bound is the bare legacy estimate, not legacy + parent. |
| 3 | m7 §3 width-3 claim reworded: both models admit 2×2 at 12 GiB; for width-3 requests the corrected model narrows 3→2 — the intended C6-60 F6 correction, not "no change". |
| 4a | `plan_phase_admission` now forwards `visibility_mode`/`export_overlap` to geometry/simulation reservations and raises `ValueError` for preprocess jobs that set either (preprocess has no visibility payload and no publication window); two new tests cover forwarding and rejection. |
| 4b | Patch wiring forwards `block_pixels=runtime.block_pixels` at W1/W2 (was ~8.8 MiB/worker undercharge at 1024). |
| 4c | m7 §1 documents parent-side GDAL caching safety (metadata-only opens, short-lived per-tile datasets, no parent raster IO) and the condition that would require revisiting `DEFAULT_PARENT_FOOTPRINT_BYTES`. |
| 4d | Stale counts updated: 31 tests / 0.96 s here and in m7 §5. |

No constant, reservation formula or boundary byte total changed in rev 3;
the probe decision-table JSON is byte-identical to rev 2.
