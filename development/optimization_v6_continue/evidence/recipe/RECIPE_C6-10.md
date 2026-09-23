# C6-10 — Versioned common geometry recipe (terminal evidence)

Worker: C6-10 (numerical_implementer). Worktree `/Users/alansynn/Workspace/solweig-light-v6-recipe`,
detached at `5e1fab46`, base for parity `e7a2d6ec8594b234820e7783e0ca26d821de7f3d`.
Routing: GLM via Z.ai (no other model identity claimed).

## Verdict

**COMPLETE.** All three completion gates pass. The duplicate cold geometry CONSTRUCTION is
eliminated by a shared, versioned `GeometryRecipe`; the construction/export metadata moves to a
separate export identity that never enters the native key.

## Deliverables

| Artifact | Path | sha256 |
|---|---|---|
| Recipe module (NEW) | `src/solweig_light/geometry/recipe.py` | `56cf88da32d83fa4923fc367ea3e9948888ef95c39ac593cea058c83f096b6a5` |
| Integration patch (proposal for C6-70) | `optimization_v6_continue/evidence/recipe/integration_patch_C6-10.diff` | `886c07f6c2bd00851b07a0c84209f005a23c1178ec30e2b8544f1aab61ece26d` |
| Tests (8) | `tests/optimization_v6/geometry_recipe/` | — |
| Structured evidence | `optimization_v6_continue/evidence/recipe/RECIPE_C6-10.json` | — |

`service.py`, `pipeline.py`, `identities.py`, `api.py`, `cache/*` were NOT edited (integrator-owned).
`git status` shows only owned untracked paths. No branch, commit, or push.

## Design

- `RECIPE_POLICY = 'common-numerical-geometry-v1'`. `numerical_geometry_recipe(paths, patch_option)`
  builds `geometry_identity(sources, patch_option)`, overrides `policy`, extends the implementation
  closure with fingerprints of `geometry/service.py` **and** `geometry/recipe.py`, freezes the dict
  via a canonical-JSON round-trip (plain dicts only), and derives
  `digest = sha256(canonical_json(identity))`.
- `GeometryRecipe.produce()` is the real producer (same normalization as both routes +
  `svf_calculator_compact(..., save_rasters=False)`), returning the 19 `RESULT_NAMES` fields.
- `GeometryRecipe.export_identity(construction=..., exporter_implementation=..., operation_policy=...)`
  carries construction/export provenance separately — it never enters `store.key_for(identity)`.
