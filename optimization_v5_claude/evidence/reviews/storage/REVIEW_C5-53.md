# REVIEW C5-53 — S07 checkpoint digest+IO patch (commit 9b0d010f, integration bf99def0)

**Reviewer:** independent GLM review (Opus unavailable). Not the author.
**Patch:** `git diff 8b3252ca..9b0d010f` — `src/solweig_light/persistence.py` (+62/−5) and
`tests/optimization_v5/storage/test_checkpoint_digest_storage.py` (+208). Nothing else touched.
Scope claim verified: `--name-only` lists exactly these two files.
**Base:** 8b3252ca. Integration merge: bf99def0 (worktree `/Users/alansynn/Workspace/solweig-light-claude-v5`).

## Verdict

**APPROVE WITH FINDINGS.** The patch is a faithful, byte-identical replacement of the old
recorded identity — verified empirically, including the pathological signed-zero class, where I
proved old-path and new-path digests are equal (`new_live == old_live: True`). The three failure
boundaries are safe and loud. The zero-block law is correctly classified and, on this build
(GDAL 3.13.3), empirically real. **However**: the patch's central guarantee is misdocumented for
the live-band path (F1), the flagship identity test does not exercise the path `write()` actually
uses (F2), and the claimed 4.19M-pattern probe does not exist in the tree (F3). F1 is a
pre-existing flaw inherited unchanged from the base — not a regression — but on a
durability-critical patch it deserves a follow-up, and the docstring as written is false.

## Observed test runs (threads<=2, this worktree)

| Suite | Expected | Observed |
|---|---|---|
| `uv run pytest tests/optimization_v5/storage -q` | 24 | **24 passed** (14.07s) |
| `uv run pytest tests/unit/test_persistence.py -q` | 38 | **38 passed** (1.54s) |
| `uv run pytest tests/integration -k "resume or runtime" -q` | 11 | **11 passed** (18.58s) |

## 1. Diff scope — CLEAN

Only `persistence.py` and the new storage test. `_encode`, `checkpoint`, `write`, `_recover`,
`_validate_dataset` read in full; final file read end to end. Formats, paths, artifacts, atomicity
(`_atomic_json` tmp+rename+dir-fsync), and durability (payload write+fsync before return) unchanged.

## 2. The zero-block law — implementation correct; law confirmed on this build

`_stored_bytes_digest` (persistence.py:202-229) classifies each block by `bits & 0x7FFFFFFF`
(sign-bit-clearing mask): a float32 value has all non-sign bits zero iff it is ±0.0, so
- **nonzero/mixed block** (any other bit set: numbers, denormals, ±inf, any NaN payload) → hashed
  from buffer bytes;
- **signed-zero-only block** (some -0.0, rest +0.0) → `band.ReadAsArray` of exactly that block
  window (persistence.py:225); edge-safe: the slice shape clips the window, args order correct;
- **pure +0.0 block** → `bytes(block.nbytes)`.

Empirical confirmation on GDAL 3.13.3 (my probes, `/tmp/c553-review/`):
- A 1000×8 band (strips of 256 rows: 3 full + 232-row partial) with strip classes
  {all -0.0, all 7.5, all +0.0, all -0.0}: **all-(-0.0) strips, including the partial edge strip,
  read back as bit-zero (`[0x0]`)** — the law claim (elision incl. -0.0, read-back as +0.0) is real
  on this build.
- Denormals `0x00000001`/`0x80000001` are masked nonzero → buffer branch → stored → correct
  (probe E digest match over a 4,194,304-value seeded random-bit-pattern band with all special
  classes injected: recorded == read-back).
- **NaN payloads preserved bit-exact** through write+read-back, including sNaN forms
  `0x7F800001`, `0xFF800001`, `0xFFFFFFFF`, `0x7FFFFFFF`, `0x7FC12345` inside nonzero blocks
  (bit-level construction, no arithmetic).
- Big-endian (`>f4`) and Fortran-order inputs digest identically to native C-order
  (`np.ascontiguousarray(..., dtype=np.float32)` normalizes order and byte sex).
- Rewrite-after-flush semantics safe on this build (resume replay): flushed-nonzero block
  rewritten with +0.0 **does** store zeros (no stale-tile skip); elided(-0.0) block rewritten with
  9.5 stores 9.5.

**But see F1: the signed-zero read-back runs on the live band and reads GDAL's block cache, not
the file.**

## 3. Failure boundaries — all three safe and loud (probed; suite coverage partial)

Implementation shape: digests accumulate per write into `_pending_band_hashes`
(persistence.py:275, 460-463); `checkpoint` extends a **copy** (`hashes = {name: list(values)}`,
persistence.py:473) under a strict count guard (persistence.py:476-478) and clears pendings only
**after** `_atomic_json` commit (persistence.py:489-490).

