# C5-61 Freeze manifest

Date: 2026-09-20. Frozen at commit `d2edbc105d5d3658d25613326439d3a3efb74bb9`
(branch `perf/claude-glm53-cpu-v5`, integration base `bfd9915e`, historical
checkpoint `14e88876`).

## Artifacts

- Batch/protocol definition: `benchmarks/protocols/claude_v5/final_protocol_v1.json`
- Wheel: `wheel/solweig_light-0.1.0.dev0-py3-none-any.whl`
  sha256 `8fe69a5831cb340ce72ce911be9ccbd50c8808f6dcaaa8d4c69c6506a05b2ad4`
  (built with `uv build --wheel` from clean tree at the frozen commit)
- Isolated install: `site-packages/` (pip `--target`, `--no-deps`)
- Installed check: `installed_check_dense256.json` — L2 chronological harness
  (`evidence/l2/l2_chrono.py`, dense_urban_256, 24 steps, 153 patches, 10 save
  flags, checkpoint_interval=1) executed with `PYTHONPATH` pointing at the
  isolated `site-packages/`; import origin asserted inside the installed wheel;
  torch not imported. Result: 23/23 artifacts bitwise-identical to the pristine
  `REFERENCE_bfd9915e_dense256.json`. PASS.

## Parity reference for L4

The existing v4 large-run outputs at
`reports/characterization/local_cpu_optimization_v1/qualification/final_combined_v1/large_harness/large_runs_v1/{dense1024,vegetation1024}/candidate_manifest.json`
are reused as the numerical reference (no new baseline, no missing-reference
capture). Integrity re-verified 2026-09-20: all 20 stored output files re-hashed,
all match recorded sha256. Provenance chain recorded in
`final_protocol_v1.json` (`parity_gate.reference_provenance`): v4 outputs
produced from source identical to `14e88876` (empty src/pyproject/tests diff to
`bfd9915e`); v5 tip proven bitwise-equal to `bfd9915e` at L2. Therefore the v5
final campaign must reproduce those sha256 values exactly on the same fixtures
and runtime options.

## Fixture copies

1024 fixture TIFFs copied into this worktree from the main-repo copies and
sha256-verified against the fixture manifests (dense1024 `51e5aac7…`,
vegetation1024 `6cc92180…`). TIFF binaries stay untracked (size); manifests and
met.txt are tracked.

## Environment

`.venv` (CPython, macOS arm64, darwin 25.6.0), numba njit cache enabled, math
profile `solweig-portable-sleef-5a1d179d-v1` (fingerprint
`8e4d38460b61b0299e7c1d525c8499750dcd219ef01cc785d7496dbe1dcbef30`) — identical
profile id/fingerprint as the v4 large runs.
