# development/

Development history and the test-coupled evidence kept alongside it. Nothing
in here is imported by the package (`src/` is independent of this tree).
The consolidated development record of the whole project — organized by
theme: the vanilla upstream model vs this port, the exactness/verification
state, the performance record, the repository/archive state — is
**[HISTORY.md](HISTORY.md)**.

## Map

| path | why it is here |
|---|---|
| [HISTORY.md](HISTORY.md) | the single sequential history document (everything else was archived 2026-10-17) |
| [docs/evidence_storage.md](docs/evidence_storage.md) | evidence-storage policy + Dropbox archive index (sha256 lists) |
| [benchmarks/protocols/comparison_v1.json](benchmarks/protocols/comparison_v1.json) | machine-readable numerical authority read by the differential/integration suites |
| [benchmarks/protocols/p7_persistent_jit_serial_variant/](benchmarks/protocols/p7_persistent_jit_serial_variant/) | frozen protocol read by `tools/run_p7_serial_variant.py` (kept through the `run_exact_cpu_pairs` chain — see below) |
| [reports/](reports/) | what live tests read: `contract_snapshot.json`, the characterization subsets (`p8_utci_official_source`, `p8_umep_source`) and `scientific_release_exceptions.json` |
| [tools/](tools/) | the five exactness scripts (`run_exact_cpu_pairs`, `summarize_exact_cpu_pairs`, `capture_exact_pipeline`, `run_p7_serial_variant`, `characterize_inputs`) + `evidence_archive_20261013/`. `run_exact_cpu_pairs` (exercised by `tests/unit/test_exact_cpu_pairs.py`) imports `run_p7_serial_variant`, which reads the frozen protocol above — that chain is why both stay |
| [experiments/optimization_v8/packaging/build_native.py](experiments/optimization_v8/packaging/build_native.py) | the single surviving experiments file: collection-time import of `tests/optimization_v8/packaging/conftest.py` (restored at the post-closure audit) |
| optimization_v6_continue/evidence/, optimization_v7_backends/evidence/captures/ (capture manifest + `b7_02_fixtures.npz` module-loaded by the v7 suite), optimization_v8_native_default/evidence/{installed,dx_baseline}, optimization_s10_semantic_systems/evidence/ | packet evidence read by `tests/optimization_v6/`, `tests/optimization_v7/`, `tests/optimization_v8/`, `tests/optimization_s10/` |

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
`development/` today; `characterize_inputs.py` is sha-pinned by its test and
must not be modified. `benchmark_p7_pipeline.py` and the two P7 harness test
modules it and the serial-variant protocol served were removed 2026-10-17
(the baseline-hygiene closure: user-directed removal of the platform-bound
harness guards; archived under `repo_closure_20261017/`).
