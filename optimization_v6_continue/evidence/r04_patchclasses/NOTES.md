# R04+G06 implementation notes: exact patch-classification tables (C6-81r item #1)

Date: 2026-09-21. Owner: specialist implementer (v6-r04 worktree, base
ae37d96b, detached). SYNTHETIC dev-tier evidence only; no actual-target or
exclusive-lease claims.

## What landed

Dispatch-gated exact-table route for the patch classification `_classes`
path in `src/solweig_light/radiation/patch_radiation.py`. Gate:
`SOLWEIG_LIGHT_PATCH_CLASS_TABLES == '1'` (strict; every other value,
including empty, keeps the retained route). Default OFF reproduces current
behavior; the wrapper routes (`Kside_veg_v2022a`,
`define_patch_characteristics`, `kside_cylinder_anisotropic`,
`cylinder_longwave`) were NOT edited — all four funnel through
`_class_coefficients` -> `prepared` -> `_classes`, which is where the gate
lives. No call signatures changed.

1. **R04 exact coefficient finite-state tables** (`_class_coefficients`):
   the per-patch scalar chain (`|azimuth - patch_azimuth|` -> `cos` ->
   `2*xi*tan(solar_altitude*deg2rad)` -> `where(yi>0, 0.0, yi)`) was
   extracted verbatim into `_class_coefficient`; both gates evaluate exactly
   that helper. Original intermediate dtypes are preserved by construction
   (identical `_operate`/`_divide` calls, identical operand objects, the
   original per-patch `deg2rad` recomputation, and the original separate
   coefficient cast on store into the float32 table). No additions were
   combined or reordered.
2. **G06 exact source-state classes** (gate-on `_class_coefficients`):
   within one call the solar scalars are fixed, so the coefficient bits are
   a pure function of the patch-azimuth source state. Patches whose full
   source-state tuple is equal (exact float32 bit pattern via a uint32 view;
   signed zeros and NaN payloads stay distinct classes) share one verbatim
   chain evaluation; the stored float32 coefficient is scattered to the
   class members. This is the "U expression evaluations + N scatter" shape
   with no float reassociation: each class runs the original chain once, and
   the scatter copies stored bits (no second rounding).
3. **Single compiled block classification** (gate-on `_classes`): the
   retained `tan32(field)` array pass is kept verbatim (rows elements), then
   one serial numba pass (`_classes_table`, contiguous whole-vault state
   set; `_classes_table_masked`, solar-gate subsets) reproduces the retained
   elementwise sequence per element: float32 add of the tan32 value and the
   per-state coefficient, the SLEEF scalar arctangent (`atan_fma` — the
   exact core `atan_array` loops over, so array-vs-scalar equivalence is
   structural), float32 multiply by the degree factor, and the two strict
   comparisons against the patch altitude. No FMA, no reassociation, no
   tolerance change; only the float32/bool temporaries and per-op NumPy
   dispatch disappear. Column selection: O(1) contiguity check on the
   flatnonzero indices (`indices[0]==0 and indices.size==indices[-1]+1`).

## Dossier deviations / scoping calls

- **G06 "emission material/thermal classes"**: scoped to the classification
  route as the task text directs. The classification coefficient classes are
  what feed the sun/shade emission masks in both longwave and shortwave
  consumers. No wrapper internals (`box_gate`, `directions`, `solar_gate`
  lists, `_model2` band emission) were touched; those belong to the wrapper
  route per the coordination boundary.
- **Serial kernel only.** `_classes` has no `parallel` parameter (unchanged
  signature), so a `prange` variant could not honor the wrapper's
  `parallel=False` requests. Rows are independent (bitwise-identical under
  any thread count), but the route deliberately adds no thread interactions;
  the masked kernel also keeps R04's "poor if lookup dominates" warning
  visible rather than hidden by threads.
