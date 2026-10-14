"""Offline wheelhouse assembly for the S10-31 installed-source DX tests.

Method (no network, offline only): every runtime dependency of
``solweig-light`` at the pinned baseline versions is already installed in
the packet venv (``.venv``, CPython 3.12.15, linux x86_64) and its original
wheel body is still present in the local uv cache as an unpacked archive
(``~/.cache/uv/archive-v0/<key>`` holding the wheel contents plus an intact
``*.dist-info`` with ``METADATA``/``WHEEL``/``RECORD``).  This module
locates each wanted distribution's archive entry, re-zips it under the
original wheel filename, and verifies the result (port of the v8 method;
versions re-pinned to this host's installed closure, platform check made
abi3-aware because timezonefinder 9.0.0 ships as ``cp311-abi3``).

A wheel for the setuptools build backend (needed to build/install the
project from source offline, because PEP 517 build isolation cannot
download) is repacked from the uv cache the same way (uv's seed wheels live
inside the binary, not on disk).
"""

from __future__ import annotations

import email.parser
import re
import zipfile
from pathlib import Path

# The exact runtime closure declared by pyproject.toml (six dependencies)
# plus their transitive runtime dependencies as installed in the packet
# venv: timezonefinder pulls h3/cffi/flatbuffers/timezonefinder-data; numba
# pulls llvmlite; cffi pulls pycparser.
RUNTIME_CLOSURE: dict[str, str] = {
    "numpy": "2.4.6",
    "scipy": "1.17.1",
    "numba": "0.67.0",
    "llvmlite": "0.49.0",
    "gdal": "3.13.3",
    "pytz": "2026.3.post1",
    "timezonefinder": "9.0.0",
    "timezonefinder-data": "3.2026.3.post1",
    "h3": "4.5.0",
    "cffi": "2.1.1",
    "pycparser": "3.0",
    "flatbuffers": "25.12.19",
}

# The build backend for source builds/wheels (pyproject: setuptools>=77);
# repacked from the same cache, not part of the runtime closure.
SETUPTOOLS_SEED = ("setuptools", "84.0.0")

UV_CACHE_ARCHIVE = Path.home() / ".cache" / "uv" / "archive-v0"

# The gate platform: fresh venvs are created from the packet venv's
# interpreter generation.  Divergent hosts translate this into a labelled
# skip.
TARGET_PYTHON = (3, 12)
TARGET_MACHINE = "x86_64"


class WheelhouseUnavailable(RuntimeError):
    """A prerequisite for offline assembly is missing in this environment."""


def _dist_info(metadata_dir: Path) -> tuple[str, str]:
    text = (metadata_dir / "METADATA").read_text(encoding="utf-8", errors="replace")
    message = email.parser.Parser().parsestr(text, headersonly=True)
    return message["Name"].lower(), message["Version"]


def _wheel_tags(metadata_dir: Path) -> list[str]:
    wheel = metadata_dir / "WHEEL"
    if not wheel.exists():
        raise WheelhouseUnavailable(f"archive entry {metadata_dir} has no WHEEL file")
    return [
        line.split(":", 1)[1].strip()
        for line in wheel.read_text(encoding="utf-8").splitlines()
        if line.startswith("Tag:")
    ]


def _python_tag_ok(python_tag: str) -> bool:
    if not python_tag.startswith("cp"):
        return True  # py3x / py2 wildcard tags
    if python_tag == f"cp{TARGET_PYTHON[0]}{TARGET_PYTHON[1]}":
        return True
    # abi3 wheels are upward-compatible from their lower bound (e.g.
    # cp311-abi3 installs on cp312); the tag carries major+minor after the
    # implementation prefix, so the minor is everything past "cp<major>".
    return False


def _platform_ok(tag: str) -> bool:
    python_tag, abi_tag, platform_tag = tag.split("-")
    if abi_tag == "abi3":
        if python_tag.startswith("cp"):
            wheel_minor = int(python_tag[2 + len(str(TARGET_PYTHON[0])):])
            if wheel_minor > TARGET_PYTHON[1]:
                return False
        return platform_tag == "any" or TARGET_MACHINE in platform_tag
    if not _python_tag_ok(python_tag):
        return False
    if platform_tag == "any":
        return True
    return TARGET_MACHINE in platform_tag


