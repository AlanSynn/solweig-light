# C6-81 review: prepared visibility decode declined by default (+ C6-80 evidence, C6-81 selection)

- Reviewer: independent GLM review; Opus unavailable.
- Range: `2ce117e0..5928ead4` (3 commits), work tree
  `/Users/alansynn/Workspace/solweig-light-claude-v5`, branch
  `perf/claude-glm53-cpu-v5`, HEAD `5928ead4` at review time.
- Review date: 2026-09-21.
- Method: code inspection + test runs only. No benchmark was re-executed; no
  timing claim in the range needed re-measurement. Where numbers are quoted
  below as "recomputed", they are arithmetic recomputations from the
  committed evidence JSONs, not new measurements.

## Verdict

**APPROVE.** The decline gate is a total, side-effect-free short-circuit that
restores the originally-accepted decode route as the default; the opt-in path
is byte-identical to the reviewed C6-50 behavior; both dispatch sites fall
back completely; the tests are correctly armed/pinned; the evidence, selection
record and ledger are internally consistent and honestly labeled dev-tier.
Findings are LOW/INFO only; none blocks.

## What was verified, and how

### 1. Exactness of the decline (commit 46450c75)

- The gate is the first executable statement of `prepare_channels`
  (`src/solweig_light/geometry/visibility_prepared.py:331-332`):
  `if not _prepared_enabled(): return None`. It precedes `base = []`, the
  isinstance admission predicates, `_build_slot` (which acquires owner locks),
  `_diffuse_slot` and owner aggregation. With the env unset the function
  returns `None` unconditionally: no lock acquisition, no descriptor fetch,
  no JIT dispatch, no exception path. `os.environ.get` cannot raise for any
  environment state and the `== '1'` comparison is total, so declined
  admission is side-effect-free for every input, including adversarial ones.
- `decode_shortwave_block` / `decode_longwave_block` obtain admission solely
  through `prepare_channels` (module read in full); there is no second
  admission path. `SOLWEIG_LIGHT_PREPARED_VIS` occurs nowhere else in `src/`
  (grep over src/ and tests/: only the gate, the conftest fixture and the new
  test).
- Both dispatch sites fall back completely on `None`:
  - `_shortwave_visibility_blocks` (`src/solweig_light/radiation/patch_radiation.py:118`):
    prepared `None` -> `sh/vs/vb` via `_block`, then
    `diff_from_shared_decoded`, else `_block(diffuse)` — the original
    observable sequence.
  - longwave inside `define_patch_characteristics` (`patch_radiation.py:908`):
    `decode_longwave_block(...)` `None` -> triple `_block` comprehension, then
    the unchanged kernel call.
- The fallback branches are byte-identical to pre-range: `git diff
  2ce117e0~1..5928ead4 -- src/` touches only
  `visibility_prepared.py` (19 insertions, 1 deletion; the deletion is a
  docstring-line rewrap). `patch_radiation.py` is untouched in the range.
  Therefore, with the env unset, dispatch executes the accepted original
  route end-to-end for every input — identical numerical output, identical
  error types/messages/checkpoint order, identical observable ordering.
  This also restores the pre-C6-50 default that the accepted L2/differential
  evidence was built on; the prepared route's own exactness evidence (C6-50)
  remains attached to the opt-in path.
- Opt-in path unchanged vs C6-50: function-level diff of `prepare_channels`
  between `46450c75^` and `46450c75` shows exactly two changes — a docstring
  sentence and the two-line gate. With `SOLWEIG_LIGHT_PREPARED_VIS=1`,
  `_prepared_enabled()` is true, the gate no-ops, and every admission
  predicate is byte-identical to the previously reviewed C6-50 code. The
  gate pattern mirrors the existing `_fused_enabled`
  (`SOLWEIG_LIGHT_FUSED_RAD == '1'`) precedent verbatim.
- Env read cost/placement: `_prepared_enabled` is pure Python
  (`os.environ.get`, a dict lookup), called once at the top of
  `prepare_channels`, i.e. once per block in the dispatch hot loops —
  nanoseconds against ~0.5–4 ms block decodes (drop-in single-block timings
  in the committed probe), before any numba work, lock, or I/O. No concern.

### 2. Conftest autouse fixture and the new default-off test

- `tests/optimization_v6/decoder/conftest.py:79-96`: autouse, directory-scoped
  to the decoder family. Marker check
  (`request.node.get_closest_marker('prepared_default_off')`) yields without
  arming; every other test is armed via a dedicated `pytest.MonkeyPatch`
  with `setenv('SOLWEIG_LIGHT_PREPARED_VIS','1')` and `undo()` in `finally`
  — no leakage on setup or teardown failure, and the fixture is invisible
  outside `tests/optimization_v6/decoder/` (confirmed by the combined
  9-family run passing).
