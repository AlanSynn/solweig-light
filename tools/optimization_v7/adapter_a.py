"""B7-31 variant A adapter: baseline Numba _longwave_primary at frozen HEAD.

A accepts row-major inputs directly and has no validation guard of its own
(it is the reference kernel); adapter_total == prepare + kernel dispatch with
zero conversion cost. Sequence fixtures loop the captured call order and the
output of every call is verified bitwise against the captured baseline
output in-child (A IS the capture oracle).
"""
import sys
from pathlib import Path

import numpy as np

REPO = Path('/Users/alansynn/Workspace/solweig-light')
sys.path.insert(0, str(REPO / 'src'))
sys.path.insert(0, str(REPO / 'tools' / 'optimization_v7'))

from solweig_light.radiation import cylinder_longwave as cyl  # noqa: E402
import trial_fixtures  # noqa: E402


def load_inputs(spec):
    return trial_fixtures.load(spec['fixture'], spec.get('schedule'))


def supported(inputs):
    return True  # reference kernel; fixtures are in the accepted domain


def prepare(inputs):
    return inputs  # A consumes row-major views as-is


def _dispatch(args, label):
    kernel = cyl._longwave_primary if label == 'parallel' else cyl._longwave_primary_serial
    return kernel(*args)


def _verify(fixture, outputs):
    if fixture['kind'] != 'sequence':
        return 0
    mismatches = 0
    for call, out in zip(fixture['calls'], outputs):
        if not np.array_equal(out.view(np.uint32), call['expected'].view(np.uint32)):
            mismatches += 1
    return mismatches


def _run(fixture):
    if fixture['kind'] == 'single':
        label = fixture.get('label') or 'serial'
        return [_dispatch(trial_fixtures.call_args(fixture), label)]
    outs = []
    for i, call in enumerate(fixture['calls']):
        outs.append(_dispatch(tuple(call['args']), call['label']))
    mismatches = _verify(fixture, outs)
    if mismatches:
        raise AssertionError(
            f'A sequence replay diverged from captured oracle on {mismatches} calls')
    return outs


def kernel_only(prepared):
    return _concat(_run(prepared))


def adapter_total(inputs):
    return _concat(_run(inputs))


def _concat(outputs):
    return np.concatenate([o.reshape(-1, 7) for o in outputs], axis=0)


def identity():
    import os

    import numba
    try:
        layer = numba.threading_layer()
    except ValueError:
        layer = None  # no parallel target initialized yet
    return {
        'variant': 'A_baseline_numba',
        'numba': numba.__version__,
        'numpy': np.__version__,
        'effective_num_threads': numba.get_num_threads(),
        'threading_layer': layer,
        'requested_env_NUMBA_NUM_THREADS': os.environ.get('NUMBA_NUM_THREADS'),
        'kernels': ['_longwave_primary (parallel prange)',
                    '_longwave_primary_serial'],
    }
