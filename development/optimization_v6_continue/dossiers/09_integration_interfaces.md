# D09: keep integration narrow and reviewable

## Private interfaces to agree before workers edit

1. `GeometryRecipe`: immutable numerical dependency identity + normalizer/producer configuration; no GDAL dataset, mutable global, forcing or export destination in payload. Source dependencies complete; export operation provenance separate.
2. `GeometryHandle`: reuse existing validated fields/mapping lifetime. Explicit owner closes it only after consumers finish. Cross-process transfer is a cache key/path with validation, not a pointer.
3. `RadiationDemand`: private full-diagnostic versus admitted cylinder-anisotropic pipeline requirement. Public functions continue full returns; no placeholder diagnostic arrays.
4. `PreparedVisibility`: only recognized immutable owners, field/layout/profile descriptors, stable lock lifetime and complete fallback. No implicit full-cube conversion.
5. `PreparedGVFStep`: read-only snapshots before/after water mutation plus proven invariant expression results. Owner is one step; not a static radiance cache.
6. `PhaseJob`: stage, original tile order, source paths, normalized runtime and output destination identity. JSON-safe references only. Existing public methods retain signatures.
7. `MeasuredRun`: spatial manifest, source/wheel/profile, requested/effective/admitted resources, cache regime, timer boundaries, outputs/state checks and outcome. This is not just one elapsed float.

Names are proposed private interfaces, not mandatory class proliferation. Existing dicts/handles can carry the same clear ownership without abstraction overhead. Prefer a small shared helper over copying the whole engine or framework.

## Shared-file authority

Integrator alone changes api.py, pipeline.py, engine.py shared dispatch, identities.py policy and central runtime/public-schema wiring. A family worker can supply a minimal patch recipe for these paths while implementing its private module and tests. If an independent alternative needs those files, work in a separate detached tree; never merge it by copying an entire file over newer changes.

Source identities may include shared modules; changing a wrapper can invalidate caches. Initially be conservative and account for cold rebuilding. Do not narrow a dependency closure only to make a benchmark warm. New internal diagnostic-demand fields must not alter public RuntimeOptions.as_dict or seven public signatures without explicit scope.

## Integration ordering

Common recipe -> phase-precompute integration. Lside narrow specialization -> private core demand dispatcher -> reduced cylinder longwave. GVF expression preparation -> typed postprocess -> optional fused local storage. Decoder preparation -> channel batching -> optional aniLum reuse. Stored export verification may proceed independently of ray math but meets recipe/export-interface changes at integration.

Actual numerical kernels and ordering changes stay separate from profiler/harness patches. Checkpoint/serialization policy stays untouched unless its own task was selected. A code cleanup with no measurable benefit should not delay useful optimized commits.

## Acceptance bundle per patch

Immutable base/candidate commit/tree or scoped diff hash, typed proof record, recognized/fallback domains, actual commands/exit status, reference source IDs, exact comparison data, measurements with class/cache/resources, independent reviewer identity and unresolved items. Do not infer model identity from reviewer text; use route record.

A reviewer can reject this plan's proposed proof. Preserve a counterexample and fallback, not a false implementation. Combined source must pass affected small interactions before performance promotion. On later integration changes, reuse evidence only for unaffected closures.
