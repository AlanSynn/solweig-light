# N8-30 review of N8-40 — integration of the policy-selected region dispatch

**Verdict: APPROVE-WITH-NOTES.** No blocking defects, no required repairs.
Five non-blocking recommendations (R1–R5), seven notes (N1–N7). Machine-readable
twin: `n8_30_review_n8_40_integration.json` (same directory, includes probe
transcripts).

Reviewer: independent N8-30 review service; the coordinator authored this diff,
this reviewer did not. Worktree `/Users/alansynn/Workspace/solweig-v8-native` @
base `16cdc56c` (`perf/native-optimization`), all work uncommitted. Tracked-diff
audit via `git diff src/`: exactly `pipeline.py` (+9), `cylinder_longwave.py`
(+20/-0: the `_lw_region_route` seam + guarded call site), plus the untracked
NEW `src/solweig_light/radiation/_lw_dispatch.py` and
`tests/optimization_v8/integration/test_lw_dispatch.py`. Nothing else tracked
changed.

## Rerun (this review, interpreter = worktree `.venv/bin/python`)

| Suite | Result |
|---|---|
| `tests/optimization_v8/integration/test_lw_dispatch.py -v -rs` | **9 passed, 0 skips** (1.85 s) — row C EXECUTED against the genuine staged generation `lw-g8-390acd5f57df1fe7` |
| `tests/optimization_v6/cylinder_lw/ -q` | **39 passed** (8.39 s) |
| `tests/optimization_v8/policy/test_legacy_env_parity.py -q` | **26 passed** (DX env-surface gate vs the new seam) |
| `tests/optimization_v8/region/ -q` | **153 passed** (current tree incl. the landed n8-14 repair; was 151 at the N8-14 review) |

No timed benchmarking; host loaded; pass/fail suites + untimed probes only.
Probe scripts and all fake trees live under `/tmp/n840_review/` — nothing in
the repository outside `evidence/reviews/` was written.

## Per-obligation

**A. Shipped-state inertness — PASS.** The seam import is function-local, so
importing `cylinder_longwave` does not even import `_lw_dispatch` (module level:
pathlib/sys/numpy only). The default `FULL_DIAGNOSTICS` demand returns the
untouched public full path (`cylinder_longwave.py:456-457`) and
`define_patch_characteristics_primary` has exactly one caller
(`Lcyl_v2022a_primary`, :443). Probe A executed in a fresh interpreter:
(A1) default-demand `Lcyl_v2022a_by_demand` — `seam_calls=[]`, zero machinery in
`sys.modules`, **zero sys.path growth**; (A2) shipped parallel
`Lcyl_v2022a_primary` — bitwise-identical (uint32) to the forced-legacy run on
fields 0/1 with `NOT_REQUESTED` singleton identity on 2..5 (the complete public
6-tuple), **no execution machinery imported**, selector resolves
`[absent] → row A`. Precision (N1/R1): the *selector* IS imported and run per
call in shipped row A (registry file read, repo state) — the docstring's
"without touching any of it" is true only of the execution machinery.

**B. Note-N6 discipline — PASS.** Three executed legs: (B1) through the REAL
qualified-row-C chain, a spy on `primary_aosoa` recorded `sh/vs/vb` float32
`(6,153,8)` C-contiguous and `sun/shade` bool — the 41-row tail arrived as 6
whole gangs; (B2) `produce()` genuinely emits raw uint32/bool (view applied only
in `consume`, `_lw_dispatch.py:210-212`); (B3) the entry's own admission rejects
the raw feed — `UnsupportedInput: sh: dtype uint32 != float32 (pass the producer
block as block.view(np.float32) …)` (`lw_native_aosoa.py:177-181`). A raw uint32
payload cannot be admitted, let alone silently misread.

**C. Decline-vs-fallback boundary — PASS.** The only `except` in the routed
path is `region_route`'s `except ImportError` around bootstrap+selector import
(`_lw_dispatch.py:111-115`) — strictly pre-selection. `execute_regions`
collects every `BaseException` and `_raise_first` re-raises the original object
type-intact; the driver chain has no try; the `[7,total]` buffer is a local of
`_execute_row`, discarded on raise — a normal return implies every block
started. Executed: (C1) sabotaged 3rd block → `RuntimeError` propagates out of
`Lcyl_v2022a_primary` annotated `first_failing_block=2, blocks_started=(0,1,2)`,
nothing returned; (C2) double failure → canonical lowest index, loud; (C4)
post-selection `OSError` propagates; (C3) the one real conflation is
pre-selection by construction: a *present-but-broken* selector module silently
resolves row A (N2/R2 — fail-safe direction, dies with N8-41 vendoring). The
N8-14 multi-failure corner affects which error is raised, never whether. Side
evidence: an injected record whose certified module is missing under the fake
root declines `[stale]` — the selector stays fail-closed at the integration
boundary too.

**D. Expert-env staging — PASS.** The seam (:194) uses the identical
`strip().lower()` normalization as the pre-existing `_lw_kernel` read (:214),
returns None before any policy import, so the selector's expert route is
unreachable from the dispatch flow (n840-6 as recorded). Executed: the
suite's expert-env test asserts `resolve_lw_backend` never runs and output stays
bitwise-equal for `native|ispc`; unknown `numba` value pins legacy; DX parity
gate green. Grep: `_lw_dispatch` reads no env; the LW variable is read at two
sites of the same frozen name in the same file; all other src env names
unchanged. Precision: "no second env-read site exists in src" is not literally
true — a second read *site* of the same var was added; what the frozen contract
pins (and the gate verifies) is the name surface.

