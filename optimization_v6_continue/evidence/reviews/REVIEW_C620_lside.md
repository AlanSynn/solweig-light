# REVIEW_C620_lside — independent review of C6-20 anisotropic Lside private specialization

- Reviewer: C6-60 (independent GLM review; Opus unavailable), service instance for SOLWEIG-light v6
- Date: 2026-09-21
- Candidate: worker v6-lside, worktree `/Users/alansynn/Workspace/solweig-light-v6-lside`, detached at `5e1fab467f7e6038dcf3992cb694008a51ea2c58`
- Review worktree: `/Users/alansynn/Workspace/solweig-light-v6-rev620`, detached at `01092950bd710ab91ec6647e446d6362ba3c0616` (engine.py and `_math_profile.py` are byte-identical between 01092950 and 5e1fab46, verified by `git diff 01092950 5e1fab46 --stat` on both files)
- Interpreter: `/Users/alansynn/Workspace/solweig-light/.venv-light/bin/python`

## Late-write / integrity check

All seven sha256 anchors in `evidence/lside/commands.txt` re-hashed at review time match exactly
(`pipeline_demand.py` 0b837791…f18d856; three test files; `run_l1_evidence.py`; recipe diff; latest
`l1_parity_and_timing.json` 8ef8f8d3…c07b74). `git status` in the candidate worktree shows exactly the
declared untracked additions and an empty tracked diff — no shared-file edits, no late writes.

## VERDICT: APPROVE-WITH-NOTES

5 findings (0 blocking; 1 medium latent, pipeline-unreachable; 2 low; 2 informational).

## Claim-by-claim verification

### 1. R-A core — VERIFIED, reduction complete (re-derived independently from base source)

Re-derived from `engine.py` at 5e1fab46. Under `anisotropic_longwave == 1` each direction block of
`Lside_veg_v2022a` is exactly:

- E: `engine.py:1397-1398` `Lground = _operate(np.multiply, LupE, 0.5); Least = Lground`
- S: `engine.py:1420-1421`, W: `engine.py:1443-1444`, N: `engine.py:1466-1467` (same shape)
- Return: `engine.py:1476` `(Least, Lsouth, Lwest, Lnorth)` — the function exports nothing else
  (the 6-tuple docstring at `engine.py:1363` is stale; the code returns 4 values).

Consumer census: the sole call site is `engine.py:1658`, unpacking exactly those four names;
downstream (`engine.py:1659-1675`, Sstr/Tmrt and Lcyl addition branches) consumes only the four.
No intermediate of the prologue (svfalfa\*, vikt\*, Lsky_allsky, azi\*, Lwallsun, Lwallsh) escapes the
function, and the `Ldown` argument is never read on the anisotropic path (contrast the isotropic
branches at `engine.py:1400-1404` etc.). The pipeline profile therefore demands exactly
`_operate(np.multiply, LupX, 0.5)` per direction and nothing else — the candidate's
`_demanded_anisotropic_result` (`pipeline_demand.py:306-315`) is the identical original operation on
the identical operands, so bitwise equality is structural, not statistical. The reduction is complete.

### 2. Two-tier guard and warning contract — VERIFIED, documented delta acceptable

- Tier A/B split and per-direction `log_dirs` logic: `pipeline_demand.py:257-282`. Tier B re-executes
  the original `subtract` + `np.log` pair via the original `_operate` (`pipeline_demand.py:290-303`),
  same ufunc, same values, same errstate regime.
- Warning contract: I re-ran the harness twice; stderr shows exactly the documented delta
  (`pipeline_demand.py:303` vs `engine.py:1370`, both `RuntimeWarning: divide by zero encountered in
  log`, identical text). The harness compares full warning streams per step under
  `simplefilter('always')` (no dedup) — all 4 parity blocks report `warnings_match_reference: true`.
- Dedup semantics: Python's "default" action dedups in the `__warningregistry__` of the calling
  module, and numpy attributes ufunc warnings to the Python frame that invoked the ufunc, so the
  candidate's registry (pipeline_demand) is distinct from the original's (engine). Homogeneous
  streams therefore dedup identically: my probe measured 1 warning over 5 fast-path calls vs 1 over
  5 original calls under the default filter — per-stream count parity holds; a mixed
  original-then-fast-path process could register the warning once at each location. README.md:76-85
  documents exactly this. Acceptable: the delta affects only the reported source file:line, not the
  stream semantics.
- Only-logged-when-needed: original always evaluates the log but warns only for svf==1 pixels;
  candidate evaluates it only for those directions — warning streams identical either way (suite
  `test_tier_a_no_warnings`, `test_tier_b_warning_count_per_direction`).

### 3. Admission domain (worker's flagged note) — functionally sound; one coverage gap (F2)

Structural argument, then probes (all 16²):

