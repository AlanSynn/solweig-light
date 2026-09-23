# D01: measure actual resources and preserve the correct denominator

## Objective and ownership

Evidence owner owns only new small harnesses, counters and manifests. No model edits to make the baseline easier. Shared runtime changes belong to the integrator. Use the current accepted branch as the optimization baseline; preserve original-upstream references separately.

## Native-thread defect to resolve

The old portfolio iterates RuntimeOptions(threads_per_worker=H) in one Python process and calls run_tile directly. ContextVars choose dispatch but do not set Numba's native mask. Also H=1 chooses serial GVF, H>1 chooses G03, so one set of times confounds algorithm and thread count. Do not infer `t(H)=s+p/H` from these labels.

For each shortlisted configuration start a fresh subprocess with explicit native limits BEFORE imports. Record Python/NumPy/Numba/LLVM/GDAL/math profile, requested H, numba.config.NUMBA_NUM_THREADS, numba.get_num_threads, initialized threading_layer, selected kernel route, requested/admitted W and parent CPU affinity/cgroup where available. Native OS thread count is not the same as concurrently active numerical threads. Treat BLAS/OpenMP pools separately and avoid nested HxH demand; preserve backend math behavior.

A tiny standalone Numba probe may verify startup mechanics, but the actual pipeline worker must report its mask at first real kernel entry. Capture the parent/preprocessing thread policy too. Prefer the real public entry for workflow timing. Internal component entry is valid only when the harness owns the thread context and restores it.

## Small source-bound cold census

Use a 64/128-square genuine own-met TIFF scene and all 24 time records. Trace actual invocations, wrapping without mocking the underlying functions:

- standalone producer and its GeometryStore key;
- pipeline producer and key;
- any cache miss/rebuild, cause and producer duration;
- required standalone exports/validation and simulation export branch;
- simulation step stages, write/checkpoint and final publication.

Record stage intervals without double-counting parents and children. A wrapper must not force lazy loading, allocate a time history or alter input dtypes/arrays. Instrumentation is diagnostic; uninstrumented repetitions decide speed. In cache-disabled mode two productions may remain a deliberate fallback; distinguish from cache-enabled default.

The primary code prediction is **two different identity dictionaries**, not a measured two-build claim. The tiny real call-count test decides whether it is active in the current workflow and whether normalization/configuration equality holds.

## Shortlist

Same four-core envelope: simulation 1x4 vs 2x2. Same eight-core envelope, only when actually available: 2x4 vs 4x2. Geometry: single-thread tasks vs admitted pixel-parallel tasks. Do not test a large Cartesian product. Separate route effects from native scaling by measuring the same private kernel route under different H where useful.

Start with two or three small paired trials per selected candidate/configuration, predeclare order and caches, exclude profiler runs. Record all failures and setup. A single noisy 1% improvement is not sufficient reason to retain complexity; prioritize work counts and improvement above measured run variability. Do not change trial selection after inspecting failures. Use independent tuning and evaluation scenes where practical.

## Evidence reuse and final protocol

Reference validity includes transitive numerical source, fixture, data, test harness, dependency/compiler, math profile, effective runtime and output settings. Same branch name or unchanged filename is insufficient. Reuse currently valid small golden files; do not create candidate-derived upstream expected output. Cache warmup is explicit and not an uncounted second full run.

Final output must distinguish spatial_tiles=24, timesteps_per_tile=24, patches=153, actual shapes, physical resolution/overlap, data kind, outputs, cache states, checkpoint policy, native budgets, start/end timing boundaries and publication completion. Two cases or replicated synthetic cases cannot set `actual_target_demonstrated_once`.

Missing actual data/reference is not a reason to stop kernel work. It is a reason to keep the original-target claim unverified. See VALIDATION_POLICY.md for the final-only campaign budget.
