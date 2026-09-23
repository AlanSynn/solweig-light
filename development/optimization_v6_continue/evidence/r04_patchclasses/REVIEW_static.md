# Static review: R04+G06 exact patch-classification tables

Date: 2026-09-21. Reviewer: independent review via opus alias (GLM-5.3) —
not Anthropic Opus. Worktree: /Users/alansynn/Workspace/solweig-light-v6-r04
(detached at ae37d96b + uncommitted implementer changes).

Scope constraint honored: an exclusive timing lease was held by another
worker during this review. No tests, python, benchmarks, or any compute were
run. File reads and `git diff` only. All dynamic verification is deferred to
the integration gate.

## What was reviewed

- `git diff` (+117/−13, single file `src/solweig_light/radiation/patch_radiation.py`)
  and `git diff --stat`; `git status` (only that file modified; tests +
  evidence untracked).
- `src/solweig_light/radiation/patch_radiation.py` (full file).
- `src/solweig_light/radiation/_sleef_classifier.py` (atan_fma / atan_array),
  `src/solweig_light/radiation/_math_profile.py` (tan32 / atan32),
  `src/solweig_light/radiation/engine.py` `_operate`/`_divide`/`_operands`
  (engine.py:1683-1712), `cylinder_shortwave.py:125-180`,
  `cylinder_longwave.py` (public drivers).
- `tests/optimization_v6/patchclasses/` (conftest + 3 test modules).
- `optimization_v6_continue/evidence/r04_patchclasses/NOTES.md`.
- `optimization_v6_continue/dossiers/08_residual_strategy_register.md`
  (R04 line 15, G06 line 28 + exclusions §).
- `optimization_v6_continue/evidence/selection/C6-81r_selection_reopened.md`.

## 1. Exactness — VERIFIED (static argument; bitwise proof deferred to tests)

- Coefficient chain verbatim: the diff moves the retained loop body unchanged
  into `_class_coefficient` (patch_radiation.py:261-275); the gate-off loop
  now calls that helper per patch (:312-313). Identical `_operate`/`_divide`
  calls, operand objects, operand order, and the separate store-cast into the
  float32 table. `deg2rad=e._divide(np.pi,180.0)` stays inside the helper
  (recomputed per evaluation, pure function of constants — identical bits);
  the two separate multiplies (`2*xi`, then `*tan(...)`) and
  `np.where(yi>0,0.0,yi)` are unreassociated; all NumPy scalar ops, no FMA.
- G06 key construction: `states=np.ascontiguousarray(geometry.azimuth).view(
  np.uint32)`, `key=int(states[patch])` (:302-305). Integer dict keys over
  raw bit patterns — no float `==` anywhere in the dedup. Signed zeros
  (0x00000000 vs 0x80000000) and every NaN payload are distinct keys. The
  float32 dtype of `geometry.azimuth` is admission-guaranteed (:287-290), so
  the uint32 view is per-element exact. The NOTES claim holds.
- "Full source-state tuple": within one `_class_coefficients` call the chain
  consumes azimuth (call-fixed), altitude (call-fixed), and patch_azimuth
  (keyed). The helper references no other per-patch input — no `field`/`asvf`
  use in its body — so keying on the patch-azimuth bits is equivalent to
  keying on the full tuple. No equality shortcut that merges distinct states.
- Block pass arithmetic: `delta=np.float32(value+coefficients[column])`
  matches the retained elementwise `np.add(tan32(field),coefficients[None,:])`
  (f32+f32); `degrees=np.float32(atan_fma(delta)*radians_to_degrees)` matches
  `np.multiply(atan32(delta),np.asarray(rad2deg,dtype=f32))` — rad2deg is
  extracted as an np.float32 scalar via `[()]` (:338,:342), which numba types
  float32, so the product is a single f32 multiply, then strict `<`/`>`
  against per-column `geometry.altitude[indices]`. Kernels are
  `fastmath=False, error_model='numpy'` (:360,:383), matching `atan_array`;
  no `a*b+c` pattern exists to contract.
