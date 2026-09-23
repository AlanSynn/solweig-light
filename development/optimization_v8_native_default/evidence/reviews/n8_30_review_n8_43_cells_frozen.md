# N8-43 Campaign-Cell Freeze Review — APPROVE-WITH-NOTES

- **Reviewer**: n8-rev-n8-41 (independent; did not author the freeze)
- **Reviewed**: `optimization_v8_native_default/evidence/selection/n8_43_campaign_cells_frozen.json` (untracked NEW) at HEAD `3079d69a`, worktree `/Users/alansynn/Workspace/solweig-v8-native`
- **Companion record**: `n8_30_review_n8_43_cells_frozen.json` (full executed evidence)
- **Scope honored**: read-only + light verification; no commits, no timed work, no builds; writes only under `evidence/reviews/`

## Verdict: APPROVE-WITH-NOTES (one required repair, before campaign start)

The freeze is honest, pre-results, and correctly scoped. The decisive H finding is **CONFIRMED in every link** and is properly recorded as a fact requiring a separately reviewed wiring change — no wiring decision is smuggled. One factual defect in the scene inventory must be amended before the campaign starts.

## Required repair

**R1 — amend the scene inventory before the campaign starts (dated amendment, not a silent edit).** Two statements in `scene_inventory_at_freeze` are false:

1. `state_sequence_original_cpu/scene` is described as an "IDENTICAL duplicate of small_original_cpu scene; same 32x35, **24 records**". Executed comparison: raster inputs are byte-identical (Building_DSM `e13aefb5…`, DEM `a550dd0b…`), but `met.txt` has **49 lines = 48 records** (small has 25 = 24), `processed_inputs` differ, and the captured reference outputs differ. It is a **distinct 48-record forcing on the same geometry, with PRESENT reference outputs**.
2. `census_gaps` claims "NO 48-record fixture exists (every named scene has exactly 24 met records)" — the census's own enumeration contains one.

No PROMOTION_POLICY or BENCHMARK_PROTOCOL sentence requires a 48-step cell, so the **cell table needs no change**; but the freeze rule bars adding cells after campaign start, so the operator must consciously ratify (or amend) the exclusion of a 48-record reference-anchored cell now, while the pre-results window is open.

## Per-claim results

| # | Claim | Result | Key evidence |
|---|-------|--------|--------------|
| 1 | Pre-results: zero B=1024 A/B/C records | PASS | exactly 5 `abc_quiet_window_check_*` smokes + 1 timed archive with `block_sizes == [128]`, INFORMATIONAL/NON-PROMOTION; `trials/` holds only the tier-A record + addendum |
| 2 | 13-row compliance matrix vs PROMOTION_POLICY | PASS | all rows match the actual sentences; dense coverage via two configs of one dense scene is valid ("workload/configuration cells"); p1 legally holds ordinary-default + protected + canary roles; H/B pins verified; 128/256×dense/veg covered 3/4 with the 256-dense exclusion predeclared |
| 3 | **H finding** | **PASS — confirmed** | gates at engine.py **1655/1762/1770/1778** (`parallel = threads_per_worker > 1`); driver defaults `parallel=True` at cylinder_longwave.py **356/406**; seam guard `if parallel and rows*cols` at 386–388; `test_serial_demand_never_dispatches` pins spy==[]; RuntimeOptions `threads_per_worker=1`; DX main_surface.json @**14e88876** pins `threads_per_worker: 1`. Conclusion holds: at the public H=1 default the seam never fires and `resolve_lw_backend` is unreachable — no registry content can produce a native no-env public default. Primary cells c1–c6 are unaffected (driver-boundary `parallel=True`) |
| 4 | Scene census honesty | PASS **with R1** | my independent census reproduces exactly the 3 enumerated scenes (nothing missing); c6/p1 oracle PRESENT (10 TIFFs verified); c1–c5 "absent → unverified" correct; public_roughness manifest genuinely absent; scene_256_dense exclusion predeclared |
| 5 | Arms, N7, RSSTreeSampler, memory arithmetic | PASS | N7 per-call read in all three arms (superset of the addendum's obligation, fair direction); RSSTreeSampler verified at `tools/optimization_v8/n8_02_run.py:81` (0.15 s, ps tree-walk, per-PID peaks); all four per-cell memory figures reproduce from the record's own byte model (c5: 135.7 + 114.7 ≈ 250.4 MiB) |
| 6 | Schedule | PASS | 3 alternating triples = finalist structure; frozen order is a protocol-permitted alternative to randomization; untimed warm pass feeds bitwise parity BEFORE any timed credit, consistent with the protocol and the N8-31 base freeze |
| 7 | Quiet-window gates | PASS | ambient ≤8.0 (B=128) / strict <2.0 (B=1024) / 1.5 GB floor match the N8-31 amendments verbatim (incl. the 4.4→1.5 GB correction); N8-23's 4.33 GB admission explicitly separate; whole block marked PROPOSED-FOR-OPERATOR-CONFIRMATION, not self-ratified |
| — | **Special: H-finding scoping** | **PASS — correctly scoped** | "This freeze changes nothing"; p1 empirically archives the fail-closed fact as a canary; PROMOTION_POLICY's own fallback sentence is invoked instead of a decision; no cell/arm/gate/binding depends on a wiring change; the seam-rework work lives in a separate task |

## Recommended (non-blocking)

- **R2**: line-cite slips — engine gate is 1762 (record says 1767 in two places); the driver seam is 386–390 (record says 401–404, which is the legacy loop tail). Substance unaffected.
- **R3**: the strict-tier headroom is ~2.6–2.8x by the record's own numbers (250.5 MiB + ~0.3 GiB vs 1.5 GB), not "≥3x". Floor still holds; state the honest multiplier.
- **R4**: the check-vs-timed archive distinction is real but rests on filename + content, not a literal `tag` field in the JSONs.

## Bottom line

The predeclaration property holds (claim 1 fully verified), the cell table satisfies every policy sentence, the decisive H finding is factually airtight at HEAD and scoped exactly as "recorded fact + separately reviewed wiring change required, campaign unaffected, p1 measures it", and the schedule/gates faithfully transcribe the N8-31 amendments without self-ratifying. Amend the two false census statements (R1) before the campaign starts and this freeze is ready for operator ratification.
