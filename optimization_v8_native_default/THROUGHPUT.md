# Cost model, default value and future optimization budget

## Reported anchor and scope

B7-60 four synthetic 1024-square tiles x24 records, workers=1, H=4, B=1024: warm A median 538.84s, native 544.86s; cold A 930.8192s. These are prior reported prepared-input stage totals, not fresh measurements or actual 24-tile target evidence. Parent-only RSS is insufficient. Never use the synthetic dense-wrapper 1.5-2.2% fraction as real-path f.

## Calling-boundary model

Expected LW calls `K*T*ceil(N/B)`. For 4*24*1024^2 at B=1024, 98,304. Per-call removable overhead h yields `n*h`; 25/50/100us imply 2.46/4.92/9.83 seconds, only hypothetical. Actual E0 measures loader/validation costs. A one-time handle changes repeated fixed overhead, not ordered arithmetic.

AoSoA direct generation removes a materialization/permutation cost P rather than just reducing reducer K:

`T_old = D + P + C + K + dispatch`

`T_new = D_final_layout + C_final_layout + K_layout + region_dispatch`.

Do not add independent speedup factors for deleting P, increasing dispatch M and eliminating the same copy in a fused kernel. Recompute the final dataflow costs.

## Amdahl with boundary cost

For disjoint original fractions f_j and real region speedups s_j:

`remaining = f_unchanged + sum(f_j/s_j) + delta_new`

`total_speedup = 1/remaining`.

For one region f, target S and overhead delta, finite kernel speed needed is `s = f/(1/S - 1 + f - delta)` when the denominator is positive; otherwise that region alone cannot deliver the target at finite speed. f must come from the current matched workload, not an unrelated profile.

Illustrative only: f=.5,s=2,delta=.02 yields 1.30x total; f=.6,s=3,delta=.03 yields 1.59x; f=.7,s=4,delta=.03 yields 1.98x. No native candidate has demonstrated these values in this packet.

## Phase model

`T_batch ~= sum_j ceil(K_j/W_j)*t_j(W_j,H_j,b_j,M_j) + serial_cost + setup`.

Here t_j is measured under concurrent execution, not lone-worker latency divided by W. Keep geometry construction, export/validation and simulation as nonoverlapping components. Serial publication remains serial unless a new reviewed design changes it. A parent phase timer includes children and must not be added again to its nested production times.

Necessary capacity lower bounds are `max(total_CPU_work/effective_capacity, dependency_span, actual_DRAM_bytes/bandwidth, required_IO_bytes/IO_bandwidth)`. These are lower bounds, not proof of completion. CPU quotas, asymmetric P/E cores, native pool efficiency and memory pressure require actual measurement.

## Memory planning

`M_live = M_static + M_state + M_compact + H*M_microblock + M_region_outputs + M_queue + M_native_reserve`.

Keep original arrays that still serve other consumers. A 4-bit longwave predicate cache costs ~76.5MiB per 1024-square/153-patch tile and can increase persistent memory even while reducing per-step decode work. Count raw fallback separately. Stage scratches can take max only when their lifetimes genuinely do not overlap. Exact cached geometry is reusable; changing radiance/state is not.

## Break-even and selection

Handle init/binary load J and per-job savings d minus bridge b pay back when K*(d-b)>J. Repeated categorical table preparation similarly pays only with enough steps. Native AOT shifts build cost to the maintainer distribution path; package size/install extraction/loading remain real DX costs. Comparing end-user installed native to developer first-time ISPC compile is not a matched deployment comparison.

Jointly tune workers/H/dispatch on a tiny shortlist. Default H/W limits do not increase automatically just because more cores are visible. One native thread pool per admitted region, not per block. If default workload is too small, auto selects Numba. If only huge blocks win, the ordinary default objective remains open.

## Actual target

24 spatial tiles /1800 seconds =0.8 tiles/minute. The simple sequential extrapolations from B7-60 are ~53.88min warm and ~93.08min cold, corresponding to ~1.80x/~3.10x needed improvement; they are not forecasts for another corpus. Installed-default speedup and actual-target achievement are separately reported.

Use the supplied `tools/cost_model.py` for transparent sensitivity calculations. It deliberately does not attach framework names to assumed speedup values. Never mark its result as a measured performance outcome.
