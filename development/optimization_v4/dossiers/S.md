> Worker limit: L0-L2, owned branch/worktree, no 1024/full-batch or hosted-CI run. Submit L3 requests to the single lab owner. Read `../VALIDATION_POLICY.md` for identity-based reuse; full-scale checks wait for the frozen final candidate.

# S family dossier

Load this file only for assigned S IDs. Full catalog and proof requirements are authoritative.

## S01: Liveness-based memory admission with honest raw fallback

**Tier:** first. **Class:** operational_exact. **Relation:** additional.

**Transformation.** Model scene, state, real encoded payloads, per-stage peak workspace, native/JIT/GDAL caches and active writers. Admit jobs by simultaneous live bytes rather than summing mutually exclusive scratch.

**Admission and failure modes.** Do not replace worst-case accounting with two observed RSS samples, ignore mmap resident pages, or simply raise the RAM limit. Include a conservative safety reserve and out-of-core fallback.

**Cost and crossover.** Can permit larger W under the same physical budget. Memory saving is a scheduling enabler, not a multiplicative kernel speedup.

**Smallest deciding experiment.** Actual allocations and process-tree memory under concurrent large/raw fixtures, bounded queue tests, failure before OOM and unchanged model outputs.

**Source anchors:** [S07].

## S02: Persistent bounded worker processes

**Tier:** first. **Class:** operational_exact. **Relation:** additional.

**Transformation.** Initialize one worker/JIT/math environment, process sequential independent tile jobs, release tile state/handles/locks after each, and reuse only bounded immutable runtime resources.

**Admission and failure modes.** No retained tile history or stale state. Avoid unsafe fork after native thread initialization; use supported process startup. Retire leaking/fragmented workers at safe job boundaries.

**Cost and crossover.** Reduces K*(import+JIT_load) to W*(import+JIT_load) plus task dispatch. Large-tile savings may be modest; compare actual startup share.

**Smallest deciding experiment.** Multiple heterogeneous tiles, cancellation, worker death, memory plateau and one-owner file lifecycle.

**Source anchors:** [S07], [T03].

## S03: Joint worker/thread/microtile optimization

**Tier:** first. **Class:** operational_exact. **Relation:** additional.

**Transformation.** Select W,H,B under one CPU/RAM budget using measured concurrency curves and disjoint tuning scenes. Explicitly account for writer/compression threads and hybrid-core behavior.

**Admission and failure modes.** W*H is a reservation, not a promise that all cores are equivalent or fully busy. Changing resources is not a same-resource speedup. No tuning on final evaluation results.

**Cost and crossover.** Ideal X=C/(p+C*s/W) before contention; actual t_tile(W,H,B) decides. Share-memory saturation and tail imbalance can reverse the ranking.

**Smallest deciding experiment.** Fixed-budget 1x8,2x4,4x2 or hardware-supported equivalents, real concurrent times, thermal/order controls and memory peaks.

**Source anchors:** [S07], [T04], [T05].

## S04: Memory-weighted longest-job-first tile scheduling

**Tier:** second. **Class:** operational_exact. **Relation:** additional.

**Transformation.** Use static input features or a calibrated cost estimator to order independent ready tiles, reducing the last slow-worker tail. Keep logical identities and final artifacts unchanged.

**Admission and failure modes.** Estimate only from tuning/calibration data. No priority policy may starve a tile, alter per-tile forcing, or bypass publication ordering requirements.

**Cost and crossover.** For heterogeneous jobs, greedy assignment can reduce makespan versus arbitrary order. Quantify idle-tail seconds; no benefit for identical jobs.

**Smallest deciding experiment.** Unequal tile shapes/heights/vegetation, deterministic output mapping, fairness, cancellation and actual full-batch makespan.

**Source anchors:** [S07], [T05].

## S05: Stage-aware resource tokens and producer/consumer scheduling

**Tier:** conditional. **Class:** operational_exact_research. **Relation:** additional.

**Transformation.** Reserve resources separately for cold geometry, simulation and export; overlap independent tile stages while maintaining per-tile chronological and durability dependencies.

**Admission and failure modes.** Token acquisition must be deadlock-free, reserve transient memory and count native threads. No model timestep reordering. Static worker simplification may be faster to implement.

**Cost and crossover.** Steady-state throughput bounded by the slowest stage capacity, min_j(m_j/service_j), with startup/drain and shared bandwidth penalties.

**Smallest deciding experiment.** Event-DAG validation, injected worker/writer failures, peak concurrent memory, no oversubscription and pipeline-drain latency.

**Source anchors:** [S07], [S08], [T05].

## S06: Bounded asynchronous single-owner writer

**Tier:** conditional. **Class:** operational_exact_research. **Relation:** additional.

