# C6-31 typed node inventory of `ground_view._postprocess_block` (base 5e1fab46)

Source of truth: `src/solweig_light/radiation/ground_view.py` lines 501-541 at
commit 5e1fab467f7e6038dcf3992cb694008a51ea2c58. The function is a 1:1 copy of
`_sun`'s post-gather lines (ground_view.py lines 343-378) applied to one row
block; every node below is elementwise over the 16 receiver planes and the
sliced rasters.

## Count reconciliation with the task text

The task gate says "all 16 intermediate + 5 return-path comparisons". The
actual source at this base contains:

- **10 comparison expressions** (listed C1-C10 below),
- **5 in-place mask/zeroing assignments** (Z1-Z5) -- these match the task's
  "5 return-path" items in count but are zeroing steps, not comparisons,
- **5 returned fields** (`gvf, gvfLup, gvfalb, gvfalbnosh, gvf2`).

The gate is satisfied over the complete inventory (a superset of any
reasonable reading of "16"): every comparison, every cast and every zeroing
is proven bitwise-equal in original order, per node and end-to-end.

## Comparisons (original order)

| # | source line | expression | dtype/semantics |
|---|---|---|---|
| C1 | 516 | `weightsumwall_first > 0` | f32 vs python int 0 -> f32 compare; NaN>0 False; -0.0>0 False |
| C2 | 517 | `weightsumalbwallnosh_first > 0` | as C1 |
| C3 | 518 | `weightsumwall > 0` | as C1; **evaluated before Z2 zeroing** |
| C4 | 519 | `weightsumalbwallnosh > 0` | as C1 |
| C5 | 520 | `weightsumwall == second` | f32 array vs 0-d f64 -> f64 promote; **before Z2** |
| C6 | 521 | `keep == -1` | f32 vs python int -1 -> f32 compare |
| C7 | 523 | `keep == 1` | f32 vs python int 1 -> f32 compare (zeroing mask for plane 1) |
| C8 | 525 | `gvf2 > 1.0` | f32 vs python float -> f32 compare (clamp mask) |
| C9 | 527 | `keep == 1` | same mask object semantics, re-evaluated (plane 3) |
| C10 | 530 | `keep == 1` | re-evaluated (plane 5) |

Note: C6 (`keep == -1` zeroing) is behaviorally inert for outputs and plane
state -- `keep` is only ever compared against 1 afterwards, and -1 != 1
either way -- but the kernel reproduces it anyway (identical order).

## Casts (original order / cast points)

| # | source line | cast | bits |
|---|---|---|---|
| K1 | 520 | `(weightsumwall == second).astype(np.float32)` | bool -> +0.0 / 1.0 |
| K2-K9 | 522,524,526,528,529,531,532,533 | `_operate(np.multiply, f32plane, bool influence)` / `... (int64 mask)` | engine `_operands` casts bool/int operand to f32: 0.0 / 1.0 (the int64 path is `bool*-1+1` -> {0,-1}+1 = {1,0} int64 -> f32 +1.0/+0.0) |
| K10-K17 | 522,524,526,528,529,531,532,533 | denominator casts in `_divide`: `np.asarray(first+1, f32)`, `np.asarray(first, f32)`, `np.asarray(second+1, f32)`, `np.asarray(second, f32)` | f64 -> f32 RN; `first`/`second` are `np.round` outputs (integers >= 1 after the `first < 1` clamp) so exact |
| K18-K26 | 534,535,537,539 | scalar literals `0.5`, `0.4`, `0.9` via `_operands` | python float -> f32 RN (f32(0.4), f32(0.9) are inexact roundings, reproduced identically) |

## Zeroing / in-place assignments (original order)

| # | source line | statement | observable effect |
|---|---|---|---|
| Z1 | 521 | `keep[keep == -1] = 0` | inert (C6 note) |
| Z2 | 523 | `weightsumwall[keep == 1] = 0` | mutates plane 1 **before gvf2 reads it**; writes +0.0 |
| Z3 | 525 | `gvf2[gvf2 > 1.0] = 1.0` | mutates the returned gvf2; writes +1.0; **the only op that can hide a nonfinite value from the outputs** |
| Z4 | 527 | `weightsumLwall[keep == 1] = 0` | mutates plane 3 before gvfLup2 |
| Z5 | 531 | `weightsumalbwall[keep == 1] = 0` | mutates plane 5 before gvfalb2 |

