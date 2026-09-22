# Tools and honest evidence

All provided tools use Python standard library and are assistance utilities, not model implementation. Their unit tests use synthetic records and temporary dummy repositories/wheels. Passing them says nothing about SOLWEIG numerical parity, packaged native execution or performance.

Commands from repository root:

```
python optimization_v8_native_default/tools/preflight.py --repo .
python optimization_v8_native_default/tools/install_assets.py --repo .
python optimization_v8_native_default/tools/prepare_worker.py --repo . --base <full-commit> --destination <new-path>
python optimization_v8_native_default/tools/snapshot_surface.py --repo . --ref <main-commit>
python optimization_v8_native_default/tools/cost_model.py
python optimization_v8_native_default/tools/audit_wheel.py <wheel> --require-native
python optimization_v8_native_default/tools/promotion_gate.py <observed-record.json>
python optimization_v8_native_default/tools/run_packet_checks.py
```

`install_assets` and `prepare_worker` need `--apply` to write. Inspect their dry-run first; they enforce the branch and refuse collisions/symlinks. Neither commits, fetches, pushes nor removes data. The installer requires this packet to exist at the repository root and adds only its short CLAUDE import and agent files.

`preflight` reads Git and bounded public source-file hashes; it imports no numerical modules and prints no credentials/environment dump. `snapshot_surface` is a SOURCE/AST snapshot, not operational API proof. Runtime integration tests still need to compare actual signatures/defaults and CLI behavior.

`audit_wheel` statically checks archive paths, metadata/platform tags and native-payload presence. It does not load a library, audit transitive OS dependencies, sign code, verify execution or qualify a wheel. Run platform tooling and actual installation tests separately.

`promotion_gate` evaluates structured claims and paired ratios against policy. It cannot certify that a claimed test occurred. Independent review must verify referenced logs/artifact hashes. An input can be syntactically valid but dishonest; do not treat a helper verdict as evidence authenticity.

Keep raw results in task-owned evidence directories with immutable references. A template has status `pending`, and packet examples are `hypothetical` or `synthetic_tool_test`. Never copy them into runtime policy as qualified rows.
