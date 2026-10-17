# development/

Everything that is **not needed to use solweig-light** lives here: process
records, benchmark protocols, experiment machinery and audit tooling kept
while porting and optimizing the model. If you only want to run the model,
the repository root and [docs/](../docs/) are all you need; this tree is for
tracing how the current implementation came to be.

Nothing in here is imported by the package. `src/` is independent of this
tree, and moving it changed no source file.

## Map

| directory | contents |
|---|---|
| [optimization_s10_semantic_systems/](optimization_s10_semantic_systems/) | S10 campaign packet (semantic/system optimization portfolio). Kept in git: `tests/optimization_s10/` reads its `evidence/`. |
| [optimization_v6_continue/](optimization_v6_continue/) | v6 campaign packet. Kept in git: `tests/optimization_v6/` reads its `evidence/`. |
| [optimization_v7_backends/](optimization_v7_backends/), [optimization_v8_native_default/](optimization_v8_native_default/) | v7/v8 campaign packets. Kept in git: test-referenced `evidence/captures/`. |
| [docs/](docs/) | Process records: the P0–P8 port log ([progress.md](docs/progress.md)), per-phase records (p4/p5/p6/p7_*), the exact-optimization strategy review, evidence-storage policy, source audits ([audit/](docs/audit/)) and the upstream patch ([upstream_patches/](docs/upstream_patches/)). |
| [reports/](reports/) | What live tests read: `contract_snapshot.json` (public-contract pin) and `characterization/` subsets (`p7_p6_baseline`, `p8_utci_official_source`, `p8_umep_source`). |
| [benchmarks/](benchmarks/) | Frozen benchmark protocols (`comparison_v1.json` is the machine-readable numerical authority cited by [docs/numerical_contract.md](../docs/numerical_contract.md)) plus fixture scenes. |
| [experiments/](experiments/) | Repo-only experiment workspaces (e.g. the archived v8 native-dispatch qualification machinery — banned from wheels, retained for provenance). |
| [tools/](tools/) | One-shot capture/characterization/benchmark scripts used to produce the records above and exercised by harness tests. |

## Archived campaigns (external, Dropbox)

Closed-campaign working packets and unreferenced bulk measurement evidence
are NOT in git; they are archived to Dropbox under
`Alan Synn/Research/solweig-light/` — see
[docs/evidence_storage.md](docs/evidence_storage.md) for the index and
sha256 lists. Removed at the S11 closure (2026-10-16): the v4/v5/N9 campaign
packets, the S11 `optimization_s11_envelope_headroom/` packet, the
`solweig_followon_headroom/` working packet, `plans/`, and the
`reports/` bulk (everything except the test-referenced subsets above).
Everything remains recoverable: from this archive, or from git history (the
parent of the 2026-10-16 cleanup commit is the last state that carried all
of it, main `cba707db`).

The S10/S11 campaigns' terminal records: S10 —
[optimization_s10_semantic_systems/REGISTER.md](optimization_s10_semantic_systems/REGISTER.md)
(kept, test-coupled); S11 — archived, with its headline findings summarized
in [docs/evidence_storage.md](docs/evidence_storage.md) and its raw records
under `campaign_s11/phase0/`…`phase4/` on Dropbox.

## Path era-note

Records in this tree were written when these directories sat at the
repository root. Their paths therefore cite the **pre-restructure layout**:
a path like `reports/characterization/...` or
`benchmarks/protocols/comparison_v1.json` in a record means today's
`development/reports/characterization/...` etc. Record content was
deliberately **not** rewritten to the new layout — historical records are
retained as written (retain-don't-edit), so stale in-record paths are
expected and are not defects. Paths citing removed directories resolve via
the Dropbox archive or git history.

Old → new:

| recorded as | actual location now |
|---|---|
| `optimization_v4/` … `optimization_n9_final/` | archived (was `development/<same name>/`) |
| `docs/<process doc>`, `docs/audit/`, `docs/upstream_patches/` | `development/docs/…` |
| `reports/` | `development/reports/` (bulk archived) |
| `benchmarks/` | `development/benchmarks/` |
| `experiments/` | `development/experiments/` |
| `tools/` | `development/tools/` |
| `TASKS.yaml`, `SOLWEIG_LIGHT_IMPLEMENTATION_PLAN.md`, `BUNDLE_MANIFEST.json` | archived (was `development/plans/`) |

Still at the root: `README.md`, `LICENSE`, `pyproject.toml`, `.github/`,
`requirements/`, `src/`, `tests/`, `compat/`, `docs/` (user-facing), and
`AGENTS.md`.

## Running the historical tooling

Most scripts under [tools/](tools/) resolve paths relative to their own
location (`parents[1]`), which pointed at the repository root before the
restructure and points at `development/` now. Scripts that only touch
record trees (`reports/`, `benchmarks/`, `tools/`) still work; scripts that
join root-level directories (`tests/`, `src/`, `.upstream/`) only run
against their era commit — check out the pre-restructure revision for that
(`git log development/tools/` for the boundary). This is consistent with
those tools' frozen protocol digests, which pin the source states of their
era anyway. In particular
`tests/unit/test_p7_serial_variant_harness.py::test_prepare_scene_copies_only_declared_raw_inputs`
exercises such a frozen fixture path and fails under the new layout by
design; the remaining failures in that file pre-date the restructure.

Edits to this tree are limited to navigation plumbing (links, moved-path
constants). Measurement records, evidence, manifests and protocols are
retained as written; superseded records are never deleted or rewritten —
see "Measured-vs-provenance discipline" in
[docs/optimization_campaigns.md](docs/optimization_campaigns.md).