- **Measured dev-tier timing does NOT demonstrate the selected warm lever.**
  SYNTHETIC dev-tier, contended shared host, lease-free, one process,
  256x256 field, 153-patch real vault (option 2), 128-row blocks
  (`_classes` route only, best of 3 consecutive pairs shown verbatim):
  - full state set (Kside shape): off=666.5 ms, on=655.5 ms, ratio 1.02x
    (spread across reps 1.01-1.03x)
  - masked 0.7 state set (define shape): off=485.0 ms, on=511.2 ms,
    ratio 0.95x (spread 0.94-0.97x, i.e. a small regression)
  At this scale the SLEEF arctangent evaluations dominate and are identical
  in both routes; the retained NumPy sequence is already well-batched at
  128x153, and the masked kernel pays column indirection that NumPy's
  fused fancy-assignment hides. Promotion/decline should therefore rest on
  the integrator's exclusive-lease protocol at production scale; these
  numbers do not support a speed claim.
- Real production vaults nearly saturate the G06 dedup: measured unique
  azimuths are 143/145 (option 1), 151/153 (option 2), 302/305 (option 3),
  so the U-evaluations saving is ~1-2% of the scalar chain on real tables.
  The dedup is exact and structurally per dossier, but it is not a lever on
  production tables; degenerate/repeated tables benefit more.

## Parity and test results (verbatim)

New family `tests/optimization_v6/patchclasses/` (conftest + 3 test
modules): bitwise (uint32-view, NaN-payload/sign-aware) parity vs the
ungated route on real `create_patches` vaults and a crafted vault with
repeated azimuths, signed-zero and NaN states; route-level, wrapper-level
(`Kside_veg_v2022a` 7 fields box=False/box=True, `Lcyl_v2022a` 6 fields
incl. crafted vault and night empty-state), table construction vs an
external restatement of the retained chain, gate parsing strictness,
gate-off inertness (kernel symbol monkeypatched to raise: never invoked),
TypeError contract, and non-mutation of the boundary bundle.

- `NUMBA_NUM_THREADS=2 PYTHONPATH=src` pytest patchclasses: **242 passed**,
  0 failed.
- Combined with the two closest families + the pre-existing classification
  unit contract: patchclasses + cylinder_sw + cylinder_lw +
  tests/unit/test_patch_classification.py: **423 passed**, 0 failed.
- Neighbor families + unit contract with the gate ARMED
  (SOLWEIG_LIGHT_PATCH_CLASS_TABLES=1): **181 passed**, 0 failed.
- No failures were tuned away; the two test-side corrections during
  development were (a) solar altitude must be tensor-origin per the route
  contract (both gates raise the same TypeError otherwise), and (b) Kside
  box-route bundles need tensor-origin `t` or the wrapper's first admission
  gate routes them to the engine's serial reference, which itself rejects
  scalar box conditions.

## Exactness argument (why bitwise holds)

- Gate-off default: the loop body was moved verbatim into
  `_class_coefficient`; the executed operations, operand objects, and store
  casts are unchanged, and the pre-existing 61-case
  `tests/unit/test_patch_classification.py` matrix passes gate-off.
- Table: equal source state => identical helper execution => identical
  bits; the scatter copies stored float32 values (no re-rounding).
- Block pass: `tan32` output array is the same object bits in both routes;
  the kernel's per-element sequence is the same IEEE f32 add/multiply and
  strict comparisons, and the arctangent is the same scalar core
  `atan_array` loops over. NaN/inf payloads flow identically (comparisons
  False in both routes).

## Lease timing (exclusive-lease production-scale, C6-101r style)

Date: 2026-09-21 (runs 22:09–23:34 local). Tools:
`tools/lease_r04.py` (scheduler; reuses
`campaign_synthetic/tools/campaign_child.py` + `thread_limits.py` verbatim),
raw records `lease_timing.jsonl` + `lease_timing.json`, full child records in
`runs/lease_t1024/records/*.json`. Scene: the campaign's
`scene_t1024` SYNTHETIC build reused verbatim (4 x 1024^2 distinct-tile
batch, 24 records/tile) — no rebuild. T4 shape (workers 1, threads 4;
admission plan_native_threads 4 confirmed per child). WARM state only for
measured slots. Schedule frozen before the first measured run; no retries,
no tuning, no reordering.

