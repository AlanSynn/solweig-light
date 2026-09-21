# C6-60 independent review of C6-40 (native geometry precompute phase adapter)

Label: independent GLM review; Opus unavailable.
Route verification: this review session's served model is GLM-5.3-flash (Z.ai endpoint);
no Anthropic Opus route is configured or verifiable for this session (MODEL_ROUTING.md:
an alias is not served-provider evidence; `model: opus` templates require a verified route).

- Reviewer: C6-60 (independent of the C6-40 implementer; no shared implementation work).
- Review date: 2026-09-21.
- Subject: worker task C6-40, worktree `/Users/alansynn/Workspace/solweig-light-v6-phases`
  (detached at `4b83452ba7e83c4637c979a51351ea99c9001016`), deliverables
  `src/solweig_light/runtime_phases.py`, `tests/optimization_v6/phases/`,
  `optimization_v6_continue/evidence/phases/*`.

Note on evidence location: the C6-40 evidence files are NOT in the integration worktree's
`optimization_v6_continue/evidence/phases/` (that directory does not exist there); they
exist only inside the worker worktree. The integrator must copy them into the integration
worktree when landing C6-40.

## What I verified directly vs took from evidence

Verified directly (executed or read by this reviewer):

- All four recorded sha256 hashes reproduce exactly (`shasum -a 256` in the worker
  worktree): runtime_phases.py, the test file, the integration recipe diff, the decision
  matrix. The commands/hashes provenance file is self-excluded per the m5 convention.
- Worktree state matches the record: detached HEAD at 4b83452b, no branch
  (`git branch --show-current` empty), zero tracked-file modifications
  (`git diff --stat` empty), untracked files are exactly the three owned paths.
- Phase suite rerun by this reviewer in the worker worktree with the project venv
  (`PYTHONPATH=src`, single pytest process, no xdist):
  `17 passed in 21.09s` (worker recorded 20.81s / 20.93s on two runs).
- Full read of `runtime_phases.py` (935 lines), the 17-test suite, and the integration
  recipe diff.
- `git apply --check` of the recipe diff from the integration worktree at branch
  `perf/claude-glm53-cpu-v5`, HEAD `58d7fe2333ab80425f9948af8367f7b57f545f5c`
  (worker base 4b83452b is an ancestor; C6-70a..h already landed): APPLY_CHECK_OK.
  Not applied, per instructions.
- Helper contracts the module leans on, read at the worker base:
  `runtime._read_done` (None/0/nonzero, atomic done markers), `runtime._job_failure`
  (rebuilds the child's own exception via `_child_exception`, falls back to
  `TileExecutionError("...exit code N...")` for crashed children), `runtime._reap_worker`
  (terminate=True path with kill fallback), `runtime_memory.plan_phase_admission`
  (raises `ResourceAdmissionError` in-process; `admissible_workers` is the K-largest
  bound; individually infeasible jobs raise under both policies).
- Store semantics behind the fingerprint claim (`cache/geometry.py`): `_open` validates
  each generation SELF-consistently (recomputes `content_fingerprint` of the actual
  payload files and compares to that generation's manifest, plus `payload` JSON
  round-trip); `key_for(identity)` derives the cache key from identity +
  model_version/format/version only. Nothing downstream compares entry fingerprints
  across publications, so publication-unique (mkstemp-named) visibility payload
  fingerprints cannot make serial and phase stores unequal or non-interchangeable.
- The five gates hold on code inspection (details below).
- Forbidden moves: no `fastmath`, no approximation or tolerance changes
  (`rtol/atol/allclose/seterr` absent from both deliverables), no branch creation, no
  commit/push (clean tracked tree, detached HEAD), owned-paths discipline respected
  (only `src/solweig_light/runtime_phases.py`, `tests/optimization_v6/phases/`,
  `optimization_v6_continue/evidence/phases/` are new/untracked). Module inertness
  confirmed by grep: nothing in `src/` references `runtime_phases`.

Taken from evidence (not re-executed): the two recorded full-suite elapsed times, the
module-inertness import command output, the scratch `py_compile` of post-patch api.py,
and per-test internals beyond the rerun above (contended-host caveat as recorded; no
performance claims anywhere — correct posture).

## Gate findings

- GATE 1 (ordered publication, journal ceremony, manifest-last): holds. Workers stage
  `job-N.stage.json` atomically; `commit()` journals `begin`, writes `result.json` by
  single atomic rename (commit point), journals `commit`; `drain()` commits only the
  contiguous staged prefix from `committed_upto`; `PHASE_MANIFEST.json` is written last
  and re-reads each published record from disk to compute per-tile digests, so it
  attests the published bytes. Adversarial completion order cannot leak into
  publication order (staged dict + prefix drain).
- GATE 2 (failure semantics): holds. `observe_failure` gives started lower-index jobs a
  bounded grace, picks the numerically first recorded failure, harvests completions
  below it, drains with `limit=first`, reaps every dispatched slot with
  `terminate=True` before raising, and raises the child's own rebuilt error
  (`_job_failure` -> `_child_exception`); a crashed child (no failure.json) surfaces
  `TileExecutionError("exit code N")`. Ordering of stage-vs-done writes in the child
  (stage `os.replace` before done marker) makes the harvest race-free. F3 below records
  the bounded-grace corner.
- GATE 3 (native thread caps): holds. Children are fresh `Popen` processes with the
  thread-limit env set before first import (fork/spawn cannot bypass this: there is no
  in-parent fork path). The child asserts `numba.config.NUMBA_NUM_THREADS == configured`
  at import, pins with `set_num_threads`, records the mask at kernel entry, and the
  parent refuses any staged record where `mask_pinned != configured` or (for
  cache-miss tiles) `mask_at_kernel_entry != configured`; tamper test passes. F4
  records the cache-hit nuance.
