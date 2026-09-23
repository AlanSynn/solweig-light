# F2 independent review — combined candidate `7abe526a..07114fdc`

Reviewer: F2 independent_reviewer (author-distinct; read-only on src/ and
tests/). Scope: the four-file combined candidate on
`perf/native-optimization` @ `07114fdc` (direct_aosoa F1D/F1M, lw_stream
F1S, _lw_dispatch rewire, aplus_decode comparator).

## OVERALL VERDICT: APPROVE

No correction set required. No critical bug found; nothing meets the
reversion rule. Four notes for the integrator/F3 are listed at the end
(zero-risk actions, none blocking).

## A. EXACTNESS (specialized decode) — PASS

- Fallback-arm verbatim claim CONFIRMED: old and new each contain exactly
  5 occurrences of the generic runtime-divisor expression and 4 of the raw
  byte-assembly arm (patchmajor full+tail fallback, preflight fallback,
  blocked full+tail fallback); the F1M/F1S additions did not touch the njit
  classifier arithmetic (no removed `delta`/`degrees` lines in the diff).
- Independent reviewer probe
  (`f2_adversarial_probe.py`, result in `f2_adversarial_probe_result.txt`):
  the NEW `_produce_patchmajor` was compared against the BASE kernel
  compiled from the `7abe526a` blob itself:
  - 400-case grid (widths 4/8 x starts 0/3/5/7/13 x sizes
    0/1/7/8/9/127/128/131 x 5 mode mixes): outputs BITWISE EQUAL old==new,
    and equal to both python oracles (`n9_ref_decode` byte-wise
    independent decoder and `n9_legacy_expr_decode`, the exact prior
    arithmetic) on the valid extent. Both buffers poison-prefilled, so
    padding-lane non-writes are also identical.
  - Adversarial raw payloads (signed zeros, subnormals, +/-Inf, NaN
    payloads both signs): byte-exact through both kernels, no float
    conversion.
  - Reserved code 3 injected at EVERY (patch, absolute pixel) of mixed
    channels at odd starts, both widths: identical exception identity
    (`IndexError:('Reserved visibility code',)`) and identical poison
    write-prefix between old and new — the ternary arm's first-error
    position is the generic expression's; the binary arm's dead check is
    behaviorally inert.
  - Degenerate modes 0/3/5 through the fallback arm: identical old/new
    surface (mode 0 -> ZeroDivisionError; 3/5 -> reserved-code IndexError).
  - A-plus: `_decode_at_plus` bit-identical to `_decode_at` on the same
    adversarial mixes (compared as float32 BIT patterns; raw NaN payloads
    round-trip).
