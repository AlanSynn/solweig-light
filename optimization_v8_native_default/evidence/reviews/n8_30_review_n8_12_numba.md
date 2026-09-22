# N8-30 review of N8-12 — Numba B control (AoSoA consumer)

**Verdict: APPROVE-WITH-NOTES.** No blocking defects, no required repairs;
one recommended (non-blocking) test repair (F1).
Machine-readable twin: `n8_30_review_n8_12_numba.json` (same directory).

Reviewer: independent N8-30 review service; did not author N8-12.
Scope guard: nothing outside `optimization_v8_native_default/evidence/reviews/`
was written; reference oracle/grid and N8-11 producer imported read-only; no
network; no commits; no timed benchmarking (only the pytest reruns). Repo at
`16cdc56c` (`perf/native-optimization`, worktree `/Users/alansynn/Workspace/solweig-v8-native`).

Rerun (this review): `tests/optimization_v8/numba` → **396 passed, 0 failed,
0 skipped** (1.45 s; 110 bitexact + 33 admission + 253 producer; confirmation
rerun on the current bytes: 396 in 2.00 s); combined
with `tests/optimization_v8/reference` + `tests/optimization_v8/layout` →
**1289 passed, 0 failed** (2.89 s) — exactly the current expected counts
(396 + 112 + 781); the original briefing's 395/1288 was stale, predating the
author's final N6-teeth test (note F2, resolved).

**Post-dispatch state re-check.** After a coordinator state update, the
CURRENT files were re-verified: all N8-12 artifacts are byte-identical to
the reviewed state (mtimes Sep 22 16:28–16:32, all predating this review's
reruns; sha256 recorded in the JSON twin). The author's claimed final edits
are all present and were all covered by this review: the N6 citation with
failure mechanism (`lw_b_control.py:27-35`) and the N2 citation documenting
the AoSoA-boundary additions (:60-67); both producer leaves timed per size
with per-cell "A ahead/B ahead" lines and the N1 regime label on the B=128
rows (`measure_b_control.py:299-303`, 12 producer-leaf entries in the
JSON); and `test_b_pin_float32_view_convention_is_binding` with its N6
teeth, counted in the 396 throughout.

## 1. Bit-exactness — PASS

Every comparison is exact integer equality on the uint32 bits:
`bitwise_equal` (`lw_reference_oracle.py:168-173`) is `np.array_equal` on
`.view(np.uint32)`; grep for `allclose|approx|isclose|np.testing` over the
numba tests has zero hits. The grid is the FROZEN N8-04 grid **imported, not
copied**: `conftest.py:30-31` puts `tests/optimization_v8/reference` on
`sys.path` and `test_b_control_bitexact.py:36-39` imports `B_GRID`,
`P_GRID`, `_pin_args`, `adversarial_inputs`, `discriminator_args`,
`ordered_args` from the frozen modules (mtimes 15:33–15:37, all predating
the N8-12 authoring window 16:23–16:31).

Coverage: 6 B × 8 P × 2 surface profiles = **96 cells**, each asserting all
THREE formulations (parallel/serial/lanes) == oracle, parallel == serial,
lanes == serial, **and** the frozen `_longwave_primary(_serial)` cross-pinned
on the identical dense inputs (`test_b_control_bitexact.py:110-126`); P=609
boundary dedicated (:137-145); W=4 both-widths cell (:167-177); stride-12,
one-element stride-12, and negative-stride sky columns (:185-214).

All **8 discriminator pins** assert the exact claimed bits: mask·Inf NaN
`0x7FC00000` (:225); reflected-Inf visible-NaN `0x7FC00000` / occluded
`0x7F800000` (:234,:238); building raw-value predicate `0x40000000`/
`0x00000000` (:249-250); signed zeros with signbit (:256,:259);
division-not-reciprocal `0x40601716 ≠ 0x40601715` (:268-269); f32/f64
profile pins `0x3F800001`/`0x3F800000` (:281-282); RN32 `0x4B800001` plus
down-chain `0x4C000001` for all three formulations (:296,:298); BOTH
sweep-order pins `0x4B800000`/`0x4B800001` (:334-335,:347-348). The
float32-view convention is pinned **with teeth** (:301-326): the same kernel
fed raw uint32 compiles and silently loses the sky term (`a5 = 0x00000000`)
while the adapter path matches the oracle — the convention is load-bearing.

