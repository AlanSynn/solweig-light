> v5 retains the v4 lean execution scope: the strategies and proof obligations below are retained. `VALIDATION_POLICY.md` controls test size/frequency; `BRANCH_AND_CI.md` controls isolation and merge boundaries. A strategy's full-workload validation means L4 on the final combined candidate, not a new 1024 run per experiment.

# Optimization strategy catalog

This catalog contains **48 exact/guarded/operational or research candidates and 8 quarantined approaches**. It is a systematic inventory of relevant transformation families, not a proof that every possible optimization has been enumerated. A listed candidate is not an implemented or verified speedup. Some families already exist in part and are explicitly marked. Do not reimplement existing work.

Read only assigned IDs. Mathematical proofs and guard requirements are in `MATH_AND_PROOFS.md`; stage and throughput accounting is in `THROUGHPUT.md`. All source identifiers resolve in `SOURCES.md`. Generic expressions below describe our cost reasoning, not benchmark results.

`first` means a small, high-value initial discriminator. `second` means dependency-ready follow-on. `conditional` requires profiling/proof evidence before implementation. `quarantined` is outside the authorized default optimization portfolio. Each admitted optimization must preserve the full existing contract on its fast domain and use the unchanged fallback elsewhere.

## Index

| ID | Candidate | Tier | Equivalence |
|---|---|---|---|
| R01 | SVF state projection and absorbing-state termination | first | guarded_exact |
| R02 | Certified non-contributing sky suffix | first | guarded_exact |
| R03 | Flat compiled hierarchy for provably irrelevant segments | conditional | guarded_exact_research |
| R04 | Hoist input-only global bush activation, then trace pixels independently | conditional | guarded_exact_research |
| R05 | Multi-state wall-shadow suffix certificate | conditional | guarded_exact_research |
| R06 | No-vegetation and uniform-region exact specializations | conditional | guarded_exact_research |
| R07 | Ray microtiles and active-lane SIMD | second | guarded_exact |
| R08 | Reuse exact schedules and complete shadow dispatch | first | guarded_exact |
| P01 | Compiled outer blocks, ordered pixel SIMD, fused visibility consumption | first | guarded_exact |
| P02 | Exact categorical partial evaluation | first | guarded_exact |
| P03 | Tile-lifetime tan(ASVF) and immutable angular factors | first | guarded_exact |
| P04 | Classification over exact distinct ASVF bit values | second | guarded_exact |
| P05 | Certified classifier threshold with uncertain-band fallback | conditional | guarded_exact_research |
| P06 | Exact visibility/classification signatures and ordered prefix sharing | conditional | guarded_exact_research |
| P07 | Fuse aniLum with compatible shortwave visibility work | second | guarded_exact |
| P08 | Reuse longwave decode and specialize identical nocturnal components | second | guarded_exact |
| P09 | Demand graph and admitted output-profile specialization | conditional | guarded_exact |
| P10 | Typed-profile specialization and optional native extension | conditional | guarded_exact_research |
| G01 | First-blocker prefix plus exact repeated-add replay | first | guarded_exact |
| G02 | Prepare owned direction-invariant sources once | first | guarded_exact |
| G03 | Fuse gather and postprocessing; retain only live receiver fields | first | guarded_exact |
| G04 | Cache five static unshadowed-albedo GVF fields | second | guarded_exact |
| G05 | Compact ordered transport descriptors, not reassociated sparse matmul | conditional | guarded_exact_research |
| G06 | Exact material/shadow emission-state tables | second | guarded_exact |
| G07 | Interior addressing fast path and exact Boolean-channel counters | second | guarded_exact |
| V01 | SVF patch consumption fusion with original annulus additions | first | guarded_exact |
| V02 | Block-local categorical/raw codec with uniform modes | second | guarded_exact |
| V03 | Intern identical payloads and uniform spatial blocks | conditional | guarded_exact_research |
| V04 | Sparse wall/aspect evaluation and exact filter reuse | conditional | guarded_exact |
| V05 | Whole-stage out-of-core execution, not smaller model tiles | conditional | guarded_exact_research |
| V06 | Geometry lifecycle reuse and efficient mandatory legacy export | second | guarded_exact |
| F01 | UTCI exact typed-DAG partial evaluation | conditional | guarded_exact |
| F02 | Evaluate terminal comfort only on valid receivers | conditional | guarded_exact |
| F03 | WBGT forcing preparation reuse without changing convergence | conditional | guarded_exact |
| F04 | Exact forcing/solar preparation grouping | second | guarded_exact |
| F05 | Load only selected directional wind planes | second | guarded_exact |
| F06 | Optional wind/input-construction common subexpressions | conditional | guarded_exact_research |
| S01 | Liveness-based memory admission with honest raw fallback | first | operational_exact |
| S02 | Persistent bounded worker processes | first | operational_exact |
| S03 | Joint worker/thread/microtile optimization | first | operational_exact |
| S04 | Memory-weighted longest-job-first tile scheduling | second | operational_exact |
| S05 | Stage-aware resource tokens and producer/consumer scheduling | conditional | operational_exact_research |
| S06 | Bounded asynchronous single-owner writer | conditional | operational_exact_research |
| S07 | Content-addressed immutable checkpoint payload reuse | conditional | operational_exact_research |
| S08 | TIFF/NPZ packing and compression tuning with schemas intact | second | operational_exact |
| S09 | Persistent JIT identity, bounded signatures and reusable scratch | second | operational_exact |
| S10 | Owned immutable input snapshots and shared verified preparation | conditional | operational_exact_research |
| S11 | Instrumented dispatch census, lean hot-path validation and evidence reuse | first | operational_exact |
| X01 | Fewer patches, pixels, timesteps or physical components | quarantined | out_of_scope |
| X02 | Horner/reassociation, generic BLAS and angular moments without a new policy | quarantined | real_equivalence_only |
| X03 | Prefix sums, integral images or FFT replacing ordered GVF reductions | quarantined | real_equivalence_only |
| X04 | Parallel time scan or closed-form thermal recurrence | quarantined | real_equivalence_only |
| X05 | Naive inverse-trig thresholds or approximate direction/ASVF bins | quarantined | not_proved_equivalent |
| X06 | Subtracting a terrain datum or replacing oblique sample sequences | quarantined | not_proved_equivalent |
| X07 | Relaxing checkpoint/hash/durability or dropping requested artifacts | quarantined | operational_change |
| X08 | GPU/remote/hardware substitution or whole-program language rewrite as proof | quarantined | out_of_scope_or_unsubstantiated |

