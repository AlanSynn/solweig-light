#!/usr/bin/env python3
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
"""Native-wheel assembly for solweig-light (N8-41 wheel step).

The maintainer-facing contract of PACKAGING_AND_DISTRIBUTION.md, encoded:

* A build WITHOUT the native request is the declared source/no-native
  fallback: a pure wheel, unchanged byte-for-byte in mechanism.  If native
  generation content is present in the package source tree anyway, the
  pure build FAILS LOUDLY instead of silently shipping native content in a
  wheel tagged ``py3-none-any``/``Root-Is-Purelib: true``.
* A build WITH the native request (``SOLWEIG_LIGHT_PACKAGE_NATIVE`` =
  path to a LOCKED build output: the staged generation directory holding
  ``manifest.json``) stages that generation into the package tree for the
  duration of the build.  The staged generation is verified first with the
  reviewed N8-20 driver in full (schema, content-derived generation name,
  per-file sha256, sizes, Mach-O structural walk, .s FMA re-audit), then
  the FINAL LINKED IMAGE is scanned through the same reviewed regex
  (n841-1: ``otool -tV`` + ``build_native.fma_audit``) with an on-host
  positive control, and the dylib's install name / link dependencies are
  gated (bare-basename or ``@rpath/<name>`` install name; only system
  libraries or ``@``-relative references; no Homebrew or dev-tree paths).
  ANY failure aborts the build BEFORE a wheel exists (nonzero exit,
  operator message on stderr): a native-requested build can never
  silently degrade to a pure-looking wheel.
* After ``bdist_wheel`` the produced wheel is verified: native members
  present and byte-identical to the staged originals, RECORD lists them
  with digests, and ``wheel_tags.check_wheel_tags`` (N8-20) accepts the
  filename + WHEEL metadata as a NON-pure platform wheel.  A violating
  wheel is deleted and the build fails -- nothing mislabeled survives.

The staged generation is copied BYTE-IDENTICAL (never re-hashed into a
rewritten manifest, never mutated with ``install_name_tool`` post hoc:
either would break the content-derived generation identity the loader
re-derives).  The ``@rpath/<name>`` canonical wheel install name is a
one-flag rebuild at the driver level (``build_native.py --install-name
@rpath/liblw_native_g8.dylib``) and is expected with the N8-50 re-freeze;
this gate accepts both that form and the B7 dev-parity bare basename the
current candidate (lw-g8-390acd5f57df1fe7) carries -- the loader dlopens
the packaged artifact by absolute path inside package resources, so both
resolve from site-packages.

This module is maintainer build-time infrastructure only (like
build_native.py); the installed loader never imports or invokes it.
Subprocess tools here are invoked as ARG-LISTS with explicit
environments -- no shell layer, no absolute toolstore assumptions.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

# reuse the reviewed N8-20 machinery (same directory)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_native  # noqa: E402
import wheel_tags  # noqa: E402

#: Build-time-only request variable.  The RUNTIME loader reads no env on
#: the auto path; this one is read only here, inside the maintainer build.
REQUEST_ENV = "SOLWEIG_LIGHT_PACKAGE_NATIVE"

#: Where staged generations appear inside the package for the build.
PACKAGE = "solweig_light"
GENERATION_REL = ("backends", "native_generated")

_NATIVE_MEMBER_RE = re.compile(
    r"^solweig_light/backends/native_generated/[^/]+/.+$")


class AssemblyError(Exception):
    """Loud assembly failure; str() is the operator-facing message."""


# ---------------------------------------------------------------------------
# the request (locked build output, never a cache or a guess)
# ---------------------------------------------------------------------------


def native_request(env: dict | None = None) -> Path | None:
    """The requested staged generation directory, or None (pure build).

    A set-but-invalid request raises -- a half-specified native request is
    a loud failure, never a quiet pure fallback (BUILD_DESIGN: missing
    optional native output in a native release build FAILS the build).
    """
    env = os.environ if env is None else env
    raw = env.get(REQUEST_ENV)
    if raw is None or raw == "":
        return None
    gen = Path(raw).resolve()
    if not gen.is_dir():
        raise AssemblyError(
            f"{REQUEST_ENV}={raw!r}: not a directory. The variable must "
            f"name the staged generation directory (the directory holding "
            f"manifest.json) of a LOCKED build output.")
    if not (gen / "manifest.json").is_file():
        raise AssemblyError(
            f"{REQUEST_ENV}={raw!r}: no manifest.json inside. Pass the "
            f"GENERATION directory itself (e.g. "
            f"experiments/optimization_v8/native/stage/<generation>), not "
            f"the staging root.")
    return gen


# ---------------------------------------------------------------------------
# verification beyond the N8-20 driver: linked image, install name
# ---------------------------------------------------------------------------


def _run_tool(argv: list[str], *, what: str) -> str:
    try:
        proc = subprocess.run([str(a) for a in argv], capture_output=True,
                              text=True, env={"PATH": os.environ.get(
                                  "PATH", "/usr/bin:/bin"), "LANG": "C"})
    except FileNotFoundError as exc:
        raise AssemblyError(
            f"required build tool unavailable for {what}: "
            f"{argv[0]!r} ({exc}); the native wheel request cannot be "
            f"honored on this host") from exc
    if proc.returncode != 0:
        raise AssemblyError(
            f"{what} failed ({proc.returncode}): {argv}\n"
            f"stderr: {proc.stderr.strip()[:2000]}")
    return proc.stdout


def linked_image_fma_scan(dylib: Path) -> dict:
    """n841-1: otool -tV of the FINAL linked artifact through the reviewed
    regex, with a compiled positive control proving the scan can see FMA.

    Placed in the wheel-assembly path rather than inside the reviewed
    build_native.py verify_generation: verify_generation is REUSED by the
    runtime loader, where BUILD_DESIGN 8.2 forbids subprocess tools
    entirely (see tests/optimization_v8/artifacts/test_linked_image_scan.py
    for the same reasoning).
    """
    dis = _run_tool(["otool", "-tV", dylib], what="linked-image disassembly")
    audit = build_native.fma_audit(dis)
    instruction_lines = sum(
        1 for line in dis.splitlines()
        if line.split() and line.split()[0].rstrip(':').isalnum()
        and not line.startswith('('))
    if instruction_lines < 1000:  # same non-vacuity pin as the N8-21 gate
        raise AssemblyError(
            f"linked-image scan of {dylib.name} saw only "
            f"{instruction_lines} instruction lines; refusing to treat a "
            f"near-empty disassembly as an FMA-free image")
    control = _positive_control()
    if audit.passed:
        return {"instruction_lines": instruction_lines, "fma_hits": 0,
                "passed": True, "positive_control": control}
    raise AssemblyError(
        f"LINKED-IMAGE FMA AUDIT FAILED for {dylib.name}: the final "
        f"linked image contains contraction "
        f"({len(audit.matches)} hits: "
        f"{[(m['mnemonic'], m['line']) for m in audit.matches[:10]]}). "
        f"The .s re-emission audit and the linked image disagree -- "
        f"refusing to package.")


def _positive_control() -> dict:
    """Compile a genuinely contracted function, scan it, require a hit."""
    cc = shutil.which("cc", path=os.environ.get("PATH", "")) \
        or shutil.which("clang", path=os.environ.get("PATH", ""))
    if cc is None:
        raise AssemblyError(
            "positive control needs a C compiler (cc/clang) on PATH; the "
            "native wheel request cannot be honored without it")
    with tempfile.TemporaryDirectory(prefix="n841-control-") as tmp:
        src = Path(tmp) / "ctrl.c"
        src.write_text(
            "float f(float a, float b, float c) { return a * b + c; }\n")
        out = Path(tmp) / "ctrl.dylib"
        _run_tool([cc, "-arch", "arm64", "-dynamiclib", "-O2",
                   "-ffp-contract=fast", "-o", out, src],
                  what="FMA positive-control compile")
        dis = _run_tool(["otool", "-tV", out],
                        what="FMA positive-control disassembly")
        audit = build_native.fma_audit(dis)
        if audit.passed:
            raise AssemblyError(
                "FMA positive control produced NO hit: the scan is blind "
                "on this host (optimizer did not contract, or the regex "
                "regressed). A 0-hit result for the real artifact would "
                "be vacuous; refusing to package.")
        return {"mnemonic": audit.matches[0]["mnemonic"],
                "match_count": len(audit.matches), "passed": True}


_SYSTEM_DEP_PREFIXES = ("/usr/lib/", "/System/")

_INSTALL_NAME_RE = re.compile(
    r"^(?:@rpath/)?(liblw_native_g\d+\.dylib)$")


def install_name_gate(dylib: Path) -> dict:
    """The dylib must resolve from site-packages, not from a dev tree.

    otool -L line 2 is the image's own install name (LC_ID_DYLIB).  The
    admissible forms are the @rpath/<name> wheel canonical form and the
    bare basename (B7 dev-cache parity form of the current candidate):
    both are location-independent references; the loader dlopens the
    packaged artifact by absolute path inside package resources.  An
    ABSOLUTE install name (a path into some build machine's tree) is a
    packaging defect and fails the assembly.
    """
    listing = _run_tool(["otool", "-L", dylib], what="otool -L")
    lines = [ln for ln in listing.splitlines() if ln.strip()]
    if len(lines) < 2:
        raise AssemblyError(f"otool -L output unusable for {dylib.name}")
    install_name = lines[1].split("(")[0].strip()
    m = _INSTALL_NAME_RE.match(install_name)
    if not m:
        raise AssemblyError(
            f"{dylib.name}: install name {install_name!r} is not "
            f"admissible (expected @rpath/liblw_native_g<lanes>.dylib or "
            f"the bare basename); an absolute or foreign install name "
            f"cannot resolve from site-packages. Rebuild with "
            f"build_native.py --install-name @rpath/<name> for the "
            f"canonical wheel form.")
    deps = [ln.split("(")[0].strip() for ln in lines[2:] if ln.strip()]
    foreign = [d for d in deps
               if not d.startswith(_SYSTEM_DEP_PREFIXES)
               and not d.startswith("@")]
    if foreign:
        raise AssemblyError(
            f"{dylib.name}: non-system link dependencies {foreign} would "
            f"need bundling/rpath repair; refusing to package (only "
            f"system libraries and @-relative references are admissible; "
            f"no Homebrew or dev-tree paths).")
    return {"install_name": install_name, "form": (
        "@rpath" if install_name.startswith("@rpath/") else "bare-basename"),
        "link_deps": deps}


def verify_for_wheel(gen_dir: Path) -> dict:
    """Full pre-staging gate: N8-20 verify + linked image + install name.

    Returns the artifact identity that later stages assert against.
    """
    gen_dir = Path(gen_dir).resolve()
    try:
        manifest = build_native.verify_generation(gen_dir)
    except build_native.BuildError as exc:
        raise AssemblyError(
            f"staged generation {gen_dir.name} failed N8-20 verification: "
            f"{exc}") from exc
    artifacts = [e for e in manifest["artifacts"]
                 if e["path"].endswith(".dylib")]
    if not artifacts:
        raise AssemblyError(
            f"staged generation {gen_dir.name}: native-release manifest "
            f"lists no dylib; nothing to package")
    dylib = gen_dir / artifacts[0]["path"]
    scan = linked_image_fma_scan(dylib)
    names = install_name_gate(dylib)
    return {
        "generation": manifest["generation"],
        "generation_dir": str(gen_dir),
        "artifact_tag": manifest.get("artifact_tag"),
        "build_mode": manifest.get("build_mode"),
        "kernel": dict(manifest["kernel"]),
        "dylib": {"path": artifacts[0]["path"],
                  "sha256": artifacts[0]["sha256"],
                  "bytes": artifacts[0]["bytes"]},
        "manifest_sha256": _sha256(gen_dir / "manifest.json"),
        "linked_image_scan": scan,
        "install_name": names,
    }


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# staging into the package tree (byte-identical; undone in finally)
# ---------------------------------------------------------------------------


def package_generated_root(package_root: Path) -> Path:
    return package_root.joinpath(*GENERATION_REL)


def assert_pure_package_tree(package_root: Path) -> None:
    """Pure-build direction of the loud gate: a build that did NOT request
    native content must not silently carry any (e.g. left behind by a
    crashed earlier native build)."""
    native_root = package_generated_root(package_root)
    if native_root.exists() and any(native_root.iterdir()):
        raise AssemblyError(
            f"pure (no-native) build refused: "
            f"{'/'.join(GENERATION_REL)} is present in the package source "
            f"tree ({native_root}) without {REQUEST_ENV} being set. "
            f"Remove the leftover generation content or run the native "
            f"build explicitly; a pure wheel must never look native.")


def stage_generation(gen_dir: Path, package_root: Path) -> Path:
    """Byte-identical copy of the verified generation into the package.

    Refuses to touch an existing target (generations are immutable).  The
    copy is byte-compared member-by-member against the verified source so
    "what landed in the package tree" is provably "what passed the gate".
    """
    gen_dir = Path(gen_dir).resolve()
    native_root = package_generated_root(package_root)
    target = native_root / gen_dir.name
    if target.exists():
        raise AssemblyError(
            f"refusing to stage over existing "
            f"{'/'.join(GENERATION_REL)}/{gen_dir.name} in the "
            f"package tree; remove it first")
    native_root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(gen_dir, target, copy_function=shutil.copy2)
    try:
        source_members = {p.name: _sha256(p)
                          for p in sorted(gen_dir.iterdir()) if p.is_file()}
        staged_members = {p.name: _sha256(p)
                          for p in sorted(target.iterdir()) if p.is_file()}
        if staged_members != source_members:
            raise AssemblyError(
                f"staged copy of {gen_dir.name} is not byte-identical to "
                f"the verified generation "
                f"({set(staged_members) ^ set(source_members) or 'hash'})")
    except BaseException:
        shutil.rmtree(target, ignore_errors=True)
        raise
    return target


def unstage_generation(package_root: Path, generation: str) -> None:
    target = package_generated_root(package_root) / generation
    if target.exists():
        shutil.rmtree(target)
    parent = package_generated_root(package_root)
    try:
        parent.rmdir()  # remove the emptied container; ignored if not empty
    except OSError:
        pass


# ---------------------------------------------------------------------------
# post-build wheel verification
# ---------------------------------------------------------------------------


def verify_built_wheel(wheel_path: Path, identity: dict) -> dict:
    """The produced wheel must CARRY the staged generation, byte-identical,
    with RECORD digests, under non-pure platform tags.  A violating wheel
    is deleted and AssemblyError raised -- nothing mislabeled ships."""
    wheel_path = Path(wheel_path)
    gen_prefix = f"{PACKAGE}/{'/'.join(GENERATION_REL)}/"
    expected_members = {
        gen_prefix + identity["generation"] + "/" + identity["dylib"]["path"],
        gen_prefix + identity["generation"] + "/manifest.json",
    }
    with zipfile.ZipFile(wheel_path) as zf:
        names = zf.namelist()
        missing = expected_members - set(names)
        if missing:
            raise AssemblyError(
                f"wheel {wheel_path.name} is missing native members "
                f"{sorted(missing)}: this looks like a PURE wheel produced "
                f"by a native-requested build -- failing loudly instead of "
                f"shipping it")
        dylib_member = gen_prefix + identity["generation"] + "/" \
            + identity["dylib"]["path"]
        manifest_member = gen_prefix + identity["generation"] + "/manifest.json"
        dylib_sha = _sha256_bytes(zf.read(dylib_member))
        if dylib_sha != identity["dylib"]["sha256"]:
            raise AssemblyError(
                f"wheel dylib sha256 {dylib_sha} != staged identity "
                f"{identity['dylib']['sha256']}")
        if _sha256_bytes(zf.read(manifest_member)) \
                != identity["manifest_sha256"]:
            raise AssemblyError(
                "wheel manifest.json is not byte-identical to the staged "
                "generation's manifest")
        # RECORD must make artifact presence provable (digest lines exist)
        record_member = [n for n in names if n.endswith(".dist-info/RECORD")]
        if len(record_member) != 1:
            raise AssemblyError("wheel has no unique RECORD member")
        record = zf.read(record_member[0]).decode("utf-8")
        record_rows = {row.split(",")[0]: row for row in record.splitlines()}
        for member in sorted(expected_members):
            if member not in record_rows or not record_rows[member] \
                    .split(",")[1:2]:
                raise AssemblyError(
                    f"RECORD does not pin {member} with a digest; artifact "
                    f"presence would be unprovable after install")
        wheel_meta = zf.read(record_member[0].replace("RECORD", "WHEEL")) \
            .decode("utf-8")
    # tags: a wheel that carries native code must not be pure/any/abi3
    wheel_tags.check_wheel_tags(wheel_path.name, has_native_lib=True,
                                wheel_metadata=wheel_meta)
    return {"wheel": str(wheel_path), "native_members":
            sorted(expected_members), "dylib_sha256":
            identity["dylib"]["sha256"], "tags_ok": True}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# CLI (operator form; also the loud-failure seam for the gate tests)
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(
        prog="assemble_native_wheel.py",
        description="Verify + stage a locked native generation for wheel "
                    "assembly (N8-41); setup.py drives this automatically "
                    f"when {REQUEST_ENV} is set")
    parser.add_argument("command", choices=("verify",))
    parser.add_argument("--generation-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        identity = verify_for_wheel(args.generation_dir)
    except AssemblyError as exc:
        print(f"ASSEMBLY FAILED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(identity, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
