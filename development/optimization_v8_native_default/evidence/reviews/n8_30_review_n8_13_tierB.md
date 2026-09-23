# n8-rev-n8-13 tier-B review: N8-31 B=1024 transcription, 0817Z amendment, vendored B consumer

**Verdict: APPROVE-WITH-NOTES** — R-B1 through R-B5 all pass; two required repairs are record-level annotations/dispositions (no re-run, no re-measurement). Machine-readable twin: `n8_30_review_n8_13_tierB.json`.

Reviewer: n8-rev-n8-13 (independent). Worktree `/Users/alansynn/Workspace/solweig-v8-native` @ 5d020fd3 + the disclosed uncommitted harness/amendment deltas.

## R-B1 Transcription fidelity: PASS (all values exact)

Every `end_to_end_min_ms` value reproduces **exactly at 4 dp** under the record's stated uniform all-min rule — the first table in this packet that fully traces (tier-A's R13-D1 defect is not repeated):

| mix | A0p | A0s | B1 | C1 |
|---|---|---|---|---|
| all-binary | 3.3627 | 4.503 | 3.5468 | 3.4655 |
| mix | 2.7487 | 3.6432 | 3.0173 | 2.9668 |
| all-raw | 0.5485 | 1.0613 | 0.6943 | 0.7338 |

Producer accounting (2.9092/2.9534/0.0442; 2.3297/2.4561/0.1264; 0.2197/0.2243/0.0046), the +1.5..5.4% range, all verdict percentages (+3.1/+7.9/+33.8 vs A0p; −2.3/−1.7/+5.7 vs B1), the counter-accounting C1-prime (3.2683/2.7693/0.5365 → −2.8%/+0.8%/−2.2%), and adapter scaling (pack 0.1972 ≈ 7.19x tier-A's 0.0274; views ~0.0007; guard 0.0589 vs 0.0122) all recompute exactly. Owner-reported A0s all-binary 4.503 verified (4.50296).

**R-TB1 (required):** the `kernel_leaf_min_ms` section stores **relative fractions**, not ms — C1k_vs_A0p as ms would be [−0.208, −0.166, −0.076], not [−0.459, −0.395, −0.232]. All 9 values are correct as fractions (one last-digit truncation, −0.4596 → −0.459). Cheap annotation fix, needed before N8-32 quotes it: "-0.459 ms" would overstate the native leaf win ~2.2x, in the favorable-to-C direction.

**Label shopping: none in either direction.** The headline is C's worst result (loses 3/3 vs A0p under the charged accounting); the pack-excluding counter-accounting that favors C is INFORMATIONAL with an N8-50/51 demonstration caveat; B1 carries identical adapter charges to C1; A0 excludes adapters per the frozen convention (consistent with tier A); C's guard-layer cost is disclosed as the cause of B's all-raw win.

## R-B2 Archive validity: PASS

REPS=9, min+median stat, 5-way parity pass in all three cells, b_consumer = vendored package path. Ambient [2.480, 4.419, 6.591] is a literal getloadavg() (1m/5m/15m) triple; start==end is bit-identical in the archive (steady host, short timed phase — the harness verifiably reads twice; tier-A's archive shows differing start/end). Start gate: 1-min 2.48 < 5.0. Censor bound >8.0 vs max observed 2.5 → zero censored, correctly. Memory floor unchanged at 1.5 GB; owner self-check 336787 pages × 16 KB ≈ 5.5 GB, correctly labeled not-harness-archived.

## R-B3 Vendored B consumer: PASS — drift ZERO

`src/solweig_light/_native_dispatch/lw_b_control.py` is **byte-identical** (418 lines, empty diff) to `194cb973^:experiments/optimization_v8/numba/lw_b_control.py`, and git history shows no modification between the freeze-era landing (53397af6) and the vendoring move — the vendored `lw_primary_b` is exactly the frozen implementation. In-run 5-way parity proves functional equivalence at B=1024; numba cache-key differences are neutralized by parity + warmup preceding all timed reps. The harness delta records which path served the arm, and its B-unavailable degradation was actually exercised once (check 082019Z, `b_consumer: null`, B-less parity string) 51 s before the successful check — no timing occurred in that state. Note: the docstring's "original copy is kept as fallback" is no longer true (the experiments file is gone); fallback is vestigial.

## R-B4 Amendment timing/proportionality: PASS

Pre-results status verified from the evidence tree: the only tag=timed archives are tier-A ([128], 2026-09-22) and tier-B (08:21:19Z), which postdates the 0817Z amendment (addendum mtime 08:18 UTC). User authorization (< 5.0 over {< 10 immediate, keep < 2.0}) is documented with its pre-results premise. Proportionality: ~50 polls 3.56–32.27 never < 2.0; memory half always passing. All fairness/noise provisions honored (single window, mandatory per-cell annotation — done, >8.0 censor — far from binding, REPS=9 + parity unchanged, INFORMATIONAL/NON-PROMOTION preserved). `gate_amendment_provenance` represents the 5/15-min columns (4.42/6.59) honestly, naming them as the residual desktop load the relaxation accepts. Minor prose nit: "same 1.5x ratio" is 1.6x for 8.0-over-5.0.

## R-B5 N6/N7 obligations: PASS with R-TB2

`n6_envelope_BINDING` states the exact frozen numbers (~2.25 GB @1024², ~9 GB @2048², P=153) in this first-qualified record, as the binding cell requires. The whole-process-peak accounting clause is re-addressed from "N8-31 end-to-end cells" (frozen text) to N8-50/51 — substantively justified (block cells allocate ~10 MB by the 1955Z audit I verified in the tier-A review) and disclosed inline, but it is a literal re-addressal of a MUST in a frozen binding cell: **record it as an explicit disposition** at N8-32 so the selection cites an authorized scope move. `n7_fairness` is faithful: N8-31 cells have zero driver calls on all arms, the resolve is an identical additive driver-level term that cannot flip any ordering here, and the vendoring-disappearance clause is recorded verbatim.

## Required repairs (no re-run needed)

1. **R-TB1** — annotate units on the kernel-leaf delta section (fractions, not ms) or convert to ms.
2. **R-TB2** — explicit disposition for the N6 accounting re-addressal, cited at N8-32.

Recommended: fix the amendment's 1.5x/1.6x prose; fix the harness docstring's stale fallback claim; carry the still-open tier-A repairs (R13-D1/R13-D2) to disposition — this tier-B table proves the R13-D1 uniform rule works.

Scope guard: no timed work, no builds, no commits; records under review untouched; writes confined to `evidence/reviews/` and `/tmp/n8rev_n8_13/`.
