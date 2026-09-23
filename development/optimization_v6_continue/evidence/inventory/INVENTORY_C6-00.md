# C6-00 same-branch source and provider inventory

Date: 2026-09-21. Coordinator: GLM-5.3 via Z.ai (Claude Code).

## Branch and worktree

- Integration branch: `perf/claude-glm53-cpu-v5` (only named branch; no new
  branch creation, no merge/push/PR/release in this campaign).
- Integration worktree: `/Users/alansynn/Workspace/solweig-light-claude-v5`.
- Actual HEAD at campaign start: `e7a2d6ec8594b234820e7783e0ca26d821de7f3d`
  (matches the packet's known checkpoint; nothing to reconcile, never reset).
- Protected dirty state: 8 untracked paths under
  `optimization_v5_claude/evidence/final_batch/runs_v1/` (L4 run scenes,
  numba caches, RSS logs) — intentionally untracked by size; preserved.
- main branch: untouched at `14e88876` in `/Users/alansynn/Workspace/solweig-light`.
- Pushed state: branch pushed to origin at user request after v5 handover
  (remote tip `e7a2d6ec`); v6 continues locally on the same branch.

## Provider routes

- GLM-5.3 via Z.ai (Claude Code): ACTIVE — coordinator and all workers this
  campaign unless recorded otherwise.
- Actual Anthropic Opus: UNAVAILABLE (unchanged from v5 finding,
  `optimization_v5_claude/evidence/routing/`): no verified direct provider
  route; the configured `opus` alias maps to GLM. Reviews are labeled
  "independent GLM review (Opus unavailable)". No credentials created, no
  gateway built.

## Accepted v5 state carried forward (preserved, per DESIGN_AUTHORITY §7)

- R01a guarded absorbing-state exit (`geometry/sky_compiled.py`).
- G02 GVF source hoisting + two-state Lup snapshots (`radiation/ground_view.py`).
- G03 fused row-block GVF, wired for threads>1 (`_gvf_fused`).
- S02 persistent worker pool (`runtime.py`, `runtime_worker.py`; serve mode
  env-gated, inactive at defaults).
- S07 checkpoint digest optimization (`persistence.py`).
- L4-proven bitwise parity vs v4 reference on both 1024 scenes; 1.383×/1.129×.
- API surface byte-identical (api/__init__/cli/pipeline/config) — probe
  `optimization_v5_claude/evidence/final_scope/POST_REVIEW_PROBES.md`.

## Dormant / rejected (stays OFF)

- P01 fused radiation decode: measured-rejected twice (+46% then +9.4% at
  t4_b1024); dormant behind `SOLWEIG_LIGHT_FUSED_RAD=1`. Stays OFF unless a
  materially different candidate earns promotion with separate evidence.
- R04 bush specialization: rejected (bush ≡ 0 theorem).
- `SOLWEIG_LIGHT_WORKER_POOL` serve mode: functional but not default.

## Reference paths (v6 baseline = current accepted v5 branch)

- v5 final evidence: `optimization_v5_claude/evidence/final_batch/` (two-scene
  1024 campaign; scope correction handled in C6-01).
- v5 L2 reference: `optimization_v5_claude/evidence/l2/REFERENCE_bfd9915e_dense256.json`
  (23 artifacts) — valid for dense256 full-chronology gates at the same
  math profile/environment; reused where dependency-valid.
- v4 large reference (bitwise parity target at 1024): main checkout
  `reports/characterization/.../large_harness/large_runs_v1/`.
- Wheel/env freeze (v5): `optimization_v5_claude/evidence/freeze/` — env
  `.venv-light` py3.11.16 fingerprint `8e4d3846…`.

## Known inherited scientific exceptions (unchanged dispositions)

- dense1024 TMRT Linux p8 gate failure: inherited; canonical v4 record is an
  UNRESOLVED POINTER in the v5 inventory (caveat carried).
- Four inherited SVF/UMEP exceptions: failed-by-disposition; count is the
  inventory's own anchoring.
- S07 signed-zero-only-block read-back via GDAL block cache: pre-existing
  base behavior, preserved (false-fail only).
- Pre-existing differential-suite failures at base (~225, thread-cap related
  per v5 memory): exist at base and tip alike; not introduced by v5/v6 work.

## Scope facts recorded up front (from DESIGN_AUTHORITY §8, §18)

- v5's 598.9s = TWO spatial scenes × 24 timesteps. NOT 24 spatial tiles.
- v6 final target: 24 actual spatial tiles × 24 timesteps × 153 patches,
  actual shape 1024×1024, ≤1800s end-to-end, one campaign + one causal retry.
- Existence of the actual 24-tile dataset is NOT yet established — C6-100/101
  must verify data presence or record the target as unverified.

## Wave-0 dispatch

- C6-01 (evidence owner): detached worktree `../solweig-light-v6-measure`;
  scope correction + isolated-thread harness + v5 baseline.
- C6-03 (runtime specialist): detached worktree `../solweig-light-v6-mem`;
  stage live-memory + publication inventory.
- C6-02 (cold producer/key census): queued after C6-01 harness lands.
