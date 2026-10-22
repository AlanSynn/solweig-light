# Runtime, memory and recovery

## Controls

`RuntimeOptions` is immutable and scoped to the calling context with
`runtime_options(...)`. It does not change the seven workflow signatures.
The source of truth is [runtime.py](../src/solweig_light/runtime.py).

| Option | Default | Purpose |
| --- | --- | --- |
| `cpu_budget` | `1` | Available CPU slots for admitted work. |
| `workers` | `1` | Upper bound on independent tile workers. |
| `threads_per_worker` | `1` | Native threads per tile worker. |
| `block_pixels` | `128` | Internal radiation buffer/locality size. |
| `memory_budget_bytes` | `None` | Explicit admission budget, or the conservative automatic budget. |
| `resident_lw_masks` | `True` | Reuse static longwave predicates across a tile's timesteps. |
| `cache_dir` | `None` | Override the native geometry cache directory. |
| `cache_enabled` | `True` | Permit native cache reuse. |
| `legacy_cache_policy` | `"recompute"` | Recompute when legacy dependency provenance is missing; `"trust"` explicitly accepts that missing provenance. |
| `checkpoint_interval` | `1` | Number of steps between durable state checkpoints. |
| `resume` | `False` | Resume a compatible committed transaction. |

Native threads must fit the CPU budget and available CPU count. Admission
bounds active workers and aggregate reservations; increasing `workers` does
not guarantee that every requested worker can run concurrently. Independent
tile jobs use processes with thread settings established before numerical
imports. Within a tile, blocks/pixels are parallel and timesteps are ordered.

## Resident longwave predicates

