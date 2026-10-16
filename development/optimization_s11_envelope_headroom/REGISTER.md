# S11 envelope-headroom register (live)

Follow-on campaign from S10 (branch `perf/s11-envelope-headroom`, cut from
`perf/s10-semantic-systems` @ 52ad17c8). Baseline chain: the S10-36 A-arm
(walls 20.0 + svf 4063.1 + run 2529.7 = 6612.8 s = 110.2 min, 24×1024² tiles,
24 steps, 3×8 pinned). Raw evidence:
`/storage/scratch1/1/dsynn6/solweig-light-s11-raw/` (outside git; archived to
Dropbox `Alan Synn/Research/solweig-light/campaign_s11/`). Protocols are
frozen in `evidence/` before any timing.

| # | ID | mechanism | expected E2E effect (bound) | evidence status | risk | disposition |
|---|----|-----------|------------------------------|-----------------|------|-------------|
| 1 | X01 | SVF export-loop concurrency: the serial parent loop (read-back bitwise verify + atomic staged publication, **2708.2 s measured in the X02 E2E arm**) runs per-tile concurrent (spawn process pool, degree = runtime.workers, gated on cache_enabled) | **ACCEPTED, MEASURED E2E (job 14096139, x01_b1)**: export stage 2708.2 → 919.5 s (**2.946×**; ideal 3-way ≈ 903 s; gate ≤2200 ✓); chain 5636.2 → 3838.3 s = 64.0 min = **1.723× overall** vs the S10-36 A-arm (1.468× vs X02-only); svf phase 3055.0 → 1271.7 = **3.19×**; barrier 352.2 (+1.5%, in band); run 2545.9 (−0.6%, in band); **bitwise 24/24 SVF vs p1c_svf_base38 + 24/24 TMRT bands vs p2_ref_TMRT.tif**; projection matched (3831 predicted, +0.2%) | **MEASURED BITWISE PASS 24/24 tiles** (x01_b1.json); review ACCEPT WITH NOTES (phase1_x01_review.md): N2 gate fix + N1/N3 docstrings landed post-E2E (94cd7b50), battery A/B byte-identical 184-failure pre-existing set, +1 gate-pin test | documented contract amendment: publication order = completion order, failure truncation = completed set; stage gated on cache_enabled (children are cache-hit readers under the admitted phase envelope); instrument miss: per-tile child walls unrecorded (sitecustomize hook did not fire in spawn children) — stage-level gate metric unaffected, recorded | **ACCEPTED 2026-10-16 (987fbd82 + review fixes 94cd7b50); R11 next** |
| 2 | X02 | SVF pixel-parallel twin dispatch at the DEFAULT 3×8 shape: `shadows.shadow` routes on the static bush predicate — positive max → step-major serial (unchanged regime), zero/NaN-poisoned max → `sky_compiled.shadow_pixel_parallel` | **ACCEPTED, MEASURED E2E (job 14094558, x02_b1_38)**: svf phase 4063.1 → 3055.0 s (**1.331×**, barrier 1356.2 → 346.8 = 3.91×, export loop parity 2708.2); chain 6612.9 → 5636.2 s = 93.9 min = **1.173× overall**, run phase 2561.0 (+1.25% vs A-arm, in band); **bitwise 24/24 SVF vs p1c_svf_base38 + 24/24 TMRT bands**; review ACCEPT WITH NOTES (phase1_x02_review.md; 49/49 adversarial probes) | **MEASURED BITWISE PASS 24/24 tiles** (p1c_bitwise.json; k=4.13@8t, 2.70@4t; barrier scaling ~75%/worker; bush_max=0 scope note) | dispatch diff small; compile cost 3.1 s cached; 5×4 shape REJECTED — admission-refused at live budget 36.4 GiB (only 3 fit) AND dominated by twin at 3×8 (3055.0 < 3101.9) | **ACCEPTED 2026-10-16 (commits 9133c693 + docstring follow-up); X01 next** |
| 3 | R11 | run-phase engine: clean 8-thread per-tile engine **264 s** (86% in 14 day steps 15.3-19.0 s; night 3.5-4.3 s; clean day/night 4.2×); 8→24 threads only +1.5% (ceiling); cProfile-inflated phase0 shares usable only relatively (prepared GVF, Lcyl region pool, Kside aniso top) | anomaly RESOLVED (paired probe, job 14097751): the 508 s "standalone" was a **1-thread child** (`threads_per_worker` overrides job-level NUMBA env in `_child_environment`; execute_tiles always spawns children); standalone-8t ≈ pool (307.5/309.3 vs 328.2/331.8 s) — **no placement/pool effect**; candidate opened: run-phase worker shape (e.g. 6×4), break-even trivially met, bound by C6-42 admission (live budget fits only 3 jobs) | **MEASURED PAIRED PROBE** (`evidence/phase2_r11_probe_findings.json`; TMRT bitwise pass in all 6 arms; A_low reproduces p2_clean within drift; child seams clean, no profiler) | frozen C5/C6/N8/N9 lineages bound the leaf kernels; scheduling/admission-calibration only; no timestep parallelism; D arm (1×24) diagnostic-only, not a product config | **probe complete — candidate protocol next** |
| 4 | — | UTCI parallel dispatch | ≤1.013× on run (7.1 s of 548.8) | measured share; wall parity 501.95 vs 508.24 s | none — dominated | **REJECTED** (measured) |
| 5 | — | InputGuard optimization | guard at raw-sha floor (+0.3 ms/40 ms) | measured | metadata shortcut inexact (rejected) | **REJECTED** (measured) |
| 6 | — | worker shapes >5 (6×4, 12×2, 24×1) | admission-refused at default budget ('only 5 fit') | measured table | 220G out of scope | **REJECTED** (admission) |
| 7 | — | 2×12 shape | fewer workers, serial kernel — dominated | measured: worse than 4×6 | none | **REJECTED** (dominated) |

