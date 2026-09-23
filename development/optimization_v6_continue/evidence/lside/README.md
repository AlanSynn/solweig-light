# C6-20 evidence: private anisotropic Lside fast path (rule R-A)

Worktree: `/Users/alansynn/Workspace/solweig-light-v6-lside`, detached at
`5e1fab467f7e6038dcf3992cb694008a51ea2c58`. Worker C6-20 (numerical_implementer).
Python: `/Users/alansynn/Workspace/solweig-light/.venv-light/bin/python`
(3.11.16, numpy 2.4.6, numba 0.67.0, arm64 Darwin, NUMBA_NUM_THREADS=2 cap;
full environment in `l1_parity_and_timing.json` -> `environment`).

## Verdict

`ALL_BITWISE_OK`. The private demand-dispatched candidate reproduces the
original four demanded operations bitwise (per timestep, every carried input)
on every admitted case, and falls back to the untouched original
`Lside_veg_v2022a` on every rejected domain with identical results, warnings
and exceptions. Full detail: `l1_parity_and_timing.json` (per-step records,
warning streams, per-field byte hashes).

## Design (dossier 03 rule R-A, dossier 10)

Module: `src/solweig_light/radiation/pipeline_demand.py` (sha256
`db7ad07e4d15989395f33c8d4c0a54d7505b45b5ad84dff353ea9248a856f22e`).

* `RadiationDemand` (private enum): `FULL_DIAGNOSTICS` (default, original
  untouched path) and `PIPELINE_CYLINDER_ANISOTROPIC` (admitted pipeline
  profile). `LSIDE_ANISOTROPIC_DEMAND_PROFILE` records the four demanded
  outputs; every other original intermediate is the `NOT_REQUESTED` sentinel,
  never a zero array.
* Backward slice: under `anisotropic_longwave == 1` each returned direction is
  exactly `_operate(np.multiply, LupD, 0.5)`. `Ldown` is never read by the
  anisotropic branch, so it is not guarded either. The demanded multiplies use
  the original `_operate`/`_operands` helpers, so dtype promotion, signed
  zeros, nonfinite payloads and allocation ownership are identical by
  construction (fresh arrays; never views over Lup).
* Two-tier guard (`_guard_anisotropic`), all comparisons only (the guard
  itself cannot emit a floating point warning):
  - Tier A: all four plain svf in [0,1) elementwise -> return the four
    multiplies directly.
  - Tier B: svf in [0,1] with exact `1.0` pixels (real processed svfE rasters
    contain 615 such pixels in the small fixture) -> re-execute the original
    `subtract(1, svf)` + `log(...)` pair per affected direction so the
    `divide by zero encountered in log` warning keeps its class, message and
    per-call count; then return the four multiplies.
  - Fallback: everything else -> original function call.
* Guard conditions: `np.geterr()` equal to the numpy default
  (`divide/over/invalid=warn, under=ignore`); `altitude` and
  `anisotropic_longwave` 0-d; azimuth/t 0-d in BOTH altitude regimes (the
  prologue azi* sums run unconditionally and can overflow-warn on arrays);
  envelope
  bounds (svf [0,1]; svf*veg/aveg in [0,100]; Ta/Tw/F_sh/CI in [-1e3,1e3];
  SBC/ewall/esky in [-1e2,1e2]; azimuth/t/altitude in [-1e6,1e6]); broadcast
  compatibility of the removed-operation shape groups ({svf family, Ta, SBC,
  ewall} always; + {Tw, F_sh} when `altitude > 0`; {esky, SBC, Ta, CI} for
  Lsky_allsky). Any guard exception (object/string/exotic inputs) -> fallback.

Envelope derivation (float32 worst case, all maxima combined):
`|63.227*(200)^6| = 4.05e15` polynomial, `/4.4897 -> 9e14` vikt;
`power(<=2273.15, 4) = 2.7e13`; Lwallsun/Lwallsh <= `1e4 * 2.7e13 * 9e14 * 2001
* 1 = 4.8e35`; Lsky_allsky <= `2.6e19`.  The wall terms, the largest
intermediate, sit roughly 350-700x below the float32 overflow threshold
(3.4028e38); every other intermediate is orders of magnitude lower still, so
over/invalid cannot fire inside the envelope (verified empirically, probe
B1/B2: envelope extremes produce exactly the one expected svf==1 log warning
and nothing else).

