"""Wheel tagging rule checker for solweig-light native packaging (N8-20).

Enforces the PACKAGING_AND_DISTRIBUTION.md platform rules:

* any wheel containing a native library is PLATFORM-SPECIFIC: its platform
  tag must never be ``any`` and it must not be purelib
  (``Root-Is-Purelib: false`` in the WHEEL metadata);
* a C-ABI library with NO Python C API (our case: ctypes-called dylib) may
  use a generic Python tag (``py3``) plus a real platform tag; it must not
  be labelled as a stable C-extension ABI (``abi3``/``cpNN`` abi tag)
  unless the C API surface is actually verified -- we do not promise abi3;
* a wheel without native content may be pure/``none-any``;
* the build backend must produce these tags -- renaming wheels manually is
  forbidden. This checker is for builders and tests to VERIFY, and runs on
  wheel FILENAMES (plus optional WHEEL metadata text), so tests need no
  real wheels.

Exit convention for the CLI form: 0 = rules satisfied, 1 = violation.
"""

from __future__ import annotations

import argparse
import json
import re
import sys

# PEP 427 wheel filename: {dist}-{version}(-{build})?-{python}-{abi}-{platform}.whl
_WHEEL_RE = re.compile(
    r"^(?P<dist>[^-]+)-(?P<version>[^-]+)(?:-(?P<build>\d[^-]*))?"
    r"-(?P<python>[^-]+)-(?P<abi>[^-]+)-(?P<platform>[^-]+)\.whl$")

GENERIC_PYTHON_TAGS = {"py3", "py2.py3", "py31", "py32", "py33", "py34",
                       "py35", "py36", "py37", "py38", "py39", "py310",
                       "py311", "py312", "py313"}


class WheelTagError(ValueError):
    """A wheel filename/metadata violates the native packaging rules."""


def parse_wheel_filename(filename: str) -> dict:
    m = _WHEEL_RE.match(filename)
    if not m:
        raise WheelTagError(f"not a valid wheel filename: {filename!r}")
    return m.groupdict()


def check_wheel_tags(filename: str, has_native_lib: bool,
                     wheel_metadata: str | None = None) -> dict:
    """Assert the packaging tag rules for one wheel.

    filename          -- wheel file NAME (no directory)
    has_native_lib    -- whether the wheel bundles a native shared library
    wheel_metadata    -- optional WHEEL metadata text (``Root-Is-Purelib:``
                         is cross-checked when provided)

    Returns the parsed tags on success; raises WheelTagError on violation.
    """
    parts = parse_wheel_filename(filename)
    python_tag = parts["python"]
    abi_tag = parts["abi"]
    platform_tag = parts["platform"]

    if has_native_lib:
        if platform_tag == "any":
            raise WheelTagError(
                f"{filename}: a wheel containing a native library must not "
                f"be platform-independent (platform tag 'any')")
        if "linux" in platform_tag or "macosx" in platform_tag or \
                "win" in platform_tag:
            pass  # concrete platform tag: good
        else:
            raise WheelTagError(
                f"{filename}: unrecognized platform tag {platform_tag!r} "
                f"for a native wheel (expected e.g. macosx_*, manylinux*, "
                f"win_*)")
        if abi_tag == "abi3":
            raise WheelTagError(
                f"{filename}: abi3 claimed without a verified C-API surface "
                f"(abi3 is optional, not an assumed promise)")
        if python_tag not in GENERIC_PYTHON_TAGS and not python_tag.startswith("cp"):
            raise WheelTagError(
                f"{filename}: unexpected python tag {python_tag!r} for a "
                f"native wheel")
        if wheel_metadata is not None:
            root_pure = _root_is_purelib(wheel_metadata)
            if root_pure is True:
                raise WheelTagError(
                    f"{filename}: native wheel declares Root-Is-Purelib: "
                    f"true")
            if root_pure is None:
                raise WheelTagError(
                    f"{filename}: WHEEL metadata lacks Root-Is-Purelib")
    else:
        if platform_tag == "any" and wheel_metadata is not None:
            if _root_is_purelib(wheel_metadata) is False:
                raise WheelTagError(
                    f"{filename}: pure wheel declares Root-Is-Purelib: false")
    return {
        "dist": parts["dist"], "version": parts["version"],
        "python_tag": python_tag, "abi_tag": abi_tag,
        "platform_tag": platform_tag,
    }


def _root_is_purelib(metadata: str) -> bool | None:
    m = re.search(r"^Root-Is-Purelib:\s*(\S+)\s*$", metadata, re.M)
    if not m:
        return None
    return m.group(1).lower() == "true"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="wheel_tags.py",
        description="Verify solweig-light wheel tagging rules (N8-20)")
    parser.add_argument("wheel", help="wheel filename")
    parser.add_argument("--native", action="store_true",
                        help="wheel bundles a native shared library")
    parser.add_argument("--metadata", help="path to the WHEEL metadata file")
    args = parser.parse_args(argv)
    metadata = None
    if args.metadata:
        metadata = open(args.metadata, "r", encoding="utf-8").read()
    try:
        tags = check_wheel_tags(args.wheel, has_native_lib=args.native,
                                wheel_metadata=metadata)
    except WheelTagError as exc:
        print(f"WHEEL TAG RULES VIOLATED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"ok": True, **tags}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
