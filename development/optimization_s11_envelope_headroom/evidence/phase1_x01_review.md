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
