# Implementation plan: remove redundant work, then increase real throughput

## 0. Scope

The target is a same-model, same-output CPU workflow for **24 spatial tiles × 24 timesteps**, not a pair of scenes. The packet is a continuation on the existing v5 branch. Actual current HEAD may be newer than e7a2d6ec; inventory differences, do not reset. Source evidence and mathematical hypotheses are separated in SOURCE_AUDIT.md. The existing 56-family register is historical context, not an implementation queue.

## 1. One startup and a small measurement repair

The coordinator performs the branch/provider/instruction inventory once. Record existing accepted changes, dormant P01, reference paths and known scientific exceptions. Do not recreate installations that work. Run the read-only branch guard; verify source imports for test environments. Append the spatial-scope correction and inspect prior timing boundaries without overwriting old reports.

The evidence owner creates a small immutable cold own-met TIFF workload and a separate warm geometry counterpart, both with full chronology. Use wrappers that COUNT real calls without replacing their numerical work to observe geometry producer invocations from standalone and pipeline paths. Record actual identities/keys before modifying them. Use isolated processes for each native-thread configuration, with limits set before numerical imports. The primary new baseline is the current accepted v5 branch, not an older codebase.

Freeze the development shortlist, equal resource envelopes, outputs, actual shapes, physical pixel size, patches, chronological forcing and cache definitions before comparing candidates. Small kernels may use adversarial long schedules even when raster dimensions are small. Do not turn every scalar experiment into a cold JIT process or full pipeline run.

## 2. Parallel preparation with exclusive ownership

Start as many useful independent reasoning/fixture tasks as have disjoint scope. There is no artificial four-agent cap. Initial preparation can include: producer/key equivalence audit, radiation backward slice, phase publication semantics, raw-memory inventory, GVF typed DAG, decoder owner lifetime, export verifier traversal and small test fixture construction.

Write production alternatives in detached worktrees at the same immutable source. Read-only reviewers can overlap. Heavy local commands reserve CPU/RAM/disk. Timed runs use one exclusive benchmark lease. Agents do not poll one another or feed full transcripts to the coordinator.

## 3. First integration wave

### A. Single geometry construction (dossier 02)

This is the new first cold-path candidate. The standalone producer and simulation producer appear to normalize the same three rasters into the same geometry arrays, while using different native identities. Verify on actual small inputs and complete 19-field results. Introduce common normalization/recipe if useful, but initially retaining conservative extra dependency hashes is safer than aggressively pruning them. Use one numerical identity; export metadata/provenance uses a separate identity. Version the change. Keep native/legacy validation, cache-disabled fallback and standalone artifact flags.

Acceptance: a genuine small cold `thermal_comfort` runs one full numerical geometry production per logical tile when cache enabled and supported; every prior geometry/output/state value is preserved; warm execution has no new build; corrupt/stale/mismatched inputs cannot masquerade as hits. Count savings before calling them speedups.

### B. Private demand-specific radiation (dossier 03)

Implement anisotropic Lside simplification separately from reduced cylinder longwave. Preserve the complete public diagnostic path and all live TMRT/state fields. The first patch retains the original four multiply nodes. The next kernel projects out cardinal-only accumulators while keeping both longwave sweeps and their ordered main accumulators. A separate cylinder shortwave helper removes box-only setup and uses only four local reduction columns. Integrator owns shared dispatch.

Acceptance: source-bound differential checks for every demanded result and full public fallback; negative-control errors/warnings/aliases; small full chronology; measured cost/allocations. No fake return values.

### C. GVF source and block arithmetic (dossier 05)

Separate actual expression reuse from snapshot copy reuse already implemented. Hoist only after proving the input mutation/alias graph. Keep pre/post water states; typed postprocess fusion is another patch. A diagnostic entry still exposes all 16 original intermediate values on small tests.

## 4. Throughput integration wave

### D. Geometry phase scheduling and memory (dossier 04)

Extend the existing task executor or a small phase adapter, not a new job platform. First parallel-precompute the shared immutable native geometry while original sorted standalone publication uses the ready handle. Failed prefetched jobs must not bypass the original error/partial-publication behavior; retain a sequential fallback for unsupported cases. Keep the barrier before simulation. Only later parallelize verified staged exports with bounded queues and ordered commit if export timing justifies it.

Use a derived live-array inventory for geometry, export and simulation. Include parent/export overlap, worst raw mode, JIT/native reserve and mappings. Resource reservation is global; phase budgets are not added as if they were free. Legacy public signatures/default dictionaries need not change just to add private planning.

Measure fixed-budget 1x4 vs 2x2 simulation; if the chosen host envelope supports eight effective cores, compare 2x4 vs 4x2 separately and label the change in resource envelope. Geometry may prefer more single-thread tasks. Cold run improvement is not established by warm `run_tile` timing alone.

### E. Prepared decode and retained reducers (dossier 06)

Batch immutable owner checks/descriptor setup and decode channels, retaining existing accepted arithmetic reducers. Keep arbitrary public duck-type/independent diffsh fallback. Do not remove reserved-code checks merely because data is usually binary. Avoid hidden full-payload copies. Cache only owned immutable data with explicit close lifecycle. Measure the native decoder separately from Python wrapper attribution. Only test a larger block after budgeting its scratch.

## 5. Conditional second wave

One-pass validated legacy export (dossier 07) is important if cold serialization remains large: current validation consumes full NPZ for CRC, then import decodes it again for comparison. Preserve all checks but combine them on the same stored stream, with the baseline path classifying failures if necessary. Do not remove fsync/readback or rely on a producer-side digest as proof of stored bytes.

Use dossier 08's register only on measured residuals: exact coefficient/ASVF reuse, compiled aniLum, ordered exact partial evaluation, ray certificate, wind demand loading, wall preprocessing, final pointwise workspaces, tail scheduling or JIT identity refinement. Each has a specific break-even and fallback. The previous P01 result, prior Horner error and old hierarchy/moment regressions are counterevidence, not tasks to repeat unchanged.

## 6. Lean selection and final freeze

After each coherent family patch, run only affected actual-kernel and small chronology checks. After integration, run affected cross-family checks. Reuse valid evidence by dependency hashes. No per-edit wheel build/full suite; one final installed-wheel check after the source settles, plus earlier wheel checks only for packaging/import-sensitive changes.

The evidence owner runs a compact 128/256 small-batch portfolio, with two or three predeclared pairs where affordable. Use progress-free terminal evidence; do not mix profilers with measured wall trials. If a trial changes code/configuration or fails, retain it under its original identity. A local gain below noise is not a promotion proof. A statistically precise speedup claim is not required for useful development triage, but the claim must remain limited.

Freeze exact final source, wheel, math profile, actual target dataset, CPU/RAM/storage, output flags, chronological state expectations and final cache regime. Run at most the final 24-tile candidate campaign and one causally justified corrective retry, as in VALIDATION_POLICY.md. If original target data/reference are missing, state the limitation instead of redefining a synthetic workload as the goal.

## 7. Terminal state

All reviewed changes remain on `perf/claude-glm53-cpu-v5`. Deliver a merge-review manifest, NOT a main merge. Correct claims append to historical records. State what was implemented, measured, verified, reused, deferred, failed or unavailable. A two-scene pass is still valuable but cannot close the original spatial-throughput goal. No branch creation or Astra handoff is needed for completion.
