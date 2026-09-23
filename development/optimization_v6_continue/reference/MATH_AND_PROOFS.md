> v5 retains the v4 lean execution scope: the strategies and proof obligations below are retained. `VALIDATION_POLICY.md` controls test size/frequency; `BRANCH_AND_CI.md` controls isolation and merge boundaries. A strategy's full-workload validation means L4 on the final combined candidate, not a new 1024 run per experiment.

# Mathematical transformations and proof obligations

This is a proof-oriented research specification, not a universal correctness certificate. Source anchors are in `SOURCES.md`. The earlier attached theory exercises are historical abstract checks; they did not run the installed SOLWEIG pipeline. The new packet does not promote any production optimization. Read only the proof sections used by an assigned strategy.

## 0. The object to preserve

Let `R_j` be rounding at the dtype of original node j, including scalar-versus-array promotion and the pinned math profile. The computation is a typed program, not just a real-valued formula. Define observable sinks as all existing public returns, requested artifacts and metadata, all carried state, mutations and specified validation/error behavior. Debug traces can be additional sinks. A fast path must have an explicit domain D and unchanged fallback outside D.

For a stateful simulation,

    z[t+1], y[t] = Phi(scene, forcing[t], z[t]).

Equal initial state plus equal transitions establishes state equality by induction. Do not replace chronological execution by an affine scan or parallel hours. Independent pixels within an admitted stage may be reordered only when no neighbor writes/read-after-write or global control dependency is crossed. Stage barriers and separate source/destination buffers are part of this proof.

Float equality is stronger than real algebra here. Keep finite bits, signed-zero signs, categorical/sentinel masks, NaN/+Inf/-Inf locations, and raw-codec NaN payloads where manipulation promises bit preservation. Retain explicit existing SLEEF FMA nodes, but introduce no new contraction. Floating-point exception modes and fallback vector/tail behavior need explicit consideration. An input being finite does not alone prove every intermediate is finite. [S11,S12,T01]

## 1. R01: sufficient state, absorption and the first-step exception

Scope: the SVF pixel recurrence, float32 admitted inputs, global positive-bush branch false, no unsupported nonfinite/intermediate behavior. It is not the wall-height recurrence.

Write the building sample at receiver x and step k as the exact original subtraction or original +0 boundary value b_k. The original running maximum starts at a_x:

    f_k = maximum_original(f_(k-1), b_k),   f_0 = a_x.

Since this particular function emits only shadow classifications and not f, define B_k=[f_k>a_x]. On the admitted domain,

    B_k = B_(k-1) OR [b_k>a_x].

Execute the original first-step vegetation correction and reset of the combined accumulator without alteration. After that exceptional step the vegetation state is Boolean. If F_k and G_k are the exact canopy/trunk above-receiver comparisons, ordinary steps satisfy

    V_k = (V_(k-1) OR (F_k AND NOT G_k)) AND NOT B_k,
    E_k = E_(k-1) OR V_k,

where E tracks whether the original nonnegative accumulated vb is positive. Initialize E=0 at the same first-step reset. Decode outputs through the original float32 subtraction graph:

    sh = 1-B,  vegsh = 1-V,  vbsh = 1-(E-V).

`vbsh` can equal 2 when the first-step special case ends with V=1,E=0. Do not compress the public result to Boolean. A one-step ray must retain this behavior.

After an ordinary step with B=1, V=0 and E fixed, all later ordinary steps leave the emitted values unchanged. Therefore a conservative implementation processes the exceptional first step and at least one ordinary step before using absorption. Empty/one-step schedules use unchanged logic. No height normalization or alternate schedule is required.

If q is the fraction of original sample work on rays that absorb, and lambda is the retained work fraction within those rays, sample-count reduction is

    rho_samples = 1 / (1-q+q*lambda).

This is not a kernel speedup. Add guard/preflight cost, inactive SIMD lanes, address generation, loads and load imbalance. With q=.7,lambda=.1 the expression is 2.70, but actual q/lambda must come from real schedule counters. First implement early exit with original state, then state projection in a separate change. [S02]

## 2. R02: a conservative suffix ceiling

