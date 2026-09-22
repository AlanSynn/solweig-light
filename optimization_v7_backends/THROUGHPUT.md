# Throughput model and interpretation

No framework-specific speedup is assumed. The prior survey contains only source inspection and analytical scenarios. Current v6 dev observations are not a clean final batch baseline. Never use 598.9 seconds as the 24-spatial-tile denominator.

## Kernel speedup to whole-program speedup

For disjoint old time fractions f_j, actual candidate speedups s_j, and additional overhead delta normalized by old elapsed time:

    remaining = 1 - sum(f_j) + sum(f_j / s_j) + delta
    S_total = 1 / remaining

For one island f and desired S*, the required local speedup is:

    s_required = f / (1/S* - 1 + f - delta)

A nonpositive denominator means no finite island speedup suffices. Example scenarios, NOT observations: f=.6,s=3,delta=.03 gives 1.587x overall; f=.8,s=4,delta=.05 gives 2.222x. f=.6,delta=.03 needs 8.571x locally for 2x overall. The foreign runtime cannot claim that prediction without measuring f, adapter costs and the actual combined source.

Do not multiply overlapping decode/fusion/SIMD improvements. Recompute the final work/traffic and use measured combined stage ratios. Algorithm/layout A->B and backend B->C have different attribution. CPU-budget increases and GPU offload are separate tables.

## Compile amortization

With extra one-time compilation/runtime setup J, old per-tile island time L, new native time C and extra per-tile bridge cost B:

    savings_per_tile = L - C - B
    gain only if savings_per_tile > 0 and K*savings_per_tile > J

Persistent workers amortize J over assigned tiles; they do not allow keeping all scene histories. Batch scheduling adds its own tail and contention. Cached output reuse for unchanged benchmark input is not compilation amortization.

## Resource and phase model

Work/span and memory/disk bandwidth provide necessary lower bounds:

    max(work / effective_capacity, critical_path,
        actual_DRAM_bytes / effective_DRAM_bandwidth,
        disk_bytes / effective_disk_bandwidth)

These are not upper bounds or execution predictions. SIMD width is not speedup: for packet ray lengths L_i, eta=sum(L_i)/(w*max(L_i)) is a limited occupancy indicator only.

Use serial phases explicitly. For phase j with K comparable jobs, W_j workers and measured concurrent per-job time t_j(W_j,H_j):

    T_batch ≈ startup + sum_j ceil(K/W_j)*t_j(W_j,H_j) + publication/tail

Do not divide serial export by simulation workers. Do not plug 1-worker time into concurrent t_j without a measured or explicitly hypothetical contention factor. Reserve W_j*H_j plus active IO/native pools <= CPU envelope. Per-phase memory includes static state, encoded/raw payloads, layout conversion, scratch per concurrent native task, retained lazy arrays/compiler cache and parent/native reserves.

## Memory accounting

For N=1024² and P=153:

- one float32 raster = 4MiB;
- three dense float32 visibility cubes = 1836MiB;
- three binary or ternary channels = 57.375 or 114.75MiB before object overhead;
- 10 float32 outputs x24 timesteps = 960MiB per tile, 22.5GiB for 24 tiles.

Keep compact geometry and bounded blocks. For M float32 decoded channels a BxP block requires 4MBP bytes, separate from coefficient tables/outputs. A direct consumer may reduce decoded scratch but can be slower, as the rejected experiments demonstrate. Program memory, mapped RSS, process-tree sum and shared pages are distinct metrics.

## Tools

`tools/performance_model.py` computes scenarios and break-even counts using explicit inputs; it labels its output hypothetical. It rejects invalid/overlapping fraction sums and impossible resource reservations. It does not contain a guessed current SOLWEIG time. `tools/claim_check.py` rejects inconsistent CPU/final-campaign records but does not authenticate measurements. Frozen actual logs and review remain necessary.
