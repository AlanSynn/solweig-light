# C6-50 evidence: prepared multi-channel visibility decoder

Task C6-50 (decoder_specialist). Worktree
`/Users/alansynn/Workspace/solweig-light-v6-decoder`, detached at
`5e1fab467f7e6038dcf3992cb694008a51ea2c58` (see `worktree_commit.txt`).
No branch was created, checked out, committed or pushed. Writes were confined
to the owned paths:

- `src/solweig_light/geometry/visibility_prepared.py` (NEW private module)
- `tests/optimization_v6/decoder/` (6 test files + probe, conftest)
- `optimization_v6_continue/evidence/decoder/` (this directory)

Route record (honest): implemented by GLM-5.3 via Z.ai. No other identity is
claimed for this work.

## Verdict

DELIVERED. The prepared decoder decodes all demanded shortwave channels
(shadow, vegetation, vegetation_building, diffuse) or longwave channels
(shadow, vegetation, vegetation_building) in ONE native entry with:

- exact decode order and error precedence vs the original per-channel path,
- bitwise-equal decoded channels on real packed/mapped payloads,
- no hidden whole-payload copy (borrowed descriptors, tuple-identity proven),
- complete fallback (drop-ins return `None`; the original path is unchanged),
- stable lock lifetime (all owner locks acquired once in sorted-by-id order).

All 95 tests in `tests/optimization_v6/decoder/` pass; the base unit file
`tests/unit/test_duplicate_visibility_decode.py` still passes (9/9), proving
base behavior is untouched.

## Environment

- Python: `/Users/alansynn/Workspace/solweig-light/.venv-light/bin/python`
  (3.11.16), numba 0.67.0, numpy 2.4.6, macOS 26.6.2 arm64.
- Kernels: `@njit(cache=True, fastmath=False)` (no fastmath, per task).
- Tests need `PYTHONPATH=src` (package not installed in the venv) and run
  under the conftest-set `NUMBA_NUM_THREADS=2` census convention;
  `SOLWEIG_LIGHT_FUSED_RAD` is pinned to `0` per-test via `retained_route()`
  so v5 fused tests in the same pytest process are unaffected.

## Commands and exit codes

Recorded runs (cwd = worktree root):

```
PYTHONPATH=src .venv-light/bin/python -m pytest tests/optimization_v6/decoder/ -q
  -> 95 passed in 3.98s, exit 0
PYTHONPATH=src .venv-light/bin/python -m pytest tests/unit/test_duplicate_visibility_decode.py -q
  -> 9 passed in 0.94s, exit 0
.venv-light/bin/python tests/optimization_v6/decoder/probe_decoder_timing.py \
    optimization_v6_continue/evidence/decoder/timing_probe.json  -> exit 0
shasum -a 256 <module+tests> > sha256.txt -> exit 0
```

Full-suite pytest was run as one invocation (95 passed, exit 0); the three
files were additionally iterated individually during development, final state
green. `test_inventory.json` holds per-file counts.

## Completion gates

1. Decode order exact / precedence. `test_error_precedence.py` (17 tests)
   plants competing faults at different checkpoints and asserts the identical
   type AND message at the identical point. Matrix (earlier checkpoint wins
   in both paths):
   - reserved-in-shadow vs closed vegetation -> `IndexError('Reserved visibility code')`
   - reserved-in-shadow vs range-error-in-building (fewer patches) -> reserved
   - range-in-shadow vs reserved-in-vegetation -> `IndexError('Visibility block interval out of range')`
   - closed shadow owner vs reserved-in-building -> `RuntimeError('Native visibility is closed')`
   - reserved positions swept for vegetation / building / direct diffuse /
     both lazy-pair leaves
   - reuse slot: closed shared leaf reported after building's checks
   - interval boundary matrix (`start>stop`, `stop>pixels`, `patches>count`,
     negatives) -> identical range errors
   - longwave precedence incl. reserved-before-closed-building ordering
   - zero-patch demands, admission never raises nor fires checkpoints early
   Mechanism: per-channel interleaved preflight before the single kernel
   entry; hoisting all checks in front of one kernel would NOT reproduce the
   cross-channel ordering (the v5 fused path differs in this corner; the
   prepared path does not).
