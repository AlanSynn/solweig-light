# C6-80 evidence: small cold/warm distinct-tile portfolio (integrated vs baseline)

Date: 2026-09-21. Owner: C6-80 evidence worker. All numbers are **dev-tier
single-lease observations** on a host with unrelated OS/browser system
activity (below) — **no statistical claims, no actual-target claims** (the
24-tile target dataset is still absent). Timing claims come only from these
lease runs.

## Trees under test (verified before the first run)

| tree | root | HEAD | content |
|---|---|---|---|
| integrated | `/Users/alansynn/Workspace/solweig-light-claude-v5` | `76bcd2881440…` (branch `perf/claude-glm53-cpu-v5`) | task tip `3f3e8b8d` + one ledger/review-docs commit; **src/ byte-identical to 3f3e8b8d** (`git diff --stat 3f3e8b8d..76bcd288` touches only evidence docs) |
| base | `/Users/alansynn/Workspace/solweig-light-v6-base-l2` (detached, read-only for this task) | `8e0b3877c570…` | wave-1 modules landed but **unwired** (no C6-70 call sites, no `runtime_phases.py`, no api phase admission). The diff `8e0b3877..3f3e8b8d` is exactly the integration surface: api.py, service.py, pipeline.py, engine.py, ground_view.py, gvf_postprocess.py, patch_radiation.py, runtime.py (+6 C6-42 lines), runtime_phases.py (new) |

So this portfolio measures **the C6-70/C6-40/C6-42 integration wiring
itself**: shared geometry key (C6-70a), C6-40 GEOMETRY phase barrier, demand
dispatch (C6-70c-e), prepared GVF (C6-70f/g), decoder wiring (C6-70h),
demand-scope fixes (C6-70i), C6-42 phase admission + GDAL_CACHEMAX (C6-70b).

## What was measured (public workflow, three timed stages)

Fresh child process per run (C6-01 discipline: thread env set before any
numerical import, mask verified via `numba.config` + `set_num_threads`,
module origin asserted, math profile fingerprint recorded). Inside each child,
the public post-preprocess workflow of `thermal_comfort`:

- **stage A `walls_aspect`** — `api.run_walls_aspect(preprocess_dir)` (geometry production)
- **stage B `svf_geometry`** — `api.calculate_svf(prep, patch_option=2, overwrite=False)` (shared-recipe production + export/publication; C6-40 phase barrier when its gate fires)
- **stage C `simulation`** — `api.run_utci_tiles(..., 10 flags)` → `execute_tiles` persistent worker children, 24 records per tile

Component separation uses call-through wrappers only (no numerics altered):
`GeometryStore.get_or_create` producer timing, `prepare_geometry_exports`
totals, `runtime_phases.execute_geometry_phase` wall (integrated only), plus
the final cache census. Stage C runs in worker subprocesses, so parent-side
wrappers see nothing of stage C internals — the base cold duplicate is
therefore proven by the cache census and appears **inside** `simulation`.

Same-resource pairs: identical `RuntimeOptions` both trees via
`dataclasses.replace(get_runtime_options(), memory_budget_bytes=12 GiB,
cpu_budget=4, workers=W, threads_per_worker=T, block_pixels=1024,
checkpoint_interval=1, cache_enabled=True, legacy_cache_policy="recompute")`
— the budget is pinned because the auto budget is availability-sensitive.

Configs: **S1** = workers 1, threads 1 (serial default); **P2** = workers 2,
threads 1 (phase gate: >1 pending tile + cache on + workers>1); **T2** =
workers 1, threads 2 (prepared-GVF threads>1 branch). Temps per cell:
**cold** x2 (fresh run dir + fresh `NUMBA_CACHE_DIR`: cold geometry cache,
cold JIT, inside timer), **warm_geom** x1 (S1 only: same run dir, fresh JIT
cache — isolates geometry-cache warmth), **warm_full** x3 (same run dir +
same JIT cache — steady state; medians reported). 64 measured runs, one at a
time, 900 s per-run timeout, **0 failures, 0 timeouts, no retries**.

## Scenes (deterministic, distinct tiles; hashed)

