"""B7-31 appendix: variant C_drjit adapter (worktree candidate, symbolic mode).

Uses the candidate's reviewed-boundary entry longwave_primary_drjit (17-arg
signature, validate + tiled-transpose pack + JIT eval + materialize inside
the adapter). Thread budget is part of the config: configure_runtime(threads)
pins Dr.Jit's own pool so budgets can be matched against numba variants.
"""
import hashlib
import sys
from pathlib import Path

import numpy as np

REPO = Path('/Users/alansynn/Workspace/solweig-light')
CAND = Path('/Users/alansynn/Workspace/solweig-v7-drjit/experiments/optimization_v7/drjit')
sys.path.insert(0, str(REPO / 'tools' / 'optimization_v7'))
sys.path.insert(0, str(CAND))

import llvm_longwave  # noqa: E402
import trial_fixtures  # noqa: E402

_LOOP_MODE = 'symbolic'
_CURRENT_THREADS = [None]


def load_inputs(spec):
    threads = spec.get('drjit_threads')
    if threads is not None and threads != _CURRENT_THREADS[0]:
        info = llvm_longwave.configure_runtime(int(threads))
        _CURRENT_THREADS[0] = info.get('thread_count')
    return trial_fixtures.load(spec['fixture'], spec.get('schedule'))


class _Rejected(Exception):
    pass


def supported(inputs):
    """Structural pre-check; the full guard runs inside the adapter call.
    All campaign fixtures are in the admitted domain (candidate replay:
    520/520 admitted)."""
    return True


def prepare(inputs):
    if inputs['kind'] == 'single':
        return [trial_fixtures.call_args(inputs)]
    return [tuple(c['args']) for c in inputs['calls']]


def kernel_only(prepared):
    # the drjit adapter has no separate prepared-launch entry: pack runs
    # inside longwave_primary_drjit, so kernel_only == adapter_total for
    # this variant; recorded as such in the analysis notes.
    return adapter_total_from_prepared(prepared)


def adapter_total_from_prepared(prepared):
    outs = [llvm_longwave.longwave_primary_drjit(*args, loop_mode=_LOOP_MODE)
            for args in prepared]
    return np.concatenate([o.reshape(-1, 7) for o in outs], axis=0)


def adapter_total(inputs):
    return adapter_total_from_prepared(prepare(inputs))


def identity():
    import os
    return {
        'variant': 'C_drjit_llvm_symbolic',
        'drjit': __import__('drjit').__version__,
        'loop_mode': _LOOP_MODE,
        'thread_count': _CURRENT_THREADS[0],
        'requested_env_NUMBA_NUM_THREADS': os.environ.get('NUMBA_NUM_THREADS'),
        'adapter_sha256': hashlib.sha256(
            (CAND / 'llvm_longwave.py').read_bytes()).hexdigest(),
        'numpy': np.__version__,
        'boundary_note': 'kernel_only == adapter_total (pack inside adapter)',
    }
