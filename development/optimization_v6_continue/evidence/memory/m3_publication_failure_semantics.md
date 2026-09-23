# M3 — Sorted publication / partial-failure semantics map (commit e7a2d6ec)

Contract document for any future parallel phase adapter. All citations at `e7a2d6ec8594b234820e7783e0ca26d821de7f3d`, worktree `/Users/alansynn/Workspace/solweig-light-v6-mem`.

## 1. The three orderings (not one)

The pipeline uses **three different tile orderings** in its three phases:

| Phase | Ordering | Code |
|---|---|---|
| `run_walls_aspect` (preprocess) | **unsorted** — `os.listdir` order | `api.py:29` |
| `_calculate_svf` (geometry) | **lexicographic string sort** of the set intersection | `api.py:81` `common = sorted(set(building) & set(dem) & set(trees))` |
| `run_utci_tiles` (simulation) | **numeric tuple sort** | `api.py:151` `sorted(common, key=lambda key: tuple(int(value) for value in key.split('_')))`, dispatched in that order by `execute_tiles` (`runtime.py:819,901-950`) |

Consequence for an adapter: "sorted" is only a *public result/publication* guarantee at the simulation phase. `10_10` sorts before `2_2` lexicographically but after numerically — a future parallel geometry phase must not assume the SVF loop's lexicographic order equals the simulation order. Per-file preprocess publication today has **no ordering guarantee at all**.

## 2. Where publication is actually transactional

Publication is **per-tile, inside each child worker**, not a global sorted commit:

- Transaction identity = sha256 over the sorted output-path signature: `persistence.py:268` (`key = hashlib.sha256(_canonical(sorted(self.signature["outputs"]))...)`).
- Destination flock locks per output: `persistence.py:342-361` (destination key `:345`).
- Staged writes with per-band digests (`_stored_bytes_digest`, `persistence.py:456-468`, digest verify `:131,334,513,591`).
- Checkpoint = state generation save + atomic record commit: `persistence.py:470-497` (record with `state_sha256` + band hashes `:488`).
- `complete()` order (`persistence.py:540-595`): **publication journal first** → per-artifact staged→final renames (`:577`) → **completion manifest last** (`:601` references the held-set). A crash between renames leaves journal + some-renamed finals; recovery validates digests (`_recover`, `persistence.py:389-429`, state verify `:403`).
- `resume=False` refuses an existing incomplete transaction instead of discarding: `persistence.py:285-287` (`raise PersistenceError("Incomplete output transaction exists; request resume=True explicitly")`); `resume=True` with nothing to resume also raises (`:304-305`).

## 3. Error / skip semantics per phase

| Phase | Per-item failure | Resource failure |
|---|---|---|
| `run_walls_aspect` | **reported-and-skipped**: `except Exception: print(...)` per file (`api.py:43-47`) — a bad Building_DSM file does not stop the phase | `except ResourceAdmissionError: raise` (`api.py:43-44`) — admission failure aborts |
| `_calculate_svf` / `prepare_geometry_exports` | tile failure propagates (no per-tile skip in the serial loop; `api.py:81-96`); export path raises through `plan_admission` (`service.py:275`) | propagates |
| `run_utci_tiles` (child) | `_run_job` catches `BaseException` → writes `<job>.failure.json` payload (schema `runtime_worker.py:50-61`) → returncode 1 → atomic done marker (`runtime_worker.py:88-93`) | same path; `ResourceAdmissionError` is rebuilt parent-side (`_child_exception`, `runtime.py:618-660`) so type identity survives the process boundary |
| `execute_tiles` (scheduler) | raises the rebuilt failure via `_job_failure` on nonzero done code or missing marker (`runtime.py:871-874,898`), then **reaps ALL live children with `terminate=True`** (`runtime.py:955-961`; also `:868` on the early path) | same |

**Failure ordering rule (current behavior):** dispatch is strictly `next_index` ascending (`runtime.py:819,938-950`) — job i+1 is dispatched only when a slot is idle after i. On the first failing job the scheduler raises immediately; **remaining jobs never start**. Completed lower-index tiles keep their published artifacts; the failed tile leaves its staging tree under `.solweig-light/transactions/<key>/` untouched (no cleanup pass on the failure path). So partial publication across the *batch* is possible (tiles 0..k-1 published, k failed, k+1.. never run) — exactly the "first serial-order failure controls public error semantics" boundary D04 requires preserved.

## 4. Stage barriers in `thermal_comfort`

The all-geometry-complete barrier is a **workflow-level sequential call chain**, not an in-scheduler barrier: `api.py:208-210`:

```
run_walls_aspect(preprocess_dir)          # :208  — ALL preprocess before SVF
_calculate_svf(preprocess_dir, ...)       # :209  — ALL geometry before simulation
run_utci_tiles(...)                       # :210  — simulation pool
```

Any parallel phase adapter must preserve: no simulation job may be admitted until *every* geometry job has reached its public boundary (published cache generation or exported artifact). D04 sharpens this for a parallel geometry phase: higher-index success stays private until lower jobs reach the same public boundary; a failed speculative precompute must not change which serial error would have occurred, nor remove lower-index completed artifacts.

## 5. Sorted-publication guarantee today

- Simulation outputs: per-tile transactional publication happens **in dispatch order** (which is numeric-sorted), so on a fully successful run outputs appear in sorted order as a side effect of dispatch — there is no deferred global rename that publishes them in a sorted *ceremony*. A parallel adapter that publishes out-of-order would break this observable property unless it adopts D04's staged-prefix commit.
- `run_utci_tiles` returns per-tile results keyed in the numeric-sorted order (`api.py:151`); `execute_tiles` preserves this by construction (dispatch ascending, results collected per index).
- Preprocess phase publishes per-file as it goes in `os.listdir` order — the only phase with no ordering property to preserve.

## 6. Resume semantics (must survive adapter changes)

- Resume replays `_recover` from the last committed checkpoint generation, verifying `state_sha256` and band digests before continuing (`persistence.py:389-429`, verify at `:403`, `:334`).
- Completion detection is the completion manifest (written last, `:601`), so an interrupted `complete()` is always recoverable, never half-trusted.
- Failure JSON + done markers + stdout/stderr redirection per job (`runtime_worker.py:96-104`, `:88-93`) are the scheduler's only cross-process failure channel; `gc.collect()` per job (`runtime_worker.py:85`) is the per-tile memory-retirement rule D04 requires workers to honor.

## 7. Adapter checklist (distilled contract)

1. Numeric-tuple order (`api.py:151`) is the only ordering that is load-bearing for public results.
2. Per-tile transactionality (`persistence.py:268,342-361,540-595`) must wrap any parallel publication; journal-before-rename, manifest-last.
3. First failure (in numeric order among *started* jobs) controls the public exception; reaped children must not publish afterwards (today: `terminate=True`, `runtime.py:955-961`).
4. ResourceAdmissionError must keep its type identity across the process boundary (`runtime.py:618-660`) — an adapter adding a phase pool must reuse `_child_exception`, not plain pickling.
5. Barrier: all geometry public before any simulation admission (`api.py:208-210`).
6. `resume=False` must keep refusing incomplete transactions (`persistence.py:285-287`).
