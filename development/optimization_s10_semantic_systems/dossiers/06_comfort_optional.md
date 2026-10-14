# D06: Comfort, input representations and optional workflows

Candidates C01-C06/S17. Sources S05/S17/S23/S24/S30. Local audit of actual comfort/optional implementations is required before modifying them; this packet does not claim a new full line-by-line review of all optional modules.

## Uniform forcing and copies
Pipeline currently builds a full temperature raster from zero + Ta + UHI, reads its first element for uniform UTCI, and forms tmrt=zero+Tmrt. For uniform UTCI input, evaluate the exact two-step scalar expression with original casts, then materialize Ta only when WBGT/output needs it. Do not simplify Ta+UHI if zero addition or rounding is observable. Tmrt copy can be removed only with alias/ownership proof through UTCI, writer and state.

UTCI itself is a required output in the standard pipeline. There is no permission to skip it because no save_utci flag is visible. Inspect OutputPlan and StreamingOutputs before demand pruning. Building/output masks cannot remove geometry or radiation sources that affect neighboring pixels.

## UTCI
Reuse current polynomial, scalar vapor preparation and evaluation order. Common subexpressions may be computed once if they are identical typed nodes; Horner, regrouping and mixed precision are not automatically exact. Vectorize independent receivers. Fusing input preparation, polynomial and output mask is useful only if all warnings and intermediate public observables are preserved. Profile before touching a small comfort fraction.

## WBGT
The global solver's stopping rule is part of behavior. Array-wide convergence cannot become independent per-element termination without proof. Keep phase, bounds, pressure/temperature units, wetbulb type and sun/shade selection. np.where evaluates both branches; lazy branch-only evaluation can hide errors. A first improvement can fuse already prepared hcg/globe/combination without modifying the wetbulb solver.

## Wind
All 12 direction files currently may be read and validated before simulation. A lazy memory strategy can still validate all required metadata/content once, but cannot defer malformed-unused-file errors invisibly. Preserve nearest-direction tie rounding, invalid direction fallback and minimum speed. Reuse products only for exact met bits and immutable coefficient identity. An array LRU must be budgeted; memory-saving and I/O-saving are distinct claims.

## Optional workflows
Protect build_inputs, build_wind_ext_coeff, ERA5, WRF and UHI interfaces and lazy dependencies. Their performance denominator is a separate workload from prepared own-met TIFF simulation. Potential directions: cache spatial interpolation weights for identical grids, vectorize regular mapping, batch local extraction, reuse parsed met data and spatial index, parallel independent acquisition when user-authorized. Before implementation inspect units, external I/O, masks, provenance and actual API failure behavior. Labeled mocks test service integration only, never physical validation or a live-service speed claim. Do not install every optional service package just to optimize the core.

## Required checks
No-env normal import without Torch/CUDA/new backends; each public function contract smoke with real local data where feasible; optional mocks explicitly tagged; full output flag permutations selected by dependency coverage; float profile adversaries; unchanged input/output schema; UTCI/WBGT independent known cases; full chronological state and restart in L2. Missing optional credentials means unavailable, not passed, and does not block independent core work.
