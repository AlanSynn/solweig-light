# Reproducible full compute comparison

`development/tools/full_compute_benchmark.py` compares two local checkouts with the **same Python interpreter on the same server**. It executes the public `thermal_comfort` own-met CPU workflow, including preprocessing, walls, complete option-2 SVF, default legacy SVF exports, all meteorological steps, TMRT and UTCI saving, and checkpoint interval 1. It uses one logical tile at the requested raster size and overlap 0. It neither reduces model work nor substitutes a synthetic scene for the user's rasters.

The original four 600 × 600 rasters, own-met file, and `02_CPU_SpeedTest.py` are not included here. The harness does not claim to reproduce that dataset until those actual inputs are supplied. Historical numbers may be preserved literally with `--reported-note`; they are not used to compute a ratio against a different server or environment.

## Run on the original server

Use an interpreter with the package dependencies installed. `psutil` is optional but recommended to record sampled total process-tree RSS; resource-based self/child CPU and individual high-water RSS are recorded regardless.

```bash
/path/to/environment/bin/python development/tools/full_compute_benchmark.py \
  --reference-checkout /path/to/main-checkout \
  --candidate-checkout /path/to/candidate-checkout \
  --scene /path/to/original-600-inputs \
  --met-file /path/to/original-600-inputs/met.txt \
  --date YYYY-MM-DD \
  --threads 8 \
  --repeats 3 \
  --expected-size 600 \
  --expected-steps 19 \
  --workdir /path/to/evidence/full-compute-600-new-run
```

The work directory must not exist. Keep it outside the checkouts. The harness copies only the four named input rasters and staged meteorological rows into each isolated trial directory. It does not modify the originals or import pre-existing processed inputs, geometry caches, transactions or outputs. Source checkouts may acquire normal Python/Numba/native build cache files; they are not cleaned or reset.

Default raster names are `Building_DSM.tif`, `DEM.tif`, `Trees.tif` and `Landcover.tif`; lookup is case insensitive. Override a different basename with `--building-name`, `--dem-name`, `--trees-name` or `--landcover-name`. All four inputs must be single-band, have exactly the requested square dimensions, and share their geotransform and projection. There is no resampling or resizing.

`--met-file` can be omitted only when the scene root contains exactly one `.txt` or `.met` file. It must contain a header followed by at least two numeric rows with at least 24 columns. Dates come from the first four columns: year, day of year, hour and minute. If `--date` is omitted, the selected date is derived from the first retained meteorological row and recorded explicitly in the report. The date controls the public driver's selected-date argument; it does not silently discard other meteorological rows.

`--start-time` and `--end-time` optionally select rows **inclusively** before execution. They accept an ISO datetime or `HH:MM`; a clock-only value uses `--date`, or the first source row's date when no date is supplied. This staging filter is explicit because the public own-met path does not itself filter rows using those arguments. Original row text and ordering are retained, and the selected file has its own SHA-256. The harness requires the retained timestamps to increase strictly and their count to equal `--expected-steps`. It fails rather than silently benchmarking fewer than 19 steps.

## Timing protocol

Each checkout receives its own initially empty private Numba cache. First, each runs the complete workflow once in a separate fresh scene. These **first-use** runs are reported separately and excluded from the measured medians. Their process timing includes interpreter startup, imports and first-use compilation; workflow timing starts after package import. Existing checkout-local native compiler caches and operating-system file caches are not purged, so “first use” specifically describes the private Numba cache rather than an entirely cold machine.

Then each measured trial starts another process and a fresh scene with an empty geometry cache, while reusing only its checkout's private warmed Numba cache. Every trial still runs every meteorological step and produces the full requested outputs and legacy geometry exports. Trial 0 runs reference then candidate; trial 1 runs candidate then reference; this order alternates thereafter. Three repetitions per checkout are the default. The report uses the median full-workflow wall time from successful measured trials.