- **(a) write succeeded, digest capture failed.** My probe (mock raising on the second field's
  digest): the exception propagates out of `write()`; pending is partial `[1, 0]`; `checkpoint`
  refuses via the guard; the on-disk record stays at the committed boundary (ts=1); close+resume
  replays from 1 and the run completes. 6/6 probe checks pass. Note `next_band` has already
  advanced, so the failed step cannot be re-written in-process — the operator must close and
  resume, discarding work since the last checkpoint. Loud, safe.
- **(b) missing/extra pending digests.** Probed: one popped digest → refused; a stale extra
  string → refused; record uncorrupted after each refusal; after repair the checkpoint commits and
  a fresh resume validates it and completes. 6/6. **The guard has no direct unit test** (F4) — no
  suite test touches `_pending_band_hashes` or injects a digest-capture failure.
- **(c) retry after partial commit.** Covered by existing suite tests and they are real:
  `test_successful_commit_prunes_orphans_without_reopening_writer` fails `_atomic_json` 3× then
  succeeds (pendings not double-consumed — extension is on a copy, clear is post-commit);
  `test_error_after_cursor_publication_recovers_new_committed_boundary` covers commit-then-raise
  (resume reads the committed record; no stale reuse).

## 4. Identity equality — true vs the OLD implementation; false as a disk-readback claim (F1/F2)

- **Non-circular verification is real:** `test_recorded_checkpoint_digests_match_published_bytes`
  runs the real 24-step scene (`checkpoint_interval` defaults to 1, runtime.py:326), then compares
  every one of the 24 recorded band digests against `_band_digest` — the base implementation's
  function — on a fresh `gdal.Open` of the **published** artifact, and separately verifies
  `state_sha256 == _digest(state.json)` and every payload file digest. This is independent
  read-back, not circular.
- **The unit identity test bypasses the live path:** `test_recorded_digest_matches_read_back_digest`
  (test lines 63-70) computes `_stored_bytes_digest` on a **reopened** dataset, where the GDAL
  block cache is empty. `TransactionalOutputs.write` (persistence.py:460-463) digests the **live**
  band, where the cache still holds just-written values. See F1.
- **Portability (the question posed): the patch is structurally portable, and probes the law
  per-block rather than assuming it globally.** Pure +0.0 blocks digest as zero bytes, which is
  correct under both an eliding and a storing build; signed-zero-only blocks resolve by read-back,
  correct under either law (merely a wasted small read if a build stores -0.0); nonzero/mixed
  blocks hash buffer bytes, correct for any lossless build. Residual assumptions on future builds:
  (i) no build elides a block whose raster-region bits contain any nonzero bit; (ii) no lossless
  value transformation (e.g. NaN payload canonicalization). A build violating either would produce
  digests that fail recovery comparison — a **loud false-fail at every resume, never a silent
  false-pass**. On the "identical to old read-back on all builds" claim: identity vs the OLD
  implementation is structural (both read through the same live-band cache; I proved equality on
  this build including the pathological class). Correctness-vs-disk is the law-dependent part;
  flagged in F1.
- One latent coupling (F5): `_stored_bytes_digest` hashes block-by-block while `_band_digest`
  hashes row-major 64-row chunks; the byte streams are identical only because default GTiff
  `Create` yields full-width strips (verified `GetBlockSize == [8, 256]` for 1000×8, block order ==
  row-major order). Adding `TILED=YES`/`BLOCKXSIZE` creation options would structurally diverge
  the two digests → guaranteed resume false-fail, with no guard or comment at the site.

## 5. Resume path — unchanged

`_recover`/`_validate_dataset` are untouched by this diff. Recovery still compares committed bands
via `_band_digest` with bitwise (tolerance-none) semantics plus timestamp metadata
(persistence.py:373-382); `_band_digest` retained verbatim (persistence.py:193-199). The
documented 1072-byte TIFF layout shift on resume is pre-existing behavior, deliberately excluded
from `raster_identity` (test lines 73-84), and not introduced here. The SIGKILL kill/resume test
genuinely SIGKILLs the process group at a committed checkpoint (`next_timestep >= 5`) and asserts
bitwise identity of all published rasters against a clean reference — and its resume only succeeds
because recovery validated the new buffer-derived digests against disk.

## 6. Findings (severity-tagged)

