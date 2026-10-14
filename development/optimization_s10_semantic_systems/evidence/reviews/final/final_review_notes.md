# S10-33 final independent review — notes

Reviewer: independent final reviewer (not the author/coordinator session).
Reviewed at branch tip `e2cac7094f34812cae1bb82f7f2f9a0b757e017c`,
main-of-record `b3e5ca59a1080f02eda5ccda5e35a66af07e4bfa` (read-only, verified
untouched after all probes). Date: 2026-10-14.

Scope: re-execution of every cheap check; recorded evidence read for the rest.
No timing benchmarks were re-run (per brief). Scripts used live in
`/tmp/s10_33_audit/` (outside the repo). My only repo writes are this file and
`verdict.json` in this directory.

## Verdict summary

- **Verdict: approve_with_notes.**
- **Terminal state recommendation: `qualified_exact_cpu`**, with
  `actual_target_status = "unverified"` kept as a separate decision field.
- **Route-pin ruling: `update_pin`** (disclosed contract change by the
  author/integrator, keeping every exactness assertion; fallback
  accept_with_disclosure if not landed — see Q2).

## a) Freeze integrity — RE-EXECUTED, PASS

```
git diff --quiet c245ea60f32b2ca93191ea00f48a4f6085a60a2b HEAD -- src pyproject.toml
# exit 0 (empty diff)
git rev-parse main            # b3e5ca59a1080f02eda5ccda5e35a66af07e4bfa
```
Branch product source == the S10-30 campaign's B side (c245ea60), proven again
at the current tip.

## b) S10-30 gates — RECOMPUTED FROM RAW, PASS

