# Packet helper commands

These stdlib tools are implemented; they are not the SOLWEIG backend implementation.
Run from the repository root after copying `optimization_v7_backends/` there.

```sh
python optimization_v7_backends/tools/preflight.py --repo .
python optimization_v7_backends/tools/install_assets.py --repo .
# Read the dry-run, then add --apply to append one narrow CLAUDE import and roles.
# Actual Opus roles additionally require --with-opus-roles --opus-route-confirmed.

python optimization_v7_backends/tools/prepare_worker.py \
  --repo . --base <ACTUAL_IMMUTABLE_SHA> --destination ../solweig-backend-worker
# The default shows a plan only. Add --apply after the base/path are assigned.

python optimization_v7_backends/tools/performance_model.py
python optimization_v7_backends/tools/claim_check.py \
  --freeze <ACTUAL_FROZEN_JSON> --result <ACTUAL_RESULT_JSON>
python optimization_v7_backends/tools/run_packet_checks.py
```

Angle-bracket arguments are values assigned by the coordinator, not existing files.
Templates under `templates/` intentionally fail final-claim checks until completed.
Preflight does not import a framework, query a model provider or contact a network.
The installer does not change settings.json/auth/permission settings and never
silently overwrites a different role. Detached worktrees create no new branch.

Source capture, concrete native adapters, benchmark execution, device probing,
installed-wheel tests and the final campaign are implementation tasks in the DAG,
not pretend ready-made commands or public API stubs. The task-specific agent must
write and execute those using the current repository's actual paths and versions.
