"""P01 differential: fused ordered decode+accumulate vs the retained block-decode route.

Every comparison is exact (uint32 view) against the untouched original kernels
`_shortwave`/`_shortwave_serial` and `_longwave`/`_longwave_serial` driven by
the untouched `_shortwave_visibility_blocks`/`_block` reads.
"""
import numpy as np
import pytest

from solweig_light.geometry.visibility import (
    LazyDiffVisibility, PackedVisibility,
)
from solweig_light.geometry.visibility_compiled import decode_block
from solweig_light.geometry.visibility_native import (
    open_native_visibility, save_native_visibility,
)
from solweig_light.radiation import patch_radiation as compiled

from conftest import (
    assert_fields_bitwise, bitwise, classes, cube, define_arguments, kside_arguments,
    lcyl_arguments, lw_coefficients, packed, reserved_ternary, sw_coefficients, threads,
)

SHAPES = ((16, 16), (37, 53))


def _longwave_pair(rng, rows, cols, block_start, block_stop, parallel):
    """Old-route and fused-route longwave reductions for one pixel interval."""
    pixels = rows*cols
    sh = packed(rng, rows, cols, 153, ('binary', 'ternary', 'raw'))
    vs = packed(rng, rows, cols, 153, kinds_three)
    vb = packed(rng, rows, cols, 153, ('ternary', 'raw', 'binary'))
    coefficients = lw_coefficients(rng, 153, pixels)
    sun, shade = classes(rng, pixels, 153)
    sh_block, vs_block, vb_block = (compiled._block(channel, block_start, block_stop, 153)
                                    for channel in (sh, vs, vb))
    kernel = compiled._longwave if parallel else compiled._longwave_serial
    expected = kernel(sh_block, vs_block, vb_block, sun[block_start:block_stop],
                      shade[block_start:block_stop], coefficients['solid'], coefficients['sine'],
                      coefficients['cosine'], coefficients['directions'], coefficients['gate'],
                      coefficients['solar_gate'], coefficients['sky_down'], coefficients['sky_side'],
                      coefficients['sun_surface'], coefficients['shade_surface'],
                      coefficients['lup'][block_start:block_stop], coefficients['factor'])
    observed = compiled._longwave_fused_block(
        sh, vs, vb, block_start, block_stop, 153, sun[block_start:block_stop],
        shade[block_start:block_stop], coefficients['solid'],
        coefficients['sine'], coefficients['cosine'], coefficients['directions'],
        coefficients['gate'], coefficients['solar_gate'], coefficients['sky_down'],
        coefficients['sky_side'], coefficients['sun_surface'], coefficients['shade_surface'],
        coefficients['lup'][block_start:block_stop], coefficients['factor'], parallel)
    return expected, observed


kinds_three = ('binary', 'ternary', 'raw')


def _shortwave_pair(rng, rows, cols, block_start, block_stop, diff_lazy, parallel, box,
                    kinds=('binary', 'ternary', 'raw')):
    """Old-route and fused-route reductions for one pixel interval."""
    pixels = rows*cols
    sh = packed(rng, rows, cols, 153, kinds)
    vs = packed(rng, rows, cols, 153, kinds)
    vb = packed(rng, rows, cols, 153, kinds)
    diff = packed(rng, rows, cols, 153, kinds)
    channel = LazyDiffVisibility(sh, vs) if diff_lazy else diff
    coefficients = sw_coefficients(rng, 153)
    sun, shade = classes(rng, pixels, 153)
    sh_block, vs_block, vb_block, diff_block = compiled._shortwave_visibility_blocks(
        sh, vs, vb, channel, block_start, block_stop, 153)
    kernel = compiled._shortwave if parallel else compiled._shortwave_serial
    expected = kernel(sh_block, vs_block, vb_block, diff_block, sun[block_start:block_stop],
                      shade[block_start:block_stop], coefficients['lum'], coefficients['solid'],
                      coefficients['cosine'], coefficients['directions'], coefficients['diff_gate'],
                      coefficients['ref_gate'], coefficients['box_gate'],
                      coefficients['surface_sun'], coefficients['surface_sh'], box)
    observed = compiled._shortwave_fused_block(
        sh, vs, vb, channel, block_start, block_stop, 153, sun[block_start:block_stop],
        shade[block_start:block_stop], coefficients['lum'],
        coefficients['solid'], coefficients['cosine'], coefficients['directions'],
        coefficients['diff_gate'], coefficients['ref_gate'], coefficients['box_gate'],
        coefficients['surface_sun'], coefficients['surface_sh'], box, parallel)
    return expected, observed


