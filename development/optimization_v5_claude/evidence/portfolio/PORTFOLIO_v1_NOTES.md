# C5-41 portfolio comparison — measured verdicts (GLM coordinator, Opus unavailable)

Host: macOS darwin 25.6.0, exclusive lease, threads=4 in-process, warm dense_urban_256,
min of 3 in-process `run_tile` reps, fresh scene copy per rep (no geometry cache hits).
Harness: `portfolio_v1.py`; scene: `evidence/census/scene_dense256` (prepared at bfd9915e).

## Wall-time table (seconds, min)

| config | base bfd9915e | v5 + P01-fused | v5 fused-off |
|---|---|---|---|
| t1_b128 (source default) | 20.728 | 22.675 | 18.297 |
| t1_b1024 | 20.564 | 22.212 | 17.830 |
| t4_b128 | 19.532 | 19.892 | 16.865 |
| t4_b1024 | 14.396 | 17.288 | **11.793** |
| t2_b1024 | 14.515 | 17.508 | **11.916** |

- Raw manifests: `/tmp/PORTFOLIO_base.json`, `/tmp/l2_cand_rays..g02` era + `/tmp/PORTFOLIO_v5nofused.json`
  (recorded at measurement time; configs identical).
- **R01a + G02 + S02 (fused off): 1.22x vs base at t4_b1024.**
- **P01 fused route as merged: +46% regression** vs same tree with admission disabled.

## P01 fused attribution (cProfile, threads=4, warm dense_urban_256)

| stage | fused | old route |
|---|---|---|
| `_shortwave` | 3.174 s | 0.704 s |
| `_longwave(_fused)` | 5.713 s | below top-120 |
| `decode_block` | — | 2.013 s |
| census total | 18.59 s | 10.34 s |

Verdict: per-lane scalar bit extraction + LW double-decode lose to block-vectorized
`_decode` at pipeline block shapes. P01 defaulted OFF pending rework (rad-impl);
synthetic 128² micro-diag (fused 0.891x) did not transfer. REVIEW_C5-31 APPROVE
stands for exactness; performance verdict here is measured rejection.

## G03 dispatch flip (measured)

Scene-shaped 256² probe, threads=4: `_gvf` 0.352 s -> `_gvf_fused` 0.097 s (3.6x),
bitwise equal on all 17 outputs. Wired into engine dispatch at 137489e2; L2
chronological check bitwise-identical vs pristine reference (23 artifacts).

## Second-wave decisions (C5-50..54)

- C5-50 R04 bush certificates: **REJECTED — not activated.** `bush = np.logical_not(vegdem2*vegdem)*vegdem`
  is identically 0 for every scene with dem >= 0 (both L2 fixtures and both 1024
  fixtures verified: bush.max()==0); the step-major fallback with `_bush_active`
  is unreachable on real data. No residual exists to attack.
- C5-51 P04 ASVF reuse: no census signal (asvf share negligible). Not activated.
- C5-52 G01 GVF prefix replay: G03 already captured the GVF win; residual small. Not activated.
- C5-53 S07 checkpoint digest+IO: **ACTIVATED** (checkpoint+flush+digest ≈ 2.84 s of
  16.3 s warm vegetation_256 ≈ 17%, scales with pixels x steps). Owner rt-impl.
- C5-54 comfort/forcing specialization: no measured residual. Not activated.
- P01 rework continues under C5-21 disposition (default OFF until re-measured).

## L2 chronological gate status

Reference: `REFERENCE_bfd9915e_dense256.json` (23 substantive artifacts, double-run
determinism verified). Candidate checks after each integration step: bitwise identical
after rays, +S02, +G02, +P01, +G03+flip. Fixture: dense_urban_256, 24 steps, 153 patches,
10 save flags, checkpoint_interval=1.
