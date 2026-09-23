# N8-30 review of N8-11 — direct AoSoA producer

**Verdict: APPROVE-WITH-NOTES.** No blocking defects, no required repairs.
Machine-readable twin: `n8_30_review_n8_11_layout.json` (same directory).

Reviewer: independent N8-30 review service; did not author N8-11.
Scope guard: nothing outside `optimization_v8_native_default/evidence/reviews/`
was written; reference oracle/grid imported read-only; no network; no commits;
no timed benchmarking. Repo at `16cdc56c`
(`perf/native-optimization`, worktree `/Users/alansynn/Workspace/solweig-v8-native`).

Rerun (this review): `tests/optimization_v8/layout` + `tests/optimization_v8/reference`
→ **893 passed, 0 failed** (781 layout + 112 reference, 3.21 s) — matches the
author's claim exactly.

## 1. Bit-exactness — PASS

Every payload comparison is exact integer equality on the uint32 bits, never a
float tolerance: `test_producer_layout.py:105-109/121/131` compare the producer
output against `_decode(...).view(np.uint32)` via `np.array_equal`;
`test_consumer_parity.py:118-119` compare
`lw_primary_aosoa_serial(...).view(np.uint32)` against BOTH the independent
NumPy oracle and the frozen `_longwave_primary_serial`, all seven columns.
grep for `allclose|approx|isclose|assert_equal` over the layout tests: zero hits.

Grid actually covered: B ∈ {0,1,3,4,5,7,8,9,11,13,16,97,128}
(`test_producer_layout.py:82,112-121`), P ∈ {1,2,3,153} spans plus the 609
boundary (`test:83,124-132`) and {7,153,609} for classification; raw-mode bit
pool includes signed zeros, min/max subnormals, ±Inf, two NaN payloads, the
near-one pair, pi bits and 0x4B7FFFFF (`test:38-40`); the consumer pool adds
2^24, 2^±24..-25, 1±2^-23/2^-24, max-float, min-normal; sub-block spans
(5,None),(0,7),(3,130); non-unit-stride asvf field. Both widths {8,4} and both
orders parametrized throughout. Residual grid minors are note N4 (P=5/11,
B=11 at consumer level, sky-column strides — none can hide a layout defect).

## 2. Error order — PASS

(a) `_produce_patchmajor` (`direct_aosoa.py:102-132`) iterates patch → gang →
lane with `pixel = start+gang*W+lane` ascending, then a bounded tail pass —
within each patch the pixel visit order is exactly `_decode`'s row order
(`visibility_compiled.py:20-34`), and the code-extraction/byte-assembly
expressions are character-identical. The first reserved-code `IndexError`
therefore fires at the same (patch,pixel) by construction, with no preflight.
(b) `test_reserved_code_raised_for_every_position`
(`test_producer_layout.py:198-214`) sweeps **every** (patch ∈ 4, pixel ∈ 13)
single-injection position, asserting raise-parity with `decode_block` on the
same channel; `test:217-228` proves the blocked order validates pre-launch
(out stays fully POISON). (c) `_preflight_packed` (`direct_aosoa.py:135-152`)
is `_preflight_flat`'s exact order (patch-major, mode-4 skipped, row
ascending) over the zero-copy per-patch views, charged inside the blocked arm
before `_produce_blocked` (`direct_aosoa.py:227-229`). Positional
assertability caveat recorded as note N3.

## 3. Admission / locks — PASS

`_admitted_leaf` (`direct_aosoa.py:83-85`) is verbatim `_packed_leaves`'
`admitted()` (`patch_radiation.py:172-177`), with `LazyDiffVisibility`
additionally declined at both entries. `_leased`
(`direct_aosoa.py:206-220`) reproduces `decode_block`/`_fused_guard`
guard-for-guard and in order: id-sorted deduplicated owners,
enter-then-`_check_open` per owner, then the per-leaf range contract with the
identical message `'Visibility block interval out of range'`; stack closed on
any raise. Range-message parity asserted for all three entries
(`test:268-277`); closed-owner RuntimeError parity (`test:303-319`);
duck/subclass/lazy/dense declines (`test:254-265`). The poison tests genuinely
poison: producer `out` pre-filled 0xDEADBEEF with padding asserted unchanged
(`test:157-169`), exact-size payload no-out-of-interval-read case
(`test:172-177`), classification masks pre-filled True (`test_classification_
aosoa.py:76-88`), and consumer-side post-production poison of lanes 13:15 with
an all-finite-outputs assertion (`test_consumer_parity.py:155-184`). Lease
observability: instrumented lock (`test:389-397`), shared-owner dedup
(`test:400-409`), close-serialization under a held lease (`test:412-430`),
payload digests unchanged (`test:437-450`), output outlives owner close
(`test:453-460`). Admission strictness vs `decode_block` is note N2.

## 4. No hidden copy — PASS

