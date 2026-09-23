#SOLWEIG-GPU: GPU-accelerated SOLWEIG model for urban thermal comfort simulation
#Copyright (C) 2022–2025 Harsh Kamath and Naveen Sudharsan

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
"""N8-21: trusted installed-artifact loader (BUILD_DESIGN.md section 8).

The AUTO/default entry point is `auto_load()`; the operator entry point is
`load_explicit()`.  Both funnel through `attempt_load()`, which resolves a
generation ONLY inside installed package resources and gates
content/ABI/ISA/profile BEFORE any dlopen:

1. Resolution: `importlib.resources.files(package)` -> `backends/
   native_generated/<generation>/`.  No environment variable is read on the
   auto path (`SOLWEIG_LIGHT_NATIVE_CACHE` is the expert dev path and is
   ignored here); the legacy developer cache `~/.cache/solweig-light` is
   positively rejected even if the package tree somehow resolves into it.
2. Path containment (review note N5 of the N8-30 review): lexical and
   realpath containment of the generation directory inside the installed
   package root, and of every manifest-declared member inside the
   generation directory -- absolute paths, `..` traversal and symlinked
   components escaping the tree are rejected BEFORE any member content is
   opened, hashed or mmap'd.
3. Content/ABI/ISA/profile gates, once per generation, in the
   BUILD_DESIGN 8.3 order: manifest schema + per-file sha256 + byte size +
   Mach-O structural walk + FMA re-audit (reused verbatim from the N8-20
   driver's `verify_generation`, never re-implemented here), then
   `abi.abi_version` / `wrapper_abi_layout_version` / exported-symbol
   surface against this loader's compiled expectations, then the math
   profile against the qualified allow-list, then host capability (arch,
   os / os_min_version, `cpu-feature:*` requirements via a sysctl probe --
   never `platform.machine()` alone) routed to the N8-10
   `UnsupportedNativeISA` taxonomy.
4. Decline semantics (SOURCE_FALLBACK.md table, implemented exactly):
   * ABSENT artifact / `source-no-native` manifest / unqualified host =>
     quiet auto decline (None, zero new stdout/stderr, no subprocess, no
     build attempt); an EXPLICIT request raises `MissingNativeArtifact`
     / `UnsupportedNativeISA` loudly.
   * PRESENT-BUT-CORRUPT artifact (schema/JSON invalid, name-derivation
     mismatch, hash/size/Mach-O/FMA-audit failure, path escape, ABI or
     math-profile outside the loader's speakable domain) => auto declines
     to Numba AND records the reason privately (`decline_reasons()`); an
     EXPLICIT request raises `CorruptNativeArtifact` naming the packaging
     defect.  Never a silent fallback, never a hidden rebuild: unverified
     bytes are never executed.
5. No runtime writes of any kind (HOME/temp/cache/site-packages), no
   subprocess, no network, no compile, and the default path never hashes
   the packaged `.ispc` source and never touches the legacy developer
   builder (`native_lw._cache_dir` / `_build_needed` / `_build`).

Reuse, not re-implementation: execution, locking and lifetime belong to
the reviewed N8-10 module.  `prepare_native_handle()` itself admits only
the legacy `build_stamp.json` layout and hashes the packaged kernel
source, so the installed path constructs `native_handle.NativeHandle`
directly after its own (stronger) manifest admission, reusing
`native_handle._load_entries` (reviewed ctypes prototype binding),
`native_handle._dir_lock` (publication serialization) and the shared
workflow-generation clock.  Both outcomes and failures are cached per
(pid, workflow generation, resolved root) exactly like the N8-10
registry/negative cache: a second load of the same generation performs
no re-hash, and a workflow does not retry a declined artifact every
block.
"""
from __future__ import annotations

import ctypes
import importlib.resources
import json
import os
import platform as _platform
import sys
import threading
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

# N8-41 vendoring: the N8-10 execution/lifetime module ships in this
# package (the maintainer-tree copy resolved the bare ``native_handle``
# name through the sibling sys.path bootstrap).
from solweig_light._native_dispatch import native_handle  # noqa: E402

