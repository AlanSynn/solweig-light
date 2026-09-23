"""B7-31 variant B adapter: numba pixel-blocked layout (worktree candidate).

Uses the candidate's own reviewed entry points: reject_unsupported for the
pre-launch admission decision, _pack_all_numba for the schedule-matched pack
(the candidate's adapter path), and make_longwave_primary_b(W, parallel) for
the kernel dispatch. prepare() packs (timed in adapter_total, untimed in
kernel_only); inputs are never mutated.
"""
import sys
from pathlib import Path

import numpy as np

REPO = Path('/Users/alansynn/Workspace/solweig-light')
CAND = Path('/Users/alansynn/Workspace/solweig-v7-numba/experiments/optimization_v7/numba_layout')
sys.path.insert(0, str(REPO / 'src'))
sys.path.insert(0, str(REPO / 'tools' / 'optimization_v7'))
sys.path.insert(0, str(CAND))

import longwave_primary_b as mod_b  # noqa: E402
import trial_fixtures  # noqa: E402

W = 8


def load_inputs(spec):
    return trial_fixtures.load(spec['fixture'], spec.get('schedule'))


class _Rejected(Exception):
    pass


def _admits(args):
    try:
        pixels = mod_b.reject_unsupported(*args)
        return pixels
    except ValueError as exc:
        raise _Rejected(str(exc)) from exc


def supported(inputs):
    try:
        _admits(trial_fixtures.call_args(inputs))
        return True
    except _Rejected:
        return False


def prepare(inputs):
    if inputs['kind'] == 'single':
        args = trial_fixtures.call_args(inputs)
        _admits(args)
        label = inputs.get('label') or 'serial'
        return {'kind': 'single', 'label': label,
                'args': args, 'packed': _pack_single(args, label == 'parallel')}
    prepared_calls = []
    for call in inputs['calls']:
        args = tuple(call['args'])
        _admits(args)
        prepared_calls.append({'args': args,
                               'packed': _pack_single(args, call['label'] == 'parallel'),
                               'label': call['label']})
    return {'kind': 'sequence', 'calls': prepared_calls}


def _pack_single(args, parallel):
    (sh, vs, vb, sun, shade, _solid, _sine, _cosine, _directions, _gate,
     _solar_gate, _sky_down, _sky_side, _surface_sun, _surface_sh, lup,
     _refl) = args
    return (*mod_b._pack_all_numba(sh, vs, vb, sun, shade, lup, W, parallel),)


def _dispatch_single(packed_single, args, label):
    (sh, vs, vb, sun, shade, solid, sine, cosine, _directions, _gate,
     solar_gate, sky_down, sky_side, surface_sun, surface_sh, _lup,
     refl) = args
    sh_p, vs_p, vb_p, sun_p, shade_p, lup_p = packed_single
    kernel = mod_b._KERNELS[(W, label == 'parallel')]
    return kernel(sh_p, vs_p, vb_p, sun_p, shade_p, solid, sine, cosine,
                  solar_gate, sky_down, sky_side, surface_sun, surface_sh,
                  lup_p, refl, sh.shape[0])


def _run(prepared):
    outs = []
    if prepared['kind'] == 'single':
        outs.append(_dispatch_single(prepared['packed'], prepared['args'],
                                     prepared['label']))
        return outs
    for call in prepared['calls']:
        outs.append(_dispatch_single(call['packed'], call['args'], call['label']))
    return outs


def kernel_only(prepared):
    return np.concatenate([o.reshape(-1, 7) for o in _run(prepared)], axis=0)


def adapter_total(inputs):
    return kernel_only(prepare(inputs))


def identity():
    import hashlib
    import os

    import numba
    try:
        layer = numba.threading_layer()
    except ValueError:
        layer = None
    return {
        'variant': 'B_numba_layout_W8',
        'numba': numba.__version__,
        'numpy': np.__version__,
        'W': W,
        'candidate_sha256': hashlib.sha256(
            (CAND / 'longwave_primary_b.py').read_bytes()).hexdigest(),
        'effective_num_threads': numba.get_num_threads(),
        'threading_layer': layer,
        'requested_env_NUMBA_NUM_THREADS': os.environ.get('NUMBA_NUM_THREADS'),
        'pack_engine': 'numba, schedule-matched',
    }
