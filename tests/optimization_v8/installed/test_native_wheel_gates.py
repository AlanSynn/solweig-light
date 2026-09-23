#SOLWEIG-GPU: GPU-accelerated SOLWEIG model for urban thermal comfort simulation
#Copyright (C) 2022–2025 Harsh Kamath and Naveen Sudharsan
import pytest
pytest.skip(
    'archived with the N8 native row and qualification machinery '
    '(n8_32 selection closed N9 F3 NATIVE_LOSS; archived at N9 F4 closed_cpu_only): research copies preserved under '
    'experiments/optimization_v8/native_dispatch/',
    allow_module_level=True)

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
"""N8-41 native-wheel gates: candidate identity, both loud-gate directions,
and the actual-installed-origins probe against a REAL native wheel.

The candidate is the LATEST staged generation under
``experiments/optimization_v8/native/stage/`` (N8-13), SUBJECT TO N8-50
RE-FREEZE -- nothing here speculates about selection; the shipped registry
stays EMPTY and auto still resolves row A with the artifact present and
loaded (final test).

Gate directions encoded (PACKAGING_AND_DISTRIBUTION.md):

* a native-requested build with an unusable locked output FAILS LOUDLY
  (full pip-level bogus-path case: nonzero exit, message on stderr, no
  wheel; gate-level: corrupted/renamed staged copies rejected);
* the compiler-free build ships a PURE wheel without pretending (the
  session's plain built_wheel carries no native content -- the flip side
  of test_wheel_tags_match_build_mode's content branch);
* the built candidate wheel CARRIES the staged generation byte-identically
  (RECORD-digested, non-pure platform tags via the N8-20 wheel_tags
  checker);
* in the installed native-wheel venv the loader LOADS THE PACKAGED
  generation: every origin (package, generation dir, resolved N8-20
  driver) sits inside site-packages, identity checks pass against the
  staged manifest (kernel sha / dylib sha / LOADER_ABI), and there is no
  repo/experiments sys.path or anchor reach.

Skip labels (never fake-pass):
  [no-staged-artifact]        no staged generation to package
  [native-wheel-build-unavailable] the candidate wheel build/install failed
  (wheelhouse/uv labels inherit from the shared session fixtures)
"""
from __future__ import annotations

import json
import os
import sys
import zipfile
from pathlib import Path

import pytest

from installed_test_helpers import GATE_RECORD, REPO_ROOT, run_cmd, sha256_of

_STAGE_ROOT = REPO_ROOT / "experiments" / "optimization_v8" / "native" / "stage"
_PACKAGING = REPO_ROOT / "experiments" / "optimization_v8" / "packaging"
_REQUEST_ENV = "SOLWEIG_LIGHT_PACKAGE_NATIVE"

if str(_PACKAGING) not in sys.path:
    sys.path.insert(0, str(_PACKAGING))
import assemble_native_wheel  # noqa: E402  (maintainer tool home, stdlib-only)

VENDORED_DRIVER = (REPO_ROOT / "src" / "solweig_light" / "_native_dispatch"
                   / "build_native.py")
EXPERIMENTS_DRIVER = _PACKAGING / "build_native.py"


# ---------------------------------------------------------------------------
# session fixtures: candidate identity, candidate wheel, native install venv
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def staged_generation() -> dict:
    """The LATEST staged generation (locked build output = the candidate)."""
    manifests = sorted(_STAGE_ROOT.glob("*/manifest.json"))
    if not manifests:
        pytest.skip("[no-staged-artifact] no staged generation under "
                    f"{_STAGE_ROOT}")
    gen_dir = manifests[-1].parent
    try:
        identity = assemble_native_wheel.verify_for_wheel(gen_dir)
    except assemble_native_wheel.AssemblyError as exc:
        pytest.skip(f"[no-staged-artifact] staged generation failed the "
                    f"assembly gate: {exc}")
    return identity