Notes:

- S11-1 PHASE 0 COMPLETE (2026-10-16, jobs 14084547 + 14085192 + 14087232;
  `evidence/phase0_attribution.json`): M1-M6 all measured; product source
  untouched (freeze assertions at every job start). Key structural findings:
  (a) the SVF phase is NOT kernel-dominated — the serial parent export loop is
  66.7% of the phase and 41.2% of the whole chain (e = 0.667, not the Astra
  0.2-0.5 range); (b) the parked twin is bitwise-exact and real: 1.312× whole
  phase at 5×4, barrier 3.82×; (c) admission caps workers at 5 (default ~47.6
  GiB budget); (d) run phase is engine-dominated (95%) with a 5.2× day/night
  bimodal; (e) UTCI immaterial (1.3%); (f) guard at hashing floor; (g) the
  public 1-step corner is contract-unsupported (metfile >2 rows required).
  Chain floors: X02 alone 94.2 min (1.17×); X01+X02 ~58.7-63.6 min
  (1.73-1.88×, projection). Raw records + SVF snapshot corpus (~1.9 GB
  bitwise evidence) archived to Dropbox `campaign_s11/phase0/`.

- S11-2 X02 ACCEPTED (2026-10-16, job 14094558; `evidence/phase1_x02_protocol.json`
  frozen pre-timing at d03519bb, review `evidence/phase1_x02_review.md`): the
  twin dispatch landed at the DEFAULT 3×8 shape. Measured chain: walls 20.2 +
  svf 3055.0 (barrier 346.8 + export 2708.2) + run 2561.0 = 5636.2 s = 93.9 min
  = 1.173× overall vs the S10-36 A-arm 6612.9 s; bitwise 24/24 SVF vs
  p1c_svf_base38 + 24/24 TMRT bands. The 5×4 shape arm was admission-refused
  at the live budget (36.4 GiB — only 3 jobs fit; was 47.6 GiB at Phase 0) and
  is dominated by the twin at 3×8 anyway (3055.0 < 3101.9): shape policy stays
  default. Review: ACCEPT WITH NOTES — structural correction adopted (the old
  wrapper was already hybrid; the identity is _pixel_parallel == _pixel_serial),
  49/49 adversarial probes bitwise, docstring precision fixed post-E2E. Two
  pre-timing driver submissions (14094324, 14094369) died at protocol
  assertions before any timed pass; phase0/prime_64.json was briefly
  overwritten by the first and restored byte-identical from its sha-verified
  archive. Raw phase1 records archived to Dropbox `campaign_s11/phase1/`.

