# Implement a default-worthy CPU-native execution region without changing user DX

You are the GLM-5.3 coordinator in Claude Code. This packet supplies architectural decisions and proof boundaries. Use authenticated Opus specialists for difficult implementation, proof and review when available. Independent GLM agents remain useful. Do not require Astra/Codex to resume the work. Execute code changes, run bounded tests, investigate failures, repair, review and integrate locally.

## Authority and starting state

Work in the existing `perf/native-optimization` integration worktree. The observed native tip is `16cdc56cbc8755675487b9c9c1f5a7e987e2c9e4`; the observed main is `14e888760727583ef782a4dc0e7a5c7c6e6ff9d1`. These are reference pins, not reset targets. Preserve later commits, uncommitted work and earlier evidence. Record actual source and dependency closures before relying on old results. Read applicable root instructions and the short policy documents once. Resolve obsolete earlier goals in favor of this user's same-branch/default-DX objective, never in favor of weaker scientific or security guarantees.

Allowed: inspect, edit task-owned source/tests/docs, create explicitly pinned detached worker worktrees, use isolated user-space build environments, execute bounded local tests, build local wheels, fix failures, commit reviewed changes to the same branch. Not allowed: force-reset/rebase/stash user work, create a competing named integration branch, push/PR/merge/release, change credentials/provider/global configuration, disable branch protection, broadly trigger hosted CI, delete dirty worktrees or user transaction data.

## Product outcome

Implement a transparent private execution planner. Public `solweig_light` APIs and `solweig-light` CLI remain the main-compatible interface. All seven public functions remain operational. The explicitly installed compatibility distribution keeps its separate ownership of `solweig_gpu` and `thermal_comfort`; do not move those names into the main wheel.

Default users do not set `SOLWEIG_LIGHT_LW_BACKEND`, request a native extra, install ISPC/CMake/compiler/zsh, or wait for a runtime compiler/network download. Qualified platform wheels include the native library. Unsupported or unqualified configurations use the trusted Numba implementation before launch, through the same interface. Source installs without a native artifact/toolchain must continue to install and run without new requirements; do not claim they provide native acceleration. Existing main GDAL prerequisites are not eliminated by this task.

No-env automatic native selection is the goal, not permission to enable an inferior implementation. Freeze the numerical and performance promotion gates before candidate measurements. A native branch that only wins a single-thread giant-block microbenchmark, or an auto path that always falls back, is not default-qualified. Test actual public defaults including block=128 as well as supported tuned H/B profiles. Native must beat the strongest equivalent-layout Numba in its promoted region. Retain successful Numba improvements even if native remains unpromoted; report that outcome honestly.

## Required engineering sequence

1. Repair the measurement boundary. Run genuine call-through instrumentation in tile workers, not just parent timers. Count actual C entries and fallback causes; separate once-only initialization, invariant validation, dynamic validation, packing, decode, classification, reduction, output handling and I/O. Do not import the synthetic dense-wrapper 1.5-2.2% fraction as real packed-path coverage. Fix process-tree memory accounting. Scope B7-60 timings as the measured prepared-input three-stage workflow, not all cold application startup.
2. Remove repeated runtime build checks without changing arithmetic. Introduce versioned, process-local handles whose artifact/compiler/ABI/ISA/math identities are established once. Package loading and expert source compilation are separate mechanisms. No mkdir/stat/source reads/JSON/hash in the block execute path. Detect PID changes and never share a pre-fork pool blindly. Preserve hot-swap behavior only at explicit workflow boundaries.
3. Build controls A/B/C around a larger dataflow region. A is current accepted Numba; B is Numba with the same direct AoSoA producer and region schedule; C is the corresponding native region. Produce visibility and masks in the consumer layout rather than transposing a full temporary. Initially retain original mathematical classification; then port it only with its existing explicit SLEEF arithmetic intact. Keep both longwave sweeps and mixed f64/f32 nodes.
4. Separate microblock and dispatch region. Microblocks are cache-bounded; one dispatch covers many of them. Choose exactly one inner multicore owner, bounded by the public runtime budget. Do not create an executor per block or layer ISPC tasks, OpenMP and Numba pools on top of each other. Keep tile-level Python calls in subprocesses while module-global demand remains.
5. Broaden only against measured residuals. Optional exact predicate caches and finite-state coefficient reuse can eliminate repeated decode/predicate work without touching original visibility artifacts. Export/CRC/value checks can share a bounded read pass without deleting validation or changing failure/publication order. GPU regions remain research-only unless capability, exactness and full boundary timing justify them; CPU default deployment must not acquire GPU requirements.
6. Build transparent packaging and selection. Use the same distribution, verified platform tags, correct library closure/ISA detection and no machine-specific build paths. Ship immutable artifacts and manifests. Main installation examples and user scripts are unchanged. Missing optional capability is distinct from a crash inside an admitted kernel.
7. Integrate only reviewed, exact, worthwhile changes. Freeze and validate a locally installed binary wheel, a no-native source installation, fallback on unavailable/unsupported hosts, and unchanged CLI/API/metadata/state. Promote only covered ISA/math/workload profiles with a versioned private policy; leave others on Numba. Prepare release build recipes but do not publish.

## Numerical integrity

The accepted compiled dtype graph, not a pretty real-valued formula, is the reference. `RN32(f64(acc)+c64)` cannot be replaced with `RN32(acc+RN32(c64))`. Preserve ordered patch sums, branch evaluation, NaN/Inf masks, signed zero, denormals, division and rounding, two-sweep reflection and all carried state. Keep raw codec bit patterns and exact legacy export semantics. Private demand pruning does not alter full public diagnostic outputs. No relaxed fast-math or new FMA; existing deliberate SLEEF FMA is not forbidden. Separate per-compilation-unit policies and audit generated code.

## Execution and stopping rules

No artificial total model-token/agent cap. Delegate independent tasks with immutable base, exact owned paths, dossier, interface and test budget. Native completion/wait mechanisms replace status polling. Independent reviewers inspect evidence before repeating tests. Build/test/measurement slots share one resource ledger; benchmark host is exclusive.

L0/L1 for kernels and guards, real 64/128-square 24/48-step L2 for chronology, 128/256-square small batches for selection. Reserve a scale proof for the settled winner, not every edit. One final actual 24-spatial-tile campaign and at most one causal retry are the maximum default, with missing references/data explicit. An installed-default improvement and an actual-target result are separate labels.

Do not stop after scaffolding, compilation or a faster microbenchmark. Do stop a losing experiment at the frozen stop-loss boundary and move to the strongest dependency-ready alternative. If all admissible native variants lose, finish an honest partial native outcome with the best verified implementation and exact residual model. Do not lower gates or disguise B as C to manufacture completion.

## Terminal artifacts

Reviewed local commits; exact branch/base/source/environment/runtime identities; main-DX contract and differences; typed-node/proof records; direct-producer/layout/handle/memory design; raw paired A/B/C trials; installed wheel and source-fallback evidence; actual backend coverage; a conservative private default-eligibility certificate or an explicit rejection; known failures/unavailable platforms; next steps in FUTURE_OPTIMIZATION.md. The user must be able to resume without returning to Astra.
