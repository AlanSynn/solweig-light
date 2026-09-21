# CI push observation: perf/cpu-optimization — RED, runner-side root cause

Date: 2026-09-21. Operator: integrator, duty per BRANCH_AND_CI.md § CI and
publication (never report a skipped or failed check as passed). Trigger:
the user-authorized push of the renamed branch (BRANCH_RENAME.md).

## Runs observed (all `CPU reference`, workflow cpu-reference.yml)

| run | branch | commit | result | duration |
|---|---|---|---|---|
| 35655161445 | perf/cpu-optimization | 4689421c | FAILURE (3/3 jobs) | 6m6s |
| 35655118018 | perf/cpu-optimization | a90b10aa | FAILURE (3/3 jobs) | 4m11s |
| 35590418714 | perf/claude-glm53-cpu-v5 (old name) | e7a2d6ec-era tip | FAILURE | 4m42s |
| 35514184010 | main | 14e88876 | FAILURE | 2m7s |

`gh run list --status success` returns ZERO runs in recent repo history:
CI has been red repo-wide since before any of this branch's pushes.

## Root cause: runner Homebrew drift, NOT branch code

All three jobs fail identically at GDAL import:

```
ImportError: dlopen(.../osgeo/_gdal.cpython-311-darwin.so, 0x0002):
Library not loaded: /opt/homebrew/opt/poppler/lib/libpoppler.163.dylib
  Referenced from: /opt/homebrew/Cellar/gdal/3.13.3/lib/libgdal.39.3.13.3.dylib
  Reason: tried: ... /opt/homebrew/Cellar/poppler/26.09.0/lib/libpoppler.163.dylib
  (no such file)
ModuleNotFoundError: No module named '_gdal'
```

- The workflow pins the GDAL formula (GDAL_FORMULA_COMMIT/SHA256 →
  gdal 3.13.3) but does NOT pin its poppler dependency.
- The macos-15 runner image now ships Homebrew poppler 26.09.0, whose
  lib does not provide `libpoppler.163.dylib`; the pinned gdal 3.13.3
  bottle was linked against a poppler that did. `brew install` of the
  pinned formula resolves poppler to latest → dangling dylib reference.
- Consequence: `osgeo._gdal` cannot load; every test module importing it
  errors at COLLECTION (not assertion). No numerical test ran to
  completion on these runs — these failures carry NO signal about
  branch numerics.
- Identical signature on main (14e88876, 2026-09-20) which predates and
  excludes all 84 branch commits → pre-existing infrastructure failure,
  independent of v6 work.

## Candidate fix (NOT applied; proposed for review)

Mirror the existing GDAL pin for poppler: extract/install the poppler
formula at a commit whose version ships `libpoppler.163.dylib` (the
version the pinned gdal 3.13.3 formula declares), before
`brew install solweig-light/pinned/gdal`, with a SHA256 check —
same pattern as GDAL_FORMULA_COMMIT/GDAL_FORMULA_SHA256. Then re-run
via workflow_dispatch to verify, on then-current branch state.

Not applied here because: (a) it edits a CI workflow file, outside the
v6 evidence-only surface after freeze; (b) each verifying push burns a
macos-15 runner minute budget; (c) verification requires the push the
user would need to authorize. Recorded honestly instead: the two pushes
the user authorized are RED for infrastructure reasons that predate the
branch.

## Resolution (2026-09-21, later same day) — CI slimmed per user instruction, GREEN

User instruction: CI must be a LIGHTWEIGHT problem check, not a heavy suite.
Restructure landed in 44f356c7 + 242a6988:

- `push`/`pull_request` now run ONE smoke job (~4 min): pinned native stack,
  wheel build+install, dependency isolation, CLI, six fast contract-level
  unit files (cli, public_api, compatibility, models, identities,
  portable_profile).
- The three original full-wheel jobs preserved UNCHANGED in scope but moved
  to `workflow_dispatch` only (manual full validation).
- Root-cause fix: poppler formula pinned to homebrew-core
  `2b54d1e3b59ce2ebe3ca041756fbbfe03d4b3c19` (poppler 26.08.0 rebuild 1,
  formula sha256 `42b509cc…6be472`), installed before pinned gdal, with a
  post-install `libpoppler.163.dylib` existence assertion. First pin
  attempt (1400ff1c, the version-bump commit) failed in run 35657397533 —
  stale bottle checksums, "Couldn't find manifest matching bottle
  checksum"; the repin to the last 26.08.0 bottle-update commit fixed it.

Verification: run 35657536903 = SUCCESS, 3m42s, smoke green on
then-current tip 242a6988; heavy jobs show as skipped (dispatch-gated).
All four earlier red runs predate the fix and are explained above.
