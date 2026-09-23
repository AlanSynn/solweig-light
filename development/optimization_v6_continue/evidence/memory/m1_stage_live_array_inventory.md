# M1 — Stage live-array inventory (commit e7a2d6ec)

Worktree: `/Users/alansynn/Workspace/solweig-light-v6-mem` (detached at `e7a2d6ec8594b234820e7783e0ca26d821de7f3d`).
All `path:line` citations below resolve at that commit. "Full plane" = one `(rows, cols)` array; bytes at 1024x1024 float32 = 4 MiB/plane, float64 = 8 MiB/plane.

Conventions: **P** = persistent across the whole tile (multi-stage lifetime), **T** = transient inside one stage/timestep, **RO** = read-only after creation, **MUT** = mutated in place, **X** = crosses a stage barrier.

---

## Stage 0 — Parent input read + per-tile input derivation (`pipeline.py` `_run_tile`)

| Array | Lifetime | Dtype/shape class | Owner | Mut/RO | Notes |
|---|---|---|---|---|---|
| `a` (Building_DSM), `dsm`/`trees`/`dem` reads | P (tile) | full plane f32 | tile args | RO | `read_raster` `.astype(np.float32)` — `io/rasters.py:20-28` |
| `walls`, `aspects` | P (tile) | full plane **f64** | `GeometryCache` via `pipeline.py:202` | RO | produced in preprocess phase; `walls_compiled.py:39,49` returns float64 |
| vegdem/vegdem2/bush/vegdsm/vegdsm2/buildings/valid_mask derivations | P (tile) | full planes f32 (7-8 planes) | `pipeline.py:128-138` | RO after derive | subset exists only when `usevegdem` |
| `zero`, `ones` | P (tile) | full plane f32 (2) | `Workspace` `pipeline.py:224-225` | RO | prototypes for all fills |
| `Tgmap1{,E,S,W,N}`, `Tstart_wall`, `TmaxLST*`, `alb_grid`, `emis_grid`, landcover grids | P (tile) | full planes f32 (≈4-10; more with landcover branch `pipeline.py:140-153`) | args dict `pipeline.py:227-236` | RO/mild MUT in engine | material grids |
| wind coefficient planes (up to 12 channels x ~4 arrays) | P (tile) | full planes f32 (≤12 explicitly retained) | `pipeline.py:216-223` | RO | `DEFAULT_WIND_CHANNELS = 12` `runtime.py:281` |

Stage exit live set (scene floor): ≈ 30-40 full planes, of which `walls`/`aspects` are float64 (the only non-32-byte-per-pixel family at entry).

## Stage 1 — Geometry production / publication (`geometry/service.py`, `geometry/svf.py`)

Cold path (`pipeline.py:158-192`): `svf_calculator_compact(..., save_rasters=False)` then `GeometryStore.get_or_create`.

| Array | Lifetime | Dtype/shape class | Owner | Mut/RO | Notes |
|---|---|---|---|---|---|
| SVF field planes (15: svf, svfN/W/E/S, 4x veg, 4x aveg, …) | P (tile) | full plane f32 (15) | `geometry/svf.py:111` | RO after produce | compact mode replaces dense cubes with 3 `VisibilityBuilder`s `geometry/svf.py:122-126` |
| dense cube fallback `mats` | T (stage) | `(sum(counts), rows, cols)` f32 | `geometry/svf.py:126` | T | **Dense worst case: 153 full planes** — only non-compact route |
| per-patch `shadow(...)` output | T | full plane f32 per call | `geometry/svf.py:132` | T | freed each iteration |
| `shmat`, `vegshmat`, `vbshvegshmat` payloads | P (tile) | packed bytes: binary 1 b/px, ternary 2 b/px, **raw 32 b/px** (`geometry/visibility.py:90-92`) | PackedVisibility heap bytes / MappedVisibility mmap | RO | raw worst = `3*pixels*patches*4` = 1.79 GiB @1024/P153 |
| geometry store arrays (16 mmaps + 3 visibility channels) | P (tile) | mmap `mode='r'` | `cache/geometry.py:194-219` | RO | `GeometryHandle.close` `cache/geometry.py:150-158`; demand-paged but resident once touched |
| export staging (legacy TIFF/ZIP/NPZ) | T (stage) | streaming via GDAL + `PackedVisibility.from_dense` NPZ stream | `geometry/svf.py:63-84` | T | streamed, no full dense cube re-materialized in compact mode |
| `svfbuveg`, `asvf`, `svfalfa` | P (tile) | full plane f32 (3) | `pipeline.py:193-200` | RO | derived from geometry outputs |
| `diffsh` | P (tile) | **lazy** pair (shadow, vegetation) | `LazyDiffVisibility` `pipeline.py:197` | RO container, MUT-free | decodes 2 full planes **per `__getitem__`** `geometry/visibility.py:254-258` |

