# Post-handover API + config probes (request: verify API preservation and result invariance rigorously)

Date: 2026-09-21. All probes read-only wrt package source; runs use the frozen
wheel (`freeze/site-packages`) vs the v4 base install
(`final_combined_v1/site-packages`), .venv-light CPython 3.11.16, dense_urban_256.

## 1. API surface — IDENTICAL

- Source level: `api.py`, `__init__.py`, `cli.py`, `pipeline.py`, `config.py`
  byte-identical between `bfd9915e` (base) and tip. Only 8 internal files
  changed (geometry/radiation/persistence/runtime internals).
- Programmatic level (introspection of both installed trees): all seven
  workflow entry-point signatures (`thermal_comfort`, `run_utci_tiles`,
  `calculate_svf`, `run_walls_aspect`, `build_inputs`, `build_wind_ext_coeff`,
  `preprocess`) IDENTICAL; `RuntimeOptions` defaults / `as_dict()` /
  resolved properties / `__init__` / `plan_admission` / `execute_tiles`
  signatures IDENTICAL; public module callable surfaces
  (api/pipeline/cli/preprocessor/config) IDENTICAL.
- CLI: `cli.py` byte-identical → argument grammar unchanged.

## 2. Config-robustness probe — block_pixels=128 (package default)

`b128_base.json` / `b128_cand.json` (this directory): full-chronology dense256
runs, block_pixels=128, threads=4, checkpoint_interval=1, 23 artifacts each.

- v4 base vs v5 candidate at block=128: **BITWISE IDENTICAL 23/23**.
- Cross-block (base): block=128 outputs bitwise-equal to the frozen block=1024
  reference (`evidence/l2/REFERENCE_bfd9915e_dense256.json`) — block
  partitioning does not change outputs (per-pixel independence holds in the
  base design); with v5 ≡ base at both blocks, the same holds for v5.

## Residual unverified scope (unchanged from handover)

- workers>1 (S02 pool) and the two env-gated routes (`SOLWEIG_LIGHT_FUSED_RAD=1`,
  `SOLWEIG_LIGHT_WORKER_POOL`) are bit-verified only at L0/L1 kernel level,
  not at 1024 scale (default paths, which the gates leave inactive, carry the
  bitwise L2/L4 evidence).
- Thread-count variation beyond threads=4 at full scale is covered by L1
  kernel differentials and the G03 row-block deterministic ordering, not by a
  second L4 pass.
