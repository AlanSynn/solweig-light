# N8-30 review of N8-21 — trusted installed-artifact loader

**Verdict: APPROVE-WITH-NOTES (delta recheck: N1 REPAIRED and independently
re-verified — see section 9).** No blocking defects. The original required
repair N1 is closed loader-side; remaining notes are non-blocking and
routed. Machine-readable twin: `n8_30_review_n8_21_artifacts.json` (same
directory).

Reviewer: independent N8-30 review service; did not author N8-21.
Scope guard: nothing outside `optimization_v8_native_default/evidence/reviews/`
was written (all reviewer probes ran against /tmp mirrors); no network; no
commits. Repo at `16cdc56c` (`perf/native-optimization`, worktree
`/Users/alansynn/Workspace/solweig-v8-native`).

## 1. Contract fidelity (BUILD_DESIGN §8) — PASS

* **8.1 package resources only**: resolution is
  `importlib.resources.files(package)` → `backends/native_generated/`
  (`installed_loader.py:228-244`, `:545-551`); zero `os.environ` in the module
  (source-asserted `test:316-317`; my grep agrees); the legacy dev cache is
  *positively* rejected even for a fully valid tree (`:557-562`,
  `test:677-699`). Containment is enforced at four levels — member
  (lexical absolute/`..`/NUL/backslash-root at `:264-269` + realpath at
  `:271-274`, applied at `:383-393` **before any open/hash**, proven by the
  `read_opens`/`hashed` assertions in `test:588-661`), the manifest itself
  (`:365-373`), generation dirs (`:583-589`), and the native root
  (`:552-556`). This discharges N8-30 review note N5 against N8-10.
  "User/cache-writable location" is implemented as dev-cache rejection +
  containment rather than a writability probe — the correct reading (a probe
  would reject legitimate `pip install --user` trees).
