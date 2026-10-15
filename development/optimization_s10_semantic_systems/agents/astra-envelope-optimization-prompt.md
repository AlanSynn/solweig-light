# Astra mission: end-to-end speed diagnosis and headroom verdict for solweig-light

You are the architecture lead for a follow-on optimization campaign on this repository
(`/storage/scratch1/1/dsynn6/solweig-light`, branch `perf/s10-semantic-systems`). The
previous S10 campaign is CLOSED (terminal state `qualified_exact_cpu`,
`FINAL_DECISION.json`; the S10-36 synthetic-scale demonstration is appended in
`REGISTER.md`). Your mission is NOT to re-run that campaign. It is to answer, with
measurements and floor arithmetic, one question:

**How fast can this pipeline get, end-to-end, across the whole operating envelope —
small tiles, large tiles (1024²), short runs (few timesteps), long runs (24+ steps,
multi-day), serial and parallel shapes — using mathematical rigor first, and
approximation only where the error is quantified and tiny (zero preferred)?**

Then, if and only if the diagnosis justifies it, implement the top candidates through
delegated workers with the same evidence discipline as the previous campaign. State
plainly where the honest answer is "no meaningful headroom under the constraints".

Delegate freely to workers (measurement, implementation, independent review). One
writer per file scope; review is independent of author; no transcript replay; do not
fabricate measurements, APIs, or prior approvals. Ground every claim in code or
recorded evidence.

## Verified starting facts — trust these, do not re-derive (pointers checked 2026-10-15)

- Public chain: `run_walls_aspect` → `_calculate_svf(patch_option=2, 153 sky patches,
  counts [31,30,28,24,19,13,7,1], geometry/shadows.py:23)` → `run_utci_tiles` (per tile:
  5 rasters + met + timezone once; then a strict per-timestep loop `pipeline.py:268` —
  `Solweig_2022a_calc` engine.py:1541-1703, `utci_calculator_uniform`, writer + checkpoint).
- Measured envelope (paired A=main b3e5ca59 vs B=candidate c245ea60; single passes,
  observational): small cells (16²–32×35, 24–48 steps) gate 1.314x geomean, warm
  single-tile span 2.96x (3.236→1.093 s), first-call residual 0.13–0.14 s on both sides;
  production shape (24 synthetic 1024² tiles, 24 steps, pinned 3 workers × 8 threads,
  slurm 14060057): walls 20.0 s, **svf 4063.1 s (61.5% of the chain)**, run 2529.7 s;
  B/A total 0.9675 (parity-to-1.03x; run phase alone 1.074x); TMRT outputs bitwise
  identical 24/24. Evidence: `evidence/target/synthetic_scale_demo.json`,
  `evidence/selection/selection.json`, `FINAL_DECISION.json`.
- **The single largest known lever is already in the code, unused.** The SVF shadow
  kernel runs SERIALLY — one busy thread per worker process (3 of 24 cores in the
  measured configuration). `geometry/sky_compiled.py` contains `_pixel_serial` and
  `_pixel_parallel` (prange over pixels calling the same `_trace_pixel`, bitwise-identical
  per pixel, independence proof in-code at `_shadow_pixel`), plus `shadow_parallel` /
  `shadow_pixel_parallel` dispatchers — deliberately parked: "Serial default; parallel
  execution is explicit until benchmark review" (sky_compiled.py:264). `comfort/utci.py:412`
  has the same pattern (`utci_calculator_uniform(..., parallel=False)`,
  `_utci_uniform_parallel` compiled). Caveats: tiles with `bush.max()>0` take the
  step-major `_shadow` path (parallel twin exists there too, smaller gain, still exact);
  part of the 4063 s may be the serial per-tile geometry export loop
  (`api.py:146-149` → `geometry/service.py:235`) or packed-stream encoding, not the
  pixel kernel — MEASURE before claiming.
