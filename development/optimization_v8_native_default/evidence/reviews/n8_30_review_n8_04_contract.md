# N8-30 review of N8-04 — typed longwave contract freeze

**Verdict: APPROVE-WITH-NOTES.** No blocking defects, no required repairs.
Machine-readable twin: `n8_30_review_n8_04_contract.json` (same directory).

Reviewer: independent N8-30 review service; did not author N8-04.
Scope guard: nothing outside `optimization_v8_native_default/evidence/reviews/`
was written; no network; no commits. Repo at `16cdc56c`
(`perf/native-optimization`, worktree `/Users/alansynn/Workspace/solweig-v8-native`).

## 1. Contract fidelity vs source — PASS

The frozen graph matches `_longwave_primary` / `_longwave_primary_serial`
(`src/solweig_light/radiation/cylinder_longwave.py`) operation-for-operation:

| contract element | code | check |
|---|---|---|
| sky / veg / building predicates, exact `(RN32(1f-sh)*vb)==1` compare | :100-102 | match; IR shows `f32 == Literal[int](1) :: bool` (truth-identical both typings — the contract says so itself) |
| pure-f32 sky chains `RN32(a+RN32(sky*sky_x))` | :103-104 | match; IR shows `sky * sky_down :: float32` (predicate-as-number) |
| ST chains `(((surface⊗solid)⊗cos|sin)⊗veg)` grouping | :105-108 | match; IR :1192-1211 shows the f64 chain, IR :1224-1227 shows `f64 add -> (float64,) -> float32` **single-round store** — exactly `a = RN32(f64(a)+c64)` |
| solar_gate REAL branch, gated grouping `((((surface⊗sun|shade)⊗solid)⊗cos|sin)⊗building)`, shorter else chains | :109-122 | match, incl. update order a8,a7,a3,a2 |
| reflection `RN32(RN32(RN32(RN32(a0+lup)*factor)*RN32(.5))/RN32(pi))`, division not reciprocal | :124 | match; IR :1561 `$binop_truediv ... :: float32` |
| sweep-2 occlusion number-multiply, a9/a4 | :126-130 | match |
| left-fold outputs, `output[:,2:7]=accum[5:10]` | :131-133 | match |

Lineage verified: `git diff dca2035c..HEAD` on the file adds only `import os`,
the `_lw_kernel` dispatcher and the single driver line — **no hunk touches
either kernel body** (pre-image blob `27ba6ce4...` = the JSON's
`b7_reducer_blob`); the two kernels are byte-identical modulo decorator and
`prange`→`range`; `sha256(inspect.getsource(fn))` reproduces both
`kernel_fn_sha256` values exactly; file blob/sha256 and `lw_primary.ispc`
sha256 all match the JSON.

## 2. Oracle independence — PASS

`tests/optimization_v8/reference/lw_reference_oracle.py` is a vectorized NumPy
re-implementation written from the contract text; it does not call or import
the kernels for its computation. A shared error with the kernels would require
a shared misreading of the source; excluded by (a) the direct source
comparison above, (b) my own exact-rational recomputation of every pin
(§below), (c) the B7 520-call capture replay pinning the kernels against
real-pipeline goldens. The `st_add_rule='round_chain_first'` mutation is
quarantined (raises outside the f64 profile; banner-labelled MUTATION).

## 3. Discriminator validity — PASS (hand-computed)

Computed with exact `Fraction` arithmetic + explicit round-to-nearest-even
binary32 emulation — independent of numpy/numba:

* **RN32 rule** (surface `1+2^-25`, solid `[2^24,1]`, cosine 1, veg on):
  contract path → patch0 `RN32(2^24+0.5)=2^24`, patch1
  `RN32(2^24+1+2^-25)` strictly above the `2^24+1` tie midpoint (ulp 2) →
  `2^24+2` = **0x4B800001**. Forbidden path → `RN32(1+2^-25)=1.0` (below the
  `1+2^-24` midpoint), then `RN32(2^24+1.0)` exact tie → round-to-even →
  `2^24` = **0x4B800000**. The discriminator genuinely distinguishes the two
  rules in IEEE binary32/64 semantics. Live run: kernel 0x4B800001, oracle
  0x4B800001, mutated mock 0x4B800000; mock still agrees on the benign input
  (faithful single-rule mutation with teeth).
