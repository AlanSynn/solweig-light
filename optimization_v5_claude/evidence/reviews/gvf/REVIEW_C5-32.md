# C5-32 Review: v5 GVF patch (G02 source hoisting + G03 fused gather+postprocess)

- **Reviewer**: independent GLM review (Opus unavailable). Reviewer is not the author.
- **Patch**: 8933c4ae (G02) + b42035c7 (G03) on `perf/claude-glm53-cpu-v5-gvf`, worktree
  `/Users/alansynn/Workspace/solweig-light-v5-gvf` (read-only review). Base bfd9915e.
- **Scope**: `src/solweig_light/radiation/ground_view.py` + `tests/optimization_v5/gvf/`.
  Verified `git diff bfd9915e..b42035c7 --name-only` touches exactly these; engine.py untouched.
- **Verdict**: **G02 APPROVE (exact). G03 APPROVE as experimental/internal with one required
  follow-up before dispatch flips** (F1 below: aliasing-gate gap unique to the fused route).

## 1. G02 exactness — VERIFIED from code

### 1.1 Water trap (the critical area) — correct
Base ordering inside `_sun` (per direction): `Lup = ...` (base :216; patched :324) is
evaluated **before** `Tg[lc_grid == 3] = (Twater-Ta).astype(f32)` (base :217-218; patched
:325-326), and `_gather` (base :242-248; patched :337-338) runs later with the already-
computed `Lup` object. Lup is a freshly allocated `_operate` output (engine.py:1705
`_operate` → ufunc result array; nothing aliases it to Tg), so mutating Tg cannot rewrite
it. Therefore, in the baseline:
- direction 0's gather **copies the pre-mutation Lup** (the copy happens inside `_gather`
  after the mutation, but from the pre-mutation values);
- directions 1..17 recompute Lup from the mutated Tg — all bitwise identical to each other
  because the mutation writes one constant onto the fixed mask `lc_grid == 3` (mask carrier
  lc_grid is not rewritten unless Tg aliases it — see 1.3) and re-execution is a no-op.

The patch's two-snapshot scheme (`_direction_snapshot`, ground_view.py:240-259) captures
exactly these two states: `prepared['lup']` at direction 0 (pre-mutation), `lup_rest` at
direction 1 (post-mutation), reused for directions 2..17. **Tg is NOT hoisted** — it is
passed live at :442 every direction; the caller-visible mutation is preserved and asserted
by the tests (test :81-85).

The postprocessing Lup term (base :261; patched :369) re-evaluates the expression inline in
`_sun` with live (post-mutation) Tg in **both** baseline and patch — unchanged code.

### 1.2 Direction-invariance of the other hoisted sources — verified by exhaustive
assignment audit of base `_sun`/`_gather`/`_gvf`
The only in-loop mutations in the baseline are `sunwall[sunwall > 0] = 1` (:212/:320) and
the Tg water write. Buildings, shadow, Lwall (reads Tgwall/ewall/SBC/Ta — never mutated),
albshadow (= alb_grid*shadow), alb (= alb_grid), albedo are never assigned between
directions. `first`/`second`/`scale`/`ewall`/`albedo_b`/`landcover` are **rebound to fresh
copies** per direction inside `_sun` (:313-316, :330-333), never mutated — so per-direction
copies in the baseline are bitwise identical across directions and hoisting is exact.

### 1.3 `may_share_memory(Tg, {buildings, shadow, alb_grid})` gate (:433) — necessary and
sufficient **for G02**
- Necessary: the hoisted copies at :436-438 are made **before** any water mutation, while
  baseline direction 0's gather copies arrive **after** it. If Tg shared memory with any of
  those three, the snapshot would capture pre-mutation bytes where the baseline uses
  post-mutation bytes from direction 0 onward. Gate routes such inputs to `prepared=None`,
  i.e. the untouched legacy copy path at identical chronological points. Author tests
  exercise genuine shared memory for all three keys (test :131-158, non-vacuity asserted).
- Sufficient: G02 hoists no other caller-visible state. `walls`, `wallsun`, `dirwalls`,
  `emis_grid`, `lc_grid`, `Tgwall`, `first`, `second`, `scale` are still read per direction
  from the caller's objects at the same points as the baseline. Probes confirmed exactness
  under aliasing of Tg with `walls`, `emis_grid`, `lc_grid` (f32 mask carrier), `Tgwall`
  (Lwall reads it post-mutation every direction, so the dir-0 snapshot lands on the single
  post state), and `emis_grid` as a Lup input (two-state idempotency argument holds).
  Aliasing of buildings/shadow/alb_grid with each other is harmless (independent
  `copy=True` snapshots, as in baseline).

