# REVIEW_C5-31 — P01 fused ordered decode+accumulate (radiation)

- **Reviewer**: C5-31, independent GLM review (Opus unavailable). Reviewer is not the author.
- **Patch**: a343fe20 (impl) + 1343b84f (tests) + 068f9156 (diagnostic) → `068f9156` on `perf/claude-glm53-cpu-v5-rad`, worktree `/Users/alansynn/Workspace/solweig-light-v5-rad` (read-only; probes in `/tmp/c531`).
- **Base**: `bfd9915e`.

## Verdict

**APPROVE for integration**, with one latent admission gap to fix or document (Finding 1, MEDIUM — not reachable from the shipped pipeline). Numerical exactness is verified by code inspection (mechanical normalized-token diff of all four fused kernels against their base counterparts) and by 93 passing bitwise differential tests. The fused route demonstrably activates in the real pipeline shape (probe E: 136/136 blocks fused, 0 fallbacks).

## 1. Scope check — PASS

`git diff bfd9915e..068f9156 --stat`: exactly 5 files —
`src/solweig_light/geometry/visibility_compiled.py` (+29), `src/solweig_light/radiation/patch_radiation.py` (+419/-6), `tests/optimization_v5/radiation/{conftest,test_p01_fused_blocks}.py` (new), `optimization_v5_claude/diagnostics/p01_rad_diag.py` (new).
`engine.py`, `_classes`/pipeline/ground_view untouched. The only 6 removed lines in patch_radiation.py are the two retained-route decode bodies, re-added **verbatim** under `if reduced is None:` (patch_radiation.py:569-574, 912-915). Old kernels `_shortwave`/`_shortwave_serial`/`_longwave`/`_longwave_serial`, `_block`, `_shortwave_visibility_blocks`, `_classes`, `_descriptor`, `decode_block` are byte-identical to base.

## 2. Numeric exactness — PASS

