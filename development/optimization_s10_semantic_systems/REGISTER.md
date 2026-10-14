# S10 opportunity register (live)

Ranked working register. Hypothesis-level until the S10-02 census lands; re-rank
after every accepted change (bottlenecks move). Value model: removable service
`Delta_j = C_j*(1-1/r_j)` on disjoint stages; overlapping candidates share the
combined implementation cost. Dispositions follow PORTFOLIO_SELECTION.md.

Baseline: main `b3e5ca59` on `perf/s10-semantic-systems`. Census evidence goes
to `evidence/` (distilled) and `/storage/scratch1/1/dsynn6/solweig-light-s10-raw/`
(raw, outside git; dbxcli upload at milestones).

| # | ID | mechanism | expected E2E effect (bound) | evidence status | risk | disposition |
|---|----|-----------|------------------------------|-----------------|------|-------------|
| 1 | T01 | singleton-array (U) typed longwave path; removes per-daytime-step full-raster fallback | **L2 paired: 1.659 geomean (min 1.631) on landcover protected cell** — 3.26s → 1.97s run_tile median | **ACCEPTED** (evidence/t01_l2_paired_benchmark.md; L1 + unit A/B in evidence/t01_l1_kernel_differential.md, evidence/s10_unit_suite_ab.md; landcover E2E golden 24/24 primary; 14 unit tests) | route flip shifts LC longwave fields ≤6.1e-05 W/m² (≤2 ulp), within frozen comparison_v1 budgets (atol 0.05); pre-existing compiled-vs-reference divergence documented — NOT introduced by the patch | **wave-1 complete (33ab050f)**; re-profile before next rank |
| 2 | G01+G02 | prepared GVF route at H=1 (G01) + production dtype profile admitted: f64 Tg (G02) and U-profile Tgwall | **L2 paired: 1.738 geomean on landcover cell (post-T01 2.0s → 1.14s); cumulative vs main ≈2.86×; E2E bit-frozen (prepared ≡ original bitwise on this profile)** | **ACCEPTED** (evidence/g01_g02_prepared_gvf.md; root cause: production f64 Tg rejected by all-f32 guards — compiled GVF never engaged on LC scenes at any H; 14 S10 tests + C6-30 suite 217 pass; pipeline goldens pass with route active) | delegate keeps exact baseline for rejected inputs; kill switch intact | **wave-1 complete**; post-change census confirms 0 remaining gate hits (evidence/s10_post_g02_census.md) |
| 3 | R03 | ordered aniLum packed-stream kernel: replace 153×/daytime-step Python plane decode+accumulate with one njit ordered sweep over the admitted packed leaves | **L2: ≈1.05× tile cross-tree paired (1.035/1.047 geomeans, 8/10 pairs ≥1.0); within-process toggle 1.073 median (7/8). Cumulative vs main ≈3.0× (3.26s → ≈1.09s)** | **ACCEPTED** (evidence/r03_anilum_packed.md; kernel ≡ retained loop bitwise on uint32 views incl. NaN/-0/Inf raw payloads; ternary/weight/non-packed declines exact; kill switch; 14/14 E2E engagement; unit 8/8, S10 36/36, landcover goldens 2/2, tests/unit set unchanged) | decode arithmetic order preserved per pixel; ternary reserved-code scenes stay on the Python indexer (original IndexError) | **wave-2 complete (1a3cb8e2)**; re-profile before next rank |
| 4 | Lside twin | compiled twin of `Lside_veg_v2022a` (pure NumPy `_operate` body, no compiled variant exists) | **post-R03 measured: 5.1% of calc (~3.1% of tile); expected removable 1.6–2.3% of tile** | **SELECTED in the one residual round (S10-22, evidence/portfolio/residual/residual_selection.json)** — top remaining exact candidate; S10-21 disjoint shares; wave-2 review clean | ordered expression decode; 0-d scalar branches (altitude/azimuth/t) | selected → S10-23 implements |
| 5 | S03b | memory admission container mismatch: GDAL-cache charge = 5% physical RAM vs budget = cgroup headroom | unblocks default runs on container-limited hosts (correctness/ops, not speed; no perf claim) | **ACCEPTED** (evidence/s03b_gdal_container_view.md; fix: `default_gdal_cache_bytes` view = min(physical, finite cgroup limit), so applied GDAL_CACHEMAX and admission charge are one number by construction; 4 unit tests incl. census-config admission flip + no-limit causal guard; S10 40/40, landcover goldens 2/2, unit memory/admission subset 12/12; host demo: default refusal on this 68.7 GB cgroup host unchanged (correct), budget-only override runs 3/3) | changes default admission semantics — own gate + docs shipped | **wave-2 complete (313f6a15 + S03b commit)**; ordinary hosts bit-identical |
| 6 | S07/S09 | stored-stream export validation / streaming checkpoint serialization | **measured: write 4.7% tile; checkpoint 15.8% tile but fsync/flush-bound at benchmark scale — S09 ceiling here ≈1.5–2%; bytes-scaled part needs production-size scene** | post-G02 census + checkpoint split (evidence/s10_post_g02_census.md); io-audit (2026-10-14): mechanism map confirms DSM/Trees/DEM sha256'd up to 9x cold with a back-to-back E→F rehash pair (pipeline.py:240→242) and a removable `_encode` getvalue copy (byte-identical streaming) — logic-derived, not measured; consistent with the measured deferral | integrity/error-priority contracts; D08 forbids interval change | conditional — deferred pending production-scale evidence |
| 7 | gvf/Lcyl/Kside kernel-internal | the three top stages (76% of calc) are ALL on their proven compiled routes post-census | micro-opts only; exactness-frozen lineages (C5/C6/N8/N9) | post-G02 census (route counters: 0 fallbacks everywhere) | high effort, frozen ordered arithmetic | diminishing returns — not planned |
| 8 | T03 | exact finite-mask contribution tables (NP expr -> C*P eval) | win iff c_lookup < c_expression | static; dossier 02 | nonfinite states, table pressure | deferred until post-T01 profile |
| 9 | R01 | longwave consumer predicate cache (4-bit q) | win iff T*(decode3+predicate) > C0 | static; dossier 03 | 76.5 MiB@1024², error order | deferred |
| 10 | T06 | classification reuse across consumers | one classification instead of two | static; dossier 02 | key equality, lifetime | deferred |
| 11 | H* | heterogeneous region (GPU/Metal/OpenCL) | only if broad region wins incl. transfer/sync | unadmitted (no eligible hardware on this host yet) | FP64 profile, DX | design-only; at most ONE region, only with real device |
| 12 | T02 | typed execution plan (profile->kernel planning) | amortizes Python type checks; needed at scale of T01 use | folds into T01 design | cold JIT | fold into T01 |