Slots (unmeasured priming first):

- slot 0 `priming_cold` gate OFF: wall 903.692 s (walls 5.3056, svf
  391.2948, sim 501.5068) — establishes run dir + geometry cache + JIT.
- slot 1 `priming_jit` gate ON: 2.252 s — compiles `_classes_table` /
  `_classes_table_masked` into the shared NUMBA_CACHE_DIR ("jit-primed
  True").

Measured warm runs (interleaved OFF/ON/OFF/ON/OFF/ON), per-rep verbatim
seconds — `sim` = stage C `simulation_total`, `wall` = child wall for the
three-stage run:

| slot | gate | rep | sim_s | wall_s | total_measured_s |
|---|---|---|---|---|---|
| 2 | OFF | 0 | 494.8503 | 506.025 | 501.7372 |
| 3 | ON | 0 | 489.1692 | 501.137 | 496.0219 |
| 4 | OFF | 1 | 488.0766 | 500.091 | 494.9818 |
| 5 | ON | 1 | 479.5669 | 491.226 | 486.3407 |
| 6 | OFF | 2 | 539.7401 | 552.527 | 546.9777 |
| 7 | ON | 2 | 494.7134 | 507.694 | 501.6084 |

Stage A/B are gate-independent and near-constant (walls 4.82–5.27 s, svf
1.94–2.07 s) across all six runs; store hits 0 (`legacy_cache_policy=
'recompute'`), cache entries 4, native mask 4 every run,
`set_num_threads_error` None.

Bitwise parity at production scale: all six measured runs produced the same
full-output digest `491fdeceaf0ef669` and the same simulation-TIFF digest
`af9c48343a25236b`; per-tile sim digests identical OFF vs ON
(`0_0` b588c9aaaf8f0c56, `0_1` 6920615e3444a432, `1_0` 3bde41a404508003,
`1_1` 8cf33ecc2943a19f). Module origin asserted
`/Users/alansynn/Workspace/solweig-light-v6-r04/src`; math profile
`solweig-portable-sleef-5a1d179d-v1` (fingerprint in the child records).
Known record blemish: the `math_profile_id` field inside
`lease_timing.jsonl` is `null` (extraction read the wrong key); the
authoritative fingerprint lives in `runs/lease_t1024/records/*.json` —
JSONL left append-only, not rewritten.

Host context (recorded, never claimed absent): 10-core Apple M1 Pro,
loadavg snapshots per run in the JSONL (`host_before`/`host_after`,
`exclusive_now` via `heavy_jobs()`). Slots 0–5 show no heavy non-browser
processes. Slot 6 (OFF rep 2) ran into rising host load — after-snapshot
9.54/10.66/8.72 — and slot 7's after-snapshot shows loadavg 13.54 with
`exclusive_now: false`; the one OFF outlier (539.74 s sim, +45 s vs its own
arm's other reps) coincides exactly with that window.

Reading (verdict input only — promotion decision is the integrator's; no
statistical or actual-target claims): medians over the three interleaved
reps — sim stage OFF 494.8503 s vs ON 489.1692 s (ratio 1.0116x ON), full
three-stage total OFF 501.7372 s vs ON 496.0219 s (1.0115x). Paired per-rep
sim deltas (ON − OFF): −5.68 s (−1.15%), −8.51 s (−1.74%), −45.03 s
(−8.34%), the last coinciding with the host-busy window that inflated the
OFF side, so the robust estimate from the clean pairs is ~1–2% end-to-end
at this scene/step count. Direction is consistent (ON never slower within
any pair) but the magnitude is small; at 24 records/tile the simulation
stage is dominated by channels the classification gate does not touch.