**Decode bit patterns.** `_decode_slice` (visibility_compiled.py:54-67) reproduces base `_decode` (bfd9915e:17-35) exactly: mode 4 assembles little-endian uint32 from 4 bytes (bitcast, not numeric cast — matches encoder `bits.astype('<u4').tobytes()` at visibility.py:214 and `decode_pixels`' `view(np.float32)`); codebook 0→0x00000000, 1→0x3f800000, 2→0x40000000. Packing verified against the encoder (visibility.py:219-226): binary = 1 bit/value (packbits little → `pixel//8`, shift `(pixel%8)*1`), ternary = 2 bits/value low-first (`pixel//4`, shift `(pixel%4)*2`). Identical formulas in `_decode`, `_preflight`, `_decode_slice`. `_decode_slice` does **not** raise on code==3 (it would decode 2.0) — acceptable only because preflight coverage is total; it is (Finding 4).

**Accumulation order.** I extracted all 8 kernel bodies and diffed normalized token streams (pixel/lane refs and accumulator names unified; allocations/loop headers/copy-back dropped). Results:
- SW (parallel and serial): fused = base + exactly (a) the lazy-diff application, (b) tile0/lanes setup, (c) `out[tile0+lane,column]=acc[lane,column]` copy-back. Every arithmetic expression is token-identical, including `building=np.float32(np.float32(1)-sh)*vb==1`, the `contribution` grouping `((diff*lum)*cosine)*solid`, both `box` branches, and all four directional gates. Per output element the additions run in patch order 0..152 from a +0.0 init, identical to base.
- Lazy `_diff` fused (patch_radiation.py:378-383, 451-456) is token-identical to base `_diff` (visibility_compiled.py:40-46): `difference=1-veg; product=difference*float32(1-.03); d=d-product`, each float32-wrapped.
- LW (parallel and serial): zero arithmetic differences — only renames (`accum`→`acc[lane]`, `out[pixel]`→`out[tile0+lane]`, `lup[pixel]`→`lup[tile0+lane]`, `sun[tile0+lane,patch]`). The `(accum[0]+lup)*reflection_factor*0.5/pi` reflected term and the output column mapping (`out0=(acc0+acc1)+acc2)+acc3)+acc4` left-assoc, `out1=(acc5+acc6)+acc7)+acc8)+acc9`, `out[2:7]=acc[5:10]`, `out[7]=acc[10]`, `out[8]=acc[12]`, `out[9]=acc[13]`, `out[10]=acc[11]`) are verbatim.
- Two-sweep order preserved per lane: sky sweep over all patches, then `reflected` computed from completed `acc[lane,0]+lup[tile0+lane]`, then reflected sweep re-decoding sh/vs/vb (same three pairs, same order) exactly as base re-reads the decoded block. `no fastmath` on all new kernels; `cache=True` consistent with base.
- Microtile: `prange` over tile indices only (patch_radiation.py:369); `acc(lanes,20)`/`acc(lanes,14)` allocated inside the loop → private per iteration; no cross-lane reduction anywhere; `lanes=min(tile,rows-tile0)` sizes all buffers so no masking is needed and every `out` row 0..rows-1 is written (verified at rows ≡ 1 mod 32, Probe C).

## 3. Exception contract — PASS (one LOW edge note)

`_preflight` (visibility_compiled.py:39-50) walks base `_decode`'s exact patch-major/pixel-inner order and raises the identical `IndexError('Reserved visibility code')`; mode 4 skipped in both (base never checks raw). Entry order sh→vs→vb→dsh→(dveg) matches the retained route's observable read order (`_shortwave_visibility_blocks`; LW `_block` generator materializes sh,vs,vb). When the diffuse LazyDiff aliases shmat/vegshmat (the pipeline case), dsh/dveg preflight is redundant-but-harmless (same channels, already checked). Probe B: reserved code in the LAST block only raises in both routes with identical message; multi-channel reserved codes raise per channel precedence with identical observable (type+message; neither route exposes the offending pixel).

**Partial commits**: base raises inside `_decode` before that block's result is returned; prior blocks' `output[:,start:stop]` slices are already written by the untouched caller loop. Fused raises in preflight before the kernel launches — same observable. The test (test_p01_fused_blocks.py:243-289) asserts type+message on the offending block (fused parallel + serial + old route + `decode_block`) and asserts prior-block output stability via `early` vs `early_again` bitwise recompute. Nuance (INFO): this is a reproducibility proxy, not a literal partial-write run of the caller loop; parity holds structurally because the caller loop is untouched.

**LOW edge**: `_fused_guard` range-checks ALL leaves up front (patch_radiation.py:157-160) while base checks per-channel at decode time. With cross-channel shape mismatch AND a reserved code in an earlier channel, fused raises `Visibility block interval out of range` where base raises `Reserved visibility code`. Unreachable in the pipeline (all channels share one shape by construction: import_visibility_npz enforces matching shapes; GeometryStore enforces patch-count equality). Same-armed tests `test_range_validation_parity` pass.

## 4. Locks — PASS

`_fused_guard` (patch_radiation.py:149-163) replicates `decode_block`'s discipline: owners deduped via `{id(leaf): leaf}` then `sorted(..., key=id)` (identical expression), `_check_open()` immediately after each acquire, exact range-check message, held across descriptor build + preflight + kernel (the `return kernel(...)` is inside the `with`). The pipeline's `diffsh = LazyDiffVisibility(shmat, vegshmat)` (pipeline.py:197) shares leaf objects with channels 0/1, so the id-set dedupes 5 leaves to 3 owners — no double-acquire. No early release; `MappedVisibility.close()` takes the same lock, so an owner cannot be closed (or its mapping invalidated) between `_check_open` and kernel completion; descriptor payload views are only read under the lock, and close() clears the cached `_block_descriptor`. Deadlock-free: every acquirer in the codebase (`decode_block`, `diff_from_shared_decoded`, `_fused_guard`, per-call `decode_pixels/patch`) uses the same id-sorted order or a single lock. Difference from base is a superset window (up to 3 unique owners held at once vs base's ≤2 per channel call) — serializes closers longer, no correctness impact. `test_mapped_visibility_fused_route` covers mapped bits and the post-close `RuntimeError('Native visibility is closed')` on both routes.

## 5. Admission guard and ACTIVATION — PASS (latent gap, Finding 1)

Admission (`_packed_leaves`, patch_radiation.py:133-146) is `type(leaf) is PackedVisibility or isinstance(leaf, MappedVisibility)`; `SubsetPackedVisibility` subclass is rejected (test line 325-330), duck channels fall to `_block`'s `decode_pixels` route (bitwise-verified). SW admits LazyDiff for the diffuse channel only **by intent**; LW requires `len(pair)==1` for all three channels (line 198), i.e. all direct. Fallback routes are the untouched original code (verified by diff).

**ACTIVATION ANSWER: the fused path WILL run in the real dense_urban_256 pipeline (both SW and LW).** Evidence:
- Channel types: all three pipeline geometry paths produce admitted types — `svf_calculator` is aliased to `svf_calculator_compact` at pipeline.py:22 (`VisibilityBuilder.finish()` → exact `PackedVisibility`); `GeometryStore._open` → `open_native_visibility` → `MappedVisibility` (cache/geometry.py:213); legacy-trust `load_legacy_geometry` → `import_visibility_npz` → exact `PackedVisibility`.
- Dispatch: engine.py:1745-1766 forwards channels unchanged and selects `parallel = threads_per_worker > 1`; fused runs either way (parallel or serial fused kernel).
- Probe E (corrected counter, counting non-None returns): Kside with packed channels + LazyDiff diffuse → **136/136 blocks fused, 0 fallbacks**; LW `define_patch_characteristics` packed → **136/136 fused**; dense-ndarray channels → 0/136 fused, 136 fallbacks (admission rejects). 48x48, block_pixels=17.
- Probe E2: one Mapped channel in LW still takes the fused route.
- Remaining admission conditions at the entry (`_supported` float32 dtypes, scalar ndims, `anisotropic_diffuse==1`, ≤609 patches) are satisfied by the compiled profile's dense_urban_256 inputs (153 patches).

## 6. Test honesty — PASS

Old-route bodies byte-identical (diff shows only the 6 moved lines re-added verbatim). All comparisons are uint32-view bitwise (conftest.py `bitwise`, `assert_fields_bitwise`). 153 patches exercised throughout, including 51/51/51 binary/ternary/raw in one channel (`test_all_153_patches_in_mixed_modes`), 128x128 whole-scene single-block, 37x53 irregular tails at block 17/128, block_pixels=1, signed-zero/NaN/Inf payloads and nonfinite coefficients, `-0.0`/NaN Lup. Reserved-code tests assert type+message on fused (parallel and serial), old route, and `decode_block`. End-to-end packed-vs-dense Kside/Lcyl/define differentials pass in both thread modes. The diagnostic script is explicitly labeled "DIAGNOSTIC ONLY (not a benchmark claim)".

## 7. Runs (threads ≤ 2, in the rad worktree)

| Suite | Result | Expected |
|---|---|---|
| `pytest tests/optimization_v5/radiation -q` | **93 passed, 20 skipped** in 134.55s | 93/20 ✓ |
| `pytest tests/unit/test_duplicate_visibility_decode.py tests/unit/test_patch_classification.py -q` | **65 passed** in 2.19s | 65 ✓ |

Known flake `tests/differential::test_compiled_patch_parallel_diagnostics` not exercised (not in these suites); per instructions it is pre-existing at base and not counted.

## 8. Adversarial probes (/tmp/c531, results)

- **A (own probe) — LazyDiff as SW channel 0**: `_packed_leaves(LazyDiff)` admits it; fused produces **1017 differing entries** vs the retained route (which applies `_diff` via `decode_block`). Confirmed Finding 1. Not pipeline-reachable (only `diffsh` is LazyDiff and it is only ever the diffuse argument; pipeline.py:197, engine.py:1604/1320 argument order).
- **B — reserved code in LAST block only / multi-channel**: both routes raise identical `IndexError('Reserved visibility code')`; channel precedence sh→vs matches.
- **C — pixel count not multiple of 32**: 65x65 (last tile = 1 lane) SW fused bitwise-equal to base. Test suite additionally covers 37x53 tails and block 1/17/32/128/4096.
- **D — Lup layout**: C-order, F-ordered, and strided-view Lup (through `Lup.reshape(-1)[start:stop]`) all packed==dense bitwise; `reshape(-1)` guarantees a contiguous 1-D operand and numba accepts either.
- **E/E2 — activation**: see section 5.

## Findings (severity-tagged)

1. **MEDIUM (latent, not pipeline-reachable)** — `_packed_leaves` (patch_radiation.py:133-146) admits a `LazyDiffVisibility` for **any** channel, but the fused kernels apply `_diff` only to the diffuse stream (`diff_is_lazy`, lines 378-383/451-456). A LazyDiff passed as SW `shmat`/`vegshmat`/`vbshvegshmat` silently yields undiffused values where the retained route (`decode_block` → `_decode_diff`) applies the vegetation diff. Probe A: 1017 differing entries. Fix: for non-diffuse channels require the direct packed check (reject `LazyDiffVisibility`), matching LW's `len(pair)!=1` rejection; or apply `_diff` per lazy channel. No current caller can trigger it; fix before any external use of the module-level entry points.
2. **LOW** — `_fused_guard` front-loads the range check for all leaves; error-message precedence differs from base only when channel shapes mismatch AND an earlier channel holds a reserved code (section 3). Impossible from the pipeline's same-shape invariant.
3. **INFO** — prior-block commit test is a reproducibility proxy (`early` vs `early_again` bitwise), not a literal caller-loop partial-write assertion; parity holds because the caller loop is untouched (section 3).
4. **INFO** — `_decode_slice` maps code 3 → 2.0 silently; safe strictly because preflight covers every decoded pixel of every admitted block. Keep the invariant that no kernel path may bypass `_preflight`.
5. **INFO** — `_FUSED_TILE=32` is fixed; `prange` tile count and private per-tile allocations verified correct for all tails tested.

## Probes/artifacts

Probe scripts: `/tmp/c531/probe1.py`, `/tmp/c531/probe2.py`, `/tmp/c531/probe3.py`, normalized-kernel diff `/tmp/c531/normdiff.py`. No writes to the rad worktree.
