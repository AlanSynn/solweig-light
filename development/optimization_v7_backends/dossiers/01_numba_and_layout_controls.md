# D01: A/B controls and shared layout

## Goal

Separate genuine backend benefit from memory-layout, batching and algorithm changes. A is the current accepted reached reducer. B implements C's intended layout/schedule with Numba. C is the alternative runtime. All three use the same mathematical boundary, current scalar profile, exact inputs and required seven outputs.

## Capture before implementation

The fixture owner wraps the real untouched reducer during a small TIFF run and calls through to it. Copy input/output values solely for a separate diagnostic run; instrumentation is not performance timing. Capture both parallel and serial specializations reached by public configuration. Record `surface_sun`, `surface_sh`, `reflection_factor`, all array dtypes/strides and Numba signature/typed IR. Never infer double-versus-float from the output or turn a Python scalar into a zero-dimensional array without tracing the actual promotion.

Arrays with every encountered normal profile plus targeted unsupported profiles form the corpus. Keep current original-reference fixtures intact. Captures need fixture/source/profile/runtime fingerprints and a clear `reference_actual_kernel` label. Synthetically generated adversarial cases call the real baseline; a handwritten Python recurrence may be a supplemental check but never its replacement.

## Layout alternatives

A commonly decodes `[B,P]` row-major arrays, favorable to one pixel's sequential patch reads. A packet-per-block loop wants `p` outermost and contiguous lane reads. Two bounded choices are:

- explicit block transpose `[P,B]`, counted in adapter time;
- AoSoA `[ceil(B/V),P,V]`, with correct masked tail.

Do not transpose full scene visibility to avoid measuring repeated packing. The first B uses the same per-call conversion as C. A later reuse of invariant layout/decoded data is a separate optimization with ownership keys and build/validation costs included. All inputs remain readonly, and scratch is leased per active worker/native task.

Each pixel's accumulator performs p=0..P-1 in both sweeps. Pixel iteration order can change; patch order cannot. Parallelize outer independent blocks and keep pixel-lane loop SIMD-friendly. Do not nest independent native thread pools or scatter additions from patch workers. A Numba `prange` over pixels alone does not guarantee useful SIMD; inspect generated assembly, masked loads and register spills.

## Minimal selection grid

Start with current default and one measured practical block (e.g. current 128 vs 1024 pixels); then one larger bounded alternative if call overhead is material. Avoid the Cartesian product of all shapes, widths, threads and languages. SIMD tail tests are exhaustive small correctness tests, not full performance cases. Choose one common layout for a head-to-head C comparison. If two layouts differ materially by hardware, record two separately versioned variants, not one unexplained aggregate.

## Stop rule

If B matches C within noise or is faster end-to-end, prefer B. If packing costs exceed arithmetic savings at the adapter boundary, do not proceed to a full pipeline port of that layout. If A is already close to the achievable memory/instruction limit and the stage is a small fraction, close the island with evidence and select one measured residual rather than broad framework churn.

Deliverables: capture manifest, typed node ledger, A/B implementation diff, exact output comparisons, effective threading, IR/assembly excerpt, copy/workspace inventory and synchronized A/B timings. Coordinator receives a short decision; full evidence remains in files.
