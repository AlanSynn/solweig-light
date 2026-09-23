# C6-70 review condition dispositions (C6-60 review of C6-70 integration)

Date: 2026-09-21. Review: `evidence/reviews/C6-60_review_C6-70_integration.md`
(APPROVE-WITH-CONDITIONS). Label: conditions closed by integrator; the review
itself is independent GLM review; Opus unavailable.

## Condition 1 — F1 (empty-jobs ValueError): closed by code

`api.py` W1 call now guarded with `if jobs:`. A degenerate zero-tile public
run behaves exactly as at base (silent no-op through `plan_admission([])` /
`execute_tiles([])`); `plan_phase_admission` keeps its own non-empty
contract for every real call. This is a one-guard deviation from the m7 W1
hunk verbatim form (the hunk otherwise landed byte-identically); recorded
here as the required disposition.

## Condition 2 — F2 (GVF hooks not exercised by the L2 differential): closed
## by a threads_per_worker=2 whole-pipeline differential

Rerun of `chronology_probe.py` with `threads_per_worker=2` (argv[4]), both
trees, same 96x96 scene, 24 steps (`l2-logs/l2t-*.jsonl`):

- integrated (threads=2) exit 0, 62 events; base (threads=2) exit 0, 62 events.
- Lside 24/24, Kside 14/14 events bitwise on inputs and outputs.
- Cylinder longwave primary outputs (out[0] Ldown, out[1] Lside) 24/24
  hash-identical under direct base/head pairing.
- All 11 final TIFF sha256 identical.

At threads=2 the engine `gvf_2018a` branch takes the wired route
(`prepared_gvf_step` -> `gvf_postprocess_block`), so the C6-70f/C6-70g GVF
hooks ARE exercised by this differential; any GVF divergence would surface
in the bitwise Kdown/Lup/Tmrt TIFFs. Condition closed by direct evidence,
not by the recorded-rationale alternative. (Probe note: `cpu_budget` is
raised with `threads_per_worker` to satisfy the admission invariant.)

## Condition 3 — F3 (C6-10 step-E residual): accepted residual, recorded

Uncovered step-E metadata/input-perturbation cases at C6-70: geotransform/
projection perturbation; DEM/DSM content perturbation (only Trees was
perturbed); patch-table/profile/implementation perturbation; input mutation
during preparation; concurrent readers/producers; overwrite=False failure
paths. Accepted as residual because implementation perturbation rekey
follows from the fingerprint closure argument reviewed at C6-10, and the
concurrency/overwrite paths are store-level code the C6-70 range does not
touch. To be revisited only if a later task touches
`geometry/{recipe,service,cache}.py` semantics.

## F4/F5 (informational) — acknowledged, no action owed

F4 holder asymmetry and `-O` assert note: accepted; dispatchers re-verify
admission internally. F5 wording items: the L2 record's longwave claim is
superseded by the reviewer's direct out[0]/out[1] pairing (also now at
threads=2); probe `collect()` drop behavior accepted given the fixed 6-name
engine unpack; the C6-70e deviation is durably recorded in this evidence
tree: the `_fused_enabled()` guard in `patch_radiation._shortwave_
visibility_blocks` pins the experimental fused route to base behavior and
is default-inert (`SOLWEIG_LIGHT_FUSED_RAD` unset/OFF unchanged).
