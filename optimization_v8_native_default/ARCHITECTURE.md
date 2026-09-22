# Private native-region architecture

## Stable outer shell

Keep API, CLI, raster I/O, forcing, logical tiling, chronology and checkpoint contracts. Replace only private preparation/execution regions behind guarded dispatch. Main RuntimeOptions and default values remain stable; private planner parameters are derived within the existing budgets.

```
public workflow -> bounded tile process
  -> immutable scene/geometry + chronological state
  -> RegionPlanner (once per workflow/profile change)
       -> qualified shipped library OR trusted Numba
       -> NativeHandle + numerical certificate
       -> StageConstants + geometry lease
       -> workspace/microblock/dispatch plan
  -> each timestep in ORIGINAL order
       -> original dynamic preparation
       -> region execution (many cache-sized microblocks)
       -> synchronous completion and original state update
       -> original output/checkpoint publication
```

The public `block_pixels` remains a validated execution parameter with its original default. It does not define a physical domain. Initially aggregate several existing logical blocks into one dispatch while preserving each block's observable math-profile path. Only change internal microblock boundaries after proving block/layout invariance, including shape-sensitive math fallbacks.

## Four lifetimes

| Object | Lifetime | Contents | Must not contain |
|---|---|---|---|
| NativeArtifact | installed package lifetime | source/build/ABI/ISA hashes, embedded lib, immutable manifest | user cache path lookup, credentials, mutable source handles |
| NativeHandle | process + workflow-generation | loaded function pointers, capability, profile, pool owner | output histories, automatically reloaded dylib |
| GeometryLease | tile/region | immutable encoded payload views, exact masks/layout metadata, bounded derived cache | stale raw pointers after mmap close |
| StepConstants/Workspace | step and worker-slot | exact scalar provenance, active gates, bounded scratch, current output buffers | future step state or arbitrary parallel time execution |

A process-local registry is keyed by `(pid, artifact generation, ABI, ISA, math profile, pool budget)`. Read artifact content once at initialization, never per block. Do not hash an entire source tree on each key lookup. An explicit new workflow can detect a changed dev artifact; a running workflow keeps its loaded generation. Forked children reinitialize handles and pools, or only spawn-based execution is supported and tested.

## Suggested native ABI (private, versioned)

Use the current C ABI first, with a small versioned wrapper for region scheduling. A minimal CPython/nanobind extension is allowed only when measured ctypes-region overhead remains significant. Do not replace a 61us-per-block hypothesis with a major binding rewrite before removing filesystem work.

```
ABI_VERSION = 1
artifact_info() -> {abi, scalar_profiles, layouts, ISA masks, math_id}
create_context(thread_budget, workspace_limit, mode) -> context/status
prepare_static(context, checked_geometry_descriptor, exact_constants) -> lease/status
execute_region(context, lease, step_descriptor, first_pixel, pixel_count,
               output_descriptor, cancellation_flag) -> status
synchronize(context) -> status
release_static(lease)
destroy_context(context)
```

These are design interfaces, not shipped runtime stubs. Implement only functions actually needed by the selected candidate. Use explicit sizes, strides, byte order, alignment and ABI structure-size fields. Reject integer overflow in B*P and address calculations. Verify output writability and non-aliasing. Keep Python owner references alive until synchronous completion. Do not pass foreign pointers through JSON or between unrelated processes.

## Threading and cancellation

Exactly one execution-level owner: either a persistent C++ pool over independent microblocks, a proven reusable ISPC task runtime, or a Numba-owned schedule that calls a native serial/SIMD leaf with a supported typed ABI. Do not use all three. NumPy/BLAS/GDAL compression and other pools receive bounded budgets. A tile's thermal steps remain serial. No Python tile-call ThreadPool while demand is module-global.

Allocate one scratch arena per concurrently active slot, reuse it, and wait at stage barriers before the next input mutation or workspace recycling. Errors report status and earliest meaningful failing unit; no partial public artifact is committed. On cancellation, bound drain time, stop dispatch, join/reap workers, and leave previous checkpoints intact. Do not silently delete incomplete user transaction state.

## Automatic planning

Use a packaged, versioned allow-list of qualified `(host capability, math profile, scalar profile, workload/layout domain, CPU budget)` rows. Choose one region for the workflow, not an ad hoc backend per arithmetic operation. No user-data auto-benchmark, arbitrary import graph search or network tuning service. Unknown cells use Numba. Counts and reasons are available privately for diagnosis without new normal stdout.

Capability and performance eligibility are distinct: a CPU may execute a library correctly but a particular B/H combination may be slower. The default planner checks both. Initial policies may only cover the measured native host; other supported core hosts keep identical user behavior on Numba.

## Identity and trust

Native execution identity includes generated code and compiler/toolchain version/flags, target ISA, scalar/layout ABI, wrapper version and mathematical profile. Keep stable declared backend identity through resume. If cross-backend resume is later accepted, establish a separate verified compatibility mapping; never remove checkpoint identity checks solely to improve cache-hit rates. Geometry-only dependency keys should not gain irrelevant packaging changes, but actual predicate-cache consumers need their own full identity.

The automatic loader reads only package-owned trusted artifacts, with path containment and no symlink escape. SHA checks provide content integrity, not authenticity. Install provenance remains the package manager's job. Mutable developer cache code is expert opt-in and never loaded by auto merely because a filename matches.
