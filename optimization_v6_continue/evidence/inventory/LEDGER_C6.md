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
| v6-recipe | C6-10 | geometry/recipe.py + integration recipe | **LANDED 443ee2b7** (APPROVE-WITH-NOTES; post-image scratch-verified; 88/88; C6-70 deferred-coverage + pre-existing raster_fingerprint path-dependence noted) |
| v6-lside | C6-20 | radiation/pipeline_demand.py | **LANDED 2304449d** (APPROVE-WITH-NOTES post-fix; 65/65; night guard closed) |
| v6-cyllw | C6-21 | radiation/cylinder_longwave.py | **LANDED eea97fbd** (APPROVE-WITH-NOTES, 0 blocking; C6-70 handoff: demand_scope+restore, assert cyl=1) |
| v6-cylsw | C6-22 | radiation/cylinder_shortwave.py | **LANDED 99681b53** (APPROVE-WITH-NOTES; prose corrections 9/4 cases, totals 823/739; C6-70 note: consider decline when _fused_enabled()) |
| v6-gvfprep | C6-30 | radiation/gvf_prepared.py | **LANDED 986c5a09** (APPROVE-WITH-NOTES; snapshot semantics + counts independently verified; 160/160) |
| v6-gvfpost | C6-31 | radiation/gvf_postprocess.py | **LANDED d7eb148d** (APPROVE-WITH-NOTES post-fix; 139/139; recipe regenerated from verbatim base call site) |
| v6-phases | C6-40 | runtime_phases.py | **LANDED 3f3e8b8d** (APPROVE-WITH-CONDITIONS; F1 recipe fix + F2 windchannels=1 confirmed + F5 D04 retention reading recorded at landing; phases 17/17) |
| v6-decoder | C6-50 | geometry/visibility_prepared.py | **LANDED** (module 4b83452b; wiring 58d7fe23; 95/95; NOTE: prepared slower on dev tier 71.6 vs 58.1 ms — re-measure at C6-80 before adoption) |
| v6-memadm | C6-42 | runtime_memory.py | **LANDED e318c226** (APPROVE-WITH-NOTES rev3; patch apply --check PASS verified; 31/31; raw-safe count 2) |

## Landed — C6-70 first-wave controlled integration (integrator commits on this branch)

| commit | task | content | gate |
|---|---|---|---|
| 47cda54f | C6-70a | C6-10 recipe: service.py produces via numerical_geometry_recipe, shared identity/key; pipeline geometry_key + guarded_producer | adapted recipe/recipe-census/e2e/unit-geometry tests green |
| 717a7e72 | C6-70b | C6-42 W1 phase admission (api.py) + W3 GDAL_CACHEMAX (runtime.py); W2 deferred to C6-40 | phase-memory suite green (importers pinned api.py+runtime.py) |
| 0358497a | C6-70c | C6-20 Lside demand dispatch call site (engine.py) | lside + radiation suites green |
| 02c0efa4 | C6-70d | C6-21 Lcyl by_demand call site (engine.py) + pipeline private demand scope (cyl_lw/cyl_sw) | cylinder suites green (kernel-level) |
| 15dfbf2a | C6-70e | C6-22 narrow cylinder-shortwave hook (patch_radiation.py; declines under _fused_enabled) | cyl_sw + Kside differentials green |
| 6f8325aa | C6-70f | C6-30 prepared GVF dispatch, threads>1 branch (engine.py) | gvf_prepare suite green |
| 61c76a17 | C6-70g | C6-31 wrapper call in _gvf_fused (ground_view.py) + integration fixes: gvf_postprocess dtype guard (f64 lup_term delegate; SBC outside _supported), count-test floor re-measured (fused 972 < full 2285 < prepared 2745) | gvf_prepare+gvf_postprocess 217/217 |
| 58d7fe23 | C6-70h | C6-50 decoder wiring (shortwave prepend + longwave compiled branch, patch_radiation.py) + decoder conftest shims + spied recipe test | decoder 95/95; cylinder_lw+sw 125/125 |
| 78d242a6 | C6-70i | pipeline demand-scope fixes: set_demand_profile returns None (scope-finally ValueError every run) -> demand_profile() capture; C6-20 driver-side radiation_demand context added (fast path was silently inert) | found+fixed by L2 differential |
| 5aa82325 | C6-70j | L2 chronology differential evidence (probe + logs + record) | L2 GREEN (below) |

L2 chronology differential (evidence/integration/L2_chronology_differential.md):
base 8e0b3877 vs integrated 78d242a6, 96x96 real-motif scene, 24 steps —
Lside 24/24 + Kside 14/14 events bitwise (inputs+outputs), all 11 final TIFFs
sha256-identical, cylinder-longwave equality transitive (Ldown in Lside inputs
+ bitwise Ldown/Tmrt TIFFs).
**C6-70 C6-60 review: APPROVE-WITH-CONDITIONS (independent GLM review; Opus
unavailable) — conditions closed by db5928fe** (F1 empty-jobs guard; F2
threads=2 whole-pipeline differential GREEN incl. wired GVF hooks; F3
accepted-residual record; see evidence/integration/C6-70_review_dispositions.md).
Reviewer recompute: 541 + 35 scoped tests green on the integrated tree.

## Queued (not dispatched)

| task | blocked by |
|---|---|
| C6-80 small cold/warm portfolio | **DONE** (evidence committed 2ce117e0) |
| C6-81 residual choice | **DONE + APPROVE** (selection 5928ead4; decoder declined 46450c75; independent GLM review APPROVE, Opus unavailable — evidence/reviews/C6-81_review_decoder_decline.md; F1 marker registration fixed at landing) |
| C6-90..94 conditional | **NOT SELECTED** (no measured activation case; see evidence/selection/C6-81_selection.md) |
| C6-99 final integration | **DONE** — surface confirmation (zero selected optionals; evidence/integration/C6-99_surface_confirmation.md) |
| C6-100 freeze | **DONE** — frozen at ea2eed53 (wheel gate PASS bitwise; true-TIFF/state gates pass on substance; raw-True admission-boundary case dispositioned in evidence/freeze/C6-100_integrator_dispositions.md) |
| C6-101 single campaign | **BLOCKED-UNVERIFIED** — actual 24-spatial-tile dataset still absent; no frozen real target; no actual-target or release timing claim exists |
| C6-102 audit → C6-103 handover | UNBLOCKED (audit covers the tree as-is; carries raw-True + dataset-absence items) |

Standing facts: routing = GLM via Z.ai, Opus unavailable (INVENTORY_C6-00.md).
24-tile target dataset still absent (synthetic 24-tile load = load test, not
actual-target claim). Exclusive benchmark lease starts at C6-80; wave-1 worker
timings are contended development-tier.

Integrator sign-off items for C6-70 (status after integration):
- RESOLVED by adoption: m7 §3 boundary stays as landed in C6-70b (W1
  in api.py with policy='reject'); width-2 sensitivity is inherited from
  the pre-existing availability-sensitive budget resolution and is now
  C6-40 phase-adapter territory.
- RESOLVED at C6-80: GDAL_CACHEMAX cap shows no per-worker cache
  regression at the timing tier (cap active in worker/phase children;
  integrated cold wins, warm wash — evidence/portfolio/README_C6-80.md).
- STANDING base fact (unchanged): wrapper cylinder-shortwave route is not
  bitwise vs serial reference at base; specialization gates bind to the
  wrapper route (C6-70e respects this; hook declines under fused).
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
