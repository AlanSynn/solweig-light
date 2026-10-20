# Full compute optimization — round 1

## Result and scope

Three controlled pairs on the same interpreter and host completed the full public own-met CPU workflow. Median workflow time fell from **91.936602 s to 31.870904 s** (**65.3338% less wall time; 2.8847×**). This result describes the generated diagnostic scene below. It is not a measurement of the user’s original dataset or server.

The workload was an explicitly **synthetic 600 × 600 city grid at 4.0 m/pixel**, with 400 varied buildings, 1,500 planted canopies, asphalt/grass/roof landcover, and the shipped reference’s 19 actual hourly forcing rows from 04:00 through 22:00 on 2020-07-18. It used eight threads, one logical tile with overlap 0, a fixed 4,096 MiB runtime admission budget, option 2 with all 153 sky patches, TMRT and UTCI saving, all default legacy geometry exports, and checkpoint interval 1. Every measured trial started a fresh scene and geometry cache; only its variant’s private Numba cache was warmed.

The original user report concerned verified 600 × 600 rasters at **3.99 m/pixel and 16 threads**: 76.1 s total, 0.04 s preprocessing, 1.00 s walls, 28.36 s SVF, 46.67 s thermal, 182 s CPU, and 0.5 GB RSS. The historical GPU figure was 123.0 s. Those original inputs/server and `02_CPU_SpeedTest.py` were unavailable here. No ratio against those historical figures is computed.

## Source pins and protocol

- Reference commit: `288d70e2b3bd8ca5bba4b65e572048fea37bcc51`.
- Candidate commit during every numerical run: `80441eadbacb3097e1fb3af5ab8452142e43968c`.
- Reference numerical source-tree SHA-256: `ad87e9f1d24441c1be91971408108dbd4c912ba2891f4c621a40658a1ae1da20`.
- Candidate numerical source-tree SHA-256: `9c2a3bb0f35bdb031a0e968ed6fa8fc83bed60080526c0174c3d31547a06789e`.
- Both source identities were clean at the initial controlled start. Numerical source trees and both HEADs remained unchanged throughout. The checker amendment introduced only the documented tool/test diff; continued runs explicitly record that diff rather than claim an unchanged harness.
- Separate full first-use runs with empty private Numba caches were excluded: reference 113.453197 s; candidate 64.354807 s. Their complete outputs passed finite-value, size, band, visibility and checkpoint checks. Existing checkout-native build caches and OS file caches were not purged.
- Trial order: reference → candidate, candidate → reference, reference → candidate. The extra profiled candidate run was excluded from all performance medians.

## Measured trials

| Trial | Order | Reference workflow (s) | Candidate workflow (s) | Reference CPU (s) | Candidate CPU (s) |
|---|---|---:|---:|---:|---:|
| 0 | reference → candidate | 91.936601913001 | 31.870903829000 | 538.451122 | 131.713829 |
| 1 | candidate → reference | 93.409312311000 | 33.180139920001 | 543.994999 | 132.426798 |
| 2 | reference → candidate | 91.539879914002 | 31.176622946001 | 516.648626 | 130.521819 |

| Median stage / resource | Reference | Candidate |
|---|---:|---:|
| Preprocessing (s) | 0.033804090 | 0.032938099 |
| Walls (s) | 0.368756093 | 0.342988603 |
| SVF including legacy exports (s) | 23.330534433 | 13.945074689 |
| Thermal / UTCI including checkpoints (s) | 68.843722175 | 17.248277105 |
| Full workflow (s) | 91.936602 | 31.870904 |
| Self + waited-child user/system CPU (s) | 538.451122 | 131.713829 |
| Parent RSS high-water mark (bytes) | 575,410,176 | 367,108,096 |
| Child RSS high-water mark (bytes) | 575,410,176 | 515,428,352 |

