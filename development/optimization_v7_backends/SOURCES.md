# Source ledger

Official docs were checked during this packet preparation unless noted as inherited survey references. Moving documentation does not identify the installed release. Implementation proposals are our design, not performance claims by these sources. No framework benchmark was run here.

## [R01] Branch metadata checked

https://api.github.com/repos/AlanSynn/solweig-light/branches/perf/cpu-optimization

Checked tip 7a37a6f5; must resolve actual local HEAD at execution.

## [R02] Nominated longwave kernel

https://github.com/AlanSynn/solweig-light/blob/7a37a6f59924aa4c13444c977991d7f731ba5e8e/src/solweig_light/radiation/cylinder_longwave.py

Observed blob 27ba6ce4; two sweeps, ten accumulators, seven columns.

## [R03] v6 handover

https://github.com/AlanSynn/solweig-light/blob/4689421c81a9dc9ad5e047bd7ff1dcdd704483b9/optimization_v6_continue/evidence/handover/HANDOVER_C6-103.md

Prior source-read history; dev-tier observations, rejected prepared decoder, actual-target gap.

## [F01] Dr.Jit control flow

https://drjit.readthedocs.io/en/latest/cflow.html

Symbolic versus evaluated loops; avoid Python-for graph unrolling.

## [F02] Dr.Jit API

https://drjit.readthedocs.io/en/latest/reference.html

FastMath default; explicit LLVM; thread_count/set_thread_count; eval/synchronization. Verify installed version.

## [F03] ISPC guide

https://ispc.github.io/ispc.html

Uniform/varying SIMD; disable-fma; unsafe math and masked-load caveats. Pin compiler.

## [F04] Highway project

https://github.com/google/highway

Portable SIMD with runtime dispatch; actual target qualification still needed.

## [F05] Dr.Jit benchmarking

https://drjit.readthedocs.io/en/latest/bench.html

Distinguish device events from full host result boundary.

## [F06] PyOpenCL docs

https://documen.tician.de/pyopencl/

Binding versus executing device runtime; prior survey source.

## [F07] PoCL usage

https://portablecl.org/docs/html/using.html

Runtime and device options are versioned; inspect pinned build for actual pool controls.

## [F08] OpenCL C

https://registry.khronos.org/OpenCL/specs/unified/html/OpenCL_C.html

FP_CONTRACT default ON and float capability rules; strict flags are not parity proof.

## [F09] MLX compilation

https://ml-explore.github.io/mlx/build/html/usage/compile.html

Compilation semantics and asynchronous evaluation; test selected installed release.

## [F10] Numba threading

https://numba.readthedocs.io/en/stable/user/threading-layer.html

Configured pool and actual mask, set before numerical import where required.

## [C01] Claude Code subagents

https://code.claude.com/docs/en/sub-agents

Version-dependent agent file schema/model precedence; use installed supported features.

## [C02] Z.ai Claude Code routing

https://docs.z.ai/devpack/tool/claude

Claude aliases can map to GLM; real Opus must not be inferred from alias.

## [G01] Git worktree

https://git-scm.com/docs/git-worktree

Detached worktrees at an explicit immutable base without new branch.
