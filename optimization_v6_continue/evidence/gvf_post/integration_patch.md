# C6-31 integration patch recipe (INTEGRATOR applies; I do not edit ground_view.py/engine.py)

Single call-site change in `src/solweig_light/radiation/ground_view.py`,
function `_gvf_fused`, at the block loop (verbatim from base 5e1fab46,
lines 652-659 shown below). No engine.py change is needed: `gvf_2018a`
already passes `first_steps` / `second_steps` into `_gvf_fused`, and the
wrapper takes the same arguments in the same order plus `parallel=`.

## Step 1 — import (top of ground_view.py, module imports)

```python
from .gvf_postprocess import gvf_postprocess_block
```

## Step 2 — replace the call in `_gvf_fused`

Current code, verbatim from base 5e1fab46 (ground_view.py lines 652-659;
verified against the working tree after the C6-60 F2 finding):

```python
        for row0 in range(0, buildings.shape[0], block_rows):
            row1 = min(row0 + block_rows, buildings.shape[0])
            block = np.empty((16, row1 - row0, buildings.shape[1]), dtype=np.float32)
            gather(row0, row1, buildings, shadow, sunwall, lup_snap, albshadow_snap, alb, lwall_snap, np.float32(albedo_b), bounds, kernel_first, block)
            gvf_b, gvfLup_b, gvfalb_b, gvfalbnosh_b, gvf2_b = _postprocess_block(
                tuple(block[index] for index in range(16)), buildings[row0:row1],
                facesh[row0:row1], lup_term[row0:row1], alb_term[row0:row1],
                nosh_term[row0:row1], first_steps, second_steps)
```

Replacement (only the call changes; the five-name unpack and every
downstream `+=` accumulate stay byte-identical):

```python
            gvf_b, gvfLup_b, gvfalb_b, gvfalbnosh_b, gvf2_b = gvf_postprocess_block(
                block, buildings[row0:row1],
                facesh[row0:row1], lup_term[row0:row1], alb_term[row0:row1],
                nosh_term[row0:row1], first_steps, second_steps, parallel=True)
```

Notes on the argument/return deltas (the ONLY ones):

- First argument: `block` (the `(16, block_rows, cols)` float32 gather
  buffer) is passed directly; the `tuple(block[index] for index in range(16))`
  view-tuple expression is deleted. The wrapper slices its own views and, on
  the flagged fallback, restores planes 1/3/5 to exact incoming bits before
  re-running the original on equivalent views.
- Return signature: the wrapper returns exactly what `_postprocess_block`
  returns — the five fields `(gvf, gvfLup, gvfalb, gvfalbnosh, gvf2)` unpacked
  above. The in-place receiver-plane mutations (planes 1/3/5:
  weightsumwall/weightsumLwall/weightsumalbwall) happen on the caller's
  `block` array in both implementations, so no extra return values exist or
  are needed. (The earlier revision of this recipe showed an 8-name unpack —
  that was wrong and would raise ValueError; this section is the corrected
  form, matching the C6-60 review.)
- `parallel=True` is deliberate: the prange variant is bitwise-proven on the
  full adversarial L1 suite (parity_table.md "Parallel" section) and is the
  only compiled variant faster than the NumPy original (serial is 2.0-2.7x
  slower; parallel 0.63-0.68x/0.46x/0.26-0.28x of original at cols
  128/256/1024 across two runs — contended dev tier, raw medians in
  timing_raw.txt). Drop the kwarg to get the gate-default serial kernel with
  the same bitwise contract.
- `first_steps`/`second_steps` may be f64 0-d arrays or Python ints from the
  engine; the wrapper's `_step_scalar` admits exactly the production domain
  (finite integer >= 1, < 2**24) and routes anything else to the untouched
  `_postprocess_block` (bitwise + warning identical).
- Boundary dtype contract (C6-60 F4): the wrapper raises TypeError unless
  `block` is a `(16, rows, cols)` float32 array. The in-tree buffer at line
  654 is exactly that; nothing to change.

## Do NOT change

- `_postprocess_block` stays byte-for-byte: it is the fallback reference the
  wrapper re-executes on any flagged case (it reproduces the original's
  warnings and its FloatingPointError behavior for overflow/invalid/divide
  exactly; the documented underflow carve-out lives in the module docstring
  of gvf_postprocess.py and is unobservable under NumPy's default regime).
- `engine.py` dispatch (`gvf_2018a`): untouched; `parallel=True` inside
  `_gvf_fused` remains valid since the G03 path already runs only when
  `threads_per_worker > 1`.
- No cache files should be committed: numba `cache=True` writes
  `__pycache__/*.nbi/*.nbc` next to the module at first import.

## Rollback

Revert the two hunks; `_postprocess_block` and `_gvf_fused` semantics are
otherwise untouched.
