# C5-02 CONTRACTS — preserved public surface relevant to optimization

Anchors: `src/solweig_light/...:line` at worktree HEAD `6682b23e`.

## 1. Seven workflow entry points

| # | Entry point | Module:line | Notes |
|---|---|---|---|
| 1 | `thermal_comfort(...)` | `api.py:163` | full local own-met TIFF workflow: wind coeffs (optional) → preprocess → walls/aspect → SVF → `run_utci_tiles` (api.py:196-207) |
| 2 | `run_utci_tiles(base_path, preprocess_dir, selected_date_str, tile_keys=None, save_*…)` | `api.py:100` | sorts tiles, `plan_admission(jobs, runtime)` then `execute_tiles(jobs, runtime)` (api.py:146-158) |
| 3 | `calculate_svf(base_path, patch_option=2, overwrite=False)` | `api.py:50` | validate_existing=True variant |
| 4 | `run_walls_aspect(preprocess_dir)` | `api.py:17` | per-DSM `plan_admission` + `findwalls` + `filter1Goodwin_as_aspect_v3`, writes `walls_<tile>.tif` / `aspect_<tile>.tif` (api.py:33-40); per-file exceptions reported and skipped, ResourceAdmissionError re-raised (api.py:34-42) |
| 5 | `build_inputs(lat, lon, city=None, km_buffer=8.0, …)` | `api.py:216` | |
| 6 | `build_wind_ext_coeff(input_dir, era5_dir, directions=range(0,360,30), …, max_workers=None)` | `api.py:225` | |
| 7 | `preprocess(base_path=…, …)` | `preprocessor.py` (imported `api.py:13`, called `api.py:196`) | |

Internal per-tile entry retained for numerical harnesses: `pipeline.run_tile(...)`
(`pipeline.py:79-88`) — "The internal run_tile entry remains available to numerical test
harnesses" (`api.py:157-158`).

## 2. RuntimeOptions fields and defaults (`runtime.py:314-327`)

| Field | Default | Validation |
|---|---|---|
| `cache_dir` | `None` | str/PathLike or None (:330-333) |
| `legacy_cache_policy` | `"recompute"` | ∈ {`recompute`,`trust`} (:334-335) |
| `cache_enabled` | `True` | bool (:336-337) |
| `memory_budget_bytes` | `None` → resolved via `default_memory_budget_bytes()` = 0.5×min(physical, available, container headroom) (:279, :289-300, :369-375) | positive int (:338-343) |
| `cpu_budget` | `1` | positive int ≤ `_total_cpus()` (cgroup-aware) (:344-362) |
| `workers` | `1` | positive int (:344-351) |
| `threads_per_worker` | `1` | positive int, ≤ cpu_budget (:354-367) |
| `block_pixels` | `128` | positive int; bounds decode block in patch_radiation (:325, engine.py:1748/1756/1764) |
| `checkpoint_interval` | `1` | positive int; `writer.checkpoint` every N timesteps (`pipeline.py:279-280`) |
| `resume` | `False` | bool; `TransactionalOutputs(..., resume=runtime.resume)` (`pipeline.py:246-247`) |

Derived: `requested_native_threads = workers*threads_per_worker` (:377-380). Options are
context-bound (`runtime_options` context manager, :397-423); NO CLI flag exposes any of these
— they are set programmatically only (cli.py has no runtime args; verified grep).

## 3. CLI flags (`cli.py:40-85`)

`--version`, `--base_path` (req), `--date` (req), `--building_dsm` (default Building_DSM.tif),
`--dem` (DEM.tif), `--trees` (Trees.tif), `--landcover` (None), `--tile_size` (3600),
`--overlap` (20), `--use_own_met` (True), `--own_metfile` (None), `--data_source_type` (None),
`--data_folder` (None), `--start`, `--end`, `--era5_z0_find` (None→auto), `--use_uhi` (True),
`--save_tmrt` (True), `--save_svf/--save_kup/--save_kdown/--save_lup/--save_ldown/
--save_shadow/--save_wbgt/--save_ta/--save_wind` (all False). Validation in `cli.main`
(:90-125): own_metfile required/exists when use_own_met; data_source_type+data_folder+start/end
otherwise; era5_z0_find=True requires data_folder.

## 4. Artifact naming conventions

- Per-timestep/aggregate outputs: `output_folder/<tile>/<Field>_<tile>.tif`
  (`pipeline.py:237` output_dir; fields written via `writer.write` from the dict keys
  `UTCI TMRT Kup Kdown Lup Ldown Shadow Ta Wind [+WBGT]`, pipeline.py:270-277).
- Return-field vocabulary `RETURN_NAMES` (`pipeline.py:29-31`, 39 names) and
  `SVF_NAMES` (`pipeline.py:32-33`, 19 names: 15 svf fields + vegshmat vbshvegshmat shmat +
  svftotal).