- `tests/optimization_v6/decoder/test_prepared_default_off.py`: the
  marker-decorated test additionally `delenv`s with `raising=False`, so it
  exercises env-absent behavior even if the ambient environment had the
  variable set. It asserts `prepare_channels(...) is None` (both arities),
  `decode_shortwave_block(...) is None`, `decode_longwave_block(...) is
  None`. The opt-in test sets `1` explicitly and cross-checks the prepared
  outputs bitwise against `decode_block` per channel.
- The module-level by-file-path conftest import in the new test file
  (avoiding `import conftest` shadowing in combined collection) registers
  under a unique `sys.modules` name and only pulls pure helpers
  (`packed`, `bitwise`); re-executing the conftest module re-runs an
  idempotent `setdefault` — safe.
- Live evidence that the fixture is load-bearing: my shell had no
  `SOLWEIG_LIGHT_PREPARED_VIS` set, so the 96 armed decoder tests passed
  only through the fixture, while the marked default-off test passed without
  it.

### 3. Inert-pin extension

- Independent grep: `runtime_memory` importers in `src/solweig_light` are
  exactly `api.py:215`, `runtime.py:680`, `runtime_phases.py:89` — matching
  the extended pin in `tests/optimization_v6/memory/test_phase_memory_admission.py`
  (which scans `rglob('*.py')`, so `src/solweig_light.egg-info/SOURCES.txt`
  is excluded by both the extension filter and the `.py` filter).
- `runtime_phases.py` landed at `3f3e8b8d` ("Land C6-40 ... APPROVE-WITH-
  CONDITIONS, conditions closed") — the sanctioned C6-40 adapter that took
  over the deferred W2 geometry-phase admission, exactly as the extended pin
  text states.
- No other new src importer in the range: the range's only src change is
  `visibility_prepared.py`, which does not import `runtime_memory`.

### 4. Test runs (single process, worktree root, project venv)

Both runs from `/Users/alansynn/Workspace/solweig-light-claude-v5`, with
`PYTHONPATH=src NUMBA_NUM_THREADS=2` and
`/Users/alansynn/Workspace/solweig-light/.venv-light/bin/python`:

- `tests/optimization_v6/decoder/`: **97 passed** (matches expectation),
  1 warning (see finding F1), 4.09 s.
- Combined set gvf_prepare gvf_postprocess decoder cylinder_lw cylinder_sw
  lside geometry_recipe memory phases: **560 passed** (matches expectation),
  51.67 s. Warnings are the pre-existing numba/lside RuntimeWarning class.
- Restoration: `git checkout -- optimization_v6_continue/evidence/recipe
  optimization_v6_continue/evidence/census` applied; `git status` shows no
  tracked modifications and HEAD unchanged at `5928ead4`. Untracked
  pid-named raw run records under those dirs (a class that already existed
  before this review) were left in place; with other agents active in the
  session they cannot be attributed safely and deletion was not authorized.

### 5. C6-80 evidence internal consistency (commit 2ce117e0, docs+data)

Recomputed from the committed artifacts, not re-measured:

- `portfolio_v1.json` has exactly 64 slot records; 0 nonzero return codes,
  0 timeouts — matches "64 lease runs, 0 failures".
- Every cell of the README portfolio table reproduces exactly from
  `stages_s.total_measured` (e.g. t128_S1 integrated cold 20.55/22.15 med
  21.35; base 23.45/22.16 med 22.80; t256_T2 base cold 50.15/47.52 med
  48.83; all 12 rows and both warm_geom pairs 17.66/17.84, 36.98/38.48).
- Headline percentages recompute: S1 cold −6.4%/−9.8%; T2 cold
  −6.1%/−16.2%; P2 cold −10.9% at t256; warm wash +1.2%/−0.4% (S1),
  +2.9%/−3.0% (T2). All match the README to the stated precision.
- `simulation_tiff_digest`: exactly one distinct digest per shape across all
  64 slots (`fcffb12a…` t128, `6088d728…` t256) — matches the bitwise-
  identical-outputs claim; `simulation_tiff_count` 20 per run.
- Cache census claim (base 4 vs integrated 2) holds for every slot.
- Component claims verify: t256 cold integrated svf 10.42/6.12 (production
  split ⇒ ~4.3 publication); warm fast-hit svf 0.118–0.141 both trees;
  phase walls t128 cold 2.51–2.95 s, t256 cold 4.71–5.55 s, warm P2
  re-fire 0.86–1.10 s (the recorded caveat); base serial svf cold
  2.80–2.97 (t128; the README's "2.88–2.97" quotes the two-value median
  from its own stage table — see F4) and 10.20–10.33 (t256);
  `phase_calls=1` at integrated P2 only, 0 at base P2 — matching the
  activation-gate description.
- The claimed phase gate matches the code: `src/solweig_light/api.py:139`
  `if len(pending) > 1 and runtime.workers > 1 and runtime.cache_enabled:`.
- Decoder probe: all four `decoder_probe/*.json` files match the quoted
  best/mean pairs (58.32/71.95, 55.38/66.82, 236.70/288.83, 222.69/268.71
  ms), `native_threads: 2`, prepare-only ~5 µs, caller-buffers no better.
  Exact best-of-30 regression deltas: +20.7%, +20.7%, +22.0%, +23.4% —
  the "+21–24%" headline is integer-rounded endpoints (see F2).
  "Reproduces the recorded 58.1 vs 71.6" matches the C6-50 review's
  recorded 58.15/71.59 (`REVIEW_C650_decoder.md`), and that review did
  advise integrator re-measurement — which is what this probe is.
- Scene provenance: recomputed sha256 of the Building_DSM tiles matches
  `scene_manifests.json` entries; tiles distinct within each scene.
- Honesty labels: dev-tier / host-NOT-quiet (loadavg median 11.2, per-run
  `ps` snapshots) / no statistical claims / no actual-target claims are
  stated in the README, the commit messages and the selection record. The
  README records known imperfections (cold r0 child-record deletion, warm-P2
  validate_existing semantics, parent-side route telemetry not observable).
  The README also honestly notes the decoder cost sits inside the
  integrated stage-C numbers (the portfolio ran at 76bcd288, before the
  gate), and that declining "recovers margin" is directional, not measured.

### 6. C6-81 selection record (commit 5928ead4)

- Spot-checked numbers against the underlying artifacts: decoder +21–24%
  (probe, above), S1 −6.4/−9.8, T2 −6.1/−16.2, P2 −10.9 t256, warm wash,
  stage B ≈ 4.3 of 10.4 s / warm ≈ 0.13 s, simulation dominance 14–43 s of
  19–54 s (stage medians), phase walls — all reproduce as above.
- C6-90/91/92/93/94 each declined with a measured-basis sentence, not a
  catalog prior; C6-94's deferral names the honest gap (no in-sim stage
  attribution) and a concrete future trigger.
