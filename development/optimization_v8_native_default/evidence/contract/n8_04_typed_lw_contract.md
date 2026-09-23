# N8-04 — Frozen typed longwave owner/ABI contract (primary reducer)

Machine-readable twin: `n8_04_typed_lw_contract.json` (same directory).
Frozen at HEAD `16cdc56c` on `perf/native-optimization` (worktree
`/Users/alansynn/Workspace/solweig-v8-native`). The authoritative sources
ARE the code: `src/solweig_light/radiation/cylinder_longwave.py`
(`_longwave_primary` parallel, `_longwave_primary_serial` serial),
`src/solweig_light/backends/native/lw_primary.ispc`,
`src/solweig_light/backends/native/lw_native.py`,
`src/solweig_light/backends/native_lw.py`. Kernel bodies are byte-identical
to the B7-02 freeze at `dca2035c` (reducer blob `27ba6ce4...`); only the env
dispatcher was added since.

Anything N8-12 (Numba B) or N8-13 (native C) launches against this island
must reproduce this graph **bitwise** — uint32 view of all seven output
columns — on the admitted domain, before it may replace the baseline.

## 1. Typed graph

### 1.1 State

Ten float32 accumulators `a0..a9` per pixel, zero-initialized (`+0.0`, bits
`0x00000000`), one pixel = one independent lane (no cross-pixel reduction,
so the parallel label is bit-identical to the serial label — asserted).

| acc | feeds | acc | feeds |
|-----|-------|-----|-------|
| a0 | sky down; **reflection input with lup** | a5 | sky side (col 2) |
| a1 | veg down | a6 | veg side (col 3) |
| a2 | shade down (both branches) | a7 | shade side (col 4) |
| a3 | sun down (gated branch only) | a8 | sun side (col 5) |
| a4 | reflected down | a9 | reflected side (col 6) |

Output: `col0 = (((a0+a1)+a2)+a3)+a4`, `col1 = (((a5+a6)+a7)+a8)+a9`
(strict left folds), `cols 2..6 = a5..a9` verbatim.

### 1.2 Sweep 1 — ordered `p = 0..P-1`

```
sky      = (shv == 1) and (vsv == 1)
veg      = (vsv == 0) or  (vbv == 0)
building = ( RN32(1.0f - shv) * vbv ) == 1        # exact compare; raw values count
a0 = RN32(a0 + RN32(sky * sky_down[p]))           # pure float32 chain
a5 = RN32(a5 + RN32(sky * sky_side[p]))
# ST-typed chains (see 1.4):
a6 = RN32( f64(a6) + (((surface_sh ⊗ solid[p]) ⊗ cosine[p]) ⊗ veg) )
a1 = RN32( f64(a1) + (((surface_sh ⊗ solid[p]) ⊗ sine[p])  ⊗ veg) )
if solar_gate[p]:          # a REAL branch; inactive arm NOT evaluated
    a8 = RN32(f64(a8) + (((surface_sun ⊗ sun)  ⊗ solid[p]) ⊗ cosine[p]) ⊗ building)
    a7 = RN32(f64(a7) + (((surface_sh  ⊗ shade) ⊗ solid[p]) ⊗ cosine[p]) ⊗ building)
    a3 = RN32(f64(a3) + (((surface_sun ⊗ sun)  ⊗ solid[p]) ⊗ sine[p])  ⊗ building)
    a2 = RN32(f64(a2) + (((surface_sh  ⊗ shade) ⊗ solid[p]) ⊗ sine[p])  ⊗ building)
else:
    a7 = RN32(f64(a7) + (((surface_sh ⊗ solid[p]) ⊗ cosine[p]) ⊗ building))
    a2 = RN32(f64(a2) + (((surface_sh ⊗ solid[p]) ⊗ sine[p])  ⊗ building))
```

Predicates multiply as **numbers** (`0.0f`/`1.0f`), never branches:
`0*Inf = NaN` is an observable. Integer literals (`==1`, `==0`) promote to
float64 compares in the numba IR — truth-identical for these operands.

