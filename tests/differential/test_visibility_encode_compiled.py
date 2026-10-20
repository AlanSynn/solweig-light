"""Byte-for-byte codec-v1 proof; compiler-only admission is deliberately narrow."""
import warnings
import os
from pathlib import Path

import numpy as np
import pytest

from solweig_light.geometry.visibility import VisibilityBuilder
from solweig_light.geometry.visibility_encode import try_encode_native_f32, _encode_bits


def reference(plane):
    """Independent NumPy bit encoder, not a float-value comparison."""
    bits=plane.view(np.uint32).reshape(-1)
    valid=(bits==0)|(bits==0x3f800000)|(bits==0x40000000)
    if not valid.all():
        return 'raw',bits.astype('<u4',copy=False).tobytes()
    if not np.any(bits==0x40000000):
        return 'binary',np.packbits(bits==0x3f800000,bitorder='little').tobytes()
    codes=np.zeros(bits.size,dtype=np.uint8)
    codes[bits==0x3f800000]=1
    codes[bits==0x40000000]=2
    padded=np.zeros((codes.size+3)//4*4,dtype=np.uint8)
    padded[:codes.size]=codes
    packed=padded[::4]|(padded[1::4]<<2)|(padded[2::4]<<4)|(padded[3::4]<<6)
    return 'ternary',packed.tobytes()


def assert_encoding(plane):
    before=plane.tobytes()
    writeable=plane.flags.writeable
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        encoded=try_encode_native_f32(plane)
    assert encoded==reference(plane)
    assert plane.tobytes()==before and plane.flags.writeable==writeable
    builder=VisibilityBuilder((*plane.shape,1),max_workspace_bytes=128)
    builder.append(plane)
    packed=builder.finish()
    assert (packed._patches[0].mode,packed._patches[0].payload)==encoded
    np.testing.assert_array_equal(packed.decode_patch(0).view(np.uint32),plane.view(np.uint32))
    width={'binary':1,'ternary':2}.get(encoded[0])
    if width and plane.size*width%8:
        assert encoded[1][-1]>>(plane.size*width%8)==0


@pytest.mark.parametrize('pixels',[0,1,2,3,4,7,8,9,15,16,17,31,32,33,65])
@pytest.mark.parametrize('mode',['binary','ternary'])
def test_exact_codewords_and_every_byte_tail(pixels,mode):
    codes=np.array([0,0x3f800000] if mode=='binary' else [0x40000000,0,0x3f800000],dtype=np.uint32)
    bits=np.resize(codes,pixels).reshape(1,pixels)
    assert_encoding(bits.view(np.float32))


@pytest.mark.parametrize('shape',[(0,7),(3,0),(4,9),(1,257)])
def test_empty_and_random_codebook_planes(shape):
    rng=np.random.default_rng(928)
    bits=rng.choice(np.array([0,0x3f800000,0x40000000],dtype=np.uint32),size=shape)
    assert_encoding(bits.view(np.float32))


@pytest.mark.parametrize('word',[0x80000000,0x7f800000,0xff800000,0x7fc00001,
                                0xffc01234,0x7f800001,0xff800001,0x00000001,0x3f000000])
@pytest.mark.parametrize('position',[0,16])
def test_raw_signed_zero_infinities_signaling_nan_payload_and_subnormal(word,position):
    bits=np.resize(np.array([0,0x3f800000,0x40000000],dtype=np.uint32),17)
    bits[position]=np.uint32(word)
    plane=bits.reshape(1,-1).view(np.float32)
    assert_encoding(plane)
    assert try_encode_native_f32(plane)[0]=='raw'


def test_random_raw_bits_are_immutable_and_never_quiet_nan():
    rng=np.random.default_rng(107)
    bits=rng.integers(0,2**32,size=(7,39),dtype=np.uint32)
    plane=bits.view(np.float32)
    plane.flags.writeable=False
    assert_encoding(plane)
    plane=bits.copy().view(np.float32)
    result=try_encode_native_f32(plane)
    plane.fill(0)
    assert result==('raw',bits.astype('<u4',copy=False).tobytes())


@pytest.mark.parametrize('kind',['transpose','step','fortran','subclass','non_native','float64','one_dimensional','list'])
def test_unsupported_inputs_decline_without_coercion(kind):
    source=np.arange(24,dtype=np.float32).reshape(4,6)
    if kind=='transpose':plane=source.T
    elif kind=='step':plane=source[:,::2]
    elif kind=='fortran':plane=np.asfortranarray(source)
    elif kind=='subclass':
        class Subclass(np.ndarray):pass
        plane=source.view(Subclass)
    elif kind=='non_native':plane=source.astype(np.dtype(np.float32).newbyteorder('S'))
    elif kind=='float64':plane=source.astype(np.float64)
    elif kind=='one_dimensional':plane=source.reshape(-1)
    else:plane=source.tolist()
    assert try_encode_native_f32(plane) is None


def test_native_contiguous_offset_view_uses_source_bits_without_owning_input():
    source=np.resize(np.array([0,0x3f800000,0x40000000],dtype=np.uint32),50)
    plane=source[1:46].reshape(5,9).view(np.float32)
    assert not plane.flags.owndata and plane.flags.c_contiguous
    assert_encoding(plane)
    assert '__jitcache_' in _encode_bits.py_func.__qualname__
    assert _encode_bits.targetoptions['fastmath'] is False


@pytest.mark.parametrize('preserve_stat', [False, True])
@pytest.mark.parametrize('helper_name', ['visibility_encode.py', 'visibility_compiled.py'])
def test_helper_source_content_rekeys_geometry_and_shared_recipe(tmp_path, monkeypatch, preserve_stat, helper_name):
    """Code bytes, including same-size/mtime changes, invalidate both routes."""
    from solweig_light import identities
    from solweig_light.cache.geometry import GeometryStore
    from solweig_light.geometry.recipe import RECIPE_FILES, numerical_geometry_recipe

    prepared = (Path(__file__).resolve().parents[2]
                / 'tests/reference/small_original_cpu/scene/processed_inputs')
    paths = {name: next((prepared / name).glob('*.tif'))
             for name in ('Building_DSM', 'Trees', 'DEM')}
    initial = identities.geometry_identity(paths, 2)
    encoder_name = 'geometry/' + helper_name
    assert encoder_name in initial['implementation']
    package = tmp_path / 'package'
    for name in set(initial['implementation']) | set(RECIPE_FILES):
        target = package / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((identities.PACKAGE / name).read_bytes())
    monkeypatch.setattr(identities, 'PACKAGE', package)
    store = GeometryStore(tmp_path / 'cache')
    old_geometry = store.key_for(identities.geometry_identity(paths, 2))
    old_recipe = numerical_geometry_recipe(paths, 2)
    encoder = package / encoder_name
    old_stat = encoder.stat()
    content = encoder.read_bytes()
    # A one-byte source mutation keeps length equal for either helper.
    changed = bytes([content[0] ^ 1]) + content[1:]
    assert changed != content and len(changed) == len(content)
    encoder.write_bytes(changed)
    if preserve_stat:
        os.utime(encoder, ns=(old_stat.st_atime_ns, old_stat.st_mtime_ns))
        assert encoder.stat().st_size == old_stat.st_size
        assert encoder.stat().st_mtime_ns == old_stat.st_mtime_ns
    assert store.key_for(identities.geometry_identity(paths, 2)) != old_geometry
    new_recipe = numerical_geometry_recipe(paths, 2)
    assert new_recipe.digest != old_recipe.digest
    assert new_recipe.native_key(store) != old_recipe.native_key(store)
