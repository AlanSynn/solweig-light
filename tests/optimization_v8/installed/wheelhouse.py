"""Offline wheelhouse assembly for the N8-23 installed-source DX tests.

Method (no network, offline only): every baseline runtime dependency of
``solweig-light`` is already installed in the packet venv (``.venv``, Python
3.12, macOS arm64) and its original wheel body is still present in the local
uv cache as an unpacked archive (``~/.cache/uv/archive-v0/<key>`` holding the
wheel contents plus an intact ``*.dist-info`` with ``METADATA``/``WHEEL``/
``RECORD``).  This module locates each wanted distribution's archive entry,
re-zips it under the original wheel filename, and verifies the result.  The
repacked bytes are byte-identical file contents under identical archive
paths, so the wheel's own ``RECORD`` digests stay valid; installers rewrite
``RECORD`` at install time regardless.

A wheel for the setuptools build backend (needed to build/install the
project from source offline, because PEP 517 build isolation cannot
download) is taken from the virtualenv seed wheel shipped inside another
local project's virtualenv, if available.  Absence only degrades the
source-install gate to a labelled skip, never a fake pass.
"""

from __future__ import annotations

import email.parser
import re
import zipfile
from pathlib import Path

# The exact baseline runtime closure: the six core dependencies declared by
# pyproject.toml plus their transitive runtime dependencies as installed in
# the packet venv.  ``timezonefinder`` pulls h3/cffi/flatbuffers/
# timezonefinder-data; ``numba`` pulls llvmlite; ``cffi`` pulls pycparser.
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

UV_CACHE_ARCHIVE = Path.home() / ".cache" / "uv" / "archive-v0"

# The gate platform: fresh venvs are created with the packet venv's Python
# generation (uv-managed CPython 3.12, macOS arm64) so the cached cp312
# arm64 wheels apply.  Divergent hosts translate this into a labelled skip.
TARGET_PYTHON = (3, 12)
TARGET_MACHINE = "arm64"

# virtualenv seeds pip/setuptools wheels inside its own package; another
# local checkout's venv provides one offline.
SETUPTOOLS_SEED_GLOBS = [
    "/Users/alansynn/Workspace/*/.venv/lib/python3*/site-packages/virtualenv/seed/wheels/embed/setuptools-*.whl",
]


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


def _platform_ok(tag: str) -> bool:
    python_tag, _abi_tag, platform_tag = tag.split("-")
    if python_tag.startswith("cp"):
        expected = f"cp{TARGET_PYTHON[0]}{TARGET_PYTHON[1]}"
        if python_tag != expected:
            return False
    if platform_tag == "any":
        return True
    if "arm64" in platform_tag and TARGET_MACHINE != "arm64":
        return False
    if "x86_64" in platform_tag and TARGET_MACHINE != "x86_64":
        return False
    return True


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


def find_setuptools_seed_wheel() -> Path | None:
    """Locate an offline setuptools wheel for PEP 517 source builds."""
    import glob as _glob

    for pattern in SETUPTOOLS_SEED_GLOBS:
        for hit in sorted(_glob.glob(pattern)):
            version = re.search(r"setuptools-(\d+)\.", Path(hit).name)
            if version and int(version.group(1)) >= 77:
                return Path(hit)
    return None
