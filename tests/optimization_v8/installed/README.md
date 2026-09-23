# N8-23 installed-source DX gates

Executable no-env and source-install DX gates for the v8 packet
(TASKS_CLAUDE.yaml N8-23, dossier `DX_CONTRACT.md`).  Everything runs
offline on the local host; nothing modifies `pyproject.toml`, `src/` or the
packaging directories.

## What runs, in order (session fixtures in `conftest.py`)

1. **Wheelhouse** (`wheelhouse.py`) — the pinned baseline runtime closure
   (numpy/scipy/numba/llvmlite/GDAL/pytz/timezonefinder + transitives, see
   `RUNTIME_CLOSURE`) is repacked **offline** from the local uv cache: the
   cache's `archive-v0` entries hold the unpacked wheel contents with intact
   `METADATA`/`WHEEL`/`RECORD`, and are re-zipped under the original wheel
   filename.  A setuptools seed wheel (virtualenv-embedded) is added so PEP
   517 source builds can run without build-isolation downloads.
2. **Wheel build** — ordinary `pip wheel <worktree> --no-deps
   --no-build-isolation` in a throwaway build venv.  Today this yields the
   declared SOURCE/NO-NATIVE fallback wheel (pure, `py3-none-any`).
3. **Wheel venv** — a fresh venv OUTSIDE the repo receives the wheel plus
   the closure by plain `pip install --no-index --find-links`, then
   `pip check`.
4. **No-env gates** — README-style `thermal_comfort` and a real
   console-script invocation, in a child built with `env -i` semantics: no
   backend controls at all, `PATH=/usr/bin:/bin` (no ISPC / Homebrew zsh /
   build tools), `SOLWEIG_LIGHT_NATIVE_CACHE` pointed at a **non-writable**
   directory (proves auto never builds) and `NUMBA_CACHE_DIR` at a scratch
   location (baseline JIT cache).  Two properties are **enforced**, not
   assumed: the venv's site-packages is chmod'd read-only (dirs `0o555`,
   files `0o444`, symlinks untouched) for the child run and restored after,
   so any write into the installation fails loudly; and a scratch
   `sitecustomize.py` on the child's `PYTHONPATH` raises on Internet-domain
   socket use while recording every network-capable call to a scratch log —
   the tests assert the guard loaded (marker event) and that zero network
   attempts occurred.  DX-surface parity is captured through
   `dx_snapshot.capture_runtime_surface_subprocess` (the
   `SOLWEIG_DX_PACKAGE_ORIGIN=subprocess:<python>` mechanism) so N8-41/42
   rerun these gates unchanged against a native wheel's venv.
5. **Source gate** (DX gate 5) — a second fresh venv installs the worktree
   by `pip install . --no-build-isolation` under the stripped PATH
   (dependencies are prebuilt wheels; nothing compiles), then runs
   `preprocess` + `calculate_svf` on the Numba path.  Explicitly **NOT
   native-qualified**.

## Run

```sh
.venv/bin/python -m pytest tests/optimization_v8/installed -q
```

Gate results land in
`optimization_v8_native_default/evidence/installed/installed_gates.json`
(including the built wheel's sha256).

## Skip labels (never fake passes)

| label | meaning |
|---|---|
| `[wheelhouse-unavailable]` | local uv cache cannot satisfy the pinned closure offline |
| `[uv-unavailable]` | no `uv` binary for fresh-venv creation |
| `[wheel-build-unavailable]` | offline wheel build/install failed |
| `[host-memory-pressure]` | the baseline resource-admission model refused the no-env run: the scene's fixed ~1.74 GB phase reservation + 410 MB parent charge exceeds `0.5 x` the host available-memory view (`runtime.py:default_memory_budget_bytes`).  Environmental; retried, then labelled. |
| `[native-wheel-deferred-N8-41]`, `[companion-collision-deferred-N8-41]`, `[upstream-collision-deferred-N8-42]`, `[native-qualification-deferred-N8-42]` | channels that need the N8-41 native artifact / companion distribution; see `test_deferred_gates.py` |

## Boundary

The current branch carries no packaged native artifact, so every green gate
here proves the fallback channel only — necessary but NOT native
qualification (DX_CONTRACT.md: "Passing fallback installation is necessary
but insufficient for the native-default goal").
