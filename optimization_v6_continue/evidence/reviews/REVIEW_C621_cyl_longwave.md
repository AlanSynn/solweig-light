# REVIEW_C621 — Independent review of C6-21 cylinder longwave primary-output kernel

- **Reviewer**: C6-60 (service instance). Independent GLM review; Opus unavailable (routing: GLM via Z.ai).
- **Date**: 2026-09-21
- **Review worktree**: `/Users/alansynn/Workspace/solweig-light-v6-rev621`, detached at `0ff8cbce` (created for this review).
- **Candidate worktree**: `/Users/alansynn/Workspace/solweig-light-v6-cyllw`, detached at `5e1fab46`, candidate untracked; HEAD and `git status` unchanged through this review (re-verified at close).
- **Evidence under review**: `optimization_v6_continue/evidence/cyl_lw/{EVIDENCE.md, INDEPENDENCE_VERIFICATION.md, INTEGRATION_RECIPE.diff, parity_results.json, run_L1.py}`; `src/solweig_light/radiation/cylinder_longwave.py`; `tests/optimization_v6/cylinder_lw/`.
- **Anchors**: all four sha256 anchors in EVIDENCE.md re-hashed and matched at review start AND at review close (no late writes): module `37de63de…`, conftest `95e346e1…`, test `a853ddba…`, run_L1 `0a2bede2…`.
- **Citation validity**: `git diff --stat 0ff8cbce 5e1fab46 -- src/ tests/differential/` is empty, so every tracked-source `path:line` citation below resolves identically in both worktrees.

## Method

I re-derived the R-B independence chain from source myself for **each of the four** `_longwave*` njit kernels at `5e1fab46` (`patch_radiation.py:587/651/716/789`), traced every accumulator read and write, and swept consumers (engine, pipeline, state, exporters, aniLum) rather than trusting INDEPENDENCE_VERIFICATION.md. I compared the candidate wrapper/driver against the originals statement by statement (guard order, arithmetic, argument order), ran the full 39-test suite, re-ran the L1 evidence runner and diffed its output against the committed JSON, ran the differential regression sweep, and independently reproduced the claimed pre-existing failure **without** the candidate module present. All runs used `/Users/alansynn/Workspace/solweig-light/.venv-light/bin/python`. No edits to the candidate worktree.

## Claim verification

### Claim 1 — R-B independence chain: CONFIRMED (independently re-derived)

Per-kernel derivation (candidate trees at `5e1fab46`; line numbers identical in `0ff8cbce`):

- `_longwave` (`patch_radiation.py:587-647`): accumulators 10..13 are written at :605/:607 (sky sweep), :619-:620 (solar_gate branch), :628 (else branch), :639 (reflected sweep) and read **only** at :643-:646 (output columns 7..10). No other read exists. Output cols 0..6 come only from accum 0..9 (:640-:642). `reflected` at :630 reads `accum[0]` plus `lup`/`reflection_factor` only.
- `_longwave_serial` (:651-711): same structure; cardinal writes :669/:671/:683-:684/:692/:703, reads only :707-:710. CONFIRMED.
- `_longwave_fused` (:716-785): cardinal writes :743/:745/:757-:758/:766/:777, reads only :781-:784; the `masks` capture (:730) is primary state consumed by the reflected sweep (:770) and is retained in the reduced fused kernel. CONFIRMED.
- `_longwave_fused_serial` (:789-858): same; reads only :854-:857. CONFIRMED.
- The deleted cardinal loops read only inputs (`gate`, `directions`, `sky*sky_side`) and unmutated locals (`vegetation_side`, `sun_side`, `shade_side`, `side`); they write no primary accumulator and guard no primary operation, so removal cannot alter accum 0..9 or control flow. No fastmath (`fastmath=False` preserved, e.g. candidate module line 92/136/180/233), no expression regrouping.

Consumer sweep (all of `src/`, not just cited lines):