@pytest.fixture(scope="session")
def native_build_venv(work_dir, wheel_dir, wheelhouse) -> Path:
    """A minimal build interpreter: seed setuptools from the offline
    wheelhouse (the same method as the shared session fixtures)."""
    target = work_dir / "native_buildenv"
    uv = run_cmd(["uv", "venv", "--seed", target, "--python", sys.executable])
    if uv.returncode != 0:
        pytest.skip(f"[native-wheel-build-unavailable] venv creation failed: "
                    f"{uv.stderr.strip()}")
    seed = GATE_RECORD.get("wheelhouse", {}).get("setuptools_seed")
    if not seed:
        pytest.skip("[wheelhouse-unavailable] no setuptools seed for the "
                    "native wheel build")
    install = run_cmd([target / "bin" / "pip", "install", "--no-index",
                       "--no-cache-dir", wheel_dir / seed])
    if install.returncode != 0:
        pytest.skip(f"[native-wheel-build-unavailable] seed install failed: "
                    f"{install.stderr.strip()[-300:]}")
    return target


@pytest.fixture(scope="session")
def native_wheel(work_dir, wheelhouse, staged_generation,
                 native_build_venv) -> dict:
    """The candidate native wheel, built by ordinary pip with the request
    variable pointing at the staged generation (locked build output)."""
    dist = work_dir / "native_dist"
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
           "HOME": os.environ.get("HOME", ""),
           "LANG": "C",
           _REQUEST_ENV: staged_generation["generation_dir"]}
    result = run_cmd([native_build_venv / "bin" / "pip", "wheel", REPO_ROOT,
                      "--no-deps", "--no-build-isolation", "-w", dist],
                     env=env, timeout=600)
    wheels = list(dist.glob("*.whl")) if dist.is_dir() else []
    if result.returncode != 0 or not wheels:
        pytest.skip(f"[native-wheel-build-unavailable] pip wheel failed: "
                    f"{(result.stderr or result.stdout).strip()[-400:]}")
    wheel = wheels[0]
    record = {
        "path": str(wheel),
        "name": wheel.name,
        "sha256": sha256_of(wheel),
        "request_env": _REQUEST_ENV,
        "staged_generation": staged_generation["generation"],
        "build_method": "pip wheel <worktree> --no-deps --no-build-isolation "
                        f"with {_REQUEST_ENV}=<staged generation dir>; the "
                        "setup.py shim verifies + stages byte-identically "
                        "and post-verifies the wheel (wheel_tags)",
    }
    GATE_RECORD["native_wheel"] = record
    return record


@pytest.fixture(scope="session")
def native_wheel_venv(work_dir, wheel_dir, wheelhouse, native_wheel) -> dict:
    """Fresh venv OUTSIDE the repo: the candidate wheel + pinned closure."""
    target = work_dir / "nativewheelenv"
    uv = run_cmd(["uv", "venv", "--seed", target, "--python", sys.executable])
    if uv.returncode != 0:
        pytest.skip(f"[native-wheel-build-unavailable] venv creation failed: "
                    f"{uv.stderr.strip()}")
    pip = target / "bin" / "pip"
    result = run_cmd([pip, "install", "--no-index", "--no-cache-dir",
                      "--find-links", wheel_dir, native_wheel["path"]],
                     timeout=900)
    if result.returncode != 0:
        pytest.skip(f"[native-wheel-build-unavailable] native wheel install "
                    f"failed: {(result.stderr or result.stdout).strip()[-400:]}")
    check = run_cmd([pip, "check"])
    python = target / "bin" / "python"
    site_packages = run_cmd([python, "-c",
                             "import solweig_light, pathlib; print(pathlib.Path("
                             "solweig_light.__file__).resolve().parent.parent)"
                             ]).stdout.strip()
    record = {"path": str(target), "python": str(python),
              "site_packages": site_packages,
              "pip_check": check.stdout.strip() or check.stderr.strip()}
    GATE_RECORD["native_wheel_venv"] = record
    return record


# ---------------------------------------------------------------------------
# direction A: a native-requested build cannot silently degrade
# ---------------------------------------------------------------------------


