#SOLWEIG-GPU: GPU-accelerated SOLWEIG model for urban thermal comfort simulation
#Copyright (C) 2022–2025 Harsh Kamath and Naveen Sudharsan
import pytest
pytest.skip(
    'archived with the N8 native row and qualification machinery '
    '(n8_32 selection closed N9 F3 NATIVE_LOSS; archived at N9 F4 closed_cpu_only): research copies preserved under '
    'experiments/optimization_v8/native_dispatch/',
    allow_module_level=True)

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
"""N8-13 admission guards: guard-for-guard mirror of lw_native.primary
(:169-219) in the AoSoA domain, the pinned 0-d reflection_factor decision,
the post-launch NativeExecutionError contract, and the generation's
recorded ISA/FP-operation audit facts.

Every rejection must be UnsupportedInput (the pre-launch decline signal)
and must happen BEFORE any native work; only post-launch failures of an
admitted call are NativeExecutionError, which is never caught anywhere.
"""
import json

import numpy as np
import pytest
from native_test_helpers import (F32, adversarial_inputs, run_native,
                                 to_aosoa)

from solweig_light._native_dispatch import lw_native_aosoa
from solweig_light._native_dispatch.lw_native_aosoa import (NativeArtifactError, NativeExecutionError,
                             UnsupportedInput, primary_aosoa)

B, P = 9, 5          # one full gang + a 1-lane tail gang


@pytest.fixture()
def feed():
    args = adversarial_inputs(B, P, seed=99)
    return to_aosoa(args, B)


def call(f, B=B, out=None, **over):
    kw = dict(f)
    kw.update(over)
    return primary_aosoa(
        kw['sh'], kw['vs'], kw['vb'], kw['sun'], kw['shade'],
        kw['solid'], kw['sine'], kw['cosine'], kw['directions'],
        kw['gate'], kw['solar_gate'], kw['sky_down'], kw['sky_side'],
        kw['surface_sun'], kw['surface_sh'], kw['lup'],
        kw['reflection_factor'], B, out=out)


def test_admitted_call_runs(feed, generation_dir):
    out = call(feed)
    assert out.shape == (B, 7) and out.dtype == F32


# ---------------------------------------------------------------------------
# Payload shape/dtype/stride guards (the AoSoA delta of the sh/vs/vb and
# sun/shade guards; everything else mirrors lw_native guard-for-guard).
# ---------------------------------------------------------------------------

def test_sh_not_ndarray(feed, generation_dir):
    bad = dict(feed); bad['sh'] = feed['sh'].tolist()
    with pytest.raises(UnsupportedInput, match='sh'):
        call(bad)


def test_sh_bad_dtype(feed, generation_dir):
    for dtype in (np.float64, np.int32, np.uint16):
        bad = dict(feed)
        bad['sh'] = feed['sh'].astype(dtype)
        with pytest.raises(UnsupportedInput, match='sh'):
            call(bad)


def test_raw_uint32_payload_rejected_with_guidance(feed, generation_dir):
    """N8-11 review note N6: the bound consumer contract is the float32
    view; the raw uint32 producer block is declined pre-launch with the
    view instruction (bit-preserving narrowing, not an arithmetic change)."""
    bad = dict(feed)
    bad['sh'] = feed['sh'].view(np.uint32)
    with pytest.raises(UnsupportedInput,
                       match=r'view\(np\.float32\).*note N6'):
        call(bad)


def test_sh_dense_2d_rejected(feed, generation_dir):
    """The dense [B,P] domain of the B7 adapter is NOT this adapter's."""
    bad = dict(feed)
    bad['sh'] = np.zeros((B, P), F32)
    bad['vs'] = np.zeros((B, P), F32)
    bad['vb'] = np.zeros((B, P), F32)
    bad['sun'] = np.zeros((B, P), np.bool_)
    bad['shade'] = np.zeros((B, P), np.bool_)
    with pytest.raises(UnsupportedInput, match='ndim'):
        call(bad)


def test_sh_wrong_lane_width(feed, generation_dir):
    bad = dict(feed)
    for name in ('sh', 'vs', 'vb'):
        bad[name] = np.zeros((1, P, 7), F32)
    for name in ('sun', 'shade'):
        bad[name] = np.zeros((1, P, 7), np.bool_)
    with pytest.raises(UnsupportedInput, match='lane width'):
        call(bad, B=7)