For remaining steps k>=r, use the actual stored decrements d_a[k], d_v[k], d_t[k], not a recomputed trigonometric approximation. Let m_a(r)=min_{k>=r}d_a[k] and likewise for vegetation and trunk. Let M_a,M_v,M_t bound the original source values. A conservative ceiling is

    U_r = max(+0, R_a(M_a-m_a(r)), R_v(M_v-m_v(r)), R_t(M_t-m_t(r))).

The +0 term accounts for zero padding; it cannot be omitted for negative terrain. Use correct original source dtype and rounding. Suffix minima handle nonmonotone stored sequences without assuming trigonometric monotonicity.

After preserving the initial exceptional steps, U_r<=a_x establishes that later samples cannot introduce new above-receiver crossings. For the admitted Boolean projected state, V is stable and any positive V has already made E true; later nonnegative vb accumulation cannot change its final positive classification. B cannot newly change. Thus the three outputs are invariant. A more conservative implementation may require strict bounds initially and separately admit ties.

Finite-domain guards, intermediate bounds and the first-step invariant are obligations, not assertions of global support. Positive-bush tails and wall23 quantities are excluded. Binary search over a monotone conservative ceiling sequence can find a safe cutoff without a bound test at every ray step.

Combine R01 and R02 by `effective_cut=min(absorbing_cut, certified_cut, L)`, with initial-step constraints. Count saved samples once. Their improvements are not multiplicative. [S02]

## 3. R04: remove a global barrier by separating control from recurrence

The inspected code computes

    A_k = [max_x( [tv_k(x)>a(x)] * bush(x) ) > 0],

where tv_k(x) is a shifted canopy sample minus the original step decrement, or +0 outside the slice. This value is written directly from immutable inputs. It has no dependency on the evolving f/sh/vs/vb/g state. [S02]

This gives a legal two-phase dependency decomposition:

1. Compute the exact A_0,...,A_(L-1) from the immutable scene and schedule.
2. Each pixel independently executes its original ordered recurrence, using A_k to decide g updates. Apply the complete original bush tail afterwards.

Induction over k establishes the same per-pixel g and shadow state because the branch bits, inputs, and preceding local state are identical. This is a control-prepass transformation, not removal of global bush semantics.

For finite bush inputs, A_k is true exactly when an above-canopy sample occurs at a site with bush>0. Sites with negative/zero bush cannot make the maximum positive. Thus sparse positive sites can reduce activation preparation from O(L*N) to O(L*N_b). For nonfinite bush this simplification fails: false*Inf and false*NaN can poison the original reduction. Either replay the exact full original reduction or fall back.

Do not apply the building-absorption rule to terminate a pixel while its live g recurrence still needs later A_k steps. This new prepass enables independent execution; a subsequent g cutoff needs its own proof. Benefit condition:

    cost_prepass + cost_pixel_trace < cost_step_major_trace + global_scans + barriers.

N_b/N, L, the number of active A_k, and native barrier time are deciding measurements.

## 4. P01: preserve each receiver's reduction while changing interleaving

An original accumulator obeys

    a_x,p+1 = R(a_x,p + c_x,p).

No dependence connects different receiver accumulators. A new schedule may interleave receiver calculations arbitrarily while preserving the ordered sequence p=0,...,P-1 for each x. Induction on p proves identical accumulators, assuming c uses the same typed graph and all sources remain immutable.

This permits `for block; for patch; for pixel_lane` and SIMD across pixel lanes without reduction reassociation. It does not authorize arbitrary vector reductions over patches. Inspect generated code and native math helper dispatch, not just a Numba decorator. [T01,T02,T03]

Direct patch decoding into those accumulators removes four B-by-P float32 decoded arrays when the caller owns the known codec/lazy visibility objects. Workspace becomes approximately O(A*B+P), where A counts live accumulator/scratch fields. If temporary decoded blocks are retained for speed, keep them microtiled and reuse them across compatible consumers under owner locks.

Four decoded float32 arrays written then read imply 32*N*P logical bytes per sweep. With N=1024^2,P=153, that is 4.78125 GiB of logical traffic, not a measurement of DRAM bytes. Cache hits, write allocation, compiler scalar replacement and recomputation alter actual traffic. [S03,S05,T04]

## 5. P02: exact partial evaluation of finite input states

