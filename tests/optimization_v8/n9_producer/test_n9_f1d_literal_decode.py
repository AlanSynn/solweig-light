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
"""N9 F1D literal-mode producer tests.

The mode-specialized kernels must stay bit-exact with (a) an independent
pure-python byte-wise decoder and (b) the ACCEPTED producer's generic
runtime-divisor expression, over all modes, both widths, every dossier tail
size, odd starts, adversarial raw payloads, reused out buffers, readonly and
aliased inputs, and mmap owners; reserved code 3 must surface at the
identical first (patch, pixel) in both orders (patchmajor in-kernel at the
poison-scan position, blocked via the unchanged preflight before any write).
"""
import numpy as np
import pytest

from solweig_light._native_dispatch import direct_aosoa as da
from solweig_light.geometry.visibility import PackedVisibility, _EncodedPatch
from solweig_light.geometry.visibility_compiled import _descriptor, decode_block
from solweig_light.geometry.visibility_native import (MappedVisibility,
                                                      open_native_visibility,
                                                      save_native_visibility)

from n9_producer_ref import (MODE_CODES, N9_RAW_BITS, POISON, n9_aosoa_rows,
                             n9_build_channel, n9_first_reserved,
                             n9_legacy_expr_decode, n9_ref_decode,
                             n9_written_prefix)

MODE_CYCLES = {
    'mix': ('binary', 'ternary', 'raw'),
    'all-binary': ('binary',),
    'all-ternary': ('ternary',),
    'all-raw': ('raw',),
}
SIZES = [0, 1, 3, 5, 7, 8, 9, 128, 1024]  # 0, 1, W-1, W, W+1 (W in {4,8}), 128, 1024
STARTS = [0, 3, 5]  # includes odd offsets straddling packed byte boundaries