def test_sh_non_contiguous(feed, generation_dir):
    bad = dict(feed)
    bad['sh'] = feed['sh'][::-1]           # negative first-axis stride view
    with pytest.raises(UnsupportedInput, match='C-contiguous'):
        call(bad)
    bad = dict(feed)
    bad['vs'] = np.ascontiguousarray(feed['vs']).transpose(1, 0, 2)
    with pytest.raises(UnsupportedInput, match='vs'):
        call(bad)


def test_gang_count_must_match_rows(feed, generation_dir):
    with pytest.raises(UnsupportedInput, match='gangs'):
        call(feed, B=B + 8)                 # arrays hold 2 gangs, B wants 3
    with pytest.raises(UnsupportedInput, match='gangs'):
        call(feed, B=B - 1)                 # ceil(8/8)=1 != 2


def test_patch_domain(feed, generation_dir):
    dense = adversarial_inputs(8, 610, seed=4)
    over = to_aosoa(dense, 8)
    with pytest.raises(UnsupportedInput, match='outside admitted'):
        call(over, B=8)
    zero_patch = dict(feed)
    for name in ('sh', 'vs', 'vb'):
        zero_patch[name] = np.zeros((1, 0, 8), F32)
    for name in ('sun', 'shade'):
        zero_patch[name] = np.zeros((1, 0, 8), np.bool_)
    with pytest.raises(UnsupportedInput, match='outside admitted'):
        call(zero_patch, B=8)


def test_row_count_type_guard(feed, generation_dir):
    for bad_B in (8.0, np.float64(8), True, '8', None):
        with pytest.raises(UnsupportedInput, match='B'):
            call(feed, B=bad_B)
    with pytest.raises(UnsupportedInput, match='negative'):
        call(feed, B=-1)


def test_zero_rows_early_return(feed, generation_dir):
    dense = adversarial_inputs(0, 3, seed=5)
    empty = to_aosoa(dense, 0)
    out = call(empty, B=0)
    assert out.shape == (0, 7) and out.dtype == F32
    # B=0 with nonempty arrays is a gang-count violation, not a silent pass
    with pytest.raises(UnsupportedInput, match='gangs'):
        call(feed, B=0)


def test_vs_vb_shape_mismatch(feed, generation_dir):
    bad = dict(feed)
    bad['vs'] = np.zeros((1, P, 8), F32)
    with pytest.raises(UnsupportedInput, match='vs'):
        call(bad)
    bad = dict(feed)
    bad['vb'] = np.zeros((2, P + 1, 8), np.float32)   # right G, wrong P
    with pytest.raises(UnsupportedInput, match='vb'):
        call(bad)


def test_sun_shade_guards(feed, generation_dir):
    bad = dict(feed)
    bad['sun'] = feed['sun'].view(np.uint8)        # dtype, not bool
    with pytest.raises(UnsupportedInput, match='sun'):
        call(bad)
    bad = dict(feed)
    bad['shade'] = feed['shade'].astype(F32)
    with pytest.raises(UnsupportedInput, match='shade'):
        call(bad)
    bad = dict(feed)
    bad['sun'] = feed['sun'][::-1]
    with pytest.raises(UnsupportedInput, match='sun'):
        call(bad)


def test_solid_sine_cosine_guards(feed, generation_dir):
    bad = dict(feed); bad['solid'] = feed['solid'].astype(np.float64)
    with pytest.raises(UnsupportedInput, match='solid'):
        call(bad)
    bad = dict(feed); bad['sine'] = feed['sine'][:-1]
    with pytest.raises(UnsupportedInput, match='sine'):
        call(bad)
    bad = dict(feed)
    bad['cosine'] = np.zeros(2 * P, F32)[::2]
    with pytest.raises(UnsupportedInput, match='cosine'):
        call(bad)


def test_solar_gate_guard(feed, generation_dir):
    bad = dict(feed)
    bad['solar_gate'] = np.zeros(2 * P, np.bool_)[::2]
    with pytest.raises(UnsupportedInput, match='solar_gate'):
        call(bad)
    bad = dict(feed)
    bad['solar_gate'] = feed['solar_gate'].astype(np.uint8)
    with pytest.raises(UnsupportedInput, match='solar_gate'):
        call(bad)


