"""Lossless bounded export through the existing compiled block decoder."""
from concurrent.futures import ThreadPoolExecutor
import threading
import weakref

import numpy as np
import pytest

from solweig_light.geometry import visibility as codec
from solweig_light.geometry import visibility_compiled as compiled
from solweig_light.geometry import visibility_native as native


class Segments:
    def __init__(self, channel):
        self.channel, self.shape, self.dtype = channel, channel.shape, channel.dtype
    def decode_pixels(self, *args):
        return self.channel.decode_pixels(*args)


def cube(shape):
    bits = np.array([0, 0x80000000, 0x7fc00023, 0x7fa00045,
                     0x7f800000, 0xff800000, 0x3eaaaaab,
                     0x3f800000, 0x40000000], np.uint32)
    dense = np.resize(bits, shape).view(np.float32)
    dense[:, :, 0] = np.indices(shape[:2]).sum(axis=0) % 2
    if shape[2] > 1:
        dense[:, :, 1] = np.indices(shape[:2]).sum(axis=0) % 3
    return dense


@pytest.mark.parametrize('patches,budget,shape2', [(7, 128, (5, 7)), (153, 4096, (11, 13)),
                                                  (609, 16384, (11, 13)), (153, 1024*1024, (41, 43))])
@pytest.mark.parametrize('mapped', [False, True])
def test_archive_bytes_match_retained_export_and_descriptors_borrow(tmp_path, patches, budget, shape2, mapped):
    dense = cube((*shape2, patches))
    # Endian-derived raw planes must retain every float32 payload bit.
    big = dense.view(np.uint32).astype('>u4').view('>f4')
    packed = codec.PackedVisibility.from_dense(big)
    channel = packed
    if mapped:
        native.save_native_visibility(tmp_path/'native.json', packed)
        channel = native.open_native_visibility(tmp_path/'native.json')
    reference, candidate = tmp_path/'retained.npz', tmp_path/'compiled.npz'
    codec.export_visibility_npz(reference, *[Segments(channel)]*3, max_workspace_bytes=budget)
    stats = codec.export_visibility_npz(candidate, *[channel]*3, max_workspace_bytes=budget)
    assert candidate.read_bytes() == reference.read_bytes()
    assert stats['conservative_peak_numeric_workspace_bytes'] <= budget
    descriptor = channel._block_descriptor
    assert descriptor[1].nbytes == patches
    assert getattr(channel, '_fused_block_descriptor', None) is None
    # The typed list stores array descriptors, never a copy of payload bytes.
    for index, patch in enumerate(channel._patches):
        source = np.frombuffer(patch.payload, np.uint8)
        assert np.shares_memory(descriptor[0][index], source)
    if mapped:
        channel.close()
    with np.load(candidate, allow_pickle=False) as arrays:
        assert arrays.files == list(codec.LEGACY_MEMBERS)
        for name in codec.LEGACY_MEMBERS:
            np.testing.assert_array_equal(arrays[name].view(np.uint32), dense.view(np.uint32))


def test_mode_bytes_and_decoded_blocks_fit_workspace_without_overlap(tmp_path, monkeypatch):
    channels = [codec.PackedVisibility.from_dense(cube((11, 13, 5))) for _ in range(3)]
    original = compiled.decode_block
    previous = []
    calls = []
    budget = 512
    def checked(channel, start, stop, patches):
        assert all(reference() is None for reference in previous)
        result = original(channel, start, stop, patches)
        assert result.nbytes + 3*patches + (stop-start)*64 <= budget
        previous.append(weakref.ref(result))
        calls.append((start, stop))
        return result
    monkeypatch.setattr(compiled, 'decode_block', checked)
    stats = codec.export_visibility_npz(tmp_path/'v.npz', *channels, max_workspace_bytes=budget)
    assert calls and len(calls) > 3
    assert sum(channel._block_descriptor[1].nbytes for channel in channels) == 15
    assert stats['conservative_peak_numeric_workspace_bytes'] <= budget


