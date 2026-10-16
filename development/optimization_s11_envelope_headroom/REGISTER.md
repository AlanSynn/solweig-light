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
| 1 | X01 | SVF export-loop concurrency: the serial parent loop (read-back bitwise verify + atomic staged publication, **2708.2 s measured in the X02 E2E arm**) runs per-tile concurrent (spawn process pool, budget-aware degree) | export 2708 → ~900 s at 3-way (today's budget) / ~540-600 s at 5-way (looser budget); chain from measured 5636.2 → ~3831 s = 63.9 min = **1.73×** (3-way) / ~3470-3524 s ≈ 58 min = **1.88-1.90×** (5-way) — Amdahl projection on measured segments | attribution measured (phase0_attribution.json; export loop shape-invariant across all arms); concurrency UNMEASURED — needs its own pre-registered protocol + benchmark | documented invariant change ("outputs and their order are unchanged"): write order + failure-truncation shape change; GIL-bound verify ⇒ processes; spawn (no fork hazard); admission must use the LIVE budget (36.4 GiB today → 3-way; was 47.6 GiB at Phase 0 → 5-way) | **candidate — Phase-1 protocol next** |
| 2 | X02 | SVF pixel-parallel twin dispatch at the DEFAULT 3×8 shape: `shadows.shadow` routes on the static bush predicate — positive max → step-major serial (unchanged regime), zero/NaN-poisoned max → `sky_compiled.shadow_pixel_parallel` | **ACCEPTED, MEASURED E2E (job 14094558, x02_b1_38)**: svf phase 4063.1 → 3055.0 s (**1.331×**, barrier 1356.2 → 346.8 = 3.91×, export loop parity 2708.2); chain 6612.9 → 5636.2 s = 93.9 min = **1.173× overall**, run phase 2561.0 (+1.25% vs A-arm, in band); **bitwise 24/24 SVF vs p1c_svf_base38 + 24/24 TMRT bands**; review ACCEPT WITH NOTES (phase1_x02_review.md; 49/49 adversarial probes) | **MEASURED BITWISE PASS 24/24 tiles** (p1c_bitwise.json; k=4.13@8t, 2.70@4t; barrier scaling ~75%/worker; bush_max=0 scope note) | dispatch diff small; compile cost 3.1 s cached; 5×4 shape REJECTED — admission-refused at live budget 36.4 GiB (only 3 fit) AND dominated by twin at 3×8 (3055.0 < 3101.9) | **ACCEPTED 2026-10-16 (commits 9133c693 + docstring follow-up); X01 next** |
| 3 | R11 | run-phase engine (95% of run): day steps 5.2× night (31-36 vs 6.06 s); hot: prepared GVF 149.2 s, Lcyl region pool 185.1 s, Kside aniso 115.5 s (decode_block 52.5) | unknown until 316-vs-508 s pool/standalone anomaly resolved | child profile measured (p2c_child.json); anomaly open | frozen C5/C6/N8/N9 lineages bound the leaf kernels; scheduling/overlap only | **Phase-1b protocol after X01+X02** |
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