@pytest.mark.parametrize('diff_lazy', [False, True], ids=['direct-diff', 'lazy-diff'])
@pytest.mark.parametrize('parallel', [False, True], ids=['serial', 'parallel'])
@pytest.mark.parametrize('box', [False, True], ids=['cylindrical', 'box'])
@pytest.mark.parametrize('block_pixels', [1, 17, 32, 128, 4096])
@pytest.mark.parametrize('shape', SHAPES)
def test_shortwave_bitwise(shape, block_pixels, box, parallel, diff_lazy):
    """SW 20 columns match bit-for-bit across blocks, gates, and diff channels."""
    rng = np.random.default_rng(hash((shape, block_pixels, box, parallel, diff_lazy)) % 2**32)
    rows, cols = shape
    pixels = rows*cols
    if block_pixels == 1 and pixels > 512:
        pytest.skip('per-pixel blocks only on the small shape')
    if block_pixels == 4096 and pixels < 512:
        pytest.skip('single-block case only on the larger shape')
    with threads(2):
        full = range(0, pixels, block_pixels)
        for start in full:
            stop = min(start+block_pixels, pixels)
            expected, observed = _shortwave_pair(rng, rows, cols, start, stop, diff_lazy, parallel, box)
            assert observed is not None
            assert expected.shape == (stop-start, 20)
            assert bitwise(expected, observed), f'block {start}:{stop} differs'


@pytest.mark.parametrize('parallel', [False, True], ids=['serial', 'parallel'])
def test_shortwave_128_square_bitwise(parallel):
    """Full 128x128 scene, 153 mixed-mode patches, one whole-scene block."""
    rng = np.random.default_rng(11)
    rows = cols = 128
    pixels = rows*cols
    with threads(2):
        expected, observed = _shortwave_pair(rng, rows, cols, 0, pixels, False, parallel, True)
        assert bitwise(expected, observed)
        expected, observed = _shortwave_pair(rng, rows, cols, 0, pixels, True, parallel, False)
        assert bitwise(expected, observed)


@pytest.mark.parametrize('parallel', [False, True], ids=['serial', 'parallel'])
@pytest.mark.parametrize('block_pixels', [1, 17, 32, 128, 4096])
@pytest.mark.parametrize('shape', SHAPES)
def test_longwave_bitwise(shape, block_pixels, parallel):
    """LW 11 columns match bit-for-bit, including the two-sweep reflected term."""
    rng = np.random.default_rng(hash((shape, block_pixels, parallel)) % 2**32)
    rows, cols = shape
    pixels = rows*cols
    if block_pixels == 1 and pixels > 512:
        pytest.skip('per-pixel blocks only on the small shape')
    if block_pixels == 4096 and pixels < 512:
        pytest.skip('single-block case only on the larger shape')
    with threads(2):
        for start in range(0, pixels, block_pixels):
            stop = min(start+block_pixels, pixels)
            expected, observed = _longwave_pair(rng, rows, cols, start, stop, parallel)
            assert observed is not None
            assert expected.shape == (stop-start, 11)
            assert bitwise(expected, observed), f'block {start}:{stop} differs'


def test_longwave_128_square_bitwise():
    """Full 128x128 longwave scene with pixel-varying Lup on one default block."""
    rng = np.random.default_rng(13)
    with threads(2):
        expected, observed = _longwave_pair(rng, 128, 128, 0, 128*128, True)
        assert bitwise(expected, observed)


def test_all_153_patches_in_mixed_modes():
    """Every patch participates; all three encodings coexist in one channel."""
    rng = np.random.default_rng(17)
    rows, cols = 16, 16
    sh = packed(rng, rows, cols, 153, kinds_three)
    assert len(sh.modes) == 153
    assert set(sh.modes) == {'binary', 'ternary', 'raw'}
    assert sum(1 for mode in sh.modes if mode == 'binary') == 51
    assert sum(1 for mode in sh.modes if mode == 'ternary') == 51
    assert sum(1 for mode in sh.modes if mode == 'raw') == 51
    with threads(2):
        expected, observed = _shortwave_pair(rng, rows, cols, 0, rows*cols, False, True, True)
        assert bitwise(expected, observed)
        expected, observed = _longwave_pair(rng, rows, cols, 0, rows*cols, True)
        assert bitwise(expected, observed)


