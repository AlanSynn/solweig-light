# B7-21 Proof Record — C_drjit: exact longwave primary reducer on `drjit.llvm`

Status: **exactness gate PASSED (520/520 fixtures bitwise); dev-tier performance recorded — wins at real-pipeline B, loses 3-4.4x at large B.**

## Scope

Candidate C_drjit as prescribed: longwave primary reducer as explicit CPU LLVM JIT via
Dr.Jit 1.5.0 `drjit.llvm` (non-AD), FastMath disabled, vectors over pixels (width B),
patch loop sequential, accumulators A0..A9 width-B, `solar_gate` branch per-patch.
Worktree `/Users/alansynn/Workspace/solweig-v7-drjit` (detached c66ff3b6); `src/` and
`tests/` untouched; deliverables under `experiments/optimization_v7/drjit/`.

## Structure and typed graph

- `llvm_longwave.longwave_primary_drjit(...)` — signature identical to the baseline
  kernel (17 args; `directions`/`gate` accepted and ignored exactly as in the reducer body).
- Frozen typed graph into the kernel: visibility `float32 [B,P]` (sh/vs/vb), `sun`/`shade`
  `bool [B,P]`, coefficients `float32 [P]`, `solar_gate` `bool [P]`, `lup` `float32 [B]`,
  surface scalars + `reflection_factor` as width-1 runtime *data* variables.
- Scalar provenance: real-pipeline specialization (f64 surfaces; chains promote to
  float64, `fptrunc` to float32 only at the accumulator add) and synthetic float32
  specialization. Both fixture domains replay bitwise.
- Reflection: `r0 = f32(A0 + lup); r1 = r0 * rf; r2 = r1 * 0.5f; refl = r2 / pi`,
  pi bits 0x40490FDB, division a true IEEE `fdiv` (see division hazard below).
- Two loop modes: `"symbolic"` (default; Dr.Jit symbolic while-loops, one JIT compile
  per scalar specialization, uniform runtime branch on `solar_gate[p]` — untaken side
  not evaluated, matching Numba branch semantics) and `"evaluated"` (Python patch loop,
  trace-time branch; exact, kept as the prescribed-structure reference mode).

## FastMath / contraction verification

- Dr.Jit default `JitFlag.FastMath` is **ON**; disabled in `configure_runtime()` before
  any trace; effective flag recorded `False`.
- IR audit of the real symbolic kernel (`evidence/llvm_ir_symbolic_kernel_raw.txt`):
  **0** float ops carry `fast` flags, **0** `llvm.fma`/`fmuladd`, **1** `fdiv`
  (the reflection divide), 27 `llvm.masked.gather`, 8 `fptrunc` (f64→f32 rounds at
  accum adds), 17 `fpext` (chain promotions). Contraction is off; accumulation order
  and grouping are the baseline's.
- Division hazard (real and value-detectable): Dr.Jit folds division by a
  *literal* divisor into a host-computed **reciprocal multiply even with FastMath off**
  (`evidence/llvm_ir_division.txt`: `x / Float(3.0)` compiles to `fmul`, no `fdiv`).
  Literal-vs-data-divisor paths diverge bitwise on a substantial fraction of values:
  ~39656/262144 (~15.1%) for the pi divisor and 30/64 at d=3.0 — rates measured by the
  B7-30 reviewer and independently re-verified post-trials by the author with a
  corrected probe (pi 15.02%, d=3.0 33.23%; full sweep in the evidence file).
  Correction history: an earlier revision recorded "0/262144 differences" from a
  tautological probe whose scalar-constructor "divide" side folded to the same
  reciprocal multiply as its comparison side.
  Mitigation: every varying scalar (coefficients, surfaces, rf, pi) enters as a runtime
  *data* variable from a NumPy buffer — never folded — so the kernel lowers a true
  `fdiv` (verified in IR) and the IR depends only on `(P, spec, solar_gate pattern)`,
  giving one JIT compile per specialization reused across all shapes. This mitigation
  is load-bearing: without it the reflection term would diverge from the Numba
  baseline on ~15% of pixel values.

## Exactness gate

- **Fixture replay**: all 520 captured calls (`b7_02_fixtures.npz`) —
  **520 admitted / 0 rejected / 520 bitwise-matched (uint32 view)**, wall 1.17 s
  (`evidence/fixture_replay.json`). Covers both labels (serial/parallel captures),
  both scalar specializations (434 f64 / 84 f32 / 2 python-float surface calls),
  pipeline shapes 128x153 and 96x153, and all synthetic edge domains.
