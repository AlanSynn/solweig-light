# Design authority: decisions fixed in this chat, implementation delegated

## Status and precedence

This v5 specification is the user's current implementation direction. It replaces the former requirement that an Astra/Codex session coordinate, approve milestones, or perform final review. It removes the old artificial four-agent/token caps. It preserves v4's small-first validation, final-only large campaign, numerical semantics, separate branch and deferred merge.

Historical reviewed optimization source: `AlanSynn/solweig-light@14e888760727583ef782a4dc0e7a5c7c6e6ff9d1`; model/API ancestry: `nvnsudharsan/SOLWEIG-GPU@0d7fe742abeeddd890dd58fc76ed7f78bd47faec`. Reconcile actual checkout changes narrowly; do not reset a newer branch or claim this historical snapshot is current HEAD without reading it.

No proposed proof is a declaration that production code is universally equivalent. Tests and independent review can falsify or restrict any hypothesis. If a proof is wrong, reject that path and continue with eligible paths; do not preserve a flawed optimization to obey this document.

## Fixed decisions

| ID | Decision | Consequence |
|---|---|---|
| D01 | The existing physical/discrete model remains the default | Keep patch/ray sequence, resolution, timesteps, vegetation, wall quantities, forcing, constants and all required radiation |
| D02 | Machine semantics matter | Preserve typed expression nodes, intermediate rounding, explicit existing FMA, order, masks, mutations and supported errors |
| D03 | CPU-only own-met core | NumPy/Numba/SciPy; no Torch/CUDA or mandatory optional acquisition dependencies |
| D04 | Known public/API/artifact contracts remain | Seven workflows, compatibility distribution and collision prevention, CLI flags and TIFF/ZIP/NPZ schema |
| D05 | Internal execution blocks are not model tiles | Never recompute location/forcing/context at a block center; no invented halo cutoff |
| D06 | Chronology is sequential within a logical simulation | Spatial tasks need immutable input snapshots and stage barriers; do not execute dependent hours independently |
| D07 | Guarded specialization, not approximations | Use the existing path for unsupported dtype/domain/ownership/profile rather than inventing replacement behavior |
| D08 | First portfolio is ray + radiation + GVF + runtime | Prepare alternatives independently; shortlist from small evidence, do not implement all 56 entries |
| D09 | Baselines and goldens stay external to candidate | Untouched original, explicitly patched original, frozen current candidate, abstract checks and new candidate are distinct |
| D10 | Reuse prior qualification by dependency identity | Do not restart P0-P6, rebuild all environments or rerun all historical experiments |
| D11 | Optimize engineering elapsed time too | Coherent patches, selective tests, one lab owner, terminal notifications, no progress polling |
| D12 | No required Astra calls during execution | GLM coordinator and verified Opus review decide inside this authorized envelope |
| D13 | No artificial token/session-total limit | Use max reasoning when useful; practical client/provider limits and marginal utility still apply |
| D14 | Numerical tests/benchmarks have a real resource budget | Unlimited inference concurrency never licenses unlimited local processes, memory or measured-host interference |
| D15 | L4 occurs at final freeze, once by default | No per-agent 1024 admission or automatic large baseline/matrix |
| D16 | Branch-local finish | Reviewed commits go to the optimization branch only; leave main/push/PR/release untouched |
| D17 | No unmeasured speed claim | Hypothetical models rank work; only a completed measured batch can demonstrate the absolute target once |
| D18 | Opus is a served-model assertion, not a role label | Verify route/metadata; a Z.ai-remapped opus alias is not an Anthropic Opus review |
| D19 | Credentials are out of repository/context | Reuse authorized profiles; do not copy tokens into packets, logs, scripts or worktrees |
| D20 | Client scaffolding stays small | Use existing subagents/sessions and explicit worktrees; do not build an orchestration platform or provider gateway |

## Local decision authority

The implementation team is authorized to: choose block shape/layout/serial dispatch thresholds on tuning data; implement the listed exact/guarded variants; split modules behind unchanged APIs; add bounded caches with complete keys; add small counterexample fixtures; adapt compatible CLI/agent configuration; schedule independent tasks; reject an ineffective proposal; and move to the next measured bottleneck. These are not questions for an Astra session.

A verified Opus numerical reviewer may refine a proof or fast-domain guard without changing the model. The coordinator can integrate a reviewed patch after applicable small gates. They may not loosen a numerical tolerance, replace the math profile, change physical semantics, change final workload to hit the deadline, weaken durability, remove scientific failures, change branch protection or publish remotely.

When a policy-level decision truly blocks a path, write `templates/DESIGN_EXCEPTION.md` with one minimal reproducer, the proposed policy change, alternatives still inside scope, and the evidence location. Freeze only the affected path and continue other authorized work. Ask the user only if all useful dependency-ready work is genuinely blocked. A routine implementation bug or test failure is not a policy escalation.

## Priority objective

Minimize time to a verified useful optimization, not token count or number of patches:

    engineering elapsed = setup + critical path(implementation, proof, selected tests, review, integration, measurements)

A huge speculative rewrite with a difficult proof can be worse than two small work-removing transformations. Read-only mathematical review and disjoint code creation can overlap; measurements on one host cannot. The smallest successful portfolio ends the optional research work.

## What is deliberately not frozen here

Stage fractions, ray survival distributions, exact ASVF cardinality, cache working sets, target concurrency scaling and actual speedups are unknown for the executing dataset. They must come from small measurements/counters and final validation, not from the illustrative 400-second decomposition in the throughput model. Do not read assumed improvement factors as implementation requirements already known achievable.
