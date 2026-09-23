# C6-01 D3: v6 primary baseline record (accepted v5 tip under the child-isolated harness)

Date: 2026-09-21. Code under test: accepted v5 tip `e7a2d6ec8594b234820e7783e0ca26d821de7f3d`
(detached worktree `/Users/alansynn/Workspace/solweig-light-v6-measure`, module
origin asserted inside every record). Interpreter:
`/Users/alansynn/Workspace/solweig-light/.venv-light/bin/python` — CPython
3.11.16, numpy 2.4.6, numba 0.67.0, llvmlite 0.49.0, GDAL 3.13.3, arm64.
Math profile: `solweig-portable-sleef-5a1d179d-v1`, fingerprint
`8e4d38460b61b029…cbef30` (full value in every JSON record).

## Harness

Child-isolated per `dossiers/01_measurement_and_baseline.md`: each run is a
fresh process with `NUMBA/OMP/OPENBLAS/MKL/NUMEXPR/VECLIB/BLIS` thread
variables set BEFORE any numerical import, `numba.set_num_threads(H)`
verified, then the dense256 full-chronology `run_tile` workload (L2 tier:
real TIFF scene, one 256x256 tile `0_0`, actual shape `[256, 256]`, 24
records, 153 patches, 10 output flags, `block_pixels=1024`,
`checkpoint_interval=1`, `cache_enabled=True`, `legacy_cache_policy="recompute"`,
cold JIT via fresh per-child `NUMBA_CACHE_DIR`, cold pipeline cache, no
profiler). The GVF kernel route is observed by call-through wrappers on the
two `ground_view` leaves that `engine.gvf_2018a` dispatches between; the
native mask is snapshotted at first real kernel entry and again after the run.

- Harness code: `/Users/alansynn/Workspace/solweig-light-v6-measure/tools/optimization_v6/threading/`
  (`child_runner.py`, `matrix_runner.py`, `paired_timing.py`, `defect_demo.py`, `thread_limits.py`)
- Scene: `/Users/alansynn/Workspace/solweig-light-claude-v5/optimization_v5_claude/evidence/census/scene_dense256` (read-only source; copied fresh per run, stale `output_folder` removed and recorded)
- Records: `optimization_v6_continue/evidence/measurement/`
  (`thread_matrix_v1.json`, `paired_timing_v1.json`, `defect_demo.json`,
  `children/smoke_h1/record.json`, per-slot records under `matrix_runs/` and `paired_runs/`)

## Defect demonstrated (why the old labels are void)

`defect_demo.json`: in ONE process with inherited environment (Numba default
pool = 10 on this host), `runtime_options(RuntimeOptions(threads_per_worker=H))`
was seen by the real engine dispatch (context value 1 then 4) and flipped the
GVF route serial → fused, while `numba.get_num_threads()` stayed **10** in
both contexts. Positive control: `numba.set_num_threads(2)` moved the mask to
2. The old portfolio's `RuntimeOptions(threads_per_worker=H)` labels therefore
confound dispatch route with native parallelism and must not be read as
`t(H)`.

## H-matrix at e7a2d6ec (fresh child per H, one run each)

| requested H | config threads | actual native mask (final / at first GVF entry) | threading layer | admitted plan (workers x H) | observed GVF route | run_tile s | peak RSS |
|---|---|---|---|---|---|---|---|
| 1 | 1 | 1 / 1 | workqueue | 1 x 1 = 1 | `gvf_serial_full` x14 | 25.44 | 321 MB |
| 2 | 2 | 2 / 2 | workqueue | 1 x 2 = 2 | `gvf_fused_g03` x14 | 22.42 | 313 MB |
| 4 | 4 | 4 / 4 | workqueue | 1 x 4 = 4 | `gvf_fused_g03` x14 | 20.68 | 328 MB |

Requested == configured == actual mask in every child; route flips exactly at
the H=1/H>1 boundary (serial full vs fused G03), which is why H=1 rows are a
different algorithm, not a thread count of the same one.

## Paired timing (predeclared: 3 alternating pairs + old-style label, min-of-3)

| label | native mask | GVF route | runs (s) | min s | median s |
|---|---|---|---|---|---|
| child-isolated H=1 | 1 | `gvf_serial_full` x14 | 26.946, 25.576, 25.37 | **25.37** | 25.576 |
| child-isolated H=4 | 4 | `gvf_fused_g03` x14 | 20.786, 21.572, 20.62 | **20.62** | 20.786 |
| old-style label "H=4" (inherited env + in-process RuntimeOptions) | **10** | `gvf_fused_g03` x14 | 21.669, 20.238, 19.755 | **19.755** | 20.238 |

Reading (triage only, L2 development tier):

- Route + native-4 effect vs isolated H=1: 25.37 → 20.62 s (min-of-3,
  ~1.23x) — this mixes the serial-vs-fused algorithm change with native
  parallelism and cannot be split further at this tier.
- The old-style label ran with mask 10 (not 4) on the fused route and landed
  within ~0.9 s of isolated H=4: on dense256 the fused route saturates by
  ~4 native threads, and the old harness's inflated mask mostly hid behind
  its route choice. All old-style numbers are still void as t(H) evidence.
- Every timed run stayed well under the 300 s cap; no failures, no timeouts,
  no retries (9/9 slots + 3/3 matrix children + 1 smoke run returned 0).

## Host and exclusivity (recorded, not assumed)

Apple M1 Pro, 8 performance + 2 efficiency cores (`hw.ncpu`=10),
`os.sched_getaffinity` absent on macOS, 16 GiB RAM. Exclusivity was checked
before each timed pair and recorded in `paired_timing_v1.json`: pairs 0 and 1
reported system daemons above the 50% threshold (Palo Alto `pmd` endpoint
security ~93%, Spotlight `mds_stores` ~86%); pair 2 was fully clean. No local
builds/tests/profilers ran alongside. Timings were consistent across the
contended and clean pairs (H=1 spread 1.6 s, H=4 spread 1.0 s), so no run was
discarded; the contention is preserved here and in the JSON.

## Baseline claim status

This dense256 L2 measurement is the **v6 primary baseline reference** for
development comparisons at the same tier (same scene, same child isolation,
same declared cache/JIT state, math profile and fingerprint above). Per
`SCOPE_CORRECTION.md` in this directory, the v5 record's 598.9 s covers two
1024² scenes and does NOT satisfy the v6 final target (24 spatial tiles x 24
timesteps, patches=153, shape [1024,1024], <=1800 s). Nothing here is final-
target evidence; no 1024 run was performed in this task.
