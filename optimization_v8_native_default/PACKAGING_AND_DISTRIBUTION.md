# Packaging is part of the default-performance implementation

## Decision: ship native, do not compile it on ordinary first use

Use the same `solweig-light` distribution. Qualified platform wheels contain the private native binary, any redistributable runtime libraries actually needed, a complete source/build/ABI/ISA manifest and license notices. Preserve project namespace, entry points, extras and core dependencies. Do not create `solweig-light-native` as an extra package the user must discover/install.

Main currently already needs native GDAL and matching bindings. This task adds no new end-user compiler requirement; it does not claim to solve all pre-existing scientific dependency distribution. Test with baseline requirements prepared in the same way for main and candidate.

## Build-time architecture

Prefer minimal changes to the existing setuptools backend unless a concrete wheel integration issue justifies a migration. Native generation is a maintainer build step with pinned ISPC and a small portable C/C++ wrapper if a pool is required. It can be driven by Python subprocess lists, not `/bin/zsh` or `/opt/homebrew/...` assumptions. Platform-specific builders run only in isolated permitted environments. Do not fetch unsigned compilers or run curl-pipe-shell in installation hooks.

Initially keep a C ABI library and ctypes region binding, avoiding per-block pointer setup. A thin extension can later be selected if boundary evidence warrants it; preserve Python/NumPy ABI compatibility and regenerate wheel tags correctly. Use buffer ownership rather than copying merely to satisfy an extension. `abi3` is optional, not an assumed promise: select a documented stable ABI only after verifying the C API surface. Do not claim universal ABI based on filename.

Versioned build manifest includes kernel and generated source hashes, wrapper/ABI-layout version, ISPC/compiler version, full flags and target, linker dependencies, math profile, scalar profiles, OS min version, libc/architecture requirements, artifact SHA and disassembly audit. Use immutable artifact generation names and atomic publication. Release artifacts are packaged from a locked build output, not discovered in an arbitrary user cache.

## Platform rules

- macOS arm64 is the initial observed development host. Do not require Homebrew ISPC or a mutable developer dylib at runtime. Inspect `otool -L`, architecture and minimum OS; no absolute Homebrew paths. Bundle allowed non-system libraries using correct install names/rpaths. Native FP policy must match qualified ARM64 execution.
- Linux x86_64: build in an appropriate manylinux baseline; inspect/repair external dependencies and ISA. Baseline selector code must not itself execute AVX2/AVX512 before detection. Runtime ISA dispatch must check CPU and OS vector-state capability, not `platform.machine()` alone.
- Linux aarch64 / macOS x86_64: independent capability/numeric/performance qualification. A successful cross-compile is not an execution pass.
- Windows or other platforms: preserve existing core support status. The repository may have POSIX-specific dependencies outside native. Do not advertise new Windows support based on generating a DLL alone. Mark unsupported or untested scopes honestly.
- Do not force `-march=native` artifacts into a general wheel. Choose portable target baseline plus separately dispatched variants. First target only the few actual supported combinations with evidence, then expand.

Any wheel containing a native library is platform-specific. It must not be labelled `*-none-any` or `Root-Is-Purelib: true`. A C ABI with no Python C API may use an appropriate generic Python tag plus platform tag; an extension uses correct interpreter/ABI tags. The build backend, repair tools and installed tests must verify these rather than renaming wheels manually. Packaging tag standards and cibuildwheel are referenced in SOURCES.md.

## Source distribution and editable behavior

A standard source build without native artifacts/compiler produces a functioning no-native installation using the existing Numba path, without new native toolchain downloads or mandatory build deps. A maintainer can explicitly prepare native outputs and then run the same normal wheel build. A source checkout with a verified matching local artifact can include it if the build provenance is complete. Never reuse an artifact from different source simply because it loads.

Native accelerated source builds, if offered, are developer opt-in; they are not an extra step imposed on ordinary users. Missing optional native output in a **native release build** must FAIL that build, not silently upload a pure wheel while claiming native coverage. The no-native fallback build and the native release build are distinct declared build modes tested separately.

Do not include a native extra as a default prerequisite. Build requirements may be optional developer extras, but core pip usage stays unchanged. Publishing platform and pure fallback wheels of the same version must follow a coherent package policy and test installer selection. This packet does not authorize upload.

## Runtime loader

Load only a path within installed package resources. Check manifest/content once per handle generation and verify ABI/capability before executing. Default loading never hashes source `.ispc` or attempts a build. A present but corrupted artifact is a packaging defect in qualification, even if auto safely declines to Numba. Expert dev build remains separated and cannot be invoked through auto.

No requirement to write executable code into HOME, temp, cache or site-packages at runtime. No subprocess compiler. Ordinary unsupported-host fallback does not emit a new installation-error message. Actual admitted native runtime errors remain visible. Optional diagnostics can say why a row was declined without changing normal CLI output.

## Local install tests, not just wheel existence

Build an artifact with the final selected source; install into a fresh venv outside the repo; assert every loaded module/library origin is in the installation. Run actual README-style API and CLI with no backend variables, no ISPC/compiler/zsh on child PATH and no network attempt originating from the backend. Make site-packages and native dev-cache nonwritable while retaining baseline output/cache permissions. Verify actual native calls and exact required outputs/state on the qualified host.

Also build source/no-native mode and repeat ordinary usage. Verify fallback works; do not count that as native qualification. Test wrong-arch/missing-dependency/corrupt manifests and simulate supported-decline decisions without issuing illegal instructions. Repeat an expert force-native missing-capability case to confirm fail-loud semantics.

Install/run/uninstall/reinstall and editable mode receive focused tests when packaging code changes. Verify LICENSE/source distribution obligations for compiled GPL-derived project code and third-party components; preserve notices and corresponding source in release artifacts. Do not bundle random prebuilt files from an unverified worktree.

## CI boundary

Local host build/tests are mandatory for local readiness. Prepare targeted manual/native-wheel workflows or release scripts but do not trigger hosted CI/push from this task. Existing required smoke behavior stays. Full cross-platform release matrix is a future required gate for any broad support claim, not something to fake as passed to avoid overhead. A local native-default certificate is scoped to its actually tested platform.
