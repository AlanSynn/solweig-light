# Optimization campaigns — map and terminal states

For whoever inherits this repository. Each packet under `optimization_*/` is
self-contained (its own rules, evidence, and terminal records); this document
is the MAP: what each campaign was, how it ended, what shipped, and which
records are retained as provenance versus removed. Nothing in this document
overrides a packet's own terminal record.

Read first: [`optimization_n9_final/FINAL_SELECTION.json`](../optimization_n9_final/FINAL_SELECTION.json)
(terminal selection) and
[`optimization_n9_final/MERGE_MANIFEST.json`](../optimization_n9_final/MERGE_MANIFEST.json)
(gate table, hashes, merge instruction, honesty labels).

## Current state at handover (2026-09-23)

- The full campaign line lives on `perf/native-optimization` and was merged
  into **local main by fast-forward** as part of the handover wrap-up. No
  push / PR / release was performed; remote history is untouched.
- Shipped default longwave path: bounded Numba stream row B with
  `thread_budget` pinned to 1 (`_native_dispatch/lw_stream.py:303`); engine
  tri-state `parallel=True` only when `threads_per_worker > 1`
  (`radiation/engine.py:1666`); all-raw inputs decline structurally to the
  legacy route (bitwise-identical to main's reference); `aplus_decode` is
  shipped and wired into both consumer seams.
- Expert opt-in backend (B7-32, unchanged): `SOLWEIG_LIGHT_LW_BACKEND=native`
  (ISPC) — the only env read in the dispatch region
  (`radiation/cylinder_longwave.py:196` and `:216`).
- Native default promotion: **closed, not earned**. The N8 native row and
  qualification machinery are archived repo-only under
  `experiments/optimization_v8/native_dispatch/` and banned from wheels by
  gate (`tests/optimization_v8/installed/test_installed_wheel_gates.py`).

## Campaign series

| campaign | packet | where it ran | terminal state |
|---|---|---|---|
| P0–P8 port + `local_cpu_optimization_v1` | `docs/progress.md`, `reports/local_cpu_optimization.md` | main line | documented in `docs/progress.md` (log ends at local CPU optimization v1) |
| v4 operational-delta | `optimization_v4/` | local working copy (never committed as a packet) | landed at handover; strategy-catalog + L0–L4 test discipline, no numerical change |
| v5 claude | `optimization_v5_claude/` | `perf/claude-glm53-cpu-v5*` worker branches | accepted changes; evidence census→freeze→handover under `evidence/` |
| v6 continue | `optimization_v6_continue/` | same branch as v5 | continuation packet (throughput, cold-path dedup); `THROUGHPUT.md`, `SOURCE_AUDIT.md` |
| v7 backends | `optimization_v7_backends/` | `perf/cpu-optimization` track | `B7_53_HANDOVER.md`: ISPC C_native winner integrated as the opt-in env-gated expert backend, bitwise-identical, default untouched |
| v8 native default | `optimization_v8_native_default/` | `perf/native-optimization` (worktree) | `evidence/handover/n8_60_handover.json`: selection `numba_improvement_only` — native default NOT earned; landed the bounded stream row B machinery |
| n9 FINAL | `optimization_n9_final/` | same branch | `FINAL_SELECTION.json`: **closed_cpu_only** (exactly one); N8 native row archived; F6 `SHIPPED_ROUTE_CONFIRMED` |

Lineage note: the v4 packet and the loose v5 evidence records were preserved
in a local working copy and are landed in the repo at handover so the record
set is complete. `optimization_v5_claude/evidence/v5_hypothetical_throughput.json`
is an **uncalibrated analytical projection** (`solweig_executed: false`) — it
is retained for provenance only and is NOT a measurement.

## Measured-vs-provenance discipline (from the N9 close)

- F6 run 2 (`optimization_n9_final/evidence/f6_final_vs_main_timed_20260923T171623Z.json`
  + `f6_verdict.json`) is the terminal comparison: bitwise parity on all 6
  cells / 9 reps, carried geomean 1.60x median-of-times, cold PASS 0.9226
  MARGINAL. Causal-correction allowance CONSUMED — no further F6
  re-measurement is admissible (release-owner Amendment 1).
- Superseded / invalidated records are retained deliberately, never edited:
  `f6_cold_gate_ruling.json` (superseded by
  `f6_cold_gate_ruling_amendment_1.json`; its stated `ruling_utc` is VOID),
  `f6_verdict_run1_invalid_mainwarm.json` + run-1 raw (warm-pass harness
  defect, retained under the invalidation name), and
  `f6_ruling_discrepancy_note.json` (`RESOLVED_BY_AMENDMENT_1`). If any
  document cites 123x / 5.14x / 1.0843, it is citing the invalidated run-1 —
  it must cite the invalidation record explicitly.

## Removed local state (not repo content)

Removed during handover wrap-up under the user's safe-cleanup workflow
(copy → verify → Trash; recoverable until Trash is emptied):

- Campaign worktrees with no unique content: `n9-main-ref`, `n9-producer`
  (untracked drafts of packet files that exist committed on the branch),
  `n9-stream`, `solweig-v8-mainref`, `solweig-v7-{drjit,native,numba,opencl}`
  (untracked `experiments/` scratch; the lessons persist as committed v7
  evidence and in `docs/`).
- Stale build artifacts: worktree `build/` (purged per the D2 wheel-taint
  handover — wheels must always be built from a purged `build/` or a pristine
  copy), and `.numba_cache/` directories.
- The superseded working copies of campaign dirs in the primary checkout
  (canonical versions are committed on the merged main).

## Post-release follow-ups (recorded, not merge conditions)

1. **NUMBA_CACHE_DIR default** — bounded default cache under the user cache
   dir would cut the ~2.4–2.7 s per-process JIT compile paid when the
   installed tree is read-only. Reframed by Amendment 1: shared-baseline
   cost, not a measured regression; new write-location behavior requiring its
   own review. If it lands, "cold" changes meaning (~320 ms disk load vs
   full compile) and the cold gate needs its own record.
2. **Installed no-env API/CLI product runs** — admission-blocked
   environmentally on the campaign host (needs ≥ ~4.3 GB available-memory
   view; refused by construction under the no-env contract). Self-driving
   (~4 min each) once a real window opens; no env cap needed.
3. Single-channel-raw compositions remain unmeasured and stream by design.

## Practical notes

- Never reset pins `16cdc56c` / `14e88876` (v8/N9 baselines).
- Worktree `.venv` is the pinned runtime (py3.12.13 / numba 0.67.0 /
  GDAL 3.13.3); default `python3` (3.14) has no pytest.
- Merge instruction and post-merge checklist:
  `optimization_n9_final/MERGE_MANIFEST.json` (operator_checklist).
- Rehearsal proof: `optimization_n9_final/evidence/f7_merge_rehearsal.md`.