def test_native_request_with_unusable_output_fails_the_build(
        work_dir, native_build_venv):
    """Full pip-level loud gate: a request pointing at a nonexistent locked
    output fails the build BEFORE any wheel exists, naming the problem."""
    dist = work_dir / "native_bad_dist"
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
           "HOME": os.environ.get("HOME", ""),
           "LANG": "C",
           _REQUEST_ENV: "/tmp/n841-nonexistent-generation"}
    result = run_cmd([native_build_venv / "bin" / "python", "-m", "pip",
                      "wheel", REPO_ROOT, "--no-deps", "--no-build-isolation",
                      "-w", dist],
                     env=env, timeout=600)
    assert result.returncode != 0, \
        "a native request with an unusable output must fail the build"
    assert "not a directory" in (result.stderr + result.stdout), \
        "the loud failure must name the unusable request"
    assert not list(dist.glob("*.whl")), "no wheel may exist after the failure"


def test_assembly_gate_rejects_corrupt_and_renamed_generations(
        tmp_path, staged_generation):
    """Gate-level loud directions: a byte-flipped dylib (hash gate) and a
    renamed generation directory (content-derived name gate) both fail."""
    src = Path(staged_generation["generation_dir"])
    corrupt = tmp_path / staged_generation["generation"]
    corrupt.mkdir()
    for member in src.iterdir():
        (corrupt / member.name).write_bytes(member.read_bytes())
    dylib = corrupt / staged_generation["dylib"]["path"]
    raw = bytearray(dylib.read_bytes())
    raw[100] ^= 0xFF
    dylib.write_bytes(bytes(raw))
    with pytest.raises(assemble_native_wheel.AssemblyError, match="hash"):
        assemble_native_wheel.verify_for_wheel(corrupt)

    renamed = tmp_path / "renamed-generation"
    corrupt.rename(renamed)  # same bytes, wrong (non-derived) directory name
    with pytest.raises(assemble_native_wheel.AssemblyError,
                       match="name mismatch|verification"):
        assemble_native_wheel.verify_for_wheel(renamed)


def test_linked_image_positive_control_is_sensitive():
    """The compiled control REALLY contracts: the scan flags fmadd, so a
    0-hit scan of the candidate image is evidence, not blindness."""
    control = assemble_native_wheel._positive_control()
    assert control["passed"] and control["match_count"] >= 1, control
    assert control["mnemonic"] in (
        "fmadd", "fmla", "fmsub", "fnmadd", "fnmsub", "fnmla"), control


def test_candidate_generation_passes_the_full_assembly_gate(
        staged_generation):
    """Candidate identity: N8-20 verification + linked-image scan (0 FMA,
    non-vacuous line count) + admissible install name + system-only deps."""
    GATE_RECORD["native_wheel_candidate_identity"] = staged_generation
    assert staged_generation["build_mode"] == "native-release"
    assert staged_generation["generation"].startswith("lw-g8-")
    scan = staged_generation["linked_image_scan"]
    assert scan["passed"] and scan["fma_hits"] == 0
    assert scan["instruction_lines"] >= 1000, scan
    assert scan["positive_control"]["match_count"] >= 1, scan
    names = staged_generation["install_name"]
    assert names["form"] in ("bare-basename", "@rpath"), names
    assert names["install_name"] == Path(
        staged_generation["dylib"]["path"]).name or \
        names["install_name"].startswith("@rpath/"), names
    for dep in names["link_deps"]:
        assert dep.startswith(("/usr/lib/", "/System/", "@")), \
            f"non-system link dependency would need bundling: {dep}"


def test_vendored_build_driver_matches_the_reviewed_experiments_source():
    """Drift alarm for the single source of truth: the packaged N8-20
    driver copy must stay byte-identical to the reviewed experiments
    source; updating either requires re-vendoring + delta review."""
    assert VENDORED_DRIVER.read_bytes() == EXPERIMENTS_DRIVER.read_bytes(), (
        f"{VENDORED_DRIVER} drifted from {EXPERIMENTS_DRIVER}; re-vendor "
        f"(byte-identical) or schedule the delta review")


# ---------------------------------------------------------------------------
# the wheel itself: carries the generation; the pure wheel does not pretend
# ---------------------------------------------------------------------------


def _dist_info_member(zf: zipfile.ZipFile, suffix: str) -> str:
    hits = [n for n in zf.namelist() if n.endswith(f".dist-info/{suffix}")]
    assert len(hits) == 1, hits
    return hits[0]