* **8.2 never compiles/downloads/writes**: no print/subprocess/tempfile/
  mkdir/shutil/socket anywhere in the module (grep); the hardened IoSpy
  (`test:179-281` — patches `builtins.open` **and** `io.open` **and**
  `os.open` plus fs-mutation/spawn/socket sinks, also discharging prior
  note N1's pathlib blind spot for this suite) proves zero writes/subprocess/
  network on the absent, env-set, source-no-native, qualified, and all 13
  corrupt-mutation paths. The default path never hashes the packaged
  `.ispc`: `verify_generation` hashes only manifest-listed generation
  members (header/asm/dylib).
* **8.3 gates before dlopen, in order**: `_gate_candidate`
  (`:359-468`) runs containment → manifest parse → member containment →
  build-mode gate → **reused** `build_native.verify_generation` (schema,
  generation-name derivation, hashes, sizes, Mach-O structural walk, FMA
  re-audit — zero re-implementation; no hashlib import in the loader) →
  ABI (abi_version, wrapper ABI, `python_c_api is False`, exact
  exported-symbol set, package name, `:413-436`) → math-profile allow-list
  (`:438-446`) → target/gang + dylib-name presence (`:448-459`) → host
  capability (arch/machine/os/minOS + `sysctlbyname` NEON probe — never
  `platform.machine()` alone; unrecognized requirements fail closed,
  `:316-351`). Verified once per (pid, workflow generation, root).
* **8.4 absent vs corrupt**: absent / `source-no-native` / unqualified host →
  quiet auto decline with the reason recorded privately; corrupt → recorded
  decline + loud `CorruptNativeArtifact` naming the packaging defect and
  carrying the recorded reason (asserted `test:548-559`); unqualified → quiet
  auto + loud `UnsupportedNativeISA` with the capability gap. Wordings match
  the SOURCE_FALLBACK.md table exactly.
* **8.5 expert path separation**: `builder_spy` (`test:149-176`) proves
  `_cache_dir`/`_kernel_digest`/`_build_needed`/`_build`/`_ensure_loaded`/
  `native_longwave_primary`/`expert_build` are never entered on any auto
  path.

## 2. The `prepare_native_handle()` bypass — PASS, no weakened guarantee

The deviation is real and justified: `prepare_native_handle`'s admission
demands the legacy `build_stamp.json` layout and hashes the packaged kernel
source (`native_handle.py:283-302`), both forbidden on the default path by
BUILD_DESIGN 8.2. The loader replaces **admission only** and reuses lifetime
wholesale: `_load_entries` (eager argtypes/restype binding), the
`NativeHandle` class (pid pinning, `execute`, no dlclose), `_dir_lock`, the
shared workflow-generation clock, and the error taxonomy (re-exported, never
redefined). Comparing guarantee-by-guarantee:

* **PID**: handle `_pid` from `native_handle._getpid()` at instantiate
  (`:499`); `execute` re-resolves at call time. My **real `os.fork` probe**:
  the child raised `StaleNativeHandle` on the parent handle, `auto_load` in
  the child minted a *fresh* CDLL under its own pid (keys embed pid) with
  bitwise-identical output, and the parent handle kept executing. Identical
  to N8-10 semantics.
* **Generation bump**: all loader caches key on wgen; `new_workflow_generation`
  clears `native_handle._NEG_CACHE` and makes the loader's keys unreachable
  (tests `:355-371`, `:450-460`, `:562-580`). Cosmetic only: `_instantiate`
  re-reads `current_workflow_generation()` instead of the entry-captured wgen
  — a mid-attempt bump can duplicate a handle, never reuse a stale one.
* **Lock ordering**: gate/hashing outside the dir lock, then lock → recheck
  **both** caches (`:618` — strictly better than `prepare`, whose in-lock
  recheck skipped `_NEG_CACHE`, prior note N3) → instantiate → publish inside
  the lock (`:634-635`). No in-process writer to the installed tree exists
  (auto never writes; `expert_build` is dev-cache-scoped), so outside-lock
  gating cannot observe half-published state.
* **TOCTOU (verify → dlopen)**: the window exists (`:590` verify vs `:480`
  dlopen) but is **equal in kind** to `prepare_native_handle`'s
  (`native_handle.py:580-583` hashes then CDLLs under a process-local lock
  that no external writer honors). The trust root is the package manager
  (ARCHITECTURE.md: "SHA checks provide content integrity, not
  authenticity"). Not a weakening. The extra `_verified_manifest` re-read
  (`:639-643`) can raise non-taxonomy exceptions (KeyError/OSError) only
  under concurrent external mutation mid-load — folded into N1's repair.
* **Registry publication**: installed outcomes live in the loader's own
  registry; nothing consults `native_handle._REGISTRY` for the installed
  tree, and the key spaces are disjoint (no shadowing either direction).

## 3. Trust chain end-to-end — PASS (notes N3/N4)

* **(a) unverified code**: not loadable short of an external mid-load swap —
  the dlopen target is exactly the manifest-listed, hash-verified path
  (gate `:455-459` + `verify_generation` `build_native.py:607-613`);
  nothing unlisted is ever opened.
* **(b) containment**: lexical + realpath at member/generation/root levels;
  a symlinked member resolving *inside* the generation hashes and dlopens
  the same bytes; the dev cache is rejected even when the tree is valid.
* **(c) ISA lying**: unrecognized requirement strings fail closed
  (`:348-350`); the arm64/machine/minOS domain gates are loader-side
  constants, so an empty or lying requirements list cannot escape the
  qualified domain (my probe: empty `requirements` loads on arm64 — within
  domain; see N3).
* **(d) sibling poisoning**: every candidate is gated (`:577-597`); my probe
  and `test:773-789` confirm a corrupt sibling is *recorded* while the
  qualified generation loads; a crafted sibling cannot suppress it.

**Mutation teeth, three adversarial picks** (would the test fail if the
check were deleted?):

1. `truncated-dylib-fixed-manifest-macho-catch` — the mutation recomputes
   hash/size/name consistently, so only the Mach-O walk (or the dlopen
   failure, with a *different* message) can catch it; deleting
   `macho_structure_error` fails the keyword assertion. Real teeth.
2. `math-profile-fast` — `validate_manifest` accepts any non-empty id, so
   the loader's `QUALIFIED_MATH_PROFILES` gate is the *only* defense;
   deleting it executes a fast-math dylib and the test fails. Real teeth,
   loader-unique.
3. `abi-version-mismatch` — *shared* teeth: `validate_manifest`
   independently rejects `abi_version != 1` with a message containing the
   keyword, so deleting only the loader's gate would still pass the test.
   Acceptable today because the loader's expectations ARE the imported
   builder constants (the declared single-source-of-truth design); see N4.

The containment mutations additionally assert the escaped file was never
opened or hashed — deleting `_member_escape_reason` would load the escaped
file and fail the `is None` expectation.

## 4. Decline semantics — PASS WITH NOTES (crash class, N1)

Wording split, recorded-reason-in-raised-message, spy-proven silence
(`capfd` empty + IoSpy + builder_spy), and no-fallback-after-failure all
hold. **Defect N1**: three exotic present-but-corrupt inputs *crash*
`auto_load` with a raw exception instead of quietly declining (all my
empirical probes against /tmp mirrors):

| input | escaping exception | origin |
|---|---|---|
| listed member unreadable (mode 000), manifest readable | `PermissionError` | `_sha256_file` inside `verify_generation`; `_gate_candidate` catches only `VerifyFailure` (`installed_loader.py:407-410`) |
| `artifacts`/`generated_sources` entries are strings | `AttributeError` | `entry.get(...)` in `build_native.py:442-444`/`489-495` |
| `fma_audit.passed: true` without `asm_sha256` | `KeyError` | `build_native.py:632` |

All three are fail-closed (unverified bytes never execute) and unreachable
from builder-emitted artifacts, but they violate §8.4's "auto declines to
Numba" for corrupt states. **Required repair before N8-41 wheel
integration** (not blocking this approval): broaden the except at
`installed_loader.py:407-410` to map the corruption-signal set
(OSError/AttributeError/KeyError/ValueError/TypeError) to `_corrupt`,
and/or harden `build_native.validate_manifest`/`verify_generation` with
isinstance/subfield checks (N8-20 coordination; the root cause lives there).

## 5. Verify-once — PASS

Second load: zero re-hash and no re-dlopen (`hash_spy` second == `[]`,
same handle object; `test:439-447`). Workflow bump re-verifies and mints a
fresh handle (`:450-460`); absent/corrupt declines cached per
(pid, wgen, root) (`:355-371`, `:562-580`). Cache growth is one entry per
(pid, wgen, package, root) — unbounded across generations in a long-lived
process, the same carried edge as N8-10 note N4 (→ N8-14 scope);
`_DECLINE_LOG` is bounded at 32 (`:126`, `:191-193`).

## 6. Ownership — PASS (scope note N2)

`git diff HEAD` empty (zero tracked files touched). Footprint = **5 files**:
`installed_loader.py` + `linked_image_fma_scan.json` under
`experiments/optimization_v8/artifacts/` (N8-21's owned_scope), and
`conftest.py` + `test_installed_loader.py` + `test_linked_image_scan.py`
under `tests/optimization_v8/artifacts/` (listed in no task's owned_scope —
config omission, no trespass). The linked-image-scan pair was added after
review dispatch (the handoff counts 42/208/1698 predate it); the CURRENT
tree is what I reviewed and reran: 44 / 210 / 1700, all green. It
discharges N8-20 review note N2 — disposition assessed in section 8 below.
The staged-original integrity assertion is real (session digests captured
before any test; `test:806-810` re-hashes and compares), and I independently
verified the staged generation (`build_native.py verify` → PASS; dylib
sha256 `eb1071fc…2582b46a`, byte-for-byte the §9 record).

## 7. Reruns — PASS (claim counts off by the 2 unmentioned tests)

| command | result |
|---|---|
| artifacts+loader+packaging (`-p no:cacheprovider -q`) | **210 passed** in 8.70s (claim 208; delta = the 2 linked-image-scan tests). artifacts 44 (42+2), loader 122, packaging 44 |
| full `tests/optimization_v8/` tree | **1700 passed**, 1 pre-existing warning, 12.98s (claim 1698; same +2). No cross-suite interference |
| staged-absent mirror run of `test_installed_loader.py -q -rs` | **5 passed + 37 `[no-staged-artifact]` skips** — exactly as claimed |

## Notes

| id | where | summary |
|---|---|---|
| N1 | `installed_loader.py:407-410` | **REPAIRED and re-verified** (section 9): `_VALIDATOR_FAILURE_SIGNALS` clause maps the corruption-signal set to recorded declined-corrupt with the class named; build_native-side isinstance hardening still routed to N8-41 |
| N2 | handoff + TASKS_CLAUDE.yaml | handoff counts 42/208/1698 predate the post-dispatch scan pair; current tree verified 44/210/1700; `tests/optimization_v8/artifacts/` missing from N8-21 owned_scope |
| N6 | — | superseded by section 8: disposition of N8-20 note N2 assessed SOUND; admission-only divergence verified concretely |
| N3 | `:339-350` | empty `requirements` loads within the arm64 domain (lying by omission); consider positively requiring the expected cpu-feature strings |
| N4 | `:413-423`, `:496` | ABI mutations share teeth with `validate_manifest` (same imported constants — by design); stamp's `dylib_sha256` assumes `artifacts[0]` is the dylib (cosmetic for hypothetical multi-artifact wheels) |
| N5 | `:85-91` | sys.path sibling bootstrapping is experiment-stage only — N8-41 must vendor under the package; carried: per-generation cache growth (N8-14), verify→dlopen external-mutation window equal to N8-10's (package-manager trust root) |
| N6 | `installed_loader.py:639-662` | the in-lock conversion clause has no regression test; "would require racing verify→dlopen" is overstated — the reviewer exercised it deterministically by patching the `_verified_manifest` seam (quiet `declined-corrupt` naming KeyError + loud explicit); add the ~6-line test at next touch |
| N7 | `n8_21_review_notes_disposition.json` | `N2_handoff_count_note.disposition` says "47/211/1703", inconsistent with its own counts block (213 combined; full tree is a moving target mid-wave) — cosmetic author-side fix |

## 8. Follow-up verification (post-dispatch state, reviewer probes)

**Admission-only divergence — VERIFIED, not trusted.** (1) No copy-drift:
grep finds no `def execute`, no `NativeHandle` subclass/redefinition, no
`setattr`, no prototype code in `installed_loader.py` (the lone `argtypes`
is the sysctlbyname host probe); empirically, an `auto_load` handle satisfies
`type(h) is native_handle.NativeHandle` and
`type(h).execute is native_handle.NativeHandle.execute` (the reviewed class
attribute, no override), both entries are eagerly argtypes-bound to the
reviewed `lw_native._PROTO` (f32 surface scalars pinned to `c_float`,
restypes `None`), pid is pinned, and the stamp is tagged
`installed-native_generated-v1`. (2) The bypass is NECESSARY, not
convenient: I called `prepare_native_handle(artifact_dir=<staged
generation>)` myself — it raises `CorruptNativeArtifact`
("build_stamp.json missing: dylib present but its kernel binding is
unverifiable"), and even with a stamp present it would hash the packaged
`.ispc`, which BUILD_DESIGN 8.2 forbids on the default path. (3) TOCTOU
fail-safety: the CDLL is opened on the SAME resolved path that was
hash-verified (`cand_real` → `_load_entries(str(gen_real))` →
`<verified dir>/liblw_native_g{gang}.dylib`, the manifest-listed member);
no post-open re-check exists (a post-open hash would be meaningless —
pages are already mapped). Simulating an external writer inside the
verify→dlopen window (swap after `verify_generation` passes): the mutated
image **cannot execute — dyld's arm64 code-signature validation SIGKILLs
the process at dlopen** (my probe, exit 137). A post-load mutation is
caught at the NEXT workflow generation (my probe: `declined-corrupt`,
hash mismatch). Residual exposure — a validly-signed replacement image
landing in the window — is exactly `prepare_native_handle`'s exposure and
sits beyond the package-manager trust root. Verdict: equal-or-stronger
fail-safety than the code it bypassed.

**N8-20 note N2 disposition (runtime linked-image FMA scan declined;
build-side evidence adopted) — SOUND.** The recorded evidence
(`linked_image_fma_scan.json`: 0 hits over 7406 `otool -tV` instruction
lines of the final staged dylib, sha256-pinned to the generation) carries a
positive control, which I independently reproduced: clang
`-ffp-contract=fast` on `a*b+c` → the reviewed regex flags `fmadd`
(passed=False); `-ffp-contract=off` on the same source → 0 hits — the zero
is not vacuous, and `test_linked_image_scan.py` pins the regex sensitivity
synthetically plus a >1000-instruction-lines non-vacuity guard. On the
merits: a runtime scan adds nothing against post-publication mutation (the
sha256 content gate already fails it — and mutated images cannot even load,
above); its unique value — catching builder-side divergence between the
`.s` re-emission and the linked image — is a build-machine property fixed
at publication, so the scan is needed exactly once, where tools are
guaranteed present (build_native verify / N8-41). Meanwhile a runtime scan
would violate §8.2's no-subprocess-at-load line outright and, since
`/usr/bin/otool` is an xcrun shim, convert clean-CLT hosts (ordinary
supported state) into declines. The runtime scan is belt-and-suspenders
whose value is realized at build time; it is NOT necessary for runtime
trust. Disposition recorded as sound.

## 9. Delta recheck — N1 repair (reviewer verification)

Scope: the repair diff only, current tree (line numbers shifted; the
original findings above are unchanged as history).

* **Diff region read**: `_VALIDATOR_FAILURE_SIGNALS = (OSError,
  AttributeError, KeyError, ValueError, TypeError)` at
  `installed_loader.py:133-134` — deliberately NOT bare `Exception`, so
  non-signal loader bugs (NameError-class) still crash loudly; a typed
  comment documents each mapping. Clause (1) in `_gate_candidate`
  (`:417-428`) converts the signal set to `_corrupt` with the failure
  class named in both the recorded reason and the raised
  `CorruptNativeArtifact`. Clause (2) in `attempt_load`'s in-lock block
  (`:639-662`) wraps `_verified_manifest` + `_instantiate` and converts
  the same set to a recorded `declined-corrupt` outcome whose error
  message names the class. `build_native.py` untouched (917 lines; the
  `:632` KeyError site unchanged); `git diff HEAD` empty.
* **Reruns**: `tests/optimization_v8/artifacts` = **47 passed** (44+3);
  artifacts+loader+packaging = **213 passed** (my verified 210 baseline + 3;
  the 208/211 figures derived from the stale pre-scan-pair handoff counts).
  Full tree (for the record): 1948 passed, 6 skipped, **1 failed** —
  `installed/test_installed_wheel_gates.py::test_surface_gate_recorded`, a
  teammate file that never imports `installed_loader` and passes standalone
  (7/7): the known order-dependent teammate flake the author also observed
  (their failure counts varied 125→13→8 across identical reruns), not a
  repair regression and not in this review's scope.
* **Teeth independently confirmed**: in a /tmp mirror with ONLY the clause
  neutralized (tuple → `()`), the 3 new regressions fail exactly as I
  originally observed — raw `PermissionError`/`AttributeError`/`KeyError`
  propagate out of `auto_load`, the KeyError traceback pinned at
  `build_native.py:632`; clause intact → 47/47 green. The tests run through
  the shared CORRUPT_CASES template, so each also asserts quiet auto
  (capfd empty, builder_spy empty, IoSpy pure) + loud explicit
  ('packaging defect' + class name) — the quiet/loud split is preserved by
  construction and by run.
* **In-lock clause verified AND deterministically testable**: the author's
  "no deterministic test — racing verify→dlopen required" is overstated. I
  exercised clause (2) without any race by patching the
  `installed_loader._verified_manifest` seam to raise `KeyError` (the
  consequence of a mid-load manifest swap): auto → quiet `None` with
  `declined-corrupt` "validation raised an untyped validator failure
  (KeyError)"; explicit → `CorruptNativeArtifact` carrying 'packaging
  defect' and the class name. Behavior correct; a ~6-line regression test
  is feasible at the seam (note N6).
* **Residual (accepted)**: `IndexError` (e.g. `artifacts[0]` on a mid-load
  swapped manifest that keeps a valid target but empties artifacts) is
  deliberately outside the signal set — unreachable from builder-emitted
  artifacts and outside the mid-load external-mutation model; consistent
  with the repair's typed-crash philosophy.
* **Disposition record**
  (`experiments/optimization_v8/artifacts/n8_21_review_notes_disposition.json`)
  is accurate on every claim I could check, with one cosmetic
  self-inconsistency (N7: "47/211/1703" in the N2 note vs its own 213).

**Final verdict: APPROVE-WITH-NOTES.** N1 closed loader-side and verified;
N2–N5 stand as recorded (routed to N8-41 where applicable); N6/N7 are
new non-blocking notes from this delta.

## 10. Addendum — delta #2 (decline-log gap + N6 seam test; N8-21 closure)

The author's N6 work exposed a real gap this review missed: in-lock
declines (the N1 clause AND the pre-existing `NativeHandleError` branch)
were published to `_REGISTRY` but never reached the private decline log —
`decline_reasons()` recorded nothing for them. Fix: `attempt_load` calls
`_record(loaded, key)` for a non-LOADED in-lock outcome after publication
(`installed_loader.py:671-676`); `_record`'s cache guard sees the
`_REGISTRY` entry and only appends the diagnostic line.

Reviewer verification (all by probe):

* **Verify-once preserved**: first `auto_load` on an in-lock-declined key
  performs the 4 content hashes once; two cached repeats add **zero**
  hashes and the decline log stays at **exactly 1 line** (outcome served
  from `_REGISTRY`; append-only, no repeat spam, no double caching). The
  LOADED path still never calls `_record`.
* **N6 seam test valid and non-vacuous**: it is the deterministic
  `_verified_manifest` seam patch this review prescribed, and its
  `assert_quiet_decline` makes the `_record` delta load-bearing — in a
  mirror with ONLY the `_record(loaded, key)` line stripped, the quiet
  decline still happens but the test fails at
  `test_installed_loader.py:294` ("no [declined-corrupt] decline
  recorded"), i.e. it pins the logging delta specifically, while stripping
  the in-lock clause fails it earlier with the raw KeyError (established
  in section 9). Teeth in both directions.
* **Reruns**: artifacts = **48 passed**; combined = **214 passed**; policy
  (consumer of `installed_loader`) = **84 passed**; `git diff HEAD` empty.

**Closing verdict (final): APPROVE-WITH-NOTES.** N1 repaired and verified
(delta #1); the decline-log gap repaired and verified (delta #2); N6
discharged by the seam test; N2–N5 and N7 stand as recorded (routed where
applicable). No open items on this reviewer's side. N8-21 may close.
