# Fixed design authority and delegated decisions

## Priority and provenance

This continuation supersedes v3-v5 orchestration only where explicitly stated. It preserves current public functions, existing numerical/scientific policy and v4's small-first verification. It is not permission to weaken existing repository safety or user-owned data protections. Source observations refer to the known e7a2d6ec checkpoint; reconcile actual checkout differences locally, without a new research campaign or reset.

The only named integration branch is `perf/claude-glm53-cpu-v5`. A worker may use a detached worktree based on an immutable recorded commit. Only the integrator advances the existing branch. No automatic push, PR, main merge, release, rebase, stash, branch replacement, force checkout or destructive cleanup.

## Fixed decisions

1. Preserve the physical and discrete model: 153 patches in the target, original raster scale/context, every target timestep, vegetation, walls, shortwave and longwave. No surrogate or approximate lookup.
2. Preserve seven public workflows, legacy argument/CLI behavior, compatibility distribution and collision handling. Own-met CPU execution remains Torch/CUDA-free and free of mandatory network/forcing extras.
3. Default new fast paths preserve original typed operations, float32/float64 promotion, patch/ray order, supported failures, signed-zero and nonfinite masks. `fastmath=False`; preserve existing explicit SLEEF FMA, add no new contraction/reassociation.
4. The chronological state transition and neighborhood stage barriers remain sequential. No independent hours, algebraic time scan, smaller model tiles or unsupported halos.
5. Provenance/validation is never replaced by filename existence, mtime, schema alone, or `legacy_cache_policy='trust'`.
6. Public diagnostic/low-level results remain available. A private demand-specific path may omit only operations proved outside artifacts, state, future neighbor reads, public results and externally required failure/warning semantics. Return missing diagnostics explicitly, not fake zeros/stubs.
7. Preserve R01a, accepted G02/G03, persistent pool and S07. Their existence is not their current performance proof. Preserve rejected fused radiation OFF by default; a materially different candidate needs separate tests/evidence.
8. Correct the spatial denominator. TWO 1024 scenes with 24 bands each are not 24 spatial tiles. Old runs remain immutable and retain their actual scope.
9. Correct thread measurement before selecting worker configurations. Record requested, configured and effective native thread masks, code route and admitted workers.
10. First-wave design: common geometry producer/key, private demand-specific radiation, phase-level scheduling with safe publication, measured memory admission, GVF preparation/postprocess and prepared decoder. Each is separately reviewable.
11. The geometry sharing change preserves standalone exports and their ordering/presence semantics. Numerical cache identity and export-operation provenance are distinct objects with complete dependencies.
12. Parallel geometry first precomputes immutable native data while ordered legacy publication remains owned by the existing phase. More concurrency is allowed only after failure/partial-publication semantics are preserved. A stage barrier remains before simulation.
13. No all-workloads speed guarantee. Select strategies using current call counts, service demand, guard coverage and small measured crossovers. Full cold, warm and kernel-only claims remain separate.
14. Unlimited authorized GLM/Opus tokens and inference sessions do not mean unlimited host processes. Cap actual numerical work, queue memory, native threads, disk use and benchmark interference.
15. This chat supplies high-level design. No routine Astra/Codex review stage exists. Claude coordinator and independent numerical reviewers may refine implementation, reject a proof and narrow guards within the contract.
16. Opus is a provider/model identity, not the word `opus` in a config. Record the served model when available. Previous GLM reviews are not retrospectively Opus reviews. Missing Opus blocks only that route; independent GLM review may proceed with an honest label.
17. Development uses tiny kernels and 64/128-square full chronology; 128/256-square small batches for selection. No mandatory per-patch/per-worker 1024 or historical release matrix.
18. Final absolute target requires 24 actual spatial tiles × 24 timesteps at the fixed model and outputs, end-to-end <=1800 seconds. Aim for 1200-1380 in calibrated planning, not an unmeasured claim. Data absent means target unverified, not a repeated easy fixture relabeled as real.
19. One final large candidate campaign by default; one retained-failure/cause/fix/small-retest/refreeze retry. An unavailable numerical reference is not a pass. A single observation is not reliability or P7/P8 completion.
20. Stop optional research when sufficient verified improvement and scoped gates are obtained. Do not build all catalog candidates or an agent platform.

## Permitted local decisions

Choose finite guards, private helper boundaries, block layouts, cache-key schema revisions, exact partial evaluations, source ownership and phase allocation using the supplied design. Add minimal counterexamples and source-bound tests; reuse valid evidence. Resolve ordinary failures without human or Astra approval. A numerical reviewer can falsify this design and reject the affected optimization.

Changes to tolerances, scientific quirks, actual workload, math profile, error/recovery guarantees, remote state or credentials are outside this authority. Record a design exception; retain the baseline path and work on other ready tasks. Request user input only if all productive authorized tasks depend on a genuine missing decision.
