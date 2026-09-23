# Sources and provenance for v5

The technical catalog is inherited from the earlier supplied v4 packet and historical repository reads. The repository ref was NOT refreshed and no full source snapshot or SOLWEIG execution was made during this v5 preparation. At execution, read actual current HEAD and the existing authoritative numerical protocols. Earlier synthetic results remain labeled inherited.

## Current Claude Code and GLM primary documentation

These pages were inspected while preparing v5. They describe provider/client behavior, not proof of availability in the user’s installed account/version.

| ID | Source | Role |
|---|---|---|
| C01 | https://docs.z.ai/guides/llm/glm-5.3 | Actual GLM-5.3 model ID, reasoning levels and supported protocols |
| C02 | https://docs.z.ai/devpack/tool/claude | Claude-compatible endpoint and example model alias remapping |
| C03 | https://code.claude.com/docs/en/model-config | Model aliases and provider-specific configuration |
| C04 | https://code.claude.com/docs/en/settings | Settings precedence and separate config storage |
| C05 | https://code.claude.com/docs/en/cli-reference | Model/effort/agent/settings/print CLI interfaces |
| C06 | https://code.claude.com/docs/en/sub-agents | Agent Markdown schema, tools, model inheritance, actual concurrency/nesting behavior |
| C07 | https://code.claude.com/docs/en/memory | CLAUDE.md loading/imports and concise conditional instructions |
| C08 | https://code.claude.com/docs/en/worktrees | Native worktree base behavior and explicit Git alternatives |
| C09 | https://code.claude.com/docs/en/agent-teams | Optional experimental teams and interactive/non-interactive distinctions |
| C10 | https://code.claude.com/docs/en/env-vars | Environment overrides and version-dependent configuration |

No model throughput, account quota, provider support or Claude command was tested here. Documentation can change; use installed help and one authorized route smoke rather than assuming every current webpage feature is present. Do not upgrade automatically during a frozen numerical experiment.

## Pinned implementation sources

All `src/...` and `docs/...` paths below resolve under:

`https://github.com/AlanSynn/solweig-light/blob/14e888760727583ef782a4dc0e7a5c7c6e6ff9d1/`

| ID | Source | Use in this packet |
|---|---|---|
| S01 | `https://api.github.com/repos/AlanSynn/solweig-light/branches/main` | Historical main ref and metadata checked in earlier packets; not refreshed during v5. |
| S02 | `src/solweig_light/geometry/sky_compiled.py`; `geometry/shadows.py` | Sky recurrence, first-step corrections, projected state, global bush activation and schedules. |
| S03 | `src/solweig_light/radiation/patch_radiation.py` | Typed patch expressions, ordered SW/LW accumulation, classification and block dispatch. |
| S04 | `src/solweig_light/radiation/ground_view.py` | Gather recurrence, persistent boundary samples, direction order and water mutation. |
| S05 | `src/solweig_light/geometry/visibility.py`, `visibility_compiled.py`, `visibility_native.py` | Binary/ternary/raw encoding, native mapping and current decoder behavior. |
| S06 | `src/solweig_light/radiation/engine.py`; `radiation/wall_shadows.py` | Actual dispatch, aniLum, wall quantities and profile fallbacks. |
| S07 | `src/solweig_light/runtime.py`; `runtime_worker.py` | Current admission and subprocess scheduling. Recheck worker implementation at execution. |
| S08 | `src/solweig_light/pipeline.py`; `api.py` | Chronological state, outputs, input handling and public workflow context. |
| S09 | `src/solweig_light/persistence.py`; `io/rasters.py` | State generations, readback, fsync, publication and writer ownership. Recheck all I/O details before changing them. |
| S10 | `reports/local_cpu_optimization.md` and its linked final-combined qualification artifacts | Reported local single-tile timings and limitations. No new benchmark was run here. |
| S11 | `docs/numerical_contract.md`; the execution checkout's authoritative `benchmarks/protocols/comparison_v1.json` and later promotion/exception records | Numerical, artifact and mask contract. The document contains historic phase statuses; reconcile current authority rather than relaxing budgets. |
| S12 | `src/solweig_light/radiation/_math_profile.py`; `_sleef_classifier.py`; `docs/portable_math_profile.md` | Current typed SLEEF/NumPy profile and explicit fallback/identity rules. |
| S13 | `docs/p7_experiments.md`; `docs/exact_optimization_strategy.md` | Prior rejected/conditional optimizations and their evidential limits. |
| S14 | `src/solweig_light/geometry/svf.py`; geometry wall/aspect source located during B00 | Ordered SVF weighting, codec ingestion/export, preprocessing candidates. Wall/aspect residuals need a current call-site audit. |

Selected Git blob identities returned by connector reads:

- sky_compiled.py: `cb26ee56113d2aca063df969d297b5b301f847c4`
- ground_view.py: `3e316afae3b93f5f84618f8170ef749c20a375f2`
- patch_radiation.py: `f8952f231e533c50e915b28aa30134a07cb8e735`
- _math_profile.py: `52eb2dfca4e661e4199976beef04dd1d4c09cce8`
- numerical_contract.md: `386ed5e9d8e4f0eaa5f22786cdbda4a5c0dff419`

These Git blob IDs are not SHA256 hashes of a locally downloaded tree. The executing agent must create its own complete source/environment manifest and installed-wheel identity before experiments.

## Primary technical references

| ID | Reference | Relevance |
|---|---|---|
| T01 | https://llvm.org/docs/LangRef.html | Floating-point node semantics, fast-math flags, reassociation and contraction. |
| T02 | https://llvm.org/docs/Vectorizers.html | Independent-iteration vectorization versus ordered/reassociated reductions; inspect generated code. |
| T03 | https://numba.readthedocs.io/en/stable/user/parallel.html | Parallel ownership, reductions, fusion and diagnostics. No generic speed forecast. |
| T04 | https://docs.nersc.gov/tools/performance/roofline/ | Compute/bandwidth constraints, hierarchical memory levels and empirical calibration. |
| T05 | https://www.opencilk.org/doc/tutorials/opencilk-concepts/ | Work/span and parallelism concepts. |
| O01 | https://developers.openai.com/codex/subagents/ (redirects to https://learn.chatgpt.com/docs/agent-configuration/subagents) | Explicit delegation, actual model/effort configuration, inherited settings and distilled results. |
| O02 | https://developers.openai.com/codex/guides/agents-md/ (redirects to https://learn.chatgpt.com/docs/agent-configuration/agents-md) | Instruction discovery and keeping always-loaded guidance scoped. |

Historical agent documentation pointers do not establish that the user's client/account offers any particular model or effort. Resolve capabilities at execution time. The cost/role/packet limits in DELEGATION.md are proposed operational choices, not measured token-saving results or vendor guarantees.


## Evidence meaning

[Sxx] are historical implementation source targets; [Txx] are technical references; [Cxx] are current client/provider documentation. The design decisions, recipes, hypothetical throughput decomposition and orchestration policy are this packet's proposed engineering design, not vendor benchmark claims. Old [Oxx] links are archival context only, not an instruction to use OpenAI/Codex.

See `evidence/input_provenance.json` for the input bundle hash. `evidence/v5_packet_checks.json` contains only current packet/tool tests. No runtime source, original oracle, hardware benchmark, agent process, credentials or target repository was changed/executed by creating this bundle.
