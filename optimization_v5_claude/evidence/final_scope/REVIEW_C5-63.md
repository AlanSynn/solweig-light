# C5-63 final evidence review — independent GLM review (Opus unavailable)

Reviewer: GLM-5.3 via Z.ai (Claude Code agent), fresh agent, no stake in prior
work. Date: 2026-09-21. Worktree:
`/Users/alansynn/Workspace/solweig-light-claude-v5` (branch
`perf/claude-glm53-cpu-v5`, HEAD `becb3841`). All verification below was
read-only (hashing, JSON inspection, git queries); no builds, no timed runs,
no writes outside `evidence/final_scope/`.

## Verdicts

| # | Claim | Verdict |
|---|---|---|
| 1 | L4 final campaign: both 1024 cases bitwise-pass vs reused v4 reference; timings as stated; combined wall ≤1800 s; no retry / no missing-reference capture / no new baseline | **CONFIRMED** |
| 2 | Parity-chain validity (v4 source ≡ 14e88876; v5 tip ≡ bfd9915e at L2; therefore bitwise equality at 1024 validates parity) | **CONFIRMED** |
| 3 | Freeze integrity (wheel sha256, built at d2edbc10; installed checks bitwise-PASS under py3.12 AND py3.11; v4-identical environment + profile fingerprint) | **CONFIRMED** (one minor unverifiable temporal, see 3.5) |
| 4 | Handover draft accuracy | **CONFIRMED WITH NOTES** (two phrasing overstatements on inherited dispositions, see 4.4) |

**Overall: ACCEPT-WITH-NOTES.** All core numerical claims were independently
re-verified from primary artifacts. The notes are documentation caveats, none
of which undermines the parity result or the target demonstration.

## What I ran, with results

### 1. L4 campaign (CAMPAIGN_v1.md, runs_v1/)

- **Full re-hash of all 20 candidate outputs** (10 per case, ~100 MB each) in
  `final_batch/runs_v1/{dense1024,vegetation1024}/scene/output_folder/0_0/`
  against `candidate_manifest.json` (sha256 + bytes): **20/20 match**. This
  exceeds the requested 3-per-case spot check.
- Same 20 recorded hashes compared against the v4 reference manifests at
  `reports/characterization/local_cpu_optimization_v1/qualification/final_combined_v1/large_harness/large_runs_v1/{case}/candidate_manifest.json`:
  **20/20 identical** (path set, sha256, bytes). The chain
  file → candidate manifest → v4 reference manifest holds end to end.
- Timings re-read from manifests/logs: dense1024
  `elapsed_diagnostic_seconds=289.764848` (claim 289.765 ✓), vegetation1024
  `302.395695` (claim 302.396 ✓); v4 reference `400.827113` / `341.365483`
  (claims 400.827 / 341.365 ✓). Speedups recompute to 1.3832× / 1.1289×
  (claimed 1.383× / 1.129× ✓). `stdout.log` of each run corroborates
  (`{"case": ..., "elapsed": ..., "outputs": 10}`).
- Combined wall: monitor `elapsed_seconds` 293.606 + 305.307 = **598.913 s**
  (claim 598.9 ✓), ≤ 1800 s target. Both monitors: `exit_code=0`,
  `aborted=false`, `abort_reason=null`; peak RSS 1 151 434 752 B (1.07 GiB)
  and 1 213 480 960 B (1.13 GiB) — matches CAMPAIGN table.
- Retry / baseline accounting: exactly one run directory per case (attempt 1
  of 1, consistent with `attempts_per_case: 1`); protocol records
  `new_baseline_runs: 0`, `missing_reference_captures: 0`; reference reuse is
  corroborated by the child command lines pointing at the existing v4 fixture
  paths and by the absence of any new-baseline artifacts.
- `run_kwargs_frozen.json` **exactly equals** the protocol's `batch.run_kwargs`.
- Interpretation limits are honestly stated: "Single pass, single host,
  `target_demonstrated_once`. Not a speedup distribution, not robustness
  evidence, not P7/P8 release qualification." Matches the protocol
  `claim_ceiling`. **No overclaim found.**

### 2. Parity chain

- `git merge-base --is-ancestor 14e88876 HEAD` → true.
- `git diff --stat 14e88876..bfd9915e -- src/ pyproject.toml tests/` →
  **empty** (exit 0). Claim reproduced.
- `git diff --stat d2edbc10..HEAD -- src/ pyproject.toml` → empty; working
  tree src/ clean. The wheel source, freeze source, and tip src/ are all
  identical, so the wheel that ran L4 corresponds to tip source.
- `evidence/l2/REFERENCE_bfd9915e_dense256.json`: `base_commit=bfd9915e…`,
  **23 files** recorded (matches "23 artifacts").
