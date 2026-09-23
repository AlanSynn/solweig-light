# C6-50 integration recipe: prepared multi-channel visibility decoder

Module: `src/solweig_light/geometry/visibility_prepared.py` (NEW, private).
Everything else in `src/solweig_light/` is INTEGRATOR-OWNED; this document is
the complete patch. The module imports only existing symbols from
`visibility`, `visibility_compiled` (`_descriptor`) and `visibility_native`.

## 1. Shortwave — `patch_radiation._shortwave_visibility_blocks`

Prepend one prepared attempt; the original body follows unchanged (the
fallback IS the original code):

```python
def _shortwave_visibility_blocks(shadow,vegetation,vegetation_building,diffuse,start,stop,patches):
    """Read shortwave visibility in the original observable order."""
    from ..geometry.visibility_prepared import decode_shortwave_block
    prepared=decode_shortwave_block(shadow,vegetation,vegetation_building,diffuse,start,stop,patches)
    if prepared is not None:
        return prepared
    sh=_block(shadow,start,stop,patches)
    vs=_block(vegetation,start,stop,patches)
    vb=_block(vegetation_building,start,stop,patches)
    from ..geometry.visibility_compiled import diff_from_shared_decoded
    diff=diff_from_shared_decoded(shadow,vegetation,diffuse,sh,vs,start,stop,patches)
    if diff is None:
        diff=_block(diffuse,start,stop,patches)
    return sh,vs,vb,diff
```

Optional caller buffers (skip one allocation per channel): build a list of
four C-contiguous writeable float32 `(stop-start, patches)` arrays and call
`prepare_channels(...).decode(start, stop, patches, buffers)` instead of the
drop-in wrapper. Buffer-contract violations raise the new API's ValueError
before any lock is taken; they have no original counterpart, so only pass
buffers the consumer owns.

## 2. Longwave — `define_patch_characteristics` compiled branch

Replace the `_block` triple (the `if reduced is None:` arm) with a prepared
attempt plus the unchanged original arm:

```python
        if reduced is None:
            from ..geometry.visibility_prepared import decode_longwave_block
            decoded=decode_longwave_block(values['shmat'],values['vegshmat'],
                                          values['vbshvegshmat'],start,stop,count)
            if decoded is None:
                sh,vs,vb=(_block(values[name],start,stop,count)
                          for name in ('shmat','vegshmat','vbshvegshmat'))
            else:
                sh,vs,vb=decoded
            reduced=kernel(sh,vs,vb,sun,shade,values['steradian'],geometry.sine,geometry.cosine,directions,gate,solar_gate,values['Lsky_down'][:,2],values['Lsky_side'][:,2],sun_surface,shade_surface,values['Lup'].reshape(-1)[start:stop],factor)
```

`decode_longwave_block` may be prepared once per demand and reused per block:
`prepare_channels(shmat, vegshmat, vbshvegshmat)` returns a reusable handle
(prepare cost is ~5 microseconds, recorded in `timing_probe.json`); the
drop-in wrapper re-prepares per call, which is also correct.

## 3. Semantics the integrator inherits

- `None` from prepare/decode drop-ins means "not admitted": run the original
  path in full. Admission covers exactly: base channels direct
  `PackedVisibility` (or `MappedVisibility`), diffuse = shared
  `LazyDiffVisibility` under `diff_from_shared_decoded`'s identity rule
  (reuse), independent lazy pair over packed leaves, or direct packed.
- Exactness: error precedence (open checks -> range checks -> reserved-code
  scan, per channel in demand order), decoded bytes, error type/message and
  close semantics are asserted identical to the original path in
  `tests/optimization_v6/decoder/` (95 tests).
- Closed mapped owners are declined at prepare time by protocol
  (`MappedVisibility.close()` nulls `_block_descriptor`); the fallback then
  reports them at the original open checkpoint. No stale borrow exists.
- The module holds no global state and touches no public codec entry; the
  fused route (`SOLWEIG_LIGHT_FUSED_RAD`) is unaffected.
- Known tradeoff (recorded, no claims): the prepared kernel scans each stream
  in `_preflight` before the verbatim decode loop, so on the contended dev
  tier the full-frame 128x128/153-patch sequence measured slower than the
  original four-entry path (71.6 ms vs 58.1 ms best-of-30). See
  `timing_probe.json`. Precedence exactness requires the pre-pass; removing it
  would break cross-channel reserved-vs-open/range ordering.