## Warning/error contract

* Probed original warning domains (all reproduced identically by the
  candidate, either by replication or by fallback):
  - svf == 1 -> `RuntimeWarning: divide by zero encountered in log`
    (per direction, engine.py:1370-1373; Tier B replication).
  - svf > 1 -> `invalid value encountered in log` (fallback).
  - svf < 0 -> `invalid value encountered in arcsin` (fallback).
  - svf NaN -> silent (fallback, identical silent result).
  - `np.errstate(under='warn')` + tiny svf -> underflow warnings from the
    removed Lvikt polynomial (engine.py:1707) -> gate forces fallback, so the
    warnings come from the original exactly.
  - `np.seterr` any state != default, or a warning filter promoting to error
    -> fallback; the raised `FloatingPointError`/`RuntimeWarning` is raised
    from the original site with identical class and message.
* Documented delta: under the default regime the Tier B replicated warning
  carries the candidate's file:line in Python's warning dedup key
  (`pipeline_demand.py:303` instead of `engine.py:1370`). Category, message
  text and per-call count match exactly (asserted per direction). A pipeline
  run takes the fast path from timestep 1, so one warning is observed either
  way; a process that first runs the original and later the fast path could
  see the warning registered at both locations once each. This follows
  dossier 10 "pragmatic completion": failure class/condition identity is
  preserved; exact emission-site identity is impossible without paying the
  full original path for every real scene.

## L1 results (`l1_parity_and_timing.json`)

* 128x128 clean svf, 24 adversarial steps: all OK, fast path every step.
* 128x128 svfE == 1.0 (real-data-like), 24 steps: all OK, Tier B every step,
  warning stream matches per step.
* 128x128 svfE == 1.5 (fallback domain), 4 steps: all OK via original.
* Real processed SVF fixture (32x35, `svfs_0_0.zip`): all 24 steps OK on the
  fast path; fixture `svfE` has min 0.184, max 1.0, 615 exact-1.0 pixels
  (`fixture_svf_stats` in the JSON).

Timing (contended development host, 8 sibling workers; recorded, no claims;
128x128 x24 steps, min of 3 alternating pairs; the JSON is regenerated on
every harness run, latest run authoritative):
original 0.242-0.273 s; dispatch Tier A 0.024 s; Tier B 0.022-0.023 s;
FULL_DIAGNOSTICS 0.239-0.249 s; single fallback call 0.0097 s.

## Commands (all exit codes recorded in `commands.txt`)

```
.venv-light/bin/python -m pytest tests/optimization_v6/lside -q     # 65 passed, exit 0
.venv-light/bin/python tests/optimization_v6/lside/run_l1_evidence.py  # ALL_BITWISE_OK, exit 0
```

## Integration

`integration_patch_recipe.diff` (sha256
`96a9196120ef13a31aa562e22f1fc89a04a729fb9a762a3c1f573c4a33537ef7`): proposal
for the integrator-owned `engine.py` call site (one import + one call-site
replacement + driver-side `radiation_demand(...)` wrapper). Cycle-freedom of
the module-level import was simulated at head 5e1fab46. engine.py and
pipeline.py were NOT edited by C6-20.

## Unresolved items

* None blocking C6-20. Notes for the reviewer/integrator: (1) the warning
  location delta above; (2) the guard admits int/bool/longdouble svf dtypes
  via the numpy min/max path (numba kernel is float32/float64 specialized);
  empty arrays fall back conservatively; (3) numba `njit(cache=True,
  nogil=True, fastmath=False)` is used for the fused min/max guard kernel
  only - the demanded arithmetic stays on the original numpy `_operate`
  helpers to make bitwise identity structural rather than proven.
