# B7-30 review service prompt template (coordinator-held)

Reviewer model routing: this session has no verified Anthropic Opus route; all
reviews are independent GLM reviews by a fresh agent distinct from the author
agent. Routing is recorded in each review record. If an authenticated Opus
route becomes available, demanding proofs (float/ABI) may be re-dispatched.

## Per-variant review packet (fill {TRACK}, {WORKTREE_DIR})

You are an independent reviewer for SOLWEIG-light v7 task B7-30. You are not
the author. Review ONE immutable candidate: the contents of
{WORKTREE_DIR}/experiments/optimization_v7/{TRACK}/ at its current state
(treat as immutable; if you request repairs, the author applies them and a
fresh review of the affected scope follows).

Read: optimization_v7_backends/VALIDATION_POLICY.md, KERNEL_CONTRACT.md,
benchmarks/protocols/optimization_v7/b7_03_protocol.json, evidence/captures/
b7_02_contract.json, and the candidate's own proof_record.md/capability.json.

Verify by INSPECTION AND RERUN of the smallest disputed cases (not the whole
suite):
1. Exactness claims: rerun the candidate's replay/bitwise script yourself in
   the worktree venv; confirm admitted/rejected counts and that output bits
   match fixtures. Confirm negative tests actually run (guards, canaries,
   tails, B=0/1, NaN/Inf/-0.0, both scalar specializations).
2. No-contraction proof: inspect the candidate's IR/assembly evidence; judge
   whether it actually demonstrates absence of FMA/reassociation/reciprocal
   substitution for the ADMITTED domain. Flags alone are not proof.
3. Typed-graph fidelity: compare the candidate kernel against the frozen
   contract node-by-node (two ordered sweeps, reflection dependency,
   solar_gate branches, accumulator update order, RN32 cast sites, float64
   surface-chain promotion, pi bits 0x40490FDB, output fold order).
4. Adapter honesty: validation before launch, no input mutation, no silent
   fallback, conversion/packing costs inside the declared boundary, distinct
   unsupported-vs-failed outcomes.
5. Evidence provenance: commands reproducible, environments pinned, dev-tier
   timings labeled dev-tier, no invented numbers.

Deliver a review record JSON + short markdown verdict into
optimization_v7_backends/evidence/reviews/ (coordinator will land them):
verdict in {APPROVE, APPROVE-WITH-NOTES, REJECT-REPAIR, REJECT-BACKEND},
scope of approval, rerun logs (paths), findings list, and routing statement
('independent GLM review, no verified Opus route in session').
