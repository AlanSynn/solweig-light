# Locally executable work specification, not an executed campaign

## Authority and branch

Use the user's verified S10 facts. Do not restart S10 or re-derive its baselines.
Read the local `SEMANTIC_CONTRACT.md`, current product source and the exact existing
S10 harness entrypoints. Their contents are not available to the author of this
handoff; no replacement public API or guessed function signature is supplied.

Main `b3e5ca59` and the closed S10 source/evidence are read-only. Resolve full
`c245ea60` and the current `perf/s10-semantic-systems` tip locally. Create one new
local follow-on branch, for example `perf/s11-headroom`, from that S10 tip. If it
already exists, audit its base and work rather than resetting it. Detached worker
worktrees must start from immutable SHA. Never revive archived branch names.

Write a new follow-on register and decision files. Do not update S10's
FINAL_DECISION.json, MERGE_MANIFEST.json, closure records or existing REGISTER.
Snapshot protected file hashes before running tests, including hooks that may write
historical evidence. Run any such hooks against an isolated evidence location or
scratch copy, not the closed campaign. No push/PR/main merge/release/history rewrite.

## Phase-0 freeze

Bind the protocol template before ANY performance timing:
1. Resolve current candidate and read-only reference to full SHAs; inventory the
   allowed product closure (src, compatibility package, packaging and dependency locks).
2. Verify there are no pre-diagnosis product changes against c245ea60. Evidence-only
   commits are allowed on the new branch.
3. Resolve corpus manifest e2c7fa847223bb21 to its full digest, hashes, ordered tile IDs,
   actual raster windows, scale, vegetation/material profiles, and timestamps.
4. Reuse the real S10 allocation's memory/resource request after reading it. No
   guessed memory budget or unbounded login-node work. Keep the configured partition,
   account and QoS: cpu-medium / gts-hoh68 / inferno.
5. Record exact existing harness commands, environment, bootstrap/setup, timing start
   and stop, CPU affinity, effective threads, cache/JIT state, outputs, checkpoints,
   exclusion rules and one causal retry limit. Freeze the record hash.

Protocol order: paired AB/BA alternation across declared cells, one measured pass
per arm per cell. A warm-up is untimed and explicitly listed; JIT warmth is not OS
page-cache coldness. One causal retry is allowed only with cause and amendment
recorded before retry results. Retain failed and aborted results.

Instrumented attribution and uninstrumented benchmark times are distinct. Tiny
profiling checks must not be used to announce target speedups. No cProfile-heavy
run is a performance baseline. Do not subtract independently selected minima.

## M1: intra-SVF attribution

Use one declared 1024² tile, with the production patch table, geometry and physical
scale. Within an isolated diagnostic runner, trace the existing public workflow
without replacing numerical outputs. Collect nonoverlapping categories:

- ray schedule preparation;
- native pixel recurrence (no-bush vs bush path separately);
- ordered field/annulus accumulation;
- compact visibility encoding;
- native cache read/write and verification;
- legacy TIFF/ZIP/NPZ generation;
- stored artifact validation and publication;
- process start/join and unexplained residual.

Native Numba internals cannot be reliably split by adding Python wrappers to an
already-bound compiled function. Use the actual call boundaries or a separately
labelled diagnostic clone that only adds timers, then compare outputs with an
unmodified run. No per-pixel timers. Record observer cost and route coverage.

Record child CPU service separately from parent phase walltime. Across concurrent
workers, sum(service) is not makespan. A one-tile breakdown must be placed in the
actual K=24 worker-wave/export timeline before it supplies a production e fraction. Publish e=nonaccelerated SVF fraction only
for a stated acceleration candidate; export cannot be counted as pixel work.

## M2: run attribution and boundary completion

Use the existing real runner with the same complete requested output/checkpoint
policy, first a representative 24-step timeline and then a declared 1-step case.
Capture exact boundaries for initialization, solar/forcing, wall13/23, GVF, Kside,
Lcyl, aniLum, Lside, Perez, UTCI, writer, checkpoint, input checks and residual.
Distinguish per-stage exclusive time from cumulative descendants. Preserve state,
mutations and complete output consumption. Count fallback and native dispatch
routes so dead experimental paths cannot explain timings.

Verify whether S10 supports a real one-step public invocation. If initialization
requires two met records, do not alter that contract. Use a valid existing execution
window if supported; otherwise label the short kernel replay separately and leave
one-step public timing unsupported. Do not call a two-output run one step.

Expose actual UTCI fraction u and q=calc/run. The prior kernel percentages are
inside calc and must not be directly treated as whole-run fractions.

## M3: exact schedule census

Call the existing `ray_schedule` using real normalized amaxvalue, scale, dtype and
all 153 altitude/azimuth pairs. Hash the actual schedule arrays. Collect steps per
patch, aggregate pixel-sample upper bound, bounds shape, padding, dtype, daylight
profile and bush predicate. Schedule length does not equal executed work where an
existing exact early exit fires; count those separately in one diagnostic pass.
Do not use inferred lengths or N*P alone as measured DRAM bytes or an error bound.

## M4: SVF serial/parallel decision

