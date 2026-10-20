import json
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pytest

from solweig_light.geometry.visibility import PackedVisibility, LazyDiffVisibility, export_visibility_npz, import_visibility_npz
from solweig_light.geometry import visibility_native as native


def fixture():
    bits = np.array([0, 0x80000000, 0x7fc00023, 0x7fa00045, 0x7f800000, 0xff800000, 0x3eaaaaab, 0x3f800000, 0x40000000], dtype=np.uint32)
    dense = np.empty((3, 3, 3), dtype=np.float32)
    dense[:, :, 0] = np.arange(9).reshape(3, 3) % 2
    dense[:, :, 1] = np.arange(9).reshape(3, 3) % 3
    dense[:, :, 2] = bits.view(np.float32).reshape(3, 3)
    return dense


def rewrite(path, change):
    value = json.loads(path.read_text())
    change(value)
    value['manifest_sha256'] = native._digest_manifest(value)
    path.write_text(json.dumps(value))


def test_roundtrip_lifetime_and_legacy(tmp_path):
    dense = fixture()
    packed = PackedVisibility.from_dense(dense)
    path = tmp_path / 'visibility.json'
    manifest = native.save_native_visibility(path, packed, max_workspace_bytes=128)
    with native.open_native_visibility(path, max_workspace_bytes=128) as mapped:
        assert isinstance(mapped, PackedVisibility)
        assert isinstance(mapped._mapping, np.memmap)
        assert not mapped._mapping.flags.writeable
        assert mapped.modes == ('binary', 'ternary', 'raw')
        assert mapped.nbytes == packed.nbytes
        plane = mapped.decode_patch(2)
        np.testing.assert_array_equal(mapped.to_dense().view(np.uint32), dense.view(np.uint32))
        for start in range(9):
            np.testing.assert_array_equal(mapped.decode_pixels(2, start, 9).view(np.uint32), dense[:, :, 2].ravel()[start:].view(np.uint32))
        with pytest.raises(TypeError):
            np.asarray(mapped)
        diff = LazyDiffVisibility(mapped, mapped)
        np.testing.assert_array_equal(diff[:, :, 0], dense[:, :, 0] - (np.float32(1) - dense[:, :, 0]) * np.float32(.97))
        legacy = tmp_path / 'legacy.npz'
        export_visibility_npz(legacy, mapped, mapped, mapped, max_workspace_bytes=128)
        imported = import_visibility_npz(legacy, max_workspace_bytes=128)
        np.testing.assert_array_equal(imported['vbshmat'].to_dense().view(np.uint32), dense.view(np.uint32))
        native.save_native_visibility(tmp_path / 'copy.json', mapped, max_workspace_bytes=128)
    assert mapped.closed
    mapped.close()
    np.testing.assert_array_equal(plane.view(np.uint32), dense[:, :, 2].view(np.uint32))
    for operation in (lambda: mapped.decode_patch(0), lambda: mapped.decode_pixels(0, 0, 1), mapped.to_dense, lambda: mapped[:, :, 0], mapped.__enter__):
        with pytest.raises(RuntimeError, match='closed'):
            operation()
    payload = tmp_path / manifest['payload']['name']
    assert np.load(payload, mmap_mode='r').dtype == np.uint8


@pytest.mark.parametrize('shape', [(0, 3, 2), (2, 0, 2), (2, 2, 0), (1, 1, 1), (1, 7, 1), (1, 8, 1), (1, 9, 1)])
def test_boundaries(tmp_path, shape):
    dense = np.zeros(shape, dtype=np.float32)
    path = tmp_path / 'v.json'
    native.save_native_visibility(path, PackedVisibility.from_dense(dense))
    with native.open_native_visibility(path) as mapped:
        np.testing.assert_array_equal(mapped.to_dense(), dense)


