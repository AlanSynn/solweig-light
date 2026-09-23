# Implementation blueprint: exact computation, not a new physical model

## 0. Read this as a recipe with proof obligations

This document resolves engineering choices so the implementation team need not restart a broad research/design exercise. It supplements the full 56-entry catalog and `MATH_AND_PROOFS.md`; it does not override an actual counterexample, the running source's typed semantics or the frozen comparison contract. Every new fast path is a **hypothesis until its code and guards are independently reviewed and differentially checked**.

Use the actual pinned/current source definitions as the executable specification. Function names below refer to the historical inspected implementation and should be reconciled narrowly if current HEAD moved. Do not regenerate golden outputs from new helpers. No full-scale experiments are implied by a recipe; L0-L2 remain the implementation validation ceiling.

For each family write a short certificate: inputs read, outputs/side effects observed, permitted dtype/domain, ownership, typed operations/casts, accumulation order, guard cost, fallback, counterexamples, source hash, actual tests and limitations. A complete low-level API can retain its original full-return/trace implementation while a private pipeline route is optimized.

## 1. Common internal architecture

### 1.1 Three data lifetimes and one workspace

**Scene-owned immutable data:** validated DSM/DEM/canopy/trunk, original logical shape and affine metadata, buildings mask, walls/aspect, materials, exact patch geometry, encoded visibility and its owner locks. External arrays merely marked read-only are not an ownership proof. Take a deliberate snapshot at the public-to-private boundary or retain the old path for externally mutable low-level calls.

**Step-owned immutable data:** forcing scalars, original ray schedules/decrements, sky coefficients, shadow fields, source radiance snapshots and original first/later water variants. Do not cache these under a geometry-only key.

**Carried state:** original Tgmap1*, TgOut1, CI, firstdaytime, timeadd, timestepdec, Twater and every field in the actual state type. They advance in the same chronological order. Internal blocks cannot own independent timelines because neighbor source fields may be needed across blocks at the next stage.

**Scratch:** admitted block-local or stage-local buffers. Buffers may be reused only after every downstream consumer/async writer has released them. Stage barriers separate producer writes from neighboring reads. A function with an `out` parameter must declare whether it aliases any input, whether it can be partially written on error and who resets it.

### 1.2 Optional private contracts (do not add these to the legacy public API)

Use simple arrays/scalars in compiled signatures, Python records outside. Suggested conceptual interfaces:

```python
# Conceptual signatures only. Final types/return order follow inspected source.
prepare_sky_plan(scene, patch_geometry, numerical_profile) -> immutable_plan
trace_sky_into(scene_arrays, plan_arrays, output_planes, admitted_flags) -> None
prepare_gvf_step(scene, dynamic_inputs) -> first_snapshot, later_snapshot
reduce_patch_block_into(encoded_views, step_coefficients, start, stop, out_fields) -> None
run_tile_into(scene_identity, timeline, runtime_options, output_owner) -> completion
```

The integrator alone changes shared dispatch. Family workers implement their private helpers and supply an adapter recipe: import target, original call, new call, guard/fallback, dependencies and comparison points. Do not use a shared `utils.py` as an unowned dumping ground.

### 1.3 Guard once at the right boundary

Cheap validated facts can be recorded on an owned scene: dtype/layout, finite flags, exact mask codebook, bush branch applicability, geometry/profile identity and exceptional layout. Mutable public calls need their original validation every call. Never re-scan the full raster once per pixel/block for a property already established under ownership. Conversely, do not reuse a finite/shape flag after mutation without an ownership/version guarantee.

The fallback receives original arguments and retains supported errors. It is not a slower approximation. Keep a debug/trace entry that can compare original intermediates on small data, and disable high-volume traces in timing trials.

## 2. Ray track: R01/R02 first, R04 only when useful

### 2.1 R01a: absorption before state projection

Target: `geometry/sky_compiled.py::_trace_pixel` on the existing no-positive-bush pixel-major path. NOT `wall_shadows.py` and NOT the step-major global-bush algorithm.

Let receiver elevation be a; after the actual first-step correction, define B=[f>a], V=vegetation state in {0,1}, E=[vb>0]. On the validated finite typed domain:

    B' = B OR [building_sample > a]
    V' = (V OR ([canopy_sample > a] AND NOT [trunk_sample > a])) AND NOT B'
    E' = E OR V'