Parent/child overlap: `prepare_geometry_exports` (`geometry/service.py:258-327`) runs `plan_admission` at `service.py:275`, holds destination flocks (`service.py:29-59`), GDAL schema probe (`service.py:86-104`), exact-validation bounded workspace (`service.py:172-187`), staged export with hard-link rollback (`service.py:212-255`) — all while the tile's scene arrays from Stage 0 are live.

## Stage 2 — Preprocessing publication (walls/aspect, upstream of tile loop)

| Array | Lifetime | Dtype/shape class | Owner | Mut/RO | Notes |
|---|---|---|---|---|---|
| walls/aspect intermediates (`filter1Goodwin_as_aspect_v3` family) | T (stage) | **≈6-8 float64 full planes** | `walls.py:181` (`y = np.zeros(a.shape)` f64), `walls_compiled.py:39,49` f64 outputs | T | float64-heavy phase; admission still charges the full simulation estimate (see M2) |
| per-file GDAL output | T | streamed band writes | `run_walls_aspect` `api.py:17-47` | T | exceptions reported-and-skipped per file (`api.py:43-47`); `ResourceAdmissionError` re-raised (`api.py:43-44`) |

## Stage 3 — Simulation steady set (entering the timestep loop, `pipeline.py:252-283`)

Live at stage entry:

| Family | Planes (f32 unless noted) | Where established |
|---|---|---|
| Stage-0 scene planes | ≈30-40 | `pipeline.py:99-236` |
| SVF fields + svfbuveg/asvf/svfalfa | 15+3 | `pipeline.py:111` (svf.py), `pipeline.py:193-200` |
| packed visibility (3 channels) | packed bytes (1.79 GiB raw worst) | geometry stage |
| `SimulationState` (Tstart, Ta, RH-derived, etc.) | 6 | `SimulationState.initial` `pipeline.py:226`, `models.py` |
| GDAL output dataset(s) | 1-10 datasets x 24 bands (streamed; band buffers per write) | `TransactionalOutputs` `pipeline.py:244-247`; `StreamingOutputs.write` `io/rasters.py:66-78` |

## Stage 4 — Per-timestep transients (`Solweig_2022a_calc`, `engine.py:1478-1676`; returns 39-tuple at `engine.py:1676`)

| Array | Lifetime | Dtype/shape class | Owner | Mut/RO | Notes |
|---|---|---|---|---|---|
| wall-shadow output `out` | T (one timestep) | `(8, rows, cols)` f32 — 8 planes | compiled `exact_23`/`exact_13` dispatch `engine.py:1716-1727`; kernels in `wall_shadows.py:77-105,140-200` | T | single allocation per call, freed after use |
| dRad anisotropic decodes | T | 2 full planes **per patch per timestep** (serial route) | `engine.py:1563` (`aniLum += _operate(np.multiply, diffsh[:, :, idx], lv[idx, 2])`) | T | LazyDiffVisibility decode; `np.multiply` temp + `_operate` result per patch |
| GVF internals (`_gvf` serial) | T | 16 accumulator planes + per-direction `_gather` output `(16, rows, cols)` + 6 snapshot planes + prepared copies | `ground_view.py:218` (`output=np.empty((16,*shape))`), `ground_view.py:216-217`, `ground_view.py:240-263`, `ground_view.py:413-428`, `ground_view.py:443-450` | T | **largest per-timestep transient family** |
| GVF fused route (threads>1) | T | per-direction ~5 full planes + block scratch `(16, 32, cols)` f32 | `_gvf_fused` `ground_view.py:652-655`; dispatch `engine.py:1735-1745` | T | bounded by `block_rows=32` |
| compiled Kside output | T | `(7, pixels)` f32 = 7 planes | `patch_radiation.py:544`; block loop `patch_radiation.py:560-582` | T | decode scratch bounded: `_shortwave_visibility_blocks` via `_block` `patch_radiation.py:101-116`; bool `(block_pixels, patches)` per block |
| compiled define_patch output | T | `(11, pixels)` = 11 planes | `patch_radiation.py:883` | T | `patch_geometry` lru_cache(8) `patch_radiation.py:54-85` |
| compiled Lcyl output | T | ≤4 planes | `patch_radiation.py:903-932` | T | |
| numpy-fallback Kside (non-compiled route) | T | ≈30 full planes of intermediates | `engine.py:441-502` reference path | T | fallback only |
| cylindric_wedge internals | T | ≈10 planes | engine | T | |
| output dict (Tmrt, UTCI, + requested bands ≤10) | T (timestep) | ≤10 planes f32 | returned 39-tuple sliced at `pipeline.py:258-277` | T | explicitly retired `del result, fields, output, tmrt, utci, speed, temperature` `pipeline.py:283` |
| `Tg`/`Tstart` state updates | MUT | in-place on state planes | engine writes via state dicts | MUT | carried across timesteps — the only mutated persistent family inside the loop |

