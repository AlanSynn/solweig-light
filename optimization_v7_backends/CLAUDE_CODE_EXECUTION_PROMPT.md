# Execute optional CPU backend comparison in Claude Code

You are the GLM-5.3 coordinator in the existing SOLWEIG-light checkout. This is an implementation request, not a request for another strategy document. High-level design is in this packet. Complete local implementation, focused tests, independent review, justified selection and same-branch integration. Do not summon Astra/Codex. Ordinary proof refinement, layout choice, compiler debugging and experiment rejection remain inside Claude Code.

## Continuation

Use the existing `perf/cpu-optimization` integration branch. Record current HEAD, relevant source/profile/dependency hashes and protected dirty paths; never reset to a historical commit. The survey used 4689421c; this packet rechecked branch tip 7a37a6f5 and the first reducer blob. Preserve subsequent changes. Only the integrator commits. Independent workers may use detached worktrees at explicit immutable bases; no new named integration branch. No push/PR/main merge, hosted CI trigger/broadening, release, auth/global dependency changes or destructive cleanup.

Read PLAN, DESIGN_AUTHORITY, KERNEL_CONTRACT, the validation/performance policy and TASKS_CLAUDE once. Assign only relevant dossiers to workers. Reuse existing source-bound v6 references and tests. Do not restart completed P0-P6 or reread all historical evidence for every change. Preserve current slim CI.

## Goal and non-negotiable invariants

Improve measured CPU throughput while preserving all seven public functions, argument/CLI semantics, TIFF and legacy artifacts, optional compatibility distribution, logical tiles, resolution, 153 target patches, full timestep chronology, vegetation, ray support and physical components. Own-met core remains Torch/CUDA-free. Keep the exact current typed numerical profile, scalar provenance, per-pixel operation order, original SLEEF preparation, explicit source FMA only, state and source-buffer ownership. No newly enabled fast math, tree reductions, downcasting, approximate lookup/surrogate, lower spatial/time resolution or hidden durability change.

The actual target is 24 spatial 1024-square tiles, EACH 24 timesteps, <=1800s under a frozen CPU/RAM/output/cache envelope. The historic 598.9s concerns two scenes only. Missing actual data/reference leaves this target unverified, not satisfied by replicated easy scenes.

## First experiment: three controls, one boundary

Capture the actual reached `cylinder_longwave._longwave_primary` prepared arguments and seven output columns from untouched reference execution. Inspect native signatures/typed IR; float32 outputs can contain mixed-precision intermediate arithmetic. Make one immutable real/adversarial corpus and typed-node ledger.

A = current accepted Numba. B = the same algorithm with the proposed layout/scheduling in Numba. C = a foreign CPU backend using B's layout. Include layout conversion and bridge cost in the comparison. Retain both ordered patch sweeps and the reflected dependency on completed first-sweep sky accumulation. Initial SLEEF/classifier/decoder stay outside. Do not change decoder and reducer simultaneously.

Delegate parallel independent prototypes to: (1) ISPC, or Highway if the local native route is more practical; (2) Dr.Jit LLVM; (3) PyOpenCL+PoCL CPU when a real CPU runtime is available without privileged setup. Do not install every surveyed framework. MLX CPU/Halide is conditional on a named remaining pointwise/stencil bottleneck. Existing rejected fused-radiation and prepared-decoder routes remain OFF.

For each backend verify real device, compiler, ABI, supported dtypes/denormals/rounding, effective thread pools and generated code. Dr.Jit must be explicitly LLVM/non-AD, FastMath disabled and output evaluation synchronized. Native SIMD preserves original casts and no new FMA. OpenCL must select a CPU device, disallow contraction/relaxed/native math, and qualify fp64/denormal/division support. Flags are not exactness proof. GPU auto-selection is forbidden; optional GPU research is a separate record and not the CPU result.

## Performance-driven decisions

Freeze the small protocol before selecting variants. Start at tiny actual-kernel tests, then 64/128-square TIFF runs with all 24/48 chronological steps, then 128/256-square small multi-tile measurements. RuntimeOptions labels alone do not establish thread counts: use separate processes with limits before imports and query effective pools. Time lazy/async work through required host materialization and synchronization. Record first-use JIT, warm kernel, full adapter, whole pipeline, memory, failures and fallback coverage separately.

Select by end-to-end benefit against BOTH A and B, not a device-only timer or theoretical FLOPs. If B matches/beats C, prefer B. A foreign library with no qualifying improvement is rejected or retained only as a small explicit experiment; do not make it a core dependency. Do not multiply overlapping savings. Use the supplied hypothetical model only with measured inputs clearly distinguished.

## Integration and verification

A separate agent reviews each immutable candidate's proof, code, negative cases and actual evidence. Do not repeat all already-valid tests for reassurance. Numerical mismatch inside an admitted domain is a failed experiment, not a silent fallback. Unsupported input/device can use unchanged Numba before side effects, with truthful counters.

Integrator lands only selected reviewed changes, with a small private adapter, optional dependency, explicit CPU-backend selection and unchanged public defaults. Core-only import/install must work without the extension/runtime. Keep all required public diagnostics and current omitted-diagnostic sentinel semantics. Add correct backend/compiler/device/profile identity to affected cache/checkpoint records. No unbounded lazy graphs, full visibility cubes or retained histories. CPU/RAM pools and writer queues are jointly bounded. Keep independent tile jobs in processes until module-global demand state is separately proven thread-safe.

Build and test the installed winner after the source settles, plus a core-only environment. No per-commit wheel/full suite/1024 rerun. Final actual 24-tile campaign defaults to one run, zero new large baselines, one justified missing-reference capture or explicit unverified scope, and at most one causal retry after a small reproduced fix. Do not broaden the CI or historical release matrix.

## Delegation and completion

Use actual authenticated GLM/Opus routes and record them honestly; an opus alias mapped to GLM is not Anthropic Opus. There is no artificial inference-token or total-agent cap, but local builds/tests obey host budgets. No manager busy polling, transcript replay or routine user approval. Use real completion events/blocking waits; one owner times the host exclusively. Workers implement/test/repair within their bounded scope, then return concise terminal summaries and evidence paths. Shared files have one integrator owner.

Conclude with reviewed same-branch commits, A/B/C decision, exact qualified domains, actual measured throughput/resources, reproducible commands, rejected/unavailable backends, portability gaps and actual-target status. No import-only prototype, stubs, invented speedups or unowned background promise. If no C wins, complete the comparison honestly and preserve the best verified Numba implementation.