def test_signed_zero_and_nonfinite_payloads_and_coefficients():
    """Raw -0.0/NaN/Inf payloads and nonfinite coefficients stay bit-identical."""
    rng = np.random.default_rng(19)
    rows, cols = 16, 16
    pixels = rows*cols
    kinds = ('signed_zero', 'nonfinite', 'raw')
    with threads(2):
        sh = packed(rng, rows, cols, 153, kinds)
        vs = packed(rng, rows, cols, 153, kinds)
        vb = packed(rng, rows, cols, 153, kinds)
        diff = packed(rng, rows, cols, 153, kinds)
        coefficients = sw_coefficients(rng, 153)
        coefficients['lum'] = coefficients['lum'].copy()
        coefficients['lum'][1] = np.float32(-0.0)
        coefficients['lum'][2] = np.float32('inf')
        coefficients['cosine'][3] = np.float32('nan')
        coefficients['cosine'][4] = np.float32(-0.0)
        sun, shade = classes(rng, pixels, 153)
        for box in (False, True):
            blocks = compiled._shortwave_visibility_blocks(sh, vs, vb, diff, 0, pixels, 153)
            expected = compiled._shortwave_serial(*blocks, sun, shade, coefficients['lum'],
                                                  coefficients['solid'], coefficients['cosine'],
                                                  coefficients['directions'], coefficients['diff_gate'],
                                                  coefficients['ref_gate'], coefficients['box_gate'],
                                                  coefficients['surface_sun'], coefficients['surface_sh'], box)
            observed = compiled._shortwave_fused_block(sh, vs, vb, diff, 0, pixels, 153, sun, shade,
                                                       coefficients['lum'], coefficients['solid'],
                                                       coefficients['cosine'], coefficients['directions'],
                                                       coefficients['diff_gate'], coefficients['ref_gate'],
                                                       coefficients['box_gate'], coefficients['surface_sun'],
                                                       coefficients['surface_sh'], box, True)
            assert bitwise(expected, observed)
        longwave = lw_coefficients(rng, 153, pixels)
        longwave['sky_down'][5] = np.float32('-inf')
        longwave['lup'][6] = np.float32('nan')
        longwave['lup'][7] = np.float32(-0.0)
        sh_block, vs_block, vb_block = (compiled._block(channel, 0, pixels, 153)
                                        for channel in (sh, vs, vb))
        expected = compiled._longwave_serial(sh_block, vs_block, vb_block, sun, shade,
                                             longwave['solid'], longwave['sine'], longwave['cosine'],
                                             longwave['directions'], longwave['gate'], longwave['solar_gate'],
                                             longwave['sky_down'], longwave['sky_side'],
                                             longwave['sun_surface'], longwave['shade_surface'],
                                             longwave['lup'], longwave['factor'])
        observed = compiled._longwave_fused_block(sh, vs, vb, 0, pixels, 153, sun, shade,
                                                  longwave['solid'], longwave['sine'], longwave['cosine'],
                                                  longwave['directions'], longwave['gate'], longwave['solar_gate'],
                                                  longwave['sky_down'], longwave['sky_side'],
                                                  longwave['sun_surface'], longwave['shade_surface'],
                                                  longwave['lup'], longwave['factor'], False)
        assert bitwise(expected, observed)