**E. Bootstrap risk — PASS.** `_bootstrap()` is indeed reachable before
selection (every parallel lane-aligned call). Executed bounds: (E1) a copy of
`_lw_dispatch.py` served from a fake site-packages tree returns **None quietly
with zero sys.path growth** — shipped wheels untouched; (E2) post-bootstrap in a
repo, the resolvable names are the experiment module names, the `region` regular
package, and (verified by direct import) bare dir names as PEP 420 namespace
packages (`import policy` succeeds) — but append-only priority keeps installed
distributions winning (`numba` → site-packages). Existing src behavior cannot
change; the residual repo-only exposure is N3/R3.

**F. Memory/scope honesty — PASS; position: DEFER the scene-size guard to
record scope.** ~14·P bytes/pixel (P≤609 by the driver guard): **≈2.25 GB at
1024², ≈9.0 GB at 2048²** (P=153). Not a silent-failure channel: admission
precedes allocation (`direct_aosoa.py:259-264` — the dense-channel decline
allocates nothing), and MemoryError propagates loudly (obligation C). Deferred
because (1) no allocation site is reachable without a qualified record, which
requires N8-31/N8-32 + review; (2) a hardcoded pixel cap would embed an
unqualified policy constant in src, against the records-blind selector design;
(3) the real new hazard — allocation-triggered process death — is an envelope
property the first qualified record must state (**R5**). Not hedged: no src
guard now; the record-scope requirement is the follow-through.

**G. Test quality — PASS.** Non-vacuous: real 41-row tail observed reaching the
native entry as 6 gangs through the real chain; `_bitwise` covers exactly the
consumed contract (fields 0/1 uint32 + singleton identity on 2..5 = the full
public 6-tuple — this is not the vacuous-slice lesson; nothing consumed is
uncompared); declines use genuinely dense mats and `block_pixels=100`
(100%8≠0); row C ran here with zero skips; hygiene fixture resets policy and
pool state both ways. Minor (N5): internal diagnostic columns 2..6 of the routed
stack are unasserted — unconsumed by any caller and owned by the N8-13
seven-column parity suite.

**H. Pipeline teardown — PASS.** Containment executed: foreign `region` without
the attribute → ImportError caught (H1); with a `shutdown_all_pools` attribute →
**foreign code would execute per tile** (H2 — repo-gated, lowest-priority, and
removed by N8-41 vendoring; R3 suggests an explicit dispatch-owned entry point
when vendoring); row-A repo tile: the teardown import itself loads
`region.region_pool` (H3) — the comment "No-op unless this process dispatched a
region route" is true of the shutdown call, not the import. Cost per tile: one
cached import + a dict scan; pool threads are daemon, so this is hygiene, not
hang prevention (consistent with n840-1).

## Notes and recommendations

| id | finding | action |
|----|---------|--------|
| N1 | Shipped row A imports/runs the selector (per-call registry read, repo state); "no machinery touched" wording overstates | **R1**: soften docstring/record at next touch or N8-41 |
| N2 | Present-but-broken selector == absent tree → silent row A (probe C3) | **R2**: acceptable (pre-selection, fail-safe); N8-41 vendoring removes |
| N3 | Repo-only name surface: namespace importability of generic names; H2 foreign-`region` teardown hazard | **R3**: N8-41 vendor; give teardown an explicit entry point then |
| N4 | Stale state: test comment "n8-14 repair pending" and the record's found_defect disposition predate the landed repair (`region_pool.py:568/:836/:864-866`; region suite 151→153) | **R4**: wording update at next touch; assertions remain valid |
| N5 | Routed diagnostic columns 2..6 unasserted | informational; contract-bounded |
| N6 | ~2.25 GB (1024²) / ~9 GB (2048²) whole-scene state; MemoryError loud; dense decline allocates nothing | **R5**: first qualified record must state the scene-size envelope; no src guard now (defended) |
| N7 | Per-call registry file read in repo state (wheels never reach it) | flag for N8-31 throughput fairness; consider caching at N8-41 |

## Stale-review notice handling (post-notice addendum)

Team-lead notified mid-review that `region_pool.py` changed (the n8-14 repair)
and that a test-only conftest fix might land in two region test files. No
re-review was needed: this reviewer had independently detected the repair during
the review (the file's 18:38:11 mtime predates every region_pool.py read here),
so all cited pool facts and ALL obligation-C executed evidence were already
taken from the repaired file; the semantics-unchanged claim (cancellation order,
error object identity/type, `_POOLS` keying, budget cap) is verified on it.
Post-notice audit: `region_pool.py` byte-identical (still 18:38:11); the
18:47:05 delta is exactly the pre-declared test-only conftest fix
(`from region_test_helpers import LW_TEST_THREADS` replacing the bare conftest
import in `test_region_composition.py` / `test_region_consumers.py`; outside
the A-H scope). Re-certification on the exact current tree: integration
**9 passed** (2.62 s), region **153 passed** (34.11 s). Verdict unchanged.

**Scope guard:** nothing outside
`optimization_v8_native_default/evidence/reviews/` written in the repository; no
network; no commits; no timed benchmarking.