Stage medians are computed independently and therefore need not sum to the median full workflow. CPU is the resource-counter delta across the workflow, including waited child processes. RSS entries are separate process high-water marks, **not a simultaneous total process-tree sum**. `/proc` was unavailable, so psutil process-tree sampling was explicitly unavailable; no tree-peak RSS claim is made.

## Numerical and artifact checks

All three pairs passed **31 public artifact comparisons: 27 produced artifacts/arrays plus four copied source rasters**. Every compared value was bitwise identical, including finite signed-zero bits and NaN payloads; the maximum finite absolute error was **0.0**. Metadata, geotransforms, projection, dtype, band descriptions/timestamps, nodata and validity masks matched. All 15 SVF fields and all three float32 `(600, 600, 153)` visibility channels were retained.

All **11 final chronological state fields** matched, including bitwise equality of the state array payloads, expected 19-step cursors and timestamps. Frozen gates remained TMRT 0.01, UTCI 0.02 and geometry 1e-6; no tolerance was weakened. TMRT contained 6,840,000 finite values and no NaNs. UTCI contained 5,335,181 finite values and 1,504,819 NaNs, with identical masks in both variants; neither output was entirely nonfinite and neither contained infinities.

## Extra profile: interpretation only

The extra candidate profile completed in 32.841007 s and is not a performance sample. The following cumulative times describe that profiled run, independently of the timed medians above. Nested cumulative values overlap and must not be summed.

| Profile | Function / component | Calls | Cumulative (s) | Self (s) |
|---|---|---:|---:|---:|
| svf | `api.py:_calculate_svf` | 1 | 15.630368 | 0.000092 |
| svf | `service.py:_export` | 1 | 10.058018 | 0.000163 |
| svf | `visibility.py:export_visibility_npz` | 1 | 7.879377 | 0.378180 |
| svf | `~:<method 'compress' of 'zlib.Compress' objects>` | 3,346 | 5.133456 | 5.133456 |
| svf | `visibility_native.py:decode_pixels` | 106,947 | 2.578552 | 0.134665 |
| svf | `visibility.py:decode_pixels` | 106,947 | 2.419293 | 1.741126 |
| svf | `visibility.py:append` | 459 | 2.250471 | 2.195923 |
| tile | `pipeline.py:_run_tile` | 1 | 15.485728 | 0.035139 |
| tile | `engine.py:Solweig_2022a_calc` | 19 | 12.640989 | 0.022812 |
| tile | `lw_batch.py:execute` | 19 | 4.220890 | 4.178324 |
| tile | `gvf_batch.py:run` | 14 | 3.316990 | 3.002108 |
| tile | `sw_batch.py:execute` | 14 | 3.199124 | 3.171313 |

The SVF profile identifies legacy visibility export as the principal remaining geometry cost: 106,947 Python decode calls consume about 2.58 s cumulatively, while zlib compression consumes about 5.13 s. The separate tile profile attributes about 4.22 s to the batched longwave execution, 3.32 s to prepared GVF execution and 3.20 s to batched shortwave execution. These observations support a narrowly measured export-decoder follow-up; they do not establish its future gain.

## Checker amendment and evidence integrity

The first local attempt used automatic memory budgets: warmups completed, but measured runs were rejected by conservative admission after available-memory-based budgets changed. That failed attempt is preserved separately at `full_compute_round1`. The controlled run above used the same explicit 4 GiB budget in both variants.

The controlled run initially stopped after valid pair 0 because the checker traversed a private dot-prefixed `.geometry-export-*` staging path with a random name. This was a checker-only false failure. The amendment excludes dot-prefixed relative path components, retains all public TIFFs, checks ZIP/NPZ sets symmetrically and preserves detection of unexpected public extras. Four regression cases cover that distinction.

`comparison.json` remains the original failed report. `comparison-checker-amendment.json` records the corrected 31-artifact/state result without rerunning or changing pair 0. `continuation-comparison.json` retains both original warmups and pair 0, then adds only the remaining two fresh-scene pairs and the extra profile. It records both old/new harness hashes, `harness_unchanged=False`, a saved tool-only patch, the continuation driver, unchanged ASTs of the timed instrumentation functions, and unchanged numerical source trees/HEADs before and after continuation.

