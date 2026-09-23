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
"""N9 F1D/F1M producer-test helpers.

Self-contained (uniquely named module, no conftest coupling): an INDEPENDENT
pure-python reference decoder (byte-wise literal arithmetic, no numba), the
accepted producer's generic expression as a second python oracle, a channel
builder, and poison-scan utilities that recover the exact patch-major write
prefix from a poisoned ``out`` buffer after a reserved-code IndexError.

All kernels used by these tests are serial (no prange, no set_num_threads),
so the v5 thread-cap hazard does not apply.
"""
import numpy as np

from solweig_light.geometry.visibility import PackedVisibility, _EncodedPatch

POISON = np.uint32(0xDEADBEEF)
MODE_CODES = {'binary': 1, 'ternary': 2, 'raw': 4}

# Adversarial float32 bit patterns for raw payloads: signed zeros,
# subnormals, +/-Inf, NaN payloads (negative too), qNaN variants, values
# straddling the codebook. 0xDEADBEEF is deliberately absent (poison).
N9_RAW_BITS = [0x00000000, 0x80000000, 0x3F800000, 0x40000000, 0xBF800000,
               0x40490FDB, 0x80000001, 0x007FFFFF, 0x00000001, 0x7F800000,
               0xFF800000, 0x7FC00000, 0xFFC00001, 0x3F7FFFFF, 0x3F800001,
               0x4B7FFFFF, 0x7F7FFFFF, 0xFF7FFFFF, 0x807FFFFF]


def n9_build_channel(pixels, modes, *, seed=0, raw_bits=None):
    """PackedVisibility whose patches use the requested mode sequence."""
    rng = np.random.default_rng(seed)
    shape = (1, pixels, len(modes)) if pixels else (0, 0, len(modes))
    patches = []
    for mode in modes:
        if pixels == 0:
            payload = b''
        elif mode == 'raw':
            bits = rng.choice(np.array(N9_RAW_BITS if raw_bits is None else raw_bits,
                                       dtype=np.uint32), size=pixels)
            payload = bits.astype('<u4').tobytes()
        elif mode == 'ternary':
            codes = rng.integers(0, 3, size=pixels).astype(np.uint8)
            padded = np.zeros((pixels + 3) // 4 * 4, dtype=np.uint8)
            padded[:pixels] = codes
            payload = (padded[0::4] | (padded[1::4] << 2) | (padded[2::4] << 4)
                       | (padded[3::4] << 6)).tobytes()
        else:
            codes = rng.integers(0, 2, size=pixels).astype(np.uint8)
            payload = np.packbits(codes, bitorder='little').tobytes()
        patches.append(_EncodedPatch(mode, payload))
    return PackedVisibility(shape, tuple(patches))


def _codebook(code):
    return 0 if code == 0 else 0x3f800000 if code == 1 else 0x40000000


def n9_ref_decode_pixel(payload, mode, x):
    """Independent byte-wise decode of one pixel (literal shifts; raises on
    reserved code 3 exactly where the producer would first observe it).
    Bytes are widened with int() so python-arithmetic shifts never wrap."""
    if mode == 4:
        return (int(payload[4*x]) | (int(payload[4*x+1]) << 8)
                | (int(payload[4*x+2]) << 16) | (int(payload[4*x+3]) << 24))
    if mode == 1:
        code = (int(payload[x >> 3]) >> (x & 7)) & 1
        if code == 3:
            raise IndexError('Reserved visibility code')
        return _codebook(code)
    if mode == 2:
        code = (int(payload[x >> 2]) >> ((x & 3) << 1)) & 3
        if code == 3:
            raise IndexError('Reserved visibility code')
        return _codebook(code)
    code = (int(payload[x // (8 // mode)]) >> ((x % (8 // mode))*mode)) & ((1 << mode)-1)
    if code == 3:
        raise IndexError('Reserved visibility code')
    return _codebook(code)


def n9_streams(channel):
    """(readonly per-patch uint8 views, modes) via the channel descriptor --
    works for built AND mapped owners (mapped patches expose no payload)."""
    from solweig_light.geometry.visibility_compiled import _descriptor
    return _descriptor(channel)


def n9_ref_decode(channel, start, stop):
    """Independent reference: [stop-start, P] uint32, patch-major ascending.

    Column per patch, ascending pixels; reserved codes raise at the same
    first (patch, pixel) the producer reports.
    """
    payloads, modes = n9_streams(channel)
    rows = stop - start
    if rows <= 0:
        return np.zeros((0, len(payloads)), dtype=np.uint32)
    cols = []
    for patch in range(len(payloads)):
        mode = int(modes[patch])
        cols.append([n9_ref_decode_pixel(payloads[patch], mode, x)
                     for x in range(start, stop)])
    return np.array(cols, dtype=np.uint32).T


def n9_legacy_expr_decode(channel, start, stop):
    """The ACCEPTED producer's generic expression, as a python oracle.

    Same loop order and the original runtime-divisor expression for every
    packed mode, so literal-vs-generic equivalence is checked against the
    exact prior arithmetic, not a paraphrase.
    """
    payloads, modes = n9_streams(channel)
    rows = stop - start
    if rows <= 0:
        return np.zeros((0, len(payloads)), dtype=np.uint32)
    cols = []
    for patch in range(len(payloads)):
        mode = int(modes[patch])
        data = payloads[patch]
        col = []
        for x in range(start, stop):
            if mode == 4:
                offset = x * 4
                col.append(n9_ref_decode_pixel(data, 4, x))
                continue
            code = (int(data[x // (8 // mode)]) >> ((x % (8 // mode))*mode)) & ((1 << mode)-1)
            if code == 3:
                raise IndexError('Reserved visibility code')
            col.append(_codebook(code))
        cols.append(col)
    return np.array(cols, dtype=np.uint32).T


def n9_first_reserved(channel, start, stop):
    """First (patch, pixel) carrying reserved code 3 in patch-major order."""
    payloads, modes = n9_streams(channel)
    for patch in range(len(payloads)):
        mode = int(modes[patch])
        for x in range(start, stop):
            if mode == 4:
                continue
            try:
                n9_ref_decode_pixel(payloads[patch], mode, x)
            except IndexError:
                return patch, x
    return None


def n9_aosoa_rows(bits):
    """[G,P,W] -> logical [G*W, P] rows (row = gang*width + lane)."""
    gangs, patches, width = bits.shape
    return bits.transpose(0, 2, 1).reshape(gangs * width, patches)


def n9_written_prefix(out, poison, patches, count, width, start=0):
    """Number of (patch, pixel) cells written before an in-kernel raise,
    read off a poison-prefilled ``out`` in the patchmajor write order."""
    written = 0
    for patch in range(patches):
        for gang in range(-(-count // width)):
            for lane in range(width):
                pixel = start + gang * width + lane
                if pixel >= start + count:
                    break
                if out[gang, patch, lane] == poison:
                    return written
                written += 1
    return written


def n9_vault(patches=153):
    """Deterministic Tregenza-like ordered patch table (<=609 patches)."""
    bands = 15
    per_band = max(1, -(-patches // bands))
    altitudes = np.repeat(np.linspace(6.0, 84.0, bands).astype(np.float32), per_band)
    azimuths = np.tile(np.linspace(0.0, 350.0, per_band).astype(np.float32), bands)
    return np.column_stack((altitudes, azimuths))[:patches].astype(np.float32)


def n9_tensor32(value):
    return np.array(np.float32(value))


def n9_masks_rows(mask):
    gangs, patches, width = mask.shape
    return mask.transpose(0, 2, 1).reshape(gangs * width, patches)
