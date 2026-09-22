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
"""N8-10 workflow-owned native handle for the LW primary reducer.

`prepare_native_handle()` is called ONCE outside the repeated block loop
(dossier 01 'Handle lifecycle'); the immutable handle it returns carries the
loaded ctypes entry pointers for both scalar specializations (f32/f64) of one
gang dylib, plus the pid, workflow generation, content-derived artifact
generation, kernel-source digest and execution budget.

`NativeHandle.execute()` is the per-block call and performs ZERO
native-preparation work: no source IO, JSON parse, filesystem mkdir/stat,
compiler path lookup or subprocess call.  Per-call INPUT validation (dtype /
shape / stride / scalar-provenance / out-aliasing on caller arrays) STAYS in
execute -- that is invariant + dynamic validation, not loader prep.  The
validation logic is mirrored guard-for-guard from the reviewed adapter
``solweig_light.backends.native.lw_native.primary`` (read-only reuse of its
helper functions and ``UnsupportedInput``); the only structural change is that
the library is already loaded, so rejections cannot even construct a library.

Trust model (validation happens ONCE, at prepare, before any load):

* the artifact directory is an explicit parameter (packaged locations arrive
  with N8-20/N8-21; a ``manifest.json`` generation directory is recognized and
  content-verified when present);
* the legacy layout (``liblw_native_g{4,8}.dylib`` + ``build_stamp.json``) is
  accepted only when the stamp's ``kernel_sha256`` equals the sha256 of the
  packaged ``lw_primary.ispc`` and the stamp parses -- anything else is a
  DISTINCT ``CorruptNativeArtifact``; a missing dylib/dir/kernel is a DISTINCT
  ``MissingNativeArtifact``; a non-arm64 host or gang outside {4,8} is a
  DISTINCT ``UnsupportedNativeISA``; a failure of an ADMITTED C invocation is
  a DISTINCT ``NativeExecutionError``.  Stamp binding pins the kernel source;
  dylib authenticity proper (signed manifests) is N8-20/N8-21 territory --
  the dylib sha256 is recorded in the generation id either way;
* prepare NEVER builds.  The expert legacy build-on-demand route
  (``expert_build``: unique temp workdir, per-directory lock, atomic
  per-file publication, stamp written LAST) exists for explicit expert
  requests only and is not referenced by any prepare path;
* a failed prepare caches the failure per (pid, workflow generation, key) so a
  workflow does not retry missing artifacts every block; a new workflow
  generation retries.  Input validation and outputs are never cached;
* handles are pid-pinned: after a fork ``execute`` raises ``StaleNativeHandle``
  and the child must re-prepare (the registry is keyed by pid, so it loads a
  fresh CDLL -- the parent's pointers are never reused);
* a new workflow generation invalidates the prior handle for FUTURE prepares
  while a running workflow keeps the handle object it already holds (the
  library stays resident; we never dlclose while another thread may execute).
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
import platform
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

import numpy as np

# Read-only reuse of the reviewed adapter: its validation helpers, its ctypes
# prototype and its UnsupportedInput.  This module never mutates lw_native
# module globals (_LIBS / _LIB_DIR stay untouched; we own our CDLL).
import solweig_light.backends.native.lw_native as lw_native

UnsupportedInput = lw_native.UnsupportedInput

# Hot-path bindings of the reviewed adapter's validation helpers (bound once
# so execute() adds no per-call module attribute lookups of its own).
_need_array = lw_native._need_array
_need_c_contig = lw_native._need_c_contig
_scalar_spec = lw_native._scalar_spec
_reflection_spec = lw_native._reflection_spec
_buffer = lw_native._buffer
_extent = lw_native._extent
_ranges_overlap = lw_native._ranges_overlap
_MAX_PATCHES = lw_native.MAX_PATCHES

ABI_VERSION = 1
DEFAULT_MATH_PROFILE = 'lw_primary_v1'
_SUPPORTED_GANGS = (4, 8)
_ARM64_MACHINES = ('arm64', 'arm64e')
_ISPC_FALLBACK = '/opt/homebrew/bin/ispc'

_NATIVE_SRC_DIR = Path(lw_native.__file__).resolve().parent
_PACKAGE_KERNEL = _NATIVE_SRC_DIR / 'lw_primary.ispc'
_PACKAGE_BUILD_SH = _NATIVE_SRC_DIR / 'build.sh'

# Tests inject pid changes here (fork simulation); execute() resolves the
# module global at CALL time so already-created handles observe the change.
_getpid = os.getpid


# ---------------------------------------------------------------------------
# Error taxonomy (each is exercised by a distinct test)
# ---------------------------------------------------------------------------

class NativeHandleError(RuntimeError):
    """Base class: loud failures of the handle machinery (never a fallback)."""


class MissingNativeArtifact(NativeHandleError):
    """Artifact absent: no dylib / no artifact dir / no packaged kernel source.

    Auto semantics: the planner declines native BEFORE launch (the caller
    keeps Numba).  Expert semantics: an explicit request must build first via
    expert_build().  Both wordings are attached to the message.
    """


class CorruptNativeArtifact(NativeHandleError):
    """Artifact present but unverifiable: stamp missing/unreadable, stamp
    kernel_sha256 != packaged kernel digest, manifest digest mismatch."""


class UnsupportedNativeISA(NativeHandleError):
    """Host/ISA outside the qualified domain (non-arm64 host, gang not in
    {4,8}).  Capability failure, not an input failure."""


class NativeExecutionError(NativeHandleError):
    """An ADMITTED C invocation failed after launch (post-launch failures
    propagate loudly; only UnsupportedInput ever falls back)."""


class StaleNativeHandle(NativeHandleError):
    """execute() on a handle whose pid (fork) no longer matches; re-prepare
    in the child -- the parent's loaded pointers must never be reused."""


