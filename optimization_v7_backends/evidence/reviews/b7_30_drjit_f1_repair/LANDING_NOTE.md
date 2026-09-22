# F1 repair landing (B7-30 drjit review, finding F1)

Landed from worktree `/Users/alansynn/Workspace/solweig-v7-drjit`
(detached HEAD c66ff3b6, untracked deliverables) on 2026-09-22.

Scope per reviewer: evidence prose only. `llvm_longwave.py` is UNCHANGED —
sha256 `592d12a2f265fa8beb67c996f619ab3defefe22dd748340cb2ad7d9fb5b21fdd`
matches the adapter identity recorded in every b7_31_appendix trial record,
and the worktree `src/`+`tests/` are bit-clean at c66ff3b6.

What changed:
- `fastmath_contraction_audit.json` (new): correction_history documents that
  the earlier "0/262144 bit differences" division probe was tautological
  (scalar-constructor "divide" side folded to the same reciprocal multiply as
  its comparison side). Reviewer-measured rates recorded: ~39656/262144
  (~15.1%) pi divisor, 30/64 at d=3.0; author's corrected probe re-verified
  post-trials: 39373/262144 = 15.02% (pi), 87113/262144 = 33.23% (d=3.0).
- `llvm_ir_division.txt` (new): demonstration IR + full divisor sweep.
- `proof_record.md` (updated): division-hazard section rewritten with the
  corrected rates, the data-variable-divisor mitigation marked load-bearing,
  and the verdict updated to reflect the B7-31 appendix outcome
  (comparison_complete_no_winner).

Affected claim scope (per reviewer finding F1): the division-hazard note only.
The qualitative hazard (literal divisors fold to host reciprocal multiply even
with FastMath off) was CONFIRMED and is unchanged in direction — the erroneous
"0 differences" claim understated the hazard, i.e. the error was in the
conservative direction. All exactness conclusions (520/520 bitwise, IR audit:
0 fast flags, 0 fma, 1 true fdiv) stand unaffected.
