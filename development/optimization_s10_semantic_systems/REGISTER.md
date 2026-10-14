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
| 2 | G01+G02 | prepared GVF route at H=1 (G01) + production dtype profile admitted: f64 Tg (G02) and U-profile Tgwall | **L2 paired: 1.738 geomean on landcover cell (post-T01 2.0s → 1.14s); cumulative vs main ≈2.86×; E2E bit-frozen (prepared ≡ original bitwise on this profile)** | **ACCEPTED** (evidence/g01_g02_prepared_gvf.md; root cause: production f64 Tg rejected by all-f32 guards — compiled GVF never engaged on LC scenes at any H; 14 S10 tests + C6-30 suite 217 pass; pipeline goldens pass with route active) | delegate keeps exact baseline for rejected inputs; kill switch intact | **wave-1 complete**; re-profile before next rank |
| 3 | S03b | memory admission container mismatch: GDAL-cache charge = 5% physical RAM vs budget = cgroup headroom | unblocks default runs on container-limited hosts (correctness/ops, not speed) | census repro: default run refused in 6 GB Slurm step on 376 GB node (census_s10_02_route.md) | changes default admission semantics — needs own gate + docs | candidate (small, independent; propose after wave 1) |
| 4 | R03 | ordered aniLum diffuse block kernel (currently one full-raster Python update per patch) | O(NP) stays, removes Python P full-raster dispatch | static; dossier 03 | decode arithmetic order, nonbinary values | candidate (independent) |
| 5 | S07/S09 | stored-stream export validation / streaming checkpoint serialization | I/O stage share; bytes/time unknown until profile | static; dossier 08 | integrity/error-priority contracts | conditional on measured I/O share |
| 6 | T03 | exact finite-mask contribution tables (NP expr -> C*P eval) | win iff c_lookup < c_expression | static; dossier 02 | nonfinite states, table pressure | deferred until post-T01 profile |
| 7 | R01 | longwave consumer predicate cache (4-bit q) | win iff T*(decode3+predicate) > C0 | static; dossier 03 | 76.5 MiB@1024², error order | deferred |
| 8 | T06 | classification reuse across consumers | one classification instead of two | static; dossier 02 | key equality, lifetime | deferred |
| 9 | H* | heterogeneous region (GPU/Metal/OpenCL) | only if broad region wins incl. transfer/sync | unadmitted (no eligible hardware on this host yet) | FP64 profile, DX | design-only; at most ONE region, only with real device |
| 10 | T02 | typed execution plan (profile->kernel planning) | amortizes Python type checks; needed at scale of T01 use | folds into T01 design | cold JIT | fold into T01 |

Notes:
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
