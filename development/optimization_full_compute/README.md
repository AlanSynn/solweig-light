# Full-computation optimization

[Draft PR #2](https://github.com/AlanSynn/solweig-light/pull/2) remains unmerged.
This record replaces the current summary, while [the previous campaign](https://github.com/AlanSynn/solweig-light/blob/230520b784c5aaeffde8f86147a832bc358b723e/development/optimization_full_compute/manifest.json)
remains in Git history. Its unavailable raw archive is not reconstructed or pooled.
Source pins, exact statistics and evidence identifiers are in [manifest.json](manifest.json).

## Decision

Retain the existing optimized runtime. **No new memory experiment is adopted.**
The five memory candidates and a separate LW/SW lookup follow-up failed the
frozen incremental acceptance rule. This update changes only this README and
the existing manifest; raw evidence and rejected patches remain outside Git.
CI configuration and CI-based acceptance are excluded at the user's request.

The retained code compiles ordered SVF and bounded LW/SW/GVF work, reuses owned
immutable preparations, groups identical stored SW coefficients, streams
checkpoint hashing, and uses bounded visibility encoding/verification and
lossless NPZ level 3. Physical grid, rays, patches, timesteps, chronological
state and existing scientific tolerances are unchanged.

## Current matched main comparison

Measured main: `288d70e2b3bd8ca5bba4b65e572048fea37bcc51`.
Measured public PR: `230520b784c5aaeffde8f86147a832bc358b723e`, full tree
`eea4fb51213a16aba62ecab1ccfb130e7b20f0a3`; local alias `62dff51438a53001b16ba301519c84fc1cbc2f3a`
has exactly that full tree. Later evidence documentation changes no runtime code.

The 2026-10-21 workload is a **generated 600 × 600, 4 m scene**, seed 20261020,
19 hourly chronological steps, 153 patches, eight threads and one worker.
Each invocation creates fresh native geometry and outputs, writes all three
legacy SVF artifacts and TMRT/UTCI, and checkpoints every step without resume.
Private JIT caches are warmed; OS/native-build caches are not purged. An
8192 MiB admission budget admits the extra arrays; this is not measured RSS
or a claim of physically unlimited memory. Local numerical work is serialized.

| Four-run median / observed range | Main | Existing PR |
|---|---:|---:|
| Full workflow | 173.243 s | 49.435 s |
| Workflow min–max | 157.336–200.170 s | 43.248–59.004 s |
| Self + waited-child CPU | 964.932 s | 201.949 s |
| SVF including legacy exports | 40.041 s | 12.059 s |
| TMRT/UTCI including outputs/checkpoints | 132.634 s | 35.723 s |

The ratio of median runtimes is **3.504×** (main/PR), with
**71.465% less workflow wall time** and four of four paired wins over main.
Main/PR full captures match exactly; each completed timed arm is checked
against its independently audited capture. Stage medians do not sum to the
median total. Ranges are not confidence intervals.

Original Atlanta rasters, forcing selection and `02_CPU_SpeedTest.py` are
unavailable. The user's 76.1 s / 16-thread result and 2 m scene are not retested,
and no cross-environment speed ratio is inferred. Process-tree RSS is unavailable.

## Extra-memory experiments

The prespecified adoption rule requires four valid pairs, all four workflow
wins and at least 2% reduction in the ratio of medians, plus numerical gates.
It is a repeatability rule, not a statistical significance test.

| Candidate | Valid runs | Median workflow | Wins versus paired PR | Decision |
|---|---:|---:|---:|---|
| Static GVF sums | 4 | 69.527 s | 1/4 | Exclude |
| Factored LW reflection weights | 4 | 53.029 s | 2/4 | Exclude |
| GVF + LW | 4 | 46.949 s | 2/4 | Inconclusive improvement; exclude |
| Decoded LW/SW visibility | 4 | 45.052 s | 2/4 | Inconclusive improvement; exclude |
| Interleaved SVF shadow bank | 3 | 50.495 s | 1/3 | Incomplete valid pairs; exclude |

The SVF comparator median on its three common successful blocks is 44.638 s.
One of its four scheduled runs (block 1 / trial 01) failed with `ENOTEMPTY`
during temporary legacy-export cleanup.
The failure was retained without retry or imputation; its cause is unestablished.
All 27 completed workflows in this campaign passed their output checks.
An earlier interrupted attempt overlapped unrelated payload reads and is
excluded in full; its records and the continuation amendment are retained.

Extra owned arrays at 600² are about 11.52 MB (GVF), 5.76 MB (LW), 17.28 MB
(combined), 660.96 MB (decoded visibility), and 667.61 MB of conservative
SVF-bank admission including schedules. These are array budgets, not RSS.
At 2400², decoded visibility alone would be 10.58 GB; no such run was measured.

### Separate exact LW/SW lookup follow-up

An experimental table groups identical float32 `tan(acos(sqrt(SVF)))` words,
then evaluates the same rounded classification expression for each unique word.
It retains all pixel/patch reductions and exceptional-input fallbacks. The
fixture has 85,814 unique words among 360,000 pixels; the analytical `atan`
call count falls from 768,240,000 to 181,754,052 (76.342%). This is not a runtime
speedup. Its live map is 1.783 MB and largest per-call table is 27.117 MB.

The complete diagnostic capture and 36 focused tests passed. Four fixed pairs
then ran. Three pairs passed output verification: baseline median **41.130 s**,
candidate **43.437 s**, **5.607% slower**, zero wins. The fourth candidate
invocation returned normally in 47.023 s, but failed the output gate and is
not a valid performance sample. No replacement run was added.

That failure has exact TMRT values in bands 1–3, zero values in bands 4–19,
and missing time tags in bands 3–19. UTCI and final state matched. All 19
write-time TMRT digests match the reference, but the publication journal and
post-run inventory already identify the bad TIFF. The completion path checks
whole-file hashes against its own journal without independently revalidating
persisted bands against the write-time digests. This is an observed validation
gap; the cause remains unresolved. The candidate is excluded,
and the PR remains a draft. The failure is not dismissed as numerical noise.

## Numerical relaxation and compression

Only the LW factorization and combined candidate alter floating-point order.
Their maximum observed errors are **0.0000305176°C TMRT** and
**0.0000686646°C UTCI**. Every carried state value at every step remains exact;
no UTCI category changes in either boundary convention. The six spatial ROIs
and all nonempty step/output comparisons pass the frozen provisional Tier A:
max 0.001°C, p99 0.0002°C, RMSE 0.0001°C, absolute bias 0.00001°C.
These are engineering gates on this fixture, not universal scientific bounds.
Neither passing them nor a nonsignificant mean difference establishes a
use-independent tolerance or a speed gain. No approximate default is enabled.

A separate four-order compression screen includes writing, decoded readback,
CRC, hashing and fsync. It does not measure the full model workflow.

| NPZ policy | Median export/verify total | File bytes | Paired wins |
|---|---:|---:|---:|
| Level 3, 1 MiB chunks | 4.352 s | 16,835,741 | Reference |
| Level 1, 1 MiB chunks | 4.121 s | 24,303,705 | 3/4 |
| Level 0, 1 MiB chunks | 3.269 s | 661,013,049 | 4/4 |
| Level 3, 64 MiB chunks | 6.076 s | 16,835,741 | 0/4 |

Level 0 saves 24.90% in this component at 39.26× the file size. No full-workflow
compression gain or production policy change is claimed.

## Remaining work

An excluded current-PR profile records LW 13.054 s, GVF 12.358 s and SW 7.065 s;
SVF includes shadow work 4.088 s, compression 2.836 s and verification 1.779 s.
Cumulative times overlap. In the separate lookup profile even unchanged GVF
moved to 8.224 s: subtracting profiles cannot identify a causal improvement.
The lookup profile is excluded from timing acceptance and its outputs verify.

1. Investigate the persisted-output failure and independently validate saved
   bands/timestamps against recorded write intent before accepting more speed work.
2. Consider an explicit native-only geometry output policy. Public split calls
   already share the native recipe, but a fresh thermal run still publishes the
   legacy trio even with `save_svf=False`. Omitting those artifacts would change
   the output contract and needs a separately labeled measurement.
3. Explore GVF cached-plane copy removal, compact categorical visibility,
   uint8 shadow banks, and fused ordered SVF accumulation. These are unimplemented
   directions, with no measured full-workflow gain or universal exactness claim.
4. A faster shade classifier needs a certified bound on the actual rounded
   `atan` chain and reference fallback near thresholds. Mathematical inversion
   alone does not preserve strict comparisons or floating-point plateaus.

## Evidence and reproduction

The artifact named in the manifest contains exact generated inputs, all retained
capture/timing/profile records, canonical measured outputs, final checkpoints,
failed artifacts, immutable protocols and rejected candidate patches. It uses
SHA-256 chunk deduplication. The workspace archive is verified, but durable
file-saving confirmation is unavailable; the manifest records that limitation.
Extract its `bundle_tool.py` and run:

```bash
python bundle_tool.py verify solweig-memory-evidence-20261021.zip
python bundle_tool.py restore solweig-memory-evidence-20261021.zip NEW_DIRECTORY
```

Whole-archive streaming verification and a miniature build/restore/verify test
are recorded separately. The full evidence tree was not restored to disk.
Raw JSON retains original absolute paths; the archive README explains use of
separate analysis copies and the pinned public harness. The frozen campaigns
are in `timing_plan_clean.json` and `timing_plan_height.json`; failed slots and
post-run output failures remain failures. Historical campaigns are not pooled.
