# Full-computation optimization

Implementation: [Draft PR #2](https://github.com/AlanSynn/solweig-light/pull/2).
Main reference: `288d70e2b3bd8ca5bba4b65e572048fea37bcc51`.
Accepted source: `af6c27625c6dd71df45d1db7581a5548255497e5`, whose complete Git
tree is identical to measured local commit `09a08a89`. Publication only
reparents that tree; subsequent documentation does not change runtime code.
Source pins, reports and archive verification are in [manifest.json](manifest.json).

## Measured result and scope

The 2026-10-20 reproduction used a **generated 600 × 600, 4 m scene**, 19
chronological steps, 153 patches, eight threads and one worker. Four balanced
blocks ran each of four arms once in every order position. Every invocation
used fresh geometry and outputs, a warmed private JIT cache, all default legacy
SVF exports, TMRT/UTCI saving, no resume and checkpoint interval 1. The 4096 MiB
setting was an admission budget, not measured memory. OS/native-build caches
were not purged. No other local benchmark/test/build overlapped measured runs.

| Four-run median / observed range | Main | Previous PR `de54d448` | Accepted source |
|---|---:|---:|---:|
| Workflow wall | 90.081 s | 23.544 s | 22.268 s |
| Workflow min–max | 87.264–96.449 s | 22.735–24.434 s | 21.632–22.922 s |
| Whole process including startup/imports | 91.197 s | 24.630 s | 23.504 s |
| Self + waited-child CPU | 524.499 s | 108.169 s | 100.619 s |
| SVF including legacy exports | 22.158 s | 6.951 s | 6.697 s |
| TMRT/UTCI including outputs/checkpoints | 67.541 s | 16.221 s | 15.188 s |
| Walls/aspect | 0.312 s | 0.329 s | 0.334 s |

Main → accepted is **4.045×**, 75.280% less workflow wall and 80.816% less CPU,
with four of four paired wall wins. Previous PR → accepted has a descriptive
5.419% median reduction but only three wins; a stable incremental workflow
improvement remains **inconclusive**. The intermediate `787cdd24` measured
22.505 s: its final 1.050% median difference also had only three wins and
remains inconclusive. Small kernel gains are not promoted to whole-workflow claims. Stage medians do not
sum to the median total; ranges are not confidence intervals. First-use and
profile runs are excluded. This campaign does not pool older measurements.

## Accepted changes

- Compile ordered SVF accumulation and bounded LW/SW/GVF schedules while
  preserving rays, patch/direction order, dtypes and defensive fallbacks.
- Reuse owned immutable radiation preparations and ordered subexpressions;
  reduce raster copies and stream checkpoint serialization/hashing.
- Use bounded compiled visibility export/encoding and exact integer bits.
  Compare legacy visibility directly against packed bits without allocating
  a second expected block; specialize binary/ternary indexing in the verifier and preserve
  unusual-layout fallback, first-error order, CRC and independent readback.
- Group identical stored float32 SW coefficient bits, preserving each patch's
  comparisons and reduction order. Hoist masked lane bounds. Keep signed-zero,
  NaN-payload, all-unique and unsupported-shape fallback behavior.
- Price grouping metadata explicitly: build scratch is `17 * patches + 8`
  bytes per worker (2,609 bytes at 153 patches). Retain existing owner reserves,
  locks, fsync, rollback, source guards and composed JIT source identities.
- Use lossless NPZ DEFLATE level 3. The canonical visibility NPZ grows from
  10,212,358 to 16,835,741 bytes; the SVF TIFF/ZIP and thermal output sizes match.
- Publish benchmark event records atomically. The same harness instruments all
  arms; this is measurement robustness, not a product speed claim.

No public signature, resolution, ray, patch, timestep or tolerance is reduced.

## Additional UTCI candidate: excluded

A separate frozen four-pair campaign tried an eleven-line production change
that selects the existing parallel UTCI evaluator only within the active
runtime thread grant. It preserved all exact gates. The measured workflow
medians were **22.834 → 21.870 s** (4.221% lower), with **three of four wins**;
CPU medians were **102.541 → 104.716 s**. One pair regressed by 2.831%.

The preregistered gate required all four wins and at least 2% median reduction.
It failed, so commit `9fa3cc5b` is **not included**. All eight trials and the
rejected source are retained outside git; no optional reruns were added. Its
isolated 600²/eight-thread wrapper result (55.156 → 8.815 ms) is not a workflow
speedup. Do not combine this campaign's ratio with the main comparison above.

## Verification and limits

All 16 measured four-arm runs passed. Twelve comparisons, plus the excluded
profile pair, matched all 31 raster/member records (four copied inputs and 27
produced entries), including all 19 output bands, metadata, validity/special
masks, signed zeros and NaN payloads. Nine final-state arrays matched bitwise;
the other two state fields matched canonical typed integer values. Schema and
timestamps matched. The four UTCI follow-up comparisons passed the same gates.

Focused local selections passed: 910 classifier/LW/layout/memory cases, 150
verifier cases and 18 harness cases. The installed wheel matched all 74 Python
source files and passed 580 selected tests, including the genuine upstream
small-reference 24-step public pipeline at its unchanged tolerances. Selections
overlap and are not summed. Rejected UTCI routing passed its 112-test selection.
Earlier verification found the existing full-longwave NaN-payload diagnostic
failing on pinned main and the earlier PR candidate. It was not rerun in this
reproduction; these selected tests are not a whole-repository pass.
CI configuration and CI-based acceptance are excluded at the user's request.

Process-tree RSS was unavailable; no memory winner is claimed. Hidden staging
copies appeared in one run's recursive size inventory. Canonical public sizes
exclude them; logs show no second SVF production, but the filesystem mechanism
and any incidental timing impact are unestablished. Failures, including the
prior partial instrumentation campaign, remain preserved and excluded from
these timing statistics. A later-phase JIT-copy guard can be hardened; the
frozen protocol verified its initial copy once; the independent post-run audit
confirmed both the private copy and original still match that initial digest.

The original Atlanta rasters, forcing selection and `02_CPU_SpeedTest.py` were
unavailable. The user's 76.1 s / 16-thread result and the 2 m scene are not
retested or used for a cross-environment speedup. Historical reports remain in
PR history, but missing historical raw outputs are not reconstructed. The new
archive is separately labeled; durable upload remains pending explicit
destination authorization after an automatic approval-review rejection.

## Remaining profile-guided directions

An excluded accepted-source profile found LW 3.958 s, GVF 3.310 s, SW 2.125 s
and UTCI 1.109 s within the thermal tile. SVF included shadow work 1.808 s,
compression 1.633 s, export decoding 0.769 s and direct verification 0.342 s.
These are observed buckets, not removable costs; cumulative entries overlap.
Unchanged costs also moved between profiles, so subtraction is not causality.
Prioritize internal LW/GVF cost attribution, then an exporter-only literal
decoder experiment. Buffer reuse shares that decoder budget. Preserve complete
CRC/readback/hash/fsync work and avoid broad fusion, full-tile decoded caches,
changed patch/ray counts or parallel chronological timesteps.

## Reproduce

Use matching dependencies and keep data/results outside git. The archive
contains exact inputs, frozen four-arm/follow-up protocols, drivers, hashes,
raw reports, representative outputs and a local-source Git bundle. A new
matched two-arm run can use the public runner below; it is a new experiment,
not a replay of the archived four-arm ordering:

```bash
git worktree add --detach ../solweig-main-288d70e2 288d70e2
python development/tools/generate_full_compute_scene.py --output ../synthetic600
python development/tools/full_compute_benchmark.py \
  --reference-checkout ../solweig-main-288d70e2 --candidate-checkout . \
  --scene ../synthetic600 --date 2020-07-18 --threads 8 \
  --memory-budget-mib 4096 --repeats 4 --expected-size 600 \
  --expected-steps 19 --dataset-label synthetic_generated --profile \
  --workdir ../full-compute-new-run
```

For original data, supply its scene, `--met-file` and actual date/time window.
The archived campaign adds a strict bit-equality gate to the runner's original
frozen tolerances; preserve both source/input provenance and complete outputs.