- GATE 4 (admission before spawn, width bounded): holds. `plan_phase_admission` runs
  parent-side before any child exists; policy="reject" raises in-process with zero
  journal lines and zero stub events (test 13); the scheduler never exceeds
  `plan.admissible_workers` slots (spawn only when `len(slots) < width`; the
  dead-worker failover removes a slot before spawning its replacement).
- GATE 5 (single api.py hook, serial route untouched): holds structurally. The recipe
  is a pre-loop hook in `_calculate_svf` gated on `len(pending) > 1 and
  runtime.workers > 1 and runtime.cache_enabled`; for every other configuration the
  patched loop is observationally identical to the original (same pending set, same
  order, same per-tile existence check semantics; per-tile export writes cannot change
  another tile's pending decision). The legacy TIFF/ZIP/NPZ publication stays wholly
  inside the untouched serial loop. But F1 below is a real defect in this diff.

## Findings

- F1 (MAJOR — integration blocker, one-line fix): the recipe diff's
  `_precompute_geometry_phase` calls `np.sum(create_patches(patch_option)[4])`, but
  `numpy` is never imported in that scope: api.py's only `import numpy as np` is
  function-local to `run_walls_aspect` (api.py:19). The phase route would raise
  NameError on its first activation (`len(pending) > 1 and workers > 1 and
  cache_enabled`). The recorded scratch `py_compile` check cannot catch a NameError.
  The serial idiom uses the builtin: `int(sum(create_patches(patch_option)[4]))`
  (geometry/service.py:78, :248). Fix: replace `np.sum(...)` with builtin `sum(...)`,
  re-hash the diff into the evidence file, re-run `git apply --check`. Applies to
  `integration_recipe_C6-40.diff` only; `runtime_phases.py` and its gates are
  unaffected.
- F2 (MINOR — integrator confirmation): the recipe hardcodes `windchannels=1` in the
  memory descriptors while the test suite exercises 12. Geometry is wind-independent,
  so 1 is plausibly the correct (minimal) charge through
  `runtime_memory._native_allowance`, but the integrator (C6-70, api.py owner) must
  confirm that choice against the C6-42 reservation model when wiring. Not a C6-40
  gate violation: the adapter is parameter-generic.
- F3 (LOW — documented, accepted): if a lower-index job would fail only AFTER the
  bounded grace expires (`failure_grace_seconds=5.0` default), the numerically-first
  error is unattainable and the observed higher failure's rebuilt error is raised
  instead. Unbounded waiting is not an option; m3 §7.3 sanctions the bounded grace and
  the module docstring and decision matrix state it. Accepted; recorded for the
  failure-contract dossier.
- F4 (LOW — by design, honest): for `cache_hit=True` tiles the parent skips the
  kernel-entry mask equality check (no kernel ran in that child; the produced arrays
  belong to the prior producing run and are independently re-validated by the store
  manifest digest). Kernel-entry attestation therefore exists only on the producing
  run. Correct semantics; noted so nobody mistakes it for an omitted check.
- F5 (LOW — D04 reading): D04's "serial diagnostic fallback for a failed precompute"
  is satisfied by retention, not by fallback: the phase error is raised directly, the
  serial loop remains the verbatim route for workers==1 / cache-disabled /
  single-pending-tile, the raised error is the child's type/message-preserving rebuilt
  error (the same error serial publication would produce at that tile), and no
  published artifact is ever removed. Partial-output state after a phase failure
  differs from serial (no lower-tile legacy exports land before the failure), which is
  inherent to pre-loop precompute and consistent with D04's staged-prefix model. The
  integrator should make this reading explicitly.

## Counterexample hunt (adversarial notes)

- Out-of-order commit window: none found — commits are prefix-drained from a staged
  dict; completion order cannot reorder them; the reversal test (tile 0 finishing
  last) proves it end-to-end.
- Admission race: none — admission completes before the publication directory, job
  files, or any spawn exist; a rejected plan leaves zero children and zero journal
  lines (asserted by test 13).
- Mask bypass via fork vs spawn: no fork path exists; every child is a fresh
  interpreter with env set pre-import, and the child-side assert is the enforcement
  point with parent-side consistency validation. A child that falsifies its record
  consistently is not detectable parent-side — true attestation is impossible from the
  parent — and the worker does not claim otherwise.
- Serial-route behavior change: none for non-phase configurations (see GATE 5).
- Cross-run contamination: staging lives in a per-call TemporaryDirectory; the
  publication root is reused across runs but nothing reads stale journals for
  decisions, and result.json/PHASE_MANIFEST.json are atomically overwritten.
- Cache-hit lie to dodge GATE 3: a falsified `cache_hit` still requires a real store
  generation whose key and manifest digest the parent independently revalidates, so
  the dodge buys nothing.

## Verdict

APPROVE-WITH-CONDITIONS.

C6-40's module (`runtime_phases.py`) and test suite meet all five completion gates;
evidence records are accurate (hashes, worktree state, suite rerun reproduced); no
forbidden moves. Conditions, both on the integration path (C6-70 integrator + worker
follow-up), not on landing this review:

1. Fix F1 in `integration_recipe_C6-40.diff` before integration: builtin
   `sum(...)` instead of undefined `np.sum(...)` (match geometry/service.py:78);
   re-record the diff sha256 and re-run `git apply --check`.
2. The integrator explicitly confirms the `windchannels=1` memory descriptor (F2) and
   the F5 D04 reading when wiring the api.py hook, and copies the C6-40 evidence
   directory from the worker worktree into the integration worktree.
