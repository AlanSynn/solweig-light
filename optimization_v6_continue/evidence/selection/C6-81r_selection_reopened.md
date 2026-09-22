# C6-81r: reopened selection on measured in-sim residual (SYNTHETIC attribution)

Date: 2026-09-21. Owner: integrator. Basis: C6-101r Phase 1 attribution
(evidence/campaign_synthetic/phase1_attribution.json, 5 slots, profiled
sim 136.1 s self-time, one 1024² tile, integrated tree, threads=4) and
the C6-101r campaign speedup table (README_C6-101r.md). User authorization
2026-09-21: reopen C6-81 selection with in-sim residual measurement to lift
warm-state performance. All shares are single-run ratios (profiler
distortion inseparable from host noise, rep spread ±7–13%).

## Measured warm-relevant residual (self-time shares, integrated)

| family | share | note |
|---|---|---|
| visibility decode | 27.0% | 19.5 s cyl-LW slice + 11.8 s Kside/cyl-SW + 5.8 s raw-lazy |
| patch classification `_classes` | ≈15% cum | 12.3 s self + 6.5 s SLEEF atan_array |
| GVF | 15.6% | prepared route fired ×14; gather kernel 18.5 s |
| engine body/dispatch | 11.6% | |
| cylinder-LW kernels | 7.5% | |
| checkpoint/digest/IO | 7.5% | GDAL FlushCache 7.0 s |
| wall_shadows 4.1%, cyl-SW 3.3%, comfort 3.1%, Lside cum 7.1% | | |

## Decisions (select by measured residual, not catalog size)

1. **SELECT — R04+G06 (patch classification exact tables).** ≈15% cumulative
   with classification COMPUTE dominant — R04's "poor if lookup dominates"
   stop condition explicitly does NOT bite (the favorable case), and
   exact-coefficient finite-state tables match the standing priority
   "exact coefficient reuse" with typed arithmetic and zero approximation.
2. **CONDITIONALLY SELECT — cylinder-channel visibility decode fix**
   (dossier D02 microtile/batch decode / S08 native block-local mode,
   scoped to the dominant 19.5 s cyl-LW decode slice). Condition: any
   candidate must BEAT the measured C6-50/C6-81 declined evidence
   (+21–24% full-frame sweep loss; one-entry prepared decode does not
   amortize with size) under the same child-process lease protocol, or it
   stays declined. A repeat of that shape is not wanted; only a
   materially different decode structure earns promotion.
3. **NOT SELECTED — G05 (GVF postprocess+wall 14.9%+4.1%), R09 aniLum
   (Lside 7.1%), S01 export verify (cold-only ≈23% of cold run, warm-nil),
   S04/S05 comfort (3.1%).** Each is a single smaller family; the two
   selected items cover the largest warm lever (~42% combined) first.
   Re-ranked automatically if selection #1/#2 lands and re-profiling
   shifts the residual.

## Constraints carried into any implementation wave

- Freeze discipline: freeze remains ea2eed53; any src change = new
  reviewed commit + re-freeze (documented path, C6-100 dispositions §1).
- The declined C6-50 prepared one-entry decoder STAYS OFF by default
  (opt-in env only) unless a new candidate beats its evidence.
- Exactness: bitwise parity gates bind to the wrapper routes as before;
  no FMA/reassociation, no tolerance relaxation, typed arithmetic only.
- Measurement: exclusive lease, fresh configured children, SYNTHETIC
  labeling continues (dev-tier; no actual-target claims).