The first step is special and must execute exactly as source, including its reset of vb. A building hit on the first step alone is not an authorization to break before the next original step has enforced V=0.

Minimal change first:

```text
execute original per-step arithmetic and first-step block
if this is a non-first step AND original B==1:
    stop evaluating the suffix
execute original finish expressions
```

Reason: f cannot decrease, so all subsequent B remain 1; V stays 0; adding V leaves vb and its final positive test unchanged. The three observable masks remain the same. Preserve possible final combined value 2 from first-step edge cases; no output Boolean cast.

Admission: original float32 field path, no positive global bush branch, finite arrays/decrements and a proved overflow/nonfinite policy. A conservative initial implementation can require all relevant operations finite and leave overflow-producing cases to fallback. Negative receiver heights and zero padding remain original. Do not change sample offsets, rounding, termination schedule, azimuth epsilon or source precision.

Tests: actual baseline function versus candidate for first-step hit, second-step hit, no hit, late hit, empty/one/two-step schedule, receiver below zero, zero padding, canopy/trunk gaps, signed zeros, and nonfinite/unsupported fallbacks. Compare all three masks by the frozen exact rules, not only final total SVF.

Counter: full versus executed samples, hit position and fallback count. Work model is ratio of actual sums of sample counts, not an unweighted average of per-ray ratios. Branch overhead may make short open rays slower; preserve a cheap serial/no-early-exit path if crossover requires it.

### 2.2 R01b: project only unobserved state

Only after R01a is admitted, evaluate Boolean B/V/E instead of numeric f/vb. Do not erase a state a trace/public caller observes. Prove comparison and finish bits independently. Maintain original float32 finish operations `1-B`, `1-V`, `1-(E-V)`; expression regrouping is not necessary. Prefer sharing one inlined transition between serial/parallel wrappers, with distinct cache-safe compiled entry definitions if required by the current JIT identity design.

### 2.3 R02: certify an irrelevant sky suffix

Use the **actual stored** decrements for each source dtype. Precompute suffix minima, not ideal trigonometric distances. For the unexecuted suffix r:

    U(r)=max(+0, RN(M_dsm-min_suffix(d_dsm)),
                  RN(M_canopy-min_suffix(d_canopy)),
                  RN(M_trunk-min_suffix(d_trunk)))

If U(r)<=receiver elevation, every future temporary height is at most the receiver. The zero term accounts for out-of-domain padding. Subject to the no-bush/finite/first-step state proof, the suffix cannot change the final masks. Keep the first two original steps initially. A per-pixel cutoff can be found with suffix-bound monotonicity if the computed bounds actually preserve it.

Do not combine this with subtracting terrain datum, replacing decrement algebra, or changing sample order. Do not infer a wall-height certificate: wall outputs use maxima quantitatively, and equality/signed-zero tie behavior may matter. Unknown/NaN bounds force fallback. Test an intentionally non-monotone stored decrement suffix so an invalid "current decrement is the minimum" shortcut is caught.

R01 and R02 can remove the same suffix. Record their union's executed samples. Add the cheaper check first or select using measured applicability; do not multiply advertised savings.

### 2.4 R04: immutable bush control prepass

The original global condition uses `max((temporary_canopy > dsm) * bush)>0`. Its inputs depend on geometry/schedule, not on evolving f/V/E/g. Prepare exact flags A[k] once, then replay them in each independent pixel recurrence including g and the original finish tail.

When all bush values are finite, positive contributors can only occur at positive bush sites, so an indexed OR can be valid. With NaN/Inf, false*Inf/NaN can poison the old max; do not use OR there. The proof must preserve these failures/branches. Complexity of the prepass may change from O(N*L) to O(N_positive*L), but total tracing remains O(N*L) unless another proof applies. Dense bushes may erase the gain.

This is an independent conditional task with a full g-state test. Do not mix it into the first no-bush absorption patch. R01 cannot be applied to the resulting positive-bush path just because B became true: g may still change.

### 2.5 Ray SIMD, dispatch and SVF consumption

Complete existing parallel dispatch only with the admitted native-thread budget. Pixel microtiles may improve locality, but irregular absorption can leave inactive SIMD lanes; measure sorted/compact lanes only if scatter/order and costs are proved. Never sort samples within one ray.

In SVF accumulation, reuse completed patch buffers and scalar weight tables while preserving patch -> annulus -> contribution order for every output pixel. Do not replace repeated weighted additions with a summed annulus weight. Ensure the lossless encoder has consumed its bytes before overwriting a patch buffer. Preserve 15 fields, directional corrections, total field, all three visibility arrays and export schema.

