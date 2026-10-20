"""R03: ordered packed-stream aniLum accumulation.

The daytime anisotropic branch accumulates aniLum one Python plane decode per
Perez patch. The R03 route decodes the same lazy diffuse pair inside the
kernel (aplus decoder, the proven fused-kernel decoder) and keeps each
pixel's ascending patch accumulation in float32, so admitted scenes are
bitwise against the retained loop. These tests assert uint32-view equality
(loop reference computed inline, verbatim baseline order), the decline matrix
(ternary, weight profile, non-packed leaves, kill switch), and serial/parallel
kernel agreement.
"""
import numpy as np
import pytest

from solweig_light.geometry.visibility import PackedVisibility, LazyDiffVisibility
from solweig_light.geometry.visibility_native import save_native_visibility, open_native_visibility
from solweig_light.radiation.patch_radiation import anilum_packed


def scene(patches=5):
    """Packed leaf pair: binary/raw mix; NaN payloads preserved in raw mode."""
    rng = np.random.default_rng(57)
    rows, cols = 9, 13
    shadow = rng.integers(0, 2, (rows, cols, patches)).astype(np.float32)
    vegetation = rng.integers(0, 2, (rows, cols, patches)).astype(np.float32)
    vegetation[:, :, 2] = rng.normal(size=(rows, cols)).astype(np.float32)
    raw_bits = np.array([0x80000000, 0x7fc01234, 0xffc05678, 0x7f800000, 1], np.uint32)
    shadow.reshape(-1, patches)[:5, 3] = raw_bits.view(np.float32)
    vegetation.reshape(-1, patches)[:5, 4] = raw_bits.view(np.float32)
    return (PackedVisibility.from_dense(shadow),
            PackedVisibility.from_dense(vegetation))


def loop_anilum(diffuse, lv, rows, cols):
    """The retained engine loop, verbatim operand semantics."""
    aniLum = np.zeros((rows, cols), dtype=np.float32)
    for idx in range(lv.shape[0]):
        aniLum += np.multiply(diffuse[:, :, idx], lv[idx, 2])
    return aniLum


def weights(patches, seed=11, dtype=np.float32):
    rng = np.random.default_rng(seed)
    table = rng.random((patches, 3)) * 40.0
    return table.astype(dtype)


@pytest.fixture
def packed_pair():
    return scene()


def test_admitted_bitwise(packed_pair):
    shadow, vegetation = packed_pair
    diffuse = LazyDiffVisibility(shadow, vegetation)
    lv = weights(diffuse.shape[2])
    rows, cols = diffuse.shape[:2]
    packed = anilum_packed(diffuse, lv, rows * cols, parallel=False)
    assert packed is not None
    np.testing.assert_array_equal(packed.reshape(rows, cols).view('u4'),
                                  loop_anilum(diffuse, lv, rows, cols).view('u4'))


def test_parallel_serial_bitwise(packed_pair):
    shadow, vegetation = packed_pair
    diffuse = LazyDiffVisibility(shadow, vegetation)
    lv = weights(diffuse.shape[2])
    rows, cols = diffuse.shape[:2]
    parallel = anilum_packed(diffuse, lv, rows * cols, parallel=True)
    serial = anilum_packed(diffuse, lv, rows * cols, parallel=False)
    np.testing.assert_array_equal(parallel.view('u4'), serial.view('u4'))


def test_mapped_leaves_bitwise(tmp_path, packed_pair):
    shadow, vegetation = packed_pair
    paths = [tmp_path / name for name in ('shadow.json', 'vegetation.json')]
    save_native_visibility(paths[0], shadow)
    save_native_visibility(paths[1], vegetation)
    mapped = LazyDiffVisibility(open_native_visibility(paths[0]),
                                open_native_visibility(paths[1]))
    lv = weights(mapped.shape[2])
    rows, cols = mapped.shape[:2]
    packed = anilum_packed(mapped, lv, rows * cols, parallel=False)
    assert packed is not None
    np.testing.assert_array_equal(packed.reshape(rows, cols).view('u4'),
                                  loop_anilum(mapped, lv, rows, cols).view('u4'))


def test_ternary_declines_and_loop_raises_untouched():
    """Reserved ternary codes stay the Python indexer's contract: the route
    declines any ternary patch and the retained loop raises the original
    IndexError on a hand-crafted reserved code."""
    from solweig_light.geometry.visibility import _EncodedPatch
    shadow = PackedVisibility((1, 1, 1), (_EncodedPatch('ternary', b'\x03'),))
    vegetation = PackedVisibility((1, 1, 1), (_EncodedPatch('binary', b'\x00'),))
    diffuse = LazyDiffVisibility(shadow, vegetation)
    lv = weights(1)
    assert anilum_packed(diffuse, lv, 1, parallel=False) is None
    with pytest.raises(IndexError):
        loop_anilum(diffuse, lv, 1, 1)


def test_weight_profile_declines(packed_pair):
    shadow, vegetation = packed_pair
    diffuse = LazyDiffVisibility(shadow, vegetation)
    patches = diffuse.shape[2]
    rows, cols = diffuse.shape[:2]
    assert anilum_packed(diffuse, weights(patches, dtype=np.float64),
                         rows * cols, parallel=False) is None
    assert anilum_packed(diffuse, weights(patches).astype(np.int32),
                         rows * cols, parallel=False) is None
    assert anilum_packed(diffuse, weights(patches)[:, :2],
                         rows * cols, parallel=False) is None
    assert anilum_packed(diffuse, weights(patches - 1),
                         rows * cols, parallel=False) is None
    assert anilum_packed(diffuse, weights(patches), rows * cols + 1,
                         parallel=False) is None