## R01: SVF state projection and absorbing-state termination

**Tier:** first. **Class:** guarded_exact. **Relation:** extends prior R.

**Transformation.** Keep the exact first step, then project f/sh/vs/vb to building/vegetation/ever-visible Boolean state. After an ordinary step reaches building=1, vegetation=0, the final three masks are invariant to the remaining finite samples.

**Admission and failure modes.** No positive bush; no NaN/Inf or unsupported intermediate behavior; preserve initial correction and decode outputs as 1-B, 1-V, 1-(E-V). The combined output can be 2. Do not use this proof for wall-height outputs.

**Cost and crossover.** Sample ratio 1/(1-q+q*lambda), where q is original-work-weighted absorbing-ray share and lambda is the retained fraction. Add guards, branch cost and SIMD divergence. No-occlusion scenes may gain nothing.

**Smallest deciding experiment.** Capture all three original outputs, first-step-only and two-step cases, adversarial corners, negative heights, bit masks; measure retained sample counts before timing.

**Source anchors:** [S02], [S11].

## R02: Certified non-contributing sky suffix

**Tier:** first. **Class:** guarded_exact. **Relation:** extends prior suffix certificate.

**Transformation.** Bound every remaining building/canopy/trunk sample using exact stored decrements and source maxima. Retain the initial exceptional steps; stop only when the bound proves the complete visibility projection invariant.

**Admission and failure modes.** Include out-of-domain +0 padding, nonmonotone stored decrement suffix minima, dtype rounding and signed-zero effects. Use strict conservative bounds unless ties are proved. Positive-bush and wall23 require separate proofs.

**Cost and crossover.** Visits sum_x,p min(L_p, certified_cut_x,p) plus O(P*L) preparation and optional O(log L) per-pixel search. R01 and R02 share removed suffixes: combine cuts with min, never multiply gains.

**Smallest deciding experiment.** Exhaustive small actual schedules and high-datum/low-obstacle scenes; compare certificate to exhaustive original traversal and count proof failures.

**Source anchors:** [S02].

## R03: Flat compiled hierarchy for provably irrelevant segments

**Tier:** conditional. **Class:** guarded_exact_research. **Relation:** additional.

**Transformation.** Use conservative multi-resolution height bounds over the exact discrete source addresses, with a packed iterative traversal rather than Python object recursion.

**Admission and failure modes.** A bound must include boundary values and every live state update. Preserve equality operand selection and raw/nonfinite fallback. Existing oblique translated-horizon shortcuts are not equivalent.

**Cost and crossover.** B_build + N*(node_visits*c_node + evaluated_samples*c_step) < N*L*c_step. A hierarchy is useful only when enough samples are skipped to repay construction and cache misses.

**Smallest deciding experiment.** Separate building13 research from the actual vegetation23 path; full return tuples, node/sample counters and flat-terrain negative controls.

**Source anchors:** [S02], [S06], [S13].

## R04: Hoist input-only global bush activation, then trace pixels independently

**Tier:** conditional. **Class:** guarded_exact_research. **Relation:** additional.

**Transformation.** The global branch A_k=max_x([canopy_temp_k(x)>a(x)]*bush(x))>0 depends on immutable inputs and the schedule, not on f/vs/vb/g. Compute the exact flag sequence first; then replay each pixel recurrence using A_k without step-wide barriers.

**Admission and failure modes.** For finite bush, scan only bush>0 sites to decide positivity. Otherwise retain the original complete NaN-poisoning reduction. Keep all g updates and the bush tail; building absorption does not permit discarding live bush work.

**Cost and crossover.** Activation cost O(L*N_b) on the admitted sparse finite domain instead of O(L*N) global scans, plus pixel tracing. Compare added prepass cost with eliminated barriers and scans.

**Smallest deciding experiment.** Exact activation bits and final masks against the original step-major positive-bush implementation; negative/zero/nonfinite bush cases and worker-count variation.

**Source anchors:** [S02].

## R05: Multi-state wall-shadow suffix certificate

**Tier:** conditional. **Class:** guarded_exact_research. **Relation:** additional.

**Transformation.** Prove a suffix cannot increase the current building/vegetation maxima or alter canopy/trunk crossing states, including previous-step decrements; replay only the final unchanged wall calculations.

**Admission and failure modes.** Wall23 returns quantities, not just binary shadows. Its volumeveg, previous height and wall sun/shade outputs invalidate the simple SVF building-absorption rule. No admission without an all-output proof.

