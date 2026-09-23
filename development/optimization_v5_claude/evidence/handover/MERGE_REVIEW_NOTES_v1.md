# C5-64 Merge-review packet

Status: FINAL. L4 campaign complete (both cases bitwise-pass, target
demonstrated once); C5-63 independent review verdict ACCEPT-WITH-NOTES
(`evidence/final_scope/REVIEW_C5-63.md`), all notes applied in this packet.
The commit containing this file is the final branch tip; the final evidence
commit before handover is `de48e54e`.

## Branch / base / tip

- Branch: `perf/claude-glm53-cpu-v5` (worktree
  `/Users/alansynn/Workspace/solweig-light-claude-v5`), left unmerged, no push,
  no PR.
- Historical optimization checkpoint (v4): `14e888760727583ef782a4dc0e7a5c7c6e6ff9d1`.
- Integration base: `bfd9915e411e28bfe498d547e3c820a4de863ee2` — source-identical
  to `14e88876` over `src/`, `pyproject.toml`, `tests/` (verified: empty diff).
- Tip at freeze (wheel source): `d2edbc105d5d3658d25613326439d3a3efb74bb9`;
  freeze commit `d63636ae`; final evidence commit `de48e54e`; branch tip: the
  handover commit containing this file.
- Model/API ancestry: `nvnsudharsan/SOLWEIG-GPU@0d7fe742abeeddd890dd58fc76ed7f78bd47faec`.

## Accepted patches (reviewed, integrated, L2-gated)

Every integration merge was followed by the L2 chronological gate (dense_urban_256,
24 steps, 153 patches, 10 outputs, checkpoint_interval=1; 23 substantive artifacts
bitwise-identical vs pristine `REFERENCE_bfd9915e_dense256.json`).

| Patch | Family | Worktree of origin | Review record | Verdict |
|---|---|---|---|---|
| R01a guarded absorbing-state early exit (`_trace_pixel`) | rays | `../solweig-light-v5-ray` | `evidence/reviews/rays/REVIEW_C5-30.md` | accepted |
| P01 fused decode+accumulate (DORMANT behind `SOLWEIG_LIGHT_FUSED_RAD=1`) | radiation | `../solweig-light-rad` | `REVIEW_C5-31.md` + portfolio rejection notes | measured rejection — retained dormant, default path unchanged |
| G02 direction-invariant source hoisting in `_gvf` (+ two-state Lup snapshots, ewall gate) | gvf | `../solweig-light-gvf` | `REVIEW_C5-32.md` + amendment `c987cbb8` (AMENDMENT-ACCEPTED) | accepted |
| G03 fused row-block gather+postprocess `_gvf_fused` (block_rows=32) wired for threads>1 | gvf | `../solweig-light-gvf` | `REVIEW_C5-32.md` + F1 aliasing-gate follow-up | accepted |
| S02 persistent worker pool (`plan_admission`, serve mode `SOLWEIG_LIGHT_WORKER_POOL`) | runtime | this branch | `REVIEW_C5-33.md` | accepted (inactive at workers=1 default) |
| S07 checkpoint digest optimization (pending per-write digests, stored-bytes law) | storage | `../solweig-light-rt` | `REVIEW_C5-53.md` + F2/F3 follow-ups `fd3392c7`,`0ecb9042` | accepted |

Rejected / not selected (valid outcomes, recorded):

- R04 bush-path specialization — rejected: `bush ≡ 0` theorem
  (`pipeline.py:130` — `np.logical_not(vegdem2*vegdem)*vegdem` identically 0 when
  dem≥0); step-major bush path unreachable.
- P01 fused route (active) — rejected twice by measurement (portfolio v1: +46%
  pipeline regression at t4_b1024; rework: still +9.4%); env-gated dormant final.
- Second-wave C5-50/51/52/54 residuals — not selected: measured post-S07 residual
  census showed remaining stages below adoption threshold; census recorded in
  `evidence/portfolio/PORTFOLIO_v2_*` and post-S07 census notes.

## Honest routing record

All implementation and review work executed by GLM-5.3 via Z.ai (Claude Code).
Actual Anthropic Opus route: NOT AVAILABLE — recorded in
`evidence/routing/` (routing manifest, C5-01). All review records are labeled
"independent GLM review (Opus unavailable)". Reviewer independence was procedural:
distinct agents, immutable commits under review, negative controls reproduced
(e.g. G02 amendment reproduced 79/396-cell divergence before acceptance; P01
rejection backed by isolation experiment in a throwaway worktree).

## Numerical-parity evidence

- Small/medium: L2 gate after every merge (23 artifacts bitwise) —
  `evidence/l2/`.
- Freeze: installed-wheel L2 checks under py3.12 and py3.11, both bitwise-PASS;
  py3.11 doubles as cross-interpreter proof — `evidence/freeze/`.
- Final scale: L4 candidate runs vs intact v4 large reference (bitwise sha256,
  provenance chain in `benchmarks/protocols/claude_v5/final_protocol_v1.json`)
  — `evidence/final_batch/` (filled at handover).

## Deferred gates / unverified scope

- dense1024 TMRT Linux p8 gate failure: inherited disposition, preserved as-is
  (different host; no local large parity claim inherits it). Caveat per
  `evidence/inventory/PRIOR_EVIDENCE.md:147-152`: the canonical v4 record
  itself is an UNRESOLVED POINTER in the v5 inventory — only the
  disposition-preservation policy was locatable, not the full v4 record.
- Inherited SVF/UMEP exceptions: failed-by-disposition, unchanged. Caveat: the
  inventory anchors exactly four code/test anchors but could not locate the
  authoritative v4 list; the count "four" is the inventory's own anchoring.
- Single-pass L4 demonstrates the target once (`target_demonstrated_once`); not
  robustness/reliability, not P7/P8 release qualification.
- S07 signed-zero-only-block read-back reads the live band through the GDAL block
  cache rather than the file — pre-existing base behavior, preserved unchanged
  (false-fail-only risk, documented at `persistence.py` docstring fix `fd3392c7`).
- Per-merge L2 gating is a procedural record (run during the campaign, not
  archived per merge); the stored, independently re-verifiable evidence is the
  pristine reference plus the freeze-time installed checks, which together
  carry the load-bearing claim (tip ≡ base numerics).
- v4 reference output binaries live only in the MAIN checkout
  (`/Users/alansynn/Workspace/solweig-light/reports/.../large_runs_v1/`);
  the v5 worktree holds their manifests only (size). Merge reviewers verify
  parity against the main-checkout copies.
- Installed-check run trees were transient (`/tmp/v5-installed-check{,-311}`);
  the durable artifacts are the two committed check JSONs plus
  `freeze/FREEZE_CHECKS_ATTRIBUTION.json` (exact invocations and interpreter
  versions; the check JSONs themselves do not embed the interpreter version).

## Cleanup at handover

- Throwaway worktrees `/tmp/v5-base-bench` and `/tmp/v5-nofused` removed.
  `/tmp/v5-nofused` contains a diagnostic `return None` in `_packed_leaves` —
  NEVER merge from it.
- Family worktrees (`../solweig-light-v5-ray`, `-rad`, `-gvf`, `-rt`) left in
  place for merge-review inspection (unmerged branches).