- "What this selection does NOT claim" is explicit: no statistical/release
  claim, no actual-target claim, all numbers dev-tier. Nothing in the record
  claims more.
- Phase-route disposition ("gate stays as landed; no shape-threshold tuning
  on this host") matches the code gate and the measured net-negative-t128 /
  pays-t256 split; caveat recorded.

### 7. Ledger consistency

`LEDGER_C6.md` diff in `5928ead4`: C6-80 DONE (evidence 2ce117e0), C6-81
DONE (selection + decline), C6-90..94 NOT SELECTED (pointer to the selection
record), C6-99 reduced to branch-surface confirmation, C6-101 scope marked
unverified until the 24-tile dataset exists, and the C6-70 GDAL_CACHEMAX
sign-off item moved OPEN -> RESOLVED with the README pointer. All four
changes match the selection record and README; standing facts (routing, Opus
unavailable) untouched.

## Findings

- **F1 (LOW, non-blocking)** — `pytest.mark.prepared_default_off` is not
  registered in pytest config (`pyproject.toml [tool.pytest.ini_options]`
  has no `markers` list). Confirmed live: the decoder run emits
  `PytestUnknownMarkWarning`. Functionally harmless — `get_closest_marker`
  resolves unknown marks and no `filterwarnings=error` is configured — but
  every decoder run carries the warning. Register the marker (pyproject or a
  `pytest_configure` hook) whenever these files are next touched; no
  dedicated commit warranted.
- **F2 (INFO)** — The "+21–24%" headline rounds the exact best-of-30
  endpoints (+20.7% … +23.4%; +23.5% from the README's own display-rounded
  values) outward to integer percent. Direction and decision are unaffected
  and the rounding is symmetric, but the precise range is worth quoting if
  the number is ever reused.
- **F3 (INFO)** — The env is read per `prepare_channels` call, so toggling
  `SOLWEIG_LIGHT_PREPARED_VIS` mid-process could flip routes between blocks.
  Numerically irrelevant (both routes exact; the fallback is the original
  path), and identical to the `SOLWEIG_LIGHT_FUSED_RAD` convention.
- **F4 (INFO)** — README verdict 2 quotes the t128_P2 base serial svf stage
  as "2.88–2.97 s" where the two cold reps are 2.80/2.97; 2.88 is the
  two-value median shown in the README's own stage-median table, so the text
  is internally consistent but a reader could mistake 2.88 for a rep value.
- **F5 (INFO)** — Scope note for traceability: the C6-80 portfolio measured
  the integrated tree at 76bcd288 with the prepared route still armed; the
  later gate commit changes the default route of that tree. The README
  discloses this (decoder cost inside integrated stage-C) and the selection
  uses the numbers directionally only, so no evidence is invalidated; but
  any future re-run of the integrated tree at default env will not reproduce
  the integrated stage-C numbers cell-for-cell.

## Test counts measured by this review

- `tests/optimization_v6/decoder/`: **97 passed, 0 failed** (97 collected).
- Combined 9-family set (gvf_prepare, gvf_postprocess, decoder, cylinder_lw,
  cylinder_sw, lside, geometry_recipe, memory, phases): **560 passed,
  0 failed**.
