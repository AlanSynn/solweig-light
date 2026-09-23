> Worker limit: L0-L2, owned branch/worktree, no 1024/full-batch or hosted-CI run. Submit L3 requests to the single lab owner. Read `../VALIDATION_POLICY.md` for identity-based reuse; full-scale checks wait for the frozen final candidate.

# G family dossier

Load this file only for assigned G IDs. Full catalog and proof requirements are authoritative.

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