`scenes/scene_t128`, `scenes/scene_t256` — 2 tiles each (`0_0`, `1_0`), each
tile 128² / 256², dense_urban 32-pixel motif (pinned p7 generator lineage, no
RNG), per-tile height/tree shift ⇒ **distinct content per tile (sha256
distinct, `scene_manifests.json`)**; real own-met file byte-for-byte from the
C6-01 dense256 workload (header + 24 records). Pristine layout has no
walls/aspect/SVF/cache — all produced inside the timed stages.

## Portfolio table (seconds; stage sums; per-run values, medians for warm_full)

Legend: total = A+B+C measured (excludes interpreter+import, recorded
separately in child records). Full per-run stage values in
`portfolio_v1.json` / `portfolio_v1.jsonl`.

| cell | tree | cold r0 / r1 (total) | cold med | warm_full r0/r1/r2 | warm med |
|---|---|---|---|---|---|
| t128_S1 | integrated | 20.55 / 22.15 | 21.35 | 10.16 / 9.62 / 9.99 | **9.99** |
| t128_S1 | base | 23.45 / 22.16 | 22.80 | 9.78 / 9.87 / 9.89 | **9.87** |
| t128_P2 | integrated | 20.50 / 18.11 | 19.31 | 7.26 / 7.19 / 7.58 | **7.26** |
| t128_P2 | base | 18.89 / 18.44 | 18.66 | 6.24 / 6.45 / 6.30 | **6.30** |
| t128_T2 | integrated | 19.46 / 19.95 | 19.71 | 9.23 / 8.24 / 7.91 | **8.24** |
| t128_T2 | base | 20.98 / 20.99 | 20.99 | 8.01 / 8.16 / 7.90 | **8.01** |
| t256_S1 | integrated | 48.54 / 48.75 | 48.65 | 31.06 / 31.28 / 30.95 | **31.06** |
| t256_S1 | base | 53.86 / 53.98 | 53.92 | 31.18 / 31.18 / 30.84 | **31.18** |
| t256_P2 | integrated | 34.60 / 35.33 | 34.96 | 17.81 / 18.01 / 19.69 | **18.01** |
| t256_P2 | base | 39.42 / 39.08 | 39.25 | 17.20 / 17.08 / 18.09 | **17.20** |
| t256_T2 | integrated | 41.45 / 40.41 | 40.93 | 21.64 / 21.60 / 22.41 | **21.64** |
| t256_T2 | base | 50.15 / 47.52 | 48.83 | 22.32 / 22.74 / 21.51 | **22.32** |

Stage medians per cell (walls / svf / phase / sim):

| cell | tree | walls | svf | phase | sim |
|---|---|---|---|---|---|
| t128_S1 | int / base | 0.51 / 0.47 | 2.83 / 2.92 | – | 18.01 / 19.42 |
| t256_S1 | int / base | 0.61 / 0.61 | 10.48 / 10.11 | – | 37.56 / 43.21 |
| t128_P2 | int / base | 0.53 / 0.49 | 3.88 / 2.88 | 2.73 / 0 | 14.89 / 15.29 |
| t256_P2 | int / base | 0.65 / 0.62 | 9.61 / 10.27 | 5.13 / 0 | 24.70 / 28.37 |
| t128_T2 | int / base | 0.50 / 0.48 | 2.87 / 2.78 | – | 16.34 / 17.73 |
| t256_T2 | int / base | 0.60 / 0.62 | 10.39 / 10.76 | – | 29.95 / 37.45 |

Warm_geom (S1, JIT cold again): int 17.66 / base 17.84 (t128), int 36.98 /
base 38.48 (t256) — geometry-cache warmth alone buys the same on both trees;
the remaining warm gap to warm_full is JIT compile, identical both trees.

## Component separation

- **Cold duplicate (the C6-02 two-identity-dictionary defect), eliminated at
  integrated.** Cache census after every run: **base 4 cache entries vs
  integrated 2** (2 tiles; base stores a standalone key
  (`standalone_implementation`) AND a pipeline key; integrated stores ONE
  shared recipe key per tile — the standalone export production carries the
  pipeline key, verified in `store_calls`). Cost signature, t256_S1 cold sim:
  base 43.21 s vs integrated 37.56 s (−13%); the base duplicate production
  (~2.8 s/tile x 2) runs inside worker children and is included in `sim`.
  At warm the base cache also serves its second key, so the warm sim delta
  closes to a wash (30.83 vs 30.73 median) — exactly the expected shape.
