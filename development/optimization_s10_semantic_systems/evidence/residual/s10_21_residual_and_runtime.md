# S10-21: residual profile and joint resource comparison

Date: 2026-10-14. Branch `perf/s10-semantic-systems`, measurements at
`17574b4e`. Deliverables: `residual_costs.json` (disjoint stage costs) and
`runtime_comparison.json` (measured t(W,H) portfolio + worker context) in
this directory. Raw harnesses and outputs live outside git under
`/storage/scratch1/1/dsynn6/solweig-light-s10-raw/residual/` (sha256s listed
below; Dropbox archive follows). Method notes: `THROUGHPUT.md` (Amdahl with
complete boundary overhead, no multiply-counted gains, confidence rules),
`BENCHMARK_PROTOCOL.md` (boundaries, noise policy), dossier
`07_runtime_memory.md` (t(W,H) recording list).

## 1. Residual stage costs (disjoint, small workload)

Wrapper-timed `perf_counter` (the census method — not cProfile), 1 warmup +
3 timed in-process runs of the landcover golden tile (32×35, 24 steps,
workers=1/threads=1, 256 MiB GDAL cap + 5.5e9 budget deviations as in the
census). Tile ≈ 1.17 s (reps 1.29/1.09/1.12 under loadavg ≈ 17-20).

Disjoint accounting — calc 0.709 s:

| stage | calls/run | % calc | route |
|---|---|---|---|
| gvf_2018a | 2 | 31.6% | prepared (C6-30 + G01/G02) |
| Lcyl_v2022a_by_demand | 4 | 28.1% | primary + N9 stream; **dpc nested inside** |
| Kside_veg_v2022a | 2 | 24.8% | compiled primary |
| Lside_veg_v2022a | 4 | 5.1% | NumPy `_operate` body (no compiled twin) |
| anilum_packed | 2 | 2.5% | R03 packed kernel |
| shadowingfunction_wallheight_23 | 2 | 1.7% | exact_23 |
| body residual | — | 6.2% | — |

(Runs are 24 steps; the calls/run column shows the 3-rep accumulator divided
by 3.) Two structural notes: `define_patch_characteristics` fires 24/24
**nested inside** the Lcyl demand span (cylinder_longwave.py:466), so its
cost is inside that stage — not additive; and R03 is verified in-place — the
packed kernel is 2.5% of calc where the retained Python loop was 11.1%
pre-R03, and the body residual collapsed 8.6% → 6.2%.

Pipeline-side buckets (tile = calc + buckets + startup residual):

| bucket | % tile |
|---|---|
| checkpoint (interval=1) | 14.7% |
| write + digests | 4.8% |
| comfort (UTCI/BGT/WBGT) | ~1% |
| state accept / timeline / restore | <0.1% |
| **startup residual (unwrapped)** | **18.7%** |

Reading for S10-22 selection:

1. **Lside compiled twin** — 5.1% of calc (~3.1% of tile): the top remaining
   exact CPU candidate; mechanical A-plus/T01-pattern decode (register row 4).
2. **S07/S09 export+checkpoint** — write 4.8% + checkpoint 14.7% of tile,
   but the checkpoint is fsync/flush-bound at this scale (post-G02 split:
   `_flush` ≈ 43%): bytes-scaled ceiling here ≈ 1.5-2% of tile; production
   scale evidence still owed; D08 forbids interval change.
3. **Startup residual 18.7% of tile is UNWRAPPED** (geometry load/verify,
   metdata, publication, interpreter) — a measurement gap: no candidate can
   be valued there until it is decomposed.
4. gvf + Lcyl + Kside = 84.5% of calc, all on their pinned compiled routes —
   kernel-internal, exactness-frozen (C5/C6/N8/N9): diminishing returns.

No multiply-counting: these are measured shares of disjoint call spans, not
composable speedups; overlapping candidates (e.g. T02/T03-class dispatch
savings inside the same spans) share the combined implementation cost.

## 2. Joint resource comparison: measured t(W,H)

Four same-content 24-step golden tiles (byte-copied keys, disclosed) through
the public `run_utci_tiles` pool path, cpu_budget = 4, budget 19e9, fresh
process per run, frozen alternating order (1×4, 2×2, 4×1) × 3 reps —
the D07 t(W,H) rule: the whole batch is timed, never a per-worker time
divided or summed.

| W×H | runs (s) | median | spread |
|---|---|---|---|
| 1×4 | 43.3 / 33.6 / 28.3 | 33.6 | 1.53× |
| 2×2 | 24.9 / 17.6 / 17.7 | 17.7 | 1.41× |
| 4×1 | 15.4 / 13.0 / 12.7 | 13.0 | 1.21× |

Paired medians: 1×4/4×1 ≈ 2.59, 1×4/2×2 ≈ 1.74, 2×2/4×1 ≈ 1.39.
**The ordering 4×1 < 2×2 < 1×4 holds in all 9 runs — no inversions.** Noise
verdict (THROUGHPUT.md discipline): direction robust on this 4-CPU cgroup
host — process parallelism beats intra-process threads for this batch;
magnitudes contention-affected, indicative only, not an SLA or broad machine
claim.

D07 recording list, satisfied: requested H (options echo), admitted workers
(plan record: 1 / 2 / 4 exactly), worker PIDs per run, per-tile estimates
(0.81 GB each), and the in-worker execution context from a dedicated probe
child spawned with the verbatim `_child_environment` recipe (disclosed: a
diagnostic child, not a tile worker): NUMBA_NUM_THREADS = H exactly
(1/2/4), threading layer `omp`, CPU affinity = 4, applied GDAL cache
3,435,134,976 B per child (the S03b container-correct view). Effective
resource limits therefore match the requested masks; no hidden workload
reduction (same 4 tiles × 24 steps per run).

## 3. Scope and threats

- Same-content tiles measure pool/threads scaling, not spatial diversity.
- All wall times carry co-tenant load (loadavg recorded per run); only
  orderings and within-host comparisons are claimed.
- The startup residual (18.7% of tile) is attributed as a bucket, not
  decomposed — flagged as the measurement gap above.
- Worker-context is probe-child evidence; the tile workers' own masks are
  set by the identical env recipe before first import (runtime.py:663-682).

## 4. Raw artifacts

Outside git, `/storage/scratch1/1/dsynn6/solweig-light-s10-raw/residual/`:
`s10_residual_profile.py` (sha256 `cc14ea7c…`),
`s10_runtime_portfolio.py` (`e2873d3b…`), `s10_worker_context.py`
(`8bd655d4…`), `s10_collect_residual.py` (`bac887a3…`), plus
`residual_profile_out.json`, `portfolio_out.json`, `worker_context_H{1,2,4}
.json`, progress/error logs. Archived to Dropbox `Alan Synn/Research/
solweig-light/s10/s10_s21_residual.tar.gz`, sha256
`fb22af79ac4a218ba2e9b53ba84aa5db4291c4fafbc9fcc15fe1591ab5d854e9`.

## 5. Gates at this commit

- `tests/optimization_s10`: 59/59 (re-run this task; no product code changed
  — measurement-only task).
- No route or numerical behavior touched.
