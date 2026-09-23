# C6-100 integrator dispositions (freeze at ea2eed53)

Date: 2026-09-21. Integrator dispositions on the C6-100 worker report;
freeze source remains ea2eed53 (no src/tests edits after the freeze — any
fix would require a new reviewed commit and a re-freeze).

## raw-True differential failure — disposition: sanctioned stricter
## admission boundary, environmental trigger; numerics independently covered

Observation (worker, reproduced by integrator twice): at HEAD ea2eed53,
`tests/differential/test_pipeline_reference.py::test_chronological_tiff_pipeline[raw-True]`
raises `ResourceAdmissionError` (runtime_memory.py:919) — "simulation job
0_0 (32x35, patches=153) needs about 1,736,017,587 B but only
1,307,272,806 B of the 1,736,769,536 B budget remains after parent
(429,496,730 B)". The same suite at base 8e0b3877 passes 9/9 under the
same host conditions (integrator-verified).

Analysis:
- The budget is the PRE-EXISTING availability-sensitive default:
  `default_memory_budget_bytes()` = min(physical, available) × ¼
  (runtime.py:289). With 40% of 16 GiB free at measurement time, budget
  = ~1.617 GiB; the corrected C6-42 reservation for the job is ~1.617 GiB
  plus the 0.4 GiB parent charge, so admission rejects — before any worker
  spawns, with the pipeline's own public error.
- The rejecting check is the C6-42 W1 `plan_phase_admission`, whose
  stricter boundary was explicitly adopted at the C6-42 review
  (APPROVE-WITH-NOTES rev3; ledger m7 §3: single-job budgets in a band
  would NEWLY raise — accepted). Base lacks `runtime_memory` entirely and
  could not raise this error; the base-vs-HEAD delta is the sanctioned
  admission correction, not a numerical change.
- The numerical content of this exact scenario is already proven at the
  freeze: the wheel gate ran the same public entry (full `thermal_comfort`,
  35×32 true small_original_cpu fixture, 24 met records, 1 tile) twice —
  wheel vs src, pinned 12 GiB budget — and all 10 simulation output TIFFs
  are BITWISE IDENTICAL. The raw-True failure contains no numerical
  comparison at all (rejection precedes execution).
- Trigger is host memory pressure (other agents active, loadavg 6–10,
  40% free): at a quieter host the default budget exceeds the requirement
  and the case passes. The test binds default options, so its pass/fail
  tracks host available RAM — an availability-sensitive test on an
  availability-sensitive budget, not a regression introduced by the freeze.

Resolution recorded here rather than patched: weakening or special-casing
the admission after the C6-42 review adoption, or editing a differential
test after the freeze, are both out of scope for C6-100. Carried as a
standing known item:
1. the raw-True case (and any default-options public-entry test) is
   host-RAM-sensitive by construction; future work may pin
   `memory_budget_bytes` in the test for determinism (small reviewed
   commit + re-freeze), and
2. low-RAM hosts now get an explicit pre-spawn `ResourceAdmissionError`
   where base would have proceeded — the C6-42 adopted trade-off, visible
   in this one case.

## Gate verdict for the freeze record

Small true TIFF/state gates: PASS on substance — 8/9 suite cases green,
and the one red case is admission-boundary sensitivity with its numerical
scenario proven bitwise by the wheel gate. Wheel gate: PASS (build,
fresh-venv install, import origin asserted, end-to-end scene bitwise).
Freeze stands at ea2eed53 with the two known items above and the
already-recorded absences (24-tile dataset → C6-101 unverified).
