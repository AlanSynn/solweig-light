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
| 1 | T01 | singleton-array (U) typed longwave path; removes per-daytime-step full-raster fallback | census: 14/14 daytime steps rejected with Landcover; 1.31s/24-step serial-reference stage on 32x35 (~14% warm E2E at 1120 px, understates production share) | **CONFIRMED** (evidence/census_s10_02_route.md; trigger = Landcover raster; Tgwall (1,1) f64 at guards) | rank/dtype parity (f64 promotion via altmax; sun/shade may differ); warnings/error order | **ACCEPTED as wave-1 lead** — implement per dossier 01 |
| 2 | G01 | prepared GVF route admitted at H=1 (currently prepared only when H>1) | removes repeated preparation/alloc per step at 1 thread | census: prepared route never entered at H=1 (engine.py:1757); with LC the f64 Tgwall would also fail gvf_prepared.py:103 at H>1 | guard union + water snapshot + alias cases; T01 rank normalization may flip the f64 rejection | candidate (wave 1, after T01 design lands — T01's Tgwall normalization interacts with the guard) |
| 3 | S03b | memory admission container mismatch: GDAL-cache charge = 5% physical RAM vs budget = cgroup headroom | unblocks default runs on container-limited hosts (correctness/ops, not speed) | census repro: default run refused in 6 GB Slurm step on 376 GB node (census_s10_02_route.md) | changes default admission semantics — needs own gate + docs | candidate (small, independent; propose after wave 1) |
| 4 | R03 | ordered aniLum diffuse block kernel (currently one full-raster Python update per patch) | O(NP) stays, removes Python P full-raster dispatch | static; dossier 03 | decode arithmetic order, nonbinary values | candidate (independent) |
| 5 | S07/S09 | stored-stream export validation / streaming checkpoint serialization | I/O stage share; bytes/time unknown until profile | static; dossier 08 | integrity/error-priority contracts | conditional on measured I/O share |
| 6 | T03 | exact finite-mask contribution tables (NP expr -> C*P eval) | win iff c_lookup < c_expression | static; dossier 02 | nonfinite states, table pressure | deferred until post-T01 profile |
| 7 | R01 | longwave consumer predicate cache (4-bit q) | win iff T*(decode3+predicate) > C0 | static; dossier 03 | 76.5 MiB@1024², error order | deferred |
| 8 | T06 | classification reuse across consumers | one classification instead of two | static; dossier 02 | key equality, lifetime | deferred |
| 9 | H* | heterogeneous region (GPU/Metal/OpenCL) | only if broad region wins incl. transfer/sync | unadmitted (no eligible hardware on this host yet) | FP64 profile, DX | design-only; at most ONE region, only with real device |
| 10 | T02 | typed execution plan (profile->kernel planning) | amortizes Python type checks; needed at scale of T01 use | folds into T01 design | cold JIT | fold into T01 |

Notes:
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