All invocations use `sys.executable`. `PYTHONPATH` begins with the chosen checkout's `src`, followed by an owned instrumentation-hook directory; inherited Python paths are excluded. The child checks that the imported package belongs to that checkout. Thread variables are set before interpreter startup, propagated to runtime workers, and recorded again from each process. Runtime workers are fixed at 1, with both CPU budget and threads per worker equal to `--threads`. The runtime's own admission limits still apply; requesting more CPUs than the server permits is an error. GDAL's block cache cap is fixed to 256 MiB for both variants.

An owned `sitecustomize` hook wraps API stages without editing either checkout: preprocessing, walls, SVF and TMRT/UTCI. It also instruments worker tile execution. The reports distinguish full-workflow timing from whole-process timing, and include stage wall times, per-process startup environments, self/child user and system CPU usage, and RSS observations. The stage wrappers record a small JSON event after each stage; this identical instrumentation overhead is included in both variants.

With `psutil`, total process-tree RSS is sampled every 50 ms. This is an observed peak, not an exact allocation bound; short-lived peaks can be missed and shared pages are counted in each process's RSS. Without `psutil`, the sampled tree peak is explicitly null. `resource.getrusage` still records parent and child high-water RSS, which is not a simultaneous process-tree sum.

## Correctness and provenance

For each checkout the JSON records the commit, tracked dirty-diff SHA-256, untracked file hashes and a source-tree content hash. It checks source identities again after execution and rejects a source change during the benchmark. Input raster hashes, raster schemas, original met hash, selected met hash and timestamps are retained. Do not edit either checkout while a benchmark is running.

Reference and candidate outputs are compared after every measured pair. Raster comparisons operate in 128 × 128 windows and require matching dimensions, band counts, projection, geotransform, global and band metadata, descriptions, nodata semantics and masks. Every saved output must have the expected band count. Final transaction cursors must have the expected number of steps; checkpoint manifests and arrays are hash checked, state fields are compared, and final timestamps must match.

Frozen absolute tolerances are:

| Family | Absolute tolerance |
|---|---:|
| TMRT | 0.01 |
| UTCI | 0.02 |
| Geometry fields | 1e-6 |
| Visibility channels | Exact values |
| Final chronological state | Exact values |

Reports separately expose finite maximum absolute error, special-value mask equality, finite bitwise equality, equality of all bits and NaN payload equality. A signed-zero or NaN-payload difference is not conflated with a value-tolerance failure. Special-value masks must always agree. State scalar/container types and scalar encodings must agree.

The fifteen SVF rasters inside ZIP files are read through GDAL's `/vsizip/`. Visibility NPZ entries are streamed to temporary NPY files and compared with memory mapping, avoiding simultaneous dense visibility cubes in RAM. Those comparison scratch files are removed afterwards; the original exported artifacts remain available in each trial scene.

Public artifact discovery excludes dot-prefixed private staging/cache paths.
It still compares all public TIFFs and checks the ZIP/NPZ name sets in both
directions, so an unexpected public extra fails the comparison. Compressed
ZIP bytes may differ when a storage compression setting changes; the decoded
arrays, headers, metadata and integrity requirements above still apply.

## Results and optional profiling

The work directory contains:

- `comparison.json`: complete configuration, provenance, all trials, stage events, dependency versions, resource measurements, output schemas, state inventory and paired comparison metrics.
- `comparison.md`: a readable result table, measured medians and same-host relative wall-time change.
- `first_use-*`: complete warmup scenes and logs, reported separately.
- `measured-*`: complete fresh scenes, logs, checkpoint states and per-run result JSON.
- `jit-reference` and `jit-candidate`: isolated Numba caches reused only within their corresponding variant.

Pass `--profile` for one additional candidate run with `cProfile` coverage of the complete SVF API stage and actual worker tile computation. Files are saved as `profile-svf-PID-*.pstats` and `profile-tile-PID-*.pstats` under that run's `events` directory. This run is labeled **profiled** and excluded from performance medians. The SVF profile includes geometry construction and legacy export; the tile profile covers thermal computation rather than only scheduler waiting. It is not a performance sample.

