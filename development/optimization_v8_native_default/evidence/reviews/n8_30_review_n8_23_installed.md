# N8-30 review of N8-23 (installed DX gates) — APPROVE-WITH-NOTES

Reviewer: n8-30 review service (independent; did not author N8-23).
Target: `tests/optimization_v8/installed/` (8 files) + `optimization_v8_native_default/evidence/installed/installed_gates.json` @ `16cdc56c` (perf/native-optimization).
Full record: `n8_30_review_n8_23_installed.json` (this directory).

## Verdict

**APPROVE-WITH-NOTES.** No blocking defects. The implemented gates enforce what they claim, isolation is real (env -i semantics, external venvs, METADATA-pinned offline wheelhouse), labels are honest (including the memory-blocked skips), and the routed shadowing fix is applied and verified. Two contract lines are approximated rather than enforced (N1 site-packages read-only, N2 no-network monitoring) — both become mandatory before the N8-41 native-wheel rerun.

## Reviewer-recomputed facts (independent of the author's code path)

| Item | Value |
|---|---|
| suite rerun | `.venv/bin/python -m pytest tests/optimization_v8/installed -p no:cacheprovider -q` → **11 passed, 6 skipped, 0 failed, 147.97s** (matches the claimed 11/6/0) |
| skip composition | 4 deferred-by-design (`N8-41`×2, `N8-42`×2) + 2 `[host-memory-pressure]` (API + CLI, each 3/3 admission-refused attempts) |
| collection safety | `pytest tests/optimization_v8/installed tests/optimization_v8/region --collect-only -q` → **168 tests, 0 errors** (0.54s) |
| frozen main-vs-branch asserted-leaf drift | recomputed via dx_snapshot in a fresh interpreter: **empty** — the parity gate's empty allowlist is correct, not a bypass |
| frozen CLI flags | **27** in `main_surface.json` (claim: 27) — help gate asserts set equality both directions |
| admission arithmetic | pass needs budget ≥ 1,736,017,587 + 429,496,730 = 2,165,514,317 B → host available view ≥ **4.33 GB** (claim "≥4.3 GB" ✓); observed host views 3.26–3.49 GB; parent charge 429,496,730 B = 409.99 MiB (claim "~410 MB" ✓) |
| wheel digest | run-scoped as disclosed: 4 builds → 4 digests (`1beed50d…` pre-review evidence, `042315ec…` my rerun, `9bd9a62e…` author's post-fix rerun = **final evidence file, 17:23:01**, `1058a71d…` handoff claim — stale, see N4) |
| final evidence state | author's post-fix rerun (17:23:01) superseded my regeneration; gate statuses identical (both blocked 3/3, needs 1,736,017,587 B, 4 deferred, surface_gate null) |
| ownership | zero tracked-file modifications; HEAD unchanged at `16cdc56c`; pyproject/src/packaging untouched |

## Shadowing fix — APPLIED (verified in final bytes)

The routed fix landed **during this review** (17:13:56–17:18:13); I re-read the final bytes and ran everything after completion. `installed_test_helpers.py` (unique name, sole instance in `tests/`) now holds the shared constants/helpers including `GATE_RECORD`; `conftest.py:50-64` imports from it; all three test files are rewired (`test_installed_noenv_gates.py:21-22`, `test_installed_wheel_gates.py:23-24`, `test_source_fallback_gates.py:23-26`). No bare `from conftest import` remains. The hazard was real and pre-proven (`experiments/optimization_v8/policy/results/full_tree_failures.json`, entry for `test_surface_gate_recorded`). Post-fix: standalone suite green (11/6/0), combined collection clean (168 tests).

## Per-obligation results

1. **Gate fidelity — PASS, two gaps (N1/N2).** Gate 2: README-style `thermal_comfort` in the installed venv interpreter (`conftest.py:323-341, 344-369`; `test_installed_noenv_gates.py:58-80`) + real console-script run (`:372-422`, `:108-118`); the child env is a literal 5-key dict so no `PYTHONPATH` can exist. Gate 3: backend vars absent by construction, `PATH=/usr/bin:/bin`, native dev cache chmod-555 with before/after emptiness asserted (`test:76-77,117`), scene outputs + Numba cache the only writable targets. Gate 5: source install under stripped PATH with no ispc/c-compiler tokens in the log + real `preprocess`/`calculate_svf` on Numba with GDAL-verified SVF (`test_source_fallback_gates.py:89-123`). Gate 7: torch/cuda/nvidia payload ban, canonical Requires-Dist equality to the frozen surface, forbidden-dep scan, real own-met scene (`test_installed_wheel_gates.py:73-99`). **"No network" is asserted/structural, not enforced** — nothing monitors or blocks sockets during model execution (N2); **site-packages is never made nonwritable** (N1).
2. **Isolation honesty — PASS.** Venvs under pytest tmp outside the repo; origins enforced twice (child-side `sys.modules` sweep after the real run, `API_SCRIPT:336-340`; parent-side `pkgutil.walk_packages` with an explicit `/src/solweig_light` ban, `test_installed_wheel_gates.py:105-121`); wheelhouse pins 12 exact name==version pairs matched from each archive's dist-info METADATA and re-verified inside the repacked zip (`wheelhouse.py:32-45, 111-114, 154-165`), with pip's RECORD-hash check backstopping the repack; `child_env` cannot leak parent vars (no `os.environ` copy).
3. **Labels — PASS.** NOT-native-qualified appears in every fallback surface (docstrings, asserted constant, `GATE_RECORD.mode_label`, README, evidence); deferred skips carry exact owner IDs; the `[host-memory-pressure]` skips record 3 attempts each with the full admission numbers, retry at 20 s spacing, never fake a pass. **Pass-on-idle is arithmetically plausible** (0.85–1.1 GB shortfall vs a ≥4.33 GB host-view requirement; idle hosts clear it with ≥2× margin), but **gates 2/3's execution halves remain UNPROVEN until the quiet-host rerun** — the TMRT/UTCI output assertions have never executed. Partial credit is real and bounded: preprocess+SVF completed and the Numba JIT cache populated (4 entries) inside the installed venv before the refusal. Context N5: the refusing check is the branch's own C6-42 admission gate; main would not refuse.
4. **Surface parity — PASS.** Capture runs in a child of the installed venv's python with only the dx dir on its path (`dx_snapshot.py:606-622`, called at `test_installed_wheel_gates.py:138`); the `SOLWEIG_DX_PACKAGE_ORIGIN=subprocess:<python>` form exists at `test_dx_surface.py:56-62`. Empty-allowlist comparison with baseline↔branch cross-check means any drift fails (`dx_snapshot.py:681-734`); reviewer recomputed the frozen pair's drift as empty.
5. **Shadowing fix — APPLIED** (above).
6. **Rerun — PASS.** 11/6/0 in 147.97s; `installed_gates.json` regenerated by the rerun's own sessionfinish (inherent side effect of the instructed rerun).
7. **Ownership — PASS.** No tracked diffs, no commits, deliverables confined to the two owned paths; wheel is a plain `py3-none-any` from the untouched pyproject.

## Notes (non-blocking)

- **N1** — site-packages never made nonwritable (`PACKAGING_AND_DISTRIBUTION.md:43`); only the native dev cache is. Add chmod-or-diff enforcement before the N8-41 rerun.
- **N2** — no-network is structural (`--no-index`, local files), not monitored; a backend-origin socket attempt would go undetected. Add a socket blocker or socket-open assertion; mandatory once a native build path exists (N8-41).
- **N3** — `GATE_RECORD["surface_gate"]` is initialized but never written; the evidence JSON permanently shows `null` and the parity gate's proof lives only in the pytest outcome.
- **N4** — handoff's wheel digest `1058a71d…1917` matches none of the three on-disk/run digests (`1beed50d…`, `042315ec…`, `9bd9a62e…` final); consistent with the disclosed run-scoped digest, but the quoted value is stale — treat digests as run-scoped only.
- **N5** — the memory block originates from the branch-added C6-42 parent-side admission (documented divergence); "baseline resource-admission model" is accurate for this branch, but cross-branch comparisons should note main would not refuse.

## Still open (tracked, not blocking this verdict)

- Quiet-host rerun of the two blocked gates (coordinator-scheduled) — gates 2/3 execution halves **UNPROVEN** until then; reviewer did not force them under current host load, per review instructions.
- N8-41: native-wheel + companion channels; N8-42: upstream-collision + adversarial native channels (all correctly deferred with labels).
