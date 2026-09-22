# Exact typed computation and ownership contract

## Authoritative reference

Read the current `radiation/cylinder_longwave.py`, current native `.ispc`, `backends/native/lw_native.py`, B7 typed captures and the actual new signatures/IR. The earlier packet pseudocode is explanatory, not authoritative. Capture affected native specializations and provenance before porting. In particular, float32 surface scalars and Python/NumPy float64 surface scalars are DIFFERENT typed graphs.

## Longwave state

Each pixel has ten float32 accumulators a0..a9 initialized to the reference zero. There are two ordered patch sweeps. The first sweep feeds sky, vegetation and wall terms. Reflection depends on the completed first sky accumulator and that pixel's Lup. The second sweep accumulates reflected terms. Output is the same float32 [B,7] as the current primary reducer, including all five side components. The surrounding demand API remains responsible for its omitted cardinal diagnostics.

For f64 surface profiles, a representative update is:

`c64 = (((surface64 * f64(solid[p])) * f64(cosine[p])) * f64(mask))`

`a6 = RN32(f64(a6) + c64)`

Do NOT write `a6 = RN32(a6 + RN32(c64))`. The mask-to-number multiply stays a multiply, not a branch that skips 0*Inf. Solar_gate controls which expression is evaluated; do not evaluate inactive branches using a vector select merely for convenience. Signed zeros, NaN/Inf masks and original arithmetic exceptions in the admitted domain remain observables.

The building predicate uses the original float32 subtraction/product followed by its exact comparison. Raw decoded values need not be 0/1. Reflection is the original sequence of f32 addition, multiply, multiply and division by the exact stored float32 pi. No reciprocal rewrite. Retain left-fold output combinations and p=0..P-1 order in each sweep. No warp tree sum, dot product, reassociation, tensor-core approximation or scan over time.

## Direct AoSoA transform

For SIMD width W, define `Q[g,p,lane] = V[g*W+lane,p]` for valid pixels only. This is a bit-preserving permutation. Original producer indices and byte order must be identical. Tail lanes must not read outside source or write outside destination; zero padding is not allowed to become a real pixel. If W/ISA affects the existing mathematical fallback path, keep that part in the original layout until proved identical.

`P` can be any source-admitted count 1..609 in lower-level tests, while the production target retains 153. B=0, B=1, prime tails, B=W-1/W/W+1, negative/nonunit strides, aliasing and read-only outputs get explicit behavior. Do not silently make unsupported inputs contiguous and exclude the copy from timing; either admit/copy with counted ownership or reject before launch.

## Longwave-specific quotient states

If the only visibility observations are sky, vegetation, building and reflection predicates, exact state code q can represent those four booleans. Prove that every read in this selected region factors through q; keep original visibility artifacts and other consumers intact. Preparing q is a geometry operation, not a per-step substitute for changing ground-view radiance or sun/shade. Out-of-domain raw/NaN/payload/error cases retain the original route until separately proven.

When partial-evaluating categorical contributions, store them in the ORIGINAL intermediate type (often f64), and keep the original accumulator-add rounding. If two source expressions are mathematically equal but grouped differently, they require distinct table entries. `mask=false` cannot universally be turned into +0 without a signed-zero/nonfinite proof.

## Proof obligations for every accepted transformation

1. Define admitted input domain, complete dependency key and unsupported fallback.
2. Map new registers/state to old state and show equal initial bits.
3. Induct per pixel and per ordered step/patch; handle first-step ray corrections separately.
4. Show reflected/neighbor/chronological dependencies remain identical at barriers.
5. Prove no alias mutation, invalid tail, use-after-close or partial publication.
6. Compare warnings/exceptions required by the public/private boundary; add a guarded legacy path for observably different diagnostic profiles.
7. Audit generated instructions and exact dtype transitions. A `fastmath=False` spelling or broad grep alone is not a proof. Explicit existing SLEEF FMA must remain; new contraction in reducer math is forbidden.

## Tests

Reuse source-matched captured calls; generate independent adversarial inputs as additions, not replacement goldens. Compare all seven reducer outputs, affected intermediate radiation and every carried state on small 24/48-step real TIFFs. Verify source and installed wheel separately. Raw-codec bit payload tests differ from NaN-output-mask tests; do not conflate them.

Small numeric identity may be checked across f32/f64 surface profiles, scalar/0-d variants, one-element strided sky columns, normal/subnormal, zeros, near-one thresholds, finite cancellation and nonfinite cases. Candidate creation must not overwrite any existing reference file. The old CPU/GPU scientific budgets remain unchanged and separate from new exact branch-to-candidate checks.