**Cost and crossover.** Possible O(N*L) to O(N*L_live); actual bound tightness and query overhead determine benefit. No forecast before a cut-length census.

**Smallest deciding experiment.** All wall23 outputs at exact angular boundaries and trunk/canopy gaps; compare against exhaustive traversal, never a building-only surrogate.

**Source anchors:** [S06].

## R06: No-vegetation and uniform-region exact specializations

**Tier:** conditional. **Class:** guarded_exact_research. **Relation:** additional.

**Transformation.** Specialize the executed vegetation path when exact input predicates establish absent canopy/trunk/bush or a uniform block. Eliminate only states proved observationally redundant.

**Admission and failure modes.** Calling wall13 instead of wall23 is not automatically correct: initial indices, schedule arithmetic, padding and returns differ. Keep the wall23 schedule and prove its specialized recurrence.

**Cost and crossover.** Reduces field loads and comparisons per sample; gains depend on admitted-area fraction and memory/compute bottleneck, not vegetation file existence.

**Smallest deciding experiment.** Zeros, signed zeros, absent vegetation on rooftops, negative terrain and exceptional first steps; test all original return fields.

**Source anchors:** [S02], [S06].

## R07: Ray microtiles and active-lane SIMD

**Tier:** second. **Class:** guarded_exact. **Relation:** additional.

**Transformation.** Run the original sample sequence over contiguous receiver lanes, with exclusive lane state. Batch rays/blocks to amortize launches; compact inactive lanes only if ownership/order remain exact.

**Admission and failure modes.** Irregular termination can waste vector lanes. Do not reorder samples within a receiver or infer translated-ray equivalence. Stage-global bush flags must already be established.

**Cost and crossover.** SIMD saves instruction overhead, but utilization approximately live_lane_steps/issued_lane_steps can dominate. Compare scalar early-exit versus SIMD masked execution, not only vector width.

**Smallest deciding experiment.** Generated target assembly, lane utilization, exact serial/parallel comparisons; sparse and dense obstruction workloads.

**Source anchors:** [S02], [T02], [T03].

## R08: Reuse exact schedules and complete shadow dispatch

**Tier:** first. **Class:** guarded_exact. **Relation:** partially existing; audit dispatch gaps.

**Transformation.** Reuse O(L) ray descriptors keyed by exact shape, scalar dtype/bits, family and termination policy; connect existing independent-pixel kernels to the admitted CPU budget where still serial.

**Admission and failure modes.** GVF addressing and some JIT caches already exist. Do not conflate sky and wall families, cache approximate angles, or count existing work as a new optimization.

**Cost and crossover.** Amortized preparation and startup reduction plus measured thread scaling. Larger CPU allocations are reported separately from equal-budget code improvements.

**Smallest deciding experiment.** Fresh-process JIT cache tests, schedule hashes, original outputs, same total CPU reservation across worker configurations.

**Source anchors:** [S02], [S06], [S07].

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

## G01: First-blocker prefix plus exact repeated-add replay

**Tier:** first. **Class:** guarded_exact. **Relation:** extends earlier GVF-prefix proposal.

**Transformation.** For finite binary building masks, precompute the first absorbing zero of f=min(f,b). Gather dynamic ground channels only before that blocker. Reconstruct continuing wall sums using tables A_c[n+1]=RN(A_c[n]+c), not n*c.

**Admission and failure modes.** Preserve persistent outside-slice samples, first-distance snapshots, all 16 intermediates and float32 count range. Nonbinary/nonfinite inputs and diverse per-pixel wall values retain fallback. Keep water source mutation separate.

**Cost and crossover.** Full N*D*R preparation plus T_d*N*D*(mean_prefix+h) instead of T_d*N*D*R, or skip static preparation for open scenes. O(N*D) blocker storage.

**Smallest deciding experiment.** Exhaustive short binary paths, signed-zero/subnormal finite channels, first/second distances, water and no-occlusion negative controls.

**Source anchors:** [S04].

## G02: Prepare owned direction-invariant sources once

**Tier:** first. **Class:** guarded_exact. **Relation:** extends prior G.

**Transformation.** Hoist buildings/materials, aspect radians and eligible dynamic emission/albedo fields out of the 18-direction loop, maintaining explicit immutable snapshots.

**Admission and failure modes.** The first Lup is prepared before the upstream water Tg mutation; later directions may observe changed Tg. Keep first/later snapshots or fall back. Read-only views of externally mutable arrays are not ownership.

**Cost and crossover.** Six per-direction source copies alone imply 2*6*4*N*D*T_d logical bytes. Shared preparation can reduce D-fold repetition, but memory hierarchy determines elapsed benefit.

**Smallest deciding experiment.** All original _sun/_gvf outputs and mutated Tg, aliases, water class, direction ties and fallback dtypes.

**Source anchors:** [S04].

## G03: Fuse gather and postprocessing; retain only live receiver fields

**Tier:** first. **Class:** guarded_exact. **Relation:** extends prior G.

**Transformation.** Consume gather sums in a block-local postprocessor and immediately update final total/cardinal outputs in original direction order; avoid writing 16 full intermediate planes.

**Admission and failure modes.** Keep each arithmetic/cast node, direction order, denominator conventions, keep masks and material mutation. Full intermediate tracing uses a diagnostic path.

**Cost and crossover.** Scratch O(16*N) -> O(A*B) for the affected stage; removes stores/loads but gather work may remain dominant.

