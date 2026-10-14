# Wave-1 independent review notes (S10 semantic systems)

Reviewer: glm-5.3-flash independent subagent. Date: 2026-10-14.
Base `b3e5ca59`, HEAD `2c7324d9`. Machine-readable verdicts: `wave1_reviews.json`
in this directory. I authored none of the reviewed changes; everything below
was verified by execution on this host unless explicitly marked otherwise.

## Verdicts

| task | commits | verdict |
|---|---|---|
| T01 | 33ab050f, 65097719 | approved_with_notes |
| G01+G02 | 65097719, 612fbb13 | approved_with_notes |
| R03 | 1a3cb8e2, 04faa6cf, 313f6a15 | approved |
| S03b | 22daa0b0 | approved |
| S10-14 | 2c7324d9 | approved_with_notes |

No blockers. Three recurring minor notes: (1) E2E route engagement is only
pinned for R03; (2) `_uniform_tgwall`/`_admits` admit size-one arrays of any
dtype where docs say float; (3) the "C6-30 suite 217 pass" count is not
reconstructible.

## What I executed

- `pytest tests/optimization_s10 -q` → **58 passed** (7.5 s), in suite order.
- `pytest tests/differential/test_pipeline_reference.py -k landcover -q` →
  **2 passed**; full file → 1 F / 8 P, the failure being the documented
  pre-existing `[raw-True]` cell.
- `pytest tests/unit -q` → **10 F / 453 P**, exactly the documented
  pre-existing set (p7 harness, portable_profile; threads=10 numba-limit etc.).
- `pytest tests/optimization_v6/gvf_prepare tests/optimization_v5/gvf -q` →
  **160 passed** (the locatable C5-22/C6-30 lineage bitwise differentials).
- Adversarial scripts under `/tmp/s10review/` (scratch, outside the repo):
  - `exp_partition.py` — python-float vs ndarray-wrapper partition,
    `_uniform_tgwall` admission set, decline error-parity.
  - `exp_anilum.py` — aniLum kernel vs the ENGINE's own retained loop
    (`engine._zeros`/`engine._operate`), declines, kill switch.
  - `exp_s03b.py` — live host memory-view numbers, census algebra.
  - `exp_gvf_env.py` — GVF kill switch through the REAL env var.
- Census-trap probes with kill switches set in the environment (see below).
- Baseline checks in `git archive` copies under `/tmp` (no repo modification):
  `tests/optimization_v6/cylinder_lw` and
  `test_compiled_patch_parallel_diagnostics` at `b3e5ca59`, plus a fresh/warm
  double-run at HEAD.

## Per-patch reasoning

### T01 (33ab050f)

The guard flip is exactly scoped: reading both primaries, the only semantic
change is `Tgwall` moved from "must be 0-d" to "must be singleton"
(`_uniform_tgwall`); the other four scalar keys and `_supported` clauses are
untouched, and every reference-return path gained a counter increment, so a
route flip cannot happen without moving the counters. The U extraction keeps
the shaped arithmetic and lifts the completed value with no arithmetic after
(`reshape(-1)[0]`); I confirmed U-route output is bitwise-equal to the S route
on the shared fixture bundle, and that size-2/empty arrays are declined with
byte-identical original `ValueError` messages. The python-float admission set
matches the docs for float inputs.

L2 benchmark audited for internal consistency only (per instruction; raw
records are on Dropbox): the five pair ratios recompute to geomean 1.6593,
min/max and medians match the quoted figures, and the removed time
(3.26−1.97 = 1.29 s) matches the census attribution (~1.31 s). The A side
(`4e76183a`) is genuinely source-identical to main under `src/` (diff shows
only docs and a test-harness import path). Numbers: consistent. Independence:
not re-measured — said explicitly in the JSON.

