# B7-30 review: B7-10 Numba layout control B — APPROVE-WITH-NOTES

Reviewer: independent GLM review (no verified Anthropic Opus route in this session).
Candidate: `/Users/alansynn/Workspace/solweig-v7-numba/experiments/optimization_v7/numba_layout/` at c66ff3b6, module sha256 `fcd9cf05…74566` (matches capability.json/proof_record.md). Baseline blob `27ba6ce4…` verified unmodified in the worktree before and after my reruns. Full detail: `b7_30_numba_b_review.json` (same directory).

## Verdict

**APPROVE-WITH-NOTES.** All author claims reproduced under my own runs; the typed-graph audit passes on every axis I was asked to scrutinize. Two low-severity notes, neither touching correctness: a documentation inaccuracy about tail zero-fill (F1) and a missing direct IR dump for the default W=8 kernels (F2).

## Rerun outcomes (candidate .venv-v7, NUMBA_CACHE_DIR redirected to /tmp)

| Check | Result |
|---|---|
| `replay_bitwise.py 4 8` | exit 0 — 4 configs (W=4/8 x serial/parallel) each 260 admitted / 0 rejected / 260 bitwise matched / 0 mismatched |
| `adversarial_checks.py` | exit 0 — 1842 checks, 0 failures, 108 rejection checks passed (reproduced exactly) |
| `ir_audit.py` (fresh cache) | exit 0 — identical counts all 8 specializations: 0 fmuladd, 0 fma, 0 fast-math flags, 0 asm fmadd/fmsub/fmla; B vector fops 75 serial / 67 parallel, A 0 |
| Reviewer probes (/tmp/b7_30_probe.py) | exit 0 — B=0, multi-payload NaN/Inf/-0.0, all-NaN-sh: bitwise vs both A kernels, 4 configs |
| `dev_timing.py` | NOT rerun (exclusive-lease policy; other agents on host). Code+logs audited instead |

## Judgments on the five audit axes

**(a) Branchless predicates — PASS.** `(sh==1)&(vs==1)`, `(vs==0)|(vb==0)`, 3-way `|` mask: identical truth tables to the short-circuit forms; `NaN==k` is False on both. Verified live with all-NaN sh (bitwise vs A). No float op newly unmasked: the `solar_gate` branch stays control flow, so sun/shade expressions execute only on the taken path.

**(b) Cast sites — PASS.** Every `np.float32` node matches A line-for-line (building, all ten accum adds, `0.5f`, `np.float32(np.pi)` = 0x40490FDB, folds); non-cast chains stay f64 until the accum add — confirmed textually for both gate paths and directly in IR: B's f64-surface specialization contains 28 `<4 x double>` ops (the f64 chains vectorized as doubles), f32-surface counts differ as expected. Both specializations replay bitwise.

**(c) Update order — PASS.** Gate true: A8,A7,A3,A2; gate false: A7,A2. Two strictly sequential sweeps; reflection only from A0+lup; ordered left folds, columns 2..6 = A5..A9.

**(d) Lane mapping — PASS.** `accum[k,lane]` allocated inside the prange body (thread-local per block); lanes never read each other; IR shows 0 `llvm.vector.reduce`, and the non-broadcast shuffles are only the stride-7 output-store interleave. Tails: `range(min(W, pixels-p0))` — no OOB read, padding never loaded (see F1 for a doc nit on padding contents).

**(e) IR audit — PASS (W=4 direct, W=8 empirical).** My independent greps (not the script's regexes) confirm 0 contraction/fastmath/fma-forms in all 8 fresh dumps; gate appears as `load i8 → icmp eq i8 → br i1` into two distinct loop regions; the only 3 selects in the serial kernel (6 parallel) are vectorizer runtime-dependence merges (`%brmerge`/`%conflict.rdx`), not gate logic. Note: `ir_audit.py` builds only W=4 kernels — F2.

## Adapter + timing honesty

Pre-launch `ValueError` with explicit reasons, no fallback path, inputs never written (hash-verified in-suite). Pack cost is **inside** adapter-total timing (adapter = validate + pack + kernel) and the pack kernels are schedule-matched; pack is 41-54% of serial adapter cells, matching the author's own disclosure. Paired alternating reps, median = upper-of-two (disclosed, conservative for B), both W variants measured. W=8 > W=4 in every cell (one tie at reported precision), robust to the high-variance 64K-serial W4 cell either way. Dev-tier caveats (2 sizes not 3, no cold-start) are disclosed.

## Findings

- **F1 (low, docs):** tail zero-fill claim is true only for the `'numpy'` pack engine; the default `'numba'` engine leaves packed tail slots uninitialized (`np.empty`, written only for lanes < width). Never read, so no correctness impact — but reword at the next capability re-issue (`longwave_primary_b.py:32-33`, `proof_record.md:59-60`).
- **F2 (low, evidence gap):** `ir_audit.py` audits only W=4; add W=8 before the B7-31/32 selection freeze so the default width has direct IR/asm evidence.
- **F3-F6 (info):** "67-75 `<4 x float>`" actually includes 28 `<4 x double>` ops (accurate in layout_and_schedule.md itself); "1842 + 108" double-counts (108 is part of 1842); dev-tier scope/variance notes; admission-surface observations (directions/gate shape unvalidated — unused, as in A; aliasing not rejected — inert and documented; ownership honestly `owndata=False` memsys like A).
- **F7 (info, verified-true):** recorded positive evidence beyond reruns (textual graph identity, thread-local accumulators, probe results) for the selection ledger.

## Recommended disposition

Advance B7-10 to the B7-31/32 A/B/C trials as control B with W=8 default, under the frozen gates. Conditions: reword F1 at the next capability re-issue; add W=8 to ir_audit.py before selection freeze (F2); any module edit invalidates the sha256 and requires re-review; final performance claims only from the perf owner's frozen campaign.
