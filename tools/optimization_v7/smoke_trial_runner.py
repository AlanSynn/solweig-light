"""Smoke-test the B7-31 trial runner with baseline A only (no foreign C)."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path('/Users/alansynn/Workspace/solweig-light')
sys.path.insert(0, str(REPO / 'src'))

from solweig_light.radiation import cylinder_longwave as cyl  # noqa: E402


def _inputs():
    rng = np.random.default_rng(20260922)
    pixels, patches = 16384, 153
    sh = (rng.random((pixels, patches)) > .3).astype(np.float32)
    vs = (rng.random((pixels, patches)) > .5).astype(np.float32)
    vb = (rng.random((pixels, patches)) > .6).astype(np.float32)
    sun = rng.random((pixels, patches)) < .5
    shade = rng.random((pixels, patches)) < .5
    solid = rng.random(patches).astype(np.float32) + .01
    sine = rng.random(patches).astype(np.float32)
    cosine = rng.random(patches).astype(np.float32)
    solar_gate = rng.random(patches) < .7
    sky_down = rng.random(patches).astype(np.float32)
    sky_side = rng.random(patches).astype(np.float32)
    lup = rng.random(pixels).astype(np.float32)
    return dict(sh=sh, vs=vs, vb=vb, sun=sun, shade=shade, solid=solid, sine=sine,
                cosine=cosine, solar_gate=solar_gate, sky_down=sky_down,
                sky_side=sky_side, surface_sun=np.float64(0.7),
                surface_sh=np.float64(0.9), lup=lup, factor=np.float32(0.1),
                directions=np.zeros((patches, 4), dtype=np.float32),
                gate=np.zeros((patches, 4), dtype=bool))


INPUTS = _inputs()
KERNEL = cyl._longwave_primary


def load_inputs(spec):
    # The fixture is rebuilt deterministically in-child; arrays are never
    # shipped through the spec file.
    assert spec.get('inputs', {}).get('note') == 'module builds its own fixture'
    return INPUTS


def supported(inputs):
    return inputs['sh'].dtype == np.float32


def prepare(inputs):
    return inputs


def kernel_only(prepared):
    return KERNEL(prepared['sh'], prepared['vs'], prepared['vb'], prepared['sun'],
                  prepared['shade'], prepared['solid'], prepared['sine'],
                  prepared['cosine'], INPUTS['directions'], INPUTS['gate'],
                  prepared['solar_gate'], prepared['sky_down'], prepared['sky_side'],
                  prepared['surface_sun'], prepared['surface_sh'], prepared['lup'],
                  prepared['factor'])


def adapter_total(inputs):
    return kernel_only(inputs)


def identity():
    import numba
    return {'backend': 'numba-A', 'numba': numba.__version__,
            'schedule': 'parallel prange'}


if __name__ == '__main__':
    print('adapter module OK:', identity())
