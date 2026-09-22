"""B7-02 frozen contract: baseline `_longwave_primary` reproduces captured outputs.

The fixtures were captured (tools/optimization_v7/capture_longwave_primary.py)
from untouched execution at the recorded HEAD: the genuine 35x32 TIFF pipeline
(24 records, PIPELINE_CYLINDERS_ANISOTROPIC) in its serial-default and
threads_per_worker=4 configurations, plus synthetic edge domains. Every kept
call must replay bitwise (uint32 view, NaN payload and sign included) on the
baseline kernels. A failure here means the fixtures, environment, or kernels
changed - not a tolerance to renegotiate.
"""
import json
from pathlib import Path

import numpy as np
import pytest

from solweig_light.radiation import cylinder_longwave as cyl

ROOT = Path(__file__).resolve().parents[3]
CAPTURES = ROOT / 'optimization_v7_backends/evidence/captures'
MANIFEST = json.loads((CAPTURES / 'b7_02_capture_manifest.json').read_text())
FIXTURES = np.load(CAPTURES / 'b7_02_fixtures.npz')

ARGNAMES = ('sh', 'vs', 'vb', 'sun', 'shade', 'solid', 'sine', 'cosine',
            'directions', 'gate', 'solar_gate', 'sky_down', 'sky_side',
            'surface_sun', 'surface_sh', 'lup', 'reflection_factor')


def _bitwise_equal(a, b):
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    if a.shape != b.shape:
        return False
    return np.array_equal(a.view(np.uint32), b.view(np.uint32))


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
    """Every kept captured call replays bitwise on the baseline kernels."""
    kernel = cyl._longwave_primary if parallel else cyl._longwave_primary_serial
    checked = 0
    for record, args in _fixture_calls():
        expected_label = 'parallel' if parallel else 'serial'
        if record['label'] != expected_label:
            continue
        observed = kernel(*args)
        prefix = f'call{record["call_index"]:04d}_output'
        expected = FIXTURES[prefix]
        assert observed.shape == expected.shape, record['call_index']
        assert _bitwise_equal(observed, expected), (record['case'], record['call_index'])
        checked += 1
    assert checked > 0


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