## 3. Radiation track: reduce memory movement, then expression work

### 3.1 P01: ordered pixel SIMD and decoded-block elimination

Target actual `patch_radiation.py` and `visibility_compiled.py` consumer routes, not a disconnected microbenchmark. Current masks are patch-major encoded but some decoded outputs are pixel-major. Avoid merely making the existing strided writes larger.

Start with a single shortwave or longwave consumer and compare:

```text
parallel each independent receiver microtile:
    allocate private accumulators [field, lane]
    for patch in original order:
        decode exact current patch slice for lanes
        evaluate original typed contribution for each lane
        update that lane's accumulator in original order
    emit required outputs
```

Different lanes are independent; each lane keeps original patch order. Do not reduce across patches in parallel. Do not allocate a shared packed output byte written by multiple owners. If a second longwave sweep depends on completed sky accumulation and per-pixel Lup, preserve that barrier and second ordered sweep. Re-decoding a small packed slice can be cheaper than retaining the full decoded cube; compare rather than assuming.

For binary/ternary/raw paths, preserve every float32 bit on decode. Validate reserved codes and errors before parallel launch or use a deterministic status/validation path that reproduces the existing error contract. A raw bitcast is not a numeric cast. Hold mapped-owner lifetime/locks across all native reads; direct fusion cannot keep pointers after close.

Begin with proposed microtile sizes 64/128/256 lanes chosen by scratch footprint and SIMD shape, then compare the already supported larger execution-block settings separately. These are internal scheduling choices, not new logical tile boundaries. Avoid a giant fusion that spills every accumulator into memory. Inspect target LLVM/assembly for lane vectorization; a `parallel=True` decorator is not evidence of SIMD or useful scaling.

Memory benefit: decoded scratch O(B*P*channels) may become O(B*accumulators)+O(P*small_coefficients). Count logical cache traffic separately from measured DRAM. Do not claim removed allocation bytes equal disk/RAM-bandwidth time saved.

### 3.2 P02: exact categorical partial evaluation

For an expression E(c[p,t], masks) whose only pixel-varying operands are admitted discrete codes, prepare every possible contribution using **the original typed expression graph**. Then choose the exact precomputed contribution per pixel and perform the same ordered addition. Never pre-sum two separately added terms.

Example: binary masks u,v admit four entries per patch. A ternary shadow/vegetation pair admits nine, but do not assume every channel is ternary on a raw path. A category code is admitted by exact payload bits (+0,1,2), not approximate equality. Signed zero and NaNs follow original/raw fallback.

Prepare separate tables for shortwave diffuse, vegetation, sunlit wall, shaded wall and cardinal contributions only where their true dependencies are pixel-uniform. Pixel-varying Lup or material/temperature inputs invalidate such a table unless exact full-tuple grouping is separately established. Avoid replacing float64 intermediates by float32 because outputs are float32. Scalar-vs-array promotion and math helper dispatch must match the original contribution evaluation. A table built with scalar libm is not automatically equivalent to a vector fallback.

Test all code/mask combinations on captured real coefficient values, extreme finite values, signed zeros, type-promoted inputs and the low-level independent diffsh case. Compile original and candidate kernels under the same profile and compare actual emitted contributions before accumulators, then every final field. Tabulation across finite states removes repeated arithmetic, not the O(N*P) decode/add work.

### 3.3 P03/P04/P05: classification options in priority order

**P03:** cache exactly `tan32(asvf)` under immutable scene/profile ownership. Preserve unsupported-layout NumPy fallback behavior. Solar coefficients and atan result stay dynamic. One float32 plane costs 4*N bytes; include setup and memory admission.

**P04:** measure distinct exact ASVF bit values U. Compute expensive classification once per distinct value and patch/time; scatter via exact indices. This reduces transcendental evaluations from N*P*T to U*P*T, not total memory/add work. Own/protect the ASVF data, include all changing coefficient/profile keys and preserve signed zero. If U~N, reject early from the census. Do not eagerly cache U*P*T Boolean history; use a bounded time/patch slab.

