# Follow-on headroom verdict: accepted S10 evidence, conditional floors, blocked host measurements

## Status and provenance

This is a follow-on diagnosis, not a reopening or re-measurement of S10.
The supplied S10 terminal state is `qualified_exact_cpu`; its source candidate is
`c245ea60`, and its S10-36 synthetic-scale demonstration remains observational.
The supplied measurements are accepted as starting facts, not independently
reproduced by this session.

No target-host measurement or product edit was executed here. The requested
`/storage/scratch1/1/dsynn6/solweig-light` workspace is not mounted in this runtime;
`sbatch` and an authenticated remote execution connection are unavailable. The
GitHub connector returned 404 for `perf/s10-semantic-systems`, 422 for `c245ea60`,
and its branch listing exposed only `main` at `b3e5ca59...`. This is a visibility
limit, not evidence that the user's local branch or results do not exist.

Executed here: standard-library floor calculations; 18 tests of those calculations
and capacity arithmetic; a temporary-file counterexample for metadata-only hash
reuse. These are not SOLWEIG performance or numerical qualification tests.

The exact source shape, S03b admission, 83-test order, and post-S10 APIs must be read
locally before implementing. No older main source is substituted for c245ea60.
No subagents were executed in this session; the local execution handoff assigns
independent roles without claiming those reviews have happened.

## 1. Production-shape arithmetic

Given 24 synthetic spatial tiles, each 1024², 24 timesteps, pinned 3 workers × 8
threads, the recorded stage times are W=20.0 s, G=4063.1 s, R=2529.7 s.
Their sum is 6612.8 s = 110.2133 minutes, with G/T=0.6144296.
Observed synthetic throughput derived from this sum is 0.2177595 tiles/minute.
These numbers are neither a repeated distribution nor an actual-target result.

For improvements to the *entire* G phase with all other stages and barriers fixed:

| Whole-SVF speedup | Chain seconds | Chain minutes | Overall speedup | Run-phase speedup also needed for 1800 s |
|---:|---:|---:|---:|---:|
| 1 | 6612.80 | 110.21 | 1.000 | Infeasible even if run is free |
| 2 | 4581.25 | 76.35 | 1.443 | Infeasible even if run is free |
| 3 | 3904.07 | 65.07 | 1.694 | 5.943 |
| 5 | 3362.32 | 56.04 | 1.967 | 2.615 |
| 7 | 3130.14 | 52.17 | 2.113 | 2.109 |
| 8 | 3057.59 | 50.96 | 2.163 | 1.989 |
| Free SVF | 2549.70 | 42.50 | 2.594 | 1.421 |

This is the first decisive verdict: no SVF-only transformation can achieve a
30-minute chain at this measured run-phase service and execution shape. Even an
SVF approximation with zero cost would not suffice. This is a constrained floor,
not an absolute hardware lower bound: different run scheduling or run algorithms
could lower the residual.

For target D and overhead O, the required run gain is

    r_R >= R / (D - W - G/r_G - O),

when the denominator is positive. If it is zero or negative, the proposed G gain
cannot reach D regardless of run improvement. All table entries use O=0; any
additional cost makes the requirement stricter.

## 2. Pixel-kernel speedup is not whole-SVF speedup

Let e be the measured fraction of SVF time outside the accelerated kernel, and k
be the measured effective speedup of that kernel under the same aggregate
allocation. Then

    r_G = 1 / [e + (1-e)/k].

If k=8, whole-phase 5× needs e<=0.0857143. Whole-phase 7× needs e<=0.0204082.
For e=0.20, phase speedup is only 3.333×, and chain time is 62.81 min.
For e=0.50, phase speedup is 1.778×, and chain time is 80.59 min.
With e=0 and k=8, the chain limit is 50.96 min, not 30 min.

M1 is therefore indispensable. A one-tile service fraction is not automatically the
24-tile phase fraction: serial export, worker waves and overlaps must be mapped
back to the measured phase makespan before choosing e. Its ledger must separate ray schedules, native
shadow recurrence, ordered SVF accumulation, encoding, numerical store, legacy
export, export validation, and scheduling. Do not count child CPU service seconds
as parent makespan or add inclusive profile totals.

The suggested 29–45 GB/s aggregate load estimate is not a no-bandwidth-wall proof.
Logical loads, cache misses, achieved DRAM bandwidth, irregular latency, NUMA
placement, branch imbalance, and repeated barriers are different quantities.
Measure scaling first; retain the bandwidth figure as an unmeasured hypothesis.

