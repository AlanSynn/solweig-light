"""Verifier fusion preserves decoded bits, bounded reads and validation order."""
from concurrent.futures import ThreadPoolExecutor
import io
import threading
import weakref
import zipfile

import numpy as np
import pytest

from solweig_light.geometry import visibility as codec
from solweig_light.geometry import visibility_compiled as compiled
from solweig_light.geometry import visibility_native as native


def cube(pixels=35, patches=7):
    bits = np.array([0, 0x80000000, 0x7fc00023, 0x7fa00045, 0x7f800000,
                     0xff800000, 0x3eaaaaab, 0x3f800000, 0x40000000], np.uint32)
    dense = np.resize(bits, (1, pixels, patches)).view(np.float32)
    dense[0, :, 0] = np.arange(pixels) % 2
    if patches > 1:
        dense[0, :, 1] = np.arange(pixels) % 3
    return dense


def archive(path, dense, *, fortran=False, endian='<', compression=zipfile.ZIP_DEFLATED):
    with zipfile.ZipFile(path, 'w', compression=compression) as output:
        for name in codec.LEGACY_MEMBERS:
            stream = io.BytesIO()
            # Convert uint32 first to preserve signaling NaNs across endian layouts.
            values = dense.view(np.uint32).astype(endian+'u4').view(endian+'f4')
            np.lib.format.write_array(stream, np.asfortranarray(values) if fortran else values)
            output.writestr(name+'.npy', stream.getvalue())


