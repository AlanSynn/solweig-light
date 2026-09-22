# N8-30 review of N8-10 — workflow-owned native handle

**Verdict: APPROVE-WITH-NOTES.** No blocking defects, no required repairs.
Machine-readable twin: `n8_30_review_n8_10_loader.json` (same directory).

Reviewer: independent N8-30 review service; did not author N8-10.
Scope guard: nothing outside `optimization_v8_native_default/evidence/reviews/`
was written; no network; no commits. Repo at `16cdc56c`
(`perf/native-optimization`, worktree `/Users/alansynn/Workspace/solweig-v8-native`).

## 1. IO-freedom claim — PASS

The spy is armed only around `execute()` (`test_native_handle.py:163-176`) and
— the strongest form — there is **no warmup execute before arming**: the first
f64 call, first f32 call, first caller-out call and each first bundle-shape
all occur under the armed spy (150 executes; entry counters match the tally
exactly). Every op class the old per-call path performed
(`native_lw.py:49-115`: mkdir, dylib/stamp exists, stamp read + json.loads,
kernel read_bytes, sha256, CDLL, which, subprocess) has at least one spied
chokepoint; `Path.exists`/`is_file`/`os.path.exists` route through `os.stat`
at call time on py3.12 (empirically probed). Lazy-init audit: `execute()`
(`native_handle.py:412-518`) and every helper it calls are pure numpy
introspection/pointer arithmetic; both entries **and their argtypes are bound
eagerly at prepare** (`native_handle.py:538-547`), so no ctypes/dlopen init
can fire on first call, first spec, first caller-out, or B=0 (np.zeros only,
no-C-entry proven at `test:180-185`).

One honest gap (note N1): pathlib file reads go through `io.open`, which
patching `builtins.open` does **not** intercept (probed: counts stayed `{}`);
`os.scandir`/C-level opens are likewise unspied. Not blocking — the chokepoint
argument covers the old path's op classes, and the structural read shows
`execute()` contains no IO of any kind. Harden the spy at next touch.

## 2. Guard-for-guard fidelity — PASS

Line-by-line diff of `execute()` vs `lw_native.primary()`
(`lw_native.py:169-219` vs `native_handle.py:428-488`): the rejection set and
order are identical — sh dtype/ndim; P 1..609; B<0; B==0 zeros((0,7)) before
any pointer; vs/vb shape+contig; sun/shade; solid/sine/cosine; solar_gate
stride-1; sky columns any-stride; directions/gate shape-only (never read);
lup; scalar-spec equality incl. unsupported provenance; reflection spec; out
(B,7) contig + byte-extent alias rejection over **all 14** array inputs. Same
`UnsupportedInput` class throughout, so the real dispatcher's fallback
decision (`cylinder_longwave.py:198-204`, catches exactly `UnsupportedInput`)
is unchanged. The entry-call argument order is byte-identical to shipped.

The one addition — `out.flags.writeable` rejection
(`native_handle.py:473-477`) — is dossier-mandated (dossier 01: writable,
sized, nonoverlapping before native writes); it converts the shipped path's
silent C-writes-into-read-only-pages into a pre-launch decline. Sanctioned
non-input divergences only: post-launch failures wrapped
`NativeExecutionError` (contract §3 "post-launch failures propagate" — loud,
never caught by `_dispatch`, proven at `test:244-257`); pid-first
`StaleNativeHandle`; gang/ISA moved to prepare-time `UnsupportedNativeISA`
(capability vs input separation per ARCHITECTURE). No missing input check.

## 3. Error taxonomy — PASS

Five sibling subclasses of `NativeHandleError(RuntimeError)`
(`native_handle.py:114-144`), none is or subclasses `UnsupportedInput`
(asserted `test:420-427`; note N2: the pairwise assertion uses `is not` —
weaker than `issubname` both ways, though the source shows direct siblings).
Auto-decline vs expert-loud wording present in Missing and Corrupt messages
and asserted (`test:377`). Missing artifact never builds: prepare calls only
`_validate_artifact` + `_load_entries`; the only subprocess lives in
`expert_build`, referenced by no prepare path; zero subprocess on the miss
and zero IO on a cached retry proven (`test:439-448`).

## 4. Lifetime/concurrency — PASS

- **PID**: `execute()` resolves the module-global `_getpid` at call time.
  Beyond the author's pid-injection test I ran a **real `os.fork` probe**:
  the child raised `StaleNativeHandle` on the parent handle, re-prepared a
  fresh CDLL under its own pid (registry key includes pid,
  `native_handle.py:525-529`), and reproduced the parent's output bitwise.
