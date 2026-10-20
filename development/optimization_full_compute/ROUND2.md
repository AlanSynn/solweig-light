# Full compute round 2: final candidate versus main

The final candidate completed the full public CPU workflow in a median
**23.965122 s**, versus **91.267964 s** for main on the same local server:
**73.7420% less wall time**, or a **3.80837× speedup** for this sequential
full-workflow workload.
All three measured pairs produced bitwise-identical decoded arrays and exact
final chronological state. The source and harness stability guards passed.

These measurements use the explicitly generated **600 × 600, 4 m/pixel,
8-thread** diagnostic scene. The user's original Atlanta inputs and benchmark
script are unavailable here. The original report concerned **3.99 m/pixel and
16 threads**; its reported 76.1 s must not be compared with these local timings.

## Pins and workload

| Item | Value |
|---|---|
| Reference | `288d70e2b3bd8ca5bba4b65e572048fea37bcc51` |
| Candidate | `afa54cb3041e9481ad6691b4c71c1e5ec0362d5a` |
| Dataset label | `synthetic_generated` |
| Inputs | Deterministic analytic city grid, seed 20261020; four matching single-band 600 × 600 rasters |
| Resolution / CRS | 4 m; EPSG:32618; origin (583000, 4507000) |
| Forcing | 19 original shipped rows, 2020-07-18 04:00 through 22:00 inclusive |
| Geometry | Option 2; 153 patches; all three visibility channels |
| Public calculation | Own meteorology, CPU, landcover, one 600-pixel tile, overlap 0, TMRT and UTCI saved |
| Persistence / exports | Checkpoint interval 1; fresh geometry cache for every trial; complete default legacy SVF exports |
| Runtime | 8 threads; one worker; CPU budget 8; fixed 4096 MiB admission budget; GDAL cache 256 MiB |
| Repetitions | Two separate first-use runs, three alternating measured pairs, one extra candidate profile |

Both checkouts were tracked-clean at the start. No checkout edits, tests,
archiving or competing benchmark jobs ran during the exclusive measurement
window. The private reference and candidate Numba caches started empty. The
first-use runs warmed only their own cache; measured trials reused that JIT
cache while starting with fresh scene copies and cold geometry. Native build
and operating-system caches were not purged.

The environment was Python 3.12.14, NumPy 2.4.6, Numba 0.67.0, llvmlite 0.49.0,
SciPy 1.17.1 and GDAL 3.13.3. The process saw nine affinity CPUs, requested and
reported eight Numba threads, and had all BLAS/OpenMP thread caps fixed to eight.
The complete environment snapshots are in `comparison.json`.

## Measured wall time

| Pair | Execution order | Main (s) | Candidate (s) | Correctness |
|---|---|---:|---:|---|
| 0 | Main, candidate | 91.267964469 | 24.496363969 | Passed |
| 1 | Candidate, main | 91.124813863 | 23.753016733 | Passed |
| 2 | Main, candidate | 94.418598416 | 23.965121620 | Passed |
| **Median** | | **91.267964469** | **23.965121620** | All pairs passed |
| Range | | 91.124813863–94.418598416 | 23.753016733–24.496363969 | |

Stage wall times include production and legacy exports in the SVF stage.
TMRT/UTCI includes the complete chronological thermal work, saved outputs and
checkpoints. Stage medians are calculated independently and should not be added
to reconstruct the median workflow sample.

| Stage | Main median (s) | Main range (s) | Candidate median (s) | Candidate range (s) |
|---|---:|---:|---:|---:|
| Preprocessing | 0.033029 | 0.028393–0.050930 | 0.032335 | 0.029452–0.033117 |
| Walls | 0.386702 | 0.340611–0.405750 | 0.340311 | 0.325330–0.347636 |
| Complete SVF | 24.183081 | 22.551562–24.540555 | 7.037012 | 6.954694–7.164612 |
| TMRT/UTCI | 68.157562 | 66.710468–69.420420 | 16.655007 | 16.214954–17.077567 |

### First use and profiling are separate

| Additional run | Workflow wall (s) | Whole process wall (s) |
|---|---:|---:|
| Main first use, empty private JIT cache | 114.340642 | 116.110997 |
| Candidate first use, empty private JIT cache | 56.621304 | 58.664967 |
| Candidate extra profiled workflow | 25.461128 | Recorded in raw report |

All three additional workflows passed completeness checks. Their timings are
excluded from the measured medians above. Workflow timing begins after package
import; whole-process timing includes interpreter startup and imports.

## CPU and memory

CPU is the delta of self plus waited-child user and system CPU, measured around
the public workflow. It is not wall time and can exceed wall time under parallel
execution.

| Pair | Main CPU (s) | Candidate CPU (s) |
|---|---:|---:|
| 0 | 516.834540 | 113.339254 |
| 1 | 530.353268 | 111.803583 |
| 2 | 537.350469 | 112.434316 |
| **Median** | **530.353268** | **112.434316** |

The host does not expose the process information needed by the psutil sampler.
Sampled process-tree RSS is therefore explicitly unavailable. The following
`resource.getrusage` high-water values are reported separately. These are
**lifetime process counters**, including preworkflow activity, not isolated
workflow allocation peaks. They are not simultaneous totals and must not be
summed to claim a process-tree peak.

