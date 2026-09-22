# N8-20: build-time architecture for the bundled-native wheel

Implements the packaging dossier (`optimization_v8_native_default/PACKAGING_AND_DISTRIBUTION.md`)
for the v8 native-default packet. This file is the contract N8-21 (trusted
installed-artifact loader) implements against; the wheel integration itself
is N8-41, after candidate selection. Nothing here changes user commands:
installation stays `pip install solweig-light` (or `pip install .`), the CLI
entry point stays `solweig-light`, and no new runtime dependency is added.

Companion artifacts in this directory:

* `build_native.py` — the working maintainer build driver (proved below);
* `wheel_tags.py` — the wheel tagging rule checker (builder/test-side only);
* `SOURCE_FALLBACK.md` — what a plain source install produces and how the
  loader must distinguish absent vs corrupt artifacts;
* `stage/lw-g8-42aeba6a50dc5937/` — the proof generation built from the B7
  kernel, and `stage/dylib_comparison.json` — the byte-parity record.

## 1. Distribution shape

One distribution: `solweig-light` (setuptools backend unchanged). The
qualified native artifact ships as **package data inside platform wheels**:

```
solweig_light/backends/native_generated/<generation>/   (package data)
    liblw_native_g8.dylib        the C-ABI shared library
    manifest.json                schema v1, see section 4
    lw_primary_g8.h              ISPC-generated header (declared ABI surface)
    lw_primary_g8.s              the audited disassembly (audit evidence)
```

* No second package (`solweig-light-native`) the user must discover.
* The directory is private to the package; nothing on `sys.path` and no
  entry point refers to it directly. The loader (N8-21) resolves it via
  `importlib.resources` on `solweig_light`, never via `__file__` string
  walks of arbitrary wheels.
* Release artifacts are packaged from a **locked build output** (a staging
  tree published by `build_native.py`), never discovered in an arbitrary
  user cache (`~/.cache/solweig-light` stays the expert dev path and is
  never read by the packaged loader).
* `pyproject.toml` will need one line added at N8-41
  (`"backends/native_generated/**/*.dylib"` + manifest/h/asm globs under
  `package-data`); the source `.ispc`/`.sh`/`.py` globs already present are
  kept for source transparency and license obligations.

## 2. The maintainer build step

Native generation is a maintainer step run in an isolated permitted
environment — **not** an install hook and **not** a runtime path:

```
.venv/bin/python experiments/optimization_v8/packaging/build_native.py \
    build --kernel src/solweig_light/backends/native/lw_primary.ispc \
          --staging <locked-build-output>
# then, at wheel assembly time (N8-41):
#   copy the verified generation dir into the package data tree and build
#   the platform wheel; the wheel build FAILS if the generation is absent.
```

Driver discipline (all implemented in `build_native.py`):

* **Arg-list subprocesses only.** Every external tool is invoked with a
  Python argv list and an explicit allow-listed environment
  (`PATH`, `LANG`, `SDKROOT`, `DEVELOPER_DIR`, `MACOSX_DEPLOYMENT_TARGET`).
  No `/bin/zsh`, no shell string, no `curl | sh` anywhere.
* **No toolstore assumptions.** No `/opt/homebrew/...` constant exists in
  the driver. ISPC resolution order: `--ispc` flag → `SOLWEIG_LIGHT_ISPC`
  env → `PATH` lookup. Absence is a loud `ToolUnavailable` (exit 3), and
  the version is **pinned-checked** (`--ispc-version`, default `1.31.0`)
  before any compile: a wrong ISPC refuses to build.
* **Recorded identity.** ISPC (version, LLVM, path, binary sha256) and the
  C compiler (kind, full version string, path, binary sha256) are hashed
  and written into the manifest.
* **Declared targets.** First target: macOS arm64, ISPC `neon-i32x8`
  (`liblw_native_g8.dylib`), flags `-O2 --opt=disable-fma --math-lib=default
  --pic` (the B7 numerical contract: no fast-math, contraction disabled).
  No `-march=native` artifacts in wheels; portable target + separately
  dispatched variants only, per-platform qualification first.
