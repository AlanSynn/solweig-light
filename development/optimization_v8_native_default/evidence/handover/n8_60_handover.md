# N8-60 Handover — native-default packet, retained (non-promoted) state

- Author: **n8-rev-n8-13**, yaml role `independent_reviewer` (role flip: reviewer authors, integrator verifies and commits)
- Branch: `perf/native-optimization` @ **5ed9699e** (N8-50 freeze), worktree `/Users/alansynn/Workspace/solweig-v8-native`
- JSON twin: `n8_60_handover.json` (schema house style; `recorded_utc: SET_AT_COMMIT`)
- Scope guard honored: written only under `evidence/handover/`; no src changes, no commits; commits/records cited verbatim.

## Headline — the honest B-only outcome

**`numba_improvement_only_native_goal_open`.** The packet ships **no native default**. At the production block B=1024 (tier B, amended quiet window, parity-proven, min-of-9), native C **lost end-to-end to the parallel main-parity Numba row A0p in 3/3 mixes** (all-binary uniform all-min: A0p **3.3627 ms** vs C1 **3.4655 ms**; mix 2.7487 vs 2.9668; all-raw 0.5485 vs 0.7338). The selection applied the pre-registered branch `numba_improvement_only_native_goal_open`.

- The **Numba improvements are retained and shipped** (row A everywhere, bitwise main-parity).
- The **native goal remains OPEN**.
- **Promotion is INCOMPLETE by measured decision** (N8-44: "NO CERTIFICATE (promotion incomplete by measured decision, honestly recorded)").
- **Nothing was published**: no qualified artifact, no default flip; `src/solweig_light/_native_dispatch/qualification_registry.json` ships `{"records": []}` and fail-closes to row A.
- Per the goal contract: *source fallback success is not native deployment success*, and missing-candidate is *unverified, not passed*.

Never claim: native deployed / qualified / faster end-to-end at production block.

## Anchor commits (cited verbatim)

| Commit | Subject |
|---|---|
| `4761c4d6` | N8-32 selection: numba_improvement_only_native_goal_open (APPROVE-WITH-NOTES; R-SEL-1 applied) |
| `b4a4c5ba` | N8-40 formal completion + N8-42/43/44 unavailable-state closure; N1/N2 docstring repairs |
| `5ed9699e` | N8-50 freeze: retained state frozen; first complete installed no-env pass |

Supporting lineage: `8878fc14` (N8-31 tier-B record), `5d020fd3` (N8-41 candidate wheel), `a19e22db` (N8-40b public seam), `730eb4de` (N8-42/43 cell freeze), `3079d69a` (n841-3 install_assets), `290da338` (selection skeleton pre-registration, 2026-09-22T23:55:56Z).

## Yaml gates

**Gate 1 — "N8-51 outcome or unavailable state present": SATISFIED, unavailable state present.** N8-50 `scale_protocol_N8-51`: "UNAVAILABLE STATE -- no final scale campaign". The final 1024/24-tile campaign exists to qualify a native default; no candidate advanced; running it without a candidate would produce a record with nothing to promote. What *was* measured: the production block B=1024 end-to-end in tier B (3 mixes × REPS=9, parity, both accountings) — `evidence/trials/n8_31_tierB_record.json`. Reactivation: rerun the frozen N8-42/43 cells after new pre-registered evidence per the selection's flip conditions; no gate loosening after failures.

**Gate 2 — "native goal vs B-only outcome honest; no publication": SATISFIED.** N8-44 affirms positively that **no promotion criterion was loosened at any point** — the only amendment was the tier-B *measurement window* (loadavg < 2.0 → < 5.0, `amendment_2026-09-23T0817Z`), reviewer-verified **pre-results** (tier-B review R-B4) before any candidate had failed. Shipped state is fallback-only on this platform by fail-closed selection; native execution exists only in the N8-31 harness cells (INFORMATIONAL/NON-PROMOTION); no platform is claimed native-qualified. This record's headline *is* the B-only outcome.

## Shipped end state

Row A (main-parity Numba) everywhere by fail-closed empty registry; vendored machinery inert; the N8-41 candidate native wheel ships staged generation with **no qualification claim**. At freeze (5ed9699e): policy+dx **95 passed**; integration+region **167 passed** in 41.6 s; installed no-env suite **24 passed, 4 skipped** — first complete pass of both pipeline gates (offline wheelhouse → plain pip wheel → fresh venv outside the repo; API and real CLI under read-only site-packages, network guard, non-writable native cache; 48-band UTCI+TMRT default contract via GDAL). Freeze-time snapshot: `evidence/installed/installed_gates.json` (api_gate=passed, cli_gate=passed, 4 labelled deferred skips). DX surface **AFFIRMED**, not re-frozen. The 4 skips are the deferred native-channel labels, dispositioned by N8-42's unavailable-state record and the selection.

