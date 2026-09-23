# D06: optional backend integration after a measured win

## Small boundary, not a framework layer around everything

Keep top-level API/CLI, models, GDAL, cache validation, forcing and state on their existing path. Integrate one CPU island first. Suggested new implementation area is `src/solweig_light/backends/` with backend-private code and a minimal private dispatcher; this is a proposed internal location, not a demand to restructure the repository. The integrator confirms existing conventions before creating it.

During experiments use isolated modules, not public placeholder functions. After promotion a private selector such as `SOLWEIG_LIGHT_CPU_BACKEND=numba|ispc|highway|drjit_llvm|pocl_cpu` may be added without changing existing Python argument defaults. Freeze the actual names then. Default is `numba`. Never choose GPU automatically. Explicitly requesting an unavailable backend produces a clear capability error; default operation without optional packages remains fully functional.

Per-input unsupported profiles can intentionally use Numba before launch, with reason/counters. Capability tokens cover dtype/scalars, shape/layout, ISA/device, compiler/version/options and profile. Do not benchmark a backend whose calls actually all fell back. An admitted mismatch/runtime failure is surfaced, not treated as a reason to quietly rerun Numba and claim success.

## Input/output and lifecycle

The dispatcher owns a prepared readonly block until CPU native completion. No consumer can overwrite neighboring source fields while a kernel reads them. Output becomes visible only after all asynchronous computation/conversion finishes. Buffers may be pooled only under bounded leases and exact compatibility keys. On cancellation, drain/cancel native work before unmapping or freeing memory. Unknown outstanding work must not leave a worker marked idle.

Keep independent tile jobs in processes because current demand state is module-global. Native pixel threads inside one tile are permitted. Do not make global backend/thread settings leak to the parent process or another user thread. Backend flags initialized in each child before any numerical work are easier to audit than repeatedly toggled shared global state.

## Identity and provenance

Persist backend id and effective route, native source/ABI/compiler/options/ISA, runtime build and math fingerprints in simulation/checkpoint identity and evidence. If a kernel's backend can affect geometry, its dependency belongs in geometry identity too. Do not bypass existing source identity checks to force a cache hit. Wrapper-only changes may cause conservative invalidation; refine that closure only through a separate reviewed equivalence/key change.

Existing immutable native geometry can be reused only under current keys and validation. Cross-machine compilation cache entries cannot be keyed by source name alone. Include compiler, flags, CPU features/device, dtypes, dimensions required by compilation and data-constant specialization. Raw memory addresses are not stable cache keys. Dynamic inputs are not safe constants just because a tracer reused an object.

## Packaging

One winning optional backend is sufficient. Prefer an optional extension/extra with no top-level import of its runtime. A default core installation must neither download a compiler at import nor require an OpenCL ICD. Pin tested versions and document user-space build steps, licenses and platform requirements. Do not ship machine-specific compiler outputs pretending to be portable. Local Mac arm64 evidence is not Linux x86/Windows evidence; other platforms retain Numba fallback until qualified.

Test installed wheel outside repo PYTHONPATH and a clean core-only environment lacking optional dependencies. Verify seven workflow signatures, compatibility package namespace collision behavior and at least one actual TIFF chronology. Avoid rebuilding identical wheels per tiny edit; do one wheel after the selected source settles.

## Useful failure outcome

If every C loses or fails exactness, retain B if it passes and improves the whole pipeline. Otherwise retain A and archive concise rejection evidence. Do not land a maze of dormant backends or a general abstraction with no measured consumer. Completion of a comparison is not a claim of performance gain.