**Transformation.** Overlap completed-buffer output writes with independent computation using explicit buffer ownership and a small queue; commit checkpoint cursor only after writes and required durability acknowledgments.

**Admission and failure modes.** Never overwrite a queued buffer, share writable GDAL datasets, skip readback/fsync, or silently accept writer failure. Writer CPU and buffers count toward budgets.

**Cost and crossover.** Can approach max(compute,write) rather than compute+write only when resources permit overlap. Extra copies may erase the benefit.

**Smallest deciding experiment.** Backpressure, buffer-reuse corruption, writer exception propagation, crash at each commit boundary and byte/metadata equality.

**Source anchors:** [S09].

## S07: Content-addressed immutable checkpoint payload reuse

**Tier:** conditional. **Class:** operational_exact_research. **Relation:** additional.

**Transformation.** Reuse already durable unchanged state-map payloads across generations with generation manifests referencing immutable content; write and sync only new payloads while preserving every checkpoint boundary.

**Admission and failure modes.** Object identity/read-only flags are insufficient for mutable arrays. Prove owned versioned immutability or compare content. Keep corruption verification, GC pins, fsync and atomic cursor semantics.

**Cost and crossover.** State write bytes scale with changed distinct payloads rather than all state each step; hashing may still cost O(T*N). Most beneficial for unchanged nocturnal carried maps.

**Smallest deciding experiment.** Interrupted reuse/publication/GC, content mutation, retained-reader lifetime, all state values and exact recovery at every original boundary.

**Source anchors:** [S09].

## S08: TIFF/NPZ packing and compression tuning with schemas intact

**Tier:** second. **Class:** operational_exact. **Relation:** additional.

**Transformation.** Batch writes to useful storage blocks; reuse bounded export buffers and benchmark compatible compression settings when binary layout is not an API contract.

**Admission and failure modes.** Preserve decoded pixels, metadata, filenames, bands and required cold exports. Include compression CPU and actual disk writes/reads. Do not mislabel a changed output workload.

**Cost and crossover.** Lower syscall/compression/packing overhead or physical bytes. Original float32 payload for 24x24x1024^2x10 outputs is 22.5 GiB before metadata, cache/export/checkpoints.

**Smallest deciding experiment.** Legacy reader round-trips, filesystem failure, all metadata, full end-to-end equal-output timing and writer CPU accounting.

**Source anchors:** [S09], [S11], [S14].

## S09: Persistent JIT identity, bounded signatures and reusable scratch

**Tier:** second. **Class:** operational_exact. **Relation:** partly existing; investigate residual only.

**Transformation.** Reuse verified compiled signatures and owned scratch inside persistent workers; compile unavoidable cold signatures once per appropriate cache identity and reserve JIT memory.

**Admission and failure modes.** Much JIT reuse already exists. No serial/parallel cache-key collisions, stale constants or platform-profile leakage. Warmup cost belongs inside first-use timing.

**Cost and crossover.** Eliminates residual compilation/allocations only where observed. Too many specialized kernels increase startup and instruction-cache footprint.

**Smallest deciding experiment.** Fresh-process compile-order permutations, installed-wheel source hashes, read-only caches and first-use total time.

**Source anchors:** [S07], [S12], [T03].

## S10: Owned immutable input snapshots and shared verified preparation

**Tier:** conditional. **Class:** operational_exact_research. **Relation:** additional.

**Transformation.** Where the declared mutation contract permits it, read/verify input once into an owned immutable preparation object shared by independent consumers, avoiding duplicate parse/read/derivation.

**Admission and failure modes.** Do not replace content validation by mtime or remove input-change detection. Snapshot creation is timed; current public mutation/error semantics stay authoritative. Unsupported callers retain original checks.

**Cost and crossover.** Reduces duplicate reads/computation only if snapshot/verification cost is less than repetition. A memory mapping of a user-writable file is not immutable.

**Smallest deciding experiment.** Input mutation at every validation boundary, failed snapshots, shared readers, file replacement and current exception contracts.

**Source anchors:** [S07], [S08], [S09].

## S11: Instrumented dispatch census, lean hot-path validation and evidence reuse

**Tier:** first. **Class:** operational_exact. **Relation:** additional.

**Transformation.** Collect cheap per-stage aggregate counters and validated feature flags once; avoid repeated introspection/type scans when owned inputs cannot change. Reuse source-keyed test evidence for unchanged components.

**Admission and failure modes.** Never delete validations with observable error behavior or reuse evidence after a dependency/profile change. Profilers do not run during final paired timings.

**Cost and crossover.** Reduces Python/dispatch overhead and developer/agent work. Numerical runtime and development-token savings are reported separately.

**Smallest deciding experiment.** Validation-call coverage, adversarial mutations, source/dependency hashing and profiler noninterference.

**Source anchors:** [S03], [S07], [S11].

