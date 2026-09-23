# M2 — Worst-case raw memory model: 1024x1024x24 @ 153 patches (commit e7a2d6ec)

All citations at `e7a2d6ec8594b234820e7783e0ca26d821de7f3d` in worktree `/Users/alansynn/Workspace/solweig-light-v6-mem`.
Plane = 1024x1024; float32 plane = 4,194,304 B (4 MiB); float64 plane = 8 MiB.

## 1. The admission model as written

`estimate_memory` (`src/solweig_light/runtime.py:457-502`), components at `:478-490`:

```
raw_visibility = 3 * pixels * patches * 4                       # :479
live_arrays    = (LIVE_FULL_PLANE_EQUIVALENTS                    # 192, :285
                  + DTYPE64_RESERVED_PLANES                      #  32, :286
                  + windchannels) * pixels * 4                   #  12, :281
decoded        = block_pixels * patches * (windchannels + 4) * 4 # :486-487
native         = 256 MiB + 64 MiB * min(8, windchannels)         # :489-490
total          = sum                                             # :491
```

`default_memory_budget_bytes` (`runtime.py:289-300`) = 50% (`DEFAULT_MEMORY_FRACTION`, `:279`) of `min(physical, available, cgroup headroom)`.

`plan_admission` (`runtime.py:566-592`): (a) each active job's individual estimate must be ≤ budget; (b) the K largest per-job estimates (K = active workers) summed descending must be ≤ budget; returns `AdmissionPlan(active, estimates, active*threads_per_worker)`. It is a **static sum of per-tile estimates** — it has no phase dimension and no overlap-window concept.

## 2. Peak live-bytes per phase (raw worst case, 1024/P153/w12)

Constants: `raw = 1.793 GiB`, `live = 0.922 GiB`, `dec = 1.2 MiB (block128) / 9.6 MiB (block1024)`, `native = 0.750 GiB`.

| Phase | Live set composition | Peak arithmetic | GiB |
|---|---|---|---|
| P0 parent preprocess (walls/aspect) | float64-heavy intermediates (M1 Stage 2), **no** visibility, no SVF | ≈ 8-10 f64 planes + GDAL streams | ≈ 0.1-0.2 |
| P1 geometry produce (cold, in-tile) | scene planes (≈0.15) + SVF fields 15 (0.06) + 3 visibility payloads (1.79 raw) + compact builders | ≈ raw + live-ish subset | ≈ 2.0-2.4 |
| P1' geometry export overlap (`service.py:258-327` in-tile; legacy SVF `pipeline.py:286-300`) | **P1 set still live** + GDAL staging streams + NPZ stream buffers | max(P1) + streams; streamed so ≤ tens of MiB | ≈ 2.1-2.5 |
| P2 simulation steady state (serial route) | raw 1.793 + live 0.922 + per-timestep transients (GVF serial family ≈ 40 planes ≈ 0.16 GiB + wall shadows 8 ≈ 0.03) | ≈ estimate total + transient delta | ≈ 3.6 |
| P2' simulation (fused GVF, threads>1) | same steady set; GVF bounded to ≈10 planes + 32-row scratch (`ground_view.py:652-655`) | ≈ estimate total | ≈ 3.5 |
| P3 checkpoint/write pulse | + digest copies ≤10 planes (`persistence.py:456-468`) + state BytesIO (`:84-104`) | + ≈ 0.05-0.08 (transient) | ≈ 3.6-3.7 |

The model's own total at block1024 = **3.4742 GiB** (3,730,374,656 B) — matches dossier D04's "~3.474 GiB at 1024/P153/default wind reserve/block1024" exactly (block128 variant: 3.4660 GiB).

**Phase-vs-model:** the model is a good simulation-phase approximation (P2 ≈ estimate + ~0.1 GiB serial-GVF/digest transients) but **over-admits P0** (charges 3.47 GiB for a float64 preprocess that uses ≈0.2) and **under-admits P1'** overlap by the export stream cost.

## 3. float32/float64 promotion points

- Charged-but-mislabeled: the 32 `DTYPE64_RESERVED_PLANES` are multiplied by `float32 = 4` (`runtime.py:478-484`), not 8. At 1024 this undercharges by `32 * 4 MiB = 128 MiB`. This is precisely D04's warning: "Correct float64 accounting means eight-byte arrays, not just a label on four-byte planes."
- Actual f64 families in the pipeline: `walls`/`aspects` (preprocess outputs, `walls_compiled.py:39,49`; `walls.py:181`) — they persist tile-long (M1 Stage 0) inside the `live_arrays` envelope; the f32-promotion guard `_operands` (`engine.py:1693-1707`) keeps engine arithmetic from silently promoting, so no additional engine-side f64 blowup exists in compiled routes. The numpy reference routes (`engine.py:441-502`) can carry more intermediates but are fallback-only.
- Checkpoint `_encode` serializes state via BytesIO (`persistence.py:84-104`) — transit dtype may differ from resident f32; counted nowhere.

## 4. Parent/export overlap windows (where stages sum, not max)

D04: "stages that overlap must be summed, not maxed." Overlap windows found:

1. **In-tile geometry + export**: `prepare_geometry_exports` (`service.py:258-327`) executes while Stage-0 scene arrays are live in the same process (cold `_calculate_svf` path). Export streams (GDAL/NPZ) add on top of the geometry peak.
2. **Legacy SVF export at tile end** (`pipeline.py:286-300`): runs while ALL simulation-persistent families (raw visibility 1.79 GiB + 0.92 GiB live) are still live. This is the widest overlap; it is inside the estimate only because the estimate's `live_arrays` never drops — i.e. the model implicitly assumes the steady set persists through publication. True.
3. **Parent + children**: `M_total = M_parent + sum(active reservations)` (D04). The parent process (CLI holding `run_utci_tiles`) retains only bookkeeping + GDAL schema probes; per-child reservations are the 3.47 GiB estimates. Parent RSS ≈ 0.2-0.4 GiB (Python + GDAL libs).

