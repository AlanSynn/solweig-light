"""N8-20 packaging tests: shared fixtures.

These tests are fast and local-only (no network, no real wheels). They
import the build driver directly from experiments/optimization_v8/packaging.

Skip labels (never fake-pass):
  [ispc-unavailable]      -- the pinned ISPC is not reachable; native-mode
                             positive tests skip
  [no-staged-artifact]    -- the proof generation from build_native.py is
                             not present under experiments/.../packaging/stage
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
PACKAGING = REPO / "experiments" / "optimization_v8" / "packaging"
B7_KERNEL = REPO / "src" / "solweig_light" / "backends" / "native" / \
    "lw_primary.ispc"

if str(PACKAGING) not in sys.path:
    sys.path.insert(0, str(PACKAGING))

import build_native  # noqa: E402


def ispc_available() -> bool:
    try:
        build_native.discover_ispc(None)
        return True
    except build_native.ToolUnavailable:
        return False


ISPC_AVAILABLE = ispc_available()
REQUIRES_ISPC = pytest.mark.skipif(
    not ISPC_AVAILABLE, reason="[ispc-unavailable] pinned ISPC not reachable")


@pytest.fixture(scope="session")
def staged_generation() -> Path:
    manifests = sorted(STAGE_DIR.glob("*/manifest.json"))
    if not manifests:
        pytest.skip(
            "[no-staged-artifact] run build_native.py on the B7 kernel to "
            "produce experiments/optimization_v8/packaging/stage/<gen>")
    return manifests[-1].parent


STAGE_DIR = PACKAGING / "stage"


@pytest.fixture()
def driver_proc():
    """Run build_native.py as a subprocess the way a maintainer would.

    ispc_hidden=True strips the environment down so no ISPC can be found
    (no /opt/homebrew magic in the driver under test)."""

    def run(args: list[str], *, ispc_hidden: bool = False,
            cwd: Path | None = None) -> subprocess.CompletedProcess:
        if ispc_hidden:
            env = {"PATH": "/usr/bin:/bin", "LANG": "C",
                   "HOME": os.environ.get("HOME", "")}
        else:
            env = dict(os.environ)
            env.pop("SOLWEIG_LIGHT_ISPC", None)
        return subprocess.run(
            [sys.executable, str(PACKAGING / "build_native.py"), *args],
            env=env, cwd=None if cwd is None else str(cwd),
            capture_output=True, text=True, timeout=120)

    return run
