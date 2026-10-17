#!/usr/bin/env python3
"""Maintainer-side native artifact builder for solweig-light (N8-20).

This is the build-time driver described in BUILD_DESIGN.md (same directory).
It is NOT a runtime component: the installed loader (N8-21) never compiles,
downloads, or writes to HOME; it only reads published generations from
installed package resources.

Properties required by PACKAGING_AND_DISTRIBUTION.md:

* every external tool is invoked as a Python subprocess ARG-LIST with an
  explicit environment -- no /bin/zsh, no shell quoting layer, and no
  /opt/homebrew (or any absolute toolstore) assumption anywhere in this
  driver; the ISPC path comes from --ispc / SOLWEIG_LIGHT_ISPC / PATH and
  its version is pinned-checked before any compile;
* two declared build modes:
    --mode native  ("native release"): MUST produce and self-verify the
        artifact; missing ISPC, a failing FMA audit, or any verification
        error fails the build loudly (nonzero exit, message on stderr);
    --mode source  ("source / no-native fallback"): emits a no-native
        manifest and never touches ISPC, even when ISPC is present;
* the emitted assembly is audited for fused multiply-add mnemonics; a
  contraction-free kernel is a build-time invariant (B7 contract), not a
  hope;
* output is published ATOMICALLY under an immutable content-derived
  generation name: everything is materialized in a private temp directory
  and moved into place with a single rename; an existing generation is
  never overwritten;
* manifest.json follows the versioned schema (manifest_version 1) with
  real sha256 hashes, full flags, toolchain versions, platform facts and
  the audit result, so the loader can verify content, ABI and math
  profile before executing.

Usage:
    python build_native.py build  --kernel lw_primary.ispc --staging DIR [--mode native|source] [options]
    python build_native.py verify --generation-dir DIR

Exit codes: 0 ok, 2 usage, 3 required tool unavailable, 4 build/tool
failure, 5 FMA audit failure, 6 verification failure, 7 generation
collision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

MANIFEST_VERSION = 1
PACKAGE_NAME = "solweig-light"

# Versioned private C ABI of the shipped region library (ARCHITECTURE.md,
# "Suggested native ABI"). The artifact exposes plain C symbols and has no
# Python C API dependency, which is why a generic-py3 + platform wheel tag
# is admissible (BUILD_DESIGN.md, wheel tagging rules).
ABI_VERSION = 1
WRAPPER_ABI_LAYOUT_VERSION = "lw-region-abi-1"

# Math profile identity of this kernel family: strict FP, contraction off,
# no fast-math, default math lib. Must match the numerical certificate of
# the candidate (B7 build contract).
MATH_PROFILE_ID = "lw-primary-strict-fp-contract-off"

# FMA audit: same mnemonic set as the B7 build.sh gate. Any hit is a hard
# build failure.
FMA_MNEMONICS = ("fmadd", "fmla", "fmsub", "fnmadd", "fnmsub", "fnmla")
_FMA_RE = re.compile(r"(?<![A-Za-z0-9_])(?:%s)" % "|".join(FMA_MNEMONICS))

# Manifest fields excluded from the content fingerprint: the generation
# name is DERIVED from the fingerprint and the wall-clock stamp is
# informational only, so both must not feed the hash.
_VOLATILE_KEYS = ("generation", "created_utc")

# Known-bad manifest field values that would silently defeat verification.
_REQUIRED_STRINGS = ("package", "build_mode")


class BuildError(Exception):
    """Any loud build-time failure; str() is the operator-facing message."""


class ToolUnavailable(BuildError):
    exit_code = 3


class ToolFailed(BuildError):
    exit_code = 4


class FmaAuditFailure(BuildError):
    exit_code = 5


class VerifyFailure(BuildError):
    exit_code = 6


class GenerationCollision(BuildError):
    exit_code = 7


class GenerationExists(BuildError):
    exit_code = 7


# --------------------------------------------------------------------------
# subprocess layer: arg-lists only, explicit environment
# --------------------------------------------------------------------------


def _build_env(extra_path: str | None = None) -> dict[str, str]:
    """Explicit, allow-listed environment for child processes.

    Only variables with a real effect on the compiler are forwarded; the
    child never sees the maintainer's full session environment.
    """
    env: dict[str, str] = {
        "PATH": extra_path or os.environ.get("PATH", "/usr/bin:/bin"),
        "LANG": "C",
    }
    for key in ("SDKROOT", "DEVELOPER_DIR", "MACOSX_DEPLOYMENT_TARGET"):
        value = os.environ.get(key)
        if value:
            env[key] = value
    return env


def run_tool(cmd: list[str], cwd: Path | None = None) -> str:
    """Run an argv list; raise loud typed errors on ENOENT / nonzero."""
    argv = [str(a) for a in cmd]
    try:
        proc = subprocess.run(
            argv, cwd=None if cwd is None else str(cwd),
            env=_build_env(), capture_output=True, text=True,
        )
    except FileNotFoundError as exc:
        raise ToolUnavailable(
            f"required tool not found: {argv[0]!r} ({exc})") from exc
    if proc.returncode != 0:
        raise ToolFailed(
            f"command failed ({proc.returncode}): {argv}\n"
            f"stderr:\n{proc.stderr.strip()[:4000]}")
    return proc.stdout


# --------------------------------------------------------------------------
# tool discovery and identity (no absolute toolstore assumptions)
# --------------------------------------------------------------------------


def discover_ispc(explicit: str | None) -> Path:
    """explicit --ispc > SOLWEIG_LIGHT_ISPC > PATH lookup. Never a
    hard-coded fallback path."""
    if explicit:
        path = Path(explicit)
        if not path.is_file():
            raise ToolUnavailable(f"--ispc {path} is not a file")
        return path
    env = os.environ.get("SOLWEIG_LIGHT_ISPC")
    if env:
        path = Path(env)
        if not path.is_file():
            raise ToolUnavailable(
                f"SOLWEIG_LIGHT_ISPC={env!r} is not a file")
        return path
    found = shutil.which("ispc", path=_build_env()["PATH"])
    if not found:
        raise ToolUnavailable(
            "ispc not found: pass --ispc, set SOLWEIG_LIGHT_ISPC, or put "
            "ispc on PATH (native release mode requires the pinned ISPC)")
    return Path(found)


def ispc_identity(ispc: Path, pinned_version: str) -> dict:
    """Run `ispc --version`, require the pinned series, return identity."""
    out = run_tool([ispc, "--version"])
    match = re.search(r"ISPC.*?,\s*v?([0-9][^\s,]+)", out)
    if not match:
        raise ToolUnavailable(
            f"cannot parse ispc version output: {out.strip()[:200]!r}")
    version = match.group(1)
    llvm_m = re.search(r"LLVM\s*v?([0-9][^\s,)]+)", out)
    llvm = llvm_m.group(1) if llvm_m else "unknown"
    if not version.startswith(pinned_version):
        raise ToolUnavailable(
            f"ISPC version pin violated: found {version}, pinned "
            f"{pinned_version}. Refusing to build an artifact whose "
            f"toolchain identity was not qualified.")
    return {"version": version, "llvm": llvm,
            "path": str(ispc), "sha256": _sha256_file(ispc)}


def cc_identity(cc: Path) -> dict:
    first = run_tool([cc, "--version"]).splitlines()[0].strip()
    kind = "clang" if "clang" in first.lower() else (
        "gcc" if "gcc" in first.lower() else "unknown")
    return {"kind": kind, "version": first, "path": str(cc),
            "sha256": _sha256_file(cc)}


# --------------------------------------------------------------------------
# FMA audit (build-time invariant)
# --------------------------------------------------------------------------


@dataclass
class FmaAuditResult:
    passed: bool
    matches: list[dict]

    def to_manifest(self, asm_sha256: str) -> dict:
        return {
            "passed": self.passed,
            "tool": "regex-text-scan",
            "mnemonics": list(FMA_MNEMONICS),
            "matches": self.matches,
            "match_count": len(self.matches),
            "asm_sha256": asm_sha256,
        }


def fma_audit(asm_text: str) -> FmaAuditResult:
    """Scan emitted assembly for fused multiply-add mnemonics.

    Every hit is recorded with its line number; any hit fails the build.
    """
    matches = []
    for lineno, line in enumerate(asm_text.splitlines(), start=1):
        for m in _FMA_RE.finditer(line):
            matches.append({
                "line": lineno,
                "mnemonic": m.group(0),
                "text": line.strip()[:200],
            })
    return FmaAuditResult(passed=not matches, matches=matches)


def audit_or_fail(asm_text: str, asm_name: str) -> FmaAuditResult:
    result = fma_audit(asm_text)
    if not result.passed:
        hits = "; ".join(
            f"{m['mnemonic']}@line{m['line']}" for m in result.matches[:10])
        raise FmaAuditFailure(
            f"FMA AUDIT FAILED in {asm_name}: contraction present "
            f"({len(result.matches)} hits: {hits}). The baseline graph has "
            f"separate mul/add nodes (fastmath=False); contraction would "
            f"change the arithmetic graph. Refusing to publish.")
    return result


# --------------------------------------------------------------------------
# platform facts (recorded into the manifest, verified by the loader)
# --------------------------------------------------------------------------


def macho_facts(dylib: Path) -> dict:
    """Extract min-OS, arch and external link deps of a Mach-O dylib.

    Required on darwin builds: a manifest that cannot state its platform
    facts is not publishable. (Linux equivalents -- readelf/objdump -- are
    a documented future step in BUILD_DESIGN.md, not silently skipped.)
    """
    if not shutil.which("otool", path=_build_env()["PATH"]):
        raise ToolUnavailable(
            "otool not found on PATH; cannot record min-OS/arch/link deps "
            "for a darwin artifact")
    if not _is_macho(dylib):
        raise VerifyFailure(f"{dylib.name} is not a Mach-O image")

    # otool -L line 1 is the header; line 2 is always the image's own
    # LC_ID_DYLIB install name -- only the following lines are dependencies.
    deps = [
        line.split("(")[0].strip()
        for line in run_tool(["otool", "-L", dylib]).splitlines()[2:]
        if line.strip()
    ]
    load_cmds = run_tool(["otool", "-l", dylib])
    header = run_tool(["otool", "-h", dylib])
    minos = re.search(r"LC_BUILD_VERSION.*?minos\s+(\S+)", load_cmds, re.S)
    # otool -h prints a column table: magic cputype cpusubtype caps ...
    # cputype is the SECOND whitespace-separated field of the value row.
    cputype = re.search(
        r"^\s*magic\s+cputype.*$\n^\s*\S+\s+(\d+)", header, re.M)
    if not minos or not cputype:
        raise VerifyFailure(
            f"cannot parse LC_BUILD_VERSION/cputype from otool output of "
            f"{dylib.name}")
    arch = {"16777228": "arm64", "16777223": "x86_64"}.get(
        cputype.group(1), f"cputype-{cputype.group(1)}")
    return {"link_deps": deps, "os_min_version": minos.group(1),
            "arch": arch}


def _is_macho(path: Path) -> bool:
    try:
        return path.read_bytes()[:4] == b"\xcf\xfa\xed\xfe"  # MH_MAGIC_64
    except OSError:
        return False


def macho_structure_error(path: Path) -> str | None:
    """Pure-Python Mach-O 64 integrity walk: returns None when the image's
    header, load commands and segment file ranges are all inside the file.

    A content hash only proves the bytes are the bytes someone recorded;
    THIS check is what catches truncation/corruption of a shipped image
    (a truncated dylib keeps its magic). The loader (N8-21) reuses it.
    """
    data = path.read_bytes()
    if data[:4] == b"\xca\xfe\xba\xbe":
        return "universal (fat) images are not shippable artifacts"
    if data[:4] != b"\xcf\xfa\xed\xfe":
        return f"bad Mach-O 64 magic {data[:4].hex()}"
    if len(data) < 32:
        return "truncated Mach-O header"
    ncmds = int.from_bytes(data[16:20], "little")
    sizeofcmds = int.from_bytes(data[20:24], "little")
    if 32 + sizeofcmds > len(data):
        return "load commands extend past end of file (truncated?)"
    off = 32
    for i in range(ncmds):
        if off + 8 > len(data):
            return f"load command {i} truncated"
        cmd = int.from_bytes(data[off:off + 4], "little")
        cmdsize = int.from_bytes(data[off + 4:off + 8], "little")
        if cmdsize < 8 or off + cmdsize > len(data):
            return f"load command {i} overruns the file"
        if cmd == 0x19:  # LC_SEGMENT_64
            fileoff = int.from_bytes(data[off + 40:off + 48], "little")
            filesize = int.from_bytes(data[off + 48:off + 56], "little")
            if fileoff + filesize > len(data):
                return (f"segment (load command {i}) claims bytes "
                        f"{fileoff}..{fileoff + filesize} beyond EOF "
                        f"({len(data)}): truncated or corrupt")
        off += cmdsize
    if off != 32 + sizeofcmds:
        return "load command sizes disagree with sizeofcmds"
    return None


# --------------------------------------------------------------------------
# manifest: schema, validation, fingerprint, generation naming
# --------------------------------------------------------------------------


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def build_manifest(*, build_mode: str, kernel_path: Path, artifacts: list[dict],
                   generated_sources: list[dict], toolchain: dict,
                   target: str, ispc_flags: list[str], cc_flags: list[str],
                   platform: dict, scalar_profiles: dict,
                   exported_symbols: list[str], fma_audit_entry: dict | None,
                   artifact_tag: str) -> dict:
    return {
        "manifest_version": MANIFEST_VERSION,
        "build_mode": build_mode,
        "package": PACKAGE_NAME,
        "abi": {
            "abi_version": ABI_VERSION,
            "wrapper_abi_layout_version": WRAPPER_ABI_LAYOUT_VERSION,
            "exported_symbols": exported_symbols,
            "python_c_api": False,
        },
        "kernel": {
            "name": kernel_path.name,
            "sha256": _sha256_file(kernel_path),
            "source_ref":
                "src/solweig_light/backends/native/" + kernel_path.name,
        },
        "generated_sources": generated_sources,
        "toolchain": toolchain,
        "build": {
            "target": target,
            "ispc_flags": ispc_flags,
            "cc_flags": cc_flags,
            "link_deps": platform.get("link_deps", []),
        },
        "math_profile": {
            "id": MATH_PROFILE_ID,
            "fast_math": False,
            "fma_contraction": "disabled",
            "math_lib": "default",
        },
        "scalar_profiles": scalar_profiles,
        "platform": platform,
        "artifacts": artifacts,
        "fma_audit": fma_audit_entry,
        "artifact_tag": artifact_tag,
    }


def validate_manifest(manifest: dict) -> list[str]:
    """Return a list of schema violations (empty == valid).

    Mode-aware: ``native-release`` manifests carry the full toolchain,
    artifact and audit identity; a ``source-no-native`` manifest declares
    the ABSENCE of native content and may leave those fields unset.
    """
    errors: list[str] = []
    strict = manifest.get("build_mode") == "native-release"

    if manifest.get("manifest_version") != MANIFEST_VERSION:
        errors.append(f"manifest_version must be {MANIFEST_VERSION}")
    for key in _REQUIRED_STRINGS:
        if not manifest.get(key):
            errors.append(f"missing required field: {key}")
    abi = manifest.get("abi")
    if not isinstance(abi, dict):
        errors.append("abi: missing object")
    else:
        if abi.get("abi_version") != ABI_VERSION:
            errors.append(f"abi.abi_version must be {ABI_VERSION}")
        if not abi.get("wrapper_abi_layout_version"):
            errors.append("abi.wrapper_abi_layout_version: missing")
        if strict and not abi.get("exported_symbols"):
            errors.append("abi.exported_symbols: native-release needs the "
                          "exported C symbols")
    kernel = manifest.get("kernel")
    if kernel is not None:
        if not isinstance(kernel, dict) or not kernel.get("sha256"):
            errors.append("kernel: must be an object with sha256")
        elif not re.fullmatch(r"[0-9a-f]{64}", kernel.get("sha256", "")):
            errors.append("kernel.sha256: not a lowercase hex sha256")
    elif strict:
        errors.append("kernel: native-release must record the kernel hash")
    for entry in manifest.get("generated_sources", []):
        if not (entry.get("path") and entry.get("sha256")):
            errors.append(f"generated_sources entry missing path/sha256: {entry}")
        elif not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]):
            errors.append(f"generated_sources {entry['path']}: sha256 not "
                          f"lowercase hex")
    toolchain = manifest.get("toolchain")
    if strict and (not isinstance(toolchain, dict)
                   or "ispc" not in toolchain or "cc" not in toolchain):
        errors.append("toolchain: native-release needs ispc and cc identity")
    build = manifest.get("build")
    if not isinstance(build, dict):
        errors.append("build: missing object")
    else:
        if strict and not build.get("target"):
            errors.append("build.target: missing")
        if strict and (not isinstance(build.get("ispc_flags"), list)
                       or not build["ispc_flags"]):
            errors.append("build.ispc_flags: must be a non-empty list")
        if not isinstance(build.get("cc_flags"), list):
            errors.append("build.cc_flags: must be a list")
    if not isinstance(manifest.get("math_profile"), dict):
        errors.append("math_profile: missing object")
    elif not manifest["math_profile"].get("id"):
        errors.append("math_profile.id: missing")
    profiles = manifest.get("scalar_profiles")
    if not isinstance(profiles, dict):
        errors.append("scalar_profiles: missing map")
    elif strict:
        for required in ("f32", "f64"):
            prof = profiles.get(required)
            if not isinstance(prof, dict) or not prof.get("symbol"):
                errors.append(
                    f"scalar_profiles.{required}: needs a symbol entry")
    platform_ = manifest.get("platform")
    if not isinstance(platform_, dict):
        errors.append("platform: missing object")
    else:
        for key in ("os", "arch"):
            if not platform_.get(key):
                errors.append(f"platform.{key}: missing")
        if strict and not platform_.get("os_min_version"):
            errors.append("platform.os_min_version: missing")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        errors.append("artifacts: missing list")
    else:
        for entry in artifacts:
            if not (entry.get("path") and entry.get("sha256")
                    and isinstance(entry.get("bytes"), int)):
                errors.append(f"artifacts entry incomplete: {entry}")
            elif not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]):
                errors.append(f"artifacts {entry['path']}: sha256 not "
                              f"lowercase hex")
    if strict:
        audit = manifest.get("fma_audit")
        if not isinstance(audit, dict) or audit.get("passed") is not True:
            errors.append(
                "fma_audit: native-release manifest must record a PASSED "
                "disassembly audit")
        if not artifacts:
            errors.append("artifacts: native-release must bundle a library")
    return errors


def manifest_fingerprint(manifest: dict) -> str:
    """sha256 over the canonical JSON of all non-volatile fields."""
    core = {k: v for k, v in manifest.items() if k not in _VOLATILE_KEYS}
    blob = json.dumps(core, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def generation_name(manifest: dict, prefix: str = "lw") -> str:
    """Immutable, content-derived generation name."""
    tag = manifest.get("artifact_tag") or "gen"
    return f"{prefix}-{tag}-{manifest_fingerprint(manifest)[:16]}"


# --------------------------------------------------------------------------
# atomic publication
# --------------------------------------------------------------------------


def atomic_publish(staging: Path, generation: str,
                   producers: dict[str, "callable"]) -> Path:
    """Materialize `producers` (name -> bytes callable) in a private temp
    dir inside `staging`, fsync, then rename into `staging/<generation>`.

    The single rename is the publication point: an observer either sees
    the complete previous state or the complete new generation, never a
    half-published directory. Any exception removes the temp dir.
    """
    staging = staging.resolve()
    staging.mkdir(parents=True, exist_ok=True)
    target = staging / generation
    if target.exists():
        raise GenerationExists(
            f"generation {generation} already published (generations are "
            f"immutable; never overwrite -- pick the new content hash)")
    tmp = staging / f".tmp-publish-{os.getpid()}-{uuid.uuid4().hex[:12]}"
    try:
        tmp.mkdir()
        for name, produce in producers.items():
            dest = tmp / name
            if "/" in name or name in (".", ".."):
                raise BuildError(f"refusing non-contained path {name!r}")
            data = produce()
            with open(dest, "wb") as fh:
                fh.write(data)
                fh.flush()
                os.fsync(fh.fileno())
        dfd = os.open(tmp, os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
        os.rename(tmp, target)  # atomic publication point
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    dfd = os.open(staging, os.O_RDONLY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)
    return target


# --------------------------------------------------------------------------
# verification (shared by the driver's post-build self-check, the `verify`
# subcommand, and the packaged loader contract)
# --------------------------------------------------------------------------


def verify_generation(gen_dir: Path) -> dict:
    """Full content verification of a published generation directory."""
    manifest_path = gen_dir / "manifest.json"
    if not manifest_path.is_file():
        raise VerifyFailure(f"{gen_dir}: no manifest.json")
    try:
        manifest = json.loads(manifest_path.read_text())
    except ValueError as exc:
        raise VerifyFailure(f"{gen_dir}: manifest.json is not valid JSON "
                            f"({exc})")
    errors = validate_manifest(manifest)
    if errors:
        raise VerifyFailure(
            f"{gen_dir}: manifest schema violations: {'; '.join(errors)}")

    expected = generation_name(manifest)
    if gen_dir.name != expected:
        raise VerifyFailure(
            f"{gen_dir}: generation name mismatch: directory is "
            f"{gen_dir.name!r}, manifest content derives {expected!r}")

    for entry in manifest.get("generated_sources", []):
        f = gen_dir / entry["path"]
        if not f.is_file():
            raise VerifyFailure(f"{gen_dir}: generated source "
                                f"{entry['path']} missing")
        if _sha256_file(f) != entry["sha256"]:
            raise VerifyFailure(f"{gen_dir}: generated source "
                                f"{entry['path']} hash mismatch")

    for entry in manifest.get("artifacts", []):
        f = gen_dir / entry["path"]
        if not f.is_file():
            raise VerifyFailure(f"{gen_dir}: artifact {entry['path']} missing")
        if _sha256_file(f) != entry["sha256"]:
            raise VerifyFailure(f"{gen_dir}: artifact {entry['path']} hash "
                                f"mismatch")
        if entry["path"].endswith(".dylib"):
            problem = macho_structure_error(f)
            if problem:
                raise VerifyFailure(
                    f"{gen_dir}: artifact {entry['path']}: {problem}")
        if entry.get("bytes") is not None and \
                f.stat().st_size != entry["bytes"]:
            raise VerifyFailure(f"{gen_dir}: artifact {entry['path']} size "
                                f"drifted from the manifest record")

    audit = manifest.get("fma_audit")
    if manifest.get("build_mode") == "native-release":
        asm_entries = [e for e in manifest.get("generated_sources", [])
                       if e["path"].endswith(".s")]
        if not asm_entries:
            raise VerifyFailure(
                f"{gen_dir}: native-release must ship the audited assembly")
        for entry in asm_entries:
            if _sha256_file(gen_dir / entry["path"]) != audit["asm_sha256"]:
                raise VerifyFailure(
                    f"{gen_dir}: audited asm {entry['path']} no longer "
                    f"matches fma_audit.asm_sha256")
        result = fma_audit((gen_dir / asm_entries[0]["path"]).read_text(
            errors="replace"))
        if not result.passed:
            raise VerifyFailure(
                f"{gen_dir}: re-audit of shipped asm found contraction: "
                f"{result.matches[:5]}")
    return manifest


# --------------------------------------------------------------------------
# the native build pipeline
# --------------------------------------------------------------------------


def native_build_impl(*, kernel: Path, staging: Path, target: str,
                      artifact: str, ispc_path: Path | None, ispc_pin: str,
                      cc_name: str, ispc_flags: list[str],
                      cc_flags: list[str], install_name: str | None,
                      gen_prefix: str, verbose: bool = False) -> dict:
    """Single-pass implementation: compile into one private dir, audit,
    hash in place, publish atomically, then self-verify the publication."""
    if not kernel.is_file():
        raise BuildError(f"kernel not found: {kernel}")
    stem = kernel.stem
    m = re.fullmatch(r"liblw_native_(g\d+)\.dylib", artifact)
    if not m:
        raise BuildError(
            f"artifact name {artifact!r} does not match "
            f"liblw_native_g<lanes>.dylib")
    tag = m.group(1)
    obj_name = f"{stem}_{tag}.o"
    header_name = f"{stem}_{tag}.h"
    asm_name = f"{stem}_{tag}.s"

    staging = staging.resolve()

    ispc = discover_ispc(ispc_path and str(ispc_path))
    ispc_id = ispc_identity(ispc, ispc_pin)
    cc_path = shutil.which(cc_name, path=_build_env()["PATH"])
    if cc_path is None and Path(cc_name).is_file():
        cc_path = cc_name
    if cc_path is None:
        raise ToolUnavailable(
            f"C compiler {cc_name!r} not found on PATH (native release "
            f"mode requires the linker stage)")
    cc = Path(cc_path)
    cc_id = cc_identity(cc)

    build_dir = Path(tempfile.mkdtemp(prefix="n820-build-"))
    try:
        shutil.copyfile(kernel, build_dir / kernel.name)
        common = [f"--target={target}", *ispc_flags]

        for label, cmd in (
                ("ispc object+header", [ispc, kernel.name, "-o", obj_name,
                                        "-h", header_name, *common]),
                ("ispc asm emit", [ispc, kernel.name, "--emit-asm",
                                   "-o", asm_name, *common]),
        ):
            if verbose:
                print(f"[n820] {label}: {cmd}", file=sys.stderr)
            run_tool(cmd, cwd=build_dir)

        asm_text = (build_dir / asm_name).read_text(errors="replace")
        audit = audit_or_fail(asm_text, asm_name)

        link_cmd = [cc, *cc_flags]
        if install_name:
            link_cmd += ["-install_name", install_name]
        link_cmd += ["-o", artifact, obj_name]
        if verbose:
            print(f"[n820] link: {link_cmd}", file=sys.stderr)
        run_tool(link_cmd, cwd=build_dir)

        facts = macho_facts(build_dir / artifact)

        manifest = build_manifest(
            build_mode="native-release",
            kernel_path=kernel,
            artifact_tag=tag,
            artifacts=[{
                "path": artifact, "kind": "shared-library",
                "binary_format": "mach-o-dylib",
                "sha256": _sha256_file(build_dir / artifact),
                "bytes": (build_dir / artifact).stat().st_size,
            }],
            generated_sources=[
                {"path": header_name, "kind": "ispc-generated-header",
                 "sha256": _sha256_file(build_dir / header_name)},
                {"path": asm_name, "kind": "disassembly-audit-copy",
                 "sha256": _sha256_file(build_dir / asm_name)},
            ],
            toolchain={"ispc": ispc_id, "cc": cc_id},
            target=target, ispc_flags=ispc_flags, cc_flags=cc_flags,
            platform={
                "os": sys.platform,
                "os_min_version": facts["os_min_version"],
                "arch": facts["arch"],
                "requirements": ["cpu-feature:neon"],
                "link_deps": facts["link_deps"],
            },
            scalar_profiles={
                "f32": {"symbol": "lw_primary_f32",
                        "surface_scalars": "float32"},
                "f64": {"symbol": "lw_primary_f64",
                        "surface_scalars": "float64",
                        "accumulator_round": "float32-at-accumulator-add"},
            },
            exported_symbols=["lw_primary_f32", "lw_primary_f64"],
            fma_audit_entry=audit.to_manifest(
                _sha256_file(build_dir / asm_name)),
        )
        manifest["generation"] = generation_name(manifest, gen_prefix)
        manifest["created_utc"] = datetime.now(
            timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        producers = {
            artifact: lambda: (build_dir / artifact).read_bytes(),
            header_name: lambda: (build_dir / header_name).read_bytes(),
            asm_name: lambda: (build_dir / asm_name).read_bytes(),
            "manifest.json": lambda: json.dumps(
                manifest, indent=2, sort_keys=True).encode() + b"\n",
        }
        target_dir = atomic_publish(staging, manifest["generation"],
                                    producers)
    finally:
        shutil.rmtree(build_dir, ignore_errors=True)

    verified = verify_generation(target_dir)
    return {"generation_dir": target_dir, "manifest": verified}


def source_fallback_manifest(staging: Path, kernel: Path | None,
                             gen_prefix: str) -> dict:
    """Declared no-native fallback build: no artifact, no compiler, no
    ISPC invocation. The loader must treat this manifest as an explicit
    'native absent' marker and quietly decline to Numba."""
    manifest = {
        "manifest_version": MANIFEST_VERSION,
        "build_mode": "source-no-native",
        "package": PACKAGE_NAME,
        "abi": {
            "abi_version": ABI_VERSION,
            "wrapper_abi_layout_version": WRAPPER_ABI_LAYOUT_VERSION,
            "exported_symbols": [],
            "python_c_api": False,
        },
        "kernel": ({"name": kernel.name,
                    "sha256": _sha256_file(kernel),
                    "source_ref":
                        "src/solweig_light/backends/native/" + kernel.name}
                   if kernel else None),
        "generated_sources": [],
        "toolchain": None,
        "build": {"target": None, "ispc_flags": [], "cc_flags": [],
                  "link_deps": []},
        "math_profile": {"id": MATH_PROFILE_ID, "fast_math": False,
                         "fma_contraction": "disabled",
                         "math_lib": "default"},
        "scalar_profiles": {},
        "platform": {"os": sys.platform, "os_min_version": None,
                     "arch": "any", "requirements": [],
                     "link_deps": []},
        "artifacts": [],
        "fma_audit": None,
        "artifact_tag": "none",
        "note": ("no native artifacts and no compiler: the packaged loader "
                 "must quietly auto-decline to the Numba path, which is "
                 "NOT native-qualified"),
    }
    manifest["generation"] = generation_name(manifest, gen_prefix)
    manifest["created_utc"] = datetime.now(
        timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    producers = {"manifest.json": lambda: json.dumps(
        manifest, indent=2, sort_keys=True).encode() + b"\n"}
    target_dir = atomic_publish(staging.resolve(), manifest["generation"],
                                producers)
    verified = verify_generation(target_dir)
    return {"generation_dir": target_dir, "manifest": verified}


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="build_native.py",
        description="Maintainer-side native artifact builder "
                    "(N8-20); see BUILD_DESIGN.md")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p):
        p.add_argument("--staging", type=Path, required=True,
                       help="output staging directory (generations are "
                            "published atomically inside it)")
        p.add_argument("--gen-prefix", default="lw",
                       help="generation-name prefix (default: lw)")
        p.add_argument("--verbose", action="store_true")

    p_build = sub.add_parser("build", help="build + publish a generation")
    add_common(p_build)
    p_build.add_argument("--mode", choices=("native", "source"),
                         default="native",
                         help="native = native release build (artifact "
                              "REQUIRED, loud failure); source = declared "
                              "no-native fallback (ISPC never invoked)")
    p_build.add_argument("--kernel", type=Path,
                         help="kernel .ispc source (native mode)")
    p_build.add_argument("--target", default="neon-i32x8",
                         help="ISPC target (default: neon-i32x8)")
    p_build.add_argument("--artifact", default="liblw_native_g8.dylib",
                         help="library filename to publish")
    p_build.add_argument("--ispc", type=Path, default=None)
    p_build.add_argument("--ispc-version", default="1.31.0",
                         help="pinned ISPC version series (default 1.31.0)")
    p_build.add_argument("--cc", default="clang")
    p_build.add_argument("--ispc-flag", action="append",
                         default=["-O2", "--opt=disable-fma",
                                  "--math-lib=default", "--pic"],
                         help="extra ISPC flag (repeatable; B7 defaults "
                              "preloaded)")
    p_build.add_argument("--cc-flag", action="append",
                         default=["-arch", "arm64", "-dynamiclib"],
                         help="extra linker flag (repeatable; B7 defaults "
                              "preloaded)")
    p_build.add_argument("--install-name", default=None,
                         help="dylib install name (default: bare basename, "
                              "B7 dev-cache parity; bundled wheels pass "
                              "@rpath/<name>)")

    p_verify = sub.add_parser("verify",
                              help="verify a published generation directory")
    p_verify.add_argument("--generation-dir", type=Path, required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            manifest = verify_generation(args.generation_dir)
            print(json.dumps({
                "generation_dir": str(args.generation_dir),
                "generation": manifest["generation"],
                "build_mode": manifest["build_mode"],
                "verified": True,
            }, indent=2))
            return 0

        staging = args.staging
        if args.mode == "source":
            result = source_fallback_manifest(
                staging, args.kernel, args.gen_prefix)
        else:
            if args.kernel is None:
                parser.error("--kernel is required in --mode native")
            result = native_build_impl(
                kernel=args.kernel, staging=staging, target=args.target,
                artifact=args.artifact, ispc_path=args.ispc,
                ispc_pin=args.ispc_version, cc_name=args.cc,
                ispc_flags=list(args.ispc_flag),
                cc_flags=list(args.cc_flag),
                install_name=args.install_name,
                gen_prefix=args.gen_prefix, verbose=args.verbose)
        print(json.dumps({
            "generation_dir": str(result["generation_dir"]),
            "generation": result["manifest"]["generation"],
            "build_mode": result["manifest"]["build_mode"],
            "artifact_sha256": (result["manifest"]["artifacts"][0]["sha256"]
                                if result["manifest"]["artifacts"]
                                else None),
        }, indent=2))
        return 0
    except BuildError as exc:
        print(f"BUILD FAILED: {exc}", file=sys.stderr)
        return getattr(exc, "exit_code", 4)
    except OSError as exc:
        print(f"BUILD FAILED (io): {exc}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    sys.exit(main())
