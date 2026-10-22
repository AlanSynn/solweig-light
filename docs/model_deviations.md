# Model behavior and deviations

This ledger separates inherited behavior, candidate compatibility repairs and
explicit reference policy. Optimization does not authorize a scientific
correction. The numerical oracle is SOLWEIG-GPU
`0d7fe742abeeddd890dd58fc76ed7f78bd47faec`; the latest-upstream source comparison
uses a separate pin in [provenance](provenance.md).

The detailed predecessor ledger is preserved in Git at
`e6a87f9be16beeb4be6f347b2a48760eba5660fc:docs/model_deviations.md`.
Retained reference packets below contain executable outcomes; older report
paths in that historical ledger may refer to archived evidence.

## Approved inherited scientific limitations

Policy [inherited-svf-umep-compatibility-v1](../development/reports/scientific_release_exceptions.json)
approves retaining upstream behavior for exactly four independent checks.
Their outcomes remain **failed**, with approved known-limitation disposition:

| Independent check | Retained behavior and evidence |
| --- | --- |
| Open-scene SVF physical bounds, full `svf_calculator` | Directional open-scene unity fails under inherited option-2 initialization. |
| Open-scene SVF physical bounds, compact calculator | Same inherited failure; original/candidate agree bitwise across all 19 outputs on the recorded 9×13 fixture. |
| Independent UMEP ground view, land-cover variant 0 | SOLWEIG-GPU/candidate float32 `gvfSum` differs from UMEP float64 beyond `1e-6` in 12/99 cells; maximum `1.7106533043431682e-6`. Normalized output passes. |
| Independent UMEP ground view, land-cover variant 1 | Same inherited precision limitation; all 17 candidate fields pass the unchanged original-Torch comparison. |

Executed option-2 SVF initialization declares 153 azimuth entries but writes
149. Declared band counts are `[31,30,28,24,19,13,7,1]`; writes are
`[31,29,27,24,19,12,6,1]`. Float32 reciprocal arithmetic and integer truncation
shorten four loops; the consumer uses declared lengths and reaches four
trailing zeros. This is not explained away as ordinary quadrature. A corrected
initializer needs a separate scientific policy and downstream validation.

Do not claim unobstructed directional vegetation SVF equals unity or complete
UMEP agreement at that independent tolerance. Tests, fixtures, assertions,
tolerances and failed records are unchanged. A changed/worsened result needs
fresh investigation. The exception does not cover exact-zenith visibility,
math-profile admission, other failures or overall release qualification.

## Geometry and low-level compatibility outcomes

| Behavior | Disposition and reproducible evidence |
| --- | --- |
| Combined vegetation/building visibility can equal 2 on short-ray trunk cases, in float32 and float64. | Preserve exact values with categorical/raw storage; Boolean conversion loses information. [Shadow tests](../tests/differential/test_geometry_reference.py). |
| Unobstructed flat zero-elevation ground has some `sh=0` cells at exact zenith. | Inherited independent physical-check failure, outside the four-check exception. No correction is applied; other characterized positive-altitude flat cases pass. |
| Full SVF patch option 4 raises `TypeError` from float annulus bounds used as integer range bounds. | Preserved upstream failure; a valid patch table does not imply successful full SVF option 4. [SVF packet](../tests/reference/svf_original_cpu/manifest.json). |
| Low-level UTCI calculator fails masked assignment for characterized profiles containing float64 arrays. | Preserve the observed failure rather than silently narrow accepted arrays. Direct `utci_polynomial` retains its different mixed/float64 contract. [UTCI packet](../tests/reference/utci_original_cpu/manifest.json). |
| Compiled wall-shadow/GVF coverage is narrower than every low-level dtype. | Non-admitted profiles use the characterized NumPy path without silent dtype narrowing. |

## Driver, ground view and state

The port preserves compatibility behavior for land-cover normalization and
aliasing, positive-median terrain altitude handling (the driver substitutes
3 m), wind floors, canopy transmission, logical tile/overlap context and
timestamps. These are not opportunities for an optimization to change the
scientific model.

Own-met UHI column 24 is retained independently of `use_uhi`. Radiation uses
base air temperature while comfort-stage temperature receives UHI; WBGT
sun/shade selection uses the inherited `shadow < 0.1` rule. No unit or
scientific correction is implied by compatibility.

