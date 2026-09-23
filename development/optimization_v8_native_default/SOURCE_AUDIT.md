# Source observations, prior evidence and new hypotheses

Reference pins: native branch `16cdc56cbc8755675487b9c9c1f5a7e987e2c9e4`, main `14e888760727583ef782a4dc0e7a5c7c6e6ff9d1`, upstream model `0d7fe742abeeddd890dd58fc76ed7f78bd47faec`. Consult SOURCES.md. Recheck actual checkout and closures before implementing; no reset is implied.

| Finding | Classification | Consequence |
|---|---|---|
| `native_lw.native_longwave_primary` calls `_ensure_loaded` every time; it queries paths, reads JSON and hashes kernel source before `_load`'s own cache | source observation | hoist preparation to process/workflow handle; instrument actual avoidable overhead |
| native library currently not shipped; build invokes zsh and Homebrew-style ISPC fallback | source observation | automatic default cannot use this deployment mechanism |
| same single-thread native entry serves serial and parallel-labelled calls | source observation | equal-resource region/pool design needed, not a thread label |
| Main block default is not the B7-60 block=1024 workload | source observation to snapshot exactly | unchanged-default installed evaluation must be a first-class gate |
| B7-60 warm four synthetic tiles: A total median 538.84s, C 544.86s; three paired sim ratios >1 | prior reported measurement | preserve default and negative result; do not claim new wins from old kernel ms |
| B7-60 parent `ru_maxrss` excludes tile workers | source observation | repair whole process-tree resource accounting before concurrency admission |
| build stamp can exist before pre-launch input rejection/fallback | source observation | entry counters must prove actual native execution |
| B7-03 1.5-2.2% scale fraction is dense fallback dominated, explicitly NOT real packed path | prior protocol caveat | obtain current real-path cost coverage; no stale Amdahl denominator |
| AoSoA B kernel-only faster than ISPC but loses after pack boundary | prior reported measurement | direct producer-to-consumer layout is stronger next experiment than new framework search |
| current real scalar surface specialization can be float64 with f64 accumulator add then f32 cast | source observation/previous typed ledger | do not pre-round contributions; GPU f32-only path cannot impersonate this contract |
| derived four longwave masks may be sufficient for this consumer | new design hypothesis with explicit projection proof | assess prepare/read crossover and raw/error domain; not yet validated |
| full export validation/import/re-encode repeats stored payload traversals | source observation from prior audit | retain validation while merging passes if this residual is material |

## Calculations, not new timings

4 * 24 * ceil(1024^2/1024) = 98,304 expected LW calls if every step follows that branch. Actual counters may differ through guards/demand/fallback. 6.0187s divided by this count is about 61.2 microseconds/call, a sensitivity scale, not a measured loader cost. Reading a 10,194-byte source per call is roughly 0.93 GiB of logical reads, not necessarily disk traffic.

598.9s describes two spatial scenes with 24 time records each. B7-60 describes four synthetic spatial tiles. Neither is the actual 24-tile corpus. B7-60 prepared three-stage totals exclude parts of startup/data preparation; use the exact child boundary when comparing old numbers.

## Baseline distinctions

- R0: untouched upstream CPU artifacts / documented patched oracle where necessary.
- M0: frozen main DX and optionally separately measured main performance.
- A0: frozen accepted native-branch Numba under actual supported workload/resource conditions.
- C0: existing optional native implementation, including its regression.
- B1: improved layout/region in Numba.
- C1: new native with matched layout/region; no new physics.

Freeze A0/B1/C1 test data independently from their outputs. Candidate outputs never regenerate oracle goldens. Include numerical scope in evidence, not just a number named speedup.