def test_sky_column_guards(feed, generation_dir):
    bad = dict(feed); bad['sky_down'] = feed['sky_down'].astype(np.float64)
    with pytest.raises(UnsupportedInput, match='sky_down'):
        call(bad)
    bad = dict(feed); bad['sky_side'] = feed['sky_side'][:-1]
    with pytest.raises(UnsupportedInput, match='sky_side'):
        call(bad)


def test_directions_gate_lup_guards(feed, generation_dir):
    bad = dict(feed); bad['directions'] = np.zeros((P, 3), F32)
    with pytest.raises(UnsupportedInput, match='directions'):
        call(bad)
    bad = dict(feed); bad['gate'] = feed['gate'].astype(F32)
    with pytest.raises(UnsupportedInput, match='gate'):
        call(bad)
    bad = dict(feed); bad['lup'] = feed['lup'][:-1]
    with pytest.raises(UnsupportedInput, match='lup'):
        call(bad)
    bad = dict(feed); bad['lup'] = feed['lup'].astype(np.float64)
    with pytest.raises(UnsupportedInput, match='lup'):
        call(bad)


def test_surface_scalar_guards(feed, generation_dir):
    bad = dict(feed); bad['surface_sun'] = np.int32(1)
    with pytest.raises(UnsupportedInput, match='surface_sun'):
        call(bad)
    bad = dict(feed); bad['surface_sun'] = F32(1.0)     # f32 vs f64 mismatch
    with pytest.raises(UnsupportedInput, match='mismatch'):
        call(bad)
    bad = dict(feed); bad['surface_sh'] = F32(1.0)
    with pytest.raises(UnsupportedInput, match='mismatch'):
        call(bad)


# ---------------------------------------------------------------------------
# 0-d reflection_factor: PIN decision (review note N7). The shipped numba
# path and lw_native._reflection_spec admit a 0-d float32 ndarray computing
# as float32; this adapter keeps that normalize and pins it from both
# sides before any launch.
# ---------------------------------------------------------------------------

def test_reflection_zero_d_pinned_equal_to_scalar(feed, generation_dir):
    """0-d float32 ndarray == np.float32 scalar, exact bits (positive pin)."""
    via_scalar = call(feed)
    boxed = dict(feed)
    boxed['reflection_factor'] = np.array(feed['reflection_factor'],
                                          dtype=F32)      # 0-d ndarray
    assert boxed['reflection_factor'].ndim == 0
    via_boxed = call(boxed)
    assert np.array_equal(via_boxed.view(np.uint32), via_scalar.view(np.uint32))


@pytest.mark.parametrize('bad', [
    np.array(0.3, dtype=np.float64),        # 0-d float64: wrong graph
    np.array([0.3], dtype=F32),             # 1-d: not a scalar
    np.array([[0.3]], dtype=F32),           # 2-d
    0.3,                                    # Python float: f64 promotion
    np.int32(1),
])
def test_reflection_rejections(feed, generation_dir, bad):
    with pytest.raises(UnsupportedInput, match='reflection_factor'):
        call(dict(feed, **{'reflection_factor': bad}))


# ---------------------------------------------------------------------------
# out guards (writeable + alias rejection over all 14 array inputs).
# ---------------------------------------------------------------------------

def test_out_guards(feed, generation_dir):
    with pytest.raises(UnsupportedInput, match='out'):
        call(feed, out=np.zeros((B, 6), F32))
    with pytest.raises(UnsupportedInput, match='out'):
        call(feed, out=np.zeros((B, 14), F32)[:, :7])   # row-stride 56 != 28
    ro = np.zeros((B, 7), F32)
    ro.setflags(write=False)
    with pytest.raises(UnsupportedInput, match='read-only'):
        call(feed, out=ro)
    # aliasing: out carved from the same buffer as the sh payload
    base = np.zeros(4096, F32)
    aliased = dict(feed)
    aliased['sh'] = base[:feed['sh'].size].reshape(feed['sh'].shape)
    with pytest.raises(UnsupportedInput, match='aliases'):
        call(aliased, out=base[:B * 7].reshape(B, 7))


