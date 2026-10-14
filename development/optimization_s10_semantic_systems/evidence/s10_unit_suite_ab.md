# S10 unit/differential suite A/B (T01 patch vs baseline)

Date: 2026-10-13. Method: identical selections run twice on this host — once
with the T01 patch applied (uncommitted working tree) and once with the two
patched source files stashed — then exact failure-ID set difference.

| selection | patched | unpatched | patch-caused failures |
|---|---|---|---|
| `tests/unit` | 10 F / 453 P | 10 F / 453 P | 0 |
| `tests/differential/test_patch_radiation.py` + `test_radiation_reference.py` | 138 F / 547 P | identical ID set | 0 |
| v5–v8 parity (`optimization_v5/radiation`, `v6/{cylinder_lw,decoder,patchclasses}`, `v8/{stream,integration,policy}`) | 509 FAILED/ERROR lines | byte-identical list | 0 |
| `tests/differential/test_pipeline_reference.py` | 1 F / 8 P | identical | 0 |

All failures in both arms are pre-existing on this host and unrelated to the
patch:

- `threads=10` parametrization cells: `numba.set_num_threads(10)` exceeds this
  4-core host limit (`ValueError: between 1 and 4`), raised before any
  campaign code runs. Stash-verified pre-existing.
- `test_original_cpu_radiation_boundaries[*]` (48 cells): collector
  function-list drift vs the frozen fixture (`assert captured == references`
  on function NAMES), fires before arithmetic. Stash-verified pre-existing.
- `test_chronological_tiff_pipeline[raw-True]`: fails identically unpatched.

Key positive gates that PASS with the patch active (not merely "no delta"):
`test_original_longwave_boundaries` threads {0,1,4} × packed {F,T} × 24 steps;
`test_chronological_tiff_pipeline[landcover-False]` and
`[landcover_normalized-False]` — with route counters showing 24/24 daytime
primary admission on the landcover case (see t01_l1_kernel_differential.md).

New S10 tests: `tests/optimization_s10/semantic/test_t01_tgwall_admission.py`
— 14 cases covering U32/U64 (1,)/(1,1) admission within frozen budgets,
S/U route bit-equality, multi-row and size-2 rejection with original error
parity, true-field fallback bit-equality, non-array altitude TypeError order,
`block_pixels` validation position, night U admission, direct dpc U admission,
and reference rank-invariance. All pass.