## Stage 5 — Checkpointing / writing (inside timestep loop)

| Array | Lifetime | Dtype/shape class | Owner | Mut/RO | Notes |
|---|---|---|---|---|---|
| per-field float32 copy for digest | T (per write) | 1 plane per output field (≤10) | `persistence.py:456-468` (`_stored_bytes_digest`), allocator `persistence.py:219` | T | duplication of every written band |
| checkpoint state BytesIO | T (per checkpoint) | 6 state planes serialized (f64 in transit) | `persistence.py:84-104` (`_encode`), `persistence.py:160-173` (`save_state`) | T | transient ~1.5-3x state size |
| GDAL band write buffers | T | per band | `io/rasters.py:66-78` (WriteArray + FlushCache) | T | FlushCache per band flushes dirty blocks; **GDAL block cache itself uncounted** (M2) |

## Stage 6 — Final publication (`writer.complete(extra_artifacts=extra)`, `pipeline.py:286-300`)

| Array | Lifetime | Notes |
|---|---|---|
| All Stage-3 persistent families | still live | conditional legacy SVF export runs **while every scene/geometry/state array is still live** — parent/export overlap window |
| publication journal → rename sequence | metadata only | `persistence.py:540-595`: journal first, per-artifact renames, completion manifest **last** |

## Stage-barrier crossers (arrays that must survive a barrier)

1. Input planes + derived masks: Stage 0 → 3 (whole tile lifetime).
2. `walls`, `aspects` (float64): Stage 2 preprocess → 3.
3. Packed visibility payloads + SVF fields: Stage 1 → 3 (geometry cache or in-tile production).
4. `svfbuveg`/`asvf`/`svfalfa`/`diffsh`: Stage 1 → 3 (derived at `pipeline.py:193-202`).
5. `SimulationState` 6 planes + engine scalar dicts: per-timestep MUT, cross every timestep boundary; serialized at each checkpoint (`persistence.py:470-497`).
6. GDAL output datasets: opened before loop, flushed per band, committed at Stage 6.
7. Worker-retained bounded resources across jobs (persistent pool): JIT caches, `patch_geometry` lru_cache(8), ray-schedule lru_cache(36) ≤64 KiB each (`ground_view.py:64-77`) — explicitly bounded, `runtime_worker.py:82-85` `gc.collect()` retires everything else per job.

## Parent/child relationship summary

- `PackedVisibility` holds immutable heap `bytes`; `MappedVisibility` (native cache mode) is a readonly NPY mmap with explicit close (`geometry/visibility_native.py:63-119`, open at `:260-261`). Both are RO containers; all decode paths produce fresh transients and never write back.
- `LazyDiffVisibility` is the only visibility family with *deferred* cost: payload is 2 references, cost lands per-access inside the dRad loop (`engine.py:1563`).
- GDAL datasets own their own C-level block cache — invisible to Python allocators and to the admission model.

## Mutated vs read-only

- MUT (in place): `SimulationState` planes and engine scalar/state dicts (per timestep); GDAL band data (append per band); `_stored_bytes_digest` bookkeeping.
- Everything else in the inventory is RO after creation. Notably `walls`/`aspects`, all SVF fields, packed payloads, material grids, wind planes are never mutated during simulation.

## Inventory → admission model deltas (feeds M2)

- Raw-mode packed channels (1.79 GiB @1024/P153) are genuinely live heap for the entire simulation — correctly counted by `estimate_memory` `runtime.py:478-490` (`raw_visibility` term).
- GVF serial route's 16+16+6+copies ≈ 40+ plane transient family is *within* the `live_arrays` 192-plane envelope but is the phase that actually approaches it; fused route cuts it to ≈10 planes + 32-row scratch.
- Digest copies, checkpoint BytesIO, GDAL cache, and export-overlap are the four windows the model does not itemize (arithmetic in M2).