Generated inputs should be supplied as a separate explicitly identified scene with `--dataset-label synthetic_generated`. The harness does not generate, relabel or imply possession of the original dataset. A synthetic result establishes behavior only for that generated case.

The tool exits nonzero when a workflow, completeness check, source-stability check or paired numerical comparison fails. Inspect `stderr.log`, `child-result.json`, stage events and `comparison.json` rather than discarding a failed trial. Keep bulky raw evidence outside git; commit the harness and protocol, not benchmark scenes or caches.

## Original user figures (historical report only)

The user reported the following results on the original, currently inaccessible server. These figures have not been rerun or independently verified here. They must not be divided by timings collected on another machine.

| Reported item | User-reported value |
|---|---:|
| Lite full wall time (revision not identified in the report) | 76.1 s |
| Preprocessing | 0.04 s |
| Walls | 1.00 s |
| SVF | 28.36 s |
| Thermal calculation | 46.67 s |
| CPU time | 182 s |
| RSS | 0.5 GB |
| Threads | 16 |
| Meteorological steps | 19 |
| Raster size / pixel size | 600 × 600 / 3.99 m |
| Historical SOLWEIG-GPU package wall time (CPU execution) | 123.0 s |

The local harness validates actual raster dimensions and retained meteorological rows instead of deriving its workload from those historical figures. Only the two checkout measurements obtained by the same harness on the same server support its reported relative wall-time change.

## Deterministic synthetic full-compute scene

For a separately labeled diagnostic workload, the accompanying generator creates a 600 × 600 analytic city grid at 4 metre resolution. It uses the shipped small reference scene only for its projected origin/CRS and the actual meteorological rows from 04:00 through 22:00; it does not upscale that scene's buildings or claim to recreate Atlanta. The generated DSM is terrain plus varied 8–55 metre buildings. Grass, asphalt and roofs have explicit model landcover codes. Tree canopy peaks are 4–15 metres, with tapered edges and no overlap with building DSM footprints.

```bash
/path/to/environment/bin/python development/tools/generate_full_compute_scene.py \
  --output /path/to/evidence/synthetic-full-600 \
  --size 600 --pixel-size 4 --seed 20261020
```

The output directory must be new. `synthetic_manifest.json` records the generator hash, seed, dimensions, pixel size, source projection/origin, source forcing hash, selected forcing hash, selected year/day/hour/minute values, raster hashes and scene counts. Pass this scene to the benchmark with `--dataset-label synthetic_generated`. All timings and profiles from it describe the generated diagnostic workload only.

The benchmark now also checks finite output counts and stops before measured trials if either first-use workflow or its completeness checks fail. An entirely nonfinite TMRT or UTCI output is rejected. Process-tree RSS sampling may be unavailable even when `psutil` is installed, for example when the host does not expose `/proc`; that condition is recorded explicitly, while resource-based parent/child CPU and high-water RSS remain available.

### Fixed memory admission budget

`--memory-budget-mib` defaults to **4096 MiB**, passed as the same explicit `RuntimeOptions.memory_budget_bytes` to every process and both checkouts. This prevents the runtime's automatic free-memory-based budget from changing between first-use and measured trials as system headroom changes. The benchmark's environment snapshots also record physical memory, available host memory and any exposed container memory limit when those probes are supported.

Choose a fixed budget that both covers the model's conservative admission estimate and fits the server's real headroom. An explicit budget does not allocate that amount of RAM or make an oversized workload safe. The runtime's existing admission calculations remain intact. If admission fails, the harness stops before launching subsequent runs; it does not shrink tiles, skip timesteps, change GDAL limits between variants or weaken a numerical gate.

The first local synthetic round exposed this distinction: both first-use workflows completed, but later runs were rejected before thermal calculation when their automatic budgets fell below the conservative simulation estimate. Those failed runs remain separate evidence, and no performance ratio is derived from them. A new controlled round uses the same explicit 4096 MiB budget for both variants, with fresh first-use caches and complete source provenance.
