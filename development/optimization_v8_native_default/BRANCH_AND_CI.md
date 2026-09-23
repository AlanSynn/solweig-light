# Same branch, local work, no publication

Only named integration branch: `perf/native-optimization`. Do not resurrect older perf/cpu-optimization or perf/claude-* goals. Verify actual worktree branch and HEAD; never reset to a documented SHA. Record dirty paths and avoid them unless owned by this task. No automatic stash, force cleanup, reset, rebase or main edits.

Detached worktrees at explicit immutable commits are allowed for parallel implementation/review. They must start at the integrator's nominated base, not whatever default branch Claude auto-worktree chooses. Return patches or commits from detached worktrees. Only integrator updates the named branch. No two agents edit shared dispatch/API/packaging/state files simultaneously. Use `git add -- <owned paths>` rather than `git add .`.

No push, PR, merge to main, release, package upload or automatic hosted CI. Preserve existing CI settings. Prepare manual wheel recipes/config where necessary, but do not add per-commit heavy native platform matrices. Do not use skip markers or relaxed checks to fabricate a green merge condition. Later publication requires then-current required checks.

Local installed-wheel tests are mandatory for default-readiness, even when hosted CI is avoided. A native wheel that was not executed on its platform stays unverified. Keep release build environment and publishing credentials separate; this task needs no credentials.

Tool defaults are read-only/dry-run. `prepare_worker.py --apply` creates only a new detached worktree, never a branch. `install_assets.py --apply` appends a short CLAUDE import and new task agent files; it refuses nonidentical existing agent files and symlink paths. It does not commit or modify provider permissions.

Temporary test directories created by tests may be cleaned by those tests. Do not delete incomplete user output transactions to force a rerun; reproduce the failure in an owned copy and use existing documented recovery. Retain failed logs and resource events.
