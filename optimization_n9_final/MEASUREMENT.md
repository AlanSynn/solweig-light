# Measurement and scope for a final decision

## N8 accounting is diagnostic, not a complete elapsed-time result

N8 tier-B defines A0p = minimum(decode x3) + minimum(parallel reducer), and C1 = minimum(producer) + minimum(mask packing) + minimum(views) + minimum(adapter). The minima can come from different repetitions/cache states. Their sum is not `min` or `median` of an actual composed call. Classification, complete scheduling, workspace lifetime and final placement also need explicit coverage. Preserve that record as component attribution; do not invalidate its cautious non-promotion decision or relabel it as a real pipeline measurement.

## Four controls

- M: pinned current main, the user's installed DX baseline.
- A: pinned accepted default at N8 endpoint, including actual main-facing defaults and all accepted preceding CPU changes.
- B: strongest new Numba implementation using the same producer/layout/schedule/guards as native. Give A-compatible layout equivalent mode specialization when possible.
- C: native using exactly that common preparation. A low-level public defensive adapter and a private prepared adapter are different profiles; report the actual production profile.

A/B/C decide native incremental value. M/final decide the merge's user-facing benefit. Historical upstream CUDA/CPU is a separate source and hardware comparison; do not rename M/A as SOLWEIG-GPU.

## Freeze before new target-host results

Retain inherited N8 numerical/DX/performance requirements. Record a new protocol version because continuous timing and bounded production are new implementations. Keep B=128 and 1024, binary/mixed/raw, f64 real provenance, actual H=1/4, tuning vs held-out split and actual default call. No post-result deletion of raw or T4. Retain the existing N8-42/43 named cells and explain any corrected harness boundary without changing workload or gates. Source changes that remove mask packing are legitimate candidates, not reasons to subtract estimated time from old records.

Suggested compact procedure: two alternating pairs for triage; three complete paired observations for the selected small held-out cells. Run a whole frozen sequence, never stop on the first favorable number. Report raw continuous times, per-pair ratios, medians and sample count; no inferential confidence claim from this small n. N8's sum-of-minima remains diagnostic only.

## Exact timer boundary

Start before the first operation the actual invoked region requires; stop after owned host outputs are ready and no worker/async work remains. Include descriptor preparation when not already paid, direct decode, exact classification, mask clearing, allocation or workspace acquisition, guards, task submission, native calls, join, output scatter/copy. First-use includes load and mandatory verification; warm still includes real stage setup. Compiler-free native wheels must not build. Avoid timing a low-level function while production calls a heavier wrapper.

Separate profiled runs from uninstrumented timings. Actual native-entry/completion counts and allocated bytes are proof probes, not permanent per-pixel counters. Timed code must be the same executable path; low-overhead counters should be one per invocation or use a paired untimed verification run. Report fallback counts/reasons and region coverage.

## Environment: finite observations, not polling

Use the existing approved resource envelope, configured/effective native masks, CPU budget, actual admitted processes, background-load snapshots, memory pressure/swap and process-tree RSS. Do not reimpose an unattainable loadavg <2 gate and wait indefinitely. At most two explicitly scheduled/local available measurement opportunities, no busy polling or endless wait tasks. If conditions are invalid, retain censored records and close native unqualified for this release rather than relaxing a numeric gate. Build/test contention on the measured host is prohibited; remote inference may continue if it has no local load.

Memory checks cover parent and workers, not `RUSAGE_SELF` alone. Sum-of-RSS may double-count shared pages, so label it; also note OS pressure and admission inventory. Pin deterministic test budgets, but never invent memory that the machine lacks. A resource block is not an arithmetic pass.

## Tiers

L0: tiny bit/guard/ownership probes. L1: actual source baseline/candidate kernel with all affected inputs. L2: genuine 64/128-square TIFF-to-TIFF, 24/48 steps, intermediate radiation and carried state; no numeric mocks. L3: compact 128/256-square multi-tile, same outputs/cache/checkpoint, no-env installed main/final. Native shortlisting must pass through L2/L3, not stall at producer arithmetic. L4: final frozen artifact only.

## Final large confirmation without another long campaign

Freeze dataset choice before seeing the final candidate's large result. If actual 24 spatial tiles plus references exist, one target campaign may demonstrate the 1800s goal. Otherwise explicitly report `actual_target_unverified`. The existing four synthetic 1024 tiles may be used for a declared synthetic confirmation, never substituted for the actual target. No large test for a candidate already rejected by valid small pipeline evidence. Baseline reuse requires identical source/environment/workload/protocol; 538.8s from a different dependency state is not a matched baseline. One causal environment retry is the entire extra allowance, not a performance rescue loop.

A CPU-only merge is not blocked merely because an unrelated original 24-real-tile performance target is unavailable; its own required compatibility, relevant tests, installed behavior and honest comparative claims must still be satisfied. Conversely a native promotion requiring a missing gate stays unqualified. No C benchmark can waive missing wheel/DX evidence.

## Positive performance gate

Inherited N8 default-native criteria: geometric mean A/auto >=1.10 for declared primary cells, every native-eligible primary cell A/auto and B/auto >=1.05, protected/default/cold regressions <=3%, meaningful actual native coverage >=80% of predeclared eligible work, numerical/state/DX/memory gates. More favorable microbenchmarks cannot override these. No global native default based solely on one ISA/mix/serial setting.

## Completion evidence

For every number label measured, derived-from-measurement, hypothetical, or unavailable. No-env row A must not be recorded as deployed B. One qualified local platform is not global platform portability. A single target run is not reliability/p95. No goal-success banner may stand in for actual native, throughput or merge status.
