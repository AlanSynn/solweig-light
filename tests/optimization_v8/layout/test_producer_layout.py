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
"""N8-11 direct-AoSoA producer layout tests (dossier 02_direct_aosoa).

Bit-exact layout equivalence against visibility_compiled._decode on the
adversarial grid (uint32 views), padding-lane poison invariants, reserved
code observability at every injection position, decode_block's admission
and range contract, owner-lease lifetime, alias immutability, and the
B/P/mode tails named by the dossier.
"""
import hashlib
import threading

import numpy as np
import pytest

from solweig_light._native_dispatch import direct_aosoa as da
from solweig_light.geometry.visibility import (LazyDiffVisibility, PackedVisibility,
                                               VisibilityBuilder, _EncodedPatch)
from solweig_light.geometry.visibility_compiled import _decode, _descriptor, decode_block
from solweig_light.geometry.visibility_native import (MappedVisibility, open_native_visibility,
                                                      save_native_visibility)

POISON = np.uint32(0xDEADBEEF)

# Adversarial float32 bit patterns for raw payloads: signed zeros,
# subnormals, ±Inf, NaN payloads, codebook values, near-one thresholds.
RAW_BITS = [0x00000000, 0x80000000, 0x3F800000, 0x40000000, 0x40490FDB,
            0x80000001, 0x007FFFFF, 0x00000001, 0x7F800000, 0xFF800000,
            0x7FC00000, 0x7FC00001, 0x3F7FFFFF, 0x3F800001, 0x4B7FFFFF]


def aosoa_rows(bits):
    """[G,P,W] -> logical [G*W, P] rows (row = gang*width + lane)."""
    gangs, patches, width = bits.shape
    return bits.transpose(0, 2, 1).reshape(gangs * width, patches)


