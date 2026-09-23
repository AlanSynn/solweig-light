# Gated heterogeneous follow-on, not a shortcut to CPU-native default

GPU may be evaluated when real residual coverage is large enough and the complete residency region can win after transfer/synchronization. This is not a mandated additional framework campaign. It must not add GPU runtime dependencies to ordinary CPU installation.

First establish reusable semantic region descriptors and compact producer layout on CPU. A GPU region can upload immutable encoded geometry/predicate states once, keep a bounded working set, perform original ordered per-pixel sweeps and return only required outputs/checkpoint state. Logical time remains chronological. Minimize global intermediate arrays, inspired by IO-aware tiled algorithms, not by attention-specific formulas.

Full device cost includes conversion, H2D, launch, device work, D2H, synchronization, allocation/compile and interaction with surrounding stages. A smaller CPU/GPU boundary is not always better; compare a contiguous residency region to the best CPU region.

The current real longwave graph includes f64 surface chains and f64 accumulator add before f32 cast. A f32-only device path cannot claim equivalence by pre-rounding coefficients. Test actual FP64 support and throughput; otherwise choose another wide integer/f32-safe region or retain CPU. Numerical relaxation is not authorized here. Disable only unsafe new contraction, not explicit reference SLEEF FMA.

Use capability detection and a shared private semantic interface, with architecture-specific schedules if justified. Do not promise OpenCL source portability implies performance/FP64 portability. Run small CPU-vs-GPU region tests only after the same numerical contract and boundary accounting are frozen. GPU results get distinct hardware/resource labels, never mixed with CPU-native speedup.

If an accelerator wins, stage it as an optional profile requiring separate packaging/default eligibility. Native CPU default and unchanged user DX are still the primary deliverables. A GPU-only success cannot close them.
