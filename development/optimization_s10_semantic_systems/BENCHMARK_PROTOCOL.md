# Benchmark and promotion protocol

## Claim hierarchy
A: frozen current-main default. B: same new algorithm/layout in existing Numba. C: optional new backend of B. U: separately pinned upstream SOLWEIG-GPU CPU; CUDA is a separate hardware comparison. H: historical project versions. Never rename A or H as U.

Boundaries: leaf, adapter, producer+consumer, stage, full installed invocation, complete batch. Every measurement identifies exactly one boundary. Route coverage and correctness are independent of timing. A faster unsupported-domain fallback is not optimized route execution.

## Freeze before results
Create templates/protocol.json as an executed protocol record with source/fixture/environment hashes. Choose primary/guard cells, intended deployment, timestamps and power state, JIT/geometry cache regimes, outputs/checkpoints and effective CPU budget. Baseline-only characterization may calibrate noise and justify gate changes BEFORE candidate result inspection; freeze a version. Historical N8/N9 gates are not amended.

Proposed S10 default gates (not achieved results):
- exact required radiation/state/artifact/mask and error-contract tests;
- three alternating paired observations for each of four small primary cells;
- geometric mean of per-cell paired geometric-mean A/candidate >= 1.10 at full installed entry;
- no more than 3% paired-median regression in any predeclared protected cell, with uncertainty/noise disclosed;
- per-cell optimized-eligible work coverage >=80% of the PREDECLARED eligible work, plus absolute whole-workload coverage;
- new backend C must additionally beat equivalent-layout B by >=5% at the same application boundary to justify new deployment cost;
- requested CPU/RAM and actual masks match, no hidden workload reduction;
- cold/first-use overhead and memory bound pass separately.

These are engineering decision gates with small samples, not a p95 guarantee or statistical significance claim. If baseline noise cannot distinguish the proposed effect, either justify the protocol before results or call evidence inconclusive, never passed.

## Minimal primary design
Use 64/128 squares for correctness, 128/256 for performance selection. At least:
1. standard landcover U daytime + night, no-env defaults, 24 steps;
2. no-landcover scalar control, no-env defaults, 24 steps;
3. landcover mixed geometry, matched production H/B, 24 steps;
4. small independent multi-tile batch with actual W/H admission and full 24/48 chronology.
Guard cases include raw visibility, original fallback types, malformed inputs, output flags, cold entry and partial edge block. Cell inputs must be independent of tuning where practical. Holdout selection is recorded before timing. Do not compare smaller candidate work to a larger reference.

## What to time
Start before workflow preparation/imports if claiming first-use. End after output/checkpoint/publication completion. Warm geometry excludes its construction only for BOTH sides. Report geometry-cold and JIT-cold separately. An uncontrolled OS page cache is not disk-cold. Conversion, packing, hash validation, interpreter/native dispatch and lazy synchronization count. Sum-of-best-components is NOT E2E.

Measure actual main/proposed paths continuously. Use aggregate/nested timers in separate diagnostic runs; instrumented percentages do not calibrate wall-clock gains. Sampling profiler preferred for attribution where available; deterministic cProfile is only diagnostic because Python/native call structures differ. Interference, battery/AC switches and host pressure are recorded, not silently filtered. Pair orders alternate or randomize by frozen seed.

## System measurements
Fresh process for each thread configuration; capture actual Numba max/mask/layer inside worker, effective BLAS/GDAL limits, worker process IDs and input import provenance. Report process-tree sampled RSS/USS/PSS where available, sample cadence, dropped peaks and shared-page double-count limitations. OS pressure/swap and native/device allocations matter. M4 heterogeneous cores mean core-count arithmetic is illustrative, not a calibrated CPU model.

## Actual target
Spatial tile count and timesteps are SEPARATE fields. For the original target: 24 spatial tiles, nominal core 1024² where relevant, actual raster extent/overlap recorded, 24 timesteps, original patch option and physical resolution, frozen output plan, <=1800s. Single success is demonstrated_once. Repeated synthetic motif performance never proves a real-scene target. Two scenes x24 hours is two spatial jobs, not 24.

## After a failure
Correctness failures: minimize locally, repair, rerun affected tests. Performance failure: do not weaken gate or redefine primary domain; reject or select retained implementation. Resource/missing data: blocked or unavailable. Freeze is a source boundary, not an excuse to avoid reporting later defects. No 1024-scale experiments while choosing variants.