def _find_archive(name: str, version: str) -> Path:
    """Locate the unpacked uv-cache wheel archive for one distribution."""
    if not UV_CACHE_ARCHIVE.is_dir():
        raise WheelhouseUnavailable(
            f"uv cache archive {UV_CACHE_ARCHIVE} not present; cannot assemble "
            "an offline wheelhouse"
        )
    matches: list[Path] = []
    for entry in sorted(UV_CACHE_ARCHIVE.iterdir()):
        infos = list(entry.glob("*.dist-info"))
        if len(infos) != 1:
            continue
        try:
            found_name, found_version = _dist_info(infos[0])
        except (OSError, KeyError, TypeError):
            continue
        if found_name == name.lower() and found_version == version:
            matches.append(entry)
    candidates = []
    for entry in matches:
        tags = _wheel_tags(list(entry.glob("*.dist-info"))[0])
        if any(_platform_ok(tag) for tag in tags):
            candidates.append(entry)
    if not candidates:
        raise WheelhouseUnavailable(
            f"no uv-cache archive for {name}=={version} matching this "
            f"interpreter/platform (searched {len(matches)} version matches)"
        )
    return candidates[0]


def _wheel_filename(name: str, version: str, tags: list[str]) -> str:
    escaped = re.sub(r"[^\w\d.]+", "_", name, flags=re.UNICODE)
    ver = re.sub(r"[^\w\d.]+", "_", version, flags=re.UNICODE)
    python_tags = ".".join(sorted({tag.split("-")[0] for tag in tags}))
    abi_tags = ".".join(sorted({tag.split("-")[1] for tag in tags}))
    platform_tags = ".".join(sorted({tag.split("-")[2] for tag in tags}))
    return f"{escaped}-{ver}-{python_tags}-{abi_tags}-{platform_tags}.whl"


def repack_archive(archive: Path, target: Path) -> Path:
    """Zip an unpacked wheel archive back into a wheel file."""
    contents = sorted(archive.rglob("*"))
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in contents:
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            arcname = path.relative_to(archive).as_posix()
            mode = (path.stat().st_mode & 0o555) << 16
            zf.write(path, arcname, compresslevel=6)
            # preserve the executable bit shared libraries rely on
            info = zf.getinfo(arcname)
            info.external_attr = mode | (info.external_attr & 0xFFFF)
    return target


def verify_wheel(path: Path, name: str, version: str) -> None:
    """A repacked wheel must carry its dist-info and match METADATA."""
    canonical = name.lower().replace("-", "_")
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        dist_info = f"{canonical}-{version}.dist-info/METADATA"
        if dist_info not in names:
            raise WheelhouseUnavailable(f"{path.name}: missing {dist_info}")
        message = email.parser.Parser().parsestr(
            zf.read(dist_info).decode("utf-8", errors="replace"), headersonly=True)
        if message["Name"].lower() != name.lower() or message["Version"] != version:
            raise WheelhouseUnavailable(f"{path.name}: METADATA mismatch")


def build_wheelhouse(target_dir: Path) -> dict[str, str]:
    """Assemble every runtime-closure wheel into ``target_dir``.

    Returns ``{distribution: wheel filename}``.  Raises
    :class:`WheelhouseUnavailable` when the offline cache cannot satisfy the
    closure; callers translate that into a labelled skip.
    """
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    built: dict[str, str] = {}
    for name, version in sorted(RUNTIME_CLOSURE.items()):
        archive = _find_archive(name, version)
        tags = _wheel_tags(list(archive.glob("*.dist-info"))[0])
        out = target_dir / _wheel_filename(name, version, tags)
        if not out.exists():
            repack_archive(archive, out)
        verify_wheel(out, name, version)
        built[name] = out.name
    return built


def find_setuptools_seed_wheel(target_dir: Path) -> Path:
    """Repack the offline setuptools wheel into ``target_dir``."""
    name, version = SETUPTOOLS_SEED
    archive = _find_archive(name, version)
    tags = _wheel_tags(list(archive.glob("*.dist-info"))[0])
    out = Path(target_dir) / _wheel_filename(name, version, tags)
    if not out.exists():
        repack_archive(archive, out)
    verify_wheel(out, name, version)
    return out
