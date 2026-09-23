"""C6-81: the prepared decode route is opt-in, default OFF.

C6-80 measured the wired prepared route at +21-24% per full-frame sweep
against the per-channel entries at both timing shapes (evidence/portfolio/
decoder_probe/), so ``prepare_channels`` now declines unless
SOLWEIG_LIGHT_PREPARED_VIS=1. Declined admission returns ``None`` -- the
same contract as unsupported inputs -- so every caller falls back completely
to the original per-channel decode path.
"""
import importlib.util as _ilu
import sys as _sys
from pathlib import Path as _Path
# Load THIS family's conftest by file path: bare `import conftest` is
# shadowed by sibling families' conftest modules when several test
# directories are collected in one pytest invocation.
_conftest_path = _Path(__file__).resolve().parent / 'conftest.py'
_spec = _ilu.spec_from_file_location('_decoder_conftest_default_off', str(_conftest_path))
_conftest = _ilu.module_from_spec(_spec)
_sys.modules['_decoder_conftest_default_off'] = _conftest
_spec.loader.exec_module(_conftest)
packed = _conftest.packed
bitwise = _conftest.bitwise
import numpy as np
import pytest

from solweig_light.geometry.visibility_compiled import decode_block
from solweig_light.geometry.visibility_prepared import (decode_longwave_block,
                                                        decode_shortwave_block,
                                                        prepare_channels)


def _channels(rng):
    shadow = packed(rng, 16, 16, 3, ['binary'])
    vegetation = packed(rng, 16, 16, 3, ['ternary'])
    building = packed(rng, 16, 16, 3, ['raw'])
    diffuse = packed(rng, 16, 16, 3, ['binary'])
    return shadow, vegetation, building, diffuse


@pytest.mark.prepared_default_off
def test_default_declines_prepared_route(monkeypatch):
    monkeypatch.delenv('SOLWEIG_LIGHT_PREPARED_VIS', raising=False)
    shadow, vegetation, building, diffuse = _channels(np.random.default_rng(65))
    assert prepare_channels(shadow, vegetation, building, diffuse) is None
    assert prepare_channels(shadow, vegetation, building) is None
    assert decode_shortwave_block(shadow, vegetation, building, diffuse, 0, 16, 3) is None
    assert decode_longwave_block(shadow, vegetation, building, 0, 16, 3) is None


def test_opt_in_admits_and_matches_original(monkeypatch):
    monkeypatch.setenv('SOLWEIG_LIGHT_PREPARED_VIS', '1')
    rng = np.random.default_rng(65)
    shadow, vegetation, building, diffuse = _channels(rng)
    assert prepare_channels(shadow, vegetation, building, diffuse) is not None
    assert prepare_channels(shadow, vegetation, building) is not None
    shortwave = decode_shortwave_block(shadow, vegetation, building, diffuse, 0, 16, 3)
    longwave = decode_longwave_block(shadow, vegetation, building, 0, 16, 3)
    assert shortwave is not None and longwave is not None
    # Same environment, original entries: bitwise outputs.
    for channel, decoded in zip((shadow, vegetation, building, diffuse), shortwave):
        assert bitwise(decoded, decode_block(channel, 0, 16, 3))
    for channel, decoded in zip((shadow, vegetation, building), longwave):
        assert bitwise(decoded, decode_block(channel, 0, 16, 3))