- SVF artifacts: `svfs{suffix}.zip` (15 float32 GeoTIFFs named svf…svfNaveg),
  `SkyViewFactor{suffix}.tif` (total), `shadowmats{suffix}.npz` (3 packed channels via
  `export_visibility_npz`), suffix `_<number>` = tile (`geometry/svf.py:63-84`); atomic
  publish via tempdir + `os.replace` (:71-84).
- SVF cache location: `preprocess_dir/SVF/{SkyViewFactor_<tile>.tif, svfs_<tile>.zip,
  shadowmats_<tile>.npz}` (`pipeline.py:158-160`).
- Loading: `pipeline.load_svf` reads `/vsizip/...` members + npz + total tif
  (`pipeline.py:59-69`).
- Transaction staging/publish: `TransactionalOutputs(output_dir, tile, ...)` with
  `staging_directory`, `publication_path`, `completion_path`
  (`pipeline.py:244-247`, `persistence.py:196+`).

## 5. Cache / manifest behavior

- Geometry store: `cache/geometry.py` — "A manifest is the only commit point. Generations are
  never removed here" (module docstring :3); `content_fingerprint` sha256 (:56);
  `GeometryStore.load` validates `manifest_sha256` digest, format/version/model_version/key/
  identity and per-array + per-visibility payload fingerprints (:185-212); store path
  `runtime.cache_dir or preprocess_dir/.solweig-light/cache` (`pipeline.py:188`); key =
  `geometry_identity(paths, 2)` (`pipeline.py:166`).
- Trusted legacy path: `legacy_cache_policy=='trust'` requires all three SVF artifacts and
  re-checks an `InputGuard` over them before AND after use (`pipeline.py:170-178`, :242-243,
  :297-299); fingerprints recorded under `geometry_key['trusted_legacy']`.
- Identity guards: `InputGuard(guarded_paths)` over raster+wind paths, re-checked at
  produce_geometry, pre-publish and post-publish (`pipeline.py:97`, :167, :183, :241, :285,
  :297); `simulation_identity(...)` + geometry key embedded in the transaction record
  (:239-240).
- Persistent JIT identity: `_jit_cache.bind_cache_identity` namespaces only
  `_wall13_serial`/`_wall23_serial` and the two SLEEF kernels (wall_shadows.py:109,204;
  _sleef_acos.py:90; _sleef_classifier.py:129,142); all other compiled kernels use plain
  numba `cache=True` on-disk caches.
- Math profile identity: `radiation/_math_profile.profile_identity()` (sha256 of
  `_sleef_acos.py,_sleef_classifier.py,_math_profile.py,_jit_cache.py,SLEEF_LICENSE.txt` +
  runtime fingerprint) is the cache-relevant numerical-profile identity (_math_profile.py:19,
  :34-57).

## 6. Checkpoint / publish requirements

- Semantics: `checkpoint_interval=N` → `writer.checkpoint(i+1, state)` when
  `(i+1)%N==0` OR on the final step `i+1==len(timeline.met)` (`pipeline.py:279-280`);
  a checkpoint commits BOTH the state pointer and the output-band boundary
  (persistence.py:3, :419-434: record gains `checkpoint={next_timestep, generation,
  state_sha256, band_hashes, band boundaries}`).
- Durability: staged writes fsync'd; commit via `os.replace` of temporary files
  (`persistence.py:47-66`, :465-475); checkpoint payload validation on load with typed
  `PersistenceError` failures (:89-151, :174-184, :353-364).
- Resume: `writer.restore()` returns `(start, state)` or None (`pipeline.py:248-251`,
  persistence.py:410); `resume=True` required for restore to engage (`pipeline.py:246-247`).
- Completion: `writer.complete(extra_artifacts=extra)` publishes staged SVF artifacts and
  final outputs atomically (`pipeline.py:300`, persistence.py:483+); SVF exports skipped when
  already publishing or cache available (:286-292); `SVF_<tile>.tif` extra only when
  `save_svf` and cache not on disk (:293-296).
- Error contract at runtime boundary: child failures surface as reconstructed builtin or
  owned exceptions (`runtime.py:618-660`) with exit-code note, else `TileExecutionError`
  (:780-782); every sibling stopped before raise (:614-615).

## 7. Hard invariants cited by the rules (anchors)

- Chronological state advance per tile, single timeline; no independent time workers
  (blueprint §5.2; `pipeline.py:252-283` loop is the only state carrier).
- Torch-free own-met core: no torch import anywhere under `src/` (verified by read of
  imports in audited modules; the "Torch" comments document promotion semantics only).
- Exactness gate: `tests/differential/test_sky_compiled.py:24-29` `assert_exact` pattern
  (dtype/shape/array_equal/NaN-Inf masks/signbit) — the minimal acceptance comparator.
