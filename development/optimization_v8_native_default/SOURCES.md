# Source and documentation provenance

Reviewed 2026-09-22. Repository claims refer to fixed commits or the supplied prior report; recommendations/formulas are design judgments, not measured results. Verify installed compiler/client versions rather than assuming current web main matches a release.

## Repository

- Main user-facing contract: https://github.com/AlanSynn/solweig-light/blob/14e888760727583ef782a4dc0e7a5c7c6e6ff9d1/README.md
- Current packaging: https://github.com/AlanSynn/solweig-light/blob/16cdc56cbc8755675487b9c9c1f5a7e987e2c9e4/pyproject.toml
- Repeated native preparation: https://github.com/AlanSynn/solweig-light/blob/16cdc56cbc8755675487b9c9c1f5a7e987e2c9e4/src/solweig_light/backends/native_lw.py
- Guard and scalar ABI: https://github.com/AlanSynn/solweig-light/blob/16cdc56cbc8755675487b9c9c1f5a7e987e2c9e4/src/solweig_light/backends/native/lw_native.py
- Native computation: https://github.com/AlanSynn/solweig-light/blob/16cdc56cbc8755675487b9c9c1f5a7e987e2c9e4/src/solweig_light/backends/native/lw_primary.ispc
- Current reference and caller: https://github.com/AlanSynn/solweig-light/blob/16cdc56cbc8755675487b9c9c1f5a7e987e2c9e4/src/solweig_light/radiation/cylinder_longwave.py
- Actual decoder/classifier: https://github.com/AlanSynn/solweig-light/blob/16cdc56cbc8755675487b9c9c1f5a7e987e2c9e4/src/solweig_light/radiation/patch_radiation.py
- Scope and control results: https://github.com/AlanSynn/solweig-light/blob/16cdc56cbc8755675487b9c9c1f5a7e987e2c9e4/optimization_v7_backends/B7_53_HANDOVER.md
- Benchmark protocol caveats: https://github.com/AlanSynn/solweig-light/blob/16cdc56cbc8755675487b9c9c1f5a7e987e2c9e4/benchmarks/protocols/optimization_v7/b7_03_protocol.json
- Four-tile report: https://github.com/AlanSynn/solweig-light/blob/16cdc56cbc8755675487b9c9c1f5a7e987e2c9e4/optimization_v7_backends/evidence/trials/b7_60/b7_60_whole_pipeline.json
- Parent-only memory/timing harness: https://github.com/AlanSynn/solweig-light/blob/16cdc56cbc8755675487b9c9c1f5a7e987e2c9e4/optimization_v6_continue/evidence/campaign_synthetic/tools/campaign_child.py

## Official documentation checked for this packet

- Python platform tags: https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/
- Binary wheel format: https://packaging.python.org/en/latest/specifications/binary-distribution-format/
- cibuildwheel build/repair/installed tests: https://cibuildwheel.pypa.io/en/stable/
- ISPC language, task and floating-point options: https://ispc.github.io/ispc.html
- Claude Code subagent configuration: https://code.claude.com/docs/en/sub-agents
- Z.ai Claude Code alias routing: https://docs.z.ai/devpack/tool/claude

Prior supplied v6/v7 packets and framework review are historical design references, not source-current numerical evidence. No new framework installation or backend execution occurred while writing this packet.