## 2. Semantic fidelity — PASS

Token-level diff of canonicalized bodies: `lw_primary_b_parallel` and
`lw_primary_b_serial` arithmetic cores are **character-identical** to the
frozen `_longwave_primary` / `_longwave_primary_serial`
(`cylinder_longwave.py:94-178`) modulo exactly the intended substitutions —
`sh/vs/vb/sun/shade[pixel,patch]` → `[gang,patch,lane]`, `lup[pixel]`/
`output[pixel]` → `[row]`, shape unpack, output passed in rather than
allocated, row loop with `gang=row//width`, `lane=row-gang*width`. Ten f32
accumulators, two ordered sweeps, reflection barrier on the completed
`a0+lup` with the true IEEE division by stored pi `0x40490FDB`, `solar_gate`
a real branch, `fastmath=False` on all three decorators
(`lw_b_control.py:87,142,191`). No reassociation, no fastmath flag, no
barrier reorder, no division→reciprocal. The lanes formulation preserves
per-lane operation ORDER (only loop nesting changes); its relocation of the
`building` predicate inside both gate arms is a pure function of the same
inputs — no bit effect; padding lanes are never visited (`live` bound,
:211); it is experimental and **not dispatched** (:409, :416-418).

## 3. Admission parity — PASS

Guard-for-guard and in order against `lw_native.primary`
(`lw_native.py:169-219`), with character-identical `_need_array`/
`_scalar_spec`/`_reflection_spec` helpers: sh type/dtype/ndim → gang gate →
P 1..609 → rows<0 → **rows==0 early return beating all downstream checks
including `out`** (pinned `test_b_control_admission.py:221-231`) → vs/vb →
C-contig → sun/shade → solid/sine/cosine → solar_gate stride-1 → sky
any-stride → directions/gate (shape only) → lup → surface spec → reflection
factor → out validity + the same 14-array alias loop in the same order.

**0-d reflection_factor**: both arms admit `np.float32` scalar and 0-d f32
ndarray, both reject a Python float with the same message
(`lw_native.py:138-144`, `lw_b_control.py:302-308`) — **no divergence**;
positive admission is pinned bitwise-equal to the scalar form
(`test_b_control_admission.py:184-191`). Strided/one-element/negative
columns admitted and bit-verified. Two precedence divergences exist, both in
doubly-invalid corners where both adapters reject (domain unaffected,
documented at `lw_b_control.py:53-67`): native gates its explicit gang param
before sh, while B must validate sh's ndim before W is readable from the
shape; and B's rows-type / `G=ceil(rows/W)` checks have no native analog
because native derives B from `sh.shape`.

