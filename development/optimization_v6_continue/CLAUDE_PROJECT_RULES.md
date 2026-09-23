# SOLWEIG CPU continuation rules

Continue on **perf/claude-glm53-cpu-v5**. Do not create/switch a named optimization branch or merge/push/PR/release. One integrator owns this branch and shared dispatch. Isolated workers use detached worktrees at a verified SHA; preserve user changes.

Follow optimization_v6_continue/DESIGN_AUTHORITY.md and PLAN.md. These replace old instructions to create a fresh v5 worktree, call Astra, or run 1024 after each milestone. Read only assigned dossiers; do not bulk-load the historical catalog/evidence.

Keep model/API/artifact/state, typed math, exact guards and recovery guarantees. Existing fast paths stay; rejected P01 stays off. Default own-met remains CPU-only. Never create candidate-derived upstream goldens or relax a failing gate.

Actual GLM/Opus routes must be recorded; alias names are not provider proof. Delegate independent work without artificial token/agent-count caps, but bound local CPU/RAM/disk and use one benchmark lease. Do not poll workers for progress; use completion/blocker events and supported waits. Tests and resource monitoring are not forbidden polling.

Small kernels and small real TIFF/full chronology during development. Actual 24 spatial tiles only at final freeze. Two 1024 scenes × 24 timesteps is not the original batch target. Numerical evidence and throughput claims stay source/configuration-bound.

Implement, run, inspect, fix, retest and review without routine approval requests. Do not stop at import/compile success. Do not mark hypotheses or unavailable work complete. Full details and reproducible commands live in files.