# The N8-20 build driver resolves ONCE, on first use, from two homes:
# the repo-checkout tool home (maintainer tree; the sys.path insertion
# keeps ``sys.modules['build_native']`` ONE module object shared with the
# packaging/artifact test suites that import it by bare name) or -- when
# that tree is absent, i.e. inside an installed wheel -- the vendored
# byte-identical copy packaged as ``solweig_light._native_dispatch
# .build_native`` (N8-41 native wheel; provenance and drift alarm:
# tests/optimization_v8/installed/test_native_wheel_gates.py asserts the
# vendored copy stays byte-identical to the experiments source, so the
# two homes can never diverge silently).  A tree with NEITHER home fails
# LOUDLY with both paths named, never with a silent behavioral drift.
_BUILD_NATIVE: list = []


def _build_native():
    """The N8-20 build driver (verify_generation + versioned constants),
    resolved once, on first use."""
    if not _BUILD_NATIVE:
        packaging = Path(__file__).resolve().parents[3] \
            / 'experiments' / 'optimization_v8' / 'packaging'
        if packaging.is_dir():
            if str(packaging) not in sys.path:
                sys.path.insert(0, str(packaging))
            import build_native
        else:
            try:
                from solweig_light._native_dispatch import \
                    build_native as build_native
            except ImportError as exc:
                raise ImportError(
                    f'solweig_light._native_dispatch.installed_loader '
                    f'requires the N8-20 build driver, resolved either from '
                    f'the repo-checkout anchor {packaging} or from the '
                    f'vendored packaged copy '
                    f'solweig_light._native_dispatch.build_native; neither '
                    f'is reachable from this installation') from exc
        _BUILD_NATIVE.append(build_native)
    return _BUILD_NATIVE[0]

# ---------------------------------------------------------------------------
# Loader compiled-in expectations (BUILD_DESIGN section 4 / section 8.3)
# ---------------------------------------------------------------------------

PACKAGE = 'solweig_light'
GENERATION_ROOT_PARTS = ('backends', 'native_generated')

# Single source of truth: the builder's versioned constants ARE the
# loader's expectations; a wheel built against different values cannot
# pass this gate (that is the point). They resolve lazily from the build
# driver (module __getattr__, PEP 562) for the same deferred-resolution
# reason as _build_native above; the gate path reads them off the driver
# object directly.
EXPECTED_SYMBOLS = frozenset(('lw_primary_f32', 'lw_primary_f64'))


def __getattr__(name):
    if name == 'LOADER_ABI_VERSION':
        return _build_native().ABI_VERSION
    if name == 'LOADER_WRAPPER_ABI':
        return _build_native().WRAPPER_ABI_LAYOUT_VERSION
    if name == 'EXPECTED_PACKAGE_NAME':
        return _build_native().PACKAGE_NAME
    if name == 'QUALIFIED_MATH_PROFILES':
        return {(_build_native().MATH_PROFILE_ID, False, 'disabled',
                 'default')}
    raise AttributeError(f'{__name__!r} has no attribute {name!r}')

# Qualified (target -> gang) rows of the versioned allow-list; unknown
# cells use Numba (ARCHITECTURE.md 'Automatic planning').
QUALIFIED_TARGETS = {'neon-i32x8': 8}

# Math profiles this loader is qualified to execute (the B7 numerical
# contract): resolved lazily from the build driver -- see __getattr__.
# Anything else in a wheel is a packaging defect.

STATUS_LOADED = 'loaded'
STATUS_ABSENT = 'declined-absent'
STATUS_CORRUPT = 'declined-corrupt'
STATUS_UNQUALIFIED = 'declined-unqualified'

# Non-typed failure surfaces of the reused build_native validator (n8-30
# review note N1): unreadable listed members (PermissionError is an OSError),
# non-dict artifacts/generated_sources entries (AttributeError), audit-record
# key drift (KeyError), malformed JSON/types (ValueError/TypeError).  Each
# maps to the same recorded declined-corrupt outcome -- fail closed, never a
# crash of the quiet auto path.  build_native's own isinstance hardening of
# these surfaces is N8-41's delta review; this tuple is loader-side only.
_VALIDATOR_FAILURE_SIGNALS = (
    OSError, AttributeError, KeyError, ValueError, TypeError)

