# Optimization portfolio

Every entry is a hypothesis, not a measured speedup. E = exact execution-domain transformation; G = exact only behind proved guards; R = real-algebra/operational change, design-only without separate authorization. Priorities 1/2 are initial eligibility, 3/4 require residual evidence, 5 is fenced research. Read AUDIT_SCOPE.md before interpreting source coverage.

| ID | Candidate | Stage | Class | Priority |
|---|---|---|---|---|
| T01 | Singleton-array longwave typed fast path | daytime_longwave | G | 1 |
| T02 | Prepare a small typed execution plan | daytime_longwave | G | 1 |
| T03 | Exact finite-mask contribution tables | daytime_longwave | G | 2 |
| T04 | Compute true field radiance once per timestep | daytime_longwave | G | 3 |
| T05 | Exact ASVF equivalence classes | classification | G | 3 |
| T06 | Reuse exact classification across consumers | classification | G | 2 |
| T07 | Precompute exact tan32(ASVF) | classification | G | 2 |
| T08 | Extend private demand projection across fallback | daytime_longwave | G | 2 |
| T09 | Uniform-value representation by provenance | pointwise | G | 2 |
| T10 | Low-entropy field category coefficient evaluation | pointwise | G | 3 |
| R01 | Longwave consumer-specific predicate cache | radiation | G | 2 |
| R02 | Proven inactive-contribution skipping | radiation | G | 3 |
| R03 | Ordered aniLum block kernel | diffuse | G | 1 |
| R04 | Share diffuse decode with shortwave at a legal boundary | diffuse | G | 3 |
| R05 | Direct predicate/visibility consumption in microtiles | radiation | G | 3 |
| R06 | Reusable scratch with explicit generation ownership | radiation | G | 2 |
| R07 | Coarse dispatch with small microblocks | radiation | G | 2 |
| R08 | Compiler/layout tuning under current backend first | radiation | G | 3 |
| R09 | Exact repeated signature and prefix sharing | radiation | G | 4 |
| R10 | Remove unused private patch tables and copies | radiation | G | 2 |
| G01 | Prepared GVF at one thread | ground_view | G | 1 |
| G02 | Ground contribution prefix before first blocker | ground_view | G | 3 |
| G03 | Exact repeated-addition tables for wall contributions | ground_view | G | 3 |
| G04 | Cache static unshadowed albedo subfields | ground_view | G | 3 |
| G05 | Fuse remaining gather and postprocess storage | ground_view | G | 2 |
| G06 | Reuse exact addressing and direction constants | ground_view | G | 3 |
| G07 | Pointwise thermal-state fusion without time scan | state | G | 2 |
| Y01 | Use existing exact wall-shadow parallel paths selectively | geometry | G | 2 |
| Y02 | Separate static global bush control sequence | geometry | G | 4 |
| Y03 | Certified ray suffix pruning | geometry | G | 3 |
| Y04 | Hierarchy skipping on the actual discrete sample set | geometry | G | 4 |
| Y05 | SVF annulus accumulation fusion | geometry | G | 2 |
| Y06 | Residual wall/aspect scheduling and filter reuse | geometry | G | 4 |
| Y07 | Exact ray schedule reuse across identical calls | geometry | G | 3 |
| Y08 | Receiver packet grouping for divergence | geometry | G | 4 |
| C01 | UTCI input/output pointwise fusion | comfort | G | 3 |
| C02 | Avoid unnecessary uniform Ta and Tmrt copy planes | comfort | G | 2 |
| C03 | Wet-bulb solver work reuse/compilation | comfort | G | 4 |
| C04 | Black-globe/WBGT postprocess fusion | comfort | G | 3 |
| C05 | Exact wind forcing reuse | comfort | G | 3 |
| C06 | Optional forcing/acquisition preprocessing | optional | G | 4 |
| S01 | Effective thread accounting and one parallel owner | runtime | E | 1 |
| S02 | Joint worker/thread/microblock selection | runtime | G | 2 |
| S03 | Memory inventory from live encoded data | runtime | G | 2 |
| S04 | Bounded/lazy directional wind loading | runtime | G | 3 |
| S05 | Fuse fingerprints with required reads | io | G | 3 |
| S06 | Implementation identity manifest with complete dependency closure | runtime | G | 2 |
| S07 | Single stored-stream export validation | io | G | 2 |
| S08 | Parallel preparation, ordered artifact publication | io | G | 3 |
| S09 | Streaming checkpoint serialization | io | G | 2 |
| S10 | Reuse identical durable checkpoint payloads | io | G | 4 |
| S11 | Bounded output overlap | io | G | 3 |
| S12 | Validated preprocessing artifact reuse | preprocess | G | 4 |
| S13 | Align GDAL reservations with enforced actual cache caps | runtime | G | 2 |
| S14 | Reusable worker-static preparation and bounded JIT cache | runtime | G | 3 |
| S15 | Remove unsafe global demand coupling before thread fanout | runtime | G | 2 |
| S16 | Bounded mmap/descriptor and file-handle reuse | runtime | G | 3 |
| S17 | Demand-driven terminal computation and outputs | pipeline | G | 3 |
| S18 | Allocator/GC and import overhead investigation | runtime | G | 4 |
| H01 | Select whole CPU/GPU residency regions | heterogeneous | G | 4 |
| H02 | Device-side compact decode and ordered accumulation | heterogeneous | G | 4 |
| H03 | Keep sensitive scalar/profile math on CPU | heterogeneous | G | 4 |
| H04 | Bounded transfer/compute pipeline | heterogeneous | G | 4 |
| H05 | Unified-memory and out-of-core device scheduling | heterogeneous | G | 4 |
| H06 | New native/portable compiler only after causal coverage evidence | backend | G | 4 |
| H07 | Architecture-specific schedules behind portable contract | backend | G | 4 |
| H08 | Multi-accelerator independent job routing | heterogeneous | G | 4 |
| Q01 | Band-wise angular operator precomputation | research | R | 5 |
| Q02 | Matrix multiply or batched time contraction | research | R | 5 |
| Q03 | Convolution/prefix scan/horizon replacement | research | R | 5 |
| Q04 | Mixed precision, fast math and approximations | research | R | 5 |
| Q05 | Operational contract tradeoffs | research | R | 5 |
| Q06 | Hardware/power/affinity changes | research | R | 5 |

## T01: Singleton-array longwave typed fast path

**Transformation:** Add U-profile retaining singleton arithmetic during coefficient preparation, then consume verified scalar values in a matching compiled typed DAG. Do not change the public material function.

**Equivalence and guard:** size==1 is an admission clue, not permission for early .item(); trace every broadcast/promotion and allow different sun/shade dtypes.

**Cost and crossover:** Remove fallback dispatch and O(Td*P) full-raster Python expressions; remaining ordered work O(Td*N*P).

**Small deciding experiment:** 64/128-square landcover and no-landcover 24/48-step actual traces; count scalar/singleton/field fallback and compare every radiation/state boundary.

**Stop or reject:** Array rank or compiler math makes parity fail; keep retained reference for unproven profiles.

**Interaction:** Foundational coverage improvement; do not double-count disappearance of _operate inside this same fallback.

**Source:** S03, S04, S05, S06, S07 in SOURCES.md. **Implementation guide:** [dossiers/01_typed_longwave.md](dossiers/01_typed_longwave.md).

## T02: Prepare a small typed execution plan

**Transformation:** Resolve scalar/array promotion and input capabilities once per invocation/timestep; use a small reviewed family of kernels rather than a general compiler project.

**Equivalence and guard:** Static profile facts remain stable; dynamic values, ownership and errors stay at required checkpoints.

**Cost and crossover:** O(number_of_profiles) compilation and O(T) planning replace repeated Python type checks.

**Small deciding experiment:** Record typed nodes for real captures; compare profile signatures and intermediate bits against original helpers.

**Stop or reject:** Plan creation, specializations or cold JIT dominate savings.

**Interaction:** T01 first; no independent speedup multiplier for type checks already removed by T01.

