# Repository working policy

Follow [AGENTS.md](AGENTS.md) for the project contract and
[README.md](README.md) for current usage and architecture.

## Evidence storage

Keep bulk benchmark outputs, captures, and campaign packets outside Git.
Retain test-coupled fixtures, frozen protocols, provenance, and archive hashes.
`tests/reference/` remains in the repository for differential verification.
Do not rewrite Git history or recreate archived evidence commits.

The existing archive index is
[development/docs/evidence_storage.md](development/docs/evidence_storage.md).
Its recorded paths and hashes describe historical snapshots, not a required
layout for new work. New evidence should use the storage authorized for the
current task and record a durable location and checksum.