| High-water RSS, bytes | Pair 0 | Pair 1 | Pair 2 | Median |
|---|---:|---:|---:|---:|
| Main parent | 579043328 | 575246336 | 572993536 | 575246336 |
| Main children | 579043328 | 575246336 | 572993536 | 575246336 |
| Candidate parent | 344256512 | 534970368 | 535375872 | 534970368 |
| Candidate children | 515555328 | 512483328 | 512389120 | 512483328 |

The parent counters before and after the workflow show the limitation directly:

| Parent high-water RSS, bytes | Before workflow | After workflow |
|---|---:|---:|
| Main pair 0 | 249896960 | 579043328 |
| Main pair 1 | 534970368 | 575246336 |
| Main pair 2 | 535375872 | 572993536 |
| Candidate pair 0 | 249610240 | 344256512 |
| Candidate pair 1 | 534970368 | 534970368 |
| Candidate pair 2 | 535375872 | 535375872 |

In candidate pairs 1 and 2 the parent lifetime high-water was already equal to
its final value before the workflow started. No cause is inferred from these
counters, and neither a total-memory winner nor a memory change against round 1
is established by this experiment.

The explicit 4096 MiB runtime budget is an admission setting, not an observed
allocation. The same fixed setting was used for both variants and every run.

## Numerical and artifact proof

Every measured pair passed all of these checks:

- **31 compared decoded artifacts:** four copied inputs plus 27 produced
  arrays. The produced set includes the saved 19-band TMRT and UTCI rasters,
  prepared rasters, all fifteen legacy ZIP SVF rasters and all three full
  153-patch visibility NPZ arrays.
- All finite values and all bits match; maximum finite absolute error is
  **0.0**. Special-value masks and NaN payloads match. The frozen gates remain
  TMRT 0.01, UTCI 0.02, geometry 1e-6 and exact visibility/state.
- Raster dimensions, bands, dtypes, projection, geotransform, nodata semantics,
  metadata, timestamps and validity masks match. Both output rasters contain
  exactly nineteen bands with the expected 04:00–22:00 timestamps.
- All **eleven final chronological state fields** agree: `CI`, `TgOut1`,
  `Tgmap1`, `Tgmap1E`, `Tgmap1N`, `Tgmap1S`, `Tgmap1W`, `Twater`,
  `timestepdec`, `firstdaytime` and `timeadd`. The nine numeric arrays/scalars
  match bitwise, and the two integer fields match in type and value. State
  schema, checkpoint integrity, final cursor and timestamps also pass.

Each output TMRT stack has 6,840,000 finite values and no NaNs. Each UTCI stack
has 5,335,181 finite values and 1,504,819 NaNs, identically in both variants.
The nonfinite roof values are retained; no all-NaN result is being accepted.

Compressed NPZ bytes intentionally differ because the candidate uses the
measured level-3 storage compression setting. Decoded array bytes remain exact.
Sizes below are identical across the three measured repetitions of each variant.
The fifteen physical public files include the four source rasters; archive
members expand to the 31 compared artifacts above.

| Public artifact | Main bytes | Candidate bytes |
|---|---:|---:|
| Four source input TIFFs together | 5766880 | 5766880 |
| `shadowmats_0_0.npz` | 10212358 | 16835741 |
| `svfs_0_0.zip` | 6514913 | 6514913 |
| `TMRT_0_0.tif` | 27453833 | 27453833 |
| `UTCI_0_0.tif` | 27453833 | 27453833 |
| All produced public files | 81726497 | 88349880 |
| All public files, including copied inputs | 87493377 | 94116760 |

The raw summary contains every individual prepared TIFF size. Native caches,
private staging files and chronological checkpoints are outside this public
artifact size total; their evidence remains in each trial directory.

## Extra profile: remaining costs

The extra candidate workflow took 25.461128 s with profiling enabled. Its SVF
API profile and worker tile profile cover different parts of that same run.
These are **profile observations**, not the unprofiled stage medians. Cumulative
rows include their callees, overlap hierarchically and must not be summed.

| SVF profile function | Calls | Cumulative (s) | Self (s) |
|---|---:|---:|---:|
| Complete SVF API stage | 1 | 7.854275 | 0.000114 |
| Geometry export wrapper `_export` | 1 | 4.695368 | 0.000169 |
| `save_svf_zip_npz_outputs` | 1 | 3.180505 | 0.000345 |
| Compact SVF calculation | 1 | 2.974676 | 0.000047 |
| Visibility NPZ export | 1 | 2.620195 | 0.006823 |
| Shadow pixel kernel wrapper | 153 | 1.953763 | 1.836502 |
| zlib compression | 3346 | 1.850461 | 1.850461 |
| `decode_block` | 3291 | 1.576530 | 1.036958 |
| Legacy geometry comparison | 1 | 1.442651 | 0.000084 |
| Complete `VisibilityBuilder.append` | 459 | 0.253207 | 0.005481 |
| `try_encode_native_f32` | 459 | 0.244440 | 0.234511 |

