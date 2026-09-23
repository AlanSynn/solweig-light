# N8-30 review of N8-20 (packaging) — APPROVE-WITH-NOTES

Reviewer: n8-30 review service (independent; did not author N8-20).
Target: `experiments/optimization_v8/packaging/` + `tests/optimization_v8/packaging/` @ `16cdc56c` (perf/native-optimization).
Full record: `n8_30_review_n8_20_packaging.json` (this directory).

## Verdict

**APPROVE-WITH-NOTES.** No blocking defects. Every dossier MUST is present and honest; every claim I could recompute, I recomputed, and all held.

## Reviewer-recomputed facts (all independent of the author's code path)

| Item | Value |
|---|---|
| staged dylib sha256 | `eb1071fc…2582b46a`, 34280 B — byte-identical to `~/.cache/solweig-light/native/liblw_native_g8.dylib` |
| staged asm sha256 | `bbdfdc95…afc0e8` — identical to B7 cache `build/lw_primary_g8.s`; equals `fma_audit.asm_sha256` |
| header sha256 | `7d2b2ed4…ab2d5f` — matches manifest |
| kernel sha256 | `52652a59…61663c` — matches B7 `build_stamp.json`; byte-identical to the B7 build input (diff-verified) |
| generation name | `lw-g8-42aeba6a50dc5937` — re-derived by me from manifest content (canonical-JSON sha256); matches dir and manifest |
| validate / verify | `[]` violations / PASS; my own Mach-O walk on the real dylib: clean |
| otool facts | LC_ID_DYLIB = bare basename; sole dep `/usr/lib/libSystem.B.dylib`; minos 26.0; arm64 — all match manifest |
| flags | `-O2 --opt=disable-fma --math-lib=default --pic` + `-arch arm64 -dynamiclib`, target `neon-i32x8` — portable, no `-march=native` equivalent |
| FMA on shipped image | my `otool -tV` disassembly of the **linked dylib**: **0 hits** in 7412 lines (same for the B7 cache dylib) |
| tests | normal: **44 passed** (4.25s); ISPC stripped (`env -i PATH=/usr/bin:/bin`): **41 passed + 3 `[ispc-unavailable]` skips** (0.21s) |
| git | dylib ignored via user-global `~/.config/git/ignore:50 (*.dylib)`; zero tracked-file modifications; author scope clean |

## Per-obligation results

1. **Dossier fidelity — PASS.** Single distribution; platform-specific wheel rules enforced (no `any`/purelib/abi3 for native wheels); arg-list subprocesses with allow-listed env (no `/bin/zsh`, no `/opt/homebrew` outside docstrings asserting their absence, no curl/network); manifest v1 carries every dossier-listed field; content-derived immutable names + single-rename publish + exit-7 republish refusal; two build modes with native-release failing loudly (3/4/5/6/7) and source mode never touching ISPC; loader contract (BUILD_DESIGN §8) states path containment, no runtime compile/download/HOME writes, absent=quiet vs corrupt=recorded+loud; license obligations mentioned (source globs kept "for source transparency and license obligations"; pyproject already ships kernel source + SLEEF license); CI boundary honest (wheel assembly and local-readiness tests correctly deferred to N8-41; no upload authorized).
2. **Manifest/artifact — PASS.** All hashes, the byte-parity claim, the generation-name derivation, otool facts, and the portable-baseline rule verified as above.
3. **FMA gate — PASS.** Audit targets the shipped, hash-bound `.s`; `verify_generation` re-checks both the binding hash and re-runs the audit; immutability blocks silent replacement. The `.s` is a deterministic re-emission, not a disassembly of the linked image — I closed that loop directly on the shipped dylib (0 hits). See N2.
4. **Test teeth — PASS.** Real injected defects with asserted refusal: malformed sha256 fixtures, 11 manifest mutations, truncated dylib with stale hash, truncated dylib with **matching** hash (Mach-O walk catches it), forged generation name, mid-publish explosion (staging stays empty), path escape, immutability exit 7. Skips are genuinely environment-conditional (proven by the stripped-env run). No fake passes found. One gap: exit-5 path tested at function level only (N3).
5. **Honest labels + discipline — PASS.** Git exclusion verified; SOURCE_FALLBACK.md says "explicitly NOT native-qualified" in bold; no default-enable (zero tracked-file diffs); ownership confined to the two owned directories. The 3-compile/budget-overrun disclosure is corroborated by my runs (full suite = exactly 2 in-suite compiles + 1 stage build) but recorded only in the handoff, not in a deliverable file (N1).
6. **Suite run — PASS.** 44 pass; 41+3 labelled skips with ISPC hidden.

## Notes (non-blocking)

- **N1** — compile-budget-overrun disclosure lives only in the review-request handoff; add one sentence to BUILD_DESIGN §9 for durability.
- **N2** — FMA gate audits re-emitted asm; recommend `verify_generation`/N8-21/N8-41 additionally scan `otool -tV` of the final artifact (reviewer already confirmed 0 hits today).
- **N3** — no end-to-end contracting-kernel exit-5 test (fixture not deterministically constructible; acceptable).
- **N4** — dylib exclusion is user-global, not repo-level; N8-41 must add a repo `.gitignore` rule so the exclusion survives on other machines.
