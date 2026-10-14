# T01 L2 paired benchmark: landcover protected cell (S10)

Date: 2026-10-13. Commit under test `33ab050f` (T01) vs source-identical-to-main
`4e76183a` (A side; census commit touched docs only, src == `b3e5ca59`).

## Protocol

- Cell: protected cell #1 — "standard landcover U daytime + night, no-env
  defaults, 24 steps". Scene: `tests/reference/optional_original_cpu/landcover`
  (the E2E golden scene), full `run_tile` entry, all ten output flags on.
- Paired alternation: 5 pairs; each observation = 1 warmup + 3 timed in-process
  `run_tile` executions in a fresh subprocess per side (separate source trees,
  independent JIT caches; A tree = detached worktree at `4e76183a`).
- Timing inside the process (`perf_counter`), subprocess startup and JIT cache
  load excluded. Documented census deviation applied equally to both sides:
  GDAL cache capped at 256 MiB + explicit 5.5 GB budget (Slurm-step admission
  mismatch, see census evidence; does not differ between arms).
- Raw record: `/storage/scratch1/1/dsynn6/solweig-light-s10-raw/bench/`
  (`run_tile_timed.py`, `paired_ab.jsonl`); archived to Dropbox `s10/`.

## Result

| pair | A median (s) | B median (s) | ratio |
|---|---|---|---|
| 1 | 3.2828 | 2.0017 | 1.6400 |
| 2 | 3.2467 | 1.9913 | 1.6305 |
| 3 | 3.2271 | 1.9725 | 1.6360 |
| 4 | 3.2623 | 1.8926 | 1.7237 |
| 5 | 3.2608 | 1.9551 | 1.6678 |

**Paired-median geomean speedup 1.659** (min 1.631, max 1.724) on this cell —
far above the 1.10 candidate gate, with tight per-pair spread (A arm
range 3.23–3.29 s, B arm 1.89–2.04 s). Matches the census attribution
(~1.31 s/24-step serial-reference stage removed).

## Correctness side of the same cell

B vs the original-CPU golden on this exact scene is enforced by
`test_chronological_tiff_pipeline[landcover-False]` (passed; route counters
24/24 primary) under frozen `comparison_v1.json` budgets — see
t01_l1_kernel_differential.md. A (main) takes the reference fallback there,
which is the original code path itself.

## Threats to validity

- Single host, shared login-class node (noise policy: paired alternation;
  no quiet-window retry was needed — spread is small).
- One scene/tile size (golden 0_0). Multi-tile throughput and larger-tile
  behavior are measured separately in the campaign-level held-out run.
- `run_tile` includes preprocessing cache reuse from `processed_inputs`
  (copied per observation); both arms identical.
