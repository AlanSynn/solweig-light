> Worker limit: L0-L2, owned branch/worktree, no 1024/full-batch or hosted-CI run. Submit L3 requests to the single lab owner. Read `../VALIDATION_POLICY.md` for identity-based reuse; full-scale checks wait for the frozen final candidate.

# P family dossier

Load this file only for assigned P IDs. Full catalog and proof requirements are authoritative.

## P01: Compiled outer blocks, ordered pixel SIMD, fused visibility consumption

**Tier:** first. **Class:** guarded_exact. **Relation:** extends prior P.

**Transformation.** Move block scheduling into native code; traverse patches in original order for each receiver while vectorizing independent pixels. Decode one patch microtile and immediately update accumulators rather than materializing four B-by-P float arrays.

**Admission and failure modes.** Preserve accumulator dtype, separate rounding nodes, scalar promotion, raw payloads, mapped-owner locks and exception preflight. Avoid too many live registers or hidden nested thread pools.

**Cost and crossover.** Workspace O(B*A+P) instead of O(B*P) for decoded cubes. Up to 32*N*P bytes of logical write/read for four float32 decoded arrays can be avoided per sweep, not necessarily DRAM bytes.

**Smallest deciding experiment.** All SW/LW fields, mixed encodings, irregular final blocks, 1/multiple threads; assembly and per-memory-level traffic counters.

**Source anchors:** [S03], [S05], [T02], [T03].

## P02: Exact categorical partial evaluation

**Tier:** first. **Class:** guarded_exact. **Relation:** extends prior P.

**Transformation.** Evaluate the original typed expression E(coeff_t,p, discrete_state) for every allowed discrete state once per patch/timestep. Pixel kernels select that exact contribution and retain every original accumulation in order.

**Admission and failure modes.** Not a surrogate, interpolation or rounded-coefficient lookup. Tables store each separate contribution in its original dtype. Raw visibility and nonfinite-domain behavior retain an exact fallback.

**Cost and crossover.** Expression evaluations O(N*P*T) -> O(C*P*T), but selection/ordered additions remain O(N*P*T). Use stage fraction alpha and table overhead, not the N/C ratio, to predict stage speed.

**Smallest deciding experiment.** All categories including combined=2, signed zero, 0*NaN, mixed scalar types and every original intermediate cast.

**Source anchors:** [S03], [S05], [T01].

## P03: Tile-lifetime tan(ASVF) and immutable angular factors

**Tier:** first. **Class:** guarded_exact. **Relation:** previously identified, not counted as new.

**Transformation.** Compute the same profile tan32(asvf) and genuinely invariant patch/cardinal coefficients once at their valid lifetime, then reuse them across SW/LW and timesteps.

**Admission and failure modes.** Fallback NumPy vector/tail behavior can be layout-sensitive. Restrict to the certified SLEEF domain or preserve fallback layout. Solar coefficients and atan classifications remain dynamic.

**Cost and crossover.** One float32 plane costs 4*N bytes. Benefit T*c_tan*N minus build/load cost; must include added working-set pressure.

**Smallest deciding experiment.** Exact profile keys, cache invalidation, unsupported dtype/layout tests and cold/warm timings.

**Source anchors:** [S03], [S12].

## P04: Classification over exact distinct ASVF bit values

**Tier:** second. **Class:** guarded_exact. **Relation:** additional.

**Transformation.** Intern exact admissible ASVF bit patterns once per tile. For each timestep and patch evaluate the original classifier for U distinct inputs, then scatter classifications by IDs.

**Admission and failure modes.** Use bit identity, not tolerance, bins or decimal values. Signed zeros and NaN/raw classes require exact handling. Full classifier inputs, scalar dtype and math profile belong in identity.

**Cost and crossover.** O(N*P*T) transcendental evaluations -> O(U*P*T) plus O(N*P*T) cheap lookup/scatter. Benefit requires U much smaller than N and modest ID/table memory.

**Smallest deciding experiment.** Unique-value census on real scenes; dense-random ASVF negative control; exact sun/shade equality including equality yielding neither class.

**Source anchors:** [S03], [S12].

## P05: Certified classifier threshold with uncertain-band fallback

**Tier:** conditional. **Class:** guarded_exact_research. **Relation:** additional.

**Transformation.** For a patch/time classifier, derive an interval enclosure of the implemented typed tan/add/atan/degree pipeline. Return a Boolean only when the entire enclosure lies on one side; evaluate the original expression in the uncertain band.

**Admission and failure modes.** Real-number monotonicity alone does not certify rounded SLEEF monotonicity. Need a rigorous bound for the implemented profile or an admitted exhaustive float-domain certificate. Preserve separate < and >, equality and nonfinite cases.