def build_channel(pixels, modes, *, seed=0, raw_bits=None):
    """PackedVisibility whose patches use the requested mode sequence."""
    rng = np.random.default_rng(seed)
    shape = (1, pixels, len(modes)) if pixels else (0, 0, len(modes))
    patches = []
    for mode in modes:
        if pixels == 0:
            payload = b''
        elif mode == 'raw':
            bits = rng.choice(np.array(RAW_BITS if raw_bits is None else raw_bits,
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


def payload_digest(channel):
    return hashlib.sha256(b''.join(p.payload for p in channel._patches)).hexdigest()


# ---------------------------------------------------------------------------
# Bit-exact layout equivalence vs _decode over the adversarial grid.
# ---------------------------------------------------------------------------

B_GRID = [0, 1, 3, 4, 5, 7, 8, 9, 11, 13, 16, 97, 128]
P_GRID = [1, 2, 3, 153]
MODE_CYCLES = {
    'mix': ('binary', 'ternary', 'raw'),
    'all-binary': ('binary',),
    'all-ternary': ('ternary',),
    'all-raw': ('raw',),
}


@pytest.mark.parametrize('width', da.WIDTHS)
@pytest.mark.parametrize('order', ['patchmajor', 'blocked'])
@pytest.mark.parametrize('mode_name', MODE_CYCLES)
@pytest.mark.parametrize('patches', P_GRID)
@pytest.mark.parametrize('pixels', [128, 131])
@pytest.mark.parametrize('span', [(0, None), (5, None), (0, 7), (3, 130)])
def test_layout_bits_equal_decode(pixels, patches, mode_name, order, width, span):
    modes = [MODE_CYCLES[mode_name][i % len(MODE_CYCLES[mode_name])] for i in range(patches)]
    channel = build_channel(pixels, modes, seed=patches * 31 + pixels)
    start, stop = span[0], min(span[1] or pixels, pixels)
    if start > stop:
        return
    produced = da.produce_block_aosoa(channel, start, stop, patches, width=width, order=order)
    expected = _decode(*_descriptor(channel), start, stop, patches).view(np.uint32)
    assert produced.dtype == np.uint32
    gangs = -(-(stop - start) // width)
    assert produced.shape == (gangs, patches, width)
    assert np.array_equal(aosoa_rows(produced)[:stop - start], expected)


def test_layout_bits_equal_decode_full_grid_b_values():
    """Every dossier B tail against P=153 with a mixed vault, both widths."""
    patches = 153
    modes = [('binary', 'ternary', 'raw')[i % 3] for i in range(patches)]
    channel = build_channel(131, modes, seed=99)
    for width in da.WIDTHS:
        for count in B_GRID:
            produced = da.produce_block_aosoa(channel, 0, count, patches, width=width)
            expected = _decode(*_descriptor(channel), 0, count, patches).view(np.uint32)
            assert np.array_equal(aosoa_rows(produced)[:count], expected), (width, count)


def test_p609_boundary():
    patches = 609
    modes = [('binary', 'ternary', 'raw')[i % 3] for i in range(patches)]
    channel = build_channel(128, modes, seed=5)
    for width in da.WIDTHS:
        for order in ('patchmajor', 'blocked'):
            produced = da.produce_block_aosoa(channel, 0, 128, patches, width=width, order=order)
            expected = _decode(*_descriptor(channel), 0, 128, patches).view(np.uint32)
            assert np.array_equal(aosoa_rows(produced), expected)


def test_three_channel_entry_matches_single():
    rng = np.random.default_rng(3)
    shape = (8, 16, 6)
    planes = np.where(rng.random(shape) < 0.5, np.float32(0), np.float32(1))
    planes[..., 2] += np.float32(1e-3)  # force one raw patch
    channels = []
    for index in range(3):
        builder = VisibilityBuilder(shape)
        for patch in range(shape[2]):
            builder.append(np.ascontiguousarray(planes[..., patch]))
        channels.append(builder.finish())
    blocks = da.produce_blocks_aosoa(*channels, 16, 128, 6)
    assert blocks is not None and len(blocks) == 3
    for channel, block in zip(channels, blocks):
        expected = _decode(*_descriptor(channel), 16, 128, 6).view(np.uint32)
        assert np.array_equal(aosoa_rows(block)[:112], expected)


# ---------------------------------------------------------------------------
# Padding lanes: never written, never read.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('width', da.WIDTHS)
@pytest.mark.parametrize('order', ['patchmajor', 'blocked'])
@pytest.mark.parametrize('count', [1, 3, 5, 7, 9, 11, 13, 97, 127])
def test_padding_lanes_never_written(width, order, count):
    modes = ('binary', 'ternary', 'raw')
    channel = build_channel(128, modes, seed=17)
    gangs = -(-count // width)
    out = np.full((gangs, 3, width), POISON, dtype=np.uint32)
    produced = da.produce_block_aosoa(channel, 0, count, 3, width=width, order=order, out=out)
    assert produced is out
    assert np.array_equal(aosoa_rows(produced)[count:], np.full((gangs * width - count, 3), POISON))
    expected = _decode(*_descriptor(channel), 0, count, 3).view(np.uint32)
    assert np.array_equal(aosoa_rows(produced)[:count], expected)


def test_padding_never_reads_outside_payloads():
    """A payload sized exactly for the requested interval must decode clean."""
    # 7 binary pixels = 1 byte; asking for 7 rows at W=8 leaves lane 7 unset.
    channel = build_channel(7, ('binary',))
    out = da.produce_block_aosoa(channel, 0, 7, 1, width=8)
    assert np.array_equal(aosoa_rows(out)[:7], _decode(*_descriptor(channel), 0, 7, 1).view(np.uint32))


# ---------------------------------------------------------------------------
# Reserved code 3: same observable as legacy, at every injection position.
# ---------------------------------------------------------------------------

def inject_reserved(mode, pixels, position):
    """Patch payload with a code 3 at row ``position`` (0-based pixel)."""
    if mode == 'binary':
        payload = bytearray(np.packbits(np.zeros(pixels, np.uint8), bitorder='little').tobytes())
        payload[position // 8] |= np.uint8(1)  # code 1, not 3: binary cannot encode 3
        return bytes(payload), False
    codes = np.zeros(pixels, np.uint8)
    codes[position] = 3
    padded = np.zeros((pixels + 3) // 4 * 4, np.uint8)
    padded[:pixels] = codes
    payload = (padded[0::4] | (padded[1::4] << 2) | (padded[2::4] << 4) | (padded[3::4] << 6)).tobytes()
    return payload, True


@pytest.mark.parametrize('order', ['patchmajor', 'blocked'])
def test_reserved_code_raised_for_every_position(order):
    """No (patch, pixel) escapes validation: exhaustive single-position sweep."""
    pixels, patches = 13, 4
    for patch in range(patches):
        for position in range(pixels):
            payload, injectable = inject_reserved('ternary', pixels, position)
            if not injectable:
                continue
            good = build_channel(pixels, ('ternary',) * patches, seed=1)
            replaced = list(good._patches)
            replaced[patch] = _EncodedPatch('ternary', payload)
            channel = PackedVisibility((1, pixels, patches), tuple(replaced))
            with pytest.raises(IndexError, match='Reserved visibility code'):
                da.produce_block_aosoa(channel, 0, pixels, patches, order=order)
            with pytest.raises(IndexError, match='Reserved visibility code'):
                decode_block(channel, 0, pixels, patches)


def test_reserved_code_blocked_preflight_leaves_out_untouched():
    """Blocked order validates pre-launch: a poison out survives the error."""
    pixels, patches = 9, 3
    payload, _ = inject_reserved('ternary', pixels, 4)
    good = build_channel(pixels, ('ternary',) * patches, seed=2)
    replaced = list(good._patches)
    replaced[1] = _EncodedPatch('ternary', payload)
    channel = PackedVisibility((1, pixels, patches), tuple(replaced))
    out = np.full((2, patches, 8), POISON, dtype=np.uint32)
    with pytest.raises(IndexError, match='Reserved visibility code'):
        da.produce_block_aosoa(channel, 0, pixels, patches, order='blocked', out=out)
    assert np.all(out == POISON)


def test_binary_mode_cannot_carry_reserved_code():
    """Binary payloads (1 bit/pixel) are structurally reserved-free."""
    channel = build_channel(16, ('binary',))
    produced = da.produce_block_aosoa(channel, 0, 16, 1, order='blocked')
    assert np.array_equal(aosoa_rows(produced),
                          _decode(*_descriptor(channel), 0, 16, 1).view(np.uint32))


# ---------------------------------------------------------------------------
# Admission, range contract, error parity with decode_block.
# ---------------------------------------------------------------------------

class DuckChannel:
    """Duck-typed channel: the producer must decline (legacy route keeps it)."""

    def __init__(self, shape):
        self.shape = shape


class CustomPacked(PackedVisibility):
    """Subclass with custom indexing: never admitted."""


def test_duck_and_subclass_and_lazy_declined():
    duck = DuckChannel((1, 128, 3))
    assert da.produce_block_aosoa(duck, 0, 128, 3) is None
    assert da.produce_blocks_aosoa(duck, duck, duck, 0, 128, 3) is None
    base = build_channel(8, ('binary',))
    subclass = CustomPacked(base.shape, base._patches)
    assert da.produce_block_aosoa(subclass, 0, 8, 1) is None
    lazy = LazyDiffVisibility(base, base)
    assert da.produce_block_aosoa(lazy, 0, 8, 1) is None
    assert da.produce_blocks_aosoa(lazy, base, base, 0, 8, 1) is None
    dense = np.zeros((1, 8, 1), dtype=np.float32)
    assert da.produce_block_aosoa(dense, 0, 8, 1) is None


@pytest.mark.parametrize('start,stop,patches', [(-1, 8, 1), (4, 3, 1), (0, 9, 1),
                                                (0, 8, 3), (9, 9, 1)])
def test_range_contract_matches_decode_block(start, stop, patches):
    channel = build_channel(8, ('binary', 'ternary'))
    with pytest.raises(IndexError, match='Visibility block interval out of range'):
        decode_block(channel, start, stop, patches)
    with pytest.raises(IndexError, match='Visibility block interval out of range'):
        da.produce_block_aosoa(channel, start, stop, patches)
    with pytest.raises(IndexError, match='Visibility block interval out of range'):
        da.produce_blocks_aosoa(channel, channel, channel, start, stop, patches)


def test_out_buffer_validation():
    channel = build_channel(8, ('binary',))
    bad = np.zeros((1, 1, 4), dtype=np.uint32)
    with pytest.raises(ValueError, match='out must be'):
        da.produce_block_aosoa(channel, 0, 8, 1, width=8, out=bad)


def test_bad_order_rejected():
    channel = build_channel(8, ('binary',))
    with pytest.raises(ValueError, match='producer order'):
        da.produce_block_aosoa(channel, 0, 8, 1, order='reverse')


# ---------------------------------------------------------------------------
# Mapped owners: parity, lease held, close observability, alias immutability.
# ---------------------------------------------------------------------------

def mapped_copy(channel, tmp_path):
    manifest = tmp_path / 'mapped.json'
    save_native_visibility(manifest, channel)
    return open_native_visibility(manifest)


def test_mapped_owner_parity_and_close(tmp_path):
    channel = build_channel(131, ('binary', 'ternary', 'raw'), seed=11)
    mapped = mapped_copy(channel, tmp_path)
    try:
        for width in da.WIDTHS:
            for order in ('patchmajor', 'blocked'):
                produced = da.produce_block_aosoa(mapped, 3, 97, 3, width=width, order=order)
                expected = _decode(*_descriptor(mapped), 3, 97, 3).view(np.uint32)
                assert np.array_equal(aosoa_rows(produced)[:94], expected)
        blocks = da.produce_blocks_aosoa(mapped, mapped, mapped, 0, 128, 3)
        assert all(np.array_equal(aosoa_rows(b)[:128],
                                  _decode(*_descriptor(mapped), 0, 128, 3).view(np.uint32))
                   for b in blocks)
    finally:
        mapped.close()
    with pytest.raises(RuntimeError, match='Native visibility is closed'):
        da.produce_block_aosoa(mapped, 0, 8, 3)


def test_mapped_reserved_code(tmp_path):
    """A mapped owner built outside open_native_visibility still preflights."""
    import json
    pixels = 9
    payload, _ = inject_reserved('ternary', pixels, 6)
    good = build_channel(pixels, ('ternary',), seed=13)
    manifest = tmp_path / 'corrupt.json'
    save_native_visibility(manifest, good)
    # Rewrite the payload NPY with a reserved code at the mapped offset.
    document = json.loads(manifest.read_text())
    payload_path = tmp_path / document['payload']['name']
    data = bytearray(payload_path.read_bytes())
    patch = document['patches'][0]
    header = np.lib.format.open_memmap(payload_path, mode='r').offset
    data[header + patch['offset']:header + patch['offset'] + patch['length']] = payload
    payload_path.chmod(0o644)
    payload_path.write_bytes(data)
    # The manifest digest no longer matches; construct the owner directly.
    mapping = np.lib.format.open_memmap(payload_path, mode='r')
    mapped = MappedVisibility((1, pixels, 1), [{'mode': 'ternary', 'offset': 0,
                                             'length': len(payload)}], mapping)
    try:
        for order in ('patchmajor', 'blocked'):
            with pytest.raises(IndexError, match='Reserved visibility code'):
                da.produce_block_aosoa(mapped, 0, pixels, 1, order=order)
    finally:
        mapped.close()


class InstrumentedMapped(MappedVisibility):
    """Records lock traffic so the lease is observable from the test."""

    def __init__(self, shape, patches, mapping):
        super().__init__(shape, patches, mapping)
        self.events = []
        real = self._lock

        class _Recording:
            def acquire(self, *_a, **_k):
                outer.events.append('acquire')
                return real.acquire(*_a, **_k)

            def release(self, *_a, **_k):
                outer.events.append('release')
                return real.release(*_a, **_k)

            def __enter__(self):
                self.acquire()
                return self

            def __exit__(self, *exc):
                self.release()

        outer = self
        object.__setattr__(self, '_lock', _Recording())


def instrumented_copy(channel, tmp_path):
    """InstrumentedMapped over a saved+reopened copy of ``channel``."""
    manifest = tmp_path / 'leased.json'
    save_native_visibility(manifest, channel)
    mapped = open_native_visibility(manifest)
    return InstrumentedMapped(mapped.shape,
                              [{'mode': p.mode, 'offset': p.offset, 'length': p.length}
                               for p in mapped._patches], mapped._mapping)


def test_owner_lease_held_through_producer(tmp_path):
    """Lock is acquired before decode work and held until the kernel returns."""
    channel = build_channel(128, ('binary', 'ternary', 'raw'), seed=19)
    mapped = instrumented_copy(channel, tmp_path)
    try:
        da.produce_block_aosoa(mapped, 0, 128, 3)
        assert mapped.events == ['acquire', 'release']
    finally:
        mapped.close()


def test_owner_lease_held_through_three_channel_entry(tmp_path):
    channel = build_channel(64, ('binary', 'ternary', 'raw'), seed=43)
    mapped = instrumented_copy(channel, tmp_path)
    plain = build_channel(64, ('raw', 'binary', 'ternary'), seed=47)
    try:
        da.produce_blocks_aosoa(mapped, plain, mapped, 0, 64, 3)
        # Shared mapped owner deduplicated by id: one acquire per distinct owner.
        assert mapped.events == ['acquire', 'release']
    finally:
        mapped.close()


def test_owner_close_serializes_on_the_producer_lock(tmp_path):
    """close() waits on the same lock the producer holds; it cannot retire
    the mapping while a producer call is between acquire and release."""
    channel = build_channel(64, ('binary', 'ternary', 'raw'), seed=23)
    mapped = instrumented_copy(channel, tmp_path)
    finished = []

    def close():
        mapped.close()
        finished.append(True)

    with mapped._lock:  # stand in for an in-flight producer lease
        thread = threading.Thread(target=close)
        thread.start()
        thread.join(timeout=0.2)
        assert not finished, 'close() retired the mapping under a held lease'
        assert not mapped.closed
    thread.join(timeout=5)
    assert finished and mapped.closed


# ---------------------------------------------------------------------------
# Alias safety: payloads bit-identical before/after producer calls.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('order', ['patchmajor', 'blocked'])
def test_inputs_bit_identical_after_call(order, tmp_path):
    channel = build_channel(131, ('binary', 'ternary', 'raw'), seed=29)
    before = payload_digest(channel)
    da.produce_block_aosoa(channel, 7, 130, 3, order=order)
    da.produce_blocks_aosoa(channel, channel, channel, 0, 131, 3, order=order)
    assert payload_digest(channel) == before
    mapped = mapped_copy(channel, tmp_path)
    try:
        before_mapped = payload_digest(mapped)
        da.produce_block_aosoa(mapped, 0, 131, 3, order=order)
        assert payload_digest(mapped) == before_mapped
    finally:
        mapped.close()


def test_producer_output_owned_not_a_view(tmp_path):
    """Returned blocks are fresh allocations; they survive owner close."""
    channel = build_channel(64, ('raw',), seed=31)
    mapped = mapped_copy(channel, tmp_path)
    produced = da.produce_block_aosoa(mapped, 0, 64, 1)
    mapped.close()
    expected = _decode(*_descriptor(channel), 0, 64, 1).view(np.uint32)
    assert np.array_equal(aosoa_rows(produced), expected)