**Smallest deciding experiment.** Full intermediate comparison in diagnostic mode, all state and outputs in optimized mode, changed block size, parallel ownership and maximum RSS.

**Source anchors:** [S04].

## G04: Cache five static unshadowed-albedo GVF fields

**Tier:** second. **Class:** guarded_exact. **Relation:** extends prior G.

**Transformation.** Build total/cardinal unshadowed-albedo fields in the original ordered recurrence and reuse only under complete immutable geometry/material/search-distance identity.

**Admission and failure modes.** The complete GVF radiance is dynamic and cannot be cached as geometry. Invalidation must include albedo, input bits, logical boundary, scale and algorithm profile.

**Cost and crossover.** Win when T_d*C_static > B_build + T_d*C_read. Five float32 maps cost 20*N bytes (20 MiB at 1024 squared).

**Smallest deciding experiment.** Perturb every dependency, compare exact maps and multi-day states, include first-use build time and additional memory.

**Source anchors:** [S04].

## G05: Compact ordered transport descriptors, not reassociated sparse matmul

**Tier:** conditional. **Class:** guarded_exact_research. **Relation:** additional.

**Transformation.** Represent static blocker/face events and retained sample addresses compactly, then replay original ordered dynamic contributions. Share schedules and run boundaries instead of storing N*D*R full addresses.

**Admission and failure modes.** Standard CSR/BLAS/FFT may change floating-point grouping. Preserve out-of-slice history and each term/cast. Reject huge expanded index tables that exceed saved work.

**Cost and crossover.** Construction amortization versus eliminated address predicates; O(N*D) event data plus O(D*R) shared schedules is the preferred size target.

**Smallest deciding experiment.** Count descriptor bytes, address operations and replay equivalence, including tiny tiles whose Python slices clip unusually.

**Source anchors:** [S04].

## G06: Exact material/shadow emission-state tables

**Tier:** second. **Class:** guarded_exact. **Relation:** additional.

**Transformation.** Find repeated complete material/forcing/shadow input tuples for source emission expressions. Evaluate the original typed expression once per exact tuple and scatter the field.

**Admission and failure modes.** Use exact bit keys and all temperature parameters, shadow/transmittance values and first/later water state. Do not quantize Tg or merge nearby materials. Dynamic delayed radiance is not automatically categorical.

**Cost and crossover.** Expression cost O(N*T_d) -> O(U_material_state*T_d), plus O(N*T_d) scatter; useful only with low exact-state entropy.

**Smallest deciding experiment.** Actual unique-tuple census; mixed materials, water, rare shadow states, signed zero and raw-value fallback.

**Source anchors:** [S04], [S08].

## G07: Interior addressing fast path and exact Boolean-channel counters

**Tier:** second. **Class:** guarded_exact. **Relation:** additional.

**Transformation.** Use branch-free prevalidated source offsets in the interior and the exact boundary recurrence on edges. Replace Boolean 0/1 accumulation with counters only where the float32 sequence is exactly represented, then restore the original numeric value.

**Admission and failure modes.** No halo truncation or changed logical domain. Count limits matter: repeated float32 +1 does not equal casting arbitrary large integers. Weighted emission/albedo sums cannot become count*value.

**Cost and crossover.** Interior fraction approx (max(0,n-2r)/n)^2 on square tiles; counter savings depend on loop instruction mix. Boundary-heavy tiny tiles should use fallback.

**Smallest deciding experiment.** Integer-range boundary, every edge/corner, zero/one-sample rays and exact intermediate counts.

**Source anchors:** [S04].

## V01: SVF patch consumption fusion with original annulus additions

**Tier:** first. **Class:** guarded_exact. **Relation:** extends prior geometry proposal.

**Transformation.** Prepare scalar weight sequences once, reuse patch planes, accumulate all 15 SVFs per receiver in exact patch/annulus order and encode completed visibility without retaining float cubes.

**Admission and failure modes.** Do not sum annulus weights first or multiply an accumulated weight. The builder must own captured bytes before scratch reuse; preserve directional corrections and output order.

**Cost and crossover.** Reduces O(N*P*annuli) materialization passes without changing addition count; scratch reuse and SIMD across pixels can help cold geometry.

**Smallest deciding experiment.** All 19 outputs, irregular patch tables, clipping, raw visibility, exact weight node rounding and full required exports.

**Source anchors:** [S14].

## V02: Block-local categorical/raw codec with uniform modes

**Tier:** second. **Class:** guarded_exact. **Relation:** extends codec discussion.

**Transformation.** Add versioned constant-payload and block-local binary/ternary/raw storage, or sparse raw-bit exceptions, so one exceptional sample does not force an entire patch raw.

**Admission and failure modes.** Preserve every float32 bit, reserved-code failures, signed zeros, NaN payloads and old cache/legacy NPZ interoperability. Compression may increase metadata and branch costs.

**Cost and crossover.** For raw fraction e, approximate payload categorical_bits*N/8 + e*N*exception_bytes + metadata instead of 4*N per affected patch. Evaluate actual e and decode access locality.

**Smallest deciding experiment.** Round-trip arbitrary uint32 bit patterns, sparse/dense exceptions, mapped close/read races, corrupt metadata and output schemas.

**Source anchors:** [S05].

## V03: Intern identical payloads and uniform spatial blocks

**Tier:** conditional. **Class:** guarded_exact_research. **Relation:** additional.

**Transformation.** Use hash-plus-byte comparison to share identical immutable encoded patch/block payloads or exact uniform regions; retain independent logical identities and masks.