This is the fastest validated exact longwave setting from
[PR #3](https://github.com/AlanSynn/solweig-light/pull/3): on its generated
600×600, 19-step, 153-patch workload with eight threads and one worker,
median workflow time fell from 26.79 s to 22.59 s with bitwise-equal results.
Four interleaved trials per setting used fresh geometry/outputs and warmed
JIT. This supports the default choice, not a universal speedup guarantee.

The default caches four exact visibility predicates in a single uint8 for each
padded pixel/patch position. The predicates depend only on the tile's leased
static visibility channels. They are created lazily, read-only during reuse,
and released when the tile scope ends. Dynamic thermal values and solar
classification still run each step.

The extra allocation is exactly `ceil(N / 32) * 32 * P` bytes per tile, where
`N = rows * columns` and `P` is patch count:

| Tile | Patches | Bytes | MiB |
| --- | ---: | ---: | ---: |
| 600×600 | 153 | 55,080,000 | 52.53 |
| 1200×1200 | 153 | 220,320,000 | 210.11 |
| 2400×2400 | 153 | 881,280,000 | 840.45 |

This is additional memory, not the total tile reservation. Opt out explicitly
when the memory/reuse tradeoff is unsuitable:

```python
from solweig_light import RuntimeOptions, runtime_options, thermal_comfort

with runtime_options(RuntimeOptions(resident_lw_masks=False)):
    thermal_comfort(
        base_path="/absolute/path/to/scene",
        selected_date_str="2020-07-18",
        own_met_file="/absolute/path/to/scene/met.txt",
        ERA_5_z0_find=False,
    )
```

Both settings execute the same model. Preflight includes the resident
allocation when enabled; it does not silently disable it, reduce patches or
shrink the logical tile to make a job fit.

## Memory admission

Admission runs before cold geometry production and before tile execution,
using raster metadata and the actual patch count. The automatic budget is
half the smallest available view of physical RAM, available host RAM and
finite container memory headroom, including cgroup ancestors. Exhausted
headroom rejects work. Budgets are estimates at admission time; they are not
operating-system RSS limits and cannot reserve RAM against other processes.

[runtime_memory.py](../src/solweig_light/runtime_memory.py) owns phase-aware
accounting. The conservative inventory includes static scene arrays,
chronological state, radiation/GVF scratch, dtype promotions, outputs,
directional wind fields, visibility, native/JIT overhead and active workers.
Phase-specific reservations account for live buffers; geometry-only
admission can still be conservative. Detailed allocation formulas belong to
that source inventory. Resident predicates are an additional explicit term.
Advanced direct scheduler jobs must provide shape or DSM metadata for
resident-mask accounting, even when they supply `memory_estimate_bytes`;
otherwise explicitly opt out with `resident_lw_masks=False`. Public
`run_utci_tiles` already supplies the required DSM metadata.

Wind generation has its own [resource inventory](../src/solweig_light/wind_resources.py):
expanded forward and inverse rotations, height-dependent wake ramps, tree
footprints, smoothing, writer scratch and active directions. It never
truncates wake support to fit a budget. Only admitted futures are live, one
writer owns output datasets, and completed direction arrays are released.
`max_workers` adds a bound to the runtime controls.

A rejected request needs a suitable budget or an explicit user choice of a
smaller logical problem. Admission never changes resolution, overlap,
forcing, rays, patch count or model physics automatically.

## Geometry cache and legacy exports

Native geometry lives under `<preprocess_dir>/.solweig-light/cache` unless
overridden; the default preprocessing directory is `<base_path>/processed_inputs`.
Identities hash raster contents and metadata, patch arrays/order,
normalization, implementation sources, dependencies and the math profile.
Standalone and thermal geometry share one numerical recipe and native cache
key; export-operation provenance is separate. Checksummed immutable generations publish via a
completion manifest; per-key advisory locks coordinate concurrent requests.
Old generations may remain so active mapped readers stay valid.

This differs from latest upstream's [standalone existence check](https://github.com/nvnsudharsan/SOLWEIG-GPU/blob/1fec79a78002f0c7f3f4af817ce34d1952d8b8f3/solweig_gpu/solweig_gpu.py#L362-L374)
and [thermal legacy cache check/load](https://github.com/nvnsudharsan/SOLWEIG-GPU/blob/1fec79a78002f0c7f3f4af817ce34d1952d8b8f3/solweig_gpu/utci_process.py#L234-L320):
those paths use the presence of the expected artifact set, which alone cannot
establish that source geometry is current.

The default `legacy_cache_policy="recompute"` refuses to treat missing
provenance as validated geometry. `"trust"` explicitly permits loading legacy
geometry without dependency identity, while retaining schema, dimensions and
spatial checks. Trusted content hashes enter checkpoint identity.

Standalone `calculate_svf(..., overwrite=False)` validates matching manifests,
content hashes and schemas. Without provenance it obtains current native
geometry and compares every decoded legacy value exactly. Equal exports are
preserved and receive a validation manifest; unequal or malformed complete
sets are preserved and raise an error requesting `overwrite=True`. A partial
set is regenerated. Thermal execution can recompute valid native geometry
while preserving unverified legacy exports.

`overwrite=True` stages and validates the complete TIFF/ZIP/NPZ set before
replacement. Destination locks exclude competing writers; completion
manifests publish last. Ordinary failures roll back replaced files. A process
crash can leave mixed files, which hashes/manifests prevent accepting as a
complete generation. New NPZ compression is lossless DEFLATE level 3;
compression bytes are not part of semantic equality.

Sources must stay stable during a call. Content checks around identity,
computation and publication reject detected mutations; they are not atomic
filesystem snapshots or locks on external editors.

## Checkpoints and output publication

Transactions live under `<base_path>/.solweig-light/transactions`. Each
checkpoint commits flushed output progress and complete carried state,
including thermal/delay maps, scalars and water temperature. After an
interruption, repeat the same inputs, date and output options under
`RuntimeOptions(resume=True)`. Only a committed boundary resumes; unfinished
bands are replayed. Operational CPU, block and memory settings may change.

Mismatched/corrupt checkpoints are rejected, including incompatible math or
implementation fingerprints. A completed resume validates published files.
A normal fresh call can replace a validated complete run; it does not silently
discard incomplete work. Per-destination locks give each writable dataset one
owner. Only the final completion manifest certifies the complete requested
file set: individual file renames cannot be atomic as a group.
