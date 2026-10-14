# S10 S03b: one container-correct view for the GDAL cache default and its admission charge

Date: 2026-10-14. Branch `perf/s10-semantic-systems`, on top of the R03
hygiene fix (`313f6a15`). Correctness/ops change (S10-13) — no performance
claim.

## Defect (census repro)

`s10_post_g02_census` recorded the default run **refused inside a 6 GB Slurm
step on a 376 GB node**. Root cause: the two sides of memory admission read
different views of the machine.

- Budget side (`runtime.default_memory_budget_bytes`):
  min(physical, available, cgroup headroom) × fraction → container-correct.
- Charge side (`runtime_memory.default_gdal_cache_bytes`): 5 % × **physical
  RAM** → on a small cgroup step on a large host this charge can exceed the
  *entire* budget, so the default run can never admit (5 % of 376 GB ≈
  18.8 GB > 6 GB).

D07 (`development/dossiers/07_runtime_memory.md`) requires the reservation to
match the actually applied `GetCacheMax`/`SetCacheMax` behavior; pre-fix the
applied child cap (`runtime._child_environment` → `GDAL_CACHEMAX`) and the
admission charge happened to share the function but not the view.

## Fix

`runtime_memory.default_gdal_cache_bytes` now derives its view as
min(physical bytes, finite cgroup limit) before applying the 5 % ratio — the
same most-restrictive stable view the budget side uses. Because
`runtime._child_environment` imports the function at call time
(`runtime.py`), the applied `GDAL_CACHEMAX` handed to GDAL workers and the
admission charge are the *same number* by construction; a future divergence
would need two code paths, not two probes.

No other behavior changes: hosts without a cgroup limit keep the physical
view; limits larger than physical RAM are ignored; explicit
`gdal_cache_bytes` / `GDAL_CACHEMAX` overrides are untouched.

## Proof

- Unit tests `tests/optimization_s10/semantic/test_s03b_gdal_container_view.py`
  (4): limit caps the default at 5 % of the limit; `limit=None` keeps the
  physical view; limit > physical ignored; **census configuration admits**
  (376 GB node / 6 GB step, landcover golden 32×35 job,
  `plan.admissible_workers >= 1`) with the causal guard that removing the
  cgroup limit reproduces the recorded pre-fix refusal
  (`ResourceAdmissionError`) — pinning direction, not just outcome.
- Suite: `tests/optimization_s10` 40/40 in suite order (this required the
  R03 E2E test hygiene fix in `313f6a15` — its bare
  `default_gdal_cache_bytes` assignment leaked into these tests); landcover
  differential goldens 2/2; `tests/unit -k "memory or admission or gdal or
  container"` 12/12.
- Host demo (raw: `s10-raw/s03b/s03b_host_demo_out.json`, script
  `s03b_host_demo.py`, sha256 in the archive manifest): this session's host
  is itself a 68.7 GB cgroup with ~5.65 GB headroom → post-fix GDAL default
  3.44 GB, budget 2.83 GB, so the **default still refuses here** — correct,
  headroom-driven (the refusal message names the budget, parent/writer
  reservations and the supported remedies). With the explicit
  `memory_budget_bytes` override only, the landcover golden tile runs to
  completion 3/3. Wall times in that record are host-contended
  (loadavg ≈ 19 on 4 cores) and are not performance claims.

## Scope and threats

- The change alters default admission semantics on container-limited hosts
  (more configurations admit); the register row flags this — it shipped with
  its own gate (the four tests) and this doc. Ordinary hosts are bit-identical
  (the view only changes when a *finite limit smaller than physical RAM*
  exists).
- The admission model itself (fractions, parent/worker reservations,
  headroom) is unchanged — S03b is a view correction, not a re-derivation.
- Not covered: hosts whose cgroup limit changes between admission and worker
  spawn (admission is a point-in-time decision, as before).