def test_native_wheel_carries_the_staged_generation(
        native_wheel, staged_generation):
    """Members byte-identical, RECORD-digested, non-pure platform tags."""
    gen = staged_generation["generation"]
    prefix = f"solweig_light/backends/native_generated/{gen}/"
    with zipfile.ZipFile(native_wheel["path"]) as zf:
        names = zf.namelist()
        expected = {prefix + staged_generation["dylib"]["path"],
                    prefix + "manifest.json"}
        assert expected <= set(names), (expected - set(names))
        dylib_bytes = zf.read(prefix + staged_generation["dylib"]["path"])
        manifest_bytes = zf.read(prefix + "manifest.json")
        record = zf.read(_dist_info_member(zf, "RECORD")).decode()
        wheel_meta = zf.read(_dist_info_member(zf, "WHEEL")).decode()
    import hashlib
    assert hashlib.sha256(dylib_bytes).hexdigest() == \
        staged_generation["dylib"]["sha256"], "wheel dylib != staged identity"
    assert hashlib.sha256(manifest_bytes).hexdigest() == \
        staged_generation["manifest_sha256"], "wheel manifest != staged"
    rows = {row.split(",")[0]: row.split(",") for row in record.splitlines()}
    for member in sorted(expected):
        assert member in rows and rows[member][1], \
            f"RECORD does not pin {member} with a digest"
    assert "Root-Is-Purelib: false" in wheel_meta, wheel_meta
    from wheel_tags import check_wheel_tags
    tags = check_wheel_tags(native_wheel["name"], has_native_lib=True,
                            wheel_metadata=wheel_meta)
    assert tags["platform_tag"] != "any"
    GATE_RECORD["native_wheel_gate"] = {
        "status": "passed",
        "wheel": native_wheel["name"],
        "wheel_sha256_run_scoped": native_wheel["sha256"],
        "generation": gen,
        "dylib_sha256": staged_generation["dylib"]["sha256"],
        "kernel_sha256": staged_generation["kernel"]["sha256"],
        "manifest_sha256": staged_generation["manifest_sha256"],
        "install_name": staged_generation["install_name"],
        "linked_image_scan": staged_generation["linked_image_scan"],
    }


def test_pure_wheel_ships_no_native_content(built_wheel):
    """The compiler-free direction: the ordinary build (no request) is a
    pure wheel that carries no native content and does not pretend to."""
    assert "py3-none-any" in built_wheel["name"], built_wheel["name"]
    with zipfile.ZipFile(built_wheel["path"]) as zf:
        native = [n for n in zf.namelist()
                  if "native_generated" in n
                  or n.endswith((".dylib", ".so"))]
    assert not native, f"pure wheel carries native content: {native}"


# ---------------------------------------------------------------------------
# actual installed origins: the wheel-installed package loads the PACKAGED
# generation, never a repo/experiments path
# ---------------------------------------------------------------------------

PROBE_SCRIPT = """
import importlib, json, sys
from pathlib import Path
repo = %(repo)r
import solweig_light
from solweig_light._native_dispatch import installed_loader
out = {}
out['package_file'] = str(Path(solweig_light.__file__).resolve())
outcome = installed_loader.attempt_load()
out['status'] = outcome.status
out['generation'] = outcome.generation
out['generation_dir'] = str(outcome.generation_dir)
out['decline_reasons'] = installed_loader.decline_reasons()
driver = installed_loader._build_native()
out['driver_file'] = str(Path(driver.__file__).resolve())
out['loader_abi'] = driver.ABI_VERSION
out['wrapper_abi'] = driver.WRAPPER_ABI_LAYOUT_VERSION
out['expected_package'] = driver.PACKAGE_NAME
out['repo_sys_path'] = [p for p in sys.path if p and repo in p]
handle = outcome.handle
out['stamp'] = dict(handle._stamp)
sel = importlib.import_module(
    'solweig_light._native_dispatch.lw_default_policy')
decision = sel.resolve_lw_backend()
out['selection'] = {'row': decision.row, 'mode': decision.mode,
                    'expert': decision.expert,
                    'record_present': decision.record is not None,
                    'reason': decision.reason,
                    'registry': str(sel.DEFAULT_REGISTRY_PATH)}
print(json.dumps(out))
"""


