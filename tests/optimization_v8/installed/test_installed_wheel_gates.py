"""N8-23 wheel/install gates: content, origins, collision/dependency bans.

The wheel under test is built from this worktree by ordinary pip in a fresh
venv (session fixtures in conftest.py) and installed, fully offline, into a
second fresh venv OUTSIDE the repo together with the pinned baseline runtime
closure.  Today this is the declared SOURCE/NO-NATIVE fallback wheel: the
native artifact arrives with N8-41, so every gate here is labelled fallback
and is explicitly NOT native qualification (DX_CONTRACT.md, last line).

These gates are origin-parametrized: the dx-surface capture runs through
``dx_snapshot.capture_runtime_surface_subprocess`` (the
``SOLWEIG_DX_PACKAGE_ORIGIN=subprocess:<python>`` mechanism), so N8-41/42
can rerun them unchanged against a native wheel's venv.
"""

from __future__ import annotations

import json
import zipfile

import pytest

from installed_test_helpers import GATE_RECORD, REPO_ROOT
from installed_test_helpers import run_cmd as _run

import dx_snapshot  # noqa: E402  (conftest put tests/optimization_v8/dx on sys.path)

MAIN_SURFACE = dx_snapshot.load_surface(dx_snapshot.MAIN_SURFACE_PATH)
BRANCH_SURFACE = dx_snapshot.load_surface(dx_snapshot.BRANCH_SURFACE_PATH)


def _dist_info_path(zf: zipfile.ZipFile, member: str) -> str:
    hits = [n for n in zf.namelist()
            if n.endswith(f".dist-info/{member}")]
    assert len(hits) == 1, hits
    return hits[0]


def test_wheel_tags_match_build_mode(built_wheel):
    """Tags must match the declared build mode of the wheel content.

    Today: no native artifact exists before N8-41, so the fallback build is
    a pure wheel.  When N8-41's native artifact enters the tree this same
    gate flips expectations: a wheel carrying native code must be a
    platform wheel (never ``*-none-any`` / purelib) with a build manifest,
    per PACKAGING_AND_DISTRIBUTION.md.
    """
    with zipfile.ZipFile(built_wheel["path"]) as zf:
        names = zf.namelist()
        wheel_metadata = zf.read(_dist_info_path(zf, "WHEEL")).decode()
    has_native = any(
        "/native_generated/" in name
        or name.endswith((".dylib", ".so"))
        for name in names)
    if has_native:
        assert "Root-Is-Purelib: false" in wheel_metadata, wheel_metadata
        assert "py3-none-any" not in built_wheel["name"], built_wheel["name"]
        assert any("manifest" in name.lower() for name in names), (
            "native wheel without a build manifest")
    else:
        assert "Root-Is-Purelib: true" in wheel_metadata, wheel_metadata
        assert "py3-none-any" in built_wheel["name"], built_wheel["name"]


def test_wheel_contains_no_solweig_gpu_module(built_wheel):
    """No upstream-colliding top-level module ships in the main wheel."""
    with zipfile.ZipFile(built_wheel["path"]) as zf:
        names = zf.namelist()
    top_level = {n.split("/")[0] for n in names}
    assert not any("solweig_gpu" in name.lower() for name in top_level), top_level
    assert "solweig_light" in top_level, sorted(top_level)


def test_wheel_ships_no_torch_cuda_code(built_wheel):
    """No torch/cuda payload in the wheel, and the core dependency set stays
    clean (dx_snapshot.check_forbidden_core_dependencies).

    Requirement strings are compared canonically (name + sorted specifier
    clauses): the setuptools backend may reorder clauses like ``<2.5,>=2.4``
    relative to the frozen pyproject rendering without semantic change.
    """
    from packaging.requirements import Requirement as parse_requirement

    def canonical(requirement: str) -> tuple:
        parsed = parse_requirement(requirement)
        return (parsed.name.lower(), tuple(sorted(str(s) for s in parsed.specifier)))

    with zipfile.ZipFile(built_wheel["path"]) as zf:
        names = zf.namelist()
    assert not [n for n in names
                if "torch" in n.lower() or "cuda" in n.lower() or "nvidia" in n.lower()]
    with zipfile.ZipFile(built_wheel["path"]) as zf:
        metadata = zf.read(_dist_info_path(zf, "METADATA")).decode()
    requires = [line.split(":", 1)[1].strip() for line in metadata.splitlines()
                if line.startswith("Requires-Dist:") and "extra ==" not in line]
    assert sorted(map(canonical, requires)) == \
        sorted(map(canonical, MAIN_SURFACE["distribution"]["dependencies"])), requires
    failures = dx_snapshot.check_forbidden_core_dependencies(
        {"distribution": {"dependencies": requires}})
    assert not failures, failures