# ---------------------------------------------------------------------------
# Spec and registry
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class NativeHandleSpec:
    """Immutable preparation request; every field is part of the registry key
    (pid, artifact generation, ABI, ISA, math profile, pool budget)."""

    artifact_dir: Path | str | None = None   # None -> env/default legacy cache
    gang: int = 8
    isa: str = 'neon'
    math_profile: str = DEFAULT_MATH_PROFILE
    thread_budget: int = 1


_REGISTRY_LOCK = threading.Lock()
_REGISTRY: dict[tuple, 'NativeHandle'] = {}
_DIR_LOCKS: dict[str, threading.Lock] = {}
_NEG_CACHE: dict[tuple, NativeHandleError] = {}
_WORKFLOW_GENERATION = 'w0-initial'


def _dir_lock(resolved_dir: str) -> threading.Lock():
    """Per-artifact-directory lock: concurrent prepares of one directory (and
    an expert_build publishing into it) serialize here, so no reader ever
    observes half-published state."""
    with _REGISTRY_LOCK:
        lock = _DIR_LOCKS.get(resolved_dir)
        if lock is None:
            lock = _DIR_LOCKS[resolved_dir] = threading.Lock()
        return lock


def new_workflow_generation(token: str | None = None) -> str:
    """Advance the workflow generation.  Subsequent prepares use the new
    token (fresh handle, retry of previously unavailable capability); handles
    already handed out keep working for their owning workflow."""
    global _WORKFLOW_GENERATION
    _WORKFLOW_GENERATION = token or uuid.uuid4().hex
    _NEG_CACHE.clear()
    return _WORKFLOW_GENERATION


def current_workflow_generation() -> str:
    return _WORKFLOW_GENERATION


def reset_for_tests() -> None:
    """Test-only: drop registry/negative cache and reset the generation."""
    global _WORKFLOW_GENERATION
    with _REGISTRY_LOCK:
        _REGISTRY.clear()
        _NEG_CACHE.clear()
    _WORKFLOW_GENERATION = 'w0-initial'


