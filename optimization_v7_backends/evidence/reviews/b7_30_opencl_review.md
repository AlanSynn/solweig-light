# B7-30 independent review — B7-22 OpenCL/PoCL candidate

**Verdict: APPROVE-WITH-NOTES.** All six author claims held under independent rerun and source audit.
Full detail in `b7_30_opencl_review.json`.

## What I reran (candidate's venv, candidate's env, candidate untouched)

| rerun | exit | result |
|---|---|---|
| `replay_fixtures.py` | 0 | 520/520 admitted, 520/520 bitwise (uint32, NaN payload+sign), 0 rejected, canary OK — log **byte-identical** to the author's |
| `adversarial_tests.py` | 0 | 512/512 bitwise vs numba A (504 domain combos x both schedules + padded tails), 7/7 pre-launch rejections — log **byte-identical** to the author's |

Provenance verified before rerunning: worktree `c66ff3b6`, kernel-source blob `27ba6ce4…` matches the frozen contract, captures byte-identical to the main checkout, kernel/adapter sha256 match `capability.json`, `.venv-v7` matches the frozen environment. Original candidate logs restored after comparison.

## Source audit highlights

- `lw_primary.cl` matches `b7_02_typed_ir.txt` node-for-node: +0 init; ordered sweeps; bool-as-multiplier NaN semantics; veg/sun/shade chains in the chain scalar type with float32 rounding only at the accum add (both f64 and f32 numba add nodes represented); gate true-branch updates A8,A7,A3,A2 in source order, false-branch A7,A2; reflection only after sweep 1; **pi enters as a host float32 kernel argument asserted to bits 0x40490FDB** (not a literal); sweep-2 cast per multiply; ordered left folds; outputs 2..6 = A5..A9.
- Adapter: validates everything before launch; raise-only (`UnsupportedInput` / `DeviceUnavailable` / raw build errors) — **no fallback path exists in the file**; explicit PoCL-CPU-only selection, Apple GPU/Rusticl structurally excluded; sync + copy-back inside the timed boundary; per-call buffers, no cross-call device caching.
- FP methodology is genuinely discriminative: 480/4096 f32 contraction cases would differ under FMA and the device matched separate-op semantics on all; division checked bitwise against correctly-rounded numpy over 19,889 adversarial finite pairs; denormals and NaN payloads verified behaviorally on the actual built kernels.
- Dev-tier timing claim is honest: dev-tier/noisy-host labeled, alternating paired reps, full adapter boundary; 0.91x / 0.94x (C ~6–10% slower) — correctly reported as below the 1.10x adapter gate and **not recommended for integration**.

## Findings (2 minor, 4 notes — none blocking)

- **F1 (minor):** the `P_over_609` rejection tripped the sun shape check (`shape (8,4) != (8,610)`), not the P≤609 guard — the guard is correct by inspection but untested. Fix the test's argument shapes if this backend is ever revived.
- **F2 (note):** stale header comment in `lw_primary.cl` lines 13–16 (claims lowercase pragma + build option both disable contraction; contradicted by lines 34–38 and the proof record). Operative code is correct.
- **F3 (note):** proof record's sizing-probe numbers (26/356/364 ms) aren't in the retained `dev_timing.json` (22.3/24.6/26.3 ms) — superseded-run prose, same conclusion.
- **F4 (note):** replay canary bookkeeping is per-case-last-call; a mutation wouldn't fail the exit code (none occurred; adapter structurally can't mutate).
- **F5 (note):** division check is finite-only; Inf/NaN divide propagation covered transitively via lup_nonfinite replay.
- **F6 (note):** single-process noisy-host observations with 2 reps — correctly labeled; clean trials remain the performance owner's scope.

## Recommended disposition

Record as `comparison_complete` / `available_exact_not_selected_on_performance` for the PoCL track; do not integrate on performance grounds. No repair required for the evidence as recorded.
