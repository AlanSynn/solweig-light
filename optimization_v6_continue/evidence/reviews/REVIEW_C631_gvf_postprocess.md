# REVIEW C6-60: C6-31 typed GVF block postprocess kernel

- **Reviewer**: C6-60, independent GLM review; Opus unavailable (routing: GLM via Z.ai).
- **Date**: 2026-09-21.
- **Candidate**: worker v6-gvfpost, worktree `/Users/alansynn/Workspace/solweig-light-v6-gvfpost`, detached at `5e1fab467f7e6038dcf3992cb694008a51ea2c58`, untracked additions `src/solweig_light/radiation/gvf_postprocess.py`, `tests/optimization_v6/gvf_postprocess/`, `optimization_v6_continue/evidence/gvf_post/`.
- **Reviewer worktree**: `/Users/alansynn/Workspace/solweig-light-v6-rev631` (detached at `01092950`).
- **Integrity**: all 6 hashes in `sha256s.txt` recomputed and match; every file mtime precedes the 11:58 sha256 record; `git diff` empty (no tracked-file edits, no late writes). Tests, parity harness and probes in this review were executed by me against the hash-verified bytes.

## VERDICT: APPROVE-WITH-NOTES

The kernel is node-for-node faithful to `_postprocess_block` at 5e1fab46, the warning/error fallback contract holds under the default NumPy errstate regime, the prange variant is sound, and the step-domain guard is exact. Two findings require follow-up before or at integration: F1 (underflow clause of the errstate claim is overstated) and F2 (integration recipe's "current code" snippet does not match the base source and would break if applied verbatim). Neither is a bitwise-correctness defect on any reachable production path.

## Verification performed (my own runs)

1. **125-test suite**: reran `pytest tests/optimization_v6/gvf_postprocess/` with `/Users/alansynn/Workspace/solweig-light/.venv-light/bin/python` → **125 passed, 84 warnings** (matches commands.txt). Assertions are bitwise via `uint32` views (`_cases.bits_equal`, `np.array_equal` on `.view(np.uint32)`) — no `allclose` anywhere in the suite.
2. **Parallel parity, independent rerun**: all 10 case builders x 3 sizes x 3 repeats = **90 runs, all bitwise-equal** to the original on the five outputs and all 16 planes (probe P1).
3. **Odd shapes**: serial vs parallel vs original on (1,1), (3,17), (32,33), (17,129) — all bitwise PASS (probe P7).
4. **Step guard table** (probe P3): `0.0, 0.5, -1.0, nan, inf, 2**24, np.array([2.]), 1-d, None, '3', True → None` (reference route); `1 (python int, from the first<1 clamp), 2**24-1, np.float64, np.float32, 0-d array → admitted`. Matches the module docstring exactly; `bool` is explicitly excluded (gvf_postprocess.py:71).
5. **Engine production steps land in-domain** (probe P4): `np.round(_operate(np.multiply, 30, _array(1.0)))` yields `np.float32(30.0)`; the `first_steps < 1` clamp yields Python `int 1`; both admitted. The `second<=0` guard (ground_view.py:564) plus `np.round`'s integer-valued outputs mean every engine-reachable step is a finite integer ≥ 1; anything else (nonfinite, ≥ 2^24, array-valued) routes to the reference. Claim 5 verified.
6. **first=0 routing** (probe P5): wrapper routes to reference; all 13 warnings reproduce identically (4x divide-by-zero, 4x invalid divide, 5x invalid multiply), outputs and planes bitwise-equal. The task-text "first=0 divide" concern is covered both by tests and by this probe.
7. **Bench consistency**: recomputed ratios from `timing_raw.txt` medians — serial/original 2.013/2.463/2.577, parallel/original 0.630/0.461/0.279; parity_table/README claims "0.28-0.63x parallel" matches; "1.9-2.6x serial" — recorded data supports 2.0-2.6 (see F3). `bench_postprocess.py` measures the wrapper (including its three save-copies) vs the original at production block_rows=32, median of 60 warm calls; no performance claim is made anywhere in the evidence beyond selection. Claim 4 verified.

## Claim-by-claim analysis

### Claim 1 — warning/FPE hole: CLOSED for the default regime; one residual clause gap (F1)

I enumerated every op in the original (`ground_view.py:516-540`) that can fire a warning-domain event, using the engine dtype semantics (`_operands`, engine.py:1693-1704: scalar/int operands are cast to the f32 raster's dtype, so every arithmetic node is f32):

- **Divide** (`/first`, `/first+1`, `/second`, `/second+1`, `/0.9`): all denominators ≥ 1 in the admitted domain, so divide-by-zero is genuinely excluded; out-of-domain steps route to the reference first (verified probe P3/P5).
- **Overflow** necessarily yields Inf; **invalid** necessarily yields NaN. Every such nonfinite propagates to raw pre-clamp `gvf2` or one of the four unclamped returns: the DAG's only non-propagating consumers are comparisons (never warn), the `keep` arithmetic (eq∈{0,1} minus facesh∈{-1,0,1,2}; `1 + FLT_MAX` rounds back to `FLT_MAX`, cannot overflow), and the Z2/Z4/Z5 `+0.0` writes. `term * influence` with influence=0 turns Inf/NaN into NaN which still propagates through the add.
- **The clamp hides only +Inf** (`Inf > 1.0 → 1.0`; NaN and -Inf survive the clamp into returned `gvf2`), and the raw pre-clamp check (gvf_postprocess.py:182-186) observes it before the clamp — the exact hole named in the task. `case_overflow_clamp_hidden` passes warning parity: the wrapper warns (via fallback) even though every returned field is finite.
- **Post-flag-point ops**: moot — the fallback re-executes the entire original function, so any independently-warnable later op fires identically.
- **Plane restore completeness**: the original's only in-place plane mutations are lines 523 (`weightsumwall`), 527 (`weightsumLwall`), 530 (`weightsumalbwall`) = planes 1/3/5; `keep` and `gvf2` are fresh arrays from `_operate`/`astype`, not caller planes. The wrapper's save (gvf_postprocess.py:107-109, before the kernel) and restore (115-117, full-plane bitwise copies, sNaN payloads included) is therefore complete, and the re-run sees bit-identical inputs. Under a raised error the caller-visible state comes only from the original's own partial mutation sequence — verified by `test_errstate_raise_parity` (post-raise plane states bitwise-equal on all 6 warn cases).

**Residual gap (F1)**: the flag observes nonfinite values only. Underflow produces a finite (subnormal/zero) result with no nonfinite anywhere, so on the fast path the wrapper cannot reproduce `np.errstate(under='raise'|'warn')` behavior. Confirmed empirically (probe P2): with subnormal operands, original under `errstate(all='raise')` raises `FloatingPointError: underflow encountered in divide` while the wrapper returns silently — **with bitwise-identical outputs and no warning under the default regime** (under='ignore'). The docstring's unconditional "If the flag is clean, the original NumPy sequence could not have warned" (gvf_postprocess.py:23-24) is true for the default regime and for overflow/invalid/divide under any errstate, but the `errstate(all='raise')` sentence (lines 30-31) holds only on the flagged fallback path. Production reachability is effectively nil (planes are radiance-scale accumulators; subnormal operands do not occur), so this is a claim-scoping defect, not a correctness defect on any reachable path. Recommended fix: scope the docstring claim, e.g. "under the default warning regime the flag is exhaustive; under non-default errstate only underflow (finite subnormal results) can diverge on the fast path."

### Claim 2 — order sensitivity: VERIFIED, reconciliation honest

I checked the kernel's statement order against `ground_view.py:516-540` node by node: C1-C4 influence comparisons (kernel 150-153) precede keep (155-161), keep precedes gvf1 (163-168), Z2 precedes gvf2's read of `weightsumwall` (170-172 → 174), C3 is computed from the pre-zeroing value (152, read at 146), Z3 clamps only after the raw check (182-186), Z4 precedes gvfLup2 (197-199), Z5 precedes gvfalb2 (215-217), return path R1-R4 (239-243) matches lines 534-540 including the `gvfalbnosh2 /second` asymmetry (no +1, kernel uses `f_second`, lines 232-236) and the `* buildings_b + nosh_term_b` ordering. The three `keep == 1` re-evaluations and the inert `keep[keep==-1]=0` are reproduced in place.

`node_inventory.md` is honest: it states plainly that the source has **10 comparison expressions** (C1-C10, line numbers 516-530 — all correct against the actual source) and **5 in-place assignments** Z1-Z5 (521/523/525/527/531 — correct), that the task gate's "16" corresponds to the 16 exported debug nodes, and that the gate is satisfied over the complete inventory. The debug-node parity table (16 nodes x 27 in-domain cases, all TRUE) is generated by `parity_harness.py` from live runs; `test_original_matches_replica` proves the replica (hence the inventory) against the untouched original first. One immaterial imprecision: C5 describes the step as "0-d f64" while production steps are actually np.float32 scalars (probe P4) — with in-domain integers the two promotion readings are bitwise-identical, so no behavioral consequence (folded into F4).

### Claim 3 — prange: SOUND

Source inspection of `_postprocess_pixel`: every read and write is indexed by the same (row, col); planes 1/3/5 are read (146-147) before being written (171/198/216) within the same element; there is no cross-element accumulation, no stencil, no order dependence. The only cross-iteration state is `flagged`, an integer `+=` reduction (disjoint contributions, sum is schedule-independent and only its zero/nonzero status is consumed). Each output element is written exactly once by its owning iteration before any read. My independent rerun: 90/90 bitwise (P1) plus odd shapes (P7). Claim verified.

### Claim 6 — integration recipe: semantics right, snippets wrong (F2)

Argument order/types are exact: the wrapper signature `(block, buildings_b, facesh_b, lup_term_b, alb_term_b, nosh_term_b, first, second, parallel=)` matches the call site's argument order (ground_view.py:656-659); passing `block` directly is equivalent to the inlined `tuple(block[index] ...)` views; no dtype coercion occurs at the boundary for the in-tree caller (block allocated `np.float32` at ground_view.py:654; raster args are f32 by `_supported`/explicit copies; steps admitted via `_step_scalar`).

However, `integration_patch.md`'s "Current (base 5e1fab46)" snippet is **not the base source**: it shows a `planes = tuple(...)` statement and an 8-name unpack receiving `weightsumwall, weightsumLwall, weightsumalbwall` as return values. The actual call (ground_view.py:656) unpacks **five** names (`gvf_b, gvfLup_b, gvfalb_b, gvfalbnosh_b, gvf2_b`), `_postprocess_block` returns five fields (ground_view.py:541), and the wrapper also returns five (gvf_postprocess.py:119) — the recipe's "Return signature ... AND the three in-place-mutated planes" is false on both sides. Applied verbatim, the replacement raises `ValueError` (5 values into 8 targets). The patch's own caveat ("exact form of the surrounding loop must be checked against the working tree") limits the blast radius, but the snippets must be corrected before handoff; the correct integrated call is:

```python
gvf_b, gvfLup_b, gvfalb_b, gvfalbnosh_b, gvf2_b = gvf_postprocess_block(
    block, buildings[row0:row1], facesh[row0:row1], lup_term[row0:row1],
    alb_term[row0:row1], nosh_term[row0:row1], first_steps, second_steps,
    parallel=True)
```

(`_postprocess_block` itself stays untouched as fallback; plane mutation remains in-place through the caller's `block`, which the wrapper preserves.)

## Findings

| # | Severity | Finding |
|---|---|---|
| F1 | Medium (contract wording) | Fast-path flag observes only nonfinite values; under `np.errstate(under='raise')` (incl. `all='raise'`) with subnormal-producing inputs the original raises `FloatingPointError: underflow encountered in divide` while the wrapper returns silently — confirmed empirically (probe P2); outputs bitwise-identical and both silent under the default regime. Docstring lines 23-24/30-31 overstate the errstate contract. Scope the claim to the default warning regime (or to overflow/invalid/divide); production reachability ~nil. |
| F2 | Medium (recipe doc bug) | `integration_patch.md` "Current" snippet and return-signature note do not match base 5e1fab46 (no `planes =` statement; call unpacks 5 names; both functions return 5 fields, not 8). Verbatim application breaks with an unpack ValueError; semantic intent (single call-site swap, arg order as given) is correct. Corrected call recorded above; recipe must be regenerated. |
| F3 | Low (evidence hygiene) | `timing_raw.txt` records one run's numbers plus a manually appended `run2 exit=0` with no run2 data; the claimed serial lower bound "1.9x" is not present in the recorded file (recorded range 2.0-2.6). The parallel 0.28-0.63x claim matches the record. Re-record both runs or trim the claim to the recorded range. |
| F4 | Low (robustness note) | The wrapper does not assert dtype at the boundary. An out-of-contract f64 caller gets f32 returns (original returns f64; probe P6). Unreachable in-tree (block is `np.empty(..., dtype=np.float32)`, ground_view.py:654; args f32-guarded). Optional: a cheap `block.dtype == np.float32` check routing to `_reference_block`. Related footnote: node_inventory C5 says steps are "0-d f64"; production steps are np.float32 scalars — bitwise-neutral in-domain. |
| F5 | Info (positive) | Node inventory reconciliation is honest and line-accurate (10 comparisons + 5 in-place assignments + 5 returns, all verified against source); the clamp-hidden-Inf hole is genuinely closed by the raw pre-clamp check; plane-restore completeness verified (only planes 1/3/5 are mutated by the original); first=0 and all out-of-domain steps route to the untouched reference with identical warnings (probe P5); prange per-pixel independence holds by construction and 90/90 bitwise reruns. |

## Bottom line

The compiled kernel and its fallback contract are sound for every input the engine can produce; the two medium findings are documentation defects (claim scoping in the module docstring; the integration recipe's snippets), not behavioral defects on any reachable production path. APPROVE-WITH-NOTES: integrate only after F2's recipe snippets are corrected; F1 should be fixed by scoping the docstring (no code change required).
