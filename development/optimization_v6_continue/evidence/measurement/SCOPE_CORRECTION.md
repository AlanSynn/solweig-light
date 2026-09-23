# C6-01 D1: Scope correction to the v5 final-batch record (append-only)

Date: 2026-09-21. Written by the C6-01 evidence owner (worktree detached at
`e7a2d6ec8594b234820e7783e0ca26d821de7f3d`).

## Immutable originals (never edited by this correction)

- `optimization_v5_claude/evidence/final_batch/CAMPAIGN_v1.md` at pinned commit
  `e7a2d6ec8594b234820e7783e0ca26d821de7f3d` (introduced by `becb3841`
  "Record L4 final campaign: both 1024 cases bitwise-pass, target demonstrated").
  Integration-copy path: `/Users/alansynn/Workspace/solweig-light-claude-v5/optimization_v5_claude/evidence/final_batch/CAMPAIGN_v1.md`.
- `optimization_v6_continue/TASKS_CLAUDE.yaml`, `target:` block (schema
  `solweig-claude-continuation-v6`).

This file appends a reading correction; the originals above stand as written
and are not modified.

## What the v5 record actually measured

`CAMPAIGN_v1.md` reports **598.9 s combined** wall clock for "the full
24×1024² batch". That batch is **TWO spatial scenes**:

| case | pixels | timesteps | outputs |
|---|---|---|---|
| dense1024 | 1024 x 1024 | 24 (24 bands per output file) | 10 |
| vegetation1024 | 1024 x 1024 | 24 (24 bands per output file) | 10 |

It is **not** 24 spatial tiles. The "24" in that record is the per-scene time
dimension (24 output bands per file), and the spatial dimension is exactly two
scenes. The v5 record itself states this honestly ("both scenes"); the error
to correct is any later reuse of `598.9 s <= 1800 s` as a pass of a
24-tile target.

## Why the v6 target is not satisfied by that pass

The v6 target (`TASKS_CLAUDE.yaml`, `target:` block) is:

- `spatial_tiles: 24`
- `timesteps_per_tile: 24`
- `patches: 153`
- `actual_shape: [1024, 1024]`
- `seconds: 1800` (end-to-end)

That is **24 ACTUAL spatial tiles, each 1024x1024 pixels, each run for 24
timesteps** — 12x the spatial work of the v5 two-scene batch at the same
per-tile shape. `VALIDATION_POLICY.md` (Final-only campaign; Incomplete or
failing outcomes) already requires counting "spatial tiles separately from
bands and scenes" and forbids redefining "the original 1800-second spatial
objective to two cases". Accordingly: **the v5 two-scene pass does not
satisfy the v6 target, and must not be cited as `actual_24_tile_target_
demonstrated_once`**. At v5 pace the 24-tile workload is far outside the
1800 s budget, which is exactly the gap the v6 campaign exists to close.

## Standing v6 final-target definition (quoted from TASKS_CLAUDE.yaml)

```yaml
target:
  spatial_tiles: 24
  timesteps_per_tile: 24
  patches: 153
  actual_shape:
  - 1024
  - 1024
  seconds: 1800
```

`historical_spatial_cases: 2` in the same file confirms the historical
coverage was two cases. Any v6 final claim (`actual_24_tile_target_
demonstrated_once`) requires all 24 target jobs completed under the frozen
final-only protocol in `VALIDATION_POLICY.md`; missing tiles leave the claim
unverified rather than passed by analogy.
