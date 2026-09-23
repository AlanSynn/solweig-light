# Branch-local execution and minimal CI

## 1. Branch isolation is mandatory; remote actions are not automatic

Create a local integration branch `perf/lean-cpu-v4` from the actual current HEAD in a separate worktree. If the branch/path exists, use a unique suffix; never use force/reset flags. Preserve the original checkout, staged changes and untracked files. Record base SHA and the treatment of any preexisting user changes. Do not auto-stash, auto-commit or silently exclude essential uncommitted work; when it cannot be resolved from context, keep only that dependency blocked and proceed elsewhere.

Example for a clean committed base, after confirming neither destination exists:

```bash
BASE=$(git rev-parse HEAD)
git worktree add -b perf/lean-cpu-v4 ../solweig-light-perf-v4 "$BASE"
```

Family worktrees branch from the same frozen integration tip, for example `perf/lean-cpu-v4-ray`, `-radiation`, `-gvf`, `-runtime`. Do not check out the same branch in multiple worktrees. The integrator may bring reviewed worker commits into the **optimization branch** using non-destructive cherry-picks or merges. No worker writes main or changes another worker's checkout. [CI04]

Local commits at coherent milestones are allowed; no commit for every edit or status line. Default remote pushes: zero. Default PR creation: zero. Default automatic merges/releases: zero. A request to work on a branch and merge later is not a request to merge now. End with the branch and a merge-review packet.

## 2. Prefer no hosted trigger over trying to skip it afterward

Local-only development is the default way to avoid hosted CI overhead. Do not add a new workflow merely to run checks that already run locally. Do not globally disable Actions, delete numerical tests or weaken protected-branch requirements.

If a later explicit instruction authorizes backup pushes, batch them rather than pushing every worker commit. A draft PR is not a reliable CI suppression mechanism: ordinary `pull_request` triggers may still run. Do not open a draft PR solely as a progress log. Inspect actual repository triggers once before pushing. [CI01]

`[skip ci]` is not the default policy. GitHub documents that skipped path/branch/commit-filtered workflows can leave required checks pending; skip instructions also do not cover every trigger, including `pull_request_target`. Never claim a skipped required check passed or bypass it to merge. [CI02]

## 3. Low-cost PR policy, only when a PR is actually requested

Keep one fast, real CPU-only TIFF-to-TIFF check on the repository's canonical supported Python/OS, plus affected unit/differential/import/schema checks. It must execute real numerical kernels and use a small chronological fixture. Do not automatically add a broad OS/Python matrix, GPU allocation, optional live services or 1024/2048/3600 runs.

For existing non-required expensive jobs, prepare a narrowly scoped diff to make them explicit manual work or a separately requested release campaign. Do not repurpose a required job to produce a success without its promised tests. Any branch-protection change needs a separate user decision; deliver the branch for review if an existing check remains required.

Avoid duplicate push+PR jobs for the same candidate where the actual workflow contracts allow it. Use branch/PR-scoped concurrency to cancel superseded **optional development CI**, not the user's other workflows or final benchmark. Cache dependencies/JIT with exact environment/source keys; do not reuse stale pass results as current hosted checks. Prefer the repo's already approved action pins, not unverified new versions. [CI03]

An existing workflow may use:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true
```

This is a fragment for the integrator to adapt, not an installed workflow. Keep benchmark campaigns on a separate non-canceling group and exclusive host lease. No `pull_request_target` execution of untrusted candidate code, secret elevation, `continue-on-error` masking or forced green gate.

Manual hosted qualification is optional, not mandatory for branch development. GitHub's documented `workflow_dispatch` setup requires the workflow on the default branch; a brand-new branch-only workflow is not assumed dispatchable. Use an already available workflow with an explicit branch ref after authorization, or run the equivalent local commands. Never merge just to make a workflow button appear. [CI05]

## 4. Merge later, on the user's instruction

Produce base/tip/runtime-tree/wheel hashes, reviewed commits, small test evidence, any final target result, deferred release requirements and the prospective CI diff. Do not silently merge or enable auto-merge.

When a later merge request arrives, compare current main and the optimization branch in a disposable integration worktree. Run changed-dependency small checks and required merge checks once. If only commit metadata changed but runtime code/environment/input identities did not, reuse valid large evidence. If runtime dependencies changed, that evidence is invalidated; do not pretend a previous branch run tested the new merge result. No automatic force-push, broad rebase or branch deletion.

## Official sources

- [CI01] GitHub workflow events: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- [CI02] Skipping workflow runs: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/skip-workflow-runs
- [CI03] Workflow concurrency: https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency
- [CI04] Git worktree: https://git-scm.com/docs/git-worktree
- [CI05] Manual workflow runs: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow

CI02, CI03, CI04 and CI05 were checked while preparing this document. Repository workflows/settings have not been changed by this packet.
