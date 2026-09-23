# REVIEW C6-60 — independent review of the C6-70 first-wave controlled integration

Reviewer: C6-60 (service instance). Routing: **independent GLM review; Opus unavailable**
(reviewer model GLM-5.3 via Z.ai; no Opus route is configured or verifiable for this
session — no Opus identity claimed).
Review base: integration worktree `/Users/alansynn/Workspace/solweig-light-claude-v5`,
branch `perf/claude-glm53-cpu-v5`, diff under review `git diff 8e0b3877..5aa82325`
(commits C6-70a..C6-70j, `47cda54f`..`5aa82325`). Prior per-worker reviews
(`REVIEW_C6{10,20,21,22,30,31,42,50}, REVIEW_C603`) all APPROVE; their findings were
checked for closure. Tracked `src/` and `tests/` are clean at `5aa82325`; `5aa82325`
(C6-70j) is evidence-only.

## Verdict: APPROVE-WITH-CONDITIONS

Conditions 1 and 2 below are evidence/disposition records, not code reverts. All
recipe call sites verified; no approximation, fastmath, or tolerance relaxation exists
anywhere in the range; public contracts are untouched; the L2 chronology claim is
reproduced from the committed logs and is in fact stronger than documented.

## Scope verified vs taken-from-evidence

Verified directly by me (code, diffs, logs, test runs):

