# Throughput and total-service analysis

## No observed S10 speedup exists

All authoring-time speed estimates are hypothetical or arithmetic derived from an UNVERIFIED_USER_REPORT. Current repository source was inspected, but the production model was not executed. The user's 512-square table reports simulation 37.5s, SVF 36.7s, walls .5s as selected minima; it is NOT a paired end-to-end benchmark here. The claimed daytime LW fraction .45 is profiler-derived and not an unprofiled stage fraction. Use it only for sensitivity, never as calibration.

## Four separate objectives

1. Default single-job latency: same install and no-env call, same resource defaults.
2. Throughput under a fixed CPU/RAM budget: true completed spatial jobs per second.
3. Cold first-use latency: actual import, compile, preprocess, geometry, validation and publication.
4. Repeated warm simulation: matching validated geometry/JIT state on both sides.

A candidate may improve one and regress another. Profile eligibility and product default are separate. Better resource tuning is reported independently of pure code improvement at the same W/H configuration.

## Amdahl with complete boundary overhead

For disjoint fractions f_j, stage speedups s_j and newly added normalized overhead delta:

    S = 1 / (1 - sum(f_j) + sum(f_j/s_j) + delta)

Avoid double counting: T01 removes fallback Python work; T02 and T03 may remove the same work. Classification/predicate fusion and dispatch savings overlap. Existing absorption and new suffix bounds often skip the same ray samples. Model the final graph's disjoint work, not products of isolated improvements.

Using the user's numbers only as a hypothetical sensitivity:

| Assumed daytime LW improvement | Conditional simulation speedup (f=.45) | Conditional sum-of-stages speedup |
|---|---:|---:|
| 2x | 1.2903x | 1.1273x |
| 3x | 1.4286x | 1.1773x |
| 5x | 1.5625x | 1.2206x |

The fixed stages are .5+36.7s and simulation is 37.5s. There is no new S10 execution behind these numbers. Daytime cannot be assumed as cheap as nighttime because dynamic masks and wall contributions still exist. JIT/IO omitted from a user stage sum cannot be claimed as included application time.

For one stage to yield target S*, required s is:

    s >= f / (1/S* - 1 + f - delta)

A nonpositive denominator means that stage alone cannot attain the target with any finite improvement under the model. The tool reports no finite solution, not an arbitrary infinite JSON number.

## Stage barriers and real concurrency

For independent phase j jobs of measured contended duration t_j(W,H):

    T_batch approximately sum_j ceil(K_j/W_j)*t_j(W_j,H_j) + serial + setup/tail

Use actual job sizes and a queue model if they vary. A memory-bound cold export may stay serial while simulation overlaps multiple tiles. Existing stage barriers cannot disappear in the model just because workers exist. W*H must stay within the same allowed CPU budget, plus any GDAL/BLAS/compression threads. GPU link and writer work can saturate while compute is idle.

Simple t(H)=s+p/H only describes ideal fixed algorithm scaling. Current serial/parallel routes can use different implementations, so fitting s and p to those two modes can be misleading. Also thread_budget=1 in outer region does not alone prove one Numba thread. Record actual masks in the worker's execution context.

## Resource lower bounds, not predictions

    T >= max(total_work/effective_compute, critical_span,
             actual_DRAM_bytes/effective_DRAM_BW,
             required_disk_bytes/effective_disk_BW)

These are necessary bounds. Cache hits, branch divergence, launch latency and exact math profiles affect attainable performance. Summed logical array loads are not actual DRAM traffic. Sum of per-process RSS may double-count shared pages; mmap is not zero residence. Use an allocation ledger and measured process-tree/pressure trace together.

Output payload alone, for 10 float32 fields x24 steps x24 tiles x1024², is 22.5 GiB. At an illustrative effective 100 MiB/s pure payload bandwidth this needs at least 230.4s, before checkpoints, reads, compression and fsync. This is a unit calculation, not an SSD measurement. Do not claim I/O is dominant or negligible without actual effective bandwidth.

## Preparation amortization

Typed LUT: expression NP -> C*P, with NP lookups/additions remaining.
Predicate cache: prepare once vs T*(decode+predicate); win only when recurring savings exceed build+extra memory pressure.
GVF prefix: prepare + Td*ND*(mean_valid_prefix+state_overhead) vs Td*NDR.
JIT: candidate wins repeated K jobs only when K*(cpu_service-gpu_or_jit_service-boundary_cost)>setup_J.

Do not store a huge cache merely because reuse is theoretically possible. Report U/N (exact unique states), cache hit rate, derived bytes, read volume, allocation count and gain including setup.

## CPU/GPU region selection

    T_region_GPU = prepare + conversion + upload + launches + device_work
                   + required_download + sync + neighbor_stage_penalty

Compare to strongest CPU region. A locally slower stage can be worthwhile if it avoids a much larger transfer at a downstream boundary. Conversely a 10x leaf kernel can lose E2E. Model unified-memory sharing and exact FP64 capability. Overlap uses max instead of sum ONLY when an implemented event/ownership pipeline truly overlaps independent work; not for chronological dependencies or required commit barriers.

## Confidence and termination

Small paired runs provide local engineering evidence, not a general SLA. Publish pair ratios, medians, range and raw timings; do not cherry-pick minima. Do not bootstrap broad physical-machine confidence from a handful of thermally drifting samples. Under noise or missing data, verdict is inconclusive/unavailable. No repeated full-size run until a favorable minimum appears.

The original target is 24 spatial tiles x24 times, not two scenes with 24 bands. Target status remains separate from local default speedup and optional accelerator qualification. A single successful large run is demonstrated_once, never an assured p95 <=1800s.
