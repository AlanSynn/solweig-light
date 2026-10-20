"""Lossless codec-v1 encoder for exact native contiguous float32 ndarrays.

Only immutable encoded output storage is allocated. The input is read through
an integer view; no floating arithmetic can quiet NaNs or change signed zero.
Unsupported layouts, endian variants and subclasses retain the generic codec.
"""
import numpy as np
from numba import njit
from ..radiation._jit_cache import bind_cache_identity


@njit(cache=True, fastmath=False)
@bind_cache_identity
def _encode_bits(bits):
    mode = 0
    for word in bits:
        if word == 0x40000000:
            mode = 1
        elif word != 0 and word != 0x3F800000:
            mode = 2
            break
    total = len(bits)
    width = 1 if mode == 0 else 2
    size = total * 4 if mode == 2 else (total * width + 7) // 8
    payload = np.empty(size, dtype=np.uint8)
    if mode == 2:
        for index in range(total):
            word = bits[index]
            for offset in range(4):
                payload[index * 4 + offset] = np.uint8(word >> (offset * 8))
    else:
        per_byte = 8 // width
        for byte in range(size):
            packed = 0
            for offset in range(per_byte):
                index = byte * per_byte + offset
                if index < total:
                    packed |= (bits[index] >> 29) << (offset * width)
            payload[byte] = np.uint8(packed)
    return mode, payload


def try_encode_native_f32(plane):
    """Return ``(mode, bytes)`` or None without coercing unsupported inputs."""
    if (type(plane) is not np.ndarray or plane.ndim != 2
            or plane.dtype != np.dtype(np.float32) or not plane.dtype.isnative
            or not plane.flags.c_contiguous):
        return None
    bits = plane.reshape(-1).view(np.uint32)
    bits.flags.writeable = False
    mode, payload = _encode_bits(bits)
    return ('binary', 'ternary', 'raw')[mode], payload.tobytes()
