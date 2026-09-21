> v5 retains the v4 small-first scheduling policy: read `VALIDATION_POLICY.md` before experiments. Numerical derivations and conditional examples below remain inherited analysis, not new measurements. Develop at 128/256 scale; one frozen final-scale batch, no routine large matrix.

# End-to-end throughput, feasibility and experiment accounting

## 1. Freeze the product workload

Primary proposed target: 24 **actual logical** 1024x1024 spatial tiles, each with 24 chronological timesteps and the existing 153-patch model, complete requested outputs and checkpoint policy, on one frozen local CPU/RAM/storage envelope. Distinguish 24 spatial tiles from 24 time bands. Record every tile's true dimensions, affine transform, physical pixel size, overlap and source context. `tile_size=1024` plus overlap is not necessarily an actual 1024-square array.

The deadline is 1800 s, giving X_target=24/1800=0.013333 tiles/s=0.8 tiles/min. A margin objective is 1200-1380 s, not a promise. Each measurement starts at the declared invocation boundary and ends only after all required artifacts and completion manifests are published. Avoid shrinking the timer to the numerical inner loop.

Maintain separate regimes:

- **First use:** empty relevant JIT/native geometry caches, complete required local preprocessing, simulation, export, writes and validation.
- **Geometry cold, compatible JIT warm:** same work, except compilation cache starts prepared.
- **Geometry warm:** includes validation/loading of geometry and complete outputs; preparation excluded and separately reported.
- **Kernel-only:** useful for attribution, never the target gate.

Network acquisition is excluded only when the target is explicitly defined as preexisting local TIFF/forcing inputs. Optional wind preprocessing is included if invoked by the frozen workflow. Hold requested outputs and checkpoint interval equal between competitors. Do not make an all-output baseline compete against UTCI-only candidate results.

## 2. Evidence boundary

The repository reports 400.827 s (dense1024) and 341.365 s (vegetation1024) in single four-thread, one-worker admissions, not repeated 24-tile batch trials. [S10] These observations do not identify stage fractions, core work, memory bandwidth demand or a target-machine concurrency curve. Earlier example decompositions are hypotheses, not profile results. The attached calculator deliberately marks every example as uncalibrated and `actual_goal_passed=false`.

A 400-second run at four threads can be consistent with many decompositions s+p/4=400. Thus s+p can range widely in the simple model. Never interpret 4*400 as measured core work or infer four-worker performance by division.

## 3. Three levels of performance reasoning

### 3.1 Necessary resource lower bounds

Let C be total equivalent core service, W_work total compute demand, L critical-path span, Q_D actual DRAM bytes and B_D sustained bandwidth. Add disk bytes Q_I and sustained disk bandwidth B_I:

    T_batch >= max(W_work/C, L, Q_D/B_D, Q_I/B_I).

Exclusive setup can be added separately only if it cannot overlap. These are necessary lower bounds, not a prediction or a sufficient feasibility proof. FLOPs alone omit branches, integer addressing, transcendental functions and decoder work. Use weighted instruction costs or measured stage core service. [T04,T05]

Distinguish logical array traffic, L1/L2/last-level traffic, DRAM traffic and disk traffic. A 4.78 GiB logical block-array traversal may remain largely in cache. Conversely poor locality, write allocation and concurrent workers can increase DRAM traffic. Vendor peak bandwidth is not attainable sustained bandwidth for this workload. Hybrid cores are not automatically identical C units.

### 3.2 A calibrated schedule approximation

For a homogeneous admitted tile, write t(H)=s+p/H+o(H), with s per-tile serial work, p parallel work in equivalent core-seconds and o overhead. These are fitted from multiple H and stage measurements, not chosen to make a goal pass. With W workers and fixed budget W*H<=C,

    X(W,H) approx W/t(H),
    T_batch approx ceil(K/W)*t(W,H) + setup + tail.

At ideal saturation H=C/W and o=0,

    X(W)=C/(p+C*s/W).

Per-tile serial stages can overlap across tiles, but batch-global serial work cannot. Shared bandwidth and processor asymmetry can invalidate ideal scaling. Use measured concurrent t(W,H,B), not isolated t(1,H,B), when evaluating a real schedule.

For heterogeneous jobs, list-schedule measured or feature-predicted t_k at fixed W/H, accounting for a memory cap. Report the final idle tail. A mean tile duration hides high-obstruction or shallow-sun outliers.

### 3.3 Final evidence

The final authority is elapsed time for the complete frozen 24-tile batch on the specified hardware. Retain raw repetitions, source/wheel/input/output identities, failures, concurrency settings, actual monitoring gaps and resource observations. A theory bound or modeled pass is never a release pass.