def test_installed_native_loader_loads_the_packaged_generation(
        native_wheel_venv, staged_generation, native_wheel):
    """Executed probe in the native-wheel venv, minimal env (no backend
    variables at all): the loader loads the PACKAGED generation from
    site-packages, the vendored N8-20 driver resolves from site-packages
    (no repo/experiments reach), and kernel/dylib/LOADER_ABI identity
    matches the staged candidate manifest."""
    env = {"HOME": os.environ.get("HOME", ""),
           "PATH": "/usr/bin:/bin",
           "LANG": "C",
           "NUMBA_CACHE_DIR": str(Path(native_wheel_venv["path"]) / ".nbc")}
    probe = run_cmd([native_wheel_venv["python"], "-c",
                     PROBE_SCRIPT % {"repo": str(REPO_ROOT)}],
                    env=env, cwd=native_wheel_venv["path"], timeout=300)
    assert probe.returncode == 0, probe.stderr[-2000:]
    payload = json.loads(probe.stdout.strip().splitlines()[-1])
    site = native_wheel_venv["site_packages"]
    assert site in payload["package_file"], payload
    assert payload["status"] == "loaded", payload
    assert payload["generation"] == staged_generation["generation"], payload
    assert site in payload["generation_dir"], payload
    assert payload["generation_dir"].endswith(staged_generation["generation"])
    # zero repo/experiments reach: origins and sys.path
    assert site in payload["driver_file"], payload
    assert payload["repo_sys_path"] == [], payload
    assert "/src/solweig_light" not in payload["driver_file"], payload
    # identity against the staged candidate manifest
    assert payload["stamp"]["kernel_sha256"] == \
        staged_generation["kernel"]["sha256"], payload
    assert payload["stamp"]["dylib_sha256"] == \
        staged_generation["dylib"]["sha256"], payload
    assert payload["stamp"]["build_mode"] == "native-release", payload
    assert payload["loader_abi"] == 1 and \
        payload["wrapper_abi"] == "lw-region-abi-1", payload
    assert payload["expected_package"] == "solweig-light", payload
    GATE_RECORD["native_installed_origins"] = {
        "status": "passed",
        "method": "attempt_load() probe in the native-wheel venv, minimal "
                  "no-backend env, cwd outside the repo",
        "installed_generation_dir": payload["generation_dir"],
        "installed_driver": payload["driver_file"],
        "repo_sys_path_entries": payload["repo_sys_path"],
        "handle_stamp": payload["stamp"],
        "wheel_sha256_run_scoped": native_wheel["sha256"],
    }


def test_installed_native_selection_stays_row_a(
        native_wheel_venv, staged_generation):
    """SHIPPED-STATE SELECTION INVARIANCE on the native wheel: with the
    generation present AND loaded, the shipped-empty registry still
    resolves auto -> row A exactly like the pure wheel's registry gates
    assert -- the '[absent]' reason, never the '[malformed]' accident."""
    env = {"HOME": os.environ.get("HOME", ""),
           "PATH": "/usr/bin:/bin",
           "LANG": "C"}
    probe = run_cmd([native_wheel_venv["python"], "-c", (
        "import importlib, json\n"
        "mod = importlib.import_module("
        "'solweig_light._native_dispatch.lw_default_policy')\n"
        "sel = mod.resolve_lw_backend()\n"
        "print(json.dumps({'row': sel.row, 'mode': sel.mode,\n"
        "                  'expert': sel.expert, 'record': sel.record,\n"
        "                  'registry': str(mod.DEFAULT_REGISTRY_PATH),\n"
        "                  'reason': sel.reason}))\n"
    )], env=env, cwd=native_wheel_venv["path"], timeout=300)
    assert probe.returncode == 0, probe.stderr[-2000:]
    payload = json.loads(probe.stdout.strip().splitlines()[-1])
    assert (payload["row"], payload["mode"]) == ("A", "auto-legacy"), payload
    assert payload["expert"] is False and payload["record"] is None, payload
    assert native_wheel_venv["site_packages"] in payload["registry"], payload
    assert payload["reason"].startswith("[absent]"), payload
    assert "no qualification records" in payload["reason"], payload
    assert "[malformed]" not in payload["reason"], payload