**Source:** S06, S07 in SOURCES.md. **Implementation guide:** [dossiers/01_typed_longwave.md](dossiers/01_typed_longwave.md).

## T03: Exact finite-mask contribution tables

**Transformation:** Evaluate original ordered contribution separately for each used Boolean mask state per patch and time. Retain contribution dtype until the original accumulator addition.

**Equivalence and guard:** No pre-summing terms; unused states must not introduce warnings; preserve zero multiplication, mixed sun/shade precision and original patch order.

**Cost and crossover:** Expression evaluation NP -> C*P per timestep, with NP lookups/additions remaining; win if c_lookup<c_expression.

**Small deciding experiment:** Compare every contribution and prefix for actual U/S profiles, signed zero and guarded nonfinite paths; time table preparation too.

**Stop or reject:** Lookup traffic or branch pressure exceeds eliminated arithmetic; table state count approaches N.

**Interaction:** Evaluate after T01; two-table and one-table variants only.

**Source:** S06, S07 in SOURCES.md. **Implementation guide:** [dossiers/01_typed_longwave.md](dossiers/01_typed_longwave.md).

## T04: Compute true field radiance once per timestep

**Transformation:** For genuinely varying wall inputs, retain array coefficient preparation once, then feed field values to an ordered compiled kernel.

**Equivalence and guard:** Keep full rank/broadcast contract, ndarray promotion and alias/mutation epoch; no assumed uniformity.

**Cost and crossover:** P repeated surface expression evaluations -> one evaluation plus NP loads.

**Small deciding experiment:** Small nonuniform field cases admitted by original low-level API; compare full diagnostics separately.

**Stop or reject:** Real production never uses field profile or implementation cost cannot repay observed coverage.

**Interaction:** Not needed to fix the standard singleton case; T01 does not depend on this.

**Source:** S06, S07 in SOURCES.md. **Implementation guide:** [dossiers/01_typed_longwave.md](dossiers/01_typed_longwave.md).

## T05: Exact ASVF equivalence classes

**Transformation:** Group exact ASVF bit patterns plus every relevant input/profile and classify unique values; scatter results without quantization.

**Equivalence and guard:** Byte identity including sign and profile; hash collisions resolved by content; reject semantic changes in fallback.

**Cost and crossover:** Expensive evaluations NP -> UP, but scatter still NP; U is unique-state count.

**Small deciding experiment:** Measure U/N, grouping cost and scatter on actual landcover scenes before writing kernel.

**Stop or reject:** U near N, class construction cost or poor scatter locality.

**Interaction:** Separate from coefficient-table path already shipped.

**Source:** S27, S28 in SOURCES.md. **Implementation guide:** [dossiers/02_partial_eval_classification.md](dossiers/02_partial_eval_classification.md).

## T06: Reuse exact classification across consumers

**Transformation:** Share sun/shade masks between shortwave and longwave only when actual patch order, ASVF, angles, active mask and math profile are identical.

**Equivalence and guard:** Full-key equality; different active masks may use a proven common superset but must preserve error behavior.

**Cost and crossover:** One classification rather than two, at extra bounded lifetime/space.

**Small deciding experiment:** Capture full keys from both real consumers; count exact overlaps and live bytes.

**Stop or reject:** Different tables or stage lifetime make reuse impossible or memory-heavy.

**Interaction:** May overlap T07/R04; no NP-wide persistent mask history.

**Source:** S06, S07, S27, S28 in SOURCES.md. **Implementation guide:** [dossiers/02_partial_eval_classification.md](dossiers/02_partial_eval_classification.md).

## T07: Precompute exact tan32(ASVF)

**Transformation:** Retain one immutable field of the original tan32 result for geometry lifetime or reuse block-local values.

**Equivalence and guard:** Same input layout-sensitive math profile and guards; key includes exact ASVF bytes and implementation; do not replace atan.

**Cost and crossover:** One N-element field (~4N bytes) versus repeated block tan calls across P/T consumers.

**Small deciding experiment:** Compare exact tan output at vector tails, strides and fallback domains; include preparation/memory.

**Stop or reject:** Already cached in selected path, cache cost not amortized or profile-dependent layout changes output.

**Interaction:** Avoid counting as new if current code already reuses it in a particular route.

**Source:** S27, S28, S08 in SOURCES.md. **Implementation guide:** [dossiers/02_partial_eval_classification.md](dossiers/02_partial_eval_classification.md).

## T08: Extend private demand projection across fallback

**Transformation:** Keep only live primary accumulators in a new typed fallback replacement; full public diagnostic API remains complete.

**Equivalence and guard:** Backward liveness includes late additions, state, errors and requested traces. Omitted values are NOT_REQUESTED, not fabricated arrays.

**Cost and crossover:** Remove diagnostic-only arithmetic and writes; primary two-pass recurrence unchanged.

**Small deciding experiment:** Demand-on/off with full reference returned fields; compare TMRT and carried state.

**Stop or reject:** Value assumed diagnostic influences later state or errors.

**Interaction:** Existing scalar primary reduction already does this; new only for currently uncompiled profiles.

**Source:** S06, S07, S05 in SOURCES.md. **Implementation guide:** [dossiers/01_typed_longwave.md](dossiers/01_typed_longwave.md).

## T09: Uniform-value representation by provenance

**Transformation:** Represent known uniform forcing/material data as (value, typed-origin) and materialize only for consumers/output requiring arrays.

**Equivalence and guard:** Uniformity from immutable construction or exact validation; preserve plus-zero and add-order semantics.

**Cost and crossover:** Avoid N-size preparation/loads and temp arrays; O(N) outputs still necessary when requested.

**Small deciding experiment:** Temperature and speed construction with signed zero/UHI values, output flags and mixed-dtype profiles.

**Stop or reject:** Uniformity check costs more than reuse or shape is observable through public return.

**Interaction:** T01 applies rank-aware mechanism to a specific high-value case.

**Source:** S05, S06 in SOURCES.md. **Implementation guide:** [dossiers/02_partial_eval_classification.md](dossiers/02_partial_eval_classification.md).

## T10: Low-entropy field category coefficient evaluation

**Transformation:** Use exact material/forcing state tuples to prepare per-category expressions once; retain gather by material label.

**Equivalence and guard:** Current material map performs value-based successive replacement, not always clean ID lookup; reproduce its actual result before reindexing.

**Cost and crossover:** NF expensive evaluations -> UF+N gather, U=unique tuples.

**Small deciding experiment:** Small crafted classes with output values equal to later class IDs; exact final mapped arrays.

**Stop or reject:** Unsafe alias/value-replacement behavior or few repetitions.

**Interaction:** Do not silently fix inherited landcover mapping quirks.

**Source:** S03, S05, S06 in SOURCES.md. **Implementation guide:** [dossiers/02_partial_eval_classification.md](dossiers/02_partial_eval_classification.md).

## R01: Longwave consumer-specific predicate cache

**Transformation:** Derive sky/veg/wall/reflection four predicates once from original three channels; store up to four bits per pixel-patch for the LW consumer only.

**Equivalence and guard:** Compute original typed predicates including (1-sh)*vb; preserve original visibility/raw export. New early warnings must not appear.

**Cost and crossover:** Prepare C0; reuse if T*(decode3+predicate-code_read)>C0. Packed derived size NP/2 bytes.

**Small deciding experiment:** All binary/ternary/raw profiles, odd shapes, sign/nonfinite guards, cache corruption and 24-step amortization.

**Stop or reject:** Additional 76.5 MiB at 1024 square is not amortized, raw guard expensive or classification dominates.

**Interaction:** Not a claim of a 32x overall traffic reduction. Alternative to repeated decode, not multiplicative with R05.

**Source:** S06, S07, S19 in SOURCES.md. **Implementation guide:** [dossiers/03_visibility_and_stream.md](dossiers/03_visibility_and_stream.md).

## R02: Proven inactive-contribution skipping

**Transformation:** Skip contributions only after proving they are bitwise no-ops for each accumulator and cannot cause warnings.

