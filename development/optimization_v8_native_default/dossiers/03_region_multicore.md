# E3: cache-sized microblocks inside coarse native dispatch

## Two scales

`b` is the cache-local microblock. `M` is the dispatch region covering many b blocks. Existing public `block_pixels` is not silently increased to win benchmarks. First aggregate existing blocks; later use a private b only if layout/math/exception behavior is invariant. The requested logical tile, forcing location and boundary support never change.

Call count changes from `K*T*ceil(N/b)` to `K*T*ceil(N/M)` only if the region stays in native execution. A loop that calls Python decode/classify callbacks for every b has not eliminated the boundary. Do not count the theoretical reduction without an actual trace.

## Stage recipe

1. Python validates/coerces original inputs and builds exact coefficients and immutable owner leases once per required lifetime.
2. Native context receives descriptor arrays, scalar profile and resource budget.
3. One persistent pool partitions M into independent microblocks. Each slot exclusively owns its scratch arena and output span.
4. Per slot, decode/classify into the chosen layout, retain original ordered reduction, scatter required outputs.
5. Barrier before releasing sources, mutating state or publishing output.

Initially moving accepted classifier into native may not be worth its proof cost. Keep classification at an outer prepared-region boundary and include that region's bounded temporary in memory/timing. Once this is correct, test exact classifier fusion separately. Don't build an all-in-one kernel that defeats register/cache locality.

## Memory model

`M_live = M_scene + M_state + M_encoded + H*M_scratch(b) + M_output_region + M_native + M_queue`.

Do not allocate all M*P values for every in-flight region if b-sized scratch suffices. For three f32 channels + two bool masks the elementary decoded size is 14*b*P bytes, plus real coefficient temporaries/accumulators and layout padding. At b=1024,P=153 that is about 2.09MiB before other state. H copies and simultaneous producers count. Allocate arenas once, zero only accumulators that need zero, and prevent return of reused-buffer aliases.

## Parallel owner choice

Select one of:
- portable bounded C++ workers or reviewed existing thread pool around serial/SIMD leaves;
- ISPC tasks with explicit application task runtime and join;
- Numba-owned outer parallel block loop calling a supported native leaf interface, proven to release no necessary lock and obey typed ABI.

Choose by implementation cost and evidence, not by adding all runtimes. No executor per b and no OpenMP nested under Numba. For H=1 use the same correct fast implementation without task overhead. A runtime option labelling H=4 does not make an ISPC kernel use four cores; query/record actual service threads and CPU time.

Tile concurrency and inner H are jointly bounded. Start same-budget comparisons 1x4 vs 2x2 (if 4 cores allowed), and only a separately declared 8-core group for 2x4 vs 4x2. Do not convert Python tile processes to threads while demand globals exist. Geometry and export stages may choose different concurrency, while original barriers/publication order remain.

## Faults and determinism

All source snapshots are immutable until complete. An error in one slot cancels dispatch, joins others and returns a structured error; never publishes a half-computed field or recomputes through Numba after a partial write. Test interruption, worker teardown, last partial block, out-of-memory pre-admission and repeated workflows in one process. Earlier valid checkpoint artifacts remain.

## Gate

A valid change lowers full-region/installed total under both ordinary defaults and a production H/B cell. It must not merely shift cost from the timer to unmeasured preparation. Per-region constants and leases may amortize, but include their cold cost and lifetime in first-use totals. Avoid the large workload until local residual and end-to-end evidence justify it.