def test_non_lazy_decline(packed_pair):
    shadow, vegetation = packed_pair
    lv = weights(shadow.shape[2])
    rows, cols = shadow.shape[:2]
    assert anilum_packed(shadow, lv, rows * cols, parallel=False) is None


def test_kill_switch(packed_pair, monkeypatch):
    shadow, vegetation = packed_pair
    diffuse = LazyDiffVisibility(shadow, vegetation)
    lv = weights(diffuse.shape[2])
    rows, cols = diffuse.shape[:2]
    monkeypatch.setenv('SOLWEIG_LIGHT_ANILUM_PACKED', '0')
    assert anilum_packed(diffuse, lv, rows * cols, parallel=False) is None
    monkeypatch.setenv('SOLWEIG_LIGHT_ANILUM_PACKED', '1')
    assert anilum_packed(diffuse, lv, rows * cols, parallel=False) is not None


def test_engine_routes_packed_on_landcover_golden(tmp_path, monkeypatch):
    """E2E engagement: one landcover tile routes every daytime aniLum sum
    through the packed stream (the census trap — goldens pass on budgets
    even when a route never fires — so the route itself is asserted)."""
    import shutil
    from pathlib import Path
    import unittest.mock as mock

    import solweig_light.runtime_memory as runtime_memory
    # Same deviation the L2 bench harness uses: cap the GDAL cache so the
    # small tmp-tree run admits on this host. Reverted by monkeypatch — a
    # bare assignment here leaked into the s03b tests downstream.
    monkeypatch.setattr(runtime_memory, 'default_gdal_cache_bytes',
                        lambda: 256 * 1024 * 1024)
    import solweig_light.radiation.patch_radiation as pr
    from solweig_light.pipeline import files_by_key, run_tile

    source = Path(__file__).resolve().parents[3] / \
        'tests/reference/optional_original_cpu/landcover/processed_inputs'
    prepared = tmp_path / 'processed_inputs'
    shutil.copytree(source, prepared)
    paths = {n: files_by_key(prepared / n)['0_0'] for n in
             ('Building_DSM', 'Trees', 'DEM', 'walls', 'aspect', 'metfiles', 'Landcover')}
    flags = {f'save_{n}': True for n in ('tmrt', 'kup', 'kdown', 'lup', 'ldown', 'shadow')}

    calls = {'n': 0}
    real = pr.anilum_packed

    def counted(*args, **kwargs):
        result = real(*args, **kwargs)
        if result is not None:
            calls['n'] += 1
        return result

    out = tmp_path / 'run'
    with mock.patch.object(pr, 'anilum_packed', counted):
        run_tile(tmp_path, prepared, '2020-07-18', '0_0', paths, flags)
    # 14 daytime steps on the July golden date; every one must engage.
    assert calls['n'] == 14


def test_mapped_descriptor_and_kernel_hold_owner_lease(tmp_path, monkeypatch):
    """A concurrent close cannot unmap bytes during descriptor or kernel use."""
    import threading
    from solweig_light.radiation import patch_radiation as pr
    from solweig_light.geometry import visibility_compiled as codec
    shadow, vegetation = scene()
    mapped = []
    for name, channel in [('shadow',shadow),('vegetation',vegetation)]:
        path=tmp_path/(name+'.json')
        save_native_visibility(path,channel)
        mapped.append(open_native_visibility(path))
    diffuse=LazyDiffVisibility(*mapped)
    real_descriptor=codec._fused_descriptor
    checked=[]
    def descriptor(channel):
        # Nonblocking acquisition from a different thread proves the owner
        # lock is already held before the borrowed descriptor is created.
        acquired=[]
        def probe():
            success=channel._lock.acquire(blocking=False)
            acquired.append(success)
            if success:channel._lock.release()
        thread=threading.Thread(target=probe)
        thread.start();thread.join(timeout=5)
        assert not thread.is_alive()
        assert acquired == [False]
        checked.append(channel)
        return real_descriptor(channel)
    monkeypatch.setattr(codec,'_fused_descriptor',descriptor)
    closer=[]
    attempted=threading.Event()
    closed=threading.Event()
    def kernel(*args):
        def close():
            attempted.set()
            mapped[0].close()
            closed.set()
        thread=threading.Thread(target=close)
        closer.append(thread);thread.start()
        assert attempted.wait(timeout=5)
        assert not closed.is_set()
        assert not mapped[0].closed
        return np.zeros(diffuse.shape[0]*diffuse.shape[1],np.float32)
    monkeypatch.setattr(pr,'_anilum_packed_serial',kernel)
    try:
        result=pr.anilum_packed(diffuse,weights(diffuse.shape[2]),
                               diffuse.shape[0]*diffuse.shape[1],parallel=False)
        assert result is not None and len(checked)==2
        closer[0].join(timeout=5)
        assert closed.is_set()
    finally:
        for thread in closer:thread.join(timeout=5)
        for channel in mapped:channel.close()