The charged path calls only `_descriptor` (per-patch readonly `frombuffer`
views + mode bytes, cached per channel; `visibility_compiled.py:90-102`);
output materialization is one per-block `np.empty [G,P,W]`
(`direct_aosoa.py:248,264`). grep over `direct_aosoa.py`: `_fused_descriptor`
appears only in docstrings (never called); `np.ascontiguousarray` only on the
rows-sized `tan32(field)` temporary (`:344`, byte-identical to the retained
route's `patch_radiation.py:335`); `.copy()` only inside `pack_masks_aosoa`
(`:371`) — the measured **alternative** adapter. The flat copy is timed once
per mix under `flat_copy_build_s_informational` and never charged
(`measure_direct_aosoa.py:160,172-180`). The results JSON's embedded
correctness checks report `bitwise_equal_decode: True` for both orders and the
adapter at both widths, and `bitwise_equal_classes: True`.

## 5. Classification — PASS

`classify_block_aosoa` (`direct_aosoa.py:315-352`) mirrors `_classes`
(`patch_radiation.py:317-357`) structurally — same field slice, prepared
delegation, heights/factor construction, contiguous-vs-masked dispatch — and
reuses `_class_coefficients` **by import** (`direct_aosoa.py:78`), so the
R04+G06 tables are the same objects/values, not a reimplementation.
`_classes_table_aosoa`/`_classes_table_masked_aosoa` are elementwise identical
to `_classes_table`/`_classes_table_masked` (float32 add, the same SLEEF
`atan_fma` core that `atan32 → atan_array` loops over —
`_math_profile.py:87-92`, `_sleef_classifier.py:141-146` — float32 degree
multiply, strict `<`/`>`). Tests assert bitwise mask equality against retained
`_classes` in **both** dispatch regimes (`SOLWEIG_LIGHT_PATCH_CLASS_TABLES`
0 and 1, `test_classification_aosoa.py:52-73`); prepared-reuse parity
(`test:110-120`); NaN/±Inf rows pin actual both-false cells with
shade ≠ ~sun (`test:91-107`); float64 decline (`test:123-126`); pack-helper
identity and False tail padding (`test:143-157`).

## 6. RN32 safety — PASS

The producer kernels (`direct_aosoa.py:88-203`) contain no float conversion of
any visibility payload: codebook codes write the uint32 literals
0/0x3f800000/0x40000000; raw mode assembles little-endian bytes into uint32
exactly as `_decode` does; visibility is never bool-cast. All `np.float32`
occurrences are confined to the classification kernels (asvf-field arithmetic
identical to the retained tables) and to `lw_primary_aosoa_serial`, the
explicitly-labelled TEST/proof consumer operating on float32 **views** of
already-produced blocks, reproducing the frozen kernel's own arithmetic
(`cylinder_longwave.py:137-178` — verified line-by-line).

## 7. Measurement honesty — PASS (with note N1)

Logical-bytes accounting justified; the tracemalloc caveat is disclosed twice
(script docstring + JSON provenance note, with the correct direction: measured
peaks would favor the producer). min-of-N with median co-reported, warmup 3,
gc disabled during sampling. Flat-copy and descriptor first-build labelled
informational; no protocol-cell claims (N8-31 scope untouched). Provenance
records head/branch/platform/python/numpy/threads/timestamp. Every headline
number reproduces exactly from the JSON (0.782/0.816, 0.985/1.052, 0.075/0.170,
612/1224 KiB, 0.394/0.611 ms, 0.228–0.274 ms descriptor build), and all 12
block + 4 classification cells are present, including the unfavorable ones.

## 8. Ownership — PASS

`git status` shows zero tracked-file modifications. N8-11 artifacts are
confined to `experiments/optimization_v8/layout/` (+ its results JSON) and
`tests/optimization_v8/layout/`; no `src/` writes; no aosoa references
anywhere else; sibling `loader`/`packaging`/`reference` dirs belong to other
packets.

## Notes (N1–N6, none blocking)

* **N1 — the every-mix win is B=1024-only.** At B=128 the comparison reverses
  in 3 of 6 cells (W=8 mix 0.067 vs 0.037 ms; W=4 mix 0.068 vs 0.057; W=4
  all-binary 0.111 vs 0.102). N8-04 names block_pixels=128 as the production
  block size, so the direct producer's advantage is a full-tile result. All
  cells are disclosed in the JSON and the claim's parenthetical pins B=1024 —
  but the headline sentence must not be read at the 128-pixel block regime,
  and default-path selection remains N8-31's protocol cells.
* **N2 — admission stricter than `decode_block`** (= `_packed_leaves`
  exactly): PackedVisibility subclasses that `decode_block` would decode are
  declined to legacy; `LazyDiffVisibility` always declined here. Conservative,
  safe, sanctioned convention.
* **N3 — "same first-offending (patch,pixel)" is construction-proven**, not
  message-provable (the IndexError carries no position). Exhaustive
  single-injection raise-parity + verified loop order is the strongest
  available test; multi-code injection is observably indistinguishable.
* **N4 — grid minors**: P ∈ {5,11} in no N8-11 suite (in the N8-04 reference
  grid); B=11 layout-level only; consumer sky columns contiguous-only (the
  frozen kernel's own stride coverage lives in the reference suite, and this
  consumer does not modify that path).
* **N5 — error-path write asymmetry**: patchmajor may leave partial output in
  a caller-supplied `out` before the reserved-code raise (same observable
  class as `_decode`'s partial fill); blocked guarantees untouched `out` via
  preflight. Callers must discard on exception either way.
* **N6 — float32-view convention**: the proof consumer's parity is conditioned
  on being fed `.view(np.float32)` blocks; raw uint32 blocks would change
  numba promotion and could diverge. Wave-2 consumers (N8-12/N8-13) must bind
  this convention.