- The demanded result depends only on `Lup*`; svf dtype cannot affect values because the candidate
  returns the exact original multiply. Extended precision (longdouble Lup) cannot diverge — the
  candidate does not recompute in float64; it calls the identical `_operate`. Note on this platform
  (arm64 Darwin) `np.longdouble` IS float64 anyway.
- Original must not raise before the anisotropic branch for admitted dtypes: for svf in [0,1] of any
  dtype, the only FP event is `log(1-svf)` at svf==1 (warning, not error, under the guard-enforced
  default errstate). `Lvikt_veg`'s powers are integer exponents — integer svf overflow would be
  silent in the original, so candidate silence is parity, not divergence.
- int64 svf: covered by the suite (`svf_int` mode, all shapes/steps, fast path asserted, bitwise).
- longdouble svf: covered by the suite (`test_exotic_inputs_match_original`) and re-verified by my
  probe with longdouble Lup + longdouble svf==1: fast path, warning parity, bitwise, Least dtype
  preserved.
- bool svf: NOT covered by the suite anywhere (three test files read in full). My probe: bool
  all-True svfE (Tier B) and mixed bool svfN — both fast path, warning parity exact, bitwise equal.
  Functionally sound; untested (finding F2).
- Empty arrays: suite asserts fallback + parity. My probe (30 reps) shows `_array_range` on an empty
  float32 array returns (0.0, 0.0) from an out-of-bounds `a[0]` read in the numba kernel
  (`pipeline_demand.py:142-143`, boundscheck off) — the fallback actually comes from the broadcast
  check `(0,0)` vs `(16,16)` failing, i.e. conservative-by-accident, stable in practice (finding F3).
- Silent-vs-warn: no admitted dtype case found where the original warns and the candidate stays
  silent; Tier B reproduces the one dtype-relevant warning.

### 4. Fallback correctness — VERIFIED in source and by tests

- Guard-exception (object/string/exotic): `pipeline_demand.py:283-287` → `_GuardResult(False)` →
  original at `:356`.
- Non-default `np.geterr()` (including `under='warn'`, which gates the removed Lvikt polynomial
  underflow): `pipeline_demand.py:209-210` → original. Suite
  `test_seterr_under_warn_falls_back_with_identical_warnings` asserts spy==1, warning-stream parity
  AND bitwise equality under `under='warn'`.
- Warning filter promoted to error: Tier B replication raises → caught at
  `pipeline_demand.py:350-354` → original re-runs, so the error raises from the original site; suite
  asserts spy==1 for both `filters=['error']` (RuntimeWarning) and `errstate divide/invalid='raise'`
  (FloatingPointError) with matching class+message.
- `anisotropic_longwave != 1`: guard rejects at `pipeline_demand.py:222-223` → full original
  isotropic branch; suite additionally asserts the isotropic result DIFFERS from the naive halving.
- FULL_DIAGNOSTICS/default: `pipeline_demand.py:331-338` calls the original verbatim; suite asserts
  arg-identity through a spy plus bitwise equality.

### 5. Demand plumbing — VERIFIED; one integration risk noted (F4 informational)

- `threading.local` state (`pipeline_demand.py:362`); context manager saves/restores the previous
  value, nests correctly, rejects non-members; default is FULL_DIAGNOSTICS. Suite includes a
  cross-thread isolation test.
- Cycle-freedom: `pipeline_demand.py` imports engine only lazily inside functions
  (`:299`, `:308`, `:329`); its top-level imports are stdlib/numpy/numba + `._math_profile`, whose
  imports (stdlib/numpy/`._sleef_*`/`._jit_cache`) never reference engine. Verified structurally and
  by the worker's simulated-import command.
- Recipe (`integration_patch_recipe.diff`): the import-hunk context matches engine.py's actual
  import block (`from osgeo import gdal, osr` / `import datetime` / `import calendar` / `import
  scipy.ndimage.interpolation as sc`), and the call-site hunk text matches `engine.py:1658`
  verbatim, adding `demand=current_demand()`. I confirmed `engine.py:1658` is the ONLY call site of
  `Lside_veg_v2022a` in src.
- Risk: a worker thread that escapes the `radiation_demand(...)` context resolves
  `current_demand()` → FULL_DIAGNOSTICS → untouched original. That is a silent performance cliff,
  never a correctness failure; each tile/worker thread must wrap its own stage (recipe states this).
  The call site passes `azimuth.item()` and `t=0.0` scalars, which also keeps the real pipeline
  outside finding F1's domain.

### 6. Tests — RUN MYSELF, VERIFIED

- `pytest tests/optimization_v6/lside -q` in the candidate worktree: **62 passed** (exit 0),
  matching commands.txt. (The `overflow encountered in cast` warnings in the pytest summary
  originate from `engine.py:1703` inside the original's own arithmetic on the fallback-domain
  reference runs, e.g. SBC=1e38 float64→float32 — identical on both sides.)