* **pi division**: `x = 11+2^-20` (exactly the f32 literal);
  `RN32(x/RN32(pi))` = **0x40601716** vs `RN32(x*RN32(1/RN32(pi)))` =
  **0x40601715**; `RN32(pi)` = **0x40490FDB**.
* **profile separation**: f64 `RN32(1+2^-24+2^-49)` → **0x3F800001**; f32
  provenance rounds the scalar to 1.0, `RN32(1.0+2^-24)` tie-to-even →
  **0x3F800000**.
* **sweep order**: `[2^24,1,1]` → **0x4B800000**; `[1,1,2^24]` →
  **0x4B800001** (both sweeps; sweep 2 via `lup=2·pi32` making reflected
  exactly 1.0).
* **building raw values**: `RN32(1-(1-2^-23)) = 2^-23` (Sterbenz-exact);
  `2^-23·2^23 == 1` **true**, `2^-23·1 == 1` **false**.

The mutation test exists and is clearly labelled
(`test_rn32_accumulation_rule.py:93-114`, "MUTATION CHECK (teeth)").

## 4. Domain coverage vs KERNEL_CONTRACT.md — PASS WITH NOTES

Covered: B=0/1, W=8 tails 7/8/9, primes 11/13; P∈{1,2,3,5,7,11,13,153}+609
boundary; strided/one-element/negative-stride sky columns; subnormals, ±0,
±Inf, NaN, near-one thresholds, finite cancellation, raw visibility values;
parallel==serial bitwise incl. (13,609); both surface profiles on the full
grid + separation pin; four gate patterns; 0·Inf / Inf·0 NaN pins; signed
zeros; division-not-reciprocal pin.

Non-blocking notes (none gates N8-12/13 acceptance today, all must be carried
forward):

1. **0-d ndarray `reflection_factor`** is declared admitted (and exists as a
   captured B7 specialization) but is not bitwise-exercised anywhere: v8 tests
   pass `np.float32` scalars; the v7 replay unpacks 0-d fixtures via
   `value[()]` (`test_v7_contract_freeze.py:46`). N8-12/N8-13: pin it or
   narrow the admission.
2. KERNEL_CONTRACT.md's **24/48-step real TIFF** end-to-end comparisons and
   **source-vs-installed-wheel** verification are deferred to the candidate
   gates (L2/L3) and N8-20/N8-23 — consistent with the contract's own §5
   checklist, but they must appear there.
3. solar_gate inactive-arm non-evaluation has **no value-observable** (the
   contract states this); IR-level obligation only — honestly recorded.

## 5. Golden hygiene — PASS

`git status --porcelain`: zero modified tracked files; only untracked
additions (`optimization_v8_native_default/`, `tests/optimization_v8/`,
`tools/optimization_v8/`). Nothing under `tests/reference/` or
`optimization_v7_backends/` touched. All twelve sha256 claims in the contract
JSON reproduce exactly (5 new test files, v7 replay test, 4 B7 captures,
`lw_primary.ispc`).

## 6. Suite run — PASS

`.venv/bin/python -m pytest tests/optimization_v8/reference/ tests/optimization_v7/reference/ -q`
→ **117 passed in 1.39s** (112 v8 collected + 5 v7 goldens), matching the
author's claim. Environment matches
the JSON (py 3.12.13, np 2.4.6, numba 0.67.0, pytest 9.1.1, arm64 macOS 26.6);
conftest pins `set_num_threads(min(4, NUMBA_NUM_THREADS))` with no
`NUMBA_NUM_THREADS` export (avoids the known v5 hazard).

## Record-precision notes (fix at next touch; not blocking)

* `admitted_input_domain.wrapper_level` in the contract JSON omits **`esky`**
  from the non-0-d guard key list; the code checks
  `('esky','Ta','Tgwall','ewall','solar_altitude','solar_azimuth')` at
  `cylinder_longwave.py:397`. Fallback-path documentation only; no effect on
  the typed graph or the executable gates.
* The "`==1` literal promotes to float64 compare" parenthetical is not
  directly visible in the IR dump (it shows `f32 == Literal[int](1) :: bool`);
  it is truth-identical in both typings, as the contract itself notes.
  Optional: soften the wording to "mixed literal compare, truth-identical".