- Freeze installed checks
  (`freeze/installed_check_dense256.json`, `..._py311.json`): each records 23
  files; **both are path-identical and value-identical (sha256+size) to the
  reference**, i.e. bitwise-PASS under both interpreters at the recorded
  level. I additionally re-hashed all 23 recorded files in the still-present
  `/tmp/v5-installed-check` and `/tmp/v5-installed-check-311`: **23/23 and
  23/23 match**.
- Manifest field equality v5 vs v4 reference: `runtime_options` **equal**,
  `profile` (incl. fingerprint `8e4d3846…`) **equal**,
  `fixture_manifest_sha256` **equal** (and independently recomputed:
  dense fixture manifest `51e5aac79281…ad755d`, vegetation
  `6cc921803564…ed7ed5b7`, both exactly as in the protocol). Expected
  differences only: `schema` and `package_origin`/`module_origins` (different
  schema names and install roots by design).
- `verify_parity.py` reviewed: compares fixture sha, profile fingerprint,
  runtime_options, and full output sha256/sets. Sound. Note it compares
  manifest-to-manifest; the live-file gap is covered by my own re-hash above.
- Chain logic is valid **given** the two premises, both of which check out at
  the artifact level. The historical premise that the v4 reference manifests
  honestly describe a v4 run cannot be re-derived today; what is verifiable —
  reference integrity — was verified (below).

### 3. Reference integrity

- The v4 reference `scene/output_folder/0_0/*.tif` files are **absent from the
  v5 worktree copy** (metadata-only, ~12 K; large TIFFs untracked) but
  **present in the main checkout**
  `/Users/alansynn/Workspace/solweig-light/reports/.../large_runs_v1/`.
  `verify_parity.py` and the protocol hardcode the main-checkout path, so
  this is consistent, but reviewers should know the reference binaries live
  only in the main checkout.
- Re-hashed 3 of 10 reference outputs per case (Kdown, Kup, Ldown) against
  the reference manifests in the main checkout: **6/6 match**. Combined with
  the 20/20 candidate-side equality, reference-side integrity is confirmed
  for the sampled files.

### 4. Freeze integrity

- **Wheel sha256 recomputed**: `8fe69a5831cb340ce72ce911be9ccbd50c8808f6dcaaa8d4c69c6506a05b2ad4`
  for `freeze/wheel/solweig_light-0.1.0.dev0-py3-none-any.whl` — **exact
  match** to FREEZE_MANIFEST and CAMPAIGN.
