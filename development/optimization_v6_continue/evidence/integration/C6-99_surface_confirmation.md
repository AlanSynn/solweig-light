# C6-99: final integration surface confirmation

Date: 2026-09-21. Owner: integrator. C6-81 selected **zero** conditional
implementation tasks (evidence/selection/C6-81_selection.md), so C6-99
reduces to confirming the branch's final surface: every landed change
reviewed or rejected, no public stubs, gate green, contracts intact.

## Final surface (base 8e0b3877 → HEAD 88ef6db0, branch perf/claude-glm53-cpu-v5)

`src/` delta — 10 files, +1173/−86:

| file | change | review |
|---|---|---|
| geometry/service.py | C6-70a shared numerical geometry recipe + identity/key | C6-60 review of C6-70 (APPROVE-WITH-CONDITIONS, closed db5928fe) |
| pipeline.py | geometry producer/key wiring; private demand scopes (C6-70d); C6-70i scope fixes | same |
| radiation/engine.py | C6-20 Lside demand dispatch (c); C6-21 Lcyl by_demand (d); C6-30 prepared GVF threads>1 branch (f) | same |
| radiation/ground_view.py | C6-31 wrapper call in _gvf_fused (g) | same |
| radiation/gvf_postprocess.py | dtype guard delegating f64 lup_term to reference (g) | same |
| radiation/patch_radiation.py | C6-22 shortwave hook (e); C6-50 decoder wiring (h) | same; decoder now gated per C6-81 (below) |
| api.py | C6-42 W1 phase admission (b) + `if jobs` guard (F1 disposition); C6-40 phase route `_precompute_geometry_phase` + gate `len(pending) > 1 and workers > 1 and cache_enabled` | C6-60 review of C6-40 (APPROVE-WITH-CONDITIONS, closed at landing); C6-60 review of C6-70 |
| runtime.py | C6-42 W3 GDAL_CACHEMAX cap (b) | C6-60 review of C6-70 |
| geometry/visibility_prepared.py | C6-50 module; **C6-81: default-declined, opt-in `SOLWEIG_LIGHT_PREPARED_VIS=1`** | C6-50 review; C6-81 review APPROVE (evidence/reviews/C6-81_review_decoder_decline.md) |
| runtime_phases.py (new) | C6-40 geometry phase adapter (ordered publication, journal-first/manifest-last, numeric-first failure, native thread-cap pin) | C6-60 review of C6-40 |

New public-surface items in the whole range: the opt-in environment variable
`SOLWEIG_LIGHT_PREPARED_VIS` (default OFF; same convention as the existing
`SOLWEIG_LIGHT_FUSED_RAD`) and the `prepared_default_off` pytest marker.
No signature, `__all__`, CLI, TIFF, or workflow-contract change; all seven
workflows and the seven-workflow compatibility surface are untouched.

## No public stubs

- runtime_phases.py is functional and wired (api.py phase route, verified
  firing in C6-80 P2 cells with journal+manifest publication).
- visibility_prepared.py is fully implemented; the C6-81 gate is a measured
  performance decline of its DEFAULT route, not a missing implementation —
  the opt-in route remains exact and reviewed.
- No TODO/stub markers exist in src at base or at HEAD
  (`git grep -n "TODO\|NotImplemented" <rev> -- src/` = 0 matches at both
  8e0b3877 and 88ef6db0).

## Gates at confirmation time

- Combined v6 suite, single process, `PYTHONPATH=src NUMBA_NUM_THREADS=2`:
  **560/560 green** (gvf_prepare, gvf_postprocess, decoder, cylinder_lw,
  cylinder_sw, lside, geometry_recipe, memory, phases) — reviewer-measured
  and reproduced.
- L2 chronology differential GREEN (5aa82325; threads=2 GVF-inclusive
  closure db5928fe); C6-80 outputs bitwise-identical across trees in all 64
  lease runs (2ce117e0).

## Rejections on record

- Prepared decoder as default route — measured +21–24% per full-frame sweep
  (C6-80), declined 46450c75, review APPROVE.
- Fused radiation route — stays OFF (v5 measured rejection unchanged).
- C6-90..94 — not selected (no measured activation case; C6-81 record).

## Remaining gap (unverified, not claimed)

The actual 24-spatial-tile workload dataset is still absent: C6-101's
single large campaign has no real target scope, so no actual-target or
release timing claim is made anywhere in this tree. Measured scoped gains
(dev-tier): cold −6.4/−9.8% (S1), −6.1/−16.2% (T2), −10.9% (P2 t256);
warm steady-state wash with the decoder loss now declined.