- The shifts/masks are exact for the non-negative pixels the range
  contract guarantees (`x>>3 == x//8`, `x&7 == x%8` for all ints in
  two's-complement semantics); operand dtypes/promotions match the
  generic expression's (uint8 data, int64 index/shift/mask).

## B. CLASSIFIER CONTRACT (F1M scratch reuse) — PASS

- Rejection matrix (`direct_aosoa.py:435-445`): non-ndarray, wrong dtype,
  wrong shape, non-C-contiguous (transposed), readonly all rejected with
  the parameter name in the message — all tested
  (`test_n9_f1m_rejects_bad_buffers`).
- Overlap rejection BEFORE any write (`direct_aosoa.py:490-506`):
  sun==shade, out-vs-asvf-storage, out-vs-prepared-coefficients all
  rejected; genuinely disjoint arena slices accepted (slot-style reuse) —
  `test_n9_f1m_rejects_overlapping_scratch_before_writes`,
  `test_n9_f1m_rejects_overlap_with_prepared_coefficients`. The check uses
  the FULL `np.asarray(asvf)` span — conservative direction (may reject a
  harmless layout, never misses a hazard).
- Clearing semantics (`direct_aosoa.py:506-511`): valid extent (all
  columns, lanes with row<rows) cleared on supplied scratch — inactive
  valid columns end False under a narrowed active set (poison-probe
  proven), padding lanes keep poison. Alternating day/night, changing
  active sets, repeated partial tails, all-false active set: all equal
  fresh allocation.
- `shade != not sun` at equality/NaN preserved (strict `<`/`>` untouched;
  NaN/Inf rows have BOTH bits false; tested explicitly).
- Direct-vs-dense parity: `test_n9_f1m_parity_dense_classify_then_pack`
  compares against the GENUINE OLD path — `patch_radiation._classes`
  (dense) + `da.pack_masks_aosoa` — under BOTH exact-table env regimes
  ('0'/'1'), fresh AND reused scratch, four start/stop windows.

## C. STREAM SAFETY (F1S) — PASS

- Lease lifetime: acquired once at mint (`lw_stream.py:271`); mint-time
  failure closes it (`lw_stream.py:303-305`); `_execute_row` releases it
  in `finally` (`_lw_dispatch.py:133-134`) — covers consumer-constructor
  failure, region cancellation, and post-launch native errors.
- Workers never re-enter public leasing: `_StreamBase.produce` calls
  `classify_block_aosoa` (contains NO leaf-lock acquisition — verified by
  read: no `_leased`/`_lock` reference) and `_produce_patchmajor` directly
  on the pinned `BorrowedVisibility` descriptors. `produce_blocks_aosoa`
  is never called on the routed path (asserted by
  `test_slot_payload_is_block_bounded_not_scene_bounded`'s bomb).
- Slot keying: `ctx.slot.id` matches `region_pool._SlotPool`'s actual
  contract — exactly `budget` slots with ids 0..budget-1, acquired/
  released around each block (`region_pool.py:408-426, 674-687`), so
  lease-exclusive per executing block. Pre-allocation
  `range(plan.thread_budget)` matches `shared_pool(None)`'s budget; a
  mismatch grows the table under `_alloc_lock`, still bounded.
- Canonical first-error: `test_reserved_code_canonical_first_error`
  injects a reserved code in a MIDDLE block (block 1 of 3 and block 2)
  and asserts the parallel stream (budget 3) raises the SAME error
  identity as the serial stream and a plain serial loop in the frozen
  per-block order, at the LOWEST failing block. Passes.
- Memory: slot = 3x uint32 + 2x bool at (B/8, P, 8) + (B,7) f32 frame =
  exactly 14*B*P payload (block_pixels % 8 == 0 is a plan gate, so
  slot_gangs*width == capacity exactly); B=1024/P=153 -> 2,193,408 B =
  2.092 MiB/slot, H=4 -> 8.37 MiB. No `14*N*P` cube anywhere on the
  routed path; `test_routed_peak_memory_independent_of_scene_extent`
  shows tracemalloc peak flat as the scene grows 4x.
- Edges: total=0 declines pre-launch (plan gate + region_route gate);
  total=1 exact vs whole-scene (`test_total_zero_declines_and_total_one_
  is_exact`); lane-misaligned blocks decline
  (`test_lane_misaligned_block_declines`).
- Decline parity: `test_plan_admission_mirrors_producer_exactly` asserts
  `(plan is None) == (produce_blocks_aosoa(...) is None)` across
  packed/mapped/dense/mixed/lazy triples, with a spy proving a decline
  never touches the region machinery. The admission predicate is the
  plural producer's own (`_admitted_channels` mirrors
  `produce_blocks_aosoa` line-for-line).
- Argument parity old->new: all 12 patch-level args identical objects/
  expressions (`values['steradian']`, `geometry.sine/cosine/
  longwave_cardinal_cosine/reflection_cardinal`, `Lsky_down[:, 2]`,
  `Lsky_side[:, 2]`, `Lup.reshape(-1)`, surfaces, factor); verified
  against the 7abe526a `_execute_row`.

## D. DEADLOCK / REENTRANCY — PASS

- The top-level leaf lease is held by the SUBMITTING thread only. Workers
  run `produce` (classify: no locks; decode: pinned arrays) and `consume`
  (leaf adapters take no leaf locks). No worker path calls
  `produce_blocks_aosoa`/`decode_block`/`_leased`.
- SELF_PARALLEL (B): `region_pool._run_self_parallel` dispatches strictly
  sequentially in the calling thread (in-flight == 1 by construction);
  pool workers are never spawned for B (`_ensure_workers` is only called
  by the fanout session) and merely idle-block on the queue if a prior C
  session created them. The Numba prange inside `lw_primary_b` is the
  only parallelism and touches no locks; the held lease cannot interact
  with it. No nested parallelism: the session guard raises
  PoolSessionConflict on re-entry.
- BLOCK_FANOUT (C): workers write disjoint slots keyed by exclusive
  scratch ids and disjoint output spans; shared inputs are immutable
  (readonly descriptor views, prepared coefficients). `load_generation`
  concurrency is pre-existing behavior (the old consumer also called it
  per block under fanout).
- H=1: zero background threads, calling thread executes (tested for both
  rows); H=4 fanout over four disjoint slots is bitwise equal to serial
  and doubles as the no-deadlock proof with the lease held
  (`test_stream_c_h1_and_h4_budgets`).

## E. EVIDENCE HONESTY — PASS

- `f1d_codegen_targethost.txt`: the division-removal claim matches its
  own census — the specialized kernels' 5 surviving div/rem are accounted
  (1x `rows//width` prologue, labeled; 4x inside the fallback arm,
  identified by operand-chain fingerprint `udiv 8, mode -> sdiv x, zext`),
  corroborated by the standalone literal-arm micro-kernels showing
  exactly 1 div each (the prologue). Vectorization explicitly NOT claimed.
  The cache-stub hazard is disclosed (fresh NUMBA_CACHE_DIR; an earlier
  warm-cache all-zero run discarded). Honest.
- `f1m_classifier_diagnostic.json`: labeled "DIAGNOSTIC -- variant-
  selection data only, NOT the F3 verdict", protocol "outside N9-CONT-v1
  timers", window_gate "NOT MET (1-min loadavg >= 5.0)" with loadavg
  8.956 recorded start/end, negative derived values retained raw. It can
  never be cited as an F3 number; its own label forbids it.
- Freeze-before-results: both F0 freeze docs committed in `704d01de`
  (2026-09-23T06:59-04), BEFORE the F1D+F1M result commit `e04a8ece`
  (07:33) and the F1S commits. Order correct.

## F. TEST RUN — PASS

`NUMBA_NUM_THREADS=2 NUMBA_CACHE_DIR=<worktree>/.numba_cache .venv/bin/
python -m pytest tests/optimization_v8/{stream,n9_producer,region} -q` in
the shared worktree @ 07114fdc: **661 passed**, 3 warnings (pre-existing
fork-policy DeprecationWarnings), exit 0. Plus the reviewer's own
adversarial probe: ALL PASS (see A).

## NOTES for the integrator / F3 (no code correction required)

1. FREEZE-FIDELITY: `f0_interface_freeze.md` lists
   `produce_blocks_aosoa(..., out=None)`; the implemented plural
   signature retains the base signature WITHOUT `out=` (only the singular
   `produce_block_aosoa` has it). The stream satisfies the scratch-reuse
   intent via BlockSlot + pinned descriptors, and nothing calls a plural
   `out=`. Recommend a one-line freeze amendment at F2 close (integrator
   sign-off, per the freeze's own amendment clause) recording that the
   plural `out=` is superseded by the private stream path — or, if the
   letter of the table is preferred, the small keyword addition. Zero
   behavioral impact either way.
2. FIRST-ERROR ORDER DELTA (documented, freeze-conformant): the stream's
   canonical first error is lowest-block-index (F0 freeze mandates this);
   the retired whole-scene path surfaced the scene-wide patch-major first
   position. Identical exception type/message; identical when only one
   reserved code exists (the realistic case); nothing is published on
   failure. Recorded here so the delta is deliberate, not accidental.
3. F3 HYGIENE: `f1m_classifier_diagnostic.json` is window-NOT-MET and
   must not be cited as an F3 magnitude (its label says so). The F1M
   "charge BOTH" comparison must be re-decided on F3's continuous timer.
4. `AosoaNativeCConsumer` and the whole-scene consumers remain in
   `_lw_dispatch.py` for measurement/comparison, per the module
   docstring — integrator cleanup scope (F4), not an F2 correction.

Reviewer probe artifacts (this directory): `f2_adversarial_probe.py`,
`f2_adversarial_probe_result.txt`.
