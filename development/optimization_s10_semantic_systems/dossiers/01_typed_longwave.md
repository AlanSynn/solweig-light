# D01: Typed longwave coverage, not another scalar leaf contest

Candidates T01/T02/T04/T08. Owners: one numerical implementer; independent proof reviewer. Shared engine/driver wiring belongs to integrator. Primary references S03-S07, S21-S22, E01-E02.

## Source-bound problem
`Tgmaps_v1` uses `wall_pos=np.where(lc_class[:,0]==99)` then `lc_class[wall_pos,3]`. With one standard wall row this is a one-element array, normally shape (1,1), not a spatially varying wall map. Pipeline retains it as float32. Daytime expressions preserve nonzero rank. `Lcyl_v2022a_primary` and `define_patch_characteristics_primary` reject ndim != 0 for Tgwall, sending such calls to reference code before the bounded stream. Night uses `_array(0)` and may take the admitted path. Do not claim all real daytime calls take this route until runtime counters confirm shapes/dtypes and the first rejecting guard.

The first deliverable is an actual installed-call route census. Capture every time step's profile without serializing its full arrays: name, Python type, ndarray shape/strides/dtype, unique count only for size-one inputs, admitted guard, active patches, retained/full demand, math profile, leaf route. One representative 64-square landcover scene and one non-landcover control with 24/48 steps suffice initially. This work is not a profile of a synthetic scalar-only reducer.

## Separate three profiles
S is the existing scalar profile. U is a singleton ARRAY profile; a value is uniform but rank changes promotion. F is a true broadcastable field, deferred unless present in relevant user workloads. Empty arrays, multiple wall rows, arbitrary subclasses and unsupported broadcasting stay on the existing route in the first patch. An output field that is constant by coincidence is not automatically U.

Do NOT call `.item()` before original expression preparation. Do NOT remove every ndim guard. Do NOT squeeze singleton values at material-loading time, which would change other consumers and their errors.

## Exact preparation and typed DAG
At the existing coefficient checkpoint, execute original `_array`, `_operate`, `_divide`, trig and powers on their ORIGINAL shaped inputs. These arrays are tiny in U. Extract only completed coefficient values together with their typed-origin descriptor. Record every operation after extraction which the original performed on an array or Boolean raster. A scalar carrying the same bits is legal only when the NEW kernel reproduces the original arithmetic dtype explicitly.

A useful private immutable plan is:

    profile_id / profile_version / math_identity
    source rank-and-dtype descriptors
    surface_sun_value + arithmetic profile
    surface_shade_value + arithmetic profile
    patch constants with original dtypes and strides
    accumulator dtype and final-store dtype per term
    private demand / fallback continuation / ownership epoch

Do not require sun and shade to have the same dtype. In U, the sun expression can be float32 while the shade expression is float64 because its source path lacks the singleton array. Table lookup values may therefore need different storage dtypes. Reflection arithmetic must be derived separately from `(Ldown_sky + Lup)*(1-ewall)*.5/pi` with original cast points.

Implement two or three explicit typed kernels, or generated source from a REVIEWED finite expression map, not an unconstrained compiler/code generator. A profile-specific helper may read a uniform value for all receivers but must cast constants and operands where the original did. Keep trusted NumPy/SLEEF coefficient preparation initially; transcribing pow/trig into Numba at the same time needlessly enlarges proof scope.

## Loop contract
Each receiver owns the original ten primary accumulators. First sweep visits every original patch and each contribution in its original order. Reflection is computed only after sky sum completion. Second sweep stays ordered. Compose final Ldown/Lside and requested diagnostic results exactly as before. Public FULL_DIAGNOSTICS remains complete. Internal unrequested cardinal outputs use existing NOT_REQUESTED semantics, never fake zero frames.

## Equivalence proof outline
For each graph node, equality follows from equal input bits, the same operand conversion, operation and rounding behavior. Then use patch-index induction: equal entering accumulator and equal typed contribution imply equal stored accumulator. Reflection follows from equality of completed sky state and Lup. This requires matching the implementation's math profile; matching algebra on real numbers is insufficient.

A one-element-array-to-scalar rewrite is invalid if it changes any earlier node's dtype. The bundled semantic probe demonstrates a counterexample, not complete pipeline equivalence.

## Minimal implementation sequence
1. Census and frozen source trace.
2. Add U-only coefficient preparation with no dispatch change. Test intermediate types/bits.
3. Add U kernel and compare direct outputs against the FULL original path projected to needed fields. Do not use the new kernel to generate expected outputs.
4. Add guard and private stream integration. Existing S, raw and unsupported F paths unchanged.
5. Trace every carried state and final artifact in genuine 64/128-square 24/48-step runs.
6. Only after correctness measure contiguous preparation+classification+decode+reduction+output composition on held-out 128/256 scenes.

## Tests that matter
S/U32/U64 scalar-array combinations; 0d vs (1,) vs (1,1); multiple wall rows rejected; noncontiguous coefficient views; positive/negative zero; safe extreme finite values and guarded overflow; strict `np.seterr` modes; false mask with nonfinite coefficient; no landcover; standard landcover; manually supplied varying field fallback; day/night boundary; no active sun patches; raw/binary/ternary visibility; 128 and 1024 block sizes plus nonmultiple tail; restart mid-day; original error order.

Do not pay a full-raster admission scan per patch. Where safe finite preconditions are needed, derive conservative bounds once from already owned inputs or use original guarded behavior. Warnings from unused table states must not be created.

## Success and stop
A route counter must show U calls actually executing the new kernel. Measure saved FULL daytime stage time, not night vs day ratio. Keep installed default arguments unchanged. If U is rare, parity cannot be established, or the overall stage does not improve beyond noise, retain reference and record the causal result. This does not justify reopening the closed ISPC track.
