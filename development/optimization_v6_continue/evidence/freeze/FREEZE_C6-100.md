# C6-100: final candidate freeze record

Date: 2026-09-21. Owner: C6-100 evidence worker. Evidence only — nothing
committed; the integrator commits this directory. This is a freeze and
correctness-gate record: **it contains no statistical claims and no
timing claims.** All elapsed values that appear are recorded run
telemetry, not claims.

## Frozen source

- Tree: `/Users/alansynn/Workspace/solweig-light-claude-v5`,
  branch `perf/claude-glm53-cpu-v5`
- Frozen rev: **`ea2eed53a3338f2bd45b7dfac364efe20ecd3084`**
  (`git rev-parse` verified at freeze time; `src/` and `tests/` clean,
  zero modifications, before and after all gates)
- `src/` delta vs the wave-1 base `8e0b3877` (shortstat): **10 files
  changed, +1173/−86**

| file | Δ (+ins/−del) |
|---|---|
| src/solweig_light/api.py | +83/−0 (C6-42 W1 phase admission + `if jobs` guard; C6-40 phase route) |
| src/solweig_light/geometry/service.py | +10/−30 (C6-70a shared numerical geometry recipe + identity/key) |
| src/solweig_light/geometry/visibility_prepared.py | +19/−1 (C6-50 module; C6-81 default-declined opt-in gate) |
| src/solweig_light/pipeline.py | +63/−39 (geometry producer/key wiring; C6-70d/i demand scopes) |
| src/solweig_light/radiation/engine.py | +18/−9 (C6-20/C6-21/C6-30 dispatch) |
| src/solweig_light/radiation/ground_view.py | +9/−3 (C6-31 wrapper in `_gvf_fused`) |
| src/solweig_light/radiation/gvf_postprocess.py | +10/−3 (dtype guard, f64 lup_term to reference) |
| src/solweig_light/radiation/patch_radiation.py | +21/−1 (C6-22 shortwave hook; C6-50 decoder wiring, gated) |
| src/solweig_light/runtime.py | +6/−0 (C6-42 W3 GDAL_CACHEMAX cap) |
| src/solweig_light/runtime_phases.py (new) | +934/−0 (C6-40 geometry phase adapter) |

Exact per-file counts: `git diff --numstat 8e0b3877..ea2eed53 -- src/`.
Commits after the C6-80 measurement tree (`76bcd288`): C6-81 selection,
decoder default-decline (`46450c75`, src delta confined to
`geometry/visibility_prepared.py` +19/−1), C6-81 review, C6-99 — i.e.
the only functional change after measurement is the C6-81 opt-in gate.

## Math profile fingerprint (frozen)

- Portable profile id: **`solweig-portable-sleef-5a1d179d-v1`**
- Fingerprint: **`8e4d38460b61b0299e7c1d525c8499750dcd219ef01cc785d7496dbe1dcbef30`**

Verified two ways at the frozen rev: computed live from the frozen tree
(`PYTHONPATH=src`, project venv) and read back from the C6-80 portfolio
child records (`evidence/portfolio/runs/t128_S1/integrated/records/*.json`)
— identical. Implementation identity: SLEEF commit
`5a1d179df9cf652951b59010a2d2075372d67f68`, coefficient policy
`numpy-float64-cos-tan-scalar-v1`; runtime: CPython 3.11.16, numpy 2.4.6,
numba 0.67.0, llvmlite 0.49.0, GDAL 3.13.3, arm64/Darwin. The wheel gate
(below) recorded the same fingerprint inside both the installed-wheel and
src-tree runs.

## Pinned RuntimeOptions / budget policy

Following the C6-80 protocol: runtime options are **pinned, not auto**,
because the auto memory budget derives from currently-available memory and
is availability-sensitive. Pinned cell used by the freeze gates:

```
memory_budget_bytes = 12 GiB, cpu_budget = 4, workers = 1,
threads_per_worker = 1, block_pixels = 1024, checkpoint_interval = 1,
cache_enabled = True, legacy_cache_policy = "recompute"
```

(worker/phase variants of the C6-80 portfolio additionally used workers=2 /
threads=2 cells under the same pinned budget). Native thread limits are set
in the child environment **before the first numerical import** (all seven
thread variables), and the mask is verified from `numba.config` /
`get_num_threads`. The raw-True admission failure below is a direct
demonstration of why the budget is pinned: the unpinned auto budget
rejected under current host load.

## Wheel gate (installed-wheel deployment parity) — PASS