1. **Recipe fidelity, per patch.** Each landed call site was compared against its
   worker recipe:
   - C6-70a vs `evidence/recipe/integration_patch_C6-10.diff`: **verbatim** (byte-level
     match modulo diff headers and one trailing blank context line; verified by
     normalized line comparison). `service._producer` deleted; both routes produce via
     `numerical_geometry_recipe`; trusted-legacy extends a **copy**
     (`dict(geometry_key, trusted_legacy=...)`); export provenance separate via
     `export_identity`; `recipe.py` itself landed pre-range (`443ee2b7`, reviewed) and
     its sha256 prefix `56cf88da32d83fa4` still matches the C6-10 anchor.
   - C6-70b vs `evidence/mem_adm/m7_phase_admission_wiring.proposed.patch`: W1 (api.py)
     and W3 (runtime.py) hunks **byte-identical** (same blob index hashes
     `596a87c3..8fcbfff7`, `cf7b39f3..7a08b428`). W2 deferral is explicitly sanctioned
     by m7 §3 (boundary-change sign-off deferred to the phase adapter).
   - C6-70c vs `evidence/lside/integration_patch_recipe.diff`: call-site hunk exact;
     import placed after the `shadows` import — a variation the recipe explicitly
     permits ("the integrator may place the import differently … without semantic
     change").
   - C6-70d vs `evidence/cyl_lw/INTEGRATION_RECIPE.diff`: the engine.py hunks (the
     `Lcyl_v2022a_by_demand` swap and **both** sentinel-guarded `+=` sites) match the
     recipe **verbatim**. The pipeline scope is the amended form described below.
   - C6-70e vs `evidence/cyl_sw/INTEGRATION_RECIPE.md` patch 1: matches, plus one
     **additional** conservative guard `and not _fused_enabled()` (see A5).
   - C6-70f vs `evidence/gvf_prep/INTEGRATION_RECIPE.md`: **verbatim** (single call
     swap `_gvf_fused` → `prepared_gvf_step`, identical argument list plus
     `parallel=True, block_rows=32`; kill switch `SOLWEIG_LIGHT_GVF_PREPARE=0`
     unchanged).
   - C6-70g vs `evidence/gvf_post/integration_patch.md`: **verbatim** (import + single
     call swap, 5-name unpack, `parallel=True`); `_postprocess_block` confirmed
     byte-for-byte untouched in the range (`git diff` shows only the wrapper docstring
     + dtype-guard addition in `gvf_postprocess.py`).
   - C6-70h vs `evidence/decoder/integration_recipe.md`: both prepend-with-fallback
     call sites as specified (`decode_shortwave_block` ahead of the `_block` triple;
     `decode_longwave_block` ahead of the identical generator expression; kernel call
     line untouched).
   All fallbacks route to byte-identical originals: `lside_veg_v2022a_demanded` →
   untouched `Lside_veg_v2022a` (pipeline_demand.py:344-348, 364, 366);
   `Lcyl_v2022a_by_demand` FULL → untouched `Lcyl_v2022a` (cylinder_longwave.py:406-407);
   `kside_cylinder_anisotropic` None → generic wrapper body continues unchanged;
   `prepared_gvf_step` → `_gvf_fused`; `gvf_postprocess_block` flagged →
   `_reference_block` → untouched `_postprocess_block`; decoders None → original
   decode expressions.

2. **No numerical relaxation.** Grepped the entire `src/` range diff for
   fastmath/allclose/rtol/atol/isclose/allow_nan/seterr/errstate/filterwarnings
   additions: none. `identities.py` unchanged in the range. Patch tables
   (`geometry/shadows.py`, `svf.py`) untouched. `SOLWEIG_LIGHT_FUSED_RAD` predicate is
   byte-identical at base and head; default remains OFF.

3. **Public contracts.** AST comparison of base vs head public surface (module-level
   public functions/classes with signatures, `__all__`) for api.py, pipeline.py,
   runtime.py, identities.py, geometry/service.py, radiation/{engine,patch_radiation,
   ground_view}.py: **unchanged**. `RuntimeOptions.as_dict` untouched (runtime.py range
   diff is the 6-line W3 hunk only). No new RuntimeOptions fields; the demand profiles
   are programmatic only (D09 honored).

4. **Chronology evidence recomputed from committed logs** (not trusted from the .md):
   - `l2-base.jsonl` / `l2-integrated.jsonl`: 62 events each; label multiset
     {longwave_patches: 24, Lside: 24, Kside_veg_v2022a: 14} vs {longwave_demand: 24,
     Lside: 24, Kside_veg_v2022a: 14}.
   - Lside: 24/24 events with **inputs AND outputs** hash-identical. Kside: 14/14
     identical. The day-gated Kside count (14 of 24) matches base in both trees.
   - Longwave, direct equality (stronger than the .md's transitivity claim): pairing
     base `longwave_patches` with integrated `longwave_demand` per step,
     **out[0] (Ldown) and out[1] (Lside) are hash-identical across all 24 paired
     events** — the dispatcher's primary outputs are pinned event-by-event, not merely
     transitively. 10 shared input hashes per first event confirm common inputs.
   - Chronology: the label interleaving sequence is identical after normalizing
     longwave_patches/longwave_demand to one name; no step gained or lost a radiation
     call.
   - Final outputs: `l2-base-output-hashes.json` and `l2-integrated-output-hashes.json`
     are byte-identical (11 files incl. TMRT/UTCI/SVF and processed inputs).
   - Cardinal-diagnostic soundness: in the `cyl==1 ∧ anisotropic_sky==1` branch the
     `+=` sites execute **after** Sstr/Tmrt (engine.py:1662-1669 vs 1676-1681), so the
     omitted Lcyl cardinal diagnostics under the reduced profile affect only returned
     diagnostic fields the pipeline never reads; identical TMRT is consistent, not
     coincidental. `Lcyl_v2022a_primary` returns NOT_REQUESTED sentinels (never zeros),
     and the `is not NOT_REQUESTED` identity guard covers the fallback domain (real
     arrays ⇒ `+=` runs exactly as base).
   - Probe transport: `chronology_probe.py` swaps `execute_tiles` in-process with
     `tuple(_run_tile(**job, runtime=options) for job in jobs)` — same job dicts, same
     `run_tile` entry, both trees; transport-only, as documented. Wrappers are read-only
     hash collectors (dtype+shape+bytes sha256).

5. **Amendments beyond the recipes — all sound:**
   - **A1** `gvf_postprocess.py` dtype guard (61c76a17): delegates any non-float32 term
     raster to the untouched `_postprocess_block` via `_reference_block` instead of
     silently downcasting a float64-promoted `gvfLup` (float64 `lup_term` is reachable:
     SBC is outside `_gvf_fused`'s `_supported` screen). Strictly conservative; the
     in-tree all-float32 invariant keeps the fast path; caught by a real differential
     (`test_float64_derived_lup_conversion_preserved`). Contract-preserving.
   - **A2** `test_gvf_prepare_counts.py` floor adaptation (61c76a17): legitimate — the
     C6-31 typed postprocess legitimately inverted the old aggregate premise (fused
     now makes the fewest `_operate` calls: measured 972 < 2285 full < 2745 prepared);
     the per-direction tree reduction remains pinned by the `_lup_expression` tests;
     new floors (fused < prepared; full − fused ≥ 600 vs measured 1313) are honest and
     documented. Not a weakened gate.
   - **A3** decoder conftest-by-path shims + spied recipe test (58d7fe23): the
     family-unique `importlib` load removes real sibling-shadowing fragility (proven by
     my combined-collection run below); the rewritten
     `test_longwave_end_to_end_with_recipe_shim` is **stronger** than the `_block`
     monkeypatch it replaces — it spies the real `decode_longwave_block` and proves the
     wired call site actually takes the prepared route with exactly the demand
     channels, inputs by identity, fields bitwise.
   - **A4** `set_demand_profile` returns-None fix (78d242a6): verified against source —
     `cylinder_shortwave.set_demand_profile` is deliberately set-only and raises
     `ValueError` on `None`, so C6-70d's `_previous_sw_profile` storage was broken for
     every pipeline run; capturing `demand_profile()` first and restoring through the
     validated setter is correct and exception-safe (both restorations are validated
     values that cannot raise in `finally`). The C6-70d breakage existed only between
     `02c0efa4` and `78d242a6`; its gates were kernel-only (39/39 cylinder_lw) and the
     L2 differential was genuinely the first full-pipeline gate, as recorded.
   - **A5** Lside fast-path activation + `_fused_enabled()` hook guard:
     - Activation (78d242a6): `radiation_demand(PIPELINE_CYLINDER_ANISOTROPIC)` wraps
       the per-timestep `Solweig_2022a_calc` call — exactly the C6-20 recipe's
       driver-side placement. Thread-locality is correct: `pipeline_demand._demand_state`
       is `threading.local()`; the context is set and restored **in the same thread
       that synchronously calls** `Solweig_2022a_calc`/`current_demand()`; the timestep
       loop is sequential per worker child in the shipped subprocess scheduler
       (`execute_tiles` children serve tile jobs sequentially; each child is a fresh
       process), so per-thread and per-tile coincide. The in-process transport used by
       tests/the probe is likewise sequential. The timestep loop body is otherwise
       byte-identical modulo indentation (verified), and the call arguments are
       unchanged.
       Asymmetry note (F4): the two cylinder demand holders are **module globals**, not
       thread-local — safe under the shipped one-tile-at-a-time-per-process scheduler
       and explicitly documented in the C6-21 recipe, but a future concurrent in-process
       tile runner would leak profiles across tiles.
     - `_fused_enabled()` guard (15dfbf2a): deviates from the C6-22 recipe text, but is
       conservative and default-inert: the predicate is byte-identical to base and
       defaults OFF (`SOLWEIG_LIGHT_FUSED_RAD == '1'`), so the default path is exactly
       the recipe's; the guard only pins the experimental fused route to base behavior.

6. **Preserve-check.**
   - Seven workflows/CLI: no CLI or workflow-signature changes; no new env-driven
     defaults beyond the recipe-specified `GDAL_CACHEMAX` child cap (W3) and the
     pre-existing GVF kill switch.
   - Patch count: unchanged (no shadow/patch-table code in the diff).
   - Chronology/state: empirically pinned by the recomputed differential (all carried
     state observable through per-step argument hashes; 24/24 identical).
   - Tests re-run by me, single pytest process, no xdist, no benchmarks, in the
     integration worktree with `PYTHONPATH=src`: `tests/optimization_v6/{gvf_prepare,
     gvf_postprocess,decoder,cylinder_lw,cylinder_sw,lside,geometry_recipe,memory}` →
     **541 passed**; `tests/unit/test_geometry_service.py tests/unit/test_identities.py
     tests/optimization_v6/geometry_census` → **35 passed**. Zero failures; warnings
     are the documented adversarial-domain RuntimeWarnings.

## Findings

1. **F1 (minor, behavioral edge — condition 1).** `plan_phase_admission` raises
   `ValueError` on an empty job list (`runtime_memory.py:876-877`), and W1 feeds it the
   public `jobs` list unconditionally. Base behavior for a degenerate zero-tile public
   run (`common` empty, `tile_keys=None`) was a silent no-op
   (`plan_admission([])` → `AdmissionPlan(0, (), 0)`; `execute_tiles([])` → `()`); the
   integrated tree now crashes with `ValueError: plan_phase_admission requires at least
   one job`. No numerical effect and failure is early/parent-side, but it is an
   observable public-behavior delta on a (pathological) input, not covered by the m7
   recipe text. Disposition owed: either guard with `if jobs:` or record the stricter
   behavior as accepted in the integration evidence.
2. **F2 (minor, evidence gap — condition 2).** The L2 differential ran in-process with
   `threads_per_worker=1`, so `gvf_2018a` took the serial branch: the **C6-70f prepared
   dispatch and the C6-70g postprocess hook were never exercised by the differential**,
   and W1 admission was bypassed with `execute_tiles` swapped. The .md's "Whole-pipeline
   A/B" framing overstates coverage; its Limits section does not name the GVF gap. The
   GVF wiring is currently gated by the family suites (217 tests, re-run green by me,
   including the wired `prepared_gvf_step`/`gvf_postprocess_block` paths and the
   engine-dispatch argument identity), which is adequate for correctness review — but a
   threads>1 differential (or a recorded rationale that the one-line dispatch swap plus
   family coverage closes the gate) is owed before any performance promotion that
   includes the GVF hooks.
3. **F3 (minor, deferred coverage — record as accepted residual or schedule).** C6-10
   review Finding 2 asked for the full census step-E matrix at C6-70. Delivered:
   corruption (array payload, visibility payload, forged manifest), stale-source rekey,
   integrated cold/warm/cache-disabled censuses. Still absent: metadata perturbation
   (geotransform/projection), DEM/DSM content perturbation (only Trees was perturbed),
   patch-table/profile/implementation perturbation, input mutation during preparation,
   concurrent readers/producers, overwrite=False failures. Mitigation: implementation
   perturbation rekey follows from the fingerprint closure, and concurrency/overwrite
   semantics are store-level code the range does not touch — but the residual should be
   dispositioned explicitly, not silently dropped.
4. **F4 (informational, robustness).** Demand-profile holder asymmetry: Lside profile
   is `threading.local()`; both cylinder profiles are module globals. Correct under the
   shipped sequential per-process scheduler (and the C6-21 recipe documents the choice),
   but any future in-process concurrent tile runner must first convert the cylinder
   holders or serialize tiles. Also: the reduced-profile gate in `pipeline.py:260` is an
   `assert`, skipped under `python -O`; numerics stay safe regardless because every
   reduced path re-verifies admission in its own dispatcher, but the loud-misuse
   guarantee is lost under -O.
5. **F5 (informational, documentation precision).** (a) The C6-21 recipe note "same
   runtime block_pixels/parallel the current wrapper used" is imprecise: base used the
   wrapper defaults (128, True); the wired call passes runtime-resolved values
   (`block_pixels`, `threads_per_worker > 1`). Numerically pinned by the proven
   block/parallel invariance evidence and the L2 differential (all 24 longwave primary
   outputs identical), so no defect — but the recipe wording should not be cited as the
   equivalence proof. (b) The probe's `collect()` silently drops non-array/non-scalar
   objects (NOT_REQUESTED sentinels, the `demand=` enum), which produces the claimed
   log normalization but would also hide a sentinel-instead-of-array arity defect; here
   the fixed 6-name engine unpack makes that impossible. (c) The C6-70e "recorded
   ledger sign-off note" for the `_fused_enabled()` deviation lives only in the commit
   message; an evidence-tree note would be more durable. (d) W3 overrides a user-set
   parent `GDAL_CACHEMAX` in children (recipe-proposed, intentional cap; the calculator
   docstring already tells explicit-setters to pass `gdal_cache_bytes`).

## Conditions (for APPROVE-WITH-CONDITIONS)

1. **F1 disposition**: guard the empty-jobs case or record the stricter ValueError as
   accepted public behavior in `evidence/integration/` (one line of code or one
   paragraph of evidence; either is acceptable).
2. **F2 closure before GVF-inclusive performance claims**: one threads_per_worker>1
   in-process or L2 differential covering the wired `prepared_gvf_step` +
   `gvf_postprocess_block` path against base, or a recorded rationale that the family
   suites' wired-tree bitwise coverage plus the argument-identity dispatch swap close
   the gate. Correctness approval of the landed code does not wait on this; performance
   promotion does.
3. F3 may be closed by an explicit accepted-residual note listing the uncovered step-E
   cases; no rerun required for this approval.

## Review-method footprint

All verification ran in the integration worktree read-only except this review file.
Commands: `git show`/`git diff` per commit; normalized line comparison of recipe
patches vs applied diffs; AST public-surface comparison base vs head; NDJSON log
recomputation (per-label streams, per-event input/output hash equality, longwave
out[0]/out[1] direct pairing, interleaving pattern, output-hash file diff); scoped
pytest runs as listed above (one process, `NUMBA_NUM_THREADS=2`). No file outside
`optimization_v6_continue/evidence/reviews/` was modified; no full suite, no
chronology probe rerun, no benchmarks.
