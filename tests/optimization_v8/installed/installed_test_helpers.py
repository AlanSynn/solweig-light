"""Shared constants and subprocess helpers for the N8-23 installed gates.

Imported by the suite's test modules and conftest under this unique module
name.  Never import the bare name ``conftest`` in this multi-suite tree:
pytest's prepend import mode rebinds ``sys.modules['conftest']`` to the
last-collected sibling suite's conftest, so in-function ``from conftest
import ...`` breaks under full-tree collection (proven classification:
``experiments/optimization_v8/policy/results/full_tree_failures.json``,
failure_catalog entry for ``test_surface_gate_recorded``; see also the
v8-test-conftest-name-collision memory note).
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_DIR = REPO_ROOT / "development/optimization_v8_native_default" / "evidence" / "installed"
SCENE = REPO_ROOT / "tests" / "reference" / "state_sequence_original_cpu" / "scene"

# The no-env contract: the child sees none of these backend controls, and
# every other variable except the deliberate allowlist below is stripped.
BACKEND_ENV_VARS = (
    "SOLWEIG_LIGHT_NATIVE_CACHE",
    "SOLWEIG_LIGHT_FUSED_RAD",
    "SOLWEIG_LIGHT_PATCH_CLASS_TABLES",
    "SOLWEIG_LIGHT_PREPARED_VIS",
    "SOLWEIG_LIGHT_WORKER_POOL",
    "EE_PROJECT",
)
# Baseline-required cache destinations kept writable in the child.
# NUMBA_CACHE_DIR is where the existing Numba fallback is allowed to keep
# its JIT cache (main already JITs); the native developer cache is pointed
# at a directory made non-writable for the run.
CHILD_ENV_ALLOWLIST = ("HOME", "NUMBA_CACHE_DIR", "SOLWEIG_LIGHT_NATIVE_CACHE")
CHILD_PATH = "/usr/bin:/bin"  # no ISPC, no Homebrew zsh, no build tools

FORBIDDEN_STDOUT_TOKENS = (
    "ispc", "native", "backend", "fallback", "avx", "neon", "kernel-select",
)

EXPECTED_DEFAULT_OUTPUTS = ("TMRT_0_0.tif", "UTCI_0_0.tif")

GATE_RECORD: dict = {
    "task": "N8-23; disposition N9 F4 closed_cpu_only",
    "mode_label": "SOURCE/NO-NATIVE fallback wheel (the N8 native row and "
                  "qualification machinery are archived repo-only as of N9 F4 "
                  "closed_cpu_only; n8_32 selection closed N9 F3 NATIVE_LOSS). "
                  "Necessary but NOT native qualification (DX_CONTRACT.md: "
                  "'Passing fallback installation is necessary but insufficient "
                  "for the native-default goal')",
    "wheel": None,
    "wheelhouse": None,
    "wheel_venv": None,
    "source_venv": None,
    "api_gate": None,
    "cli_gate": None,
    "surface_gate": None,
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


def child_env(numba_cache: Path, native_cache: Path, *, extra=None) -> dict:
    """No-backend-control child environment with a minimal PATH.

    Constructed from scratch (``env -i`` semantics) so backend controls are
    absent rather than merely overwritten.  ISPC, Homebrew zsh and build
    tools are off PATH; network is not used by any code path (all
    dependencies are installed from the offline wheelhouse and the run
    reads only local files).
    """
    env = {
        "HOME": os.environ.get("HOME", ""),
        "PATH": CHILD_PATH,
        "NUMBA_CACHE_DIR": str(numba_cache),
        # deliberate: the one backend variable we set points at a
        # non-writable directory to prove auto never builds into it
        "SOLWEIG_LIGHT_NATIVE_CACHE": str(native_cache),
        "LANG": "C",
    }
    if extra:
        env.update(extra)
    return env


def listing(path: Path) -> list[str]:
    return sorted(entry.name for entry in Path(path).iterdir())


@contextlib.contextmanager
def readonly_site_packages(site_packages):
    """Reviewer note N1: make the installation genuinely read-only for the
    duration of a no-env child run (DX_CONTRACT: site-packages non-writable
    while retaining baseline output/cache permissions).

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


# Reviewer note N2: the no-network property is enforced, not structural.
# This module is placed on the child's PYTHONPATH as ``sitecustomize.py``:
# Python imports it at startup, so every gate child (API ``python -c``,
# console-script CLI, ``--help``) runs with Internet-domain socket creation
# raising, and every network-capable call recorded to SOLWEIG_NO_NET_LOG.
# AF_UNIX sockets and literal-IP/localhost resolution are allowed (neither
# touches the network).  A ``guard_installed`` marker line proves the guard
# actually loaded in a given child -- parents assert on it.
NO_NET_SITECUSTOMIZE = '''
"""Auto-loaded via PYTHONPATH by the N8-23 no-env DX gate children.

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
