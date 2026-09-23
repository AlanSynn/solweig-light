# D04: cold phase throughput, safe ownership and realistic admission

## Existing scope

The simulation persistent pool is implemented. `thermal_comfort` still runs preprocessing, all walls/aspect, then a serial `_calculate_svf` tile loop, before invoking the simulation pool. Increasing simulation workers alone cannot accelerate this prefix. [S04/S15/S16]

For K similar tiles with per-tile geometry g and simulation s:

    old ~ K*g + ceil(K/Ws)*s + other

This is a structural lower bound, not a measured stage split. Once D02 removes duplicate computation, do not keep counting both geometry calls in the speedup model.

## Safest first parallel stage

Use a small phase adapter to the bounded executor for native numerical geometry precomputation. Workers build the versioned common key with complete guards and checks but do not publish promised legacy TIFF/ZIP/NPZ outputs out of order. The existing ordered standalone loop consumes ready native handles and performs legacy publication as before. In-flight computation and parent export share one memory/CPU/disk admission budget.

Do not force the baseline's cache-disabled behavior into a persistent cache. For that mode initially retain sequential behavior. Public workers=1 preserves the old route. A failed speculative/precompute task must not silently change which serial-publication error would have occurred or remove lower-index completed artifacts. Retain original sorted publication and a serial diagnostic fallback for a failed precompute. Numerical work in internal immutable cache directories is different from publicly committed artifacts.

After measurements, a second patch may stage/verify exports in parallel and commit them by the original sorted prefix. Required contract: higher-index success remains private until lower jobs have reached the same public boundary; the first serial-order failure controls public error semantics; failed/unpublished temp work is retained or safely cleaned without touching user outputs. Bounded staging queues avoid unbounded disk/memory use. Preserve the all-geometry-complete barrier before simulation. If this cannot be done simply, keep export publication sequential and optimize its redundant reads instead.

Do not make a new actor framework. Reuse immutable JSON job descriptions, existing worker lifecycle/failure reporting and private command dispatch. Do not serialize GDAL handles or raw arrays through JSON. Add a validated job kind/stage internally with exhaustive tests, preserving existing execute_tiles and public return semantics.

## Phase-aware resource model

Inventory actual buffer lifetimes:

    M_worker,s = M_scene + M_required_state + M_encoded_or_raw_resident
                 + M_stage_scratch + M_jit_native + M_io
    M_total = M_parent + sum(active reservations) + writer_queue_bytes

Compute geometry/export/simulation peaks separately; stages that overlap must be summed, not maxed. Include raw visibility mode, transpose/decoder scratch, per-native-thread buffers, concurrent mmap demand and C library caches. A read-only mapping may become resident; mmap is not free memory. An observed 1.1 GiB peak on two scenes is not a universal 1.1 GiB bound.

Current estimate uses three raw cubes and old full-plane equivalents (~3.474 GiB at 1024/P153/default wind reserve/block1024). For warm native geometry, verify exact encoded mode sizes first. For cold unknown modes, reserve the fallback or use genuinely bounded disk-backed production; do not predict binary unconditionally. Correct float64 accounting means eight-byte arrays, not just a label on four-byte planes. No overflow/negative budget arithmetic.

Avoid public RuntimeOptions signature/default/as_dict changes when private planning can use existing workers/cpu_budget/memory_budget. If a new opt-in internal policy is unavoidable, keep existing defaults and public introspection compatibility, or document a genuinely required interface change for separate approval.

## Parallelism selection

Native thread limits must be set before imports in each child; verify actual Numba mask. Numerical-core phases may need H=1 for multiple geometry tasks, H=2/4 for simulation. Parent preprocessing also consumes cores; do not count it outside the envelope. BLAS nested pools are budgeted. New phase pools may require separate processes if thread maximums differ; do not reuse a process initialized with an incompatible thread cap.

Measure 1x4 versus 2x2 under four cores first. Under an explicitly selected eight-core envelope, compare 2x4 and 4x2. More workers only help until bandwidth, I/O, serial publication or RAM binds. Persistent workers retain JIT/small tables, not growing scenes; validate close locks/maps, descriptors, timezone/cache lifetimes and a per-tile memory-retirement rule.

For unequal jobs use deterministic cost estimates from metadata/counters and balance internal compute tasks. Do not reorder public output/failure semantics casually. A longest-job-first internal queue can reduce the tail; public return ordering remains original. Do not benchmark 24 identical cached scenes and call it 24 real sites.

## Tests and acceptance

Small batch of 4-8 genuinely distinct 128/256-square logical jobs, 24 steps each. Compare one and multiple workers with actual masks. Test cancellation, failed producer, corrupt cache, missing file, duplicate output destination, overlapping cache key, restart and public sorted result ordering. Check exact artifacts/state and no cross-tile contamination. Verify memory admission for binary/ternary/raw and parent-export overlap using explicit buffer accounting; RSS sampling is supporting evidence, not a hard upper bound.

Keep progress polling out of agent orchestration. OS process-liveness/resource monitoring and bounded completion markers remain necessary for safe execution. This is not a request to remove scheduler supervision.
