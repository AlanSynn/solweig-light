# N8-30 review: N8-14 region dispatch + bounded multicore owner

*Independent review; reviewer did not author N8-14. Worktree
`/Users/alansynn/Workspace/solweig-v8-native` @ `16cdc56c`
(`perf/native-optimization`). JSON twin:
`n8_30_review_n8_14_region.json`.*

**Verdict: APPROVE-WITH-NOTES.** No blocking defects; no required
repairs. Four non-blocking recommendations (R1–R4) and seven notes
(N1–N7), all edge-documentation or integrator-contract items.

**Rerun:** `.venv/bin/python -m pytest tests/optimization_v8/region/ -q`
→ **151 passed, 3 warnings** (34.05 s), then again **151 passed, 3
warnings** (34.18 s, with `-rs`: **zero skips**, so the native C-arm
tests executed against the real staged artifact). Exactly the claim.
The 3 warnings are the expected `DeprecationWarning`s from `os.fork` in
a multi-threaded process, one per real-fork test. Collected per file:
plan 31, pool_budget 12, cancellation 10, composition 77, consumers 6,
scratch 12, fork_policy 3 = 151.

## 1. Exactness — PASS

- Bitwise convention is real: every comparison goes through
  `outputs_bitwise_equal` → `np.array_equal(u32(a), u32(b))` with
  `u32 = ascontiguousarray().view(np.uint32)` (`region_case.py:88-93`).
- Per-arm AND cross-arm, plus whole-call: A (oracle fanout) 11 shapes ×
  budgets {1,2,4} × seeds {0,1} = 66 cases assert serial == parallel ==
  one whole-extent oracle call (`test_region_composition.py:31-58`); B
  (SELF_PARALLEL `lw_primary_b`) serial == parallel == one whole kernel
  call with `max_in_flight == 1` (:61-92); C (native handle fanout)
  serial == parallel == one whole `NativeHandle.execute`, tails included
  (:105-137); cross-arm A == B and A == C on one adversarial case
  through the same boundary (:140-160); repeated-execution stability on
  one pool across 4 runs (:163-177).
- Block-grid identity is **structural**, not just tested:
  `block_spans()` *is* the serial loop expression
  (`region_plan.py:88-90`); regions are pure block-*index* ranges
  (:99-105) and both executors build spans exclusively via
  `plan.block_spans()` (`region_pool.py:604-606, 919-921`) — there is
  no other span source to diverge. Pinned by property tests over 8
  (total, b) grids including b=7 and the 0/1/127/128/129 edges, and a
  gapless ascending exact-partition test with region edges ⊆ block
  edges (`test_region_plan.py:23-54`).

## 2. Thread budget — PASS (the core gate)

- **Observed, not configured.** `max_in_flight` is maintained under the
  pool lock around real block execution (increment before slot acquire,
  decrement after release, `region_pool.py:402-425`) and asserted
  `<= N`, with `>= 2` for `N >= 2` under a GIL-releasing sleep that
  forces genuine overlap (`test_region_pool_budget.py:37-52`). A live
  thread census taken **inside blocks** bounds `threading.active_count()`
  to baseline + N − 1 (:55-76). N=1: zero threads, in-flight 1 (:79-90).
  Exactly N−1 persistent workers (`region_pool.py:521-536`); the
  submitting thread works the same queue (:436-451); slots == N.
- **SELF_PARALLEL** is a sequential per-block loop leasing one slot at a
  time (`region_pool.py:653-688`): in-flight == 1 structurally, nothing
  is ever enqueued so pre-existing workers stay blocked on
  `queue.get()` (quiescent, no CPU). Asserted with the real Numba kernel
  (`test_region_composition.py:90`) and on a fresh pool
  (`test_region_pool_budget.py:93-108`). My probe additionally confirmed
  in-flight == 1 and zero worker spawns on a pool with **live** workers
  from a prior fanout session — the one case the suite didn't pin (N6).
  No path lets B's Numba threads run while the owner holds >1 block.
