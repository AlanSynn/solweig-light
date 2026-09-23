# Independent review — C6-22 cylinder shortwave narrow scratch

- Reviewer service: C6-60. **Independent GLM review; Opus unavailable** (routing: GLM via Z.ai, recorded per MODEL_ROUTING).
- Date: 2026-09-21. Candidate: worker v6-cylsw, worktree `/Users/alansynn/Workspace/solweig-light-v6-cylsw`, detached at `5e1fab46`.
- Reviewer worktree: `/Users/alansynn/Workspace/solweig-light-v6-rev622`, detached at `0ff8cbce` (`src/solweig_light/radiation/` and `src/solweig_light/geometry/` verified byte-identical to `5e1fab46` via `git diff --stat 5e1fab46 0ff8cbce`, so base reproductions here are faithful).
- Integrity: candidate module sha256 `3273def45b23e1ec…` and all five test/evidence hashes match the EVIDENCE.md manifest; late-write re-check at review end found no changes (still only the three owned untracked paths at `5e1fab46`).
- Interpreter: `/Users/alansynn/Workspace/solweig-light/.venv-light/bin/python` (numpy 2.4.6, numba 0.67.0). No edits to the candidate worktree; the candidate module+tests were copied into the reviewer worktree for execution.

## VERDICT: APPROVE-WITH-NOTES

8 findings verified (F1–F8, all PASS), 2 minor evidence-prose errors (M1–M2, machine record correct, prose wrong), 3 non-blocking notes (N1–N3). No correctness, parity-contract, inertness, or honesty problem found.

---

## Findings (claim → verification → verdict)

### F1 — R-C independence from source (Claim 1) — PASS

Claim: cylinder route consumes reduction columns 0..3 only; columns 4..19 and wrapper direction/box_gate work are box-only.

Verification (read at `5e1fab46`, candidate worktree tracked files):
- Kernel `_shortwave` allocates `np.zeros((pixels,20))` (patch_radiation.py:296); the non-box branch writes only columns 0..3 (patch_radiation.py:305-309); columns 4..19 are written exclusively in the `else`/box branch (patch_radiation.py:310-335). Same structure in `_shortwave_serial` (339-383) and both fused kernels (387-506).
- Wrapper cylinder assembly reads `reduced[:,0]`..`reduced[:,3]` only (patch_radiation.py:574-576); `output[4]` (direct) and `output[0..3]` (Kup/2) are built outside the kernel (546-550). The box-only consumers (`reduced[:,4+direction]` etc.) live only in the `else` at 577-582.
- Box-only wrapper setup under cylinder: `directions` cosine table (535-538), `diff_gate`/`ref_gate` pure references (539-541), `difference`/`box_gate` subtract (542-543). The box `angles`/`gates` block (552-556) is inside the `else`.
- Serial engine reference: cylinder branch returns exactly the seven fields (engine.py:542-559, return at 635: `Keast, Ksouth, Kwest, Knorth, KsideI, KsideD, Kside`), same five-term Kside addition order (engine.py:555 vs wrapper patch_radiation.py:575).
- No counterexample found: no cylinder-route consumer of columns 4..19 or of the removed wrapper setup exists at base.

### F2 — Pre-existing wrapper-vs-serial divergence, reproduced WITHOUT the module (Claim 2a) — PASS

In the reviewer worktree (sources = base, module absent; asserted via `find_spec` in the probe): real captured case `000-Kside_veg_v2022a-input.npz` (32x35 = 1120 pixels, 153 patches), wrapper compiled route (`block_pixels=17, parallel=False`) vs `engine._serial_Kside_veg_v2022a`:

| field | bit diffs (mine) | record | max finite err (mine) | record |
|---|---|---|---|---|
| KsideD | 764 | 764 | 9.155273e-05 | 9.155273e-05 |
| Kside  | 703 | 703 | 1.220703e-04 | 1.220703e-04 |
| KsideI, Kup*/2 | 0 | 0 | 0.0 | 0.0 |

Exact match to `parity_record.json` and to EVIDENCE.md. The divergence is pre-existing and unchanged by the module.

Mechanism check (code-level, confirms the worker's attribution is coherent): the cached geometry computes `solid_angle`/`sine` with float32 `radians=e._array(np.pi/180)` (patch_radiation.py:60, 65-68), while the serial `steradian`/`radTot` path multiplies float32 *patch scalars* by the float64 `deg2rad` (engine.py:476-477; `deg2rad=_divide(np.pi,180.0)` is a float64 `np.generic`, which `_array` passes through uncast per engine.py:1678-1681), and scalar-scalar NumPy ops promote to float64 — so `sin` is applied to differently-rounded arguments. This perturbs exactly the solid-angle-dependent fields (KsideD, and Kside which sums it), leaving KsideI and Kup*/2 clean — matching the observed diff pattern. (The worker's one-line summary "float32-vs-float64 deg2rad geometry profile" is accurate; the float64 constant is immaterial where it feeds array-scalar ops, but it is load-bearing exactly where the diffs appear.)