@pytest.mark.parametrize('pixels', [0, 1, 3, 7, 8, 9, 31, 35])
@pytest.mark.parametrize('mapped', [False, True])
def test_block_companion_exact_for_modes_bits_intervals_and_tails(tmp_path, pixels, mapped):
    dense = cube(pixels)
    packed = codec.PackedVisibility.from_dense(dense)
    channel = packed
    if mapped:
        native.save_native_visibility(tmp_path/'native.json', packed)
        channel = native.open_native_visibility(tmp_path/'native.json')
    try:
        for start, stop in [(0, pixels), (pixels//2, pixels), (pixels, pixels),
                            (min(1, pixels), pixels), (min(3, pixels), min(8, pixels)),
                            (min(7, pixels), min(9, pixels))]:
            actual = dense.reshape(pixels, 7)[start:stop].view(np.uint32)
            expected = compiled.decode_block(channel, start, stop, 7).view(np.uint32)
            np.testing.assert_array_equal(actual, expected)
            assert compiled.compare_block_bits(channel, actual, start, stop, 7) == -1
            if stop > start:
                changed = actual.copy()
                changed[-1, 6] ^= np.uint32(1)
                changed[0, 2] ^= np.uint32(0x80000000)
                assert compiled.compare_block_bits(channel, changed, start, stop, 7) == 2
        if pixels > 2:
            assert packed.modes[:2] == ('binary', 'ternary')
        for index, patch in enumerate(channel._patches):
            assert np.shares_memory(channel._block_descriptor[0][index], np.frombuffer(patch.payload, np.uint8)) or not pixels
        assert getattr(channel, '_fused_block_descriptor', None) is None
    finally:
        if mapped:
            channel.close()


@pytest.mark.parametrize('patch,pixel', [(0, 0), (0, 34), (1, 8), (6, 34)])
def test_mismatch_never_skips_later_reserved_encoding(patch, pixel):
    dense = np.zeros((1, 35, 7), np.float32)
    packed = codec.PackedVisibility.from_dense(dense)
    payload = bytearray(9)
    payload[pixel//4] |= 3 << (2*(pixel % 4))
    patches = list(packed._patches)
    patches[patch] = codec._EncodedPatch('ternary', bytes(payload))
    malformed = codec.PackedVisibility(dense.shape, tuple(patches))
    actual = np.ones((35, 7), np.uint32)
    with pytest.raises(IndexError) as original:
        compiled.decode_block(malformed, 0, 35, 7)
    with pytest.raises(IndexError) as candidate:
        compiled.compare_block_bits(malformed, actual, 0, 35, 7)
    assert str(candidate.value) == str(original.value) == 'Reserved visibility code'
    assert candidate.value.__context__ is None


def test_reserved_codes_follow_original_patch_major_byte_access_order():
    # Two invalid pixels expose accidental pixel-major validation. The original
    # reaches patch 0's last pixel before patch 1's first pixel.
    reads = []
    class Traced:
        def __init__(self, patch, data):
            self.patch, self.data = patch, data
        def __getitem__(self, index):
            reads.append((self.patch, index))
            return self.data[index]
    payloads = [Traced(0, np.array([0, 0, 3], np.uint8)),
                Traced(1, np.array([3, 0, 0], np.uint8))]
    modes = np.array([2, 2], np.uint8)
    with pytest.raises(IndexError, match='Reserved'):
        compiled._decode.py_func(payloads, modes, 0, 9, 2)
    original = reads.copy()
    reads.clear()
    with pytest.raises(IndexError, match='Reserved'):
        compiled._compare_bits.py_func(payloads, modes, np.ones((9, 2), np.uint32), 0, 9, 2)
    assert reads == original == [(0, pixel//4) for pixel in range(9)]


@pytest.mark.parametrize('budget', [176, 512, 4096])
def test_archive_first_mismatch_stays_channel_then_patch_order(tmp_path, budget):
    dense = cube(103)
    path = tmp_path/'v.npz'
    archive(path, dense)
    changed = dense.copy()
    changed.view(np.uint32)[0, 0, 6] ^= np.uint32(1)
    changed.view(np.uint32)[0, -1, 1] ^= np.uint32(1)
    original = codec.PackedVisibility.from_dense(dense)
    differing = codec.PackedVisibility.from_dense(changed)
    # vbshmat is visited before vegshadowmat, but legacy reporting is fixed.
    channels = dict(zip(codec.LEGACY_MEMBERS, (original, differing, differing)))
    assert codec._compare_visibility_npz(path, channels, shape=dense.shape, max_workspace_bytes=budget) == (
        'Legacy geometry values differ in channel vegshadowmat, patch 1')


@pytest.mark.parametrize('budget', [176, 4096])
def test_crc_still_precedes_deferred_mismatch_on_compiled_path(tmp_path, budget):
    dense = cube(103)
    path = tmp_path/'v.npz'
    archive(path, dense, compression=zipfile.ZIP_STORED)
    with zipfile.ZipFile(path) as source:
        member = source.getinfo('vegshadowmat.npy')
        offset = member.header_offset+30+len(member.filename.encode())+len(member.extra)
    data = bytearray(path.read_bytes())
    data[offset+member.file_size-1] ^= 1
    path.write_bytes(data)
    changed = dense.copy()
    changed.view(np.uint32)[0, 0, 0] ^= np.uint32(1)
    channels = dict.fromkeys(codec.LEGACY_MEMBERS, codec.PackedVisibility.from_dense(changed))
    with pytest.raises(zipfile.BadZipFile, match='CRC'):
        codec._compare_visibility_npz(path, channels, shape=dense.shape, max_workspace_bytes=budget)


@pytest.mark.parametrize('kind', ['fortran', 'endian', 'host', 'subclass', 'custom', 'tiny'])
def test_unusual_paths_keep_retained_decoder(tmp_path, monkeypatch, kind):
    dense = cube()
    packed = codec.PackedVisibility.from_dense(dense)
    channel = packed
    calls = []
    if kind == 'subclass':
        class Subclass(codec.PackedVisibility):
            def decode_pixels(self, *args):
                calls.append(args)
                return super().decode_pixels(*args)
        channel = Subclass(packed.shape, packed._patches)
    elif kind == 'custom':
        class Custom:
            def decode_pixels(self, *args):
                calls.append(args)
                return packed.decode_pixels(*args)
        channel = Custom()
    if kind == 'host':
        monkeypatch.setattr(codec.np, 'little_endian', False)
    def forbidden(*args):
        pytest.fail('unusual paths must retain their decoder')
    monkeypatch.setattr(compiled, 'compare_block_bits', forbidden)
    path = tmp_path/'v.npz'
    archive(path, dense, fortran=kind == 'fortran', endian='>' if kind == 'endian' else '<')
    assert codec._compare_visibility_npz(path, dict.fromkeys(codec.LEGACY_MEMBERS, channel),
        shape=dense.shape, max_workspace_bytes=128 if kind == 'tiny' else 4096) is None
    if kind in ('custom', 'subclass'):
        assert calls


def test_no_expected_block_and_numeric_budget_includes_all_modes(tmp_path, monkeypatch):
    dense = cube(103)
    channels = [codec.PackedVisibility.from_dense(dense) for _ in range(3)]
    path = tmp_path/'v.npz'
    archive(path, dense)
    budget, patches = 176, dense.shape[2]
    original = compiled.compare_block_bits
    previous, calls = [], []
    def compared(channel, actual, start, stop, count):
        assert all(reference() is None for reference in previous)
        assert actual.nbytes+3*patches <= budget
        assert stop-start <= budget//(16*patches+64)
        previous.append(weakref.ref(actual))
        calls.append((start, stop))
        return original(channel, actual, start, stop, count)
    def forbidden(*args):
        pytest.fail('native verifier must not allocate an expected block')
    monkeypatch.setattr(compiled, 'compare_block_bits', compared)
    monkeypatch.setattr(compiled, 'decode_block', forbidden)
    assert codec._compare_visibility_npz(path, dict(zip(codec.LEGACY_MEMBERS, channels)),
        shape=dense.shape, max_workspace_bytes=budget) is None
    assert len(calls) == 3*103
    assert sum(channel._block_descriptor[1].nbytes for channel in channels) == 3*patches


def test_mapped_close_waits_through_compare_and_closed_owner_fails(tmp_path, monkeypatch):
    dense = cube()
    packed = codec.PackedVisibility.from_dense(dense)
    native.save_native_visibility(tmp_path/'native.json', packed)
    channel = native.open_native_visibility(tmp_path/'native.json')
    actual = dense.reshape(35, 7).view(np.uint32)
    entered, release, closing = threading.Event(), threading.Event(), threading.Event()
    original = compiled._compare_bits
    def held(*args):
        entered.set()
        assert release.wait(5)
        return original(*args)
    monkeypatch.setattr(compiled, '_compare_bits', held)
    def close():
        closing.set()
        channel.close()
    with ThreadPoolExecutor(2) as pool:
        comparison = pool.submit(compiled.compare_block_bits, channel, actual, 0, 35, 7)
        assert entered.wait(5)
        closed = pool.submit(close)
        assert closing.wait(5)
        assert not closed.done()
        release.set()
        assert comparison.result(timeout=10) == -1
        closed.result(timeout=10)
    assert channel._block_descriptor is None
    with pytest.raises(RuntimeError, match='closed'):
        compiled.compare_block_bits(channel, actual, 0, 35, 7)


@pytest.mark.parametrize('start,stop,patches', [(-1, 2, 7), (0, 36, 7), (0, 1, 8)])
def test_companion_range_validation_matches_decoder(start, stop, patches):
    channel = codec.PackedVisibility.from_dense(cube())
    with pytest.raises(IndexError) as original:
        compiled.decode_block(channel, start, stop, patches)
    with pytest.raises(IndexError) as candidate:
        compiled.compare_block_bits(channel, np.empty((1, 7), np.uint32), start, stop, patches)
    assert str(candidate.value) == str(original.value)


def test_comparison_source_upgrade_invalidates_persistent_cache(tmp_path):
    from pathlib import Path
    import shutil
    from test_composed_persistent_jit_cache import mutate_function
    from test_exact_persistent_jit_cache import (
        assert_loaded, assert_saved, copy_active_source, run_probe,
    )
    source = copy_active_source(tmp_path/'source')
    cache = tmp_path/'cache'
    probe = Path(__file__).resolve().parents[1]/'helpers/visibility_compare_cache_probe.py'
    original, _ = run_probe(source, cache, tmp_path/'cold', 'compare', debug=True, probe=probe)
    warm, debug = run_probe(source, cache, tmp_path/'warm', 'compare', debug=True, probe=probe)
    assert warm == original
    assert_loaded(debug, '_compare_bits')
    # Change the live binary arm, not the retained generic fallback. The probe
    # owns all-one binary patches, so masking their codes to zero must mismatch.
    mutate_function(source/'solweig_light/geometry/visibility_compiled.py', '_compare_bits',
                    b'>> (pixel & 7)) & 1', b'>> (pixel & 7)) & 0', 1, same_stamp=True)
    changed, debug = run_probe(source, cache, tmp_path/'changed', 'compare', debug=True, probe=probe)
    shutil.copytree(source, tmp_path/'relocated')
    fresh, _ = run_probe(tmp_path/'relocated', tmp_path/'fresh-cache', tmp_path/'fresh',
                         'compare', debug=True, probe=probe)
    assert changed == fresh
    assert original['result'] == -1 and changed['result'] == 0
    assert changed['qualname'] != original['qualname']
    assert_saved(debug, changed['qualname'])
