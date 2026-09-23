> Worker limit: L0-L2, owned branch/worktree, no 1024/full-batch or hosted-CI run. Submit L3 requests to the single lab owner. Read `../VALIDATION_POLICY.md` for identity-based reuse; full-scale checks wait for the frozen final candidate.

# R family dossier

Load this file only for assigned R IDs. Full catalog and proof requirements are authoritative.

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