### 1.4 sunwall normalization no-op — verified
`_gvf`'s sunwall is `(_operate(...) == 1).astype(np.float32)` (:425): a boolean-derived
array, exactly {0.0, 1.0}; NaN cannot occur in a boolean cast. `sunwall[sunwall > 0] = 1`
writes 1.0 over 1.0 and never touches 0.0 → bitwise no-op, so hoisting the single copy
(:440) across directions is exact. Fractional sunwall is only possible through the direct
`sunonsurface_2018a` entry, which passes `prepared=None` (keyword-only, default) → legacy
path, code unchanged; probe P7 (fractional sunwall 0..2, old vs new `_sun`) is bitwise exact.

## 2. G03 exactness — verified on supported paths

- **Block kernel** `_gather_block_pixel` (:145-187) is a line-by-line mirror of
  `_gather_pixel` (base :85-119): identical arithmetic, casts, `_minimum` NaN policy,
  persistent outside-slice samples, `step+1<=first` prefix snapshots; only the output
  indexing gains the `row-row0` offset. Per-pixel independence preserves parallel
  correctness (`_gather_block_parallel`, :197-202).
- **Postprocess** `_postprocess_block` (:491-531) duplicates `_sun`'s post-gather lines
  (:339-374) node-for-node in order: the four flags, `keep` computation and `-1` clip,
  gvf1/gvf2 with the `gvf2>1` clip, gvfLup1/2, gvfalb1/2, gvfalbnosh1/2 **including the
  `second`-only denominator** (no `+1`, :523 vs :366), the 0.5/0.4/0.9 combines, and the
  lup/alb/nosh add-back terms. `lup_term`/`alb_term`/`nosh_term` (:620-622) are spelled
  identically to `_sun`'s inline terms (:369, :371, :373) and evaluated post-mutation at the
  same chronological position (nothing mutates Tg between the baseline's gather and its
  postprocessing).
- **Accumulation order** preserved: directions outer / row-blocks inner, in-place float32
  `+=` per block slice (:633-652); each pixel receives its 18 adds in original azimuth
  order, matching the baseline's full-raster `+=` sequence. Cardinal windows use the same
  `azimuthA[j]` predicates. Post-loop reductions (:653-670) are textually identical to
  `_gvf` (:463-480), including `gvfNorm[buildings == 0] = 1`.
- **Guard union**: fused delegates to `_gvf` on `_gvf`'s own guard (:547-548) and on
  `_sun`'s first/second clauses (:549-551). The delegated dispositions reproduce
  structurally (it is literally the same downstream code). The `_sun` `facesh`
  UnboundLocalError gap (no `else` in the azilow/azihigh chain) is unreachable for the
  fixed azimuth grid (azilow==0 would need azimuth ≡ 90° mod 180°; 5+20k never hits it) in
  all three routes; the fused chain (:612-619) replicates the same no-else shape. The
  schedule `RuntimeError` raise site is reached at the same logical point (after the same
  Tg mutation) in all routes — confirmed empirically (probe below).

## 3. Findings

- **F1 (MEDIUM before dispatch flip / LOW today — latent, unreachable): `_gvf_fused`
  hoists state the baseline re-reads per direction, and its aliasing gate (:575) checks
  only (buildings, shadow, alb_grid).** Unlike `_gvf`, the fused route additionally
  hoists `wallbol = (walls > 0)` (:587) and `scale/ewall/albedo_b/landcover` copies
  (:583-586), which the baseline re-copies/re-computes per direction inside `_sun`
  (base :313-319). Under caller-side aliasing of Tg with these inputs the routes diverge:
  - *Demonstrated end-to-end*: `scale` passed as a 0-d view into a Tg water cell (valid
    value 1.0 pre-mutation): baseline and patched `_gvf` both raise `RuntimeError`
    (schedule build) at direction 1; `_gvf_fused` hoists scale=1.0 and **completes** — a
    raise-vs-return disposition divergence.
  - *Internal-only so far*: Tg aliasing `walls` — wallbol provably flips (6 cells in the
    probe scene) between baseline direction 0 and directions 1..17; fused keeps the
    direction-0 wallbol. Outputs nevertheless matched bitwise in 40/40 random seeds,
    because manifestation needs a `keep == 1` coincidence (facesh==0 AND
    weightsumwall==second at a flipped cell). The internal divergence is real.
  - Mitigation: route is not called anywhere in src/ (grep: only its own definition and
    docstring; "internal until the integrator flips dispatch"). **Required before flipping
    dispatch**: extend the gate to `walls` and to 0-d views for scale/ewall/albedo_b/
    landcover (or route any Tg memory overlap with any caller input to the legacy path).
