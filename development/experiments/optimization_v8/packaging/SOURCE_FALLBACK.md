# N8-20: source-fallback record

What a plain `pip install .` produces with no native artifacts and no
compiler, and how the packaged loader must treat absent vs corrupt
artifacts. Companion to BUILD_DESIGN.md (section 7-8); the loader contract
itself is implemented by N8-21.

## What `pip install .` yields today (no native artifacts, no compiler)

* The setuptools build runs exactly as on main: no ISPC, no C toolchain,
  no extra build requirement is consulted. `build_native.py` is not part
  of the build backend — it is a maintainer script under `experiments/`.
* The resulting installation is **functioning and no-native**: every
  region runs on the existing Numba path.
* **Label: explicitly NOT native-qualified.** The Numba path carries no
  numerical certificate for the native-default claim; the v8 native
  performance policy must treat a source install as an ordinary core host
  with identical user behavior to main. Nothing in output, CLI text, or
  checkpoint identity may imply native execution happened.
* The source distribution still ships the kernel source
  (`backends/native/*.ispc` package-data globs already in `pyproject.toml`)
  for transparency and license obligations; presence of source is NOT
  presence of an artifact.

## Declared fallback build mode (what maintains this property)

`build_native.py build --mode source` performs the no-native fallback
build: it publishes a `source-no-native` manifest (`artifacts: []`,
`toolchain: null`) and **never invokes ISPC even when it is installed**.
It is exercised in the test suite with a stripped environment
(`PATH=/usr/bin:/bin`): the build succeeds and the manifest validates.
Symmetrically, the native release mode **fails loudly** (exit 3,
`BUILD FAILED: ispc not found …`) when ISPC is absent — it never quietly
publishes a pure wheel while claiming native coverage.

## Loader semantics: absent artifact vs corrupt artifact (N8-21 contract)

| Installation state | Auto/default behavior | Explicit native request |
|---|---|---|
| **Absent artifact** (no `native_generated/` resources, or only a `source-no-native` manifest — the ordinary `pip install .` case) | **Quiet auto decline**: select Numba, no error, no new installation-error message in normal CLI output. Absence is an expected, supported state. | Fails loudly ("no qualified native artifact in this installation") — requesting native on a no-native install is an operator error worth a clear message. |
| **Corrupt artifact** (manifest missing/invalid, hash mismatch, Mach-O structure failure, FMA re-audit failure, ABI/platform mismatch) | **Recorded decline**: auto declines to Numba AND privately records the reason (available through diagnostics without changing normal stdout). This is a packaging defect in qualification, not a supported host state. | **Fails loudly** with the recorded reason. Never silently falls back as if nothing happened, never executes unverified bytes. |
| **Qualified artifact, qualified host** | Load once per handle generation: schema → hashes → Mach-O walk → ABI version → host capability (arch, min-OS, ISA/OS vector state). Then execute. | Same verified load. |
| **Qualified artifact, unqualified host** (wrong arch, older OS, missing NEON) | Ordinary supported-host fallback: quiet decline to Numba, like absence. Not an installation error. | Fails loudly with the specific capability gap. |

Two invariants worth restating:

1. **Absent and unqualified are quiet; corrupt and explicit-request
   failures are loud.** A truncated-but-present dylib must never be
   executed and must never pass silently: the recorded decline reason is
   what makes the packaging defect visible in qualification.
2. **The expert dev path stays out of this table.**
   `solweig_light/backends/native_lw.py` (build-on-demand into the user
   cache) is expert opt-in behind explicit backend requests. Auto never
   enters it merely because a filename matches, and a packaged loader
   never reads the developer cache (`~/.cache/solweig-light/native`).

## Verification status of this record

* `test_build_modes.py::test_source_fallback_build_needs_no_ispc` — the
  fallback build runs under a stripped environment and validates.
* `test_build_modes.py::test_native_mode_fails_loudly_without_ispc` — the
  native mode refuses (exit 3) when ISPC cannot be found anywhere.
* `test_atomic_publication.py::test_verify_rejects_*` — corrupt (hash /
  truncated-image / forged-name) artifacts are detected and rejected; the
  loader contract table above is the behavioral restatement N8-21
  implements.
