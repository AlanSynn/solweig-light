# S10-02 route census — Tgwall singleton fallback (distilled)

Date: 2026-10-13. Repo head: `ec4298ae` (branch `perf/s10-semantic-systems`).
Raw evidence (outside git): `/storage/scratch1/1/dsynn6/solweig-light-s10-raw/census/`
(script `census_s10_02.py`, per-run records, `census_summary.json`; uploaded to
Dropbox `Alan Synn/Research/solweig-light/s10/census/`).

## Protocol

Fixture `tests/reference/small_original_cpu` (32x35 synthetic scene, 24-step
chronology 2020-07-18). Two configurations, identical scene rasters:

- **A0** `landcover_filename=None` (fixture default) — wall params are Python
  floats (`pipeline.py:150-153`).
- **A1** synthesized deterministic `Landcover.tif` (classes {2,5,6}, sha256 of
  raster bytes in `census_summary.json`) — wall params are `(1,1)` arrays
  (`pipeline.py:146-149` -> `materials.py:47-50`).

In-process `pipeline.run_tile` per rep (1 cold + 2 warm, alternating order),
diagnostic wrappers on `patch_radiation.Lcyl_v2022a` and
`patch_radiation.define_patch_characteristics`, per-call wall time + descriptors.

Census-only admission deviation (documented, no product change): GDAL-cache
charge capped at 256 MiB and `memory_budget_bytes=5.5 GB` because the shipped
model charges 5% of physical RAM (18.8 GB) while this Slurm step cgroup allows
5.86 GB headroom. See "New product finding" below.

## Results

| run | e2e (s) | dpc calls | rejected by Tgwall rank | dpc time |
|-----|---------|-----------|--------------------------|----------|
| A0 cold | 9.83 | 0 | 0 | 0 |
| A1 cold | 9.96 | 14 | **14** | **1.309 s** |
| A0 warm | 8.62 / 5.99 | 0 | 0 | 0 |
| A1 warm | 9.02 / 13.82 | 14 | **14** | **1.303 / 1.309 s** |

- Production demand is `PIPELINE_CYLINDERS_ANISOTROPIC` (primary-output route),
  so the entry is `cylinder_longwave.Lcyl_v2022a_primary`; its guard
  (`cylinder_longwave.py:432`, same clause in `patch_radiation.py:1033`)
  rejects `Tgwall` with `ndim != 0` and falls back to the serial reference for
  the whole daytime longwave, every daytime step.
- Tgwall descriptor at the guard: **shape (1,1), dtype float64** — the f32
  cast at `pipeline.py:149` is re-promoted to f64 by `altmax` multiplication
  (`engine.py:1579-1581`), and the rank survives to every consumer.
- Per-step serial reference time: 92.3-94.3 ms on a 1120-pixel tile
  (~14% of warm E2E at this tiny scale; production 1024² tiles are ~93x
  larger, where the serial reference is O(pixels x patches) Python-block work
  vs the O(pixels) compiled primary).
- A0 (scalar wall params): zero rejections — the primary path is admitted.
  **The Landcover raster is the trigger.**

## Verdicts

- **T01**: CONFIRMED statically and dynamically. Fix scope: the four strict
  `ndim != 0` guard clauses (`cylinder_longwave.py:376,432`,
  `patch_radiation.py:983,1033`) plus rank normalization (U-profile
  preparation) that preserves arithmetic order, dtype promotion (f64!),
  and the `(1,1)`-broadcast semantics of the reference expressions.
- **G01**: dispatch-level evidence — `gvf_prepared` is never entered at
  threads=1 (`engine.py:1757` routes straight to serial); with Landcover the
  prepared guard would reject anyway at H>1 because Tgwall arrives f64, not
  f32 (`gvf_prepared.py:103`).
- **New product finding (S03-adjacent)**: memory admission is infeasible by
  default on container-limited hosts — the charge side prices the GDAL cache
  at 5% of *physical* RAM (`runtime_memory.py:485-494`) while the budget side
  honours cgroup headroom (`runtime.py:245-300`); on a 376 GB node inside a
  6 GB Slurm step every default run is refused regardless of actual usage.
  Registered as a candidate; needs its own gate (changes default admission
  semantics).

## Threats to validity

- Shared login-class node (loadavg 16-19 during runs); absolute times are
  noisy — per-stage contrasts (dpc on/off) are the decision metric, and the
  14/14-vs-0/14 admission split is deterministic, not timing-dependent.
- A1 vs A0 E2E differ by more than the longwave stage (LC feeds GVF/TsWave
  inputs); only the dpc-stage delta is attributed to T01.