def test_installed_modules_resolve_inside_the_venv(wheel_venv):
    """Every solweig_light module of the installed distribution lives in the
    fresh venv's site-packages -- never the repository src/ tree."""
    probe = _run([wheel_venv["python"], "-c", (
        "import importlib, json, pkgutil, pathlib\n"
        "import solweig_light\n"
        "bad, seen = [], 0\n"
        "for m in pkgutil.walk_packages(solweig_light.__path__, 'solweig_light.'):\n"
        "    mod = importlib.import_module(m.name)\n"
        "    seen += 1\n"
        "    f = str(pathlib.Path(getattr(mod, '__file__', '')).resolve())\n"
        "    if 'site-packages' not in f or '/src/solweig_light' in f:\n"
        "        bad.append((m.name, f))\n"
        "print(json.dumps({'seen': seen, 'bad': bad}))\n"
    )], cwd=wheel_venv["path"])
    assert probe.returncode == 0, probe.stderr
    payload = json.loads(probe.stdout.strip().splitlines()[-1])
    assert payload["seen"] > 0, "no submodules discovered"
    assert not payload["bad"], payload["bad"]
    assert str(REPO_ROOT) not in probe.stdout


def test_installed_runtime_is_the_pinned_version(wheel_venv):
    probe = _run([wheel_venv["python"], "-c",
                  "import solweig_light; print(solweig_light.__version__)"])
    assert probe.returncode == 0, probe.stderr
    assert probe.stdout.strip() == MAIN_SURFACE["package"]["dunder_version"]


def test_dx_surface_parity_in_subprocess_origin(wheel_venv):
    """Frozen-contract parity, probed in the installed venv's interpreter.

    Zero unexpected divergences: any asserted-leaf drift must be an
    allowlisted, real main-vs-branch source divergence (dx_snapshot
    self-verifies that cross-check).
    """
    candidate = dx_snapshot.capture_runtime_surface_subprocess(wheel_venv["python"])
    assert candidate["package_path"], "runtime capture lost the package path"
    assert "site-packages" in candidate["package_path"]
    assert candidate["evidence_class"] == dx_snapshot.RUNTIME_INTROSPECTION
    skip = frozenset({"companion_distribution.console_scripts"})
    drift = dx_snapshot.surface_divergences(MAIN_SURFACE, candidate, skip_paths=skip)
    failures = dx_snapshot.check_divergences_allowed(
        drift, {},
        baseline=MAIN_SURFACE, branch_surface=BRANCH_SURFACE, skip_paths=skip)
    failures.extend(dx_snapshot.check_forbidden_core_dependencies(candidate))
    # reviewer note N3: the evidence record must carry this gate's result
    GATE_RECORD["surface_gate"] = {
        "status": "passed" if not failures else "failed",
        "method": "dx_snapshot.capture_runtime_surface_subprocess "
                  "(SOLWEIG_DX_PACKAGE_ORIGIN=subprocess:<python>)",
        "candidate_evidence_class": candidate["evidence_class"],
        "candidate_package_path": candidate["package_path"],
        "skip_paths": sorted(skip),
        "unexpected_divergences": drift,
        "failures": failures,
        "wheel_sha256_run_scoped": GATE_RECORD["wheel"]["sha256"],
    }
    assert not failures, ("installed candidate DX surface drifted:\n"
                          + "\n".join(failures))


def test_surface_gate_recorded(wheel_venv):
    """The evidence record carries the subprocess-origin gate result."""
    assert GATE_RECORD["wheel_venv"] is not None
    assert GATE_RECORD["wheel"]["sha256"], "wheel sha256 must be recorded"
    surface = GATE_RECORD["surface_gate"]
    assert surface is not None and surface["status"] == "passed", surface
    assert "site-packages" in surface["candidate_package_path"], surface
    assert GATE_RECORD["wheel"]["sha256"], "wheel sha256 must be recorded"