_DECLINE_LOG_LIMIT = 32


# Taxonomy reuse (N8-10 classes; never redefined here).
MissingNativeArtifact = native_handle.MissingNativeArtifact
CorruptNativeArtifact = native_handle.CorruptNativeArtifact
UnsupportedNativeISA = native_handle.UnsupportedNativeISA


@dataclass(frozen=True)
class LoadOutcome:
    """Result of one attempt: status, recorded reason, taxonomy error and
    (on success) the workflow-owned handle."""

    status: str
    reason: str
    error: native_handle.NativeHandleError | None = None
    handle: native_handle.NativeHandle | None = None
    generation: str | None = None
    generation_dir: Path | None = None
    package: str | None = None


# ---------------------------------------------------------------------------
# Module state: registry / negative cache / private decline log
# ---------------------------------------------------------------------------

_REGISTRY_LOCK = threading.Lock()
_REGISTRY: dict[tuple, LoadOutcome] = {}
_NEG_CACHE: dict[tuple, LoadOutcome] = {}
_ROOT_CACHE: dict[tuple, 'Path | None'] = {}
_ROOT_ABSENT_REASON: dict[tuple, str] = {}
_DECLINE_LOG: list[str] = []
_UNSET = object()


def decline_reasons() -> tuple[str, ...]:
    """Private diagnostics: recorded decline reasons (never printed)."""
    return tuple(_DECLINE_LOG)


def registry_snapshot() -> dict[str, str]:
    """Private diagnostics: root key -> outcome status/generation."""
    with _REGISTRY_LOCK:
        return {str(k): f'{v.status}:{v.generation}' for k, v in
                _REGISTRY.items()}


def reset_for_tests() -> None:
    """Test-only: drop loader caches (and the shared N8-10 state)."""
    with _REGISTRY_LOCK:
        _REGISTRY.clear()
        _NEG_CACHE.clear()
        _ROOT_CACHE.clear()
        _ROOT_ABSENT_REASON.clear()
        _DECLINE_LOG.clear()
    native_handle.reset_for_tests()


def _record(outcome: LoadOutcome, key: tuple | None) -> LoadOutcome:
    """Cache a decline per key and append the private diagnostic line."""
    if key is not None:
        with _REGISTRY_LOCK:
            if key not in _NEG_CACHE and key not in _REGISTRY:
                _NEG_CACHE[key] = outcome
    _DECLINE_LOG.append(f'[{outcome.status}] {outcome.package}: '
                        f'{outcome.reason}')
    del _DECLINE_LOG[:-_DECLINE_LOG_LIMIT]
    return outcome


def _absent(package: str, reason: str) -> LoadOutcome:
    return LoadOutcome(STATUS_ABSENT, reason, MissingNativeArtifact(
        f'no qualified native artifact in this installation: {reason}'),
        package=package)


def _corrupt(package: str, reason: str) -> LoadOutcome:
    return LoadOutcome(STATUS_CORRUPT, reason, CorruptNativeArtifact(
        f'packaging defect: present-but-corrupt native artifact -- {reason}'
        f' (auto declined to Numba and recorded this reason; never a silent'
        f' fallback, never a hidden rebuild; unverified bytes were not'
        f' executed)'), package=package)


def _unqualified(package: str, reason: str) -> LoadOutcome:
    return LoadOutcome(STATUS_UNQUALIFIED, reason, UnsupportedNativeISA(
        f'host not qualified for the installed native artifact: {reason}'),
        package=package)


# ---------------------------------------------------------------------------
# Resolution: installed package resources ONLY (never env, never dev cache)
# ---------------------------------------------------------------------------


def _dev_cache_root() -> Path:
    """Legacy developer cache root (positively rejected; monkeypatched in
    tests so tests never write into the real user cache)."""
    return Path.home() / '.cache' / 'solweig-light'