- **No nesting / no second submission on one owner**:
  `PoolSessionConflict` from the session guard (`region_pool.py:573-586`),
  from re-entry inside a block, and from a genuinely concurrent second
  submitter while a block is held (tests :111-162).
- **Second-pool paths:** `shared_pool()` is keyed `(pid, budget)`,
  hard-capped at 8 distinct live budgets with a loud
  `PoolRegistryBound`, closed/poisoned entries replaced in place
  (`region_pool.py:812-837`; test :165-192). Residuals are declarative
  (N2) and per-owner-not-process-wide (N3) — see notes.

## 3. Cancellation — PASS

- Defined order, proven immune to wall-clock inversion: block 7 fails
  immediately, block 2 fails 250 ms later — block 2's error is raised
  (`test_region_cancellation.py:61-88`; `_raise_first`,
  `region_pool.py:710-743`, lowest admitted index, original object,
  type intact).
- Type preservation where it matters: `UnsupportedInput` stays a
  TypeError so the dispatcher's fallback decision is unchanged (:91-105);
  `NativeExecutionError` never swallowed (:108-119), including a
  synthetic post-launch failure through the real handle
  (`test_region_consumers.py:179-209`).
- No starts after cancel, nothing past the failing block (:122-164);
  drain bounded (every queued item retired exactly once). On failure no
  report is returned — the raise precedes `RegionReport` construction
  (`region_pool.py:628-640`); structural checks run before any dispatch
  (:203-220).
- Pool reusable after a cancelled session: state resets in `finally`
  blocks (:618-623, 587-591); my probe ran a clean bitwise-correct
  session on the same pool after a cancelled one. No dedicated in-suite
  test (N5 → R2).

## 4. Scratch — PASS

Dispatch-size independence including `region_blocks=10**6` with
allocation count `min(budget, blocks-per-region)` (`test_region_scratch.py:59-74`);
bounded by slots not blocks — 32 blocks → exactly 4 allocations at
budget 4 (:77-83); byte-extent disjointness of concurrent leases +
same-object reuse (:86-96); two distinct slots observed simultaneously
under a barrier (:99-122); NaN-poison between runs changes nothing and
the canary has teeth — a read-before-write consumer sees the poison
(:125-172); shape rebinding rejected loudly, tail misbind fails with
the same type through the region (:175-203). Full-capacity lease +
`[:rows]` view keeps arenas fixed-shape (`consumers.py:88-91`).

## 5. Fork hook — PASS (the subtle one)

- **Strictly lock-free, verified statement-by-statement.**
  `_poison_child_pools` (`region_pool.py:865-878`) executes exactly:
  a global int increment, `_POOLS.clear()` (dict clear), per-pool
  `pool._poisoned = True` (plain instance-dict store — `RegionPool` has
  no `__slots__`/`__setattr__` override and the read-only `poisoned`
  property does not intercept `_poisoned`), `_LIVE_POOLS.clear()`. No
  `with`, no `.acquire`, no lock is constructed or touched; queues,
  slots and worker state are never modified; a poisoned pool is refused
  at both `_ensure_workers` and `_session_guard` (:524-529, 575-578).
- **No constructed-pool escape:** the hook is registered at import
  (:881-882) and every `RegionPool.__init__` calls `_track_pool(self)`
  before returning (:477). The only escape is the silent 64-pool
  tracking cap (N4 → R1) — unreachable via `shared_pool()`'s 8-budget
  cap.
- **Real-fork tests, all executed:** child use of an inherited pool →
  `ForkedRegionPool`; child re-prepare via the cleared table reproduces
  the parent's bits; parent unpoisoned and reusable
  (`test_region_fork_policy.py:45-94`). Fork **while a block is held
  in-flight mid-session**: child runs clean on a fresh owner, parent
  session completes bitwise == serial (:97-171). `shared_pool()` in the
  child is fresh with an advanced fork generation (:174-208).

## 6. Common boundary — PASS

