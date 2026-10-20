"""Exact bounded legacy NPZ comparisons, including accepted alternate layouts."""
import io
import zipfile

import numpy as np
import pytest

from solweig_light.geometry.visibility import PackedVisibility, LEGACY_MEMBERS, _compare_visibility_npz


def cube():
    bits = np.array([0, 0x80000000, 0x7fc00023, 0x7fa00045, 0x7f800000,
                     0xff800000, 0x3eaaaaab, 0x3f800000, 0x40000000], dtype=np.uint32)
    return np.resize(bits, (3, 5, 7)).view(np.float32)


def archive(path, dense, *, fortran=False, endian='<', version=(1, 0), bad=None):
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as output:
        for name in LEGACY_MEMBERS:
            values = np.array(dense, dtype=endian+'f4', order='F' if fortran else 'C')
            if bad == 'bits' and name == 'vegshadowmat':
                values.view(endian+'u4')[0, 1, 2] ^= np.uint32(1)
            stream = io.BytesIO()
            np.lib.format.write_array(stream, values, version=version)
            data = stream.getvalue()
            if bad == 'length' and name == 'shadowmat':
                data += b'bad'
            output.writestr(name+'.npy', data)
        if bad == 'extra':
            output.writestr('extra', b'')


@pytest.mark.parametrize('budget', [128, 1024, 1024*1024])
@pytest.mark.parametrize('fortran,endian,version', [(False, '<', (1, 0)), (False, '>', (2, 0)),
                                                    (True, '<', (1, 0)), (True, '>', (2, 0))])
def test_exact_bits_and_alternate_layouts(tmp_path, budget, fortran, endian, version):
    dense = cube()
    packed = PackedVisibility.from_dense(dense)
    path = tmp_path / 'v.npz'
    archive(path, dense, fortran=fortran, endian=endian, version=version)
    assert _compare_visibility_npz(path, dict.fromkeys(LEGACY_MEMBERS, packed),
                                   shape=dense.shape, max_workspace_bytes=budget) is None


@pytest.mark.parametrize('fortran', [False, True])
@pytest.mark.parametrize('bad', ['bits', 'length', 'extra'])
def test_rejects_changed_bits_and_schema(tmp_path, fortran, bad):
    dense = cube()
    path = tmp_path / 'v.npz'
    archive(path, dense, fortran=fortran, bad=bad)
    channels = dict.fromkeys(LEGACY_MEMBERS, PackedVisibility.from_dense(dense))
    if bad == 'bits':
        assert 'values differ' in _compare_visibility_npz(path, channels, shape=dense.shape, max_workspace_bytes=128)
    else:
        with pytest.raises(ValueError):
            _compare_visibility_npz(path, channels, shape=dense.shape, max_workspace_bytes=128)


def test_crc_error_precedes_deferred_value_mismatch(tmp_path):
    dense = cube()
    path = tmp_path / 'v.npz'
    # Stored members let us corrupt a later member without changing its ZIP CRC.
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_STORED) as output:
        for name in LEGACY_MEMBERS:
            stream = io.BytesIO()
            np.lib.format.write_array(stream, dense)
            output.writestr(name+'.npy', stream.getvalue())
    with zipfile.ZipFile(path) as source:
        member = source.getinfo('vegshadowmat.npy')
        offset = member.header_offset + 30 + len(member.filename.encode()) + len(member.extra)
    data = bytearray(path.read_bytes())
    data[offset+member.file_size-1] ^= 1
    path.write_bytes(data)
    changed = dense.copy()
    changed.view(np.uint32)[0, 0, 0] ^= 1
    channels = dict.fromkeys(LEGACY_MEMBERS, PackedVisibility.from_dense(changed))
    with pytest.raises(zipfile.BadZipFile, match='CRC'):
        _compare_visibility_npz(path, channels, shape=dense.shape, max_workspace_bytes=128)


def test_reads_once_and_never_repacks_standard_member(tmp_path, monkeypatch):
    dense = cube()
    path = tmp_path / 'v.npz'
    archive(path, dense)
    packed = PackedVisibility.from_dense(dense)
    def forbidden(*args, **kwargs):
        pytest.fail('standard C-order comparison must not repack or materialize a cube')
    monkeypatch.setattr(PackedVisibility, 'from_dense', forbidden)
    monkeypatch.setattr(PackedVisibility, 'to_dense', forbidden)
    reads = []
    original = zipfile.ZipExtFile.read
    def bounded(stream, size=-1):
        assert 0 <= size <= 128
        reads.append(size)
        return original(stream, size)
    monkeypatch.setattr(zipfile.ZipExtFile, 'read', bounded)
    assert _compare_visibility_npz(path, dict.fromkeys(LEGACY_MEMBERS, packed),
                                   shape=dense.shape, max_workspace_bytes=128) is None
    assert reads


@pytest.mark.parametrize('index,mask', [(0, 0x80000000), (2, 0x00000001), (3, 0x00000001)])
def test_signed_zero_and_nan_payload_mismatches_are_detected(tmp_path, index, mask):
    dense = cube()
    path = tmp_path / 'v.npz'
    archive(path, dense)
    changed = dense.copy()
    changed.view(np.uint32).flat[index] ^= np.uint32(mask)
    channels = dict.fromkeys(LEGACY_MEMBERS, PackedVisibility.from_dense(changed))
    assert 'values differ' in _compare_visibility_npz(path, channels, shape=dense.shape)
