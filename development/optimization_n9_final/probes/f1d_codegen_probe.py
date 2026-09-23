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
"""F1D codegen probe (TARGET HOST): division/remainder and vectorization
census for the mode-specialized producer kernels.

Method: force real compilation via a live produce call, then
  1. dump inspect_llvm / inspect_asm for each specialized kernel signature;
  2. count integer division/remainder instructions (LLVM: udiv/sdiv/urem/srem;
     AArch64 asm: udiv/sdiv) and NEON vector-register usage;
  3. compile, in this same script, (a) a verbatim replica of the ORIGINAL
     generic kernel body (the pre-F1D arithmetic) and (b) micro-kernels that
     are EXACTLY the new literal binary/ternary arm bodies, so the hot-arm
     division removal is attributable arm-by-arm on this host, not inferred
  4. record where any surviving division lives (expected: only in the
     mode-1/2/4 fallback arm of the specialized kernels, reachable for no
     canonical mode; and in the original-body replica).

Run from the worktree root with NUMBA_NUM_THREADS/NUMBA_CACHE_DIR exported.
"""
import platform
import re
import sys

import numpy as np
from numba import njit
from numba.typed import List
from numba import types

DIV_OPS = ('udiv ', 'sdiv ', 'urem ', 'srem ')


def census(name, kernel, sig):
    llvm = kernel.inspect_llvm(sig)
    asm = kernel.inspect_asm(sig)
    if len(llvm.splitlines()) < 20:
        raise RuntimeError(
            f'{name}: inspect_llvm returned a stub ({len(llvm.splitlines())} lines) '
            '-- kernel was loaded from the numba on-disk cache. Re-run with a '
            'FRESH NUMBA_CACHE_DIR; cached code inspection is disabled.')
    llvm_div = sum(llvm.count(op) for op in DIV_OPS)
    asm_div = sum(asm.count(op) for op in ('udiv\t', 'sdiv\t', 'udiv ', 'sdiv '))
    neon = sum(asm.count(tok) for tok in ('.16b', '.8b', '.4s', '.2d', '.4h'))
    shifts = {op: llvm.count(op) for op in ('lshr ', 'ashr ', 'shl ')}
    print(f'--- {name} ---')
    print(f'LLVM div/rem instruction occurrences : {llvm_div}')
    print(f'AArch64 udiv/sdiv instruction count  : {asm_div}')
    print(f'LLVM shift counts (lshr/ashr/shl)    : {shifts}')
    print(f'NEON vector-register token count     : {neon}')
    # Attribution: an sdiv whose DIVISOR operand is the zext/sext of a udiv
    # RESULT is the generic expression's `pixel // (8 // mode)` (fallback-arm
    # fingerprint); any other sdiv is the `rows // width` gang-count prologue.
    results = set(re.findall(r'(%\S+) = udiv[^\n]*', llvm))
    for i, line in enumerate(llvm.splitlines()):
        if any(op in line for op in DIV_OPS):
            m = re.search(r'= (?:sdiv|udiv|urem|srem) i\d+ ([^,]+), ([^\n]+)$', line.strip())
            kind = 'other'
            if m:
                divisor = m.group(2).strip().rstrip(',')
                base = divisor.split('.')[0]
                if base in results or divisor in results:
                    kind = 'generic-fallback expression (pixel // (8 // mode))'
                elif 'arg.width' in divisor:
                    kind = 'gang-count prologue (rows // width)'
            print(f'  llvm[{i}] [{kind}]: {line.strip()[:150]}')
    return llvm, asm, llvm_div, asm_div, neon


