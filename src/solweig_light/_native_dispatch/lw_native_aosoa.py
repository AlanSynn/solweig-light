#SOLWEIG-GPU: GPU-accelerated SOLWEIG model for urban thermal comfort simulation
#Copyright (C) 2022–2025 Harsh Kamth and Naveen Sudharsan

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
"""N8-13 native ctypes adapter for the direct AoSoA consumer (dossier 02).

`primary_aosoa()` is the AoSoA-domain twin of
``solweig_light.backends.native.lw_native.primary`` (:169-219): the SAME
C ABI (argtypes borrowed verbatim from ``lw_native._PROTO``, both exact
scalar specializations f32/f64 bound like ``lw_native._load``), the SAME
rejection set in the same order and the same ``UnsupportedInput`` class,
with exactly three sanctioned deltas required by the input-domain change:

1. sh/vs/vb are the producer's [G,P,W] payload passed as its float32 view
   (``block.view(np.float32)``; W=8, G=ceil(B/8), element
   ((g*P+p)*W+lane)) -- the N8-11 review note N6 binding convention for
   wave-2 consumers, and the same dtype lw_native.primary admits for its
   dense sh. The raw uint32 block is rejected with guidance (it would
   change a numba consumer's promotion; one bound dtype keeps B/C
   comparisons comparable). sun/shade are bool [G,P,W]. The row count B
   arrives as an explicit parameter (it is no longer derivable from the
   array shape) and is pinned to the gang count: G must equal ceil(B/8).
   Padding lanes are never validated numerically and never read by the
   kernel (tail-gang index redirection, see lw_primary_aosoa.ispc).
2. 0-d ndarray ``reflection_factor`` is PINNED, not narrowed (review note
   N7 of n8_30_review_n8_10_loader, carried from N8-04): the shipped
   numba path and ``lw_native._reflection_spec`` admit a 0-d float32
   ndarray computing as float32, so this adapter keeps the identical
   documented normalize (``float(x[()])``) and enforces it with positive
   AND negative tests in tests/optimization_v8/native/ BEFORE launch.
   Python float stays rejected (it would promote the reflection chain to
   float64 and change the typed graph).
3. A native failure AFTER launch raises ``NativeExecutionError`` and is
   never hidden: only ``UnsupportedInput`` is a pre-launch decline (the
   dispatcher-style fallback signal); everything else is loud.

Artifacts are loaded from an N8-20 generation directory (manifest.json
layout) -- the directory is fully content-verified through
``build_native.verify_generation`` (which re-runs the FMA audit on the
shipped assembly) before the CDLL is constructed. The default location is
the ``stage/`` directory next to this module; an explicit
``generation_dir=`` always wins. This is an experiment-scope adapter: it
is NOT wired into any dispatcher and enables no default.

Symbol names reuse the B7 C-ABI names (lw_primary_f32/lw_primary_f64) so
the scalar-specialization binding and manifest schema of the N8-20 driver
stay truthful; the AoSoA interpretation of the first five pointers is
carried by this adapter plus the kernel identity recorded in the
generation manifest (kernel name + sha256), never by symbol-table
conventions.
"""
from __future__ import annotations

import ctypes
import numbers
from pathlib import Path

import numpy as np

import solweig_light.backends.native.lw_native as lw_native

# Read-only reuse of the reviewed adapter's validation helpers, prototype
# and error class (same pattern as experiments/optimization_v8/loader/
# native_handle.py). This module never mutates lw_native globals.
UnsupportedInput = lw_native.UnsupportedInput
_need_array = lw_native._need_array
_need_c_contig = lw_native._need_c_contig
_scalar_spec = lw_native._scalar_spec
_reflection_spec = lw_native._reflection_spec
_buffer = lw_native._buffer
_extent = lw_native._extent
_ranges_overlap = lw_native._ranges_overlap
_PROTO = lw_native._PROTO
_MAX_PATCHES = lw_native.MAX_PATCHES

WIDTH = 8                      # lane width this consumer is compiled for
_MODULE_DIR = Path(__file__).resolve().parent
# N8-41 vendoring: the default staging root stays the maintainer-tree N8-13
# stage (evidence durability; the dev-build artifacts staged there are what
# the tests and the staged-expert route load). The installed-artifact home
# is the N8-21 loader, which activates with the wheels-time expert flip.
_DEFAULT_STAGE = _MODULE_DIR.parents[2] / 'experiments' / 'optimization_v8' \
    / 'native' / 'stage'


