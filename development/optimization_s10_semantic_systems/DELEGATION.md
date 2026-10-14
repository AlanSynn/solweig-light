# Claude Code delegation and parallel execution

GLM-5.3 coordinator owns execution DAG, integration and finite closure. Actual available Opus can implement hard numerical/system work and independently review another author's changes. No mandatory Astra call exists. General debugging and safe local retries are delegated, not escalated.

## Roles and scope
- numerics: typed U path, finite-state expression and exact reductions;
- systems: memory, hashing, persistence, scheduling;
- fixture engineer: independent main/upstream traces, adversarial inputs and installed paths;
- proof/reviewer: typed equivalence, counterexamples, raw evidence and failure boundaries;
- optional accelerator specialist: at most one measured eligible region;
- performance owner: exclusive target host resource lease;
- integrator: shared engine/pipeline/API/identity/packaging and branch state.

No artificial total model-token or reasoning-agent cap. This is NOT unlimited local CPU/RAM/I/O/GPU. Local execution uses resource admission. Compilers/tests cannot overlap an exclusive performance trial. Reasoning/review may run remotely in parallel. One writer owns each code scope; alternatives live on detached worktrees. Cross-cutting edits are patch proposals to integrator, never concurrent writes to its file.

No uncontrolled recursive agent spawning. Coordinator may create more bounded jobs if independent, but must have a DAG node, ownership and expected deliverable. Prefer existing roles over dozens of one-off managers. Fixed source SHA plus one dossier and evidence pointers are enough; do not give every worker the entire chat or all historical packets.

## Progress without polling
Workers execute implement -> relevant tests -> inspect failure -> repair -> retest -> concise completion/blocker. Use supported completion events or blocking waits. No repeated 'are you done' calls, full transcript rereads or duplicated lead implementation. A watchdog for an actually hung subprocess is an engineering control, not model polling; use a predeclared heartbeat/timeout policy and preserve logs.

Default worker completion report: task/base/result commit, changed files, executed commands, exact outcomes, evidence paths/hashes, measured vs assumed numbers, unresolved conditions, next ready dependency. Narrative ideally <=500 words; detailed evidence goes to files. No proof or failure information is discarded merely to meet a word target.

Reviewer != author. Reviewer checks immutable diff, proof obligations, raw results, source provenance and admitted domain. Reexecute only missing/suspicious/critical evidence; do not repeat every successful suite. Only integrator updates canonical task/decision state. Agent memory is nonauthoritative; repository evidence wins.

## Authorization
Autonomous local edits/tests/compiler use in project-owned scratch are allowed. No global provider/credential changes, paid services, hidden data uploads, deployment, destructive user-work cleanup or remote publication. New scientific or operational-contract changes need explicit approval; affected work pauses, independent tasks continue. Failed ideas are rejected, not used to enlarge scope indefinitely.