* **FMA audit gate.** The same compilation is emitted as text asm
  (`--emit-asm`) and scanned for `fmadd|fmla|fmsub|fnmadd|fnmsub|fnmla`
  (the B7 `audit_fma` set). Any hit fails the build (exit 5) and nothing is
  published: a contraction-free kernel is a build-time invariant.
* **Mach-O facts recorded.** `otool -L/-l/-h` (arg-list) yields external
  dependencies, min-OS and cputype; the loader later re-checks capability
  against these recorded facts. A darwin build that cannot state its
  platform facts is not publishable. (Linux equivalents — readelf/objdump
  and manylinux repair — are future work for the Linux target; not faked
  here.)
* **Bundled-library discipline.** The link runs with a cwd-scoped relative
  `-o`, so the dylib's `LC_ID_DYLIB` is the bare basename. When the wheel
  is assembled, the maintainer passes `--install-name
  @rpath/liblw_native_g8.dylib` so the bundled library is located via
  rpath inside the installation — never an absolute Homebrew path. Only
  `/usr/lib/libSystem.B.dylib` is external today (a system library, no
  bundling needed); `otool -L` verification of that fact ships in the
  manifest.

## 3. Two declared build modes

| Mode | Driver flag | Requires ISPC | Behavior when the artifact cannot be produced |
|---|---|---|---|
| **native release** | `--mode native` (default) | yes, pinned | **FAILS THE BUILD** (exit 3/4/5/6/7, message on stderr). It never silently publishes a pure wheel that claims native coverage. |
| **source / no-native fallback** | `--mode source` | no (never invoked) | Publishes a `source-no-native` manifest with `artifacts: []`. The resulting installation uses the Numba path, explicitly **not native-qualified** (see SOURCE_FALLBACK.md). |

They are distinct, separately tested build modes (see
`tests/optimization_v8/packaging/test_build_modes.py`). The fallback mode
is exercised with a fully stripped environment (`PATH=/usr/bin:/bin`, no
ISPC reachable) and proves `pip install .` needs no new toolchain; the
native mode is exercised end-to-end plus in its failure modes (missing
ISPC → exit 3; unparseable kernel → exit 4 + clean staging area;
republish attempt → exit 7).

## 4. Build manifest schema (manifest_version 1)

Emitted per generation by `build_native.py`; validated by
`validate_manifest()` (mode-aware) and `verify_generation()` (content).
Required fields of a `native-release` manifest:

| Field | Contents |
|---|---|
| `manifest_version` | `1` |
| `build_mode` | `native-release` \| `source-no-native` |
| `package` | `solweig-light` |
| `generation` | immutable content-derived name, see section 5 |
| `abi` | `abi_version` (1), `wrapper_abi_layout_version` (`lw-region-abi-1`), `exported_symbols` (`lw_primary_f32`, `lw_primary_f64`), `python_c_api: false` |
| `kernel` | name, sha256, source_ref (repo path of the .ispc) |
| `generated_sources` | per entry: path, kind, sha256 (the ISPC-generated header and the audited `.s`) |
| `toolchain` | `ispc`: version, llvm, path, binary sha256; `cc`: kind, full version, path, binary sha256 |
| `build` | `target` (`neon-i32x8`), full `ispc_flags`, `cc_flags`, `link_deps` |
| `math_profile` | `id` (`lw-primary-strict-fp-contract-off`), `fast_math: false`, `fma_contraction: disabled`, `math_lib: default` |
| `scalar_profiles` | `f32`: symbol `lw_primary_f32`, surface scalars float32; `f64`: symbol `lw_primary_f64`, surface scalars float64, accumulator rounds float32 at the accumulator add (matches the numba-typed baseline) |
| `platform` | `os`, `os_min_version` (from `LC_BUILD_VERSION`), `arch` (arm64), `requirements` (`cpu-feature:neon`), `link_deps` |
| `artifacts` | per entry: path, kind, binary_format, sha256, byte size |
| `fma_audit` | passed, tool, mnemonic set, per-hit records, `asm_sha256` binding the audit to the shipped disassembly |
| `created_utc` | informational wall-clock stamp (excluded from identity) |

