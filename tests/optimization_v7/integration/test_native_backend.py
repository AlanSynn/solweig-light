"""B7-41: integrated native (ISPC) longwave backend — identity and exactness.

The integrated backend must satisfy:

* default path untouched: env unset resolves to the baseline Numba kernel
  objects themselves (no wrapper);
* native replay bitwise: every captured B7-02 call (520) replays bitwise
  through the env-gated dispatch, both schedule labels;
* pre-launch fallback: unsupported input provenance falls back to the Numba
  kernel without launching the backend (result equals the Numba output);
* loud unavailability: a requested backend that cannot build raises
  RuntimeError naming the toolchain — never a silent fallback;
* B=0 edge and runtime identity fingerprint.

The dylib is built once per test session into a session-scoped cache; tests
skip (with the build command in the reason) only if the ISPC toolchain is
absent from the machine — the backend itself never skips.
"""
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
import pytest

from solweig_light.radiation import cylinder_longwave as cyl

ROOT = Path(__file__).resolve().parents[3]
CAPTURES = ROOT / 'optimization_v7_backends/evidence/captures'
MANIFEST = json.loads((CAPTURES / 'b7_02_capture_manifest.json').read_text())
FIXTURES = np.load(CAPTURES / 'b7_02_fixtures.npz')

from solweig_light.backends import native_lw  # noqa: E402


def _bitwise_equal(a, b):
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    return a.shape == b.shape and np.array_equal(a.view(np.uint32), b.view(np.uint32))


def _fixture_calls():
    for record in MANIFEST['calls']:
        prefix = f'call{record["call_index"]:04d}'
        if f'{prefix}_output' not in FIXTURES:
            continue
        args = []
        for index in range(17):
            value = FIXTURES[f'{prefix}_arg{index:02d}']
            args.append(value[()] if value.ndim == 0 else value)
        yield record, args


@pytest.fixture(scope='session')
def native_cache(tmp_path_factory):
    if shutil.which('ispc') is None and not Path('/opt/homebrew/bin/ispc').exists():
        pytest.skip('ispc toolchain absent; build manually: '
                    'cd src/solweig_light/backends/native && zsh build.sh')
    cache = tmp_path_factory.mktemp('native-lw-cache')
    native_lw._build(cache)  # loud failure if the toolchain is broken
    return cache


@pytest.fixture(autouse=True)
def native_env(monkeypatch, native_cache):
    monkeypatch.setenv('SOLWEIG_LIGHT_LW_BACKEND', 'native')
    monkeypatch.setenv('SOLWEIG_LIGHT_NATIVE_CACHE', str(native_cache))


def test_default_path_unchanged(monkeypatch):
    """Env unset: the resolver returns the baseline Numba kernel objects."""
    monkeypatch.delenv('SOLWEIG_LIGHT_LW_BACKEND', raising=False)
    assert cyl._lw_kernel(True) is cyl._longwave_primary
    assert cyl._lw_kernel(False) is cyl._longwave_primary_serial
    for stale in ('', 'numba', 'NATIVE', ' ispc '):
        monkeypatch.setenv('SOLWEIG_LIGHT_LW_BACKEND', stale)
        if stale.strip().lower() in ('native', 'ispc'):
            continue
        assert cyl._lw_kernel(True) is cyl._longwave_primary


def test_identity_fingerprint(native_cache):
    info = native_lw.identity()
    assert info['backend'] == 'native_ispc_lw_primary'
    assert info['gang'] == 8 and info['effective_threads'] == 1
    assert info['kernel_sha256'] == hashlib.sha256(
        (ROOT / 'src/solweig_light/backends/native/lw_primary.ispc')
        .read_bytes()).hexdigest()
    assert info['build_stamp']['kernel_sha256'] == info['kernel_sha256']


def test_native_replay_bitwise_all_captured_calls(monkeypatch):
    """Every captured call replays bitwise through the env-gated dispatch,
    and every one of them actually ran on the native backend (a silent
    per-call fallback to Numba would otherwise be invisible: it matches
    bitwise too, so the spy counts native invocations)."""
    calls = {'native': 0}
    real = native_lw.native_longwave_primary

    def spy(*args):
        calls['native'] += 1
        return real(*args)

    monkeypatch.setattr(native_lw, 'native_longwave_primary', spy)
    kernel = cyl._lw_kernel(True)   # label-independent: native has one schedule
    checked = 0
    for record, args in _fixture_calls():
        observed = kernel(*args)
        expected = FIXTURES[f'call{record["call_index"]:04d}_output']
        assert observed.shape == expected.shape, record['call_index']
        assert _bitwise_equal(observed, expected), \
            (record['case'], record['call_index'])
        checked += 1
    assert checked == MANIFEST['kept_calls']
    assert calls['native'] == checked


def test_serial_label_dispatches_to_same_backend():
    """The serial runtime label uses the native kernel and stays bitwise."""
    kernel = cyl._lw_kernel(False)
    record, args = next(_fixture_calls())
    observed = kernel(*args)
    expected = FIXTURES[f'call{record["call_index"]:04d}_output']
    assert _bitwise_equal(observed, expected)


def test_unsupported_input_falls_back_before_launch():
    """Python-float reflection factor is outside the native admission domain:
    the native guard rejects pre-launch, the dispatch falls back to Numba,
    and the fallback output equals a direct Numba call with the same args."""
    args = list(next(_fixture_calls())[1])
    args[16] = 0.25  # python float reflection_factor: unsupported provenance
    with pytest.raises(native_lw.UnsupportedInput):
        native_lw.native_longwave_primary(*args)
    kernel = cyl._lw_kernel(True)
    observed = kernel(*args)
    expected = cyl._longwave_primary(*args)
    assert _bitwise_equal(observed, expected)


def test_b0_edge():
    kernel = cyl._lw_kernel(True)
    empty_sh = np.zeros((0, 4), np.float32)
    out = kernel(empty_sh, empty_sh, empty_sh,
                 np.zeros((0, 4), bool), np.zeros((0, 4), bool),
                 np.ones(4, np.float32), np.ones(4, np.float32),
                 np.ones(4, np.float32), np.zeros((4, 4), np.float32),
                 np.zeros((4, 4), bool), np.ones(4, bool),
                 np.ones(4, np.float32), np.ones(4, np.float32),
                 np.float64(0.9), np.float64(0.8), np.zeros(0, np.float32),
                 np.float32(0.05))
    assert out.shape == (0, 7) and out.dtype == np.float32


def test_unbuildable_backend_fails_loudly(monkeypatch, tmp_path):
    """A requested backend with no toolchain raises; it never falls back."""
    monkeypatch.setattr(native_lw.shutil, 'which', lambda _: None)
    monkeypatch.setattr(native_lw, '_ISPC_FALLBACK', str(tmp_path / 'no-ispc'))
    monkeypatch.setenv('SOLWEIG_LIGHT_NATIVE_CACHE', str(tmp_path / 'nocache'))
    with pytest.raises(RuntimeError, match='ispc'):
        native_lw._build(native_lw._cache_dir())
