#SOLWEIG-GPU: GPU-accelerated SOLWEIG model for urban thermal comfort simulation
#Copyright (C) 2022–2025 Harsh Kamath and Naveen Sudharsan

#This program is free software: you can redistribute it and/or modify
#it under the terms of the License above, and the GNU General Public
#License as published by the Free Software Foundation.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
"""N9-F1S stream-test helpers (uniquely named ON PURPOSE).

Test modules import shared builders from HERE, never from ``conftest``
(bare ``conftest`` is shadowed across the optimization_v8 tree in
combined sessions). Everything heavy is imported READ-ONLY: the frozen
reference suite and the N8-14 region-case builders.
"""
import sys
from pathlib import Path

import numba

_HERE = Path(__file__).resolve().parent
for _entry in (_HERE.parents[0] / 'reference',
               _HERE.parents[0] / 'region',
               _HERE.parents[0] / 'policy',
               _HERE):
    if str(_entry) not in sys.path:
        sys.path.insert(0, str(_entry))

#: Pinned thread budget for the B kernel (same discipline as the region
#: suite): bit-deterministic at any count, fixed so runs compare. Region
#: pools in these tests never exceed this. Never export NUMBA_NUM_THREADS.
LW_TEST_THREADS = max(1, min(4, numba.config.NUMBA_NUM_THREADS))
numba.set_num_threads(LW_TEST_THREADS)

import numpy as np  # noqa: E402

from solweig_light.geometry.visibility import (  # noqa: E402
    PackedVisibility, _EncodedPatch)
from solweig_light.radiation.patch_radiation import (  # noqa: E402
    _class_coefficients, patch_geometry)

#: The frozen 17-argument signature order.
NAMES = ('sh', 'vs', 'vb', 'sun', 'shade', 'solid', 'sine', 'cosine',
         'directions', 'gate', 'solar_gate', 'sky_down', 'sky_side',
         'surface_sun', 'surface_sh', 'lup', 'reflection_factor')

POISON_U32 = np.uint32(0xDEADBEEF)


def build_channel(pixels, modes, *, seed=0, codes=None):
    """PackedVisibility whose patches use the requested mode sequence.

    ``codes`` optionally supplies the exact per-pixel code array for
    ternary patches (reserved-code injection uses this).
    """
    rng = np.random.default_rng(seed)
    patches = []
    for index, mode in enumerate(modes):
        if pixels == 0:
            payload = b''
        elif mode == 'raw':
            bits = rng.integers(0, 2 ** 32, pixels,
                                dtype=np.uint64).astype(np.uint32)
            bits[0] = 0x40600000  # never a codebook pattern: raw mode
            payload = bits.astype('<u4').tobytes()
        elif mode == 'ternary':
            values = (codes if codes is not None else
                      rng.integers(0, 3, size=pixels).astype(np.uint8))
            padded = np.zeros((pixels + 3) // 4 * 4, dtype=np.uint8)
            padded[:pixels] = values
            payload = (padded[0::4] | (padded[1::4] << 2)
                       | (padded[2::4] << 4) | (padded[3::4] << 6)).tobytes()
        else:
            values = rng.integers(0, 2, size=pixels).astype(np.uint8)
            payload = np.packbits(values, bitorder='little').tobytes()
        patches.append(_EncodedPatch(mode, payload))
    return PackedVisibility((1, pixels, len(modes)), tuple(patches))


def payload_digest(channel):
    import hashlib
    return hashlib.sha256(b''.join(patch.payload
                                   for patch in channel._patches)).hexdigest()


def make_case(rows, patches, *, seed=0, modes_cycle=('binary', 'ternary',
                                                     'raw'), gate='sun'):
    """A full routed-call argument bundle over packed channels.

    ``gate``: 'sun' (a real mixed gate), 'none' (all-inactive), or
    'all' (every patch active) -- the mask-clearing alternations.
    """
    modes = [modes_cycle[i % len(modes_cycle)] for i in range(patches)]
    channels = tuple(build_channel(rows, modes, seed=seed + i)
                     for i in range(3))
    rng = np.random.default_rng(seed + 100)
    alt = (rng.random(patches) * 60).astype(np.float32)
    azi = (rng.random(patches) * 360).astype(np.float32)
    geometry = patch_geometry(np.column_stack((alt, azi)))
    solar_altitude = np.array(35.0, dtype=np.float32)
    solar_azimuth = np.array(180.0, dtype=np.float32)
    difference = np.abs(np.asarray(solar_azimuth) - azi)
    if gate == 'sun':
        solar_gate = ((difference > 90) & (difference < 270)
                      & (solar_altitude > 0))
    elif gate == 'all':
        solar_gate = np.ones(patches, dtype=bool)
    else:
        solar_gate = np.zeros(patches, dtype=bool)
    asvf = np.full(rows, .6, dtype=np.float32)
    prepared = _class_coefficients(solar_altitude, solar_azimuth, geometry,
                                   asvf, solar_gate)
    values = dict(
        shmat=channels[0], vegshmat=channels[1], vbshvegshmat=channels[2],
        solar_altitude=solar_altitude, solar_azimuth=solar_azimuth,
        asvf=asvf, steradian=rng.random(patches).astype(np.float32),
        Lsky_down=rng.random((patches, 3)).astype(np.float32),
        Lsky_side=rng.random((patches, 3)).astype(np.float32),
        Lup=(rng.random(rows * 3).reshape(rows, 3).astype(np.float32) * 400))
    return dict(values=values, geometry=geometry, solar_gate=solar_gate,
                prepared=prepared, factor=np.float32(0.1),
                sun_surface=np.float32(1.5), shade_surface=np.float32(1.25))


def whole_scene_args(case, rows, width=8):
    """The OLD whole-scene prologue: full [G,P,W] tensors + masks."""
    from solweig_light._native_dispatch import direct_aosoa as da
    values = case['values']
    patches = case['geometry'].altitude.size
    aosoa = da.produce_blocks_aosoa(
        values['shmat'], values['vegshmat'], values['vbshvegshmat'],
        0, rows, patches, width=width)
    sun_a, shade_a = da.classify_block_aosoa(
        values['solar_altitude'], values['solar_azimuth'], case['geometry'],
        values['asvf'], 0, rows, active=case['solar_gate'],
        prepared=case['prepared'], width=width)
    args = dict(zip(NAMES, (*aosoa, sun_a, shade_a)))
    args.update(solid=values['steradian'], sine=case['geometry'].sine,
                cosine=case['geometry'].cosine,
                directions=case['geometry'].longwave_cardinal_cosine,
                gate=case['geometry'].reflection_cardinal,
                solar_gate=case['solar_gate'],
                sky_down=values['Lsky_down'][:, 2],
                sky_side=values['Lsky_side'][:, 2],
                surface_sun=case['sun_surface'],
                surface_sh=case['shade_surface'],
                lup=values['Lup'].reshape(-1),
                reflection_factor=case['factor'])
    return args


def stream_plan(case, rows, row='B', block_pixels=128, width=8):
    from solweig_light._native_dispatch import lw_stream
    return lw_stream.plan_invocation(
        row, case['values'], case['geometry'], case['solar_gate'],
        case['prepared'], rows, block_pixels, case['factor'],
        case['sun_surface'], case['shade_surface'], width=width)


def outputs_bitwise(a, b):
    import numpy as np
    return all(np.array_equal(x.view(np.uint32), y.view(np.uint32))
               for x, y in zip(a, b))
