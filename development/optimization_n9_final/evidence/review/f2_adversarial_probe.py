# F2 reviewer probe: NEW specialized _produce_patchmajor vs the BASE
# (7abe526a) generic kernel compiled from the base source blob, on
# adversarial cases both must agree on bit-for-bit, including the
# observable error surface for degenerate modes (0, 3) and reserved codes.
# Read-only wrt src/ and tests/; run with the worktree's .venv python.
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

REPO = Path('/Users/alansynn/Workspace/solweig-v8-native')
sys.path.insert(0, str(REPO / 'src'))
sys.path.insert(0, str(REPO / 'tests' / 'optimization_v8' / 'n9_producer'))

from n9_producer_ref import (N9_RAW_BITS, n9_aosoa_rows, n9_build_channel,
                             n9_first_reserved, n9_legacy_expr_decode,
                             n9_ref_decode, n9_written_prefix, POISON)
from solweig_light._native_dispatch import direct_aosoa as da
from solweig_light.geometry.visibility import PackedVisibility, _EncodedPatch

# --- compile the BASE kernel from the base blob (independent module) ------
base_src = subprocess.run(
    ['git', '-C', str(REPO), 'show',
     '7abe526a:src/solweig_light/_native_dispatch/direct_aosoa.py'],
    capture_output=True, text=True, check=True).stdout
lines = base_src.splitlines(True)
start = next(i for i, ln in enumerate(lines)
             if ln.startswith('def _produce_patchmajor'))
end = next(i for i, ln in enumerate(lines) if ln.startswith('def _leased'))
module_text = (
    'import numpy as np\nfrom numba import njit\n\n\n'
    '@njit(cache=False, fastmath=False)\n'
    + ''.join(lines[start:end]))
tmp = tempfile.mkdtemp(prefix='f2_probe_base_')
base_mod_path = Path(tmp) / 'f2_probe_base_kernel.py'
base_mod_path.write_text(module_text)
spec = __import__('importlib.util', fromlist=['util']).spec_from_file_location(
    'f2_probe_base_kernel', str(base_mod_path))
base_mod = __import__('importlib.util', fromlist=['module_from_spec']) \
    .module_from_spec(spec)
sys.modules['f2_probe_base_kernel'] = base_mod
spec.loader.exec_module(base_mod)
old_kernel = base_mod._produce_patchmajor

FAILS = []


def check(name, ok, detail=''):
    print(('PASS ' if ok else 'FAIL ') + name + ((' -- ' + detail) if detail else ''))
    if not ok:
        FAILS.append(name)