def test_tiny_budget_keeps_original_segment_path(tmp_path, monkeypatch):
    channel = codec.PackedVisibility.from_dense(cube((2, 3, 41)))
    def forbidden(*args):
        pytest.fail('insufficient mode/block workspace must keep the retained path')
    monkeypatch.setattr(compiled, 'decode_block', forbidden)
    stats = codec.export_visibility_npz(tmp_path/'v.npz', *[channel]*3, max_workspace_bytes=128)
    assert getattr(channel, '_block_descriptor', None) is None
    assert stats['conservative_peak_numeric_workspace_bytes'] <= 128


def test_big_endian_host_gate_keeps_retained_path(tmp_path, monkeypatch):
    dense = cube((3, 5, 7))
    channel = codec.PackedVisibility.from_dense(dense)
    monkeypatch.setattr(codec.np, 'little_endian', False)
    def forbidden(*args):
        pytest.fail('big-endian hosts must retain canonical little-endian export')
    monkeypatch.setattr(compiled, 'decode_block', forbidden)
    path = tmp_path/'v.npz'
    codec.export_visibility_npz(path, *[channel]*3)
    with np.load(path) as arrays:
        for name in codec.LEGACY_MEMBERS:
            np.testing.assert_array_equal(arrays[name].view(np.uint32), dense.view(np.uint32))


def test_exact_type_gate_keeps_subclass_override_and_atomic_failure(tmp_path):
    class Interrupted(codec.PackedVisibility):
        def decode_pixels(self, *args):
            raise RuntimeError('subclass override')
    packed = codec.PackedVisibility.from_dense(cube((3, 5, 7)))
    channel = Interrupted(packed.shape, packed._patches)
    path = tmp_path/'v.npz'
    path.write_bytes(b'previous')
    with pytest.raises(RuntimeError, match='subclass override'):
        codec.export_visibility_npz(path, *[channel]*3)
    assert path.read_bytes() == b'previous'
    assert list(tmp_path.iterdir()) == [path]


def test_reserved_error_replays_original_before_closed_later_channel(tmp_path):
    bad = codec.PackedVisibility((1, 1, 1), (codec._EncodedPatch('ternary', b'\x03'),))
    good = codec.PackedVisibility.from_dense(np.zeros((1, 1, 1), np.float32))
    native.save_native_visibility(tmp_path/'native.json', good)
    closed = native.open_native_visibility(tmp_path/'native.json')
    closed.close()
    reference, candidate = tmp_path/'retained.npz', tmp_path/'compiled.npz'
    with pytest.raises(IndexError) as old:
        codec.export_visibility_npz(reference, Segments(bad), Segments(closed), Segments(good))
    candidate.write_bytes(b'previous')
    with pytest.raises(IndexError) as new:
        codec.export_visibility_npz(candidate, bad, closed, good)
    assert str(new.value) == str(old.value)
    assert new.value.__context__ is None
    assert candidate.read_bytes() == b'previous'
    assert not reference.exists()
    assert not list(tmp_path.glob('.compiled.npz.*'))


@pytest.mark.parametrize('level', [1, 3, 6])
def test_compiled_failure_preserves_previous_archive(tmp_path, monkeypatch, level):
    monkeypatch.setattr(codec, '_LEGACY_NPZ_COMPRESSION_LEVEL', level)
    channel = codec.PackedVisibility.from_dense(cube((11, 13, 5)))
    path = tmp_path/'v.npz'
    path.write_bytes(b'previous')
    original = compiled.decode_block
    calls = []
    def interrupted(*args):
        calls.append(1)
        if len(calls) == 2:
            raise RuntimeError('compiled interruption')
        return original(*args)
    monkeypatch.setattr(compiled, 'decode_block', interrupted)
    with pytest.raises(RuntimeError, match='compiled interruption'):
        codec.export_visibility_npz(path, *[channel]*3, max_workspace_bytes=512)
    assert path.read_bytes() == b'previous'
    assert list(tmp_path.iterdir()) == [path]