Call the already-present serial and parallel twins on the same captured inputs,
without changing product dispatch. Use the 1- and 8-thread requested configurations
and report actual Numba mask, layer, affinity and worker process ID. Compile the
needed specializations in the declared untimed warmup. Cache and source identities
must match the timing regime.

Compare all three visibility channels and all completed SVF fields. Ordinary
np.array_equal is NOT bitwise comparison: it equates +0/-0 and treats NaNs specially.
Compare shape/dtype and bytes or matching unsigned views; apply the frozen NaN
payload policy. Cover no-bush, positive bush, boundaries, low altitude, nonfinite
fallback and first-step semantics on small adversarial inputs before target shape.

The positive-bush route still needs its global predicate and step barriers. More
threads do not authorize parallel patch accumulation into shared output arrays.
Measure the complete SVF stage as well as the pixel kernel. At fixed 24-CPU budget,
verify that 3 concurrent H=8 workers do not erase single-tile scaling.

## M5: UTCI serial/parallel decision

Capture genuine uniform UTCI inputs from the same timestep and current numerical
profile. Compare the existing serial and parallel variants. Preserve polynomial
and cast order, no fastmath, wind floor and invalid output masks. Test small and
1024² arrays and actual H. If the whole-chain infinite-speed ceiling 1/(1-u) is
small, report that limit and avoid an extended tuning campaign.

## M6: content checks and serialization

Measure content_fingerprint and InputGuard at their actual call sites. Report files,
bytes, walltime, and whether calls are same-checkpoint or different mutation epochs.
No `(mtime,size)` shortcut in an exact candidate: the included counterexample shows
it misses changed contents. Reusing an immutable digest needs a proof of ownership
and unchanged observation boundary, or an explicit integrity-policy amendment.

Do not assume BytesIO.getvalue copies its entire buffer on the installed interpreter.
Measure allocation and serialization self-time; record CPython version. For a new
stream writer, compare complete NPY payloads and state types and preserve flush,
fsync, directory, commit and error ordering. Checkpoint-frequency changes require
explicit user sign-off, not a benchmark option silently changed between arms.

## Phase 1 only after an attribution report

Candidate S: wire existing exact parallel shadow route at the narrow dispatch.
Guard by valid domain, requested/effective budget, measured size crossover and
existing no-bush/bush semantics; keep `SOLWEIG_LIGHT_SVF_SHADOW_PARALLEL=0` as the
requested exact serial kill switch. Resolve it once per invocation, not per pixel.
Use a fixed predeclared policy from development cells; held-out cells test it.

Candidate U: same for existing UTCI parallel route, when M2/M5 justify service.
No change to ordered comfort arithmetic. Default one-thread use remains one thread.

Candidate F: bounded exact fixed-cost changes shown material by M2/M6. Hash trust
relaxation is not included. No blanket context-manager removal.

Candidate A: use audited post-S03b admission to enumerate W,H and memory reservations.
First compare at most two viable shapes plus incumbent, not a giant parameter grid.
All choices use the same allocated CPU/RAM and output contract. H=1 multiple workers
is distinct from an H=8 kernel; do not combine their ideal gains multiplicatively.

If M1 accumulation is material, preserve per-accumulator patch/annulus order in a
pixel-owned fused loop before considering any tier-2 reordered sum. Frozen
C5/C6/N8/N9 kernel interiors require separate causal authorization to amend.

## Envelope and verdict

Each requested corner gets a row with measured/derived/hypothetical/unavailable
status. Small 16² and 32×35 have separate 1/24/48-step cases; large 256²/1024² have
1/24; 72+ synthetic timelines use correct timestamps and full carried state. No
assumption that one hour's solar workload equals the 24-hour mean. Serial shipped
and best admissible parallel are separate measurements. Large multi-day campaigns
are not silently claimed from scaling arithmetic.

Current-main b3e5ca59 remains a historical read-only comparator. Follow-on speedup
uses c245ea60. Never multiply old 1.314×, 2.96× or 1.074× results across different
cells. Original SOLWEIG-GPU is a third evidence class, not the follow-on baseline.

The 83 canonical S10 tests are run in their known order when justified by the product
diff, plus new tests. Missing tests/references or malformed archives are unavailable,
not successful. Raw artifacts remain outside git; commit distilled manifests and
hashes. Archive with the user's existing dbxcli setup, absolute paths and SHA-256
sidecars; do not expose credentials or fabricate upload verification.

Stop after measured candidate selection or a scoped no-material-headroom verdict.
Do not manufacture approximation: tier 3 starts only with explicit later user
approval, new budgets and conservative per-pixel/state propagation evidence.

## Delegation without repeated status checks

Parallel work: one measurement/inventory owner; one proof/test owner for shadow and
UTCI; one persistence reviewer; one integrator. Additional bounded reasoning tasks
are allowed, not required. One writer per file scope. Benchmark allocations are
exclusive to a single evidence owner. Use completion events rather than periodic
transcript polling. Author and reviewer differ. The coordinator does not rerun
identical accepted tests only for reassurance. No independent review is claimed
until an actual separate reviewer has produced a result.