**Equivalence and guard:** 0*Inf and negative zero are counterexamples; zero masks alone insufficient. Keep exact replay otherwise.

**Cost and crossover:** Visit active contributions plus guard cost rather than every possible update.

**Small deciding experiment:** Small exhaustive accumulator/sign cases and domain certificates; measure active fraction.

**Stop or reject:** Proof excludes most workload or masked branch divergence outweighs skipped arithmetic.

**Interaction:** Strictly harder than predicate caching; never implied by R01.

**Source:** S06, S07 in SOURCES.md. **Implementation guide:** [dossiers/03_visibility_and_stream.md](dossiers/03_visibility_and_stream.md).

## R03: Ordered aniLum block kernel

**Transformation:** Compile the separate diffuse patch sweep with block-owned accumulator, original patch order and typed multiply/add.

**Equivalence and guard:** Preserve LazyDiffVisibility arithmetic, channel read order, raw values and float addition.

**Cost and crossover:** O(NP) stays, Python P full-raster dispatch/materialization removed.

**Small deciding experiment:** Real dRad/aniLum traces before Kdown and shortwave; 64-256 square warm stage time.

**Stop or reject:** Stage fraction too small, new decode loses or error checkpoints differ.

**Interaction:** Independent small implementation; do not wait for native research.

**Source:** S06, S19, S27 in SOURCES.md. **Implementation guide:** [dossiers/03_visibility_and_stream.md](dossiers/03_visibility_and_stream.md).

## R04: Share diffuse decode with shortwave at a legal boundary

**Transformation:** Move or join aniLum consumption only after proving dRad is not needed before the joint region; otherwise bounded shared decode cache.

**Equivalence and guard:** Full use-def order; no change to shadows, temperature preparation or Kdown chronology.

**Cost and crossover:** Eliminate duplicate visibility read/decode; store only needed bounded fields.

**Small deciding experiment:** Exact execution trace of reads/writes plus old/new stage outputs.

**Stop or reject:** Consumer lifetime requires a full cube or would move an observable computation.

**Interaction:** R03 is safe independent fallback; this is not automatic fusion.

**Source:** S06, S27 in SOURCES.md. **Implementation guide:** [dossiers/03_visibility_and_stream.md](dossiers/03_visibility_and_stream.md).

## R05: Direct predicate/visibility consumption in microtiles

**Transformation:** Consume packed data in cache-sized pixel groups using original arithmetic, not a full-scene AoSoA conversion.

**Equivalence and guard:** Per-pixel patch order and byte-error order intact; code is new only if it differs from failed fused designs.

**Cost and crossover:** Scratch O(BP) -> O(BA)+small patch slices, plus decode arithmetic; choose via actual traffic.

**Small deciding experiment:** Compare current N9 stream, same schedule Numba, changed producer and combined region.

**Stop or reject:** Repeated per-lane bit extraction or register pressure recreates P01 regression.

**Interaction:** Do not enable old rejected env switches as the implementation.

**Source:** S08, S09, S19 in SOURCES.md. **Implementation guide:** [dossiers/03_visibility_and_stream.md](dossiers/03_visibility_and_stream.md).

## R06: Reusable scratch with explicit generation ownership

**Transformation:** Allocate bounded slots per worker/profile and initialize exactly the active ranges before reuse across calls.

**Equivalence and guard:** No stale inactive masks/tail lanes, aliasing, open owner or exception leakage; no buffer reuse before consumer completion.

**Cost and crossover:** Reduce repeated allocations/zeros at cost of stable live space.

**Small deciding experiment:** Changing active patches, alternating shapes, poisoned padding, cancellation and repeated scenes.

**Stop or reject:** Saved allocation is negligible or retained cache bloats resident memory.

**Interaction:** Existing per-call slots already exist; target cross-call and unnecessary initialization only.

**Source:** S08, S09, S05 in SOURCES.md. **Implementation guide:** [dossiers/03_visibility_and_stream.md](dossiers/03_visibility_and_stream.md).

## R07: Coarse dispatch with small microblocks

**Transformation:** Separate public block size, cache microblock and native dispatch region; move loops across Python boundary when all operations are compiled.

**Equivalence and guard:** No callback per microblock in a purported coarse kernel; enforce exact read/error and output order.

**Cost and crossover:** Calls K*T*N/B -> K*T*N/M, M>=B; scratch stays O(BP), not O(MP).

**Small deciding experiment:** Count actual calls, stage time and scratch; small/large/tail blocks and caller-requested block controls.

**Stop or reject:** Dispatch savings already achieved by N9 or required callbacks remain.

**Interaction:** Combined savings with R06 are measured together; not multiplied.

**Source:** S08, S09 in SOURCES.md. **Implementation guide:** [dossiers/03_visibility_and_stream.md](dossiers/03_visibility_and_stream.md).

## R08: Compiler/layout tuning under current backend first

**Transformation:** Inspect assembly/IR for gaps; compare lane width, unroll, coefficient hoists and locality with original ordering in Numba.

**Equivalence and guard:** No FMA/contraction/reassociation; SIMD across outputs only.

**Cost and crossover:** Gain depends on baseline SIMD efficiency, gather latency and occupancy, not vector width alone.

**Small deciding experiment:** Two bounded variants, one actual profile; assembly and wrapper measurements.

**Stop or reject:** No material residual or near-parity complexity makes maintenance unjustified.

**Interaction:** Native alternative only after this strongest B exists.

**Source:** S07, S08 in SOURCES.md. **Implementation guide:** [dossiers/03_visibility_and_stream.md](dossiers/03_visibility_and_stream.md).

## R09: Exact repeated signature and prefix sharing

**Transformation:** Memoize identical complete typed computations or identical ordered prefixes with the SAME entering accumulator.

**Equivalence and guard:** Visibility equality alone insufficient: include Lup, material, ASVF, coeffs, order and initial state.

**Cost and crossover:** UP or trie-prefix work replaces repeated NP, with hashing/gather/scatter overhead.

**Small deciding experiment:** Only census exact duplicate rate first; then tiny verified prototype if high.

**Stop or reject:** U near N or index overhead dominates.

**Interaction:** Not low rank, quantization or approximate lookup.

**Source:** S06, S07 in SOURCES.md. **Implementation guide:** [dossiers/03_visibility_and_stream.md](dossiers/03_visibility_and_stream.md).

## R10: Remove unused private patch tables and copies

**Transformation:** Audit unused Lsky_normal/cardinal setup and temporary table copies inside primary demand only.

**Equivalence and guard:** Full public diagnostic return preserved; warning/mutation/liveness analysis before removal.

**Cost and crossover:** O(P) setup and some allocations removed; small expected coverage.

**Small deciding experiment:** Complete private-vs-full projection tests and allocation counts.

**Stop or reject:** No significant measured cost; do not distract from T01.

**Interaction:** Already-shipped diagnostic elimination is baseline, not new credit.

**Source:** S07, S05 in SOURCES.md. **Implementation guide:** [dossiers/03_visibility_and_stream.md](dossiers/03_visibility_and_stream.md).

## G01: Prepared GVF at one thread

**Transformation:** Decouple invariant source preparation and bounded postprocessing from the threads>1 route gate. Use serial compiled gather when H=1.

**Equivalence and guard:** Preserve guard union, first/later water snapshot, dtype and mutation timing, alias fallbacks.

**Cost and crossover:** Same gather work with less repeated preparation/allocation; useful for W workers at H=1.

**Small deciding experiment:** H1/H2 default calls with/without landcover, water and aliases; compare every GVF field.

**Stop or reject:** Serial prepared path is slower on protected cells or changes errors.

**Interaction:** Not a blanket increase of CPU budget.

**Source:** S06, S10, S11 in SOURCES.md. **Implementation guide:** [dossiers/04_gvf_state.md](dossiers/04_gvf_state.md).

## G02: Ground contribution prefix before first blocker

**Transformation:** Precompute static first blockage index and stop ground contribution loads after f becomes zero; retain all wall-state updates or exact substitutes.

