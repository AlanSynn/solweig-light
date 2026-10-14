# Integration branch, baseline and CI

## Important source fact (updated 2026-10-13)
Main reviewed at b3e5ca59a1080f02eda5ccda5e35a66af07e4bfa already contains the closed v5-N9 campaign line, the bounded Numba longwave default, A-plus decode and the development/ reorganization; the raw campaign evidence was archived to Dropbox (`Alan Synn/Research/solweig-light`). The historical campaign branches `perf/native-optimization`, `perf/cpu-optimization` and `handover/campaign-line` were archived and then deleted. NEVER merge, rebase onto or recreate them; their results are historical provenance, not work bases. Main is READ-ONLY during this task.

Create a NEW LOCAL integration branch `perf/s10-semantic-systems` at current main. If a branch with that name already exists, audit its content first and preserve any unique work; do not discard it.

1. Record `git status --porcelain`, current branch/HEAD and refs. Preserve dirty/untracked user files. Use a worktree for a dirty checkout. Never reset, clean, rebase or force checkout.
2. Recheck actual HEAD against the packet pin (START_HERE.txt); record source drift as evidence, do not force the old pin.
3. If main has advanced since the pin, re-pin the branch baseline to the rechecked main HEAD and note the drift in the preflight record.
4. Freeze A as the current-main active source; old campaign-branch results are historical, never current A.

Workers use detached worktrees created from explicit integrator-approved SHA. Do not trust default Claude worktree base or start from stale default branch. Only integrator commits shared driver/API/packaging/identity changes to integration. No force push, automatic push, PR, main merge or release.

## CI
Local targeted tests during development. Do not create repeated PRs or push every experiment. Run installed-wheel gates after packaging settles, current mandatory smoke near final integration, not the entire retained historical matrix every commit. Optional workflow changes are unnecessary; don't use skip-ci to falsify required checks or disable branch protections. Required final checks unavailable remain unavailable. Superseded optional jobs may use existing authorized cancellation, never fabricate success.

Final MERGE_MANIFEST must name actual source and target SHAs and a disposable merge rehearsal result. Target-main drift after validation requires a dependency-aware reevaluation. This packet does not execute merge approval.