Notes:
- S10-22 residual-round selection COMPLETE (2026-10-14, evidence/portfolio/
  residual/residual_selection.json): ONE exact improvement selected (Lside
  compiled twin, measured 5.1% calc, expected removable 1.6-2.3% tile,
  low burden via the A-plus/T01 pattern). Second exact slot DEFERRED —
  T03/R01/T06 assessed against the post-R03 profile and bounded below
  useful effect (R01's target collapsed into anilum_packed 2.5%; T03
  bounded by the 6.2% body residual); S07/S09 deferred pending
  production-scale evidence; backend study not eligible (no hardware);
  Y06 deferred (startup residual 18.7% tile unwrapped — decomposition may
  ride along as S10-30 diagnostics, not a new candidate round). The
  candidate list CLOSES with this round.
- Wave-2 independent review COMPLETE (2026-10-14, evidence/reviews/wave2/):
  S10-20 + S10-21 approved_with_notes, NO blockers. Reviewer independently
  re-ran compare24/compare48 from disk (byte-identical), re-verified
  multitile bitwise with its own checker, audited multiply-counting (dpc
  nesting confirmed), reproduced the 9-run t(W,H) ordering, matched all
  harness/archive sha256s, re-ran gates (59/59 + 2/2). Five minor findings
  (doc numeric errors, derivation labels, provenance/retention notes) — all
  closed same day; no measurement claim changed.
