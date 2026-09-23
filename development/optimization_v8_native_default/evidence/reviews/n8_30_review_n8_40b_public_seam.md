# Review: N8-40b public LW route seam (n8-seam) — n8_30_review_n8_40b_public_seam

- schema: sw8-n8-30-review-v1 · verdict: **APPROVE** · 2026-09-23T03:44Z
- object: the 4-path diff on top of HEAD `730eb4de` in `/Users/alansynn/Workspace/solweig-v8-native` (branch `perf/native-optimization`); author `n8-seam`; reviewer independent (n8-rev-n8-41).
- working tree at review start: **exactly** the four declared paths (`M engine.py`, `M cylinder_longwave.py`, `?? test_lw_public_seam.py`, `?? n8_40b_public_seam_record.json`). The reported v6-raws clobbering incident is fully cleaned (no v6 path in `git status`).

## Claims — all 7 PASS (executed evidence)

1. **Mechanism** — engine.py:1663 passes `parallel=True if threads_per_worker > 1 else None`; grep census: `Lcyl_v2022a_by_demand` has exactly one src caller (engine.py:1663). Route gate at cylinder_longwave.py:396 `if parallel is not False and rows*cols:` (consult :397, def :181); the package's single env-read standdown inside `_lw_region_route` is unchanged. Engine :1762/:1770/:1778 stay patch_radiation boolean paths; grep proves patch_radiation never imports cylinder_longwave → cannot reach the route at any H. Executed: seam-capture test asserts `[None]` at H=1, `[True]` at H=2 (aborts the calc at the exact call site).
2. **No None reaches njit** — `_lw_kernel` (:215) and `_longwave_fused_primary_block` (:332, plain Python) select kernels by truthiness → None → serial; the njit fused pair (:227/:280) take no `parallel` parameter; the non-fused fallback call passes none; FULL_DIAGNOSTICS normalizes `bool(parallel)` (:473). Every existing caller passes True/False (v6 parity parametrizes `(False, True)`; engine previously passed an H-derived bool) — behavior identical.
3. **Shipped-state inertness, EXECUTED** — real public calc, small_original_cpu day event, PIPELINE demand, shipped registry at H=1: exactly 1 `resolve_lw_backend` consult, `'[absent]'` reasons, `region_spy == []`, parallel-kernel counts 0 / serial ≥ 1, Ldown/Lside bitwise (uint32) vs route-forced-None. H=2: bitwise, 1 consult, parallel family only.
4. **Qualified state** — injected B-row (real lw_b_control sha256) through the PUBLIC wrapper at H=1: exactly one `execute_regions` (self_parallel), all numba kernel counts 0, bitwise vs legacy. Driver-level `parallel=False` under the qualified row: zero consults, zero dispatch; `None` dispatches. No existing test modified (`git status`; `test_serial_demand_never_dispatches` green inside the 14).
5. **Test file quality** — unique module names (`_n840b_v6_conftest`, `policy_test_helpers`), real reference-scene anchor (boundaries manifest, input event ts 7; day-branch enforced by the capture assertion), no skip labels declared and none used (correct: row B needs no staged artifact).
6. **Suites (all run by me; loadavg 4.84/4.42/5.09/8.05 before each — all ≥ 2.5)** — integration **14 passed** (5.48s); policy+dx **95 passed** (3.28s); installed dedicated **13 passed / 6 skipped** (152.33s; skips = 4 deferred gates + 2 host-memory-pressure, unchanged); full tree one invocation **1972 passed / 6 skipped / 0 failed** (200.58s) = 1967 baseline + exactly 5 new; same 4 pre-existing warnings.
7. **Record** — design-first with 3 mechanism-level rejected candidates; shipped-state delta stated explicitly (one fail-closed registry read per public LW call at H=1; H>1 delta none); site-inventory correction (:1770/:1778 cannot reach the route) documented and independently confirmed; negative control recorded (pre-seam: 4 fail / 1 pass).

## Negative-control corroboration (not re-executed — destructive)

Structurally: pre-seam, the H=1 capture would read False (test 1 fails), the gate stays shut so consults==0 (test 2 fails), None-as-False leaves `region_spy` empty under a qualified row (tests 4+5 fail); only the H=2 test passes on both trees — exactly the recorded 4/1 split. Non-vacuity holds.

## Notes

- **N1** (presentational): the record cites pre-diff line numbers for the changed sites (:1655/:387/:388 at head_at_start); post-diff they are engine.py:1663 / cylinder_longwave.py:396 / :397. Untouched-site citations are current. No repair required.
- **N2** (coordinator action): my verification runs regenerated `optimization_v8_native_default/evidence/installed/installed_gates.json` (67/67 lines — pytest tmp-dir indices and host budget figures inside captured error strings; outcomes identical) — the exact disclosed run-metadata class; `git checkout --` to restore if unwanted. I did not touch it (guardrail). My scoped runs did not touch the v6 raws.
- **N3**: record-internal probe numbers were taken as recorded; every load-bearing figure that is also a test assertion was independently reproduced in my runs.
- **N4** (forward-looking): `parallel=None` is now a route-eligible driver value; the only producer is engine.py:1663 and all three driver docstrings document the contract. Nothing to change.

## Conclusion

The seam does exactly what it claims and nothing more: H>1 byte-identical, H=1 gains exactly one fail-closed registry read over an otherwise bitwise-identical serial path, `False` remains the only serial demand, no `None` reaches any njit kernel, and a qualified row dispatches through the public wrapper at the shipped default. **APPROVE.**
