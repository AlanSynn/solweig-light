# REVIEW C6-60: C6-30 GVF source-expression preparation

- **Reviewer:** independent GLM review; Opus unavailable (C6-60 service instance)
- **Date:** 2026-09-21
- **Candidate:** worker v6-gvfprep, worktree `/Users/alansynn/Workspace/solweig-light-v6-gvfprep`, detached at `5e1fab46`; candidate files untracked and intact (`sha256s.txt` recomputed — all 8 hashes match; `git status --porcelain` shows only the three owned paths, no late writes).
- **Review worktree:** `/Users/alansynn/Workspace/solweig-light-v6-rev630`, detached at `01092950`. `git diff 01092950 5e1fab46 -- src/` is empty, so baseline source was read from the review worktree; line numbers below are valid for both commits.
- **VERDICT: APPROVE-WITH-NOTES** — 8 findings, none blocking; findings 1-2 are evidence-document inaccuracies, 3-7 notes, 8 is the positive verification record.

## Claim verification (check, don't reassure)

### 1. Snapshot semantics — VERIFIED from source

Water-mutation position and consumers, `_gvf_fused` at `ground_view.py:616-628`:

- Per direction the order is: `aspect` (617), `azimuth` (618), `Lup` (619), **water mutation (620-621)**, `Lwall` (622), `albshadow` (623), `first/second_steps` (625-628), snapshots (629-636), `azilow/azihigh/facesh` (637-646), `lup_term/alb_term/nosh_term` (647-649), `ray_schedule` (650), block loop. `prepare_gvf_step` (`gvf_prepared.py:133-199`) mirrors this order exactly for everything it hoists: Lup evaluated at :147 **pre-mutation**, scatter at :155, Lwall/:178, albshadow/:181, steps/:186-189, terms/:191-194, sky/:199 all **post-mutation**.
- Between baseline's first Tg read (619) and the mutation (621) the only intervening computation is `azimuth` (618), which does not read Tg. **No consumer exists whose value would differ.** (a) confirmed.
- **18→1 write idempotency (b):** the scatter `Tg[lc_grid == 3] = _operate(np.subtract, Twater, Ta).astype(np.float32)` (621) has inputs `landcover` (frozen copy, 613), `lc_grid` (gated: no Tg alias, candidate `gvf_prepared.py:113-118`), `Twater`/`Ta` (scalars, `Twater` gated at :117). Under the gates **no write input depends on state changed by an earlier write**; the mask and value are constant, so the 18 baseline writes deposit the same constant into the same cells — idempotent. One write at first position + stable post-state is bitwise-equivalent, and the only pre-mutation read (dir-1 Lup) is separately reproduced via `lup_first`. Confirmed additionally by the suite's negative controls (`test_water_mutation_and_first_direction_split_controls`: mutation and first/later split proven non-vacuous) and by bitwise Tg-after equality on all water scenes.
- Post-mutation Lup for dirs 2..18: after the first write, memory state is stable, so each of the 17 post-mutation evaluations at 619 is bitwise identical; one suffices. Same argument for the 18 Lwall/lup_term/albshadow/steps evaluations and the 5 post-loop sky evaluations (680, 683-686).
- `landcover == 1` with no `lc_grid == 3` cell and `landcover != 1` both correctly collapse to a single Lup evaluation (`gvf_prepared.py:159-161`; pinned by `test_water_mask_without_water_cells_reuses_lup`, `lup_evaluations == 1`).

### 2. Tg-alias split 11 delegate / 4 prepared — VERIFIED

