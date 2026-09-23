# Sources and provenance

Repository paths below refer to the inspected checkpoint, not an instruction to reset the working branch. Blob IDs are Git object IDs returned by the connector, not newly measured local SHA256 hashes. Historical records report executions performed elsewhere; this packet did not reproduce those runs. External sources are official documentation.

## S01: Branch identity

https://api.github.com/repos/AlanSynn/solweig-light/branches/perf/claude-glm53-cpu-v5

Scope: branch metadata, source-inspection checkpoint.

Git blob: `e7a2d6ec8594b234820e7783e0ca26d821de7f3d`.

## S02: Final protocol

https://github.com/AlanSynn/solweig-light/blob/e7a2d6ec8594b234820e7783e0ca26d821de7f3d/benchmarks/protocols/claude_v5/final_protocol_v1.json

Scope: two spatial cases, runtime and cache conditions.

## S03: Final campaign and harness

https://github.com/AlanSynn/solweig-light/blob/e7a2d6ec8594b234820e7783e0ca26d821de7f3d/optimization_v5_claude/evidence/final_batch/CAMPAIGN_v1.md

Scope: reported one-pass two-case times; interpret with run_final_large.py.

## S04: Public API orchestration

https://github.com/AlanSynn/solweig-light/blob/e7a2d6ec8594b234820e7783e0ca26d821de7f3d/src/solweig_light/api.py

Scope: thermal_comfort, _calculate_svf, run_utci_tiles.

Git blob: `596a87c34f938906c151113fb0a20e188ee59f01`.

## S05: Standalone geometry service

https://github.com/AlanSynn/solweig-light/blob/e7a2d6ec8594b234820e7783e0ca26d821de7f3d/src/solweig_light/geometry/service.py

Scope: _producer, _export, _compare, prepare_geometry_exports.

Git blob: `74c3671656f44db06364f65eff117df045fc6b5f`.

## S06: Chronological pipeline

https://github.com/AlanSynn/solweig-light/blob/e7a2d6ec8594b234820e7783e0ca26d821de7f3d/src/solweig_light/pipeline.py

Scope: normalization, unextended native key, output/state demand.

Git blob: `58608f99d42d1c93ed77e90b61491a8d2be063e3`.

## S07: Geometry and simulation identities

https://github.com/AlanSynn/solweig-light/blob/e7a2d6ec8594b234820e7783e0ca26d821de7f3d/src/solweig_light/identities.py

Scope: InputGuard, geometry_identity dependency closure.

Git blob: `f11b0cb3b0fc4ffa89a37495a7900fda29a9966e`.

## S08: Geometry store

https://github.com/AlanSynn/solweig-light/blob/e7a2d6ec8594b234820e7783e0ca26d821de7f3d/src/solweig_light/cache/geometry.py

Scope: whole identity hash and exact manifest equality.

Git blob: `1f47ab7ee9fe6e9ac03fb9bd39c31fc6fdd893b2`.

## S09: Old in-process portfolio

https://github.com/AlanSynn/solweig-light/blob/e7a2d6ec8594b234820e7783e0ca26d821de7f3d/optimization_v5_claude/evidence/portfolio/portfolio_v1.py

Scope: RuntimeOptions-only native thread limitation concern.

Git blob: `fccb08fdc389afcdb43206b0adc26f4d59c4039b`.

## S10: Radiation engine Lside

https://github.com/AlanSynn/solweig-light/blob/e7a2d6ec8594b234820e7783e0ca26d821de7f3d/src/solweig_light/radiation/engine.py

Scope: Lvikt_veg, Lside_veg_v2022a.

Git blob: `583055c198fa4f7b1a3c1eba226988ca394c5ef5`.

## S11: Engine final dependency ordering

https://github.com/AlanSynn/solweig-light/blob/e7a2d6ec8594b234820e7783e0ca26d821de7f3d/src/solweig_light/radiation/engine.py

Scope: Solweig_2022a_calc: TMRT before cylinder cardinal diagnostic addition.