- `engine.py:1650` is the **only** `Lcyl_v2022a` call site (compiled wrapper at :1766-:1769 → `patch_radiation.py:903`). Under `cyl==1 ∧ anisotropic_sky==1` (the demand's domain), Tmrt's `Sstr` (:1667) uses only `Ldown` (col 0) and `Lside` (col 1); the cardinal `+=` sites run **after** Tmrt (:1671-:1675) and mutate only the returned `Least/Lsouth/Lwest/Lnorth`.
- `pipeline.py:267-277`: outputs consume only `Tmrt, Kup, Kdown, Lup, Ldown, Shadow` (+wetbulb path); cardinals appear in `RETURN_NAMES` (:31) but are dropped with `del result, fields` (:284). `models.py:10-11` `STATE_NAMES` carries no cardinal/Lside field (`accept` filters at :90-:93).
- Other consumers checked and ruled out: `aniLum` (engine.py:1561-:1564) is shortwave-region, computed before the Lcyl call, consumes `lv`/`diffsh` not Lcyl outputs; `Lside_veg_v2022a` (:1658) receives `Ldown` (col 0); the `cyl==0 ∧ aniso==1` branch (:1659-:1663) DOES consume cardinals before Tmrt — outside the demand's domain, see Finding 3. `L_patches` returned at :1676 is the input table, unaffected.

No missed consumer found. The reduction's backward slice is exactly output columns 0..1 for the demand's domain.

### Claim 2 — Guard mirroring in original order: CONFIRMED

`Lcyl_v2022a_primary` (cylinder_longwave.py:368-:374) mirrors `patch_radiation.Lcyl_v2022a` (:907-:913) guard for guard, in order: (1) `solar_altitude` ndarray check, (2) scalar-ndim tuple + `_supported` check, (3) `0 < n <= 609` — all falling back to the same `_reference('Lcyl_v2022a')`. `define_patch_characteristics_primary` (:317-:340) mirrors `define_patch_characteristics` (:864-:887) including kernel selection, `factor`, the `block_pixels<1` ValueError position, and `prepared` conditional. The band-flux loop and `model2` call (:376-:392) are statement-identical to :914-:931. Guard order matters for exception-vs-fallback selection and is preserved byte-semantically; `test_fallback_guard_order_preserved` verifies float64-cube and >609-patches fall back bitwise to the serial reference's six real fields, and scalar-altitude preserves the original `TypeError`, under **both** demands.

Fused gate: `_longwave_fused_primary_block` (cylinder_longwave.py:288-:290) imports and calls the **same** `_fused_enabled` function from patch_radiation (`SOLWEIG_LIGHT_FUSED_RAD == '1'`, default OFF, patch_radiation.py:131-:138); descriptor/preflight order mirrors `_longwave_fused_block` (:214-:234). Default-OFF exercised by every wrapper test (env unset → `reduced is None` → retained route).

### Claim 3 — Parity gates: CONFIRMED (run by this reviewer)

- `pytest tests/optimization_v6/cylinder_lw/ -q` in the candidate tree: **39 passed**, 4 pre-existing numpy RuntimeWarnings, exit 0 (matches evidence; parametrization count independently sums to 39).
- `run_L1.py` re-run: `{"all_passed": true, "cases": 32}`; wrapper/kernel/fused groups **byte-identical** to the committed `parity_results.json` (timing group differs, expected — contended tier, no claim).
- Bitwise claim: `conftest.bitwise_equal` (conftest.py:15-:20) asserts `np.array_equal(a.view(np.uint32), b.view(np.uint32))` — exact bit equality, NaN payload and signed-zero aware. Not a closeness check.
- Coverage spot-checks all present: raw-codebook/signed-zero/NaN/±Inf payloads (conftest.py:56-:83, :115-:141, coefficients :86-:112), `block_pixels ∈ {1,3,128,10⁶} × parallel both` (test :126-:136), 6-step day-night-day per-timestep chronology with per-step bitwise asserts (:153-:164), 90° gate boundary — `create_patches(2)` azimuths produce 3 patches with `|90° − azi| == 90.0` exactly under schedule `(10., 90.)` (verified numerically), zero-pixel domain (:213-:221), 14 degenerate input cases (:167-:192).

### Claim 4 — FULL_DIAGNOSTICS delegates to the untouched full path: CONFIRMED

`Lcyl_v2022a_by_demand` (cylinder_longwave.py:397-:410) forwards to `patch_radiation.Lcyl_v2022a` under FULL_DIAGNOSTICS (default, module :66) and raises on unknown demand; the reduced path is reachable only via explicit `PIPELINE_CYLINDERS_ANISOTROPIC`. `test_by_demand_dispatch_full_default` asserts bitwise equality with the direct full call for default and explicit FULL_DIAGNOSTICS. No reduced kernel is reachable under full demand.

### Claim 5 — Inertness: CONFIRMED

No import of `cylinder_longwave` anywhere under `src/` (grep over all `src/**/*.py`: zero hits outside the module itself). `git status` shows exactly the three untracked candidate paths and no modification to any tracked file. Default demand is FULL_DIAGNOSTICS; since the module is not imported, current behavior is untouched — additionally evidenced by the differential sweep result below.

### Claim 6 — Honesty: CONFIRMED

- Timing recorded as `tier='contended_development', claim='none'` (run_L1.py:121-:122); EVIDENCE.md presents the table with an explicit no-claim statement. Measured kernel-only ratios span 1.48x–1.74x (64² parallel is 1.48x; the coordinator's "~1.6-1.7x" paraphrase fits the serial cases; the evidence itself makes no claim — honest).
- `test_compiled_patch_parallel_diagnostics` not absorbed: independently verified pre-existing, see Finding 1.

## Findings

### 1. Pre-existing differential failure — CONFIRMED pre-existing, mechanism clarified (informational)

Differential sweep in the candidate tree: `634 passed, 1 failed` — exactly as evidenced. The failing test reproduces **without** the candidate module: run in this review worktree (`src/` identical between `0ff8cbce` and `5e1fab46`), it fails identically (`AttributeError: 'NoneType' object has no attribute 'get'` at `numba/core/dispatcher.py:968`, inside `parallel_diagnostics`). Additional nuance the evidence does not record: the failure is **numba njit function-cache-state dependent** — a cold-cache first run in this worktree PASSED, the warm-cache second run FAILED. The worker's "fails identically with the module physically removed" holds for warm cache (the state any full suite run leaves behind); a reviewer re-running from a clean cache may see it pass and should not mistake that for a fix or regression. Unrelated to C6-21; consistent with C6-22's independent finding.

### 2. EVIDENCE.md parity count misstated: "wrapper, 24 cases" is 22 (minor, documentation)

`parity_results.json` wrapper group has 22 cases (schedules 5×2 + degenerate 3×2 + block 4 + lup 2); total `cases: 32` is correct. Also, the block_pixels sweep inside run_L1.py ran `parallel=True` only (run_L1.py:153-:154); both-parallel block_pixels coverage comes from the pytest suite (`test_wrapper_lcyl_primary_bitwise`, 4×2), so the coverage claim is true of the bundle overall but the EVIDENCE.md sentence ("block_pixels ∈ {…}, parallel both … (wrapper, 24 cases)") overstates the JSON group. No correctness impact; fix the count when convenient.

### 3. Reduction domain and silent-omission risk live at integration time (minor, handoff — recipe NOT applied)

The reduction is valid only for `cyl==1 ∧ anisotropic_sky==1`. Under `cyl==0 ∧ aniso==1` the Lcyl cardinals feed Tmrt **before** the addition sites (engine.py:1659-:1663 → :1669-:1670). The proposed recipe's sentinel guards (`Least_ is not NOT_REQUESTED`) correctly preserve behavior under FULL_DIAGNOSTICS and the fallback domain (both tested), but they convert a mis-set demand + `cyl==0` from a loud `TypeError` into a **silent** cardinal omission in public `Least/Lsouth/Lwest/Lnorth` (and thus Tmrt via :1669). Combined with the recipe's process-global `set_demand` without restoration (pipeline loop entry; `demand_scope` noted only as an alternative), a reused worker process could carry the demand into a different later caller. The candidate module itself is inert and the enum name encodes the domain; recommendation to the integrator: prefer `demand_scope` (or restore after the loop) and assert `cyl==1` when opting in. Not a defect in the reviewed artifact.

### 4. Reduced kernels retain two dead parameters (informational, no action needed)

`_longwave_primary*`/`_longwave_fused_primary*` accept `directions` and `gate` but never read them (signature parity with the full kernels and the shared driver call sites). Verified harmless (numba accepts unused args; tests pass); retained for drop-in call-site symmetry. Acceptable as-is.

## Verdict

**APPROVE-WITH-NOTES** — 4 findings (0 blocking; 1 minor documentation, 1 minor integration-time handoff, 2 informational).

The core R-B reduction is independently re-derived and correct for all four kernel variants; guard mirroring and order are faithful; parity is bitwise-uint32 and reproduces exactly; the FULL_DIAGNOSTICS default delegates to the untouched full path; the module is inert; the honesty claims hold, including the pre-existing failure which I reproduced without the candidate module and additionally traced to numba cache warmth (Finding 1). Findings 2-3 should accompany the artifact to the integrator; neither blocks.
