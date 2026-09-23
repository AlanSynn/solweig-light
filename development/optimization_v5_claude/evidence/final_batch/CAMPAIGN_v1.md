# C5-62 Final campaign record (L4, attempt 1 of 1, no retries used)

Date: 2026-09-21. Harness: `run_final_large.py` (this directory), driven by
`benchmarks/protocols/claude_v5/final_protocol_v1.json`. Wheel frozen at
`d63636ae` (wheel sha256 `8fe69a58…`, built at source `d2edbc10`); environment
`.venv-light` CPython 3.11.16 (v4-identical; fingerprint asserted equal to the
reference profile before the run). Host lease exclusive during both runs.

## Results

| case | parity (bitwise sha256 vs v4 reference) | candidate s | v4 reference s | speedup | peak RSS | note |
|---|---|---|---|---|---|---|
| dense1024 | BITWISE_PASS (10/10 outputs) | 289.765 | 400.827 | 1.383× | 1.07 GiB | exit 0, not aborted |
| vegetation1024 | BITWISE_PASS (10/10 outputs) | 302.396 | 341.365 | 1.129× | 1.13 GiB | exit 0, not aborted |

- Combined wall clock (monitored): 598.9 s for the full 24×1024² batch (both
  scenes, all 10 outputs each, 24 bands per output, checkpoint_interval=1,
  cold JIT included via per-run `NUMBA_CACHE_DIR`). Target ≤1800 s:
  **demonstrated once** with large margin (claim ceiling per protocol).
- Preprocessing (tile creation, SVF standalone pass) included in wall time but
  excluded from `elapsed_diagnostic_seconds`, matching the v4 reference
  accounting (that field measures `thermal_comfort` only).
- Parity gates checked beyond sha256: fixture manifest sha256, math-profile
  fingerprint, full `runtime_options` dict — all equal to the reference
  (`verify_parity.py`).
- Corrective retry: NOT used (0 of 1 allowed). Missing-reference capture: NOT
  used (0 of 1 allowed) — existing v4 reference reused; no new baseline.

## Interpretation limits

Single pass, single host, `target_demonstrated_once`. Not a speedup
distribution, not robustness evidence, not P7/P8 release qualification.
dense1024 gains more than vegetation1024 from R01a (vegetation scenes keep
more rays live through canopy interactions, so the absorbing-state early exit
fires less often); both remain bitwise-identical to the reference outputs.

## Raw evidence

- `runs_v1/dense1024/` — stdout/stderr, monitor.json, rss_samples.jsonl (20 ms
  stdlib-ps sampling), kwargs_used.json, candidate_manifest.json (module
  origins inside freeze site-packages, torch_imported=false, per-output
  sha256), full scene copy with outputs.
- `runs_v1/vegetation1024/` — same layout.
- `verify_parity.py` invocations recorded in this file's Results table.