**Equivalence and guard:** Finite-safe absorption proof against actual bounds and previous-sample edge retention; zero multiplication not harmless with Inf.

**Cost and crossover:** T*N*D*R -> prepare+T*N*D*(mean_prefix+overhead).

**Small deciding experiment:** Dense/open/water adversarial rays and all 16 original intermediates.

**Stop or reject:** Open scenes have no short prefix; guard/precompute cannot repay.

**Interaction:** Conditional companion to G03, not naive break at building.

**Source:** S11 in SOURCES.md. **Implementation guide:** [dossiers/04_gvf_state.md](dossiers/04_gvf_state.md).

## G03: Exact repeated-addition tables for wall contributions

**Transformation:** Store A_c(0)=+0; A_c(n+1)=RN(A_c(n)+c), then use exact count of repeated activated contributions.

**Equivalence and guard:** Never n*c; c dtype and initial signed-zero accumulator fixed, count reproduces actual step order.

**Cost and crossover:** O(U*R) table prep versus repeated constant addition per receiver/direction.

**Small deciding experiment:** Counts at first/second search boundaries, c signs, overflow guards and mutation profiles.

**Stop or reject:** c varies per pixel so U large, or random table lookup loses.

**Interaction:** Enables legal wall continuation after G02; cannot remove all post-blocker work without proof.

**Source:** S11 in SOURCES.md. **Implementation guide:** [dossiers/04_gvf_state.md](dossiers/04_gvf_state.md).

## G04: Cache static unshadowed albedo subfields

**Transformation:** Factor only fields dependent on immutable geometry/albedo, not changing radiance or shadows.

**Equivalence and guard:** Trace full dependencies and validity key; ordered total/cardinal sums unchanged.

**Cost and crossover:** T*Cs -> Cs+T*read; need T*(Cs-read)>build.

**Small deciding experiment:** Small multi-day, changed-albedo and changed-shadow tests; setup+memory included.

**Stop or reject:** Static fraction tiny or extra five maps cost more than saved work.

**Interaction:** Never cache the full ground-view radiance.

**Source:** S10, S11 in SOURCES.md. **Implementation guide:** [dossiers/04_gvf_state.md](dossiers/04_gvf_state.md).

## G05: Fuse remaining gather and postprocess storage

**Transformation:** Use exact typed receiver accumulators through immediate postprocess before storing outputs; inspect current compiled postprocess before redesign.

**Equivalence and guard:** 16 intermediates remain observable in diagnostic route; direction order and keep-mask moment preserved.

**Cost and crossover:** Avoid intermediate write/read traffic; arithmetic unchanged.

**Small deciding experiment:** Trace all intermediates in diagnostic build and compare final fields; inspect spills.

**Stop or reject:** Already fused in selected route or oversized kernel spills.

**Interaction:** G03/current typed postprocess already shipped; only missing boundaries count.

**Source:** S10, S11 in SOURCES.md. **Implementation guide:** [dossiers/04_gvf_state.md](dossiers/04_gvf_state.md).

## G06: Reuse exact addressing and direction constants

**Transformation:** Reuse verified schedule and angle constants across directions/timesteps within exact scale/shape/profile keys.

**Equivalence and guard:** No giant ND*R address table; source boundary history and scalar rounding preserved.

**Cost and crossover:** Prepare once vs repeated setup; bounded descriptors.

**Small deciding experiment:** Pointer identity/call-count census, varied scale, original rounding boundaries.

**Stop or reject:** Current cache already covers work or descriptors dominate memory.

**Interaction:** Catalogued to prevent rebuilding an existing schedule cache.

**Source:** S10, S11 in SOURCES.md. **Implementation guide:** [dossiers/04_gvf_state.md](dossiers/04_gvf_state.md).

## G07: Pointwise thermal-state fusion without time scan

**Transformation:** Fuse updates of independent carried maps at one chronological step, keeping old source versions alive through all reads.

**Equivalence and guard:** No independent timesteps, no closed-form recurrence; snapshot aliases and original rounding/order.

**Cost and crossover:** Fewer raster temporaries/pass crossings for five directional maps.

**Small deciding experiment:** State after every 24/48 step including firstdaytime, night and restart.

**Stop or reject:** State updates differ by dtype/branch or dominate little time.

**Interaction:** Separate from GVF physics and persists same complete state.

**Source:** S05, S06 in SOURCES.md. **Implementation guide:** [dossiers/04_gvf_state.md](dossiers/04_gvf_state.md).

## Y01: Use existing exact wall-shadow parallel paths selectively

**Transformation:** Dispatch exact_13/exact_23 under measured within-tile budget rather than hardcoded serial on all compatible calls.

**Equivalence and guard:** Both wall shadow families and outputs; process-level thread masks; no nested pools.

**Cost and crossover:** Same work, shorter span until bandwidth/divergence saturation.

**Small deciding experiment:** H1/H2/H4 actual route counters and branch-safe small scene parity.

**Stop or reject:** Little scaling or phase overhead exceeds gain.

**Interaction:** Do not attribute it to source compilation; kernels already exist.

**Source:** S06, S25 in SOURCES.md. **Implementation guide:** [dossiers/05_geometry.md](dossiers/05_geometry.md).

## Y02: Separate static global bush control sequence

**Transformation:** Precompute per-step global activation from immutable shifted canopy and bush, then run a verified pixel recurrence using the control sequence.

**Equivalence and guard:** Global NaN poisoning and first-step behavior must match; sparse-any shortcut only for proven finite domain.

**Cost and crossover:** Control O(LN) may become O(LNb); reduced barriers but pixel shadow work remains.

**Small deciding experiment:** Positive-bush actual fixtures, all-negative and nonfinite edge tests, full three masks.

**Stop or reject:** Bush path rare or global control prep more expensive.

**Interaction:** Absorption shortcut for no-bush is already shipped; this is different.

**Source:** S12 in SOURCES.md. **Implementation guide:** [dossiers/05_geometry.md](dossiers/05_geometry.md).

## Y03: Certified ray suffix pruning

**Transformation:** Use suffix minima of stored decrements plus conservative height maxima to prove all remaining samples ineffective.

**Equivalence and guard:** Include zero padding, first-step correction and every output; wall quantities need separate proof.

**Cost and crossover:** Saved sample visits minus bound/search setup; no absolute-height normalization.

**Small deciding experiment:** Count provably removable suffix before implementing; low sun, negative terrain, disordered decrements.

**Stop or reject:** Few certifiable suffixes or invalid proof on vegetation/wall state.

**Interaction:** Shares saved samples with existing absorption; combine as a union, not product.

**Source:** S12, S25 in SOURCES.md. **Implementation guide:** [dossiers/05_geometry.md](dossiers/05_geometry.md).

## Y04: Hierarchy skipping on the actual discrete sample set

**Transformation:** Use flat conservative region bounds only where all exact scheduled sample updates can be proved irrelevant.

**Equivalence and guard:** Do not replace oblique discrete rays with a continuous horizon recurrence.

**Cost and crossover:** Build+bound queries+visited exact samples; upper-bounded improvement by truly pruned fraction.

**Small deciding experiment:** Small compiled prototype only after counters justify; compare original coordinates verbatim.

**Stop or reject:** Old Python hierarchy regression repeats or construction cannot amortize.

**Interaction:** Known rejected horizons/hierarchies are controls, not candidate implementations.

**Source:** S12, S25 in SOURCES.md. **Implementation guide:** [dossiers/05_geometry.md](dossiers/05_geometry.md).

## Y05: SVF annulus accumulation fusion

**Transformation:** Accumulate all required SVF fields with original per-annulus multiply/add rounding, avoiding transient full planes.

**Equivalence and guard:** Keep each annulus weight and addition sequence; no sum-weights-first substitution.

**Cost and crossover:** Same scalar arithmetic, fewer whole-raster passes.

**Small deciding experiment:** Compare all SVF fields, masks and exports at all supported patch options.

**Stop or reject:** Already optimized sufficiently or compiler/profile mismatch.

**Interaction:** Patch count and correction/clipping rules unchanged.

