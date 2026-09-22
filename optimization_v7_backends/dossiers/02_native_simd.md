# D02: native CPU prototype, ISPC first or Highway

## Why this track

ISPC's uniform/varying execution directly expresses one ordered patch loop across independent pixel lanes [F03]. Highway supplies portable C++ vector operations and runtime ISA dispatch [F04]. Choose one native route based on actual local tool availability. A second route is conditional, not a mandatory extra production dependency.

## ISPC implementation recipe

1. Install/pin a compatible compiler in an isolated local prefix if needed and permitted. Record official source/release URL, artifact hash, compiler version, license, host ISA and output target. Do not publish a `--target=host` binary as universally portable.
2. Export a C-compatible function taking bounded pointers, dimensions, output buffer and the explicitly captured scalar specializations. Represent bool masks with an agreed fixed width (typically uint8), not C++ bool ABI assumptions. Use int64/size_t-safe addressing and overflow checks in the Python/native adapter.
3. Use `foreach` or equivalent independent lane ownership for pixels. Declare patch index/coefficients uniform only when they actually are. Keep both p loops ordered. Keep per-lane A0..A9 in registers; no cross-lane reduction.
4. Generate separate f32/f64 scalar specializations if both are reached, or admit only the evidenced one and fall back the other. Do not silently downcast surface coefficients to make a backend easier.
5. Leave transcendental preparation in existing NumPy/SLEEF. Preserve all source RN32 boundaries, pi bits, multiplication grouping and exact division behavior.
6. Prohibit unsafe fast-math and masked out-of-bounds loads. The inspected ISPC guide provides `--opt=disable-fma`; confirm accepted flags for the pinned compiler [F03]. Do not use approximate reciprocal math or `--opt=fast-masked-vload`. Inspect emitted code for contraction and rounding, not only command text.
7. Start with serial packet execution plus a single explicit host task mechanism if needed. ISPC's tasking or OpenMP must fit the worker's H reservation. Reuse one native pool if needed, do not create H tasks inside each of H existing Numba threads.

## Highway alternative

Implement a portable C ABI with baseline/scalar fallback and runtime-dispatched ISA kernels. Use vector lanes for independent pixels, not associative patch reductions. Keep explicit Mul and Add operations separate unless the original typed node used FMA; inspect assembly to ensure the C++ compiler has not contracted them. No `-ffast-math`; use a verified contraction-off/strict-FP build configuration for each compiler. Keep a reference scalar kernel in the native test suite, but actual SOLWEIG remains the oracle.

Native vector double support and conversion costs vary by ISA. Narrow domains must be explicit; reject unqualified hardware at capability admission rather than SIGILL. No GPU runtime is required for this track.

## Python boundary

A minimal nanobind/pybind11/Cython wrapper is acceptable, whichever the repository can package cleanly. Freeze one wrapper approach after triage; do not add all bindings. Expose borrowed readonly arrays and an owned output; validate dtype/contiguity/lifetime before releasing the GIL. Include every copy and allocation in adapter timing. A C ABI does not itself prove zero-copy: use pointer/stride records and allocation measurements. Retain buffer references through completion.

Use guarded tail lanes without reading beyond B. Canary and sanitizer checks on tiny buffers catch errors output parity cannot. No per-pixel Python or native callback.

## Packaging and decision

Local prototype compilation is not deployment. After a win build one optional wheel/extension with isolated dependencies, target feature dispatch, ABI fingerprint and license notices. Test fresh installation outside source tree and core-only installation without the extension. Other OS/ISA builds are future or compile-only unless run; do not add a hosted matrix now.

Advance only if exact corpus and full adapter timing beat B materially. Native compiler speed alone is not a result; sum conversion, bridge, kernel and synchronization. Source/source-profile changes invalidate the native binary cache.
