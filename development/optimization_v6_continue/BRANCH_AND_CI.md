# Same branch, isolated workers, no CI churn

## Only one named integration branch

The user explicitly requires `perf/claude-glm53-cpu-v5`. This overrides the old packet's new-branch setup. Find the EXISTING worktree via read-only `git worktree list --porcelain`. Record HEAD/status before changing code. If the worktree is not present, locate the existing branch and safely open it without inventing another named branch, or ask only when no safe local target exists. Do not force-checkout a branch already checked out elsewhere.

The packet's branch_guard tool is read-only and refuses an incorrect integration branch; it never repairs a mismatch by moving refs. A newer actual HEAD is not an error to solve by reset. Identify relevant diffs and protect dirty/user-owned paths. Do not auto stash, clean, reset, rebase, pull, push or remove worktrees.

## Detached worker isolation

For a recorded immutable base SHA, an authorized example is:

    git -C "$REPO" worktree add --detach "$WORKER_PATH" "$BASE_SHA"

No `-b`, no `-B`, no `--force`. Do not rely on Claude's automatic `isolation: worktree` starting from the current integration HEAD; documented defaults can start from the default branch. Verify the worker's detached HEAD, source hash and intended base BEFORE implementation. The named v5 branch remains checked out only by the integrator.

Workers may produce a scope-limited patch plus base/candidate hashes or a local detached commit. Only the integrator applies/cherry-picks accepted deltas to the named v5 branch. A worker's snapshot must contain any newly committed prerequisites; otherwise schedule it from the new immutable base. Do not blindly copy files from historical throwaway worktrees, including previous diagnostic no-fused variants.

No named v6 branch is necessary. Read-only review sessions may share immutable worktrees; writable sessions need exclusive paths or isolation. Do not run tests against a source tree another agent is editing.

## Integration discipline

Only integrator edits central engine/pipeline/API dispatch, identities/schema policy and status. Family workers create private modules/tests and provide a precise interface patch recipe. Shared interface changes are applied in dependency order. Commit only reviewed paths; never `git add .` across unknown user changes. A merge conflict requires source reinspection and affected small tests, not choosing an entire worker file over newer work.

After each accepted integration, record the resulting source/tree hash and patch-to-test dependency map. Append claims/evidence; leave old manifests unchanged. Final handover includes branch/base/tip and exactly which commits remain unmerged.

## CI and publication

Local work by default: no push, PR or workflow dispatch means no new hosted CI runs from this work. Do not change workflow YAML or branch protection just to avoid overhead. Keep the actual small CPU-only TIFF PR test and required checks intact. Avoid `[skip ci]` as the default mechanism; skipped required workflows can leave pending merge checks. The current task does not create a PR or merge anything, so that workaround is unnecessary.

Later, when the user requests push/PR/merge, run then-required checks on the then-current dependency state. Reuse eligible local evidence, but never report a skipped check as passed. Large benchmarks and broad platforms remain separately scheduled qualification, not a mandatory response to every commit.

## Cleanup

Workers close all maps, datasets, child processes and leases. Remove only clean, task-owned throwaway worktrees after results are integrated and evidence paths are safe. Never force-remove a dirty worker or delete references/original fixtures to reclaim disk. Keep cleanup explicit in the terminal record.
