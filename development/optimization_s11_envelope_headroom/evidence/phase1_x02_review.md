# X02 independent review — ACCEPT WITH NOTES (2026-10-16)

Reviewer: independent agent (fresh context, adversarial brief), reviewing
commit `9133c693` (X02 twin dispatch in `shadows.shadow`) against the
requirement of bitwise identity with the pre-change behavior. Review ran in
parallel with the E2E job 14094558; reviewer had no hand in the
implementation. Probe artifact preserved at
`solweig-light-s11-raw/phase1/review/probe_twin.py`
(sha256 `18d1c37d13f8d53e118765672dc5f1ba505116be4f37960a7791b3f6832d8c5f`).

## Verdict

No counterexample input could be constructed where the new routing differs
bitwise from `c245ea60` behavior.

## Key structural correction (reviewer's, adopted into the record)

The old wrapper was ALREADY hybrid: `shadow_pixel_serial` =
`_shadow_pixel(parallel=False)` branches internally on `bush.max()>0` —
positive bush → step-major serial; zero/NaN-poisoned max (even with positive
cells present) → pixel-major SERIAL twin. The load-bearing bitwise identity
is therefore `_pixel_parallel == _pixel_serial`, not twin-vs-step-major. The
new wrapper preserves old behavior in all regimes, including the NaN cases
the change's docstring framing glosses over (note (a) below).

## What was checked (reviewer's own probes, independent of Phase 0)

- 49/49 adversarial cases bitwise PASS (uint32 views, NaN-safe) comparing the
  new `shadows.shadow` vs `sky_compiled.shadow_pixel_serial` (the exact old
  behavior): bush zeros / NaN+zeros / NaN+3.0 / all-NaN / f64 / negative /
  bool / uint8 / clean positive; NaN in a/vegdem/vegdem2; negative altitude;
  altitude 90; azimuth boundary sweep; scale variants; amaxvalue
  -1/0/inf/NaN; non-contiguous views; 1x1, 2x2, 0x0 (identical ValueError);
  shape mismatch (identical); bush list (identical). Output hashes invariant
  across NUMBA_NUM_THREADS=1 vs 2.
- Suites at NUMBA_NUM_THREADS=24: 1167/1167 PASS (test_sky_compiled.py +
  test_r01a_absorption_exit.py). The 284 failures under a 4-thread cap occur
  in `numba.set_num_threads` before any kernel runs — pre-existing
  environmental, unrelated (matches the implementer's baseline).
- Diff scope: commit touches shadows.py only; pyproject.toml untouched;
  protocol `product_diff_sha256` matches actual diff bytes.
- Predicate consistency: `np.max(bush)` (wrapper, pre-asarray) and
  `bush.max()` (`_shadow_pixel`) are the same reduction; NaN propagates
  identically → same route in old and new. Only theoretical disagreement
  surface: fully-masked MaskedArray (not a production surface — svf.py
  builds plain float32) — probed anyway, still bitwise-equal.
- Return contract: same tuple arity/dtypes/shapes both routes; bush-dtype
  promotion of vegetation unchanged.
- Callers: sole production importer svf.py:20 (call at svf.py:132);
  `shadow_numpy` alias order correct (line 110 precedes the re-binding def).
- Test pins: no monkeypatch/spy of the dispatch seam anywhere in tests/;
  differential tests bind kernels directly; nothing became vacuous.
- Threading: pool children are subprocesses with per-child NUMBA caps — no
  nested numba parallelism; the Phase-0 sitecustomize probe patched exactly
  the object+arguments the native routing now reaches; for the production
  hot path (bush identically zero from svf.py:101) the twin IS the route.
  For bush>0 scenes the product is MORE conservative than the Phase-0 probe
  (serial, unchanged).

## Notes (none blocking acceptance)

- (a) Docstring `shadows.py:116-117` — "bush > 0 anywhere keeps the
  step-major serial path" is imprecise: NaN-poisoned bush (even with positive
  cells) routes to the pixel path in BOTH old and new; wording, not
  behavior. Fix as a docstring-only follow-up after the E2E completes (do
  not mutate product files mid-run).
- (b) `bush=None` now raises TypeError instead of ValueError — unreachable
  (svf.py validates inputs first); theoretical contract nit.
- (c) Latent (not this commit): `test_sky_compiled.py:62`'s
  `reference.__module__` guard would NOT catch a future reordering that
  aliases `shadow_numpy` to the dispatch wrapper (same module) — the
  differential would go silently vacuous. Filed as test-hygiene debt.
- (d) Range flag: `c245ea60..9133c693` also contains S10-33's `de706808`
  (relaxes a GVF dispatch-route test pin in
  tests/differential/test_ground_view_dispatch_exact.py) — a prior,
  review-attributed S10 commit touching tests only. The E2E product-diff
  assertion (src+pyproject → shadows.py only) is unaffected; the E2E verdict
  must not be read as covering that test change.

## E2E blind spots (recorded, mitigated)

The frozen synthetic scene has bush==0, so the E2E bitwise A/B exercises the
twin route on clean inputs only; the bush>0 route is covered by literal code
identity (same call as before) and NaN-bush routing by the reviewer's probes.
Downstream (run/UTCI) is timed; bitwise coverage is SVF artifacts + TMRT
tile, sufficient because downstream consumes the bitwise-equal SVF outputs
(transitivity).