@pytest.mark.parametrize('order', ['patchmajor', 'blocked'])
@pytest.mark.parametrize('mode_name', MODE_CYCLES)
@pytest.mark.parametrize('width', da.WIDTHS)
@pytest.mark.parametrize('start', STARTS)
@pytest.mark.parametrize('count', SIZES)
def test_n9_literal_matches_reference_and_legacy(count, start, width, mode_name, order):
    modes = [MODE_CYCLES[mode_name][i % len(MODE_CYCLES[mode_name])] for i in range(3)]
    channel = n9_build_channel(start + count, modes, seed=count * 7 + start)
    produced = da.produce_block_aosoa(channel, start, start + count, 3,
                                      width=width, order=order)
    expected_ref = n9_ref_decode(channel, start, start + count)
    expected_legacy = n9_legacy_expr_decode(channel, start, start + count)
    assert produced.dtype == np.uint32
    assert produced.shape == (-(-count // width), 3, width)
    assert np.array_equal(n9_aosoa_rows(produced)[:count], expected_ref), 'vs independent decoder'
    assert np.array_equal(n9_aosoa_rows(produced)[:count], expected_legacy), 'vs accepted producer'


def test_n9_raw_adversarial_bits_exact_sequence():
    """Every adversarial raw bit pattern round-trips bit-exactly (signed
    zeros, NaN payloads both signs, +/-Inf, subnormals, codebook straddles)."""
    pixels = len(N9_RAW_BITS)
    payload = np.array(N9_RAW_BITS, dtype='<u4').tobytes()
    channel = PackedVisibility((1, pixels, 1), (_EncodedPatch('raw', payload),))
    for width in da.WIDTHS:
        produced = da.produce_block_aosoa(channel, 0, pixels, 1, width=width)
        assert np.array_equal(n9_aosoa_rows(produced)[:pixels],
                              n9_ref_decode(channel, 0, pixels))


def _ternary_reserved_payload(pixels, position):
    """Ternary payload with code 3 at ``position``."""
    codes = np.zeros(pixels, np.uint8)
    codes[position] = 3
    padded = np.zeros((pixels + 3) // 4 * 4, np.uint8)
    padded[:pixels] = codes
    payload = (padded[0::4] | (padded[1::4] << 2) | (padded[2::4] << 4)
               | (padded[3::4] << 6)).tobytes()
    return payload, True


def _channel_with_reserved(pixels, position, patch_index, patches):
    """Mixed channel whose ternary patch ``patch_index`` has code 3 at
    ``position``."""
    good = n9_build_channel(pixels, ('binary', 'ternary', 'raw') * patches, seed=9)
    replaced = list(good._patches)
    while len(replaced) < patches:
        replaced.append(replaced[len(replaced) % 3])
    replaced = replaced[:patches]
    payload, _ = _ternary_reserved_payload(pixels, position)
    replaced[patch_index] = _EncodedPatch('ternary', payload)
    return PackedVisibility((1, pixels, patches), tuple(replaced))


def test_n9_reserved_first_error_position_patchmajor_poison_scan():
    """Patchmajor: the poison prefix left in ``out`` is exactly the
    patch-major cell count before the FIRST reserved (patch, pixel), for
    every injection position -- identical to the independent decoder's."""
    pixels, patches = 13, 4
    for patch_index in range(patches):
        for position in range(pixels):
            channel = _channel_with_reserved(pixels, position, patch_index, patches)
            first = n9_first_reserved(channel, 0, pixels)
            assert first == (patch_index, position)
            out = np.full((-(-pixels // 8), patches, 8), POISON, dtype=np.uint32)
            with pytest.raises(IndexError, match='Reserved visibility code'):
                da.produce_block_aosoa(channel, 0, pixels, patches, out=out)
            expected_written = patch_index * pixels + position
            assert n9_written_prefix(out, POISON, patches, pixels, 8) == expected_written
            # The accepted legacy route observes the same error.
            with pytest.raises(IndexError, match='Reserved visibility code'):
                decode_block(channel, 0, pixels, patches)


def test_n9_reserved_blocked_preflight_leaves_out_poisoned():
    """Blocked order validates pre-launch: a poison out survives the error at
    every injection position."""
    pixels, patches = 13, 4
    for patch_index in range(patches):
        for position in range(pixels):
            channel = _channel_with_reserved(pixels, position, patch_index, patches)
            out = np.full((-(-pixels // 8), patches, 8), POISON, dtype=np.uint32)
            with pytest.raises(IndexError, match='Reserved visibility code'):
                da.produce_block_aosoa(channel, 0, pixels, patches, order='blocked',
                                       out=out)
            assert np.all(out == POISON), 'blocked order validates before any write'


def test_n9_reused_out_buffer_fully_rewritten():
    """A reused out buffer carries no stale bytes from the previous call."""
    first = n9_build_channel(64, ('binary', 'ternary', 'raw'), seed=1)
    second = n9_build_channel(64, ('ternary', 'raw', 'binary'), seed=2)
    for order in ('patchmajor', 'blocked'):
        out = np.full((8, 3, 8), POISON, dtype=np.uint32)
        da.produce_block_aosoa(first, 0, 64, 3, order=order, out=out)
        da.produce_block_aosoa(second, 0, 64, 3, order=order, out=out)
        fresh = da.produce_block_aosoa(second, 0, 64, 3, order=order)
        assert np.array_equal(out, fresh)


def test_n9_readonly_and_aliased_payload_inputs():
    """Descriptor views are readonly; payloads shared across patches alias
    safely and decode identically to distinct copies."""
    shared = n9_build_channel(128, ('binary', 'ternary', 'raw'), seed=3)
    payloads, modes = _descriptor(shared)
    assert all(not view.flags.writeable for view in payloads)
    aliased = PackedVisibility((1, 128, 3), tuple(shared._patches))
    twin = PackedVisibility((1, 128, 3), tuple(shared._patches))
    for order in ('patchmajor', 'blocked'):
        a = da.produce_block_aosoa(aliased, 3, 99, 3, order=order)
        b = da.produce_block_aosoa(twin, 3, 99, 3, order=order)
        assert np.array_equal(a, b)
        assert np.array_equal(n9_aosoa_rows(a)[:96],
                              n9_ref_decode(shared, 3, 99))
    blocks = da.produce_blocks_aosoa(aliased, twin, shared, 0, 128, 3)
    assert all(np.array_equal(n9_aosoa_rows(block)[:128], n9_ref_decode(shared, 0, 128))
               for block in blocks)


def _mapped(channel, tmp_path):
    manifest = tmp_path / 'n9_mapped.json'
    save_native_visibility(manifest, channel)
    return open_native_visibility(manifest)


def test_n9_mapped_owner_close_and_exception_cleanup(tmp_path):
    """A mapped owner produces, refuses after close, and releases its lease
    when the kernel raises on a reserved code (lock re-acquirable)."""
    channel = _mapped(n9_build_channel(64, ('binary', 'ternary', 'raw'), seed=4),
                      tmp_path)
    try:
        produced = da.produce_block_aosoa(channel, 0, 64, 3)
        assert np.array_equal(n9_aosoa_rows(produced)[:64], n9_ref_decode(channel, 0, 64))
    finally:
        channel.close()
    with pytest.raises(RuntimeError, match='closed'):
        da.produce_block_aosoa(channel, 0, 8, 3)

    events = []
    # save_native_visibility rejects reserved codes, so the corrupt mapped
    # owner is constructed directly over a raw memmap (as in the N8-11 suite).
    pixels = 9
    corrupt_payload, _ = _ternary_reserved_payload(pixels, 4)
    mapping_path = tmp_path / 'corrupt_payload.npy'
    raw = np.lib.format.open_memmap(mapping_path, mode='w+', dtype=np.uint8,
                                    shape=(len(corrupt_payload),))
    raw[:] = np.frombuffer(corrupt_payload, dtype=np.uint8)
    raw.flush()
    mapping = np.lib.format.open_memmap(mapping_path, mode='r')
    corrupt = MappedVisibility((1, pixels, 1),
                               [{'mode': 'ternary', 'offset': 0,
                                 'length': len(corrupt_payload)}], mapping)

    class _Recording:
        def acquire(self, *_a, **_k):
            events.append('acquire')
            return real.acquire(*_a, **_k)

        def release(self, *_a, **_k):
            events.append('release')
            return real.release(*_a, **_k)

        def __enter__(self):
            self.acquire()
            return self

        def __exit__(self, *exc):
            self.release()

    real = corrupt._lock
    object.__setattr__(corrupt, '_lock', _Recording())
    try:
        for order in ('patchmajor', 'blocked'):
            events.clear()
            with pytest.raises(IndexError, match='Reserved visibility code'):
                da.produce_block_aosoa(corrupt, 0, pixels, 1, order=order)
            assert events == ['acquire', 'release'], 'lease leaked across the error'
    finally:
        corrupt.close()


def test_n9_mapped_mode4_keeps_byte_assembly(tmp_path):
    """Raw mapped payloads keep the original byte-assembly loop's output."""
    channel = _mapped(n9_build_channel(131, ('raw', 'raw', 'raw'), seed=5), tmp_path)
    try:
        produced = da.produce_block_aosoa(channel, 5, 130, 3)
        assert np.array_equal(n9_aosoa_rows(produced)[:125],
                              n9_legacy_expr_decode(channel, 5, 130))
    finally:
        channel.close()


def test_n9_b_control_inherits_specialized_producer():
    """F1D note pinned: the B control consumes THIS producer's output, so the
    specialization flows to it with no separate change (identity check on a
    mixed vault, uint32 views vs float32 views of the same bytes)."""
    from solweig_light._native_dispatch import lw_b_control as bc
    channel = n9_build_channel(128, ('binary', 'ternary', 'raw'), seed=6)
    blocks = da.produce_blocks_aosoa(channel, channel, channel, 0, 128, 3)
    for block in blocks:
        assert block.dtype == np.uint32
        f32 = block.view(np.float32)
        assert np.array_equal(n9_aosoa_rows(block)[:128],
                              n9_ref_decode(channel, 0, 128))
        # The B adapter's zero-copy view convention stays valid on these bytes.
        assert f32.shape == block.shape and f32.strides == block.strides
    assert callable(bc.lw_primary_b)