def registry_snapshot() -> dict[tuple, str]:
    """Diagnostics: registry key -> handle generation id (no IO)."""
    with _REGISTRY_LOCK:
        return {key: h.generation for key, h in _REGISTRY.items()}


def _resolve_artifact_dir(explicit) -> str:
    """Resolve the artifact directory WITHOUT touching the filesystem: an
    explicit parameter wins, then SOLWEIG_LIGHT_NATIVE_CACHE, then the
    per-user legacy cache default.  Missing dirs are reported by validation,
    not by mkdir -- prepare never creates anything."""
    if explicit is not None:
        return str(Path(os.fspath(explicit)))
    env = os.environ.get('SOLWEIG_LIGHT_NATIVE_CACHE')
    if env:
        return str(Path(env))
    return str(Path.home() / '.cache' / 'solweig-light' / 'native')


# ---------------------------------------------------------------------------
# One-time artifact validation (all filesystem/hash/JSON work lives here)
# ---------------------------------------------------------------------------

def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_artifact(resolved_dir: str, gang: int
                       ) -> tuple[str, dict, str]:
    """Validate the artifact content ONCE and derive its generation id.

    Returns (generation_id, stamp_dict, kernel_digest).  Raises the taxonomy
    errors above; performs no writes and never builds.
    """
    if platform.machine() not in _ARM64_MACHINES:
        raise UnsupportedNativeISA(
            f'host {platform.machine()!r} is outside the qualified arm64/'
            f'neon domain of the reviewed dylibs')
    if gang not in _SUPPORTED_GANGS:
        raise UnsupportedNativeISA(
            f'gang must be one of {_SUPPORTED_GANGS}, got {gang!r}')

    if not _PACKAGE_KERNEL.is_file():
        raise MissingNativeArtifact(
            f'packaged kernel source {_PACKAGE_KERNEL} is missing; '
            f'auto: native is declined pre-launch (Numba fallback). '
            f'expert: reinstall the package or point artifact_dir at a '
            f'verified generation directory.')

    artifact_dir = Path(resolved_dir)
    dylib = artifact_dir / f'liblw_native_g{gang}.dylib'
    if not artifact_dir.is_dir() or not dylib.is_file():
        raise MissingNativeArtifact(
            f'native artifact {dylib} not found (artifact_dir='
            f'{resolved_dir!r}); auto: the planner declines native '
            f'pre-launch and keeps Numba. expert: build it explicitly with '
            f'expert_build({resolved_dir!r}) or run the packaged build.sh.')

    kernel_digest = _sha256_file(_PACKAGE_KERNEL)
    dylib_digest = _sha256_file(dylib)

    stamp = _load_and_check_stamp(artifact_dir, kernel_digest)
    _verify_manifest_if_present(artifact_dir)

    generation_seed = '\n'.join((
        f'abi={ABI_VERSION}', f'gang={gang}',
        f'kernel_sha256={kernel_digest}',
        f'dylib={dylib.name}:sha256={dylib_digest}',
        f'stamp_built_utc={stamp.get("built_utc", "")}',
        f'stamp_ispc={stamp.get("ispc", "")}',
    ))
    generation = hashlib.sha256(generation_seed.encode()).hexdigest()
    return generation, stamp, kernel_digest


def _load_and_check_stamp(artifact_dir: Path, kernel_digest: str) -> dict:
    """Legacy build_stamp.json gate: the stamp is the B7 generation key."""
    stamp_path = artifact_dir / 'build_stamp.json'
    try:
        stamp = json.loads(stamp_path.read_text())
    except FileNotFoundError:
        raise CorruptNativeArtifact(
            f'{stamp_path} missing: dylib present but its kernel binding '
            f'is unverifiable (refusing to load). expert: rebuild with '
            f'expert_build({str(artifact_dir)!r}) to write a valid stamp.') from None
    except (OSError, ValueError) as exc:
        raise CorruptNativeArtifact(
            f'{stamp_path} unreadable/invalid JSON: {exc!r}') from exc
    stamped = stamp.get('kernel_sha256')
    if stamped != kernel_digest:
        raise CorruptNativeArtifact(
            f'stamp kernel_sha256 {stamped!r} != packaged kernel digest '
            f'{kernel_digest!r}: artifact was built from different source '
            f'(mismatched digest). auto: decline native. expert: rebuild.')
    return stamp


