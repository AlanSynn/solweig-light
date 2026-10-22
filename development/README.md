# Development

These pages supplement the [current documentation](../docs/) with guidance
for changing and measuring SOLWEIG-light. Start with the
[project README](../README.md) for installation and usage.

| Resource | Purpose |
| --- | --- |
| [Validation](validation.md) | Choose relevant checks and understand their reference sources. |
| [Performance measurement](benchmarking.md) | Define comparable workloads and interpret timing and memory records. |
| [Reference data](../tests/reference/) | Frozen contracts, upstream fixtures and independent scientific sources. |
| [Verification helpers](tools/) | Specialized capture and comparison tools with separately supplied inputs. |

Preserve source bytes, manifests and frozen comparison rules used by tests.
Record new validation with the relevant change or PR, and keep bulk generated
outputs outside Git.

Earlier development records, archive locations and restoration checksums are
available in the [development snapshot at 380e56ad](https://github.com/AlanSynn/solweig-light/tree/380e56ad43a10604652f66c3243ac2372cc9c232/development).
Its timings and validation results describe the sources and workloads recorded
there.