## 4. Non-overlapping improvement accounting

If f_j are non-overlapping stage fractions at a fixed execution configuration and s_j are their isolated measured improvements, then residual single-worker time is R=sum_j(f_j/s_j). Each new setup/cache cost must be added.

A useful reachability test with unchanged fraction u is R>=u. Even infinitely fast selected kernels cannot beat that unchanged fraction. This determines whether to broaden the portfolio to I/O, geometry or state processing.

For overlapping changes within one stage, recalculate the final instruction/byte counts or measure the combined variant. Do not multiply:

- absorbing exit and suffix bounds that remove the same samples;
- categorical tables and common-subexpression elimination that remove the same multiplications;
- larger blocks and compiled outer loops that remove the same launches;
- geometry compression and memory admission as if each were an independent kernel gain;
- thread speedup and a worker gain that consumes the same cores.

If a component occupies fraction alpha and is improved r-fold with new normalized overhead delta, stage gain is 1/((1-alpha)+alpha/r+delta). Example: alpha=.6,delta=.05 gives at most 2.22-fold stage gain even when that component disappears completely. A ray-sample count reduction must be weighted by the ray fraction of geometry before forecasting geometry speed.

## 5. Reproducible uncalibrated feasibility example

`throughput_inputs.json` has a deliberately hypothetical stage decomposition: geometry 140 serial core-seconds, radiation 480 parallel, GVF 320 parallel, other 60 serial. At H=4 the unchanged tile model gives 400 s. This is NOT the measured decomposition of dense1024.

Other assumptions: 8 equivalent homogeneous cores, 12 GiB RAM budget, parent/shared 0.8 GiB, worker base 1.85 GiB plus .075 GiB per reserved native thread, 90 s exclusive batch overhead, equal tiles. No actual DRAM/disk measurements are supplied, and their unknown values are not certified as zero. Source-independent code calculates the CPU/capacity screening below.

| Scenario | Geometry/radiation/GVF/other work reduction | Best admitted W x H in tested model grid | CPU schedule minutes | Tiles/min | With 20% slower body |
|---|---|---|---:|---:|---:|
| Unchanged work, tuned scheduling | 1/1/1/1; geometry remains serial | 4 x 2 | 61.50 | .390 | 73.50 min |
| Dispatch only | 1/1/1/1; geometry becomes parallel | 4 x 2 | 54.50 | .440 | 65.10 min |
| Modest portfolio | 1.5/1.5/1.3/1 | 4 x 2 | 40.47 | .593 | 48.27 min |
| Target portfolio | 2.5/3/2/1 | 4 x 2 | 26.30 | .913 | 31.26 min |
| Margin portfolio | 4/4/3/1.25 | 4 x 2 | 19.38 | 1.238 | 22.96 min |

The optimized work factors are goals/hypotheses for complete stages, not experimentally established values. The target portfolio is only 2.34-fold relative to the **same-resource tuned model baseline** (61.5/26.3), even though it is more than six-fold relative to a hypothetical serial repetition of a 400-second four-thread call. Report both and do not call the latter a pure code speedup. These are candidate-to-candidate examples, not original-upstream comparisons.

If only two workers with four threads fit, the target portfolio becomes 32.30 minutes in the same CPU model. Thus improved memory admission can matter even at the same eight reserved native threads. Four workers require 8.8 GiB of the assumed budget; this is an assumed reservation, not an observed safe bound.

For W=4,H=2,other=60 s, the 30-minute condition is

    140/r_g + 480/r_r + 320/r_v <= 450.

With r_g=2.5,r_v=2, radiation must reach r_r>=2.0513. Under W=2,H=4 the analogous requirement is r_r>=4.2105. Both rely on the stated toy decomposition and no extra resource bottleneck.

At 26.30 modeled minutes, only about 14.9% body slowdown is tolerable before 1800 s. A 20% slowdown fails. Targeting a substantial margin is therefore necessary for a credible deployment objective, not just a cosmetic stretch goal.

Reproduce:

    python optimization_v5_claude/tools/throughput_model.py --output optimization_v5_claude/evidence/throughput_scenarios.json

Changing reductions to measured values still does not make a calibrated forecast unless the stage demands, memory model, concurrency penalties and resource bounds are also measured and validated out of sample.

## 6. Memory and I/O feasibility

Count simultaneously live storage:

    M = M_parent + sum_active_tiles(M_scene + M_state + M_encoded + M_stage_peak + H*M_microtile + M_native) + M_writer_queues.

