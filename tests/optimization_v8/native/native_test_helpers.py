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
"""N8-13 native-consumer shared test helpers (uniquely named, N-D2 repair).

Same content the conftest used to export, in a module whose name cannot
collide with any other package's ``conftest`` when test trees are collected
together (the region-shadowing bug class the n8-rev-n8-14 delta review
closed; see also the region_test_helpers.py pattern). Tests and experiment
scripts import THIS module; conftest.py keeps only the pytest fixture.

Imports the module under test (the packaged one since N8-41 vendoring;
READ-ONLY reuses two frozen modules:

* the N8-04 adversarial input constructor
  (tests/optimization_v8/reference/test_typed_graph_identity.py) via
  importlib under a distinct module name, exactly like the N8-10 loader
  conftest -- nothing under tests/optimization_v8/reference/ is modified;
* the N8-11 producer (experiments/optimization_v8/layout/direct_aosoa.py)
  for producer-output bit-identity -- the producer is consumed, never
  modified.

All kernels exercised are serial (no prange, no thread-cap env).
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np

_REPO = Path(__file__).resolve().parents[3]
# N8-41 vendoring: lw_native_aosoa / direct_aosoa are imported from the
# package (solweig_light._native_dispatch); no experiment dir goes on
# sys.path anymore. The reference suite stays a sys.path entry (the
# frozen oracle modules are read in place, never moved).
_NATIVE_DIR = _REPO / 'experiments' / 'optimization_v8' / 'native'
_PACKAGING_DIR = _REPO / 'experiments' / 'optimization_v8' / 'packaging'
_REFERENCE_DIR = _REPO / 'tests' / 'optimization_v8' / 'reference'
if str(_REFERENCE_DIR) not in sys.path:
    sys.path.insert(0, str(_REFERENCE_DIR))

from solweig_light._native_dispatch import lw_native_aosoa  # noqa: E402  (module under test)

# Read-only reuse of the frozen N8-04 adversarial grid constructor.
_spec = importlib.util.spec_from_file_location(
    'lw_identity_grid', _REFERENCE_DIR / 'test_typed_graph_identity.py')
lw_identity_grid = importlib.util.module_from_spec(_spec)
sys.modules['lw_identity_grid'] = lw_identity_grid
_spec.loader.exec_module(lw_identity_grid)

adversarial_inputs = lw_identity_grid.adversarial_inputs
_pin_args = lw_identity_grid._pin_args

from lw_reference_oracle import (F32, bitwise_equal, kernel_pair,  # noqa: E402
                                 lw_primary_reference, u32)
from solweig_light._native_dispatch import direct_aosoa as da  # noqa: E402  (N8-11 producer, read-only)

_PARALLEL, SERIAL = kernel_pair()

WIDTH = 8
POISON = 0x7FC0DEAD      # NaN-ish padding poison for payload lanes


def aosoa_rows(bits):
    """[G,P,W] -> logical [G*W, P] rows (row = gang*width + lane)."""
    gangs, patches, width = bits.shape
    return bits.transpose(0, 2, 1).reshape(gangs * width, patches)


def pack_payload(dense, B, poison=POISON):
    """float32 [B,P] -> C-contiguous float32 [G,P,8] view of the packed
    payload, poison padding lanes (N8-11 review note N6 convention: the
    consumer is fed the .view(np.float32) block)."""
    P = dense.shape[1]
    G = -(-B // WIDTH)
    flat = np.full((G * WIDTH, P), poison, dtype=np.uint32)
    if B:
        flat[:B] = dense.view(np.uint32)
    return np.ascontiguousarray(
        flat.reshape(G, WIDTH, P).transpose(0, 2, 1)).view(np.float32)


def pack_mask(mask, B, pad=True):
    """bool [B,P] -> C-contiguous bool [G,P,8] (padding lanes `pad`)."""
    P = mask.shape[1]
    G = -(-B // WIDTH)
    flat = np.full((G * WIDTH, P), pad, dtype=np.bool_)
    if B:
        flat[:B] = mask
    return np.ascontiguousarray(flat.reshape(G, WIDTH, P).transpose(0, 2, 1))


def to_aosoa(args, B, poison=POISON):
    """Dense 17-argument bundle -> AoSoA bundle for primary_aosoa.

    Padding lanes of sh/vs/vb carry ``poison`` and padding lanes of
    sun/shade carry True: any read of a padding lane that could influence
    a stored result fails the parity assertions.
    """
    out = dict(args)
    out['sh'] = pack_payload(args['sh'], B, poison)
    out['vs'] = pack_payload(args['vs'], B, poison)
    out['vb'] = pack_payload(args['vb'], B, poison)
    out['sun'] = pack_mask(args['sun'], B)
    out['shade'] = pack_mask(args['shade'], B)
    return out


def run_native(args_aosoa, B, **over):
    call = dict(args_aosoa)
    call.update(over)
    return lw_native_aosoa.primary_aosoa(
        call['sh'], call['vs'], call['vb'], call['sun'], call['shade'],
        call['solid'], call['sine'], call['cosine'], call['directions'],
        call['gate'], call['solar_gate'], call['sky_down'], call['sky_side'],
        call['surface_sun'], call['surface_sh'], call['lup'],
        call['reflection_factor'], B)