### 1.3 Reflection — after sweep 1 completes

Reads the **completed** `a0` and `lup[pixel]` (a barrier between sweeps):

```
r0        = RN32(a0 + lup[pixel])        # float32 add
r1        = RN32(r0 * reflection_factor) # float32; factor is float32
r2        = RN32(r1 * RN32(0.5))
reflected = RN32(r2 / RN32(pi))          # DIVISION by stored f32 pi 0x40490FDB
```

Reciprocal rewrite is forbidden and bit-different
(`0x40601716` division vs `0x40601715` reciprocal at x=11.000000953674316).

### 1.4 Surface-scalar profiles — two different typed graphs

* **f64 profile** (the real accepted pipeline; numpy float64 scalar or
  Python float): chains compute in float64, round ONCE at the accumulator
  store — `a = RN32(f64(a) + c64)`. **Never** `a = RN32(a + RN32(c))`.
* **f32 profile** (synthetic, also frozen in B7-02): same expression tree,
  every node float32, `a = RN32(a + c32)`.

Same supplied value, different provenance ⇒ different bits (pinned:
surface `1+2^-25`, solid `[1, 2^-24]` ⇒ a6 `0x3F800001` vs `0x3F800000`).
Both scalars must share one provenance; a candidate implements both or
restricts its admission domain.

### 1.5 Sweep 2 — ordered `p = 0..P-1`

```
mask = (shv == 0) or (vsv == 0) or (vbv == 0)     # occlusion predicate
a9 = RN32(a9 + RN32(RN32(RN32(reflected * solid[p]) * cosine[p]) * maskf))
a4 = RN32(a4 + RN32(RN32(RN32(reflected * solid[p]) * sine[p])  * maskf))
```

`maskf` is the 0.0f/1.0f multiply: `reflected=Inf` gives NaN on visible
patches (`Inf*0`) and `+Inf` on occluded ones (`Inf*1`) — both pinned.

### 1.6 Forbidden everywhere

Reassociation, tree/pairwise sums, dot products, sorted-order accumulation,
tensor-core approximations, FMA contraction in mixed mul+add nodes
(`fastmath=False`; the native build audits assembly for fused mnemonics and
refuses to emit any), select-evaluation of the inactive solar_gate arm,
`mask=false → +0` without a signed-zero/nonfinite proof.

**Transcendentals: none.** No acos/classifier/SLEEF call exists in this
reducer; SLEEF obligations attach to the sky-patch/classification layers
outside this island.

## 2. Input signature and admitted domain

17 args: `sh, vs, vb` float32 `[B,P]` (raw values need not be 0/1);
`sun, shade` bool `[B,P]`; `solid, sine, cosine` float32 `[P]`;
`directions` float32 `[P,4]` and `gate` bool `[P,4]` — **never read**;
`solar_gate` bool `[P]`; `sky_down, sky_side` float32 `[P]` any element
stride (real path: stride-12 column views); `surface_sun, surface_sh` per
1.4; `lup` float32 `[B]`; `reflection_factor` np.float32 scalar or 0-d f32
ndarray (a Python float is not admitted). Returns float32 `[B,7]`, owned by
the kernel. Domain: `B ≥ 0` (B=0 early-returns the zero frame without
touching patch data), `P = 1..609`; production target P=153,
block_pixels=128. Wrapper guards and their order are listed in the JSON
(`admitted_input_domain.wrapper_level`); scalar `solar_altitude` in the
original path keeps its original TypeError.

## 3. Owner/ABI obligations (for any new consumer)

* **Pre-launch decline** (`UnsupportedInput`, before any native work):
  dtype/ndim/shape/stride violations per §2, P outside 1..609, B<0, gang
  not in {4,8}, surface provenance mismatch, non-f32 reflection factor,
  caller `out` overlapping any input byte extent. The caller then keeps the
  unchanged Numba fallback in the original guard order.
