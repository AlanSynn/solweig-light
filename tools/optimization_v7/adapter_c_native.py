"""B7-31 variant C_native adapter: ISPC reducer (worktree candidate, as-shipped).

Uses the candidate's reviewed boundary lw_native.primary verbatim: full
pre-launch validation, uint8 zero-copy views, synchronous single-thread
native call, owned float32 [B,7] output. No chunking/threading adapter (the
chunked path is not in the reviewed as-shipped scope). gang=8 build to match
control B's W=8 lane width.

supported() performs only a structural pre-check (dtype/shape/stride against
the documented admission); the full guard runs inside primary() during the
timed call, and any UnsupportedInput there is recorded as a rejection, never
a silent fallback.
"""
import hashlib
import sys
from pathlib import Path

import numpy as np

REPO = Path('/Users/alansynn/Workspace/solweig-light')
CAND = Path('/Users/alansynn/Workspace/solweig-v7-native/experiments/optimization_v7/native')
sys.path.insert(0, str(REPO / 'tools' / 'optimization_v7'))
sys.path.insert(0, str(CAND))

import lw_native  # noqa: E402
import trial_fixtures  # noqa: E402

GANG = 8


def load_inputs(spec):
    fixture = trial_fixtures.load(spec['fixture'], spec.get('schedule'))
    lw_native._load(GANG)  # dylib pinned before any timing
    return fixture


def _structural_ok(inputs):
    if inputs['kind'] == 'single':
        args = [trial_fixtures.call_args(inputs)]
    else:
        args = [tuple(c['args']) for c in inputs['calls']]
    for a in args:
        sh = a[0]
        if not (isinstance(sh, np.ndarray) and sh.dtype == np.float32
                and sh.ndim == 2 and sh.shape[1] <= lw_native.MAX_PATCHES):
            return False
        for i in (1, 2):
            if not (isinstance(a[i], np.ndarray) and a[i].shape == sh.shape):
                return False
        for i in (3, 4):
            if not (isinstance(a[i], np.ndarray) and a[i].dtype == np.bool_
                    and a[i].shape == sh.shape):
                return False
    return True


def supported(inputs):
    return _structural_ok(inputs)  # full guard inside primary()


def prepare(inputs):
    """C consumes row-major buffers natively; prepare = the uint8 zero-copy
    views the ctypes call needs (timed in adapter_total)."""
    if inputs['kind'] == 'single':
        return [trial_fixtures.call_args(inputs)]
    return [tuple(c['args']) for c in inputs['calls']]


def kernel_only(prepared):
    outs = [lw_native.primary(*args, gang=GANG) for args in prepared]
    return np.concatenate([o.reshape(-1, 7) for o in outs], axis=0)


def adapter_total(inputs):
    return kernel_only(prepare(inputs))


def identity():
    lib_sha = {}
    for gang in (4, GANG):
        p = CAND / f'liblw_native_g{gang}.dylib'
        if p.exists():
            lib_sha[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    return {
        'variant': 'C_native_ispc_g8',
        'gang': GANG,
        'effective_threads': 1,
        'thread_control_method': 'none (synchronous single-thread kernel)',
        'adapter': 'lw_native.primary as-shipped (no chunking)',
        'binary_sha256': lib_sha,
        'adapter_sha256': hashlib.sha256((CAND / 'lw_native.py').read_bytes()).hexdigest(),
        'numpy': np.__version__,
    }
