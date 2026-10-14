# Semantic and numerical contract

## Frozen public surface
Capture all seven functions: thermal_comfort, preprocess, build_inputs, build_wind_ext_coeff, run_walls_aspect, calculate_svf, run_utci_tiles. Preserve positional/keyword semantics, Python/CLI differences, import namespaces, timestamps, TIFF schemas, masks, extent, float storage and legacy exports. Keep the explicit compatibility distribution; prevent accidental collision with upstream. Distinguish current-main behavior from upstream corrections already documented.

## Typed operation graph
For every selected contribution, record nodes `(operation, input category, input dtype, shape/rank class, broadcast domain, arithmetic dtype, output dtype, rounding point, possible warnings)`. Types include Python float/int, NumPy scalar, ndarray rank 0, singleton rank 1/2, true field and Boolean masks. `_operands` is part of the model implementation, not disposable overhead.

Example: float64 air + float32 [[wall]] can yield float32 under the project's wrapper, whereas extracting wall before the add can yield float64. Singleton identity is not scalar execution equivalence.

Preserve surface-sun and surface-shade profiles independently; they can have DIFFERENT dtypes. Do not force both through the same specialization merely because old native admission did so. Reflection still uses the completed sky sum and Lup in original order.

Coefficient preparation may remain in trusted NumPy/SLEEF outside compiled loops. That is often the fastest safe initial port. Cache exact values only if every numerical dependency, rank profile, backend math mode, dtype, rounding context and mutation epoch matches.

## Observables
Outputs, public low-level returns, carried state after EACH timestep, source mutations, input read/error checkpoints, requested diagnostics, stored bytes, metadata, corruption detection and transaction recovery are observable. A private demand profile may omit values not consumed by any of these; full public calls remain complete. Do not manufacture zeros for omitted diagnostics.

## Special values and warnings
Preserve signed zero and tested NaN/Inf behavior. Exact bit tests cover all finite values and signed zero; preserve nonfinite masks and NaN payloads where the frozen contract observes payloads. Specify this before results. `np.errstate` warning/raise/call behavior and masks with 0*Inf invalidate many skip/partial-evaluation shortcuts. Default fast paths may admit only a proven safe finite range. Finite inputs alone do not prove finite intermediates. Preserve callback/error order by fallback or proof, not by globally suppressing warnings. Do not hoist evaluations for mask states never used if doing so creates a new error.

## Chronology and logical context
z[t+1]=F(z[t],u[t]) stays chronological. Do not parallelize timesteps or compute initial state independently. Execution blocks never change logical tiles, halos, physical scale, solar location, met aggregation or pixel extents. Source data read by neighbors is immutable until the stage barrier. A final output mask does not authorize removing shadow casters or intermediate neighbor values.

## Persistence
Same output/checkpoint frequency, generation cursor, payload integrity, flush/fsync/rename ordering and cancellation semantics. New private storage can be versioned only with a proven old-state loader and explicit version/migration policy, or remain disabled. Hash equality is evidence of equal content only at the checked snapshot, not a perpetual permission to skip corruption checks.

## Verification boundary
L0 packet arithmetic is NOT an upstream golden. Freeze an independent current-main oracle and original upstream CPU reference in separate environments. Candidate-generated fixture inputs are acceptable with disclosed generation; candidate-generated expected outputs are not baseline evidence. Reference repair is separate, versioned and hashed. Do not compare current-main-vs-candidate results as if they were SOLWEIG-GPU speedups.