For a subexpression with pixel-independent coefficients c_t,p and discrete state s_x,p in C, define

    table[t,p,s] = E_original_typed(c_t,p, s).

Evaluate E with the original node dtypes and operation grouping; store its result in the original contribution dtype. Each pixel chooses its exact state and performs the same ordered accumulator updates. No quantization, interpolation, coefficient fitting or model approximation is involved.

For binary/ternary shadow and vegetation, diffuse visibility may have only 9 input pairs. Boolean sun/shade/building terms have similarly small joint state sets. Keep separate contribution tables when the original added terms separately. Do not pre-sum them. A zero mask does not universally imply +0 because of signed-zero and nonfinite arithmetic.

Cost model:

    old ~ N*P*T*(decode + expr + add)
    new ~ |C|*P*T*expr + N*P*T*(decode_new + select + add).

The ordered additions are still O(N*P*T). Table-evaluation count reduction is not stage speedup. Dynamic per-pixel Lup in longwave reflection prevents a single visibility-only table from covering the complete longwave calculation. [S03]

## 6. P04/P05: exact-value reuse first; certified inverse tests second

The relevant classifier contains the original typed pipeline

    D(a,c) = R(atan_profile(R(tan_profile(a)+c))*rad_to_deg).

The output uses two predicates D<patch_alt and D>patch_alt; equality can select neither. The profile contains explicit SLEEF and preserved NumPy fallback behavior. [S03,S12]

### Exact unique values (P04)

For U distinct admitted ASVF **bit patterns**, evaluate the same elementwise helper for U values instead of N, then map by exact IDs. This is ordinary same-input computation reuse:

    work_transcendental: O(N*P*T) -> O(U*P*T).

ID lookup/scatter remains O(N*P*T). Precompute IDs once per immutable tile. Preserve +0/-0 and nonfinite behavior; shape-dependent NumPy fallback calls retain their original layout or use the fallback path. Cache keys include every coefficient/profile/input dependency. If U is near N, stop.

### Certified threshold (P05)

It is unsafe to infer the exact rounded decision from real-valued atan monotonicity alone. A sound bypass constructs an enclosure [D_lo,D_hi] for the **implemented typed function**, including helper error, each rounding and coefficient identity. Decide sun only when D_hi<patch_alt, shade only when D_lo>patch_alt; otherwise run the original function. Handle equality deliberately.

A monotone threshold implementation requires proof that the admitted machine implementation is monotone, or an exhaustive checked certificate over the chosen finite domain. Do not infer this from plots or a handful of samples. A reference-centered interval fallback is allowed only when its enclosure itself is justified. Until then P05 is research, not a production fast path.

## 7. P06: exact quotienting and prefix DAGs

If f(x)=E(k(x)) and keys k(x) capture every typed input and mutation-relevant dependency, then equal keys imply equal result. Compute one result per equivalence class and scatter. This is exact memoization, not approximate spatial clustering.

For an ordered patch reduction, a prefix node can be shared only when the incoming accumulator state and all prefix contributions are identical. A prefix trie/DAG keeps the original sequence of rounded additions, unlike a matrix factorization or reordered sum.

Cost is O(U*P+N) for complete-row sharing, or O(E_edges+N) for ordered-prefix sharing, plus classification/group construction. Memory is O(E_edges) and can approach the full uncompressed workload. Test duplicate rates first. Static visibility signatures are insufficient for a subexpression that also sees varying ASVF, material, solar classification or Lup. Hash matches require exact byte comparison.

## 8. G01: static blocker prefixes and exact wall-count replay

With b(x) in {0,1}, the gather's f recurrence is

    f_k = min(f_(k-1), b(j_k)),

where j_k means the **effective original sample**, including persistent prior sample outside the current slice. The first zero at k_b is absorbing. Ground contributions multiplied by f become zero after k_b.

For admitted finite binary32 channels under the original rounding mode, initial +0 and non-overflowing ordered additions, subsequent +/-0 additions do not change a reachable ground accumulator. Prove this exact domain and retain the original path for nonfinite/intermediate failures. Do not merely assert finite inputs imply every expression is safe.

Wall contributions may continue after k_b. Let k_s be the first effective sunwall encounter before ground blocking. For a prefix m, active counts are n_s=max(0,m-k_s) and n_b=max(0,m-k_b). For a repeated value c, use

    A_c[0]=+0; A_c[n+1]=RN(A_c[n]+c),

