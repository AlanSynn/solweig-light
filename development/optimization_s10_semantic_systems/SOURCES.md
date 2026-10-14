# Source map

All repository findings are bound to the immutable commit recorded below. A path is not proof of executed behavior; use its stated review scope.

Main: `90d72b50e6396bb0182db41598c9bd535dd9c487`. Old remote integration tip: `7abe526aae2f97e689b1a1e4ae183e5370f29aa1`.

- **S01** [main branch](https://api.github.com/repos/AlanSynn/solweig-light/branches/main): live-ref read.
- **S02** [perf/native-optimization branch](https://api.github.com/repos/AlanSynn/solweig-light/branches/perf/native-optimization): live-ref read.
- **S03** [src/solweig_light/radiation/materials.py](https://github.com/AlanSynn/solweig-light/blob/90d72b50e6396bb0182db41598c9bd535dd9c487/src/solweig_light/radiation/materials.py): complete function read.
- **S04** [src/solweig_light/data/landcoverclasses_2016a.txt](https://github.com/AlanSynn/solweig-light/blob/90d72b50e6396bb0182db41598c9bd535dd9c487/src/solweig_light/data/landcoverclasses_2016a.txt): table read in preceding review; pin unchanged.
- **S05** [src/solweig_light/pipeline.py](https://github.com/AlanSynn/solweig-light/blob/90d72b50e6396bb0182db41598c9bd535dd9c487/src/solweig_light/pipeline.py): setup and chronological loop read.
- **S06** [src/solweig_light/radiation/engine.py](https://github.com/AlanSynn/solweig-light/blob/90d72b50e6396bb0182db41598c9bd535dd9c487/src/solweig_light/radiation/engine.py): relevant longwave, daylight, promotion, state, dispatch ranges read.
- **S07** [src/solweig_light/radiation/cylinder_longwave.py](https://github.com/AlanSynn/solweig-light/blob/90d72b50e6396bb0182db41598c9bd535dd9c487/src/solweig_light/radiation/cylinder_longwave.py): typed guards, two sweeps and driver read in preceding review; pin unchanged.
- **S08** [src/solweig_light/_native_dispatch/lw_stream.py](https://github.com/AlanSynn/solweig-light/blob/90d72b50e6396bb0182db41598c9bd535dd9c487/src/solweig_light/_native_dispatch/lw_stream.py): plan, producer, slot and consumer read in preceding review; pin unchanged.
- **S09** [src/solweig_light/_native_dispatch/direct_aosoa.py](https://github.com/AlanSynn/solweig-light/blob/90d72b50e6396bb0182db41598c9bd535dd9c487/src/solweig_light/_native_dispatch/direct_aosoa.py): producer/classifier examined in preceding reviews; recheck local current implementation.
- **S10** [src/solweig_light/radiation/gvf_prepared.py](https://github.com/AlanSynn/solweig-light/blob/90d72b50e6396bb0182db41598c9bd535dd9c487/src/solweig_light/radiation/gvf_prepared.py): preparation, gate and mutation logic examined in preceding review; pin unchanged.
- **S11** [src/solweig_light/radiation/ground_view.py](https://github.com/AlanSynn/solweig-light/blob/90d72b50e6396bb0182db41598c9bd535dd9c487/src/solweig_light/radiation/ground_view.py): gather, mutation, prepared/fused/serial routes read in preceding review; pin unchanged.
- **S12** [src/solweig_light/geometry/sky_compiled.py](https://github.com/AlanSynn/solweig-light/blob/90d72b50e6396bb0182db41598c9bd535dd9c487/src/solweig_light/geometry/sky_compiled.py): schedules, bush/global states and absorption route read in preceding review; pin unchanged.
- **S13** [src/solweig_light/api.py](https://github.com/AlanSynn/solweig-light/blob/90d72b50e6396bb0182db41598c9bd535dd9c487/src/solweig_light/api.py): lines 1-220 read this review; remainder is continuation audit task.
- **S14** [src/solweig_light/identities.py](https://github.com/AlanSynn/solweig-light/blob/90d72b50e6396bb0182db41598c9bd535dd9c487/src/solweig_light/identities.py): complete file read.
- **S15** [src/solweig_light/persistence.py](https://github.com/AlanSynn/solweig-light/blob/90d72b50e6396bb0182db41598c9bd535dd9c487/src/solweig_light/persistence.py): lines 1-235 read this review; transaction remainder must be inspected before changes.
- **S16** [src/solweig_light/runtime_memory.py](https://github.com/AlanSynn/solweig-light/blob/90d72b50e6396bb0182db41598c9bd535dd9c487/src/solweig_light/runtime_memory.py): lines 430-575 read this review; runtime admission previously examined.
- **S17** [src/solweig_light/preprocessor.py](https://github.com/AlanSynn/solweig-light/blob/90d72b50e6396bb0182db41598c9bd535dd9c487/src/solweig_light/preprocessor.py): lines 1-210 read this review; forcing-specific body remains local audit.
- **S18** [src/solweig_light/geometry/service.py](https://github.com/AlanSynn/solweig-light/blob/90d72b50e6396bb0182db41598c9bd535dd9c487/src/solweig_light/geometry/service.py): lines 1-245 read this review; publication continuation must be inspected.
- **S19** [src/solweig_light/geometry/visibility.py](https://github.com/AlanSynn/solweig-light/blob/90d72b50e6396bb0182db41598c9bd535dd9c487/src/solweig_light/geometry/visibility.py): consumer/export interfaces established in prior review; inspect full selected codec before mutation.
- **S20** [src/solweig_light/runtime.py](https://github.com/AlanSynn/solweig-light/blob/90d72b50e6396bb0182db41598c9bd535dd9c487/src/solweig_light/runtime.py): runtime options, masks, pool and admission read in preceding review; pin unchanged.
- **S21** [development/optimization_n9_final/FINAL_SELECTION.json](https://github.com/AlanSynn/solweig-light/blob/90d72b50e6396bb0182db41598c9bd535dd9c487/development/optimization_n9_final/FINAL_SELECTION.json): terminal record read in preceding review; pin unchanged.
- **S22** [development/docs/optimization_campaigns.md](https://github.com/AlanSynn/solweig-light/blob/90d72b50e6396bb0182db41598c9bd535dd9c487/development/docs/optimization_campaigns.md): accepted/rejected map read in preceding review; pin unchanged.
- **S23** [src/solweig_light/comfort/utci.py](https://github.com/AlanSynn/solweig-light/blob/90d72b50e6396bb0182db41598c9bd535dd9c487/src/solweig_light/comfort/utci.py): call-site reviewed; polynomial internals require local selected-path audit.
- **S24** [src/solweig_light/comfort/wbgt.py](https://github.com/AlanSynn/solweig-light/blob/90d72b50e6396bb0182db41598c9bd535dd9c487/src/solweig_light/comfort/wbgt.py): call-site reviewed; solver internals require local selected-path audit.
- **S25** [src/solweig_light/radiation/wall_shadows.py](https://github.com/AlanSynn/solweig-light/blob/90d72b50e6396bb0182db41598c9bd535dd9c487/src/solweig_light/radiation/wall_shadows.py): call-site and exact_13/exact_23 read in preceding review; inspect selected implementation.
- **S26** [src/solweig_light/geometry/svf.py](https://github.com/AlanSynn/solweig-light/blob/90d72b50e6396bb0182db41598c9bd535dd9c487/src/solweig_light/geometry/svf.py): patch loop and export paths read in preceding review; pin unchanged.
- **S27** [src/solweig_light/radiation/patch_radiation.py](https://github.com/AlanSynn/solweig-light/blob/90d72b50e6396bb0182db41598c9bd535dd9c487/src/solweig_light/radiation/patch_radiation.py): reference/compile dispatch and classification helpers read in preceding review.
- **S28** [src/solweig_light/radiation/_math_profile.py](https://github.com/AlanSynn/solweig-light/blob/90d72b50e6396bb0182db41598c9bd535dd9c487/src/solweig_light/radiation/_math_profile.py): profile use reviewed; full selected math implementation is local prerequisite.
- **S29** [src/solweig_light/geometry/recipe.py](https://github.com/AlanSynn/solweig-light/blob/90d72b50e6396bb0182db41598c9bd535dd9c487/src/solweig_light/geometry/recipe.py): shared-recipe call sites verified; inspect full recipe before identity changes.
- **S30** [src/solweig_light/io/rasters.py](https://github.com/AlanSynn/solweig-light/blob/90d72b50e6396bb0182db41598c9bd535dd9c487/src/solweig_light/io/rasters.py): writer interfaces reviewed; inspect serialization implementation before changes.

## Primary technical sources

- **E01** [NumPy promotion](https://numpy.org/doc/2.2/reference/arrays.promotion.html), accessed 2026-10-13.
- **E02** [LLVM floating-point semantics](https://llvm.org/docs/LangRef.html), accessed 2026-10-13.
- **E03** [Numba threading layer](https://numba.readthedocs.io/en/stable/user/threading-layer.html), accessed 2026-10-13.
- **E04** [GDAL thread ownership](https://gdal.org/en/stable/user/multithreading.html), accessed 2026-10-13.
- **E05** [GDAL read-only thread safety](https://gdal.org/en/stable/development/rfc/rfc101_raster_dataset_threadsafety.html), accessed 2026-10-13.
- **E06** [FlashAttention original paper](https://arxiv.org/abs/2205.14135), accessed 2026-10-13.
- **E07** [Claude Code subagents](https://code.claude.com/docs/en/sub-agents), accessed 2026-10-13.
- **E08** [Claude Code teams](https://code.claude.com/docs/en/agent-teams), accessed 2026-10-13.
- **E09** [Z.ai Claude configuration](https://docs.z.ai/devpack/tool/claude), accessed 2026-10-13.
- **E10** [MLX data types](https://ml-explore.github.io/mlx/build/html/python/data_types.html), accessed 2026-10-13.