- `d2edbc105d5d…` exists ("Record portfolio v2 …"), is an ancestor of HEAD;
  freeze commit `d63636ae` ("Freeze v5 final protocol, wheel, and installed
  check") has an **empty src/pyproject diff** to d2edbc10, so "built at
  source d2edbc10, frozen at d63636ae" is coherent.
- Wheel content vs installed tree: all **46** `solweig_light/*.py` entries in
  the wheel are byte-identical to `freeze/site-packages/` copies.
- `module_origins` in both candidate manifests: 6 entries each, **all inside
  `evidence/freeze/site-packages/`, all files exist**; `package_origin` same
  root; **`torch_imported: false`** in both. Monitor command lines show both
  children launched via `/Users/alansynn/Workspace/solweig-light/.venv-light/bin/python`
  with `--site …/freeze/site-packages`.
- Environment: protocol and FREEZE_MANIFEST record `.venv-light` CPython
  3.11.16 / numpy 2.4.6 / numba 0.67.0 / llvmlite 0.49.0; the monitor command
  confirms .venv-light was actually used.
- Profile fingerprint `8e4d3846…cbef30` recorded in both candidate manifests
  equals the v4 reference's — the substantive equality holds.
- CAMPAIGN says "Wheel frozen at `d63636ae` … built at source `d2edbc10`" —
  slightly compressed wording (d63636ae is the freeze *commit*, d2edbc10 the
  source commit) but internally consistent with FREEZE_MANIFEST. No
  contradiction.

### 5. Handover draft (MERGE_REVIEW_NOTES_v1.md)

- Review records cited in the patch table all exist:
  `evidence/reviews/rays/REVIEW_C5-30.md`,
  `evidence/reviews/radiation/REVIEW_C5-31.md` (cited without a directory in
  the draft, but present),
  `evidence/reviews/gvf/REVIEW_C5-32.md`,
  `evidence/reviews/runtime/REVIEW_C5-33.md`,
  `evidence/reviews/storage/REVIEW_C5-53.md`; `PORTFOLIO_v2_*` files present.
- Commits cited exist: `c987cbb8` (G02 amendment / F1 aliasing gate),
  `fd3392c7` (signed-zero docstring + probe test),
  `0ecb9042` (S07 follow-ups F2/F3).
- R04 "bush ≡ 0": `src/solweig_light/pipeline.py:130` is exactly
  `bush = np.logical_not(vegdem2 * vegdem) * vegdem` with
  `vegdem = trees + dem` after `trees[trees < 0] = 0`. With dem ≥ 0 and
  trees ≥ 0, a zero product forces vegdem = 0, otherwise `logical_not` yields
  0 — so bush ≡ 0. **Mathematically correct.**
- P01 dormant: `src/solweig_light/radiation/patch_radiation.py:132,138` —
  fused route opt-in via `SOLWEIG_LIGHT_FUSED_RAD == '1'`, default OFF. ✓
- Routing honesty: `evidence/routing/ROUTING_MANIFEST.json` records
  `opus_route.available: false` with the GLM-via-Z.ai alias mapping
  (`ANTHROPIC_DEFAULT_OPUS_MODEL: glm-5.3` etc.). The draft's "all GLM, Opus
  unavailable" is accurate.
- Deferred gates: signed-zero read-back docstring present at
  `src/solweig_light/persistence.py:210-214`; the draft's description
  ("reads the live band through the GDAL block cache … pre-existing base
  behavior") matches. `target_demonstrated_once` boundary restated correctly.

## Notes / discrepancies (non-blocking)

1. **4.4a — dense1024 TMRT Linux p8 record.** The draft states it as
   established fact ("inherited, stays recorded as-is"). The v5 team's own
   inventory (`evidence/inventory/PRIOR_EVIDENCE.md:147-152`) explicitly
   flags the canonical v4 record as an **UNRESOLVED POINTER** — only the
   disposition-preservation policy (`optimization_v4/VALIDATION_POLICY.md`,
   main checkout: "Preserve all old scientific failure dispositions") was
   locatable. The draft should carry that caveat rather than implying a
   locatable canonical record.
2. **4.4b — "Four SVF/UMEP exceptions".** The inventory lists exactly four
   code/test anchors but itself caveats that the count "matches four" by its
   own anchoring and that the authoritative v4 list was not located. The
   draft states "Four" flatly. Same fix: carry the caveat.
3. **3.5 — pre-run fingerprint assertion temporal.** "Verified before the
   run" is not independently verifiable from stored artifacts (no pre-run
   assertion artifact found; the fingerprint equality is recorded in the
   manifests). The equality itself is confirmed; only its timing is not.
4. **Interpreter attribution of the installed checks.** The check JSONs
   (`c5-40-l2-chrono-v1`) do not self-record the Python version; the py3.12
   vs py3.11 attribution rests on the distinct `run_dir` names
   (`/tmp/v5-installed-check`, `/tmp/v5-installed-check-311`) and
   FREEZE_MANIFEST text. The artifacts are mutually bitwise-identical either
   way, so the cross-interpreter conclusion stands, but the artifacts would
   be stronger with an embedded interpreter field.
5. **Ephemeral /tmp evidence.** The installed-check run outputs live in
   `/tmp/v5-installed-check{,-311}` and happened to still exist at review
   time; they are not archived in the repo. For a durable evidence chain,
   consider copying the (small) artifact set into `evidence/freeze/` or
   noting their transience.
6. **Reference binaries location.** v4 reference outputs exist only in the
   main checkout, not the v5 worktree (untracked by size). Consistent with
   how the tooling is written, but worth stating in handover for merge
   reviewers.
7. **Per-merge L2 gating not auditable.** "Every integration merge was
   followed by the L2 gate" cannot be re-verified from stored evidence (only
   the pristine reference and the freeze-time installed checks are stored).
   The load-bearing claim — tip equality — *is* evidenced; the per-merge
   history is procedural.

## Scope NOT verified by me

- I ran no code, no builds, no benchmarks (per task constraints); all
  verification is artifact/hash/git-level. I did not re-execute the L4 runs
  or the installed checks.
- I did not verify the v4 reference run's own historical provenance (that the
  recorded v4 `module_origins` site-packages was truly built from 14e88876-identical
  source); I verified the git side of the premise and that the v4 manifest
  records such origins, not the v4 install event itself.
- I did not verify the internal contents of the five review records (C5-30/31/32/33/53)
  beyond their existence; their conclusions are taken as recorded.
- I did not audit the L2 `l2_chrono.py` harness logic line-by-line.
- Per-merge L2 gate execution history (note 7).
- "No new baseline" is corroborated by protocol counters, run-dir census, and
  command lines, but an exhaustive negative (no baseline run anywhere) is not
  provable by inspection.

## Overall verdict

**ACCEPT-WITH-NOTES.** The four claims are supported by primary evidence that
I independently re-verified at the strongest available level (full 20/20
output re-hash on both sides of the parity comparison, live wheel/site-packages
byte comparison, reproduced git identity claims, live re-hash of the installed
checks). The notes are documentation-quality fixes — chiefly carrying the
inventory's own caveats about the p8 and four-exception inherited
dispositions into the handover draft — and none affects the validity of the
bitwise parity result, the freeze, or the once-demonstrated ≤1800 s target.