- `guarded_producer(recipe, check)` re-validates inputs around the production (used with
  pipeline's `InputGuard`).
- Patched `pipeline.py` keeps its trusted-legacy branch by extending a **copy** of the identity
  (`trusted_legacy=...`), never mutating the shared recipe.

## Gate 1 — source-bound bitwise parity: PASS

Real `service._producer` (route A) and the pinned unmodified `pipeline.py` producer body (route B,
with a source-line guard) vs the recipe producer, all 19 fields bitwise, on two real scenes:

- reference 35x32 scene (`tests/reference/small_original_cpu/scene`)
- 96x96 dense-urban motif from the real generator

`recipe_vs_standalone`, `recipe_vs_pipeline`, `standalone_vs_pipeline`: **19/19 bitwise equal** on
both scenes; normalized inputs (clamped tree, `trees+dem`, `trees+a`, `tree*.25+a`, bush,
amaxvalue, scale) all bitwise equal.
Evidence: `raw/parity_reference-35x32-real-scene.json`, `raw/parity_dense96-96x96-real-generator-motif.json`.

## Gate 2 — exactly one full production per cold tile: PASS

Recipe level (`test_recipe_single_production.py`): both routes through one shared recipe against one
store → **svf producer calls == 1**; second route `hit=True, producer_calls=0`; warm repeat 0
productions; exactly 1 generation on disk. Evidence: `raw/recipe_single_production.json`.

End-to-end (`test_end_to_end_single_production.py`), real `thermal_comfort` runs on real 96x96
scenes, cache enabled, C6-02 census instrumentation:

| Stage | svf calls | store consults | keys |
|---|---|---|---|
| baseline-cold (unmodified) | 2 (standalone 1 + pipeline 1) | both miss, both produce | 2 (reproduces census) |
| recipe-cold (integration simulation) | **1** | standalone miss+produce; pipeline `hit=True, producer_calls=0` | **1 shared** `7998d95e…`, disjoint from baseline keys |
| recipe-warm | **0** | pipeline consult hit | same shared key |

Output parity baseline vs recipe: `output_folder/0_0` TIFF pixels **and** bytes, SkyViewFactor TIFF,
all `svfs_0_0.zip` members, all `shadowmats_0_0.npz` visibility channels — **all bitwise identical**.
Evidence: `raw/end-to-end/end_to_end_summary.json`, `raw/end-to-end/<stage>/`.

**Scope statement (explicit):** the end-to-end stage runs the *labeled integration simulation* —
the service half is the exact `git apply` post-image of the owned diff (validated at runtime, must
differ from base); the child half is an identity-only patch (`recipe_probe`) deriving
`numerical_geometry_recipe(...).identity` exactly as the diff's `pipeline.py` section does, while
the child producer stays the **unmodified** `pipeline.py` producer that gate 1 proves bitwise
identical. Production counts on unpatched integrator code are NOT proven and follow at C6-70 once
the diff is applied.

## Gate 3 — corrupted/stale cache rejected: PASS

Real producer rebuilds in every case; nothing stale is served; rebuilt fields bitwise equal to
reference:

- `array_payload`: `svf.npy` flipped at offset 512 → rejected, rebuilt (`raw/corruption_array_payload.json`)
- `visibility_payload`: `shmat` sidecar flipped at offset 256 → rejected, rebuilt (`raw/corruption_visibility_payload.json`)
- `forged_manifest`: `patch_option` rewritten to 999 with a recomputed self-consistent digest → still rejected by the identity check (`raw/corruption_forged_manifest.json`)
- `stale_source`: `Trees.tif` content changed → rekey, old generation preserved, no stale hit, `svftotal` changed 2488 px (`raw/stale_input.json`)

## Test runs (commands and exit codes)

- `PYTHONPATH=<worktree>/src NUMBA_NUM_THREADS=2 .venv-light/bin/python -m pytest tests/optimization_v6/geometry_recipe/ -q` → exit 0, **8 passed in 21.60s**
- same env on `tests/unit/test_geometry_service.py tests/unit/test_identities.py tests/unit/test_geometry_cache.py` → exit 0, **80 passed, 2 warnings** (pre-existing zipfile UserWarnings from the cache corruption fixtures themselves)
- `… test_end_to_end_single_production.py -x -q` → exit 0, **1 passed in 16.34s**

Environment: `.venv-light` Python 3.11.16; `NUMBA_NUM_THREADS=2` before numba imports (children
additionally capped by the runtime); contended development host (8 sibling workers) — wall times
recorded only, **no timing claims**; L1/L2-small tier (<=256²); no fastmath; existing
`njit(cache=True)` policy untouched; warnings/`np.seterr` behavior preserved.

## Notes for the integrator (C6-70)

1. Apply `integration_patch_C6-10.diff` (verified with `git apply --check`).
2. If applying into a staging root with `git apply --directory <root>`, the `--include` pattern must
   match the **rewritten** path (e.g. `'*src/solweig_light/geometry/service.py'`); a non-matching
   pattern silently skips the patch with exit 0 (this bit the simulation harness).
3. The post-image fingerprints its own `__file__` for the export identity — keep the file on disk
   wherever it is loaded from.
4. `construction` now lives in the separate export identity; `standalone_implementation` is dropped
   from the native key. If a standalone wrapper fingerprint must be retained anywhere, the diff
   already supplies `exporter_implementation=content_fingerprint(__file__)` in the export identity.
