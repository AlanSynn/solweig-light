# C6-22 evidence: cylinder shortwave narrow scratch

Worker: C6-22 (numerical_implementer), served model GLM via Z.ai routing (recorded per
MODEL_ROUTING; no other model identity claimed). Base: detached worktree at `5e1fab46`.
Owned paths only: `src/solweig_light/radiation/cylinder_shortwave.py` (new private
module), `tests/optimization_v6/cylinder_sw/`, this evidence directory.

## Verdict

IMPLEMENTED, gates met, pending independent numerical review. The narrow cylinder
shortwave specialization is bitwise-identical to the retained production route on all
seven public fields across real captured boundaries, adversarial schedules and a
24-step solar arc, with no box-only scratch under the admitted demand profile.

## R-C source verification (base 5e1fab46)

- `patch_radiation._shortwave` writes columns 4..19 only in its `box` branch
  (patch_radiation.py:310-335); with box=False columns 4..19 remain at the
  `np.zeros((pixels,20))` initialiser (line 296) and `directions`, `diff_gate`,
  `ref_gate`, `box_gate` are never read.
- Wrapper cylinder assembly reads `reduced[:,0..3]` only and builds KsideI plus the
  four Kup/2 fields outside the kernel (patch_radiation.py:546-550, 573-576). Seven
  demanded fields: Keast/Ksouth/Kwest/Knorth = Kup*/2, KsideI (direct), KsideD, Kside.
- Serial engine reference cylinder branch returns the same seven fields
  (engine.py:555-559, 635). Box-only wrapper setup under cylinder: `directions` loop
  and `box_gate` difference list (patch_radiation.py:535-543).
- No counterexample found: no cylinder route consumes columns 4..19 or the removed
  wrapper setup. The narrow-footprint claim of R-C holds for shortwave.

## Removed box-only work and its observability audit

Removed under the admitted profile: the 20-column kernel scratch (-> 4 columns,
80 B -> 16 B per pixel row per block), the per-call `directions` cosine table
((patches,4) plus patches `np.cos` evaluations), the `box_gate` difference list, and
gate pass-through (pure references, no arithmetic). The removed evaluations can emit
invalid-value warnings or raise for nonfinite/exotic inputs, so the entry declines
(returns None -> generic route) unless `t`, solar `azimuth` and patch azimuths are all
finite; any exception in the audit also declines. `box_gate`'s subtract is arithmetically
a subset of the kept `_class_coefficients` per-patch subtract, so the added warning
surface of the removal is the `directions` cosine domain, which the finiteness audit
covers exactly.

Slice nuance (recorded, tested in `test_cylsw_guards.py`): with `t=inf` the compiled
wrapper's removed direction work raises FloatingPointError under `np.seterr(all='raise')`
while the serial reference's cylinder slice never reads `t` and stays silent. The
wrapper is the production route whose behaviour the specialization preserves, so the
wrapper contract is the asserted oracle; serial comparison applies only where both
slices share the domain.

## Oracle structure and the pre-existing serial delta

At base, the retained compiled route is NOT bitwise-equal to the serial reference on
transcendental-driven fields: the cached geometry uses float32 `e._array(np.pi/180)`
radians while the serial engine uses a float64 `deg2rad` (patch_radiation.py:522+ and
`_cached_geometry` vs engine.py:476-477). Measured on the real captured case
`original-small-daytime-step12` (32x35, 153 patches), UNCHANGED by this task (present
with the module absent): wrapper-vs-serial bit diffs KsideD 764/1120, Kside 703/1120,
max |delta| 1.2e-4. Consequence: no specialization of this route can be bitwise vs the
serial translation. Therefore:

- Bitwise gate binds the entry to the retained compiled wrapper route it specializes
  (the arithmetic removed is provably dead under cylinder; kept arithmetic is line-
  identical). Result: 0 bit differences on every case, every field.
- Entry-vs-serial comparisons retain the UNTOUCHED upstream budget
  (`benchmarks/protocols/comparison_v1.json`: atol 0.05, rtol 1e-5) plus exact
  nonfinite-sentinel-mask equality, matching the existing differential suite's own
  contract. No tolerance was weakened or introduced.

## Parity results (real captured boundaries, `patch_radiation_original_cpu`)

13 captured Kside cases: 8 cylinder (raw/binary, patch options 1-4 incl. 145/153/305/609
patch vaults, and the real 32x35 scene with cyl=True), 5 box/control. Machine-readable:
`parity_record.json`.

- entry_vs_wrapper bit diffs: 0 across all cylinder cases, all seven fields,
  parallel and serial kernels, block_pixels=17.
- entry_vs_serial: all finite values within the original budget (max finite error
  1.221e-04 on `original-small-daytime-step12`/Kside, budget atol 0.05); nonfinite
  sentinel masks exactly equal on the raw-mode cases. KsideI is bitwise-equal to
  serial on every captured case; the Kup*/2, KsideD and Kside fields carry small
  pre-existing wrapper-vs-serial bit deltas (totals across the 13 cases: Keast 56,
  Ksouth 8, Kwest 39, Knorth 41, KsideD 764, Kside 703 — all within the untouched
  budget, present identically without this module).
- Adversarial synthetic schedules (16/32/64/128 square, six-patch vault): baseline,
  zero-sentinel (all-zero shmat/diffsh/Kup/radI/radD/shadow), extreme-sun
  (altitude 89.5, azimuth 359.9), vegetated (vegsh/vbsh all zero): bitwise vs wrapper
  route, within budget vs serial.
- 24-step solar arc (altitude 62 -> -53, azimuth 70 -> 284.8, 32x24): bitwise per
  timestep vs wrapper route, within budget vs serial at every step.
