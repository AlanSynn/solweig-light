# D05: finish GVF preparation and typed block postprocessing

## What v5 already did

G02 caches converted source snapshots and handles first/later water state; G03 uses row-block receiver scratch instead of sixteen full raster planes. Retain those benefits. `_gvf_fused` still evaluates several source expressions every direction BEFORE snapshot reuse, and `_postprocess_block` still uses Python/NumPy helpers. [S13]

## G-A: actual invariant expression preparation

For an admitted nonaliased core call, identify inputs read by each expression, not only the output array object:

- direction-independent aspect radians, wall mask, source buildings/shadow/albedo;
- first/second rounded search distances and immutable ray schedules;
- albshadow, receiver albedo terms;
- Lup from current Tg/shadow/Ta/emissivity;
- Lwall from Tgwall/Ta/ewall;
- postprocessing's Lup receiver term AFTER water mutation.

Build pre-water and post-water expressions only where needed. For no water mutation and no alias, the same Lup expression can serve both gather and postprocess across all 18 directions. With water, keep first pre-state and subsequent post-state, plus exact mutation of Tg at the baseline point. Aliases through any expression input can defeat invariance: Tgwall, emissivity, scalar views, scale, wall arrays, landcover or albedo must be analyzed. Do not assume existing v5 guards cover a stronger hoist. Keep the full old route for unproved aliases.

A function of identical owned inputs evaluated once returns the same result only under the fixed math backend/layout/profile and supported warning behavior. Keep original expression grouping; do not expand fourth powers or factor out base temperature. Public input mutation semantics stay intact. Never create a persistent cache keyed by Python array id for mutable caller arrays.

Historical _lup_expression calls=504 = 14 daytime*18 directions*2. Reducing these calls to one or two per step removes real redundant evaluations; its measured census cost was only about .16 s, so it is a supporting change, not a standalone 36x GVF claim.

## G-B: compile postprocess, then optionally fuse its storage

Port `_postprocess_block` to an actual nopython implementation over pixels. Preserve the exact mixed-type nodes. Extract a typed node inventory from the untouched function first. Comparisons producing wall influence precede `keep` zeroing. First/second denominators differ in the unshadowed branch. The baseline row/slice source-history behavior remains in gather. No reassociation, FMA or changing original np.minimum/NaN semantics.

Initially return the same five block fields and retain the sixteen input receiver planes. This isolates arithmetic from the later storage fusion. Compare every intermediate/return bit on actual captured inputs. Then evaluate moving receiver postprocess directly into the gather kernel, maintaining all 16 accumulators privately and writing only demanded fields. Keep an instrumented full diagnostic function for small comparison, not a permanently enabled 16-field output history.

Historical postprocess: 2016 calls and ~.775 s in a 9.859 s warm diagnostic. This is a lead, not current DRAM traffic or target speed. Profile Numba native work without misattributing all cost to wrappers. Test block_rows 16/32/64 only on selected tuning data and under workspace accounting; do not start a huge grid.

## G-C: prefix/repeated-add replay, only if residual justifies it

For canonical binary buildings, f_k=min(f_{k-1},b_k) becomes absorbing at first blocker k_b. Finite bounded source contributions past k_b are zero; wall state may persist and MUST still be reconstructed. Use exact repeated-add tables A_c(n+1)=RN(A_c(n)+c), not n*c. Keep the actual source history outside slices and initial/first-prefix snapshots. Subnormal/signed-zero/overflow and seterr domains require guard or fallback. Static blockers can be prepared once; dynamic sunwall onset still depends on time.

Memory for k_b is N*18*index_width, about 18 MiB for uint8 at 1024 only if range/sentinel fits; otherwise uint16/32. No N*directions*distance address cube. Include build, lookup, static-field cache and reads in benefit. Open terrain with long prefixes can regress, so retain original compiled gather. Historical abstract tests are not actual-kernel proof.

## G-D: static unshadowed albedo

The total/cardinal unshadowed fields may be prepared using original direction/step order if their full input graph is immutable. Five float32 maps cost 20N bytes. Break-even: Td*C_recompute > C_build + Td*C_read + admission_penalty. A memory cache that lowers active workers can erase the local gain. Do not statically cache changing ground-view radiance.

## Minimal tests

Use actual original functions, including water first/later, alias views (both arrays and scalar views), nonfinite sources, out-of-domain persistent sampling, short distances, material classes and ndarray dtypes. Compare mutated Tg as well as all sixteen receiver values and final cardinal totals. Follow with small 24/48-step TIFF state comparison. Each hoist/fusion/prefix variant is separate, reviewable and measured; do not combine all into a single difficult patch.