def _resolve_package_root(package: str) -> tuple[Path | None, str | None]:
    """Resolve the installed package root via importlib.resources.

    Returns (realpath, None) or (None, reason).  Non-filesystem traversable
    resources (zip/frozen) are outside the qualified install shape and
    decline absent -- quietly, like any unqualified installation.
    """
    try:
        traversable = importlib.resources.files(package)
    except Exception as exc:  # ImportError & friends: not an install state
        return None, f'package {package!r} is not importable ({exc!r})'
    root = Path(str(traversable))
    if not root.is_dir():
        return None, (f'package resources of {package!r} are not a '
                      f'filesystem tree ({traversable!r}); only regular '
                      f'installs are in the qualified domain')
    return root.resolve(), None


def _contained_within(child_real: Path, ancestor_real: Path) -> bool:
    """Realpath containment (both arguments must already be resolved)."""
    return child_real.is_relative_to(ancestor_real)


def _member_escape_reason(gen_real: Path, rel) -> str | None:
    """Lexical + realpath containment of one manifest member path.

    Returns a reason string when the member is not safely inside the
    generation directory, or None when it is.  Uses only lstat/readlink
    syscalls (os.path.realpath) -- no content open, so it can gate BEFORE
    any hashing.  This discharges N8-30 review note N5.
    """
    if not isinstance(rel, str) or not rel:
        return f'path is not a non-empty string ({rel!r})'
    if '\x00' in rel:
        return f'NUL byte in path {rel!r}'
    pure = PurePosixPath(rel)
    if pure.is_absolute() or rel.startswith('/') or rel.startswith('\\') \
            or len(pure.drive) or len(pure.root):
        return f'absolute path {rel!r}'
    parts = pure.parts
    if not parts or any(part in ('', '.', '..') for part in parts):
        return f'traversal/empty component in {rel!r}'
    real = Path(os.path.realpath(gen_real.joinpath(*parts)))
    if not _contained_within(real, gen_real):
        return (f'{rel!r} resolves to {real}, outside the generation '
                f'directory {gen_real} (symlink escape)')
    return None


# ---------------------------------------------------------------------------
# Host capability (never platform.machine() alone)
# ---------------------------------------------------------------------------


def _sysctl_int(name: str) -> int | None:
    """Read a sysctl as int via libSystem (no subprocess, no writes)."""
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        fn = libc.sysctlbyname
    except (OSError, AttributeError):
        return None
    fn.restype = ctypes.c_int
    fn.argtypes = [ctypes.c_char_p, ctypes.c_void_p, ctypes.c_void_p,
                   ctypes.c_void_p, ctypes.c_size_t]
    value = ctypes.c_int(-1)
    size = ctypes.c_size_t(ctypes.sizeof(value))
    if fn(name.encode(), ctypes.byref(value), ctypes.byref(size), None,
          0) != 0:
        return None
    return int(value.value)


def _host_neon() -> int | None:
    """1 present / 0 definitively absent / None not determinable."""
    return _sysctl_int('hw.optional.neon')


def _version_tuple(text: str) -> tuple[int, ...]:
    return tuple(int(piece) for piece in text.split('.') if piece.isdigit())


def _host_os_version() -> str | None:
    if sys.platform == 'darwin':
        return _platform.mac_ver()[0] or None
    return None  # Linux glibc baseline comparison: future target work


def _host_capability_gap(pf: dict) -> str | None:
    """Artifact platform block vs host; None when executable.

    An unqualified host is an ORDINARY supported state (quiet decline),
    distinct from a corrupt artifact -- this returns the capability gap
    string routed to UnsupportedNativeISA.
    """
    machine = _platform.machine()
    arch = pf.get('arch')
    if arch != 'arm64':
        return (f'artifact arch {arch!r} is outside the qualified arm64/'
                f'neon domain (host {machine!r})')
    if machine not in native_handle._ARM64_MACHINES:
        return f'host {machine!r} cannot execute an arm64 artifact'
    os_name = pf.get('os')
    if os_name and os_name != sys.platform:
        return f'artifact os {os_name!r} != host os {sys.platform!r}'
    minos = pf.get('os_min_version')
    host_os = _host_os_version()
    if minos and host_os and \
            _version_tuple(minos) > _version_tuple(host_os):
        return (f'host OS {host_os} is older than the artifact minimum '
                f'{minos}')
    for req in pf.get('requirements') or []:
        if req == 'cpu-feature:neon':
            probe = _host_neon()
            if probe == 0:
                return 'cpu-feature:neon required but the host probe ' \
                       'reports NEON unavailable'
            # probe None on an arm64 host: NEON/ASIMD is architectural
            # baseline there; the machine check above already gated the
            # domain (machine + sysctl attempt, never machine alone).
        else:
            return (f'requirement {req!r} is not recognized by this '
                    f'loader; unrecognized requirements fail closed')
    return None


