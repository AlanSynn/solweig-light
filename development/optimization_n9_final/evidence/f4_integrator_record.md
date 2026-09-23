# F4 integrator record: applied disposition (closed_cpu_only)

Integrator record complementing `f4_release_disposition.md` (release-owner
audit, adopted in full) and `f1r_cpu_only_plan.md`. Basis: F3 TERMINAL
NATIVE_LOSE -> native closed for this release; the CPU stream is the
verified win carrier (F3: B1/A8 2.08x binary-1024, 1.32x mix-1024, 1.23x
binary-128, 1.04x mix-128 MARGINAL; raw class 0.88-0.93x LOSS -> guard).

## Shipped default route (recorded for FINAL_SELECTION/MERGE_MANIFEST)

Admitted packed channel triple, NOT all-raw, lane-aligned block, no
explicit serial demand, env unset or non-expert
  -> bounded Numba stream row B, budget PINNED 1
     (SELF_PARALLEL, one slot, zero background pool threads; leaf prange
     owns numba's threads; region owner keyed (pid, 1) via
     execute_regions(budget=stream.thread_budget)).
Declines -> legacy A8 path (bitwise-identical by construction + pinned
tests): all-raw-everywhere (the F3 measured loss class, O(P) mode-byte
guard at mint), non-admitted channels, degenerate/lane-misaligned blocks,
driver parallel=False, expert env native|ispc (B7-32 route).

## Audit adoption + integrator completions

- A1c (budget pin) ADOPTED and completed: the release-owner's fix pinned
  the plan; the integrator additionally passes the pinned budget to
  execute_regions -- the pool reads threads_per_worker when no budget is
  given (region_pool.resolve_budget), so a mint-only pin would still have
  sized the shared owner (pid, threads_per_worker). Both are in.
- A3 (tri-state) ADOPTED: engine.py keeps `True if threads>1 else None`;
  the consult fires at the shipped threads_per_worker=1 default. This
  ships an UNMEASURED-at-budget-1 timing claim, accepted under a
  PRE-COMMITTED F6 rule (recorded before F6 runs): F6 gains one compact
  threads_per_worker=1 cell, FINAL vs pinned main; if the stream LOSES
  there, engine restores the plain boolean and the manifest records the
  removal. Correctness at budget 1 is not in question (bitwise chain).
- A2 (aplus wiring) ADOPTED: aplus_decode stays SHIPPED;
  patch_radiation.py and cylinder_longwave.py now import
  `_decode_at_plus as _decode_at`. The fused route (env-gated OFF at
  defaults) decodes mode-specialized; generic fallback arm retained;
  parity pinned by the n9_producer suite. NO default-path decode
  improvement is claimed (the dense A8 decline target has no packed
  decode).
- Archive moves (N1/N2/N3), packaging (N4/N5), doc repairs (N6),
  inverted installed-wheel gates: applied as specified. Research copies:
  experiments/optimization_v8/native_dispatch/ (+ region_native_reduce.py
  extracted from region/consumers.py so the shipped package carries no
  native-artifact dependency).

## Accepted residuals (honesty labels, carried into the manifests)

1. 128-mix stream win is MARGINAL (+4.3%, within the F3 spread rule).
2. Single-channel-raw compositions are UNMEASURED and stream by design;
   the guard is exactly the measured all-raw loss class -- no widening
   without measurement.
3. B1-over-B4 dominance is measured in all 6 cells; the mechanism is
   partially attributed (slot page cost / pool sizing), accepted as a
   configuration selection between two measured arms.
4. Cold-start JIT: the default path gains njit kernels; the inherited
   cold-regression gate (<=3%) is explicitly assigned to the F6
   cold/warm comparison (release-owner 4.5), not assumed.
5. The default executor CHANGES vs the N8 endpoint (row A everywhere).
   The timing claim is F3/F6-bounded; the correctness claim rests on the
   stream == whole-scene == legacy bitwise test chain and the decline
   parity (the decline target IS the reference).

## Commit sequencing (integrator, forward on perf/native-optimization)

- Commit A (behavior): budget pin + raw guard + structural dispatch +
  tri-state keep + aplus wiring + pipeline/engine/cylinder doc repairs.
- Commit B (removal/packaging): archive relocations, consumers split,
  _native_dispatch/__init__ rewrite, pyproject data, setup.py deletion,
  archived-feature skips, inverted installed-wheel gates.