def test_reserved_code_contract():
    """Reserved codes raise the original error at the same block; no partial commit."""
    rng = np.random.default_rng(23)
    rows, cols = 16, 16
    block_pixels = 17
    reserved_pixel = 40  # inside the third block [34, 51)
    sh = reserved_ternary(rows, cols, 153, (reserved_pixel,))
    vs = packed(rng, rows, cols, 153, ('binary',))
    vb = packed(rng, rows, cols, 153, ('ternary',))
    diff = LazyDiffVisibility(sh, vs)
    coefficients = sw_coefficients(rng, 153)
    sun, shade = classes(rng, rows*cols, 153)
    with threads(2):
        # decode_block itself still raises the original error.
        with pytest.raises(IndexError, match='Reserved visibility code'):
            decode_block(sh, 0, rows*cols, 153)
        # Blocks before the offending one commit and stay stable across the failure.
        early = compiled._shortwave_fused_block(sh, vs, vb, diff, 0, 2*block_pixels, 153, sun, shade,
                                                coefficients['lum'], coefficients['solid'],
                                                coefficients['cosine'], coefficients['directions'],
                                                coefficients['diff_gate'], coefficients['ref_gate'],
                                                coefficients['box_gate'], coefficients['surface_sun'],
                                                coefficients['surface_sh'], True, True)
        early_again = compiled._shortwave_fused_block(sh, vs, vb, diff, 0, 2*block_pixels, 153, sun, shade,
                                                      coefficients['lum'], coefficients['solid'],
                                                      coefficients['cosine'], coefficients['directions'],
                                                      coefficients['diff_gate'], coefficients['ref_gate'],
                                                      coefficients['box_gate'], coefficients['surface_sun'],
                                                      coefficients['surface_sh'], True, True)
        assert bitwise(early, early_again)
        start = 2*block_pixels
        stop = 3*block_pixels
        with pytest.raises(IndexError, match='Reserved visibility code'):
            compiled._shortwave_fused_block(sh, vs, vb, diff, start, stop, 153, sun, shade,
                                            coefficients['lum'], coefficients['solid'],
                                            coefficients['cosine'], coefficients['directions'],
                                            coefficients['diff_gate'], coefficients['ref_gate'],
                                            coefficients['box_gate'], coefficients['surface_sun'],
                                            coefficients['surface_sh'], True, True)
        with pytest.raises(IndexError, match='Reserved visibility code'):
            compiled._shortwave_fused_block(sh, vs, vb, diff, start, stop, 153, sun, shade,
                                            coefficients['lum'], coefficients['solid'],
                                            coefficients['cosine'], coefficients['directions'],
                                            coefficients['diff_gate'], coefficients['ref_gate'],
                                            coefficients['box_gate'], coefficients['surface_sun'],
                                            coefficients['surface_sh'], True, False)
        # The old route raises the identical error for the identical interval.
        with pytest.raises(IndexError, match='Reserved visibility code'):
            compiled._shortwave_visibility_blocks(sh, vs, vb, diff, start, stop, 153)
        assert bitwise(early, early_again)


def test_reserved_code_longwave_contract():
    """The longwave preflight reproduces the reserved-code error per block."""
    rng = np.random.default_rng(29)
    rows, cols = 16, 16
    vs = reserved_ternary(rows, cols, 153, (5,))
    sh = packed(rng, rows, cols, 153, ('binary',))
    vb = packed(rng, rows, cols, 153, ('ternary',))
    coefficients = lw_coefficients(rng, 153, rows*cols)
    sun, shade = classes(rng, rows*cols, 153)
    with threads(2):
        with pytest.raises(IndexError, match='Reserved visibility code'):
            compiled._longwave_fused_block(sh, vs, vb, 0, rows*cols, 153, sun, shade,
                                           coefficients['solid'], coefficients['sine'],
                                           coefficients['cosine'], coefficients['directions'],
                                           coefficients['gate'], coefficients['solar_gate'],
                                           coefficients['sky_down'], coefficients['sky_side'],
                                           coefficients['sun_surface'], coefficients['shade_surface'],
                                           coefficients['lup'], coefficients['factor'], True)


def test_range_validation_parity():
    """Interval and patch-count violations match decode_block's error contract."""
    rng = np.random.default_rng(31)
    sh = packed(rng, 16, 16, 153, ('binary',))
    with pytest.raises(IndexError, match='Visibility block interval out of range'):
        decode_block(sh, 0, 257, 153)
    with pytest.raises(IndexError, match='Visibility block interval out of range'):
        compiled._shortwave_fused_block(sh, sh, sh, sh, 0, 257, 153,
                                        *(np.zeros((256, 153), dtype=np.bool_) for _ in range(2)),
                                        np.zeros(153, np.float32), np.zeros(153, np.float32),
                                        np.zeros(153, np.float32), np.zeros((153, 4), np.float32),
                                        np.zeros((153, 4), np.bool_), np.zeros((153, 4), np.bool_),
                                        np.zeros(153, np.bool_), np.float32(0), np.float32(0), True, True)
    with pytest.raises(IndexError, match='Visibility block interval out of range'):
        compiled._longwave_fused_block(sh, sh, sh, 0, 256, 154,
                                       *(np.zeros((256, 153), dtype=np.bool_) for _ in range(2)),
                                       np.zeros(153, np.float32), np.zeros(153, np.float32),
                                       np.zeros(153, np.float32), np.zeros((153, 4), np.float32),
                                       np.zeros((153, 4), np.bool_), np.zeros(153, np.bool_),
                                       np.zeros(153, np.float32), np.zeros(153, np.float32),
                                       np.float32(0), np.float32(0), np.zeros(256, np.float32),
                                       np.float32(0), True)