Git blob: `583055c198fa4f7b1a3c1eba226988ca394c5ef5`.

## S12: Patch radiation

https://github.com/AlanSynn/solweig-light/blob/e7a2d6ec8594b234820e7783e0ca26d821de7f3d/src/solweig_light/radiation/patch_radiation.py

Scope: Kside, _shortwave/_longwave, class preparation, dormant P01.

Git blob: `464117ac6a0eb524402d7783ce435632b706d2f6`.

## S13: Ground view

https://github.com/AlanSynn/solweig-light/blob/e7a2d6ec8594b234820e7783e0ca26d821de7f3d/src/solweig_light/radiation/ground_view.py

Scope: _direction_snapshot, _gvf_fused, _postprocess_block.

Git blob: `be62ef2ca34ecad8130a1f9f35eeab1761bf17ef`.

## S14: Legacy verification

https://github.com/AlanSynn/solweig-light/blob/e7a2d6ec8594b234820e7783e0ca26d821de7f3d/src/solweig_light/cache/legacy.py

Scope: full member CRC/readability then separate import path.

Git blob: `ad508137f2496fd821a71efba15e573cd749e749`.

## S15: Runtime memory/pool

https://github.com/AlanSynn/solweig-light/blob/e7a2d6ec8594b234820e7783e0ca26d821de7f3d/src/solweig_light/runtime.py

Scope: RuntimeOptions, estimate_memory, execute_tiles persistent pool.

Git blob: `cf7b39f321f03559c1c3859722ea352d0cd86201`.

## S16: Accepted/rejected v5 handover

https://github.com/AlanSynn/solweig-light/blob/e7a2d6ec8594b234820e7783e0ca26d821de7f3d/optimization_v5_claude/evidence/handover/MERGE_REVIEW_NOTES_v1.md

Scope: already applied work, P01 regressions, actual GLM-only route record.

Git blob: `4942000a9708bd03a8795dcc2c5bd82e23e3214a`.

## S17: Decoder

https://github.com/AlanSynn/solweig-light/blob/e7a2d6ec8594b234820e7783e0ca26d821de7f3d/src/solweig_light/geometry/visibility_compiled.py

Scope: _decode, descriptor, fused copies and preflight.

Git blob: `121a73fa88f6d9b254674c37f50fbbd4ccb434a0`.

## S18: Post-S07 census

https://github.com/AlanSynn/solweig-light/blob/e7a2d6ec8594b234820e7783e0ca26d821de7f3d/optimization_v5_claude/evidence/census/census_dense256_post_s07.json

Scope: instrumented warm diagnostic, not 1024 phase timings.

Git blob: `7110064fd4a4c580c7231b8379ec348a7b5a05b8`.

## S19: Math profile

https://github.com/AlanSynn/solweig-light/blob/e7a2d6ec8594b234820e7783e0ca26d821de7f3d/src/solweig_light/radiation/_math_profile.py

Scope: SLEEF domain and fallback behavior.

## S20: State and output model

https://github.com/AlanSynn/solweig-light/blob/e7a2d6ec8594b234820e7783e0ca26d821de7f3d/src/solweig_light/models.py

Scope: carried state and requested output names.

Git blob: `f6db62488b2480f4dac407902570a204e35f063a`.

## O01: Claude Code subagents

https://code.claude.com/docs/en/sub-agents

Scope: official: model inheritance, frontmatter, worktree default.

## O02: Z.ai Claude Code integration

https://docs.z.ai/devpack/tool/claude

Scope: official: Claude aliases can map to GLM; verify current route.

## O03: Numba threading layers

https://numba.readthedocs.io/en/stable/user/threading-layer.html

Scope: official: thread pool, mask, environment-before-import.

## O04: Git worktree

https://git-scm.com/docs/git-worktree

Scope: official: explicit detached worktree without named branch.

## O05: Numba performance tips

https://numba.readthedocs.io/en/stable/user/performance-tips.html

Scope: official: nopython, loop performance, fastmath semantics.
