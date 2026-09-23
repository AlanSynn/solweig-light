# Zero-DX-change contract relative to main

## Main is the user surface baseline

Observed main: `14e888760727583ef782a4dc0e7a5c7c6e6ff9d1`. Its README prescribes an existing GDAL setup, a venv/dependency installation and `pip install .`; ordinary calls import `thermal_comfort` from `solweig_light`. The main distribution provides `solweig-light`; the explicit companion owns `solweig_gpu` imports and `thermal_comfort` executable. These are source observations, not a new installation test.

Capture the actual main and working-branch public surfaces in separate environments or by source AST where execution is unnecessary. Do not import upstream into candidate. Main is the DX baseline; accepted branch A is the immediate performance/numeric comparison. Original SOLWEIG-GPU remains a separate scientific/model oracle.

## Unchanged user actions

- Same distribution name, namespace, seven public workflows: thermal_comfort, preprocess, build_inputs, build_wind_ext_coeff, run_walls_aspect, calculate_svf, run_utci_tiles.
- Same positional/keyword signatures, default values, returned values, relative path resolution, date handling and documented import paths. Keep RuntimeOptions introspection/defaults, including original block_pixels, stable.
- Same normal executable/help/exit behavior and legacy companion installation. No silently colliding `solweig_gpu` files in main wheel.
- Same own-met TIFF filenames, output sets, dimensions, bands, metadata, masks, order, cache and checkpoint guarantees.
- Same normal installation flow. No new native extra, backend flag, license prompt, first-call native build/download, mandatory cache-prewarming, manual block tuning or OS-specific shell command.
- Optional forcing/acquisition packages remain optional. Native install must not pull Torch, CUDA, a GPU runtime or a full compiler toolchain into the normal core dependency set.
- No new normal stdout progress chatter about selected backend. Diagnostic APIs/logs are private or optional. Do not claim zero total filesystem activity: existing model caches/output remain, and existing Numba fallback may still JIT.

## Installation-channel matrix

| Channel | Expected behavior | Acceleration promise |
|---|---|---|
| Qualified platform wheel, supported host/profile | install once using ordinary pip; native package data present; automatic selection | native where prequalified and faster |
| Same wheel, unsupported ISA/profile/resource cell | no SIGILL, no rebuild prompt; pre-launch Numba path | correctness and DX, not native |
| Plain source/sdist/editable, no native binary/compiler | normal build/install succeeds with no new toolchain requirement | Numba; explicitly not native-qualified |
| Source tree with matched locally built/bundled artifact | same install command may package that artifact after full checks | only if source/ABI/profile certificate matches |
| Maintainer native wheel build | explicit isolated build toolchain and local release recipe | build-time activity, not end-user workflow |
| Expert explicit native override | preserves deliberate fail-loud request semantics | development capability; not needed for ordinary use |

No native artifact in the source tree plus no compiler implies fallback, not magic compilation. Do not fetch remote wheels from setup.py/PEP517 hooks. Do not commit massive platform bundles merely to make a source-install benchmark look native. If the final project later demands every Git source install be accelerated without a compiler, that requires a separately agreed binary-source distribution policy.

## Backend policy visible only to implementation

With the legacy env unset, select auto only after promotion. Existing explicit `numba` selects reference. Existing `native`/`ispc` remains an expert requested backend: retain its documented supported-domain fallback and fail-loud missing-build semantics until a deliberate documented migration; isolate its legacy developer build path so auto never reaches it. Unknown legacy strings retain historical Numba behavior rather than becoming auto by accident. An explicit diagnostic `auto` alias can be added privately, but no user must set it.

Ordinary auto selection falls back for missing binary, unqualified math/ISA, unsupported dtype/layout, insufficient reserved workspace or known poor crossover. ABI/integrity mismatch must never load the library; record a bounded reason. Noisy warnings are not required on unsupported hosts. Once an admitted native call begins, propagate its errors and preserve transaction state. Never catch all exceptions and silently compute a second version.

## Executable DX gates

1. Snapshot signatures/defaults/entry points and compare main vs installed candidate; document any already-existing branch divergence rather than blaming or hiding it.
2. Execute the README-style call and real CLI in a fresh installed environment, not through PYTHONPATH=src.
3. Unset all backend controls; remove ISPC/zsh/build tools from the child PATH without damaging the host. Disable candidate-origin network access during model execution. Use read-only site-packages and an inaccessible native developer-cache path. Keep only baseline-required output/cache destinations writable.
4. On qualified wheel host, count actual native work >0 and verify complete requested outputs/state. On unsupported/no-native case, verify Numba work and successful original API, not a fake native pass.
5. Source/sdist installation test with no new native toolchain. Existing GDAL/dependency build prerequisites are prepared independently, just as main requires.
6. Missing/corrupt/wrong-arch binary, stale certificate, ABI mismatch and unsupported CPU tests: default does not execute incompatible instructions; explicit native request is distinguishable.
7. Fresh venv no Torch/CUDA/forcing extras, real own-met path. Separate companion install and upstream import-collision tests remain.
8. Portable support claims list OS/ISA/Python/native and core status separately. Compiler cross-build success is not execution evidence.

Passing fallback installation is necessary but insufficient for the native-default goal. A default wheel that always chooses Numba has not met it.