def _verify_manifest_if_present(artifact_dir: Path) -> None:
    """Packaged generation directory (N8-20 layout): verify every listed
    file's sha256 when a manifest.json exists.  Absent manifest -> legacy
    layout, stamp already gated."""
    manifest_path = artifact_dir / 'manifest.json'
    if not manifest_path.is_file():
        return
    try:
        manifest = json.loads(manifest_path.read_text())
    except (OSError, ValueError) as exc:
        raise CorruptNativeArtifact(
            f'{manifest_path} unreadable/invalid JSON: {exc!r}') from exc
    files = manifest.get('files') if isinstance(manifest, dict) else None
    if not isinstance(files, dict):
        return  # schema subset we can check; full validation is N8-21's
    for rel, expected in files.items():
        member = artifact_dir / rel
        if not member.is_file():
            raise CorruptNativeArtifact(
                f'manifest lists {rel!r} but it is missing from the '
                f'generation directory')
        if _sha256_file(member) != expected:
            raise CorruptNativeArtifact(
                f'manifest digest mismatch for {rel!r}')


# ---------------------------------------------------------------------------
# The handle
# ---------------------------------------------------------------------------

class NativeHandle:
    """Process + workflow-generation-scoped loaded native reducer.

    Immutable after prepare (entries are never rebound; execute only reads).
    The CDLL owner reference is kept alive for the process lifetime -- we do
    not dlclose while any thread may still execute the code.
    """

    __slots__ = ('_lib', '_entries', '_pid', '_workflow_generation',
                 '_generation', '_kernel_digest', '_gang', '_spec', '_stamp',
                 '_thread_budget', '_prepared')

    def __init__(self, lib, entries, pid, workflow_generation, generation,
                 kernel_digest, gang, spec, stamp):
        self._lib = lib                    # CDLL owner (kept alive)
        self._entries = entries            # {'f32': fn, 'f64': fn}
        self._pid = pid
        self._workflow_generation = workflow_generation
        self._generation = generation
        self._kernel_digest = kernel_digest
        self._gang = gang
        self._spec = spec
        self._stamp = stamp
        self._thread_budget = spec.thread_budget
        self._prepared = True

    # -- identity (cached strings; no IO) --------------------------------

    @property
    def pid(self) -> int:
        return self._pid

    @property
    def workflow_generation(self) -> str:
        return self._workflow_generation

    @property
    def generation(self) -> str:
        return self._generation

    @property
    def kernel_digest(self) -> str:
        return self._kernel_digest

    @property
    def gang(self) -> int:
        return self._gang

    @property
    def entry_specs(self) -> tuple[str, ...]:
        return tuple(self._entries)

    @property
    def thread_budget(self) -> int:
        return self._thread_budget

    def identity(self) -> dict:
        """Runtime fingerprint (no IO): everything was captured at prepare."""
        return {
            'backend': 'native_handle_lw_primary',
            'abi_version': ABI_VERSION,
            'generation': self._generation,
            'pid': self._pid,
            'workflow_generation': self._workflow_generation,
            'kernel_sha256': self._kernel_digest,
            'gang': self._gang,
            'scalar_entry_map': {k: f'lw_primary_{k}'
                                 for k in self._entries},
            'thread_budget': self._thread_budget,
            'math_profile': self._spec.math_profile,
            'isa': self._spec.isa,
            'stamp': dict(self._stamp),
            'effective_threads': 1,
        }

    # -- execution --------------------------------------------------------

    def execute(self, sh, vs, vb, sun, shade, solid, sine, cosine,
                directions, gate, solar_gate, sky_down, sky_side,
                surface_sun, surface_sh, lup, reflection_factor,
                out=None) -> np.ndarray:
        """17-argument drop-in for _longwave_primary; returns float32 [B,7].

        Zero loader work: validation below mirrors
        lw_native.primary guard-for-guard (same order, same UnsupportedInput
        class), then dispatches straight to the pre-loaded entry pointer.
        """
        if _getpid() != self._pid:
            raise StaleNativeHandle(
                f'handle pid {self._pid} != current pid {_getpid()}; fork '
                f'detected -- re-prepare in the child, never reuse the '
                f'parent’s loaded pointers')

        # ---- validation (all rejections happen before any native work) ----
        _need_array(sh, 'sh', np.float32, 2)
        B, P = sh.shape
        if not (1 <= P <= _MAX_PATCHES):
            raise UnsupportedInput(
                f'P={P} outside admitted 1..{_MAX_PATCHES}')
        if B < 0:
            raise UnsupportedInput(f'B={B} negative')
        if B == 0:
            # Original supports B=0: prange(0) yields the zero-filled frame.
            return np.zeros((0, 7), dtype=np.float32)

        _need_array(vs, 'vs', np.float32, 2, sh.shape)
        _need_array(vb, 'vb', np.float32, 2, sh.shape)
        for name, arr in (('sh', sh), ('vs', vs), ('vb', vb)):
            _need_c_contig(arr, name, 4)
        for name, arr in (('sun', sun), ('shade', shade)):
            _need_array(arr, name, np.bool_, 2, sh.shape)
            _need_c_contig(arr, name, 1)
        for name, arr in (('solid', solid), ('sine', sine),
                          ('cosine', cosine)):
            _need_array(arr, name, np.float32, 1, (P,))
            _need_c_contig(arr, name, 4)
        _need_array(solar_gate, 'solar_gate', np.bool_, 1, (P,))
        if solar_gate.strides != (1,):
            raise UnsupportedInput(
                f'solar_gate: strides {solar_gate.strides} != (1,)')
        for name, arr in (('sky_down', sky_down), ('sky_side', sky_side)):
            _need_array(arr, name, np.float32, 1, (P,))
        _need_array(directions, 'directions', np.float32, 2, (P, 4))
        _need_array(gate, 'gate', np.bool_, 2, (P, 4))
        _need_array(lup, 'lup', np.float32, 1, (B,))
        _need_c_contig(lup, 'lup', 4)

        spec = _scalar_spec(surface_sun, 'surface_sun')
        if spec != _scalar_spec(surface_sh, 'surface_sh'):
            raise UnsupportedInput(
                f'surface scalar specialization mismatch: surface_sun is '
                f'{spec}, surface_sh is '
                f'{_scalar_spec(surface_sh, "surface_sh")}')
        refl = _reflection_spec(reflection_factor)

        if out is not None:
            _need_array(out, 'out', np.float32, 2, (B, 7))
            _need_c_contig(out, 'out', 4)
            if not out.flags.writeable:
                # a direct-pointer adapter does not make read-only NumPy
                # memory writable safely (dossier: dynamic out checks stay)
                raise UnsupportedInput(
                    'out is read-only; rejecting before native launch')
            out_range = _extent(out)
            for name, arr in (('sh', sh), ('vs', vs), ('vb', vb),
                              ('sun', sun), ('shade', shade),
                              ('solid', solid), ('sine', sine),
                              ('cosine', cosine), ('solar_gate', solar_gate),
                              ('sky_down', sky_down), ('sky_side', sky_side),
                              ('lup', lup), ('directions', directions),
                              ('gate', gate)):
                if _ranges_overlap(out_range, _extent(arr)):
                    raise UnsupportedInput(
                        f'out aliases input {name}; rejecting before launch')

        # bool arrays are uint8 storage with values 0/1: zero-copy views.
        sun_u8 = sun.view(np.uint8)
        shade_u8 = shade.view(np.uint8)
        gate_u8 = solar_gate.view(np.uint8)

        if out is None:
            out = np.empty((B, 7), dtype=np.float32)

        entry = self._entries[spec]
        try:
            entry(
                _buffer(sh), _buffer(vs), _buffer(vb),
                _buffer(sun_u8), _buffer(shade_u8),
                _buffer(solid), _buffer(sine), _buffer(cosine),
                _buffer(gate_u8),
                _buffer(sky_down), sky_down.strides[0] // 4,
                _buffer(sky_side), sky_side.strides[0] // 4,
                float(surface_sun), float(surface_sh),
                _buffer(lup),
                refl,
                B, P,
                _buffer(out),
            )
        except Exception as exc:  # admitted call failed after launch
            raise NativeExecutionError(
                f'admitted native lw_primary_{spec} invocation failed '
                f'(generation {self._generation[:12]}...): '
                f'{type(exc).__name__}: {exc}') from exc
        return out