- **Adversarial** (`evidence/adversarial_replay.json`, 21/21): B=0/1/17, P=1/2/153;
  NaN/±Inf payloads in visibility/lup/sky tables; -0.0 inputs; f64/f32/python-float
  surfaces; stride-12 non-contiguous sky views (accepted, tiny copy);
  evaluated-mode equivalence; input canaries (sha256 before/after — never mutated);
  explicit pre-launch rejections: f64 visibility, mixed surface specs, python-float
  `reflection_factor`, P=610, f64 sun mask. Denormal-visibility probe (1e-40/1e-45
  sh/vs values, near-unity vb): bitwise-true.

## Dev-tier timing (NOT the B7-03 protocol; full adapter vs unchanged baseline A)

`evidence/dev_tier_timing.json`; P=153, numba 10 threads, drjit 10 threads,
2 alternating paired reps (pair1 A→C, pair2 C→A), rep = mean of 3 (B=128/96: 5) calls:

| B | A numba mean | C drjit mean | C/A |
|---|---|---|---|
| 128 (pipeline) | 4.04 ms | 0.41 ms | **0.10x** |
| 96 (pipeline) | 3.82 ms | 1.85 ms | **0.48x** |
| 16 384 | 7.00 ms | 30.58 ms | 4.37x |
| 65 536 | 21.67 ms | 66.54 ms | 3.07x |

- Cold compile (empty `DRJIT_CACHE_DIR`): 150.6 ms per (spec, kernel); with Dr.Jit's
  on-disk kernel cache warm, first call 4.7 ms; steady-state B=128 adapter 0.4-1.6 ms.
- Interpretation: Numba `prange` fixed cost (~4 ms) dominates real-pipeline tiles,
  where C_drjit's single fused kernel wins by 2-10x. At large B the picture inverts:
  Dr.Jit emits `llvm.masked.gather` per packet (no vector-load API exists in 1.5.0 —
  probed: no raw-load primitive), so the reducer is gather-bound; the numba baseline
  emits plain vectorizable loads. Stage split at B=65536: pack (validate + 5 tiled
  parallel transposes) ≈ 20 ms, symbolic run ≈ 49 ms, materialize ≈ 0.3 ms.

## Adapter engineering recorded

- Tiled (4096-row) thread-pool transpose for the [B,P]→[P,B] layout: ~13.7 ms for all
  five rasters at B=65536 vs ~80-100 ms naive; small arrays (≤1 MB, incl. every
  real-pipeline tile) transpose inline. Pure permutation, bitwise-verified.
- Sweep-2 occlusion predicate captured during sweep 1 into a scratch Bool buffer
  (in-kernel `dr.scatter`/`dr.gather`, conflict-free) — the same pattern the fused
  baseline uses (`masks` buffer); caller-visible kernel inputs unchanged; boolean-identical
  (`(sh==0)|(vs==0)|(vb==0)` computed from the already-gathered sweep-1 values); all
  520 fixtures + adversarial suite re-verified bitwise after the change.
- Alternative measured (not shipped): no-transpose strided gathers straight from [B,P]
  — rejected: gather line utilization drops 16x (4 useful bytes per 64-byte line),
  kernel becomes DRAM-bound; drjit-internal scatter transpose ≈ 17.5 ms/array — no
  better than the tiled host transpose.

## Known limitations / honesty notes

- `solar_gate` must be a NumPy bool array (any contiguity); non-contiguous [P] views
  are copied once. `directions`/`gate` unused (as in the reducer body).
- Zero-copy: none — every input crosses into Dr.Jit arenas by copy (`zero_copy_verified=false`).
- The module keeps `FastMath` off process-wide after the first call (conservative for
  any other in-process Dr.Jit user; recorded in `configure_runtime`).
- Thread state: `dr.set_thread_count` is process-global; numba's pool is pinned
  separately in benchmarks. No arrays/graphs retained across calls; the scratch mask
  buffer and packed arrays are per-call.

## Verdict (for portfolio selection)

C_drjit is **exact on the entire fixture corpus** and was exact-eligible at review
(APPROVE-WITH-NOTES, B7-30). The dev-tier "2-10x faster at B≤128" reading below did
NOT survive the B7-31 appendix trials: at matched thread budgets (drjit pool pinned
1T/4T, 3 paired warm reps, all digests bitwise-equal to A and C_native) C_drjit
measured 2.6x slower than A at the pipeline block size, 3.8x slower on the warm
216-call sequence, and 1.85x slower at B=65536 — per-call JIT dispatch + pack
dominate at pipeline sizes once budgets are honestly matched. The track closes as
**comparison_complete_no_winner**; the dev-tier table below is retained as the
record of what was measured at default thread settings, not as a performance claim.
