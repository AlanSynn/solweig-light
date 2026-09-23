# C6-81: residual selection after the C6-80 portfolio

Date: 2026-09-21. Owner: coordinator (dossier 08). Inputs:
`evidence/portfolio/README_C6-80.md` (64 single-lease runs, dev tier, host
NOT quiet — loadavg median 11.2 from unrelated OS daemons), decoder probe
re-measurement, and the landed integration surface at 2ce117e0.

## Decision rule (dossier 08)

Activate residual work only on a remaining **measured** service demand;
rank by removed bottleneck service over implementation+proof+validation
effort; do not select from catalog size. Dev-tier honesty rule from C6-80:
directional calls only, no <5% adoption decisions on this host.

## Selections

| candidate | decision | measured basis |
|---|---|---|
| Prepared decoder default adoption (C6-50 wiring) | **DECLINED** (landed 46450c75) | +21–24% per full-frame sweep at all four cells (t128/t256 x strides 128/1024); reproduces the recorded dev-tier numbers; preflight does not amortize with size. Route now opt-in (`SOLWEIG_LIGHT_PREPARED_VIS=1`), fallback byte-identical; adoption arguments remain exactness/memory-profile only. |
| C6-90 one-pass stored export verifier (S01) | **NOT SELECTED** | Export/publication is unchanged by the integration and small at the timing tier (t256 cold stage B ≈ 4.3 s publication/compare of 10.4 s; warm fast-hit ≈ 0.13 s both trees). No measured read-amplification demand in the service path. |
| C6-91 exact radiation preparation + aniLum (R09/R06) | **NOT SELECTED** | Simulation dominates (14–43 s of 19–54 s totals) but no measurement isolates aniLum/coefficient-preparation cost; selecting on catalog prior is what dossier 08 forbids. |
| C6-92 remaining ray/GVF prefix (S07/G05) | **NOT SELECTED** | Same: no measured in-sim residual attribution for ray suffixes or prefix replay. |
| C6-93 ordered staged exports / tail scheduling (C04/S10) | **NOT SELECTED** | Phase route already carries production concurrency at its gate; warm production pending is empty under production semantics; 2-tile batches show no tail worth removing. |
| C6-94 profile-driven residual | **NOT SELECTED (deferred)** | The honest gap IS measurement: no in-sim stage attribution exists. Deferred until a measured demand appears — first candidate trigger: the actual 24-spatial-tile dataset (still absent), at which point C6-100's frozen workload should be profiled under lease before any tier-5 implementation. |

## Additional dispositions recorded

- **Phase route at t128 is net negative** (spawn+barrier ≥ the serial svf
  stage it replaces) while it **pays at t256** (production ~halved; P2 cold
  −10.9% vs base P2). Gate stays as landed (`workers > 1 and cache_enabled
  and >1 pending`): the serial default is untouched, activation is already
  user-opt-in via workers, and tuning a shape threshold on this noisy host
  would be exactly the <5%-confidence call C6-80 forbids. Caveat recorded
  for any future gate work.
- **Cold wins are the integration's durable gain**: S1 −6.4/−9.8%, T2
  −6.1/−16.2%, P2 −10.9% at t256; warm steady state a wash with the decoder
  loss still inside — declining it (above) recovers margin without new
  mechanism.
- **C6-70 sign-off item closed** ("OPEN until C6-80: GDAL_CACHEMAX cap no
  per-worker regression"): C6-80 telemetry shows the cap applied in worker/
  phase children via `_child_environment`, integrated cold wins and warm
  wash with the cap active — no regression signal at the timing tier.
- **Zero conditional implementation tasks selected** → C6-99 reduces to
  confirming the branch's final integration surface; C6-90..94 remain
  available, each requiring a fresh measured activation case.

## What this selection does NOT claim

No statistical or release claim; no actual-target claim (the 24-tile
dataset is still absent — C6-101's campaign scope remains unverified until
it exists); all numbers dev-tier single-lease observations.