Defect found and repaired *at* freeze: `installed_cli_run` never set `record['scene']`; the CLI gate reached its output assertion for the first time (prior runs were `[host-memory-pressure]`-skipped) and the KeyError exposed the latent fixture bug — repaired, suite re-run green. The gate itself passed on the first attempt.

## Known residuals (obligations for whoever picks this up)

1. **R1 — tier-A R13 lineage.** Tier-A numbers live in `n8_31_tierA_record.json` as corrected by R13-D1/D2 and **R-SEL-1** (canonical B1 = produce + pack_masks + adapter; corrected row 0.5035/0.4688/0.2024; outcome-invariant). The selection **skeleton's** tier-A B1 row (0.4757/0.4396/0.175) and its malformed `recorded_utc` are **stale** — R-SEL-1 verbatim: "the skeleton's numbers must never be cited over the corrected records."
2. **R2 — conftest discipline.** Bare `from conftest import ...` breaks under combined runs (pytest rebinds `conftest` to the last-collected sibling suite's conftest; see `tests/optimization_v8/installed/conftest.py` header). Use uniquely named helpers modules (`native_test_helpers`, `installed_test_helpers` pattern) for any new suite.
3. **R3 — N13-7, deferred at next harness touch.** `quiet_window_abc.py --block-sizes 0` parses to a zero-size block with no validation → vacuous pass. Fix only at the next harness edit, inside its delta review.
4. **R4 — expert-route flip obligation (wheels-time).** n840-6 "staged expert migration" + n841-7/n841-8 (`n8_40_integration_record.json`, `n8_41_pre_wiring_notes.json`): vendoring landed early with the guardrail that the expert env route keeps serving the legacy B7-32 path until the wheels-time flip; keep the **single env-read site** (cylinder_longwave seam); and a broken selector module must **not** silently resolve to row A without a recorded decline (reviewer probe: ImportError today resolves quietly to A — fail-safe but unrecorded).
5. **R5 — memory-gated installed-gate skips.** `[host-memory-pressure]` is an environmental block (scene phase reservation ~1.74 GB vs budget = 0.5 × host available-memory view), retried then recorded with exact numbers — never a fake pass, and never an admission-model weakening.
6. **R6 — registry-empty invariant tests are the qualification guard.** The shipped registry must stay empty and fail-closed to row A until a candidate clears the promotion gates (`test_lw_dispatch.py`, `test_lw_public_seam.py`, `test_installed_loader.py`, `test_deferred_gates.py`, `test_region_fork_policy.py`). Future qualification = new registry record + passing gates + pre-registered amendment — never test relaxation.

## Unavailable-state lineage and reactivation

- **N8-42** (`evidence/integration/n8_42_unavailable_state.json`): small exact chronology + no-env DX qualification NOT STARTED — no qualified candidate exists. "Starting this qualification without a selected candidate would manufacture promotion evidence the selection does not authorize."
- **N8-43** (`evidence/default_trials/n8_43_unavailable_state.json`): installed-default paired comparison NOT STARTED — no native default arm exists; row A itself *was* measured as arm A0 in both tiers.
- **N8-44** (`evidence/promotion/n8_44_no_certificate.json`): promotion rejected as inapplicable; criteria never loosened.

All three are **NOT-STARTED BY DECISION**, not skipped-by-omission. Budget: the one-final-workload-campaign budget was consumed by tier B (zero retries, censored-free); the at-most-one-causal-retry budget remains unspent. Reactivation sequence: frozen N8-42/43 cells → N8-51 scale protocol → registry record only after promotion gates pass → wheels-time expert-route flip (R4) → only then any default change.

## Dossier

`FUTURE_OPTIMIZATION.md` (repo root) carries the durable practice — evidence-ledger discipline, the 9-step future sequence, residual metrics, known mistakes (including *"Default enabling on one giant-block synthetic win"*, the exact failure mode the 3/3-mixes-at-production-block rule exists to prevent), and future interfaces. Forward-looking ideas live there; the residuals above are obligations, not ideas.

## Review lineage (all by n8-rev-n8-13, all under `evidence/reviews/`)

- `n8_30_review_n8_13_delta` — harness delta / conftest repair / tier-A fidelity (R13-D1, R13-D2)
- `n8_30_review_n8_13_tierB` — tier-B transcription (R-B1..R-B5; R-TB1 applied)
- `n8_30_review_n8_32_selection` — selection (APPROVE-WITH-NOTES; R-SEL-1 applied at 4761c4d6)

**Next:** integrator verifies this handover against the cited commits/records and commits it. Packet N8 ends here — **native goal OPEN, promotion incomplete, nothing published.**
