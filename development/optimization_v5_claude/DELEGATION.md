# Delegation v5: no Astra supervision dependency, no artificial inference quota

## Ownership

This chat has fixed the optimization envelope in `DESIGN_AUTHORITY.md`. The GLM-5.3 coordinator implements that plan, dispatches work, resolves ordinary engineering questions, consumes completed results and maintains a compact ledger. Actual Opus specialists handle high-risk numerical patches, proof review and difficult differential failures. The independent reviewer is not the implementation author. The integrator owns shared source and central state; the lab owner owns timing campaigns.

No routine approval from Astra or the user is needed for safe local work. Do not start an Astra session at the end for ceremonial review. Exceptional model-policy decisions get a concise file, not repeated chat supervision. Work inside the envelope continues.

## Parallelism frontier

There is no fixed four-agent cap, session-total cap or token budget. Launch all **useful ready independent tasks** supported by the actual runtime/provider. The frontier is constrained by:

1. dependencies and immutable interface contracts;
2. exclusive write ownership, including tests and generated manifests;
3. provider/client capacity and rate limits;
4. local process memory, CPU and disk admission;
5. an exclusive performance lease.

The 56 catalog entries are ideas, not 56 mandatory implementation workers. Read-only proof audits, counterexample design, disjoint helper modules and API review can run simultaneously. Alternative writers for the same family use isolated experimental worktrees; only one chosen patch is integrated. Partition implementation and test files explicitly before both workers start.

Do not create redundant agents just because tokens are available. A second worker must reduce critical-path elapsed time, find an independent counterexample or own a genuinely different implementation. Duplicate context scanning and repeated tests still cost time.

## Separate three concurrency budgets

- **Inference sessions:** elastic, no artificial cap; backpressure on real rate/client limits. Their local client processes still use RAM.
- **Local compilation and validation jobs:** centrally admitted. A worker does not self-allocate all native threads. L0/L1 jobs may share the host only with a known summed budget; L2 jobs are especially bounded.
- **Performance runs:** one owner and exclusive host lease. All other local builds/tests/compression/profilers pause before the measured interval. Remote inference may continue only if its local client activity cannot contaminate the frozen measurement envelope; simplest policy pauses those local processes too.

Unlimited inference is not permission to issue unlimited 1024 tests. `VALIDATION_POLICY.md` remains unchanged in that respect.

## Topology choices

Preferred: GLM coordinator with bounded native GLM subagents plus separate real-Opus sessions where the GLM endpoint cannot serve Opus. Use native mixed-model subagents only with a verified multi-provider route. `MODEL_ROUTING.md` is authoritative. Do not mistake an Opus alias remapped to GLM for Opus use.

Native nesting is optional, not required. A coordinator may authorize a manager to split a task when the installed runtime supports it, but child packets must partition ownership and retain the same validation ceiling/resource budget. Reviewers and benchmark owners do not recursively delegate broad tasks. No recursive "make a team for the whole project" prompts.

## Task packet

Use `templates/WORK_PACKET.yaml`. Supply an immutable base, exact task, proposed interface, owned files, forbidden/shared files, relevant blueprint/dossier, guard/fallback, required observables, test/reference locations, L0-L2 ceiling, resource lease requirements and completion artifact path. A worker never receives the entire conversation and all historical evidence by default.

Packet size is determined by technical sufficiency, not a hard token cap. Include all details needed to implement without rediscovering decisions. The terminal summary remains concise; large diffs/traces live in files. Sessions can use as much reasoning as needed within the actual subscription/provider capability.

## Complete, do not poll

A worker executes: read relevant source -> implement coherent patch -> selected tests -> inspect failures -> repair -> finish evidence -> terminal result. It returns only when done, genuinely blocked, or the actual client reports a partial/session limit. A resumable partial result is not failure or completion; resume it from its packet/artifacts without reloading all history.

Use native completion notifications, supported blocking waits, or OS child-exit events. Do not repeatedly ask "finished?", call status/list/log every few turns, or replay every transcript into the coordinator. Necessary process CPU/RAM monitoring is machine-level measurement, not LLM polling.

The result contains commit/tree hash, actual route, changed files, exact test commands/outcomes, reused evidence identities, failures/limitations, integration recipe and next dependency. The coordinator processes each terminal event once. A large worker transcript is evidence to open only for a concrete debugging need.

## Review and integration

Opus proof specialist may work alongside an implementer on the immutable mathematical draft. Final review reads the immutable actual patch and evidence, not only the draft. Routine tests are not rerun unless a hole, changed dependency or inconsistent log is identified.

Only the integrator edits `engine.py`, `pipeline.py`, public APIs, shared dispatcher/config formats and central task status. Family workers deliver a patch recipe for these. Integrate one accepted source identity at a time onto `perf/claude-glm53-cpu-v5`; run affected small interactions. This serial integration point is intentional and does not serialize independent coding.

New mutations to an already reviewed source invalidate relevant evidence. Documentation-only result aggregation normally does not. Do not chase an exact git commit hash with full tests if runtime content/dependency identity is identical, but current CI requirements remain separate.

## Blocking and stop policy

A failed speculative strategy is locally rejected and another eligible strategy can proceed. Absence of Opus is recorded, not silently replaced under the same label. A true physics/tolerance/durability/remote-action boundary creates `DESIGN_EXCEPTION.md`; affected work stops, independent authorized work continues.

When selected small checks and the final allowed campaign finish, deliver the branch, full scope and measured result or blocker. Do not implement every idea after the objective is met. Do not call source inspection a benchmark, synthetic algebra an actual-kernel pass, or one batch a reliability distribution.
