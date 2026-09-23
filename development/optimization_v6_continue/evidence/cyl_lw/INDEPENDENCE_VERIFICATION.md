# R-B independence verification at worktree HEAD 5e1fab46

Worker C6-21 re-derived the reduction rule from source before relying on it.
Verdict: **the claim holds for the compiled `_longwave` kernel family**; the
reduction is confined to that family and to the compiled wrapper's primary
outputs. No counterexample was found. The serial reference path is never
reduced.

## 1. Kernel family (src/solweig_light/radiation/patch_radiation.py)

Four variants were read line by line: `_longwave` (:587, parallel),
`_longwave_serial` (:651), `_longwave_fused` (:716, parallel),
`_longwave_fused_serial` (:789). In all four:

- Accumulators `accum[10..13]` are **write-only sinks**: every occurrence is
  `accum[10+direction] = np.float32(accum[10+direction] + term)`. There is no
  read of `accum[10+i]` anywhere in any variant.
- Output columns 0..6 are computed exclusively from `accum[0..9]`:
  `output[..,0]=a0+a1+a2+a3+a4`, `output[..,1]=a5+..+a9`,
  `output[..,2:7]=accum[5:10]`. Columns 7..10 are exactly `accum[10],accum[12],
  accum[13],accum[11]`.
- The reflected sweep (`reflected = f(accum[0]+lup, reflection_factor)`) reads
  only `accum[0]`. It never reads a cardinal accumulator.
- All cardinal update sites (sky sweep, solar_gate branch, else branch,
  reflected sweep) read only `gate[patch,direction]`, `directions[patch,d]`,
  `sky*sky_side[patch]` and local temporaries (`vegetation_side`, `sun_side`,
  `shade_side`). They write no primary accumulator and guard no primary
  operation, so deleting them cannot change control flow or values of
  `accum[0..9]`.
- `njit(cache=True, fastmath=False)` is preserved; no new reassociation is
  possible because no floating expression was regrouped — only whole
  statements whose results feed `accum[10..13]` were deleted, and the output
  block was narrowed from 11 to 7 columns.
- Warning/np.seterr scope: the cardinal arithmetic lives inside njit kernels,
  where numpy's error machinery does not apply (no warnings can be emitted
  from it). All wrapper-level numpy arithmetic (band flux loop, `_classes`,
  model2, surfaces) is retained verbatim, so wrapper-level warning/seterr
  behavior is unchanged. Gate/direction arrays are produced internally by
  `patch_geometry`, not caller inputs, so no reachable failure domain (raised
  exception) is removed.

## 2. Wrapper and consumers

- `patch_radiation.Lcyl_v2022a` (:903) returns
  `tuple(result[index] for index in (0,1,7,8,9,10))` — Ldown, Lside and the
  four cardinal fields. Guard order: ndarray scalar-altitude check, ndim/dtype
  `_supported` check, patch-count `0 < n <= 609`, each falling back to
  `_reference('Lcyl_v2022a')` (the untouched engine serial function).
- `engine.Solweig_2022a_calc` (:1650) consumes `Ldown` (returned/written as
  the public Ldown TIFF by pipeline.py:270) and, under `cyl==1 and
  anisotropic_sky==1` (:1666-1667), `Lside` in `Sstr` (`Lside*Fcyl`) feeding
  Tmrt. Tmrt uses **no** Lcyl cardinal field: the `Least += Least_` additions
  happen **after** Tmrt (:1671-1675) and only mutate the publicly returned
  `Least/Lsouth/Lwest/Lnorth`.
- The private pipeline driver (src/solweig_light/pipeline.py) reads only
  `Tmrt, Kup, Kdown, Lup, Ldown, shadow` from the returned fields (:267-277)
  and carries state via `SimulationState.accept`
  (src/solweig_light/models.py:90; `STATE_NAMES` = CI, firstdaytime,
  timestepdec, timeadd, Tgmap1*, TgOut1 — no cardinal or Lside field). The
  returned cardinal sums and `Lside` are discarded with `del result, fields`.
- Therefore, under the private pipeline cylinder-anisotropic demand the
  demanded cylinder-longwave outputs are exactly output columns 0 and 1
  (derivable only from accumulators 0..9); the cardinal channels 10..13 are
  outside the backward slice of every observable.

## 3. Scope boundaries

- The engine **serial** `Lcyl_v2022a`/`define_patch_characteristics`
  (engine.py:1258/:1134) consumes all 11 output fields, but it is the
  fallback for unsupported profiles and is not reduced; wrapper guard
  failures return its full six-field result unchanged (tested).
- The compiled fast path is **not** bitwise-equal to the serial reference
  (pre-existing v5 property, outside this task); all parity in this task is
  reduced-vs-full **within the compiled path**.
- `_longwave_fused_block` (:214) is gated by `SOLWEIG_LIGHT_FUSED_RAD=1`
  (default OFF); the reduced fused block mirrors the same gate, descriptor
  preflight order and `masks` capture. The `masks` array is retained because
  the reflected sweep (primary) consumes it.