not n*c. Keep each wall channel's original first-distance snapshot and final count. Binary +1 counters require an admitted exact representable range; large counts can saturate a float32 accumulator differently from casting an integer.

If wall c is uniform or has a small exact-value set, replay tables are cheap. Per-pixel arbitrary wall c can make table preparation prohibitively large; fall back or use the non-table path. Water first/later source preparation is external to this proof and must be preserved separately. [S04]

Preparation amortization for mean retained prefix kbar and normalized extra cost h is

    old ~ T_d*N*D*R
    new ~ B_prepare + T_d*N*D*(kbar+h).

With B_prepare approximated by N*D*R, the normalized ratio is

    rho_work ~ 1 / (1/T_d + (kbar+h)/R).

This is only an operation-count model. Open scenes can lose; choose fallback based on a preregistered input-feature crossover, not evaluation outcome.

## 9. G02/G03/G04/G06: partial evaluation plus liveness

The total ground-view function is not static. Trace every operand of each candidate cached subfield. The unshadowed-albedo family is an exact reuse candidate only under complete geometry/material/search identity. A static calculation is profitable when

    T_d*C_recompute > B_build + T_d*C_read.

Five float32 maps cost 20*N bytes. The physical cache/memory impact belongs in the same comparison.

Preparation can be hoisted out of the direction loop only if the inputs are unchanged. The source constructs first-direction Lup before mutating water Tg; later directions may see the changed Tg. Preserve two snapshots or fall back. Similarly, a read-only view does not prevent its external owner from writing.

Fuse gather and postprocessing in the original typed graph to avoid 16 full intermediate planes. Prove their removal with a backward slice from final fields, all state, API returns and required debug sinks. The trace path may retain intermediates for differential testing.

Repeated material/shadow emission tuples can also be partially evaluated exactly, but raw or high-entropy temperature fields defeat the table. Never infer that delayed radiance is categorical from land-cover categories alone. [S04,S08]

## 10. P09: what may be bypassed entirely?

An operation is removable only if no observable sink depends on its value, mutation or specified validation/error effect. Sinks include all requested outputs, carried state, future neighbors, full low-level return APIs and current error behavior. This is compiler-style dead-code elimination, not a reduced model.

Examples to investigate: unused diagnostics in a known private cylinder-only pipeline, a terminal comfort value replaced by a prescribed invalid mask, and repeated scalar-wrapper conversion on owned validated buffers. Counterexamples: an output-masked building still casts shadows; a disabled save flag does not make the underlying flux irrelevant to TMRT; nocturnal shortwave=0 does not make nocturnal longwave or state unnecessary.

The public full-return/trace path remains available. Optimization provenance must identify the output profile; all-output benchmarks cannot claim benefits from a smaller output set.

## 11. S07: reuse durable state without changing checkpoints

Let state payload P_g be immutable, content-identified and already durable. A new generation can reference P_g rather than rewrite identical bytes if ownership/versioning proves unchanged content (or a complete comparison establishes it), the payload is validated according to the existing contract, and garbage collection pins every live generation/reader.

Commit order remains: output completion/readback -> required durability -> new state references durable -> atomic cursor generation -> safe garbage collection. Removing fsync, weakening verification or increasing checkpoint interval is not this optimization.

If fraction phi of state bytes changes per timestep, ideal write volume changes from T*M_state to M_state*(1+phi*(T-1)). Hash/comparison cost can remain O(T*M_state), and state is not necessarily static during night. Measure before implementing.

## 12. Proof-to-code certificate required for every promotion

Each change must state: source/base/candidate identity; observable sinks; admitted domain; exact typed nodes; state invariants; preserved loop orders; input ownership; bounds and tie cases; nonfinite/signed-zero policy; fallback predicate; cache dependencies; proof sketch; counterexample corpus; executed commands; and separate numerical/performance outcomes.

A finite synthetic test is not a universal proof. A proof sketch is not evidence that a compiler implements the sketch. Require both adversarial differential tests and actual installed-kernel/pipeline checks. Mixed optimizations need combined tests because their guards, layouts and caches interact. Do not treat historical analysis scripts as an upstream oracle.