- Working hypotheses from pre-campaign analysis (UNMEASURED — your Phase 0 decides):
  parallel SVF ≈ 5–7x on that phase (bandwidth check says no memory wall: ~1.2–1.9 GB/s
  per serial core, 29–45 GB/s aggregate) → production chain 1.97–2.11x, bitwise, with
  relative gains largest for short runs (svf ≈ 93% of 1-step compute). Fixed-cost package
  (input-guard re-hash dedup — DSM/Trees/DEM sha256'd ~7–9x cold incl. the back-to-back
  pair at pipeline.py:240-242; per-step import inside the loop at pipeline.py:277;
  `persistence.py:94-96` `_encode` getvalue() copy) ≈ 10–25% on warm small tiles.
  Run phase: candidate margin was only 1.074x — the frozen compiled kernels
  (gvf 28.5–29.2%, Lcyl 25.0–25.8%, Kside 22.0–22.2% of calc, zero fallbacks,
  `evidence/s10_post_g02_census.md`) likely dominate it; attribute before touching.

## Hard constraints (violating any of these is a failed mission)

- main (b3e5ca59) is READ-ONLY, forever. No push, PR, merge to main, release, or history
  rewrite. Never resurrect archived campaign branches (handover/campaign-line,
  perf/cpu-optimization, perf/native-optimization). Work on a new branch off
  `perf/s10-semantic-systems`; keep the product-source freeze discipline (product diff
  vs c245ea60 must be intentional from your first commit onward — you are now ALLOWED
  to change product source, on the branch, with evidence).
- `SEMANTIC_CONTRACT.md` stands: 7-function public surface, signed-zero/NaN/warning
  order, persistence ordering, and **strict chronology — no timestep parallelism**.
  Long-run speedups must come from within-timestep efficiency, temporal reuse of
  timestep-independent quantities, or contract amendments the USER approves explicitly.
- Exactness tiers, in order of preference: (1) bitwise; (2) within the frozen
  `development/benchmarks/protocols/comparison_v1.json` budgets (Tmrt 0.01 °C; UTCI/WBGT
  0.02; radiation fields atol 0.05/rtol 1e-5; SVF fields 1e-6; shadow categories exact);
  (3) approximation — ONLY behind a dispatch guard with serial/exact fallback and a kill
  switch, with quantified error bounds on certified fixtures, a predeclared budget
  amendment, and explicit user sign-off. NEVER relax a golden or gate to admit a change.
  SVF VALUE approximation is contract-exposed (svf feeds Ldown→Tmrt every step) — treat
  as tier 3 at best; note patch_option 1 (145 patches) already exists as a user option.
- Frozen ordered-arithmetic lineages C5/C6/N8/N9 (gvf/Lcyl/Kside kernel internals):
  not amendable without a causal design + user authorization; precision/fastmath
  relaxation of them buys ~nothing (memory/structure-bound) — do not propose.
- NO GPU/heterogeneous hardware exists on this host. NO native C++/ISPC re-port without
  explicit new user authorization (historical native line stays deleted). No new runtime
  dependencies (6-dep closure + extras are identity-pinned vs main in the wheel). No
  page-cache/host-memory tricks on the shared login node cgroup. Pure stdlib/numba/numpy
  code changes only.
- Timing: login node is noisy — paired alternation only; real measurements on slurm
  allocations (`sbatch -p cpu-medium --account=gts-hoh68 --qos=inferno`; foreground shell
  calls cap ~2 min). Predeclare every measurement protocol in writing BEFORE timing
  (S10-35 precedent: `evidence/target/synthetic_scale_protocol.json`): one timed pass per
  arm per cell + at most one causal retry, disclosed. Raw artifacts outside git
  (`/storage/scratch1/1/dsynn6/solweig-light-s10-raw/`, archive to Dropbox
  `Alan Synn/Research/solweig-light/` via dbxcli `put` with absolute paths + sha256
  sidecars); repository keeps manifests + distilled evidence only. Synthetic scenes are
  NEVER the real target — `actual_target_status` stays `unverified`; label accordingly.

## The envelope (report every corner separately; no summed minima, no multiplied
overlapping speedups, no treating 2 scenes × 24 h as 24 tiles)

| corner | tiles | steps | notes |
|---|---|---|---|
| S-small | 16², 32×35 (golden P1 shape) | 1, 24, 48 (half-hourly) | fixed-cost dominated; startup residual 12–13% |
| L-large | 256², 1024² (synthetic corpus exists: `/storage/scratch1/1/dsynn6/solweig-light-s10-raw/synthetic_target/`, 24 tiles, manifest sha e2c7fa847223bb21) | 1, 24 | svf + run dominated |
| T-short / T-long | same tiles | 1 vs 24 vs 72+ (metfile extension allowed for synthetic) | svf is once-per-tile and timestep-independent → amortizes with length; run is per-step |
| shapes | serial shipped defaults AND the best admissible parallel shape | — | re-derive admissible worker counts on the CANDIDATE's post-S03b admission (its GDAL charge is a budget view, so more workers may now admit than main's 3×8; verify by admission arithmetic, then measure) |

