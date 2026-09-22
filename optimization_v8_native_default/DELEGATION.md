# GLM coordinator, independent Opus/GLM implementation and review

## Roles, not an artificial worker cap

GLM-5.3 coordinates this plan in Claude Code. Use actual authenticated Opus for numerics, proofs, difficult systems code and review where available; strong GLM workers can implement and independently review too. There is no artificial total-token or total-agent quota. Platform/client limits still apply, and useful parallelism requires independent ownership.

Suggested independent tracks: contract/evidence; loader; direct layout; native region; Numba B; packaging/DX; storage; numerical reviewer. More reviewers can inspect narrow proof obligations without editing code. Do not manufacture activity by splitting every small function into a new session.

Agent templates use `model: inherit` to avoid claiming Opus from a GLM-mapped alias. Route difficult tasks to a verified Opus profile or separate already-authenticated session. Record actual provider/model/effort when available and `unverified` when not. No setup of a new routing gateway, no secret dumping or global config changes. Z.ai can map the `opus` alias to GLM; a name is not evidence of model identity.

## Task packet

Each dispatch includes immutable base SHA; owned files; one expected implementation outcome; relevant dossier and kernel/DX contract links; the exact A/B controls; preconditions and error ownership; allowed local CPU/RAM/build budget; permitted L0-L3 scope; output/evidence paths; independent reviewer role. Whole prior chat and raw archives are not copied. A worker may read more if a dependency requires it, but does not scan every prior packet by default.

## Completion instead of polling

Use available completion events or blocking waits. Coordinator does unrelated dependency-ready work or waits, never repeatedly asks whether a worker is done. Workers finish implementation, relevant tests and repairs before one terminal summary. Real blockers are reported when no safe local path exists; routine bugs are fixed without user confirmation. Large logs go to files; the summary contains changed scope, commands, results, failures, numeric/performance boundary and next task.

## Resource ownership

Model reasoning is independent of local compute limits. A build/test reservation accounts for native compilers, pytest workers, Numba thread pools, GDAL caching and data copies. Benchmark owner has exclusive measured-host execution; other local builds/tests/profile probes stop. Remote read-only reasoning can continue if it creates no work on the timed host. Do not kill user applications to quiet the machine.

Native region scheduler and coding agents are different notions of worker. Unlimited coding agents does not authorize W*H oversubscription or unlimited device-memory queues.

## Integration and review

Each author submits an immutable patch and raw evidence. A different agent reviews arithmetic graph, ownership/ABI, fallback, gates and packaging as appropriate. Evidence review precedes rerunning the same tests. Shared files and policy certificates are integrator-owned. Later edits to reviewed numerical/lifecycle code invalidate that affected review; unrelated docs do not trigger the entire suite.

The coordinator can decide guards, layouts and losing-candidate closure inside DESIGN_AUTHORITY. Only genuine policy exceptions require user decision; they do not pause unrelated safe work. No final return to Astra is required.