**Admission and failure modes.** A hash is not an equality proof by itself. Do not merge nearly equal visibility or assume translated scene geometry has identical edge/solar behavior.

**Cost and crossover.** Benefit scales with duplicate payload fraction; hashing/metadata and random access can exceed storage savings. No gain expected for high-entropy scenes.

**Smallest deciding experiment.** Duplicate-byte census, adversarial collisions, serialization round-trip and real decode throughput.

**Source anchors:** [S05].

## V04: Sparse wall/aspect evaluation and exact filter reuse

**Tier:** conditional. **Class:** guarded_exact. **Relation:** existing family: only implement an identified residual.

**Transformation.** Reuse original rotated sparse filter offsets and evaluate only original wall locations. Improve layout and reuse while preserving angle order and strict score ties.

**Admission and failure modes.** A compiled sparse version may already exist. Audit before implementing; do not substitute gradient/Sobel orientations or change SciPy rotation semantics.

**Cost and crossover.** Costs scale with wall fraction and sparse filter cardinality, but filter construction and fallback-gradient work remain.

**Smallest deciding experiment.** All wall/aspect fixtures, rotation ties, no-wall inputs and exact border behavior; cold preprocessing profile.

**Source anchors:** [S14], [S13].

## V05: Whole-stage out-of-core execution, not smaller model tiles

**Tier:** conditional. **Class:** guarded_exact_research. **Relation:** additional.

**Transformation.** Keep logical geometry and state on bounded backing storage; use owner-compute receiver blocks that read the full required context and obey stage barriers. Bound physical working sets, not only decoded visibility.

**Admission and failure modes.** mmap is not a resident-memory guarantee. Long shallow rays can touch the whole domain. Never change solar location, meteorological aggregation, overlap or output extent through block size.

**Cost and crossover.** Capacity grows with active workspace rather than all tiles. Additional page faults/I/O can reduce throughput; report a capacity result separately from acceleration.

**Smallest deciding experiment.** Adversarial long rays, 2048/default-3600 or resource-limit outcomes, dirty-page/RSS measurements, cross-block state equality.

**Source anchors:** [S07], [S08].

## V06: Geometry lifecycle reuse and efficient mandatory legacy export

**Tier:** second. **Class:** guarded_exact. **Relation:** partly existing; optimize lifecycle residuals.

**Transformation.** Reuse the existing verified native geometry for repeated dates and stream legacy float32 members with bounded packing/compression work. Avoid regenerating identical immutable intermediates.

**Admission and failure modes.** Existing native cache already works. Required cold exports remain in cold timing; do not call skipped export work an exact default improvement. Verify complete dependency fingerprints.

**Cost and crossover.** Savings from avoided recomputation amortize across dates; export cost scales with the required serialized payload even when encoded native storage is small.

**Smallest deciding experiment.** Cold/warm identical contracts, stale and corrupted caches, legacy consumer round-trips, cache-hit rates and export wall time.

**Source anchors:** [S05], [S08], [S14].

## F01: UTCI exact typed-DAG partial evaluation

**Tier:** conditional. **Class:** guarded_exact. **Relation:** residual of an already compiled family.

**Transformation.** Hoist weather-only typed subexpressions for uniform Ta/RH and reuse exact repeated powers/nodes without regrouping the polynomial. Compile the pointwise remaining DAG.

**Admission and failure modes.** The Horner rewrite previously failed its frozen gate. Do not reassociate terms, replace math profiles, clamp to a different validity range or make a new UTCI approximation.

**Cost and crossover.** Stage gain bounded by the weather-only fraction; UTCI has not been established as the dominant full-run cost. Profile before prioritizing.

**Smallest deciding experiment.** Coefficient/source checksums, original term/cast behavior, adverse cancellation, missing inputs and final masks.

**Source anchors:** [S08], [S13].

## F02: Evaluate terminal comfort only on valid receivers

**Tier:** conditional. **Class:** guarded_exact. **Relation:** additional.

**Transformation.** For outputs that are replaced by a fixed invalid mask and do not feed state/neighbor calculations, compute terminal comfort only at valid receivers; scatter original invalid values.

**Admission and failure modes.** Invalid output receivers can still obstruct others and contribute model state. Never prune geometry, TMRT fields needed elsewhere, or validations based solely on the UTCI output mask.

**Cost and crossover.** Terminal comfort work scales with valid fraction v instead of 1, plus index/scatter cost. It gives no equivalent reduction in radiation or shadow work.

**Smallest deciding experiment.** All output flags, invalid-mask equality, buildings with strong neighbor effects, sentinel/nonfinite error behavior.

**Source anchors:** [S08].

## F03: WBGT forcing preparation reuse without changing convergence

**Tier:** conditional. **Class:** guarded_exact. **Relation:** additional.

**Transformation.** Reuse uniform wet-bulb input preparations and immutable scalar coefficients across equivalent timelines; fuse eligible pointwise globe/selection operations in their original typed order.

**Admission and failure modes.** Preserve array-wide stopping and iteration counts; independent per-pixel early convergence may change results. No scientific change to shade selection or pressure/temperature units.

**Cost and crossover.** Benefit depends on whether WBGT is requested and how much of its cost is repeated forcing versus spatial evaluation.

**Smallest deciding experiment.** All solver branches and convergence/failure fixtures, scalar/array inputs, missing values and original shade condition.

**Source anchors:** [S08].

## F04: Exact forcing/solar preparation grouping

**Tier:** second. **Class:** guarded_exact. **Relation:** additional.

