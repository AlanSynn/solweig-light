# N8-30 delta review: N8-14 pool-lifecycle + conftest-shadowing repairs

*Independent delta review (reviewer did not author N8-14 or N8-40).
Worktree `/Users/alansynn/Workspace/solweig-v8-native` @ `16cdc56c`
(`perf/native-optimization`, all uncommitted). Delta against
`n8_30_review_n8_14_region.md` (APPROVE-WITH-NOTES, 151 passed) and the
`found_defect` / `known_interference` sections of
`n8_40_integration_record.json`. JSON twin:
`n8_30_review_n8_14_delta.json`.*

**Verdict: APPROVE-WITH-NOTES.** Both repairs close their defects; the
two new regression tests are proven non-vacuous by re-introducing the
bug in a scratch copy. No blocking defects, no required repairs. One
recommended integrator-side comment refresh (R-D1) and three notes.

**Reruns (this review, loaded host, pass/fail only):** region standalone
**153 passed, 3 warnings** (34.3 s) — baseline 151 + exactly the 2 new
tests; `integration/test_lw_dispatch.py` **9 passed**; `policy/ + dx/`
**95 passed**; CLI order `region/ integration/ policy/ dx/` — the order
that produced 2 collection errors per `known_interference` — now
**collects clean: 257 passed, 3 warnings**.

## 1. Defect closed (lifecycle) — PASS

Probed against the real worktree package (`/tmp/n8rev14_delta/
probe_lifecycle.py`):

- One `shared_pool(2)` → **exactly 1** `_LIVE_POOLS` entry (identity
  count). `RegionPool.__init__`'s `_track_pool` (region_pool.py:477) is
  the single registration point; the unguarded append in
  `shared_pool` is gone (region_pool.py:836-839).
- `shutdown_all_pools()` → **0** entries, `_POOLS` empty; five
  create/shutdown cycles stay at 0 (no accumulation).
- Explicit `RegionPool(3)`: tracked exactly once at construction,
  untracked by `close()` → `_forget_pool` (removes **all** occurrences
  by identity, region_pool.py:848).
- **Deliberate refused-close case, constructed cheaply and executed
  positively:** a pool with an active session refuses `close()`;
  `shutdown_all_pools()` suppresses the raise and the pool **stays
  listed** with `closed=False`; once the session ends and `close()`
  succeeds it leaves the list.

**Not vacuous:** the old bug was reintroduced in a scratch copy
(unguarded `shared_pool` append, single-occurrence `_forget_pool`
remove, prune-less shutdown) and the two new tests' exact assertion
logic re-run: one create → **2** entries
(`test_live_pool_tracked_exactly_once` FAILS); per cycle one phantom
survives close and the list grows 1→2→3→4→5 across shutdown cycles
(`test_closed_pools_leave_the_live_list` FAILS) — precisely the
`found_defect` description.

## 2. Adversarial — PASS

- **The prune cannot drop a still-live pool (executed):** with a
  still-live pool holding an active session (refused close) plus
  simulated closed + poisoned leftovers, the prune keeps the live pool
  and drops the dead ones. `poisoned` is only ever set by the fork hook
  (service-refusing, never live), and `closed=False ∧ poisoned=False`
  entries are unconditionally kept.
- **Fork logic unharmed:** `_FORK_GENERATION` untouched by
  close/forget/prune; the 3 real-`os.fork` fork-policy tests are green
  in-suite (the 3 suite warnings are their expected DeprecationWarnings).
- **No new deadlock:** `_POOLS_LOCK → pool._lock` is the only lock
  nesting; `close()` releases `self._lock` before `_forget_pool`, and
  `shutdown_all_pools()` releases `_POOLS_LOCK` before calling
  `close()`. No reverse order exists.
- **Cosmetic:** the final
  `assert all(not p.closed and not p.poisoned for p in tracked)` in
  `test_closed_pools_leave_the_live_list` runs over an already-empty
  list and cannot fail under any code. The two load-bearing asserts
  before it are proven non-vacuous above (N-D3 in JSON is this note).

## 3. Claimed-unchanged semantics — PASS

- Per-file counts match the baseline review exactly: plan 31,
  pool_budget 12→**14** (+2 new), cancellation 10, composition 77,
  consumers 6, scratch 12, fork_policy 3. No test removed or rewritten.
- The real driver dispatch path (`test_lw_dispatch.py`, incl.
  `test_region_pool_reuse_and_shutdown` which exercises the pool through
  `cyl.Lcyl_v2022a_primary`) is green standalone; policy/ + dx/ green.
- Lock-free fork hook, `_POOLS` keying/reuse, `MAX_POOL_BUDGET_SLOTS`
  bound, cancellation/error identity: unchanged code paths —
  baseline citations at :477, :526-529, :575-578, :604-606, :783-784
  still hold verbatim; only lines ≥ ~836 shifted (+11, the NOTE comment
  and the shutdown prune/docstring), which moves the fork hook
  :881→:892 exactly.

## 4. Conftest repair — PASS

- **Zero bare `conftest` imports remain** under
  `tests/optimization_v8/region/` (docstring mentions only). The
  bootstrap + `LW_TEST_THREADS` pinning moved verbatim into
  `region_test_helpers.py`; `conftest.py` imports it and keeps the
  `sessionfinish` reset hook.
- **Uniquely named:** `region_test_helpers` exists only in the region
  suite (grep over tests/, experiments/, src/); it is neither
  `conftest` nor a name any other suite uses.
- The import swap is line-for-line (composition :23, consumers :21;
  net-zero line delta), so the baseline review's line citations in
  those files still align (spot-checked :31-33, :140-142).
- The previously-failing CLI order `region/ integration/ policy/ dx/`
  collects clean and passes 257 — the shadowing ImportError class is
  closed for region/.

## 5. Delta scope — CLEAN

mtimes show exactly six touched files: `region_pool.py` +
`test_region_pool_budget.py` (18:38, CHANGE 1) and
`region_test_helpers.py` (new), `conftest.py`,
`test_region_composition.py`, `test_region_consumers.py` (18:46-18:47,
CHANGE 2). Every other region file (region_plan.py, consumers.py,
region_case.py, __init__.py, the five other test files) predates the
baseline review (16:38-16:56). No out-of-scope delta found.

## Notes and obligations

| id | finding | action |
|----|---------|--------|
| R-D1 | `test_lw_dispatch.py:386-388` (integrator-owned) still says "a closed pool can stay listed -- n8-14 repair pending" — factually wrong post-repair; the filter there is now a pure safety net. | integrator refreshes the comment (content may stay) |
| N-D1 | Post-repair, the `shutdown_all_pools` prune is a pure safety net: `close()` always untracks on success, so no natural path leaves a closed pool listed (the probe had to simulate the stale entry). Matches the record's "documented safety net". | keep, do not extend |
| N-D2 | Same bare-`conftest` bug class remains live **out of scope** in `tests/optimization_v8/native/` (`test_aosoa_native_admission.py:26`, `test_aosoa_native_parity.py:29`). Pre-existing, covered by the documented native-first interference; not n8-14's to fix. | native-suite owner / N8-41 |
| N-D3 | The final `all(...)` assert over the empty list in `test_closed_pools_leave_the_live_list` is vacuous (cosmetic; the preceding asserts carry the proof). | optional tightening |

**Scope guard:** nothing outside
`optimization_v8_native_default/evidence/reviews/` was written (scratch
probes live under `/tmp/n8rev14_delta/` only); no network; no commits;
no timed benchmarking.
