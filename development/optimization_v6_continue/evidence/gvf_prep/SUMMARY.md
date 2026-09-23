# C6-30 evidence summary: per-step GVF source-expression preparation

Worker: C6-30 (gvf_specialist). Worktree
`/Users/alansynn/Workspace/solweig-light-v6-gvfprep`, detached at
`5e1fab467f7e6038dcf3992cb694008a51ea2c58` (verified via `git status
--porcelain`: only the two owned paths below are new; no branch
checkout/commit/push). Model routed via GLM (Z.ai).

## Deliverables

| Path | Role |
|---|---|
| `src/solweig_light/radiation/gvf_prepared.py` | NEW private module: `prepare_gvf_step`, `run_prepared_gvf_step`, `prepared_gvf_step`, `PreparedGVFStep`, `prepared_enabled` |
| `tests/optimization_v6/gvf_prepare/` | conftest, shared cases, differential suite, count suite, warning suite |
| `optimization_v6_continue/evidence/gvf_prep/` | this summary + INTEGRATION_RECIPE.md |

engine.py untouched (integrator-owned). Recipe:
[evidence/gvf_prep/INTEGRATION_RECIPE.md](INTEGRATION_RECIPE.md).

## Verdict

SHIP-CANDIDATE. All three completion gates pass on real kernels. 78/78
C6-30 tests and 82/82 v5 GVF regression tests (G02/G03 intact) at
base 5e1fab46.

## Completion gate 1: exactness (bitwise)

`tests/optimization_v6/gvf_prepare/test_gvf_prepare_differential.py` — 40
tests, all bitwise (uint32/uint64 views: catches NaN payloads, signed
zeros, dtype drift), each comparing prepared vs `ground_view._gvf_fused`
(accepted G03 route) and, where applicable, `engine.gvf_2018a_numpy`
(verbatim original body). Tg (caller-visible mutated output) compared after
every call.

- Size/feature grid: 16^2, 33x21, 64^2, 128^2 x water/no-water x
  built/open x serial/parallel — all exact, incl. Tg and all 17 outputs.
- Adversarial: NaN/+-inf/-0.0 in shadow/buildings/alb_grid/Tg; overflowing
  Tg (~1e33 -> inf/NaN masks); degenerate buildings (0/1) and maxwalls;
  search-distance corners (1/1, 5/2, 0.5/6); block_rows {1,3,32,10000};
  float64-SBC Lup (float32 snapshot conversion value-changing, pinned);
  scalar float64 Tgwall broadcast.
- Water pre/post: scatter hoisted to one write at the baseline's position
  (after direction-1 Lup, before Lwall/lup_term states); idempotency
  equivalence vs 18 baseline writes proven bitwise. Negative controls pin
  the mutation is real (Tg changes) and the first/later split is real
  (pre- vs post-mutation Lup differs).
- Alias hazards: 11 gated aliases (buildings, shadow, alb_grid, walls,
  lc_grid, dirwalls, scale, ewall, albedo_b, landcover, Twater) delegate
  to `_gvf_fused` with delegate-spy pinning and oracle parity, including
  Twater alias (progressive per-direction divergence) and lc_grid alias
  (mask movement). 4 position-faithful aliases (Tgwall, emis_grid, first,
  second) stay PREPARED and stay bitwise-exact (spy asserts no delegation).
- No leakage: sequential different-input calls each track the baseline
  (step object never reused; nothing keyed by array identity).
- Fallback: prepared off via `SOLWEIG_LIGHT_GVF_PREPARE=0` -> delegate spy
  proves zero preparation and fused-parity; float64-raster and
  unsupported-step inputs raise identically to base (guard runs before any
  mutation).

## Completion gate 2: measured evaluation reduction (counts, not timing)

`test_gvf_prepare_counts.py` wraps `ground_view._lup_expression` and
`engine._operate` (the exact callables both routes resolve at call time).
Measured at 64^2, water scene (repr in run log):

