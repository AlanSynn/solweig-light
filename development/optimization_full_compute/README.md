# Full-computation optimization

Work in progress, requested 2026-10-20. Reference: main commit
`288d70e2b3bd8ca5bba4b65e572048fea37bcc51`.

## Workload and comparison contract

The requested production comparison is the user's 600 × 600 Atlanta tile,
19 chronological timesteps, 153 sky patches, all four raster layers, and
the same own-met forcing. Keep one original logical tile, output timestamps,
TMRT and UTCI outputs, checkpoint interval 1, full legacy geometry exports,
and matched cold geometry / warmed JIT conditions on both sides. Report
first-use startup separately. Run reference and candidate with the same
Python environment, CPU affinity, thread count and output options.

The original data and `02_CPU_SpeedTest.py` are on another machine and are
not present in this checkout. The reported 76.1-second lite result is
historical context, not a measurement of this pinned main on the current
machine. Synthetic family timings and repository fixtures must never be
presented as that production comparison.

## Implementation scope

- Ordered SVF accumulation around the unchanged ray calculation; static
  bush routing; cached parallel daylight wall-shadow kernels.
- Single-pass exact legacy visibility comparison, combined TIFF validation,
  vector native payload validation, write-time hashes and mapped descriptors.
- Compiled bounded shortwave/longwave block schedules, mixed-dtype prepared
  GVF postprocessing, and explicitly owned static radiation preparations.
- Reused engine subexpressions, streamed checkpoint serialization, reduced
  raster copies and explicit accounting for added resident/scratch memory.

Each accepted implementation must pass its frozen intermediate and final
numeric contracts, mutation/corruption checks and output/restart behavior.
No physics, ray, resolution, patch, timestep or tolerance reduction is part
of this change. Preserve defensive fallback paths and public signatures.

## Verification and performance rounds

1. Establish family references; implement and run focused differentials.
2. Run genuine chronological TIFF-to-TIFF and restart checks.
3. Compare main/candidate with identical inputs, including every requested
   output and state; keep raw timing and profile results outside git.
4. Profile the candidate, make a small change addressing a measured residual,
   then repeat the relevant correctness and paired timing checks.

Only compact summaries, invocations and evidence hashes belong here. Raw
rasters, profiles, timing trials and compiled caches follow `CLAUDE.md`'s
external-evidence policy. The PR remains a draft until its comparison and
remaining verification requirements are resolved.
