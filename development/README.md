# Development evidence

Current behavior and architecture are documented in [../docs/](../docs/).
This directory contains retained verification inputs and archive metadata;
the runtime package does not import it.

| Path | Purpose |
| --- | --- |
| [benchmarks/protocols/](benchmarks/protocols/) | Frozen numerical and benchmark protocols used by verification tools. |
| [reports/](reports/) | API/CLI snapshot, independent reference sources, and approved scientific limitations. |
| [tools/](tools/) | Exact CPU comparison/capture tools and archive utilities. |
| [experiments/optimization_v8/packaging/](experiments/optimization_v8/packaging/) | Native build helper imported by packaging tests. |
| `optimization_*/evidence/` | Small evidence packets and fixtures still read by tests. |
| [docs/evidence_storage.md](docs/evidence_storage.md) | Historical archive locations and checksums. |
| [HISTORY.md](HISTORY.md) | Link to the frozen development narrative in Git history. |

Keep test-coupled files at their existing paths. Some records use older paths
such as `reports/` or `tools/`, now under `development/`; these describe their
capture environment. Do not regenerate scientific references from candidate
code or change source files pinned by their manifests. Record new validation
in the relevant change or PR, with bulk artifacts outside Git.