- S10-21 residual profile + joint resource comparison COMPLETE (2026-10-14,
  evidence/residual/): disjoint stage costs at HEAD re-rank the residuals —
  Lside twin 5.1% calc (~3.1% tile) is the top exact candidate; S07/S09
  ceiling here ~1.5-2% (checkpoint fsync-bound); startup residual 18.7% of
  tile is UNWRAPPED (measurement gap before any candidate can be valued
  there); gvf+Lcyl+Kside 84.5% of calc pinned on compiled routes. R03
  verified in place (anilum kernel 2.5% calc vs 11.1% loop; body residual
  8.6% -> 6.2%). t(W,H) portfolio (4 same-content tiles, cpu_budget 4,
  alternating x3, fresh process per run): 4x1 < 2x2 < 1x4 in ALL 9 runs
  (medians 13.0/17.7/33.6 s; direction robust, magnitudes
  contention-affected); D07 recording list satisfied (admitted workers,
  estimates, PIDs, probe-child numba/GDAL masks = requested H exactly).
  Raw archived s10_s21_residual.tar.gz sha256 fb22af79...
- S10-20 integration COMPLETE (2026-10-14, evidence/integration/): four real
  full-pipeline runs at HEAD — (A) pure-default run ADMITS the 24-step golden
  tile on this host (estimate 0.81 GB vs 2.74 GB default budget view; the
  default outcome is estimate-dependent — refines, not contradicts, the S03b
  demo); (B) 24-step golden vs stored original-CPU goldens PASS all ten
  products (worst: Ldown 4.58e-04 vs atol 0.05; TMRT 6.1e-05 vs 0.01;
  Ta/Wind/Shadow exact), run-to-run deterministic; (C) 48-step half-hourly
  chronology (disclosed metfile extension, timestepdec 0.5 h) candidate vs
  forced-reference oracle (R03/G01 kill switches + T01 admission decline —
  main's census-documented fallback) PASS with route engagement proven both
  sides (candidate: prepared 30/30 daytime, primaries 48/48; oracle: serial
  30/30, reference 48/48); (D) 2-tile worker pool: 5.5 GB budget refusal of
  2 concurrent phase reservations recorded (C6-42 reject, by design), rerun
  at 9.6 GB completes concurrently and tile 0_0 is BITWISE-identical to the
  in-process run B (10 files × 24 bands). Machine-readable:
  evidence/integration/integration_commit.json + l2_results.json. Gates:
  S10 59/59, landcover differential 2/2.
- S10-15 wave-1 independent review COMPLETE (2026-10-14, evidence/reviews/
  wave1/): no blockers — R03/S03b approved, T01/G01+G02/S10-14 approved
  with notes; all seven deferrals (rows 6-12) agreed. Review follow-ups
  closed same day: standing landcover-golden E2E engagement pin added for
  T01/G01 (the review demonstrated the census trap by execution — goldens
  pass with the aniLum kill switch on, only the E2E pin fails); G01
  evidence count corrected (217 → locatable lineage 160, re-run green);
  dtype-blind admission predicate documented with int32/int64 probes;
  S10-14 python-float partition recorded as dtype-conditional. Reviewer
  rerun recommendation: re-run the three L2 paired cells (T01/G02/R03) on
  a quiet window before any merge — scheduled as the held-out campaign
  (S10-30).
- Operative numerical acceptance standard (established 2026-10-13, L1
  differential): the frozen `development/benchmarks/protocols/comparison_v1.json`
  budgets (Lcyl/dpc fields atol 0.05 W/m² rtol 1e-5; Tmrt 0.01 °C; UTCI/WBGT
  0.02) — the same standard all shipped compiled kernels are qualified
  against. Bit-equality vs the engine serial reference is NOT the operative
  bar: the shipped S-profile primary itself diverges from the reference by
  1–2 f32 ulp on real fractional-visibility inputs (documented in
  evidence/t01_l1_kernel_differential.md; pre-existing, in both fused and raw
  kernel routes).
- N9 shipped items (bounded stream row B, A-plus decode, packed visibility,
  geometry dedup, worker pools) are BASELINE A — not opportunities.
- Rejected without new causal design: ISPC/native leaf rerun, fused decoder
  variants, relaxed precision, persistence weakening.
- Host facts: PACE login-class node, nproc=4, loadavg shared (noise policy:
  paired alternation + quiet-window retries), RAM 376 GB BUT the session runs
  in a Slurm step cgroup with 5.86 GB headroom — memory admission refuses
  default runs (see S03b). Runtime env: conda(libgdal 3.13) + uv locked deps,
  restored 2026-10-13.
- Production longwave demand is PIPELINE_CYLINDERS_ANISOTROPIC (primary-output
  route); the Tgwall rank fallback silently degrades it to the serial
  reference (census).