- S11-3 X01 ACCEPTED (2026-10-16, job 14096139; `evidence/phase1_x01_protocol.json`
  frozen pre-timing at 2614c397, review `evidence/phase1_x01_review.md`): the
  per-tile export loop runs as a spawn-pool concurrent stage on top of the
  accepted X02 dispatch. Measured chain: walls 20.8 + svf 1271.7 (barrier 352.2
  + export stage 919.5) + run 2545.9 = **3838.3 s = 64.0 min = 1.723×** vs the
  S10-36 A-arm 6612.9 s — the pre-registered projection (3831 s) matched to
  +0.2%. Export stage 2708.2 → 919.5 s = **2.946×** (ideal 3-way ≈ 903 s;
  acceptance gate ≤ 2200 ✓). Bitwise 24/24 SVF vs p1c_svf_base38 + 24/24 TMRT
  bands vs p2_ref_TMRT.tif. Contract amendment (documented in
  `_concurrent_geometry_exports`): publication order is completion order; a
  failure truncates to the completed set rather than a sorted prefix.
  Review ACCEPT WITH NOTES: N1 (spawn re-imports parent `__main__` — unguarded
  user scripts now fail) and N3 (abrupt child death surfaces
  BrokenProcessPool) fixed as docstring precision; N2 (cache-disabled +
  workers>1 had no aggregate admission) fixed by gating the stage on
  `runtime.cache_enabled` post-E2E (94cd7b50) — the stage is now co-extensive
  with the C6-40 phase route; battery A/B byte-identical 184-failure
  pre-existing sets, +1 gate-pin test. Instrument miss (recorded, not chased):
  the per-tile child-timing hook (S11_X01_TIMING sitecustomize) did not fire
  in spawn children (export_child_reports=0); the pre-registered gate metric
  is the parent-measured stage wall, so acceptance is unaffected. Raw records
  archived to Dropbox `campaign_s11/phase1/phase1b_raw_records.tar.gz`.
  Run phase (2545.9 s, 66.3% of the chain) is now the dominant segment → R11
  probe (`evidence/phase2_r11_probe_protocol.json`).

- S11-4 R11 PROBE COMPLETE (2026-10-16, jobs 14097616 + 14097751;
  `evidence/phase2_r11_probe_findings.json`, protocol amended pre-timing at
  a28690ce): the 316-vs-508 s/tile anomaly is RESOLVED — the phase-0
  standalone baseline ran a ONE-thread engine child
  (`_child_environment` overwrites NUMBA/OMP thread vars with
  `threads_per_worker`; `execute_tiles` always spawns children, even at
  workers=1). Paired same-job arms, every arm TMRT bitwise 24/24:
  standalone 1×8 = 307.5/309.3 s (repeat pair), standalone 1×1t = 535.7 s
  (reproduces p2_clean's 508.2 s within drift), pool 3×8 = 328.2/331.8 s
  with per-child clean engines 264-285 s — no placement or pool effect.
  Re-annotations: p2c_child's 521.4 s engine was cProfile +97% over the
  clean ~264 s; clean day/night is 4.2× (was reported 5.2×); 1×24 threads
  = +1.5% only (thread ceiling). Clean production-condition baseline:
  ~264 s engine + ~40 s non-engine per tile-child. First attempt
  (14097616) aborted on a DRIVER bug (arm wipe missed
  `.solweig-light/transactions` completion records → PersistenceError);
  partial records preserved in the raw archive; causal retry with the fix
  completed all six arms. Candidate opened: run-phase worker shape
  (workers×threads), bound by C6-42 phase admission (live 36.4 GiB budget
  fits only 3 concurrent simulation jobs at the current per-job estimate);
  requires its own frozen protocol (measured child RSS calibration +
  engine-at-4-threads + E2E bitwise A/B if admission-legal). Raw records
  archived to Dropbox `campaign_s11/phase2/`.
