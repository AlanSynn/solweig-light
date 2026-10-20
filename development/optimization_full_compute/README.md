# Full-computation optimization

Implementation: [PR #2](https://github.com/AlanSynn/solweig-light/pull/2).
Measured reference: `288d70e2`; numerical candidate: `afa54cb3`.
Later documentation edits do not change the measured numerical source.

## Result and scope

Three alternating pairs on one host used a **generated 600 × 600, 4 m**
scene, 19 chronological steps, 153 patches and eight threads. Each run used
fresh geometry and outputs, warmed private JIT caches, every default legacy
SVF export, TMRT/UTCI saving and checkpoint interval 1. The fixed 4096 MiB
setting was an admission budget, not observed memory consumption.

| Median / artifact size | Main | Candidate |
|---|---:|---:|
| Full workflow | 91.268 s | 23.965 s |
| Observed workflow range | 91.125–94.419 s | 23.753–24.496 s |
| Whole process, including startup/imports | 92.479 s | 25.223 s |
| Self + waited-child CPU | 530.353 s | 112.434 s |
| SVF including legacy exports | 24.183 s | 7.037 s |
| TMRT/UTCI including output/checkpoints | 68.158 s | 16.655 s |
| Visibility NPZ | 10,212,358 bytes | 16,835,741 bytes |

This is a **3.808× workflow speedup, 73.742% less elapsed time**. Independent
stage medians do not sum to the median total; ranges are not confidence
intervals. First-use runs (114.341 / 56.621 s) and the extra profile are
excluded. Process-tree peak RSS was unavailable, so no memory winner is
claimed. The earlier candidate took 31.871 s; its profile selected the
export/codec follow-up. Separate campaigns do not isolate individual gains.

All three pairs matched bitwise across four copied inputs plus 27 produced
raster/member entries, all 19 output bands and eleven final state fields.
Maximum finite error was zero; signed zeros and NaN payloads matched. UTCI
retained 1,504,819 NaNs among 6,840,000 samples; TMRT was entirely finite.

## Changes

- Compile ordered SVF accumulation and bounded LW/SW/GVF schedules; keep
  original rays, patch/direction order, dtypes and defensive fallback paths.
- Reuse owned immutable radiation data and ordered engine subexpressions.
- Decode/export visibility in bounded compiled blocks and encode native
  float32 planes through exact integer bits.
- Combine compatible validation passes, borrow mapped descriptors, reduce
  copies and stream checkpoint serialization/hashing. Preserve independent
  readback, CRC, mutation guards, locking, rollback and chronological state.
- Account explicitly for additional buffers and bind composed JIT caches to
  reviewed helper-source identities.
- Use lossless NPZ DEFLATE level 3. The complete export-family median was
  7.16 → 3.76 s with larger files. Existing valid exports are not recompressed.

No public signature, resolution, ray, patch, timestep or tolerance is reduced.
The slower serial GVF batch was rejected; small wall arrays keep serial routing.

## Validation and open gates

Final focused encoder/export/service/native/cache selection: 459 passed.
Eight numerical source-upgrade cases passed in two invocations. The installed
wheel matched all 74 candidate Python files. Its combined selection recorded
166 passes / three failures: two explicit automatic-admission failures and
one pause/event timeout of unestablished cause. The same three unchanged tests
passed separately against the same wheel. These overlapping selections are
not a single clean 169-test run or a whole-repository pass.

The existing `test_kernel_primary_matches_full_route_invariance` diagnostic
fails on both pinned main and candidate at the unchanged full-longwave NaN
payload assertion. Its assertion and tolerance remain unchanged.

**Original-data gate:** the Atlanta rasters, forcing selection and original
`02_CPU_SpeedTest.py` were unavailable. The historical 76.1 s / 16-thread result
and the 2 m scene are not measured by this comparison.

**Evidence availability:** detailed completion reports remain in PR history,
but the completed raw directories and prepared ZIPs were absent after task
resumption. Durable upload had been rejected by automatic approval review
pending explicit destination authorization. Raw evidence cannot currently be
downloaded; recovery or a separately labeled reproduction and durable save
remain open. No replacement measurements were inferred from summary numbers.

## Reproduce

Use matching dependencies for both checkouts and keep generated data outside
git. From the candidate checkout, with the project environment active:

```bash
git worktree add --detach ../solweig-main-288d70e2 288d70e2
python development/tools/generate_full_compute_scene.py --output ../synthetic600
python development/tools/full_compute_benchmark.py \
  --reference-checkout ../solweig-main-288d70e2 --candidate-checkout . \
  --scene ../synthetic600 --date 2020-07-18 --threads 8 \
  --memory-budget-mib 4096 --repeats 3 --expected-size 600 \
  --expected-steps 19 --dataset-label synthetic_generated --profile \
  --workdir ../full-compute-new-run
```

For original data, supply its scene, `--met-file` and actual date/time selection;
`--start-time` / `--end-time` filter rows inclusively. Both arms receive the
same selected rows. The runner refuses mismatched dimensions, missing steps,
source mutation, incomplete artifacts or numerical differences beyond frozen
gates. It reports first-use, measured and extra profile runs separately.
Preserve its JSON, logs, outputs and source/input identities outside git before
closing the evidence gate. The original benchmark script is needed to verify
that the selected forcing and options reproduce the user's workload.