- **Export/publication:** stage B minus production (t256 cold: integrated
  10.42 total, 6.12 production ⇒ ~4.3 publication/compare; fast-hit warm B
  ≈ 0.13 s both trees). Publication cost is unchanged by the integration;
  the phase route moves production out of stage B but keeps publication in
  the serial loop (by design, D04).
- **Simulation:** dominates at every shape (14–43 s of 19–54 s totals);
  the integration's cold wins come mostly from here (duplicate removal +
  demand specialization + prepared GVF + decoder effects all inside).

## Verdicts

1. **Serial default (S1) cold:** integrated **−6.4%** (t128 21.35 vs 22.80)
   and **−9.8%** (t256 48.65 vs 53.92) — single-run paired observations.
   **Warm steady state: a wash** (t128 +1.2%, t256 −0.4% medians; spread
   between reps is of the same order). The warm wash says the integration
   does not regress steady state, but its cold win is one-time (duplicate
   removal + first-run specialization) — at this tier.
2. **Phase route (P2) at its activation gate (2 tiles, workers=2, cache on):**
   fires only at integrated (verified: `phase_calls=1`,
   `phase_publication_files` journal+manifest present; base P2 has no phase
   by construction). **t128: net negative.** The phase wall (2.51–2.95 s for
   both tiles) does not beat the serial svf stage it replaces (2.88–2.97 s),
   and stage B ends at 3.6–4.2 s vs base 2.8–3.0 s — child spawn + barrier
   overhead dominates small tiles; the P2 cell still beats serial S1 overall
   (19.31 vs 21.35 cold) because 2-worker simulation parallelizes stage C,
   but base P2 gets the same stage-C benefit (18.66 cold, 6.30 warm vs
   integrated 19.31 / 7.26). **t256: pays off.** Phase wall 4.71–5.55 s vs
   base serial svf 10.2–10.3 s — concurrent production roughly halves the
   geometry stage; integrated P2 cold 34.96 vs base P2 39.25 (−10.9%) and vs
   integrated S1 48.65 (−28%). Warm caveat: I called the public
   `calculate_svf` wrapper (`validate_existing=True`), under which every tile
   stays pending on every run, so the phase re-fires at warm P2 (~0.9 s
   fixed spawn overhead, visible in the warm medians). The production
   `thermal_comfort` calls with `validate_existing=False`, where warm pending
   is empty and no phase spawn happens — the S1 warm cells demonstrate that
   path (B ≈ 0.08 s). Under the production semantics the warm phase overhead
   does not occur.
3. **threads=2 (T2, prepared-GVF branch active at integrated):** native mask
   verified 2 both trees (parent; worker children get the same env via
   `_child_environment`, phase children self-verify with an assertion).
   Cold: integrated −6.1% (t128) and **−16.2%** (t256, 40.93 vs 48.83; sim
   stage alone 29.95 vs 37.45). Warm_full medians: t128 +2.9% (integrated
   worse, within rep spread), t256 −3.0%. The integrated threads>1 branch is
   the biggest cold winner at 256 after the S1 duplicate removal.
4. **Prepared decoder (C6-50, wired only at integrated): HURTS at both
   shapes.** Re-measured with the C6-50 probe construction (warm JIT,
   best/mean of 30, census thread cap 2, read-only reuse of the decoder
   test builders) at both shapes and both block strides:
   t128/128px 58.3 vs 72.0 ms (reproduces the recorded 58.1 vs 71.6),
   t128/1024px 55.4 vs 66.8, t256/128px 236.7 vs 288.8, t256/1024px
   222.7 vs 268.7 — the prepared one-entry path is **+21–24% slower** per
   full-frame sweep at every cell (`decoder_probe/*.json`; caller-buffers
   variant no better; prepare-only ~5 µs). The preflight scan does not
   amortize with size. Its cost is inside the integrated stage-C numbers
   above — integrated still wins cold, and the warm wash is partly the
   decoder eating back the specialization gains. For C6-81: **decline the
   decoder wiring for latency**; keep adoption arguments to
   exactness/memory-profile only (per the C6-50 note).
5. **Output integrity:** all 64 runs published bitwise-identical simulation
   TIFFs per shape — one digest per shape across both trees, all configs,
   all temps (`simulation_tiff_digest` `fcffb12a…` t128, `6088d728…` t256;
   20 files = 2 tiles x 10 outputs). Consistent with the L2 chronology
   differential. Full-tree manifest digests churn only from ZIP/NPZ member
   timestamps (svfs artifacts), not numerics.

