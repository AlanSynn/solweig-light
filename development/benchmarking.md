# Performance measurement

A useful comparison fixes the work, source versions and measurement boundary
before collecting trials. The [performance scope](../docs/provenance.md#interpreting-performance)
explains how results relate to upstream and to the supported model;
[runtime controls](../docs/runtime.md#controls) define the execution settings.

## Define the workload

Record spatial tile count, each logical tile's dimensions and overlap,
resolution, timesteps, patches, forcing, vegetation and requested outputs.
Record compatibility exports and checkpoint settings too. Count spatial tiles
separately from timesteps and output bands. A smaller problem or fewer saved
fields changes the comparison.

State whether the timed boundary is a complete workflow, prepared-tile
execution or a numerical kernel. Identify which of process startup, imports,
JIT compilation, geometry, export serialization, checkpoint writes and final
publication it includes. Keep correctness tracing and profiling outside the
timed trials; their instrumentation can change the measured cost.

## Match cache and execution conditions

| Regime | State to establish and record |
| --- | --- |
| First use | Empty private JIT cache; geometry computed during the measured call. |
| Geometry cold | Compatible JIT warmed; geometry recomputed. |
| Geometry warm | Compatible JIT and matching geometry reused. |
| Kernel only | Prepared inputs and compilation state declared for the measured numerical family. |

Record setup separately and give each compared source its own caches.
Geometry-cold results do not imply cold disk reads when the OS page cache is
uncontrolled. Compatible warm JIT can still include compilation for kernels
that deliberately do not persist compiled code.

Record CPU budget, workers, native threads, block size and memory budget,
including the settings actually observed during execution. Establish thread
limits before numerical imports. Increasing a requested worker count may not
increase admitted concurrency; a different dispatch route can also change the
algorithm being measured. Consult [runtime admission](../docs/runtime.md#memory-admission)
when interpreting such comparisons.

## Interpret paired results

Interleave baseline and candidate trials under a declared schedule, retain
failures and report the individual observations. Compute ratios within each
pair: the median paired ratio can differ from the ratio of the two medians.
Small samples and shared-host contention limit how broadly a result applies.

The [exact CPU pair helper](tools/run_exact_cpu_pairs.py) compares candidate
sources on one host. It requires separately supplied, hash-bound protocols,
source/admission records and fixtures for its supported workload. The
[serial helper](tools/run_p7_serial_variant.py) and its
[frozen protocol](benchmarks/protocols/p7_persistent_jit_serial_variant/protocol.json)
retain shared machinery and historical bindings; their defaults can refer to
archived inputs. Read the applicable helper's requirements before preparing a
new run.

The [summarizer](tools/summarize_exact_cpu_pairs.py) authenticates complete
pair records and their original protocol. For five pairs, its bootstrap
interval describes those observations and does not model thermal drift or
cross-host variability. A completed matrix still needs assessment against its
declared numerical, benefit, regression and memory criteria. These contracts
are covered by the [pair](../tests/unit/test_exact_cpu_pairs.py) and
[statistics](../tests/unit/test_exact_cpu_statistics.py) tests.

Sampled process-tree RSS can miss short peaks, and summing process RSS counts
shared pages more than once. Report the sampling interval and observed gaps
with the peak. Keep the admission estimate distinct from measured memory.
For stage profiles, distinguish inclusive and exclusive times before adding
them; nested timings overlap. A kernel improvement needs a workflow
measurement to establish its effect on total runtime.

## Keep a reproducible record

Retain source and input hashes, invocation, dependency versions, hardware,
execution settings, cache setup, timing boundary, trial order, raw times,
failures, numerical comparisons and memory samples. Keep bulk outputs outside
Git and record the result with the relevant change or PR. Candidate comparisons
support claims about the measured candidates; an upstream speed comparison
requires a separately measured upstream configuration doing equivalent work.