**Transformation.** Group only tiles/dates with exactly identical complete forcing/solar-preparation keys; reuse timezone machinery and parsed meteorology while preserving per-tile location and aggregation.

**Admission and failure modes.** Same hour or same nearest station is insufficient. Include coordinates, date/UTC conventions, altitude quirks, units, averaging order, leaf schedule and optional UHI policy.

**Cost and crossover.** O(K*T) preparation -> O(U*T)+O(K) dispatch where U is exact-key count. Setup benefit can matter for many small tiles; do not assume it dominates 1024-square runs.

**Smallest deciding experiment.** DST/date rollover, distinct centroids, aggregation identities, own-met/ERA5/WRF parity and invalidation.

**Source anchors:** [S08].

## F05: Load only selected directional wind planes

**Tier:** second. **Class:** guarded_exact. **Relation:** additional.

**Transformation.** After validating the complete directional-input contract, load/mmap the direction bins actually used in the timeline and reuse them lazily under bounded ownership.

**Admission and failure modes.** Unused missing files must still produce the original validation outcome when the contract requires all 12. Preserve nearest-bin ties, wind-from convention and the existing floor.

**Cost and crossover.** Resident wind storage about 4*N*U_d instead of 4*N*12; input hashing/metadata validation costs remain. U_d=12 has no capacity saving.

**Smallest deciding experiment.** All direction bins, ties, unknown directions, missing unused files, shape/CRS mismatches and concurrent close safety.

**Source anchors:** [S08].

## F06: Optional wind/input-construction common subexpressions

**Tier:** conditional. **Class:** guarded_exact_research. **Relation:** additional.

**Transformation.** For optional wind preprocessing, reuse exactly matching rotations, connected-component geometry and morphology descriptors across directions; bound direction-worker memory and retain source APIs.

**Admission and failure modes.** Network acquisition is outside the local preexisting-TIFF target unless explicitly included. Preserve labels, boundary fill, interpolation, roughness policy and dependency isolation.

**Cost and crossover.** Only benefits runs actually requesting these workflows. Include preprocessing in the target when enabled; no credit from omitting it.

**Smallest deciding experiment.** Original optional workflow comparisons, missing dependency behavior, directional symmetry traps and actual preprocessing profiles.

**Source anchors:** [S08].

## S01: Liveness-based memory admission with honest raw fallback

**Tier:** first. **Class:** operational_exact. **Relation:** additional.

**Transformation.** Model scene, state, real encoded payloads, per-stage peak workspace, native/JIT/GDAL caches and active writers. Admit jobs by simultaneous live bytes rather than summing mutually exclusive scratch.

**Admission and failure modes.** Do not replace worst-case accounting with two observed RSS samples, ignore mmap resident pages, or simply raise the RAM limit. Include a conservative safety reserve and out-of-core fallback.

**Cost and crossover.** Can permit larger W under the same physical budget. Memory saving is a scheduling enabler, not a multiplicative kernel speedup.

**Smallest deciding experiment.** Actual allocations and process-tree memory under concurrent large/raw fixtures, bounded queue tests, failure before OOM and unchanged model outputs.

**Source anchors:** [S07].

## S02: Persistent bounded worker processes

**Tier:** first. **Class:** operational_exact. **Relation:** additional.

**Transformation.** Initialize one worker/JIT/math environment, process sequential independent tile jobs, release tile state/handles/locks after each, and reuse only bounded immutable runtime resources.

**Admission and failure modes.** No retained tile history or stale state. Avoid unsafe fork after native thread initialization; use supported process startup. Retire leaking/fragmented workers at safe job boundaries.

**Cost and crossover.** Reduces K*(import+JIT_load) to W*(import+JIT_load) plus task dispatch. Large-tile savings may be modest; compare actual startup share.

**Smallest deciding experiment.** Multiple heterogeneous tiles, cancellation, worker death, memory plateau and one-owner file lifecycle.

**Source anchors:** [S07], [T03].

## S03: Joint worker/thread/microtile optimization

**Tier:** first. **Class:** operational_exact. **Relation:** additional.

**Transformation.** Select W,H,B under one CPU/RAM budget using measured concurrency curves and disjoint tuning scenes. Explicitly account for writer/compression threads and hybrid-core behavior.

**Admission and failure modes.** W*H is a reservation, not a promise that all cores are equivalent or fully busy. Changing resources is not a same-resource speedup. No tuning on final evaluation results.

**Cost and crossover.** Ideal X=C/(p+C*s/W) before contention; actual t_tile(W,H,B) decides. Share-memory saturation and tail imbalance can reverse the ranking.

**Smallest deciding experiment.** Fixed-budget 1x8,2x4,4x2 or hardware-supported equivalents, real concurrent times, thermal/order controls and memory peaks.

**Source anchors:** [S07], [T04], [T05].

## S04: Memory-weighted longest-job-first tile scheduling

**Tier:** second. **Class:** operational_exact. **Relation:** additional.

**Transformation.** Use static input features or a calibrated cost estimator to order independent ready tiles, reducing the last slow-worker tail. Keep logical identities and final artifacts unchanged.

**Admission and failure modes.** Estimate only from tuning/calibration data. No priority policy may starve a tile, alter per-tile forcing, or bypass publication ordering requirements.

**Cost and crossover.** For heterogeneous jobs, greedy assignment can reduce makespan versus arbitrary order. Quantify idle-tail seconds; no benefit for identical jobs.

**Smallest deciding experiment.** Unequal tile shapes/heights/vegetation, deterministic output mapping, fairness, cancellation and actual full-batch makespan.

