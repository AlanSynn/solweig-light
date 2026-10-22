# Execution architecture and optimizations

## Comparison scope

The source comparison is against SOLWEIG-GPU commit
[`1fec79a78002f0c7f3f4af817ce34d1952d8b8f3`](https://github.com/nvnsudharsan/SOLWEIG-GPU/tree/1fec79a78002f0c7f3f4af817ce34d1952d8b8f3).
Its public driver still uses Torch-based geometry and thermal calculations,
selecting CUDA when available and CPU otherwise. SOLWEIG-light supplies CPU
NumPy/Numba implementations with a different memory and execution strategy.
The numerical oracle remains the older frozen revision described in
[provenance](provenance.md); this source inspection is not a latest-upstream
numerical or performance comparison.

## Pipeline and ownership

[api.py](../src/solweig_light/api.py) coordinates preprocessing, walls/aspects,
geometry preparation and tile execution. [preprocessor.py](../src/solweig_light/preprocessor.py)
retains logical tile, overlap, forcing and timestamp semantics.
[runtime.py](../src/solweig_light/runtime.py) admits jobs and starts worker
processes with native-thread limits in place, including the one-worker case.

A **logical tile** defines the model domain. An **execution block** is an
internal buffer/locality unit inside that domain. Changing `block_pixels`
does not change overlap, solar location, forcing aggregation, raster extent,
ray support or sky-patch count. Independent pixels and tiles can run in
parallel; timesteps within a tile cannot.

[pipeline.py](../src/solweig_light/pipeline.py) prepares static fields, then
advances the radiation engine in meteorological order. Temperature/delay maps,
first-day flags, water temperature and scalar state pass to the next step.
Requested bands stream to transaction files after use; completed raster
histories are not retained in RAM. Checkpoints contain carried state as well
as output progress. [Runtime](runtime.md) explains publication and restart.

## Where work is reduced

| Component | Implementation and preserved behavior |
| --- | --- |
| Rays and walls | [Compiled sky rays](../src/solweig_light/geometry/sky_compiled.py) and [wall shadows](../src/solweig_light/radiation/wall_shadows.py) remove Python/tensor dispatch while preserving sample rounding, ray termination, bush predicates, slice updates and wall quantities. Unsupported profiles retain the characterized fallback. |
| Visibility storage | [Visibility encoding](../src/solweig_light/geometry/visibility_encode.py) uses binary or categorical packing where lossless. General values retain raw float32 storage. Combined vegetation/building visibility can equal 2, so Boolean conversion is invalid. Consumers decode bounded regions instead of expanding three complete pixel×patch arrays. |
| SVF accumulation | [svf.py](../src/solweig_light/geometry/svf.py) counts admitted binary masks by altitude band, groups equal count patterns and replays the original ordered float32 additions. It avoids repeating the same accumulation per pixel without replacing it with count×weight multiplication. Nonbinary cases use ordered replay. |
| Longwave and shortwave | [Cylinder LW](../src/solweig_light/radiation/cylinder_longwave.py), [cylinder SW](../src/solweig_light/radiation/cylinder_shortwave.py) and private [LW](../src/solweig_light/_native_dispatch/lw_batch.py)/[SW](../src/solweig_light/_native_dispatch/sw_batch.py) schedules fuse bounded decoding and reduction. Pixel lanes process patches in the original order; one parallel block owner prevents shared accumulator writes. Admission checks descriptors, layout, categorical modes and numeric ranges before selecting lane kernels. Exceptional inputs retain strict leaves. |
| Resident LW predicates | Static sky, vegetation, building and reflection predicates are computed once from the tile's exact visibility owners and reused across steps. Four predicate bits share one uint8 per padded pixel/patch position. No forcing-dependent radiance or sun/shade classification is cached. The cache ends with the tile scope. |
| Ground-view factors | [Prepared GVF](../src/solweig_light/radiation/gvf_prepared.py) and [batched gather](../src/solweig_light/radiation/gvf_batch.py) prepare reusable geometry/schedules and process owned row blocks. Dynamic temperature, shadow and radiance work still runs each step. Scratch history, water-temperature mutation and directional order retain their compatibility semantics. |
| Anisotropic reductions | [patch_radiation.py](../src/solweig_light/radiation/patch_radiation.py) reduces packed visibility directly and shares static patch geometry. Demand-specific cylinder paths avoid constructing return fields unused by the calling engine, while preserving model-required components and public full-return paths. |
| Geometry reuse and I/O | Content-addressed geometry avoids repeated valid work. Separate export controls omit compatibility serialization when requested. Legacy schemas remain available; new NPZ exports use lossless DEFLATE level 3. |

These mechanisms do not reduce resolution, timesteps, patches, rays,
vegetation, radiation components or chronological state. Default thermal
geometry uses the same 153-patch workload. Arithmetic order and strict patch
classification matter: mathematically equivalent rewrites can change an
observable boundary. See [compatibility](compatibility.md#numerical-contract).

Resident LW predicate reuse is the default. It adds exactly
`ceil(N / 32) * 32 * P` bytes per tile for `N` pixels and `P` patches;
[its memory tradeoff and opt-out](runtime.md#resident-longwave-predicates)
are explicit. It changes reuse, not the physical model.

## Backend boundary and future GPU work

The implemented runtime is CPU-only. Public workflows, tile orchestration,
geometry storage and numerical families already have separate modules; a
future GPU backend could target those numerical boundaries while retaining
resource, cache, chronology and output contracts. There is no implemented
CUDA backend, device-resident pipeline, GPU scheduler or general GPU backend
interface. Adding one requires implementation and independent numerical and
resource validation.

A future implementation should keep static geometry and carried state on the
device across timesteps, transferring requested bands at the writer boundary.
Device-memory admission and buffer ownership must be explicit, and numerical
validation must cover intermediate fields as well as final UTCI. Keep device
dependencies optional so the CPU-only installation remains usable.

The optional ISPC longwave backend is also a CPU backend. It is selected with
`SOLWEIG_LIGHT_LW_BACKEND=native`; the default route is Numba. Its reviewed
admission checks retain Numba fallback for unsupported inputs, while a missing
ISPC build toolchain raises an error. Builds use
`~/.cache/solweig-light/native` (override with `SOLWEIG_LIGHT_NATIVE_CACHE`).
This specialized backend is not required for the default optimizations.
