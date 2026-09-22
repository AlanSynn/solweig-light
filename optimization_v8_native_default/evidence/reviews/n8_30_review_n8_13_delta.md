# n8-rev-n8-13 delta review: commit 823ab00a (harness CLI delta, N-D2 repair, tier-A record)

**Verdict: APPROVE-WITH-NOTES** — deltas 1 and 2 PASS outright; delta 3 passes with two required record corrections (R13-D1, R13-D2). No REJECT-level finding: the measurement archive is intact and authoritative, parity is complete, and every direction-level conclusion survives independent recomputation.

Reviewer: n8-rev-n8-13 (independent; authored none of the reviewed work). Worktree `/Users/alansynn/Workspace/solweig-v8-native` @ 823ab00a. Machine-readable twin: `n8_30_review_n8_13_delta.json`.

## Delta 1 — quiet_window_abc.py CLI delta: PASS

- **Default identity (executed, not read):** `tuple(int(s) for s in '128,1024'.split(','))` == `BLOCK_SIZES` (128, 1024); a full default `--check-only` run returns rc=0, iterates both sizes x 3 mixes (6 cells, all `pass (A0==C1==C1k==B1==B1k)`), and archives a record whose 13-key schema is set-equal to the parent commit's. Loop order and B-derived seeds unchanged, so default invocation is bit-identical.
- **Gate:** refuses with rc=2 and `[gate] ... aborting before any timed work` on stderr; archives check-tagged with `mode: 'check-only (gate refused; no timing)'`, `reps: 0` — matching the committed refusal `abc_quiet_window_check_20260922T232442Z.json` (load 10.177 > 8.0). `check_only=True` is hardcoded in the refusal archive, so a timed invocation that refuses can never be mistaken for a measurement. Boundary semantics match the amended gate: refuse on `load > max`, so exactly 8.0 proceeds. The loadavg is read before the timed loops; `kernel_pair()` + `_find_b_consumer()` run pre-gate but are untimed setup (N13-6).
- **Adversarial:** `'abc'`, `'128,'`, `''` raise ValueError at parse — before `kernel_pair()`, before any parity exists to mask, no archive written, exit 1 via traceback (clear but ungraceful; N13-7). `'0'` parses and completes `--check-only` with vacuous B=0 parity-pass cells (N13-7). `--max-loadavg 0` and `-1.0` both refuse cleanly (rc=2, refusal record captured). No evidence/ writes from any probe (listing verified identical before/after; archive redirected to a /tmp sink in-process).

## Delta 2 — N-D2 conftest repair: PASS

- Zero bare `from conftest import` remain under `tests/optimization_v8/native/` (grep: 0 hits). `native_test_helpers.py` is unique tree-wide (single .py).
- The helpers module is a verbatim body-move of the old conftest (same sys.path bootstrap, same importlib reuse of the frozen `lw_identity_grid`, same import-time `kernel_pair()`, all 14 formerly-exported names present); `conftest.py` keeps the session fixture, F401 re-exports, and the module-under-test import, so side effects are preserved. No circularity (helpers never imports conftest).
- Executed: native-first combined order `native/region/integration/policy/dx` → **451 passed in 37.50s** (coordinator: 451/~37s); standalone native → **194 passed in 0.85s** (coordinator: 194). Residual bare-conftest hits live in other packages' trees (v5/v6/installed); the installed/conftest.py match is docstring-only.

## Delta 3 — tier-A record fidelity: PASS-WITH-REQUIRED-CORRECTIONS

Recomputed every table in `n8_31_tierA_record.json` against `abc_quiet_window_timed_20260922T232539Z.json` + the stderr transcript (script-enumerated compositions; no trusting).

**Traces exactly:** ambient start/end loadavg (6.57/6.17/6.09, 6.84/6.24/6.11); per-cell loadavg (6.6/6.6/6.8); all four kernel-leaf ranges; B1k ratio 2.6–2.9x; all producer-accounting cells and deltas; parity strings in all 3 cells; 0 censored cells; kernel-only all-raw (C1 0.100 < A0s 0.109); all verdict directions and the +14% loss arithmetic on the record's own table.

**R13-D1 (required):** `end_to_end_min_ms` is not reproducible under any single composition rule. Uniform protocol composition (produce+views+pack+kernel, all min) gives all-binary B1 0.504/C1 0.472 (claimed 0.503/0.471 — views dropped), all-raw B1 0.203/C1 0.169 (claimed 0.205/0.171 — needs produce **median**), A0s all-raw 0.149 (claimed 0.150 — needs component-wise rounding), while the mix row matches views-included. Discrepancies are 0.001–0.002 ms in **both** directions (no direction-shopping pattern), and recomputing uniformly flips no conclusion: C still wins all-binary and mix end-to-end (0.472 vs 0.577; 0.427 vs 0.452), all-raw remains the sole loss (0.169 vs 0.149, +13%), C < B1 everywhere. Transcription-fidelity repair, not re-measurement.

**R13-D2 (required):** the tier-A memory view "3.17 GB" has no committed source — the harness archives loadavg only, and `host_quiet_window_note.json` says "~3.2 GB (inactive+free)" at 17:52 local, pre-run. Gate satisfaction is plausible; the precise number is unevidenced. Add provenance or restate.

**Recommended:** N13-2 all-raw pack_masks quoted as "0.0277 min_ms" but all-raw min is 0.0274 (0.0277 = median truncated, or all-binary's min); attribution conclusion unaffected (loss 0.021 ~ pack cost). N13-3 A0p/C1k is ~5–6x (4.97/5.61/5.92), not "~4-5x" — conservative. N13-5 record's `next[]` cites the superseded 4.4 GB tier-B floor (amendment 1955Z corrected it to 1.5 GB; the record postdates the amendment), and `recorded_utc` holds local time. N13-7 argparse-level `--block-sizes` validation.

**Amendment 1955Z allocation audit: VERIFIED.** Against `adversarial_inputs` shapes at B=1024, P=153, W=8, G=128: (B,P) f32 x3 = 626,688 B each, bool masks 156,672 B x2, uint32 [G,P,W] AoSoA = 626,688 B x3, (B,7) outputs 28.7 KB — order ~4–10 MB total, independent of scene size; the 1.5 GB floor is ≥150x need. The whole-scene ~2.25 GB N6 envelope correctly remains the driver/pipeline-campaign obligation.

## Scope guard

No timed benchmarking (check-only paths and test suites only), no builds, no commits. Writes confined to `evidence/reviews/` and `/tmp/n8rev_n8_13/`. Tier B was not run and not waited for.
