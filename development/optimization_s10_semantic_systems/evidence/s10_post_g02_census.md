# S10 post-G02 census: dtype-profile gate survey + full tile profile

Date: 2026-10-14. Branch `perf/s10-semantic-systems` (612fbb13). Landcover
golden cell, H=1 (defaults), landcover protected route. Probes:
`/storage/scratch1/1/dsynn6/solweig-light-s10-raw/probes/`
(`s10_gate_census.py`, `s10_pipeline_probe.py`, `s10_checkpoint_split.py`,
`s10_startup_probe.py`); outputs in the same directory. Method: wrapper-timed
`perf_counter` (not cProfile — wrapper-inflation caveat in
g01_g02_prepared_gvf.md), 1 warmup + 3 timed in-process runs, 256 MiB GDAL
cap + 5.5 GB budget deviation documented for the campaign record.

## 1. Dtype-profile gate census — decisive negative

Every guarded compiled route was counter-probed on the production landcover
profile (f64 Tg, U-profile Tgwall, LazyDiffVisibility diffuse, MappedVisibility
shadow channels, f64 radI/radG scalars):

| route | probe | result per run |
|---|---|---|
| Lcyl primary (T01 U + by_demand) | ROUTE_COUNTS | 24/24 primary, **0 reference** |
| dpc primary (T01 U) | ROUTE_COUNTS | 24/24 primary, **0 reference** |
| Kside primary | `_reference` invoke counter | 14/14 primary, **0 fallback** |
| prepared GVF (G01+G02) | serial-delegate counter | 14/14 prepared, **0 delegates** |
| exact_13 / exact_23 | `*_numpy` fallback counter | **0 fallbacks** |
| N9 bounded Lw stream | `_lw_region_route` consult | **24/24 accepted** |

Kside guard detail (captured production args): scalar radI/radD are float64
but the guard only requires 0-d for them; rasters are all float32;
`diffsh` (LazyDiffVisibility) and `shmat`/`vegshmat`/`vbshvegshmat`
(MappedVisibility) pass `_supported` via their dtype attributes. The G01+G02
f64-Tg gate was the **last** never-engaged compiled route on this profile;
the dtype-profile gate class is exhausted.

## 2. Tile profile after G01+G02 (tile ≈ 1.10–1.20 s; shares of calc ≈ 0.75–0.77 s)

| stage | calls/run | s | % calc | route |
|---|---|---|---|---|
| gvf_2018a | 14 | 0.218 | 28.5–29.2% | prepared (C6-30 + G01/G02) |
| Lcyl_v2022a_by_demand | 24 | 0.186–0.198 | 25.0–25.8% | primary + accepted N9 stream |
| Kside_veg_v2022a | 14 | 0.165–0.177 | 22.0–22.2% | compiled primary |
| Lside_veg_v2022a | 24 | 0.034 | 4.4–4.5% | NumPy `_operate` body (no compiled twin) |
| shadowingfunction_wallheight_23 | 14 | 0.012 | 1.5% | exact_23 |
| body residual (aniLum loop, Tmrt, Tg/dRad) | — | 0.131–0.136 | 17.6–17.7% | — |

Inside the residual, the aniLum loop dominates: `LazyDiffVisibility.__getitem__`
2142 calls/run (14 daytime steps × 153 Perez patches) = **85.3 ms = 11.1% of
calc** — the largest single remaining candidate (R03).

## 3. Pipeline-side shares (tile ≈ 1.15–1.20 s)

| bucket | s | % tile | detail |
|---|---|---|---|
| Solweig_2022a_calc | 0.74–0.77 | ~64% | above |
| checkpoint (interval=1) | 0.19 | **15.8%** | split: `_flush` ≈ 43%, `save_state` ≈ 38%, json+prune ≈ 11% — fsync/flush-bound at this scale, not bytes |
| writer.write + band digests | 0.057 | 4.7% | 10 fields × 24 steps |
| startup residual | ~0.12–0.17 | ~10–14% | metdata 1.9%, geometry recipe 1.6%, publication.complete 1.2%, read_raster 0.5%; remainder = geometry load/verify + interpreter noise |
| comfort (UTCI/WBGT) | 0.012 | ~1% | — |

S09 (D08 streaming checkpoint serialization) attacks the bytes-scaled part of
`save_state` (`_encode` BytesIO copy); at this scene scale checkpoint is
fsync/flush-bound, so the measured ceiling here is ≈1.5–2% of tile. D08 also
fixes checkpoint interval ("No checkpoint interval change under the default
workload"). Deferred pending production-scale evidence.

## 4. Re-rank consequences

1. **R03 (aniLum ordered packed-stream kernel)** — top remaining candidate:
   ~11% of calc, exact arithmetic order preservable per pixel (ordered patch
   accumulation), infrastructure proven (`_fused_descriptor`, `_decode_at`,
   `_fused_guard` in the accepted Lcyl stream). Expected ≈4–6% of tile.
2. **Lside compiled twin** — 4.4% of calc, mechanical A-plus/T01-pattern;
   ≈2–3% of tile. Second.
3. gvf/Lcyl/Kside (~76% of calc combined) — all already on their proven
   compiled routes; kernel-internal only, exactness-frozen lineages.
   Diminishing returns.
4. S07/S09 — measured shares modest at benchmark scale (write 4.7%,
   checkpoint ceiling ~2%); conditional candidates stay conditional.
5. Multi-tile throughput axis: G02 additionally unlocked the compiled GVF at
   threads>1 on f64-Tg scenes (route-tested); batch measurement still owed.