## 3. Thread allocation and tile allocation spend the same CPUs

With the supplied serial geometry behavior, only three worker threads perform the
pixel work despite a 24-CPU reservation. There are two routes to fill the reserve:
parallel pixels within tiles, or more independent tiles.

For homogeneous large pixel work and negligible overhead, effective service
capacity is W*k(H), not W*H*k(H). Relative to three serial workers, ideal compute
capacity at 24 effective cores has an 8× ceiling. Gaining 8× from more workers and
then another 8× from pixel threads double-counts the same resource.

Enumerate candidate shapes from the actual post-S03b admission and memory view.
Examples to consider, not to assume feasible: 3×8, 6×4, 12×2, 24×1.
Pick only the incumbent and the two most informative admitted competitors. Use
stage-specific shapes if the existing execution contract permits that selection.

For H>1 ensure the job's children inherit enough CPUs, record actual Numba masks,
threading layer, usable CPU affinity, CPU time, and physical-core/SMT mapping.
A Slurm request alone does not prove that eight threads ran on eight physical
cores. With OpenMP, avoid forking a process after a parallel runtime has been
initialized; retain the project's safe process-launch path.

No new dependencies, GPU/native backend, host page-cache manipulation, or global
NUMA/OS tuning is authorized. Affinity limited to an allocated job is a recorded
execution parameter, not a source of extra cores.

## 4. Temporal envelope: what can and cannot be inferred

A useful fitted model is

    T(K,N,T) = startup + phase_makespan(geometry/export)
               + phase_makespan(tile_initialization + sum_t step_cost(t)).

Use separate day/night/transition costs, fixed writer setup, checkpoints, material
and visibility modes, and shape-dependent scheduling. One 24-step time cannot
identify all coefficients. Short and long runs must retain actual chronology.

The following table is ONLY an average-step sensitivity calculation. It assumes
zero fixed cost inside R, average step cost R24/24, repeated comparable forcing,
24 spatial tiles, and the same geometry and resource shape. It is not a forecast.

| Steps | Baseline model min | Whole G 5× min | Whole G 7× min | Overall gain with G 7× |
|---:|---:|---:|---:|---:|
| 1 | 69.81 | 15.63 | 11.76 | 5.934× |
| 24 | 110.21 | 56.04 | 52.17 | 2.113× |
| 48 | 152.38 | 98.20 | 94.33 | 1.615× |
| 72 | 194.54 | 140.36 | 136.49 | 1.425× |
| 168 | 363.18 | 309.01 | 305.14 | 1.190× |

At about 38.55 average timesteps, geometry and run cost are equal in this model.
The 1-step geometry fraction is 97.0% in this simplified model, not an independently
measured 93%. Neither number should be used as a verified 1-step fraction.

Each requested corner must have its own record:
- 16² and 32×35, 1/24/48 steps: startup and fixed-service floors; no large-tile extrapolation.
- 256², 1/24: development and cost-model calibration.
- 1024², 1/24: one representative real computational shape inside a Slurm allocation.
- 72+ steps: actual synthetic timestamps and day/night transitions, plus state/restart checks.
- Shipped serial and best admitted parallel: separate latency and throughput results.

If the public API needs two met records to initialize a timestep, a one-step kernel
replay is not a one-step public run. Verify S10's actual supported contract; retain
lookahead only if the API already supports one committed step. Otherwise label the
public one-step corner unsupported, and report the replay boundary explicitly.

For one item K=1, extra tile workers cannot help. For large K, whole-job throughput
can improve even when single-tile latency worsens. Do not report one as the other.

## 5. Small/warm and long-run ceilings

The reported 0.13–0.14 s fixed residual can yield at most 1.135–1.147× if and only if
it is contained in the same 1.093 s timing boundary and could be removed entirely.
This is a ~12–13% service fraction, not evidence of a 10–25% overall improvement.
First-call/import cost cannot be subtracted from a warm time that excludes it.

For UTCI, if its true inclusive-disjoint fraction of the measured workflow is u,
its infinite-speed limit is 1/(1-u). At u=0.02 the ceiling is 1.0204×; at u=0.10 it
is 1.1111×. M5 is inexpensive and worthwhile, but M2 decides its priority.