@pytest.mark.parametrize('change', [
    lambda m: m.update(native_version=2),
    lambda m: m.update(dtype='<f8'),
    lambda m: m.update(codebook_bits=[0, 1, 2]),
    lambda m: m['patches'][0].update(offset=1),
    lambda m: m['patches'][0].update(length=20),
    lambda m: m['patches'][0].update(mode='boolean'),
    lambda m: m['payload'].update(name='../bad.npy'),
    lambda m: m.update(shape=[True, 3, 3]),
])
def test_bad_metadata(tmp_path, change):
    path = tmp_path / 'v.json'
    native.save_native_visibility(path, PackedVisibility.from_dense(fixture()))
    rewrite(path, change)
    with pytest.raises(ValueError):
        native.open_native_visibility(path)


@pytest.mark.parametrize('kind', ['digest', 'truncate', 'missing', 'reserved', 'padding'])
def test_corruption(tmp_path, kind):
    path = tmp_path / 'v.json'
    m = native.save_native_visibility(path, PackedVisibility.from_dense(fixture()))
    payload = tmp_path / m['payload']['name']
    if kind == 'missing':
        payload.unlink()
    elif kind == 'digest':
        path.write_text(path.read_text().replace('"native_version":1', '"native_version":2'))
    else:
        payload.chmod(0o644)
        if kind == 'truncate':
            payload.write_bytes(payload.read_bytes()[:-1])
        else:
            mapping = np.load(payload, mmap_mode='r+')
            if kind == 'reserved':
                mapping[m['patches'][1]['offset']] = 3
            else:
                mapping[m['patches'][0]['length'] - 1] = 128
            mapping.flush()
            mapping._mmap.close()
            rewrite(path, lambda value: value['payload'].update(sha256=native._hash_file(payload, 128)))
    with pytest.raises((ValueError, FileNotFoundError)):
        native.open_native_visibility(path, max_workspace_bytes=128)


def test_atomic_failure_and_concurrent_tiles(tmp_path, monkeypatch):
    packed = PackedVisibility.from_dense(fixture())
    paths = [tmp_path / f'{i}.json' for i in range(4)]
    with ThreadPoolExecutor(4) as pool:
        list(pool.map(lambda p: native.save_native_visibility(p, packed, max_workspace_bytes=128), paths))
    names = [json.loads(p.read_text())['payload']['name'] for p in paths]
    assert len(set(names)) == 4
    before = paths[0].read_bytes()
    def fail(*args):
        raise OSError('interrupted')
    monkeypatch.setattr(native.os, 'replace', fail)
    with pytest.raises(OSError):
        native.save_native_visibility(paths[0], packed)
    assert paths[0].read_bytes() == before
    with native.open_native_visibility(paths[0]) as mapped:
        np.testing.assert_array_equal(mapped.to_dense().view(np.uint32), fixture().view(np.uint32))


def test_bounded_hash_reads(tmp_path, monkeypatch):
    path = tmp_path / 'v.json'
    dense = np.full((80, 80, 1), np.float32(.37))
    native.save_native_visibility(path, PackedVisibility.from_dense(dense), max_workspace_bytes=128)
    original = native._hash_file
    chunks = []
    def check(path, chunk):
        chunks.append(chunk)
        assert chunk <= 128
        return original(path, chunk)
    monkeypatch.setattr(native, '_hash_file', check)
    with native.open_native_visibility(path, max_workspace_bytes=128) as mapped:
        assert mapped.nbytes == 80 * 80 * 4
    assert chunks == [128]


def test_random_bits_and_concurrent_close(tmp_path):
    rng = np.random.default_rng(703)
    bits = rng.integers(0, 2**32, size=(17, 19, 3), dtype=np.uint32)
    dense = bits.view(np.float32)
    path = tmp_path / 'v.json'
    native.save_native_visibility(path, PackedVisibility.from_dense(dense), max_workspace_bytes=128)
    mapped = native.open_native_visibility(path, max_workspace_bytes=128)
    def read(_):
        try:
            plane = mapped.decode_patch(2)
        except RuntimeError:
            return
        np.testing.assert_array_equal(plane.view(np.uint32), bits[:, :, 2])
    with ThreadPoolExecutor(4) as pool:
        futures = [pool.submit(read, i) for i in range(30)]
        mapped.close()
        for future in futures:
            future.result()
    assert mapped.closed


