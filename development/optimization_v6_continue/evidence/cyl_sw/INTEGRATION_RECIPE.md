# C6-22 integration recipe: cylinder shortwave narrow scratch

Integrator-owned files: `src/solweig_light/radiation/patch_radiation.py` (dispatch hook),
`src/solweig_light/pipeline.py` (demand-profile wiring). This module ships the private
kernel/entry and tests only; nothing outside the owned paths was modified.

## Private interface

```python
from solweig_light.radiation import cylinder_shortwave

cylinder_shortwave.PIPELINE_CYLINDER_ANISOTROPIC   # admitted pipeline demand
cylinder_shortwave.FULL_DIAGNOSTICS                # default; public full path
cylinder_shortwave.set_demand_profile(profile)     # raises ValueError on unknown
cylinder_shortwave.demand_profile()                # current profile

cylinder_shortwave.kside_cylinder_anisotropic(values, block_pixels=128, parallel=True)
# values: the wrapper's bound-argument mapping (inspect.signature(...).bind(...).arguments)
# returns the seven public fields (KupE/2..KupN/2, KsideI, KsideD, Kside) bitwise-equal
# to the retained wrapper route, or None => caller must fall back to the generic route.
# Omitted diagnostics are NOT REQUESTED under the private profile; never zeros.
```

## Patch 1 of 2 — `patch_radiation.py`, function `Kside_veg_v2022a`

All guard/fallback early-returns of the wrapper run BEFORE this point, so the original
failure order for public/invalid calls is untouched. The entry re-verifies admission
(cyl==1 scalar, anisotropic_diffuse==1, dtype profile, lv bound 1..609, finite solar
scalars and finite patch azimuths) and returns None otherwise.

```diff
@@ def Kside_veg_v2022a(*args,block_pixels=128,parallel=True,**kwargs):
     azimuth=values['azimuth']
     t=values['t']
     box=values['cyl']!=1
+    if not box:
+        from .cylinder_shortwave import kside_cylinder_anisotropic as _narrow
+        narrowed=_narrow(values,block_pixels=block_pixels,parallel=parallel)
+        if narrowed is not None:
+            return narrowed
     total=np.zeros(1,dtype=np.float32)
```

Notes:
- Function-local import keeps the module import graph exactly as today (the private
  module imports numpy/numba at top level and `patch_radiation` lazily inside its entry).
- The hook sits before the generic `directions`/`box_gate` construction, so under the
  admitted profile that box-only setup is never evaluated (the removed-work audit lives
  inside the entry: any nonfinite `t`, solar azimuth or patch azimuth declines the
  narrow route and the generic path keeps its exact warning/exception behaviour).
- The dormant fused decode route is NOT activated: the narrow entry always uses the
  retained ordered decode (`_shortwave_visibility_blocks`) and its own 4-column kernel.
- When `narrowed is None` the wrapper continues exactly as at base; no wrapper line is
  deleted or reordered.

## Patch 2 of 2 — `pipeline.py`, run setup (integrator chooses exact site)

Set the demand profile once per pipeline run that executes the standard own-met
cylinder-anisotropic workflow (the wrapper guards still require cyl==1 and
anisotropic_diffuse==1 per call), and restore it after:

```python
from solweig_light.radiation import cylinder_shortwave as _cyl_sw

_cyl_sw.set_demand_profile(_cyl_sw.PIPELINE_CYLINDER_ANISOTROPIC)
try:
    ...  # existing run body unchanged
finally:
    _cyl_sw.set_demand_profile(_cyl_sw.FULL_DIAGNOSTICS)
```

Contract: the private profile never alters `RuntimeOptions.as_dict`, public signatures,
or the seven public workflows. Public/diagnostic calls outside the pipeline window keep
`FULL_DIAGNOSTICS` and the untouched generic path.

## Post-integration checks (family/integration owner)

1. `tests/optimization_v6/cylinder_sw/` full suite green (86 tests at C6-22 hand-off).
2. `tests/differential/test_patch_radiation.py` unchanged behaviour — at base with this
   module present: 634 passed / 1 pre-existing order-dependent failure
   (`test_compiled_patch_parallel_diagnostics`, identical without the module).
3. L2 small real TIFF chronology: per-timestep comparison of the seven Kside fields and
   all carried state between the patched tree and base (numerical reviewer scope).
