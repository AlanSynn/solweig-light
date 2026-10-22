"""Shared constants and subprocess helpers for the S10-31 installed gates.

Adapted from the v8 installed-suite helpers (tests/optimization_v8/installed/)
with the S10 deltas: no native backend row (the native-cache/ISPC machinery
does not exist on this line), the S10 evidence directory, and the control-
variable list matching what the candidate package actually reads.

Imported by the suite's test modules and conftest under this unique module
name.  Never import the bare name ``conftest`` in this multi-suite tree:
pytest's prepend import mode rebinds ``sys.modules['conftest']`` to the
last-collected sibling suite's conftest, so in-function ``from conftest
import ...`` breaks under full-tree collection.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_DIR = REPO_ROOT / ".pytest_cache" / "evidence" / "installed_s10"
SCENE = REPO_ROOT / "tests" / "reference" / "state_sequence_original_cpu" / "scene"

# The no-env contract: the child sees none of these backend controls, and
# every other variable except the deliberate allowlist below is stripped.
# This is the complete set of environment variables the candidate package
# reads (src/solweig_light, S10-26 freeze): the shipped-default view must be
# exercised, not a tuned profile ("a resource-tuned profile is not
# unchanged-default DX proof").
BACKEND_ENV_VARS = (
    "SOLWEIG_LIGHT_ANILUM_PACKED",
    "SOLWEIG_LIGHT_FUSED_RAD",
    "SOLWEIG_LIGHT_LSIDE_DISPATCH",
    "SOLWEIG_LIGHT_NATIVE_CACHE",
    "SOLWEIG_LIGHT_PATCH_CLASS_TABLES",
    "SOLWEIG_LIGHT_PREPARED_VIS",
    "SOLWEIG_LIGHT_WORKER_POOL",
    "EE_PROJECT",
    "GDAL_CACHEMAX",
)
CHILD_ENV_ALLOWLIST = ("HOME", "NUMBA_CACHE_DIR")
CHILD_PATH = "/usr/bin:/bin"  # no build tools on scope for product children

# Host deployment shim (NOT a product backend control): this host's GDAL
# wheel is locally built (platform tag linux_x86_64) and its osgeo/_gdal.so
# carries a DT_RPATH whose first entry pins the pace spack gcc-12 libstdc++,
# which lacks CXXABI_1.3.15 -- but the wheel's libgdal.so.39 requires it.
# DT_RPATH outranks LD_LIBRARY_PATH, so ANY process whose first osgeo import
# precedes its first numpy import fails to load _gdal on this host.  The
# product pipeline itself always imports numpy first (which loads the
# compatible solweig-s10-env/lib runtime and satisfies the soname), so the
# campaign harness never saw this; the thermal_comfort/CLI path lazily
# imports osgeo before numpy and does.  Pre-loading the compatible runtime
# is the deployment the wheel needs here; it applies to a baseline install
# identically and sets no product behavior.  Recorded in every child env.
DEPLOYMENT_CXX_RUNTIME = ("/storage/project/r-hoh68-0/dsynn6/solweig-s10-env"
                          "/lib/libstdc++.so.6")

# save_tmrt is the only non-False save default of thermal_comfort, so the
# required default output set is TMRT + UTCI for tile 0_0; the scene met has
# 48 records, so TMRT carries 48 bands (one per met record).
EXPECTED_DEFAULT_OUTPUTS = ("TMRT_0_0.tif", "UTCI_0_0.tif")
EXPECTED_MET_RECORDS = 48

GATE_RECORD: dict = {
    "task": "S10-31 clean installed DX and relevant mandatory checks",
    "mode_label": "wheel + source install of the S10 candidate "
                  "(qualified_exact_cpu track); no native backend exists on "
                  "this line",
    "wheel": None,
    "wheelhouse": None,
    "wheel_venv": None,
    "source_venv": None,
    "api_gate": None,
    "cli_gate": None,
    "wheel_manifest": None,
    "deferred": [],
}


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_cmd(cmd, *, env=None, cwd=None, timeout=600):
    return subprocess.run(
        [str(part) for part in cmd], capture_output=True, text=True,
        env=env, cwd=None if cwd is None else str(cwd), timeout=timeout)


def child_env(numba_cache: Path, *, extra=None) -> dict:
    """No-backend-control child environment with a minimal PATH.

    Constructed from scratch (``env -i`` semantics) so every control in
    ``BACKEND_ENV_VARS`` is absent rather than merely overwritten.  Network
    is additionally blocked for the product children by the PYTHONPATH guard
    (``install_no_net_guard``); all dependencies are installed from the
    offline wheelhouse and the run reads only local files.  The one
    deployment variable is the host C++ runtime shim (DEPLOYMENT_CXX_RUNTIME
    above) -- required by the locally-built GDAL wheel here, independent of
    the product version under test.
    """
    env = {
        "HOME": os.environ.get("HOME", ""),
        "PATH": CHILD_PATH,
        "NUMBA_CACHE_DIR": str(numba_cache),
        "LANG": "C",
    }
    if DEPLOYMENT_CXX_RUNTIME and Path(DEPLOYMENT_CXX_RUNTIME).exists():
        env["LD_PRELOAD"] = DEPLOYMENT_CXX_RUNTIME
    if extra:
        env.update(extra)
    return env


def listing(path: Path) -> list[str]:
    return sorted(entry.name for entry in Path(path).iterdir())


@contextlib.contextmanager
def readonly_site_packages(site_packages):
    """Make the installation genuinely read-only for the duration of a
    no-env child run (DX contract: site-packages non-writable).

    Directories get 0o555 and files 0o444, so creating, replacing, deleting
    or editing anything in the installation raises PermissionError inside
    the child -- a loud failure, never a silent write.  Symlinks are left
    untouched (chmod would follow them into shared targets).  Original
    modes are restored in ``finally``.
    """
    site = Path(site_packages)
    if not site.is_dir():
        raise RuntimeError(f"site-packages missing: {site}")
    protected: list[tuple[str, int]] = [(str(site), site.stat().st_mode & 0o777)]
    for root, dirs, files in os.walk(site):
        for name in dirs:
            path = os.path.join(root, name)
            if not os.path.islink(path):
                protected.append((path, os.stat(path).st_mode & 0o777))
        for name in files:
            path = os.path.join(root, name)
            if not os.path.islink(path):
                protected.append((path, os.stat(path).st_mode & 0o777))
    for path, _mode in protected:
        os.chmod(path, 0o555 if os.path.isdir(path) else 0o444)
    try:
        yield
    finally:
        failed = []
        for path, mode in reversed(protected):
            try:
                os.chmod(path, mode)
            except OSError as error:
                failed.append((path, str(error)))
        if failed:
            raise RuntimeError(
                f"could not restore site-packages permissions: {failed[:3]} ...")


# The no-network property is enforced, not structural.  This module is
# placed on the child's PYTHONPATH as ``sitecustomize.py``: Python imports
# it at startup, so every gate child (API ``python -c``, console-script CLI)
# runs with Internet-domain socket creation raising, and every
# network-capable call recorded to SOLWEIG_NO_NET_LOG.  AF_UNIX sockets and
# literal-IP/localhost resolution are allowed (neither touches the
# network).  A ``guard_installed`` marker line proves the guard actually
# loaded in a given child -- parents assert on it.  (Port of the v8 N2
# guard, unmodified in behavior.)
NO_NET_SITECUSTOMIZE = '''
"""Auto-loaded via PYTHONPATH by the S10-31 no-env DX gate children.