`_admits` (`gvf_prepared.py:107-118`) gates exactly 11: walls, scale, ewall, albedo_b, landcover (matching `_gvf_fused`'s own 567 set) + buildings, shadow, alb_grid (matching 602) + **lc_grid, dirwalls, Twater (new)**. The three new gates are real hazards:

- `lc_grid`: mask is re-derived per direction at 621 from the live array; a Tg alias lets the mutation move the mask.
- `dirwalls`: `aspect` is re-derived per direction at 617 from live dirwalls; a Tg alias moves aspect mid-loop.
- `Twater`: the scatter value is re-computed per direction at 621; a Tg alias (0-d view of a water cell) makes the value diverge progressively after the first write (proved non-vacuous in the test).

The 4 stay-prepared aliases are position-faithful in the source: `Tgwall` read at 622 always post-mutation; `emis_grid` read pre-mutation at 619 and post-mutation at 622/647/680 — candidate reads at the identical pre/post points (`:147` vs `:164/:178/:199`); `first`/`second` read post-mutation at 625-628, candidate at :186-189 (post-mutation). Delegation is bitwise-safe because `prepare_gvf_step` returns None **before any mutation** and `prepared_gvf_step` (`:301-303`) then forwards the untouched originals to `_gvf_fused`, whose own guards reproduce baseline behavior. Tested with delegate-spy + oracle (`engine.gvf_2018a_numpy`) parity for all 11, and spy-pinned no-delegation + bitwise parity for all 4.

### 3. Tg caller-visible mutation — VERIFIED

In-place scatter at `gvf_prepared.py:155` matches baseline 621. Guard failure (`_admits`, :127) precedes the mutation, so failing calls hand over untouched Tg (`test_unsupported_step_inputs_raise_identically` pins raise-type parity; both routes then execute identical downstream code on identical copies). `np.errstate(over='raise')`: the first overflow site is the Tg-side `^4` power of dir-1 Lup — `ground_view.py:619` **before** the mutation at 620-621, and `gvf_prepared.py:147` **before** :155 — so both routes abort pre-mutation with identical Tg (`test_errstate_raise_aborts_prepared_route_like_baseline`). Note: that test compares the two routes' post-abort Tg against each other rather than against a pre-call snapshot; untouched-ness is joint test+source-order (finding 5). A post-mutation-first-overflow scenario (pre Lup clean, post Lup overflows) also aborts with exactly one mutation on both routes by the same ordering argument.

### 4. Warning census — VERIFIED, method sound

`test_overflow_warning_count_contract` wraps the real route calls in `warnings.catch_warnings(record=True)` + `simplefilter('always', RuntimeWarning)` — every occurrence is counted, nothing suppressed; the scene suppresses invalid/divide via `errstate` so only genuine overflow occurrences count. Arithmetic maps to source: fused = 18 Lup (619) + 18 lup_term (647) = **36**; prepared = lup_first (:147) + lup_rest (:164), lup_term reusing the raw `lup_rest` (:192) = **2**; sky term reads Ta only (no overflow), Lwall's `^4` reads ambient Tgwall (no overflow in scene), sunwall divide is loop-external in fused (597). Both asserts are exact `== 36` / `== 2` and pass under my run. The reduction reflects genuinely fewer evaluations, not suppression (the counts suite independently pins `_lup_expression` 36→2/1). engine.py:1370 `svfalfaE = np.arcsin(np.exp(_divide(np.log(_operate(np.subtract, 1, svfE)), 2)))` confirmed verbatim in `Lside_veg_v2022a`; the per-Lside-call log-divide warning is outside the closure and pinned unchanged (before == after == 1). sunwall walls-zero divide parity asserted once-per-call both routes.

### 5. Count reduction honesty — VERIFIED, reproduced independently

I re-measured with my own counting harness (same transparent call-through wrapper design; wrap points are correct because both routes resolve `_operate`/`_divide`/`_lup_expression`/`ray_schedule` via lazy imports or module globals **at call time**):

| Metric (64², seed 65) | fused | prepared | SUMMARY |
|---|---|---|---|
| `_lup_expression` water | 36 | 2 | 36→2 ✓ |
| `_lup_expression` no water | 36 | 1 | 36→1 ✓ |
| `_operate` water | **3564** | **2745** (−819) | 3564→2745 ✓ |
| `_operate` no water | **3546** | **2733** (−813) | 3546→2733 ✓ |

Direction-dependent work not over-hoisted, from source: azilow/azihigh/facesh remain inside `run_prepared_gvf_step`'s direction loop (`gvf_prepared.py:232-241`); `ray_schedule` pinned `== 18` by test; azimuth cardinal accumulators copied 1:1 (:256-271 vs 664-679). The `_operate` test itself pins only a `>= 600` floor (finding 6).

### 6. Parity — VERIFIED by my own runs

- `tests/optimization_v6/gvf_prepare/`: **78 passed, 4 warnings in 3.68s** (NUMBA_NUM_THREADS=2, venv-light python) — matches the recorded command and exit code.
- `tests/optimization_v5/gvf/`: **82 passed in 4.27s** — G02/G03 intact.
- Bitwise assertions are genuine uint32/uint64 views over `ascontiguousarray` (`gvf_prepare_cases.py:48-59`), catching NaN payloads / signed zeros / dtype drift; all 17 outputs + post-call Tg compared; the differential grid is 16², 33×21, 64², 128² × water/open-built/serial-parallel (32 configs) plus adversarial scenes — within the review size rules.
- float64-SBC pin (`test_float64_derived_lup_conversion_preserved`, `SBC = np.array([5.67051e-08])`): the conversion exists because the gather planes must be float32 for the numba kernels; baseline performs the identical value-changing `np.array(Lup, dtype=np.float32, copy=True)` per state (`_direction_snapshot`, `ground_view.py:258/261`), and the candidate reproduces the same two conversions (`gvf_prepared.py:170-174`) while keeping `lup_term` on the **raw** evaluation (:192) exactly as baseline's inline 647 does. Pinned bitwise.

### 7. Kill switch + inertness — VERIFIED

`SOLWEIG_LIGHT_GVF_PREPARE=0` short-circuits at `gvf_prepared.py:299-300` **before** `prepare_gvf_step`; spy test pins zero preparation + fused parity; default (unset / any other value) is ON. `grep -rn gvf_prepared src/` in the candidate worktree: **no matches** — the module is imported by nothing in src; engine.py untouched (`git status` shows only the owned untracked paths). No module-level mutable state (only the env-var name constant); nothing keyed by array identity; `test_no_leakage_across_steps` covers sequential different-input calls.

### 8. Integration recipe — VERIFIED against base source

Recipe's "current code" block matches `engine.py:1735-1745` verbatim (import line, threads gate, `_gvf_fused(..., parallel=True, block_rows=32)` at :1744, serial fallback at :1745). The patch swaps in `prepared_gvf_step` with the **same 20 positional arguments in the same order** — matches `prepared_gvf_step`'s signature (`gvf_prepared.py:293`) — plus explicit `parallel=True, block_rows=32`, identical to the current fused call. Serial branch untouched as stated. Recipe's note that `gvf_2018a_numpy` stays reachable is correct in substance; its wording is wrong (finding 3).

### 9. Honesty — VERIFIED

Timing labeled RECORD ONLY / NO CLAIMS (0.1079 vs 0.1264 s at 256², contended host) — appropriately modest, no speedup claims anywhere. Gate-2 numbers are exact and reproducible (I reproduced all four). The two documentation slips below are the exceptions.

## Findings

1. **[minor, doc] SUMMARY miscounts the differential suite.** `SUMMARY.md:28` says `test_gvf_prepare_differential.py` has "40 tests"; pytest collects **69** (69 differential + 4 counts + 5 warnings = 78, consistent with the total). Evidence-number slip only; no code impact.
2. **[minor, doc] SUMMARY's 4-warning attribution is imprecise.** `SUMMARY.md:125-128` attributes all 4 captured warnings to "bare `prepare_gvf_step` calls in the stats/count tests". Actual split (pytest warnings summary): 2 are sunwall 0/0 `invalid value in divide` from the two bare stats calls (`test_water_mask_without_water_cells_reuses_lup`, `test_preparation_stats_water_scene`); the other 2 are `overflow encountered in power` from the overflow-scene tests (`test_overflowing_tg_bitwise_nonfinite_masks`, `test_overflow_nonfinite_parity_despite_warning_counts`), whose `errstate` suppresses invalid/divide but leaves over='warn'. Substance is right — all four are baseline-consistent warnings both routes emit, none a route leak — but the source split should be corrected in the ledger.
3. **[minor, doc] Recipe wording:** `INTEGRATION_RECIPE.md:40-42` — "`gvf_2018a_numpy = gvf_2018a` (engine.py:1731) keeps pointing at the **dispatched symbol**" is wrong: engine.py:1731 executes before the :1735 redefinition, so it binds the **line-230 original body** (which is exactly what the differentials need). Conclusion stands, phrase should read "retained original body".
4. **[note, API] Default mismatch:** `prepared_gvf_step` defaults `parallel=True`; `_gvf_fused` defaults `parallel=False`. Harmless today — the recipe's dispatch passes explicit `parallel=True` on both sides, and the suite's parallel parametrization (prepared-serial vs fused-parallel, bitwise equal across all 16 grid configs) shows serial/parallel gather parity for this route — but future direct callers relying on defaults get a different kernel than `_gvf_fused` would give. The 01092950 ledger wrapper-vs-serial divergence is cylinder-route-specific and does not apply here.
5. **[note, test] errstate-raise "Tg untouched" is a joint test+source proof:** `test_errstate_raise_aborts_prepared_route_like_baseline` compares the two routes' post-abort Tg to each other, not to a pre-call snapshot; untouched-ness follows from source order (first overflow site precedes the mutation on both routes — `ground_view.py:619` before 620-621; `gvf_prepared.py:147` before 155). Sound as it stands; a pre-call snapshot assert would make it self-contained.
6. **[note, test] `_operate` reduction pinned as a floor (`>= 600`), not the measured −819** (`test_gvf_prepare_counts.py:93`). Acceptable conservatism — the load-bearing `_lup_expression` 36→2/1 counts are pinned exactly, and I reproduced the exact −819/−813 — but the ledger should note the exact numbers are reproduced-once, suite-pinned-as-floor.
7. **[trivial] Docstring typo:** `gvf_prepared.py:62` "_gvf_funed" (missing 's').
8. **[positive] Verification record:** both suites re-run by this reviewer and pass (78 + 82); all four `_operate`/`_lup_expression` counts reproduced exactly; sha256 manifest matches; candidate worktree clean; kill switch and inertness proven; snapshot order, idempotency, alias gates, warning census, count reductions, and recipe arg mapping all verified against base `5e1fab46` source as detailed above.

## Verdict

**APPROVE-WITH-NOTES.** The core hazard (snapshot vs live re-read semantics around the water mutation) is correctly argued from source and correctly gated; the 11/4 alias split is exactly right; nothing is over-hoisted; the fallback is delegation of untouched inputs, which cannot diverge. Findings 1-3 are evidence-document corrections for the ledger; 4-7 require no action before integration.
