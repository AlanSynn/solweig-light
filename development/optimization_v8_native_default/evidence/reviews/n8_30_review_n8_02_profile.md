# N8-30 review of N8-02 (profile evidence)

Verdict: **APPROVE-WITH-NOTES** — no blocking defects. Machine-readable record: `n8_30_review_n8_02_profile.json`.

## What was verified and how

Evidence-first review per VALIDATION_POLICY: read the policy/dossier/protocol, the full record, all three harness scripts (`tools/optimization_v8/n8_02_{instrument,child,run,analyze}.py`) and the src call path under review; recomputed the load-bearing numbers from `evidence/profile/raw/`; reran only cheap read-only checks (full fixture census, raster read-back). The instrumented campaign was NOT rerun (exclusive-owner evidence).

## Per-obligation results

1. **Record integrity — PASS.** `evidence_class: new_region_measurement` matches what was done. answers (a)-(d) consistent with `instrumented/`/`timing_paired/` (spot-checked values identical). `failures: []` matches console `failures: 0` and all 24 child returncodes 0 (recomputed). Ambient non-quiet = 6 recomputed from raw = recorded 6. No censored or mislabelled runs.

2. **Raw-data recomputation — PASS, every number matches.**
   - Island default b128: 0.063056/0.300185 = **0.2101** of Lcyl, /1.4124 = **0.0446** of wall; native b128 0.095549/0.327919 = **0.2914**. (claimed 21.0% / 4.5% / 29.1%)
   - Loader prep (433 calls): warm **130.96 us**, mean-incl-first **145.67 us** (claimed 131-146 us at b128); op chain 1:1 per call (mkdir 433, exists 867, stamp read_text/json_loads 433, kernel read_bytes 433 x 10194 B, sha256 433).
   - Paired ratios: b128 **1.00707**, b1024 **1.02103** (claimed 1.0071 / 1.021).
   - Counterfactual loader-fixed island: **0.038973 s** -> 0.039 s claimed; vs Numba 0.0631 -> **1.62x** (~1.6x claimed).

3. **Methodology — PASS.** Kernel-entry proof is genuine: the instrument replaces `entries[spec]` in `lw_native._LIBS[gang][1]` and production `primary()` re-resolves that dict entry per call (`src/solweig_light/backends/native/lw_native.py:230-231`), so the wrapper sits immediately around the function-pointer invocation; 432/96 f64 entries + 432/96 admitted prove interception. Default-arm zero rests on the real gate (`native_lw.py:130` `_ensure_loaded()` first, wrapped without loading in the default arm) plus the empty scratch cache after the production pool entry. Counterfactual and B7-60 extrapolation are labelled as derived/diagnostic. No dense-fallback shape used (labelled caveat). Stage totals are nested, not additively double-counted; in-Lcyl decode/classifier parts labelled `_estimated` and recompute exactly (0.4092 / 0.1143 / 0.2197).

4. **Fixture census — PASS (independently rerun).** Full unfiltered scan of all 390 TIFFs under `tests/reference`: **zero** 128/256-square (or min-side >= 128) fixtures; largest real scenes 32x35 (171) and 32x48 (99). Author's 297-file census reproduced exactly under their filter (92 output_folder artifacts + 1 corrupt WindCoeff TIFF excluded). Scene 32x35 confirmed by manifest + gdal read-back; 48 steps by counters; P=153 corroborated by `evidence/contract/n8_04_typed_lw_contract.json:193`.

5. **Bitwise parity — PASS, with presentation note.** Per-run digests exist in raw for both arms (every child `output_manifest`, 10 per-file sha256 + aggregate). Reviewer extracted all 24: the 22 runtile runs all share `7aa97c69a83d24d0` across arms/blocks/modes; pool default = pool native = `c059e7b94574a071`. The record's parity section itself holds booleans only (see N3).

## Notes (non-blocking), N1-N8

- **N1** `~2.3x faster` prose in answer (c) uses Numba-island vs C-entry-only means (145.96/62.44 = 2.34); the loader-fixed counterfactual implies ~1.6x. Overstates the loader-only fix; both numbers are present so it is reconstructable.
- **N2** `runtile_child_ru_maxrss_mb` is actually the ps tree sum again (analyzer reuses `rss_tree`), not ru_maxrss; immaterial (200.1 vs 200.2 MB single-process).
- **N3** `bitwise_output_parity` booleans are hard-coded in the analyzer; digests live only in raw. Embed the two digest values and derive the booleans.
- **N4** `first_use_native.run_wall_s` (1.416 s) excludes the 2.478 s build/load triggered by the instrument at install; counters are transparent but no combined workflow-first-use wall is surfaced, and the runner docstring calls it "workflow_first_use evidence".
- **N5** Census note wording ("no synthetic scenes") does not match the actual filter (`.solweig-light`/`output_folder` skips + 1 silently skipped corrupt TIFF); claim robust regardless (verified on the full corpus).
- **N6** Two orphaned pre-campaign smoke artifacts in `raw/` (`n8_02_smoke_*`, 15:30) referenced nowhere; they corroborate 0-default/432-native.
- **N7** "131-146 us" prep range is b128-only; b1024 measured 251.6 us warm (recorded, but not in the quoted range).
- **N8** Fixture provenance (N8-03 scope): scene `manifest.json` files_sha256 for met.txt is stale vs the on-disk met.txt the preflight hashed.

## Bottom line

Every quantitative claim in the terminal report was independently recomputed from raw and matched. The instrumentation honors the dossier's core requirement (counters immediately around the admitted C function-pointer invocation, worker-local, bounded record, overhead measured separately). The eight notes are labelling/presentation repairs, none of which change a measured value or the default-arm/native-arm conclusions.