**Cost and crossover.** New cost N*P*T*(c_compare + q_uncertain*c_original) plus certificate construction. Useful only if q_uncertain and certificate overhead are small.

**Smallest deciding experiment.** Adjacent floats around both boundaries, exact-equality values, exhaustive certified domain or checked interval proof. Unsupported intervals always fall back.

**Source anchors:** [S03], [S12], [T01].

## P06: Exact visibility/classification signatures and ordered prefix sharing

**Tier:** conditional. **Class:** guarded_exact_research. **Relation:** additional.

**Transformation.** Group receivers with identical complete inputs for a radiation subexpression, or share ordered-prefix accumulator nodes with identical incoming state and exact contribution sequence. Compute shared results once, then scatter.

**Admission and failure modes.** Visibility alone is insufficient when ASVF, Lup or material/temperature differs. Include all live inputs; verify hash collisions by byte equality. Bound trie/group memory and stop at the first pixel-dependent input.

**Cost and crossover.** Full-row grouping replaces N ordered reductions with U reductions plus O(N) scatter. Prefix sharing costs O(E) unique edges rather than O(N*P), but can be worse if E approaches N*P.

**Smallest deciding experiment.** Measure signature entropy and group/trie construction; perturb each dependency and test state/outputs bitwise. No quantization.

**Source anchors:** [S03], [S12].

## P07: Fuse aniLum with compatible shortwave visibility work

**Tier:** second. **Class:** guarded_exact. **Relation:** previously identified.

**Transformation.** Add a separate original-order aniLum accumulator to a traversal already reading the same visibility. Move it only across nodes with no data/state/error dependencies and retain the original multiplication/cast graph.

**Admission and failure modes.** Kdown consumes dRad; other radiation and ground-view stages have dependencies. This is not permission to reorder chronological state or share unrelated low-level diffsh objects.

**Cost and crossover.** Removes one independent visibility sweep and its materialization costs; derive combined work once with P01/P02, never multiply their savings.

**Smallest deciding experiment.** Intermediate aniLum/dRad plus all output fields and state; independent dense diffsh fallback and scalar-type fixtures.

**Source anchors:** [S03], [S06], [S08].

## P08: Reuse longwave decode and specialize identical nocturnal components

**Tier:** second. **Class:** guarded_exact. **Relation:** additional.

**Transformation.** Keep exact decoded categories or compact masks locally across the two required LW sweeps. Hoist nighttime coefficients that are exactly equal while retaining sky anisotropy and chronological updates.

**Admission and failure modes.** The reflected term uses completed sky accumulation and pixel Lup. Never replace LW with total SVF or skip nighttime. Cache keys include all coefficients and state-dependent inputs.

**Cost and crossover.** Reduces repeated decode/preparation and some coefficient arithmetic; two ordered mathematical sweeps may remain. Match emitted scratch to cache capacity.

**Smallest deciding experiment.** Night/day transitions, low sun, varying Lup, leaf state, cloudy sky, SW-off but LW-active fixtures.

**Source anchors:** [S03], [S08].

## P09: Demand graph and admitted output-profile specialization

**Tier:** conditional. **Class:** guarded_exact. **Relation:** additional.

**Transformation.** Construct backward liveness from all requested artifacts, public returns, carried state, validation/error effects and trace mode. Omit only truly dead intermediates; specialize common cylinder/flag paths while retaining every live radiation contribution.

**Admission and failure modes.** Do not skip physics because a diagnostic save flag is off. Keep full low-level return contracts and a full-trace execution path. Validation side effects and alias writes are observable sinks.

**Cost and crossover.** Work/bytes removed equal the proven dead subgraph, not an assumed output percentage. No saving in all-output/full-trace profiles where values remain live.

**Smallest deciding experiment.** All seven workflows, each flag combination, state equality, low-level full returns, and errors. Audit backward-slice edges explicitly.

**Source anchors:** [S03], [S06], [S08].

## P10: Typed-profile specialization and optional native extension

**Tier:** conditional. **Class:** guarded_exact_research. **Relation:** additional.

**Transformation.** Build lean common-profile kernels rather than repeated inspect.signature and generic wrapper dispatch; consider a small C/C++ SIMD extension only when generated-code evidence shows persistent Numba limitations.

**Admission and failure modes.** Preserve NumPy fallback, package portability, explicit SLEEF FMA and all original arithmetic nodes. A language rewrite alone is not a performance argument.

**Cost and crossover.** Reduces dispatch or poor machine-code overhead; include compilation, wheel distribution and instruction-cache costs in first-use evaluation.

**Smallest deciding experiment.** Installed-wheel CPU-only tests, scalar/array dtype matrix, unsupported-profile fallback, LLVM/assembly evidence and same-host pairs.

**Source anchors:** [S03], [S06], [S12], [T02].