class DuckChannel:
    """Duck-typed channel driving _block's decode_pixels fallback."""

    dtype = np.dtype(np.float32)

    def __init__(self, dense):
        self.dense = dense
        self.shape = dense.shape

    def decode_pixels(self, patch, start, stop):
        return self.dense.reshape(-1, self.shape[2])[start:stop, patch]


class SubsetPackedVisibility(PackedVisibility):
    """Arbitrary PackedVisibility subclass; fusion must not admit it."""


def test_fallback_and_admission():
    """Unsupported channels return None and the retained route stays bit-identical."""
    rng = np.random.default_rng(37)
    rows, cols = 16, 16
    pixels = rows*cols
    dense = cube(rng, rows, cols, 153, kinds_three)
    duck = DuckChannel(dense)
    assert compiled._packed_leaves(duck) is None
    assert compiled._packed_leaves(PackedVisibility.from_dense(dense)) is not None
    subset = SubsetPackedVisibility((rows, cols, 153),
                                    PackedVisibility.from_dense(dense)._patches)
    assert compiled._packed_leaves(subset) is None
    dense_leaves = tuple(cube(rng, rows, cols, 153, ('binary',)) for _ in range(2))
    lazy_dense = LazyDiffVisibility(*dense_leaves)
    assert compiled._packed_leaves(lazy_dense) is None
    # Duck channels still decode through the retained _block route.
    block = compiled._block(duck, 3, 19, 153)
    reference = dense.reshape(-1, 153)[3:19, :]
    assert bitwise(block, reference)


def test_fused_route_is_opt_in(monkeypatch):
    """Default OFF: the fused route arms only under SOLWEIG_LIGHT_FUSED_RAD=1."""
    rng = np.random.default_rng(59)
    sh = packed(rng, 16, 16, 153, kinds_three)
    start, stop = 0, 32
    coefficients = sw_coefficients(np.random.default_rng(61), 153)
    sun, shade = classes(np.random.default_rng(67), 256, 153)
    lw = lw_coefficients(np.random.default_rng(71), 153, 256)
    arguments = (sh, sh, sh, sh, start, stop, 153, sun[start:stop], shade[start:stop],
                 coefficients['lum'], coefficients['solid'], coefficients['cosine'],
                 coefficients['directions'], coefficients['diff_gate'], coefficients['ref_gate'],
                 coefficients['box_gate'], coefficients['surface_sun'], coefficients['surface_sh'])
    longwave = (sh, sh, sh, start, stop, 153, sun[start:stop], shade[start:stop], lw['solid'],
                lw['sine'], lw['cosine'], lw['directions'], lw['gate'], lw['solar_gate'],
                lw['sky_down'], lw['sky_side'], lw['sun_surface'], lw['shade_surface'],
                lw['lup'], lw['factor'], True)
    monkeypatch.delenv('SOLWEIG_LIGHT_FUSED_RAD', raising=False)
    assert compiled._fused_enabled() is False
    assert compiled._shortwave_fused_block(*arguments, False, True) is None
    assert compiled._longwave_fused_block(*longwave) is None
    monkeypatch.setenv('SOLWEIG_LIGHT_FUSED_RAD', '0')
    assert compiled._fused_enabled() is False
    monkeypatch.setenv('SOLWEIG_LIGHT_FUSED_RAD', '1')
    assert compiled._fused_enabled() is True
    assert compiled._shortwave_fused_block(*arguments, False, True) is not None


