# B7-53 Final disposition & same-branch handover

Date: 2026-09-22. Branch `perf/cpu-optimization`, **unmerged and unpushed**.
Final HEAD at handover: see `git log` — frozen source state is `009a1e66`;
the only commits after it are the freeze record itself (`4ab7961a`) and this
track's evidence-only landings (`fc3f4f68` F1 repair, this document/ledger).
`git diff 009a1e66..HEAD --stat -- src tests` is **empty**: no source file
changed after the freeze pin.

## 1. Directive outcome (one paragraph)

An optional, exact CPU backend for the cylinder-longwave primary reducer
(`_longwave_primary`) was prototyped across three foreign backends, measured
under a frozen equal-budget protocol (B7-03), reviewed by independent
reviewers on immutable patches (B7-30), and the winner — a single-thread ISPC
implementation — was integrated as an opt-in env-gated backend (B7-40..42)
with bitwise-identical outputs to the unchanged Numba default, qualified on
real-scene chronology including 4-worker concurrency (B7-50). The default
path is untouched Numba; unsupported inputs fall back before any side effect;
a native failure inside the admitted domain raises instead of silently
falling back.

## 2. Selected portfolio

**C_native — ISPC 1.31.0 `lw_primary.ispc`, gang 8, ctypes adapter,
single-thread, synchronous.** Shipped in
`src/solweig_light/backends/native/` (source + build script with a grep-based
FMA-audit gate) behind `SOLWEIG_LIGHT_LW_BACKEND=native` (alias `ispc`).
Dylib builds on demand into `~/.cache/solweig-light/native`
(`SOLWEIG_LIGHT_NATIVE_CACHE` overrides); a missing ISPC toolchain fails
loudly. Default (`native`, `` and every other value) returns the untouched
Numba kernel objects.

## 3. Measured A/B/C summary (B7-31 protocol, b7_03_protocol.json)

A = unchanged Numba baseline; B = new AoSoA layout in Numba (control);
C = C_native (as-shipped single-thread ISPC). Equal CPU budgets; paired
alternating reps, independent child processes; sample 0 = process-cold guard,
warm = median of samples 1..3. Host: Apple M1 Pro, ambient load 13-17
recorded, exclusive agent lease during measurement. All output digests
bitwise-equal across A/B/C_native in every config.

Ratios are speedups: C/A = A's median time ÷ C's (below 1.0 means C is
slower than that variant).

| boundary (P=153)                 | A        | B        | C_native | C/A    | C/B    |
|----------------------------------|----------|----------|----------|--------|--------|
| kernel-only serial, B=4096       | 6.00 ms  | 1.19 ms  | 1.60 ms  | 3.76x  | 0.75x  |
| kernel-only serial, B=16384      | 23.91 ms | 5.01 ms  | 6.53 ms  | 3.66x  | 0.77x  |
| kernel-only serial, B=65536      | 93.34 ms | 19.58 ms | 26.56 ms | 3.51x  | 0.74x  |
| adapter total serial, B=16384    | 23.54 ms | 11.75 ms | 6.63 ms  | 3.55x  | 1.774x |
| adapter total serial, B=65536    | 93.94 ms | 46.28 ms | 26.25 ms | 3.58x  | 1.763x |
| warm real scene serial (216 calls) | 27.83 ms | 26.26 ms | 18.34 ms | 1.518x | 1.432x |
| warm real scene 4-worker         | 29.05 ms | 101.59 ms | 18.26 ms (1T) | 1.591x | 5.564x |
| process-cold guard               | 204-322 ms | 497-2241 ms | 2-40 ms | best | best |

B wins kernel-only (C/B 0.74-0.77x): its pack-free layout is genuinely
faster inside the kernel, but that advantage never survives the pack cost at
the adapter boundary — which is the boundary the pipeline actually calls
through. The 4T-labeled kernel config at B=65536 has C(1T) at 0.955x of
A(4T) — the 4.7% multi-threaded large-block caveat of §4.

Selection gates (frozen in B7-03 before results): adapter ≥1.10x over B on
held-out — **PASS** (1.774x / 1.763x); warm ≥1.05x over BOTH A and B —
**PASS** (1.518x / 1.432x); kernel ≥1.20x — triage-only signal.

Dr.Jit appendix (same protocol, drjit pool pinned to matched budgets):
kernel B=128: A 0.19 / C_native 0.08 / C_drjit 0.49 ms; warm serial 1T:
A 27.12 / C_native 18.19 / C_drjit 103.55 ms; warm 4T: A-4T 29.09 /
C_drjit-4T 74.65 ms; adapter B=65536: A 95.69 / C_native 27.74 /
C_drjit 177.40 ms. The author's dev-tier "2-10x at B=96/128" **did not
reproduce** at the honest adapter boundary once per-call JIT dispatch and
pack transposes were inside the measured region at matched budgets.

Primary records: `evidence/trials/b7_31_trials.json`,
`evidence/trials/b7_31_appendix_drjit.json`,
`evidence/trials/b7_32_selection.json`.

## 4. Qualified scope — read before quoting any number

- **Island scope.** The reducer is a minor island end-to-end (1.5-2.2% of the
  Lcyl wrapper at scale per the frozen B7-03 residual profile). The 3.5x
  adapter win is at the kernel dispatch boundary; end-to-end effect on large
  serial workloads is correspondingly small. The warm 1.5x on small-scene
  records is the more representative integrated outcome. No end-to-end
  speedup claim is made.
