# Wave-2 independent review notes (S10-20 + S10-21)

Date: 2026-10-14. Reviewer: fresh-context independent subagent (author
excluded). Verdicts: **S10-20 approved_with_notes, S10-21
approved_with_notes — no blockers.** Full record: `wave2_reviews.json`
(also archived raw at
`/storage/scratch1/1/dsynn6/solweig-light-s10-raw/residual/reviews/`).

Independent verification the reviewer executed (not author-supplied):

- Census-trap clearance from RAW data: run48/oracle48 route counters read
  directly (`prepared=30/serial=0` + primaries `48/0` vs
  `prepared=30/serial=30` + references `0/48`), and the wrapper-bite
  mechanism confirmed at the source level (engine in-function imports;
  all four `_uniform_tgwall` admission sites).
- `compare24` and `compare48` re-run from disk by the reviewer: PASS,
  worst values and coordinates byte-identical to the repo deliverables.
- Multitile bitwise re-verified with a reviewer-written checker (10 files
  × 24 bands, uint32 views, all equal) — not the harness's own code.
- Multiply-counting audit: dpc nesting confirmed (cylinder_longwave.py:466
  inside the wrapped Lcyl span; the separate engine-level dpc wrapper
  recorded 0 calls); all fractions disjoint by call span.
- t(W,H): ordering holds in all 9 raw_runs; medians/spreads/ratios
  reproduce; no minima cherry-picked; D07 recording list complete.
- Gates re-run: `tests/optimization_s10` 59/59; landcover differential
  2/2.
- Provenance: all 6 harness sha256s and both Dropbox archive sha256s
  match; repo JSONs identical to raw outputs (value blocks).

Findings — all minor, all closed same day:

| id | task | defect | closure |
|----|------|--------|---------|
| F1 | S10-21 | doc calls/run column wrong (2/4/...); JSON calls_per_run floor-divided | true counts 14/24/14/24/14/14 in doc + regenerated JSON (raw final-rep counts); probe derivation fixed for future runs; shares unchanged |
| F2 | S10-20 | default budget view typo 2,744,623,104 vs raw 2,744,442,496 | doc + integration_commit.json claim corrected; collector source fixed |
| F3 | S10-20 | l2_results 'reading' claimed Kdown/Kup exact vs goldens | reworded: within budget vs goldens; exact only in the 48-step oracle differential (and Shadow/Ta/Wind both) |
| F4 | both | dirty flag undisclosed; residual head self-reported | provenance_note added (dirty = untracked packet zip); S10-30 instruction: full porcelain + git-derived HEAD in-harness |
| F5 | S10-20 | determinism pair not independently verifiable from disk | doc caveat + retention note added; future claims retain per-execution compare JSONs |

No measurement claim changed: every numeric correction was prose or a
misderived presentation field; the underlying raw values were verified
correct by the reviewer.
