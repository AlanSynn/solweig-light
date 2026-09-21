C6-40 decision and ordering test matrix

Gates from the C6-40 dispatch, mapped to the proving test, the mechanism, and the observed
result (all 17 tests pass, exit code 0, two consecutive full-suite runs).

| # | Gate / decision | Test (tests/optimization_v6/phases/test_geometry_phase_adapter.py) | Mechanism in runtime_phases.py | Result |
|---|---|---|---|---|
| 1 | Inert until wired; nothing in src imports the module | test_module_is_inert_until_wired | module has no importers; docstring points at the recipe diff | PASS |
| 2 | Job descriptor is a JSON-safe phase job with a real memory dimension | test_job_descriptor_json_round_trip_and_memory_dimension | GeometryPhaseJob.to_dict/from_dict; memory_job -> runtime_memory.PhaseJob(PHASE_GEOMETRY, ...) | PASS |
| 3 | Descriptor validation: complete source paths, contiguous unique orders | test_job_descriptor_rejects_incomplete_sources_and_bad_orders | from_dict rejects missing sources; builder/executor reject non-contiguous or duplicate orders/tiles | PASS |
| 4 | Cache-disabled mode refuses the phase route (D04) | test_scheduler_requires_cache_enabled_and_unique_ordered_tiles | execute_geometry_phase raises ValueError when options.cache_enabled is false | PASS |
| 5 | GATE 1: ordered publication under adversarial completion orders | test_ordered_publication_survives_reversed_completion_orders (5 tiles, delays [2.0, 0.6, 0.4, 0.2, 0.0], width 2 -> tile 0 finishes LAST) | workers stage atomically (job-N.stage.json); parent commits contiguous staged prefix; journal "begin"/"commit" ceremony per tile, result.json manifest-last via atomic rename | PASS (commits == [0,1,2,3,4]; begin index == last commit + 1; first stop != order 0) |
| 6 | Phase manifest written last and self-verifying | test_phase_manifest_written_last_and_digest_verifies | PHASE_MANIFEST.json carries per-tile record sha256s; digest recomputed and compared | PASS |
| 7 | GATE 2a: mid-phase failure -> identical public error, prefix committed, no partial publications | test_mid_phase_failure_preserves_serial_error_and_prefix_publication | observe_failure: bounded grace, harvest staged prefix, drain(limit), stop+reap, raise child's rebuilt error | PASS (published == [0,1]; error is the child's own) |
| 8 | GATE 2b: numerically FIRST failure controls the public error | test_numerically_first_failure_controls_the_public_error (tile 1 fails at 1.5s, tile 4 fails at 0.1s; higher failure observed first) | grace window collects the lower job's recorded failure; first-in-numeric-order wins | PASS ("lower tile 1 failure"; published == [0]) |
| 9 | GATE 2c: crashed child (no failure.json) surfaces generic error, prefix holds | test_crashing_worker_surfaces_generic_error_and_prefix_holds | exit-code path rebuilds TileExecutionError("exit code 9") exactly like runtime.execute_tiles | PASS (published == [0]) |
| 10 | GATE 2d: survivors reaped per m3 | test_live_children_are_reaped_after_failure | _reap_worker(terminate=True) for every dispatched slot before the error propagates | PASS (os.kill(pid, 0) raises ProcessLookupError for all recorded pids) |
| 11 | GATE 3: child records native mask at kernel entry; configured == actual | test_child_native_mask_recorded_at_kernel_entry_equals_configured | env-before-import child (Popen env=, C6-01 finding), set_num_threads + config assert, njit(parallel=True) probe at kernel entry, parent asserts mask_pinned and mask_at_kernel_entry == configured before commit | PASS (all masks == 2) |
| 12 | Tampered mask record rejected at publication | test_tampered_native_mask_is_rejected_at_publication | _validate_stage_record refuses a stage record whose kernel-entry mask != configured | PASS (ValueError "kernel entry"; published == [0]) |
| 13 | GATE 4: width rejected by plan_phase_admission is never dispatched | test_rejected_width_never_dispatches_any_child (policy="reject", budget admits 2 of 4) | admission runs parent-side BEFORE any spawn; ResourceAdmissionError raised in-process | PASS ("only 2 fit"; zero stub worker events; zero journal lines) |
| 14 | Individually infeasible job raises even under policy="queue" | test_individually_infeasible_job_raises_even_under_queue | queueing cannot make a single job fit; plan raises | PASS |
| 15 | Admitted width bounds concurrency (memory/thread budget real) | test_admitted_width_bounds_concurrent_children | scheduler dispatches at most plan.admissible_workers persistent slots | PASS (exactly 2 distinct pids; observed concurrency <= 2; commits ordered) |
| 16 | GDAL_CACHEMAX per child = per-worker allowance (m7 W3) | test_gdal_cachemax_env_reaches_children | child env GDAL_CACHEMAX set from plan reservation bytes (MB interpretation) | PASS (native snapshot records env value) |
| 17 | Real scene end-to-end: phase production is bitwise the serial production | test_real_scene_phase_matches_serial_production_bitwise (3 real tiles, 32x35, real worker + real producer; second run asserts cache_hit=True) | same C6-10 recipe identity/key as serial; ordered publication; masks == 2 | PASS (arrays equal after stripping random generation names; visibility channels equal on shape + patch table + encoded payload sha256 — the field GeometryStore itself validates; identity equal) |

Ordering decisions recorded for the reviewer:

- Dispatch strictly ascending in `order`; publication commits ONLY the contiguous staged
  prefix (D04 staged-prefix rule) — gate 5's reversal case proves completion order does not
  leak into publication order.
- On failure, the public error is chosen by NUMERICALLY first recorded failure among started
  jobs (m3 §3), not by observation order — gate 8's inverted-delay case proves it.
- All-geometry-complete barrier: execute_geometry_phase returns only after every tile is
  committed and PHASE_MANIFEST.json (written last) is complete; no simulation can be
  admitted earlier; no overlap credit is taken.
- workers == 1 / cache_enabled == false are NOT intercepted: the integration recipe gates the
  phase route on `runtime.workers > 1 and runtime.cache_enabled`, preserving the serial route
  verbatim (D04).
- Legacy TIFF/ZIP/NPZ publication stays owned by the existing serial loop; the adapter
  publishes ready native handles that the loop consumes as cache hits. This is why the
  recipe diff is a pre-loop hook, not a replacement of the loop.

Scope proven vs deferred:

- Proven: phase-level GEOMETRY construction with ordered publication, transactional per-tile
  commit, serial-identical failure semantics, survivor reaping, native thread-cap assertion at
  kernel entry, admission-gated width, per-child GDAL_CACHEMAX, barrier manifest, and bitwise
  equality with serial production on a real (small) scene.
- Deferred (stated in the module docstring and recipe diff): legacy artifact publication
  (unchanged serial loop), the SIMULATION phase adapter (C6-70 wiring), and any pipeline.py
  edit — `run_pipeline` already calls `_calculate_svf` before `run_utci_tiles` (api.py:209),
  so the single api.py hook covers the pipeline route without touching pipeline.py.
