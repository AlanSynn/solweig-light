# S10 R03: ordered packed-stream aniLum accumulation

Date: 2026-10-14. Branch `perf/s10-semantic-systems`, commit `1a3cb8e2` on top
of the post-G02 census (`c75f0174`).

## Mechanism

The daytime anisotropic branch (`engine.Solweig_2022a_calc`) accumulated
`aniLum` with one Python plane decode per Perez patch — the post-G02 census
measured `LazyDiffVisibility.__getitem__` at 2142 calls / 85.3 ms per tile
run (14 daytime steps × 153 patches) = **11.1% of calc**, the largest single
remaining item. R03 adds `patch_radiation.anilum_packed`: the admitted lazy
diffuse leaves (the same two admitted packed implementations as the fused
kernels) are decoded inside a small njit kernel via the aplus decoder
(`_decode_at`) with the per-pixel ascending patch accumulation kept in
float32:

    d_v = decode(shadow, patch, pixel)
    t_v = decode(vegetation, patch, pixel)
    d_v = d_v - float32((float32(1) - t_v) * float32(1 - .03))
    acc = float32(acc + float32(d_v * lum[patch]))

— the exact `LazyDiffVisibility.__getitem__` arithmetic and the baseline's
in-place `+=` order, so admitted scenes are **bitwise**. Descriptors,
preflight machinery and mmap lock discipline are the proven fused-route
helpers (`_fused_descriptor`, `_fused_guard`). parallel/serial kernel pair
follows the N8 house pattern (prange over pixels preserves per-pixel patch
order).

Declines to the verbatim retained loop (exact fallback): non-lazy or
non-admitted leaves, weight profiles that would leave float32 (f64/int lv or
missing column 2), shape mismatch, any ternary patch (reserved-code contract
stays with the Python indexer's original IndexError), and
`SOLWEIG_LIGHT_ANILUM_PACKED=0`.

## Proof

- Unit tests (`tests/optimization_s10/semantic/test_r03_anilum_packed.py`,
  8 cases, all pass): kernel ≡ retained loop on uint32 views (binary/raw mix
  with NaN/-0/Inf payloads); parallel ≡ serial; MappedVisibility leaves
  bitwise; ternary decline preserves the original IndexError; weight-profile
  and shape decline matrix; kill switch; **E2E engagement — one landcover
  golden tile routes 14/14 daytime aniLum sums through the packed stream**
  (guards against the census trap of routes that never fire).
- `tests/differential/test_pipeline_reference.py -k landcover`: 2/2 pass.
- `tests/optimization_s10/semantic`: 36/36 pass.
- `tests/unit`: 10F/453P — the same pre-existing set recorded on the G01+G02
  A/B (p7 harness ×9, portable_profile ×1).

## L2 paired benchmark (protected cell #1, landcover, H=1, 24 steps)

Host load 12.8–15.1 throughout (shared login node; paired alternation per
the campaign noise policy).

1. Cross-tree paired (A = `c75f0174`, B = `1a3cb8e2`; 5 pairs × 2 sets,
   fresh subprocess per side, median of 3): set 1 geomean **1.047** (all
   pairs ≥ 1.0), set 2 geomean **1.035** (8/10 pairs ≥ 1.0). Raw:
   `paired_ab_r03.jsonl`, `paired_ab_r03_run2.jsonl`.
2. Within-process toggle (same tree, same JIT, `SOLWEIG_LIGHT_ANILUM_PACKED`
   alternated per run_tile call, 8 alternating pairs): per-pair median ratio
   **1.073**, 7/8 wins, geomean 1.082 (one 1.48 s contention outlier on both
   arms). Raw: `wip_ab_r03_out.json`.

Conservative claim: **≈1.05× tile on this cell** (cross-tree paired-median
geomean), with the within-process toggle supporting ≈1.07. Cumulative vs
main on this cell: 3.26 s → ≈1.09 s ≈ **3.0×**.

## Threats to validity

- One golden scene/tile; the effect scales with daytime-step count × Perez
  patch count, not pixel count (kernel is O(N·P) either way), so scene
  shapes with more patches benefit more; scenes without the anisotropic
  branch are untouched.
- Host noise ±5% per observation; conclusions rest on paired alternation
  and two independent methods agreeing in sign and magnitude.
