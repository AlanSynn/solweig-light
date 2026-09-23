# D02: compute geometry once without trusting legacy caches

## Source evidence and performance hypothesis

`prepare_geometry_exports` starts from geometry_identity(paths, patches), appends construction and standalone implementation fields, then calls GeometryStore.get_or_create. `_run_tile` uses the unextended geometry_identity unless legacy_cache_policy explicitly requests trust. GeometryStore.key_for hashes the complete identity. Therefore the two lookup keys differ on the current source. Both producers call svf_calculator_compact on apparently equivalent normalized arrays. [S05-S08]

The cold full workflow calls standalone SVF before simulation. If both native keys are initially absent, source structure predicts two complete geometry constructions. This is a stronger optimization candidate than micro-tuning a ray loop: remove one complete duplicate. Confirm actual call counts on tiny real TIFFs first.

Let one construction cost G, required exports/validation cost E, other setup I and simulation S:

    T_old = 2G + E + I + S
    T_new = G + E + I + S + Delta_validation
    speedup = T_old / T_new

If the removed duplicate accounts for fraction f of old total and added overhead is delta, speedup is 1/(1-f+delta). A 20% duplicate fraction would imply 1.25x only in this assumed isolated decomposition. Do not measure f with a geometry-warm census. Worker-level overlap and native cache I/O can change it.

## Equivalence proof and guard

Compare both preparation functions node by node, including:

1. Read single-band raster values with the same float32 conversion and same metadata checks.
2. Clamp negative tree values in the same place; preserve NaN comparisons.
3. tree+DEM and tree*float32(.25)+DEM, then the original bush expression.
4. tree+buildingDSM and trunk+buildingDSM, then exact equality-to-DSM zeroing.
5. identical amaxvalue maximum semantics, scale scalar dtype/value and patch option.
6. identical compact SVF producer, output name mapping and all 19 results (16 arrays plus three visibility channels).
7. branch, first-step, signed-zero/nonfinite and raw-codec behavior.

Do not assume mathematical equivalence proves arbitrary read-error equivalence: standalone template handling and pipeline input validation differ. Keep public input validation at its existing phase. Restrict shared numerical preparation to the admitted common normalized domain; malformed or differing profiles retain their original path until separately proven.

## Recommended implementation

Introduce a small private `geometry/recipe.py` or equivalent shared producer, NOT another public API:

    recipe = make_numerical_geometry_identity(paths, patch_option, profile)
    handle = GeometryStore(...).get_or_create(recipe, common_producer)
    export_identity = {
        'numerical_recipe': digest(recipe),
        'export_schema': schema,
        'exporter_implementation': complete_export_dependency_identity,
        'operation_policy': original_overwrite_and_presence_policy,
    }

Both standalone and pipeline use the same numerical recipe. Their operational manifests may differ and remain separate. The numerical key must include all true normalization/geometry/profile dependencies. Initially keep a conservative closure containing both wrapper hashes if that is safer; dependency-pruning can be a later separately proved warm-cache optimization.

Use a new cache identity/schema policy version. A key equality assertion must be accompanied by producer equivalence tests. Never remove identity fields globally just to manufacture a cache hit. Never relabel old payloads with a new expected identity or copy a candidate hash into a reference. Old caches may remain on disk; preserve reader ownership. Recompute one verified new generation when necessary and include it in first-use accounting.

Prefer a read-only mapped shared native representation; do not carry 24 scenes in a parent Python object. Parent and child processes open validated handles from the same cache root. A path/key reference is transferable; a GDAL dataset or borrowed mmap view is not a safe process message.

## Contracts that must not change

- Standalone `calculate_svf` still produces all promised ZIP/NPZ/TIFF artifacts.
- Existing complete export sets follow original validate_existing/overwrite behavior. Partial/stale/corrupt cases preserve original files or raise as before.
- The default `legacy_cache_policy='recompute'` remains: a validated dependency-addressed native hit is not trust of identity-less legacy files.
- `save_svf` is cache-presence dependent in the pipeline. Do not change the order of standalone exports simply to save work; this can change whether SVF_<tile>.tif appears.
- InputGuard detects content mutation at existing required boundaries. A common cache key does not waive input stability.
- A corrupt numerical cache is rebuilt from the real producer under ownership, not replaced by a convenient legacy artifact.
- `cache_enabled=False` must remain meaningful. Initially retain its prior path even if it produces twice; do not silently persist data. A run-scoped ephemeral transfer is separate work with its own budget and behavior proof.

## Minimal code/test sequence

A. Add a test that wraps the actual producer, runs tiny cold thermal_comfort, records keys/calls and validates real outputs. No numerical mock.
B. Differentially compare standalone/pipeline normalized inputs and all output fields on open, dense, vegetated, negative-height, signed-zero and guarded nonfinite scenes. Preserve original unsupported failures.
C. Add common producer/key and retain separate export identity.
D. Assert one real production per admitted cold tile, zero on a validated warm repeat. Compare old and new small whole-pipeline outputs/state/artifact presence.
E. Perturb every dependency: tree/DEM/DSM data and metadata, scale, patch table, profile and implementation. Confirm misses. Corrupt payload/manifest and test mutation during preparation. Exercise simultaneous cache readers/producers and overwrite=False failures.
F. Count saved production and native generations; time the entire small cold pipeline including required exports, validation and cache creation.

Do not combine this initial patch with phase parallelism. Its before/after comparison should make the duplicate elimination directly attributable.
