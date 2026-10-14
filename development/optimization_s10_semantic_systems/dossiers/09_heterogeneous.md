# D09: CPU/GPU/backend exploration after coverage repair

Candidates H01-H08. Design is architecture-agnostic; implementation portfolio is intentionally small. No backend installation contest and no automatic revival of N9 native default.

## Admission by complete execution region
Compare best CPU A/B against GPU region time:

    prepare + JIT amortization + layout conversion + H2D + launches
    + device work + required D2H + synchronization + CPU remainder

Initial region might be exact longwave predicates/typed contribution tables plus both ordered sweeps. A wider region may retain geometry and chronological state, but must preserve every required output/checkpoint step. Do not copy to/from GPU once per patch or 128-pixel block. Chronological state can remain device-owned; it cannot execute future dependent timesteps concurrently.

## I/O-aware computation
FlashAttention is a methodological analogy: trade cheap local work for fewer slow-memory traversals, tile data into fast memory, avoid giant intermediates. It does NOT prove SOLWEIG's equality or predict a speed multiplier. Fused kernels can spill registers and lose occupancy. Compare medium fusion regions with split kernels; record on-chip/global bytes, transfer bytes, compile time and synchronization.

One work-item owning one receiver and iterating patches in original order is an initial exact mapping. Do not turn the patch loop into a warp tree reduction. Shared/local-memory tiles must honor barriers and tail lanes. Use one output owner. Compact geometry can be decoded on device if integer/error semantics match; do not expand all tiles into dense cubes to satisfy a GPU array interface.

## Numerical profile is decisive
The standard singleton path may produce different sun and shade precision. A source float32 output does not prove all arithmetic is float32. Original float64 contribution added in float64 then cast to float32 cannot be replaced by pre-rounding the coefficient. Apple/MLX GPU support for float64 is limited/absent according to inspected MLX docs, so probe actual backend capability and either retain the affected component on CPU, use a capable device, or decline that profile. No software FP64 emulation project unless a measured cost model justifies it.

Keep SLEEF/NumPy-sensitive coefficient/classification preparation on CPU initially. This can still lose if masks require transferring huge arrays. Derive transferred bytes explicitly. Disabling FastMath is necessary but not sufficient; verify FMA, denormals, signed zero, library functions and original dtype rounding. No new tolerance policy without separate approval.

## Framework portfolio
- Existing Numba remains the required A and strongest changed-layout B.
- A CPU native SIMD backend is conditional on material residual coverage and new broad producer/consumer design, not an old leaf rerun.
- For Apple GPU, inspect Metal/custom MLX capability and exact profile.
- For cross-vendor GPU, inspect OpenCL/PoCL or SYCL backend actually available on target.
- For NVIDIA-specific deployment, CUDA/Triton may be an optional named hardware experiment.
- Dr.Jit/Halide/other compilers only when control-flow/regularity matches the measured residual.

At most ONE accelerator implementation enters the first qualification cycle. Other candidates receive evidence-based defer/reject dispositions. CPU-only import, install and seven workflows must continue without them. Runtime device availability is not a performance certificate. No hidden toolchain download, credentials or new paid services.

## Capacity and overlap
Reserve host/device static+state+scratch+queue+runtime with headroom. Unified memory shares bandwidth and pressure; it is not zero-cost. Overlap transfer and compute only for independent leased buffers, with timing that waits for actual completion. Multi-GPU requires distinct logical tile ownership, ordered publication and shared-host I/O accounting.

## Promotion
Only a named device/profile with measured end-to-end gain, exact allowed-domain parity, bounded memory, clean installed DX and actual execution counters may be selected. Unsupported cases retain CPU. Broader platform portability remains unverified until executed there. A GPU win is reported separately from same-hardware CPU-only code speedup.