The supplied gvf/Lcyl/Kside shares are percentages of `calc`, not `run` or the
whole chain. Let q=calc/run and rho be the disjoint locked-family share of calc
(roughly 0.755–0.772 from the supplied ranges). Eliminating EVERYTHING outside
these families has a run-phase ceiling 1/(q*rho), if their execution and concurrency
stay unchanged. Without q and nonoverlapping measurements, a numeric ceiling is
not known. Do not repack or reassociate the frozen internals to chase a target.

Long-run meaningful gains are therefore conditional on better resource use,
existing exact routes, or substantial measured outside-kernel costs. SVF-only gains
amortize toward 1× as timestep count grows. There is no evidence yet for another
large warm-run speedup.

## 6. Correct the proposed quick-win contracts

### Hash guard: reject the metadata cache as an exact default
The supplied proposal `hash_once(path,mtime,size)` is a trust-policy amendment.
A file can change bytes without changing length and have its mtime restored.
The included executed stdlib counterexample retains the same path, inode, mtime
and size yet produces a different SHA-256. Do not deploy metadata-only reuse under
the frozen content-integrity contract. Reusing content within the same immutable
snapshot or combining reads at the same already-defined validation boundary is a
candidate; silently dropping a later check is not. Explicit policy sign-off is
required before weakening detection, regardless of numerical parity.

### Import hoisting and contexts: low-risk does not mean material
Python imports are cached. Measure actual self-time and distinguish cold imports
from repeated loop lookup. Moving demand contexts can expose another operation to
a profile it previously did not observe; preserve nesting, restoration, exception
order and context-local ownership. Hoist imports first; do not remove context
boundaries wholesale without a causal proof.

### `_encode`: measure allocation before asserting a copied payload
CPython BytesIO.getvalue() may share or resize its backing bytes depending on the
runtime path. Do not assume a second full copy solely from the function name.
A streaming hash writer can still reduce buffering. Preserve NPY header/version,
array dtype/shape/order, scalar/container identity, stored bytes, fsync, generation
commit, and recovery. First compare every serialized byte outside performance timing.

### SVF fusion: attempt tier 1 before tier 2
Fuse pixel-owned work while retaining, for every accumulator, the original patch
and annulus update sequence and cast points. Moving independent pixel iterations
is different from summing weights first. Combining weights/reordering additions is
a separate tier-2 candidate and cannot silently rewrite frozen C5/C6/N8/N9 lineages.

## 7. Approximation: scheduling is the better first bet

No approximation is currently approved. The value budget for SVF is 1e-6 and shadow
categories remain exact. A ray-count census alone is not an error bound: one
omitted occluder can flip a categorical result. Reducing patch count changes a
quadrature rule, not just execution cost. An existing public alternative option
is not permission to change this workflow's pinned 153-patch calculation.

For a derived radiative sensitivity, let theta be the Kelvin-like value before
the model's Celsius offset and S=epsilon*sigma*theta^4. To guarantee |delta T|<=e
for theta>e, a sufficient two-sided flux limit is

    |delta S| <= epsilon*sigma * [theta^4 - (theta-e)^4].

At theta=300, e=0.01, epsilon=.95, sigma=5.67051e-8 this is about 0.058 W/m².
This is NOT a certified model-wide budget: all weighted contributions, time-carried
state, extrema and UTCI/WBGT sensitivity must be bounded too. It shows why a tiny
local SVF error cannot simply be declared harmless. No relaxed fastmath, reordered
frozen radiative kernels, GPU, C++ or ISPC work is proposed.

## 8. Verdict and execution boundary

Priority 1: M1/M4 and exact SVF dispatch, if existing parallel twins are bitwise and
actually faster. It has the strongest large-cold leverage.
Priority 2: post-S03b shapes and exact UTCI dispatch, with CPU/memory guard and genuine
whole-pipeline measurements. Never multiply overlapping scaling gains.
Priority 3: exact field accumulation or export/serialization work only if M1/M2 show
material service; small fixed costs only after attribution.
No material headroom statement: for a measured nonoverlapping fraction f, even
elimination gives at most 1/(1-f). If this is below a predeclared meaningful threshold,
reject that candidate class. Scope the statement to that class, workload and resource
contract, not all theoretically possible algorithms.

Phase 0 remains BLOCKED by host/source access. No product implementation or independent
review is claimed. The phase-0 handoff specifies how to finish M1–M6 locally; it is not
itself a phase-0 result. `actual_target_status` remains `unverified`.