Ground-view scratch retains values outside each ray's updated slice.
`sunwall` normalization is in place, and water-cell `Tg` changes after the
initial directional `Lup` computation, so later directions can see different
temperatures. Building inputs are not mutated by the minimum recurrence.
Beyond-raster traversal and zero rounded second-distance cases retain the
recorded `RuntimeError`/`UnboundLocalError` outcomes. See the
[ground-view packet](../tests/reference/ground_view_original_cpu/manifest.json).

Chronological scalar dtypes vary across day/night. Temperature/delay maps,
first-day state, daily water/CI resets and scalar promotions are carried
rather than reconstructed independently for each timestep. The
[delay packet](../tests/reference/delay_original_cpu/manifest.json) includes
first-day flags and step-duration boundaries; restart must preserve the
complete state.

Low-level box shortwave rejects a native-bool condition at the corresponding
upstream tensor operation. Active longwave sun-facing classification rejects
a native scalar solar altitude at its tensor tangent helper; nighttime or
inactive-patch calls do not reach that failure. Equivalent `TypeError` classes
are preserved, without reproducing exact Torch diagnostic wording.

## WRF timestamp repair

The original parser returns `(datetime, domain)`, but the WRF time-window
filter compares that tuple directly with datetimes and raises `TypeError`.
The explicit one-line [wrf_timestamp_v1.patch](upstream_patches/wrf_timestamp_v1.patch)
selects element zero only at that comparison. Candidate WRF follows this
versioned repair. Successful outputs are compared with the separately labeled
[patched CPU packet](../tests/reference/wrf_patched_cpu/manifest.json), while
[original forcing evidence](../tests/reference/forcing_original_cpu/manifest.json)
retains the unmodified failure.

Tuple sorting/domain order, inclusive endpoints, accepted filenames, units,
rotation and hourly coordinates are unchanged. Missing-hour and duplicate-
domain handling are not repaired; the recorded multiple-domain/one-hour shape
failure remains a failure. `build_inputs` builds static rasters, matching the
executed upstream entrypoint rather than its broader met/wind docstring.

## Candidate compatibility defects repaired

Two diagnosed candidate defects were repaired without changing model,
fixtures or tolerances:

- Ground-view tensor-origin float32 scalar angles had been promoted to float64
  around Python angular constants. Strict wall-aspect masks differed at 65°,
  145°, 245° and 325°. Compiled and fallback paths now preserve upstream
  promotion; the diagnosed 24-hour scene and expanded seven-scene output gates
  passed. This was a candidate bug, not an upstream scientific correction.
- SVF annulus arithmetic differed by one ULP and changed a near-zero derived
  angle, amplifying reflected shortwave beyond its gate. The repair preserves
  reciprocal-then-multiply float32 arithmetic and sine ordering. Of 180
  characterized original weights, 174 were bitwise equal and six differed by
  one ULP on that host; boundary sums/angles were exact. Seven complete scene
  gates and 18 geometry export fields per scene subsequently passed.

These finite checks do not establish bitwise equivalence for every input or
platform. Source-based cache identities invalidate pre-repair geometry.
Historical details and original hashes remain in the predecessor ledger.

## Transcendental and reference-profile differences

A historical Linux original-Torch/MKL dense1024 comparison failed TMRT:
maximum `0.04949951171875 °C` against the `0.01 °C` gate. At the diagnosed
cell, a one-ULP ASVF acos difference moved four building patches across strict
sun/shade boundaries; equality belongs to neither class. Greater precision
was not a universal repair: M1 and Linux dispatch differed. Serial/compiled
radiation agreed given identical ASVF bits.

Standalone MKL experiments supplied diagnostic evidence but MKL was not
adopted as a production dependency. The versioned
`solweig-portable-sleef-5a1d179d-v1` profile now supplies source-derived bounded
helpers plus the original NumPy-ufunc fallback, under an explicit canonical
original-SLEEF reference amendment. See
[the numerical policy](compatibility.md#portable-math-profile) and
[validation boundaries](provenance.md#validation-boundaries).

Both platforms passed retained large-scene SLEEF field/schema gates and
actual-call classifier corpora. Later Linux candidate comparisons with
original MKL also passed final-output gates on those scenes. Historical
pre-profile failures and strict-boundary disagreements remain recorded;
neither result establishes universal MKL or CUDA parity. Large admissions
preceded the final fallback-only accepted-domain repair, so they are not
fresh tests of that repaired wheel. Full release qualification remains
incomplete.