# ---------------------------------------------------------------------------
# prepare (once per key; all IO lives here and only here)
# ---------------------------------------------------------------------------

def _registry_key(spec: NativeHandleSpec, pid: int,
                  workflow_generation: str) -> tuple:
    resolved = _resolve_artifact_dir(spec.artifact_dir)
    return (pid, workflow_generation, resolved, spec.gang, ABI_VERSION,
            spec.isa, spec.math_profile, spec.thread_budget)


def _load_entries(resolved_dir: str, gang: int
                  ) -> tuple[ctypes.CDLL, dict[str, ctypes._FuncPointer]]:
    """Own CDLL + entry pointers (lw_native._LIBS is never touched)."""
    dylib = Path(resolved_dir) / f'liblw_native_g{gang}.dylib'
    lib = ctypes.CDLL(str(dylib))
    entries = {}
    for scalar_spec in ('f32', 'f64'):
        fn = getattr(lib, f'lw_primary_{scalar_spec}')
        proto = list(lw_native._PROTO)
        if scalar_spec == 'f32':   # surface scalars pinned to float
            proto[13] = ctypes.c_float
            proto[14] = ctypes.c_float
        fn.argtypes = proto
        fn.restype = None
        entries[scalar_spec] = fn
    return lib, entries


def prepare_native_handle(spec: NativeHandleSpec | None = None, *,
                          artifact_dir=None, gang: int = 8,
                          workflow_generation: str | None = None,
                          ) -> NativeHandle:
    """Validate the artifact once, load both scalar entries, return the
    process-local immutable handle.  All hash/JSON/stat work happens here and
    never in execute().  Failures are cached per (pid, workflow generation,
    key) so a workflow retries unavailable capability only on a new
    generation.  NEVER builds -- see expert_build for the explicit route.
    """
    if spec is None:
        spec = NativeHandleSpec(artifact_dir=artifact_dir, gang=gang)
    pid = _getpid()
    wgen = workflow_generation or current_workflow_generation()
    key = _registry_key(spec, pid, wgen)

    with _REGISTRY_LOCK:
        cached = _REGISTRY.get(key)
        failure = _NEG_CACHE.get(key)
    if cached is not None and cached.pid == pid:
        return cached
    if failure is not None:
        raise failure

    resolved = key[2]
    with _dir_lock(resolved):
        with _REGISTRY_LOCK:                       # double-checked
            cached = _REGISTRY.get(key)
        if cached is not None and cached.pid == pid:
            return cached
        try:
            generation, stamp, kernel_digest = _validate_artifact(
                resolved, spec.gang)
            lib, entries = _load_entries(resolved, spec.gang)
        except NativeHandleError as exc:
            with _REGISTRY_LOCK:
                _NEG_CACHE.setdefault(key, exc)
            raise
        handle = NativeHandle(lib, entries, pid, wgen, generation,
                              kernel_digest, spec.gang, spec, stamp)
        with _REGISTRY_LOCK:
            _REGISTRY[key] = handle   # publish fully-built only
        return handle


