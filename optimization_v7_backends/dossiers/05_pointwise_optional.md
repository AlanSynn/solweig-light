# D05: conditional MLX CPU / Halide island

Activate only after a named remaining pointwise/stencil stage occupies enough current total time to repay the port. The source has already integrated typed GVF postprocessing and demand-specific radiation. Comparing against an obsolete unoptimized NumPy function is not acceptable.

## MLX CPU

The prior survey identified Linux CPU installation and CPU compilation support; verify the chosen installed release/OS rather than public main. Force CPU device/stream and use only dtypes it actually implements. Do not downcast unsupported float64 intermediate operations to obtain a compiling demo. A precision/domain that cannot be represented remains on the accepted path.

Start with a pure, bounded pointwise island from already prepared inputs and all needed outputs, not a patch reduction hidden in `sum`. Freeze the original typed DAG, warnings, nonfinite handling, ownership and error behavior. `mx.compile` equivalence is not a promise of bitwise equality [F09]; compare actual outputs and generated behavior. Explicitly evaluate lazy outputs and synchronize the CPU stream before ending a timer. Keep copies and temporary allocations visible.

Avoid tracing thousands of discrete ray steps or all 24 time records into a single giant graph. A small captured pure expression can be useful even when a full MLX port is not. The controls remain A current Numba/NumPy path, B same fusion/layout in Numba, C MLX. If B wins, use B.

## Halide

Use a regular image/stencil expression where separate algorithm and schedule can reduce intermediate storage. Preserve operation grouping, floating-point mode and all border rules. Reuse the exact current data inputs; do not substitute a different wall detector or orientation filter. An aggressive reduction schedule/associative optimization may violate ordered sums. Verify target support and strict-float controls for the pinned release instead of treating CPU/GPU backend names as a guarantee.

Same typed-DAG, trace and full adapter timing gates apply. Runtime allocator/thread count is part of admission. AOT schedules and ISA-specific binaries must have correct runtime dispatch or an explicit supported-platform scope.

## Other surveyed frameworks

SYCL/AdaptiveCpp, Kokkos, Taichi, DaCe, JAX/XLA, Pythran, Cython, ArrayFire, Futhark, IREE, TVM, KernelAbstractions and Slang remain in `reference/FRAMEWORK_REVIEW_KO.md`. They are not an installation checklist. Activate one only for a specific bottleneck and a written reason it is a better discriminator than the current three tracks. New language/runtime/toolchain maintenance is a cost, not proof of speed.

CPU-first native shared-library wrappers are allowed; a full framework rewrite, surrogate, isotropic sky, lower resolution, fewer timesteps/patches or approximate thermal-comfort replacement is not.
