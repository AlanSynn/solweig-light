# Throughput model and explicit uncertainty

## Correct denominator

Historical monitored time=598.9 s for TWO spatial 1024-square scenes, each 24 time records. Therefore its descriptive average is 299.45 s/scene and 0.200367 spatial tiles/min for that pair. The original goal=24 spatial tiles/1800 s=0.8 tiles/min. Sequentially extrapolating the pair gives 119.78 min, but that is NOT a measured 24-tile baseline. Do not count bands as tiles.

The historical 289.765/302.396 inner timers surround thermal_comfort, which includes preprocessing/standalone geometry in the source. A narrative statement about excluded preprocessing is not an instrumentation definition. Final timing must explicitly include every required application phase and artifact publication.

## Hardware/phase model

For stage j and tile i, record actual non-overlapping resource demands, not only cProfile cumulative time. A convenient calibrated model for similar tiles is:

    t_j(H) = s_j + p_j/(H*eta_j(H)) + u_j
    T_phase_j ~ ceil(K/W_j)*chi_j(W_j,H_j)*t_j(H_j)
    T_batch ~ global_setup + sum_j T_phase_j

s_j is tile-local serial CPU work, p_j is parallelizable work in equivalent core-seconds, u_j is declared non-overlapped stage overhead. eta and chi capture scaling/contended slowdown and must be fitted from actual masks/routes on small trials; do not set them to one and claim a forecast. Some phases, including serial publication, can have W=1. A separate globally serial cost is NOT divided by W. If stages overlap, replace this barrier model with an explicit DAG/resource schedule rather than subtracting guessed overlap.

Necessary resource lower bounds include max(total_CPU_work/effective_capacity, critical_span, actual_DRAM_bytes/sustained_DRAM_bandwidth, actual_disk_bytes/sustained_disk_bandwidth). A lower bound <1800 does not establish achievability. Logical NumPy bytes are not measured DRAM traffic. Apple performance/efficiency cores are not assumed equal; fixed thread counts are not measured active service.

Memory admission: parent + active geometry/export/simulation reservations + writer queues <= budget. Mapped pages and raw fallback remain accounted. Increasing memory capacity can unlock W, but this is not an independent multiplier to apply after scheduling gain.

## Duplicate geometry and remaining phases

For a cold tile with two equivalent productions:

    old = 2G + E + S + I
    after common key = G + E + S + I + added_validation

After phase concurrency, a simple barrier model is:

    T = K*I_serial
        + ceil(K/Wg)*chi_g*G/r_g
        + ceil(K/We)*chi_e*E/r_e
        + ceil(K/Ws)*chi_s*S/r_s
        + O

E includes required export and stored-byte validation; We=1 until ordered publication/concurrency is proved. If a precompute/parent-export pipeline overlaps, measure it as such; do not credit free overlap. S no longer contains a second G once eliminated. r values refer to actual phase work reduction after all overlapping strategies, not multiplication of local optimistic ratios.

Example: if exactly one redundant G is f=0.20 of old total, eliminating it with negligible new overhead predicts 1.25x for that same serial workflow. f is UNKNOWN here; measure real cold producer times before using it. G duplication is a structural source hypothesis, not a measured 20% fraction.

## Conditional aggregate target boundary

For communication only, suppose every material tile phase has become parallelizable at the selected level. Let r be its measured combined implementation benefit and chi include both contention AND moving from the old H=4 to the selected H. With W=4, anchor=299.45 s and an illustrative O=90 s:

    T = 24 * 299.45 * chi / (4*r) + 90

| assumed r | assumed chi | conditional seconds | minutes |
|---:|---:|---:|---:|
| 1.00 | 1.00 | 1886.700 | 31.445 |
| 1.25 | 1.10 | 1671.096 | 27.852 |
| 1.25 | 1.25 | 1886.700 | 31.445 |
| 1.50 | 1.15 | 1467.470 | 24.458 |
| 1.70 | 1.15 | 1305.415 | 21.757 |

These are hypothetical arithmetic, not model measurements. They are invalid if cold geometry, serial export, JIT initialization or other substantial work remains outside the parallelized envelope. The new phase calculator explicitly keeps W=1 where appropriate to expose that limitation. Extra CPU resources are not an equal-resource code speedup.

With the same illustrative constants the aggregate requirement is r/chi >= 1.0507 for W=4. This superficially small requirement depends on the very strong full-workflow concurrency premise. Do not use it to promise success.

## Optimization accounting

- Shared geometry keys remove one producer and one redundant native generation. A ray improvement applies only to the remaining construction; don't count both savings on the original two calls.
- Lside projection and longwave cardinal removal affect different graph sections; allocate measured fractions once.
- Cylinder scratch reduction, finite-state evaluation, decoder batching and SIMD can overlap. Recount final instruction/memory work; do not multiply all local speedups.
- Cache hits change a regime. Report cold, validated geometry-warm and kernel-only separately.
- One-pass validation preserves work requirements while deleting redundant traversals; fsync/output obligations remain.
- Shorter required wall clock due to actual higher throughput must be demonstrated on completed spatial jobs, not partial tiles or extrapolated pixel counts.

## Minimal model calibration before final scale

D01 small cold trace supplies actual producer counts and durations. Small warm pipeline supplies repeated simulation. Small distinct multi-tile runs under fixed CPU/memory show W/H scaling and tail. Store setup, service, cache, active masks, allocations and actual data features. Use at most a few configurations; avoid a 1024 tuning sweep.

Predict final using low/base/high assumptions or measured uncertainty ranges for ray length/guard coverage/raw mode, bandwidth and tail, not one fitted number. First-use JIT can be amortized per persistent worker only if the real final harness shares the worker cache, not if it clears caches per tile. Historical per-case private caches are not the same regime.

A calibrated 20-23 minute design target leaves more margin than 29 minutes, but is not a promise. Final goal is a single observed <=1800-second 24-real-tile campaign with the required numerical coverage, on the frozen host/configuration. A single observation still establishes no reliability percentile.