# ---------------------------------------------------------------------------
# Expert legacy build route (explicit requests ONLY; never called by prepare)
# ---------------------------------------------------------------------------

def _atomic_write_bytes(path: Path, data: bytes) -> None:
    """Publish file content atomically: temp file in the same directory,
    fsync, single rename."""
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent),
                                    prefix=f'.{path.name}.',
                                    suffix='.tmp')
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, 'wb') as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def expert_build(artifact_dir, *, kernel: Path | None = None,
                 ispc: str | None = None, gangs: tuple[int, ...] = (4, 8)
                 ) -> dict:
    """Deliberate expert build of the legacy dylibs into ``artifact_dir``.

    Mirrors the reviewed build.sh (toolchain-pinned ISPC, -O2
    --opt=disable-fma --math-lib=default --pic, in-script FMA audit) but
    publishes under the per-directory lock from a unique temp workdir with
    atomic per-file renames and the build stamp written LAST (manifest-last
    semantics: a concurrent validated reader sees old-stamp+old-content or
    new-stamp+new-content, never a mixed generation).  Raises RuntimeError
    loudly on any failure.  This function is never referenced by prepare.
    """
    artifact_dir = Path(os.fspath(artifact_dir))
    artifact_dir.mkdir(parents=True, exist_ok=True)
    kernel = Path(kernel) if kernel is not None else _PACKAGE_KERNEL
    ispc = ispc or shutil.which('ispc') or _ISPC_FALLBACK
    if not Path(ispc).exists():
        raise RuntimeError(
            f'expert_build requested but ispc was not found at {ispc!r}; '
            f'install ISPC (>= 1.31) or pass ispc=<path>')
    if not kernel.is_file() or not _PACKAGE_BUILD_SH.is_file():
        raise RuntimeError(
            f'expert_build needs {kernel} and {_PACKAGE_BUILD_SH}')

    with _dir_lock(str(artifact_dir)):
        work = Path(tempfile.mkdtemp(dir=str(artifact_dir),
                                     prefix='.expert-build-'))
        try:
            shutil.copy2(kernel, work / 'lw_primary.ispc')
            shutil.copy2(_PACKAGE_BUILD_SH, work / 'build.sh')
            proc = subprocess.run(['/bin/zsh', 'build.sh'],
                                  cwd=work, capture_output=True, text=True,
                                  env={**os.environ, 'ISPC': ispc})
            if proc.returncode != 0:
                raise RuntimeError(
                    f'expert_build failed (rc={proc.returncode}):\n'
                    f'{proc.stdout[-800:]}\n{proc.stderr[-800:]}')
            # publish: dylibs first (atomic rename each), stamp LAST
            for gang in gangs:
                built = work / f'liblw_native_g{gang}.dylib'
                if not built.is_file():
                    raise RuntimeError(
                        f'build reported success but {built} is missing')
                os.replace(built, artifact_dir / built.name)
            stamp = {
                'kernel_sha256': hashlib.sha256(
                    kernel.read_bytes()).hexdigest(),
                'ispc': str(ispc),
                'built_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ',
                                           time.gmtime()),
            }
            _atomic_write_bytes(artifact_dir / 'build_stamp.json',
                                json.dumps(stamp).encode())
        finally:
            shutil.rmtree(work, ignore_errors=True)
    return stamp


__all__ = [
    'ABI_VERSION', 'NativeHandle', 'NativeHandleSpec',
    'prepare_native_handle', 'expert_build',
    'new_workflow_generation', 'current_workflow_generation',
    'registry_snapshot', 'reset_for_tests',
    'NativeHandleError', 'MissingNativeArtifact', 'CorruptNativeArtifact',
    'UnsupportedNativeISA', 'NativeExecutionError', 'StaleNativeHandle',
    'UnsupportedInput',
]
