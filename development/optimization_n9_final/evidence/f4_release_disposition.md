# F4 release disposition: F3-informed CPU-only closure (audit + plan)

Supersedes the contingency sections of `f1r_cpu_only_plan.md` (which assumed a
pure dormant-machinery removal). Basis: F3 TERMINAL NATIVE_LOSS
(`f3_verdict.json` @ 3f0e4699; `f3_continuous_timed_20260923T144131Z.json`),
continuous cells (median ms, B1 = stream row B, budget 1):

| cell | A8 | B1 | B4 | B1/A8 | note |
|---|---:|---:|---:|---:|---|
| 1024 binary | 4.827 | 2.323 | 2.451 | 2.08x win | primary |
| 1024 mix | 4.024 | 3.055 | 3.094 | 1.32x win | primary |
| 1024 raw | 1.762 | 1.889 | 2.046 | 0.93x LOSS | the guard class |
| 128 binary | 1.344 | 1.094 | 1.169 | 1.23x win | DEFAULT block_pixels=128 (runtime.py:325) |
| 128 mix | 1.202 | 1.150 | 1.295 | 1.04x win (marginal) | |
| 128 raw | 0.945 | 1.071 | 1.089 | 0.88x LOSS | the guard class |

B1 dominates B4 in all 6 cells. Native C fails gate 2 (B4/C4 geomean 0.999).
The default block size is 128, so the shipped default path wins 2 of 3
visibility classes and the raw guard removes exactly the measured loss class.

## 0. Audit verdict on the integrator's five-element shape

| element | verdict |
|---|---|
| 1. stream-B default + structural raw guard | CORRECT with 3 refinements (guard placement, env-read wording, H pinning) — see A1 |
| 2. aplus decode integrated into legacy | CORRECT but imprecise about scope — see A2 |
| 3. removals + "restore plain boolean" | registry/selector removal CORRECT; shutdown consult: KEEP; **tri-state restoration: REJECT (contradicts element 1)** — see A3 |
| 4. preserve list | CORRECT, with additions — see A4 |
| 5. test disposition | CORRECT, made specific in §3 |

### A1. Element 1 refinements

- **Guard placement**: the raw guard belongs in `plan_invocation`
  (`src/solweig_light/_native_dispatch/lw_stream.py:229-305`), PRE-launch,
  after the descriptors are pinned. The modes arrays are already in hand:
  `BorrowedVisibility` holds `(payloads, modes)` per channel from
  `visibility_compiled._descriptor` (lw_stream.py:273-276), and the encoding
  is `{'binary': 1, 'ternary': 2, 'raw': 4}`
  (`visibility_compiled.py:98`). Decline iff
  `all(np.all(modes_ch == 4) for ch in (sh, vs, vb))` — O(P), no payload
  touch. Decline returns None before any launch, so the caller's legacy loop
  produces bitwise-identical output by construction and no mid-stream decline
  can exist (the frozen plan contract, lw_stream.py:59-61). Guard is
  channel-level only; classification/`solar_gate` are orthogonal.