### F3 — No tolerance weakened (Claim 2b) — PASS

- `benchmarks/protocols/comparison_v1.json` is untouched (candidate `git status` shows only the three owned untracked paths; reviewer copy has atol 0.05, rtol 1e-05).
- The suite does not hardcode a budget: `conftest.assert_within_original_budget` (conftest.py:56, 59-76) reads `PROTOCOL['field_rules']['Kside_veg_v2022a/<field>']` live from the protocol file and additionally asserts exact nonfinite-sentinel-mask equality (conftest.py:69). No new or looser tolerance introduced anywhere in the test files.

### F4 — Judgment: wrapper-route bitwise binding is the correct parity contract (Claim 2c) — PASS

- The retained compiled wrapper (`patch_radiation.Kside_veg_v2022a`) is the production dispatch target under the admitted profile; the seven public pipeline results are its outputs. Binding the specialization bitwise to those outputs closes the only reachable gap: the kept kernel arithmetic is line-identical to `_shortwave`'s box=False branch (module lines 64-75 vs patch_radiation.py:297-309, same expressions, same accumulation order), and the removed arithmetic is provably dead (F1).
- Nothing is hidden: the wrapper-vs-serial delta is real but pre-existing at base, identical with the module absent (F2), and remains measured — the entry-vs-serial gate records the same per-field errors against the untouched comparison_v1 budget with exact sentinel-mask equality (parity_record.json: entry_vs_serial max err 9.155e-5 / 1.2207e-4 on case 000, `all_within_original_budget: true`). Serial-binding a specialization of a route that is not itself serial-bitwise is impossible without changing the route; the chosen split (bitwise entry↔wrapper, original budget entry↔serial) is the correct and only faithful contract.

### F5 — Decline-domain audit complete (Claim 3) — PASS

The removed evaluations read only `t`, solar `azimuth`, and patch azimuths:
- `directions` cos (patch_radiation.py:538): warns (`cos(inf)` invalid) or produces NaN payload for nonfinite `t`/`geometry.azimuth` — the entry requires `isfinite(t)`, `isfinite(azimuth)`, `isfinite(geometry.azimuth).all()` (module lines 115-118).
- `box_gate` subtract (patch_radiation.py:542): warns only for inf−inf — covered by the same two finiteness checks; the kept `_class_coefficients` performs the identical per-patch subtract in both routes, so nothing is added.
- Any exception in the audit or in `patch_geometry` declines (module lines 114-122, 137-140) → the untouched wrapper keeps its original failure order.
- Extra domains I probed beyond the worker's matrix: `t=nan` propagates quietly (cos of NaN warns nothing) but is dead under `box=False`, and the entry declines anyway → identical base behavior; huge-finite `t` (e.g. 1e30) is admitted, but the removed cos then neither warns nor raises and is dead, so admission is harmless; nonfinite `geometry.altitude` flows through `patch_geometry`/`_class_coefficients` identically in both routes (nothing removed reads it); ndarray/str `azimuth`/`t`, non-scalar forcings, dtype profile, `lv` bounds, `cyl!=1`, `anisotropic_diffuse!=1` all decline via module lines 107-112 mirroring wrapper lines 512-518.
- Test coverage is real: `test_cylsw_guards.py` mutation matrix (azimuth inf/nan/string, t=inf, patch-azimuth inf) asserts decline + identical wrapper-vs-serial failure classes + warning-flag equality where domains are shared (lines 87-109), seterr-raise FloatingPointError parity (112-127), float64-profile bitwise fallback (130-139), and the public wrapper within budget under both demand profiles on all cylinder cases (142-158).

### F6 — Inertness (Claim 4) — PASS

- `grep -rn cylinder_shortwave src/` hits only the module itself — not imported anywhere in `src` (pipeline.py and patch_radiation.py included). Wiring exists only as the two-patch recipe for integrator-owned files.
- Candidate `git status`: only `optimization_v6_continue/evidence/cyl_sw/`, `src/.../cylinder_shortwave.py`, `tests/optimization_v6/cylinder_sw/` (all untracked, no tracked-file modifications).
- Default `_demand_profile=FULL_DIAGNOSTICS` (module line 43) → entry returns `None` before touching anything (lines 133-134) → generic route. `set_demand_profile` rejects unknown profiles with `ValueError` (lines 49-50), tested including `None` and `1` (test_cylsw_demand.py:29-34). Box and isotropic modes decline even with the profile set (test_cylsw_demand.py:37-47).

### F7 — Scratch claims real (Claim 5) — PASS