- **`actual_target_unverified`.** The 24-tile 1024² × 24-timestep corpus and
  its references are ABSENT from this machine
  (`evidence/freeze/b7_51_corpus_availability.json`). B7-52 remains blocked;
  no substituted/duplicated scenes were run and none may be quoted as the
  actual target. The historic 598.9s figure was two scenes, not 24 tiles.
- **4-worker caveat.** At the 4T-labeled config, C_native runs 1T by design
  (different budget); it beats A-4T on the warm sequence outright but trails
  A-4T by 4.7% on the 65536-pixel block. Large-block multi-threaded runtime
  configs are recorded as an integration caveat, not a gate failure.
- **Host.** Single Apple M1 Pro host; no Linux/final-source evidence; that
  remains part of the outstanding P7/P8 release gates, untouched by this
  track.

## 5. Rejected / closed tracks (with evidence)

| track | outcome | why |
|-------|---------|-----|
| B (Numba AoSoA layout) | integration rejected | dominated by C at every gated boundary (0.74x adapter, 0.70x warm); warm_parallel 4T regression 101.59 vs A 29.05 ms (per-call parallel pack launch overhead ×216). Kernel-only 4.8-5.0x noted. Flip condition: B7-24 decode-side block-major emit removing pack cost |
| PoCL / PyOpenCL | closed below threshold | B7-22 measured 0.91-0.94x — never reached the 1.05x warm gate; review closed the track |
| Dr.Jit LLVM | exact but rejected | 520/520 bitwise + adversarial 21/21; loses to A at every matched-budget boundary (2.6-3.8x); per-call JIT dispatch + gather-bound kernel |
| MLX / Halide | not executed by design | optional tier, conditional on earlier shortfalls; conditions never triggered |
| fused-radiation, prepared-decoder | stay OFF | rejected upstream of this track; not revisited |
| B7-24 second island | nominated, not executed | budget discipline; decode-side pack emit recorded as future work |

All three prototype reviews landed under `evidence/reviews/` (numba-b
APPROVE-WITH-NOTES with W=8 IR audit; ispc APPROVE with zero-FMA asm
byte-identical rebuild; opencl closed; drjit APPROVE-WITH-NOTES with the F1
probe-number repair landed at `fc3f4f68` — error was in the conservative
direction, exactness conclusions unaffected).

## 6. Exactness & safety evidence for the integrated path

- Spy-verified 520-call bitwise replay through the integrated dispatch
  (`tests/optimization_v7/integration/test_native_backend.py`, 7 tests):
  the native entry executes (call counter), outputs match the default
  bitwise (uint32/uint64 views), including the unsupported-input fallback
  path and B=0 edge; unbuildable toolchain fails loudly.
- Chronology: full 48-step real-scene run with `SOLWEIG_LIGHT_LW_BACKEND=native`
  produces outputs bitwise-equal to the default on all 10 rasters, both
  serial and under tpw4 concurrency
  (`evidence/trials/b7_50_chronology.json`).
- Protected regression: 44 tests
  (tests/optimization_v6/cylinder_lw + tests/optimization_v7/reference)
  green after integration. Default path returns the byte-identical baseline
  kernel objects.
- The fused route does not consult the backend resolver (dispatch-site
  change only; the resolver's other occurrence untouched).

## 7. Environment & reproduction

- Baseline venv `.venv` (python 3.12.13 / numba 0.67.0 / numpy 2.4.6,
  GDAL present) — the oracle; never mutated. Worktree venvs identical plus
  their backend (drjit venv lacks GDAL; cross-venv fixtures flow through the
  baseline-primed byte-cache in `tools/optimization_v7/trial_fixtures.py`).
- Enable the backend:
  ```sh
  SOLWEIG_LIGHT_LW_BACKEND=native .venv/bin/python <your pipeline entry>
  ```
- Re-run trials:
  `tools/optimization_v7/b7_31_run.py` (main A/B/C),
  `b7_31_appendix.py` (drjit, under the drjit worktree venv),
  `b7_50_chronology.py` (chronology qualification).
- Re-run integration tests:
  `uv run --python .venv/bin/python --with pytest -- python -m pytest
  tests/optimization_v7/integration tests/optimization_v6/cylinder_lw
  tests/optimization_v7/reference -q`

## 8. Worktrees and cleanup decision

Four detached worktrees are **retained** at the pinned immutable base
`c66ff3b6` (B7-00..03 groundwork): `solweig-v7-drjit` (candidate +
evidence; source of the landed F1 repair), `solweig-v7-native`,
`solweig-v7-numba`, `solweig-v7-opencl`. Their deliverables and the
reviewers' reports are landed in-tree under `optimization_v7_backends/`;
the worktrees stay for provenance and because the drjit candidate directory
remains the only copy of the reviewed `llvm_longwave.py` execution
environment. Removal is safe after any future re-verification and is a
normal `git worktree remove --force` per directory (they hold untracked
probe artifacts by design).

## 9. Handover state

- Branch `perf/cpu-optimization`: unmerged, unpushed, as directed. Ledger
  (`optimization_v7_backends/TASKS_CLAUDE.yaml`) carries final statuses;
  B7-52 stays `blocked_actual_target_unverified` until the corpus exists.
- Freeze: `evidence/freeze/b7_51_freeze.json` (source sha 009a1e66 + addendum
  for the two evidence-only follow-up commits) and
  `evidence/freeze/b7_51_corpus_availability.json`.
- If the 24-tile corpus appears later: run B7-52 as specified in
  `benchmarks/protocols/optimization_v7/b7_03_protocol.json` against the
  frozen source; until then, nothing in this document may be quoted as an
  actual-target result.
