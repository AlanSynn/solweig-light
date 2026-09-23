# M4 run notes (2026-09-21, commit e7a2d6ec)

Command (executed from `/Users/alansynn/Workspace/solweig-light-v6-mem/optimization_v6_continue/evidence/memory`):

```
PYTHONPATH=/Users/alansynn/Workspace/solweig-light-v6-mem/src \
  /Users/alansynn/Workspace/solweig-light/.venv-light/bin/python m4_run.py m4_instrumented_run.json
```

- Executes the worktree's own `src/` (`e7a2d6ec`), in-process `run_utci_tiles`, 35x32 reference tile, 24 steps, 1 thread, `block_pixels=128`, `memory_budget_bytes=4 GiB`. Numerics unmodified; run dir was a cleaned system-temp copy.
- Host check before run: no other agent python/pytest processes (`ps -axo pcpu=,comm=`).

## Results and reading

| Metric | Value |
|---|---|
| wall | 14.813 s (includes numba first-import/JIT) |
| tracemalloc peak | 64.6 MiB |
| RSS peak (sampled, ru_maxrss) | 219.4 MiB |
| RSS end | 256.8 MiB |

Interpretation (limitation stated honestly): at 35x32 the tile arrays are ~940x smaller than 1024x1024, so this run **cannot** validate M2's 1024-scale peaks. Its two real findings:

1. **Baseline process overhead ≈ 0.22-0.26 GiB** (interpreter + numba/LLVM + GDAL libs before any tile-scale array) — corroborates M2 §6(f)'s parent-footprint estimate of ≈ 0.2-0.4 GiB and confirms the 750 MiB `native` allowance has real library weight behind it.
2. Top tracemalloc sites are import machinery (`importlib._bootstrap_external:729` = 22.7 MiB of code objects) because tracing started before the first package import — i.e. fixed startup cost, not per-timestep allocation. No leak signature: `tracemalloc_end` (55.1 MiB) < peak, consistent with the per-job `gc.collect()` retirement rule (`runtime_worker.py:85`).

Scale-linear caveats per VALIDATION_POLICY: RSS sampling is supporting evidence only; this is an L1-scale observation, not an admission bound.
