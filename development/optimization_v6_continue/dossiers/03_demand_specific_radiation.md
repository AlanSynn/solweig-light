# D03: remove unobserved work while retaining the full model and API

## General proof rule

Let O be the complete observable set: requested TIFFs, all carried state, later neighbor reads, public low-level returns, supported mutations/failures and required warning behavior. Only nodes outside the backward slice of O may be removed. Save flags alone do not prove physical terms dead. Geometry/source pixels that never appear in an output may still affect neighbors.

Use an explicit private demand profile, for example PIPELINE_CYLINDER_ANISOTROPIC versus FULL_DIAGNOSTICS. Public signatures and full-return functions keep their existing path. Do not call a reduced kernel and fill missing fields with fake zero arrays. Keep optional trace mode on the full path, or return named optional diagnostics with actual missingness in a PRIVATE structure. Do not let telemetry become the benchmark result.

## R-A: anisotropic Lside ground-only result

In Lside_veg_v2022a, when anisotropic_longwave==1, each final directional result is exactly the original `_operate(np.multiply, LupDirection, .5)`. The preceding SVF angle transforms, Lvikt polynomial and wall terms do not feed the return. [S10]

Private specialization:

    # Same scalar conversion, promotion and ownership as the demanded nodes.
    return tuple(original_multiply(Lup_d, .5) for d in [E,S,W,N])

Keep allocation ownership: return four new original-operation results, not views that would later mutate Lup. Do not add cardinal patch diagnostics before TMRT; the original engine adds them afterwards for cylinder mode.

Important guard: removed operations can issue warnings or raise under np.seterr, malformed shapes, object/duck arrays, bad inputs or unexpected global state. Do not assume a finite Lup alone certifies every skipped node. Admit only a verified core profile and preserve necessary validation, with original fallback for unproved warning/error domains. Do not globally silence warnings. If preserving warning behavior makes a domain expensive, first ship a narrower successful finite profile. Invalid/public calls keep the existing order of failures. Keep a trace full path so diagnostics can reproduce the original graph.

Historical post-S07 256 census: this function about .665 s of 9.859 s. Removing all its cost would bound that particular measured route at about 1.072x, not a 2x full-pipeline claim. It is a low-code-cost improvement, not the entire solution.

## R-B: reduced cylinder longwave

Current _longwave has primary accumulators 0..9 and cardinal-only accumulators 10..13. The first two returned totals depend on 0..9; the cardinal loop updates do not feed them. The main sky sweep is followed by a reflected field depending on completed sky-down + pixel Lup, then a second ordered sweep. Keep both sweeps and every primary operation exactly. [S11/S12]

Mathematical projection:

    state = (a,c),  a' = F(a, inputs), c' = G(c, a, inputs)
    pi(state)=a; pi(Phi(state))=F(pi(state),inputs)

No c value is read by F. By induction over ordered patches/sweeps, the primary totals are identical. Cylinder TMRT uses the primary totals and the four Lup*.5 ground terms. It does NOT use the later-added cardinal diagnostic patch fields. The private TIFF driver neither writes these fields nor carries them as state. Revalidate this at actual HEAD.

Implementation: a private longwave kernel returns only the required totals and any genuinely demanded internal values. Allocate only necessary columns; do not multiply/add cardinal-direction projection terms. Full public Lcyl and Solweig_2022a_calc retain all diagnostics. Keep daylight/night, canopy/trunk, reflection and exact zero-mask arithmetic. Component trace tests compare the demanded values to the untouched full kernel. Whole-pipeline tests compare every carried map and output. Four no-longer-computed diagnostic fields must be marked not requested, never compared as if generated.

The historical Lcyl family occupies ~26.9% of the instrumented warm census. A stage gain of 1.5x would imply ~1.10x total under those fixed fractions; 2x ~1.16x. It does not prove current large-stage fractions.

## R-C: cylinder shortwave scratch/setup specialization

Kside's admitted cylinder branch consumes reduced columns 0..3, while generic _shortwave allocates 20 and its wrapper builds box-only direction cosines/gates. Preserve seven public final fields, direct term and four Kup/2 fields; remove only unused generic scratch/setup in the known cylinder route. This cuts that reduction-output allocation from 80B to 16B bytes per B-pixel block. It is not a fivefold speedup of all radiation. [S12]

Guard scalar and ndarray semantics exactly; preserve public non-cylinder paths. Tables containing transcendental values require original math/layout behavior. Removing evaluations that can throw requires the same observability audit as R-A. Do not activate dormant fused decode here.

## R-D: exact partial evaluation, only after typed DAG extraction

For a contribution E(c, mask1, mask2) with pixel-independent coefficients and Boolean masks, precompute all four expressions using ORIGINAL intermediate dtypes and casts. The source may mix float64 scalar coefficients with float32 arrays, so a blindly float32 table is wrong. Retain each contribution separately when the baseline adds them separately. Do not merge additive terms into one table cell.

A table lookup for an exactly equal discrete input is not approximation. raw visibility outside the established categorical set still decodes original bits. Build cost CP versus NP is useful only if expression work actually dominates lookup/addition. Do not multiply its benefit by R-C or prepared decode without recomputing overlapping work.

## File and test plan

Family worker writes new private kernel module and family tests. Integrator owns engine.py, pipeline.py and the profile selection. Avoid duplicating the 1,800-line engine to create a fast path: extract the narrow shared dispatcher/body boundary with full fallback, preserving the public signature mechanically.

L1: original function calls on shape edges, float32/64 scalar-origin cases, sign zeros, mask 2/raw modes, day/night and simultaneous readers. Exercise exceptions with np.seterr(raise), bad shapes, unsupported dtype and alias views. L2: full 24/48-step small real TIFF with requested ten-output profile plus default output flags; compare metadata/masks, all state and demanded radiation. Full diagnostic API tests must still run. L3: time reduced core path and full public fallback separately; do not compare a diagnostic run to a reduced-output benchmark without naming the contract.