def run_new(channel, start, stop, patches, width):
    out = np.full((-(-(stop - start) // width), patches, width), POISON,
                  np.uint32)
    payloads, modes = da._descriptor(channel)
    da._produce_patchmajor(payloads, modes, start, stop, patches, out, width)
    return out


def run_old(channel, start, stop, patches, width):
    out = np.full((-(-(stop - start) // width), patches, width), POISON,
                  np.uint32)
    payloads, modes = da._descriptor(channel)
    old_kernel(payloads, modes, start, stop, patches, out, width)
    return out


def poisoned_run(kernel_run, channel, start, stop, patches, width):
    """Run under a poison-filled out and return (exc_type_name, out)."""
    raise NotImplementedError


def run_both_poisoned(kernel_fn, channel, start, stop, patches, width):
    out = np.full((-(-(stop - start) // width), patches, width), POISON,
                  np.uint32)
    payloads, modes = da._descriptor(channel)
    try:
        kernel_fn(payloads, modes, start, stop, patches, out, width)
        return None, out
    except BaseException as exc:
        return type(exc).__name__ + ':' + str(exc.args), out


# 1. Bitwise agreement old-vs-new (+ vs the two python oracles) on a wide
#    adversarial grid: odd starts near byte boundaries, widths 4/8, all
#    mode mixes, sizes incl. 0/1/7/8/9/127/128, adversarial raw payloads.
SIZES = [0, 1, 7, 8, 9, 127, 128, 131]
STARTS = [0, 3, 5, 7, 13]
MIXES = [('binary', 'ternary', 'raw'), ('binary',), ('ternary',), ('raw',),
         ('raw', 'binary', 'ternary', 'raw')]
count_cases = 0
for width in (8, 4):
    for start in STARTS:
        for count in SIZES:
            for mix in MIXES:
                patches = len(mix)
                ch = n9_build_channel(start + count, mix,
                                      seed=count * 91 + start * 7 + patches)
                new = run_new(ch, start, start + count, patches, width)
                old = run_old(ch, start, start + count, patches, width)
                if count:
                    ref = n9_ref_decode(ch, start, start + count)
                    leg = n9_legacy_expr_decode(ch, start, start + count)
                    assert np.array_equal(n9_aosoa_rows(new)[:count], ref)
                    assert np.array_equal(n9_aosoa_rows(new)[:count], leg)
                if not np.array_equal(new, old):
                    check(f'grid w={width} s={start} n={count} {mix}',
                          False, 'old/new outputs differ')
                    break
                count_cases += 1
check('bitwise grid old==new==ref==legacy', count_cases == 2 * 5 * 8 * 5,
      f'{count_cases} cases')

# 2. Adversarial raw bits (signed zero, NaN payloads, +/-Inf, subnormals)
#    through BOTH kernels, byte-exact.
pixels = len(N9_RAW_BITS)
payload = np.array(N9_RAW_BITS, dtype='<u4').tobytes()
ch = PackedVisibility((1, pixels, 1), (_EncodedPatch('raw', payload),))
for width in (8, 4):
    new = run_new(ch, 0, pixels, 1, width)
    old = run_old(ch, 0, pixels, 1, width)
    ref = n9_ref_decode(ch, 0, pixels)
    check(f'adversarial raw bits w={width}',
          np.array_equal(n9_aosoa_rows(new)[:pixels], ref)
          and np.array_equal(new, old))


# 3. Reserved code 3 at EVERY (patch, pixel) of a mixed channel, odd start,
#    width 4 and 8: identical exception identity AND identical poison
#    write-prefix between old and new kernels.
def ternary_reserved(pixels, position):
    codes = np.zeros(pixels, np.uint8)
    codes[position] = 3
    padded = np.zeros((pixels + 3) // 4 * 4, np.uint8)
    padded[:pixels] = codes
    payload = (padded[0::4] | (padded[1::4] << 2) | (padded[2::4] << 4)
               | (padded[3::4] << 6)).tobytes()
    return _EncodedPatch('ternary', payload)


mismatch = 0
for start in (0, 5, 7):
    for width in (8, 4):
        pixels = 29
        for patch_index in range(3):
            for position in range(pixels):
                good = n9_build_channel(start + pixels,
                                        ('binary', 'ternary', 'raw'), seed=9)
                patches = list(good._patches)
                # Code 3 at ABSOLUTE pixel ``position`` (payload indexed by
                # absolute x); positions < start are outside the decode
                # range and must raise in NEITHER kernel.
                patches[patch_index] = ternary_reserved(start + pixels,
                                                        position)
                ch = PackedVisibility((1, start + pixels, 3), tuple(patches))
                first = n9_first_reserved(ch, start, start + pixels)
                exc_n, out_n = run_both_poisoned(da._produce_patchmajor, ch,
                                                 start, start + pixels, 3,
                                                 width)
                exc_o, out_o = run_both_poisoned(old_kernel, ch,
                                                 start, start + pixels, 3,
                                                 width)
                pre_n = n9_written_prefix(out_n, POISON, 3, pixels, width,
                                          start=0)
                pre_o = n9_written_prefix(out_o, POISON, 3, pixels, width,
                                          start=0)
                if (first is not None) != (exc_n is not None):
                    mismatch += 1   # reference disagrees on error presence
                if not (exc_n == exc_o and pre_n == pre_o
                        and (exc_n is None
                             or 'Reserved visibility code' in exc_n)):
                    mismatch += 1
                    if mismatch < 4:
                        print('  mismatch', start, width, patch_index,
                              position, exc_n, exc_o, pre_n, pre_o)
check('reserved code 3: old/new identical error identity + write prefix '
      '(all injection positions)', mismatch == 0, f'{mismatch} mismatches')

# 4. Degenerate modes 0 and 3 (fallback arm): identical behavior old vs new.
#    Mode 0 -> 8//0; mode 3 -> mask 7 with code 3 possible. Build direct
#    descriptor pairs (modes are just bytes to the kernel).


def raw_desc(ch):
    return da._descriptor(ch)


def with_modes(ch, modes_arr):
    payloads, _ = da._descriptor(ch)
    return payloads, np.array(modes_arr, np.uint8)


ch = n9_build_channel(64, ('binary', 'ternary', 'raw'), seed=3)
for modes_arr in ([0, 0, 0], [3, 3, 3], [5, 1, 0], [2, 0, 4]):
    payloads, modes = with_modes(ch, modes_arr)
    out_n = np.full((8, 3, 8), POISON, np.uint32)
    out_o = np.full((8, 3, 8), POISON, np.uint32)
    try:
        da._produce_patchmajor(payloads, modes, 0, 64, 3, out_n, 8)
        exc_n = None
    except BaseException as exc:
        exc_n = type(exc).__name__ + ':' + str(exc.args)
    try:
        old_kernel(payloads, modes, 0, 64, 3, out_o, 8)
        exc_o = None
    except BaseException as exc:
        exc_o = type(exc).__name__ + ':' + str(exc.args)
    check(f'degenerate modes {list(modes_arr)}: old/new identical surface',
          exc_n == exc_o and np.array_equal(out_n, out_o),
          f'exc={exc_n}')

# 5. A-plus comparator vs _decode_at (not dispatched; verify its claim).
from solweig_light._native_dispatch.aplus_decode import _decode_at_plus
from solweig_light.geometry.visibility_compiled import _decode_at

aplus_bad = 0
for mix in MIXES:
    ch = n9_build_channel(137, mix, seed=17)
    payloads, modes = da._descriptor(ch)
    flat = np.concatenate([np.asarray(p, np.uint8).reshape(-1)
                           for p in payloads]) if payloads else \
        np.zeros(0, np.uint8)
    offs, run = [], 0
    for p in payloads:
        offs.append(run)
        run += np.asarray(p, np.uint8).size
    offsets = np.array(offs, np.int64)
    for patch in range(len(payloads)):
        for x in range(137):
            a = np.array(_decode_at_plus(flat, offsets, modes, patch, x),
                         np.float32).view(np.uint32)
            b = np.array(_decode_at(flat, offsets, modes, patch, x),
                         np.float32).view(np.uint32)
            if a != b:
                aplus_bad += 1
check('aplus _decode_at_plus == _decode_at on adversarial mixes',
      aplus_bad == 0, f'{aplus_bad} mismatches')

print()
print('RESULT:', 'ALL PASS' if not FAILS else f'{len(FAILS)} FAILURES: {FAILS}')
sys.exit(1 if FAILS else 0)
