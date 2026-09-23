# Review: C6-81r reopened selection record

Date: 2026-09-21. Reviewer: independent GLM review; Opus unavailable (per
DELEGATION.md provider-integrity rule; standing routing fact INVENTORY_C6-00).
Subject: `evidence/selection/C6-81r_selection_reopened.md` vs its cited
evidence. Read-only verification; the record under review was NOT edited.

## Scope

Read: the record under review; `campaign_synthetic/README_C6-101r.md`,
`campaign_verdict.json`, `phase1_attribution.json`; prior
`selection/C6-81_selection.md`; `DELEGATION.md`; `inventory/LEDGER_C6.md`
(rows C6-81, C6-81r, C6-100, C6-101, standing facts).

Recomputed from `phase1_attribution.json` (profiled total self 136.1013 s):
every percentage quoted in the record's residual table, the two selections'
arithmetic, the additive-family sum, the S01 cold-share claim, and the
campaign speedup table against `campaign_verdict.json`.

Trusted (outside the permitted reading set): C6-100 integrator dispositions
§1 (re-freeze path), the recorded user-authorizations of 2026-09-21, the raw
`phase1_profile.json`/pstats artifacts behind the decode callsite split,
freeze-commit identity beyond the ledger row.

## Recomputation results

1. **Residual shares vs attribution — MATCH.**
   - visibility 36.7611/136.1013 = 27.01% (record: 27.0%). Split slices
     19.5/11.8/5.8 s match README verbatim (decode_patch self 5.7621).
   - patch `_classes`: self 12.2833 + SLEEF atan_array 6.4981 inside cum
     20.5807 → 15.12% (record: ≈15% cum; 12.3 s + 6.5 s exact).
   - GVF 15.6% = (gvf_ground_view 20.2349 + gvf_prepared 0.9853)/136.1013
     = 15.59%; gather kernel 18.4775 ≈ 18.5 s; prepared route ncalls = 14.
   - engine 11.61%, cyl_lw 7.53%, checkpoint/io 7.48% (FlushCache 7.0304 s),
     wall_shadows 4.08%, kside_cylsw 3.32%, comfort 3.12% — all match.
   - All 17 nonzero additive families sum to 99.99% (internally consistent).
   - Combined selected lever 27.0 + 15.1 = 42.1% (record: ~42%).
   - S01: 217 s / 930.17 s T4-cold integrated median = 23.3% (record ≈23%);
     warm svf 1.94–1.97 s both trees supports "warm-nil".
2. **Conditional decode gate — CORRECTLY BOUND.** "+21–24% full-frame sweep
   loss" and "does not amortize with size" match C6-81_selection.md's
   DECLINED row (46450c75; four cells t128/t256 × strides 128/1024); the
   stay-off/opt-in constraint matches `SOLWEIG_LIGHT_PREPARED_VIS=1`; the
   "materially different decode structure" requirement matches the README's
   mechanism warning (locality/batching, not the declined one-entry
   prepared variant); same-protocol requirement is consistent with the
   C6-80/C6-101r single-lease child protocol.
3. **R04 stop-condition reading — SUPPORTED.** `_classes` self is 12.28 s of
   its 20.58 s cum; the only large callee is SLEEF atan compute (6.50 s);
   remaining callees ≈ 1.8 s. No lookup/memoization entries appear anywhere
   in the top-25 self table — compute-dominant, i.e. "poor if lookup
   dominates" does not bite. Matches the README selection input exactly.
4. **NOT SELECTED vs "measured residual, not catalog size" — CONSISTENT.**
   All declines cite measured shares smaller than the selected items'
   addressable shares, and all match the README ranking (decode 27% >
   patch 15.1% > G05 > R09 7.1% > comfort 3.1%); S01 declined as warm-nil
   against the record's stated warm-lift purpose. Decline logic evolved
   coherently from the prior C6-81 record: reasons shifted from "no
   measurement exists" to "measured smaller than selected", never
   contradicting it. G05's addressable slice (postprocess cum 8.4352 +
   wall 5.5554 = 10.3%) is indeed below patch 15.12%, so the ordering holds.
5. **Constraints — COMPLETE AND CORRECT per the ledger.** Freeze ea2eed53
   (ledger C6-100 row), decoder stays off/opt-in (C6-81 decline + ledger
   C6-50 note), exactness gates bound to wrapper routes (ledger standing
   fact; bitwise gates imply no-FMA/no-reassociation), exclusive lease +
   SYNTHETIC/no-actual-target labeling (ledger standing facts; README).
6. **SYNTHETIC labeling — PRESENT.** Title, basis paragraph (single-run
   ratios, profiler distortion, ±7–13% rep spread quoted from README), and
   constraints all carry the dev-tier/no-actual-target framing. Slot count
   (5) and threads=4/one-tile Phase-1 setup match the README; warm-sim
   98.6%-of-workflow figure recomputes to 98.65%.

## Verdict

**APPROVE-WITH-NOTES.** No blocking findings; every recomputed number in the
record matches its cited evidence.

## Notes (non-blocking; do not require edits to the record)

- N1 — GVF share basis differs between lines of the record: 15.6% in the
  residual table (gvf_ground_view + gvf_prepared wrapper) vs 14.9% in the
  G05 NOT SELECTED line (additive family alone). Both are correct against
  the evidence; the unstated basis switch could confuse a later reader.
- N2 — "Lside cum 7.1%" is a share of engine cum (8.4538/119.748 = 7.06%),
  whereas its row-neighbors (4.1/3.3/3.1%) are shares of profiled total
  (Lside is 6.2% of total). The record mirrors the README's convention
  without restating it.
- N3 — The decode callsite split sums to 19.52 + 11.84 = 31.36 s against
  decode_block cum 30.75 s (0.61 s, ~2%, upstream README figures the record
  repeats). Within single-run noise; no effect on the 27% family share or
  the selection.
- N4 — The G05 decline line quotes whole-family shares (14.9% + 4.1%) while
  the ranking decision effectively compares G05's addressable slice
  (≈10.3%) against patch 15.1%; also, patch 15.1% vs GVF 14.9% is a
  knife-edge ordering on a single-run ratio, which the record resolves via
  its stated secondary criterion (exact-coefficient reuse priority) — that
  criterion is recorded, so the decision stands, but later readers should
  not read the G05 line as "a 19% family was passed over for a 15% one".
- N5 — The C6-100 dispositions §1 re-freeze path and the 2026-09-21 user
  authorizations were trusted, not independently read, per this review's
  fixed file scope.
