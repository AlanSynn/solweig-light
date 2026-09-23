#SOLWEIG-GPU: GPU-accelerated SOLWEIG model for urban thermal comfort simulation
#Copyright (C) 2022–2025 Harsh Kamath and Naveen Sudharsan

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
"""Build shim for the N8-41 native wheel (PACKAGING_AND_DISTRIBUTION.md).

Metadata stays entirely in pyproject.toml; this file only wires the two
declared build modes:

* DEFAULT (no ``SOLWEIG_LIGHT_PACKAGE_NATIVE``): the ordinary pure
  no-native wheel -- this shim is inert except for one guard that refuses
  to build a pure wheel while native generation content sits in the
  package source tree (a crashed earlier native build must never leak
  into a fallback wheel that "looks native").
* NATIVE REQUEST (``SOLWEIG_LIGHT_PACKAGE_NATIVE`` = staged generation
  directory): the locked build output is verified by the reviewed N8-20
  driver plus the N8-41 linked-image/install-name gates BEFORE staging,
  staged byte-identically into the package tree for the build (undone in
  ``finally``), and the produced wheel is re-verified after ``bdist_wheel``
  (members byte-identical, RECORD-digested, non-pure platform tags per
  ``wheel_tags.py``).  Any failure deletes the wheel and fails the build
  LOUDLY: a native-requested build can never silently ship a pure wheel.

All real logic lives in experiments/optimization_v8/packaging/
assemble_native_wheel.py (the maintainer tool home, next to the reviewed
build_native.py/wheel_tags.py it reuses); this shim stays deletable.
Deleting this file returns the project to the pre-N8-41 pure build
(except the pure-tree guard, which lives here on purpose: without the
shim nothing stages, so nothing can leak).
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_PACKAGING = _ROOT / "experiments" / "optimization_v8" / "packaging"

# Literal fallback of the request variable name for the loud error below.
_REQUEST_ENV = "SOLWEIG_LIGHT_PACKAGE_NATIVE"

try:
    sys.path.insert(0, str(_PACKAGING))
    import assemble_native_wheel as _assemble  # noqa: E402 (tool home)
except ImportError:  # pragma: no cover - only if the tool home is gutted
    _assemble = None

from setuptools import Distribution, setup  # noqa: E402
from setuptools.command.build_py import build_py  # noqa: E402

try:
    from setuptools.command.bdist_wheel import bdist_wheel  # noqa: E402
except ImportError:  # pragma: no cover - pre-70.1 setuptools
    from wheel.bdist_wheel import bdist_wheel  # type: ignore # noqa: E402

_REQUESTED_RAW = os.environ.get(_REQUEST_ENV)

if _REQUESTED_RAW and _assemble is None:
    raise RuntimeError(
        f"{_REQUEST_ENV}={_REQUESTED_RAW!r} is set but the native-wheel "
        f"assembly plumbing could not be imported from {_PACKAGING}. "
        f"Refusing to build: a native-requested build must never "
        f"silently degrade to a pure wheel.")


def _request():
    """The requested generation dir (raises on a malformed request)."""
    return _assemble.native_request()


def _identity(request):
    """Verified artifact identity, computed once per build process."""
    key = str(Path(request).resolve())
    cache = _identity._cache  # type: ignore[attr-defined]
    if key not in cache:
        cache[key] = _assemble.verify_for_wheel(request)
    return cache[key]


_identity._cache = {}  # type: ignore[attr-defined]


def _src_package_root(build_py_cmd) -> Path:
    base = build_py_cmd.distribution.package_dir.get("") or "src"
    path = Path(base).expanduser()
    if not path.is_absolute():
        path = _ROOT / path
    return path / _assemble.PACKAGE


class _GuardedBuildPy(build_py):
    """Stage/verify for native requests; purity guard for pure builds."""

    def run(self):
        request = _request()  # loud on malformed requests
        src_pkg = _src_package_root(self)
        if request is None:
            # pure build: refuse to silently carry native content
            _assemble.assert_pure_package_tree(src_pkg)
            super().run()
            return
        _identity(request)  # full gate BEFORE anything is staged
        staged = _assemble.stage_generation(request, src_pkg)
        try:
            super().run()
        finally:
            _assemble.unstage_generation(src_pkg, staged.name)


class _GuardedBdistWheel(bdist_wheel):
    """Post-build wheel verification for native requests.

    A native wheel that came out pure-tagged, missing its members, or
    carrying non-identical bytes is DELETED and the build fails: nothing
    mislabeled survives to be uploaded or installed."""

    def run(self):
        request = _request()
        started = time.time()
        dist_dir = Path(self.dist_dir) if self.dist_dir else _ROOT / "dist"
        super().run()
        if request is None:
            return
        identity = _identity(request)
        prefix = "solweig_light-"
        recent = [p for p in sorted(dist_dir.glob(prefix + "*.whl"))
                  if p.stat().st_mtime >= started - 5]
        if not recent:
            raise RuntimeError(
                f"native-requested build produced no wheel under {dist_dir}")
        failures = []
        for wheel in recent:
            try:
                _assemble.verify_built_wheel(wheel, identity)
            except Exception as exc:  # noqa: BLE001 - loud operator message
                failures.append(f"{wheel.name}: {exc}")
        if failures:
            for wheel in recent:
                wheel.unlink(missing_ok=True)
            raise RuntimeError(
                "NATIVE WHEEL VERIFICATION FAILED (wheels deleted, nothing "
                "shipped): " + " | ".join(failures))


_SETUP_KWARGS: dict = {}
if _assemble is not None:
    class _NativeAwareDistribution(Distribution):
        """Native-requested builds are platform builds (platlib, non-pure
        wheel tags); the C ABI has no Python C API, so this only flips the
        pure/plat decision -- tags are checked by wheel_tags post-build."""

        def has_ext_modules(self):
            return _request() is not None

    _SETUP_KWARGS = {
        "distclass": _NativeAwareDistribution,
        "cmdclass": {"build_py": _GuardedBuildPy,
                     "bdist_wheel": _GuardedBdistWheel},
    }

if __name__ == "__main__":
    setup(**_SETUP_KWARGS)