# ---------------------------------------------------------------------------
# Post-launch failure: loud, never a hidden fallback.
# ---------------------------------------------------------------------------

def test_native_execution_error_after_launch(feed, generation_dir,
                                             monkeypatch):
    def boom(*a, **k):
        raise RuntimeError('simulated native fault')
    monkeypatch.setattr(lw_native_aosoa, 'load_generation',
                        lambda _dir=None: (None, {'f32': boom, 'f64': boom}))
    with pytest.raises(NativeExecutionError, match='simulated native fault'):
        call(feed)


def test_execution_error_is_not_unsupported(feed):
    """The dispatcher's fallback signal catches exactly UnsupportedInput;
    NativeExecutionError must be outside that class."""
    assert not issubclass(NativeExecutionError, UnsupportedInput)
    assert not issubclass(NativeExecutionError, TypeError)


def test_missing_generation_is_loud(tmp_path, monkeypatch):
    monkeypatch.setattr(lw_native_aosoa, '_DEFAULT_STAGE',
                        tmp_path / 'nowhere')
    with pytest.raises(NativeArtifactError):
        lw_native_aosoa.load_generation()


def test_corrupt_generation_rejected(tmp_path, monkeypatch, generation_dir):
    """A byte-flipped dylib fails the content gate before any CDLL."""
    import shutil
    staged = tmp_path / 'corrupt-stage'
    staged.mkdir()
    shutil.copytree(generation_dir, staged / generation_dir.name)
    dylib = staged / generation_dir.name / 'liblw_native_g8.dylib'
    data = bytearray(dylib.read_bytes())
    data[len(data) // 2] ^= 0xFF
    dylib.write_bytes(bytes(data))
    monkeypatch.setattr(lw_native_aosoa, '_DEFAULT_STAGE', staged)
    with pytest.raises(NativeArtifactError):
        lw_native_aosoa.load_generation()


# ---------------------------------------------------------------------------
# Recorded build facts: ISA target and generated FP operations audited.
# ---------------------------------------------------------------------------

def test_manifest_records_isa_and_fp_audit(generation_dir):
    manifest = json.loads((generation_dir / 'manifest.json').read_text())
    assert manifest['build']['target'] == 'neon-i32x8'
    assert manifest['platform']['arch'] == 'arm64'
    assert 'cpu-feature:neon' in manifest['platform'].get('requirements', [])
    assert manifest['toolchain']['ispc']['version'].startswith('1.31.')
    profile = manifest['math_profile']
    assert profile['fast_math'] is False
    assert profile['fma_contraction'] == 'disabled'
    assert profile['math_lib'] == 'default'
    audit = manifest['fma_audit']
    assert audit['passed'] is True and audit['match_count'] == 0
    assert manifest['scalar_profiles']['f32']['symbol'] == 'lw_primary_f32'
    assert manifest['scalar_profiles']['f64']['symbol'] == 'lw_primary_f64'
    # The audited assembly is the shipped bytes (digest-bound).
    import hashlib
    asm = next(e['path'] for e in manifest['generated_sources']
               if e['path'].endswith('.s'))
    digest = hashlib.sha256((generation_dir / asm).read_bytes()).hexdigest()
    assert digest == audit['asm_sha256']


def test_evidence_audit_json_exists_and_passes(generation_dir):
    # N8-41 vendoring: the module now ships inside the package, so the
    # evidence archive no longer sits beside it -- resolve the maintainer
    # tree anchor the package documents (experiments/optimization_v8).
    from solweig_light._native_dispatch import experiments_dir
    try:
        evidence = experiments_dir('native', 'evidence')
    except FileNotFoundError:
        pytest.skip('canonical staging not used in this session')
    audits = sorted(evidence.glob('build_audit_*.json'))
    assert audits, 'no archived build audit JSON'
    latest = json.loads(audits[-1].read_text())
    assert latest['passed'] is True
    assert latest['isa_target'] == 'neon-i32x8'
    assert latest['fma_audit']['passed'] is True
    assert latest['reciprocal_audit']['passed'] is True
    assert latest['true_division_audit']['fdiv_mnemonic_count'] > 0
