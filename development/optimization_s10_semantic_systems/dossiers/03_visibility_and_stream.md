# D03: Visibility, diffuse radiation and bounded execution

Candidates R01-R10. Sources S06-S09/S19/S27. N9 bounded stream and mode-specialized decode are already default. Keep them as A, not as a proposed accomplishment.

## Consumer-specific geometry state
Longwave observes visibility through four predicates:

    sky = (sh == 1) & (vs == 1)
    veg = (vs == 0) | (vb == 0)
    wall = (original_float32((1-sh)*vb) == 1)
    refl = (sh == 0) | (vs == 0) | (vb == 0)

A four-bit q caches exactly these observations, not approximate visibility. Preserve original packed/raw visibility for exports, other consumers and fallback. No naive bool cast. Original wall predicate has floating subtraction and multiplication, so special values and warnings need admission/proof. This cache is private, versioned and keyed by exact source identity plus predicate implementation/profile.

Memory at 1024², P=153: q at 4 bits costs 76.5 MiB; three all-binary source channels cost 57.375 MiB. Keeping both increases persistent storage. The reason to try q is repeated decode/predicate avoidance, not a guarantee of smaller total memory. A one-byte q costs 153 MiB but could decode faster; allow a small one-byte-vs-nibble tuning test only when memory permits. Support block on-demand generation or a byte-budgeted cache; generation costs count in first-use/cold timing.

If building q evaluates all pixels before the original error checkpoint, corrupt payload errors may change order. Validate original channel streams in the same contract order, maintain lease lifetime, or restrict reuse to already-validated owned geometry. Do not replace a required read/check with a historical hash.

## Diffuse aniLum
The engine still computes aniLum via one full-raster Python update per patch before Kdown. Port this exact ordered recurrence separately:

    for independent receiver block:
        acc = original_zero
        for p in original order:
            d = original_lazy_diff_decode(p, block)
            acc = original_multiply_add_and_store(acc, d, lv[p,2])
        dRad[block] = original_multiply(acc, radD)

No FMA or reassociation. LazyDiffVisibility may have nonbinary values; retain the subtract/multiply provenance. Compare aniLum and dRad at their original point, then complete the chronology. Sharing this pass with shortwave is a later use-def graph transformation, not an assumption. If dRad is consumed before shortwave, only legal scheduling or bounded decode reuse may help.

## Three sizes, not one
Logical tile is physical model context. Public block_pixels is a caller-controlled execution option. Internal cache microtile and dispatch region may differ only without changing logical output or input error behavior.

Preferred shape:

    prepare immutable invocation
    allocate bounded slots
    coarse compiled region loop
        initialize active mask extent and tails
        classify bounded microtile
        decode/derive states directly in consumer layout
        execute original ordered arithmetic
        write disjoint output region
    join then release owner leases

Do not materialize the whole scene as [N,P] or [N/W,P,W] and call it streaming. Existing slots already have this bounded property; target residual repeat allocation or dispatch only if measured.

## Reuse correctness
A reused classification scratch can contain previous timestep's active patches. Clear inactive columns and valid tail extents before evaluation. Tests alternate day/night, active solar gates and partial blocks with poisoned buffers. Every worker has a unique slot; output views and descriptor lifetimes outlast asynchronous work. Parent must not hold a lock then make a child reacquire it in a deadlock cycle; share approved read-only descriptors under the owning lease.

## Backend-neutral order
Compare A=current N9; B=changed producer/layout in Numba; C=optional equivalent backend. Direct production avoids separate pack, but producer can still be slower. Never compute new E2E by subtracting a historical pack time. Measure contiguous calls. Existing ISPC/PoCL/Dr.Jit failures remain evidence; no speculative rebuild.

## Error/alias tests
Binary/ternary/raw; reserved code 3; misaligned bit start; shape 1; width < SIMD; odd tails; closed mmap; close during read; poisoned scratch; dtype/stride mismatch; output alias; exception before/after launch; scalar/U profile combinations; all-raw fallback. Errors after launch are loud. Exact output bits do not establish correct exception or ownership behavior.
