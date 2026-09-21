# SOLWEIG-light v6: same-branch Claude Code continuation

This is a detailed implementation handoff, not an optimization release. Continue on the existing integration branch **`perf/claude-glm53-cpu-v5`**. Do not create a new named optimization branch. Production code has not been changed by preparing this packet.

Start by giving `START_HERE.txt` to the already configured GLM-5.3 Claude Code coordinator. `CLAUDE_CODE_EXECUTION_PROMPT.md` is the longer equivalent, not additional mandatory repeated context. The coordinator reads `DESIGN_AUTHORITY.md`, `PLAN.md`, `VALIDATION_POLICY.md`, `DELEGATION.md` and `TASKS_CLAUDE.yaml` once. Workers receive only their dossier, immutable source identity, assigned paths and required tests. The 56-family historical catalog is included under `reference/`; it is not a command to implement everything.

## What changes from v5

* Keep the same branch and all accepted v5 changes. Temporary worker isolation uses explicit detached worktrees at a recorded commit, not native default-branch forks.
* The observed 598.9 seconds covers TWO spatial scenes, each with 24 time steps. It does not establish the 24-spatial-tile target. Do not rewrite old evidence; append a scope correction.
* Recheck effective numerical threads. The previous in-process `RuntimeOptions` sweep does not alone establish 1/2/4-thread scaling.
* First investigate a newly identified cold-path duplication: standalone geometry adds identity fields that the simulation geometry key lacks. The same full workflow can therefore create two native geometry generations for the same calculation. Share a proved common numerical producer and versioned identity rather than trusting legacy exports or deleting validation.
* Prioritize demand-driven anisotropic/cylinder calculations, phase-level tile concurrency, actual GVF expression hoisting, compiled GVF postprocessing and batched prepared decoders. Do not re-enable the measured-rejected fused radiation route merely because it is named fused.
* Combine CRC/schema/value validation into a bounded read pass where possible; preserve every validation and recovery guarantee.
* No Astra/Codex invocation is needed. Unlimited authorized inference is distinct from bounded CPU/RAM/disk consumption. Actual Opus availability must be verified, not assumed from an alias.
* Small-first tests, no development 1024 runs, no automatic push/PR/CI/merge, one final large candidate campaign with at most one causally justified retry.

## Evidence status

Repository source inspected through GitHub at `e7a2d6ec8594b234820e7783e0ca26d821de7f3d` on 2026-09-21. This is a known checkpoint, not an instruction to reset a newer checkout. Original model/API ancestry remains `nvnsudharsan/SOLWEIG-GPU@0d7fe742abeeddd890dd58fc76ed7f78bd47faec`.

`SOURCES.md` and `SOURCE_AUDIT.md` separate source observations, historical reported executions and new hypotheses. The container could not directly download the repository; the inspected source was read through the connector. GDAL is not present in this packet-preparation environment. No SOLWEIG source kernel, target-machine benchmark, numerical oracle or Claude/GLM/Opus session was executed here. Any `evidence/packet_checks.json` or thread probe output is labeled as packet-tool testing only.

## Contents

- `PLAN.md`, `DESIGN_AUTHORITY.md`: fixed design and authorized decision envelope.
- `dossiers/01_...10_...`: concrete implementation, mathematics, guards, fallback and test recipes.
- `VALIDATION_POLICY.md`: low-overhead verification and honest final target conditions.
- `THROUGHPUT.md`: phase model and non-overlapping savings.
- `BRANCH_AND_CI.md`, `DELEGATION.md`, `MODEL_ROUTING.md`: same-branch coordination and provider integrity.
- `agents/`: optional conservative Claude agent templates; do not blindly overwrite existing definitions.
- `tools/`: read-only branch audit, separate-process thread probe, scope validator and hypothetical phase model.
- `templates/`: task packets, proof, evidence and final campaign records.

Run packet-only checks: `python -m unittest discover -s optimization_v6_continue/tests -v`.
This checks the handoff tools, not SOLWEIG. Source-bound implementation tests are specified separately.
