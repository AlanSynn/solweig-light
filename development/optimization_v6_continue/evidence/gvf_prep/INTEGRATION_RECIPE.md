# C6-30 integration recipe: prepared GVF step dispatch

Integrator-only change. `src/solweig_light/radiation/engine.py` is
integrator-owned; this recipe is the exact patch. Base: 5e1fab46.

## 1. Dispatch patch (engine.py, `gvf_2018a`, threads>1 branch)

Current code (engine.py:1735-1745 region):

```python
def gvf_2018a(wallsun, walls, buildings, scale, shadow, first, second, dirwalls, Tg, Tgwall, Ta, emis_grid, ewall, alb_grid, SBC, albedo_b, rows, cols, Twater, lc_grid, landcover):
    """Dispatch the identical ordered gather within the admitted CPU budget."""
    from .ground_view import _gvf_fused, gvf_2018a as serial, gvf_2018a_parallel as parallel
    from ..runtime import get_runtime_options
    threads = get_runtime_options().threads_per_worker
    if threads > 1:
        return _gvf_fused(wallsun, walls, buildings, scale, shadow, first, second, dirwalls, Tg, Tgwall, Ta, emis_grid, ewall, alb_grid, SBC, albedo_b, rows, cols, Twater, lc_grid, landcover, parallel=True, block_rows=32)
    return serial(...)
```

Patch: replace the `_gvf_fused(...)` call with `prepared_gvf_step(...)` and
extend the import. The argument list is identical plus `parallel` /
`block_rows`; the fallback inside `prepared_gvf_step` delegates to
`_gvf_fused` itself, so the serial branch and every unsupported input keep
the exact current behavior.

```python
    from .ground_view import gvf_2018a as serial, gvf_2018a_parallel as parallel
    from .gvf_prepared import prepared_gvf_step
    from ..runtime import get_runtime_options
    threads = get_runtime_options().threads_per_worker
    if threads > 1:
        return prepared_gvf_step(wallsun, walls, buildings, scale, shadow, first, second, dirwalls, Tg, Tgwall, Ta, emis_grid, ewall, alb_grid, SBC, albedo_b, rows, cols, Twater, lc_grid, landcover, parallel=True, block_rows=32)
    return serial(wallsun, walls, buildings, scale, shadow, first, second, dirwalls, Tg, Tgwall, Ta, emis_grid, ewall, alb_grid, SBC, albedo_b, rows, cols, Twater, lc_grid, landcover)
```

Notes:
- `_gvf_fused` can stay in the import line if other code still references
  it; the prepared entry imports its own default delegate lazily.
- No other engine.py change is required. `gvf_2018a_numpy = gvf_2018a`
  (engine.py:1731) keeps pointing at the dispatched symbol, so the retained
  original body remains reachable for the differentials.

## 2. Kill switch

`SOLWEIG_LIGHT_GVF_PREPARE=0` (read per call via `os.environ.get`) routes
every `prepared_gvf_step` call to `_gvf_fused` unchanged — bitwise base
path, no preparation work. Default (unset or any value except
`0`/`false`/`False`) is ON.

## 3. Behavior envelope

- Admitted domain: exactly the `_gvf_fused` guard union PLUS three stronger
  alias exclusions required by the once-per-call snapshots — `lc_grid`,
  `dirwalls`, `Twater` may not share memory with `Tg` (they are re-read per
  direction by the baseline). Violators delegate to `_gvf_fused` before any
  caller-visible memory is touched.
- Proven-exact without delegation: aliases through `Tgwall`, `emis_grid`,
  `first`, `second` (both routes read them at the same pre/post-mutation
  points; tested).
- Step context: one `PreparedGVFStep` per call, never registered, never
  keyed by array identity, dead at return. No cross-step/tile reuse.
- Warning contract: hoisted expressions warn once per call at preparation
  under the ambient errstate; `np.seterr(raise)` aborts both routes on the
  same first evaluation with Tg untouched. The engine.py:1370
  divide-by-zero-in-log warning (Lside_veg_v2022a svfalfaE) is outside the
  closure and unchanged.

## 4. Verification commands (recorded in SUMMARY.md)

```
cd /Users/alansynn/Workspace/solweig-light-v6-gvfprep
PYTHONPATH=src NUMBA_NUM_THREADS=2 \
  /Users/alansynn/Workspace/solweig-light/.venv-light/bin/python \
  -m pytest tests/optimization_v6/gvf_prepare/ -q
PYTHONPATH=src NUMBA_NUM_THREADS=2 \
  /Users/alansynn/Workspace/solweig-light/.venv-light/bin/python \
  -m pytest tests/optimization_v5/gvf/ -q
```

Exit codes at recording time: 0 / 0 (78 passed, 82 passed).