* **Inputs never written.** Bool arrays cross the ABI as zero-copy uint8
  views. Execution is synchronous — nothing can be unmapped or mutated
  in flight; no partial publication.
* **Handle/lease/generation**: resolve the dylib through a digest-gated
  cache (`build_stamp.json` `kernel_sha256` is the generation key; kernel
  sha256 `52652a58...`), process-pinned `_LIBS` keyed by gang, per-user
  cache dir (`SOLWEIG_LIGHT_NATIVE_CACHE` or `~/.cache/solweig-light/native`).
  N8-10's workflow-owned handle must add PID scoping and keep all
  hash/JSON/build IO out of per-block timed regions.
* **Error propagation**: build failures (missing ispc, rc≠0, missing dylib)
  are loud `RuntimeError`s; post-launch failures propagate; only
  `UnsupportedInput` falls back.
* **Build contract**: `-O2 --opt=disable-fma --math-lib=default`, no
  `--fast-math`; assembly FMA audit gates the artifact. Entries
  `lw_primary_f32` / `lw_primary_f64` (+`_g4`/`_g8` libs), gang=8 default.
* **Scheduling**: pixels across ISPC lanes, ordered patch sweeps per lane,
  one effective thread; serial and parallel labels map to the same kernel.

## 4. Exactness gates (executable)

* **Oracle**: `tests/optimization_v8/reference/lw_reference_oracle.py` —
  independent NumPy re-implementation of the graph (both profiles).
* **Identity tests**: `test_typed_graph_identity.py` — adversarial grid
  (B ∈ {0,1,7,8,9,11,13} incl. W=8 tails and primes; P ∈ {1,2,3,5,7,11,13,
  153} plus 609 boundary; normals, subnormals, ±0, ±Inf, NaN, near-one
  thresholds, finite cancellation, raw visibility values, gate patterns,
  strided/negative-stride/one-element sky columns), both kernels, both
  profiles, all seven columns, uint32-exact; plus hand-derived bit pins for
  every discriminator in §1.
* **RN32 rule** (`test_rn32_accumulation_rule.py`): pins
  `a = RN32(f64(a)+c)` via the `0x4B800001` vs `0x4B800000` discriminator,
  and includes the clearly-marked MUTATION CHECK: a local NumPy mock of the
  forbidden `RN32(a+RN32(c))` fails the discriminator (teeth) while
  agreeing on a benign input (faithful single-rule mutation).
* **Order** (`test_sweep_order.py`): patch order is an observable in BOTH
  sweeps (`[2^24,1,1]` vs `[1,1,2^24]` ⇒ `0x4B800000` vs `0x4B800001`),
  and permuting the inputs equals running on permuted data (no hidden patch
  identity).
* Current status: **112 passed / 0 failed** (0.62 s cached, 3.25 s cold;
  threads pinned to `min(4, NUMBA_NUM_THREADS)`; no `NUMBA_NUM_THREADS`
  export — avoids the v5 env-vs-set conflict hazard).

B7 coverage is REUSED, not duplicated: the 520-call bitwise replay in
`tests/optimization_v7/reference/test_v7_contract_freeze.py` over
`optimization_v7_backends/evidence/captures/` (manifest `9caa229f...`,
fixtures `4a48530a...`, typed IR `3eff3591...`) already pins the real
pipeline serial+4-thread calls and the P1/B0/raw-visibility/nonfinite-lup/
direct-scalar edges. No file under `tests/reference/` or any pre-existing
golden was read for mutation or overwritten.

## 5. Review checklist for N8-12/N8-13

1. Candidate == oracle, bitwise, on the full adversarial grid, both
   profiles, both sweep orders.
2. Every discriminator in §1 reproduced (or the input declined pre-launch).
3. Accumulator adds single-round through f64 where §1.4 requires.
4. Division by stored pi, mask multiplies, signed zeros, NaN/Inf payloads
   bitwise.
5. No FMA/contraction in emitted code (assembly audit attached).
6. Decline taxonomy, alias checks, handle generation and error propagation
   per §3 — each with its own test.
