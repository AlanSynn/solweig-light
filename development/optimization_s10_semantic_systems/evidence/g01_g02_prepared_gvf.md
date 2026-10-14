# S10 G01+G02: prepared GVF route on the production dtype profile

Date: 2026-10-14. Branch `perf/s10-semantic-systems`, on top of T01 (`33ab050f`).

## Dtype-profile finding (root cause)

A post-T01 stage profile showed `gvf_2018a` at ~45% real wall time at the
default `threads_per_worker=1` (0.87 s of 1.93 s on the landcover golden
cell), routed to the serial per-direction original. The reason it never takes
the compiled route at ANY thread count: production landcover scenes carry a
**float64 `Tg`** (the daytime amplitude expression promotes through the f64
landcover parameters — the same materials mechanism as the T01 Tgwall U
profile), and every compiled GVF guard (`_supported`) requires all-f32
arrays. Guard probes on the golden scene: 14/14 calls rejected, sole failing
input `Tg:float64`. The compiled GVF lineage (C5-22 fused, C6-30 prepared)
has therefore never engaged on landcover production scenes; it engaged only
on no-LC scenes, whose scalar parameters keep `Tg` float32.

cProfile caveat recorded: an intermediate profile attributed ~63% to this
stage via wrapper-call inflation (`_operate` 238k calls); wrapper-timed wall
clocks put it at ~45%.

## Change

1. **G01 dispatch** (`engine.gvf_2018a`): the `threads==1` path now enters
   `prepared_gvf_step(..., parallel=False, delegate=serial)`. Unsupported
   inputs and `SOLWEIG_LIGHT_GVF_PREPARE=0` delegate to the exact H=1
   baseline (`ground_view.gvf_2018a`), so rejected calls behave as before.
   The delegate drops the `parallel`/`block_rows` kwargs the prepared
   entry forwards for the fused route (the baseline takes none).
2. **G01 Tgwall U clause** (`gvf_prepared._admits`): size-one arrays of any
   float dtype admitted (T01 U profile); multi-element arrays remain
   float32-only.
3. **G02 Tg dtype admission** (`gvf_prepared._admits`): `Tg` removed from the
   all-f32 `_supported` tuple; float32 and float64 admitted, any other dtype
   delegates. Tg reaches the snapshot only through the Lup expression,
   evaluated in NumPy here and float32-converted exactly as the baseline's
   per-direction `_direction_snapshot` does.

## Proof

- The C6-30 differentials already prove `prepared_gvf_step` **bitwise**
  (uint32 views) against both the fused baseline and the verbatim original
  engine body for `parallel=[False, True]` — 217 tests, all passing with the
  change.
- New S10 tests (`tests/optimization_s10/semantic/
  test_g01_prepared_gvf_dispatch.py`, 14 cases): prepared ≡ original
  **bitwise** on float64-Tg scenes (water × buildings variants, caller-
  visible Tg included); dispatch route matrix at H=1 (U32/U64 Tgwall,
  multi-element f32 admitted; multi-element f64, f16/int Tg delegated with
  bitwise baseline parity); kill switch at H=1; threads>1 route unchanged
  and now also unlocked for f64 Tg.
- Pipeline goldens: `landcover` and `landcover_normalized` E2E cases pass
  with the prepared route active (these tests run at the default H=1, so the
  new dispatch is exercised); within frozen comparison_v1 budgets. Because
  the prepared route is bitwise-equal to the original on this profile, and
  the pre-change production path delegated to that same original, E2E
  outputs on this scene are bit-frozen, not merely in-budget.
- `tests/unit` failure set byte-identical to baseline (10 pre-existing).

## L2 paired benchmark (protected cell #1, landcover, H=1, 24 steps)

A = `65097719` (post-T01), B = G01+G02 working tree; 5 alternating pairs,
1 warmup + 3 timed in-process runs per observation, fresh subprocess per
side (independent JIT caches):

| pair | A median (s) | B median (s) | ratio |
|---|---|---|---|
| 1 | 1.9434 | 1.1565 | 1.6805 |
| 2 | 1.9748 | 1.1094 | 1.7802 |
| 3 | 2.0443 | 1.1669 | 1.7520 |
| 4 | 1.9977 | 1.1176 | 1.7875 |
| 5 | 2.0009 | 1.1812 | 1.6939 |

**Paired-median geomean 1.738** (min 1.680). Cumulative vs main on this
cell: 3.26 s → 1.14 s ≈ **2.86×**. Raw record:
`/storage/scratch1/1/dsynn6/solweig-light-s10-raw/bench/paired_ab_g02.jsonl`,
archived to Dropbox `s10/`.

Post-change stage wall times (same probe): gvf 0.87 s → 0.22 s; remaining
top stages `Lcyl by_demand` 0.24 s (19.6%), `Kside` 0.17 s (13.8%).

## Threats to validity

- One golden scene/tile for L2 (cell #1); no-LC control cells are unchanged
  (f32 profile took the compiled route before at H>1; at H=1 they now gain
  the same dispatch — covered by the route tests, not yet by a separate L2
  cell).
- The intermediate no-gain observation (delegate firing everywhere before
  G02) is preserved in `paired_ab_g01.jsonl` as the causal record.