Records network-capable calls and raises on Internet socket use.
Installed by the test suite into a scratch dir; never part of the package.
"""
import ipaddress as _ip
import json as _json
import os as _os
import socket as _socket
import time as _time

_LOG = _os.environ.get("SOLWEIG_NO_NET_LOG")


def _record(kind, detail):
    if not _LOG:
        return
    try:
        with open(_LOG, "a", encoding="utf-8") as fh:
            fh.write(_json.dumps(
                {"kind": kind, "detail": detail, "t": _time.time()}) + "\\n")
    except OSError:
        pass


class _GuardedSocket(_socket.socket):
    def __init__(self, family=-1, type=-1, proto=-1, fileno=None):
        family = family if family != -1 else _socket.AF_INET
        if family in (_socket.AF_INET, _socket.AF_INET6):
            _record("socket", str((family, type, proto)))
            raise OSError("[no-net-gate] Internet socket blocked and recorded")
        super().__init__(family, type, proto, fileno)


_orig_getaddrinfo = _socket.getaddrinfo


def _guarded_getaddrinfo(host, *args, **kwargs):
    literal = False
    if isinstance(host, str):
        try:
            _ip.ip_address(host)
            literal = True
        except ValueError:
            literal = host == "localhost"
    if literal:
        return _orig_getaddrinfo(host, *args, **kwargs)
    _record("getaddrinfo", str((host,) + tuple(args[:1])))
    raise OSError("[no-net-gate] DNS resolution blocked and recorded")


def _guarded_gethostbyname(host):
    try:
        _ip.ip_address(host)
        return _socket._orig_gethostbyname(host)
    except ValueError:
        pass
    _record("gethostbyname", str(host))
    raise OSError("[no-net-gate] DNS resolution blocked and recorded")


def _guarded_create_connection(address, *args, **kwargs):
    _record("create_connection", str(address))
    raise OSError("[no-net-gate] connect blocked and recorded")


_socket.socket = _GuardedSocket
_socket.getaddrinfo = _guarded_getaddrinfo
_socket._orig_gethostbyname = _socket.gethostbyname
_socket.gethostbyname = _guarded_gethostbyname
_socket.create_connection = _guarded_create_connection
_record("guard_installed", {"pid": _os.getpid()})
'''


def install_no_net_guard(target_dir) -> Path:
    """Write the network-guard ``sitecustomize.py`` into a scratch dir."""
    target = Path(target_dir)
    target.mkdir(parents=True, exist_ok=True)
    (target / "sitecustomize.py").write_text(NO_NET_SITECUSTOMIZE, encoding="utf-8")
    return target


def no_net_env_extra(guard_dir, log_path) -> dict:
    """Extra ``child_env`` keys activating the network guard for one child."""
    return {"PYTHONPATH": str(guard_dir), "SOLWEIG_NO_NET_LOG": str(log_path)}


def read_no_net_events(log_path) -> list[dict]:
    """Parsed guard events; empty list iff the guard never loaded."""
    path = Path(log_path)
    if not path.exists():
        return []
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            events.append(json.loads(line))
    return events


def assert_no_net_events(events: list[dict], where: str) -> None:
    """Guard must have loaded (marker present) and nothing else may appear."""
    assert events, f"{where}: network guard did not load (no marker event)"
    attempts = [event for event in events if event.get("kind") != "guard_installed"]
    assert not attempts, f"{where}: network attempts during no-env gate: {attempts}"


def loadavg() -> str:
    try:
        return Path("/proc/loadavg").read_text().split()[0]
    except OSError:
        return "unknown"