- **F1 [Medium, PRE-EXISTING — inherited unchanged, not a regression]: live-band digest
  divergence for signed-zero-only blocks.** persistence.py:225's `band.ReadAsArray` reads through
  GDAL's block cache. After `WriteArray`+`FlushCache` on a live band of all -0.0, a live read
  returns a **mix** of `0x0` (evicted, disk: elided → +0.0) and `0x80000000` (still cached -0.0),
  so the recorded digest differs from disk: probe shows `digest(live)=ec2feed6…` vs
  `digest(disk)=0c92bddb…`, and a full adversarial transaction (all-(-0.0) step 0) fails resume
  with `PersistenceError: Corrupt committed TIFF band: F, band 1` — recorded `7cea07d5…` vs
  read-back `0c92bddb…`, disk bits `[0x0]`. Once committed, the transaction **permanently refuses
  resume**. Impact: an output band containing any signed-zero-only block makes the run
  unrecoverable at that checkpoint. **Not a regression**: the old checkpoint-time `_band_digest`
  read the same live cache — I measured `new_live == old_live: True` and `old_live == disk: False`;
  old code false-failed identically. Never a false-pass (no disk state yields the -0.0-bits
  digest). Production exposure is low (physically valued SOLWEIG outputs don't produce
  signed-zero-only blocks; NaN masks are nonzero-bit), but the docstring at
  persistence.py:209-212 ("a block … is digested from the band itself, so the recorded identity
  always matches the bytes recovery reads back") is **false as written** — it matches what the
  *cache* holds, not what the build *stores*. Suggested fix direction: for signed-zero-only
  blocks, digest the buffer with -0.0 canonicalized to +0.0 once the build's elision law is
  confirmed (one-time per dataset confirmation), keeping read-back only for unconfirmed builds —
  this also repairs the pre-existing flaw. Suggested regression test: digest through the **live**
  writer, then validate via actual resume.
- **F2 [Medium]: the flagship identity test does not exercise the real path.**
  test_checkpoint_digest_storage.py:67-70 reopens the file before computing `_stored_bytes_digest`,
  so its 11-pattern sweep — including `negative_zero` and `signed_zero_mix` — would pass even with
  F1 present. Only the live path is the implementation; the suite never digests a live band.
- **F3 [Medium-Low, evidence integrity]: the claimed 4.19M-pattern probe does not exist.** Searched
  both worktrees (`4194304`, `2**22`, "4.19", "exhaustive", "bit pattern") across tests and
  `optimization_v5_claude/`: the committed law coverage is 11 curated patterns × 2 + 2 end-to-end
  tests. I ran a substitute — a 4,194,304-value seeded random-bit-pattern band with all special
  classes injected (probe E): recorded == read-back. The law holds broadly on this build, but the
  claimed evidence is not in the tree and should either be committed or the claim withdrawn.
- **F4 [Low]: the count guard (persistence.py:476-478) has no direct unit test.** No suite test
  tampers `_pending_band_hashes` or injects a digest-capture failure; my probes cover both
  directions plus repair-and-resume. Cheap to add; it is the linchpin of boundary (b).
- **F5 [Low, latent]: strip-layout equivalence is implicit.** Block-order == row-major only for
  full-width blocks (default GTiff strips). A future `TILED=YES` would silently guarantee resume
  false-fail. Add a comment or an explicit `block_x == cols` assertion at persistence.py:216.

## 7. Reviewer probes (all in /tmp/c553-review/, run under this worktree's venv, GDAL 3.13.3)

- `probe_law.py` — multi-strip mixed zero/nonzero/signed-zero band; all-(-0.0) band (disk bits
  `[0x0]` — law confirmed); random+finite bit band; rewrite-after-flush both directions;
  4,194,304-value seeded bit-pattern band; big-endian/Fortran digest equality. 7/8 (the one FAIL
  was a probe bug: arithmetic quieted sNaN payloads before writing).
- `probe_cache.py` — isolated the F1 mechanism: live `ReadAsArray` after FlushCache returns mixed
  `0x0`/`0x80000000`; `digest(live) != digest(disk)`; mixed-block case unaffected
  (`digest(live) == digest(disk): True`); multi-band all-(-0.0) affected regardless of interleave.
- `probe_old_path.py` — `new_live == old_live: True` (no regression);
  `old_live == disk: False` (pre-existing); stable across later writes.
- `probe_final.py` — failure boundaries: 12/12 (digest-capture propagation, partial pending, guard
  refusals both directions, record integrity, repair, resume, completion).
- End-to-end adversarial transaction (`probe_boundaries.py` probe D) — reproduced the F1
  permanent resume false-fail with a real committed record (evidence above).

## Bottom line

Recorded identity under this patch is bit-identical to the base implementation everywhere I could
measure, all three failure boundaries fail loud and safe, and the law handling is portable by
construction with violations surfacing as loud resume failures, never silent false-passes. The
durability caveat that must travel with this patch: a band containing a signed-zero-only block
still records an unresumable checkpoint — exactly as the base did — so the patch neither widens
nor narrows that exposure, but its docstring and its reopened-band test claim more than the live
path delivers. F1+F2 warrant a follow-up commit (canonicalized signed-zero digest + a live-path
identity test); F3 requires an evidence correction.