| Tile profile function | Calls | Cumulative (s) | Self (s) |
|---|---:|---:|---:|
| Complete `run_tile` | 1 | 15.883127 | 0.002168 |
| `Solweig_2022a_calc` | 19 | 13.120893 | 0.033280 |
| Longwave batch `execute` | 19 | 4.443751 | 4.401563 |
| Ground-view batch `run` | 14 | 3.468432 | 3.127602 |
| Shortwave batch `execute` | 14 | 3.361285 | 3.331923 |
| Uniform UTCI calculator | 19 | 1.136957 | 1.125432 |
| Checkpoint wrapper | 19 | 0.897341 | 0.000965 |

The remaining measured costs are mainly thermal batches, ray shadows, archive
compression/decoding and required export verification. This profile is evidence
for possible future work; no additional optimization experiment is included in
the final round.

## Relationship to round 1

[ROUND1.md](ROUND1.md) records a separate earlier campaign with candidate
`80441eadbacb3097e1fb3af5ab8452142e43968c`. It used the same generated inputs,
8-thread/fixed-budget/full-export protocol and main reference. Its measured
medians were 91.936602 s for main and 31.870904 s for that candidate. Round 2
starts fresh with final candidate `afa54cb3`, new private JIT caches and three
new paired trials. Its medians are 91.267964 s and 23.965122 s.

The final candidate adds the bounded profile-driven export, encoding and cache
dependency work documented in the implementation. These campaigns establish
whole-workflow results for their respective source pins. Subtracting their
times does not isolate the contribution of any one change, and overlapping
profile rows are not additive attribution measurements. Round 2 needs no
checker amendment or continuation: the complete harness exited successfully
with unchanged source and harness checks.

## Reproduction and evidence

Exact invocation from `/workspace/scratch/2c9f54f632af`:

```bash
/workspace/scratch/2c9f54f632af/.venv-solweig/bin/python \
  /workspace/scratch/2c9f54f632af/solweig-light-impl/development/tools/full_compute_benchmark.py \
  --reference-checkout /workspace/scratch/2c9f54f632af/solweig-light-main \
  --candidate-checkout /workspace/scratch/2c9f54f632af/solweig-light-impl \
  --scene /workspace/scratch/2c9f54f632af/synthetic_full_600 \
  --date 2020-07-18 --threads 8 --memory-budget-mib 4096 \
  --repeats 3 --expected-size 600 --expected-steps 19 \
  --dataset-label synthetic_generated --profile \
  --workdir /workspace/scratch/2c9f54f632af/full_compute_round2
```

Raw evidence root: `/workspace/scratch/2c9f54f632af/full_compute_round2`.
The parent log is `/workspace/scratch/2c9f54f632af/full_compute_round2.log`.
Key files are `comparison.json`, `comparison.md`, `round2-summary.json`,
`round2-summary.txt`, `profile-svf-top.txt` and `profile-tile-top.txt`. Complete
scenes, logs, invocation specs, result/inventory JSON, stage events and final
states are retained under all nine trial directories. Both original pstats
files are under `profiled-00-candidate/events/`.

| Provenance item | SHA-256 |
|---|---|
| Main numerical source tree | `ad87e9f1d24441c1be91971408108dbd4c912ba2891f4c621a40658a1ae1da20` |
| Candidate numerical source tree | `39bb2dbdc29600b14b106242677370937bf552618d1d6cd6f8d70293351d53b6` |
| Harness | `b8dfa3b76ff692d262f6238d1286ec9f9b530e52643a5e0c65db1c52e5fab6c9` |
| Final `comparison.json` | `273da534cab7c8ba32b6a2d66925d963d661537a2414a7d262faa441aa67eafc` |
| Building DSM input | `2cd6dac82db33f864d42e5407aa1c8d0cfd471462ba107bfa9286273fa63c5e9` |
| DEM input | `40bf20aa2ea22652ff963f6200c3c47b947c55dd580e9eae1ac6433069592801` |
| Trees input | `32bfdb1ec8f13719b2fb610a97dc067fd3a8d28ba0028bebd7d0d1e621235496` |
| Landcover input | `9da146f2d1342216798bfd0ccf99d885654a24aae74a437bc85a0084025f5cd6` |
| Source and selected forcing | `ceb3173fab0439e98e7008c699474bedb70fded57ecbd65356d89148de7c73a0` |

Both source dirty-diff hashes were the empty-content SHA-256; both source
identities remained unchanged at the end. The harness hash also remained
unchanged. Full file-level source hashes are retained in the JSON report.

### Transfer archive

[EVIDENCE.md](EVIDENCE.md) records five verified ZIP filenames, exact sizes,
SHA-256 values, selected contents and exclusions. The core archive contains
all final reports/profiles and the actual generated input scene. Four further
ZIPs contain the first measured reference/candidate pair's complete selected
SVF/TMRT/UTCI outputs and final checkpoints. Repeated bulk outputs and native
caches remain outside those archives. Durable upload was rejected by automatic
approval review pending explicit authorization; the local ZIPs are prepared,
but no remote archival closure is claimed. No raw evidence is committed to git.