- **"No env read in this route" is wrong as stated.** The expert stand-down at
  `cylinder_longwave.py:194` (`SOLWEIG_LIGHT_LW_BACKEND in (native, ispc)` ->
  return None) MUST STAY: it is what keeps B7-32 expert forcing owning the
  call instead of being silently overridden by the new default row. Removing
  it violates MERGE_SCOPE ("No surprise removal of an already offered
  override"). Correct statement: the route's ACTIVATION reads no env and no
  registry; the one pre-existing expert stand-down read remains, so the
  package env-read surface is unchanged (still exactly the frozen
  `SOLWEIG_LIGHT_LW_BACKEND`, read at :194 and :214).
- **H must be PINNED to 1 for row B.** As wired, `plan_invocation` sets
  `thread_budget=resolve_budget()` (lw_stream.py:285), which returns
  `threads_per_worker` (region_pool.py:783-784) — i.e. on any multi-worker
  default the shipped route would be the **B4 arm, which LOST all 6 cells**
  and wastes 4x slot memory (4 x 2.09 MiB at 1024/153). Under SELF_PARALLEL
  the owner grants in-flight==1 anyway (lw_stream.py:425-432), so extra slots
  buy nothing; the kernel's `prange` uses numba's own threads, not the pool
  budget. Fix at the mint: `thread_budget = 1 if row == 'B' else
  resolve_budget()`. This exactly reproduces the measured B1 arm (zero
  background pool threads, one slot, self-parallel leaf) and also removes the
  worker-thread/prange oversubscription B4 suffered.

### A2. Element 2 precision

`aplus_decode.py` exists but is currently ORPHANED in src — nothing imports it
(grep: only `tests/optimization_v8/n9_producer/test_n9_aplus_decode_at.py`).
Integration is real work, and its scope must be stated honestly:

- Integration point: the packed fused-kernel decode. `_decode_at` is imported
  by exactly `patch_radiation.py:31` and `cylinder_longwave.py:41`
  (both -> `geometry.visibility_compiled`). Either re-point those imports to
  `aplus_decode._decode_at_plus` (same signature/bits, `inline='always'`,
  generic fallback arm retained for unknown modes) or swap the fused kernel
  bodies for the transcribed `_longwave_fused_primary_aplus[_serial]` already
  in aplus_decode.py:48+. Parity is pinned by the n9_producer suite; raw mode
  keeps the original little-endian byte assembly (identical bits).
- Scope: this improves the FUSED route only, which is env-gated OFF at
  defaults (`_fused_enabled`: `SOLWEIG_LIGHT_FUSED_RAD=1`; asserted OFF in the
  F3 A8 arm). The dense A8 fallback that actually serves the raw-guard
  decline (`_block` on dense arrays) has no packed decode and gains nothing —
  correctly so. Do not claim a default-path decode improvement from element 2;
  it is comparator/equity work (native must not win by withholding shared
  improvements from Numba) plus a fused-route improvement.

### A3. Element 3: shutdown consult and the tri-state

- **Region-pool shutdown consult (`pipeline.py:312-318`): KEEP.** The pool is
  now the DEFAULT executor. The consult is the teardown that releases owner
  state between tiles; with budget pinned 1 / SELF_PARALLEL it typically
  finds nothing, but the pool machinery still participates (scratch slot ids,
  canonical cancellation, fork-poisoning registration). Removing it risks a
  cross-tile leak for zero gain. Update the comment: no longer "No-op unless
  this process dispatched a region route" — the default route dispatches on
  every admitted tile.
- **`engine.py:1662` tri-state -> plain boolean: REJECT. This contradicts
  element 1.** The tri-state `None` (threads<=1, "no explicit demand") is what
  makes the route consult fire at H=1 (`cylinder_longwave.py:396`
  `parallel is not False`), and H=1 is precisely the winning arm: F3 shows B1
  beating A8 2.08x at 1024 binary and 1.23x at the DEFAULT 128 binary. Plain
  boolean would pass `parallel=False` at threads<=1, shut the route gate, and
  send every single-thread user to the legacy serial loop — silently
  destroying the measured default win. The MERGE_SCOPE restoration clause
  ("where N8 introduced tri-state solely to reach a rejected route") no
  longer applies: the route is now SELECTED, and the None value is
  load-bearing. Keep `True if threads_per_worker > 1 else None`; keep
  `False` = explicit serial demand (route gate shut); repair the stale
  docstrings instead (engine.py:1653-1661 "one resolve_lw_backend read per
  call — the deliberate shipped-state delta" is now false; also
  cylinder_longwave.py:181-197, :356-367, :457-469 and the `_lw_dispatch`
  module docstring, whose entire header narrates the registry selector).

### A4. Element 4 additions

Preserve, beyond the stated list: `region/consumers.py` whole-scene B
consumer (measurement suite, tests active); the whole-scene consumers in
`_lw_dispatch` marked "retained for measurement until integrator cleanup"
(lw_stream.py imports `_lw_dispatch.AosoaNativeCConsumer` as the C mixin) —
recommend deleting the whole-scene C consumer together with the C row and its
mixin base (`lw_stream._AosoaNativeCBase`, `AosoaCStreamConsumer`), keeping
the whole-scene B consumer installed (small, pure Python, tested).

## 1. Revised removal list (installed path)

| # | Target | Why | Breaks |
|---|--------|-----|--------|
| N1 | `lw_stream.AosoaCStreamConsumer`, `lw_stream._AosoaNativeCBase`, row-C branch in `_execute_row` (`_lw_dispatch.py:125-128`), `_lw_dispatch.AosoaNativeCConsumer` (whole-scene C) | Native C not selected (`not_selected_for_this_release`); artifact resolution at mint (lw_stream.py:278-283) goes with it | Only C-row tests (archived). Row B untouched. |
| N2 | `_native_dispatch/lw_default_policy.py` + `qualification_registry.json` from the call path and wheel | Structural rule replaces the selector (`region_route` keeps only lane-align pre-check -> `plan_invocation(row='B')`); the per-timestep registry file read + JSON parse + `policy_reasons()` diagnostics disappear | Registry/selector tests -> archived. No user surface: the selector never activated anything (empty registry, n8_32). The planned "N8-22 expert route via installed loader" never shipped; B7-32 remains THE expert route. |
| N3 | `_native_dispatch/installed_loader.py`, `native_handle.py`, `build_native.py`, `lw_native_aosoa.py` -> repo-only research | Reachable only via the removed selector/row C (the B7-32 dev-build route has its own loader in `backends.native_lw`; the `native_handle.py:221` import is the reverse direction, unaffected) | Loader/native-wheel tests -> archived. |
| N4 | `pyproject.toml` package-data: `backends/native/*`, `_native_dispatch/*.json`, `backends/native_generated/**` | No native artifact route remains; MERGE_SCOPE forbids shipping maintainer build programs | Packaging tests asserting shipped registry/native data -> archived. Installed tests REPOINT (wheel still contains `_native_dispatch` — now stream/direct_aosoa/lw_b_control/region/aplus — but no registry json, no native data). |
| N5 | `setup.py` (N8-41 native-wheel shim) | The native wheel product has no executing route | None (pure build was already the default; docstring says deletable). |
| N6 | Stale-docstring repairs (DX parity gate): `engine.py:1653-1662`, `cylinder_longwave.py:181-197/:203-223/:356-367/:457-476`, `_lw_dispatch.py` header + `region_route` docstring, `_native_dispatch/__init__.py` wheel-content paragraphs, `pipeline.py:308-311` | All narrate the registry selector / shipped row-A state that no longer exists | None; required by DX_CONTRACT doc accuracy. |

KEEP INSTALLED AND NOW DEFAULT: `lw_stream.py` (row B), `direct_aosoa.py`
(producer/classifier/lease), `lw_b_control.py` (the default leaf; frozen
`_longwave_primary` graph, N6 float32-view convention), `region/*` (executor:
plan_regions/execute_regions/budget/slots/fork safety), `aplus_decode.py`
(once wired per A2). KEEP REPO-ONLY: everything in N2/N3, all research trees.

## 2. Default route map (for FINAL_SELECTION.json)

Admitted packed channel triple, not all-raw, lane-aligned block, no explicit
serial demand, env unset or non-expert -> stream row B, budget 1 (self-parallel
leaf). All-raw-everywhere, non-admitted channels, degenerate/misaligned
blocks, explicit `parallel=False`, or SOLWEIG_LIGHT_LW_BACKEND=native|ispc ->
A8 legacy path (expert env additionally dispatches the B7-32 dev-build leaf in
`_lw_kernel`). Default executor CHANGES vs the N8 endpoint (row A everywhere);
outputs are bitwise pinned by the stream == whole-scene == legacy test chain,
and the raw decline is the reference itself. REQUIRED before F5: run the
frozen small chronology under the new default and a decline-parity test
(all-raw tile bitwise == A8 in the same process, including tile alternation
raw->packed->raw exercising slot reuse across the guard boundary).

## 3. Test disposition (specific)

- Archived-feature (skip with reason naming n8_32 -> N9 F3 NATIVE_LOSS; never
  weakened): selector/registry activation cases in `tests/optimization_v8/
  policy/`, `loader/`, `artifacts/`, `packaging/` native-wheel assembly, C-row
  cases in `tests/optimization_v8/native/`, and any test asserting the shipped
  empty-registry file or `policy_reasons()` taxonomy. Fixtures preserved.
- Active (now default-path safety): `tests/optimization_v8/stream/`,
  `tests/optimization_v8/region/` (pool safety, fork poisoning, budget),
  `tests/optimization_v8/n9_producer/`, `tests/optimization_v8/dx/`,
  `tests/optimization_v8/policy/test_legacy_env_parity.py` (its
  import-isolation pin still holds: `import solweig_light` imports none of
  `_native_dispatch`; the DEFAULT CALL now imports lw_stream/direct_aosoa/
  region/lw_b_control — it already imported lw_default_policy+region before,
  so the parity delta is removal, not addition), all v5/v6 trees, `tests/unit/`.
- New (integrator's list, confirmed + two additions): raw-guard decline parity
  (incl. same-process alternation across the guard boundary); H=1 pinning
  (plan.thread_budget == 1 for row B regardless of threads_per_worker);
  default-route smoke; decline-parity for non-admitted/misaligned (exists);
  expert-env precedence over the row-B default (env native/ispc must still
  reach `_lw_kernel`, NOT the stream).

## 4. What the shape missed (completeness)

1. **B4 default trap** (A1c): without the H pin, the shipped route is the arm
   that lost every cell. This is the highest-priority correction.
2. **Tri-state contradiction** (A3): boolean restoration silently removes the
   default win for threads<=1 users.
3. **Expert stand-down read** (A1b): "no env read" as stated would silently
   override B7-32 forcing.
4. **Element 2 scope** (A2): aplus touches the env-gated fused route, not the
   dense A8 decline target; no default-path decode claim.
5. **Cold-start/JIT**: the default path gains njit kernels (`lw_primary_b`,
   `classify_block_aosoa`, `_produce_patchmajor`, plus aplus if wired).
   Read-only site-packages defeats numba cache writes, so first-call compile
   is per-process — the same class of cost as the existing A8 kernels but
   larger. The inherited cold-regression gate (<=3%) must be explicitly
   covered by the F6 cold/warm main comparison, not assumed.
6. **Default-behavior-change record**: this disposition changes the shipped
   default executor, so FINAL_SELECTION/MERGE_MANIFEST must name the route map
   (§2) and the bitwise-parity chain, distinct from the timing claim.
7. **Honesty labels**: 128-mix is a marginal win (+4.3%); single-channel-raw
   compositions are UNMEASURED and stream by design — record both as accepted
   residuals; do not widen the guard without measurement (the guard is exactly
   the measured loss class).
8. **Companion/workflow surface**: no signature, env, output, or companion
   ownership change (route is internal to the same call) — confirm in the
   merge manifest's main-delta table.

## 5. Sequencing (forward commits, integrator implements)

1. Commit A (behavior): H pin at mint (A1c) + raw guard in `plan_invocation`
   (A1a) + tri-state kept, stale comments repaired (N6 subset) + new tests
   (§3). Default chronology + decline parity green.
2. Commit B (equity): aplus wiring per A2 + n9_producer green.
3. Commit C (removal): N1/N2/N3 relocations to repo-only research, N4/N5
   packaging, archived-feature skips, remaining N6 repairs.
4. F5/F6 then verify: installed no-env wheel (stream present, registry/native
   absent), cold/warm main comparison incl. cold-JIT gate.