# ---------------------------------------------------------------------------
# Per-candidate gate: containment -> content -> ABI -> profile -> host
# ---------------------------------------------------------------------------


def _gate_candidate(cand_real: Path, package: str) -> LoadOutcome:
    """Gate one generation directory.  Nothing is opened before the
    manifest itself is proven contained; member paths are proven contained
    before any of them is opened or hashed."""

    # -- manifest: contained, then present, then parseable -----------------
    manifest_path = cand_real / 'manifest.json'
    manifest_real = Path(os.path.realpath(manifest_path))
    if not _contained_within(manifest_real, cand_real):
        return _corrupt(package, f'manifest.json resolves outside the '
                                 f'generation directory: {manifest_real}')
    if not manifest_real.is_file():
        return _corrupt(package, f'generation directory {cand_real} has no '
                                 f'manifest.json (dylib present but '
                                 f'unverifiable is a packaging defect)')
    try:
        manifest = json.loads(manifest_real.read_text())
    except (OSError, ValueError) as exc:
        return _corrupt(package, f'manifest.json unreadable/invalid JSON '
                                 f'({exc!r})')
    if not isinstance(manifest, dict):
        return _corrupt(package, 'manifest.json is not a JSON object')

    # -- N5 containment gate BEFORE any member open/hash -------------------
    listed = list(manifest.get('artifacts') or [])
    listed += list(manifest.get('generated_sources') or [])
    for entry in listed:
        if not isinstance(entry, dict):
            continue
        escape = _member_escape_reason(cand_real, entry.get('path'))
        if escape:
            return _corrupt(package, f'manifest path containment '
                                     f'violation: {escape} (tampered '
                                     f'manifest; rejected before any '
                                     f'content was read)')

    # -- declared absence is quiet ------------------------------------------
    mode = manifest.get('build_mode')
    if mode == 'source-no-native':
        return _absent(package, 'installation ships a source-no-native '
                                'manifest (ordinary source install; the '
                                'Numba path is explicitly NOT '
                                'native-qualified)')
    if mode != 'native-release':
        return _corrupt(package, f'unknown build_mode {mode!r}')

    # -- content verification: schema, generation-name derivation, hashes,
    #    sizes, Mach-O structural walk, FMA re-audit (N8-20, reused) -------
    # Loader expectations, read off the resolved driver (single source of
    # truth; identical to the lazy module attributes above).
    driver = _build_native()
    try:
        verified = driver.verify_generation(cand_real)
    except driver.VerifyFailure as exc:
        return _corrupt(package, f'content verification failed: {exc}')
    except _VALIDATOR_FAILURE_SIGNALS as exc:
        # Review note N1: the reused validator has non-typed failure
        # surfaces (unreadable member / string entry / audit key drift / ...).
        # A present artifact whose validator crashes is still present-but-
        # corrupt: decline and record, never crash the quiet auto path.
        return _corrupt(package, f'content verification raised an untyped '
                                 f'validator failure '
                                 f'({type(exc).__name__}): {exc!r}')

    # -- ABI gate: speakable by THIS loader ---------------------------------
    abi = verified.get('abi') or {}
    if abi.get('abi_version') != driver.ABI_VERSION:
        return _corrupt(package, f'artifact abi_version '
                                 f'{abi.get("abi_version")!r} != loader '
                                 f'abi_version {driver.ABI_VERSION!r} '
                                 f'(wheel built against a different ABI)')
    if abi.get('wrapper_abi_layout_version') \
            != driver.WRAPPER_ABI_LAYOUT_VERSION:
        return _corrupt(package, f'wrapper ABI layout '
                                 f'{abi.get("wrapper_abi_layout_version")!r}'
                                 f' != loader expectation '
                                 f'{driver.WRAPPER_ABI_LAYOUT_VERSION!r}')
    if abi.get('python_c_api') is not False:
        return _corrupt(package, 'artifact declares a Python C API '
                                 'dependency; the qualified surface is a '
                                 'pure C ABI')
    if frozenset(abi.get('exported_symbols') or ()) != EXPECTED_SYMBOLS:
        return _corrupt(package, f'exported symbols '
                                 f'{sorted(abi.get("exported_symbols") or ())}'
                                 f' != the qualified surface '
                                 f'{sorted(EXPECTED_SYMBOLS)}')
    if verified.get('package') != driver.PACKAGE_NAME:
        return _corrupt(package, f'manifest package '
                                 f'{verified.get("package")!r} != '
                                 f'{driver.PACKAGE_NAME!r}')

    # -- math profile gate: qualified allow-list ----------------------------
    mp = verified.get('math_profile') or {}
    row = (mp.get('id'), mp.get('fast_math'), mp.get('fma_contraction'),
           mp.get('math_lib'))
    qualified_profiles = {(driver.MATH_PROFILE_ID, False, 'disabled',
                           'default')}
    if row not in qualified_profiles:
        return _corrupt(package, f'math profile {mp.get("id")!r} is '
                                 f'outside the loader qualified allow-list '
                                 f'{sorted(r[0] for r in
                                           qualified_profiles)}')

    # -- target/gang gate ----------------------------------------------------
    target = (verified.get('build') or {}).get('target')
    gang = QUALIFIED_TARGETS.get(target)
    if gang is None:
        return _corrupt(package, f'build target {target!r} is outside the '
                                 f'qualified targets '
                                 f'{sorted(QUALIFIED_TARGETS)}')
    artifacts = verified.get('artifacts') or []
    dylib_name = f'liblw_native_g{gang}.dylib'
    if not any(entry.get('path') == dylib_name for entry in artifacts):
        return _corrupt(package, f'native-release manifest lists no '
                                 f'{dylib_name} artifact')

    # -- host capability gate (ordinary, quiet) ------------------------------
    gap = _host_capability_gap(verified.get('platform') or {})
    if gap:
        return _unqualified(package, gap)

    return LoadOutcome(STATUS_LOADED, 'verified and loaded', package=package,
                       generation=verified['generation'],
                       generation_dir=cand_real)