- **F2 (NOTE)**: `test_gvf_fused_delegates_sun_level_guards` (:361-381) compares only the
  raise-vs-ok label, not the exception type, for the raising cases. Benign today because
  both patched routes delegate to the same `_gvf` code, but a type equality assert would
  pin it.
- **F3 (NOTE)**: the baseline comment inside `_gather` (:214-215, pre-existing) — "Each
  direction owns fresh receiver fields; subsequent Tg mutation cannot rewrite Lup" — was
  always imprecise (direction 0's Lup copy is pre-mutation by design). The new
  `_direction_snapshot` docstring documents the true two-state behavior correctly; consider
  fixing the stale comment when convenient.
- No correctness issues found in G02. No other issues found in G03.

## 4. Test honesty — verified independently

- Reference module `tests/optimization_v5/gvf/_reference_ground_view.py` diffed by me
  against `git show bfd9915e:...ground_view.py`: differences are exactly the module
  docstring, `cache=True`→`cache=False` on this module's own kernels, absolute engine
  imports, and the dropped (unused-by-tests) public wrappers. Functions and the
  water-mutation ordering are byte-identical. Claim verified.
- Comparisons are bitwise via uint32 views on all 17 outputs plus post-call Tg
  (:50-66, :81) — catches NaN payloads and signed zeros; NaN/inf/-0.0 input test at :100.
- Non-vacuity controls: water mutation must actually change Tg (:82-85); aliased mutation
  must actually change shared bytes (:156-157); direction-order control (reversed order
  must differ) (:274); NaN-first control must actually raise (:371).
- Water trap is observably exercised: `test_sun_water_trap_first_direction_differs`
  (:161-191) asserts direction 0's gvfLup differs from direction 1's in both modules
  (gather Lup snapshot is pre-mutation, postprocessing term post-mutation → the split is
  load-bearing and reproduced), and that mutated Tg persists bitwise across calls.
- Aliased-Tg tests construct genuine shared memory after scene snapping (:141-146,
  :338-343). No skips/xfail in the suite. 73 tests collected = 24 (gvf grid) + 32 (fused
  grid) + 17 singles — no hidden parametrization gaps.

## 5. Runs (threads≤2, read-only gvf worktree)

- `NUMBA_NUM_THREADS=2 uv run --extra test pytest tests/optimization_v5/gvf/ -q`
  → **73 passed** in 4.04s (expected 73).
- `uv run --extra test pytest tests/differential -k "gvf or ground" -q`
  → **217 passed**, 2614 deselected, in 3.95s (expected 217; full selection ran, no subset).

## 6. Adversarial probes (reviewer-authored, /tmp/gvf_c532_probe.py + sweeps)

All old-vs-new via the verbatim reference module, bitwise uint32 on 17 outputs + Tg:

| Probe | _gvf (G02) | _gvf_fused (G03) |
|---|---|---|
| P1 Tg aliased to walls (link re-established post-snap, asserted) | EXACT | EXACT (outputs; internal wallbol differs — see F1) |
| P2 lc_grid==3 everywhere (whole scene water) | EXACT | EXACT |
| P3 NaN Twater | EXACT | EXACT |
| P4 Tg aliased to emis_grid (Lup input) | EXACT | EXACT |
| P5 Tg aliased to lc_grid (f32 mask carrier) | EXACT | EXACT |
| P7 public `_sun`, fractional sunwall 0..2 | EXACT | n/a (legacy path) |
| P8 Tg aliased to Tgwall (Lwall input) | EXACT | EXACT |
| Scale as 0-d view into Tg water cell | RuntimeError at dir 1 = baseline | **completes — disposition divergence (F1)** |
| 40-seed sweep, Tg∩walls aliasing | 0 divergences | 0 output divergences (internal wallbol divergence confirmed) |

Probe-methodology note: my first probe draft snapped scenes before aliasing, which silently
destroyed the aliasing; fixed by re-linking the shared array after the snapshot with an
`assert may_share_memory` guard. The author's tests do this correctly.

## 7. Verdict

- **G02**: exact. Approve for integration as-is.
- **G03**: numerically exact on all supported/non-aliased paths and on the tested aliased
  raster paths; carries F1 (hoisted wallbol + scalar copies outside the aliasing gate),
  which is unreachable in production today. Approve as internal/diagnostic; **fix F1
  before any dispatch flip** to this route.