def test_lazydiff_nondiffuse_channel_falls_back():
    """A lazy direct channel is never fused; only the diffuse stream may be a pair (C5-31).

    The fused kernels apply the leaf subtraction on the diffuse stream alone, so a
    LazyDiffVisibility in a direct shortwave position would silently drop the
    vegetation term. Admission must reject it and the retained route must produce
    the observed outputs bit-for-bit (the C5-31 reviewer probe).
    """
    rng = np.random.default_rng(53)
    rows, cols = 16, 16
    pixels = rows*cols
    leaf_sh = packed(rng, rows, cols, 153, kinds_three)
    leaf_vs = packed(rng, rows, cols, 153, kinds_three)
    lazy_direct = LazyDiffVisibility(leaf_sh, leaf_vs)
    assert compiled._packed_leaves(lazy_direct) is None
    assert compiled._packed_leaves(lazy_direct, allow_lazy=True) is not None
    start, stop = 5, 22
    coefficients = sw_coefficients(rng, 153)
    sun, shade = classes(rng, pixels, 153)
    arguments = (start, stop, 153, sun[start:stop], shade[start:stop], coefficients['lum'],
                 coefficients['solid'], coefficients['cosine'], coefficients['directions'],
                 coefficients['diff_gate'], coefficients['ref_gate'], coefficients['box_gate'],
                 coefficients['surface_sun'], coefficients['surface_sh'])
    lw = lw_coefficients(rng, 153, pixels)
    vb = packed(rng, rows, cols, 153, kinds_three)
    for parallel in (False, True):
        assert compiled._shortwave_fused_block(
            lazy_direct, leaf_vs, vb, leaf_sh, *arguments, False, parallel) is None
    # Negative control: the same pair in the diffuse stream stays admitted.
    assert compiled._shortwave_fused_block(
        leaf_sh, leaf_vs, vb, lazy_direct, *arguments, False, True) is not None
    assert compiled._longwave_fused_block(
        lazy_direct, leaf_vs, vb, start, stop, 153, sun[start:stop], shade[start:stop],
        lw['solid'], lw['sine'], lw['cosine'], lw['directions'], lw['gate'],
        lw['solar_gate'], lw['sky_down'], lw['sky_side'], lw['sun_surface'],
        lw['shade_surface'], lw['lup'], lw['factor'], True) is None
    with threads(2):
        for parallel in (False, True):
            values = kside_arguments(rng, rows, cols, 153, False)
            # The dense reference carries the exact content the packed routes read.
            values['shmat'] = _diff_reference(leaf_sh, leaf_vs, rows, cols)
            values['vegshmat'] = _dense_of(leaf_vs, rows, cols)
            values['vbshvegshmat'] = _dense_of(vb, rows, cols)
            packed_values = dict(values)
            packed_values['shmat'] = lazy_direct
            packed_values['vegshmat'] = leaf_vs
            packed_values['vbshvegshmat'] = vb
            packed_values['diffsh'] = PackedVisibility.from_dense(values['diffsh'])
            left = compiled.Kside_veg_v2022a(**values, block_pixels=17, parallel=parallel)
            right = compiled.Kside_veg_v2022a(**packed_values, block_pixels=17, parallel=parallel)
            assert_fields_bitwise(left, right)


def _dense_of(channel, rows, cols):
    """Full-scene dense content decode_block yields for one packed channel."""
    return decode_block(channel, 0, rows*cols, 153).reshape(rows, cols, 153)


def _diff_reference(shadow, vegetation, rows, cols):
    """Dense content decode_block yields for a LazyDiff pair: sh - (1-vs)*(1-.03)."""
    left = _dense_of(shadow, rows, cols)
    right = _dense_of(vegetation, rows, cols)
    return left - (np.float32(1) - right)*np.float32(1-.03)


def test_packed_equals_dense_end_to_end_kside():
    """Kside on packed channels (fused) equals Kside on dense channels (fallback)."""
    rng = np.random.default_rng(41)
    with threads(2):
        for parallel in (False, True):
            values = kside_arguments(rng, 16, 16, 153, False)
            # The lazy diffuse channel equals this exact elementwise expression.
            values['diffsh'] = (values['shmat']
                                - (np.float32(1) - values['vegshmat'])*np.float32(1-.03))
            packed_values = dict(values)
            for key in ('shmat', 'vegshmat', 'vbshvegshmat'):
                packed_values[key] = PackedVisibility.from_dense(values[key])
            packed_values['diffsh'] = LazyDiffVisibility(packed_values['shmat'],
                                                         packed_values['vegshmat'])
            left = compiled.Kside_veg_v2022a(**values, block_pixels=17, parallel=parallel)
            right = compiled.Kside_veg_v2022a(**packed_values, block_pixels=17, parallel=parallel)
            assert_fields_bitwise(left, right)