Full record: `wheel_gate/wheel_gate_summary.json`; child records
`wheel_gate/wheel_child.json`, `wheel_gate/src_child.json`.

1. **Build**: `python -m pip wheel . --no-deps` from the frozen tree
   (PEP 517, setuptools.build_meta) →
   `solweig_light-0.1.0.dev0-py3-none-any.whl`, sha256
   `368b15afdf757b91ec039daf7b5d82c42a5a2cc101a15933a2defe975256f8d1`.
2. **Install**: fresh throwaway venv `wheel_gate/fresh_venv`
   (`python -m venv --system-site-packages` from the project-venv
   interpreter) + `pip install --no-deps <wheel>`. Third-party deps
   (numpy/scipy/numba/GDAL/pytz/timezonefinder — same versions as the src
   side) resolve via a `.pth` to the project venv's site-packages;
   `solweig_light` is NOT installed there, so the wheel is the only
   solweig_light on the path. Import origin asserted:
   `fresh_venv/lib/python3.11/site-packages/solweig_light/__init__.py`.
   **No PYTHONPATH into src anywhere on the wheel side** (env `-u
   PYTHONPATH`; recorded `pythonpath_env: null`).
3. **Scene**: one tiny end-to-end run per side — the in-tree true fixture
   `tests/reference/small_original_cpu/scene` root files (35×32, 1 tile,
   24 met records), copied fresh into each run root; full public
   `api.thermal_comfort` entry (preprocess → walls/aspect → SVF →
   simulation, 10 save flags); pinned options above; `NUMBA_NUM_THREADS=1`
   pinned identically on both sides; fresh `NUMBA_CACHE_DIR` per side
   (cold JIT both); worker children inherit the same environment, so the
   src side's children import `src/` and the wheel side's children import
   the installed wheel. Both runs completed, exit 0, math profile
   fingerprint identical.
4. **Comparison (sha256 per file, classified)**:
   - `output_folder/0_0/` — the 10 simulation output TIFFs (Kdown, Kup,
     Ldown, Lup, Shadow, TMRT, Ta, UTCI, WBGT, Wind): **10/10 bitwise
     identical** between installed wheel and src tree.
   - `processed_inputs/` published artifacts: 8/9 bitwise identical
     (tile TIFFs, SkyViewFactor, shadowmats NPZ, aspect, walls, metfile).
     The one difference, `svfs_0_0.zip`, differs **only in ZIP member
     timestamps** — all 15 members are content-identical (CRC + size +
     data sha256 checked member-by-member), exactly the C6-80 verdict-5
     artifact churn.
   - Geometry export manifest: differs only in (a) the svfs zip digest,
     (b) `numerical_recipe.digest`, (c) its own self-digest. Root cause
     verified, not assumed: `raster_fingerprint` captures all GDAL
     metadata domains, and GDAL's `DERIVED_SUBDATASET` strings embed the
     raster's **absolute path**, which necessarily differs between
     `run_wheel/` and `run_src/`. Recomputing the recipe in BOTH
     environments over the SAME paths yields byte-identical identity
     documents and digests (`wheel_gate/recipe_probe.py`,
     `ident_wheel.json` vs `ident_src.json`). All implementation files in
     the identity closure are byte-identical between src and the
     installed wheel (checked individually).
   - Internal bookkeeping (`.solweig-light` transactions, random-named
     lock files): 49 run-unique files per side; not outputs, not
     comparable by design.
5. **Verdict: PASS — numerical outputs bitwise identical from the
   installed wheel and the src tree.** Nothing was tuned.

## Scoped true-TIFF / chronological-state gates

Commands, counts, loadavg before each run, and the verbatim failure are in
`gates_summary.json`. Discipline: single process, sequential, project
venv, `PYTHONPATH=src`, `NUMBA_NUM_THREADS=2`.

| gate | result | verdict |
|---|---|---|
| `tests/optimization_v6/geometry_recipe` | 8 passed (21.27 s) | PASS |
| `tests/optimization_v6/phases` | 17 passed (20.31 s) | PASS |
| `tests/differential/test_pipeline_reference.py` (small_original_cpu-driven real-TIFF + chronological suite) | 1 failed, 8 passed (9.11 s) | **FAIL recorded** (raw-True) |

Failed case verbatim (full capture in `gate_raw_true.full.txt`):

```
solweig_light.runtime.ResourceAdmissionError: simulation job 0_0 (32x35, patches=153) needs
about 1,736,017,587 B but only 1,307,272,806 B of the 1,736,769,536 B budget remains after
parent (429,496,730 B) and writer queue (0 B); queueing cannot make this phase fit. Reduce
the tile shape, cap GDAL_CACHEMAX, or use supported disk-backed execution with an explicit
live-array inventory
```
at `src/solweig_light/runtime_memory.py:919`.

