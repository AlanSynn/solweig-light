# Residual-round independent review — reviewer notes (S10-25)

Reviewer: independent (not an author). Head reviewed: `91e37d53`, base `321edb94`.
Machine-readable outputs: `residual_reviews.json`, `product_scope_review.json` (same directory).

## Verdicts

| Task | Verdict |
| --- | --- |
| S10-22 (selection) | approved |
| S10-23 (Lside exact dispatch twin) | approved_with_notes |
| S10-24 (optional heterogeneous region) | approved (no implementation; not-eligible disposition consistent with PLAN.md and the DAG's own "unavailable/rejected" completion condition) |

No blockers. Two minor findings (R1, R2) on S10-23, both unreachable from any
caller in this repository, both leaving values bitwise-exact, both with one-line
closures. The integrator closes findings; details and evidence in the JSONs.

## What was independently re-derived

- **Exactness by reading**: the retained body's four `anisotropic_longwave==1`
  branches return exactly `_operate(np.multiply, LupX, 0.5)` in
  `(E, S, W, N)` order; no other term reaches the returned fields; neither
  implementation mutates inputs or aliases them in the outputs.
- **Exactness by execution**: 20+ adversarial in-domain cases beyond the shipped
  21 tests — extreme in-domain bounds (day and night), strided views, read-only
  arrays, mixed f32/f64, NaN Lup (admitted), NaN svf / empty arrays (declined),
  four admitted `aniso` forms, leaked regime with `svf==1`, promoted-warning
  fallback — all bitwise with the 4-tuple contract intact.
- **Warning regimes**: the shipped C6-20 fast path already swallows everything
  the twin swallows under the default regime (precedent confirmed by probe);
  for f32/f64 the domain bounds provably (static analysis + bounds probe)
  exclude every over/invalid emitter of the removed chains.
- **Route split**: fresh-process e2e re-run reproduced 24 = 7 upstream fast +
  17 twin primary, reference 0; in-process span harness re-run reproduced
  B ≈ 0.0337–0.0346 s / 24 calls vs A = 0.0 span / 0 body calls.
- **Provenance**: all 8 recorded sha256s match; Dropbox listing (read-only)
  confirms the tarball + sidecar under `s10/`; `residual_costs.json` correction
  verified purely additive by diff.
- **Pre-existing failure**: `test_kernel_primary_matches_full_route_invariance`
  re-proven failing at base `321edb94` in a throwaway worktree — see the
  methodology caveat below. Failure cause at HEAD matches the record
  (AssertionError column 7, NaN payload comparison).

## Methodology caveat worth keeping (worktree runs)

The venv's editable install resolves `solweig_light` to the **main checkout's**
`src/`. A pytest run inside a throwaway worktree therefore tests the worktree's
*tests* against the *main checkout's product code* unless `PYTHONPATH` points at
the worktree's `src`. The reviewer's first worktree attempt made exactly this
mistake, was discarded as invalid, and repeated with the override
(`solweig_light.__file__` verified inside the worktree before running). The same
caveat applies to the recorded 706-failure differential worktree proof: the
claim was not re-run here (out of scope) and its proof procedure is not
auditable from the record, but every spot gate passes and the one failure the
record names is real, pre-existing, and cause-matched.

## Findings summary

- **R1 (minor, S10-23)** — `divide`/`invalid` `'call'/'print'/'log'` regimes are
  admitted (only `'raise'` excluded) but not replicated; the body's redirected
  FP-error handling is swallowed (probe: seterrcall hook fires for the body,
  never for the twin). Pre-S10-23 the C6-20 guard declined those regimes, so
  this is a user-observable regression in an exotic, repo-unreachable regime.
  Closure: restrict to `{'warn','ignore'}` or fix the claim text.
- **R2 (minor, S10-23)** — non-f32/f64 dtypes (float16 probed) pass the domain
  bounds; the removed float16 chains over/invalid-warn under `over='warn'` and
  the twin swallows them. **Pre-existing** via the shipped C6-20 guard (probed:
  same case admitted there with 0 warnings), so not a regression — but the
  record's "values AND warnings on the whole admitted domain" wording is
  overbroad. Closure: dtype-gate or correct the wording.
- **R3/R4/R5/R6/R7 (notes)** — stale FULL_DIAGNOSTICS contract text in
  `pipeline_demand.py` (behavior is pinned correct by tests); `s10/residual/`
  vs `s10/` Dropbox path slip in REGISTER.md + the task md; bind-time TypeError
  origin on malformed calls; S10-24 DAG status field still `not_started`;
  S10-22 verification-plan wording superseded (met or exceeded everywhere).
