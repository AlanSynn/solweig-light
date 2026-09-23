# C6-21 evidence: cylinder longwave primary-output kernel (R-B)

Worktree: /Users/alansynn/Workspace/solweig-light-v6-cyllw, detached at
5e1fab467f7e6038dcf3992cb694008a51ea2c58. No branch checked out, nothing
committed or pushed; only owned paths were written (git status shows exactly
`src/solweig_light/radiation/cylinder_longwave.py`,
`tests/optimization_v6/cylinder_lw/`,
`optimization_v6_continue/evidence/cyl_lw/` as new).

## Verdict

R-B reduction implemented and verified. The compiled `_longwave` family's
cardinal accumulators 10..13 are write-only sinks feeding only output columns
7..10; primary accumulators 0..9 (output columns 0..6) are independent of the
cardinal sweep, including under NaN/Inf payloads and signed zeros. The
private module specializes the kernel under
`CylinderLongwaveDemand.PIPELINE_CYLINDERS_ANISOTROPIC`, reports omitted
diagnostics as `NOT_REQUESTED` (a singleton marker, never zeros), and
delegates to the untouched public full path under `FULL_DIAGNOSTICS`
(default) and under every guard-failure fallback.

## Independence verification

See INDEPENDENCE_VERIFICATION.md (source-line proof at this HEAD; consumer
analysis: engine.py:1650/1666-1667/1671-1675, pipeline.py:267-277,
models.py:10-11/90-94). No counterexample found; the reduction is confined to
the compiled path — the serial reference is never reduced and its full
six-field fallback contract is preserved (tested).

## Artifact hashes (sha256)

- src/solweig_light/radiation/cylinder_longwave.py
  37de63ded1696edb9085bc0f5517be9368abf9bf37a78a121de326f0eda21c74
- tests/optimization_v6/cylinder_lw/conftest.py
  95e346e10392c1f5b526d92d1115d5c1058512ace673a7e6ab2a12c8a7b43fee
- tests/optimization_v6/cylinder_lw/test_cyl_lw_parity.py
  a853ddbacfcf76acc5810a9645d315c3b0889386d27d0558c1feda7573af20c6
- optimization_v6_continue/evidence/cyl_lw/run_L1.py
  0a2bede2eef1b84c1ed41d4f4887ece91bb5a74f1116022e87e442e3cf6a2106

## Commands and exit codes

Python: /Users/alansynn/Workspace/solweig-light/.venv-light/bin/python
(numpy, numba njit cache=True fastmath=False throughout; no fastmath, no new
math profile, no tolerance changes — comparisons are bitwise uint32 views).

1. L1 differential suite:
   `PYTHONPATH=src python -m pytest tests/optimization_v6/cylinder_lw/ -q`
   -> `39 passed, 4 warnings in 3.46s`, exit 0.
   Warnings are pre-existing numpy RuntimeWarnings from the unchanged
   wrapper band-flux loop on degenerate inputs (Ta=1e30 overflow), identical
   in both profiles; a `-W error::RuntimeWarning` run confirms they
   originate there, not in removed arithmetic.

2. L1 evidence runner (structured results):
   `PYTHONPATH=src:tests/optimization_v6/cylinder_lw python
   optimization_v6_continue/evidence/cyl_lw/run_L1.py
   optimization_v6_continue/evidence/cyl_lw/parity_results.json`
   -> `{"all_passed": true, "cases": 32}`, exit 0.
   Full per-case results in parity_results.json.

3. Affected existing family (regression sweep):
   `PYTHONPATH=src python -m pytest tests/differential/test_patch_radiation.py -q`
   -> `634 passed, 1 failed`. The single failure
   (`test_compiled_patch_parallel_diagnostics`) is **pre-existing**: it fails
   identically with the new module physically removed from the tree
   (AttributeError inside numba parfor-diagnostics overloads, unrelated to
   this change; matches the known base-level differential failures).

## Parity coverage (gate items)