## Phase 0 — mandatory diagnosis before any product change (deliverable: attribution report)

M1. Intra-svf attribution, 1 tile 1024²: schedule prep vs pixel kernel vs field
accumulation (svf.py:129-144, Python annulus loop) vs packed-stream encoding vs export
loop (api.py:146-149). Without this, the 4063 s cannot be attributed.
M2. Run-phase per-kernel attribution: 1 tile × 24 steps AND 1 tile × 1 step (separates
per-call fixed cost): wall13/23, gvf, Kside, Lcyl, aniLum, Lside, Perez, UTCI, writer,
checkpoint, guard.
M3. Ray-step census: call `ray_schedule` for all 153 patches with production
amaxvalue/scale (pure Python, seconds) — turns the ~105–160 steps/patch inference into a
measurement and bounds any future truncation approximation.
M4. SVF serial-vs-parallel A/B (the decisive experiment): 1 tile, bitwise array_equal +
timing at 1/8 threads. M5. UTCI serial-vs-parallel A/B, 1 tile-step. M6. One
`input_guard.check()` timed × call sites.

## Phase 1 — bitwise quick wins (each: guard + exact fallback + kill switch + differential tests + goldens)

1. Wire `shadow_pixel_parallel` behind a dispatch guard (default ON only after M4 proves
   bitwise + speedup; `SOLWEIG_LIGHT_SVF_SHADOW_PARALLEL=0` fallback). Expected tier-1
   result, pending M1/M4.
2. Parallel UTCI uniform (same pattern).
3. Fixed-cost package: hash-once-per-(path,mtime,size) guard fingerprints (disclose the
   trust-policy change), hoist per-step imports/context managers out of the timestep
   loop, drop the `_encode` extra copy (byte-identical streaming).
4. Re-derive and measure the post-S03b parallel shape envelope (admission arithmetic
   first, then timed): the 3×8 pin was proven against MAIN's inflated GDAL charge.

## Phase 2 — envelope completion (only where Phase 0 shows service)

- Small tiles: decompose the 0.13–0.14 s residual (`python -X importtime`; pipeline.py's
  module-scope gdal/pytz/timezonefinder/numba imports), lazy-import the tail.
- Short/repeat runs: geometry `GeometryStore` reuse is already content-addressed — make
  it a documented operational path, measure warm-cache rerun.
- Long runs: after M2, revisit deferred EXACT routes if their stage shows service
  (T03 contribution tables <6.2% bound; T06 classification reuse; writer batching
  ≈ halving S07's 4.7%; checkpoint policy is a SEMANTIC change — recovery window —
  requires explicit user approval, do not silently tune).
- svf field accumulation fusion into the kernel (reordered sums — tier 2, within Tmrt
  0.01) if M1 shows the annulus loop matters.

## Phase 3 — approximation tier (only on explicit user request after Phases 0-2 report)

Patch-count reduction, ray truncation below the exact `amaxvalue` exit, precision
changes: each requires quantified per-pixel error bounds (M3 bounds truncation),
a predeclared amended budget, fixtures demonstrating the bound, and user sign-off.
Expected honest verdict: poor trades vs bitwise Phase 1 — say so if so.

## Deliverables and stopping condition

1. Diagnosis report: per-corner attribution tables, floor arithmetic, per-corner
   speedup ceiling (bitwise tier vs tier-2 vs tier-3), explicit "no headroom" statements
   where true. 2. If implementing: routes behind guards, differential + golden + S10
   suite evidence (83/83 canonical order), REGISTER entries, evidence-only commits, raw
   to Dropbox. Do NOT modify FINAL_DECISION.json / MERGE_MANIFEST.json / closure
   records; the closed campaign stays closed. Stop at a measured, reviewed verdict plus
   (if justified) an implemented, independently-reviewed candidate on the branch — not
   at an open-ended optimization promise.
