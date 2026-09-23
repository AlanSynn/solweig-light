# Same branch, isolated workers, no CI expansion

Required integration branch: `perf/cpu-optimization`.
Historical review SHA: `4689421c81a9dc9ad5e047bd7ff1dcdd704483b9`.
Branch rechecked for this packet: `7a37a6f59924aa4c13444c977991d7f731ba5e8e`.
These are provenance anchors, not reset targets. Record local HEAD and existing dirty paths. Find the existing worktree on the required branch; do not change an unrelated checkout or create a similarly named branch. If no such local worktree exists, report the actual setup blocker rather than silently checking out main.

Read-only inspection and local commits on the existing branch are authorized. Only the integrator commits; detached worker worktrees at an explicit reachable immutable base are allowed. `git worktree add --detach <new-empty-path> <base-sha>` creates no new integration branch [G01]. Do not use automatic worktree defaults without confirming the exact base. Do not force-remove dirty worktrees or use reset/clean/stash/rebase to discard user work.

No automatic push, PR, merge to main, auto-merge, release or hosted workflow_dispatch. Earlier permission to rename/push a branch does not authorize new pushes. The newest checked tip includes slim-CI maintenance; preserve it. No full platform/framework matrix is added. Do not use [skip ci], disable protection or fake passed checks. On a later user-authorized publication, run only then-required checks for the actual source/configuration.

Experimental dependency environments and build caches are private to the task. Never upgrade the oracle environment or global Homebrew/ICD/driver settings. Installing a pinned wheel/compiler into an isolated user directory is allowed when it needs no elevated permissions; supply-chain provenance and package licenses go in the capability record. A driver/backend requiring privileged changes is marked unavailable for this run.

End with same-branch commit list, source/ABI/compiler fingerprints, evidence paths and unmet gates. Do not claim a merge or CI run that was not executed.
