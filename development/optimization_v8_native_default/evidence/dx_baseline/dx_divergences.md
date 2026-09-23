# Existing main-vs-branch DX divergences (N8-01 baseline)

Baseline main pin: `14e888760727583ef782a4dc0e7a5c7c6e6ff9d1`
(`/Users/alansynn/Workspace/solweig-v8-mainref`, read-only detached worktree).
Candidate branch: `perf/native-optimization` @ `16cdc56cbc8755675487b9c9c1f5a7e987e2c9e4`
(`/Users/alansynn/Workspace/solweig-v8-native`).

These are **pre-existing branch divergences inherited from the accepted v7
native-backend work**. They are recorded here so the v8 zero-DX-change gate
has an honest baseline; nothing in this list was introduced by the v8 packet
and nothing here is a defect to fix in this packet. The frozen snapshot pair
(`main_surface.json`, `branch_surface.json`) shows **zero divergences at the
asserted public-surface level** (seven workflow signatures/defaults,
`RuntimeOptions` fields/defaults, runtime `__all__`, CLI flags/defaults/help,
console scripts, distribution name/version/requires-python). All divergences
below are internal implementation, private modules, or behavior behind
explicit opt-in controls.

## Public-surface level: no divergence

- `src/solweig_light/__init__.py`, `src/solweig_light/cli.py`,
  `src/solweig_light/preprocessor.py`: byte-identical between main and branch.
- `src/solweig_light/api.py`: the seven public workflow signatures and
  defaults are unchanged; branch only adds private helpers (below).
- `src/solweig_light/runtime.py`: `RuntimeOptions` unchanged, including
  `block_pixels: int = 128` (branch `runtime.py:325` = main `runtime.py:325`);
  `execute_tiles` keeps its public signature
  `(jobs, options=None, *, python_executable=None, worker_module="solweig_light.runtime_worker")`.
- `pipeline.run_tile` / `files_by_key` and
  `geometry.service.prepare_geometry_exports` signatures identical
  (branch `pipeline.py:36,79`, `geometry/service.py:235`).
- `pyproject.toml` and `compat/pyproject.toml`: distribution name
  `solweig-light`, version `0.1.0.dev0`, requires-python `>=3.11`, core
  dependencies, console script `solweig-light = solweig_light.cli:main`, and
  the companion (`solweig-light-compat`, `thermal_comfort = solweig_gpu.cli:main`)
  are unchanged; the `compat/` source tree is byte-identical.

## Existing branch divergences (internal / opt-in)

1. `api.py:55-96` — new private `_precompute_geometry_phase` (C6-40): a
   concurrent GEOMETRY construction phase used by `_calculate_svf` only when
   more than one tile is pending and `workers > 1` and `cache_enabled`
   (`api.py:139-146`); serial single-worker path is verbatim.
2. `api.py:211-238` — `run_utci_tiles` adds a parent-side C6-42
   `plan_phase_admission` check (private `runtime_memory`) with
   `policy='reject'` before `execute_tiles`; plus a zero-tile guard
   (`api.py:222-225`) that makes a degenerate empty run explicit instead of a
   silent no-op. Public resource-failure semantics
   (`ResourceAdmissionError` before any worker spawn) are preserved, but the
   admission estimate differs from main's single `plan_admission` call.
3. `runtime.py:674-681` — `_child_environment` now pins `GDAL_CACHEMAX`
   (5% of physical RAM) in every spawned tile worker; main passes only the
   numerical-library thread caps.
4. `runtime.py:684-779`, `runtime.py:791-970` — `execute_tiles` rewritten
   from one-shot per-job subprocesses to a bounded pool of persistent
   workers with a stdin handshake (`SOLWEIG_LIGHT_WORKER_POOL`,
   `runtime.py:692`); non-protocol workers fall back to respawn-per-job.
   Scheduling/cancellation behavior changed accordingly; per-job failure
   reconstruction and `TileResult` values are unchanged.