**Source:** S26 in SOURCES.md. **Implementation guide:** [dossiers/05_geometry.md](dossiers/05_geometry.md).

## Y06: Residual wall/aspect scheduling and filter reuse

**Transformation:** Inspect remaining setup and parallel scheduling; reuse sparse rotated filters already present, specialize only residual bottleneck.

**Equivalence and guard:** Tie order, interpolation, border exclusions, signed zeros and masks unchanged.

**Cost and crossover:** Only remaining setup/loop overhead removable; existing wall speedups are not new.

**Small deciding experiment:** Small scenes with ties/rotations and one geometry-cold medium case.

**Stop or reject:** Wall time is negligible relative to campaign budget.

**Interaction:** Do not implement Sobel or approximate aspect as optimization.

**Source:** S26, S22 in SOURCES.md. **Implementation guide:** [dossiers/05_geometry.md](dossiers/05_geometry.md).

## Y07: Exact ray schedule reuse across identical calls

**Transformation:** Cache immutable generated bounds/decrements when all source-relevant shape, dtype, scale, angles and termination limits match exactly.

**Equivalence and guard:** Same source range shape and slicing semantics, no approximate angle bins.

**Cost and crossover:** O(L) setup once per exact key; bounded byte LRU.

**Small deciding experiment:** Exact repeated and nextafter angle values, negative zero, different amaxvalue.

**Stop or reject:** Schedules unique or hashing all dynamic arrays costs more than generation.

**Interaction:** Most useful repeated scenarios; not a claim all solar schedules repeat.

**Source:** S12, S25 in SOURCES.md. **Implementation guide:** [dossiers/05_geometry.md](dossiers/05_geometry.md).

## Y08: Receiver packet grouping for divergence

**Transformation:** Group independent receivers by proven workload descriptors or compact active lanes while retaining each ray sequence.

**Equivalence and guard:** Only receiver scheduling changes; output scatter and error ordering protected.

**Cost and crossover:** Lane efficiency eta=sum(L)/(w*max(L)); include grouping/scatter costs.

**Small deciding experiment:** Actual packet-length distribution first, then exact receiver-order comparisons.

**Stop or reject:** Gather locality or scheduling destroys saved lane efficiency.

**Interaction:** Wide SIMD alone is not speedup evidence.

**Source:** S12, S25 in SOURCES.md. **Implementation guide:** [dossiers/05_geometry.md](dossiers/05_geometry.md).

## C01: UTCI input/output pointwise fusion

**Transformation:** Fuse accepted polynomial with exact wind/temperature preparation and output masking where liveness permits.

**Equivalence and guard:** Same coefficients, powers, operation ordering, vapor math and final mask; no Horner reordering.

**Cost and crossover:** O(NT) remains; reduce raster writes and reads.

**Small deciding experiment:** Known polynomial fixtures, adverse weather, masked receivers and output plans.

**Stop or reject:** Comfort fraction small or compiler instructions regress.

**Interaction:** Uniform vapor preparation is already shipped.

**Source:** S05, S23 in SOURCES.md. **Implementation guide:** [dossiers/06_comfort_optional.md](dossiers/06_comfort_optional.md).

## C02: Avoid unnecessary uniform Ta and Tmrt copy planes

**Transformation:** Compute the exact scalar zero-plus-temperature-plus-UHI expression once for UTCI; materialize only when a field consumer/writer needs it.

**Equivalence and guard:** Preserve +0/-0, two rounding steps, WBGT needs and public outputs; assigning Tmrt directly needs alias proof.

**Cost and crossover:** Several 4N-byte allocation/read/write passes per step avoided.

**Small deciding experiment:** Signed zero, UHI edge values, with/without Ta and WBGT outputs; writer ownership.

**Stop or reject:** Required outputs force same work or alias safety needs copy.

**Interaction:** Not equivalent to deleting output flags.

**Source:** S05 in SOURCES.md. **Implementation guide:** [dossiers/06_comfort_optional.md](dossiers/06_comfort_optional.md).

## C03: Wet-bulb solver work reuse/compilation

**Transformation:** Compile actual iterative kernel or reuse exact repeated forcing inputs, preserving global stop behavior.

**Equivalence and guard:** Array-wide convergence vs per-element convergence are NOT interchangeable; limits/phase unchanged.

**Cost and crossover:** Fewer dispatches or repeated identical iterations, conditional on real solver cost.

**Small deciding experiment:** Near convergence thresholds, extreme humidity, same iteration trace.

**Stop or reject:** WBGT not requested or solver setup tiny.

**Interaction:** No substitute thermal-comfort library.

**Source:** S24, S05 in SOURCES.md. **Implementation guide:** [dossiers/06_comfort_optional.md](dossiers/06_comfort_optional.md).

## C04: Black-globe/WBGT postprocess fusion

**Transformation:** Fuse hcg, globe and original shade expression in one pointwise stage retaining dtype.

**Equivalence and guard:** np.where eagerly evaluates both expressions; warnings and shade selection stay exact.

**Cost and crossover:** Reduce full-plane intermediates; no change in physical expression.

**Small deciding experiment:** Shadow .1 threshold nextafter, mixed field dtype and output metadata.

**Stop or reject:** WBGT has low usage/coverage.

**Interaction:** Separate from wet-bulb solver.

**Source:** S24, S05 in SOURCES.md. **Implementation guide:** [dossiers/06_comfort_optional.md](dossiers/06_comfort_optional.md).

## C05: Exact wind forcing reuse

**Transformation:** Reuse repeated direction/speed products keyed by original coefficient bytes and exact meteorology bits when frequent.

**Equivalence and guard:** Preserve 15-degree tie rounding, missing-direction errors and .15 floor; bounded LRU only.

**Cost and crossover:** Repeated N multiplications removed when K_unique << T.

**Small deciding experiment:** Directional ties, invalid met directions, changed file contents and repeated speeds.

**Stop or reject:** Every step unique or caching full speed fields increases pressure.

**Interaction:** S04 is memory/loading, this is dynamic arithmetic reuse.

**Source:** S05 in SOURCES.md. **Implementation guide:** [dossiers/06_comfort_optional.md](dossiers/06_comfort_optional.md).

## C06: Optional forcing/acquisition preprocessing

**Transformation:** Profile ERA5/WRF/wind-building separately; reuse exact spatial interpolation weights and immutable acquired inputs, batch authorized independent requests.

**Equivalence and guard:** Same interpolation/aggregation/timezone units and error behavior; no production credentials or new paid calls without authorization.

**Cost and crossover:** Eliminate repeated setup/remote bytes; core TIFF comparisons exclude network acquisition transparently.

**Small deciding experiment:** Local recorded fixture and labeled service mocks; real service validation separately.

**Stop or reject:** No active optional workload; do not install all extras for core optimization.

**Interaction:** Not a source-audited new speed claim; local full implementation audit required.

**Source:** S13, S17 in SOURCES.md. **Implementation guide:** [dossiers/06_comfort_optional.md](dossiers/06_comfort_optional.md).

## S01: Effective thread accounting and one parallel owner

**Transformation:** Record actual Numba pool/mask and nested native counts inside the real worker. Separate slot count from leaf threads.

**Equivalence and guard:** Do not assert thread_budget=1 means one CPU core; explicit parallel=False must stay serial.

**Cost and crossover:** Remove oversubscription or underuse, not arithmetic; budgets matched across arms.

**Small deciding experiment:** Fresh process H1/H2/H4, direct/private/public routes, CPU-time evidence.

**Stop or reject:** No scope for improvement after actual resource census.

**Interaction:** Required before all scaling claims.

**Source:** S08, S20, S06 in SOURCES.md. **Implementation guide:** [dossiers/07_runtime_memory.md](dossiers/07_runtime_memory.md).

## S02: Joint worker/thread/microblock selection

**Transformation:** Choose a small measured W,H,B portfolio within unchanged total budget; stage-specific settings if justified.

**Equivalence and guard:** Logical tile count/extent unchanged; preserve caller controls and per-process limits.

