# N9 protocol freeze (frozen BEFORE any target-host variant result)

Frozen at F0, candidate work not started (HEAD 7abe526a). Protocol version
`N9-CONT-v1`. This freeze inherits every N8 numerical/DX/performance
requirement and changes only: (a) the verdict timing is a CONTINUOUS composed
wrapper, not sum-of-component-minima; (b) production is bounded per region.
N8's sum-of-minima record stays diagnostic attribution; it is neither
invalidated nor promoted to a pipeline measurement.

## Controls (frozen)

- **M**: pinned main `14e88876`, built from a detached checkout at that SHA.
  The user's installed DX baseline. Decides the merge's user-facing benefit
  together with the final candidate.
- **A8**: the branch accepted default (row A Numba fused path) on the
  candidate source, actual main-facing defaults.
- **B**: strongest new Numba implementation using the SAME producer/layout/
  schedule/guards as native (mode-specialized decode, direct classifier,
  bounded slots). Gets every shared improvement native gets.
- **C**: native using exactly that common preparation. The reported profile
  is the actual production profile (public defensive adapter vs private
  prepared adapter are different profiles; the production one is reported).

A8/B/C decide native incremental value. M/final decide merge benefit.
Historical upstream CUDA/CPU comparisons are separate and are never renamed
M or A8.

## Continuous timer boundary (frozen)

Per timed call, ONE clock around the actual composed path:

- **START**: immediately before the first operation the invoked region
  requires on already-prepared inputs. Descriptor acquisition is INSIDE the
  clock whenever the production path pays it per call.
- **Included**: descriptor prep (when per-call), direct decode, FULL exact
  classification, valid-inactive mask clearing, workspace/slot acquisition,
  guards, task submission, native or Numba calls, join, output scatter/copy
  into the owned output frame.
- **STOP**: after the owned `[7, total]` float32 host output is complete and
  no worker/async work remains.
- Cold (first-use artifact load + mandatory verification + JIT) is recorded
  separately. Warm runs still include real per-call stage setup. A low-level
  function is never timed while production calls a heavier wrapper.
- Raw per-rep times are recorded. Reported: median, min, per-pair ratios, n.
  No inferential confidence claims from small n. Sum-of-minima is never a
  verdict. Component timers may additionally run as DIAGNOSTIC attribution,
  clearly labeled, never added into the verdict.

## Frozen cells

- Block sizes: **128, 1024** (both matter; neither dropped).
- Visibility mixes: **binary, mixed, raw** (actual mixed f64 provenance
  scalars; f32 guard arithmetic untouched).
- Patches P=153, real scene values; lane width W=8 primary (W=4 admissible
  diagnostic only).
- Threads: matched across arms (one RuntimeOptions budget N; native leaves
  single-threaded per call inside the BLOCK_FANOUT owner; B SELF_PARALLEL
  granted the same N).
- Slots H=1 and H=4 where admissible (C and B-stream arms).
- REPS=9 paired, alternating-pair triage first, then three complete paired
  observations on the selected held-out cells. The whole frozen sequence
  runs; never stop on the first favorable number.

## Gates (inherited from N8, unchanged)

1. Geometric mean A8/auto >= **1.10** across declared primary cells.
2. Every native-eligible primary cell: A8/auto >= **1.05** AND B/auto >=
   **1.05**.
3. Protected/default/cold-path regressions <= **3%**.
4. Meaningful ACTUAL native coverage >= **80%** of predeclared eligible work
   (native entry/exit counters, not load stamps).
5. Numerical/state/DX/memory obligations unchanged (bitwise parity oracle,
   seven reducer outputs, DX env surface, memory budget admission).
6. Pipeline obligations before any default promotion: small REAL 24/48-step
   TIFF chronology; no-env installed API/CLI; native-entry coverage in the
   installed product. The bundled Linux decoder probe is a development
   prior, not M1 or application evidence.

More favorable microbenchmarks cannot override any gate. No global native
default from one ISA/mix/serial setting.

## Environment handling (finite observations, not polling)

- Start AND end resource snapshots per timed session: loadavg triple,
  available-memory view, swap, admitted process inventory, per-cell loadavg
  annotation to stderr.
- Measurement window gate: the AMENDED N8 tier-B window, inherited:
  1-min loadavg **< 5.0** AND available-memory view **>= 92,000 pages**
  (arm64 16 KB pages). Censor bound: > 8.0 (1.6x start bound) invalidates
  the session. This amendment was recorded and reviewer-verified
  PRE-RESULTS in N8 (amendment_2026-09-23T0817Z); it is not re-litigated.
- At most **two** explicitly scheduled measurement opportunities. If
  conditions stay invalid: retain censored records, close native
  UNQUALIFIED for this release. No busy polling, no indefinite waits, no
  numeric gate relaxation.

### Amendment 2 (F3 final-opportunity launch threshold; recorded BEFORE any timing existed)

State at amendment time: ZERO timed sessions completed in F3; opportunity
#1 was consumed by a gate refusal only (archived
f3_continuous_gaterefused_20260923T131342Z.json, 1-min loadavg 7.21). The
host owner (user) directed at 2026-09-23 ~13:2xZ: "진행 그냥 부하10 이하면
그냥 해" — launch the final opportunity if 1-min loadavg < 10.0. This is
the second pre-result environment amendment by the same authority as the
N8 2.0->5.0 amendment (amendment_2026-09-23T0817Z lineage); it changes
ONLY the launch threshold of the FINAL F3 opportunity. Unchanged: the
5-min loadavg sanity check, memory view >= 92,000 pages, per-cell loadavg
annotation, censor bound (> 1.6x the session's actual start load), the
two-opportunity total, and every promotion gate. Risk recorded: launches
under load 5-10 are noisier and CPU contention can bias arms differently
(single-threaded native leaves vs prange Numba); therefore per-pair ratios
remain the verdict basis, absolute times are annotated with their load,
and a marginal result (within 2x the observed spread of the gate margin)
must be labeled marginal in the verdict record rather than claimed as a
clear pass.
- Exclusive host lease while timing: no builds, tests, or JIT compilation
  on the measured host; remote inference may continue.

## Harness acceptance rules (F0 audit delta)

- Block-size parsing MUST reject 0, negative, and non-positive-multiple-of-
  lane-width values loudly (fixes the N13-7 vacuous `--block-sizes 0` pass).
  Minimal validation only; workload unchanged.
- Parity precheck (N8 5-way) mandatory before any timed cell.
- Native entry/exit counters and completed output extents must equal the
  declared work for every timed native cell; mismatches void the cell.
- Raw records are never deleted post-result (no T4 deletion).

## Closure semantics (frozen now)

- A valid continuous comparison LOSS on primary cells closes native for
  this release (`closed_cpu_only` path; rescue candidates prohibited).
- An environment block without credible qualification also closes native
  for this release, with blocked evidence preserved.
- Selection outcome: `closed_native_qualified` | `closed_cpu_only` |
  `blocked_no_safe_merge`. No `native_goal_open` handoff exists in N9.
