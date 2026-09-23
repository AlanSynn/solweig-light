# D04: PyOpenCL + real PoCL CPU

## Eligibility

PyOpenCL is a binding, not the executing CPU implementation [F06,F07]. Locate an existing usable CPU OpenCL device or build an isolated user-space PoCL runtime without modifying system ICD/driver configuration. Record platform/vendor/device, runtime and compiler versions, device type bitfield, OpenCL C version, fp64/fp32 capabilities, endian, allocation/global-memory limits and build options. An installed Python package with no CPU device is unavailable.

Never use an auto context that picks a GPU. Select a named CPU device and record its identity. Treat CPU-first and any future GPU result as distinct campaigns. Apple system OpenCL is not a portable long-term deployment guarantee; do not install/replace drivers to make the probe pass.

## Kernel mapping

One work-item owns one pixel. Its private accumulators execute the original patch sequence twice. In the initial port, arrays are accepted decoded values and masks, and trig/sky-coefficient preparation stays on the current CPU path. Match B's layout and include any transposition. Use a bounded global work size with `if (pixel >= B) return`; never rely on padded input reads being valid.

fp64 is needed if the captured scalar/operation profile needs double intermediates. Query support and compile explicitly; otherwise fall back that profile. Use the original literal bit patterns and conversion rounding. No `native_*`, relaxed-math, unsafe-math, finite-math-only, no-signed-zeros, denorms-are-zero or approximate divisions. OpenCL C specifies FP_CONTRACT default ON, so require `#pragma OPENCL FP_CONTRACT OFF` with verified build behavior [F08]. Explicit fma is allowed only where the source graph already has it; the initial reducer needs no new fma.

Check the device's rounding, denormal, infinity/NaN and division behavior through actual targeted kernels, not flags alone. OpenCL vector `select` semantics and Boolean representation differ from Python; use typed predicates and retain multiply-by-mask behavior when that is the source operation. Build failures and warnings are retained.

## CPU cost and thread pool

The runtime schedules work-items onto a CPU pool and may vectorize groups. This can add overhead to already efficient Numba. Query/log the **pinned PoCL runtime's actual supported thread-count control**, then verify behavior. Do not assume a historical environment variable name is recognized. CPU affinity may be unavailable on macOS; absence is explicit, not silently treated as a cap.

Only the selected CPU device's work counts as CPU backend time. Dormant GPU devices must not be initialized for primary runs. Kernel queue tasks, host packing, Numba prep and IO writer activity together fit the shared CPU budget.

## Host memory and timing

Start with ordinary explicit buffer upload/download so costs are visible. `CL_MEM_USE_HOST_PTR` is not a portable zero-copy guarantee. A pinned-host-memory or shared virtual memory experiment is separate and requires alignment, coherent ownership and lifetime proofs.

Retain queue/program/context for a worker with complete build/device/source/FP-option identity, not per block. Use events/queue completion to wait for readback before the adapter returns. Report host total and kernel event times separately. Count every upload, map/unmap, conversion, synchronization and result materialization. A device-only profile with preloaded buffers is explanatory only.

Use three small matched local-size/layout candidates at most in the initial discriminator. Stop if transfer/queue overhead exceeds useful savings or exactness cannot be admitted. Do not build a Vulkan/Metal/SYCL bridge stack to salvage this track during the first campaign.