- Original harness SHA-256: `3922cb84fa8ee5986f0ea17323cc2a90e3a2d1634e5654e51f0a40e4c5b73179`.
- Corrected/continuation harness SHA-256: `b8dfa3b76ff692d262f6238d1286ec9f9b530e52643a5e0c65db1c52e5fab6c9`.
- Continuation driver SHA-256: `c02ad4c1d8533bffc17c646c6d58187d310e7c63f0c5ed728dfef392be114995`.
- Tool-only patch SHA-256: `ff0abf5265913c46e119f5b52e7d9deeed329e7e6b4b4d498900da584212f611`.

## Input hashes

| File | SHA-256 |
|---|---|
| `Building_DSM.tif` | `2cd6dac82db33f864d42e5407aa1c8d0cfd471462ba107bfa9286273fa63c5e9` |
| `DEM.tif` | `40bf20aa2ea22652ff963f6200c3c47b947c55dd580e9eae1ac6433069592801` |
| `Landcover.tif` | `9da146f2d1342216798bfd0ccf99d885654a24aae74a437bc85a0084025f5cd6` |
| `Trees.tif` | `32bfdb1ec8f13719b2fb610a97dc067fd3a8d28ba0028bebd7d0d1e621235496` |
| Selected `met.txt` | `ceb3173fab0439e98e7008c699474bedb70fded57ecbd65356d89148de7c73a0` |
| `synthetic_manifest.json` | `9c21351bc5c62c24e2282e65487cb5a96e7ad83270d70c42a1a1d52bd9901d20` |

## Raw evidence and report hashes

**Current availability:** the completed raw directories and prepared ZIP are
no longer present in the active workspace after the task resumed. The paths
and hashes below record the completed experiment's original locations and
identities. [EVIDENCE.md](EVIDENCE.md) distinguishes the preserved summaries
from the currently unavailable bulk evidence.

Raw artifacts are outside git at `/workspace/scratch/2c9f54f632af/full_compute_round1_fixed_budget`. The source scene and generator manifest are at `/workspace/scratch/2c9f54f632af/synthetic_full_600`.

Selected raw reports, profiles, failures and actual generated inputs are packed
in `full_compute_evidence_core_20261020.zip` (SHA-256
`2847e88a5a3743e17e59b504bb93f98adaa721cf020e8de8709ffec2efb76e7f`).
[EVIDENCE.md](EVIDENCE.md) records its exact scope and delivery status. Durable
upload was blocked by automatic approval review; no remote archive closure is
claimed. Round-1 repeated bulk raster/checkpoint outputs remain outside the
selected transfer archives and in the original local run directories.

| Evidence file | SHA-256 |
|---|---|
| `comparison.json` | `241016322447dccbb9464ffce18da803f00af03b9001f76e5913c9ef1b280f2b` |
| `comparison-checker-amendment.json` | `80e2a4e48b73e88dc4857bd3ee47ff512c679b7b4aeeee330bf0c1b54217fa2b` |
| `continuation-comparison.json` | `57ef469e48bbd65a82cba8b8bb518618330d9954a57e60cab395aba0b97997d6` |
| `round1-summary.json` | `5fa4c9992faceeb9789275ee07ba1fed6323fd697f9d2235da88d902a5b0faa1` |
| `profile-svf-top.txt` | `3762e0f9eb2b312727256d6f1c3e0909e21f03f324d1196a2c8c9209b96b4098` |
| `profile-tile-top.txt` | `59df404955336a9665985411d6d432c537d520de07f0397cda0615dffef67eae` |

The `.pstats` files and per-trial stdout/stderr, complete outputs and final checkpoints remain in the raw directory. The standalone reusable protocol is documented in `development/docs/full_compute_benchmark.md`.
