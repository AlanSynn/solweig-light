"""B7-02 frozen contract: baseline `_longwave_primary` reproduces captured outputs.

The fixtures were captured (tools/optimization_v7/capture_longwave_primary.py)
from untouched execution at the recorded HEAD: the genuine 35x32 TIFF pipeline
(24 records, PIPELINE_CYLINDERS_ANISOTROPIC) in its serial-default and
threads_per_worker=4 configurations, plus synthetic edge domains. Every kept
call must replay exact float32 bits except the sign of an arithmetic NaN:
the captures came from ARM64, while invalid arithmetic can produce negative
NaNs on x86. NaN payloads and locations, signed zeros, infinities and all
finite bits remain exact, as in the v8 typed-arithmetic reference checks.
"""
import json
from pathlib import Path

import numpy as np
import pytest

from solweig_light.radiation import cylinder_longwave as cyl

ROOT = Path(__file__).resolve().parents[3]
CAPTURES = ROOT / 'tests/reference/cylinder_longwave'
MANIFEST = json.loads((CAPTURES / 'b7_02_capture_manifest.json').read_text())
FIXTURES = np.load(CAPTURES / 'b7_02_fixtures.npz')

ARGNAMES = ('sh', 'vs', 'vb', 'sun', 'shade', 'solid', 'sine', 'cosine',
            'directions', 'gate', 'solar_gate', 'sky_down', 'sky_side',
            'surface_sun', 'surface_sh', 'lup', 'reflection_factor')


def _arithmetic_equal(a, b):
    """Compare float32 bits, allowing only an arithmetic NaN sign change."""
    a = np.asarray(a)
    b = np.asarray(b)
    if a.shape != b.shape or a.dtype != np.float32 or b.dtype != np.float32:
        return False
    ab, bb = a.view(np.uint32), b.view(np.uint32)
    same_nan = np.isnan(a) & np.isnan(b) & ((ab ^ bb) == 0x80000000)
    return bool(np.all((ab == bb) | same_nan))


@pytest.mark.parametrize('left,right,equal', [
    (0x7FC00001, 0xFFC00001, True),   # Same NaN payload, different sign.
    (0x7FC00001, 0x7FC00002, False),  # Different NaN payload.
    (0x7FC00000, 0x7F800000, False),  # NaN replaced by infinity.
    (0x7F800000, 0xFF800000, False),  # Infinity sign.
    (0x00000000, 0x80000000, False),  # Signed zero.
    (0x3F800000, 0x3F800001, False),  # One finite ULP.
])
def test_arithmetic_comparison_preserves_value_bits(left, right, equal):
    a = np.array([left], dtype=np.uint32).view(np.float32)
    b = np.array([right], dtype=np.uint32).view(np.float32)
    assert _arithmetic_equal(a, b) is equal
    assert not _arithmetic_equal(a.astype(np.float64), a)
    assert not _arithmetic_equal(a.reshape(1, 1), a)


def _fixture_calls():
    for record in MANIFEST['calls']:
        prefix = f'call{record["call_index"]:04d}'
        if f'{prefix}_output' not in FIXTURES:
            continue
        args = []
        for index in range(17):
            key = f'{prefix}_arg{index:02d}'
            value = FIXTURES[key]
            args.append(value[()] if value.ndim == 0 else value)
        yield record, args


def test_capture_manifest_provenance():
    """Fixture identity: recorded HEAD, source blob and environment pinned."""
    assert MANIFEST['schema'] == 'solweig-v7-capture-v1'
    assert MANIFEST['source_identity']['reducer_blob'] == \
        '27ba6ce48454399c7b97285c8408511d050a32da'
    assert MANIFEST['env_flags']['SOLWEIG_LIGHT_FUSED_RAD'] is None
    assert MANIFEST['env_flags']['SOLWEIG_LIGHT_PATCH_CLASS_TABLES'] is None
    assert MANIFEST['call_count'] == 520


@pytest.mark.parametrize('parallel', (False, True))
def test_fixture_calls_replay_bitwise(parallel):
    """Every captured call preserves arithmetic bits and nonfinite masks."""
    kernel = cyl._longwave_primary if parallel else cyl._longwave_primary_serial
    expected_label = 'parallel' if parallel else 'serial'
    checked = 0
    for record, args in _fixture_calls():
        if record['label'] != expected_label:
            continue
        observed = kernel(*args)
        prefix = f'call{record["call_index"]:04d}_output'
        expected = FIXTURES[prefix]
        assert observed.shape == expected.shape, record['call_index']
        assert _arithmetic_equal(observed, expected), (record['case'], record['call_index'])
        checked += 1
    assert checked == sum(record['label'] == expected_label for record in MANIFEST['calls'])


def test_real_pipeline_typed_contract():
    """The real pipeline specialization is frozen: float64 surface scalars,
    bool classifications, non-contiguous stride-2 sky views, float32 factor."""
    record = next(record for record in MANIFEST['calls']
                  if record['case'] == 'pipeline_serial_default')
    kinds = {name: arg for name, arg in zip(ARGNAMES, record['args'])}
    assert kinds['surface_sun']['kind'] == 'numpy_scalar'
    assert kinds['surface_sun']['dtype'] == 'float64'
    assert kinds['surface_sh']['dtype'] == 'float64'
    assert kinds['reflection_factor']['dtype'] == 'float32'
    assert kinds['sun']['dtype'] == 'bool' and kinds['shade']['dtype'] == 'bool'
    assert kinds['sky_down']['strides'] == [12, 1] or kinds['sky_down']['strides'] == [12]
    assert kinds['sh']['shape'] == [128, 153]
    assert kinds['solid']['writeable'] is False
    output = record['output']
    assert output['dtype'] == 'float32' and output['shape'] == [128, 7]


def test_numba_signatures_frozen():
    """The parallel dispatcher holds the float64-surface pipeline signature."""
    parallel_signatures = MANIFEST['numba_signatures']['parallel']
    assert any('float64, float64' in signature and 'float32)' in signature
               for signature in parallel_signatures)
    assert any('bool, 2' in signature for signature in parallel_signatures)
