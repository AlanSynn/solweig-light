# CLAUDE.md — solweig-light working policies

The general project contract lives in `AGENTS.md` (imported globally). This file records
durable working decisions that are not restated there.

## Evidence storage policy (decided 2026-10-13, user decision)

Keep the repository as lean as possible. Raw evidence is archived externally, not kept
in git:

- Raw measurement/benchmark/capture evidence (bulk JSON/NPZ/TIF run outputs) is archived
  to Dropbox via `dbxcli` under `Alan Synn/Research/solweig-light/`.
- The repository keeps only manifests, provenance records, sha256 lists, and docs that
  identify and verify the archived artifacts. Operational details and the archive index
  live in `development/docs/evidence_storage.md`.
- Campaign-history branches (`handover/campaign-line`, `perf/cpu-optimization`,
  `perf/native-optimization`) were archived the same way before branch deletion. Do not
  recreate heavy evidence commits on new branches.
- History rewriting (`git filter-repo` etc.) and repository re-creation were explicitly
  rejected — do not propose or perform them.
- `tests/reference/` goldens stay in the repository: CI differential tests require them
  (AGENTS.md §11 forbids weakening verification gates). They are not archived
  external-only.

When producing new evidence, write raw artifacts outside git (or leave them untracked
per `.gitignore`) and record manifests + provenance in the repository.