- **Generation**: bump mints a token and clears `_NEG_CACHE`
  (`native_handle.py:181-189`); a running workflow keeps its handle
  (`test:313-323`); neg-cache is per (pid, generation, key), cannot shadow a
  different dir (`test:457-464`).
- **Double-checked locking**: closed by construction, not luck — same-key
  prepares serialize on the per-directory lock; the winner publishes under
  `_REGISTRY_LOCK` *inside* the dir lock; the loser's recheck necessarily
  sees the published handle. The 20 ms-slowed sha256 widens the window so 8
  threads genuinely contend; correctness rests on lock ordering under any
  schedule. `expert_build` publishes under the same lock, atomic renames,
  stamp LAST (`native_handle.py:642-670`; ordering proven without ispc at
  `test:559-599`).
- **No dlclose** anywhere; CDLL owner held for process life; `lw_native`
  globals never assigned (grep: NONE; pinned by `test:467-474`).
- Carried edges (note N4): fork-while-lock-held deadlock risk and unbounded
  per-generation registry growth belong to N8-14's pool/fork policy.

## 5. Bitwise parity — PASS (rerun)

`pytest tests/optimization_v8/loader/ -q` → **122 passed, 0 skipped** (real
dylibs validated through the loader's own gate; the real-ispc expert_build
test ran). With the reference suite: **234 passed** — exactly the claim.
`--collect-only` confirms **96** parametrized cases of the grid test
(6 B × 8 P × 2 surface profiles); conftest imports the frozen N8-04
constructor **read-only** via importlib (`conftest:40-45`); comparison is
uint32-view against **both** the oracle and the shipped
`native_lw.native_longwave_primary` (`test:498-503`), plus stride-12 /
one-element / negative-stride sky columns, P=609, B=0, caller-out bitwise.
Carried N8-04 note N7: 0-d ndarray `reflection_factor` still not positively
exercised (same helper as shipped — no new exposure; pin at N8-13).

## 6. Timings labelling — PASS WITH NOTES

The bench self-labels: synthetic leaf-level docstring, loadavg at start/end,
explicit shared-host ambient note (`bench:81,177-179`). The 2.25x figure is
printed as a leaf A/H speedup; the island extrapolation **cites** n8_02's
1.62x counterfactual instead of replacing it (`bench:160-169`) — consistent
with BENCHMARK_PROTOCOL (leaf kernel: "no claim of application gain"). The
b1024 H>Anomaly is reported raw and deferred to N8-13's quiet window —
matching the protocol's "delay or mark uncertainty" and the dossier's "do
not launch a new 1024 campaign merely to resolve a microsecond result".
Arithmetic internally consistent (C0−H=94.3 µs; A/H=2.247). Note N6: the
numbers live only in the handover message — archive the bench stdout before
the quiet-window rerun so the deferred question has a durable baseline.

## 7. Ownership — PASS

`git diff HEAD --stat` empty (zero tracked files touched; src/ untouched);
only untracked additions. N8-10's footprint matches its `owned_scope` in
TASKS_CLAUDE.yaml exactly: `experiments/optimization_v8/loader/` +
`tests/optimization_v8/loader/`. Sibling untracked dirs belong to parallel
wave-1 tasks (N8-11/N8-20/N8-23/N8-04).

## Notes (fix at next touch; none blocking)

| id | where | summary |
|---|---|---|
| N1 | `test_native_handle.py:63-99` | IoSpy blind spots: pathlib `io.open`, `os.scandir`, C-level opens — add to `_TARGETS` |
| N2 | `test_native_handle.py:421-427` | pairwise-distinct assertion is `is not`, not mutual-non-`issubclass` |
| N3 | `native_handle.py:575-587` | in-lock recheck skips `_NEG_CACHE` → redundant re-validation in a narrow race (correctness unaffected) |
| N4 | registry / fork policy | fork-while-locked deadlock edge + per-generation registry growth → N8-14 scope |
| N5 | `native_handle.py:305-328` | manifest `files` non-dict passes; member paths uncontained before hashing → N8-21 containment gate |
| N6 | `bench_leaf_compare.py` | archive ambient-labelled bench stdout as evidence for the deferred b1024 question |
| N7 | reflection provenance | 0-d f32 ndarray still unpinned (carried N8-04 note) → pin at N8-13 |
