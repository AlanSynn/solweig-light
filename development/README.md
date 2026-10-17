# development/

Development history and the test-coupled evidence kept alongside it. Nothing
in here is imported by the package (`src/` is independent of this tree).
The consolidated sequential record of the whole project — port, exactness
contract, campaigns, closure — is **[HISTORY.md](HISTORY.md)**.

## Map

| path | why it is here |
|---|---|
| [HISTORY.md](HISTORY.md) | the single sequential history document (everything else was archived 2026-10-17) |
| [docs/evidence_storage.md](docs/evidence_storage.md) | evidence-storage policy + Dropbox archive index (sha256 lists) |
| [benchmarks/protocols/comparison_v1.json](benchmarks/protocols/comparison_v1.json) | machine-readable numerical authority read by the differential/integration suites |
| [benchmarks/protocols/p7_persistent_jit_serial_variant/](benchmarks/protocols/p7_persistent_jit_serial_variant/) | frozen harness protocol of `tests/unit/test_p7_serial_variant_harness.py` |
| [reports/](reports/) | what live tests read: `contract_snapshot.json`, the characterization subsets (`p7_p6_baseline`, `p7_repaired_p6_baseline{,_v2}`, `p8_utci_official_source`, `p8_umep_source`) and `scientific_release_exceptions.json` |
| [tools/](tools/) | the six harness-exercised scripts (`run_exact_cpu_pairs`, `summarize_exact_cpu_pairs`, `capture_exact_pipeline`, `benchmark_p7_pipeline`, `run_p7_serial_variant`, `characterize_inputs`) + `evidence_archive_20261013/` |
| optimization_v6_continue/evidence/, optimization_v7_backends/evidence/captures/, optimization_v8_native_default/evidence/{installed,dx_baseline}, optimization_s10_semantic_systems/evidence/ | packet evidence read by `tests/optimization_v6/`, `tests/optimization_v7/`, `tests/optimization_v8/`, `tests/optimization_s10/` |

## Archives

Everything else was removed at the 2026-10-16 (S11) and 2026-10-17
(documentation) closures and is archived to Dropbox under
`Alan Synn/Research/solweig-light/` — `campaign_s11/repo_cleanup_20261016/`
(S11 cut) and `repo_closure_20261017/` (documentation cut); see
[docs/evidence_storage.md](docs/evidence_storage.md) for the full index.
Deleted trees remain recoverable from git history as well: `cba707db` is the
last commit carrying every campaign record, `07807fd8` the last carrying
every development document.

## Path era-note

Records kept here (and the archived ones) were written when these trees sat
at the repository root, so their paths cite the pre-restructure layout:
`reports/...` means `development/reports/...`, `tools/...` means
`development/tools/...`. Records are retained as written (retain-don't-edit).
The kept harness tools resolve paths via `parents[1]`, which is
`development/` today; `characterize_inputs.py` and
`benchmark_p7_pipeline.py` are sha-pinned by their tests and must not be
modified. The known baseline failures of
`tests/unit/test_p7_serial_variant_harness.py` are described in
[HISTORY.md](HISTORY.md) (era 2, test battery).
