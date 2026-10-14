# T01 L1 kernel differential: captured-input route comparison (S10)

Date: 2026-10-13. Branch `perf/s10-semantic-systems`, patch uncommitted at capture time.
Question: does admitting the U (singleton-array) Tgwall profile into the compiled
primary preserve the required output contract on real production-class inputs?

## Frozen input capture

First daytime `Lcyl_v2022a` call from a genuine landcover run (scene `a1_lc`,
census build; capture in throwaway clone). Raw artifacts:
`/storage/scratch1/1/dsynn6/solweig-light-s10-raw/probes/`
(`t01_lcyl_inputs_day0.pkl/.json`, `run_t01_differential.py`,
`baseline_outputs.npz/.json`, `t01_outputs.npz/.json`); Dropbox
`Alan Synn/Research/solweig-light/s10/`. Captured profile:

| input | value |
|---|---|
| Tgwall | (1,1) float64 = 12.709898948669434 (U profile) |
| solar_altitude | 0-d float64 = 7.756683441218101 (daytime) |
| sky_patches | (153,3) float32; rows×cols = 32×35 |
| sh/vegsh/vbsh | PackedVisibility (mmap repacked to heap, identical codec bytes) |
| kwargs | block_pixels=128, parallel=None |

## Findings

1. **Reference is rank-invariant.** `_reference('define_patch_characteristics')`
   outputs for Tgwall (1,1) vs scalar are bit-equal on these inputs
   (NEP-50 promotion is rank-independent here). The pre-patch fallback behavior
   is therefore fully described by the scalar run.
2. **Pre-existing compiled-vs-reference divergence.** With Tgwall **scalar**
   (S profile, i.e. code main already ships and runs on no-landcover scenes),
   the compiled primary differs from the engine serial reference:
   `Ldown` 5/1120 cells, `Lside` 6/1120, max abs 3.05e-05–6.10e-05 (1–2 f32
   ulp at ~450 W/m²). Cardinals: fused route 116–226/1120 cells ≤6.1e-05;
   raw block-kernel route also diverges (Lwest 565/1120 ≤3.8e-06). The
   divergence is in compiled block-kernel arithmetic vs the engine's serial
   loop — not the A-plus decode, not the T01 patch (patch adds no arithmetic).
3. **Stream ≡ block** kernel outputs are bit-equal on these inputs.
4. **U extraction is bit-preserving.** The patch's only new code extracts the
   completed `sun_surface` coefficient (post-divide, `[()]` then
   `reshape(-1)[0]`); no arithmetic after extraction, and per (1) the
   reference itself is invariant to the (1,1)-vs-scalar distinction.
5. **Operative acceptance standard.** `development/benchmarks/protocols/
   comparison_v1.json` (frozen pre-optimization; "No relaxation in response to
   candidate or optimization failure") budgets `Lcyl_v2022a/*` and
   `define_patch_characteristics/*` at atol 0.05 W/m², rtol 1e-05; `Tmrt`
   max_abs 0.01 °C; UTCI/WBGT max_abs 0.02 °C. Every closed campaign's
   compiled kernels (v6 C6-21 onward, incl. shipped S-profile primary) were
   accepted against these budgets, not bit-equality vs the serial reference —
   which per (2) the shipped baseline itself does not satisfy on real
   fractional inputs. Measured T01 route-flip delta ≤6.1e-05 W/m² ≈ 10⁻³ of
   budget.

## Gates executed with the patch active

| gate | result |
|---|---|
| `tests/differential/test_patch_radiation.py::test_original_longwave_boundaries`, threads {0,1,4} × packed {F,T} × 24 steps | PASS (vs original-CPU boundary artifacts, protocol budgets) |
| `test_chronological_tiff_pipeline[landcover-False]` (E2E U-profile golden vs original CPU) | PASS |
| `test_chronological_tiff_pipeline[landcover_normalized-False]` | PASS |
| route counters on `landcover` E2E case | `Lcyl_v2022a_primary` 24/24, `define_patch_characteristics_primary` 24/24, reference 0 — flip demonstrably executes |
| A/B `tests/differential/{test_patch_radiation,test_radiation_reference}.py` | failure sets identical patched/unpatched (threads=10 numba-limit + pre-existing collector-drift cells only) |
| A/B v5–v8 parity suites (`cylinder_lw`, `decoder`, `patchclasses`, v8 `stream/integration/policy`, v5 `radiation`) | 509-line failure sets byte-identical patched/unpatched (pre-existing host-environment mass; zero patch-caused) |
| `tests/unit` A/B | see evidence/s10_unit_suite_ab.md |

## Threats to validity

- Fixture coverage: bit-level route equality is NOT claimed — the flip shifts
  LC-scene daytime longwave fields by ≤2 ulp (within frozen budgets). Anyone
  requiring bit-frozen LC outputs must not enable this route; that would also
  condemn the shipped S-profile primary.
- `threads=10` parametrization cells fail on this 4-core host (numba
  `set_num_threads` limit) — pre-existing, stash-verified, environmental.
- The captured input is one daytime step of one 32×35 scene; L2 paired E2E
  benchmarking on protected cells covers breadth, this file covers mechanism.
