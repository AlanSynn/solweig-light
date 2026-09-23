# Execute SOLWEIG-light optimization in Claude Code, with GLM-5.3 and real Opus

You are the implementation coordinator in Claude Code. Use the existing authenticated GLM-5.3 route for orchestration and ordinary implementation. Delegate difficult numerical implementation/proof work and independent review to actual Anthropic Opus where the environment genuinely provides it. The architecture and optimization hypotheses have already been developed in this chat and are supplied in `optimization_v5_claude/`. Do not recreate a broad design project, require an Astra/Codex session or call OpenAI as a planning/review fallback.

Read applicable repository instructions and `optimization_v5_claude/DESIGN_AUTHORITY.md`, `PLAN.md`, `MODEL_ROUTING.md`, `VALIDATION_POLICY.md`, and `TASKS_CLAUDE.yaml` before changing code. Use `IMPLEMENTATION_BLUEPRINT.md` and the relevant family dossier for concrete recipes. The 56-entry technical inventory is a menu, not a mandate to implement all entries. Keep historical work/evidence; do not restart completed P0-P6.

The historical inspected optimization checkpoint is `AlanSynn/solweig-light@14e888760727583ef782a4dc0e7a5c7c6e6ff9d1`; model/API ancestry is `nvnsudharsan/SOLWEIG-GPU@0d7fe742abeeddd890dd58fc76ed7f78bd47faec`. Use actual current intended HEAD and reconcile relevant differences. Never reset, stash or discard user changes automatically. Preserve uncommitted dependencies explicitly or block only that scope.

## Setup and agent route integrity

Create a separate local integration worktree/branch `perf/claude-glm53-cpu-v5` or a safe unique suffix. No main edits, automatic push, PR, merge, auto-merge or release. Each writer receives a worktree from an explicitly recorded integration SHA. Native Claude worktrees may otherwise branch from the default branch; set supported `worktree.baseRef=head` or create them with Git and verify HEAD. Nonsecret task/rule files must exist in the child worktree.

Inspect Claude Code version and supported flags once. Z.ai's `opus` alias may be mapped to GLM; that is not an Opus backend. Prefer two existing authorized profiles: GLM coordinator/children on Z.ai, actual Opus sessions on Anthropic. Same-session mixed routing is allowed only through an already verified multi-provider route. Do not invent per-agent provider fields, create a gateway, alter global auth, copy credentials, buy services or claim a backend based on the model's self-description. Record requested/resolved route, tool support and effort evidence. If actual Opus is unavailable, label independent GLM review honestly and keep other work moving.

## Parallelism and autonomy

No artificial token budget, total-agent limit or fixed four-agent cap applies. Use high/max effort where supported and useful. Dispatch all dependency-ready independent proof, counterexample, implementation and review tasks that fit actual client/provider and machine capacity. Do not use extra agents for duplicated scans or status checks.

One writer per scope; shared `engine.py`, `pipeline.py`, API/config/schema and central ledger belong to the integrator. Distinct alternate implementations require separate worktrees/new modules. Opus can implement difficult code as well as review, but a patch's final reviewer must be independent of its author. Authorized managers can split disjoint subtasks when supported; no uncontrolled recursive full-project delegation.

Model inference parallelism is separate from native validation/benchmark parallelism. All local builds/tests reserve CPU/RAM/IO centrally. The measurement owner holds an exclusive host lease; other local tests/builds/profilers/compression stop during timing. Do not let unlimited inference create a RAM or thermal bottleneck on the benchmark host.

Proceed through implementation -> selected tests -> result inspection -> repair -> independent review -> integration without intermediate approval requests. Do not poll agents, replay full transcripts or keep asking whether a task finished. Use actual completion events, supported blocking waits or process-exit notification. Record resumable client partial results as partial, then continue them from files. Return a compact design exception only for a genuine model/tolerance/durability/authorization boundary; suspend that path and continue other useful work.

## Numerical invariants

Preserve all seven workflows, public Python argument semantics, legacy CLI, TIFF inputs, legacy output schemas and explicit compatibility distribution without collisions. Own-met core stays NumPy/Numba/SciPy and Torch/CUDA-free. Keep optional acquisition/forcing dependencies optional.

No fewer patches/pixels/timesteps, isotropic substitute, surrogate, approximate angle bins, truncated physical support, changed vegetation/material/wind/UHI/WBGT policies, hidden constant changes or weakened output/durability. Keep `fastmath=False`, original typed intermediate rounding and existing explicit FMA. Preserve first-step rules, outside-slice sample history, global bush conditions, all three visibility values including possible 2, wall quantities, state and neighbor barriers. Unsupported profiles retain the existing path.

Prioritize the supplied recipes:
1. SVF non-first-step absorbing-state termination, then separate suffix/state-projection/parallel changes.
2. Ordered pixel SIMD, fused visibility consumption, exact categorical expression preparation, exact geometry-only tangent reuse.
3. GVF source lifetime and first/later water snapshots, gather/postprocess fusion, then proved blocker-prefix/repeated-add and static subfield reuse.
4. Stage-liveness memory admission and bounded persistent workers with per-tile cleanup.
Activate second-wave catalog strategies only from measured small-workload residuals/censuses. Rejected speculative variants are valid outcomes; do not weaken a proof to retain them.

Never regenerate original goldens from candidate code. Separate original, patched original, frozen-current baseline, abstract checks and candidate evidence. Preserve frozen numerical/metadata/state comparison gates and approved inherited scientific-failure dispositions. Do not loosen tolerance, hide a failing fixture with skip, redefine the workload after failure or call unavailable hardware passed.

## Keep validation lean

Workers use L0 tiny math/guard checks; L1 actual-kernel differential usually 16-128 square; L2 real 64-128-square TIFF with full 24/48-step chronology and 153 patches. Use the minimum supported fixture and selective adversarial branches. Tests run after coherent behavior changes, not every edit/commit/status update. Reuse exact source/dependency/environment/fixture/reference/harness evidence. Rebuild a stable wheel once or when packaging actually changes. Review does not blindly repeat all worker commands.

Only the lab performs L3: 128/256 square and 2-4 small tiles, compact predeclared resource tuples, at most two shortlisted runtime variants per family. More agents may propose alternatives but do not expand the trial matrix automatically. A justified 512 probe is exceptional. No ordinary 1024 development, warmup or per-worker admission.

After final combined source/wheel/profile/environment freeze, perform the primary actual 24 x 1024-square batch once, 24 steps, 153 patches, unchanged outputs/checkpoint/physical context. Include startup/JIT, necessary geometry, I/O and publication. Existing large reference is reused; new full baseline defaults to zero. If a necessary final numerical reference is missing, one justified final capture is permitted or declare that parity scope unverified. One corrective final retry is allowed only after a retained failed/censored run, a real fix, small regression checks and refreeze. No automatic five-pair matrix or repeated large campaign.

The absolute objective is <=1800 seconds, with modeled design margin 1200-1380 seconds. Models are not measured speedups. Count overlapping savings once, evaluate throughput under fixed CPU/RAM, and keep source-bound raw observations. A single full pass is `target_demonstrated_once`, not robust reliability, a matched upstream speedup distribution or P7/P8 release completion.

## Deliver, do not stop at a prototype

Keep task/evidence records current at coherent milestones. No function stubs to satisfy imports. Do not stop at a decorator, compile pass or one unit test. End with the best independently reviewed optimization branch, executed/reused/deferred/failed test inventory, real route usage, actual final observation or blocker, resource results, reproducible commands and merge-review notes. Do not run the whole historical release matrix merely to finish this branch. Stop before remote push/PR/main merge; the user will request that later.