def _instantiate(gen_real: Path, verified: dict, gang: int
                 ) -> native_handle.NativeHandle:
    """Load the verified dylib and mint the N8-10 workflow handle.

    Reuses the reviewed entry binding, pid pinning, workflow generation,
    execute() and lifetime wholesale; only the admission differs (manifest
    gate here vs legacy stamp gate in prepare_native_handle -- see module
    docstring)."""
    try:
        lib, entries = native_handle._load_entries(str(gen_real), gang)
    except AttributeError as exc:
        raise CorruptNativeArtifact(
            f'verified dylib does not export the declared symbols: '
            f'{exc!r}') from exc
    except OSError as exc:
        raise CorruptNativeArtifact(
            f'dlopen of the verified artifact failed: {exc!r}') from exc
    spec = native_handle.NativeHandleSpec(
        artifact_dir=str(gen_real), gang=gang, isa='neon',
        math_profile=verified['math_profile']['id'], thread_budget=1)
    stamp = {
        'source': 'installed-native_generated-v1',
        'build_mode': verified['build_mode'],
        'generation': verified['generation'],
        'kernel_sha256': verified['kernel']['sha256'],
        'dylib_sha256': verified['artifacts'][0]['sha256'],
    }
    return native_handle.NativeHandle(
        lib, entries, native_handle._getpid(),
        native_handle.current_workflow_generation(),
        verified['generation'], verified['kernel']['sha256'], gang, spec,
        stamp)


# ---------------------------------------------------------------------------
# attempt / auto / explicit
# ---------------------------------------------------------------------------