5. `runtime_worker.py` — implements the persistent-pool protocol (module
   docstring and `main`); main's worker is one-shot.
6. `persistence.py:94-101` — content identity now hashes in-memory
   serialized bytes instead of re-reading the durable file;
   `persistence.py:202-236` adds `_stored_bytes_digest` digesting exactly the
   bytes GTiff stores (signed-zero block caveat documented inline). Output
   TIFF/ZIP/NPZ names, schema, and metadata are unchanged.
7. `pipeline.py` — 102 changed lines of internal kernel-call mechanics;
   public entries and output paths unchanged.
8. New private modules (no `__init__` exports, no console scripts):
   `runtime_phases.py` (934 lines), `runtime_memory.py` (970),
   `geometry/recipe.py` (181), `geometry/visibility_prepared.py` (377),
   `radiation/gvf_prepared.py` (304), `radiation/gvf_postprocess.py` (504),
   `radiation/pipeline_demand.py` (396), `radiation/cylinder_longwave.py`
   (437), `radiation/cylinder_shortwave.py` (178); modified kernels:
   `geometry/service.py`, `geometry/sky_compiled.py`,
   `geometry/visibility_compiled.py`, `radiation/engine.py`,
   `radiation/ground_view.py`, `radiation/patch_radiation.py`.
9. New private package `solweig_light.backends` (`__init__.py`,
   `native_lw.py`, `native/{lw_primary.ispc,lw_native.py,build.sh}`): the v7
   expert-requested native LW backend, selected only by explicit
   `SOLWEIG_LIGHT_LW_BACKEND=native` (`backends/__init__.py:4`,
   `backends/native_lw.py:81`), with fail-loud missing-build semantics.
10. `pyproject.toml:33-35` — package-data additions
    (`backends/native/*.ispc|*.sh|*.py`) and a pytest marker
    `prepared_default_off` (`pyproject.toml:39-43`). No new console script,
    no new core/optional dependency.
11. Environment-variable surface (source scan, `*_surface.json
    → env_vars_read`): main reads only `EE_PROJECT`
    (`inputs/construction.py:433`, optional inputs acquisition). Branch adds
    private/expert controls: `SOLWEIG_LIGHT_LW_BACKEND`,
    `SOLWEIG_LIGHT_NATIVE_CACHE`, `SOLWEIG_LIGHT_PREPARED_VIS` (default OFF,
    `geometry/visibility_prepared.py:319`),
    `SOLWEIG_LIGHT_GVF_PREPARE`, `SOLWEIG_LIGHT_FUSED_RAD`,
    `SOLWEIG_LIGHT_PATCH_CLASS_TABLES`, and the internal
    `SOLWEIG_LIGHT_WORKER_POOL` handshake. All are unset-by-default and
    preserve historical behavior when absent, per the DX contract's backend
    policy.

## Runtime behavior expected to differ (not signature-visible)

- Child tile workers run with a bounded GDAL block cache and may serve
  multiple jobs from one process (items 3-4): observable in process
  accounting, not in outputs or public calls.
- The C6-60 zero-tile guard (item 2) makes `run_utci_tiles` with an empty
  tile set raise through the phase-admission path instead of returning
  silently. Flagged here because it is a deliberate public-behavior delta
  recorded in the branch's own integration evidence.

## Verification

`tests/optimization_v8/dx/test_dx_surface.py` (7 tests) runtime-introspects
the candidate and compares it against `main_surface.json` under the empty
allowlist `EXPECTED_BRANCH_DIVERGENCES`, cross-checked against
`branch_surface.json`; teeth are proven by in-memory mutation tests
(default bump, CLI flag removal, undeclared version change). Passes in the
candidate venv both in-process and via the N8-23 subprocess-origin hook
(`SOLWEIG_DX_PACKAGE_ORIGIN=subprocess:<python>`).