Findings: (a) E2E engagement not pinned by a standing test (see "census trap"
below); (b) `_uniform_tgwall` admits size-one arrays of any dtype (int64
included) — docs and the G02 commit text say float; (c) theoretical guard-order
asymmetry for doubly-malformed inputs (Tgwall is asarray'd first now); every
tested case shows original error parity.

### G01+G02 (612fbb13)

The H=1 dispatch delegates through `prepared_gvf_step(..., parallel=False,
delegate=serial)`; I verified the delegate's positional tuple matches the
removed direct `serial(...)` call exactly and that it intentionally drops the
`parallel`/`block_rows` kwargs the fused baseline does not accept. Decline
classes (f16/int Tg, multi-element f64 Tgwall) all assert `serial==1` and
bitwise parity with `engine.gvf_2018a_numpy`. The bitwise prepared≡original
claim on the f64-Tg production profile is covered by standing tests with
uint32/uint64 views including caller-visible `Tg`, over water × buildings
variants.

Oracle provenance is genuine: `engine.gvf_2018a_numpy` is bound at module line
1758, before the dispatch `def` at 1762 rebinds the name, and the same alias
exists on main (b3e5ca59:1747) — it is the pre-optimization body, not a
campaign artifact.

I re-verified the kill switch through the **real environment variable** (the
standing test mocks `prepared_enabled()` instead): with
`SOLWEIG_LIGHT_GVF_PREPARE=0` at one thread the call delegates (serial=1) and
is bitwise vs the original including `Tg` state.

Findings: (a) the "C6-30 suite 217 pass" figure — the locatable lineage suites
are 78 (v6/gvf_prepare) + 82 (v5/gvf) = 160 items, all passing; no selection I
tried yields 217 (78+82+39 = 198 with v6/cylinder_lw). Substantive claim
supported, count unverifiable — the doc should name the selection. (b) Same
size-one dtype nit as T01 in `_admits`. (c) Same E2E-engagement note as T01.

### R03 (1a3cb8e2, 04faa6cf, 313f6a15)

Strongest of the five. I re-derived the bitwise claim against the engine's own
operands rather than trusting the test's replica loop: on packed leaves
carrying raw NaN/−0.0/+Inf payloads, `anilum_packed` output is bitwise-equal
(uint32 views) to the retained loop written with `engine._zeros` /
`engine._operate`; parallel ≡ serial; all five decline classes return `None`;
ternary decline preserves the original Python-indexer `IndexError`. The
no-preflight design is sound because the only reserved-code carrier (ternary
mode) is declined wholesale, and modes {binary, raw} cannot encode a reserved
code — the fused route needs `_preflight_flat` because it admits lazy leaves
independently; this one does not.

The E2E engagement test is genuinely load-bearing, which I demonstrated by
execution: with `SOLWEIG_LIGHT_ANILUM_PACKED=0` the landcover goldens **still
pass** while the engagement test **fails** (0 ≠ 14). That is the census trap
made concrete, and this is the only wave-1 route with a standing E2E pin.

The hygiene commit (313f6a15) is honest bookkeeping: the bare
`default_gdal_cache_bytes` assignment in 1a3cb8e2's E2E test really would have
leaked into the s03b tests (they run later in suite order), and the fix routes
it through monkeypatch; 58/58 in suite order at HEAD confirms no residual.
The set-1 jsonl overwrite disclosure matches the fixed-afterward narrative.

Nit: the anilum kill switch disables only on exact `'0'` while the GVF switch
also accepts `'false'/'False'` — both match their docs; cosmetic.

### S03b (22daa0b0)

The view change is a strict contraction: `min(physical, finite limit) ≤
physical`, so the 5% charge can never increase and no previously-admitting
configuration can newly refuse — hosts without a finite cgroup limit keep the
physical view bit-identically (verified by reading
`_container_memory_limit_bytes`: it skips `"max"` and ≥ 2^60 sentinels). The
single-source claim holds by construction: `_child_environment` imports
`default_gdal_cache_bytes` at call time for the applied `GDAL_CACHEMAX`
(runtime.py:680 area) and `_resolved_gdal_cache` calls the same function for
the charge. Live numbers on this host reconcile with the evidence doc
(376.05 GiB physical, 64.0 GiB limit = "68.7 GB", headroom 5.31 GiB, new
default 3.200 GiB vs old 18.802 GiB, budget 2.653 GiB, census algebra exact).
The remaining refusal on this host is headroom-driven (budget uses
limit−usage; charge uses the limit) and the doc says so explicitly.

Could not verify inside a real 6 GB Slurm step; the monkeypatched census
probes are the best available evidence here, and they pin direction (admits
with the limit, refuses without it), not just outcome.

### S10-14 (2c7324d9)

Oracle provenance checked fixture by fixture: expectations come from
`patch_radiation._reference` (engine serial lineage) or
`engine.gvf_2018a_numpy` (pre-optimization body — verified on main), or stated
invariance identities (wrapper bit-equality, alias-visibility, signbit masks).
No candidate-generated expectations, no numerical mocks. The GVF alias
fixture correctly reproduces the aliased binding on the oracle side, avoiding
the snapshot-copies-away-alias trap it documents. The manifest is
registry-generated and drift-pinned (test passes).

The python-float partition claim: **sound, with one nuance**. I measured it
independently over three seeds × both dtypes: with f64 wrappers the python
float is 1–2 ulp from the ndarray set on exactly 5/6 fields (Lsouth 0 ulp);
with **f32** wrappers it is bit-identical (0 ulp) — the coefficient arithmetic
stays f32 when the wrapper is f32 (via `engine._operands` semantics), so the
partition is dtype-conditional, not universal as the doc implies. The error is
in the conservative direction (it under-claims bit-equality), so no contract
risk; record the condition.

Minor: `adversarial.py` cites `patch_radiation._is_singleton`, which does not
exist (the helper is `_uniform_tgwall`).

## Things I chased that turned out clean (worth recording)

- **139 vs 138 differential failures.** Current
  `test_patch_radiation.py + test_radiation_reference.py` shows 139 F / 546 P
  vs the documented 138 F / 547 P. Classification: 90 threads=10 numba-limit
  cells + 48 collector-drift cells = the documented 138; the extra is
  `test_compiled_patch_parallel_diagnostics`, which fails inside numba's own
  `parallel_diagnostics` (`parfor_diagnostics` metadata absent). Proven
  cache-warmth-dependent, not wave-1-caused: it **passes** on fresh `git
  archive` trees of BOTH main and HEAD and **fails** on the second (warm-cache)
  run of the HEAD tree. Numba 0.67 + `cache=True` tooling artifact.
- **`test_kernel_primary_matches_full_route_invariance` (v6/cylinder_lw)
  failing.** Both sides are all-NaN with differing NaN payloads on column 7.
  Reproduces **identically at main** (baseline archive run: 1 F / 38 P) on
  kernels and test that are byte-identical to HEAD — pre-existing
  environmental, part of the documented v5–v8 parity failure mass.
- **Hidden scope.** `git diff b3e5ca59..HEAD -- src/` contains exactly the
  four areas the wave claims (T01 guards/counters/extraction, R03
  kernel+dispatch, G01 dispatch, G02 `_admits`, S03b view); no debug prints,
  no dead code beyond the intended diagnostic `ROUTE_COUNTS` (read by tests),
  no weakening of existing checks. The one `tests/unit` change is an import
  path fix for restructure-era tooling (a405fc28, pre-wave-1 infrastructure).
- **Test pollution.** The one real leak (R03 E2E GDAL override) was introduced
  in 1a3cb8e2 and fixed in 313f6a15; suite-order run at HEAD is clean.
  `runtime_options` restores via ContextVar token; kill-switch tests use
  monkeypatch.

## Unselected tasks

Agreed with all seven deferrals (S07/S09, kernel-internal, T03, R01, T06, T02,
H*) — reasoning per row in `wave1_reviews.json`. One bookkeeping suggestion:
T02's row still says "fold into T01", but T01 shipped without it, so the row
should say "dropped" to avoid implying pending work.

## Could not verify (summary)

- Dropbox raw archives (probe/benchmark tarballs and sha256s) — not reachable
  from this session.
- L2 timings (1.659 / 1.738 / ~1.05) — internal-consistency audit only; busy
  shared host, per instruction. This is the one place where a cheap independent
  rerun (quiet window or second host) would add real value before merge.
- Census stage timings (45% gvf, 11.1% aniLum, 1.31 s) — internally consistent
  with each other and with the L2 deltas (2142 = 14×153; 85.3/0.75 ≈ 11%;
  3.26−1.97 = 1.29 ≈ 1.31), not independently re-measured.
- The "C6-30 suite 217 pass" selection (see G01+G02 finding).
- The production guard-probe figure "14/14 rejected, sole failing input
  Tg:float64" — corroborated by mechanism and tests, not re-captured.

Housekeeping: `solweig-s10-semantic-system-claude-packet.zip` sits untracked in
the repo root (pre-existing; not wave-1 scope).