2. Per-channel outputs bitwise-equal on real payloads. `test_decode_equivalence.py`
   (52 tests): sizes 16/64/96/128 square, patches 1/5/153, all mode
   combinations (binary/ternary/raw/mixed/reserved-seeded), production BLOCKS
   incl. empty/odd/partial, mapped owners round-tripped through real files
   (synthetic in-memory builders are labeled in conftest), dense-source bit
   conservation, all diffuse admissions, buffer contract, longwave.
3. No hidden whole-payload copy. `test_no_hidden_copy.py`: descriptor
   tuple-identity with the accepted path's `_block_descriptor` cache;
   tracemalloc peaks with warm JIT (10 MB raw payload -> few KB peak); reuse
   diffuse adds no decoded-shadow copy; lazy pair = one exactly-sized uint32
   scratch; structural source guard (no np.empty/zeros/copy/tobytes in the
   kernels).
4. Full fallback bitwise-equal. `test_fallback.py`: every unadmitted demand
   (duck types, dense ndarrays, lazy base, unpacked lazy leaves/subclasses,
   non-codec objects, mixed) returns `None` from prepare and the drop-ins and
   reproduces the original outcome exactly — including the original path's
   own `AttributeError` for `decode_pixels`-less leaves.

## Admission domain (exact)

Base channels: direct packed only (`PackedVisibility` including exact
subclasses; `MappedVisibility` with a borrowable descriptor). Diffuse slot:
(a) the shared `LazyDiffVisibility` pair under `diff_from_shared_decoded`'s
strict exact-type identity rule (reuse, no extra copy), (b) independent lazy
pair with both leaves packed (one uint32 scratch), (c) direct packed channel.
Everything else, and any closed/descriptor-less owner, -> `None` -> original
path runs unchanged.

## Timing (contended development tier; recorded, NO claims)

See `timing_probe.json` (full-frame 128x128 scene, 153 patches, 128-row
blocks, best/mean of 30): original four-entry sequence 58.1/59.3 ms;
prepared one-entry 71.6/73.7 ms; prepared with caller buffers 74.1/78.4 ms;
prepare-only 0.005 ms; drop-in single block 0.54 ms. The prepared path
trades one extra preflight scan per stream (required for checkpoint-exact
cross-channel precedence) for three fewer native entries and no
decoded-shadow copy; on this tier the scan dominated. Numbers are
machine-contention-dependent; the integrator should re-measure if latency
matters for adoption.

## Integration

See `integration_recipe.md` — exact patch for
`patch_radiation._shortwave_visibility_blocks` (prepared-first prepend,
original body unchanged) and the `define_patch_characteristics` longwave
`_block` triple. `patch_radiation.py` itself was NOT modified (integrator-
owned); nothing outside the owned paths was written.

## Unresolved items / notes for the integrator

- `visibility_compiled._descriptor` (private) is imported by the new module;
  if the integrator renames or moves it, update the single import line.
- The borrowed-descriptor decline on close relies on the existing protocol
  that `MappedVisibility.close()` nulls `_block_descriptor`
  (visibility_native.py:117); belt-and-suspenders `closed` read included.
- Timing: prepared path measured slower on the dev tier (see above); adopt
  for exactness/memory-profile reasons only after re-measurement, or use
  caller buffers and per-demand reuse of the prepared handle (prepare is
  ~5 us) which the drop-in wrapper does not exploit.
- The v5 fused route (`SOLWEIG_LIGHT_FUSED_RAD=1`) remains inexact in the
  reserved-vs-later-channel-error corner by design; the prepared route is
  exact there and composes with the retained route only (tests pin the env
  to 0 per-test).
