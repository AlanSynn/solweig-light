# REVIEW C5-33 — S02 persistent worker pool (runtime patch)

- **Reviewer:** independent GLM review (Opus unavailable)
- **Commit:** `8b3252ca14f9df0566ae25c6fc7d8830aa81ef47` ("Schedule tiles on persistent bounded worker processes (S02)") on `perf/claude-glm53-cpu-v5-rt`, worktree `/Users/alansynn/Workspace/solweig-light-v5-rt`
- **Base:** `bfd9915e`
- **Date:** 2026-09-20
- **Verdict:** **ACCEPT**

## 1. Scope check — PASS

`git diff --name-only bfd9915e 8b3252ca`:

```
src/solweig_light/runtime.py
src/solweig_light/runtime_worker.py
tests/optimization_v5/runtime/test_persistent_worker_pipeline.py   (new)
tests/optimization_v5/runtime/test_persistent_worker_protocol.py   (new)
tests/optimization_v5/runtime/worker_helpers.py                    (new)
```

`pipeline.py` and `engine.py` diff empty (byte-verified). `plan_admission` region extracted from both revisions and byte-compared: identical. `active_workers` is only read in `execute_tiles` (runtime.py:901, 946). Admission logic untouched.

## 2. Protocol correctness

### 2.1 Child environment — PASS

- `_child_environment` (runtime.py:663-676) sets all seven native thread vars (NUMBA/OMP/OPENBLAS/MKL/NUMEXPR/VECLIB/BLIS); passed via `Popen(env=...)` (runtime.py:832-839) so values are effective before the child's first import. `runtime_worker` imports only stdlib at module top and defers the pipeline import into `_run_job` (runtime_worker.py:64-72), preserving the delayed-import contract.
- Pool dir: `env[_WORKER_POOL_ENV] = str(root)` (runtime.py:817) is set once per call on a **local dict copy** of `os.environ`. Parent env is never mutated. Each call gets a fresh `TemporaryDirectory`, so no cross-call collision; there is no per-job env to collide with (jobs are JSON files). A pre-existing `SOLWEIG_LIGHT_WORKER_POOL` in the parent env is unconditionally overwritten for children. Nested `execute_tiles` inside a worker is also safe: the grandchild scheduler overwrites the var with its own root.

### 2.2 Scheduler loop, markers, EOF — PASS

- Marker publication is atomic (`os.replace` after staging write, runtime_worker.py:88-93); `_read_done` (runtime.py:696-709) treats an existing-but-unparseable marker as rc=1, so a corrupt marker fails the job deterministically instead of hanging the scheduler. Marker is checked before `poll()` per slot (runtime.py:923-934), so a marker written just before worker exit is honored.
- Busy-wait cadence (10 ms) is unchanged from base. Parent-side stdin writes go only to idle workers blocked in `readline()` with ~100-byte payloads — cannot fill the pipe; a dead child surfaces as `BrokenPipeError` (OSError) in `dispatch` (runtime.py:850-869), which reaps and respawns a fresh child on the same index. Python's SIGPIPE-is-ignored default makes this reliable.
- EOF semantics: graceful drain closes each worker's stdin (`_reap_worker(terminate=False)`, runtime.py:951-954); the worker returns 0 from `_serve` on `readline() == ""` (runtime_worker.py:124-126).
- No-progress liveness: every slot removal is a progress event that immediately triggers a refill (idle-exit runtime.py:913-921, `reap` via the event loop, dispatch-failure respawns inline). `active_workers >= 1` for non-empty job lists (per-job admission check precedes; runtime.py:571-591), so an empty-slots/pending-jobs stall is unreachable. No hang path found.

### 2.3 Failure propagation — PASS (identical to base)

`_job_failure` (runtime.py:712-731) reproduces the base construction at bfd9915e:762-782 verbatim: same `schema_version` 1 payload parse, same `_child_exception` allowlist (unchanged, runtime.py:631-660), same 4000-char stderr tail, same note format `f"tile job {index} failed with exit code {code}"` + optional `; worker stderr: ...`, same `TileExecutionError` fallback format. All three new routes converge on it:

- marker-reported failure (`complete` → `_job_failure`, runtime.py:871-873),
- process-exit failure (`reap` else-branch, runtime.py:897-898),
- dead-worker cancellation (raise inside the event loop → `except BaseException` handler).

Ordering: cancellation iterates `list(slots)` in spawn order — deterministic, matching base's dict-insertion-order iteration. `reap_worker` is bounded terminate → wait(5) → kill → wait on every path; every branch ends in `wait()`, so no zombies (probe-verified).

### 2.4 Orphan / deadlock probes (live, in /tmp)

Scripts in `/tmp/c533_probe/`, run from the rt worktree via `uv run python`:

