# S10-23 — Lside exact dispatch twin

Task: S10-22 selected one residual improvement ("Lside compiled twin", register
row 4). This document records what was actually implemented — an **exact
dispatch twin**, a deliberate evidence-driven pivot from the selected njit
variant — and the full verification record. Machine-readable record:
`residual_parity.json` (same directory).

## 1. Recon pivot (probe evidence)

`s10_lside_argprobe.py` (raw, Dropbox `s10/residual/`) wrapped
`engine.lside_veg_v2022a_demanded` and profiled all 24 per-run Lside calls on
the landcover golden (32x35, 24 steps, HEAD 321edb94):

- **All 24 calls carry `anisotropic_longwave == 1`.** The body's returned
  cardinal fields are exactly `Lup*0.5` (pipeline_demand rule R-A); its
  transcendental prologue and wall chains are discarded work for every
  production call.
- **Regime split: 7 calls default, 17 calls `{divide:'ignore',
  invalid:'ignore'}`.** `engine.py:333` sets
  `np.seterr(divide='ignore', invalid='ignore')` globally at the first daytime
  step and never restores it. The C6-20 `_guard_anisotropic` clause 1
  (`np.geterr() != _ERR_DEFAULT` → decline) is therefore defeated wholesale
  from step 7 onward: the shipped demanded fast path silently stops engaging
  for 17 of 24 calls.

Consequence: the winning move is not a compiled kernel — it is **extending the
certified regime of the existing C6-20 demanded fast path** so the 17
regime-defeated calls also take it. The njit variant from the S10-22 selection
is **explicitly rejected**: no `aniso==0` traffic exists (24/24 `aniso==1`),
so a budget-qualified kernel adds JIT surface without demand, while the
dispatch twin is bitwise-exact on the whole admitted domain (values AND
warnings) — stronger than the budget-qualified standard — at a fraction of
the risk.

## 2. Mechanism

Three coordinated pieces (all behavior-preserving by construction):

1. `pipeline_demand._anisotropic_domain` — the domain/bounds half of
   `_guard_anisotropic`, extracted verbatim so both the C6-20 guard and the
   new admission rule certify the same inputs. The regime clause stays in
   `_guard_anisotropic` unchanged.
2. `patch_radiation.Lside_veg_v2022a` — the dispatch twin plus
   `ROUTE_COUNTS` entries. Admission rule (all must hold, else decline):

   - kill switch `SOLWEIG_LIGHT_LSIDE_DISPATCH != '0'`;
   - `over == 'warn'` **and** `under == 'ignore'` (the channels the removed
     operations can actually perturb: `over` by the discarded
     transcendental/wall chains, `under` by the removed Lvikt polynomial —
     its tiny-svf underflow escape is NOT excluded by the domain bounds, so a
     non-default `under` channel must never admit; this preserves the C6-20
     tier pin `svf=1e-20 under under='warn' → fallback`);
   - `divide`/`invalid` not `'raise'` (a promoted raise is owned by the
     original site, matching the C6-20 tier-B contract);
   - `_anisotropic_domain(args).ok`;
   - when `divide == 'warn'` and `log_dirs` nonempty, the log warnings are
     replicated via the existing `_replicate_log_warnings` (any failure →
     decline).

   Admitted result: `_demanded_anisotropic_result(LupE, LupS, LupW, LupN)` —
   the same `_operate(np.multiply, LupX, 0.5)` the body's anisotropic branch
   performs. **No re-ordered arithmetic exists to prove: byte parity is the
   contract on the whole admitted domain.**
3. `engine._serial_Lside_veg_v2022a` capture + public-name wrapper forwarding
   to the dispatch. The `_reference` search skips the patch_radiation module
   by its `__module__` guard, so there is no recursion; the reference is the
   verbatim original body, which makes every decline bitwise-trivially exact
   and leaves warning ownership at the original site.

Both production regimes are admitted: default (night steps 0–6) and the leaked
ignore regime (steps 7–23). Everything else declines to the body.

## 3. Verification record