class NativeArtifactError(RuntimeError):
    """Generation directory absent/unverifiable (loud; never a fallback)."""


class NativeExecutionError(RuntimeError):
    """An ADMITTED C invocation failed after launch; never hidden."""


_GENERATIONS: dict[str, tuple[ctypes.CDLL, dict[str, ctypes._FuncPointer]]] = {}


def _resolve_generation_dir(generation_dir) -> Path:
    if generation_dir is not None:
        return Path(generation_dir)
    if not _DEFAULT_STAGE.is_dir():
        raise NativeArtifactError(
            f'no generation directory: default staging {_DEFAULT_STAGE} is '
            f'absent; build one with build_aosoa.py or pass generation_dir=')
    candidates = sorted(p for p in _DEFAULT_STAGE.iterdir()
                        if p.is_dir() and p.name.startswith('lw-g8-'))
    if not candidates:
        raise NativeArtifactError(
            f'no lw-g8-* generation under {_DEFAULT_STAGE}; build one with '
            f'build_aosoa.py or pass generation_dir=')
    return candidates[-1]


def _bind_entries(lib: ctypes.CDLL) -> dict[str, ctypes._FuncPointer]:
    """Both scalar specializations, argtypes pinned like lw_native._load."""
    entries = {}
    for spec in ('f32', 'f64'):
        fn = getattr(lib, f'lw_primary_{spec}')
        proto = list(_PROTO)
        if spec == 'f32':   # surface scalars pinned to float
            proto[13] = ctypes.c_float
            proto[14] = ctypes.c_float
        fn.argtypes = proto
        fn.restype = None
        entries[spec] = fn
    return entries


def load_generation(generation_dir=None):
    """Content-verify an N8-20 generation dir, then own its CDLL + entries.

    Verification (manifest schema, generation-name derivation, artifact
    hashes, Mach-O structure, re-audit of the shipped assembly for FMA
    contraction) is build_native.verify_generation -- read-only reuse; the
    FMA gate therefore binds to the bytes that are actually loaded. The
    loaded library is cached per resolved directory (generations are
    immutable) and never dlclosed.
    """
    gen_dir = _resolve_generation_dir(generation_dir)
    key = str(gen_dir.resolve())
    cached = _GENERATIONS.get(key)
    if cached is not None:
        return cached
    import sys
    # N8-41 vendoring: build_native stays maintainer-tree infrastructure
    # (not vendored; see installed_loader for the full rationale). The old
    # maintainer-tree expression resolved this dir only via the test
    # harness bootstrap; the vendored module anchors it explicitly so
    # sys.modules['build_native'] stays one shared object.
    from solweig_light._native_dispatch import experiments_dir
    packaging = str(experiments_dir('packaging'))
    if packaging not in sys.path:
        sys.path.insert(0, packaging)
    from build_native import verify_generation
    try:
        verify_generation(gen_dir)
    except Exception as exc:  # corrupt/missing/failed-verification artifact
        raise NativeArtifactError(
            f'generation {gen_dir} failed content verification: '
            f'{type(exc).__name__}: {exc}') from exc
    lib = ctypes.CDLL(key + '/liblw_native_g8.dylib')
    entries = _bind_entries(lib)
    _GENERATIONS[key] = (lib, entries)
    return _GENERATIONS[key]


def _need_payload(x, name, shape=None):
    """float32 [G,P,W] view of the producer payload, W==8.

    N8-11 review note N6 (binding for wave-2 consumers): the consumer
    contract is the producer block viewed ``.view(np.float32)`` -- the
    same dtype lw_native.primary admits for its dense sh. The raw uint32
    block is rejected with guidance (a numba consumer fed uint32 would
    change promotion; binding one dtype keeps B/C comparisons
    comparable). The view is bit-preserving, so this is an admission
    narrowing, not an arithmetic change.
    """
    if not isinstance(x, np.ndarray):
        raise UnsupportedInput(
            f'{name}: expected ndarray, got {type(x)!r}')
    if x.dtype != np.float32:
        raise UnsupportedInput(
            f'{name}: dtype {x.dtype} != float32 (pass the producer block '
            f'as block.view(np.float32) -- bound wave-2 consumer '
            f'convention, N8-11 review note N6)')
    if x.ndim != 3:
        raise UnsupportedInput(f'{name}: ndim {x.ndim} != 3')
    if x.shape[2] != WIDTH:
        raise UnsupportedInput(
            f'{name}: lane width {x.shape[2]} != {WIDTH} (W=8 consumer)')
    if shape is not None and x.shape != shape:
        raise UnsupportedInput(f'{name}: shape {x.shape} != {shape}')


