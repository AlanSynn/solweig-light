# D06: reduce repeated preparation without reviving failed P01

## Current opportunity

The accepted path decodes block/channel separately and then runs accepted ordered reducers. At 256-square, B=1024, 14 daytime shortwave calls plus 24 longwave calls, three base channels produce 3*(14+24)*64 = 7296 decode calls. At 1024-square the same logical count is 116736. These are source-derived call counts for that chronology, not native decode time. Profile wrapper and native cost separately. [S12/S17]

P01's full fused path is dormant after measured regressions. It copied flat payloads, did preflight scans and decoded inside a larger kernel. Do not toggle it as an optimization. A prepared/batched decoder is a different, smaller hypothesis.

## A: immutable PreparedVisibility owner

Create a PRIVATE stage-local object containing recognized exact channel types, validated shape/range/dtype, mode descriptors and native payload owners. Acquire locks in stable owner order and preserve close behavior. Scope must not return borrowed mappings past close. Never cache it for arbitrary subclasses/duck types. A lifecycle token is not a substitute for file integrity; immutable generation validation and external mutation policy remain as before.

Prepare once per tile or stage where safe; decode three channels into caller-owned block buffers in one native entry. Preserve the original channel order and patch-major invalid-code order where externally observable. Distinguish independent `diffsh` from the known LazyDiffVisibility with the same leaves; only the latter shares arithmetic. Avoid copying the entire packed payload into a flat array merely to remove Python boxing. Mapped contiguous payload plus offsets can often be borrowed under ownership; in-memory packed leaves may need a measured small descriptor design or retained typed list.

One-time reserved-code validation is valid only if the complete validated payload is immutable over all later reads and the protocol supports that error timing. Otherwise validate bounded blocks in the original order. Prevalidating all data can move the first failure earlier than other baseline operations; retain old public behavior or an explicit slow diagnostic fallback. Do not count dropping validation as speedup.

## B: isolate decoder layout from reducer arithmetic

Keep accepted reducers. Compare a batched native decoder, a small patch-major microtile/transposition, and larger work batching with original arithmetic. Do not change all simultaneously. The current decoder writes C-order [pixel,patch] in patch-major loops; this is a source layout mismatch, not proof of a measured DRAM bottleneck.

Workspace accounting: four decoded float32 channels need 16*B*P bytes before masks/results. At B=4096/P153 that is 9.5625 MiB, at B=16384 38.25 MiB. Multiprocess/native scratch must be counted. A bigger B reduces launches but can evict cache, inflate bandwidth or hurt small inputs. Retain default behavior unless a versioned private dispatch rule is verified; block size is never model tile size.

## C: exact coefficient/tangent preparation

Cache `tan32(asvf)` once for immutable geometry under the fixed profile. One float32 plane is 4 MiB at 1024. ASVF fallback math can depend on NumPy dispatch/layout, so either keep that fallback at its original call shape or admit only the verified SLEEF domain. Do not replace tan/atan with system libm.

`_class_coefficients` reevaluates scalar altitude tangent and conversion constants per patch. Hoist only identical original scalar expressions; retain patch-dependent cosine and scalar-promotion semantics. With cylinder t=0, directional setup may be unused or reusable; coordinate with dossier 03 to avoid double-counting.

Exact ASVF-value interning is a conditional next step: U unique bit values changes expensive classifier evaluations from N*P*T to U*P*T plus N*P*T lookup/scatter. Signed zeros, profile, coefficients and every dependency are in the key. U~N is a reason not to implement. A threshold shortcut needs a certificate for the actual machine function, not real-valued arctangent monotonicity.

## D: separate ordered aniLum kernel

The engine still evaluates full-plane `aniLum += diffsh[:,:,p]*lv[p,2]` in original patch order. A compiled block consumer may remove Python patch extraction and full-plane temporaries while preserving exactly the multiply/add cast points. It need not be fused with Kside to be useful. If later sharing work with shortwave, prove dRad's downstream use and unchanged state/error timing before moving consumers. Keep raw visibility, independent diffsh and all patch support.

## Tests and promotion

All byte patterns through raw mode, 0/1/2 categorical modes, reserved code, partial final blocks, concurrent close, alternate owner combinations, independent dense diffsh, arbitrary public fallback, profile boundaries and multiple actual H. Compare every demanded radiation and chronological state on small TIFFs. Report prep cost, native decode cost, allocations and complete warm/cold small pipeline. Retain a rejected variant and causal note; do not use kernel-only success to undo a pipeline regression.
