# Freeze-before-selection protocol for CPU backend comparisons

This is a proposed engineering selection policy, not past results. B7-03 freezes exact fixtures, resource envelope and thresholds before variants are measured. Changes to protocol after observations require a new version, rationale and retained prior failures; no selective replacement of hard fixtures.

## Measurements and boundaries

A accepted Numba and B same layout/schedule Numba are immutable controls. C is a matched foreign backend. Use the same captured dynamic-input sequence and model settings. If C requires a different layout, B must implement that exact transformation as well. All comparative setup/layout/packing costs are in the appropriate total; static preparation amortization is identical or separately reported.

Record separate non-overlapping boundaries:

1. **first-use total:** process/application start through required host results/artifacts, including imports, runtime init, JIT/build that a normal fresh installed user requires and IO. Do not include developer source-wheel build unless the actual user must build at runtime; report that developer cost separately.
2. **kernel-only:** preloaded inputs, explicitly synchronized native compute, useful only for diagnosis.
3. **adapter total:** host prepared input -> validation/packing/conversion -> invocation/tracing as applicable -> completion -> required host output. Synchronize before starting and after materialization. Include fallback calls and any runtime memory churn.
4. **warm stage/pipeline:** actual timestep/chronology/full small batch, existing cache manifest/state conditions, output/checkpoint IO.

For every trial record wall time, process-tree CPU usage when available, effective pools and device, peak memory (sampling interval and shared-page double-counting caveat), byte movements/allocations if measured, and all raw failures. `logical array bytes` is not DRAM traffic. Internal device events are not end-to-end time.

## Small comparison budget

Development discrimination: normally two alternating paired repetitions on one dense and one vegetation fixture with matched full chronology. Final small-candidate selection: three paired repetitions on held-out small cases. Use a frozen alternating A/C, C/A order (and separate B/C), or a seeded recorded order. No exhaustive benchmark grid. T1 and T2 are separate-process comparisons; request pools before import and query actual threads after initialization. Equivalent CPU budgets, not environment variable names, define fairness.

Synthetic kernel inputs must change by replaying an immutable prepared sequence rather than repeatedly timing an already computed lazy output. Do not add RNG into the measured kernel interval unless all variants pay it. Recompilation caused by dynamic values or shapes is reported, never silently excluded from first use.

## Proposed gates to freeze

- Capability + exactness: mandatory; no performance exemption.
- Kernel-only >=1.20x is a useful triage signal, not a requirement if broader measured savings justify the port.
- Adapter-total paired median >=1.10x over B on at least one representative held-out workload, without >3% median regression on another supported guard workload, is the initial foreign-runtime advancement gate.
- Actual warm small-batch total paired median >=1.05x over both A and B is the initial integration gate; retain raw range and memory. A cold-first-use guard must show no material regression hidden by warm timing; a warm-only experimental backend may remain explicit opt-in with its limitation, not become a default.
- Below these thresholds, keep B/A or an experiment only. A special deployment value may justify keeping an optional backend only by a documented separate decision before claiming performance benefit, not retroactively moving the speed gate.

These finite samples support local selection, not statistical certainty or generic hardware claims. If noise is larger than the selection gap, mark inconclusive. One focused additional small discriminator may resolve a cause; do not start many large trials to chase significance.

## Thread/resource enforcement

Use independent child processes per runtime/thread configuration. Log requested H, configured maximum, effective mask/pool, worker admission, backend selected and device type. Numba controls do not cap Dr.Jit/PoCL automatically. Cap every active runtime; avoid nested/overlapping pools. CPU time can differ even at identical wall time. 4x2 versus 1x4 uses different total resource budgets and must not be reported as equal-resource speedup.

Benchmark owner holds an exclusive local host lease; no other agent builds/tests, browser automation or large scans on that host during selected measurements. Inference on a remote service is not itself prohibited, but local tool work is. A busy host makes results dev-tier/noisy, not clean performance evidence.

## Final target

One actual K=24 spatial tile campaign, T=24 records each, P=153 and fixed physical settings. Time from declared first-use/warm start boundary through durable publication of all requested artifacts. New candidate vs historical two cases is not a batch speedup. Report absolute throughput if no comparable full baseline exists. Missing actual corpus leaves target unverified, even if the model predicts <1800 seconds.

The helper claim checker validates record consistency, not the physical truth of measurements. Authoritative evidence is the retained commands, data, outputs, source fingerprints and independent review.