def attempt_load(package: str = PACKAGE) -> LoadOutcome:
    """Resolve, gate and (when fully qualified) load the installed native
    generation.  Never prints, never writes, never builds; declines are
    cached per (pid, workflow generation, root) and the resolved package
    root itself is cached per workflow generation, so a declined artifact
    is not re-scanned on every block."""
    pid = native_handle._getpid()
    wgen = native_handle.current_workflow_generation()

    root_key = (pid, wgen, package)
    with _REGISTRY_LOCK:
        root_real = _ROOT_CACHE.get(root_key, _UNSET)
    if root_real is _UNSET:
        root_real, absent_reason = _resolve_package_root(package)
        with _REGISTRY_LOCK:
            _ROOT_CACHE[root_key] = root_real
            if root_real is None:
                _ROOT_ABSENT_REASON[root_key] = absent_reason or ''
    elif root_real is None:
        absent_reason = _ROOT_ABSENT_REASON.get(root_key,
                                                'package not resolvable')
    else:
        absent_reason = None
    if root_real is None:
        return _record(_absent(package, absent_reason), root_key)

    # Absent-state cache anchor: the package root itself (native_generated
    # does not exist there).  A workflow must not re-scan for a missing
    # artifact on every block.
    key_root = (pid, wgen, package, str(root_real), '-')
    with _REGISTRY_LOCK:
        cached = _REGISTRY.get(key_root) or _NEG_CACHE.get(key_root)
    if cached is not None:
        return cached

    native_root_real = Path(os.path.realpath(
        root_real.joinpath(*GENERATION_ROOT_PARTS)))
    if not native_root_real.is_dir():
        return _record(_absent(
            package, f'no {"/".join(GENERATION_ROOT_PARTS)} package '
                     f'resources in {package!r} (source install or '
                     f'no-native wheel)'), key_root)
    if not _contained_within(native_root_real, root_real):
        return _record(_corrupt(
            package, f'{"/".join(GENERATION_ROOT_PARTS)} resolves outside '
                     f'the installed package root ({native_root_real} not '
                     f'within {root_real})'), key_root)
    dev_root_real = Path(os.path.realpath(_dev_cache_root()))
    if _contained_within(native_root_real, dev_root_real):
        return _record(_corrupt(
            package, 'generation root resolves inside the legacy developer '
                     f'cache {_dev_cache_root()}; the packaged loader '
                     'never reads it'), key_root)

    key = (pid, wgen, package, str(native_root_real))
    with _REGISTRY_LOCK:
        cached = _REGISTRY.get(key) or _NEG_CACHE.get(key)
    if cached is not None:
        return cached

    candidates = sorted(entry for entry in native_root_real.iterdir()
                        if entry.is_dir() and not entry.name.startswith('.'))
    if not candidates:
        return _record(_absent(
            package, f'{"/".join(GENERATION_ROOT_PARTS)} contains no '
                     f'generation directories'), key)

    # EVERY candidate is gated, whatever the siblings look like: a corrupt
    # artifact sitting next to a qualified one never passes silently -- it
    # is recorded as a decline even though the qualified sibling executes.
    outcomes: list[LoadOutcome] = []
    qualified: tuple[Path, LoadOutcome] | None = None
    for cand in candidates:
        cand_real = Path(os.path.realpath(cand))
        if not _contained_within(cand_real, root_real):
            outcomes.append(_corrupt(
                package, f'generation {cand.name!r} resolves outside the '
                         f'installed package ({cand_real}); symlink '
                         f'escape'))
            continue
        outcome = _gate_candidate(cand_real, package)
        if outcome.status == STATUS_LOADED and qualified is None:
            qualified = (cand_real, outcome)  # deterministic sorted order
        elif outcome.status != STATUS_LOADED:
            outcomes.append(outcome)

    for sibling in outcomes:  # sibling declines stay visible privately
        _record(sibling, None)

    if qualified is None:
        # Nothing qualified: single outcomes pass through verbatim; for
        # several, the loudest status wins (corrupt > unqualified >
        # absent) with every reason merged in.
        if len(outcomes) == 1:
            return _record(outcomes[0], key)
        rank = {STATUS_CORRUPT: 3, STATUS_UNQUALIFIED: 2, STATUS_ABSENT: 1}
        worst = max(outcomes, key=lambda o: rank[o.status])
        merged = LoadOutcome(
            worst.status,
            '; '.join(f'{o.status}: {o.reason}' for o in outcomes),
            error=worst.error, package=package)
        return _record(merged, key)

    cand_real, outcome = qualified
    # Serialize with any publisher/peer on this directory (N8-10 lock),
    # re-check both caches in-lock, then load and publish.
    with native_handle._dir_lock(str(cand_real)):
        with _REGISTRY_LOCK:
            again = _REGISTRY.get(key) or _NEG_CACHE.get(key)
        if again is not None:
            return again
        try:
            verified = _verified_manifest(outcome)
            handle = _instantiate(
                cand_real, verified,
                QUALIFIED_TARGETS[verified['build']['target']])
        except native_handle.NativeHandleError as exc:
            loaded = LoadOutcome(STATUS_CORRUPT, str(exc),
                                 error=exc, package=package)
        except _VALIDATOR_FAILURE_SIGNALS as exc:
            # Review note N1 (TOCTOU bullet, folded in): the post-gate
            # manifest re-read and target lookup can raise non-taxonomy
            # exceptions only under concurrent external mutation mid-load.
            # Fail closed to the same recorded corrupt decline -- the bytes
            # under the changed tree were never re-verified end-to-end.
            loaded = LoadOutcome(
                STATUS_CORRUPT,
                f'validation raised an untyped validator failure '
                f'({type(exc).__name__}): {exc!r}',
                error=native_handle.CorruptNativeArtifact(
                    f'packaging defect: present-but-corrupt native artifact '
                    f'-- validation raised {type(exc).__name__} ({exc!r}) '
                    f'(auto declined to Numba and recorded this reason; '
                    f'explicit requests fail loudly)'),
                package=package)
        else:
            loaded = LoadOutcome(
                STATUS_LOADED, 'verified and loaded', handle=handle,
                generation=outcome.generation,
                generation_dir=cand_real, package=package)
        with _REGISTRY_LOCK:
            _REGISTRY[key] = loaded
    if loaded.status != STATUS_LOADED:
        # An in-lock decline (load-time failure, or the N1 untyped-failure
        # clause above) must reach the private decline log like every other
        # corrupt outcome; _record's cache guard sees the _REGISTRY entry
        # and only appends the diagnostic line.
        _record(loaded, key)
    return loaded


