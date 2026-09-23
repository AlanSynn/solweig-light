# N8-30 review of N8-03 (protocol freeze)

Verdict: **APPROVE-WITH-NOTES** — no blocking defects. Machine-readable record: `n8_30_review_n8_03_protocol.json`.

## What was verified and how

Evidence-first review per VALIDATION_POLICY: read the three policies, the protocol JSON+md, both N8-03 tools, all five smoke records, both manifests and all four per-scene manifests. Programmatically diffed the gates and timing boundaries against the policy markdown; recomputed all 16 fixture hashes with `shasum`, the generator hash, the met source hash, and byte-compared the fixture metfile against the real-scene met. Cross-checked every frozen context figure against the approved `n8_02_profile.json` and its review notes. Smoke runs were NOT rerun (records + manifests suffice). No commits, no network.

## Per-obligation results

1. **Gate fidelity — PASS.** All 8 PROMOTION_POLICY gate bullets plus intro and closing are byte-identical in the protocol (programmatic diff). 1.10 geomean, dual 1.05 per-cell (vs A0 AND vs B1), 3% protected bound, 80% C-counter coverage with a non-double-counted work unit, first-use no-build, cold-guard 3%, censor rules — all present with exact numbers, nothing loosened. The protocol's exactness preconditions (N8-04 contract + green 112-test reference suite before any timing) are strictly stricter than the policy floor.

2. **Cell implementability — PASS with notes N-a/N-b.** P1/P2/P5/P6 are executable today with the shipped smoke tool (verified flags); T1 ships a complete command whose `n8_02_child.py` flags all exist. Every cell pins scene, env, runtime options (verified against `runtime.py` defaults), entry point, expected output set (10 named GeoTIFFs + checkpoint), timesteps and admission. P3/P4 miss no pinned variable but no shipped driver accepts their flags yet; P3's `run_utci_tiles / packed run_tile` must be pinned to ONE boundary before the first timed pair.

3. **Fixture identity — PASS.** The manifest scheme is specified (per-file sha256 for every produced input). All 16 hashes recomputed and matching (all four scenes, not a spot check); generator sha256 `c272575d…` matches; the met file is byte-identical to header + first 24 records of the real-scene `met.txt` (source hash `37132c88…` verified) with provenance recorded in manifest, protocol and builder docstring. Reviewer tree digests over the sorted path:hash list for future re-verification: `128_dense = 1eba11e5c29f…`, `256_veg = 9f7c4aba50d4…`.

4. **Control correctness — PASS.** B1/C1 share the direct-AoSoA producer, layout and region/pipeline boundary; only the backend differs. A0 is the untouched env-unset default at frozen HEAD; auto is env-unset packaged candidate, N8-43+ only; C0 is explicitly diagnostic-only; M0 pin `14e88876…` verified = main HEAD with no performance claim; B7-60/B7-31 marked historical. The verbatim dual 1.05 gate prevents crediting B1's layout gain to C.

5. **Measured context — PASS.** Every figure matches the approved n8_02 record: island 21.0%/4.5%/29.1%; prep 130.96 µs warm B=128 **and** 251.6 µs B=1024 (answering review note N7); adapter 220.2 µs; C entry 61.9 µs; Numba island ~146 µs; decode 40.9/46.7/41.5% labelled per-call-mean estimates; end-to-end 1.0071 (5 pairs) / 1.021 (3 pairs); instrumentation delta −1.75%..+2.69%, 157 ns/call. Review note N1 respected: no speedup expectation is stated, the 2.3x figure is absent (grep-verified), and the lone ~2.4x is the prep-vs-C-kernel cost statement from n8_02's own verdict.

6. **Honest labels — PASS.** SYNTHETIC-DEVELOPMENT labels on all four scenes with the cannot-represent-actual-corpus rule quoted; target_campaign placeholder records corpus absence + not-actual-target scale guard; the ambient admission failure is preserved as its own record, labelled environment-blocked, and drives the P1/P2 quiet-host requirement; the v5 metfile open dependency is recorded with its substitution.

7. **Consistency — PASS.** JSON parses; all 16 manifest hashes match disk; smoke-record digests, stage splits, TIFF counts, env and admission fields match the protocol's smoke_verification exactly (7e276889… / 235b3293… / e97ddaa7… / 2c87a101…); the output-digest scheme is defined in the smoke tool; the "112 tests collected" claim reproduced exactly.

## Notes (non-blocking), N-a–N-g

- **N-a** P3/P4: fully pinned config, but the shipped smoke tool only accepts `--memory-budget-gib`; a comparison-harness driver must exist before the first timed pair. No parameter would need inventing.
- **N-b** P3 entry's `run_utci_tiles / packed run_tile` is an either/or; pin ONE timed boundary for both arms before the first P3/P4 pair.
- **N-c** Smoke records identify scenes by path+label, not input hash; timed-run records should embed the input hash set (or tree digest).
- **N-d** P1's "~2.22 GiB" and the ambient note's "~4.5 GiB available" are decimal-GB readings of byte counts (2.06 / 4.12 GiB true); conservative direction, cosmetic.
- **N-e** T1's `manifest.json` pin embeds a stale internal met.txt hash (n8_02 review note N8); the protocol pins the verified on-disk hash, which is the binding value.
- **N-f** Require the n8_02-style per-run output manifest (path+size+sha256) in every timed record so pairwise bitwise identity is provable from raw.
- **N-g** `SOLWEIG_LIGHT_LW_BACKEND=numba` is not a recognized value at HEAD (accepted: native/ispc, `cylinder_longwave.py:200`), so PR1 is identity-with-A0 today — correct protected-cell semantics, but the current trivial pass is not evidence.

## Bottom line

The freeze is faithful: gates verbatim, cells pinned, fixtures hash-verified end to end, controls correctly separated, measured context matching the approved n8_02 record without the flagged 2.3x figure, and every shortcut or absence labelled rather than hidden. The seven notes are repairs owned by the comparison/campaign tasks before their first timed runs; none changes a frozen number or a gate.
