# D03: Dr.Jit LLVM, not auto-selected GPU

## Fixed boundary

Port the prepared longwave primary reducer only. Import explicitly from `drjit.llvm` with non-AD types; do not use `drjit.auto`, CUDA/Metal or AD wrappers in the CPU campaign. Call `has_backend(JitBackend.LLVM)` and record initialization result/runtime. Missing backend is unavailable, not a passing skipped test.

## Typed symbolic recurrence

Dr.Jit supports symbolic array-valued while loops [F01]. A Python `for range(153)` can unroll the graph instead, increasing compile cost. Use the pinned version's verified `dr.while_loop` or `@dr.syntax` with traced integer loop state. Carry a tuple/dataclass of explicit types, not mutable unregistered objects. Each lane is one pixel; coefficient gathers use the unchanged patch index. Complete sweep 1 before forming reflected and entering sweep 2. No `dr.sum` across patches.

The baseline signature can contain float64 surface coefficients with float32 rasters/accumulators. Construct LLVM Float/Float64 operations and RN32 conversions according to the actual node ledger. Do not let Python constants silently select a different precision. Source Boolean multiplication remains a multiplication: selecting zero in inactive lanes can change NaN/signed-zero behavior. Either replicate semantics or use an admitted guarded domain with unchanged fallback.

## Optimization controls

The inspected reference states FastMath is enabled by default [F02]. Disable it and record the effective flag. That is necessary, not sufficient. Inspect IR for contractions, reciprocal transforms, constant folding, speculative evaluation, and changed rounding. Keep existing explicit FMA in the unported preparation; do not infer this reducer permits new FMA. If exact division/rounding cannot be obtained, reject that profile rather than use a numeric tolerance exception.

Use symbolic loops for performance and evaluated loops only for debugging if needed. Do not compare an evaluated-loop baseline against a fully compiled candidate as a backend-only win. Watch register pressure and graph growth. Current two-sweep function is a bounded island; do not expand to the whole day or all tiles to amortize overhead.

## Thread and synchronization accounting

Configure `dr.set_thread_count(H)` and record `dr.thread_count()` with the installed version. Its documented count includes the calling thread [F02]. Keep Numba/OpenMP/BLAS pools within the same process reservation even while idle; avoid overlapping work from those pools unless admission explicitly accounts for it.

For host-boundary timing, synchronize prior work, start the timer, perform input conversion/packing and tracing/invocation as applicable, explicitly evaluate outputs, synchronize completion, materialize required host outputs, and stop. `dr.eval`/`dr.sync_thread` and kernel-history device timing serve different purposes [F05]. Device/kernel-only time cannot replace full adapter time.

Explicitly vary dynamic input values between benchmark iterations with a fixed prepared workload sequence. An optimizer must not reuse a previously evaluated output for an allegedly new calculation. Warm compilation does not mean constant-result reuse. Check input/output identities and retained lazy graph allocations.

## Lifetime

A NumPy conversion may copy. Document real behavior for pinned versions; do not assume DLPack or unified memory removes it. No arrays/graphs retained across unrelated tiles. Scope flags and restore state for embedded usage where feasible; otherwise run backend-specific workers. Current module-global cylinder demand prevents casually parallelizing tile invocations in one Python process.

Deliverables: typed implementation, capability/runtime flag and pool record, actual seven-column exactness, debug diagnostic at first divergent node if any, assembly/IR evidence, first-use/warm kernel/full adapter times, peak live memory, fallback counts and a clear accept/reject recommendation.