1. **kill -9 a pool worker mid-batch** (`kill_child_driver.py`): 3 long jobs (32-day met file), `cpu_budget=2, workers=2`. Result: batch fails with `TileExecutionError: tile job 0 failed with exit code -9: ` (negative-signal convention same as base), all remaining pool children reaped within the 10 s poll window, `ps` shows zero `runtime_worker` processes and no zombies. **PASS.**
2. **SIGKILL the scheduler parent mid-batch** (`kill_parent_wrapper2.py`): 6 short jobs on 2 workers. Result: workers re-parent to PID 1, finish their current job, then see stdin EOF and exit; zero `runtime_worker` processes remain. A first run with 32-day jobs showed workers alive 30 s after parent death — that is mid-job continuation (EOF is only observed at the next `readline`), **bounded by the current job's duration and identical to base**, where one-shot children also completed their in-flight job after parent death. Not a regression; no indefinite orphans.

### 2.5 One-shot / stub fallback — PASS

Respawn path is behaviorally identical to base `start()`: same Popen argv (`-m <worker_module> --job ... --options ...`), same env construction, same per-job `job-N.{json,stdout,stderr}`, same exit-code interpretation (`reap`: unconfirmed + rc 0 → success; rc != 0 → `_job_failure`). Only delta is `stdin=PIPE`, which one-shot modules never read. Existing stub unit tests pass unchanged (see §4).

## 3. Semantic preservation — PASS

- `execute_tiles` signature unchanged; `TileResult` construction and the `tuple(r for r in results if r is not None)` return are unchanged.
- Per-tile artifacts: `job-N.json/.stdout/.stderr/.failure.json` at the same tempdir paths. Parent closes its stdout/stderr copies immediately after `Popen` (runtime.py:844-847); the persistent worker re-opens each subsequent job's streams via `dup2` with O_APPEND (runtime_worker.py:96-105) — distinct file per job index, so append vs base's truncate is immaterial. Job stdout/stderr land exactly where base put them.
- Checkpoint/publish: done marker is written only after `run_tile` returns (runtime_worker.py:131), so a success marker implies full publication.
- Bitwise claim verified: `test_persistent_batch_matches_single_execution_bitwise` compares SHA-256 of **raw bytes of every output `.tif`** (`tiff_digests`, worker_helpers.py:935-938) on the real `tests/reference/small_original_cpu` scene across 3 flag variants, with references routed through the same thread-limited subprocess machinery, and asserts exactly 2 distinct worker PIDs served the 3-job batch (proves reuse, no respawn). The RSS-plateau and injected-failure tests also use the real pipeline (no mocks).

## 4. Test runs (threads<=2, rt worktree)

| Command | Result |
|---|---|
| `NUMBA_NUM_THREADS=2 uv run pytest tests/optimization_v5/runtime/ -q` | **9 passed** in 22.51s |
| `uv run pytest tests/unit -k "runtime or admission or options" -q` | **25 passed**, 438 deselected in 1.78s |

Both match the expected counts.

## 5. Resource cleanup — PASS

Pool tmpdir is a `TemporaryDirectory`: removed on success (normal context exit after graceful drain) and on failure/exception (context unwinds after the reap handler re-raising). Diagnostic `worker-{pid}.pid` / `worker-{pid}.threads.json` live inside that private tmpdir and are removed with it; nothing is written outside the tmpdir; no unbounded retention. Tmpdir leaks only on parent hard-kill — identical to base.

## 6. Findings

| ID | Severity | Location | Finding |
|---|---|---|---|
| F-1 | LOW | runtime.py:876-898 (`reap`) | `reap()` drops a self-exited worker's `Popen` without closing `process.stdin`; the pipe fd is released only at GC (immediate under CPython refcounting; `ResourceWarning` possible under `-W`). One fd per completed one-shot job. Cosmetic; base closed streams explicitly. |
| F-2 | LOW | runtime.py:923-929 + runtime_worker.py:122-131 | Marker precedence divergence: a worker that writes a **success** marker and then crashes before the next `readline` is not a batch failure (job completed, idle-exit branch just removes the slot). Base would have failed the batch on the nonzero exit. Narrow exotic window (post-publication crash), outputs are complete and valid; noting for the record. |
| F-3 | INFO | runtime.py:955-961 | Cancellation reaps slots sequentially (`terminate`→`wait(5)`→`kill` per slot); base SIGTERMed all children before waiting on any. A SIGTERM-immune worker delays its siblings' termination by up to 5 s each. Bounded; no correctness impact. |
| F-4 | INFO | runtime_worker.py:124-126 | Post-parent-death workers linger until the current job finishes (EOF observed only at `readline`). Identical to base behavior for in-flight one-shot children; no action needed. |

No MEDIUM or HIGH findings. Both LOW items are non-blocking; no changes required.

## 7. Verdict

**ACCEPT.** Scope is exact, `plan_admission` is untouched, the failure payload/message construction is byte-equivalent to base, cancellation and reaping are bounded and probe-verified (worker kill and parent kill both leave zero orphans/zombies), one-shot behavior is preserved for existing stub tests, and the bitwise single-vs-batch claim is backed by real-scene TIFF byte comparisons. Test counts observed: 9 + 25 passed.
