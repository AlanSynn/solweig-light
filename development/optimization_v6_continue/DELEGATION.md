# Delegate implementation, not the scientific contract

## No Astra orchestration dependency

The high-level design is supplied in this packet. GLM-5.3 coordinates actual execution. Real Opus specialists may implement difficult kernels, derive guards, inspect counterexamples and independently review. There is no routine call back to this chat/Codex/Astra. Ordinary implementation or proof failure is handled locally: reject/refine the candidate, preserve fallback and continue.

A policy-level exception is a small written record, not a reason to pause every task. It names the minimal reproducer, forbidden assumption, safe alternative and remaining productive work. Only a genuine global missing decision requires asking the user.

## Unlimited useful inference, finite host resources

No artificial total-token, reasoning-effort or overall agent-count cap. Use as many independent tasks as have a coherent objective and non-overlapping write ownership. Do not spawn duplicates solely to consume availability. Discover actual client/provider capability once; obey rate/context/concurrency limits without retry storms. Verify effort/model semantics in the actual client instead of copying model names from this document.

Distinguish three pools:

1. Inference/reasoning sessions: may scale across providers within practical limits.
2. Local builds/kernel tests: reserve global CPU/RAM/disk; each worker cannot seize all cores.
3. Performance execution: one exclusive owner/lease for the measured host; suspend all competing local numerical/build/profile work. A remote reasoning session is harmless only if it does not issue work on that host.

## Roles

- GLM coordinator: dependency ledger, immutable task packets, ordinary integration decisions.
- Geometry/cache implementer: D02 shared recipe and cold duplication.
- Numerical demand implementer: D03 private radiation profile.
- GVF specialist: D05 exact preparation and postprocess.
- Decoder/storage specialist: D06/D07.
- Runtime specialist: D04 phases, admission and failure frontier.
- Fixture/evidence specialist: D01 and actual source-bound small cases.
- Opus proof specialist: high-risk typed equivalence/alias/exception proofs; may implement a difficult bounded patch but not self-approve.
- Independent reviewer: immutable diff and evidence, counterexample inspection.
- Integrator: only writer to shared dispatch/core schemas and named branch.
- Performance owner: one measurement process and final campaign authority.

These are roles, not a session-count ceiling. A proof-only task, fixture task and disjoint implementation may run simultaneously. Related candidates editing the same module use different detached worktrees. Recursive untracked delegation is not allowed; coordinator registers dependent tasks so ownership and local resources remain bounded.

## Task packets and completion flow

A packet includes task ID, exact base SHA, assigned dossier sections, owned files, private interface, proof/guard requirements, existing reference IDs, permitted validation tier, host resources, expected artifacts and reject/stop rules. Do not send the full chat or entire catalog. Length should follow task need, not an arbitrary token limit; keep repetitive background out.

Worker executes implementation -> affected actual tests -> inspect failure -> fix -> retest -> evidence record. Return one terminal summary on completion or a real blocker. Full logs stay in files. No model-driven `are you done?`, sleep/check loops, replaying all worker transcripts or duplicate implementation by the coordinator. Use native completion events, messages or a supported blocking wait. If no reliable event interface exists, run coarse foreground tasks in their supported tool call; do not build an orchestration daemon.

Operational OS liveness checks, memory monitors and testing assertions are still required. 'No intermediate checks' means no needless manager/user progress polling, not no correctness/resource checks.

The reviewer consumes the immutable patch and existing evidence. Rerun only tests needed for a concern, not the entire family suite automatically. Integrator waits for completed review plus dependencies, applies the patch on the same branch and runs affected small interactions. Source changes rekey the evidence map.

## Provider integrity

Use a real Opus route if configured and verifiable. Last handover reported Opus unavailable; availability is not established by the user's budget permission. If unavailable, record 'independent GLM review; Opus unavailable' and proceed on bounded work. Never claim an Opus review from a Z.ai-remapped alias. Do not expose authentication values or build a provider gateway.

## Work minimization

Do not re-audit every source, rebuild every environment, regenerate every oracle or execute the historical performance matrix. Reuse actual source-bound evidence and focus on current measurable work. Package tooling is optional scaffolding, not a new product to perfect. Stop optional candidate exploration when the scoped objective and independent gates are met.