**Source anchors:** [S07], [T05].

## S05: Stage-aware resource tokens and producer/consumer scheduling

**Tier:** conditional. **Class:** operational_exact_research. **Relation:** additional.

**Transformation.** Reserve resources separately for cold geometry, simulation and export; overlap independent tile stages while maintaining per-tile chronological and durability dependencies.

**Admission and failure modes.** Token acquisition must be deadlock-free, reserve transient memory and count native threads. No model timestep reordering. Static worker simplification may be faster to implement.

**Cost and crossover.** Steady-state throughput bounded by the slowest stage capacity, min_j(m_j/service_j), with startup/drain and shared bandwidth penalties.

**Smallest deciding experiment.** Event-DAG validation, injected worker/writer failures, peak concurrent memory, no oversubscription and pipeline-drain latency.

**Source anchors:** [S07], [S08], [T05].

## S06: Bounded asynchronous single-owner writer

**Tier:** conditional. **Class:** operational_exact_research. **Relation:** additional.

**Transformation.** Overlap completed-buffer output writes with independent computation using explicit buffer ownership and a small queue; commit checkpoint cursor only after writes and required durability acknowledgments.

**Admission and failure modes.** Never overwrite a queued buffer, share writable GDAL datasets, skip readback/fsync, or silently accept writer failure. Writer CPU and buffers count toward budgets.

**Cost and crossover.** Can approach max(compute,write) rather than compute+write only when resources permit overlap. Extra copies may erase the benefit.

**Smallest deciding experiment.** Backpressure, buffer-reuse corruption, writer exception propagation, crash at each commit boundary and byte/metadata equality.

**Source anchors:** [S09].

## S07: Content-addressed immutable checkpoint payload reuse

**Tier:** conditional. **Class:** operational_exact_research. **Relation:** additional.

**Transformation.** Reuse already durable unchanged state-map payloads across generations with generation manifests referencing immutable content; write and sync only new payloads while preserving every checkpoint boundary.

**Admission and failure modes.** Object identity/read-only flags are insufficient for mutable arrays. Prove owned versioned immutability or compare content. Keep corruption verification, GC pins, fsync and atomic cursor semantics.

**Cost and crossover.** State write bytes scale with changed distinct payloads rather than all state each step; hashing may still cost O(T*N). Most beneficial for unchanged nocturnal carried maps.

**Smallest deciding experiment.** Interrupted reuse/publication/GC, content mutation, retained-reader lifetime, all state values and exact recovery at every original boundary.

**Source anchors:** [S09].

## S08: TIFF/NPZ packing and compression tuning with schemas intact

**Tier:** second. **Class:** operational_exact. **Relation:** additional.

**Transformation.** Batch writes to useful storage blocks; reuse bounded export buffers and benchmark compatible compression settings when binary layout is not an API contract.

**Admission and failure modes.** Preserve decoded pixels, metadata, filenames, bands and required cold exports. Include compression CPU and actual disk writes/reads. Do not mislabel a changed output workload.

**Cost and crossover.** Lower syscall/compression/packing overhead or physical bytes. Original float32 payload for 24x24x1024^2x10 outputs is 22.5 GiB before metadata, cache/export/checkpoints.

**Smallest deciding experiment.** Legacy reader round-trips, filesystem failure, all metadata, full end-to-end equal-output timing and writer CPU accounting.

**Source anchors:** [S09], [S11], [S14].

## S09: Persistent JIT identity, bounded signatures and reusable scratch

**Tier:** second. **Class:** operational_exact. **Relation:** partly existing; investigate residual only.

**Transformation.** Reuse verified compiled signatures and owned scratch inside persistent workers; compile unavoidable cold signatures once per appropriate cache identity and reserve JIT memory.

**Admission and failure modes.** Much JIT reuse already exists. No serial/parallel cache-key collisions, stale constants or platform-profile leakage. Warmup cost belongs inside first-use timing.

**Cost and crossover.** Eliminates residual compilation/allocations only where observed. Too many specialized kernels increase startup and instruction-cache footprint.

**Smallest deciding experiment.** Fresh-process compile-order permutations, installed-wheel source hashes, read-only caches and first-use total time.

**Source anchors:** [S07], [S12], [T03].

## S10: Owned immutable input snapshots and shared verified preparation

**Tier:** conditional. **Class:** operational_exact_research. **Relation:** additional.

**Transformation.** Where the declared mutation contract permits it, read/verify input once into an owned immutable preparation object shared by independent consumers, avoiding duplicate parse/read/derivation.

**Admission and failure modes.** Do not replace content validation by mtime or remove input-change detection. Snapshot creation is timed; current public mutation/error semantics stay authoritative. Unsupported callers retain original checks.

**Cost and crossover.** Reduces duplicate reads/computation only if snapshot/verification cost is less than repetition. A memory mapping of a user-writable file is not immutable.

**Smallest deciding experiment.** Input mutation at every validation boundary, failed snapshots, shared readers, file replacement and current exception contracts.

**Source anchors:** [S07], [S08], [S09].

## S11: Instrumented dispatch census, lean hot-path validation and evidence reuse

**Tier:** first. **Class:** operational_exact. **Relation:** additional.

**Transformation.** Collect cheap per-stage aggregate counters and validated feature flags once; avoid repeated introspection/type scans when owned inputs cannot change. Reuse source-keyed test evidence for unchanged components.

**Admission and failure modes.** Never delete validations with observable error behavior or reuse evidence after a dependency/profile change. Profilers do not run during final paired timings.

