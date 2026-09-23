# F7 merge rehearsal (integrator, 2026-09-23; REDONE at final tip)

Local rehearsal ONLY — no push, no PR, no main merge, no release
(separate authorization required per the FINAL packet directive).

## Topology

- local `main` = 14e888760727583ef782a4dc0e7a5c7c6e6ff9d1 (the reviewed
  main commit; also the pinned F6 reference at
  /Users/alansynn/Workspace/n9-main-ref).
- merge-base(main, perf/native-optimization) = 14e88876: the branch is
  153 commits AHEAD, 0 BEHIND -- a pure fast-forward. No merge commits,
  no conflicts possible.

## Rehearsal (disposable detached worktree /tmp/n9_merge_rehearsal)

    git worktree add --detach /tmp/n9_merge_rehearsal main
    git merge --ff-only 22876fb6
    Fast-forward: 14e88876..22876fb6 -- OK

Final branch tip (includes the two F4 fixups: a7c03171 archived-skip
reasons name the F3 NATIVE_LOSS closure per the release-owner
checklist; 22876fb6 whole-tree collection repair -- archived-dir
conftests carried module-level imports of the removed machinery, and
installed/test_native_wheel_gates.py had the skip above its module
docstring, both aborting `pytest tests/optimization_v8`):

- merged HEAD = 22876fb6 (tip)
- merged tree  = cf94ff9853559ff19a776a58a0314034421af6dc
- branch-tip tree = cf94ff9853559ff19a776a58a0314034421af6dc
  (IDENTICAL -- the merge is bit-for-bit the tested tree)
- post-merge `git status` clean.
- Post-fixup gates: full-tree collection `pytest tests/ --collect-only`
  = 6492 collected, 0 errors except the four PRE-EXISTING
  tests/optional ModuleNotFoundError cases (rasterio-class extras
  absent from this venv); stream+policy+integration re-run
  71 passed / 1 skipped.

## Post-merge smoke (no-env API/CLI probe, rerun at the FINAL tip
22876fb6 in the rehearsal checkout)

- import solweig_light: OK, version 0.1.0.dev0, HEAD 22876fb6853e6cd1
- `solweig_light._native_dispatch.lw_stream` exports exactly:
  InvocationPlan, BorrowedVisibility, BlockSlot, plan_invocation,
  AosoaBStreamConsumer
- `solweig_light._native_dispatch.lw_default_policy`: ABSENT
- `solweig_light._native_dispatch.lw_native_aosoa`: ABSENT
- `solweig_light.radiation._lw_dispatch`: zero `os.environ`/`getenv`
  lines
- `solweig_light.cli.main`: importable, callable

(An identical probe first ran at the pre-fixup tip 2c4ba021; the
fixups touch only test reason strings and conftest collection, so the
API/CLI surface is unchanged. In the first probe the lone regex hit
for "environ" was the English word "environment" in the module
docstring, verified then by grep.)

## Merge instruction for the authorized operator

    git checkout main            # at 14e88876
    git merge --ff-only perf/native-optimization   # -> closing tip (see below)

or, equivalently, `git push origin perf/native-optimization:main`
(ff-only by construction). NOTHING else is required: no conflict
resolution, no follow-up commits.

## Record commits after the rehearsed tip (evidence-only)

After the rehearsal at 22876fb6, three record-only commits landed on
the branch. They touch ONLY evidence, installed-gate tests, and the
final manifests - NO src/ changes:

- ca9a6564 N9 F5 evidence (installed-wheel gates, R1/R2, six-run
  product-run record with the construction-level environmental proof)
- 806d16a8 N9 F6 evidence (run-2 authoritative comparison
  SHIPPED_ROUTE_CONFIRMED; run-1 warm-pass defect invalidated and
  retained; cold ruling superseded by amendment 1 -
  COLD_LIMITATION_WITHDRAWN, cold gate PASS 0.9226 MARGINAL)
- the FINAL_SELECTION.json + MERGE_MANIFEST.json commit (this commit)

## Final rehearsal (re-run at the closing tip; appended below by the
closing record commit)
