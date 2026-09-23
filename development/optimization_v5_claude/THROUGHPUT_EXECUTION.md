# Throughput: measurements to collect, what to infer, what not to claim

## Fixed goal, limited run budget

K=24 actual spatial tiles, N=1024^2 pixels each, T=24 chronological timesteps, P=153 patches. Primary deadline 1800 s is 0.8 tiles/min. Physical pixel size/overlap, outputs, forcing, checkpoint policy, hardware and cache regime must be frozen. Small development fixtures are not cropped substitutes for this logical workload. L4 is final-only, once by default.

Historical dense1024 400.827 s and vegetation1024 341.365 s are single candidate observations at four threads, not a 24-tile batch distribution or a one-core work estimate. No new production timing is in this packet. The retained `throughput_inputs.json` is explicitly hypothetical.

## Service model

For one tile: t(H)=s+p/H is an idealized serial-per-tile + parallel-work model. H is native threads per worker. At W workers and W*H<=C:

    batch_cpu = ceil(K/W)*(s+p/H)+overhead
    throughput_steady = W/(s+p/H)

At H=C/W, X=C/(p+C*s/W). This is why more memory-admitted workers can overlap per-tile serial work; it is not a reason to oversubscribe physical resources. On hybrid CPUs use measured t(W,H), not raw core count as equal compute capacity.

Total work/span/bandwidth lower bound:

    max(total_work/C, critical_path, actual_DRAM_bytes/B_DRAM, actual_disk_bytes/B_disk)

A favorable bound is not a runtime certificate. Allocation counts, logical array traffic and DRAM traffic are distinct. Boolean/address/ray/transcendental work is not adequately modeled by FLOPs alone. `max(cpu_schedule, bandwidth lower bounds)` is optimistic screening, not a proven upper bound.

## What each strategy changes

R01/R02 change executed ray sample counts, sometimes the same suffix; count their union, never multiply their ratios. P01/P02/P03 change overlapping instructions, cache traffic and dispatch; reevaluate their combined stage. G01/G02/G03 can overlap source/prefix/postprocess savings. S01 changes admission, S02 startup, S03 scheduling; none is an independent arbitrary throughput multiplier. Compression/snapshot changes can move cost between CPU, disk and memory.

For a reusable component with construction B, per-step original C and reused cost R, accept only if T*C > B+T*R including reads/validation/peak memory. For a stage with optimized fraction alpha, local factor r and new overhead delta, whole-stage factor is 1/((1-alpha)+alpha/r+delta). Promotion uses measured stage cost, not an attractive algebraic asymptotic alone.

## Small-run census plan

1. Freeze a small source-bound baseline. One representative 128/256-square instrumented run identifies non-overlapping stage time and aggregate counters. Do not sum overlapping cProfile cumulative entries.
2. Record ray lengths, absorption hit positions, certified suffix lengths, positive-bush density/active flags; exact ASVF/material signature counts; binary/ternary/raw payload bytes; decoded writes and kernel launch counts; GVF copies and live-plane peaks; startup/JIT/identity/IO/checkpoint costs.
3. Compare at most two selected candidates per family with the lean L3 trials. Capture actual compiled return/state/metadata exactness separately from uninstrumented timing. Keep cold setup distinct from warm compute.
4. Use 2-4 small tiles and <=4 predeclared W/H/block tuples to see contention and worker reset. Keep memory/headroom reserved for agent clients or pause them for the measurement.
5. Before L4, predict an interval from measured stage scales and conservative cache/ray/working-set uncertainty. Record that interval before seeing L4, then report error after L4. Do not introduce a fitted "g=2" batch factor without measuring its post-optimization resource regime.

Actual target census may read headers/manifests and bounded metadata; it does not authorize repeated large simulation. Do not rerun L4 to make a noisy forecast look right.

## Illustrative feasible region, not an empirical forecast

The inherited example uses geometry/radiation/GVF/other service demands 140/480/320/60 equivalent core-seconds, C=8 equivalent cores, 90 s batch overhead and a hypothetical memory budget permitting W=4,H=2. This reproduces a 400 s four-thread tile when geometry and other work are serial. After geometry parallelization, with work reductions r_g,r_r,r_v and unchanged other work, <=1800 s requires:

    140/r_g + 480/r_r + 320/r_v <= 450.

Assuming r_g=2.5,r_r=3,r_v=2 gives 26.3 min, but +20% body time gives 31.26 min. Assuming 4/4/3 plus other-work 1.25 gives about 19.38 min, or 22.96 min at +20% body time. Those are hypothetical **whole-stage work reductions**, not promised consequences of ray-sample reductions or SIMD width.

This example motivates a 20-23 minute design margin, not a claim that it will be obtained. Run `tools/throughput_model.py` only when useful, not at every agent start. Its `actual_goal_passed` must remain false.

## Measurement ownership and final report

The performance owner holds an exclusive host lease and captures actual wall time through required publication, process-tree resource peaks and raw outcomes. Self-reported agent completion is not a timing source. Required application hashing and fsync stay inside timing; independent post-run comparisons are separately budgeted. Keep timeouts/OOM/canceled work visible.

At L4, use the exact frozen compiled source/wheel, actual inputs and primary cache policy. An absolute observed deadline requires no new upstream benchmark, but a relative speedup claim requires a matched reference. If data/hardware are absent or parity reference is unavailable, say which claim remains unverified. A completed single run is `target_demonstrated_once`, not a distribution or complete P7/P8 release.