- SLEEF core identity: `atan_array` is literally `out[i]=atan_fma(a[i])`
  (_sleef_classifier.py:141-146) and `atan32` dispatches float32 to it
  (_math_profile.py:87-92). The same njit function object (`inline='always'`,
  float32 signature) is inlined into `_classes_table`; under IEEE semantics
  with fastmath off and an explicitly emitted `llvm.fma.f32`, bit-equality
  across the two caller compilations is structural. The operative proof is
  the bitwise parity tests, which are deferred to the integration gate.

## 2. Gate — VERIFIED

- Strict check `os.environ.get('SOLWEIG_LIGHT_PATCH_CLASS_TABLES') == '1'`
  (patch_radiation.py:158); unset/empty/'0'/'true'/'on'/'1 '/'1x'/'TRUE' all
  keep the retained route (unit-tested in test_patchclasses_route.py:169-182
  and test_patchclasses_tables.py:113-121). Default OFF.
- Coverage: the gate lives at the two choke points every classification
  consumer funnels through — `_class_coefficients` (:293) and `_classes`
  (:327, inside `prepared is not None` and `indices.size`). Verified call
  sites: `Kside_veg_v2022a` (patch_radiation.py:676-679),
  `define_patch_characteristics` (:1004-1007), `kside_cylinder_anisotropic`
  (cylinder_shortwave.py:166,170), and the cylinder-longwave drivers
  `define_patch_characteristics_primary` / `Lcyl_v2022a_primary` /
  `Lcyl_v2022a_by_demand` (cylinder_longwave.py:340-343). A src-wide grep
  finds no other callers. Coverage through the choke points alone suffices;
  no wrapper was edited and no signature changed (`_classes` and
  `_class_coefficients` signatures are byte-identical to before).
- Unsupported profiles (non-f32 rasters, non-0d solar scalars) still return
  `prepared=None` and fall to the serial `shaded_or_sunlit` loop before any
  gate check — the gate cannot touch them.

## 3. Scatter correctness — VERIFIED

The shared coefficient is a pure function of (azimuth, altitude,
patch_azimuth bits); the first two are fixed within a call, so one verbatim
evaluation per class is valid and the scatter (`coefficients[column]=
evaluated[key]`, f32→f32 store) copies stored bits with no second rounding.
The block pass consumes each member's own `geometry.altitude[indices]`
per column, so class members with distinct altitudes are never conflated.
Geometry arrays are immutable (`np.frombuffer` over `bytes`), so the uint32
key view and the `geometry.azimuth[patch]` value reads cannot diverge
mid-call. No non-keyed per-patch input exists to alias or mix.

## 4. Block pass — VERIFIED

- `tan32(field)` retained verbatim as the array pass feeding `heights`
  (:334-335); only temporaries/dispatch after it are removed.
- Kernels are serial (`range`, no `prange`) — no thread interactions, no
  NUMBA_NUM_THREADS coupling.
- Variant selection `indices[0]==0 and indices.size==indices[-1]+1` (:336)
  holds exactly for 0-based prefix runs (including, but not only, the full
  vault set); there positional column == indices[column], so direct
  `sun[row,column]` writes equal the retained `sun[:,indices]` assignment.
  All other subsets take `_classes_table_masked`, whose
  `sun[row,indices[column]]` indirection reproduces the retained fancy
  assignment; inactive columns stay False (zeros init) in both routes —
  consistent with the solar-gate semantics of `define_patch_characteristics`
  and the cylinder-longwave drivers. The empty set is guarded by
  `if indices.size:` (unit-tested: kernel monkeypatched to raise, never
  invoked).

## 5. Tests — VERIFIED (binding quality)

- Parity tests bind to the real ungated route, not a re-implementation:
  test_patchclasses_parity.py runs the public `Kside_veg_v2022a` /
  `Lcyl_v2022a` gate-off vs gate-on on cloned bundles, bitwise over every
  exported field; test_patchclasses_route.py differentials
  `_classes`/`_class_coefficients` off-vs-on and adds an independent
  `e.shaded_or_sunlit` oracle; test_patchclasses_tables.py checks the table
  against an external restatement of the chain (supplementary oracle, in
  addition to — not instead of — the route differential).
- Gate-off inertness: `test_gate_off_route_is_inert` monkeypatches
  `_classes_table` to raise and asserts it never runs gate-off, plus output
  equality. Gate strictness tested twice (see §2).
