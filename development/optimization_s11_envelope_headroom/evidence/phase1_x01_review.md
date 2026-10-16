# X01 independent review — ACCEPT WITH NOTES (2026-10-16)

Reviewer: independent agent (fresh context, adversarial brief), reviewing
commit `987fbd82` (concurrent export stage) while E2E job 14096139 ran.
Reviewer had no hand in the implementation. Probe artifacts were under
`/tmp/s11x01-review/` (ephemeral; findings restated here in full).

## Verdict

All nine checklist items CONFIRMED (serial fallback byte-identical,
cross-tile state safe, failure semantics as implemented, pickling, spawn
safety, per-child admission, no pinned-prefix test broken, tests pass
33/33, scope clean). Three findings, none blocking; dispositions below.

## Findings and dispositions

- **N1 (medium, caller-facing; demonstrated by reviewer)**: mp.spawn pools
  re-import the parent's `__main__` in every child. A user script calling
  `calculate_svf` at module top level WITHOUT an `if __name__ == '__main__':`
  guard, with workers>1 and >1 pending tile, worked before X01 (serial loop
  makes no processes; the barrier dispatches `python -m` subprocesses) and
  now dies in `spawn._fixup_main_from_path` / BrokenProcessPool. In-product
  paths are safe (console script, cli guard, pytest). Disposition:
  docstring sentence documenting the spawn/`__main__`-guard contract.
- **N2 (medium, tight-budget users; constructible)**: the gate omits
  `runtime.cache_enabled`, so cache-disabled + workers>1 runs k=workers
  children doing FULL numerical production with no aggregate admission —
  serial honored the per-tile budget one-at-a-time; X01 can oversubscribe,
  surfacing OOM as BrokenProcessPool instead of ResourceAdmissionError. The
  "children strictly lighter than admitted barrier jobs" justification is
  vacuous when there are no barrier jobs. Disposition: **code fix — gate the
  concurrent stage on `runtime.cache_enabled`**, making it exactly
  co-extensive with the C6-40 phase route (children are then cache-hit
  readers, strictly lighter than the admitted barrier envelope);
  cache-disabled multi-worker runs keep the serial loop verbatim. The E2E
  path is cache-enabled and is unaffected by the gate.
- **N3 (minor)**: abrupt child death (OOM kill/segfault) surfaces
  BrokenProcessPool for whichever future is checked, not the first-sorted
  per-tile error — the "first failure in sorted order" wording overpromises
  for unpicklable/abrupt death. Serial had the same liveness exposure.
  Disposition: docstring precision.

## Recorded observations (no action)

- Store-key distinctness between same-content tiles is INCIDENTAL: the
  content identity embeds GDAL DERIVED_SUBDATASETS metadata carrying the
  absolute input path (reviewer proved 3 byte-identical copies under 3 tile
  names produce 3 distinct store keys). get_or_create is cross-process safe
  (mkdir exist_ok + blocking flock per key + atomic manifest replace), so
  the same-identity race is unreachable here — but distinctness is not
  guaranteed by an explicit tile/path field. Test-hygiene/design debt note.
- Existing tests do not pin sorted-prefix truncation (only set equality);
  downstream consumers are filename-keyed and order-free.
- Reviewer's probes (out-of-band): first-sorted failure selection verified
  with two distinguishable failures; spawn-`__main__` failure reproduced;
  33/33 unit tests pass (test_export_concurrency.py + test_geometry_service.py,
  NUMBA_NUM_THREADS=24).

## E2E blind spots (accepted)

Cache-enabled only; generous budget (N2 path unexercised); everything
succeeds (N3 unexercised); completion-order publication inherently racy and
unpinned. The post-E2E gate change (N2) is not covered by this E2E — it
narrows the cache-disabled route to serial (the pre-X01 behavior), which the
existing serial-route suites already cover.

## Post-E2E disposition (2026-10-16, commit 94cd7b50)

All three findings landed as dispositioned:

- **N2**: the stage gate is now `len(pending) > 1 and runtime.workers > 1
  and runtime.cache_enabled` — literally the same condition as the C6-40
  phase-route gate above it; cache-disabled multi-worker runs keep the
  serial loop verbatim.
- **N1/N3**: `_concurrent_geometry_exports`' docstring now documents the
  spawn `__main__`-guard contract and the BrokenProcessPool behavior on
  abrupt child death; the admission justification wording states the
  cache-enabled premise (children are cache-hit readers).
- **Tests reworked**: the content test drives the stage directly with
  `cache_enabled=False` (children do full production — the heaviest version
  of the stage); new `test_cache_disabled_multi_worker_keeps_serial_route`
  pins the N2 gate (spy asserts the stage is not entered; the serial route
  publishes the full artifact set).
- **Verification**: focused 34/34 (test_export_concurrency +
  test_geometry_service, NUMBA_NUM_THREADS=24). Battery A/B
  (tests/differential+integration+unit, identical command both legs):
  184 failed / 3124 passed without the change vs 184 failed / 3125 passed
  with — the sorted FAILED lists are byte-identical (the documented
  pre-existing contention/order flake family;
  `test_portable_profile.py::test_lowered_helpers_use_explicit_fma_without_fast_flags`
  appears in both legs' sets, confirming it is not fix-induced).

E2E outcome (recorded in REGISTER S11-3): job 14096139 chain 3838.3 s =
64.0 min = **1.723×** vs the S10-36 A-arm; export stage 919.5 s (2.946×,
gate ≤ 2200 ✓); bitwise 24/24 SVF + 24/24 TMRT bands;
export_child_reports=0 (child hook did not fire in spawn children; the
stage-level gate metric is unaffected — recorded, not chased).