- Scratch gate: narrow kernel output shape asserted `(pixels, 4)`; original
  `_shortwave_serial(..., box=False)` columns 4..19 asserted identically zero on the
  same inputs (dead-work documentation); python-level allocation manifest of the entry
  asserted to be exactly the (7,pixels) output plane plus the scalar radTot — no
  (pixels,20) block, no (patches,4) directions table.
- Demand gate: default FULL_DIAGNOSTICS declines (returns None); unknown profile
  rejected with ValueError; box mode and isotropic mode never enter the narrow route
  even with the pipeline profile set; the entry never mutates the bound `values`.
- Guard gates: block_pixels=0 ValueError parity; nonfinite azimuth/t/patch-azimuth
  domains fall back with identical wrapper-vs-serial failure classes and warning
  flags, and bitwise-within-budget results where both complete; azimuth=inf under
  seterr raise -> wrapper and serial both raise FloatingPointError, entry declines;
  float64 raster profile -> entry declines, wrapper delegates to the serial reference
  bitwise; public wrapper full route verified within original budget vs serial under
  BOTH demand profiles on all 8 cylinder cases (gate 3; the generic wrapper is
  untouched — confirmed by git status showing no modification outside owned paths).

## Commands and exit codes

Interpreter: `/Users/alansynn/Workspace/solweig-light/.venv-light/bin/python`
(numpy 2.4.6, numba 0.67.0, CPython 3.11.16, macOS arm64 Darwin 25.6.0).
Run from the worktree root with `PYTHONPATH=<worktree>/src`.

| Command | Result |
|---|---|
| `pytest tests/optimization_v6/cylinder_sw/ -q` | 86 passed, exit 0 (final run 3.53 s) |
| `pytest tests/differential/test_patch_radiation.py -q` (with module) | 634 passed, 1 failed (pre-existing, see below) |
| same, module temporarily moved out | 634 passed, 1 failed (identical) |
| `pytest tests/differential/test_patch_radiation.py::test_compiled_patch_parallel_diagnostics -q` (module absent, fresh JIT cache) | 1 passed |

The `test_compiled_patch_parallel_diagnostics` failure is a pre-existing,
test-order-dependent issue in the differential file (numba dispatcher AttributeError
after the file's own `numba.set_num_threads` matrix), reproduced identically WITHOUT
this module in the tree; single-test execution passes with a fresh JIT cache. Not
caused and not fixed by C6-22 (outside owned paths).

## Timing (record-only, contended development tier)

Warm JIT, single process, alternating pairs, min of 5; `timing_record_only.json`.
Requested threads: numba default (as configured by host); no thread caps set.

| Cell | wrapper generic | entry narrow |
|---|---|---|
| packet 32x35x153, block 17, serial | 96.27 ms | 90.64 ms |
| packet 32x35x153, block 17, parallel | 106.34 ms | 104.94 ms |
| synthetic 128x128x153, block 128, serial | 266.03 ms | 267.76 ms |
| synthetic 128x128x153, block 128, parallel | 297.06 ms | 293.18 ms |

Interpretation guard: the reduction-scratch cut is 80 B -> 16 B per pixel row per
block, but decode + class computation dominates the warm kernel-only wall time on
these cells; observed deltas are at noise level. Consistent with the dossier's bound:
this is a scratch/allocation specialization, not a stage speedup claim. No performance
claim is made from these contended-tier numbers.

## Artifact hashes (sha256)

```
3273def45b23e1ec9a65d8d4d92dfa069fe53c010568b113cb1ff8697d5c0f9b  src/solweig_light/radiation/cylinder_shortwave.py
9b0e01fb4f38830dd34fe0d9f5aecadca410f0c8a4a2401381353d53126481be  tests/optimization_v6/cylinder_sw/conftest.py
e42c1c69c3a437dc22dbde58f74ea0faa00e125746b2ed728eadc79bad765d99  tests/optimization_v6/cylinder_sw/test_cylsw_demand.py
582629d18612e8d28b4adb672a31cafe70d4045950df8b795883b18dbdc0e0ef  tests/optimization_v6/cylinder_sw/test_cylsw_guards.py
d08b39a7dfb712f6a59eaa460bfea34f37c7efe6fbdf23c7f9adb2460f295b53  tests/optimization_v6/cylinder_sw/test_cylsw_parity.py
7776d06fe6f4b34da5706781a743bd1cb3ac480ff90d804580b43f5826790a29  tests/optimization_v6/cylinder_sw/test_cylsw_scratch.py
6350d295f8c6a557ec861d4520a1a0886d86958458d932c99b96c9b9a84900de  optimization_v6_continue/evidence/cyl_sw/timing_record_only.json
88c1a481296bcf991a0fdc37346f669a1e73c50e1c78b32670e894f3504bd35f  optimization_v6_continue/evidence/cyl_sw/parity_record.json
```

## Integration

`INTEGRATION_RECIPE.md` in this directory: exact two-patch recipe (wrapper dispatch
hook + pipeline demand wiring) for the integrator-owned files, plus post-integration
checks. `engine.py`/`pipeline.py` were not modified by C6-22.

## Unresolved items / hand-off notes

1. Independent numerical review required per TASKS_CLAUDE.yaml (`requires_independent_review: true`).
2. L2 family/integration chronology comparison (real TIFF, all carried state, per
   timestep) is the family owner's gate after the integrator applies the recipe.
3. The pre-existing `test_compiled_patch_parallel_diagnostics` order dependence in
   `tests/differential/test_patch_radiation.py` is recorded here for the family owner;
   it reproduces without this module and is untouched per shared-file authority.
4. Demand-profile wiring site in `pipeline.py` is deliberately left to the integrator;
   the entry is safe to call un-wired (declines under FULL_DIAGNOSTICS default).
