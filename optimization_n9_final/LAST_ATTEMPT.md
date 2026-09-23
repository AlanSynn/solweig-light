# One candidate: fix production of data and bounded execution

## 1. Exact mode-specialized decode

Current source: `_native_dispatch/direct_aosoa.py::_produce_patchmajor` at 7abe526a. The known modes are 1-bit binary, 2-bit ternary and raw four-byte float payloads. The generic packed expression uses division/remainder whose divisor derives from runtime `mode`:

    code = (data[i // (8 // mode)] >> ((i % (8 // mode))*mode)) & ((1 << mode)-1)

For validated non-negative pixel indices:

    binary:  code = (data[i >> 3] >> (i & 7)) & 1
    ternary: code = (data[i >> 2] >> ((i & 3) << 1)) & 3

Proof: division and remainder by 8 or 4 are exactly the corresponding right shifts and low-bit masks for non-negative integers. Evaluate the mode branch once per patch; keep patch-major then ascending pixel order. Use literal shifts, not a helper retaining a runtime divisor. Mode 1 emits exactly uint32 0/0x3f800000; mode 2 emits 0/0x3f800000/0x40000000, and code 3 raises at the original first position. Raw mode retains the original little-endian byte assembly and efficient raw loops; do not route it through a generic schedule merely for code tidiness. No floating-point conversions of arbitrary raw payloads.

Optional second tuning variant: for aligned groups, load one packed byte and extract 8 binary or 4 ternary codes. Preserve order and tails; unaligned ranges require head/tail handling. A LUT, wide load, or bit trick is unnecessary unless the simple literal-mode path still loses. Do not make a new persistent format.

Generated-code obligation: inspect actual target LLVM/assembly to verify the intended hot-loop division removal and vectorization. Python source syntax does not guarantee compiler output. The supplied Linux probe showed improvement for packed modes and no dependable raw advantage, on different NumPy/Numba/ISA versions. It is not a target-host estimate.

Make the optimized producer available to the strongest Numba control. Apply the same constant-mode transformation to the accepted layout as an A-plus comparator where practical. A native gain must not be credited to unfairly withholding shared improvements from Numba.

## 2. Direct mask production, not an accounting deduction

Existing `classify_block_aosoa` uses `_class_coefficients`, `tan32`, `atan_fma`, float32 multiply and strict `<`/`>`. Preserve these exact functions and dtype provenance. The lookup input layout is `[ceil(B/W), P, W]`.

The correct comparison is:

    old classification -> dense masks -> pack -> consumer
    new classification -> direct AoSoA masks -> consumer

Charge BOTH actual classification implementations. The old reported 0.197 ms pack cost cannot simply be subtracted to declare a new result. New loop order may change classifier efficiency.

On slot reuse, set every valid inactive sun/shade element to false before writing active columns. Supplied `sun_out`/`shade_out` do not automatically initialize themselves. Test alternating daytime/nighttime, changing active patches, repeated partial last blocks, all-false active set, equality and NaN (both predicates false). Padding may remain poison only if no consumer reads it. Validate output dtype/shape/contiguity/writeability and reject overlapping output/input spans before unsafe writes.

## 3. Prepared private ownership, not erased validation

Introduce only small internal records, e.g.:

- `InvocationPlan`: pinned artifact handle/ABI/ISA/math identity, scalar specialization, patch arrays and coefficient shapes, granted thread budget.
- `BorrowedVisibility`: admitted exact immutable types, validated ranges/layout, held owner lease, zero-copy per-patch payload views and modes.
- `BlockSlot`: bounded owned uint32 channel buffers, Boolean masks, output frame, capacity and valid extent.

Prepare invariants once at invocation/workflow lifetime. Dynamic coefficients belong to timestep lifetime; do not retain them across changing forcing. Public defensive adapters continue validating unknown calls. A trusted internal call accepts only plans minted by the producer/integrator and writes only its owned slot. Retain cheap extent/tail checks per block. No persistent `id(array)` cache without owner lifetime; no size/mtime shortcut replacing content identity.

Native load binds only installed, content-verified artifacts in normal operation, never a repo `experiments/` directory, compiler executable, editable scratch or source-tree `sys.path` insertion. Keep the established explicit expert mode as a separate deliberate route. No runtime promotion-script import or verification-tool dependency. Artifact unavailability may decline before launch; unexpected execution failure must not silently retry in Numba over mutated state.

## 4. Real bounded regions

Current dormant `_lw_dispatch._execute_row` calls `produce_blocks_aosoa(...,0,total,...)` and classifies the whole frame. Replace this with a stream. Merely passing slices of a full tensor to a region consumer is not bounded production.

    select eligible path without allocating full decoded arrays
    prepare immutable plan and leases
    allocate H bounded slots (plus declared queue capacity)
    for each independent block/region:
        initialize valid masks
        classify exact block
        decode sh, vs, vb in original observable order
        consume the two ordered sweeps
        place result in uniquely owned output interval
        release slot for reuse only after completion
    join/check all work before returning or publishing

Preserve the accepted call's classification-before-decode and sh/vs/vb ordering where errors are observable. Parallel fast-path admission may rely on known validated immutable descriptors, but cannot silently suppress corrupt reserved codes or change a required first-failure contract. If a parallel diagnostic protocol becomes elaborate, keep that domain on the original path. No double full-stream preflight purely to allow a different write order.

Source-owner locks must not deadlock: do not hold an RLock on the dispatcher while workers re-enter the public leasing function. Pass pinned read-only descriptors into worker kernels; hold/release the top-level lease at the correct owner lifetime. Scratch per worker is disjoint. Stage output is private until success. Propagate failure, cancel remaining private work and join before unmapping.

Space bound for three uint32 channels and two bool masks is approximately `14*B*P` bytes per slot, plus frame, classifier temporaries, runtime, queued slots and required final outputs. For B=1024, P=153 this payload is 2.092 MiB/slot; four slots are 8.367 MiB. This is NOT total process RSS. No `14*N*P` decoded cube: it is 2142 MiB at N=1024^2 and 8568 MiB at N=2048^2, before other fields.

Keep one parallel owner. Initially use the existing region/task pool and serial leaf kernel within each task. Avoid a new nested Numba/OpenMP/ISPC pool. Compare actual same-budget H=1/4 and worker layouts. Do not call time-dependent tile APIs concurrently in threads while module-global demand state exists.

## 5. Arithmetic remains unchanged

No new FMA; existing explicit classifier FMA is preserved. Longwave surface f64 contribution chains remain f64 through the accumulator add, followed by original f32 rounding. Do not pre-round contributions. Maintain both patch sweeps and the completed sky accumulation before reflection. No `sum`, tree reduction, matrix multiply or reassociation substitution. All seven private reducer outputs remain correct at this boundary; any diagnostic omission requires its existing private demand contract.

## 6. Tests before timing

Exact producer bits against an independent decoder and accepted producer; arbitrary raw payloads including signed zero/nonfinite; code 3 and first-error order; starts near byte boundaries; widths 4/8; sizes 0,1,W-1,W,W+1,128,1024; reused buffers; readonly/aliased inputs; mmap closed/in-use and exception cleanup. Domain guards happen before launch. Actual native call counts and completed output extents must match the declared work.

Then capture/replay real mixed-f64 calls; tiny per-patch accumulator traces only in untimed tests; actual small full chronology and all carried state. B must receive the same producer/classifier/validation scheduling as C. No benchmark-only bypass of production guards.

## Stop test

If the actual combined producer/classifier/adapter/consumer path still loses to A-plus/B under the frozen production cells, stop native. Do not rescue it with another compiler, huge block, hidden all-frame cache, omitted masks, weaker dtype or a revised workload. Integrate the independently useful producer change only if it wins in the ordinary Numba path and preserves main-facing behavior.