**P05:** real-number monotonicity is insufficient for the implemented SLEEF/rounding comparison. A threshold/interval fast path needs a certificate bounding the exact machine function. Strictly classified cases may bypass the transcendental; uncertain boundary cases invoke the original. Preserve equality, NaNs, fallback domains and existing explicit FMA. Until the certificate and adversarial actual-function tests pass, leave this research path disabled. Opus specialist reviews it independently; it is not a first-wave blocker.

### 3.4 P07/P08: share actual work, not superficially similar work

`aniLum` uses a separate patch traversal over diffsh. If its inputs are unchanged and its first consumer can safely move, add an independent original-order accumulator to a compatible visibility traversal. The integrator proves stage ordering, error visibility and source lifetimes. Keep shortwave and longwave coefficient semantics separate even when they read the same packed visibility.

Night does not imply zero longwave or static state. Reuse nocturnal pieces only under exact complete dependencies. Longwave reflected terms depend on the completed sky and spatial Lup; do not substitute an angular moment product that changes float32 accumulation or revive the previously slower moments implementation unchanged.

## 4. GVF track: ownership first, then prefix/state work removal

### 4.1 G02: eliminate redundant source copies safely

`ground_view.py::_gather` historically snapshots six source fields per direction and builds 16 receiver planes. Move ownership checks to the private boundary. Immutable buildings/albedo need not be copied each direction; timestep shadow/source emissions may be reused when unchanged.

Water trap: `_sun` forms first-direction Lup before mutating Tg on water-class cells. Later directions may see changed Tg. Prepare two deliberately distinct radiance snapshots or preserve first/later execution paths. The postprocessed Tg mutation itself remains observable. Read-only views into writable caller storage do not authorize hoisting. Low-level mutable/aliased calls retain fallback.

### 4.2 G03: fuse gather and typed postprocessing

A receiver owns its ray accumulators and first-prefix snapshots. After its original ray steps, perform original formulas in the same typed grouping and accumulate its directional contributions in original direction order. Avoid writing then rereading 16 whole-raster intermediates solely to compute a smaller set of outputs.

Keep a diagnostic route that exposes the exact 16 values for comparison. The fast path may emit final fields only if no public/trace contract promises those private intermediates. Full low-level return functions remain complete. Ensure no pixel overwrites a source another receiver still reads.

### 4.3 G01: blocker prefix and repeated-add replay

On exact {+0,1} buildings, f[k]=min(f[k-1],b[j_k]) becomes permanently zero at first blocker k_b. Preserve the actual source sequence j_k, including persistent last samples outside current slices. A naive geometric zero-fill replacement is wrong.

Finite/nonoverflow source terms multiplied by f vanish after k_b, so stop gathering their dynamic source values. Wall accumulators can continue: determine first valid sunwall k_s and activation counts for full and first-distance prefixes. Reconstruct repeated scalar additions through a table A_c[0]=+0; A_c[n+1]=RN(A_c[n]+c). Do not use n*c. Different scalar c bit values/dtypes require different tables; a spatial wall value with many distinct values may defeat reuse. Keep every original postprocessing step, keep mask and mutated Tg.

Prepare k_b per pixel/direction under exact scene/search identity; storing an index costs O(N*D), not O(N*D*R). Select uint8/uint16/int32 by proven range, not overflow-prone convenience. Ordinary open scenes can be slower because preparation buys no shortened prefix. Calculate B_prepare+T_d*C_prefix+reads versus T_d*C_original. Profile fast guard cost and reject a bad crossover.

### 4.4 G04/G06/G07 conditional work

Five unshadowed-albedo fields are plausible static subgraphs, not permission to cache changing GVF radiance. Prove the full dependency set, calculate once using original ray/direction order, and preserve all invalidation behavior. Five float32 planes cost 20*N bytes.

Material/shadow tuple tables need exact emitted inputs, not merely land-cover labels; delayed temperatures may be continuous. An interior addressing kernel may avoid per-step boundary branches only after proving the receiver's **entire** original source sequence remains in-domain. Border receivers keep the exact persisted-sample semantics. Counter arithmetic replacing Boolean-channel sums must reproduce original float32 saturation/rounding and signed zeros; large R can invalidate naive integer-count substitution.

## 5. Storage/runtime track: throughput admission, not unlimited execution

### 5.1 S01 liveness inventory

Build a named allocation table: owner, dtype, shape, creation stage, last reader, mutability, optionality, mapped/storage bytes and native reserve. Compute simultaneous live maxima by stage, not the sum of all possible scratch. Use actual validated codec payload sizes for warm native geometry; cold/unknown/raw paths need conservative capacity or an explicit out-of-core fallback.