## 5. Worst raw mode: GDAL block cache + JIT scratch

- **GDAL block cache**: per-process default `GDAL_CACHEMAX` ≈ 5% of physical RAM (GDAL default when env unset). On a 32 GiB host that is **1.6 GiB per process**, none of it visible to `tracemalloc`/numpy `nbytes` and none of it in `estimate_memory`. `StreamingOutputs.write` FlushCache per band (`io/rasters.py:66-78`) flushes *dirty* blocks but clean read blocks (input DEM/DSM reads via `read_raster`, schema probes `service.py:86-104`) can accumulate up to the cap. Workers are separate processes ⇒ **W workers can hold W x 1.6 GiB** of GDAL cache. This is the single largest uncounted term.
  - Mitigation already available: the pool sets a full child env (`_child_environment`, `runtime.py:663-676`) — `GDAL_CACHEMAX` is *not* set there today.
- **JIT/LLVM reserve**: modeled as `native = 256 MiB + 64 MiB*min(8,w)` (`runtime.py:489-490`) = 750 MiB. Covers numba/LLVM code+data and BLAS workspaces. Bounded module caches observed: ray schedules lru_cache(36) x ≤64 KiB (`ground_view.py:64-77`), `patch_geometry` lru_cache(8) (`patch_radiation.py:54-85`) — KiB-scale, inside the allowance.
- **JIT scratch beyond the allowance**: compiled kernels' per-block decode scratch is bounded (`decoded` term, `runtime.py:486-487`; `patch_radiation.py:101-116,560-582`) — 1.2 MiB at block128. The *serial numpy fallback* decode path (`engine.py:1563` per-patch 2-plane decodes; `engine.py:441-502` reference Kside ≈30-plane intermediates) can transiently exceed the `decoded` term, but its planes are already inside `live_arrays`' 192-plane envelope (M1 Stage 4).

## 6. plan_admission: what it counts vs what M1 shows

Counts: per-tile estimate sum (largest-K) against budget; per-job single-tile check; thread multiplier returned but threads are CPU-governed elsewhere.

Misses (each with M1 evidence):

| # | Miss | Evidence | Magnitude @1024 |
|---|---|---|---|
| a | GDAL block cache per process | `io/rasters.py:66-78` FlushCache-only; env not set in `_child_environment` `runtime.py:663-676` | up to ≈5% RAM **per worker process** |
| b | f64 reserve charged at f32 | `runtime.py:478-484` | 128 MiB |
| c | Checkpoint BytesIO duplication | `persistence.py:84-104,160-173,470-497` | ≈ 2x state (6 planes) ≈ 48 MiB pulse |
| d | Per-write digest copies | `persistence.py:456-468`, allocator `:219` | ≤10 planes ≈ 40 MiB pulse |
| e | Export-overlap stream buffers | `pipeline.py:286-300`, `service.py:212-255` | tens of MiB, bounded by streaming |
| f | Parent process footprint | D04 `M_parent` term present in dossier formula but not in `plan_admission` arithmetic | ≈ 0.2-0.4 GiB |
| g | Phase shape: preprocess over-admission | walls/aspect phase charges full 3.47 GiB estimate though it uses ≈0.2 (`api.py:17-47` runs before any visibility exists) | blocks up to 6-7 workers unnecessarily in P0/P1 |

Pulses (c,d) land inside the 50%-budget slack and are < 0.1 GiB — negligible vs (a) and (f).

## 7. Parallel 2x2 vs a 12 GiB process-tree cap — arithmetic

- 2 workers x 3.4742 GiB estimates = 6.9484 GiB of *admitted* reservations.
- Plus parent ≈ 0.3 GiB ⇒ tree ≈ 7.25 GiB — fits 12 GiB with ≈ 4.75 GiB headroom.
- Worst raw case adding misses: 2 x (GDAL cache 1.6 GiB) + 2 x 3.4742 + parent 0.3 + pulses 0.2 ≈ **10.75 GiB** — still under 12 GiB, but headroom shrinks to ≈ 1.25 GiB. On a 32 GiB host with default budget (50% ⇒ 16 GiB), `plan_admission` would admit 4 workers of 3.4742 = 13.9 GiB estimates + 4 x 1.6 GiB GDAL + parent ≈ **20.5 GiB actual** — that configuration, not 2x2, is the one that can breach a 12 GiB cap.
- **Verdict**: 2x2 is safe under a 12 GiB cap in both admitted and raw terms (worst ≈ 10.75 GiB). 4x1 at default budget is the risky configuration; the cap breach would come from GDAL caches (uncounted, a) plus parent (uncounted, f), not from the per-tile estimate itself.
- cgroup nuance: page-cache from GDAL/mmap writes may count toward cgroup memory but is reclaimable; MappedVisibility read-only mmaps (`visibility_native.py:63-119`) become resident on touch (D04: "a read-only mapping may become resident; mmap is not free memory") and are already inside the raw term only in *packed-heap* mode — in native-cache mode the payload is mmap-backed and the raw term over-reserves it (safe direction).

## 8. Numba/LLVM reserve adequacy

750 MiB modeled vs observed bounded module caches (KiB) + numba runtime + BLAS pools. The reserve is generous for serial routes; for `threads_per_worker=4` routes each worker still holds one LLVM context per signature — the `64 MiB * min(8, w)` term scales with windchannels, not threads, but compiled kernels do not duplicate per thread. Reserve judged adequate with ≈2x slack.