The `source-no-native` variant carries the same top-level shape with
`artifacts: []`, `toolchain: null` and a `note` stating the loader must
quietly auto-decline to Numba.

## 5. Immutable generations and atomic publication

* The generation name is **content-derived**: `sha256` over the canonical
  JSON of every manifest field except `generation` and `created_utc`,
  truncated to 16 hex chars — e.g. `lw-g8-42aeba6a50dc5937`. Same source +
  toolchain + flags ⇒ same name; any change ⇒ new name.
* Publication is a **single `rename`**: everything is materialized in a
  private temp directory inside the staging area (same filesystem),
  fsynced, then renamed into `staging/<generation>`. Observers see the old
  state or the complete new generation, never a half-published directory.
  Any failure removes the temp dir and leaves staging untouched.
* Generations are **immutable**: an existing generation is never
  overwritten (exit 7). To ship changed native content, the fingerprint —
  and therefore the name — necessarily changes.
* `verify_generation()` re-checks, without any tool: schema (mode-aware),
  directory name == derived generation name, every artifact/generated-file
  hash and size, Mach-O structural integrity (header, load-command walk,
  segment file ranges within EOF — catches truncation that keeps a valid
  magic), and, for native-release, re-runs the FMA audit on the shipped
  disassembly against `fma_audit.asm_sha256`.

## 6. Wheel tagging rules (`wheel_tags.py`, checked by builders and tests)

* Any wheel containing a native library is **platform-specific**: platform
  tag must be concrete (`macosx_26_0_arm64`, `manylinux_2_28_x86_64`, …);
  `*-none-any` and `Root-Is-Purelib: true` are violations. Tags are
  produced by the build backend — manual wheel renaming is forbidden; the
  checker exists to **verify**, and tests run it on synthetic filenames.
* Our library is a **C ABI with no Python C API** (ctypes-called), so a
  generic Python tag plus platform tag is admissible:
  `solweig_light-0.1.0.dev0-py3-none-macosx_26_0_arm64.whl`.
* `abi3` is **not** claimed: it would promise a stable C API surface that
  has not been verified. `cp311-cp311-<platform>` is acceptable;
  `cp311-abi3-<platform>` is a violation.
* A no-native fallback wheel of the same version stays
  `py3-none-any`/pure; publishing platform + pure wheels of one version
  must follow a coherent installer-selection policy (N8-41 scope; this
  packet does not authorize upload).

## 7. Source, editable, and fallback installs

* `pip install .` with no native artifacts and no compiler produces a
  **functioning no-native installation** on the existing Numba path —
  no ISPC download, no compiler wheel, no mandatory build deps, no
  C toolchain requirement (the C compiler in the driver is a
  maintainer-only concern, never a pip build requirement).
* Native-accelerated source builds are developer opt-in: prepare a
  verified generation with `build_native.py` matching the checked-out
  kernel hash, then run the normal wheel build. An artifact from different
  source is never reused merely because it loads — the generation
  fingerprint binds kernel hash + toolchain + flags.
* Editable installs stay compiler-free; the expert dev path
  (`backends/native_lw.py`, build-on-demand into the user cache) remains
  separated and is never entered through auto (see SOURCE_FALLBACK.md).

## 8. Runtime loader contract (implemented by N8-21)

This is the section N8-21 implements. The packaged loader:

1. **Reads only installed package resources**: resolves
   `solweig_light/backends/native_generated/<generation>/` via
   `importlib.resources` (or an equivalent package-traversal API), with
   **path containment** — the resolved real path must stay inside the
   installed package directory; symlink escape, `../`, absolute paths in
   manifest `path` fields, and any user/cache-writable location are
   rejected before use.