- Input admissibility: route-level `ALTITUDE_STATES` uses only 0-d ndarray
  altitude (the tensor-origin contract); wrapper-level builders convert or
  pass admitted forms. The Kside box cases pass `t` as a 0-d array — that is
  an input the compiled body genuinely admits (the wrapper's first bail
  requires scalar cyl≠1 AND scalar azimuth AND scalar t together), not a
  fabricated input. The adversarial asvf field (±0.0, ±200/300 out-of-domain,
  NaN, ±inf) exceeds the production asvf domain but is route-admissible and
  only makes the parity stricter; the crafted vault exercises repeated
  azimuths, signed zeros, a NaN state, and the night/empty solar gate.
- Static parametrization count: 193 (route) + 37 (tables) + 12 (parity) =
  242, consistent with the NOTES' "242 passed".

## 6. NOTES.md honesty — VERIFIED

Timings quoted verbatim including the unfavorable masked-case 0.95x
(485.0→511.2 ms) with rep spreads; explicit statement that these numbers
"do not support a speed claim" and that promotion/decline rests on the
integrator's exclusive-lease protocol at production scale; G06 dedup
saturation on real vaults disclosed (143/145, 151/153, 302/305); serial-only
kernel rationale and the G06 scoping call flagged as deviations; SYNTHETIC
dev-tier labeling throughout; no unmeasured speed promises.

## Notes (non-blocking)

1. The gate is read independently in `_class_coefficients` and again per
   block in `_classes`. A mid-run env flip cannot corrupt results — the
   `prepared` tuple contract is identical across gates and the coefficients
   are bitwise equal either way — but the integration gate should arm the
   env before process start, as the tests already do.
2. `test_gate_off_route_is_inert` sentinel-patches only `_classes_table`
   (the contiguous variant). With active=None that is exactly the path a
   gate leak would take in that test, but a masked-path leak under an
   active-subset input is not sentinel-covered gate-off; the bitwise parity
   suite remains the real backstop there.
3. The new family's wrapper-level parity covers `Kside_veg_v2022a` and
   `Lcyl_v2022a`. `kside_cylinder_anisotropic` returns None unless the
   demand profile is PIPELINE_CYLINDER_ANISOTROPIC, and the cylinder-longwave
   primary drivers are separate entry points; both are covered only via the
   pre-existing cylinder_sw / cylinder_lw families re-run gate-armed
   (181 passed per NOTES). Keep those families in the armed matrix at the
   integration gate.
4. `_classes_table`/`_classes_table_masked` use `cache=True` without
   `bind_cache_identity`, while calling cross-module into
   `_sleef_classifier.atan_fma`: a `_sleef_classifier` source edit would not
   invalidate these kernels' numba disk cache. Dev-only stale-cache hazard;
   same shape as the pre-existing fused-kernel → `_decode_at` pattern.
5. The `_classes_table` docstring says "whole-vault state set"; the actual
   admit set is any 0-based prefix run of active indices (correct there
   too — see §4). Wording only.
6. Compiled-artifact bit-equality of `atan_fma` across the `atan_array` and
   `_classes_table` inlining sites is structurally argued (§1) but is
   ultimately a compilation claim; the deferred parity runs are the proof
   that must be re-executed at the integration gate.

## Deferred to the integration gate

- Execute the patchclasses family (242), the combined run (423), and the
  gate-armed neighbor run (181) — none were run in this review (timing
  lease).
- Exclusive-lease, production-scale timing to decide promotion/decline;
  NOTES explicitly claims no speed result.
- Cold-cache numba compilation cost of the two new kernels on the target
  host; parity re-run after any `_sleef_classifier` change (note 4).

## Verdict

**APPROVE-WITH-NOTES.** No exactness violation found statically: the
coefficient chain is verbatim with original dtypes/order/casts, the G06 key
is exact bit-pattern equality with no float-`==` shortcut, the scatter is
provably pure over the key tuple, the gate is strict-'1'/default-OFF and
covers every classification consumer through the two choke points without
wrapper edits, and the block pass reproduces the retained elementwise
arithmetic with tan32 verbatim and serial typed kernels. Tests bind to the
real ungated routes with bitwise oracles and honest gate-off inertness
checks; NOTES reports verbatim numbers including the masked-case regression
and claims no speed. The notes above are advisory; the deferred items (§
"Deferred") are the operative dynamic proof obligations.
