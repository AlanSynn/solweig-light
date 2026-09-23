> Worker limit: L0-L2, owned branch/worktree, no 1024/full-batch or hosted-CI run. Submit L3 requests to the single lab owner. Read `../VALIDATION_POLICY.md` for identity-based reuse; full-scale checks wait for the frozen final candidate.

# F family dossier

Load this file only for assigned F IDs. Full catalog and proof requirements are authoritative.

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

