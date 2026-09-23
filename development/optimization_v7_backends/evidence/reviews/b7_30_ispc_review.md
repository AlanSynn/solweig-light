# B7-30 review — B7-20 C_native (ISPC) — APPROVE-WITH-NOTES

Independent reviewer verdict for `/Users/alansynn/Workspace/solweig-v7-native/experiments/optimization_v7/native/`
(worktree c66ff3b6). Full detail in `b7_30_ispc_review.json` next to this file.
Method: sandboxed copy at `/tmp/b7_30_review` (dylib/kernel/adapter sha256-verified
against capability.json), candidate untouched, fresh numba cache, worktree `.venv-v7`,
baseline oracle = worktree src blob `27ba6ce4…` (git hash-object verified).

## All five author claim families held

1. **1040/1040 bitwise** — reproduced exactly (rerun exit 0, log identical modulo
   wall_s): 520 frozen calls x gangs 4/8, uint32-view comparison (NaN payload/sign
   included), 0 rejections, 0 canary mutations.
2. **Zero FMA** — independently reproduced: rebuilding the kernel with the build.sh
   flags (ISPC 1.31.0, `--opt=disable-fma` confirmed in COMMON_FLAGS for both
   targets) yields assembly **byte-identical** to the shipped `.s` files, with
   0 hits for `fmadd|fmla|fmsub|fnm*`; reviewer additionally verified 0
   `frecp*`/`faddp`/`fmlal` (no reciprocal approximation, no tree reduction);
   pi from immediate 0x40490FDB + hardware `fdiv.4s`; `ldrb`+`cbz` real uniform
   branch for solar_gate; f64 chains as `fmul.2d`/`fadd.2d` + `fcvtn` RN cast.
3. **22/22 rejections; 340 size-sweep + 84 payload-sweep bitwise** — reproduced,
   log identical modulo wall_s.
4. **Guard-page probe, B=0, aliasing** — probe reruns clean; reviewer negative
   control (raw ctypes, B claimed 4096 over physically 17-row arrays) faults
   (rc=-10) on both gangs, so the mechanism is real; B=0 short-circuits to
   float32 (0,7); input-input aliasing admitted and bitwise-equal.
5. **Dev-tier timings honest** — as-shipped 1T adapter does lose to 4-thread
   numba (~0.59-0.64x from timing_log.json); chunked 4-thread kernel claim
   ~2.2x at B=65536 is supported by the log arithmetic (21.20/21.02 ms vs
   9.68/9.50 ms = 2.19x/2.21x) and is bitwise-asserted after every chunked rep
   at exactly the timed B sizes (16384, 65536). Chunk schedule legality is
   sound: independent pixels, disjoint outputs, read-only shared tables,
   stateless kernel, ctypes releases the GIL.

Typed-graph audit (source level, vs numba blob `27ba6ce4…`): two ordered sweeps;
reflection only from A0+lup; solar_gate true branch A8,A7,A3,A2 / false A7,A2;
f64 chains rounded to f32 only at the accumulator add; sky chain f32; pi bits
0x40490FDB; ordered left-fold outputs; +0 init; lanes own independent pixels only.
All confirmed.

## Findings (no medium/high)

- **F1 (low)** — probe wording overstated: only `vb` (first-placed input) is flush
  with the guard page; `out` is the lowest array (43,367 B below the guard), so an
  out write-overflow cannot fault and the probe checks no-fault, not out contents.
  Mitigated by read-side fault coverage + shared mask + size sweep. Fix placement
  and wording before integration review.
- **F2 (low)** — shipped "reject P=610" case only resizes `sh` and is rejected by
  the shape check, not the P bound. Reviewer supplemented with a consistent
  P=610 block: the bound fires ("P=610 outside admitted 1..609"); P=609 admitted
  bitwise. Count claim holds.
- **F3 (low)** — proof_record.md quotes chunked ~10.7-10.9 ms / ~2x; the log says
  9.50-9.68 ms / 2.19-2.21x. Stale prose; direction unaffected. Sync it.
- **F4 (note)** — the chunked path lives in timing_dev.py, bypassing the guarded
  adapter (raw pointers, caller-owned lifetimes, no per-chunk failure isolation)
  and A always runs first (not the protocol's frozen alternating order). Author
  self-flagged. Any threaded integration needs its own adapter-level
  guard/alias/lifetime review.
- **F5 (note)** — portability: arm64 NEON + ISPC toolchain, `.dylib`-only loader,
  local prototype binaries.

## Recommended disposition

Advance C_native into the B7-30 A/B/C selection trials as an exact eligible
candidate. Performance numbers remain dev-tier; the B7-03 frozen protocol
(exclusive lease, alternating order) is the decision authority. F1-F3 are
candidate-side doc/test touch-ups, non-blocking for selection.
