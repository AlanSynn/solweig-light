# C6-101r evidence: SYNTHETIC 1024² multi-tile campaign + in-sim residual attribution

Date: 2026-09-21. Owner: C6-101r evidence worker. **Every number in this
document is a SYNTHETIC dev-tier single-lease observation** on a host with
unrelated OS/browser/system activity (and other session agents' work) —
**no statistical claims, no actual-target claims**. The 24-spatial-tile
target dataset does not exist (FREEZE_C6-100 "TARGET SCOPE"); this work is a
user-authorized scope extension (recorded 2026-09-21) for full-workload
speedup verification at 1024² and re-opened in-sim residual measurement. It
is a load/comparison fixture, NOT the actual-target dataset, and it does not
redefine the 1800-second objective.

## Trees under test (verified before the first run)

| tree | root | rev measured | src/ delta vs base |
|---|---|---|---|
| integrated | `/Users/alansynn/Workspace/solweig-light-claude-v5` | branch `perf/cpu-optimization`; freeze-time HEAD `4689421c81a9dc9ad5e047bd7ff1dcdd704483b9` (work was tasked at `f9b742a8`) | `git diff --numstat 8e0b3877..4689421c -- src/` = 10 files, +1173/−86 (the C6-70/40/42 integration surface, identical to FREEZE_C6-100's count) |
| base | `/Users/alansynn/Workspace/solweig-light-v6-base-l2` (detached, read-only; removed after the runs) | `8e0b3877c5706a25dfe71c6d1b6270a158c3c07c` | — |

Branch-name note: the integrated branch was renamed
`perf/claude-glm53-cpu-v5` → `perf/cpu-optimization` per user instruction
during this session (renames move no commits; tip hashes above are
unaffected and were verified by rev-parse at freeze time and again after
the runs).

HEAD-move note (recorded, not assumed): the integrated HEAD moved
`f9b742a8 → 30624e02 → a90b10aa → 4689421c` during this session
(`git diff --name-only f9b742a8..4689421c -- src/ tests/` is EMPTY — the
moves are evidence/ledger/branch-rename docs only), and three further
CI/docs commits landed after the campaign (`4689421c..7a37a6f5`, src/tests
delta also empty). All measured processes therefore executed byte-identical
`src/`. Per-run `module_origin` and the freeze-time per-module sha256 table
in `campaign_v1.json` are the authoritative identity records. Nothing was
committed by this task.

## Scene (SYNTHETIC, deterministic, hashed)

`scenes/scene_t1024` — FOUR distinct tiles (`0_0 1_0 0_1 1_1`) at 1024² on a
2×2 spatial grid, dense_urban 32-pixel motif of the C6-80 portfolio-builder
lineage (pinned p7 generator lineage, no RNG), per-tile height AND tree
shift ⇒ distinct content per tile. Input sha256 per tile in
`scene_manifest.json` (Building_DSM/Trees: 4 distinct hashes each; DEM
content is identical by construction, file hashes differ only via
per-tile GeoTransform). Met file is a byte-for-byte copy of the real
own-met `metfile_0_0.txt` of the C6-01 dense256 workload (header + 24
records) for every tile. Pristine layout: no walls/aspect/SVF/cache — all
produced inside the timed stages.

## Protocol (frozen before the first measured run)

Public three-stage workflow, fresh child process per run (C6-01: thread
limits set before any numerical import, mask verified, module origin
asserted, math profile fingerprint recorded), sequential single children
only:

- stage A `walls_aspect`: `api.run_walls_aspect`
- stage B `svf_geometry`: `api.calculate_svf(patch_option=2, overwrite=False)`
  (shared recipe production + export/publication)
- stage C `simulation`: `api.run_utci_tiles`, 10 save flags, 24 records per
  tile, public `execute_tiles` worker transport

Same-resource pairs, pinned identically both trees:
`dataclasses.replace(get_runtime_options(), memory_budget_bytes=12 GiB,
cpu_budget=4, workers=1, threads_per_worker=T, block_pixels=1024,
checkpoint_interval=1, cache_enabled=True, legacy_cache_policy="recompute")`.

Configs: **T4** (workers 1, threads 4 — v5-campaign-comparable) primary;
**S1** (workers 1, threads 1) secondary, predeclared time-conditional
(deadline did not fire; all S1 slots ran). Temps per tree per config:
cold ×2 T4 / ×1 S1 (fresh run dir + fresh `NUMBA_CACHE_DIR`), warm_full ×3
T4 / ×2 S1 (same run dir + same cache; medians). Tree order alternates at
every slot; the schedule was frozen in `campaign_v1.json` before slot 0.
Per-run child timeout 5400 s. 16/16 slots completed, **0 failures,
0 timeouts, 0 skips**.

## PHASE 1 — in-sim residual attribution (SYNTHETIC, one 1024² tile `0_0`, integrated tree, threads=4)

Transport: chronology-probe pattern (`evidence/integration/chronology_probe.py`)
— `runtime.execute_tiles` swapped for an in-process loop over
`pipeline.run_tile` on the same job dicts, so cProfile sees the process.
Slots (`phase1_profile.json`): prime (cold, discarded) → wall ×3 (no
profiler, warm) → profile ×1 (cProfile around the same simulate region).
Native mask 4 verified every slot; `gvf_prepared_step` fired ×14 (of 24
timesteps — the C6-30 prepared route at threads>1).

- prime (cold) sim: 146.87 s — discarded, JIT cache kept
- wall reps: 133.27 / 152.26 / 148.84 s (median 148.84)
- profiled run: 136.12 s sim — profiler overhead is NOT separable from host
  noise here (−8.5% "distortion" vs the median wall rep is the wrong sign;
  rep spread ±7–13% dominates). Shares below are ratios within ONE run and
  are robust to that; absolutes are not.

Additive families (cProfile self time, % of the 136.10 s profiled total;
njit kernels appear as their own entries — that IS the share):

| family | self s | % | notes |
|---|---|---|---|
| visibility decode | 36.76 | 27.0 | `_decode` njit 28.78 cum (116 736 calls) + raw/lazy `decode_patch` 5.83 + descriptors |
| gvf_ground_view | 20.23 | 14.9 | `_gather_block_parallel` njit 18.48 + `_postprocess_block` |
| engine_radiation (body) | 15.80 | 11.6 | `_operate` dispatch 12.49 self, engine assembly, TsWaveDelay, Kup/Kdown/Ldown math |
| patch_radiation | 12.87 | 9.5 | `_classes` 12.28 self etc. |
| cyl_lw | 10.25 | 7.5 | `_longwave_primary` njit 9.36 |
| checkpoint_digest_io | 10.18 | 7.5 | GDAL `Band_FlushCache` 7.03 (24 checkpoints × 10 bands), `_hashlib` 1.84, fsync/read |
| sleef_math | 7.14 | 5.2 | `atan_array` 6.50 — all inside `_classes` |
| wall_shadows | 5.56 | 4.1 | `_wall23_serial` 5.55 (14 calls) |
| numpy core | 5.38 | 4.0 | asarray/zeros dispatch |
| kside_cylsw | 4.52 | 3.3 | `_shortwave_cylinder` njit 4.21 |
| comfort | 4.25 | 3.1 | UTCI 3.57 cum + black-globe 0.70 |
| gvf_prepared wrapper | 0.99 | 0.7 | prepared-snapshot overhead proper |
| everything else | 2.02 | 1.5 | setup/scheduler/dispatcher/IO residue |

Nested cumulative view (engine `Solweig_2022a_calc` = 119.75 s cum = 88.0%
of run_tile; the rest is setup/comfort/checkpoint):

| inside engine | cum s | % of engine | overlap note |
|---|---|---|---|
| cylinder-LW demand (`Lcyl_v2022a_by_demand`) | 37.14 | 31.0 | contains 19.52 s of `decode_block` + 7.12 s of `_classes` |
| Kside wrapper (`Kside_veg_v2022a`) | 31.22 | 26.1 | ≈ entirely `kside_cylinder_anisotropic` (31.20); contains 11.84 s of `decode_block` + 13.46 s of `_classes` |
| GVF dispatcher (prepared route) | 28.53 | 23.8 | gather 18.5 + postprocess 8.4 |
| Lside demanded | 8.45 | 7.1 | 17/24 timesteps still delegate to full engine Lside |
| engine-body residual | 14.40 | 12.0 | estimate = engine cum minus the named parts |

Decode is the single largest measured share, and its compiled part splits
**19.5 s into cylinder-LW channel decode + 11.8 s into Kside/cyl-SW decode**
(+5.8 s raw/lazy Python-side decode). Classification (`_classes`, incl. all
6.5 s of SLEEF `atan_array`) totals ≈ 20.6 s cum ≈ 15% of the run. At warm
T4 the simulate stage is 98.6% of the measured workflow, so these in-sim
shares are effectively whole-workload shares; at COLD, stage B
(production 200 s + export/publication ≈ 217 s) is another 43.6% of the run
(T4 integrated cold median split: walls 5.34 / svf 405.89 / sim 518.89).

## PHASE 2 — paired campaign (SYNTHETIC; seconds; total = A+B+C)

Cold reps reported individually, never blended with warm. Warm = warm_full
medians (per-run values in `campaign_v1.json`/`.jsonl` and child records).

| cell | tree | cold r0 / r1 | cold med | warm r0/r1/r2 | warm med |
|---|---|---|---|---|---|
| t1024_T4 | integrated | 960.03 / 900.31 | 930.17 | 504.70 / 503.21 / 500.79 | **503.21** |
| t1024_T4 | base | 1184.14 / 1142.83 | 1163.48 | 531.41 / 532.67 / 534.67 | **532.67** |
| t1024_S1 | integrated | 1275.84 (×1) | 1275.84 | 863.71 / 859.23 | **861.47** |
| t1024_S1 | base | 1501.18 (×1) | 1501.18 | 938.52 / 913.00 | **925.76** |

Stage medians (walls / svf / sim):

| cell | tree | walls | svf | sim |
|---|---|---|---|---|
| T4 cold | int / base | 5.34 / 5.50 | 405.89 / 416.63 | 518.89 / 741.35 |
| T4 warm | int / base | 4.83 / 4.92 | 1.95 / 1.95 | 496.15 / 525.95 |
| S1 cold | int / base | 5.43 / 5.33 | 397.74 / 396.28 | 872.67 / 1099.57 |
| S1 warm | int / base | 4.89 / 4.90 | 1.94 / 1.97 | 854.64 / 918.89 |

Speedup base→integrated (best-rep for cold; medians for warm — both stated):

| comparison | total | sim stage |
|---|---|---|
| T4 cold | **1.251×** (median basis; 1.269× best-rep) | 1.429× |
| T4 warm | **1.059×** | 1.060× |
| S1 cold | **1.177×** | 1.260× |
| S1 warm | **1.075×** | 1.075× |

Mechanism notes (dev-tier, from the records):

- Cold: the base duplicate geometry identity persists (cache census: base 8
  entries = 2 keys/tile vs integrated 4 = 1 shared recipe key/tile — the
  C6-02 shape); the duplicate production runs inside worker children during
  stage C, which is where the cold sim gap (741.4 → 518.9 median) appears.
- Warm: svf collapses to ≈1.95 s both trees; integrated keeps a ≈6–7.5%
  sim lead (unlike the C6-80 warm wash at 128/256²) — consistent with the
  integration's demand-specialized radiation paths, but this tier cannot
  split mechanism from host noise; treat as directional.
- The C6-40 phase route did not fire anywhere (`workers=1`; gate needs
  workers>1) — by design; `svf_phase_calls=0` in every record.
- Parent-side route wrappers saw no stage-C events (worker transport), as
  in C6-80; route identity at threads=4 rests on the PHASE 1 in-process
  observation (`gvf_prepared_step` ×14) plus the C6-70f/g wiring reviews.

## Output integrity (bitwise parity)

Per-tile simulation-TIFF sha256 across **all 16 slots, both trees, both
configs, all temps: ONE digest per tile** — `0_0`
`b588c9aaaf8f0c56…`, `1_0` `3bde41a404508003…`, `0_1`
`6920615e3444a432…`, `1_1` `8cf33ecc2943a19f…` (10 files per tile per run:
Kdown Kup Ldown Lup Shadow TMRT Ta UTCI WBGT Wind). **Any mismatch would
have been recorded verbatim; there was none.** Full-tree manifest digests
churn only from ZIP/NPZ member timestamps (svfs artifacts), the known
C6-80/C6-100 artifact churn. Math profile fingerprint identical in every
child record: `8e4d38460b61b029…cbef30` (`solweig-portable-sleef-5a1d179d-v1`).

## Cross-check vs the v5 final campaign (honest gap accounting)

v5 CAMPAIGN_v1: dense1024 candidate 289.765 s (thermal_comfort only, ONE
real-fixture 1024² tile) / vegetation1024 302.396 s. This campaign's
integrated T4 warm sim is 496.15 s for FOUR synthetic motif tiles ≈ 124 s
per tile — same order of magnitude, ≈ 2.3× below the v5 per-tile number.
Plausible drivers (not separately measurable here): (a) different scene —
the synthetic 32-px motif has different building/ray-liveness structure
than the real dense fixture (v5 itself showed dense vs vegetation scenes
differ by 1.13–1.38×); (b) accounting — v5's 289.8 s is `thermal_comfort`
only while v5's standalone SVF pass sat nearly outside its wall, whereas
stage B here carries full recipe production + export/publication INSIDE the
timer; (c) the integrated tree adds the v6 wave-1 work (prepared GVF etc.)
on top of the v5 candidate; (d) host load differs. This cross-check supports
"same order of magnitude" only; the paired base-vs-integrated comparison on
the SAME scene is the evidence this campaign contributes.

## Host honesty (recorded per run, not assumed)

Campaign: loadavg(1) before each of the 16 runs — min 5.1, median 7.1, max
11.5; 3/16 slots had a busy non-browser process above the 50% snapshot
threshold. PHASE 1 ran under a heavier transient (loadavg spiked to ≈50
during the wall reps — visible in the ±13 s rep spread). Exclusivity is
claimed **only** as "no competing program work of this task alongside":
strictly sequential single children, no pytest/builds/profilers during timed
runs; unrelated OS/browser/system activity and other session agents' work
were present and are preserved in the per-slot `host_before`/`host_after`
snapshots. All deltas are dev-tier.

## Known imperfections (recorded)

- Cold r0 child records were removed by cold r1's fresh-run-dir rmtree
  (same as C6-80); cold r0 timings and digests survive in
  `campaign_v1.json`/`.jsonl`, so no measured cell is lost — but detailed
  `store_calls`/per-file manifests survive only for cold r1 and warm runs.
- Profiler distortion is inseparable from host noise at this tier (PHASE 1);
  attribution shares are single-run ratios.
- One synthetic scene/motif; results are not a scene distribution.
- 1024² tile in PHASE 1 profiled in-process — transport differs from the
  campaign's worker transport by design (profiler visibility), quantified by
  the wall reps.
- No actual-target claims, no statistical claims, no release claims;
  nothing committed; base worktree removed after clean verification.

## C6-81 selection input (measurement + ranking ONLY; nothing implemented)

Ranked by measured share × dossier-08 plausibility:

1. **Visibility decode ≈ 27% of in-sim** — candidates **D02**
   (microtile/transposition/batch decode) and **S08** (native visibility
   block-local mode). Mechanism warning: the C6-50 **prepared one-entry
   decoder is a measured loss** (+21–24%/sweep at 128–256², preflight does
   not amortize with size, default-DECLINED `46450c75`) — decode work must
   NOT re-try that variant; D02/S08 attack locality/batching instead. The
   decode share splits cyl-LW 19.5 s / Kside-cyl-SW 11.8 s / raw-lazy 5.8 s,
   so a cylinder-channel decode fix covers most of it.
2. **Patch classification `_classes` ≈ 15% cum (12.3 s self + 6.5 s
   atan32)** — candidates **R04** (exact coefficient finite-state tables)
   and **G06** (exact emission/thermal classes for the LW part). R04's stop
   condition "poor if lookup dominates" does NOT bite here: classification
   compute, not lookup, is the cost, which is the favorable case for R04.
3. Honorable mentions by share: **G05** prefix/repeated-add replay (GVF
   postprocess + wall terms; GVF 14.9% + wall_shadows 4.1%), **R09**
   compiled ordered aniLum (Lside 7.1% cum, only 17/24 timesteps currently
   delegate to full Lside), **S01** one-pass stored export verification
   (cold-only: export/publication ≈ 217 s ≈ 23% of a cold T4 run, absent at
   warm), **S04/S05** comfort (3.1% — small; S05's "Horner already failed"
   caution stands).

Selection input only — dossier-08's activation rules and the VALIDATION
POLICY govern any implementation; this document measures and ranks.

## Artifacts

- `README_C6-101r.md` — this record
- `scene_manifest.json`, `scenes/scene_t1024/` — scene provenance + hashes
- `phase1_profile.json` / `.jsonl` — frozen PHASE 1 protocol + 5 slot records
  with host snapshots; `phase1_attribution.json` — computed tables
- `runs/profile_t1024_tile0_0/records/*.json`,
  `runs/profile_t1024_tile0_0/pstats/profile_r0.pstats[.txt]` — PHASE 1
  child records + pstats dumps
- `campaign_v1.json` / `.jsonl` — frozen PHASE 2 protocol + 16 slot records
  with host snapshots; `campaign_verdict.json` — computed tables
- `runs/t1024_T4/<tree>/records/*.json`, `runs/t1024_S1/<tree>/records/*.json`
  — full child records (stage splits, store/export/phase calls, cache
  census, per-tile output digests, options, telemetry)
- `runs/.../run_scene/` — last-state run dirs (cold r1 state + warm reuse)
- `tools/` — `build_scene1024.py`, `profile_child.py`, `run_phase1.py`,
  `campaign_child.py`, `run_campaign.py`, `analyze_phase1.py`,
  `analyze_campaign.py`, `thread_limits.py` (C6-01/C6-80 reuse)
- `phase1_console.log`, `campaign_console.log` — console provenance
