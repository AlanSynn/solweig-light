# S10-20: integrate first wave + actual small chronology

Date: 2026-10-14. Branch `perf/s10-semantic-systems`, evidence produced at
`4506a2e9`. Machine-readable companions: `integration_commit.json`
(provenance, state, deviations) and `l2_results.json` (the two comparison_v1
differentials + pool bitwise verdict) in this directory. Raw harness, mode
outputs, and logs live outside git under
`/storage/scratch1/1/dsynn6/solweig-light-s10-raw/integration/`
(harness/probe sha256s in `integration_commit.json`;
archived to Dropbox `Alan Synn/Research/solweig-light/s10/
s10_s20_integration.tar.gz`, sha256
`0befebe8d74338dd77e7485f8052f6c1c332855e61bf5770bb7582e24481fdcf`,
plus `s10_s20_first_multitile_refusal.txt`). The archive holds scripts +
JSON outputs + logs; the copied golden inputs and output TIFF trees are
excluded (regenerable: `s10_integration_run.py <mode>`, determinism proven
by the two independent run24 executions).

## What ran

Four real full-pipeline runs at HEAD, each in its own process:

| run | chronology | config | verdict |
|-----|-----------|--------|---------|
| A `default` | 24-step golden | pure defaults (no env, no options) | admitted and completed |
| B `run24` | 24-step golden | workers=1/threads=1, explicit 5.5e9 budget | all ten products within frozen budgets vs stored original-CPU goldens |
| C `run48`/`oracle48` | 48-step half-hourly | matched workers=1/threads=1, 5.5e9 | candidate vs forced-reference oracle within frozen budgets |
| D `multitile` | 2 × 24-step | `run_utci_tiles` pool workers=2/threads=1, 9.6e9 | tile 0_0 bitwise ≡ run B (10 files × 24 bands) |

## Run A: the default path admits the golden tile at this HEAD

The pure default run (no env, no options) **admitted and completed** the
24-step golden tile: job estimate `809,673,344 B` against a resolved default
budget view of `2,744,623,104 B` (4% of the container-correct
`68,719,476,736 B` view; S03b). The admission probe
(`s10_default_probe.py`, wrapping `runtime.plan_admission`) recorded the
decision inputs verbatim. Default options on this host are
`workers=1, threads_per_worker=1, cpu_budget=1` — run B pins exactly this
execution config.

This refines, not contradicts, the S03b host demo: the default outcome is
**estimate-dependent** (tile shape drives the estimate; headroom drives the
budget view). The S03b demo's refusal was a larger-estimate scenario. Both
observations stand; neither is a fixed host verdict.

## Run B: 24-step golden, stored-golden comparison

Three repetitions under the explicit 5.5e9 budget (the only deviation from
run A). The differential harness semantics are `test_pipeline_reference.py`'s
verbatim (schema/metadata/nodata exact, nonfinite masks equal, frozen
`comparison_v1` rules, worst coordinates reported):

| file | worst max_abs | budget |
|------|---------------|--------|
| Kdown | 1.83e-04 | atol 0.05 |
| Kup | 3.05e-05 | atol 0.05 |
| Ldown | 4.58e-04 | atol 0.05 |
| Lup | 1.83e-04 | atol 0.05 |
| Shadow | 0 (exact) | — |
| TMRT | 6.10e-05 | 0.01 |
| Ta | 0 (exact) | — |
| UTCI | 4.96e-05 | 0.02 |
| WBGT | 5.72e-05 | 0.02 |
| Wind | 0 (exact) | — |

Two independent `run24` executions produced identical worst values and
coordinates (`compare24` re-verified the second execution from disk):
run-to-run determinism on this path. Wall times (8.5/7.7/6.6 s at loadavg
≈ 19-20) are contention artifacts, not performance claims — the quiet-window
rerun is S10-30.

## Run C: 48-step real chronology with a forced-reference oracle

The 48-step chronology is a **disclosed extension** of the real golden
metfile: each hourly row duplicated at `imin=30` with identical forcing
(pipeline `loadtxt` takes all rows as the chronology; no date filter;
`timestepdec` becomes 0.5 h). No original-CPU goldens exist for this
chronology, and the upstream oracle environment does not exist on this host —
so the oracle is a **forced-reference full-pipeline run**: the same inputs
with every accepted S10 route forced to its pre-S10/fallback path:

- R03: `SOLWEIG_LIGHT_ANILUM_PACKED=0` (retained Python loop),
- G01/G02: `SOLWEIG_LIGHT_GVF_PREPARE=0` (serial delegate),
- T01: `patch_radiation._uniform_tgwall` forced to decline — the Lcyl/dpc
  primaries then fall back to the serial reference, which is main's
  census-documented behavior on this profile. All four admission sites
  resolve the name from `patch_radiation` at call time, so one patch bites
  everywhere.

Engagement evidence (route counters read after each run):

| route | candidate | oracle |
|-------|-----------|--------|
| prepared GVF delegate (serial count) | 0 | 30 |
| `Lcyl_v2022a` primary / reference | 48 / 0 | 0 / 48 |
| `define_patch_characteristics` primary / reference | 48 / 0 | 0 / 48 |

(The candidate's `prepared=30` counts calls *entering* `prepared_gvf_step`,
which the engine wrapper makes unconditionally; with serial=0 all 30 were
served by the prepared route. The oracle's serial=30 is the discriminator.)
The differential passed both schema and value gates: `Kdown`/`Kup`/`Shadow`/
`Ta`/`Wind` bitwise 0; `Ldown` 2.75e-04, `Lup` 1.22e-04 W/m² (budget 0.05);
TMRT 6.10e-05 °C (budget 0.01); UTCI 6.49e-05, WBGT 5.53e-05 °C (budget
0.02) — the documented T01 ≤2-ulp Lcyl deltas propagating end-to-end, with
2-3 orders of magnitude of budget headroom.

## Run D: worker-pool multi-tile

First attempt with the 5.5e9 budget raised
`ResourceAdmissionError` **before any worker spawned** ("requested 2
concurrent phase jobs but only 1 fit: the 2 largest reservations sum to
8,625,995,928 B against a 5,070,503,270 B reservation base") — C6-42
`policy='reject'` public semantics, correct by design. The message is
recorded verbatim in `integration_commit.json` (`run_D_multitile.
refusal_record`) and in the uploaded transcript capture
`s10_s20_first_multitile_refusal.txt`; the successful rerun overwrote the
raw stderr log, which is disclosed in the capture. The rerun used the
documented remedy (explicit budget
9.6e9, disclosed) and completed both tiles concurrently. Tile 0_0 is
**bitwise-identical** to run B's in-process tile on all 10 products × 24
bands (uint32 views for floats): pool scheduling and subprocess isolation
are value-invariant.

## Scope and threats

- The second multitile tile is a byte-copy of the golden tile (same-content
  tile): the claim is pool-vs-serial value invariance, not spatial scaling.
- Wall times under loadavg 17.7-20.3 are contention artifacts only.
- The 48-step chronology exercises `timestepdec` 0.5 h — a state-init and
  hourly-`Twater` cadence variant that no stored golden covers; it is
  covered by the forced-reference differential, not by original-CPU goldens.
- Environment note: `from osgeo import gdal` fails in a bare interpreter on
  this host; importing `solweig_light` first bootstraps the native GDAL load
  path. The harness imports `solweig_light.pipeline` before `osgeo` in the
  compare modes.

## Gates at this commit

- `tests/optimization_s10`: 59/59.
- Landcover differential goldens: 2/2.
- Unit-suite known failures unchanged (documented in the register; not
  touched by this task).
