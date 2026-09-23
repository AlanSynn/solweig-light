> Worker limit: L0-L2, owned branch/worktree, no 1024/full-batch or hosted-CI run. Submit L3 requests to the single lab owner. Read `../VALIDATION_POLICY.md` for identity-based reuse; full-scale checks wait for the frozen final candidate.

# V family dossier

Load this file only for assigned V IDs. Full catalog and proof requirements are authoritative.

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