Mapped bytes can become resident; mmapping visibility does not bound decoded scratch, output buffers or JIT memory. An admission estimate is not a hard RSS proof. Record actual process-tree peaks, shared-page caveats and platform headroom on small runs; large outcome remains L4.

### 5.2 S02 worker lifecycle

A persistent worker retains imports/JIT and small immutable tables. Each tile owns scene arrays, geometry mappings/locks, output handles, state, snapshots and scratch lifetimes. Finalization closes handles and drops references at success and failure. Include cancellation, child exception propagation, partial publication recovery and no stale-tile result reuse.

Start with a bounded worker process pool created safely for the target platform. Do not fork a live threaded NumPy/Numba process casually. Configure native thread limits before imports/initialization. One process may run its own chronological tile; no independent time workers. Retire a worker at a completed tile boundary when leak/fragmentation policy requires it, without losing pending jobs.

### 5.3 S03/S04 scheduling

Choose <=4 small-tuning tuples of workers, threads and microtile size under the same budget. Memory and CPU reservations include the coordinator/clients during development; quiet timing has its own envelope. Use actual t(W,H), not one-tile time divided by worker count. If tile weights differ, memory-admitted longest-estimated-job-first can reduce tail; do not change tile forcing/context or output names. Preserve deterministic per-tile results and record execution order separately.

### 5.4 S06/S07/S08 I/O

One writable dataset owner. Async producer hands an immutable/copy-owned buffer to a bounded queue; it cannot recycle the memory until the writer acknowledges. Checkpoint cursor advancement waits for required output write/readback/durability. Queue backpressure is correctness, not just performance.

Immutable checkpoint payload reuse can eliminate identical writes, not required hashes/validation/fsync. A new generation references only already durable content, with pins and recovery-safe garbage collection. Do not conclude "same Python object" means unchanged bytes. Start by measuring the repeated-byte fraction before implementing content addressing.

Legacy NPZ/ZIP/TIFF schemas stay. Stream export in original C order with bounded scratch; never regenerate huge dense cubes to simplify export. Compression tuning changes container bytes but not decoded artifacts; preserve metadata and timed output work. Avoid a new compression dependency unless measured benefit repays packaging cost.

## 6. Safe complete bypasses and quarantines

### 6.1 What can be entirely bypassed

- An operation with no dependency path to requested artifacts, public returns, carried state, future neighbor reads, mutations or specified errors.
- Re-evaluation of a typed expression on exactly identical immutable inputs.
- A ray suffix whose full observable state is proved invariant.
- A static subgraph already computed under the identical full key.
- Loading a directional wind plane that the frozen timeline never selects, if original input validation/error behavior is still preserved at the correct point.
- Terminal comfort computation on receivers that are prescribed masked outputs, provided no future computation or API return consumes the discarded value and invalid/sentinel/error behavior is unchanged.

Do not skip masked building geometry, nocturnal state, required radiation merely because its save flag is false, or all optional workflows because the primary test uses own-met.

### 6.2 Never silently promote these

All X01-X08 remain quarantined. In particular: fewer patches/pixels/timesteps, different ray sampling, arbitrary finite halos, surrogate/isotropic sky, unvalidated Horner/BLAS/FFT/prefix-sum algebra, parallel time scans, approximate angle/ASVF bins, terrain-datum subtraction, weakened checkpoints, reduced outputs, or extra hardware counted as an equal-resource code speedup. Pure real-number equivalence does not waive typed-machine equivalence.

## 7. Integration and evidence map

Every implementation owner returns: immutable patch identity; actual route; owned code; touched dependencies; proof/guards; actual baseline comparisons; changes to buffer lifetime; expected operation-count delta; raw small measurements if lab-provided; invalidation notes; shared dispatch recipe. No new accepted result is manufactured from a reference table generated by the same candidate.

The integrator creates the full chronological path and one stable installed-wheel small check. At each affected timestep compare state/control fields, masks, output metadata and named radiation boundaries using the existing frozen contract. Heavy debug outputs can be disabled in timings but their generation must not alter execution semantics when enabled.

L4 stays final-only. No blueprint section independently authorizes a 1024 run. When an experiment loses on a small deciding crossover or fails equivalence, retain the evidence, reject that variant and move on. Correctness repairs are not an invitation to loosen tolerances or repeat the final batch indefinitely.