- Harness re-run twice: verdict **ALL_BITWISE_OK**, all four parity blocks (128 clean x24,
  128 svfE==1 x24, 128 svfE=1.5 fallback x4, real fixture 32x35 x24) bitwise OK with per-step
  warning streams matching; fixture stats reproduce (svfE min 0.184, max 1.0, 615 exact-1.0 pixels).
- Parity assertions are genuinely bitwise: `tobytes()` equality plus dtype and shape checks
  (`test_lside_bitwise_parity.py:44-53`, harness `compare()`), no allclose anywhere in the suite.
- Inertness: `grep -rn pipeline_demand src/` finds no references outside the new module itself; no
  `src` file imports it; candidate worktree tracked diff is empty.

## Findings

1. **[Medium — latent, not pipeline-reachable] Guard admits unbounded array azimuth/t at night;
   removed azi\* ops can overflow-warn in the original while the candidate stays silent.**
   `pipeline_demand.py:232` requires azimuth/t to be 0-d only when `altitude > 0`, and
   `pipeline_demand.py:234-237` bounds them only when 0-d. But `engine.py:1375-1378` computes
   azi\* = azimuth±t unconditionally, before the altitude branch. Verified by probe: night
   (`altitude=-5.0`) with float32 arrays `azimuth = t = 3.0e38` (16²) — candidate takes the fast
   path (spy 0 fallback calls), original emits 4x `RuntimeWarning: overflow encountered in add`;
   candidate emits none. Returned values remain bitwise-equal (azi\* unread at night), so this is a
   warning-stream contract gap, violating the module's own "preserving every warning ... bit-for-bit"
   claim (`pipeline_demand.py:327`) and the README envelope line "azimuth/t/altitude in
   [-1e6,1e6]" (README.md:47-49), which the guard enforces only for 0-d inputs. NOT reachable from
   the integrated call site (`engine.py:1658` passes `azimuth.item()` and scalar `t=0.0`), so it
   does not block C6-20; it should be fixed before any broader reuse of the module: require
   ndim==0 for azimuth/t regardless of altitude sign, or elementwise-bound the array case.
2. **[Low — test coverage gap] No bool-svf test despite bool being an admitted dtype.** The suite
   covers int64 (`svf_int`) and longdouble (`test_exotic_inputs_match_original`) but bool appears in
   no test. The dispatch claim "all admitted domains tested bitwise" is therefore inaccurate as
   stated. My probe shows bool svf is sound (Tier B fires, warning parity exact, bitwise equal, fast
   path), so this needs one added test, not a code change.
3. **[Low — robustness] `_minmax_1d` reads `a[0]` before any size check** (`pipeline_demand.py:142-143`,
   numba boundscheck off). On empty float32/float64 arrays this is an out-of-bounds read; it
   currently returns the buffer placeholder (0.0) and the case falls back only because the
   subsequent broadcast check fails — conservative by accident, stable across 30 probe reps, but
   the designed behavior should be an explicit `a.size == 0` early-out.
4. **[Informational — documented, accepted] Warning dedup-location delta** (`pipeline_demand.py:303`
   vs `engine.py:1370`) is real, reproduced at review time, class/message/per-stream-count identical;
   registry semantics confirmed per-calling-module, so homogeneous streams never change count.
   Accept as documented (README.md:76-85).
5. **[Informational — precision of evidence prose] README margin claim overstated.**
   README.md:56-57 states all intermediates are ">= 1000x below the float32 overflow threshold", but
   the README's own worst case (Lwallsun ≤ 1e4·2.7e13·9e14·2001 ≈ 4.9e35) gives ~700x against
   3.4e38 (≈350x if viktwall is taken as a difference up to 1.8e15). Immaterial to safety — still
   two orders below overflow — but the stated margin should read "hundreds-fold", not ">=1000x".

## What was NOT re-verified

The worker's internal envelope probes B1/B2 were not re-run; instead I independently re-derived the
envelope arithmetic (polynomial ≤4.05e15, Lsky_allsky ≤2.6e19, Lwallsun chain ≤~9.7e35 — all
float32-safe; divides only by the constant 4.4897; integer-exponent powers so no invalid) and
confirmed the removed-op silence logic, including the night-branch Tw/F_sh unread argument and the
`Lsky_allsky` broadcast group check. Timing numbers are recorded as contended-host observations and
carry no claims; I did not re-time.

## Bottom line

R-A is correctly derived and completely specified; the fast path is bitwise by construction and by
demonstration; the guard is sound for the real pipeline call site; fallbacks preserve warnings,
errors and values; the suite passes and the evidence is honest (the worker self-flagged the
dtypes/empty-arrays note and the warning-location delta). Findings 1-3 are latent hardening/coverage
items, none reachable from the integrated call site. **APPROVE-WITH-NOTES** for integration into the
C6 wave, with findings 1-3 recommended for the integrator backlog.
