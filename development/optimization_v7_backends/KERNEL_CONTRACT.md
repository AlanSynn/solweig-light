# First island: exact longwave primary reducer

## Evidence boundary

Observed source: `src/solweig_light/radiation/cylinder_longwave.py`, Git blob `27ba6ce48454399c7b97285c8408511d050a32da` at both the historical survey commit and the newly checked branch tip. The authoritative numerical implementation is the actual accepted native specialization, not the pseudocode here. B7-02 captures its arguments and type graph. No SOLWEIG kernel has been run by this packet author.

## Inputs and layout

For a block with B pixels and P patches, the current kernel accepts:

| Name | Logical role | Required treatment |
|---|---|---|
| sh, vs, vb | B x P float32 visibility values | Initially use accepted decoder output; preserve 0, 1, 2, raw bit cases and guarded fallback. Never bool-cast the channels. |
| sun, shade | B x P Boolean classifications | Already computed by accepted profile; no new trig/classifier in the first port. Both may be false at a boundary. |
| solid, sine, cosine | P coefficients | Preserve exact captured dtype/bits and original multiplication sequence. |
| solar_gate | P branch predicates | Preserve whether branch is evaluated; do not evaluate masked inactive branch just because a tensor library finds it convenient. |
| sky_down, sky_side | P radiance coefficients | Preserve actual specialization, not presumed dtype. |
| surface_sun, surface_sh | scalar radiance coefficients | Python/NumPy scalar provenance matters. Explicitly capture dtype and typed-IR operations, including any float64 intermediates. |
| lup | B receiver values | Used after completed first sky sweep. Same snapshot for both alternatives. |
| reflection_factor | scalar | Preserve cast at each original node. |
| directions, gate | original signature fields | May be unused by primary reducer; public wrappers still retain their validation/return behavior. Do not broaden low-level acceptance accidentally. |

Current return: owned `float32[B,7]`, containing totals plus five side components. All seven are required in the first experiment even when a downstream caller consumes fewer. The full diagnostic API is separate and unchanged.

A/B/C may use a transposed or AoSoA internal view, but conversion cost, memory and tail handling are part of the adapter contract. Accepted host input must never be mutated. Reject or reference-fallback for unsupported dtype/shape/alias/stride before native execution. Guard evaluation and fallback costs belong inside adapter timing.

## Exact arithmetic graph

Let RN32 be the source's explicit float32 rounding, not a license to make every intermediate float32. Let typed_mul/add/div execute with the captured native specialization. Each pixel owns ten float32 accumulators initialized to original positive zero.

At patch p:

```
sky = (sh == 1) and (vs == 1)
veg = (vs == 0) or (vb == 0)
building = (RN32(RN32(1) - sh) * vb) == 1
A0 = RN32(A0 + RN32(sky * sky_down[p]))
A5 = RN32(A5 + RN32(sky * sky_side[p]))
vside = ((surface_sh * solid[p]) * cosine[p]) * veg
vdown = ((surface_sh * solid[p]) * sine[p]) * veg
A6 = RN32(A6 + vside)
A1 = RN32(A1 + vdown)
```

When solar_gate[p] is true, preserve the four separately grouped sun/shade expressions and the source update order A8, A7, A3, A2. When false, preserve the two shade expressions and update A7, A2. Do not combine sun and shade beforehand. Source code and the typed-node ledger specify all intermediate promotions.

After every patch in sweep 1, compute:

```
r0 = RN32(A0 + lup[x])
r1 = RN32(r0 * reflection_factor)
r2 = RN32(r1 * RN32(0.5))
reflected = RN32(r2 / RN32(pi))
```

The original compiler may distinguish the scalar's multiplication dtype before RN32. The ledger must state it. Encode pi using the exact captured float32 bit pattern, not a backend-specific symbolic pi or reciprocal.

Sweep 2 traverses p=0..P-1 again. `mask = sh==0 or vs==0 or vb==0`. Preserve the cast after every multiply in `RN32(RN32(RN32(reflected*solid[p])*cosine[p])*mask)` and the analogous sine expression. Accumulate side into A9 and down into A4 with explicit RN32.

Output 0 is the ordered left fold of A0..A4; output 1 is the ordered left fold of A5..A9. Outputs 2..6 copy A5..A9. No tree reduction, parallel patch sum, dot product, matrix multiply or associative scan is an acceptable substitute.

## Correctness argument to complete

For each pixel, map candidate registers/lanes to A0..A9. Show identical initial bits. For each patch, show the same predicates, scalar provenance, rounded nodes, branches and accumulator updates. Induct over sweep 1; identical A0 and lup imply identical reflected. Induct over sweep 2 and then output combination. Independent pixels can be scheduled differently because they do not read each other's accumulators.

Output equivalence is not enough if candidate mutates inputs, reads an invalid tail, changes a warning/error that the private guarded domain admits, or lets an async kernel outlive a mapped input. The implementation must cover these observables too.

## Hard edge cases

- float64 surface coefficients in an otherwise float32 block; float32 versus Python scalar changes.
- +0/-0: no algebra such as skipping every zero contribution without a signed-zero proof.
- NaN/+Inf/-Inf and 0*Inf: retain supported behavior or reject the domain before launch. Output NaN masks are required; raw-codec payload preservation is tested separately.
- Denormals/FTZ/DAZ, cancellation, near overflow, repeated small additions, equal masks.
- P=1, P=153, irregular allowed counts and long P (up to the source-admitted 609); do not reduce target P for speed.
- B=0 where original supports it, B=1, prime tails, SIMD-width +/-1 and block-size +/-1.
- Big/little endian raw payload tests stay in the decoder. Native pointer adapters require explicit element layout and host endian support.
- No newly enabled implicit FMA. Existing explicit SLEEF FMA stays in the unchanged preparation path. Compiler flags and generated code must confirm behavior; flags alone do not prove equivalence.

## Private interface design

Before any shared dispatcher exists, experiments may expose concrete functions in isolated modules. No stubs are installed into public runtime. If one C wins, a small private adapter can accept a prepared immutable block plus a checked capability token and return seven host columns only after completion.

A capability token records backend id, device/ISA, scalar specialization, source/compiler/math fingerprints and admitted layout. It is not a global claim that the library supports every input. Backend selection is resolved once per worker; input guards are still evaluated at correct dependency boundaries. Never change global demand state to run concurrent tile calls in Python threads.

`unsupported` is an intentional pre-launch decision with the unchanged reference fallback. Build failure, device crash, OOM or an admitted numeric mismatch is an error, not an undisclosed fallback. Fallback calls count toward total time and are reported so a nominal backend win cannot consist entirely of Numba work.