| Expression | fused | prepared |
|---|---|---|
| `_lup_expression` (water) | 36 (18 gather + 18 lup_term) | **2** (pre- + post-mutation) |
| `_lup_expression` (no water) | 36 | **1** |
| `_operate` total (water) | 3564 | 2745 (-819) |
| `_operate` total (no water) | 3546 | 2733 (-813) |
| Lwall tree | 18 | 1 |
| albshadow | 18 | 1 |
| aspect | 18 | 1 |
| first/second steps | 18 each | 1 each |
| sky-emission tree (post-loop) | 5 | 1 |
| lup/alb/nosh postprocess terms | 18 each | 1 each |
| azilow/azihigh/facesh (direction-dependent) | 18 | 18 (unchanged, by design) |
| `ray_schedule` calls | 18 | 18 (unchanged; direction work kept) |

## Completion gate 3: fallback equivalence

`SOLWEIG_LIGHT_GVF_PREPARE=0` -> bitwise fused parity, delegate spy proves
zero preparation; unsupported inputs -> identical raises via the same
fused route.

## Warning / np.seterr contract (documented + tested)

`test_gvf_prepare_warnings.py`:

- Overflow census with Tg~1e33: exactly 36 RuntimeWarnings (one per
  `_lup_expression` ^4 power) on fused vs exactly 2 on prepared; the
  inf/NaN output masks stay bitwise identical. (Earlier "5 sky warnings"
  expectation corrected during validation: the sky term reads Ta only and
  does not overflow.)
- `np.errstate(over='raise')`: both routes raise `FloatingPointError` on
  the same first evaluation, with Tg left unmutated in both.
- engine.py:1370 boundary: `Lside_veg_v2022a` svfalfaE `log(1 - svfE)`
  divide-by-zero fires exactly once per Lside call (svfE containing a 1.0
  cell) both before and after an intervening gvf preparation — outside
  the hoisted closure, neither absorbed nor duplicated.
- sunwall walls-zero divide warning: once per call on both routes (already
  loop-external in fused); count parity asserted.

## Timing (contended development tier — RECORD ONLY, NO CLAIMS)

256^2 water scene, NUMBA_NUM_THREADS=2, 5 repeats after warmup, shared dev
host under concurrent load: fused min 0.1264 s, prepared min 0.1079 s.

## Commands and exit codes

```
cd /Users/alansynn/Workspace/solweig-light-v6-gvfprep
PYTHONPATH=src NUMBA_NUM_THREADS=2 \
  /Users/alansynn/Workspace/solweig-light/.venv-light/bin/python \
  -m pytest tests/optimization_v6/gvf_prepare/ -q
  -> exit 0, "78 passed, 4 warnings in 3.24s"
PYTHONPATH=src NUMBA_NUM_THREADS=2 \
  /Users/alansynn/Workspace/solweig-light/.venv-light/bin/python \
  -m pytest tests/optimization_v5/gvf/ -q
  -> exit 0, "82 passed in 3.46s"
git status --porcelain   -> only owned untracked paths; exit 0
```

The 4 pytest-captured warnings come from bare `prepare_gvf_step` calls in
the stats/count tests that run without an errstate wrapper: the same
sunwall 0/0 invalid-divide and ^4 overflow warnings the baseline emits at
those points. Not route leaks.

## Unresolved items / notes for integrator

1. `prepared_gvf_step` reads the env toggle per call — negligible cost,
   keeps the kill switch live mid-run.
2. The stronger hoist requires three NEW alias exclusions beyond
   `_gvf_fused`'s (lc_grid, dirwalls, Twater). Integration changes behavior
   only for calls that today hit the fused fast path carrying one of those
   three aliases: such calls previously ran fused with per-direction live
   reads and now delegate to `_gvf_fused` unchanged (same route; delegation
   is the mechanism, not a rewrite).
3. Serial branch (`threads <= 1`) intentionally untouched: the full
   per-direction `gvf_2018a` route remains the serial path; preparation
   targets the fused dispatch only. Extending preparation to the serial
   route is future work (G-A dossier follow-up), not required here.
4. Memory: preparation adds ~2 Lup-sized float32 snapshots + prepared
   rasters per call (transient, freed at return); no persistent growth.