**Cost and crossover.** Reduces Python/dispatch overhead and developer/agent work. Numerical runtime and development-token savings are reported separately.

**Smallest deciding experiment.** Validation-call coverage, adversarial mutations, source/dependency hashing and profiler noninterference.

**Source anchors:** [S03], [S07], [S11].

## X01: Fewer patches, pixels, timesteps or physical components

**Tier:** quarantined. **Class:** out_of_scope. **Relation:** excluded.

**Transformation.** Coarsening, isotropic replacement, shorter arbitrary rays and vegetation simplification reduce the workload rather than optimize the same one.

**Admission and failure modes.** Requires an explicitly separate approximation product and scientific validation. Never promote as default compatibility optimization.

**Cost and crossover.** No speedup credited to the exact target.

**Smallest deciding experiment.** Keep rejection visible in the ledger.

**Source anchors:** [S11].

## X02: Horner/reassociation, generic BLAS and angular moments without a new policy

**Tier:** quarantined. **Class:** real_equivalence_only. **Relation:** excluded.

**Transformation.** Algebraic regrouping can preserve real-number equations while changing typed floating-point reductions. Previous Horner/moment experiments provide counterevidence.

**Admission and failure modes.** Default exact path disallows new reassociation/FMA/math-library substitutions. Existing frozen upstream tolerance is not permission to abandon a stronger candidate-to-candidate gate.

**Cost and crossover.** Any exploratory timing remains a separately authorized numerical-policy branch, not part of this goal.

**Smallest deciding experiment.** Retain counterexamples and prior rejected experiments; do not relax gates.

**Source anchors:** [S13], [T01].

## X03: Prefix sums, integral images or FFT replacing ordered GVF reductions

**Tier:** quarantined. **Class:** real_equivalence_only. **Relation:** excluded.

**Transformation.** Window sums can be faster over real numbers but subtraction/reordered summation generally changes float32 bits; occlusion and persistent edge samples also break simple convolution assumptions.

**Admission and failure modes.** Only a proved exact-domain specialization could leave quarantine. Integer Boolean counters within range are already covered by G07.

**Cost and crossover.** No assumed O(1) per-pixel gain in the exact policy.

**Smallest deciding experiment.** Adversarial cancellation, boundaries and occlusion counterexamples.

**Source anchors:** [S04], [T01].

## X04: Parallel time scan or closed-form thermal recurrence

**Tier:** quarantined. **Class:** real_equivalence_only. **Relation:** excluded.

**Transformation.** Affine scans/closed forms change intermediate rounding and often reset/branch behavior even when the real-valued recurrence is linear.

**Admission and failure modes.** Keep chronological state. A same-input/same-full-state memoization is possible but must replay all outputs and is not this shortcut.

**Cost and crossover.** No timeline-parallel speedup credited.

**Smallest deciding experiment.** Find typed recurrence counterexamples and midnight/delay branch changes.

**Source anchors:** [S08], [T01].

## X05: Naive inverse-trig thresholds or approximate direction/ASVF bins

**Tier:** quarantined. **Class:** not_proved_equivalent. **Relation:** excluded.

**Transformation.** Replacing a rounded atan comparison with a real-number tangent inequality can flip decisions near the boundary; angle bins/quantization change exact ray sampling.

**Admission and failure modes.** Use P04 exact-value reuse or P05 certified bounds with fallback instead. Real monotonicity is insufficient.

**Cost and crossover.** No classifier speedup credited without a machine-level certificate.

**Smallest deciding experiment.** Adjacent-float and equality tests against the pinned profile.

**Source anchors:** [S12], [T01].

## X06: Subtracting a terrain datum or replacing oblique sample sequences

**Tier:** quarantined. **Class:** not_proved_equivalent. **Relation:** excluded.

**Transformation.** Input height offsets and single-translation scan recurrences can change rounding, zero padding, termination and oblique discrete sample support.

**Admission and failure modes.** R02 proves noncontributing suffixes on original values instead. General horizon-scan reuse needs a new exact phase/sampling proof.

**Cost and crossover.** No height-range or O(N) horizon speedup credited merely from real geometry.

**Smallest deciding experiment.** Signed-zero/negative-height/oblique counterexamples and previous failures.

**Source anchors:** [S02], [S13].

## X07: Relaxing checkpoint/hash/durability or dropping requested artifacts

**Tier:** quarantined. **Class:** operational_change. **Relation:** excluded.

**Transformation.** Changing checkpoint frequency, omitting verification or exports, or weakening input identity can shorten runtime but changes the product/benchmark contract.

**Admission and failure modes.** Keep original durability and outputs by default. A user-approved optional policy is labeled and benchmarked separately.

**Cost and crossover.** No benefit counted in the equal-contract goal.

**Smallest deciding experiment.** Run failure-injection and schema checks to expose silent policy changes.

**Source anchors:** [S09], [S11].

## X08: GPU/remote/hardware substitution or whole-program language rewrite as proof

**Tier:** quarantined. **Class:** out_of_scope_or_unsubstantiated. **Relation:** excluded.

**Transformation.** Different hardware/resources or a language name alone does not establish faster local CPU execution of the same computation.

**Admission and failure modes.** Native hot kernels are allowed under P10 when justified; GPU/distributed execution needs separate scope and hardware reporting.

**Cost and crossover.** No unmeasured device/core-count multiplication.

**Smallest deciding experiment.** Record actual hardware and resource envelopes.

**Source anchors:** [S07], [T04].
