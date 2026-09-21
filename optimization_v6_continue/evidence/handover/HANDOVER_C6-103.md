# C6-103: same-branch unmerged handover

Date: 2026-09-21. Role: integrator. Dossier: optimization_v6_continue/
BRANCH_AND_CI.md. This is the terminal record of the v6 continuation
(C6-00 → C6-103). No push, no PR, no merge to main, no release was
performed or is authorized by this record.

## Branch state

| item | value |
|---|---|
| branch | `perf/claude-glm53-cpu-v5` (the ONLY named integration branch; unchanged) |
| integration worktree | `/Users/alansynn/Workspace/solweig-light-claude-v5` |
| tip at handover | `98545430` |
| main tip (merge-base) | `14e88876` — the branch is strictly ahead of main; ALL 83 commits are unmerged local work |
| v6 range | `8e0b3877..98545430` = 21 integrator commits (wave-1 landings + C6-70 a–k + C6-40 + C6-80/81 + C6-99/100/102 records) |
| src delta vs v6 base | 10 files, +1173/−86 (C6-99 surface confirmation, audit-recomputed) |
| known checkpoint | `e7a2d6ec` — never reset; intact in history |
| freeze | source frozen at `ea2eed53` (C6-100); only evidence commits after |

## What the branch contains (measured, reviewed)

1. **Wave-1 specialist modules, all reviewed and landed**: shared geometry
   recipe/key (C6-10), anisotropic Lside demand dispatch (C6-20), cylinder
   longwave by_demand (C6-21), cylinder shortwave scratch (C6-22), prepared
   GVF step (C6-30) + typed block postprocess (C6-31), prepared visibility
   decoder (C6-50), phase-aware memory admission (C6-42), geometry phase
   adapter (C6-40). Every landing has an independent review record; the two
   APPROVE-WITH-CONDITIONS verdicts (C6-70, C6-40) have their conditions
   closed on the branch (db5928fe, 3f3e8b8d).
2. **Measured scoped gains** (dev-tier single-lease, 64/64 runs, host NOT
   quiet — evidence/portfolio/): cold −6.4/−9.8% (S1), −6.1/−16.2% (T2),
   −10.9% (P2 at 256²); warm steady state a wash; geometry cold-duplicate
   eliminated (cache census 4→2); outputs bitwise-identical across trees in
   every run. L2 chronology differential GREEN at threads=1 and threads=2.
3. **Measured rejections kept OFF**: fused radiation (v5, unchanged);
   prepared visibility decoder DEFAULT route (C6-81: +21–24% per full-frame
   sweep at all four cells → opt-in `SOLWEIG_LIGHT_PREPARED_VIS=1`,
   fallback byte-identical originals; review APPROVE).
4. **Corrected measurement scope** (append-only): 598.9s = two spatial
   scenes × 24 timesteps, never 24 spatial tiles; all v6 numbers carry
   tier labels. C6-90..94: zero selected — no measured activation case
   (evidence/selection/C6-81_selection.md).

## Verification gates on record

- Combined v6 suite 560/560 (`PYTHONPATH=src NUMBA_NUM_THREADS=2`, single
  process) — reviewer- and auditor-measured.
- Wheel gate PASS: wheel built from the frozen tree, installed in a fresh
  venv, imported without src on the path, full public entry bitwise
  identical wheel vs src (10/10 output TIFFs) — evidence/freeze/.
- Independent audit CLEAN-WITH-NOTES (4 info notes; no verdict changes) —
  evidence/final_review/C6-102_audit.md.

## Remaining gaps / limitations (all recorded, none hidden)

1. **C6-101 campaign UNVERIFIED**: the actual 24-spatial-tile workload
   dataset is still absent. The freeze record states what the single ≤1800s
   campaign would run when the dataset exists. No actual-target or release
   timing claim exists anywhere on the branch.
2. **raw-True differential case**: fails at HEAD under host memory pressure
   (availability-sensitive default budget × C6-42's review-adopted stricter
   admission boundary, rejection pre-spawn); base passes; the numerical
   scenario is proven bitwise by the wheel gate. Standing known items in
   evidence/freeze/C6-100_integrator_dispositions.md — including the
   candidate future fix: pin `memory_budget_bytes` in the test (small
   reviewed commit + re-freeze).
3. **Phase route at 128² is net negative** (spawn+barrier overhead); pays
   at 256². Gate unchanged (user opt-in via workers>1); no shape-threshold
   tuning on dev-tier noise.
4. **All timings are dev-tier single-lease observations** on a host with
   unrelated OS/browser load (loadavg median 11.2). Nothing here is a
   statistical or release claim.
5. Four audit info notes (wording/rounding/host-sizing assumptions) —
   evidence/final_review/C6-102_audit.md.

## Worktrees at handover (explicit cleanup record)

- REMOVED (clean, task-owned, evidence integrated): `solweig-light-v6-base-l2`
  (detached 8e0b3877), `solweig-light-v6-rev642` (detached 4c595ad8).
- KEPT — 20 detached v6 worker/reviewer worktrees (`v6-recipe`,
  `v6-lside`, `v6-cyllw`, `v6-cylsw`, `v6-gvfprep`, `v6-gvfpost`,
  `v6-decoder`, `v6-memadm`, `v6-phases`, `v6-census`, `v6-measure`,
  `v6-mem`, `v6-rev603/610/620/621/622/630/631/650`) each holding only
  UNTRACKED worker-owned copies of module/tests/evidence whose landed
  content was hash-verified at integration. BRANCH_AND_CI.md forbids
  force-removing dirty workers, so removal is left to the user, e.g.:
  `git worktree remove --force <path>` for each, or
  `git worktree list | grep v6-` to review first. Nothing in them is
  needed to continue work on the branch.
- The four `v5-*` worktrees/branches predate this task and were not touched.

## How to resume / verify

```
cd /Users/alansynn/Workspace/solweig-light-claude-v5
git rev-parse HEAD                      # expect 98545430…
PYTHONPATH=src NUMBA_NUM_THREADS=2 /Users/alansynn/Workspace/solweig-light/.venv-light/bin/python \
  -m pytest tests/optimization_v6/{gvf_prepare,gvf_postprocess,decoder,cylinder_lw,cylinder_sw,lside,geometry_recipe,memory,phases} -q
# expect 560 passed
```

Tests require `PYTHONPATH=src` (no editable install in this worktree).
The combined invocation REQUIRES the `NUMBA_NUM_THREADS=2` shell cap;
without it, per-family thread-cap setdefaults race numba's launched-threads
revalidation (~97 env-order failures, not numerical).

When the user later requests push/PR: run then-required checks on the
then-current dependency state; never report a skipped check as passed
(BRANCH_AND_CI.md § CI and publication).
