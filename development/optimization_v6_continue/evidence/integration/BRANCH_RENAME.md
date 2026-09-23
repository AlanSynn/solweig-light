# Branch rename: perf/claude-glm53-cpu-v5 → perf/cpu-optimization

Date: 2026-09-21. Operator: integrator. Authorization: EXPLICIT USER
INSTRUCTION, 2026-09-21 ("현재 v6도 브랜치 이름을 perf/cpu-optimization 이라고
하면서 원래 있던 브랜치 이름 변경하면서 푸할 것" — rename the existing branch
to perf/cpu-optimization and push). This is the sole authorization for the
push; the standing default (no push/PR/merge/release without request)
otherwise remains.

## Operation record

| step | command | result |
|---|---|---|
| 1 | `git branch -m perf/claude-glm53-cpu-v5 perf/cpu-optimization` | local branch renamed; tip UNCHANGED at `30624e02` (rename moves no commits) |
| 2 | this record + ledger row, committed on perf/cpu-optimization | included in the push |
| 3 | `git push -u origin perf/cpu-optimization` | see push receipt below |
| 4 | `git push origin --delete perf/claude-glm53-cpu-v5` | see push receipt below |

## Invariants

- Every commit, hash included, is preserved: the rename is a ref move, not a
  rewrite. Tip before rename = tip after rename = `30624e02`.
- Known checkpoint `e7a2d6ec` remains in history, untouched.
- main (`14e88876`, the merge-base) and the four `v5-*` sibling branches are
  untouched. Nothing merged; the branch remains unmerged work.

## CI consequence

`.github/workflows/cpu-reference.yml` triggers on `push` (and
pull_request/workflow_dispatch). Pushing the renamed branch STARTS the CPU
reference workflow on then-current state. Per BRANCH_AND_CI.md § CI and
publication: required checks are read from the actual run on the pushed
state; a skipped check is never reported as passed.

## Push receipt (appended after execution)

```
git push -u origin perf/cpu-optimization
  * [new branch]        perf/cpu-optimization -> perf/cpu-optimization
  branch 'perf/cpu-optimization' set up to track 'origin/perf/cpu-optimization'.
git push origin --delete perf/claude-glm53-cpu-v5
  - [deleted]           perf/claude-glm53-cpu-v5
git ls-remote --heads origin (post-operation)
  14e88876  refs/heads/main
  a90b10aa  refs/heads/perf/cpu-optimization
```

Remote now holds exactly two branches: main and perf/cpu-optimization.
No protection errors; old ref deleted cleanly. CI run started by the push
is observed on GitHub Actions, not pre-claimed here.