**Cost and crossover:** Throughput approximately W/(s+p/H), limited by bandwidth/RAM.

**Small deciding experiment:** 1x4 vs 2x2; 4x1 only after G01, actual admitted counts.

**Stop or reject:** Memory pressure or available cells are insufficient; no blind use-all-cores default.

**Interaction:** Do not multiply with same-core kernel parallel speedup.

**Source:** S13, S20 in SOURCES.md. **Implementation guide:** [dossiers/07_runtime_memory.md](dossiers/07_runtime_memory.md).

## S03: Memory inventory from live encoded data

**Transformation:** Reserve actual verified encoding payload, carried maps, simultaneous workspace, child native/GDAL caches and writer slots.

**Equivalence and guard:** Cold unknown remains worst-case or hard bounded streaming; no safety bypass based on observed RSS alone.

**Cost and crossover:** Capacity can permit more active jobs; memory is a constraint, not a speed multiplier.

**Small deciding experiment:** Known binary/mixed/raw fixtures and concurrent peak samples, allocation ledger and OOM fail-closed.

**Stop or reject:** Worst-case paths are not accounted or safety margin unverifiable.

**Interaction:** Existing phase admission is baseline; complete actual mode/lifetime pricing only.

**Source:** S16, S08 in SOURCES.md. **Implementation guide:** [dossiers/07_runtime_memory.md](dossiers/07_runtime_memory.md).

## S04: Bounded/lazy directional wind loading

**Transformation:** Keep mandatory inventory/shape checks and content guards, but load/map a bounded set of used direction planes.

**Equivalence and guard:** Unused corrupt rasters currently may error during eager read; preserve that validation checkpoint even if it limits I/O savings.

**Cost and crossover:** Reduce up to 12 full resident planes; I/O reduction only if same error policy is retained.

**Small deciding experiment:** Unused corrupt/wrong-shape direction and met tie fixtures; descriptor lifetime/restart.

**Stop or reject:** Equivalent eager validation consumes all bandwidth or cache misses dominate.

**Interaction:** Do not claim deferred validation is transparent.

**Source:** S05, S17 in SOURCES.md. **Implementation guide:** [dossiers/07_runtime_memory.md](dossiers/07_runtime_memory.md).

## S05: Fuse fingerprints with required reads

**Transformation:** Hash bytes while an existing required traversal reads the SAME stored byte stream, and reuse result only inside a frozen snapshot epoch.

**Equivalence and guard:** A raster-value digest is not a file-content digest; preserve every external-change detection checkpoint. mtime/size not equivalent.

**Cost and crossover:** Eliminate duplicated reads within a checkpoint, not all InputGuard checks.

**Small deciding experiment:** Same-size/mtime modifications, mutation during reads, cache handoff and publication.

**Stop or reject:** Storage snapshots/ownership do not support reuse; keep original guards.

**Interaction:** Implementation code hashes and input checks have distinct scopes.

**Source:** S14, S18 in SOURCES.md. **Implementation guide:** [dossiers/08_io_persistence.md](dossiers/08_io_persistence.md).

## S06: Implementation identity manifest with complete dependency closure

**Transformation:** Cache immutable installed source identity once per invocation and explicitly include changed _native_dispatch/profile sources in new execution identity.

**Equivalence and guard:** No underspecified cache key. Keep input guards separate; new identity version may force safe recomputation.

**Cost and crossover:** Reduce repeated source reads; prevent stale cache evidence after profile changes.

**Small deciding experiment:** Edit one imported helper and verify invalidation; installed read-only vs mutable checkout cases.

**Stop or reject:** Source mutation semantics cannot be preserved by caching.

**Interaction:** Correctness prerequisite, not necessarily speedup; identities.py currently enumerates only selected folders.

**Source:** S14, S08, S28 in SOURCES.md. **Implementation guide:** [dossiers/07_runtime_memory.md](dossiers/07_runtime_memory.md).

## S07: Single stored-stream export validation

**Transformation:** Combine CRC/schema and actual value checks during one bounded traversal of stored NPZ/TIFF data; remove import/reencode/decode loops.

**Equivalence and guard:** Check all bytes, members, metadata, raw bits, trailing data and original error priority; retained validator on ambiguous failure if needed.

**Cost and crossover:** Reduce repeated decompress/parse/encode/read traversals, include scratch and full verification.

**Small deciding experiment:** Small valid/corrupt archives, duplicates, late CRC failure, signed-zero TIFF, interrupted publish.

**Stop or reject:** Cannot preserve error/CRC contract or export stage too small.

**Interaction:** No deleting verification; no new export schema required.

**Source:** S18, S19 in SOURCES.md. **Implementation guide:** [dossiers/08_io_persistence.md](dossiers/08_io_persistence.md).

## S08: Parallel preparation, ordered artifact publication

**Transformation:** Run independent export/verification jobs in bounded private staging, then publish in required tile order.

**Equivalence and guard:** Same destination ownership, failure order, backup rollback, commit barriers; cancellation must drain owners.

**Cost and crossover:** Stage time ~ceil(K/W)*prepare + K*serial_publish, not whole-stage /W.

**Small deciding experiment:** 2-4 small distinct tiles, fail late/early, lock collisions and full artifacts.

**Stop or reject:** Disk/CPU compression saturation or ordering costs erase benefit.

**Interaction:** Geometry numerical parallel phase already exists.

**Source:** S13, S18 in SOURCES.md. **Implementation guide:** [dossiers/08_io_persistence.md](dossiers/08_io_persistence.md).

## S09: Streaming checkpoint serialization

**Transformation:** Replace BytesIO payload duplication with a bounded hashing writer producing exactly the required NPY bytes, then flush/fsync as before.

**Equivalence and guard:** Preserve array/scalar tags, endianness, Fortran order, header version, hashes, file names and error cleanup.

**Cost and crossover:** Avoid peak serialized array copy and getvalue duplication; write volume unchanged.

**Small deciding experiment:** Byte-for-byte checkpoint comparison, noncontiguous arrays, scalar signed zero and crash injection.

**Stop or reject:** np.save interaction requires seeks or hash stream differs; use verified helper/fallback.

**Interaction:** Already hashes serialized bytes, so do not claim eliminating a nonexistent file re-read.

**Source:** S15 in SOURCES.md. **Implementation guide:** [dossiers/08_io_persistence.md](dossiers/08_io_persistence.md).

## S10: Reuse identical durable checkpoint payloads

**Transformation:** Reference exact unchanged immutable payload generations or duplicate via safe link while preserving cursor commit.

**Equivalence and guard:** Same corruption checks and old-state resume; fsync, refcount/GC and failure cleanup proven. Private versioning if needed.

**Cost and crossover:** M+(T-1)*changed_fraction*M bytes vs T*M, plus hash/comparison read costs.

**Small deciding experiment:** Repeated states, corrupt previously stored payload, interrupted link/publication and deletion.

**Stop or reject:** Arrays change every step or identity verification costs dominate.

**Interaction:** No checkpoint interval reduction; design-only until compatibility proof.

**Source:** S15 in SOURCES.md. **Implementation guide:** [dossiers/08_io_persistence.md](dossiers/08_io_persistence.md).

## S11: Bounded output overlap

**Transformation:** One writer owner consumes immutable snapshots while computation prepares independent work; bounded double buffers with completion acknowledgement.

**Equivalence and guard:** Checkpoint cannot advance until required output durability; stop and propagate writer errors before dependent publication.

**Cost and crossover:** Potential steady-state max(compute,IO) instead of sum, only for actually overlap-safe region.

**Small deciding experiment:** Slow writer, injected error, two timesteps, cancellation and buffer poisoning.

**Stop or reject:** Per-step durability barrier prevents useful overlap or extra copy costs win.

**Interaction:** Device download overlap accounted in H04, not counted twice.

**Source:** S05, S15, S30 in SOURCES.md. **Implementation guide:** [dossiers/08_io_persistence.md](dossiers/08_io_persistence.md).

## S12: Validated preprocessing artifact reuse