Planner/pool import stdlib + numpy + `RegionPlan` only (the
`solweig_light.runtime` import in `resolve_budget` is lazy,
`region_pool.py:783-784`). A grep for
`numba|ispc|opencl|drjit|native|loader|lw_b|lw_primary|aosoa` over both
modules hits **docstrings/comments only** — no backend import, and the
single runtime discriminator is `mode is ExecutionMode.BLOCK_FANOUT`
(:609), a parallelism class, not a backend id. A deliberately
non-SOLWEIG consumer passes through the boundary
(`test_region_consumers.py:30-57`). All backend specifics live in
`consumers.py` and are lazy: `lw_b_control` inside
`AosoaBConsumer.__init__` (`consumers.py:172`), `loader.native_handle`
inside `_NativeHandleReduce.__init__` (:110) — no import-time IO.

**Arms read-only:** every loader/layout/native/numba source mtime
(16:01–16:37) predates the region files (16:38–16:50);
`lw_b_control.py` sha256 `1d142ceb…` matches the prefix pinned in the
N8-12 review's `state_recheck`; `native_handle.py` still matches the
N8-10 review's structural line citations (registry :163-164,
`registry_snapshot` :204-207, dir lock :170-178). `direct_aosoa.py` /
`lw_native_aosoa.py` rest on mtime only (N7 → R4).

## 7. Registry growth — PASS

Real and executed: `registry_snapshot()` is the loader's actual
registry diagnostic (`native_handle.py:204-207`); the test snapshots
before, runs **two** full region workflows through the real prepared
handle, asserts unchanged (`test_region_consumers.py:156-176`) — and it
ran (zero skips in both reruns). The region-pool registry itself:
`(pid, budget)` keys, 8-budget loud cap, in-place replacement of
closed/poisoned entries (`region_pool.py:812-837`; test :180-192).

## 8. Ownership — PASS

HEAD `16cdc56c`, unchanged; zero tracked-file modifications (git status
shows only untracked packet dirs), so no `src/` change. N8-14 outputs
confined to `experiments/optimization_v8/region/` +
`tests/optimization_v8/region/` (sweep for `*region*` elsewhere finds
only the pre-existing dossier and task brief). `RegionReport` carries
functional counts only ("no timing", `region_pool.py:691-707`); the
suite's sleeps are liveness-forcing only and disclaimed as such.

## Notes and recommendations

| id | finding | action |
|----|---------|--------|
| N1 | Multi-failure corner: with ≥2 failing blocks, a lower-index block can rarely be skipped by cancellation before starting, so the raised error can differ from strict serial's choice (dequeue→start window, `region_pool.py:392-406`). Defined rule (lowest admitted index) stays deterministic and type-intact; docstring's "exactly the error a serial loop would have raised first" is slightly stronger than guaranteed in that corner. | accept wording softening eventually |
| N2 | Mode is declarative: an internally-parallel consumer misdeclaring BLOCK_FANOUT would exceed N; owner cannot detect (documented in-suite). | integrator contract |
| N3 | Budget is per-owner: concurrent sessions on distinct budgets/explicit pools can sum past any single N; shared_pool caps distinct budgets at 8 but does not sum-cap (docstring acknowledges `sum(N_i−1)`). Explicit `resolve_budget` checks ≤ cpu_count but not the runtime `cpu_budget` tightening. | workflow binds one N per process |
| N4 | `_track_pool` silently declines tracking past 64 live pools (`region_pool.py:801-809`) — a 65th explicit pool would escape fork poisoning. Unreachable via shared_pool; silent where the module's philosophy is loud. | **R1**: raise/warn |
| N5 | No dedicated test for success-after-cancel on one pool (structurally reset; reviewer probe confirms). | **R2**: add test |
| N6 | Mixed-mode reuse (fanout → SELF_PARALLEL with live workers) untested in-suite; probe confirms quiescence. | **R3**: add test |
| N7 | `direct_aosoa.py`/`lw_native_aosoa.py` read-only proof is mtime-only (no hash baseline recorded). | **R4**: pin hashes |

**Scope guard:** nothing outside
`optimization_v8_native_default/evidence/reviews/` was written; no
network; no commits; no timed benchmarking (pytest reruns + short
functional probes only).
