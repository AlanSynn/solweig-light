# Source and evidence index

Repository inspection uses the GitHub connector, including earlier reads in this conversation and a renewed check of main at `14e888760727583ef782a4dc0e7a5c7c6e6ff9d1`. Current target/source descriptions should be reconciled against the actual execution checkout before implementation. A direct container download attempt failed with DNS resolution errors; no full downloaded source snapshot or executed target kernel is claimed.

## Pinned implementation sources

All `src/...` and `docs/...` paths below resolve under:

`https://github.com/AlanSynn/solweig-light/blob/14e888760727583ef782a4dc0e7a5c7c6e6ff9d1/`

| ID | Source | Use in this packet |
|---|---|---|
| S01 | `https://api.github.com/repos/AlanSynn/solweig-light/branches/main` | Main ref and commit metadata, rechecked for this packet. |
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

Official agent documentation was read for this packet, but it does not establish that the user's client/account offers any particular model or effort. Resolve capabilities at execution time. The cost/role/packet limits in DELEGATION.md are proposed operational choices, not measured token-saving results or vendor guarantees.

## Earlier conversation artifacts

The original implementation specification, its TASKS/AGENTS files, `solweig-theory-review.zip` and `solweig-mathematical-optimization.zip` are prior strategy/evidence packages. Their source-inspection, synthetic-check and hypothetical-performance distinctions must be retained. This packet does not relabel their toy checks as actual kernel/whole-model tests. Original file hashes are recorded in `evidence/prior_artifact_hashes.json` where present in the working environment.

## Citation policy inside the packet

[Sxx] identifies inspected source or source targets. [Txx]/[Oxx] identifies primary technical documentation. Mathematical derivations, example numbers, priority choices and agent policies not stated by these sources are this packet's proposed analysis. A source pointer is not evidence that a proposed transformation is implemented, universally equivalent or faster.
