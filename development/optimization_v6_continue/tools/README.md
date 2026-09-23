# Safe helper commands

These tools do not implement or verify SOLWEIG.

Read-only branch audit in the existing v5 worktree:

    python optimization_v6_continue/tools/branch_guard.py --repo . --out optimization_v6_continue/evidence/local_branch.json

Independent tiny Numba configuration probe (preview unless --execute):

    python optimization_v6_continue/tools/thread_probe.py --python /path/to/existing/python --threads 1 2 --execute --out optimization_v6_continue/evidence/local_probe.json

The probe is NOT the required actual-pipeline worker telemetry. Use its launch pattern in the source-bound harness.

Conditional phase model (illustrative stage split, not measurements):

    python optimization_v6_continue/tools/phase_model.py optimization_v6_continue/templates/phase_model_hypothetical.json

The record guard must reject the two-scene example as the 24-tile target:

    python optimization_v6_continue/tools/scope_contract.py optimization_v6_continue/templates/historical_scope_not_target.json

Expected exit=2 for that example. A passing record guard validates reporting fields, not the truth of stored outputs. No helper calls an API or edits provider settings. Only explicitly supplied --out paths are written.
