# Predetermined merge source, target and cleanup rules

## Branches and exact artifact

Source: `perf/native-optimization`. Target: `main`. Observed tips: 7abe526aae2f97e689b1a1e4ae183e5370f29aa1 and 14e888760727583ef782a4dc0e7a5c7c6e6ff9d1. Continue the same source branch with forward commits. Do not rewrite history, silently cherry-pick an assumed dependency subset, reset the endpoint or modify main. Final qualified SHA cannot be known before implementation; the final record MUST name it, its tree and source digest. Never reuse 7abe526a as a final approval for changes not yet made.

## Inventory before cleanup

Enumerate `git diff --name-status <pinned-main> <candidate>` locally. Classify every changed production path into active validated improvement, required dependency, public compatibility, dormant research, evidence/test, build/CI, unrelated user change. A commit title or test count is not proof of an active speedup. The current N8 decision explicitly says B is not default-integrated.

Candidate retained groups, subject to actual dependency and test review:

- Previous accepted exact geometry/shadow, shared geometry recipe/cache identities, chronology/state and streaming changes.
- Accepted demand-specific shortwave/longwave and GVF changes, and exact R04/G06 preparation where they are actually active and validated.
- Persistent worker/phase scheduling and memory boundaries with matching correctness/admission evidence.
- Main-compatible APIs, CLI, seven workflows, companion ownership and retained failure/recovery semantics.
- Any N9 mode-specialized producer that genuinely improves the shipped Numba/default path.

Do not assert every historic change in these groups is automatically merge-safe. Identify dependencies, default activation and evidence on the selected final source. Record unresolved regressions honestly.

## Native wins

Ship only the selected implementation, minimal private plan/loader/selection mechanism, qualified immutable artifact, necessary runtime dependencies and exact regression tests. Normal loading must work outside a repository, without `experiments`, `sys.path` mutation, source compiler, network, writeable package directory or extra user configuration. Do not ship maintainer verification/build programs as runtime dependencies just because the old empty registry made them unreachable. A candidate generation in a wheel with empty qualification is not a default-native product.

Keep architecture-specific eligibility conservative and fallback functional. Record unsupported OS/ISA/dependency combinations as CPU fallback, not native passed. Maintain the established explicit B7 expert interface or fully replace it with tested documented equivalence. No surprise removal of an already offered override.

## Native loses or qualification remains unavailable

Default is the best VERIFIED CPU/Numba route. Do not ship the N8 no-op selector merely to demonstrate effort invested in native. Remove/disable its call seam in `radiation/cylinder_longwave.py` and remove `_lw_dispatch` / private N8 production dependencies from the install closure when unused. Restore the established boolean semantics where N8 introduced tri-state solely to reach a rejected route, after exact surface tests. Do not delete useful earlier demand-specific radiation code.

Move useful N8 research sources and their versioned tests to an explicit non-installed research location, or retain their immutable historical source/reproduction manifest. Do not discard failing fixtures. Policy tests whose feature was intentionally removed are dispositioned as archived-feature tests, not weakened or marked passed; safety tests for the retained product remain active. Remove native build toggles/package data/default-runtime imports that are unreachable in the selected product. Retain prior explicit B7 expert behavior separately if it is part of the branch's agreed compatibility contract; this path does not justify default native claims.

Preserve raw evidence and history. Do not bulk-delete the user's worktrees or untracked files. Large historical experiment folders need not be rewritten to improve runtime; exclude them from wheel/sdist where appropriate and link compact release notes to immutable research evidence. Native non-selection becomes `not_selected_for_this_release` and the user-requested final campaign ends.

## Merge safety and comparison

Build the final artifact once after source settles. In a clean environment outside the repo, run original main-compatible no-env API and CLI, read-only site-packages and absent-native behavior, full small chronology and all changed-state checks. Native success additionally needs actual native entry/coverage; fallback cannot satisfy it. Review the full main delta's optional workflow and companion collision coverage without automatically rerunning every historical suite. Reuse evidence only when the relevant dependency closure is unchanged.

Compare final default with pinned main on a compact same-budget cold/warm selection. This comparison is distinct from A8/B/C. If final loses or breaks main behavior, remove the offending delta; if no safe useful tree remains, recommend no merge. Do not force a performance claim simply because previous packages were completed.

## Rehearsal and authorization

Create a disposable detached worktree at pinned main for a merge rehearsal. For a squash rehearsal use `git merge --squash <final-source-sha>` and inspect the resulting index/tree; for a merge-commit rehearsal use `--no-ff --no-commit`. `--no-commit` alone does not prevent fast-forward ref movement, so never use it as a safety guarantee on the real main checkout. No hook bypass. Conflicts are handled and affected tests re-run on the actual merged tree, not only the branch tip. If unrelated main changes exist, distinguish branch tree from merged tree and pin both.

The final manifest must enumerate included/excluded production paths, disposition reasons, retained research references, default backend map, actual binary and source hashes, test commands and outstanding platform/release gates. Set `ready_for_merge` only after required safety gates; remote checks not executed are `not_run`, not passed. Do not auto-create a PR, push, merge main or release. A later authorized squash merge is recommended to keep main reviewable while this branch preserves research history.