## Return-path arithmetic (original order)

R1 `gvf  = ((gvf1*f32(0.5)  + gvf2*f32(0.4))  / f32(0.9))` (gvf2 = post-Z3)
R2 `gvfLup = ((gvfLup1*0.5 + gvfLup2*0.4)/0.9) + lup_term_b`
R3 `gvfalb = ((gvfalb1*0.5 + gvfalb2*0.4)/0.9) + alb_term_b`
R4 `gvfalbnosh = ((gvfalbnosh1*0.5 + gvfalbnosh2*0.4)/0.9 * buildings_b) + nosh_term_b`
R5 `gvf2` (post-clamp) returned as the fifth field.

Denominator note: the `gvfalbnosh2` branch divides by `second` **without**
the `+1` (line 533); every other second-block branch uses `second + 1`.
This asymmetry is preserved in the kernel (`f_second` vs `d_second`).

## Warning/error contract of the compiled boundary

Default `np.seterr` regime (warn): a RuntimeWarning can originate only in an
add/sub/multiply/divide of the arithmetic DAG (comparisons never warn;
`keep = eq - facesh` cannot overflow since eq in {0,1} and the exact sum
`1 + FLT_MAX` rounds back to FLT_MAX). Every such event produces a nonfinite
value that necessarily reaches either the **raw pre-clamp gvf2** or one of
the four unclamped returned fields: the DAG's only non-returning consumers
are comparisons (no warn), `keep` arithmetic (cannot warn, see above), and
Z2/Z4/Z5 which write the constant +0.0. Nonfinite values propagate through
every remaining node (Inf stays Inf, Inf*mask0 becomes NaN, NaN stays NaN;
denominators are finite >= 1 in the admitted step domain). Therefore:

- kernel flag clean  =>  the original could not have warned  =>  fast-path
  return is bitwise-equal AND observably identical (silent);
- kernel flag set  =>  the wrapper restores planes 1/3/5 to their exact
  incoming bits and re-runs the untouched `_postprocess_block`, which fires
  the identical warnings at the identical source location (or raises the
  identical `FloatingPointError` under `np.errstate(all='raise')`, with the
  caller's block left in the identical state, since the reference re-executes
  its own mutations in the original order from the original values).

Scoped carve-out (review C6-60 F1): the kernel inspects result values, not
the floating-point underflow flag. NumPy's default regime ignores underflow,
so this is unobservable in production, but under a non-default
`np.errstate(under='raise')` the original raises `FloatingPointError`
("underflow encountered in divide") when a division result is subnormal
(e.g. a subnormal plane sum divided by a large admitted step) where the
wrapper returns silently with bitwise-identical outputs.
`tests/optimization_v6/gvf_postprocess/test_gvf_postprocess_parity.py::
test_underflow_regime_contract` pins both regimes; raise parity for
overflow/invalid/divide-by-zero is unaffected.

`divide` events cannot occur in the admitted step domain
(`1 <= first, second < 2**24`, finite integers -- exactly what the
`_gvf_fused`/`_sun` guards produce); step values outside it route to the
reference untouched function, preserving e.g. the first=0 divide warning.

## Serial/parallel selection (with evidence)

The task gate asks for `parallel=False` unless the prange variant is proven
bitwise-safe AND ordered identically. It is:

- every output element and every in-place plane write depends only on the
  same (row, col) inputs; no cross-element dependency exists, so no thread
  schedule can reorder results (proof by construction, plus bitwise parity
  on all 30 case-size combinations in parity_table.md);
- measured on the contended development host (`timing_raw.txt`, two runs,
  block_rows=32): serial is 2.0-2.7x SLOWER than the original NumPy (the
  scalar loop loses to numpy's vectorized ops), while the prange variant is
  0.63-0.68x / 0.46x / 0.26-0.28x of the original at cols 128/256/1024
  (run1/run2 medians).

Selection: the shipped wrapper default remains `parallel=False` (gate
compliance); the integration recipe passes `parallel=True` explicitly,
justified by the bitwise evidence and both recorded timing runs.