def _verified_manifest(outcome: LoadOutcome) -> dict:
    """Re-read the (already content-verified) manifest of a loaded
    outcome for instantiation metadata."""
    return json.loads((outcome.generation_dir / 'manifest.json')
                      .read_text())


def auto_load(package: str = PACKAGE) -> native_handle.NativeHandle | None:
    """AUTO path: the packaged qualified artifact, or None (quiet decline
    to Numba -- zero new output, no build attempt, reason recorded
    privately via decline_reasons())."""
    outcome = attempt_load(package)
    return outcome.handle if outcome.status == STATUS_LOADED else None


def load_explicit(package: str = PACKAGE) -> native_handle.NativeHandle:
    """EXPLICIT native request: the same verified load, or the loud
    taxonomy error (absent -> MissingNativeArtifact, corrupt ->
    CorruptNativeArtifact naming the packaging defect, unqualified host ->
    UnsupportedNativeISA with the capability gap)."""
    outcome = attempt_load(package)
    if outcome.status == STATUS_LOADED:
        return outcome.handle
    assert outcome.error is not None
    raise outcome.error


__all__ = [
    'PACKAGE', 'LoadOutcome',
    'STATUS_LOADED', 'STATUS_ABSENT', 'STATUS_CORRUPT',
    'STATUS_UNQUALIFIED',
    'attempt_load', 'auto_load', 'load_explicit',
    'decline_reasons', 'registry_snapshot', 'reset_for_tests',
    'MissingNativeArtifact', 'CorruptNativeArtifact', 'UnsupportedNativeISA',
]