def test_write_hash_is_exact_and_open_still_verifies(tmp_path, monkeypatch):
    path = tmp_path / 'v.json'
    original = native._hash_file
    calls = []
    def counted(*args):
        calls.append(args)
        return original(*args)
    monkeypatch.setattr(native, '_hash_file', counted)
    manifest = native.save_native_visibility(path, PackedVisibility.from_dense(fixture()), max_workspace_bytes=128)
    assert calls == []
    payload = tmp_path / manifest['payload']['name']
    assert manifest['payload']['sha256'] == original(payload, 128)
    with native.open_native_visibility(path, max_workspace_bytes=128):
        pass
    assert len(calls) == 1


def test_integrity_error_precedes_reserved_code_error(tmp_path):
    path = tmp_path / 'v.json'
    manifest = native.save_native_visibility(path, PackedVisibility.from_dense(fixture()))
    payload = tmp_path / manifest['payload']['name']
    payload.chmod(0o644)
    mapping = np.load(payload, mmap_mode='r+')
    mapping[manifest['patches'][1]['offset']] = 3
    mapping.flush()
    mapping._mmap.close()
    with pytest.raises(ValueError, match='integrity mismatch'):
        native.open_native_visibility(path)


@pytest.mark.parametrize('byte', range(256))
def test_vector_reserved_check_matches_scalar(byte):
    chunk = np.array([byte], dtype=np.uint8)
    assert bool(((chunk & (chunk >> 1)) & 0x55).any()) == any(
        ((byte >> shift) & 3) == 3 for shift in (0, 2, 4, 6))


def test_mapped_fused_descriptor_borrows_mapping_and_close_clears_cache(tmp_path):
    from solweig_light.geometry.visibility_compiled import _fused_descriptor
    path = tmp_path / 'v.json'
    packed = PackedVisibility.from_dense(fixture())
    native.save_native_visibility(path, packed)
    mapped = native.open_native_visibility(path)
    with mapped._lock:
        descriptor = _fused_descriptor(mapped)
        assert descriptor[0] is mapped._mapping
        assert not descriptor[0].flags.writeable
        np.testing.assert_array_equal(descriptor[0], np.frombuffer(b''.join(p.payload for p in packed._patches), np.uint8))
        assert getattr(mapped, '_block_descriptor', None) is None
        assert _fused_descriptor(mapped) is descriptor
    del descriptor
    mapped.close()
    assert mapped._fused_block_descriptor is None
    with pytest.raises(RuntimeError, match='closed'):
        _fused_descriptor(mapped)


@pytest.mark.parametrize('columns', [32, 33])
def test_binary_semantic_verification_reads_only_padding_tail(tmp_path, monkeypatch, columns):
    import builtins
    path = tmp_path / 'v.json'
    dense = np.zeros((2, columns, 3), np.float32)
    manifest = native.save_native_visibility(path, PackedVisibility.from_dense(dense), max_workspace_bytes=128)
    payload = tmp_path / manifest['payload']['name']
    mapping = np.load(payload, mmap_mode='r')
    data_offset = mapping.offset
    mapping._mmap.close()
    payload_opens = 0
    semantic_reads = []
    class Spy:
        def __init__(self, stream, semantic):
            self.stream, self.semantic = stream, semantic
        def __getattr__(self, name):
            return getattr(self.stream, name)
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return self.stream.__exit__(*args)
        def read(self, size=-1):
            position = self.stream.tell()
            result = self.stream.read(size)
            if self.semantic and position >= data_offset:
                semantic_reads.append((size, len(result)))
            return result
    def watched(filename, *args, **kwargs):
        nonlocal payload_opens
        stream = builtins.open(filename, *args, **kwargs)
        if filename == payload:
            payload_opens += 1
            return Spy(stream, payload_opens == 2)
        return stream
    monkeypatch.setattr(native, 'open', watched, raising=False)
    with native.open_native_visibility(path, max_workspace_bytes=128):
        pass
    assert payload_opens == 2  # Independent complete hash, then NPY layout.
    assert semantic_reads == ([(1, 1)] * 3 if columns == 33 else [])
