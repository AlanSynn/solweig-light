"""B7-31 shared in-child fixture materialization for the A/B/C trials.

Two frozen fixture families (b7_03_protocol.json):

* ``adv{pixels}`` — the tests/optimization_v6/cylinder_lw/conftest.py builders
  (lw_blocks + lw_coefficients, loaded from source with a stubbed pytest so
  the baseline venv is untouched), seed 20260922+pixels, surface scalars
  np.float64 (real-pipeline provenance). pixels in {4096, 16384, 65536};
  4096 (64^2) is the tuning-visible size, 16384/65536 are held-out.
* ``warm_serial`` / ``warm_parallel`` — the real 35x32 scene call sequences
  captured in evidence/captures/b7_02_fixtures.npz (cases
  pipeline_serial_default / pipeline_parallel_tpw4). Stride-12 sky_down /
  sky_side views are reconstructed as column-2 views of a (P,3) parent so
  the replayed calls carry the real pipeline's non-contiguous layout.
"""
import importlib.util
import json
import sys
import types
from pathlib import Path

import numpy as np

REPO = Path('/Users/alansynn/Workspace/solweig-light')
CAPTURE_DIR = REPO / 'optimization_v7_backends' / 'evidence' / 'captures'
CONFPATH = REPO / 'tests' / 'optimization_v6' / 'cylinder_lw' / 'conftest.py'
KERNEL_ARITY = 17

_conftest = None


def _load_conftest():
    """Import the frozen builders with a stub pytest (baseline venv has none)."""
    global _conftest
    if _conftest is None:
        stub = types.ModuleType('pytest')

        def _fixture(*_a, **_k):
            def deco(fn):
                return fn
            return deco
        stub.fixture = _fixture
        sys.modules.setdefault('pytest', stub)
        spec = importlib.util.spec_from_file_location('v7_b6_conftest', CONFPATH)
        mod = importlib.util.module_from_spec(spec)
        sys.modules['v7_b6_conftest'] = mod
        spec.loader.exec_module(mod)
        _conftest = mod
    return _conftest


def _adversarial(pixels):
    rng = np.random.default_rng(20260922 + pixels)
    conf = _load_conftest()
    sh, vs, vb = conf.lw_blocks(rng, pixels, 153)
    coeff = conf.lw_coefficients(rng, 153, pixels)
    inputs = {
        'sh': sh, 'vs': vs, 'vb': vb,
        'sun': rng.random((pixels, 153)) < .5,
        'shade': rng.random((pixels, 153)) < .5,
    }
    inputs.update(solid=coeff['solid'], sine=coeff['sine'], cosine=coeff['cosine'],
                  directions=coeff['directions'], gate=coeff['gate'],
                  solar_gate=coeff['solar_gate'], sky_down=coeff['sky_down'],
                  sky_side=coeff['sky_side'],
                  # builders emit 0-d ndarrays; the pipeline provenance is
                  # numpy scalars (captured fixtures recorded numpy_scalar)
                  surface_sun=np.float32(coeff['sun_surface']),
                  surface_sh=np.float32(coeff['shade_surface']),
                  lup=coeff['lup'],
                  reflection_factor=np.float32(coeff['factor']))
    return {'kind': 'single', 'pixels': pixels, 'label': None, 'inputs': inputs}


def _warm_sequence(case):
    manifest = json.loads((CAPTURE_DIR / 'b7_02_capture_manifest.json').read_text())
    z = np.load(CAPTURE_DIR / 'b7_02_fixtures.npz')
    calls = []
    for rec in manifest['calls']:
        if rec['case'] != case:
            continue
        args = []
        for i in range(KERNEL_ARITY):
            arr = z[f'call{rec["call_index"]:04d}_arg{i:02d}']
            if i in (11, 12) and arr.ndim == 1:  # sky_down/sky_side stride-12 views
                parent = np.zeros((arr.shape[0], 3), np.float32)
                parent[:, 2] = arr
                arr = parent[:, 2]
            elif arr.ndim == 0:
                arr = arr[()]  # numpy scalar
            args.append(arr)
        calls.append({'args': args, 'label': rec['label'],
                      'expected': z[f'call{rec["call_index"]:04d}_output']})
    calls.sort(key=lambda c: 0)  # manifest order is already chronological
    return {'kind': 'sequence', 'case': case, 'calls': calls, 'label': None}


def load(name, schedule=None):
    if name.startswith('adv'):
        fixture = _adversarial(int(name[3:]))
        fixture['label'] = schedule or 'serial'
        return fixture
    if name == 'warm_serial':
        return _warm_sequence('pipeline_serial_default')
    if name == 'warm_parallel':
        return _warm_sequence('pipeline_parallel_tpw4')
    raise ValueError(f'unknown fixture {name!r}')


def call_args(fixture, index=0):
    """The 17-argument kernel argument tuple for call `index`."""
    if fixture['kind'] == 'single':
        inp = fixture['inputs']
        return (inp['sh'], inp['vs'], inp['vb'], inp['sun'], inp['shade'],
                inp['solid'], inp['sine'], inp['cosine'], inp['directions'],
                inp['gate'], inp['solar_gate'], inp['sky_down'], inp['sky_side'],
                inp['surface_sun'], inp['surface_sh'], inp['lup'],
                inp['reflection_factor'])
    return tuple(fixture['calls'][index]['args'])


def n_calls(fixture):
    return 1 if fixture['kind'] == 'single' else len(fixture['calls'])
