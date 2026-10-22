# Contributing to solweig-light

## Scope and references

solweig-light is a CPU implementation of SOLWEIG with a minimal own-met
TIFF-to-TIFF runtime. Read [README.md](README.md) and the relevant page in
[docs/](docs/) for current architecture and usage; historical campaign plans are
not active instructions.

The frozen behavioral reference is `nvnsudharsan/SOLWEIG-GPU` commit
`0d7fe742abeeddd890dd58fc76ed7f78bd47faec`. Comparing newer upstream source does
not change that numerical reference. The acceptance authority is
`development/benchmarks/protocols/comparison_v1.json`; preserve its frozen gates.
Known limitations belong in [docs/model_deviations.md](docs/model_deviations.md).

## Public contracts

Preserve these seven workflows and their argument semantics:
`thermal_comfort`, `preprocess`, `build_inputs`, `build_wind_ext_coeff`,
`run_walls_aspect`, `calculate_svf`, and `run_utci_tiles`.

- Preserve accepted inputs, CLI behavior, artifact names, GeoTIFF metadata,
  masks, timestamps, and legacy export schemas unless a versioned policy
  explicitly changes them.
- The normal namespace is `solweig_light`. Only the separately installed
  compatibility distribution owns `solweig_gpu` and the legacy executable;
  it must reject an ambiguous installation with upstream.
- The own-met numerical core must run without Torch, CUDA, network access,
  or optional acquisition dependencies. Keep optional integrations lazy.
- A future GPU backend must share these contracts and preserve chronological
  state; GPU execution is not currently a supported solweig-light backend.

## Numerical behavior

Optimization must preserve the physical workload: logical extent, resolution,
sky patches, timesteps, ray support, vegetation, forcing, radiation components,
and required outputs. Do not replace the model with an isotropic shortcut,
surrogate, or lookup approximation under the default API.

- Use `fastmath=False` for compiled kernels. Establish reference parity before
  parallelization or arithmetic changes. Check dtype promotion, conversions,
  rounding, signed zero, NaNs, min/max, division, comparison boundaries, and
  reduction order. Algebraic similarity is not numerical evidence.
- Preserve shadow samples, first steps, termination, global bush predicates,
  vegetation ordering, wall quantities, slicing, and borders. An early exit
  must preserve every output, not just one settled field.
- Pack only channels proven exactly binary. Other visibility values require
  lossless categorical storage or a lossless fallback. Legacy exports must
  round-trip exactly to the required schema.
- Preserve inherited constants and behavior, including canopy transmission,
  wind floors, UHI placement, WBGT branches, altitude, land-cover normalization,
  and timezone handling. Scientific corrections need an explicit versioned
  policy, separate tests, and a reference report.
- Preserve supported failure behavior and documented upstream quirks. Do not
  hide model changes inside a performance refactor.

## Execution and ownership

Timesteps depend on carried thermal state. Parallelize independent pixels,
blocks, or logical tiles; do not parallelize dependent timesteps.

- Execution blocks are internal memory/locality units. They must not change
  logical tile extent, overlap, solar position, forcing, geometry context, or
  output extent and metadata.
- Give each writable raster and output block one owner. Never overwrite data
  while neighboring work can still read it; use separate buffers or barriers.
  Reductions and packed-word writes need deterministic ownership.
- Bound worker processes, native threads, writer queues, scratch arrays, and
  mapped payloads together. Memory admission may reject work, never silently
  shrink physical domains or reduce fidelity.
- Stream output bands when the model no longer needs them. An unsaved output
  may still be a required model intermediate; do not skip its computation.
- Cache only values with complete dependency identities. Dynamic shadows,
  ground-view radiance, material temperatures, forcing, and chronological
  state are not static merely because geometry is unchanged.
- Cache and publication paths must detect stale inputs, corruption, incomplete
  writes, and concurrent owners. Keep transactional completion, safe mapped
  lifetimes, and complete checkpoint state.

## Verification and evidence

Never generate an upstream golden from solweig-light. Keep reference and
candidate environments isolated, including the compatibility distribution.
Label original CPU, original CUDA, patched upstream, independent scientific,
and candidate evidence separately. Unavailable hardware is not a passed check.
Record unmodified upstream failures. Retain any necessary reference repair as
an explicit patch with its hash and label the resulting outputs accordingly.
Investigate CPU/CUDA disagreement rather than choosing the favorable result.

Compare affected intermediates as well as final comfort outputs: normalization,
geometry and visibility, directional radiation, temperature/delay state,
TMRT/UTCI/WBGT, masks, timestamps, metadata, and cache/export round trips.
Keep a genuine CPU-only own-met TIFF-to-TIFF integration gate without numerical
pipeline mocks or unconditional skips. Ordinarily it runs in PR CI; the user's
task instructions govern CI changes and execution.
For changes to concurrency or persistence, cover relevant thread/block/worker
settings, cold/warm caches, stale/corrupt data, interruption, and restart.

Do not relax frozen tolerances, remove difficult fixtures, add unconditional
skips, or redefine a benchmark after a failure. Preserve `tests/reference/`
and its provenance. Optional-service mocks must be labeled; they are not
live-service validation. Check installed distributions when packaging changes.

Performance comparisons must do equal work and match cache conditions.
Distinguish first use, geometry-cold, geometry-warm, and kernel-only timing.
Record source/input hashes, environment, hardware, threads, invocation, raw
trials, failures, process-tree memory, and uncertainty. Claims about upstream
CPU or CUDA need measurements of the relevant reference configuration;
a kernel improvement alone does not establish an end-to-end speedup.

Keep bulk evidence outside Git. Preserve the small manifests, frozen protocols,
and test-coupled fixtures needed to reproduce or verify claims. See
[development/README.md](development/README.md) for the retained evidence map.
Do not rewrite repository history or recreate archived bulk-evidence commits.

## Working practices

Use small, coherent changes and the smallest meaningful tests during iteration;
run the affected integration and contract checks before declaring completion.
Inspect failures and fix their cause instead of weakening the gate. Report
missing evidence, unsupported paths, and scientific limitations explicitly.

Delegate independent work with exact file ownership, invariants, and completion
criteria. Workers should return changed files, commands, results, failures, and
measurement paths, not transcripts. Avoid repeated broad scans and status
polling. Keep instructions and documentation about current durable contracts;
put one-off evidence in its existing archive rather than adding new hierarchies.

Local inspection, edits, isolated environments, fixtures, tests, profiling, and
repairs are authorized within the assigned task. Remote publication, destructive
operations, and scientific-policy changes require user authorization; carry
forward authorization already given in the session. Escalate unresolved policy
conflicts, unavailable required services/hardware, or a need to weaken a frozen
gate. Follow the user's instructions on CI and publication.
