# N8-03 protocol freeze — small evaluation, held-out cells, promotion gates

Machine-readable twin: `n8_03_protocol.json` (same directory; authoritative).
Frozen at HEAD `16cdc56c` on `perf/native-optimization`, **before any new
candidate performance results exist**. Gates are copied verbatim from
`optimization_v8_native_default/PROMOTION_POLICY.md`.

## Controls

`A0` accepted Numba default arm (env unset) · `B1` N8-12 direct-AoSoA producer
+ equivalent-layout Numba kernel · `C1` N8-13 same producer + native AoSoA
consumer · `C0` old opt-in ISPC g8 (diagnostic only) · `auto` post-integration
env-unset packaged candidate (used only from N8-43 on) · `M0` main DX baseline
(no performance claim). B7-60/B7-31 values are **historical**, not fresh
matched controls.

## Gates (frozen verbatim — see JSON `gates_verbatim_from_promotion_policy`)

Geomean `A0/auto >= 1.10` across primary native-eligible cells; per-cell
paired median `A0/auto >= 1.05` and `B1/auto >= 1.05` at the installed
region/pipeline boundary; `<= 3%` paired median regression in protected cells;
`>= 80%` actual native coverage of predeclared eligible pixel-patch work per
primary cell with C-entry counter proof; first use performs no build/download;
cold full-entry guard within the 3% paired bound; censored-run/noise rules as
written. Exactness: N8-04 typed LW contract + the 112-test
`tests/optimization_v8/reference/` suite are mandatory for B1/C1 admission —
bitwise uint32 view of all seven output columns on the admitted domain.

## Cells

- **Tuning:** real scene `tests/reference/state_sequence_original_cpu/scene`
  (32x35, 153 patches, 48 steps; five input hashes re-verified at freeze) with
  short leaf_kernel/region_total repetitions, plus boundary-only adversarial
  arrays from the N8-04 suite.
- **Held-out primary (native-eligible), SYNTHETIC-DEVELOPMENT label:** four
  generated scenes — 128/256 square x 24 records, dense + vegetation (canopy
  fraction 0.1484) — under `benchmarks/fixtures/optimization_v8/scenes/`,
  generator `tools/optimization_v8/n8_03_build_scenes.py`
  (sha256 `c272575d…`, adapted from the C6-101r builder; met = header + first
  24 records of the real own-met file, day 200 = 2020-07-18). Six cells:
  **P1/P2** 128 dense/veg pure-default (env unset, ambient RuntimeOptions
  defaults, block 128 — the main-compatible cells, quiet host required),
  **P3/P4** 128 dense/veg production (block 1024, threads-per-worker 4, 12 GiB
  B7-60 budget), **P5/P6** 256 dense/veg default-B128 with 12 GiB pinned
  admission (recorded deviation: the 256²×24 estimator reserve ~7.1 GiB cannot
  fit ambient 0.5×-available admission on this 16 GiB host).
- **Protected:** PR1 explicit `SOLWEIG_LIGHT_LW_BACKEND=numba` cell; PR2
  unsupported-input decline cell (must fall back to A0 bitwise); both under the
  3% bound.
- **target_campaign:** actual 24-tile corpus ABSENT (b7_51); fallback = the
  synthetic 4-tile 1024²×24 scale guard, explicitly labelled not-actual-target.
  Open dependency: the v6 builder's v5 metfile is gone; a rebuild substitutes
  the same real-scene-derived 24-record met.

All four scenes completed a one-step smoke through the real public entry
(walls_aspect → calculate_svf → run_utci_tiles, backend env unset, 10/10
simulation TIFFs each, distinct digests; records in `n8_03_smoke/`). Smokes
used pinned 12 GiB admission because teammates held the host; the pure-default
ambient attempt and its `ResourceAdmissionError` are preserved in
`n8_03_smoke/ambient_default_admission_attempt.json` and drive the quiet-host
requirement on P1/P2.

## Boundaries, budgets, proof

All five timing boundaries (`leaf_kernel`, `region_total`, `workflow_warm`,
`workflow_first_use`, `target_campaign`) as defined in BENCHMARK_PROTOCOL;
completion not enqueue; instrumented/uninstrumented separate; independent
child processes per H change. Fixed host identity (M1 Pro 10-core 16 GiB,
macOS 26.6.2/Darwin 25.6.0, python 3.12.13/numba 0.67.0/numpy 2.4.6/GDAL
3.13.3/ispc 1.31.0); exclusive benchmark owner; ambient windows before/after
every timed block; triage 2 alternating pairs, finalists 3 pairs per cell
(A/C, C/A or frozen randomized); medians labelled observed small-sample
summaries; memory-pressure kill = censored run (recorded, never erased); one
final large campaign with at most one causal retry. Native execution proof =
C-entry counters at the admitted function pointer vs predeclared eligible
pixel-patch work (denominator recorded on the first control run, identical
across arms or the pair is invalid); build stamps/loaded modules are not
proof.

## Measured context frozen before variants (N8-02)

Island 21.0% of Lcyl (B=128 default arm); per-call native preparation
130.96–251.6 µs vs C entry 61.9 µs and Numba island ~146 µs/call; decode ~41%
of Lcyl; current g8 native/default end-to-end 1.007 (B=128) / 1.021 (B=1024).
N8-30 review of N8-02 is in flight: any confirmed defect amends this section
by appendix with a new protocol version, never by silent edit.