@njit(cache=False, fastmath=False)
def _n9_original_generic_body(payloads, modes, start, stop, patches, out, width):
    """VERBATIM pre-F1D _produce_patchmajor body (generic packed expression)."""
    rows = stop - start
    full = rows // width
    tail = rows - full * width
    for patch in range(patches):
        data = payloads[patch]
        mode = modes[patch]
        for gang in range(full):
            pixel = start + gang * width
            for lane in range(width):
                if mode == 4:
                    offset = pixel * 4
                    value = (np.uint32(data[offset]) | (np.uint32(data[offset+1]) << 8)
                             | (np.uint32(data[offset+2]) << 16) | (np.uint32(data[offset+3]) << 24))
                else:
                    code = (data[pixel // (8 // mode)] >> ((pixel % (8 // mode))*mode)) & ((1 << mode)-1)
                    if code == 3:
                        raise IndexError('Reserved visibility code')
                    value = np.uint32(0) if code == 0 else np.uint32(0x3f800000) if code == 1 else np.uint32(0x40000000)
                out[gang, patch, lane] = value
                pixel += 1
        if tail:
            pixel = start + full * width
            for lane in range(tail):
                if mode == 4:
                    offset = pixel * 4
                    value = (np.uint32(data[offset]) | (np.uint32(data[offset+1]) << 8)
                             | (np.uint32(data[offset+2]) << 16) | (np.uint32(data[offset+3]) << 24))
                else:
                    code = (data[pixel // (8 // mode)] >> ((pixel % (8 // mode))*mode)) & ((1 << mode)-1)
                    if code == 3:
                        raise IndexError('Reserved visibility code')
                    value = np.uint32(0) if code == 0 else np.uint32(0x3f800000) if code == 1 else np.uint32(0x40000000)
                out[full, patch, lane] = value
                pixel += 1


@njit(cache=False, fastmath=False, inline='always')
def _n9_arm_binary(data, start, stop, out, patch, width):
    """EXACT new literal binary arm bodies (full gangs + tail)."""
    rows = stop - start
    full = rows // width
    tail = rows - full * width
    for gang in range(full):
        pixel = start + gang * width
        for lane in range(width):
            code = (data[pixel >> 3] >> (pixel & 7)) & 1
            if code == 3:
                raise IndexError('Reserved visibility code')
            value = np.uint32(0) if code == 0 else np.uint32(0x3f800000) if code == 1 else np.uint32(0x40000000)
            out[gang, patch, lane] = value
            pixel += 1
    if tail:
        pixel = start + full * width
        for lane in range(tail):
            code = (data[pixel >> 3] >> (pixel & 7)) & 1
            if code == 3:
                raise IndexError('Reserved visibility code')
            value = np.uint32(0) if code == 0 else np.uint32(0x3f800000) if code == 1 else np.uint32(0x40000000)
            out[full, patch, lane] = value
            pixel += 1


@njit(cache=False, fastmath=False, inline='always')
def _n9_arm_ternary(data, start, stop, out, patch, width):
    """EXACT new literal ternary arm bodies (full gangs + tail)."""
    rows = stop - start
    full = rows // width
    tail = rows - full * width
    for gang in range(full):
        pixel = start + gang * width
        for lane in range(width):
            code = (data[pixel >> 2] >> ((pixel & 3) << 1)) & 3
            if code == 3:
                raise IndexError('Reserved visibility code')
            value = np.uint32(0) if code == 0 else np.uint32(0x3f800000) if code == 1 else np.uint32(0x40000000)
            out[gang, patch, lane] = value
            pixel += 1
    if tail:
        pixel = start + full * width
        for lane in range(tail):
            code = (data[pixel >> 2] >> ((pixel & 3) << 1)) & 3
            if code == 3:
                raise IndexError('Reserved visibility code')
            value = np.uint32(0) if code == 0 else np.uint32(0x3f800000) if code == 1 else np.uint32(0x40000000)
            out[full, patch, lane] = value
            pixel += 1


@njit(cache=False, fastmath=False)
def _n9_arm_binary_standalone(data, start, stop, out, patch, width):
    _n9_arm_binary(data, start, stop, out, patch, width)


@njit(cache=False, fastmath=False)
def _n9_arm_ternary_standalone(data, start, stop, out, patch, width):
    _n9_arm_ternary(data, start, stop, out, patch, width)


def main():
    import numba
    print(f'# F1D codegen census — target host')
    print(f'# platform      : {platform.platform()}')
    print(f'# machine       : {platform.machine()}  ({platform.processor()})')
    print(f'# python        : {sys.version.split()[0]}')
    print(f'# numba         : {numba.__version__}')
    print(f'# numpy         : {np.__version__}')
    print(f'# threading cfg : NUMBA_NUM_THREADS={__import__("os").environ.get("NUMBA_NUM_THREADS")!r}')

    from solweig_light._native_dispatch import direct_aosoa as da
    from solweig_light.geometry.visibility import PackedVisibility, _EncodedPatch
    from solweig_light.geometry.visibility_compiled import _descriptor

    rng = np.random.default_rng(7)
    pixels, patches = 128, 3
    patch_defs = []
    codes_b = rng.integers(0, 2, size=pixels).astype(np.uint8)
    patch_defs.append(('binary', np.packbits(codes_b, bitorder='little').tobytes()))
    codes_t = rng.integers(0, 3, size=pixels).astype(np.uint8)
    padded = np.zeros((pixels + 3) // 4 * 4, dtype=np.uint8)
    padded[:pixels] = codes_t
    patch_defs.append(('ternary', (padded[0::4] | (padded[1::4] << 2)
                                   | (padded[2::4] << 4) | (padded[3::4] << 6)).tobytes()))
    patch_defs.append(('raw', rng.integers(0, 2 ** 32, size=pixels, dtype=np.uint32).astype('<u4').tobytes()))
    channel = PackedVisibility((1, pixels, patches), tuple(_EncodedPatch(m, p) for m, p in patch_defs))
    payloads, modes = _descriptor(channel)

    for order in ('patchmajor', 'blocked'):
        da.produce_block_aosoa(channel, 0, pixels, patches, order=order)
    _n9_original_generic_body(payloads, modes, 0, pixels, patches,
                              np.empty((16, patches, 8), np.uint32), 8)
    _n9_arm_binary_standalone(payloads[0], 0, pixels, np.empty((16, 1, 8), np.uint32), 0, 8)
    _n9_arm_ternary_standalone(payloads[1], 0, pixels, np.empty((16, 1, 8), np.uint32), 0, 8)

    list_sig = types.ListType(types.Array(types.uint8, 1, 'C', readonly=True))
    summary = {}

    summary['original_generic_body (pre-F1D replica)'] = census(
        'original_generic_body (pre-F1D replica)', _n9_original_generic_body,
        (list_sig, types.uint8[::1], types.int64, types.int64, types.int64,
         types.Array(types.uint32, 3, 'C'), types.int64))
    for name, kernel in (('specialized _produce_patchmajor', da._produce_patchmajor),
                         ('specialized _produce_blocked', da._produce_blocked)):
        for sig in kernel.signatures:
            summary[f'{name} {sig}'] = census(f'{name} sig={sig}', kernel, sig)
    summary['specialized _preflight_packed'] = census(
        'specialized _preflight_packed', da._preflight_packed, da._preflight_packed.signatures[0])
    for name, kernel in (('_n9_arm_binary_standalone (literal arm)', _n9_arm_binary_standalone),
                         ('_n9_arm_ternary_standalone (literal arm)', _n9_arm_ternary_standalone)):
        summary[name] = census(name, kernel, kernel.signatures[0])

    print('\n=== VERDICT SUMMARY ===')
    for name, (_, _, llvm_div, asm_div, neon) in summary.items():
        print(f'{name}: llvm_div={llvm_div} asm_div={asm_div} neon_tokens={neon}')


if __name__ == '__main__':
    main()
