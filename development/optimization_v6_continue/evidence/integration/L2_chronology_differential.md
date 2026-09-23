# L2 chronology differential — C6-70 first-wave integration

Date: 2026-09-21. Host: arm64 macOS, 10 cores, 16 GiB, dev tier (contended).

## Scope

Whole-pipeline A/B between the pre-integration base and the integrated tree
on the deterministic 96x96 dense_urban motif scene (reference own-met,
24 timesteps, cylinder-anisotropic workflow, save_tmrt plan), instrumented
at the radiation entries with input/output byte hashing.

- Base: detached worktree at `8e0b3877` (ledger commit; last pre-integration HEAD).
- Integrated: `perf/claude-glm53-cpu-v5` at `78d242a6` (C6-70 a..i).
- Probe: `chronology_probe.py` (identical bytes run in both trees; the
  scene fixture module is loaded from the integrated tree in both runs and
  is byte-identical input, not code under test).

## Instrumentation

Wrappers around `patch_radiation.Kside_veg_v2022a`,
`patch_radiation.define_patch_characteristics`,
`pipeline_demand.lside_veg_v2022a_demanded` (installed before the engine
module import; the engine binds the name at module level),
`engine.Lside_veg_v2022a`, and — integrated tree only —
`cylinder_longwave.Lcyl_v2022a_by_demand` (engine imports it function-
locally, so the module attribute is resolved per call). Every ndarray
argument and return is hashed (dtype+shape+bytes, sha256); logs are NDJSON.

`execute_tiles` is swapped in-process (same job dicts, same `run_tile`
entry): the persistent subprocess pool would run tiles in children where
the wrappers do not exist. Only the transport differs; the numerical work
under test is identical, and admission still runs parent-side.

## Defects found by this differential (fixed in 78d242a6)

1. `cylinder_shortwave.set_demand_profile` returns None (set-only API);
   the C6-70d scope stored it as "previous" and every pipeline run raised
   `ValueError: unknown radiation demand profile: None` at scope exit.
   Post-02c0efa4 gates were kernel-level only and never exercised the
   pipeline scope — this differential is the first full-pipeline gate.
2. The C6-20 recipe's driver-side `radiation_demand` context was never
   added, so the anisotropic Lside fast path was silently inert (full
   fallback every step). Now wrapped around the per-timestep
   `Solweig_2022a_calc` call per the recipe's driver-side placement.

## Results (integrated 78d242a6 vs base 8e0b3877)

| stream | base | integrated | verdict |
|---|---|---|---|
| `Lside` events | 24 | 24 | inputs AND outputs sha256-identical, all 24 |
| `Kside_veg_v2022a` events | 14 | 14 | inputs AND outputs sha256-identical, all 14 |
| cylinder longwave | `define_patch_characteristics` x24 | `Lcyl_v2022a_by_demand` x24 | transitively equal (see below) |
| final TIFFs | 11 | 11 | all 11 sha256-identical |

Transitivity for the longwave route: the per-timestep `Lside` input hash
covers `Ldown` (the longwave route's primary output) and the final
`Ldown`/`Lup`/`Tmrt`/UTCI TIFFs are bitwise identical, so the dispatcher's
outputs are pinned even though its signature differs from the base patch
entry (distinct label `longwave_demand`; signatures are not comparable).
The `Lside` `demand=` keyword is normalized out of the log (base has no
such keyword).

Raw logs: `l2-logs/l2-base.jsonl`, `l2-logs/l2-integrated.jsonl`,
`l2-logs/l2-{base,integrated}-output-hashes.json`.

## Limits

- Single scene (96x96), 24 steps, one date, workers=1 in-process
  transport, dev tier. This is a correctness gate, not a timing claim.
- Kside runs 14 of 24 steps (daytime cylinder shortwave) in BOTH trees —
  counts match base behavior; no step gained or lost a radiation call.
- Missing data/reference remains unverified where the probe does not reach
  (e.g. per-call fp flag states under non-default errstate are not hashed;
  the typed-kernel contracts for those are pinned by the C6-31 suite).