| Gate | Result |
| --- | --- |
| L1 twin suite (`tests/optimization_s10/residual/test_lside_twin.py`) | 21/21 — bit-level parity (dtype+tobytes) under default AND leaked regimes; night profile; demanded-result identity; discarded-work inputs; caller non-mutation; decline matrix (aniso=0, out-of-domain svf **with warning parity**, NaN svf, non-broadcastable Tw → original ValueError); default-regime log replication; promoted-warning fallback; `under='warn'` fallback pin; kill switch; FULL_DIAGNOSTICS + production-demand routes; wiring; call styles |
| `tests/optimization_s10` | 80/80 (incl. extended standing E2E pin) |
| C6-20 warning-contract + cylinder + v8 seam | 107 passed, 1 failed — **pre-existing** (`test_kernel_primary_matches_full_route_invariance`, NaN payload column 7), proven failing at clean HEAD 321edb94 in a throwaway worktree (identical failure; worktree removed) |
| Landcover differential goldens | 2/2 (`[landcover-False]`, `[landcover_normalized-False]`) |
| Full `tests/differential` tree | 706 failures — **byte-identical failure set to clean HEAD** (worktree-proven; zero new) |
| E2E engagement (fresh process) | 24 demanded calls = 7 upstream C6-20 fast + **17 dispatch primary, 0 reference** — the serial body never executes on the production profile |
| Standing E2E pin | `test_route_engagement_landcover.py` now asserts every Lside call is accounted (primary+reference == 24) and `reference == 0`, split-agnostic in the fast/twin split because the ambient seterr decides it |

## 4. Performance evidence (honest magnitudes)

- **Wrapper-timed body span (the claim):** in-process kill-switch toggle, 6
  alternating reps — B (body) span 0.0339 s median over 24 calls
  (1.39–1.43 ms/call); **A (twin) span 0.0, 0 body calls, primary 24 /
  reference 0 in every rep**. The twin removes the entire measured body span.
  (24 calls here, not 17: in-process the leaked regime persists, so night
  steps decline too — see §5.)
- **Fresh-process L2 pairs (direction only):** alternating A/B ×3 — A
  [7.293, 6.717, 6.756] median 6.756 s; B [16.866, 7.454, 8.976] median
  8.976 s; B/A > 1 in all 3 pairs; engagement split 17/0 (A) and 0/17 (B) in
  every run. Host loadavg ~11–17 (co-tenant contention); B rep 1 is a
  contention outlier. Wall deltas (0.7–9.6 s) are 1–2 orders above the
  mechanistic effect (~24 ms fresh-process) and must NOT be read as the
  effect size. Quiet-window rerun folds into the S10-30 held-out campaign.
- **Removed service, fresh-process terms:** 17 × ~1.4 ms ≈ 24 ms per run
  ≈ 2.0% of calc, ~1.2% of tile at the S10-21 measurement point.

## 5. Correction to the S10-21 record (additive, disclosed)

`residual_costs.json` recorded `Lside_veg_v2022a calls_per_run = 24`. Fresh-
process truth (verified twice: argprobe + e2e): **17 serial body calls + 7
upstream C6-20 fast-path calls.** Mechanism: the S10-21 harness ran 1 warmup
+ 3 timed reps in ONE process; the `engine.py:333` seterr leak made reps 2–4
fail the R-A regime clause on all calls. The S10-23 in-process harness
reproduces this exactly (errstate at every rep start = leaked regime; B-side
24 body calls), and its measured span (~34 ms/24 calls) matches the S10-21
time basis (0.0363 s) — the time was real, the call count was process-local.
`residual_costs.json` carries the correction as an additive
`s10_23_correction` key; the frozen S10-21 numbers are not rewritten. The
selection ranking is unaffected (Lside remained the top exact candidate).

## 6. Rejections and notes

- **njit kernel variant rejected** (§1): no production `aniso==0` traffic;
  exactness already achieved dispatch-level.
- **Defensive property found during harnessing:** the dispatch binds its
  arguments via `inspect.signature(_reference(...))`; wrapping the serial
  capture with a `*args/**kwargs` shim breaks the 28-name binding and forces
  wholesale decline (correct values, route to the wrapper). Safe for any
  instrumentation that patches `_serial_*`, but instrumentation must lend
  the real signature (`__signature__`) if it wants the fast path measurable.
- Raw artifacts (probe, L2 harnesses, retained JSONs) are archived to Dropbox
  `Alan Synn/Research/solweig-light/s10/residual/` with sha256s in
  `residual_parity.json`.
