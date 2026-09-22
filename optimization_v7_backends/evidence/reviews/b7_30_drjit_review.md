# B7-30 review verdict — C_drjit (Dr.Jit 1.5.0 LLVM backend)

**Verdict: APPROVE-WITH-NOTES** — advance to B7-31 trials as exact-eligible C variant.

**Routing statement (recorded verbatim):** "Model routing note for the record: this session has no verified Anthropic Opus route; you are an independent GLM review by a fresh agent distinct from the author agent."

**Scope of approval:** the exactness gate only — 520/520 fixture replay, adversarial and negative domains, no-contraction / true-division claims, typed-graph fidelity against the frozen contract, adapter honesty. Performance claims remain outside this review (dev-tier, pre-protocol).

## What I reran myself (smallest disputed cases, independent harnesses)

1. **Fixture replay, rebuilt from the capture manifest + npz (no author script exists):**
   520 captured / 520 admitted / 0 rejected / 520 bitwise-matched (uint32) / 0 input-canary
   failures in 1.3 s — matches the claimed 520/520 at 1.17 s.
   Log: `logs/rerun_fixture_replay.json`.
2. **Own 24-case adversarial suite vs BOTH numba baselines (serial + parallel), bitwise:**
   B=0/1/4/17, P=1/2/153; NaN/Inf in visibility/lup/sky tables; -0.0 sine and vs;
   denormal visibility; f64/f32/python-float surfaces; stride-12 sky views; all-gate /
   all-nogate; vis all-zero/all-two; both loop modes; canaries. All 5 rejections
   (f64 visibility, mixed surface specs, python-float reflection_factor, P=610, f64 sun
   mask) fire pre-launch with inputs untouched. 24/24 ok. Log: `logs/rerun_adversarial.json`.
   Plus P=609/608 boundary and B=7/3 irregular tails: all bitwise.
3. **Reflection divide, proven by value, not just IR:** I found 2041 f32 values where
   true division by pi (0x40490FDB) differs bitwise from a reciprocal multiply. The
   shipped kernel returned the true-divide bits **2041/2041** and matched the baseline
   everywhere. The kernel also passes an IR check: exactly 1 `fdiv` whose divisor is a
   runtime parameter load (`%f16_0 = load float, ptr %f16_p2`), never a constant splat.
4. **Fresh IR for BOTH specializations:** f64 reproduces the author's audit counts
   exactly (1 fdiv, 0 fma/fmuladd, 0 fast-flagged float ops, 8 fptrunc, 17 fpext,
   27 masked.gather across the 2 kernels a call launches). The f32 spec — never audited
   by the author — is also clean: 1 fdiv, 0 fma, 0 fast flags, no promotions, as its
   all-f32 design implies. Logs: `logs/ir_child_f64.txt`, `logs/ir_child_f32.txt`.
5. **Division-folding hazard re-check:** confirmed real (literal divisor → `fmul` with
   host reciprocal, no `fdiv`, with FastMath OFF) — and value-visible (30/64 linspace
   values differ literal-vs-data divisor; 39656/262144 standard-normal values differ
   for pi). The shipped kernel avoids it structurally via data variables, verified.

## Typed-graph fidelity (inspection, node by node)

Kernel bodies of the frozen blob 27ba6ce4 are byte-identical in both checkouts. The
candidate matches: predicates; sky chains kept f32 even in the f64 spec; vegetation and
sun/shade chains promoted to f64 with RN32 only at the accumulator add (IR-confirmed
fpext/fadd/fptrunc); A6→A1 and A8→A7→A3→A2 (else: A7→A2) update order; four separately
grouped sun/shade expressions; reflection re-reading A0 after the completed sweep with
the exact pi bits; sweep-2 mask captured during sweep 1 (boolean-identical; inputs
canary-proven immutable); output fold grouping and raw A5..A9 columns. The
[B,P]→[P,B] transpose is a pure permutation into the arena (`idx + B*p` offsets) and
cannot reorder arithmetic — confirmed bitwise by every replay.

Adapter honesty holds: validation before any native work, no input mutation, no silent
fallback (`Unsupported` only, distinct from failure), B=0 short-circuit, copy/transpose
and per-call host-pool costs declared, `dr.set_thread_count` at init declared
(process-global).

## Findings (details in review.json)

- **F1 (medium):** the recorded "0/262144 bit differences" division probe is not
  reproducible — I measure ~15% differing values for pi (and 30/64 on a linspace for
  3.0). The hazard itself and the structural mitigation are confirmed; only the recorded
  number is wrong (conservative direction). Amend the note; no kernel change.
- **F2 (medium):** the candidate ships no replay/audit/timing scripts — evidence is not
  self-reproducing (this review substitutes independent reproduction, but the scripts
  should be landed before B7-31).
- **F3 (low, closed here):** f32-spec kernel IR was never audited by the author; my
  fresh dump shows the same clean conclusions — land it.
- **F4 (low):** audit says "one full symbolic-kernel launch"; the dump actually contains
  the two launches a call makes (mask-scatter side-effect kernel + main kernel). Wording
  fix; note it for launch-overhead accounting.
- **F5 (info, trial design):** two thread pools on the C side (drjit pool, process-global,
  includes calling thread; plus a per-call host ThreadPoolExecutor ≤8 for large-B
  transposes) vs numba's single pool — label as different budget shapes under the
  equal-CPU-budget rule; pin `dr.set_thread_count` to the numba budget for pairing.
- **F6 (info, trial design):** freeze `DRJIT_CACHE_DIR` regime for the cold-first-use
  guard (kernels persist on disk: 150.6 ms uncached vs 4.7 ms warm); move the stage-cost
  numbers (pack ~20 ms / symbolic ~49 ms / materialize ~0.3 ms at B=65536) from prose
  into trial evidence JSONs.
- **F7 (low):** record the LLVM version fingerprint (B7-03 asks for it); dev-tier B=96
  variance (1.05 vs 2.65 ms) is for the paired-median protocol to absorb.

## Recommended disposition

**Advance to B7-31 trials as exact-eligible C variant**, with F1/F2 evidence repairs
applied (no kernel re-review needed) and F5/F6 implemented in the trial freeze.
The dev-tier "wins at pipeline B (0.10-0.48x), loses 3-4.4x at large B" split is a
selection hypothesis for B7-31/32, not a proven performance result.
