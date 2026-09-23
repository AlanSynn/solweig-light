# n8-rev-n8-13 selection review: N8-32 record against the pre-registered skeleton

**Verdict: APPROVE-WITH-NOTES.** The branch application, sub-clause reading, R-TB2 disposition, campaign disposition, and outcome integrity all check out against the pre-registered skeleton and my two tier reviews. One required carried correction (R-SEL-1) concerns the tier-A B1 composition behind the record's R13-D1 closure claim — it is outcome-invariant and does not touch the selection decision. Machine-readable twin: `n8_30_review_n8_32_selection.json`.

## R-S1 Branch fidelity: PASS — no post-hoc reinterpretation

The skeleton's pre-registration is genuine: commit 290da338 landed 2026-09-22T23:55:56Z, ~8.5 hours before the tier-B archive (08:21:19Z) and before the 0817Z amendment. The applied branch evaluation is verbatim-faithful and arithmetically confirmed from my independent tier-B recomputation:

- "tier_B native beats A0 AND B1 at 1024, tier-A confirms 128" — **FALSE on both conjuncts**: C loses A0p 3/3 (+3.1/+7.9/+33.8%) and does not beat B1 across the required cells (all-raw +5.7%).
- "tier_B native loses or ties B1" — **TRUE** under the complement reading the record states explicitly ("does not beat B1 across the required cells").

The conjunctive reading is correct: branch 2 is textually conjunctive, and the dossier's own decision language quantifies per cell across required cells (per-cell paired medians, ≤3% protected-cell regression), so "beats B1" means across the required cells and "loses or ties" is its negation. Under even the strictest alternative reading, branch 2 still fails and the outcome remains non-promotion — the applied branch is the conservative landing (N-SEL-2).

## R-S2 Sub-clause: CONFIRMED across-required-cells reading (no REQUIRED flag)

"Integrate B transparently if it beats A0" evaluates FALSE correctly. A 128-only reading would be incoherent: (1) the sub-clause is the parenthetical of a tier-B-scoped branch; (2) both block sizes are frozen REQUIRED cells and the dossier quantifies per cell; (3) that reading would mandate default-integrating a row that loses A0p 3/3 at the production block (+5.5/+9.8/+26.6% — verified: 3.5468/3.3627, 3.0173/2.7487, 0.6943/0.5485) and could never clear the dossier's own ≤3% protected-cell gate. B retained in-tree (vendored, parity-proven, drift-zero) without default integration is the right disposition.

## R-S3 R-TB2 disposition: CLOSED

The dispositions.R-TB2 wording is precisely the sentence my tier-B REQUIRED asked for — the N6 scope move recorded as AUTHORIZED with the full justification chain (1955Z reconciliation + inline disclosure + R-B5 + this record) while preserving the envelope statement as BINDING in the tier-B record.

## R-S4 Campaign disposition: PASS — honest consequence, not evasion

Selection-before-qualification: no candidate advanced, so the frozen N8-42/43 cells have nothing to qualify; starting a campaign would manufacture evidence the selection does not authorize. The deferred labels gate a native default this selection does not authorize — dispositioning them WITH this record is their correct terminal state.

## R-S5 Outcome integrity: PASS

Verified in-tree: the qualification registry ships empty with fail-closed-to-row-A semantics; `resolve_lw_backend` is records-blind for defaults with an expert-only explicit override; no default-enablement authorized; flip conditions carry measurable triggers (mask-into-classification removing the 0.197 ms charge; guard thinning 0.059→0.012 ms; producer redesign) with reopen-only-through-new-pre-registered-evidence. The gate-loosening distinction is sound: 0817Z loosened the measurement window pre-results (my R-B4 verification), touched no promotion gate, and no candidate failure existed when it landed.

## R-SEL-1 (required, carried, non-flipping): tier-A B1 composition defect behind the R13-D1 closure claim

The corrected tier-A record charges `B1 = BC_produce + B1_numba_adapter` justified as "(adapter included in kernel timing)". That is **true for the f32 view** (b_fn views the uint32 blocks internally) but **false for the masks**: the timed call receives pre-packed `sun_a`/`shade_a` (call signature verified), so `pack_masks` sits outside B1's timing — and the frozen harness comment says the adapters are "charged to B1/C1". The applied rule undercharges tier-A B1 by the pack cost (fair values 0.5035/0.4688/0.2024 vs recorded 0.4757/0.4396/0.175 — the skeleton's tier-A B1 row has the same produce+kernel-only defect), and the two tiers of this selection now use different B1 accounting (tier-B charges pack+views to B1).

**Outcome-invariant:** C < B1 at 128 under every candidate composition (0.4719 < 0.4757 < 0.5035); the branch tests are 1024-internal; the R-S2 sub-clause fails at 1024 regardless. No branch, conjunct, or verdict flips, and the error's direction is unfavorable to C (conservative on promotion).

Required follow-through: fix the tier-A B1 row + the false justification sentence (and `tools/optimization_v8/n8_31_transcribe.py`), adopt one canonical B1 rule across tiers (recommended: B1 = produce + pack_masks + B1_adapter — the view is internal to b_fn's timing; C1 = produce + views + pack_masks + C1_adapter; tier-B's views-in-B1 overcharges a negligible ~0.0007 ms), and amend this record's dispositions line to state the correction instead of unqualified R13-D1 closure.

## Recommended

- Skeleton `recorded_utc` "2026-09-22T24:05Z" is malformed (commit landed 23:55:56Z); fix at next touch, and note the tier-A B1 correction in the selection record when applied so the committed skeleton's stale numbers are never cited.

Scope guard: no timed work, no builds, no commits; the record under review unmodified; writes confined to `evidence/reviews/` and `/tmp/n8rev_n8_13/`.
