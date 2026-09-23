import pytest
pytest.skip(
    'archived with the N8 native row and qualification machinery '
    '(n8_32 selection closed N9 F3 NATIVE_LOSS; archived at N9 F4 closed_cpu_only): research copies preserved under '
    'experiments/optimization_v8/native_dispatch/',
    allow_module_level=True)
"""Declared build modes (N8-20):

* source / no-native fallback build works with NO compiler and NO ISPC on
  PATH (fully stripped environment), and never shells out to anything;
* native release build fails LOUDLY when ISPC is absent (exit 3) -- this
  test runs everywhere, it tests absence itself;
* native release build, when ISPC is present, publishes a verified
  generation and refuses to overwrite it (immutability).
"""

import json
from pathlib import Path

import pytest

import build_native

REPO = Path(build_native.__file__).resolve().parents[3]
B7_KERNEL = REPO / "src" / "solweig_light" / "backends" / "native" / \
    "lw_primary.ispc"
COMPARISON = Path(build_native.__file__).resolve().parent / "stage" / \
    "dylib_comparison.json"

try:
    build_native.discover_ispc(None)
    ISPC_AVAILABLE = True
except build_native.ToolUnavailable:
    ISPC_AVAILABLE = False

REQUIRES_ISPC = pytest.mark.skipif(
    not ISPC_AVAILABLE, reason="[ispc-unavailable] pinned ISPC not reachable")


def test_source_fallback_build_needs_no_ispc(tmp_path, driver_proc):
    proc = driver_proc(["build", "--mode", "source",
                        "--staging", str(tmp_path / "stage")],
                       ispc_hidden=True)
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["build_mode"] == "source-no-native"
    gen_dir = tmp_path / "stage" / payload["generation"]
    manifest = json.loads((gen_dir / "manifest.json").read_text())
    assert manifest["artifacts"] == []
    assert manifest["toolchain"] is None
    assert build_native.validate_manifest(manifest) == []
    # the staging area contains exactly the one published generation
    assert [p.name for p in (tmp_path / "stage").iterdir()] == \
        [payload["generation"]]


def test_native_mode_fails_loudly_without_ispc(tmp_path, driver_proc):
    """PATH is stripped so no ISPC exists anywhere; the native release
    build must refuse with the dedicated tool-unavailable exit code, not
    silently fall back to a pure wheel."""
    proc = driver_proc(["build", "--kernel", str(B7_KERNEL),
                        "--staging", str(tmp_path / "stage")],
                       ispc_hidden=True)
    assert proc.returncode == 3, proc.stderr
    assert "ispc" in proc.stderr.lower()
    assert "BUILD FAILED" in proc.stderr
    assert not (tmp_path / "stage").exists() or \
        list((tmp_path / "stage").iterdir()) == []


def test_native_mode_fails_loudly_on_missing_kernel(tmp_path, driver_proc):
    # fails before any tool discovery, so it runs even without ISPC
    proc = driver_proc(["build", "--kernel", str(tmp_path / "nope.ispc"),
                        "--staging", str(tmp_path / "stage")])
    assert proc.returncode == 4, proc.stderr
    assert "kernel not found" in proc.stderr


@REQUIRES_ISPC
def test_native_release_publishes_verified_generation(tmp_path, driver_proc):
    staging = tmp_path / "stage"
    proc = driver_proc(["build", "--kernel", str(B7_KERNEL),
                        "--staging", str(staging)])
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    gen_dir = staging / payload["generation"]
    manifest = json.loads((gen_dir / "manifest.json").read_text())
    assert manifest["build_mode"] == "native-release"
    assert len(manifest["artifacts"]) == 1

    # independent verify subcommand passes
    proc2 = driver_proc(["verify", "--generation-dir", str(gen_dir)])
    assert proc2.returncode == 0, proc2.stderr

    # generations are immutable: same build again refuses to overwrite
    proc3 = driver_proc(["build", "--kernel", str(B7_KERNEL),
                         "--staging", str(staging)])
    assert proc3.returncode == 7, proc3.stderr
    assert "immutable" in proc3.stderr


@REQUIRES_ISPC
def test_native_release_artifact_matches_b7_cache(tmp_path, driver_proc):
    """The driver's output is byte-identical to the B7 dev-cache dylib
    under the same pinned toolchain (recorded in stage/dylib_comparison.json)."""
    if not COMPARISON.is_file():
        pytest.skip("[no-staged-artifact] dylib comparison record missing")
    staging = tmp_path / "stage"
    proc = driver_proc(["build", "--kernel", str(B7_KERNEL),
                        "--staging", str(staging)])
    assert proc.returncode == 0, proc.stderr
    built = json.loads(proc.stdout)
    import hashlib
    dylib = next((staging / built["generation"]).glob("*.dylib"))
    digest = hashlib.sha256(dylib.read_bytes()).hexdigest()
    recorded = json.loads(COMPARISON.read_text())
    assert digest == recorded["comparison"]["driver_dylib_sha256"]


def test_exit_codes_documented():
    assert build_native.ToolUnavailable.exit_code == 3
    assert build_native.ToolFailed.exit_code == 4
    assert build_native.FmaAuditFailure.exit_code == 5
    assert build_native.VerifyFailure.exit_code == 6
    assert build_native.GenerationExists.exit_code == 7