2. **Never compiles, downloads, or writes**: no runtime compiler or
   subprocess tool of any kind, no network access, no writes to HOME,
   temp, cache or site-packages. Default loading never hashes the source
   `.ispc` and never attempts a build.
3. **Checks content/ABI/capability once per handle generation**: manifest
   schema + hashes + Mach-O structural walk (section 5), then
   `abi.abi_version` / `wrapper_abi_layout_version` against the loader's
   compiled expectations, then host capability (`arch`, `os_min_version`,
   `requirements`, ISA/OS vector-state detection — never
   `platform.machine()` alone) against `platform`. Read once at
   initialization; a running workflow keeps its loaded generation.
4. **Distinguishes absent from corrupt**:
   * absent artifact / `source-no-native` manifest / unqualified host ⇒
     **quiet auto decline** to Numba; no new installation-error message in
     normal CLI output (diagnostics may privately record the reason);
   * present but corrupt artifact (hash/structure/audit failure) ⇒
     recorded decline reason, auto declines to Numba, and an **explicit
     native request fails loudly** (this is a packaging defect in
     qualification, not an expected host state).
5. **Keeps the expert dev path separated**: `native_lw.py` is dev opt-in,
   keyed to explicit backend requests only; auto never enters it merely
   because a filename matches.

## 9. Proof on the existing B7 kernel

`build_native.py build --kernel src/solweig_light/backends/native/lw_primary.ispc
--staging stage` (driver invocation record, 2026-09-22):

* Published generation `stage/lw-g8-42aeba6a50dc5937/` (native-release,
  verified: schema, hashes, Mach-O walk, FMA re-audit all pass).
* **Byte-parity with the B7 dev cache**: the produced
  `liblw_native_g8.dylib` (sha256 `eb1071fc…2582b46a`, 34280 bytes) and the
  emitted `lw_primary_g8.s` (sha256 `bbdfdc95…57afc0e8`) are **byte-for-byte
  identical** to `~/.cache/solweig-light/native/` and its `build/` inputs.
  Explanation: the same pinned ISPC 1.31.0 (LLVM 22.1.8; the *pin*, not
  the path, determines output — the driver locates it without any
  /opt/homebrew constant), the same Apple clang 21.0.0 link, the same
  flags, a cwd-scoped relative `-o` giving the same `LC_ID_DYLIB`, and
  ld's content-derived UUID. Full record: `stage/dylib_comparison.json`.
* Kernel sha256 `52652a59…61663c` matches the B7 `build_stamp.json`, so
  this proof is against the exact reviewed B7-20 kernel source.
* Test suite: `tests/optimization_v8/packaging/` — 44 tests, all passing
  (3.7 s); with ISPC removed from the environment: 41 pass, 3 skip with
  the explicit `[ispc-unavailable]` label (never fake-pass).
* Compile-budget accounting: the B7 kernel was compiled **3 times** by the
  driver (~4 s each), one over the stated budget of 2 — the first run
  failed pre-publication at the `otool -h` cputype parser, the second
  published a generation carrying two metadata defects (LLVM version
  parsed as `unknown`; `link_deps` including the dylib's own install id),
  which was deleted and rebuilt; the shipped `lw-g8-42aeba6a50dc5937`
  generation is the one produced by the reviewed code.

## 10. Honest scope notes

* macOS arm64 / `neon-i32x8` is the only target prepared here. Linux
  x86_64 (manylinux baseline, repair step, ISA dispatch), Linux aarch64
  and macOS x86_64 each need independent capability/numeric/performance
  qualification — a successful cross-compile is not an execution pass.
* Windows core support status is unchanged; nothing here advertises new
  support from a DLL existing.
* The wheel assembly itself (copying a verified generation into package
  data, wheel tag production, installer-selection tests, fresh-venv
  install/origin tests) is N8-41; local readiness tests are mandatory
  there before any claim of native default.
