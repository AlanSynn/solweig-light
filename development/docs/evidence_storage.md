# Evidence storage

Raw measurement and benchmark evidence is archived externally, not kept in git
(user decision, 2026-10-13; see the repository `CLAUDE.md` "Evidence storage
policy"). The repository stays lean; it keeps manifests, provenance records,
hash lists, and every evidence path that live tests reference.

## External archive (2026-10-13 migration)

- Location: Dropbox `Alan Synn/Research/solweig-light/`, uploaded with `dbxcli`
  (restore access requires Dropbox authentication).
- Source state: main commit `90d72b50` (working tree identical to HEAD) plus the
  three campaign branches `handover/campaign-line`, `perf/cpu-optimization`,
  `perf/native-optimization`, extracted immediately before those branches were
  deleted.
- `repo_evidence/*.tar.gz` — 25,426 tracked raw-evidence files removed from git
  in the migration commit. Members are repo-root-relative paths; restore with
  `tar -xzf <bundle>.tar.gz -C <repo-root>`.
- `branch_evidence/branch_only_blobs.tar.gz` — 1,540 blobs reachable only through
  the deleted campaign branches (the `handover/campaign-line` tree is the
  superset; the two `perf/*` branches added no unique blobs). Paths that held
  different content at different history points carry a `.blob-<sha-prefix>`
  suffix mapped in the branch manifests.
- `manifests/` — `repo_evidence_manifest.sha256` (sha256 of every archived
  file), per-bundle member lists (`bundle_*.txt`), `bundle_summary.json`,
  per-branch blob manifests with cross-branch sharing, and `kept_in_repo.txt`
  (the 2,221 manifest/provenance files inside the archived directories that
  remain tracked).
- `logs/gitlog_*.txt` — full commit history (fuller + name-status, commits not
  on main) of each deleted branch.
- `EVIDENCE_ARCHIVE_README.md` — archive provenance, layout, and verification
  steps. Extraction scripts are preserved in
  `development/tools/evidence_archive_20261013/`.
- Verification protocol used at migration: every bundle and manifest was
  re-downloaded from Dropbox, bundle sha256 sidecars matched, tar member counts
  matched the member lists, and sampled members matched
  `repo_evidence_manifest.sha256`.

To restore evidence for re-analysis: download the relevant bundle, verify its
`.sha256` sidecar, then extract from the repository root. File-level integrity
can be checked afterwards against `repo_evidence_manifest.sha256`.

## What stays in the repository

- Manifests, provenance records, sha256 lists, protocols, and concise summaries
  inside the archived directories (`kept_in_repo.txt`).
- Live test inputs: `reports/contract_snapshot.json`,
  `characterization/p8_umep_source`, `characterization/p8_utci_official_source`,
  `characterization/p7_p6_baseline`,
  `characterization/p7_repaired_p6_baseline{,_v2}`, and
  `development/optimization_v8_native_default/evidence/{installed,dx_baseline}`.
  These back tests under `tests/` and must never be archived external-only.
- `tests/reference/` goldens stay tracked: CI differential tests require them
  (AGENTS.md §11); they are not archived external-only.
- `development/{tools,docs,plans,experiments,benchmarks}` and the report-root
  documents named in `reports/local_evidence_inventory.json`.

## Going forward

Do not commit new raw evidence (bulk run outputs, trial/sample JSON dumps,
rasters, array caches). Write raw artifacts outside the repository or leave them
ignored per `.gitignore`, and record manifests and provenance in the repository.

## Historical policy (before 2026-10-13)

The repository keeps concise reports, protocols, provenance records, and source
snapshots under `reports/` when tests or scripts use them as evidence. The
authoritative source snapshots include `p8_utci_official_source`,
`p8_umep_source`, and `p7_p6_baseline/src`; these remain visible to Git. The
root reports and the small review documents named in
`reports/local_evidence_inventory.json` are retained for the same reason.

Generated rasters, array dumps, compiled Numba artifacts, JIT and geometry
caches, local environments, output folders, processed inputs, and the complete
`reports/runs/` tree remain local-only. The scoped rules live in `.gitignore`.
They preserve report text and JSON by default; only explicitly identified
large sampling or whole-tree inventory captures are additionally ignored.

This policy does not delete or move local evidence. The inventory records
observed paths and sizes from the checkpoint and points to existing manifests
or hash records without recomputing them. Local-only evidence is therefore not
part of a clone and cannot be reproduced from this document alone: rerunning a
case may require the exact fixture, dependency environment, upstream commit,
hardware, cache state, and remote input recorded by its own protocol.

The local CPU optimization experiment additionally records its two large
baseline sampling captures in
[`storage_manifest.json`](../reports/characterization/local_cpu_optimization_v1/storage_manifest.json).
Those captures remain local with verified hashes. The paired trial
measurements, RSS JSONL samples, exact comparisons, protocols and source
snapshots remain tracked; generated raster histories and wheel binaries
follow the same local-only policy above.

To review the prospective tracked set without adding files, run:

```sh
git ls-files --others --exclude-standard
```

## S11 closure archive (2026-10-16)

Uploaded with `dbxcli` to Dropbox `Alan Synn/Research/solweig-light/`:

- `campaign_s11/phase0/` — S11 phase-0 attribution raw records + SVF
  snapshot corpus (~1.9 GB bitwise evidence; sha256 lists in the S11-1
  REGISTER entry, git history `development/optimization_s11_envelope_headroom/REGISTER.md`).
- `campaign_s11/phase1/phase1b_raw_records.tar.gz` — X02 raw records.
- `campaign_s11/phase2/phase2b_x03_raw_records.tar.gz` (sha256
  `697dadf451544af39d7443011f3d189169732fcbfb7f9a9a37cd1c06b58da43c`) and
  `campaign_s11/phase2/phase2c_b0_raw_records.tar.gz` (sha256
  `4356598da12f44b4ffe1b640bd546713073789b614b1ffb6f58d173dcce3d312`) —
  X03 Stage-B raw records.
- `campaign_s11/phase3/phase3_corner_raw_records.tar.gz` (sha256
  `63f50894f90070eea95ef4357d36b8b557f9c8582ed1a8be7eedd1652db73f40`) —
  S11-7 corner-matrix raw records.
- `campaign_s11/phase4/phase4_x05_raw_records.tar.gz` (sha256
  `7aa135ff28196d97859e4893f791b0b3587b1053f699404de8a4e1f664720d3b`) —
  X05 under-fill fix: battery A/B logs, review raw inputs, single E2E run
  record (all gates PASS; TMRT sha `3edfd91f…` bitwise == c2048s).
- `campaign_s11/repo_cleanup_20261016/reports_bulk_20261016.tar.gz` (sha256
  `41ca10c4e31ab0f33dfc53e767bb372c73f56a2f6aef6907e80a2eaac5ab7812`) —
  `development/reports/` and `development/reports/characterization/` bulk
  removed from git at the S11 closure; members are relative to
  `development/reports/` (restore: `tar -xzf <bundle> -C development/reports`;
  the kept subsets `contract_snapshot.json`,
  `characterization/p7_p6_baseline`, `characterization/p8_utci_official_source`,
  `characterization/p8_umep_source` are NOT in the bundle).
- `campaign_s11/repo_cleanup_20261016/campaign_packets_20261016.tar.gz`
  (sha256
  `7beb2b3583130e12ca83010261d9ff04fdbad3404fcea8c0fb0b9c3ecfd99bb3`) —
  whole-tree removals: `development/plans/`,
  `development/optimization_v4/`, `development/optimization_v5_claude/`,
  `development/optimization_n9_final/`,
  `development/optimization_s11_envelope_headroom/`,
  `solweig_followon_headroom/` (members relative to the repository root;
  restore: `tar -xzf <bundle> -C <repo-root>`).

Also removed at the closure: campaign-history branches
`perf/s10-semantic-systems` and `perf/s11-envelope-headroom` (fully merged
into main via fast-forward at `cba707db` before deletion; their commits are
reachable from main, so no branch-only blobs exist).

S11 campaign terminal summary (its REGISTER/evidence packet is inside
`campaign_packets_20261016.tar.gz`): X02 SVF pixel-parallel twin (chain
6612.9 → 5636.2 s, 1.173x), X01 concurrent export loop (→ 3838.3 s, 1.723x),
X03 measured-envelope recalibration (→ 1452.6 s, 4.552x vs the post-S10
anchor at 12x2), S11-7 corner matrix (serial c24s 10744.28 s vs c24p
1483.90 s = 7.24x at 60.3% worker efficiency; 256^2 pair 6.90x cross-config
bitwise; warm NOT faster, +3.86%), X05 under-fill admission defect fixed
end-to-end (review APPROVE 0 MAJOR; E2E at the previously-refusing 2048^2
4x6 shape bitwise vs the 1x8 record; battery FAILED sets byte-identical,
176/3133 both arms). All numerics bitwise against the corpus goldens;
actual_target_status remains unverified (synthetic corpus only).

## S12 cleanup correction (2026-10-16, post-cleanup battery)

The bulk-`reports/` removal above accidentally included two TEST-COUPLED
characterization packets: `reports/characterization/p7_repaired_p6_baseline/`
and `p7_repaired_p6_baseline_v2/` (parametrized fixtures of
`tests/unit/test_p7_benchmark_harness.py` — bare-name parametrization, missed
by the literal-path reference audit). The post-cleanup verification battery
(job 14125319, rerun 14125777) caught it deterministically: 35 setup errors,
all `FileNotFoundError` on those two packets' `manifest.json`. Both packets
were restored from git history at `cba707db` (132 KB total) and the full
reference audit was rerun mechanically: every path literal in `tests/`
resolves against repo-root/development/tests, except docstring-era citations
(cover-era paths documented in the era-note above). The post-restoration
battery re-verifies parity with the campaign FAILED set (176).

### Post-cleanup battery verdict (2026-10-16)

Protocol-correct verification battery on main @ `e3346e14` (job 14126143,
3309 tests collected — the `--ignore=tests/unit/test_exact_cpu_pairs.py`
workaround from the old-main era is OBSOLETE post-merge: old main's
pre-restructure path `parents[2]/"tools"` was fixed by the campaign line, and
the 8 exact-pair tests collect again): **FAILED set == the campaign baseline
176 + exactly one deviation**,
`tests/differential/test_patch_radiation.py::test_compiled_patch_parallel_diagnostics`.
Root-caused as a numba cache-state artifact, NOT a product regression
(job 14126396): the test introspects `parallel_diagnostics()` metadata, which
exists only when the kernel was freshly compiled in-process — fresh-cache
runs PASS (single: 1 passed; full file: 635 passed), warm-cache re-runs FAIL
(cache-hit dispatchers carry no parfor diagnostics). The campaign arms and
battery run 1 hit fresh-compile state; runs 2/3 and the isolated probe hit
warm shared `NUMBA_CACHE_DIR`. Numerics are unaffected (all 635 numerical
tests of the file pass on both cache states). No repo change needed; noted
for future battery runs on warm caches.
