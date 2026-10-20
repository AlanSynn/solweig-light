# Full-computation optimization

Requested 2026-10-20. Reference: main commit
`288d70e2b3bd8ca5bba4b65e572048fea37bcc51`. Implementation and review are in
[PR #2](https://github.com/AlanSynn/solweig-light/pull/2).

The complete own-met CPU workflow spends substantial time repeatedly
dispatching patch and direction work, decoding visibility, exporting legacy
geometry, and copying or serializing arrays. This branch reduces those costs
while preserving the existing chronological model and public output contract.

[Round 2](ROUND2.md) records the final three paired, full 600 × 600 runs.
Pinned main took a median **91.267964 seconds** and final numerical candidate
`afa54cb3041e9481ad6691b4c71c1e5ec0362d5a` took **23.965122 seconds**:
**3.80837× faster**, or **73.7420% less workflow wall time**. All compared
decoded arrays and the final chronological state matched bitwise. These are
same-host synthetic diagnostic results, not measurements of the user's
Atlanta rasters.

| Final comparison, three alternating pairs | Main | Candidate |
|---|---:|---:|
| Median complete workflow wall time | 91.267964 s | 23.965122 s |
| Observed workflow range | 91.124814–94.418598 s | 23.753017–24.496364 s |
| Median whole-process wall time, including startup/imports | 92.478838 s | 25.222607 s |
| Median workflow self plus waited-child CPU | 530.353268 s | 112.434316 s |
| Median complete SVF stage, including legacy exports | 24.183081 s | 7.037012 s |
| Median TMRT/UTCI stage, including outputs/checkpoints | 68.157562 s | 16.655007 s |
| Visibility NPZ size | 10,212,358 bytes | 16,835,741 bytes |

The workload is a generated 600 × 600 grid at 4 m, 19 chronological forcing
rows, 153 sky patches and eight threads. Every measured trial starts with
fresh geometry and outputs; only each variant's private JIT cache is warmed.
No process-tree peak-memory comparison is available. Independent stage
medians do not sum to the median total, and observed ranges are not confidence
intervals. [Evidence inventory](EVIDENCE.md) records original evidence identities
and their current availability: the completed raw benchmark directories and
prepared ZIPs are no longer present after the task resumed, and durable upload
had not succeeded. The committed implementation and measurement summaries
remain available; raw-evidence closure is still open.

[Round 1](ROUND1.md) records the first implementation and the profile used to
choose the small follow-up. Its separate campaign measured main at 91.936602 s
and the first candidate at 31.870904 s. The final candidate's median is
24.8% lower than that first candidate's median; the campaigns do not isolate
the contribution of each individual change.

## Workload and comparison contract

The requested production comparison is the user's 600 × 600 Atlanta tile,
19 chronological timesteps, 153 sky patches, all four raster layers, and
the same own-met forcing. Keep one original logical tile, output timestamps,
TMRT and UTCI outputs, checkpoint interval 1, full legacy geometry exports,
and matched cold geometry / warmed JIT conditions on both sides. Report
first-use startup separately. Run reference and candidate with the same
Python environment, CPU affinity, thread count and output options.

The original data and `02_CPU_SpeedTest.py` are on another machine and are
not present in this checkout. The reported 76.1-second lite result is
historical context, not a measurement of this pinned main on the current
machine. Synthetic family timings and repository fixtures must never be
presented as that production comparison.

## Implementation scope

- Ordered SVF accumulation around the unchanged ray calculation; static
  bush routing; cached parallel daylight wall-shadow kernels.
- Single-pass exact legacy visibility comparison, combined TIFF validation,
  vector native payload validation, write-time hashes and mapped descriptors.
- Compiled bounded shortwave/longwave block schedules, mixed-dtype prepared
  GVF postprocessing, and explicitly owned static radiation preparations.
- Reused engine subexpressions, streamed checkpoint serialization, reduced
  raster copies and explicit accounting for added resident/scratch memory.

| Area | Change and purpose | Preserved boundary |
|---|---|---|
| SVF | Compile the ordered float32 annulus accumulation; compute invariant bush routing once. | Original rays, patches, scalar/store order and mixed-dtype fallback. |
| Daylight wall shadows | Select cached parallel receiver kernels for sufficiently large arrays; retain the small-array serial route. | Independently defined serial/parallel kernels and exact output values. |
| Longwave and shortwave | Move the bounded outer block schedule into compiled code, using serial reduction leaves inside each owner. | Patch reduction order, bounded per-owner scratch and mapped-data leases. |
| Ground view factors | Batch the parallel direction/postprocessing schedule, retaining float32 accumulators and mixed-dtype behavior. | Eighteen directions, water handling, nonfinite/error fallback and chronological state. |
| Static radiation data | Own immutable snapshots and cache only proofs and tangents tied to those exact snapshots. | General caller arrays still receive defensive validation. |
| Native and legacy geometry | Combine compatible validation passes, decode C-order visibility in bounded blocks, hash accepted write bytes and borrow mapped descriptors. | Independent completed-file verification, CRC/schema checks, mutation guards, locking and rollback. |
| Thermal expressions and input | Reuse selected ordered subexpressions and avoid a redundant copy of already-owned float32 raster data. | Dtype, first failing operation and fallback behavior. |
| Checkpoints | Stream NumPy serialization into a hashing writer instead of building a complete serialized memory buffer. | Identical payload bytes, flush/fsync, checkpoint interval and publication order. |
| Admission | Price new resident static data, parallel scratch and GVF finishing overlap explicitly. | Existing conservative reserves and rejection behavior. |

The prepared serial GVF batch was rejected after it was slower in the local
family comparison (1.35477 versus 1.30413 seconds). The retained serial route
remains active. Wall parallelism also keeps a size threshold because a small
64 × 64 case regressed. Family timings support those routing decisions;
only complete paired workflow timings support an end-to-end speed claim.

## Profile-directed follow-up

The first full profile identified 106,947 Python visibility decode calls
(2.58 s cumulative), zlib compression (5.13 s self time), and 459 compact
visibility append operations (2.25 s cumulative). The next change therefore
reuses the existing bounded compiled decoder for legacy NPZ export and adds
a small integer-only encoder for exact contiguous native float32 planes.
Unsupported layouts, subclasses, tiny workspaces and special error paths
retain their existing implementation. Encoded payload bytes and decoded
array bits remain exact.

A separate complete export-family experiment compared lossless DEFLATE
levels 6, 1 and 3 with independent verification and publication included.
For the generated 600 scene, level 3 reduced median export transaction time
from 7.1584 to 3.7649 seconds, with NPZ size increasing from 10,212,358 to
16,835,741 bytes. Level 1 took 3.4163 seconds but needed 24,303,705 bytes.
Level 3 is selected as a time/size compromise, not a universally best level.
The public workflow still writes every legacy artifact. Existing valid
archives at other levels remain valid; no recompression is forced.

An independent numerical review also found that persistent outer JIT
caches need explicit source identities for their imported compiled helpers.
The reviewed LW, SW and GVF call chains now declare those dependencies at
each persistent layer; the new SVF/codec entries bind their own defining
source. Tiny process-isolated upgrade tests change numerical constants in
owned copies, including same-size/same-mtime edits, and compare the changed
warm-cache output with an independent fresh-cache result. These are scoped
dependency declarations, not automatic repository-wide dependency discovery.

Each accepted implementation must pass its frozen intermediate and final
numeric contracts, mutation/corruption checks and output/restart behavior.
No physics, ray, resolution, patch, timestep or tolerance reduction is part
of this change. Preserve defensive fallback paths and public signatures.

## Review and validation

Independent review found and corrected moved overflow/warning behavior in
GVF and shortwave assembly, the first-error order of a reused Kup expression,
NumPy-integer dimension handling in admission, and retention of unused GVF
accumulator planes. A conservative 64 bytes per pixel finishing allowance
accounts for the changed GVF lifetime; only the surviving sum plane is copied
out of the batched owner.

The first implementation passed the focused geometry, visibility/cache,
radiation and ownership suites, 144 integrated core tests, and 77 tests
against an installed wheel. The wheel set includes genuine chronological
TIFF comparisons and API/signature checks. These sets overlap and should not
be added into a unique-test total. The complete 600 comparison independently
checks all produced arrays, raster schemas, special values and final state.

The final follow-up passed 459 integrated encoder/export/service/native/cache
tests, 32 fresh-process exporter/block checks after decoder identity binding,
and eight numerical source-upgrade cases. The eight upgrade cases passed in
two invocations (seven cases, then the added decoder case). Existing exact JIT
cache checks also passed. These sets overlap with other focused checks.

The final wheel contains the same 74 Python files, byte for byte, as the
benchmarked candidate source. Its combined targeted validation recorded
**166 passes and three failures**. Two failures explicitly reported insufficient
automatic memory admission; the third reported a worker pause/event timeout,
whose cause is not established by the traceback. The same three unchanged
tests then **all passed in isolation against the same installed wheel**, using
automatic admission and no product admission override. Both the original
failures and the follow-up are retained. This is not described as one clean
169-test combined run.

All three final full-workflow pairs compare 31 decoded raster/member entries:
four copied inputs and 27 produced arrays. Their maximum finite absolute error
is zero, with exact signed-zero and NaN payload bits. All 19 TMRT/UTCI output
bands and all eleven final state fields agree. TMRT is entirely finite;
UTCI retains 1,504,819 identical NaNs among 6,840,000 samples. Internal state
is compared at the final checkpoint, not claimed independently at every step.

One existing diagnostic test remains a known environment/baseline limitation:
`test_kernel_primary_matches_full_route_invariance` finds different NaN
payload bits in column 7 of the unchanged full longwave serial/parallel
kernels. It fails on both pinned main and the final candidate in this
Python/NumPy/Numba environment.
Its failure is retained in the evidence; its assertion and tolerance are not
changed. The new primary route and the full 600 outputs have separate exact
comparisons. This observation does not certify every diagnostic kernel or
every platform.

The original production comparison remains blocked on the four original
rasters, meteorological rows and `02_CPU_SpeedTest.py`. A reproducible runner
and its [protocol](../docs/full_compute_benchmark.md) are included so the
same pinned-main comparison can be made on that server without guessing its
selected date, time range or data.

## Final profile and stopping decision

After the profile-directed follow-up, the unprofiled thermal stage accounts
for about 70% of the final workflow median. The extra profile observes 4.44 s
in the longwave batch, 3.47 s in ground-view work, 3.36 s in shortwave, 1.14 s
in UTCI and 0.90 s in checkpoint handling. These cumulative profile rows
overlap with their parents and must not be summed with the workflow stages.
They do not establish that memory bandwidth is the limiting hardware resource.

The complete visibility append family fell from 2.25 s in the first profile
to 0.25 s in the final profile; export/decoding/compression remain measurable.
The first profile's raster reads, delay helper and timezone initialization
were only hundredths of a second, so no further change was made there.
The current PR stops after the two complete comparison rounds. Further
kernel or UTCI scheduling changes require their own exactness evidence and
complete comparison; they are not bundled into an unmeasured final revision.

For this fixture, the final candidate is preferable when complete-calculation
latency and CPU work matter. Main produces a smaller visibility NPZ. The
candidate does not have a demonstrated total-memory advantage in this host,
and neither the original Atlanta performance nor a 2 m result is established.

## Verification and performance rounds

1. Establish family references; implement and run focused differentials.
2. Run genuine chronological TIFF-to-TIFF and restart checks.
3. Compare main/candidate with identical inputs, including every requested
   output and state; keep raw timing and profile results outside git.
4. Profile the candidate, make a small change addressing a measured residual,
   then repeat the relevant correctness and paired timing checks.

Only compact summaries, invocations and evidence hashes belong here. Raw
rasters, profiles, timing trials and compiled caches follow `CLAUDE.md`'s
external-evidence policy. The PR remains a draft until its comparison and
remaining verification requirements are resolved.
