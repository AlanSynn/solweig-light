# Final status, without the ambiguous "goal achieved" label

Emit `FINAL_SELECTION.json` with:

- schema `solweig.final-optimization.v1`
- status: `closed_native_qualified`, `closed_cpu_only`, or `blocked_no_safe_merge`
- source_branch: `perf/native-optimization`; target_branch: `main`
- source_sha, target_sha, source_tree_sha (40-character verified Git hashes)
- native_goal_achieved (boolean), native_research_closed_for_release (true)
- default_backend (`qualified_native_with_cpu_fallback` or `numba` or `none`)
- ready_for_merge (boolean), required_release_safety_passed (boolean)
- actual_target_status (`demonstrated_once`, `unverified`, `not_attempted`, `failed`)
- upstream_comparison_status (explicit string; no implicit comparison)
- remote_actions_performed (list; should be empty in this task)
- evidence_paths, exclusions, outstanding_claims, limitations

Invariants:

- `closed_native_qualified` requires native_goal_achieved=true and verified evidence of correctness, meaningful whole-pipeline improvement, actual native coverage and installed no-env deployment. A valid schema checker cannot verify those records by itself.
- `closed_cpu_only` requires native_goal_achieved=false, default_backend=numba, qualification records absent/empty for this unselected native path, and no ordinary runtime dependency on dormant N8 selection machinery. CPU-only closure does not imply a newly faster B was integrated.
- `blocked_no_safe_merge` requires ready_for_merge=false. A native failure does not automatically imply no safe CPU merge; examine the actual final tree.
- `ready_for_merge=true` requires required_release_safety_passed=true and a corresponding complete MERGE_MANIFEST. This does not imply all historical P7/P8 scientific/performance/platform gates have passed.
- No `native_goal_open`, `remaining_flip_conditions` as the requested next task, or success banner without the separate fields. Future voluntary research is outside this closed release decision.

`MERGE_MANIFEST.json` records source/target hashes, preview merged tree, change-group include/exclude disposition, active imports/default paths, compiled artifact hashes, exact install/test/benchmark commands, unsupported platform behavior and all unsatisfied non-blocking claims. Gate blockers must not be hidden among non-blocking claims.

A manifest is a decision artifact, not authority to perform remote actions. The user requested an identified merge candidate and target; do not interpret that as permission to publish or overwrite main.