- `test_cylsw_scratch.py:30` asserts kernel output shape `(pixels,4)`; lines 40-41 assert the original `_shortwave_serial(..., box=False)` columns 4..19 are all-zero **bits** on the same inputs and columns 0..3 match the narrow kernel bitwise. Both assertions are substantive and executed.
- The allocation gate (lines 67-82) records the entry's own `np.zeros/empty/ones` calls via a module-local proxy and asserts the `(7,pixels)` plane and the scalar accumulator are present and no `(x,20)` or `(patches,4)` shape occurs. Scope note (N3): the proxy patches only `cylinder_shortwave.np`, so it certifies the module's own python-level allocations — which is exactly what EVIDENCE.md claims ("python-level allocation manifest of the entry"). EVIDENCE.md's phrasing is accurate for that scope.

### F8 — Honesty (Claim 6) — PASS

- Timing is record-only and matches the raw data: every EVIDENCE.md table cell equals the min of the five samples in `timing_record_only.json` (96.27/90.64, 106.34/104.94, 266.03/267.76, 297.06/293.18 ms); the record includes cells where the entry is *slower* (128² serial), so no cherry-picking; "no performance claim" is stated in both files.
- Differential file reproduced in the reviewer worktree, both configurations, by me: **with** module 634 passed / 1 failed (`test_compiled_patch_parallel_diagnostics`, numba dispatcher AttributeError), **without** module (moved aside, then restored) 634 passed / 1 failed, identical failure. The worker did not absorb the failure and reported it correctly.
- Real vs synthetic labeling is consistent: packet cases sha256-verified against the manifest (conftest.py:29) and labeled; synthetic/adversarial cases generated deterministically and labeled as such (EVIDENCE.md "Adversarial synthetic schedules").
- Suite reproduced: `pytest tests/optimization_v6/cylinder_sw/ -q` → **86 passed** in the reviewer worktree with the candidate's byte-identical module (sha256 re-verified after copy).

## Minor findings (evidence prose vs machine record)

### M1 — Case-count split misstated in EVIDENCE.md — minor, prose only
EVIDENCE.md line 71-72 says "13 captured Kside cases: 8 cylinder …, 5 box/control". `parity_record.json` actually contains **9 cylinder** (000, 003, 010, 015, 022, 027, 034, 039, 046) and **4 box** (004, 016, 028, 040). Both sum to 13; all 13 captured Kside cases in the packet are covered (`packet_cases()` filter confirmed: 13 captured), so coverage is complete — only the split in prose is wrong.

### M2 — "Totals across the 13 cases" for KsideD/Kside are wrong in EVIDENCE.md — minor, prose only
EVIDENCE.md lines 81-83 cite totals "KsideD 764, Kside 703". Recomputed from `parity_record.json` across all 13 cases: **KsideD 823, Kside 739**; 764/703 are the case-000 (32x35) values alone (the other five fields' prose totals are correct: 56/8/39/41/0). The machine record is internally consistent (`entry_vs_wrapper_bit_diffs_total: 0` recomputed = 0; all `within_original_budget: true`), and the corrected totals do not change any conclusion (the max per-case error is unchanged), but the prose line as written misstates the record.

## Notes (non-blocking)

- **N1 — Fused-env pinning.** The base wrapper tries `_shortwave_fused_block` first (patch_radiation.py:563), which activates only under `SOLWEIG_LIGHT_FUSED_RAD=1` (patch_radiation.py:131-138, default OFF). The entry always uses the retained ordered-decode route. If both the env flag and the pipeline profile are set, the entry pins retained-route results; acceptable given the fused route's own drop-in contract, but the integrator may want the entry to decline when `_fused_enabled()` to keep the env switch semantically total. The INTEGRATION_RECIPE already documents that the fused route is not activated (line 51-52).
- **N2 — Process-global demand profile.** `set_demand_profile` mutates module-global state; the recipe correctly prescribes try/finally restoration (lines 62-70). Integration must not skip the `finally`.
- **N3 — Allocation-gate scope.** See F7; the gate certifies the module's own python-level allocations, not allocations inside reused `patch_radiation`/`engine` helpers or inside the JIT kernels. This matches the EVIDENCE wording but is narrower than a casual reading of "no box-only scratch" might suggest. The JIT-kernel scratch itself is (pixels,4) by construction (module lines 63, 83) and shape-asserted.

## Verification commands run (reviewer worktree)

- `pytest tests/optimization_v6/cylinder_sw/ -q` (candidate module+tests copied in, sha256 match) → 86 passed.
- `pytest tests/differential/test_patch_radiation.py -q` → 634 passed, 1 failed; repeated with module removed → identical 634/1.
- Base wrapper-vs-serial bit-diff probe on `000-…-input.npz` without the module (table in F2).
- `parity_record.json` count/total audit (M1, M2); sha256 manifest and late-write re-check (all match).

## Hand-off

Approved for integration per `INTEGRATION_RECIPE.md`. The two prose corrections (M1, M2) should be applied to EVIDENCE.md by the evidence owner or noted in the ledger; neither blocks integration. Post-integration L2 chronology remains the family owner's gate as recorded in EVIDENCE.md.