def test_mapped_close_waits_for_compiled_read_and_owned_block_survives(tmp_path, monkeypatch):
    dense = cube((3, 5, 7))
    packed = codec.PackedVisibility.from_dense(dense)
    native.save_native_visibility(tmp_path/'native.json', packed)
    channel = native.open_native_visibility(tmp_path/'native.json')
    entered, release, closing = threading.Event(), threading.Event(), threading.Event()
    original = compiled._decode
    def held(*args):
        entered.set()
        assert release.wait(5)
        return original(*args)
    monkeypatch.setattr(compiled, '_decode', held)
    def close():
        closing.set()
        channel.close()
    # Only the first member borrows this owner; the others use heap channels.
    path = tmp_path/'v.npz'
    with ThreadPoolExecutor(2) as pool:
        exported = pool.submit(codec.export_visibility_npz, path, channel, packed, packed)
        assert entered.wait(5)
        closed = pool.submit(close)
        assert closing.wait(5)
        assert not closed.done()
        release.set()
        exported.result(timeout=10)
        closed.result(timeout=10)
    assert channel.closed
    with np.load(path) as arrays:
        np.testing.assert_array_equal(arrays['shadowmat'].view(np.uint32), dense.view(np.uint32))


def test_mixed_custom_channels_keep_original_chunk_calls(tmp_path, monkeypatch):
    dense = cube((11, 13, 5))
    packed = codec.PackedVisibility.from_dense(dense)
    class Traced(Segments):
        def __init__(self, channel):
            super().__init__(channel)
            self.calls = []
        def decode_pixels(self, patch, start, stop):
            self.calls.append((patch, start, stop))
            return super().decode_pixels(patch, start, stop)
    custom = Traced(packed)
    def forbidden(*args):
        pytest.fail('a mixed custom invocation must keep its complete retained path')
    monkeypatch.setattr(compiled, 'decode_block', forbidden)
    budget = 512
    codec.export_visibility_npz(tmp_path/'v.npz', packed, custom, packed, max_workspace_bytes=budget)
    pixel_chunk = budget // (4*dense.shape[2]+64)
    assert custom.calls == [(patch, start, min(143, start+pixel_chunk))
                            for start in range(0, 143, pixel_chunk)
                            for patch in range(5)]


@pytest.mark.parametrize('level', [None, 1, 3, 6])
def test_production_compression_default_and_private_explicit_levels(tmp_path, monkeypatch, level):
    if level is not None:
        monkeypatch.setattr(codec, '_LEGACY_NPZ_COMPRESSION_LEVEL', level)
    expected = 3 if level is None else level
    original_zip = codec.zipfile.ZipFile
    observed = []
    class ObservedZipFile(original_zip):
        def __init__(self, file, mode='r', *args, **kwargs):
            if mode == 'w':
                observed.append((kwargs.get('compression'), kwargs.get('compresslevel')))
            super().__init__(file, mode, *args, **kwargs)
    monkeypatch.setattr(codec.zipfile, 'ZipFile', ObservedZipFile)
    dense = cube((11, 13, 7))
    channel = codec.PackedVisibility.from_dense(dense)
    path = tmp_path/'v.npz'
    codec.export_visibility_npz(path, channel, channel, channel)
    assert observed == [(codec.zipfile.ZIP_DEFLATED, expected)]
    # Independent consumer validates every header, exact float32 bit and CRC.
    assert codec._compare_visibility_npz(path, dict.fromkeys(codec.LEGACY_MEMBERS, channel), shape=dense.shape) is None
    with original_zip(path) as archive:
        assert archive.namelist() == [name+'.npy' for name in codec.LEGACY_MEMBERS]
        assert all(info.compress_type == codec.zipfile.ZIP_DEFLATED for info in archive.infolist())
    with np.load(path, allow_pickle=False) as arrays:
        for name in codec.LEGACY_MEMBERS:
            np.testing.assert_array_equal(arrays[name].view(np.uint32), dense.view(np.uint32))
