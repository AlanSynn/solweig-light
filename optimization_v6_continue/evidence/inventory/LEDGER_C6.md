# Live dependency ledger — v6 continuation

Coordinator-maintained. Patch IDs immutable once landed; per-patch review status
tracked here. Branch `perf/claude-glm53-cpu-v5`; branch tip advances only by
integrator commits. Base of record for wave-1 workers: `5e1fab46`.

## Landed

| commit | task | kind | review |
|---|---|---|---|
| b2d23c6c | C6-00 | inventory | n/a |
| 5e1fab46 | C6-01 | evidence+tools (scope correction, thread harness/matrix/paired/defect, BASELINE_v6) | not required |
| 5e1fab46 | C6-02 | evidence+tests (geometry census, D02 CONFIRMED: keys differ only by construction/standalone_implementation @ service.py:281-282) | not required |
| 5e1fab46 | C6-03 | evidence (memory model: 3.4742 GiB worst case; 2x2 safe / 4x1 unsafe; admission misses) | **APPROVE-WITH-NOTES** (41bfcaf4; walls/aspect f32 correction relayed to C6-42; raw-safe count 2) |

## In flight — wave 1 (detached at 5e1fab46)

| worker | task | owned module | blocked-by status |
|---|---|---|---|
| v6-recipe | C6-10 | geometry/recipe.py + integration recipe | worker PASS (3 gates; both routes -> shared key 7998d95e…; standalone_implementation dropped from native key); **C6-60 in flight (v6-rev610)** |
| v6-lside | C6-20 | radiation/pipeline_demand.py | worker PASS (ALL_BITWISE_OK; 62 tests); **C6-60 in flight (v6-rev620)** |
| v6-cyllw | C6-21 | radiation/cylinder_longwave.py | **LANDED eea97fbd** (APPROVE-WITH-NOTES, 0 blocking; C6-70 handoff: demand_scope+restore, assert cyl=1) |
| v6-cylsw | C6-22 | radiation/cylinder_shortwave.py | **LANDED 99681b53** (APPROVE-WITH-NOTES; prose corrections 9/4 cases, totals 823/739; C6-70 note: consider decline when _fused_enabled()) |
| v6-gvfprep | C6-30 | radiation/gvf_prepared.py | worker SHIP-CANDIDATE (expr 36→2; 78+82 pass); **C6-60 in flight (v6-rev630)** |
| v6-gvfpost | C6-31 | radiation/gvf_postprocess.py | worker PASS (125 tests; serial slower, parallel 0.28x); **C6-60 in flight (v6-rev631)** |
| v6-decoder | C6-50 | geometry/visibility_prepared.py | worker DELIVERED (95/95; precedence exact; NOTE: prepared slower on dev tier 71.6 vs 58.1 ms — re-measure at C6-80 before adoption); **C6-60 in flight (v6-rev650)** |
| v6-memadm | C6-42 | runtime_memory.py | **LANDED e318c226** (APPROVE-WITH-NOTES rev3; patch apply --check PASS verified; 31/31; raw-safe count 2) |

## Queued (not dispatched)

| task | blocked by |
|---|---|
| C6-40 phase adapter (runtime_phases.py) | C6-10 + C6-03 (review) |
| C6-70 first-wave integration | C6-60 verdicts on all selected wave-1 patches |
| C6-80 small cold/warm portfolio | C6-70 |
| C6-81 residual choice | C6-80 |
| C6-90..94 conditional | C6-81 selection |
| C6-99 final integration | selected optionals reviewed |
| C6-100 freeze → C6-101 campaign → C6-102 audit → C6-103 handover | C6-99 |

Standing facts: routing = GLM via Z.ai, Opus unavailable (INVENTORY_C6-00.md).
24-tile target dataset still absent (synthetic 24-tile load = load test, not
actual-target claim). Exclusive benchmark lease starts at C6-80; wave-1 worker
timings are contended development-tier.

Integrator sign-off items for C6-70:
- C6-42 m7 §3: corrected geometry reservation 4.4320 GiB means single-job
  budgets in ~[3.88, 4.83] GiB would NEWLY raise ResourceAdmissionError.
  Accept stricter boundary, or defer width-2 admission to C6-40 phase adapter.
- C6-42 m7: GDAL_CACHEMAX enforcement in _child_environment converts
  reservation into enforced cap — confirm no per-worker cache regression.
- C6-22 finding (NEW base fact): at 5e1fab46 the retained wrapper
  (production) cylinder-shortwave route is NOT bitwise vs the serial
  reference — float32-vs-float64 deg2rad geometry profile, max ~1.2e-4
  (KsideD 764/1120 px, Kside 703/1120 px on the real 32x35 packet),
  identical with the candidate module absent. Parity gates for any
  cylinder-route specialization must bind to the wrapper route; serial
  comparisons keep the original comparison_v1 budget. Corroborated by
  C6-21 (same pre-existing differential failure
  test_compiled_patch_parallel_diagnostics, order-dependent, fails
  identically without either module).
