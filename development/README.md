# development/

Everything that is **not needed to use solweig-light** lives here: the
campaign packets, measurement reports, benchmark protocols, experiment
scratch, audit tooling and work-plan ledgers produced while porting and
optimizing the model. If you only want to run the model, the repository
root and [docs/](../docs/) are all you need; this tree is for tracing how
the current implementation came to be.

Nothing in here is imported by the package. `src/` is independent of this
tree, and moving it changed no source file.

## Map

| directory | contents |
|---|---|
| [optimization_v4/](optimization_v4/) … [optimization_n9_final/](optimization_n9_final/) | Six self-contained campaign packets (strategy catalogs, dossiers, evidence, selection/merge manifests). Start at [docs/optimization_campaigns.md](docs/optimization_campaigns.md) — it is the map; each packet's own terminal record supersedes anything narrated elsewhere. |
| [docs/](docs/) | Process records: the P0–P8 port log ([progress.md](docs/progress.md)), per-phase records (p4/p5/p6/p7_*), the exact-optimization strategy review, evidence-storage policy, source audits ([audit/](docs/audit/)) and the upstream patch ([upstream_patches/](docs/upstream_patches/)). |
| [reports/](reports/) | Measurement and characterization archive: contract snapshot, per-phase verification records, `characterization/` raw evidence (including full wheel-staging snapshots). |
| [benchmarks/](benchmarks/) | Frozen benchmark protocols (`comparison_v1.json` is the machine-readable numerical authority cited by [docs/numerical_contract.md](../docs/numerical_contract.md)) and per-protocol directories. |
| [experiments/](experiments/) | Repo-only experiment workspaces (e.g. the archived v8 native-dispatch qualification machinery — banned from wheels, retained for provenance). |
| [tools/](tools/) | One-shot capture/characterization/benchmark scripts used to produce the records above. |
| [plans/](plans/) | `TASKS.yaml`, `SOLWEIG_LIGHT_IMPLEMENTATION_PLAN.md`, `BUNDLE_MANIFEST.json` — work-plan ledgers and the implementation plan. |

## Path era-note

Records in this tree were written when these directories sat at the
repository root. Their paths therefore cite the **pre-restructure layout**:
a path like `reports/characterization/...` or
`benchmarks/protocols/comparison_v1.json` in a record means today's
`development/reports/characterization/...` etc. Record content was
deliberately **not** rewritten to the new layout — historical records are
retained as written (retain-don't-edit), so stale in-record paths are
expected and are not defects.

Old → new:

| recorded as | actual location now |
|---|---|
| `optimization_v4/` … `optimization_n9_final/` | `development/<same name>/` |
| `docs/<process doc>`, `docs/audit/`, `docs/upstream_patches/` | `development/docs/…` |
| `reports/` | `development/reports/` |
| `benchmarks/` | `development/benchmarks/` |
| `experiments/` | `development/experiments/` |
| `tools/` | `development/tools/` |
| `TASKS.yaml`, `SOLWEIG_LIGHT_IMPLEMENTATION_PLAN.md`, `BUNDLE_MANIFEST.json` | `development/plans/` |

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
