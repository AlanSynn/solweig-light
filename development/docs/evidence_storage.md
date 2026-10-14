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
