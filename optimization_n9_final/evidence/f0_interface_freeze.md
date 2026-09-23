# N9 interface freeze (F0) — the small agreed input/ownership table

Freezes the ONLY interfaces F1 workers may build against. Signatures are
binding; internal implementations change. All existing aliases, errors,
f32/f64 nodes and source identities stay binding.

## Producer surface (owner: producer_owner, F1D/F1M)

```
produce_blocks_aosoa(shadow, vegetation, vegetation_building, start, stop,
                     patches, *, width=8, order='patchmajor', out=None)
    -> (uint32[G,P,W] x3) | None          # signature: out= is the ONLY
                                          # allowed addition (keyword,
                                          # default None; None = allocate)
classify_block_aosoa(altitude, azimuth, geometry, asvf, start, stop,
                     active=None, prepared=None, *, width=8,
                     sun_out=None, shade_out=None)
    -> (bool[G,P,W], bool[G,P,W]) | None  # signature UNCHANGED
```

New binding contract for `classify_block_aosoa` with supplied `sun_out`/
`shade_out`: EVERY valid lane (row < rows within its gang) of both masks is
fully written — inactive valid columns/lanes CLEARED to False before or by
the kernel write. Padding lanes stay untouched. `shade != not sun` at
equality/NaN preserved. A caller reusing scratch must size the buffers for
the same (start, stop, patches, width) it passes.

Mode specialization (F1D) is INTERNAL to the producer kernels: branch once
per patch on mode, then literal shifts/masks (binary `(data[p>>3]>>(p&7))&1`,
ternary `(data[p>>2]>>((p&3)<<1))&3`); raw keeps its original byte-assembly
loop. Patch-major order, tails, padding-lane non-writes, reserved-code-3
first-failure position: all unchanged. The same constant-mode transformation
is applied to the strongest Numba controls (lw_b_control consumer decode;
A-plus comparator where practical) — native must not win by withholding
shared improvements from Numba.

## Stream surface (owner: stream_owner, F1S)

- `_lw_dispatch._execute_row` is REPLACED by a bounded stream: per-region
  produce/classify inside the region consumer's `produce(ctx)` using
  `BlockSlot` buffers (~14*B*P bytes payload per slot), never `0,total`
  whole-scene materialization. Slicing a full tensor is not bounded
  production.
- New PRIVATE records `InvocationPlan` / `BorrowedVisibility` / `BlockSlot`
  live under `solweig_light._native_dispatch` (private module), are never
  returned through public API, and are forgeable by no public call.
  Invocation-lifetime immutable validation; cheap per-block extent/ownership
  checks retained. Public defensive adapters unchanged for unknown callers.
- Ordering preserved: classification BEFORE decode per block; sh, vs, vb
  decode in original observable order; the consumer's two ordered sweeps
  (sky then reflection) unchanged; canonical first-error order preserved
  (lowest block index, produce-before-consume). No double full-stream
  preflight.
- Region owner unchanged (`region_plan.plan_regions` / `region_pool.
  execute_regions`): BLOCK_FANOUT for C (single-thread leaf per call),
  SELF_PARALLEL for B (granted budget). No new pool, no nested parallelism,
  no RLock held while workers re-enter the public leasing function.

## Native leaf (unchanged)

`lw_native_aosoa.primary_aosoa` — 17-arg frozen order + rows + out. The
N8-04 contract binds. The ISPC kernel and installed artifact loader are
NOT modified by F1; the artifact/ABI identity enters the InvocationPlan.

## File ownership during F1 (writable scopes)

- producer_owner: `src/solweig_light/_native_dispatch/direct_aosoa.py`,
  `src/solweig_light/_native_dispatch/lw_b_control.py`, plus their own new
  test files. Detached worktree at 7abe526a.
- stream_owner: `src/solweig_light/radiation/_lw_dispatch.py`,
  `src/solweig_light/_native_dispatch/region/consumers.py`, one new private
  stream module, plus their own new test files. Detached worktree at
  7abe526a.
- integrator (only committer of the shared branch): `cylinder_longwave.py`
  seam, packaging, everything else. Workers never commit the shared branch.

Any interface change beyond this table requires integrator sign-off and a
freeze amendment recorded BEFORE the affected result exists.
