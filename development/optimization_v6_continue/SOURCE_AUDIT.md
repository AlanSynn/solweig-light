# Source-bound observations and claim boundaries

Inspected checkpoint: e7a2d6ec8594b234820e7783e0ca26d821de7f3d, branch perf/claude-glm53-cpu-v5. Read through the GitHub connector on 2026-09-21. Only the relevant files/ranges were inspected; this is not a claim of a new exhaustive source audit or full local clone. Source blob identities and URLs are in SOURCES.md.

| Observation | Source anchor | Consequence / evidence class |
|---|---|---|
| Branch tip is e7a2d6ec, after handover a6a48dd8 | S01 | Continue actual branch; do not reset it. |
| Final protocol contains exactly dense1024 and vegetation1024, 24 time bands each | S02/S03 | Historical observation is two spatial scenes, not 24 tiles. |
| `thermal_comfort` calls preprocess, walls, standalone SVF, then run_utci_tiles | S04 | Geometry phase precedes simulation pool. |
| Standalone identity adds `construction='standalone-svf-v1'` and `standalone_implementation` | S05 | Native key differs from the unextended simulation geometry identity. |
| Simulation calls GeometryStore with plain `geometry_identity` when not explicitly trusting legacy | S06/S07 | Fresh complete workflow can produce geometry twice; count actual calls to characterize cost. |
| Store keys hash the complete identity, format/model/version; manifest equality checks the entire identity | S08 | The extra fields cannot be ignored by an existing cache hit. |
| Normalization in standalone producer and pipeline appears arithmetic-equivalent on the supported single-band own-met raster path | S05/S06 | Candidate common producer/key, not permission to assert equality for every malformed/low-level input. |
| In-process portfolio changes RuntimeOptions without demonstrably setting effective Numba masks | S09 | t2/t4 are not proven two/four native-thread measurements. |
| Anisotropic Lside returns the four ground terms after computing unused weights/wall terms | S10 | Demand-specific exact fast path, preserving failure/warning guard. |
| Cylinder TMRT is computed before adding cardinal patch diagnostics to returned fields | S11 | Private pipeline may project out unused cardinal diagnostics; public returns remain complete. |
| Cylinder shortwave consumes reduced columns 0..3 but allocates 20 and builds box directions | S12 | Narrow cylinder kernel; preserve seven returned fields. |
| G03 postprocessing is still Python/NumPy and evaluates Lup twice per direction | S13 | Actual expression hoisting and typed postprocess fusion remain opportunities. |
| Legacy export validation reads full NPZ for CRC; comparison later imports/reencodes NPZ and compares again | S05/S14 | Potential single stored-stream validation/comparison, not deletion of checks. |
| Native phase memory estimate retains three raw float32 cubes plus legacy full-plane equivalents | S15 | Stage-aware admission can improve capacity; observed RSS is not a hard bound. |
| R01a/G02/G03/S02/S07 already accepted, P01 regressed and is dormant | S16 | Do not count old work twice or revive the same failed design. |

## Historical observations, not new executions

Stored final records report dense1024 289.765 s and vegetation1024 302.396 s inside `thermal_comfort`, monitored combined wall 598.9 s, 10 output TIFF hash matches per scene, sampled RSS 1.07/1.13 GiB. Those are single-case executions on the earlier target host. This packet did not reproduce them. It did not verify every intermediate or state at 1024, and it did not run 24 real spatial tiles. The old narrative timing interpretation must yield to the actual harness timer boundaries: the timer encloses `thermal_comfort`, which contains preprocessing/standalone geometry.

The post-S07 256-square census is instrumented, source-bound historical diagnostic evidence, not current 1024 stage fractions or statistically calibrated speed predictions. Native execution may be charged to a Python wrapper; do not call its entire self-time Python overhead. Alternative routes at threads=1 and threads>1 further confound strong-scaling fits.

## Preparation-environment limitations

A direct HTTPS source materialization attempt failed with DNS resolution failure. No repository source file was downloaded into this packet from that attempt. No target source function is executed by the packet's unit tests. The numerical runtime needs GDAL; it is absent here. Any executed thread probe uses only a small standalone Numba workload and establishes nothing about the user's M1, source pipeline or provider routes.

## Required append-only scope correction

Create a new record in this continuation's evidence directory with actual original spatial count=2, steps=24, original timing paths, no deletion of old files, and original target count=24/unverified. Do not retroactively change the v5 protocol or hide the previous claim. A successful later 24-tile run gets its own protocol/source/manifest and one-observation label.
