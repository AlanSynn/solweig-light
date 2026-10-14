# D07: Whole-workflow throughput and memory ownership

Candidates S01-S04/S06/S13-S16. Sources S05/S08/S13/S14/S16/S20; primary documents E03-E05.

## Measure actual concurrency
A ContextVar option is not a native thread mask. The stream's thread_budget=1 limits outer slots; the leaf uses prange and may have a different actual Numba mask. Record requested process workers, admitted workers, process IDs, requested H, numba.config.NUMBA_NUM_THREADS, numba.get_num_threads(), selected threading layer and leaf path from the thread/process doing the work. Measure effective masks within worker threads too when mask state is thread-local.

Use fresh processes for controlled pool configuration. Restore masks when scoping in-process controls. Respect an explicit serial call. Do not nest concurrent parallel regions into an unsupported workqueue backend. Prefer one parallel owner per region; tile processes and native leaves share the same CPU budget.

## Small joint portfolio
For a fixed four-core budget start with 1x4 and 2x2. Add 4x1 only after serial prepared GVF and memory feasibility; test 1x1 as a baseline/no-env control. Eight-core comparisons are separate. Block tuning is a second axis, not a new logical tiling. Use two predeclared block values then at most one justified microtile alternative. Fix power/thermal conditions; performance and efficiency cores are not interchangeable theoretical processors.

Cost of W jobs with H threads is measured t(W,H), not single-worker t(1,H). No dividing a four-thread time by another factor of four without adding resources or proving work reduction. Stage barriers mean serial export remains serial even when geometry produces in parallel.

## Allocation ledger
For every scene/state/scratch/buffer record dtype, bytes, owner, first/last use and concurrency multiplicity. Reserve:

    host shared + sum(active-job persistent + overlapping live workspaces
                      + native pools + GDAL caches + writer buffers)

Only non-overlapping scratch may use max instead of sum. Numba parallel runtime may retain allocations. mmap pages remain resident-memory pressure. Monitor process tree and OS pressure/swap in addition to deterministic allocation counts; summed RSS may double-count shared pages and sample intervals miss spikes.

Current native-cache admission reserves raw fallback-sized pages; known exact encoded modes can reduce reservations if parsing is validated. Cold unknown mode stays conservative or is processed with a hard streaming bound. The corrected runtime_memory and legacy runtime admission both exist, so inspect both gates; fixing one estimator may leave the other bottleneck unchanged.

GDAL reservation must match actual applied GetCacheMax/SetCacheMax behavior, not just an assumed 5% number. GDAL's thread-safe dataset feature is read-only and internally may open one dataset per thread; it is not permission for concurrent writes to one dataset. Each writer owns its dataset. Thread-local block caches and descriptors are budgeted.

## Persistent worker state
The process pool already persists across tiles. Residuals include TimezoneFinder creation, immutable model tables and compiled profile setup per tile. Reuse helper objects only when safe; NEVER reuse location-specific solar/forcing outputs across distinct tile centers without full key equality. Release tile-specific state, mapped descriptors and per-invocation contexts. Recycle a worker at a safe boundary if measured RSS slope exceeds bound; do not keep every tile in cache.

Demand globals currently have set/restore behavior. Sharing concurrent tile simulations inside one process needs a separate ContextVar/explicit-context proof or continued process isolation. A thread pool around the public model is not safe merely because numerical arrays are independent.

## Identity closure prerequisite
New compiled code/profile dependencies must be represented in simulation/cache identities. Current simulation_identity enumerates pipeline/models/data and radiation/comfort/geometry files, not a blanket recursive dependency closure. Add explicit semantic helper/version dependencies for any new _native_dispatch code and math plans. Avoid giant per-call scans: immutable installed manifest can be prepared once, but mutable source and input policies remain distinct.

## Success
Actual same-resource multi-tile throughput improves, memory remains bounded, no new mandatory tuning is required, and ordinary default still works. A larger tolerated memory budget or extra CPU core is an operational experiment, not an invisible implementation improvement.
