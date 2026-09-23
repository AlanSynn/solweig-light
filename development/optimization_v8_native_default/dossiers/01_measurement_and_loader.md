# E0/E1: measure real work and remove repeated preparation

## Why this goes first

The current path `_ensure_loaded -> _cache_dir -> _build_needed -> source hash/JSON` executes per native reducer call. `_load`'s internal cache does not remove that prefix. B7-60 roughly has 98,304 LW blocks; even tens of microseconds per call are consequential. This is a source-based hypothesis, not a claim that it explains all regression.

## Instrumentation recipe

Use worker-local call-through instrumentation, disabled in final uninstrumented timing. Wrap actual loaded C entry calls, not only Python resolver/build functions. Aggregate in process-local counters and emit one bounded terminal record, not one log line per block. Record:

- requested mode, effective mode and generation/ISA/scalar profile;
- region and microblock counts, total pixels*patches by native and fallback;
- once-only loader wall/CPU time; build count and source/JSON opens;
- invariant validation, per-block dynamic validation, decoder, classifier, layout, C entry and result scatter times;
- actual native pool size, Numba configured max/mask, process-tree RSS and host pressure;
- distinct fallback reasons, errors/cancellation and blocked input cases.

Counters attach inside `runtime_worker`/actual call path so parent observations do not falsely report zero work or zero memory. Kernel entry proof must occur immediately around the admitted function pointer invocation. Native library construction before an UnsupportedInput rejection is not execution proof.

Profile on current packed runtime and actual f64 scalar provenance. Dense fallback microbenchmarks stay labeled. Sampling/trace overhead is measured and separate from uninstrumented A/B/C. For a quick decomposition, use 128/256-square frames with full 24-step forcing and requested outputs; no full-size sweep.

## Handle lifecycle

Implement `prepare_native_handle()` outside the repeated block loop. Resolve installed binary path, validate package manifest/content once, ensure ABI/ISA/profile, load function pointers, establish scalar entry map and execution budget. Return a process-local immutable handle. Its execution method has no source IO, JSON parse, filesystem mkdir/stat, compiler path lookup or subprocess call.

Cache unavailable capability too, within a workflow, to avoid repeated failed import attempts. Do not cache input validation or mutable outputs blindly. The handle records PID; after a fork it must be rejected/rebuilt safely. Explicit generation changes occur between workflows, never mid-sweep. Close a pool only after work drains; retaining a loaded library until process exit can be safer than dlclose while another thread may execute it.

The expert legacy developer route may still build deliberately requested native source. It uses a content-addressed build key covering kernel, adapter ABI, compiler executable/version, flags, link inputs and target. Use a per-key lock, unique temporary build directory, assembly/ABI checks, atomic publication and manifest-last semantics. Never race multiple workers writing the same dylib. Auto does not invoke this builder.

## Separate invariant and dynamic validation

Per stage: supported class/layout, static array dtype and sizes, geometry owner generation, patch count, static coefficient pointer/stride, math profile. Per new step: scalar specialization, live coefficient values/dependencies, Lup snapshot, shape and ownership. Per microblock: valid range and tail bounds; when the planner already constructs owned scratch, avoid redundant full array API introspection.

Do not skip dynamic alias/writability checks for caller-provided output. Current helper permits reusable out; ensure it is writable, properly sized and nonoverlapping before native writes. A direct-pointer adapter does not make read-only NumPy memory writable safely.

## Small acceptance tests

- Spy source opens/JSON/stat/hash after preparation: repeated executes perform zero such native-preparation operations.
- Actual C call counter increases for admitted calls; unsupported call takes original fallback and no C entry.
- Two concurrent preparation requests use one artifact generation; no half-built file.
- Workflow generation changes and PID changes cannot reuse stale pointer/pool state.
- Missing binary/unsupported ISA versus admitted native error are distinct.
- Existing captured f32/f64 outputs remain bitwise equal because arithmetic did not change.

## Compare and stop

Benchmark C0 full call, new handle-only call and A on B=128 and B=1024 real scalar profiles before giant blocks. Include first-use separately. If this only removes ~1% total time, record it and move to the broader region; do not launch a new 1024 campaign merely to resolve a microsecond result.