**Judgment on those deviations (coordinator-requested): boundary-necessary,
not admission drift.** (a) B's signature carries no `gang` parameter — W is
*derived* from `sh.shape[2]` (the producer's chosen width, data-coupled), so
sh must pass isinstance/dtype/ndim before a width exists to test; native's
explicit gang merely selects the g4/g8 dylib and is caller-decoupled from
shape, so B cannot even express "gang ≠ data width" — a strictly *smaller*
expressive surface than native, and the divergence is rejection-precedence
only on inputs both arms reject. (b) `rows` is explicit because `[G,P,W]`
cannot recover a tail (`G=ceil(rows/W)` conflates rows in `((G-1)W, GW]`);
without the type check, `rows=9.0` would dispatch a float64 numba
specialization and fail *inside* the kernel (`range(float)` TypeError,
post-launch), violating the contract's pre-launch-decline class — the bool
rejection keeps the same TypeError discipline. The `G==ceil(rows/W)` check
is a **memory-safety precondition**: `rows > G*W` would compute
`gang = row//W ≥ G` and index `sh[gang,...]` past the allocation
(out-of-bounds read in an njit kernel). The N2 framing is likewise
structural: producer strictness (duck/subclass/lazy declines) attaches to
*acquiring* the packed buffers upstream; at the ndarray boundary there is no
visibility object left to decline. The shared admission domain is identical.

## 4. Binding notes honored — PASS

N6 (float32-view convention): the adapter constructs `sh/vs/vb
.view(np.float32)` itself **inside** the admitted call
(`lw_b_control.py:406-413`), so the zero-copy view cost is counted; every
kernel entry point in tests and the measure script feeds views; the
mutation check proves the convention load-bearing. N1 (per-B accounting):
the results carry BOTH `block_pixels` 128 and 1024 for all three mixes with
separate producer+classify leaves per size, and the script's own printout
labels the 128 regime "note N1 regime: do not read the B=1024 rows here"
(`measure_b_control.py:299-301`).

## 5. Measurement honesty — PASS (with note F3)

INFORMATIONAL/NON-PROMOTION labels in the docstring (:13), the JSON `label`
field, and the print header (:286). loadavg recorded at start, per block,
and end. min-of-N with median co-reported, warmup 3, gc disabled during
sampling. `bitwise_equal_A_vs_B` is `true` in all six configs and is
computed by the script on the exact timed artifacts (:271-274). Kernel-leaf
B-vs-A speedups reproduce: 7.3–9.8% (adapter arm, min) at B=1024; A≈B
end-to-end at B=1024; lanes slower everywhere. Provenance complete
(head/branch/platform/python/numpy/threads/timestamp). Regime unpins in the
prose claims are note F3.

## 6. Ownership + hygiene — PASS

`git status`: zero tracked modifications; `git diff HEAD` empty; N8-12 files
confined to `experiments/optimization_v8/numba/` (+ results JSON) and
`tests/optimization_v8/numba/`. Producer untouched:
`experiments/optimization_v8/layout/direct_aosoa.py` mtime Sep 22 16:10:03
(N8-11 review written 16:22) — unchanged since before that review; sha256
`e41e1ce9ba4c4103ec54ae16669d91a762e08c8b` recorded this review for future
bounding. No `src/` writes; no default enable — `lw_primary_b` is referenced
only by this packet's tests/measure and by N8-13's
`experiments/optimization_v8/native/quiet_window_abc.py` comparison harness
(the intended B-arm consumer).

## Notes (F1–F3, none blocking)

* **F1 — vacuous poison test (recommended repair).**
  `test_padding_lanes_poisoned_after_production`
  (`tests/optimization_v8/numba/test_b_control_producer.py:144-174`) poisons
  via `block[:, :, 13:]` — but the lane axis of a `[G,P,W=8]` block ends at
  7, so that slice is **empty** (numpy-verified: shape `(2,3,0)`;
  assignment is a no-op). The real padding for 13 rows at W=8 is
  `(gang 1, lanes 5..7)`, i.e. `block[1, :, 5:]`. The test therefore
  compares two runs on identical buffers. The PROPERTY it claims is
  genuinely proven elsewhere in the same suite: `pack_aosoa`
  (`test_b_control_bitexact.py:46-59`) pre-fills every padding lane with
  `0x7FC00000`, so all 96 grid cells × 3 formulations (plus W=4, 609, RN32
  pins) run with truly poisoned padding and match the oracle bitwise, and
  the 252-cell producer test compares producer output (uninitialized
  `np.empty` padding) against poisoned manual blocks bitwise. The same
  construction defect exists in N8-11's `test_consumer_reads_only_valid_lanes`
  (`tests/optimization_v8/layout/test_consumer_parity.py:166-171`), which
  the N8-11 review cited as poison evidence — recommend a layout-owned
  follow-up repair; its substance likewise remains covered by N8-11's
  pre-filled-poison producer tests.
* **F2 — RESOLVED (stale briefing count, no author miscount)**: the original
  briefing said 395 / 1288; the CURRENT files measure 396 / 1289 (110 + 33 +
  253), all passing, 0 skipped — exactly the post-edit expected counts. The
  delta is the author's final `test_b_pin_float32_view_convention_is_binding`
  (N6 teeth), which this review examined and counted throughout.
* **F3 — regime unpins in prose claims**: "~8-12% B kernel leaf" and
  "lanes 3-4x slower" are B=1024-regime numbers — at the production block
  size 128 the kernel-leaf delta is 18-28% and lanes only 1.6-2.2x;
  "2.86 of 3.44 ms" does not reproduce exactly from the archived JSON
  (min 2.850 of 3.419 ms, median 2.881 of 3.631 ms, at B=1024 mix). The
  conclusions (producer+classify dominates ≈83% of end-to-end at B=1024;
  A≈B end-to-end; lanes slower, experimental, not dispatched) all stand.
  Per-block loadavg values are identical across all six blocks — plausible
  for a short run under steady load but carries little information; the
  start/end envelope is the meaningful record.
