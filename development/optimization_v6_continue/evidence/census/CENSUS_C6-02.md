# CENSUS C6-02 — cold geometry producer/key census (commit e7a2d6ec)

Evidence owner: GLM-5.3 (Z.ai) evidence_owner agent. Machine-readable twin: `CENSUS_C6-02.json`.
Raw per-process events: `raw/cold-warm/<stage>/{parent,child}-<pid>.jsonl`, `raw/cache-disabled/...`.
Test: `tests/optimization_v6/geometry_census/test_cold_producer_counts.py` (2 passed, 21.23s) with `census_probe.py`.

## Verdict

**Hypothesis CONFIRMED.** One cold public `thermal_comfort` run on a real 96x96 own-met TIFF scene constructs geometry **twice** — one production per route — under **two distinct keys at the same store root**, despite bitwise-identical normalized producer inputs and outputs.

- Cold: `svf_calls = 2` (standalone 1 in parent, pipeline 1 in tile-worker child), `get_or_create = 2`, both miss (`hit=False`, `producer_calls=1` each).
- Keys (same cache root `<preprocess>/.solweig-light/cache`):
  - pipeline (bare `geometry_identity`): `b5453f0026364e9ff5362b01eb7c2a0a2b7f06f46ee8aab0f4da67a8a264ad98`
  - standalone (extended identity): `e7ae9597ff67236055719a47b7d0c11262c74ca92cc8083721f7487ae62d279b`
- Identity diff: `only_in_standalone == ['construction', 'standalone_implementation']`; `only_in_pipeline == []`; `differing_shared_fields == []`. Exactly the two extensions at `geometry/service.py:281-282`.
- On disk: **two** complete native generations (one per key), each 19 arrays + 3 packed visibility channels + manifest — the physical duplicate.
- Equivalence: **bitwise-identical-normalized-inputs-and-outputs** — `a`, `vegdem`, `vegdem2`, `bush` (dtype+shape+sha256 equal), `patch_option`/`amaxvalue`/`scale` (float hex equal), all 19 outputs fingerprint-equal. The two producers are numerically interchangeable; only the key strings differ.

## Warm / cache-disabled counts

| run | productions | get_or_create | key_for | note |
|---|---|---|---|---|
| cold (defaults) | 2 | 2 (both miss) | 2 | double construction |
| warm, faithful repeat | 0 | 1 (hit) | 1 | standalone route never reached the store: api short-circuits `prepare_geometry_exports` when all 3 export files exist |
| warm, exports+manifest deleted | 0 | 2 (both hit) | 2 | both routes consult native store; exports regenerate from cache — zero productions |
| `cache_enabled=False` | 2 | 0 | 0 | deliberate fallback double-production; **nothing** persisted under `.solweig-light/cache` (only the promised legacy export-manifest control files) |

## Duration sketch (census durations, NOT benchmark)

Single 96x96 runs on a shared machine; labeled accordingly in both files. Any timed comparison must use the C6-01 isolated-child harness.

- cold total ≈ 6.91 s; each geometry production ≈ 0.39 s (×2); exports ≈ 0.13 s
- warm faithful ≈ 3.94 s; warm native-only ≈ 4.24 s (exports ≈ 0.12 s); cache-disabled ≈ 5.15 s (0.37 s + 0.37 s productions)

On this tiny scene preprocessing+walls+simulation dominate, so the removable fraction f looks small here; f grows with scene size and tile count. The duplicate is a fixed extra G per cold run per scene, exactly the `T_old = 2G + E + I + S` term of dossier 02.

## T3 — field audit for C6-10 (base builder `identities.py:40-59`)

| field | cite | class | verdict |
|---|---|---|---|
| `math_profile` | identities.py:44 | numerical | KEEP |
| `policy`, `upstream_commit` | identities.py:45 | provenance constants (identical in both keys today) | KEEP (not part of mismatch) |
| `inputs{Building_DSM,Trees,DEM}` | identities.py:46-47 | numerical (raster bytes + GDAL metadata) | KEEP |
| `patch_option` | identities.py:48; pipeline.py:166 hardcodes 2, api.py:94/209 threads param | numerical | KEEP (shared recipe must thread one value) |
| `patch_arrays` | identities.py:49 | numerical | KEEP |
| `normalization` | identities.py:50-52 | descriptive constants (identical today) | KEEP |
| `implementation` | identities.py:53-57 (10-file closure) | numerical | KEEP |
| `dependencies` | identities.py:58 | numerical | KEEP |
| `construction='standalone-svf-v1'` | **service.py:281** | operational label of the export wrapper; consumed only by manifest comparison (service.py:142-144) | **MOVE-TO-EXPORT-IDENTITY** |
| `standalone_implementation=fingerprint(service.py)` | **service.py:282** | hybrid: service.py also holds the standalone normalization body `_producer` (service.py:62-83), not covered by the shared closure | **KEEP today; MOVE-TO-EXPORT-IDENTITY only after C6-10 moves normalization into the shared recipe**, with dossier step-E differential proof |

Store hashing facts backing the mechanism: `key_for` hashes the complete canonical identity (`cache/geometry.py:178-182`); `get_or_create` freezes the identity then keys before lookup (`cache/geometry.py:287-300`). Any extra identity field ⇒ different key ⇒ cold double production — exactly what was measured. Producer-side normalization is line-for-line equivalent between `service.py:62-83` and `pipeline.py:99-134` (per-step mapping recorded in the JSON twin), and both routes call the same `svf_calculator_compact`.

## Fixture record (reproducibility)

96x96 dense_urban motif, verbatim from pinned generator `reports/p7_fixture_sources/00318d13…py`, no RNG; met file byte-for-byte from `tests/reference/small_original_cpu/scene/met.txt`. sha256: Building_DSM `f5091bee…17f78`, DEM `b58de75e…3ba883`, Trees `bfacf1e1…c7ed9`, met.txt `bc8ee636…9189e4` (full values in the JSON twin). Env: python 3.11.16 / numpy 2.4.6 / numba 0.67.0 / GDAL 3.13.3, `.venv-light`, ≤2 native threads (`NUMBA_NUM_THREADS=2` parent, 1 in tile children). Instrumentation is call-through only; child processes instrumented via generated `sitecustomize` + prepended meta-path finder.

## Constraint compliance

Writes confined to `tests/optimization_v6/geometry_census/` and `optimization_v6_continue/evidence/census/` in the worktree at `/Users/alansynn/Workspace/solweig-light-v6-census` (detached at e7a2d6ec). No src/ changes, no commits, no push.