- Commit C (record): this file + release-owner disposition + plan delta.
Each lands only with its tests green (workers' reconciliation included).

## Gate triage (2026-09-23, integrator): F4 run vs pre-F4 baseline

Method: full `tests/unit tests/integration` run on the F4 tree
(fresh NUMBA_CACHE_DIR) diffed against the IDENTICAL run on the pre-F4
committed tree (8e3e9eba) in a detached worktree
(/tmp/n9_pref4_check, PYTHONPATH override, fresh cache).

Baseline (pre-F4 8e3e9eba): 17 failed, 449 passed, 8 errors.
F4 tree:                    16 failed, 450 passed, 7 errors.

Classification — every F4 failure class exists in the baseline:

1. test_portable_profile FMA inspection: pre-existing numba cache
   artifact, NOT an F4 regression. In-suite, an earlier test's
   subprocess populates the on-disk kernel cache; a later
   cache=True load returns INVALID inspect_llvm stubs ("Inspection
   disabled for cached code"). Verified: the test PASSES alone with a
   fresh cache dir (2.13 s) and FAILS in-suite on the baseline tree
   too (fresh cache dir there as well).
2. test_runtime_pipeline test_changed_input_cannot_publish_geometry
   [geometry]: pre-existing. Reproduces identically on the pre-F4
   committed tree, isolated and in-suite. The [read] boundary passes
   on both trees.
3. p7_serial_variant_harness / p7_benchmark_harness / exact_cpu_pairs
   (15 baseline failures): all present in the baseline failure list;
   harness/subprocess-flavored, pre-existing.
4. test_compatibility errors (7-8): pip-less worktree venv,
   pre-existing (verified via git stash earlier; baseline shows 8).

Delta note: baseline shows ONE MORE failure and ONE MORE error than
the F4 run (17/8 vs 16/7); the F4 rerun list is being diffed
name-by-name against the baseline before Commit A lands. No F4
failure may appear outside the baseline set.

Diff RESULT (fresh-cache F4 rerun): 16 failed, 450 passed, 8 errors
in 97 s. The F4 failure set is a STRICT SUBSET of the baseline set:
15 harness/pipeline failures identical by name, the in-suite FMA
inspection flake passed this time (order-dependent artifact: it fails
only when an earlier in-suite subprocess populates the on-disk kernel
cache before the test's first in-process call), and the compatibility
error count matches the baseline (8). ZERO F4 regressions. The
remaining gate dependency is the stream-owner's reconciled test suite.

## optimization_v8 gate (2026-09-23, integrator): GREEN

`NUMBA_NUM_THREADS=2 NUMBA_CACHE_DIR=<fresh tmp> .venv/bin/python -m
pytest tests/optimization_v8/{stream,n9_producer,region,policy,
integration,numba,layout,reference,dx} -q` ->
**1999 passed, 7 skipped, 0 failed** (101 s). The stream-owner's
reconciled test set was already applied in the shared tree (net -349
lines: N8 native-row/policy coverage removed, pinned-budget contract
asserted at stream/test_lw_stream.py:414
test_plan_thread_budget_pinned_to_one_regardless_of_runtime_threads,
all-raw/mixed-packed structural declines covered in
integration/test_lw_dispatch.py). The installed wheel-gate suite
(tests/optimization_v8/installed) is EXCLUDED here on environment
grounds (worktree venv has no pip / no working `build`; same
environmental class as the test_compatibility errors) -- the inverted
wheel gates run in F5's dedicated no-env verification instead.

## Landing record (2026-09-23, integrator)

- Commit A (behavior): 1581d882 -- 19 files, +965/-1224.
  Verified standalone in a detached worktree: unit+integration 16
  failed/450 passed/8 errors (EXACTLY the pre-existing baseline set);
  optimization_v8 1994 passed/7 skipped with 3 deselected; the only
  A-only deltas were 2 further structural-pin tests
  (integration/test_lw_dispatch.py::test_structural_default_routes_
  stream_bitwise, ::test_unknown_legacy_env_value_takes_structural_
  default) whose bitwise/mode/plan asserts ALL PASS and which fail
  ONLY at the final _policy_gone() line -- the same single class as
  the 3 deselected (they require the B archive move). Total
  structural-pin set: 5 tests, one class, all green at B.
- Commit B (removal/packaging): 08d05cef -- 24 files, +239/-357
  (git rename detection: the six machinery moves landed as 99-100%
  renames).
- FINAL gate on the committed B tree (one session, fresh cache):
  **2449 passed, 7 skipped, 16 failed, 8 errors** -- the 16 failure
  names are exactly the pre-existing baseline set (15
  harness/subprocess + runtime_pipeline[geometry]); 8 errors are the
  pip-less-venv test_compatibility class; optimization_v8 active
  suites contribute ZERO failures. installed wheel-gate suite
  excluded on environment grounds (no pip/build in this venv); it is
  F5 scope in the dedicated no-env environment.
- Commit C (records): this file, the release-owner disposition, the
  f1r supersede header, packet_tests.txt, n8_attribution.json, and
  the f4_small_chronology_default evidence.