**Transformation:** Avoid rewriting identical translated tiles only when existing contents, metadata and required side effects are fully preserved.

**Equivalence and guard:** Original clear-folder/overwrite and stale file semantics remain; no hardlink mutable input as private output.

**Cost and crossover:** Read/validate vs translate/write cost; win only with sufficient repetition.

**Small deciding experiment:** Changed affine/CRS/extent, partial folder, same data different compression and overwrite cases.

**Stop or reject:** Public preprocess must rebuild by contract; leave as separate explicit reuse mode.

**Interaction:** Not an excuse to compare cold baseline against warm candidate.

**Source:** S17, S14 in SOURCES.md. **Implementation guide:** [dossiers/08_io_persistence.md](dossiers/08_io_persistence.md).

## S13: Align GDAL reservations with enforced actual cache caps

**Transformation:** Use measured/probed effective per-process GDAL cache and explicit controlled caps consistently in admission and execution.

**Equivalence and guard:** Honor caller policy; restore process/global settings; no hidden global mutation or budget relaxation.

**Cost and crossover:** May reduce conservative over-reservation and actual cache pressure, not guaranteed runtime speed.

**Small deciding experiment:** Child GetCacheMax value, env/user caps, several processes and protected no-env behavior.

**Stop or reject:** Application cannot safely scope cap or OS effects dominate.

**Interaction:** Current planner uses physical-memory 5% default; do not merely alter estimator.

**Source:** S16, S13 in SOURCES.md. **Implementation guide:** [dossiers/07_runtime_memory.md](dossiers/07_runtime_memory.md).

## S14: Reusable worker-static preparation and bounded JIT cache

**Transformation:** Reuse expensive immutable helpers such as timezone index, import/metadata tables and compiled artifacts across independent tiles.

**Equivalence and guard:** Location-specific solar/forcing outputs remain keyed by exact coordinates/time; cache dirs require approved write-location policy.

**Cost and crossover:** Amortize imports/setup J/K; bound retained memory and stale code invalidation.

**Small deciding experiment:** Two different locations/dates/epochs in same worker, read-only install, no toolchain, cache miss/hit.

**Stop or reject:** Helper mutable/not thread-safe or process lifetime memory grows.

**Interaction:** Persistent worker pool already shipped; reuse inside it is the residual.

**Source:** S05, S20 in SOURCES.md. **Implementation guide:** [dossiers/07_runtime_memory.md](dossiers/07_runtime_memory.md).

## S15: Remove unsafe global demand coupling before thread fanout

**Transformation:** Use explicit private context or scoped ContextVar where independent tiles could share a process; otherwise keep process isolation.

**Equivalence and guard:** Public demand APIs and restoration after exceptions unchanged; no race between tile contexts.

**Cost and crossover:** Enabler for future safe scheduling, not standalone promised gain.

**Small deciding experiment:** Interleaved demand modes and exceptions, two threads, restoration assertion.

**Stop or reject:** Only process-isolated execution needed; avoid gratuitous refactor.

**Interaction:** Do not launch tile threads over process-global demand state.

**Source:** S05, S07 in SOURCES.md. **Implementation guide:** [dossiers/07_runtime_memory.md](dossiers/07_runtime_memory.md).

## S16: Bounded mmap/descriptor and file-handle reuse

**Transformation:** Retain validated owner-bound handles across related stages while closing after last reader; LRU by bytes/descriptors.

**Equivalence and guard:** Immutable content checks, close locks, inode replacement and descriptor budget honored.

**Cost and crossover:** Avoid repeated map/open/setup; page faults and resident pages still counted.

**Small deciding experiment:** Concurrent close, file replacement, repeated tiles, descriptor exhaustion.

**Stop or reject:** Long-lived maps inflate memory or undermine mutation checks.

**Interaction:** Not equivalent to zero memory usage.

**Source:** S19, S14 in SOURCES.md. **Implementation guide:** [dossiers/07_runtime_memory.md](dossiers/07_runtime_memory.md).

## S17: Demand-driven terminal computation and outputs

**Transformation:** Derive backward liveness from actual requested artifacts, public returns, state, warnings and neighbor reads.

**Equivalence and guard:** UTCI is a required pipeline output despite no obvious save_utci flag; inspect OutputPlan before pruning.

**Cost and crossover:** Remove only truly unobserved computation; bytes of required output remain.

**Small deciding experiment:** All save flags, diagnostics, WBGT, traces and resume output plans.

**Stop or reject:** Any alleged dead result is consumed by TMRT/state or error semantics.

**Interaction:** Different output plans compared separately, never hidden workload reduction.

**Source:** S05, S30 in SOURCES.md. **Implementation guide:** [dossiers/06_comfort_optional.md](dossiers/06_comfort_optional.md).

## S18: Allocator/GC and import overhead investigation

**Transformation:** Measure GC/allocation/import time before considering buffer pools, delayed imports or temporary GC policies.

**Equivalence and guard:** No blanket disable, unbounded object cache, leaked handles or global process surprise.

**Cost and crossover:** Only measured fraction removable.

**Small deciding experiment:** Allocation counters and repeated tile RSS slope, then one small controlled change.

**Stop or reject:** No meaningful evidence; defer rather than tune folklore.

**Interaction:** Numba new JIT signatures may be root cause, not GC.

**Source:** S05, S20 in SOURCES.md. **Implementation guide:** [dossiers/07_runtime_memory.md](dossiers/07_runtime_memory.md).

## H01: Select whole CPU/GPU residency regions

**Transformation:** Compare retaining geometry/predicate/state on device across multiple consumers/timesteps against best current CPU, with all boundaries.

**Equivalence and guard:** Chronology, output/checkpoint and dtype exact profile unchanged; CPU remains complete fallback.

**Cost and crossover:** Tgpu=setup+H2D+launch+kernel+D2H+sync+remaining; select regions, not fastest individual functions.

**Small deciding experiment:** Small real region, explicit device and synchronized timing plus bytes; at most one backend first.

**Stop or reject:** No GPU hardware or break-even impossible; record unavailable, do not emulate speed.

**Interaction:** Architecture study is broad; native-default N9 remains closed.

**Source:** S05, S06, S07 in SOURCES.md. **Implementation guide:** [dossiers/09_heterogeneous.md](dossiers/09_heterogeneous.md).

## H02: Device-side compact decode and ordered accumulation

**Transformation:** GPU work item owns an output; tile packed inputs, decode and consume without giant NP materialization.

**Equivalence and guard:** Original patch reduction order, two passes and raw fallback. No warp/tree sum silently.

**Cost and crossover:** Trade cheap integer work for less global traffic; report register/local-memory spills.

**Small deciding experiment:** CPU reference vs exact device intermediate states; measure decode+kernel+transfer.

**Stop or reject:** Divergence, FP64 or decoder pressure negates bandwidth savings.

**Interaction:** FlashAttention-style I/O reasoning, not borrowing its numeric guarantees or speed ratios.

**Source:** S19, S07 in SOURCES.md. **Implementation guide:** [dossiers/09_heterogeneous.md](dossiers/09_heterogeneous.md).

## H03: Keep sensitive scalar/profile math on CPU

**Transformation:** Upload trusted coefficient tables and classify on CPU initially, device runs bulk arithmetic only.

**Equivalence and guard:** Do not narrow float64 contributions before float64 add then float32 store. Device capability required for profile.

**Cost and crossover:** Small per-step coefficients vs large resident receiver state; conversion overhead included.

**Small deciding experiment:** Actual mixed sun/shade types and nonfinite predicates, fully synchronized output.

**Stop or reject:** Required FP64 unavailable/slow or coefficient masks themselves require huge transfers.

**Interaction:** MLX GPU float64 unsupported per inspected docs; backend probe must fail closed.

**Source:** S06, S28 in SOURCES.md. **Implementation guide:** [dossiers/09_heterogeneous.md](dossiers/09_heterogeneous.md).

## H04: Bounded transfer/compute pipeline

**Transformation:** Overlap independent upload/compute/download slots with explicit events and one writer.