Read `evidence/trials/protocol_frozen.json` (frozen-before-timing; gates:
geomean application speedup >= 1.10 from per-cell paired-median B/A; protected
regression bound <= 1.03; eligible-route coverage >= 0.8; `limits.
causal_large_retry_max = 1`; decision_rule predeclares "inconclusive noise ->
rerun within causal_large_retry_max or call it inconclusive, never 'passed'").

My own recomputation from `evidence/trials/raw_trials.jsonl` (47 records:
34 timed warm + 2 cold + 2 prime + 8 coverage/crosscheck + 1 refusal):

| cell | paired B/A ratios | median |
|------|-------------------|--------|
| P1 orig pairs 1-3 | 1.1629, 1.1938, 0.7714 | **1.1629** (noise-inconclusive) |
| P1 retry pairs 4-6 | 0.3546, 0.4555, 1.0054 | **0.4555** |
| P2 | 7.245, 0.2432, 0.9543 | **0.9543** |
| P3 | 0.8218, 0.3127, 0.4630 | **0.4630** |
| P4b | 0.7619, 0.6485, 0.6530 | **0.6530** |

```
geomean(P1_orig, P2, P3, P4b medians) = 0.7611  -> speedup 1.314  (gate >= 1.10 PASS)
alt geomean with P1 retry median      = 0.6021  -> speedup 1.661
```
Matches `evidence/selection/selection.json` exactly (0.7611 / 1.314), including
its explicit note that the aggregate uses P1's ORIGINAL conservative median and
"never folds" the retry into it. Wall values cross-checked per pair.

Coverage (from the `coverage P1/P2/P3` records, B arm):
Lcyl_v2022a 24/24 primary + define_patch_characteristics 24/24, 0 reference;
prepared_gvf 14/14, serial_gvf 0; anilum_packed 14, declines 0; Lside demanded
24 = 17 dispatch primary + 7 upstream fast, reference 0; kside 14. Fractions
1.0 per cell >= 0.8 gate; zero reference fallbacks. PASS.

Crosschecks (B run vs recorded A run per cell, frozen comparison_v1 budgets):
P1 4.58e-4, P2 0.0 (bitwise, all 10 files), P3 4.58e-4, P4a 4.58e-4 (2 tiles),
P4b 2.75e-4 — all far inside atol 0.05 (Ldown rule). PASS.

Retry usage vs predeclared rule: exactly one retry, on P1, granted under the
predeclared "inconclusive noise" branch (original ratios span both directions,
B won pair 3 by 24%); `causal_large_retry_max = 1` not exceeded; the retry is
reported alongside, not folded into the aggregate. The protected-regression
verdict ("PASS after retry resolution") honestly discloses that the gate rests
on the retry arm. See finding F2.

P4a: matched pair unevaluable — A (main, pre-S03b) refuses the predeclared
9.6e9 budget (recorded refusal with exact numbers: needs 21,066,014,387 B vs
9,170,503,270 B remaining; 24e9 also refused); B ran 3/3 at the predeclared
budget; the A-side 44e9 probe (87.098 s) is disclosed as options-asymmetric and
excluded from gate arithmetic. P4a tile outputs bitwise-match the P1
in-process outputs on both arms. Honest exclusion, recorded as a first-class
S03b ops finding.

Noise disclosure verified in raw records: loadavg 12-20 across the window; 7x
within-arm bursts (A P2 42.2 s vs 201.9 s; B P2 305.6 s vs 49.1 s); priming
runs kind='prime' excluded from gates; cold leg recorded separately
(A 44.437 s / B 43.678 s).

## c) S10-31 wheel DX — RE-DERIVED FROM THE ARTIFACT, PASS

Artifact: `/tmp/s10_31_work/dist/solweig_light-0.1.0.dev0-py3-none-any.whl`
(exists, 349,870 bytes).

```
sha256sum <wheel>  # 6728b6cbf5f3f431be0780595e33996ec743aa9aad289fc6dcdd0a18c5889912
```
Matches `wheel_manifest.json` and `installed_results.json`.

Unzipped to a fresh dir and verified:
- RECORD members: 79 (`wc -l RECORD`) == manifest `record_members: 79`
  (73 under `solweig_light/` + 6 dist-info).
- Top-level: only `solweig_light` + `solweig_light-0.1.0.dev0.dist-info`
  (== manifest `top_level_packages: ["solweig_light"]`; no
  original-upstream module names).
- Prefix scan `tests/|development/|experiments/|captures/|handover/|docs/`:
  zero hits (grep + find). Suffix scan `.jsonl|.npz|.nc|.tar|.tar.gz|.log|
  .ipynb`: zero hits. Native/scaffolding tokens `.so|.dylib|.dll|
  native_generated`: zero hits (grep on RECORD and find on disk).
- `entry_points.txt`: `[console_scripts] solweig-light =
  solweig_light.cli:main`. ✓
- `WHEEL`: `Root-Is-Purelib: true`, tag `py3-none-any`, generator setuptools
  84.0.0. Pure claim ✓.
- Requires-Dist identity vs `git show b3e5ca59:pyproject.toml`, normalized
  (lowercase name, sort comma-separated clauses, group by `extra == "..."`):
  runtime 6/6 identical; extras test 2/2, forcing 5/5, wind 3/3, inputs 14/14
  identical. Setuptools clause reordering (`gdal<3.14,>=3.13` vs
  `>=3.13,<3.14`) confirmed as the only difference raw. ✓
  (`/tmp/s10_33_audit/reqcheck2.py`, output: all `identical=True`.)

## d) Blocked api/cli dispositions — VERIFIED HONEST; Q3 ruled below

`installed_results.json` api_gate + cli_gate each carry:
- 3 attempts + 1 `GDAL_CACHEMAX=64` diagnostic;
- all refused by `solweig_light.runtime.ResourceAdmissionError` raised at
  `runtime_memory.py:931` in the INSTALLED wheel venv
  (`/tmp/s10_31_work/wheelenv/lib/python3.12/site-packages/...`);
- exact per-attempt byte numbers, all consistent: phase need 4,310,409,420 B
  (crop-independent; patches=153 is a model constant) vs 1,837,946,470 -
  1,899,632,230 B free of 2,267,443,200 - 2,329,128,960 B budget (cgroup
  headroom drift between attempts);
- `output_files: []`, `status: "blocked:host-memory-pressure"`,
  `returncode: 1` — no fake pass;
- stdout shows REAL pipeline start on every attempt (metfile copy, SVF
  calculation complete, `Running Solweig ...`) before the simulation-phase
  refusal;
- env discipline: `env_keys` = HOME/LANG/LD_PRELOAD/NUMBA_CACHE_DIR/PATH/
  PYTHONPATH/SOLWEIG_NO_NET_LOG; `BACKEND_ENV_VARS` (9 package-read vars incl.
  GDAL_CACHEMAX) asserted ABSENT (not merely overwritten) by the committed
  test; PYTHONPATH carries only the network-guard dir (sitecustomize), not the
  repo; site-packages read-only (0o555/0o444) with restore policy.

The blocked branch is implemented in the committed test itself
(`tests/optimization_s10/installed/test_installed_dx_gates.py:238-262`):
no-env mechanics asserted for every child; admission refusal recorded as
first-class `blocked_by_resource_admission` environmental; output checks apply
only to completed runs. Not an after-the-fact relaxation.

Environmentality: `ResourceAdmissionError` exists at main
(`git show b3e5ca59:src/solweig_light/runtime_memory.py` re-exports it; C6-42
admission model is upstream). Main pre-S03b charges 5%-of-physical GDAL cache
(~18.8 GB) vs the candidate's container-aware min(physical, cgroup) (~3.4 GB),
so main would refuse this phase HARDER. The refusal is a host-memory-view
property, not a candidate defect.

LD_PRELOAD shim: disclosed per run (`deployment_shim` +
`deployment_shim_note`) and in `installed_test_helpers.py` with the correct
mechanism (locally-built GDAL wheel's `osgeo/_gdal.so` DT_RPATH pins a
libstdc++ lacking CXXABI_1.3.15; DT_RPATH outranks LD_LIBRARY_PATH; any
osgeo-first process fails; the product pipeline imports numpy first, the
thermal_comfort/CLI entries import osgeo first). Correctly characterized as
version-independent (property of the host GDAL wheel, applies to a baseline
install identically, sets no product behavior) — consistent with the
documented host quirk.

## e) Merge rehearsal — REDONE INDEPENDENTLY, MATCH

```
git worktree add --detach /storage/scratch1/1/dsynn6/solweig-light-s10-raw/s33_final_review_wt b3e5ca59...
git -C <wt> merge --no-ff --no-commit e2cac709...   # "Automatic merge went well"
git -C <wt> write-tree                               # d215f7db62ee59629cf99caed68646bbde6f2ccc
git -C <wt> merge --abort; git worktree remove <wt>
```
My merged tree SHA equals the recorded `merge_rehearsal.json`
`merged_tree_sha` AND the branch tip tree (`git rev-parse e2cac709^{tree}` =
same SHA; expected — merge-base b3e5ca59 == main tip, so integration is a
fast-forward; `--no-ff` exercised merge-commit construction anyway).
`diff --stat` main..tip = 116 files changed, 14044 insertions(+), 29
deletions(-) — matches the recorded stat. `git rev-parse main` afterwards =
b3e5ca59 (untouched). Worktree list clean afterwards. No conflicts, no
automatic merge/PR/push performed.

## f) Required checks — VERIFIED (failsets + re-runs)

Read `evidence/reviews/final/required_checks_local.json` and the raw lists in
`/tmp/s33_failsets/`.

(i) installed vs checkout: my extraction of `FAILED <id>` lines gives
identical ID sets in all four steps (step1 1/1, step2 2/2, step3 28/28,
step4 5/5), counts matching the recorded "28 failed, 24 passed" (branch) /
"20 failed, 32 passed" (main) for step 3. Note: the raw .txt files are NOT
byte-identical as files — they embed per-run pytest timing lines and
installed_step3.txt additionally carries pytest assertion-detail lines (62 vs
30 lines). The claim "BYTE-IDENTICAL failure-ID sets" is accurate for the ID
sets; the wording "(diff empty)" refers to the set diff. Finding F1.

(ii) branch vs main: steps 1/2/4 identical sets; step-3 delta is exactly 8 IDs
— all `test_dispatch_preserves_every_field_mutation_and_error[budget-1-gvf_*]`
(beyond_raster, nan_buildings, nan_shadow, nan_temperature, nonbinary,
rounding_half, rounding_scale, water); main-minus-branch = 0. Main's own 20 =
budget-4 + budget-10 across all 10 gvf cases (verified from
main_step3.txt) — i.e. the SAME route-pin category already failing on main for
multi-thread budgets since the pre-S10 C6-30 prepared route. The two remaining
budget-1 cases (zero_distance, float64) fail on NEITHER side (declined by the
single-thread guard union, delegate to the spied serial). All as recorded.

(iii) Re-executed one delta case:
```
.venv/bin/python -m pytest "tests/differential/test_ground_view_dispatch_exact.py::test_dispatch_preserves_every_field_mutation_and_error[budget-1-gvf_water]" -q
# FAILED ... AssertionError: assert [] == ['gvf_2018a']
#   at tests/differential/test_ground_view_dispatch_exact.py:126
# 1 failed in 120.42s
```
The failure is exactly the ROUTE assertion (`calls == []` vs `['gvf_2018a']`);
the preceding loop ran all 17 field comparisons through `exact()`, which is
bit-exact (shape, dtype, NaN-position, and unsigned-int-view payload
equality — test lines 55-67), and none of them failed. Confirmed.

Route architecture confirmed at `src/solweig_light/radiation/engine.py:1762-
1784`: `gvf_2018a` dispatches threads>1 to `prepared_gvf_step(parallel=True)`
(the pre-S10 accepted C6-30 multi-thread route) and threads==1 to
`prepared_gvf_step(parallel=False, ...)` with a `delegate=` to the exact
serial baseline for inputs the guard union declines (S10 G01); kill switch
`SOLWEIG_LIGHT_GVF_PREPARE=0` documented at lines 1773-1774 and 1779-1780.

Test-file integrity: `git diff b3e5ca59 HEAD --
tests/differential/test_ground_view_dispatch_exact.py` is EMPTY (byte-identical;
no branch commit touches it). The branch's only tracked-test edit is
`tests/unit/test_exact_cpu_pairs.py`, a one-line tools path fix
(`tools/` -> `development/tools`); no assertion weakened.

My additional re-runs at the tip:
```
pytest tests/optimization_s10/{fixtures,residual,semantic} -q   # 83 passed in 84.10s
pytest ".../test_chronological_tiff_pipeline[landcover-False]"
       ".../test_chronological_tiff_pipeline[landcover_normalized-False]" -q
                                                                # 2 passed
```
Matches the recorded S10 83/83 and landcover-golden 2/2 gates.

## g) S10-32 target status — VERIFIED HONEST

`evidence/target/target_status.json`: disposition `unavailable`,
`actual_target_unverified`. Spot-checked the availability audit:
- `du -sh tests/reference` = 45M (small regression fixtures only);
- `/storage/scratch1/1/dsynn6/campaign_data/inputs` (2.7 GB): my own
  `find ... -iname '*.tif' -o -iname '*.tiff'` returns NOTHING; contents are
  flow-network/UNA-tutorial project data (geojson/csv/docx/qmd), no SOLWEIG
  DSM/DEM/Trees rasters;
- `/storage/scratch1/1/dsynn6/{data,datasets}`: unrelated preference/motion ML
  datasets.

The disposition correctly applies BENCHMARK_PROTOCOL "Actual target" (24 real
spatial tiles, nominal 1024^2, 24 steps; "Single success is demonstrated_once;
two scenes x 24 hours is two spatial jobs, not 24") and PLAN Phase 4
("If actual data ... are missing, record actual_target_unverified. Do not
fabricate a 24-tile corpus from two motif scenes"). Declaring unavailable was
the only honest option; no fabrication occurred.

## h) Wheelhouse + Dropbox — SPOT-CHECKED, PASS

Wheelhouse dir has 13 wheels (12 runtime closure + setuptools seed).
3 of 13 sha256s recomputed and matched `installed_results.json["wheelhouse"]`:
```
gdal-3.13.3-...   43d59dbe0d00903dc8f7a21498e3f851206925167e7ce03cecdeea900d78188b  OK
numpy-2.4.6-...   b6de13f090c8a6ee1202a5799731aa79ccfdbc7dc3b383a17c189a9c0817dda5  OK
numba-0.67.0-...  95ec99a3e925fa92820d9fbf33b87f5c50e5da4cc4eb39f71bfbc01f03eceb84  OK
```
Dropbox (read-only `dbxcli ls "Alan Synn/Research/solweig-light/s10"`):
`s10_s31_installed_whl.tar.gz` + `.sha256` sidecar present, plus
`s10_s30_trials.tar.gz` + `.sha256` (the S10-30 raw archive claimed in
selection.json). Both claims verified.

## Judgment questions

**Q1 — Terminal state.** `qualified_exact_cpu` qualifies.
DECISION_AND_MERGE.md and PLAN Phase 4 define goal achievement, campaign
closure, native qualification, actual-target status and merge readiness as
SEPARATE fields, and Phase 4 explicitly says missing actual data is recorded
as `actual_target_unverified` — it is not a terminal-state downgrade.
Nothing forces `retained_main_no_material_gain` (the candidate demonstrably
helps: 1.314x paired-median geomean on held-out cells, corroborated by
in-process 2.96x warm-tile spans) and nothing forces
`blocked_no_safe_merge` (correctness crosschecks inside frozen budgets, P2
bitwise, DX structurally proven by my independent wheel re-derivation, merge
rehearsal reproduces exactly, no security findings — dependency set unchanged
from main). Conditions: keep `actual_target_status` separate; no
production-scale performance claim (production-scale throughput is unmeasured);
carry the two blocked/environmental items into the decision record.

**Q2 — Route-pin finding.** Ruling: **`update_pin`**, executed by the
author/integrator as a separate disclosed commit, NOT by this reviewer.
Rationale: the pin (`calls == ['gvf_2018a_parallel' if threads>1 else
'gvf_2018a']`) encodes a superseded route contract — main's own accepted,
pre-S10 C6-30 architecture already violates it for every multi-thread budget
(main fails 20/30 today, with the test file unchanged). S10 G01 extends the
same accepted architecture to threads==1 with a delegate for declined inputs
and a runtime kill switch; in all 8 new failures the 17 fields are bit-exact
and only the route assertion fires. Merging with the pin untouched would ship
28 known-failing "permanent regression" tests and destroy the differential
gate's signal. The update must pin the ACCEPTED route semantics (prepared
route engagement incl. the delegate-declined cases), keep every `exact()`
assertion and the decline behavior assertions, be disclosed as a contract
change in the decision record, and leave the full 30-case matrix green. If the
author prefers not to touch the test pre-merge, `accept_with_disclosure` with
all 28 enumerated in FINAL_DECISION.json is the acceptable fallback; `block`
is unwarranted (zero numerical divergence).

**Q3 — api/cli blocked dispositions vs the S10-31 completion condition.**
YES. The packet's condition is "required checks pass or blocking status
recorded". The blocking status is recorded first-class with complete attempt
evidence (3 attempts + GDAL_CACHEMAX=64 diagnostic, exact byte numbers,
identical refusal each time), the blocked branch is coded in the committed
gate test (no-env mechanics still asserted; outputs checked only on
completion), and the block is demonstrably environmental: the admission model
is upstream main code, main pre-S03b refuses the same phase harder, and the
author declined to force it (page-cache reclaim in a shared cgroup = OOM risk
to co-tenants; a resource-tuned override would not be unchanged-default DX
proof). No fake pass exists anywhere in the record.

**Q4 — Overstatements / inconsistencies / reproducibility.** Everything I
re-executed reproduced exactly (freeze diff, geomean/medians, coverage,
crosscheck magnitudes, wheel sha/structure/requirement identity, 3 wheelhouse
sha256s, merged tree SHA, failset set-equality and the exact 8-ID delta, one
delta case failure mode, 83-test S10 suite, landcover goldens, Dropbox
archives). No fabrication found. Findings F1-F6 below; none blocking.

## Findings

- **F1 (note, wording):** `required_checks_local.json` says "BYTE-IDENTICAL
  failure-ID sets ... (diff empty; raw lists in /tmp/s33_failsets/...)". The
  ID sets ARE identical (verified for all four steps), but the raw .txt files
  are not byte-identical as files (embedded per-run timing lines; step-3
  installed list also carries pytest assertion-detail lines, 62 vs 30 lines).
  Substance holds; a reader diffing the raw files byte-wise would see noise.
- **F2 (minor):** The S10-30 protected-regression gate passes only through the
  single predeclared causal retry (P1 original median 1.163 > 1.03 bound;
  retry median 0.456). The retry is predeclared (decision_rule +
  `causal_large_retry_max = 1`), used exactly once, and the headline geomean
  conservatively keeps 1.163 (using 0.456 would give 1.66x). Correctly
  disclosed as "PASS after retry resolution". Noted because the terminal
  speedup/regression claims genuinely rest on the retry arm plus the in-process
  corroboration, under heavy host contention.
- **F3 (minor):** Raw failset lists and some working artifacts live in /tmp
  (volatile). Durable conclusions are recorded in the repo, but the raw lists
  should be archived to Dropbox per the evidence-storage policy or their
  ephemerality noted in the merge manifest.
- **F4 (note):** P4a is excluded from the gate geomean (matched pair
  unevaluable; main pre-S03b refuses the predeclared 9.6e9 budget — exact
  refusal bytes recorded). Disclosed prominently as a first-class S03b finding;
  the B-side pool-tile bitwise identity to P1 outputs covers correctness.
- **F5 (note):** The protocol's P2 expectation ("no gvf demand surface on
  base") was wrong; observed prepared_gvf 14/14 with 0 serial. Corrected by
  observation and disclosed; no ratio impact (P2 outputs bitwise-identical,
  median 0.954).
- **F6 (note):** P1 executed 6 timed pairs (initial 3 + retry 3) plus untimed
  priming runs against a protocol line reading `pairs_per_cell: 3`. The retry
  and priming are both disclosed and correctly excluded/segmented in the
  aggregate; no gate consumed the extra data improperly.

## What I re-executed vs only read

Re-executed: (a) freeze diff; (b) full recomputation of all paired medians,
the gate geomean, coverage fractions and crosscheck magnitudes from
raw_trials.jsonl; (c) wheel unzip + all structural/dependency checks +
sha256; (d) record inspection + upstream admission-model presence check +
env-construction code inspection; (e) full independent merge rehearsal in my
own detached worktree; (f) failset set comparisons and delta arithmetic, one
delta-case pytest re-run, engine code inspection, test-file diff, 83-test S10
suite, 2 landcover goldens; (g) du/ls/find spot-checks of the availability
audit; (h) 3 wheelhouse sha256s + read-only dbxcli ls.

Read-only (not re-executed, with reasons): S10-31 installed 7/7 suite runs
(heavy venv/wheel rebuild; structural claims independently re-derived, 7 gate
functions inspected); CI-matrix surrogate steps 1/2/4 full runs (recorded
ID sets verified and partially re-executed at the tip); main-worktree 20-failure
re-derivation (main worktree disposable, main read-only; 20 IDs verified from
the recorded main_step3.txt and consistent with the unchanged test file);
S10-30 walls (re-running timing benchmarks forbidden by brief); Dropbox
archive contents beyond listing (download not needed for the ruling).
