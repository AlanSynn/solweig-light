# Repository working policy

Follow [AGENTS.md](AGENTS.md) for the project contract and
[README.md](README.md) for current usage and architecture.

## Evidence storage

Keep bulk benchmark outputs, captures, and campaign packets outside Git.
Retain test-coupled fixtures, frozen protocols and their provenance.
`tests/reference/` remains in the repository for differential verification.
Do not rewrite Git history or recreate archived evidence commits.

The [development supplements](development/README.md) cover validation and
measurement, and link to historical archive locations and checksums. Keep
current guidance there and reusable reference data in `tests/reference/`;
remove obsolete campaign records from the current tree. New evidence should
use storage authorized for the task and record its location and checksum
with the relevant change or PR.