**Equivalence and guard:** No time dependence violation, early checkpoint, mutable buffer reuse or hidden async errors.

**Cost and crossover:** Throughput approaches max(link,compute,writer) only if independently overlap-safe.

**Small deciding experiment:** Counter/accounting trace, saturation and failure/cancel tests.

**Stop or reject:** Unified bandwidth bottleneck or extra copies exceed overlap.

**Interaction:** Do not double-count S11 writer overlap.

**Source:** S15, S30 in SOURCES.md. **Implementation guide:** [dossiers/09_heterogeneous.md](dossiers/09_heterogeneous.md).

## H05: Unified-memory and out-of-core device scheduling

**Transformation:** Treat host/device unified pages as shared capacity; bounded resident regions with explicit completion and pressure reserve.

**Equivalence and guard:** No assumption zero-copy means no synchronization, allocation or page traffic.

**Cost and crossover:** Resident static+state+scratch+queues below safe capacity; bandwidth shared with CPU.

**Small deciding experiment:** Peak memory/pressure and transfer counters on actual hardware only.

**Stop or reject:** Paging, eviction or concurrent CPU access dominates.

**Interaction:** No swap-based speedup strategy.

**Source:** S16, S19 in SOURCES.md. **Implementation guide:** [dossiers/09_heterogeneous.md](dossiers/09_heterogeneous.md).

## H06: New native/portable compiler only after causal coverage evidence

**Transformation:** Compare Numba B with equivalent-layout ISPC/Highway/Dr.Jit/PoCL only if a broad residual region and new design are established.

**Equivalence and guard:** Keep N9 decisions historical; no automatic reactivation of old env switches, runtime build or user setup.

**Cost and crossover:** Application gain via Amdahl including producer/packing/adapter/init.

**Small deciding experiment:** At most one selected backend region and full adapter comparison.

**Stop or reject:** Leaf-only win or Numba B matches it; reject C.

**Interaction:** Platform and wheel maintenance must repay measured benefit.

**Source:** S21, S22, S07 in SOURCES.md. **Implementation guide:** [dossiers/09_heterogeneous.md](dossiers/09_heterogeneous.md).

## H07: Architecture-specific schedules behind portable contract

**Transformation:** Tune x86/ARM or device schedules separately behind capability-detected internal kernels; retain semantic reference.

**Equivalence and guard:** Platform eligibility and strict math versioned; public API unmodified.

**Cost and crossover:** Different schedules may improve locality/lanes; no cross-hardware speed multiplication.

**Small deciding experiment:** Named hardware only; no claims for untested OS/ISA.

**Stop or reject:** Additional dependency/packaging complexity not justified.

**Interaction:** CPU-only core must import without all accelerator extras.

**Source:** S07, S20 in SOURCES.md. **Implementation guide:** [dossiers/09_heterogeneous.md](dossiers/09_heterogeneous.md).

## H08: Multi-accelerator independent job routing

**Transformation:** Assign independent logical tiles to available CPU/GPU devices with capacity and transfer-aware queueing.

**Equivalence and guard:** Exact output mapping, publication order, state isolation and hardware scope recorded.

**Cost and crossover:** Makespan lower bound max(total capacity demand,critical chain,IO); measure shared host bottleneck.

**Small deciding experiment:** Only if deployment actually needs multiple devices; small distinct jobs first.

**Stop or reject:** No such hardware/workload or disk/link saturated.

**Interaction:** Explicit optional extension, not part of initial execution wave.

**Source:** S13, S20 in SOURCES.md. **Implementation guide:** [dossiers/09_heterogeneous.md](dossiers/09_heterogeneous.md).

## Q01: Band-wise angular operator precomputation

**Transformation:** Factor real-valued sum by common band emissivity: H[x,b]=sum_{p in b}V[x,p]w[p]; then sum_b H[x,b]E[b,t].

**Equivalence and guard:** Same real expression may differ in float32 rounding; cannot enter exact default.

**Cost and crossover:** O(TNP) -> O(NP+TNBands) for eligible terms only.

**Small deciding experiment:** Derive error bounds and profile old rejected angular moments before any separately authorized experiment.

**Stop or reject:** No authorization to change numerical evaluation; remain design-only.

**Interaction:** Potential large arithmetic saving, no bitwise claim.

**Source:** S06, S07 in SOURCES.md. **Implementation guide:** [dossiers/10_research_boundary.md](dossiers/10_research_boundary.md).

## Q02: Matrix multiply or batched time contraction

**Transformation:** Express truly linear forcing-dependent components as operator application; consider GEMM only outside state-dependent chronology.

**Equivalence and guard:** BLAS reduction/FMA order differs; time-dependent state and nonlinear masks cannot be batched blindly.

**Cost and crossover:** Higher arithmetic intensity/BLAS utilization at operator memory cost.

**Small deciding experiment:** Symbolic dependency proof plus separately authorized numeric tolerance study.

**Stop or reject:** Current exact contract or dynamic nonlinear dependencies block it.

**Interaction:** Not default GPU tensor-core permission.

**Source:** S06 in SOURCES.md. **Implementation guide:** [dossiers/10_research_boundary.md](dossiers/10_research_boundary.md).

## Q03: Convolution/prefix scan/horizon replacement

**Transformation:** Investigate only where original discrete operator and padding can be represented exactly; FFT/continuous horizons are not automatic equivalents.

**Equivalence and guard:** Prefix subtraction and reassociation alter rounding; oblique rays differ from translation recurrences.

**Cost and crossover:** Potential asymptotic reduction, but semantics usually differ.

**Small deciding experiment:** Proof before benchmark; retain original unsupported cases.

**Stop or reject:** No discrete equivalence proof or inherited failed approach repeated.

**Interaction:** Existing rejected horizon experiments are required reading.

**Source:** S12, S11 in SOURCES.md. **Implementation guide:** [dossiers/10_research_boundary.md](dossiers/10_research_boundary.md).

## Q04: Mixed precision, fast math and approximations

**Transformation:** Catalog float16/tensor cores/approximate trig/Horner opportunities only as a separate authorized numerical profile.

**Equivalence and guard:** Never weaken exact tests, patch count, ray detail or physical components by default.

**Cost and crossover:** May increase throughput but changes arithmetic contract.

**Small deciding experiment:** Separate model policy and error study, never production adoption from this packet.

**Stop or reject:** No explicit user authorization.

**Interaction:** Do not relabel approximate as exact after final-output tolerance passes.

**Source:** S06, S28 in SOURCES.md. **Implementation guide:** [dossiers/10_research_boundary.md](dossiers/10_research_boundary.md).

## Q05: Operational contract tradeoffs

**Transformation:** Fewer checkpoints/outputs, source metadata trust, approximate caches or shorter model horizon are distinct product choices.

**Equivalence and guard:** Clearly different workload, durability or validation semantics; not transparent speedups.

**Cost and crossover:** Can reduce I/O/service, comparison denominator must change explicitly.

**Small deciding experiment:** Separate authorized deployment profile only.

**Stop or reject:** Default DX/numerical/durability contract unchanged.

**Interaction:** Listed to prevent hidden shortcuts.

**Source:** S15, S17 in SOURCES.md. **Implementation guide:** [dossiers/10_research_boundary.md](dossiers/10_research_boundary.md).

## Q06: Hardware/power/affinity changes

**Transformation:** Record plugged-in power, thermal state, ISA, affinity and storage as experimental factors.

**Equivalence and guard:** Faster hardware or extra cores is not a same-budget code speedup. Do not alter user power policy automatically.

**Cost and crossover:** Changes effective resource capacity rather than same-work algorithm.

**Small deciding experiment:** Compare within matched hardware/power cells; report resource deltas separately.

**Stop or reject:** Uncontrolled conditions invalidate affected performance comparisons.

**Interaction:** Battery/AC min-time ratios are not general performance guarantees.

**Source:** S20 in SOURCES.md. **Implementation guide:** [dossiers/10_research_boundary.md](dossiers/10_research_boundary.md).
