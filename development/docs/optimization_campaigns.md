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

## What changed in src — traceable map

The line that became main carries five recorded change eras after the P0–P8
port log in `docs/progress.md`. Every work item below is recoverable from
history by its ID (`git log --grep <id> --oneline`), has its own record set
inside the campaign packet, and ships gate tests under `tests/optimization_v*`.
Net deltas: `bfd9915e..dca2035c` = 40 src commits, 20 files, +5801/−212
(C5+C6 eras); `dca2035c..3d6a1be3` = 13 src commits (v7/v8/N9 eras).

### Era 1 — C5 work items (v5 campaign; ran on `perf/claude-glm53-cpu-v5-{rt,rad,gvf,ray}`, landed on `perf/cpu-optimization`)

| item | what landed in src | commit anchors |
|---|---|---|
| P01 | fused ordered packed-visibility decode into shortwave/longwave reductions; **default OFF** behind `SOLWEIG_LIGHT_FUSED_RAD` (tile version measured-rejected) | `a343fe20`, `77d567ef`+fix `a5b05fdd`, `ba024eeb`, `611deaff`, `39b3fab0` |
| G02 | GVF direction-invariant source hoisting out of the 18-direction loop (exact) | `8933c4ae`, `8c50de62` |
| G03 | fused GVF row-block gather+postprocess route, L2 bitwise-identical, measured ~3.6x stage win; full path kept as diagnostic | `b42035c7`, `137489e2`, `143f1f54` (+aliasing gates `c987cbb8`) |
| S02 | persistent bounded worker-process pool for tile scheduling | `8b3252ca`, `23c77804` |
| S07 | checkpoint digest IO: hash stored bytes at write time; stored-bytes band digest law | `9b0d010f`, `bf99def0`, `fd3392c7`, `0ecb9042` |
| R01a | guarded absorption exit in pixel-major sky trace | `b66fea64` |

Records: `optimization_v5_claude/` (dossiers `F/G/P/R/S/V/X.md`,
`TASKS_CLAUDE.yaml`, `evidence/` census→freeze→handover, `CHANGELOG_V5.md` —
note the changelog covers the operational packet, the items above are the src
execution), gate tests `tests/optimization_v5/`.

### Era 2 — C6 work items (v6 continuation; ran on `perf/cpu-optimization`, tip `dca2035c`)

| item | what landed in src | commit anchors |
|---|---|---|
| C6-10 | common numerical geometry recipe shared by producer paths (service + pipeline integration) | `443ee2b7`, `47cda54f` |
| C6-20 | anisotropic Lside demand-specific specialization + exact fast path | `2304449d`, `0358497a` |
| C6-21 | cylinder longwave primary-output kernel + demand dispatcher | `eea97fbd`, `02c0efa4` |
| C6-22 | cylinder shortwave narrow-scratch specialization | `99681b53`, `15dfbf2a` |
| C6-30/31 | GVF per-step source-expression preparation + typed block postprocess kernel | `986c5a09`, `d7eb148d`, `6f8325aa`, `61c76a17` |
| C6-40/50 | prepared multi-channel visibility decoder; wired via C6-70h, later **declined by default** behind an opt-in gate | `4b83452b`, `58d7fe23`, `46450c75` |
| C6-42 | private phase memory admission W1 (api) + W3 (`GDAL_CACHEMAX`); W2 deferred | `e318c226`, `717a7e72` |
| C6-70a–k | wiring/integration series across engine, pipeline, api | `47cda54f`..`db5928fe`, `78d242a6`, `3f3e8b8d` |
| C6-81 (+R04/G06) | patch-classification exact tables | `dca2035c` (reviews `ae37d96b`, `371b21ef`) |

Records: `optimization_v6_continue/` (eight numbered dossiers
`01_measurement…08_residual_strategy_register.md`, per-area `evidence/`
(cyl_lw, cyl_sw, decoder, gvf_prep, gvf_post, r04_patchclasses, …),
`SOURCE_AUDIT.md` claim boundaries, `THROUGHPUT.md` denominator discipline),
gate tests `tests/optimization_v6/`.

### Era 3 — v7 backends (B7 items; ISPC C_native opt-in expert backend)

- `cceec6d5` B7-40/41/42/50: C_native ISPC optional backend, env-gated via
  `SOLWEIG_LIGHT_LW_BACKEND`, bitwise-verified, default untouched. B7-30 drjit
  exploration remains as committed evidence/probe lessons only.
- Records: `optimization_v7_backends/` (`B7_53_HANDOVER.md`, dossiers,
  `evidence/trials/` distilled records), gate tests `tests/optimization_v7/`.

### Era 4 — v8 native default attempt (N8 items; closed `numba_improvement_only`)

- `53397af6` N8 waves 1–2 + N8-40 machinery (policy-selected region dispatch,
  wired **inert** in shipped state); `194cb973` N8-41 vendoring into
  `solweig_light._native_dispatch`; `3079d69a` qualification registry in
  wheels; `a19e22db` N8-40b public seam at H=1; `5d020fd3` native wheel gates;
  `b4a4c5ba` N8-40 completion + N8-42/43/44 unavailable-state closure.
- Outcome: native default NOT earned on measurement; selection
  `numba_improvement_only` (`evidence/handover/n8_60_handover.json`).
- Records: `optimization_v8_native_default/`, gate tests
  `tests/optimization_v8/` (still the home of the installed-wheel gates).

### Era 5 — N9 FINAL (F0–F7; closed `closed_cpu_only`)

- `e04a8ece`+`410bee47` F1D/F1M mode-specialized packed decode + A-plus
  comparator + classifier scratch-reuse contract; `06ddbd7b`+`07114fdc` F1S
  bounded stream dispatch (replaces whole-scene materialization);
  `1581d882` F4 behavior: bounded stream row B as the **shipped longwave
  default** (thread_budget pinned 1, all-raw structural guard); `08d05cef`
  F4 removal/packaging: N8 native row + qualification machinery archived
  repo-only under `experiments/optimization_v8/native_dispatch/`.
- Terminal selection, gate table, and merge manifest:
  `optimization_n9_final/FINAL_SELECTION.json` + `MERGE_MANIFEST.json`.

v4 produced **no src change** — it is the operational/validation-discipline
packet (strategy catalog, L0–L4 test discipline, ledger templates;
`CHANGELOG_V4.md`). The later operational packets (v5/v6/v7/v8) each carry
their own process docs alongside the src records above.

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