## Telemetry (actual, recorded per run)

- Math profile identical both trees: `solweig-portable-sleef-5a1d179d-v1`,
  fingerprint `8e4d3846…bef30` (full identity in every child record).
- Python 3.11.16, numpy 2.4.6, numba 0.67.0, llvmlite 0.49.0, arm64.
- Native mask: requested == `config.NUMBA_NUM_THREADS` == `get_num_threads()`
  at every S1/P2 run (1) and T2 run (2); threading layer `workqueue`;
  `set_num_threads` verified before imports. P2 admission: 2 workers x 1
  thread; parent peak RSS 184–188 MB (workers are separate processes and are
  not summed).
- GDAL_CACHEMAX was unset in the parent env; the C6-42 worker cap applies in
  the worker/phase children via `_child_environment` (value recorded in the
  run env; parent-side `GDAL_CACHEMAX` env was None).
- `PYTHONPATH` pinned to the tree's `src/` in the child environment so the
  `execute_tiles`/phase worker children (`python -m
  solweig_light.runtime_worker`) import the tree under test — the
  installed-wheel deployment parity.
- Parent-side GVF route wrappers recorded no events: stage C runs in worker
  subprocesses (public `execute_tiles` route), so leaf-level route telemetry
  is not observable from the parent. Route identity for the threads>1 branch
  rests on the C6-70f/g wiring and reviews, not on this run's observation.

## Host honesty (recorded, not assumed)

Load average before each of the 64 runs: min 5.9, median 11.2, max 16.4
(1-min) — the documented unrelated system activity (WindowServer, Palo Alto
`pmd`, Chrome helpers) was present throughout. 12/64 slots had a busy
non-browser process above the 50% CPU snapshot threshold (pmd x3,
duetexpertd x2, Orca Helper x5, ControlCenter x1, managedsoftwareupdate x1);
full before/after `ps` snapshots per run are in `portfolio_v1.json`. No
local program work of this task or other agents ran alongside: all measured
runs are strictly sequential single children. Exclusivity is claimed **only**
in that sense; the host was NOT quiet, so treat all deltas as dev-tier.

## Known imperfections (recorded)

- The harness deletes the run root on every cold run, so each cell's cold r1
  removed cold r0's child-record file; cold r0 lives on only as its slot
  summary in `portfolio_v1.json/jsonl`. Both colds were genuine fresh-cache
  runs, so timing is unaffected; the detailed `store_calls`/per-file hashes
  survive for cold r1 and all warm runs.
- Warm P2 cells used the public `calculate_svf` (`validate_existing=True`)
  semantics — see verdict 2 for what that means.
- Single-lease dev tier with unrelated system load: no statistical claims;
  warm_full medians are dev-tier paired observations (3 reps).
- No 96x96 chronology scene was used for timing; no actual-target claims;
  synthetic two-tile batches are load/comparison fixtures, not the 24-tile
  dataset.

## Artifacts

- `portfolio_v1.json`, `portfolio_v1.jsonl` — frozen protocol + 64 slot records with host snapshots
- `runs/t<128,256>_<S1,P2,T2>/<tree>/records/*.json` — full child records (stage splits, store/export/phase calls, cache census, output manifests, options, telemetry)
- `runs/.../run_scene/` — last-state run dirs (cold r1 state + warm reuse)
- `decoder_probe/t{128,256}_stride{128,1024}.json` — decoder re-measurement
- `scene_manifests.json`, `scenes/` — scene provenance + hashes
- `tools/` — `build_scene.py`, `portfolio_child.py`, `run_portfolio.py`, `decoder_probe_v2.py`, `thread_limits.py` (C6-01 reuse)

## C6-81 readiness

Clean enough for a **directional** residual choice at this tier: cold wins
are real and repeatable across both shapes (S1 −6/−10%, T2 −6/−16%, P2 −11%
at 256 only), warm steady state is a wash, the phase route is net negative
at 128 tiles and positive at 256, and the decoder wiring is a consistent
loss worth declining. NOT clean enough for fine-grained (<5%) adoption
decisions or any release claim: medians move by more than that between reps
under this host load, and every number here is dev-tier synthetic-batch.