Do not sum mutually exclusive scratch, but include transient conversion peaks, native/JIT/GDAL caches, raw codec fallback and mapped-page pressure. Account shared pages conservatively; sampled sum-RSS may double-count them and miss shorter peaks. On Linux, additional PSS/cgroup data can help; report platform availability rather than asserting a universal measurement method.

A 1024-square float32 plane is 4 MiB. Three raw 153-patch channels are 1836 MiB; all-binary packed storage is 57.375 MiB; all-ternary storage is 114.75 MiB, before metadata. These sizes describe representations, not whole-program RSS. The current code already has compact/mapped visibility. [S05]

With 10 requested outputs, 24 bands and 24 tiles, uncompressed primary pixel payload is 22.5 GiB. Required geometry NPZ members, state files, checksums/readback and metadata add work. A compressed native geometry cache does not eliminate required legacy export bytes. An I/O overlap model must include CPU compression cost and queue memory.

For many days on the same geometry, amortized cost/day=(geometry_build+cache_validation_total)/days + simulation/day. A warm-cache throughput claim cannot be used as cold performance. Many-tile capacity is achieved with bounded active workers and streaming, not by keeping every tile resident or relying on swap.

## 7. Lean evaluation protocol: small evidence first, final scale last

Use `VALIDATION_POLICY.md` and `templates/BATCH_PROTOCOL.json`. Preserve old numerical budgets and historical protocols. v4 replaces only the prior proposed five-pair full-batch campaign. Freeze the new lean protocol before selecting/evaluating candidates.

Calibrate non-overlapping service and counters on 128/256-square tuning fixtures and a small 2-4-tile concurrency workload. At most two variants and four selected resource tuples enter each shortlist comparison. Full model chronology lives on small rasters. Genuine small pipeline traces establish temporal/state behavior. A smaller logical fixture is not a context-equivalent crop of a large target; do not extrapolate its runtime as a scientific identity.

Scale prediction must account for ray-length distributions, cache working-set transitions, dtype/profile fallback, raw codec payloads, JIT signatures, write/hash volume and concurrent memory/bandwidth. In a rough model t(N)=startup+alpha*N+beta*N*mean_ray_length+I/O(N), neither alpha nor mean_ray_length is known from one 256 run. Do not assume exactly 16x from 256 square to 1024 square. A large run remains necessary to observe actual throughput, but not at each development step.

After the combined candidate and installed small checks are frozen, perform one primary final target batch. No extra mandatory 1024 warmup; early tiles belong to the timed batch. Default new full baseline count is zero. Reuse exact matching prior evidence. One final baseline capture may be justified for essential missing numerical reference coverage before evaluation; otherwise keep that scope unverified. Absolute target timing alone does not need a baseline run, and absent matched evidence no speedup ratio is published.

Default final candidate count is one. A successful run supports `target_demonstrated_once` only, with exact hardware/configuration and checked output scope. Do not report paired confidence intervals, robust deadline achievement or p95 from that result. One causally repaired final retry is allowed after a retained failure and affected small revalidation; no unchanged sampling until a favorable time appears. Additional repetitions/cold-warm/platform matrices remain explicit later qualification.

Only one evidence owner holds the quiet-host lease. Runtime-required hashing, validation, checkpoint, I/O, exports and publication stay inside application timing; independent post-run comparisons are a separately recorded engineering cost. Report all attempts, missing references and censored runs. Lack of real data/hardware blocks the corresponding claim, not small development.

The total development budget is also an objective: count small validation sessions, first-use setup, large attempts, CI minutes and redundant reexecution. Do not optimize model throughput by spending unbounded validation time before integration.

## 8. Choosing the implementation portfolio

For candidate i, estimate removable bottleneck service Delta_i, implementation/review effort E_i, admission coverage q_i and uncertainty. Prioritize the smallest falsifying experiment that gives the most decision value, rather than fully implementing each catalog entry.

First establish counters and actual stage fractions. Then rank by conservative expected full-batch time saved per implementation effort, with correctness as a hard constraint and memory as a capacity constraint. No arbitrary per-kernel speed target substitutes for this ranking. If an unchanged stage exceeds the remaining deadline budget, broaden the portfolio before polishing already-fast kernels.

The first wave should usually compare ray work elimination, radiation decode/partial evaluation, and GVF preparation/fusion independently. Runtime/memory work follows early when admission blocks concurrency. Exact-value classification, bush-control prepasses and certified thresholds are second-wave options selected by the corresponding cardinality/control/cutoff censuses. Stop implementing catalog entries once the scoped branch-review objective is satisfied; leave broader release qualification explicit and do not auto-merge.