Classification recorded (for the integrator to disposition — **not
fixed, not worked around**): the `raw` case drives the public
`thermal_comfort` entry with **unpinned auto** runtime options; admission
rejected before any worker spawned because the availability-sensitive
auto budget left insufficient headroom under the current host load
(session has other active agents; loadavg 6–8). No numerical comparison
ran in that case. The same suite's two `small` chronological
TIFF-to-TIFF cases against the original-CPU artifacts both passed, and
the identical public entry over the same fixture completed twice in the
wheel gate under pinned options with bitwise-identical outputs.

Evidence restoration after the gate runs: `git checkout --
optimization_v6_continue/evidence/recipe optimization_v6_continue/evidence/census`
(19 tracked files restored; untracked raw run records left in place).

## TARGET SCOPE — the actual target dataset is STILL ABSENT

**The actual 24-spatial-tile workload dataset does not exist in this tree.
Consequently the C6-101 single large campaign (budget ≤ 1800 s) has NO
frozen real target.** No synthetic replication is a substitute (VALIDATION_POLICY
"Final-only campaign": synthetic replications are load tests, not the
actual-target dataset).

What the C6-101 campaign WOULD run once the dataset exists, per the frozen
protocol skeleton (all items below remain UNFROZEN until the dataset
exists and the protocol is finalized before the run):

- **24 distinct spatial target tiles** at true extents/overlap/physical
  resolution — counted as spatial tiles, separately from bands and scenes;
- each tile with the **full chronological 24-record state sequence**
  (every carried state compared/handled at every small timestep per the
  frozen policy), own-met workflow, checkpoint=1 or an explicitly selected
  prior policy;
- **complete outputs** for all 153 patches per tile, durably published
  inside the campaign timer (timer starts before application imports/JIT
  for the frozen first-use mode and ends after all required artifacts are
  published);
- source at this frozen rev (or its one-causal-retry successor), the
  frozen math profile above, pinned RuntimeOptions, and a declared
  CPU/RAM/storage and cache regime.

**Until that dataset exists and the campaign runs: no actual-target claim
and no release timing claim exists anywhere in this tree.** The 1800-second
objective is NOT redefined by any dev-tier observation.

## Constraints / known-absent (explicit)

1. **24-tile dataset absent — C6-101 unverified.** See TARGET SCOPE. The
   L4 tier has never run; nothing here demonstrates or schedules it.
2. **All C6-80 numbers are dev-tier single-lease observations** on a host
   with documented unrelated system activity — cold/warm medians, −6.4/−9.8%
   (S1), −6.1/−16.2% (T2), −10.9% (P2 t256) — no statistical claims, no
   release claims; warm steady state was a wash at that tier.
3. **Prepared visibility decoder is default-DECLINED** (C6-81, `46450c75`):
   measured +21–24% per full-frame sweep; available only via opt-in
   `SOLWEIG_LIGHT_PREPARED_VIS=1`; adoption arguments limited to
   exactness/memory-profile, not latency.
4. **Phase-route t128 caveat**: the C6-40 GEOMETRY phase route is net
   negative at 128² tiles (child spawn + barrier overhead dominates) and
   paid off at 256²; its gate is `len(pending) > 1 and workers > 1 and
   cache_enabled`. Warm P2 re-fire under the public
   `validate_existing=True` wrapper semantics (~0.9 s) does not occur
   under production `thermal_comfort` semantics (C6-80 verdict 2).
5. **raw-True reference gate failing at this rev under unpinned auto
   budget** (admission rejection, recorded verbatim above) — open item for
   the integrator; the two `small` chronological cases pass.
6. Wheel-gate comparison caveats recorded honestly: svfs ZIP timestamp
   churn and the path-provenance `DERIVED_SUBDATASET` effect on
   `numerical_recipe.digest` are non-numeric (both verified as such);
   they are the only wheel-vs-src file differences besides run-unique
   bookkeeping.

## Artifacts (this directory)

- `FREEZE_C6-100.md` — this record
- `gates_summary.json` — scoped gate commands, counts, loadavg, verbatim failure
- `gate_raw_true.full.txt` — full pytest output of the failing case
- `wheel_gate/` — wheel, fresh venv, runner + probes, child records,
  manifests, `comparison_summary.json`, `wheel_gate_summary.json`,
  both run roots