def test_packed_equals_dense_end_to_end_kside_nonsquare():
    """Non-square 37x53 scene exercises irregular block tails at default and odd sizes."""
    rng = np.random.default_rng(43)
    with threads(2):
        values = kside_arguments(rng, 37, 53, 153, False)
        packed_values = dict(values)
        for key in ('shmat', 'vegshmat', 'vbshvegshmat'):
            packed_values[key] = PackedVisibility.from_dense(values[key])
        packed_values['diffsh'] = PackedVisibility.from_dense(values['diffsh'])
        for block_pixels in (17, 128):
            left = compiled.Kside_veg_v2022a(**values, block_pixels=block_pixels, parallel=True)
            right = compiled.Kside_veg_v2022a(**packed_values, block_pixels=block_pixels,
                                              parallel=True)
            assert_fields_bitwise(left, right)


def test_packed_equals_dense_end_to_end_longwave():
    """define_patch_characteristics and Lcyl match across routes and thread counts."""
    rng = np.random.default_rng(47)
    with threads(2):
        for parallel in (False, True):
            values = define_arguments(rng, 16, 16, 153, False)
            packed_values = dict(values)
            for key in ('shmat', 'vegshmat', 'vbshvegshmat'):
                packed_values[key] = PackedVisibility.from_dense(values[key])
            left = compiled.define_patch_characteristics(**values, block_pixels=17,
                                                         parallel=parallel)
            right = compiled.define_patch_characteristics(**packed_values, block_pixels=17,
                                                          parallel=parallel)
            assert_fields_bitwise(left, right)
        values = lcyl_arguments(rng, 37, 53, 153, False)
        packed_values = dict(values)
        for key in ('shmat', 'vegshmat', 'vbshvegshmat'):
            packed_values[key] = PackedVisibility.from_dense(values[key])
        left = compiled.Lcyl_v2022a(**values, block_pixels=17, parallel=True)
        right = compiled.Lcyl_v2022a(**packed_values, block_pixels=17, parallel=True)
        assert_fields_bitwise(left, right)


def test_mapped_visibility_fused_route(tmp_path):
    """Mapped owners take the fused route under their locks with identical bits."""
    rng = np.random.default_rng(53)
    rows, cols = 16, 16
    pixels = rows*cols
    dense = cube(rng, rows, cols, 153, kinds_three)
    packed_channel = PackedVisibility.from_dense(dense)
    path = tmp_path/'visibility.json'
    save_native_visibility(path, packed_channel)
    with open_native_visibility(path) as mapped:
        assert compiled._packed_leaves(mapped) is not None
        coefficients = sw_coefficients(rng, 153)
        sun, shade = classes(rng, pixels, 153)
        with threads(2):
            blocks = compiled._shortwave_visibility_blocks(mapped, mapped, mapped, mapped,
                                                           0, pixels, 153)
            expected = compiled._shortwave(*blocks, sun, shade, coefficients['lum'],
                                           coefficients['solid'], coefficients['cosine'],
                                           coefficients['directions'], coefficients['diff_gate'],
                                           coefficients['ref_gate'], coefficients['box_gate'],
                                           coefficients['surface_sun'], coefficients['surface_sh'], True)
            observed = compiled._shortwave_fused_block(mapped, mapped, mapped, mapped, 0, pixels,
                                                       153, sun, shade, coefficients['lum'],
                                                       coefficients['solid'], coefficients['cosine'],
                                                       coefficients['directions'], coefficients['diff_gate'],
                                                       coefficients['ref_gate'], coefficients['box_gate'],
                                                       coefficients['surface_sun'], coefficients['surface_sh'],
                                                       True, True)
        assert bitwise(expected, observed)
    assert mapped.closed
    with pytest.raises(RuntimeError, match='Native visibility is closed'):
        decode_block(mapped, 0, pixels, 153)
    with pytest.raises(RuntimeError, match='Native visibility is closed'):
        compiled._shortwave_fused_block(mapped, mapped, mapped, mapped, 0, pixels, 153, sun, shade,
                                        coefficients['lum'], coefficients['solid'],
                                        coefficients['cosine'], coefficients['directions'],
                                        coefficients['diff_gate'], coefficients['ref_gate'],
                                        coefficients['box_gate'], coefficients['surface_sun'],
                                        coefficients['surface_sh'], True, True)