def _need_c_contig3(x, name, itemsize=None):
    """C-contiguity for the [G,P,W] buffers.

    The kernel addresses elements at the flat C-linearization
    ((g*P+p)*W+lane), which is exactly what numpy's C_CONTIGUOUS flag
    guarantees for the shape. Exact stride equality (lw_native's 2-D
    guard) is WRONG in 3-D: numpy collapses strides across size-1
    dimensions (a (1,1,8) C-contiguous buffer legitimately carries
    strides (32,4,4)), so literal comparison would falsely decline
    admitted inputs. ``itemsize`` retained for call-site symmetry.
    """
    if not x.flags.c_contiguous:
        raise UnsupportedInput(
            f'{name}: strides {x.strides} are not C-contiguous for shape '
            f'{x.shape}')


def primary_aosoa(sh, vs, vb, sun, shade, solid, sine, cosine, directions,
                  gate, solar_gate, sky_down, sky_side, surface_sun,
                  surface_sh, lup, reflection_factor, B, out=None,
                  generation_dir=None) -> np.ndarray:
    """Run the AoSoA ISPC port of _longwave_primary; returns float32 [B,7].

    ``B`` is the block's pixel-row count; sh/vs/vb/sun/shade must supply
    exactly ceil(B/8) gangs of the N8-11 lane layout.
    """
    _, entries = load_generation(generation_dir)

    # ---- validation (all rejections happen before any native work) ----
    _need_payload(sh, 'sh')
    G, P, _ = sh.shape
    if not (1 <= P <= _MAX_PATCHES):
        raise UnsupportedInput(f'P={P} outside admitted 1..{_MAX_PATCHES}')
    if isinstance(B, bool) or not isinstance(B, numbers.Integral):
        raise UnsupportedInput(
            f'B: expected an integer pixel-row count, got {type(B)!r}')
    B = int(B)
    if B < 0:
        raise UnsupportedInput(f'B={B} negative')
    gangs = -(-B // WIDTH)
    if G != gangs:
        raise UnsupportedInput(
            f'sh: {G} gangs != ceil(B/{WIDTH})={gangs} for B={B}')
    if B == 0:
        # Original supports B=0: prange(0) yields the zero-filled frame.
        return np.zeros((0, 7), dtype=np.float32)

    _need_payload(vs, 'vs', sh.shape)
    _need_payload(vb, 'vb', sh.shape)
    for name, arr in (('sh', sh), ('vs', vs), ('vb', vb)):
        _need_c_contig3(arr, name)
    for name, arr in (('sun', sun), ('shade', shade)):
        _need_array(arr, name, np.bool_, 3, sh.shape)
        _need_c_contig3(arr, name)
    for name, arr in (('solid', solid), ('sine', sine), ('cosine', cosine)):
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
    # 0-d float32 ndarray admitted via the documented normalize (pin, not
    # narrow -- see module docstring; pinned by tests before any launch).
    refl = _reflection_spec(reflection_factor)

    if out is not None:
        _need_array(out, 'out', np.float32, 2, (B, 7))
        _need_c_contig(out, 'out', 4)
        if not out.flags.writeable:
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

    # bool arrays are uint8 storage with values 0/1: zero-copy views. The
    # payload arrays are already the float32 views the admission contract
    # requires (note N6) -- no further conversion anywhere.
    shf, vsf, vbf = sh, vs, vb
    sun_u8 = sun.view(np.uint8)
    shade_u8 = shade.view(np.uint8)
    gate_u8 = solar_gate.view(np.uint8)

    if out is None:
        out = np.empty((B, 7), dtype=np.float32)

    try:
        entries[spec](
            _buffer(shf), _buffer(vsf), _buffer(vbf),
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
            f'admitted native lw_primary_{spec} (AoSoA) invocation failed: '
            f'{type(exc).__name__}: {exc}') from exc
    return out


__all__ = ['primary_aosoa', 'load_generation', 'WIDTH',
           'UnsupportedInput', 'NativeArtifactError', 'NativeExecutionError']