- Gate 1 (primary accumulators bitwise per timestep/call vs full kernel on
  real small inputs): kernel-level shapes 16², 37×53, 64², 128² with
  adversarial float32 visibility payloads (binary/ternary/raw codebook
  modes, signed zeros, NaN/±Inf), nonfinite sky tables and Lup spikes —
  columns 0..6 bitwise-equal in parallel and serial variants
  (parity_results.json `kernel`, 8 cases). Wrapper-level: 4 solar schedules
  + gate boundary (azimuth difference exactly 90°) + night (altitude<0),
  block_pixels ∈ {1, 3, 128, 10⁶}, parallel both — Ldown/Lside bitwise,
  cardinals NOT_REQUESTED (`wrapper`, 24 cases). Per-timestep: 6-step
  day-night-day chronology at wrapper level, bitwise each step
  (test_wrapper_per_timestep_chronology).
- Gate 2 (both sweeps + live state retained under FULL_DIAGNOSTICS): both
  ordered sweeps are retained in the reduced kernels by construction; the
  FULL_DIAGNOSTICS profile delegates to the untouched
  `patch_radiation.Lcyl_v2022a` and is bitwise-identical to the direct full
  call (`test_by_demand_dispatch_full_default`); route invariance controls:
  full parallel==serial and primary parallel==serial across all columns
  (`test_kernel_primary_matches_full_route_invariance`).
- Gate 3 (fallback: diagnostic-requested → full kernel path): dispatch tests
  for both demand values plus scope-restore-on-exception; guard-failure
  fallbacks (float64 visibility cube, non-ndarray solar altitude,
  >609 patches) verified in BOTH profiles to return the serial reference's
  full six-field result bitwise — including the preserved original
  TypeError for scalar-altitude inputs — and to restore real arrays (not
  markers) so integrator-side sentinel guards keep original behavior
  (`test_fallback_guard_order_preserved`, `test_seterr_overflow_parity`).
- Fused route (opt-in SOLWEIG_LIGHT_FUSED_RAD=1): reduced fused block
  bitwise-equal to the full fused block on packed adversarial channels and
  on single-pixel / mid-block / full intervals, both parallel and serial
  (`test_fused_primary_columns_bitwise_full`,
  `test_fused_primary_block_schedule`; `fused`, 2 cases).
- Zero-pixel domain (rows=cols=0) keeps the empty contract in both profiles
  (`test_zero_pixel_domain`).

## Timing (contended development tier — recorded, no claim)

Warm kernel-only best-of-5, same process, shared host with other v6 workers;
kernels njit(cache=True), cache warm. full = existing `_longwave*`, primary =
reduced kernel. Numbers are triage-only and not comparable across hosts or
runs (VALIDATION_POLICY development-performance rules).

| shape | parallel | full warm s | primary warm s |
|---|---|---|---|
| 64²   | False | 0.01003 | 0.00577 |
| 64²   | True  | 0.00178 | 0.00120 |
| 128²  | False | 0.03894 | 0.02246 |
| 128²  | True  | 0.00648 | 0.00380 |

Consistent with skipping ~4/14 of accumulator work per patch; a stage-level
gain claim requires uncontended L3 measurement and is out of scope here.

## Integration

INTEGRATION_RECIPE.diff (proposal; engine.py/pipeline.py are integrator
owned): one call-site swap to `Lcyl_v2022a_by_demand` with the existing
runtime block_pixels/parallel, two `+=` guards on the NOT_REQUESTED sentinel,
and the pipeline opt-in via `set_demand`. Default FULL_DIAGNOSTICS keeps
byte-identical behavior for all existing callers; the fallback domain
returns real arrays so the sentinel guards degrade to original behavior.

## Unresolved items / handoff

- L2 whole-pipeline small real TIFF comparison (numerical reviewer) is the
  remaining gate once the integrator wires the recipe; this task's scope was
  L1 kernel/wrapper parity per the completion gate.
- `test_compiled_patch_parallel_diagnostics` pre-existing numba parfor
  diagnostics failure recorded here; not dispositioned by this task.
- The per-process demand holder is deliberately private; if the integrator
  wants scoped restoration in pipeline.py, the recipe notes the
  `demand_scope` alternative (loop reindent).
- One harness note for reviewers: wrapper guard-failure fallback returns the
  serial reference result, which is NOT bitwise-equal to the compiled fast
  path (pre-existing v5 property); all parity in this task is
  reduced-vs-full within the compiled path.
