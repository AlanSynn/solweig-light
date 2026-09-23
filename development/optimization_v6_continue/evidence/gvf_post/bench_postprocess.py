"""C6-31 raw timing record: untouched NumPy postprocess vs typed kernel.

DEVELOPMENT TIER: contended shared host, single-cell medians over a warm
loop. These numbers are recorded for selection only -- no performance claim
is made from them (VALIDATION_POLICY.md).
"""
import os
import statistics
import sys
import time
from pathlib import Path

import numba
import numpy as np

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'src'))

from solweig_light.radiation.ground_view import _postprocess_block  # noqa: E402
from solweig_light.radiation.gvf_postprocess import gvf_postprocess_block  # noqa: E402

BLOCK_ROWS = 32  # production block_rows in engine.gvf_2018a


def make_block(rows, cols, seed=0):
    rng = np.random.default_rng(seed)
    block = np.empty((16, rows, cols), dtype=np.float32)
    for index in range(16):
        block[index] = rng.integers(0, 6, (rows, cols)).astype(np.float32)
    aux = {
        'buildings': (rng.random((rows, cols)) < 0.4).astype(np.float32),
        'facesh': rng.integers(-1, 3, (rows, cols)).astype(np.float32),
        'lup_term': (rng.standard_normal((rows, cols)) * 10).astype(np.float32),
        'alb_term': (rng.standard_normal((rows, cols)) * 0.1).astype(np.float32),
        'nosh_term': (rng.standard_normal((rows, cols)) * 0.1).astype(np.float32),
    }
    return block, aux


def time_call(label, call, repeat=60):
    call()  # warm
    samples = []
    for _ in range(repeat):
        start = time.perf_counter()
        call()
        samples.append(time.perf_counter() - start)
    median = statistics.median(samples) * 1e3
    print(f'{label:>28}: median {median:8.3f} ms/call  (min {min(samples)*1e3:.3f})')
    return median


def main():
    print(f'numba {numba.__version__} numpy {np.__version__} '
          f'threads={numba.get_num_threads()} pid={os.getpid()}')
    print('contended development tier; raw medians only, no claims')
    for cols in (128, 256, 1024):
        rows = BLOCK_ROWS
        block, aux = make_block(rows, cols)
        first, second = np.float64(3.0), np.float64(2.0)

        def original():
            planes = tuple(block[index] for index in range(16))
            _postprocess_block(planes, aux['buildings'], aux['facesh'], aux['lup_term'],
                               aux['alb_term'], aux['nosh_term'], first, second)

        def candidate(parallel=False):
            gvf_postprocess_block(block, aux['buildings'], aux['facesh'], aux['lup_term'],
                                  aux['alb_term'], aux['nosh_term'], first, second,
                                  parallel=parallel)

        print(f'-- block (16, {rows}, {cols}) --')
        base = time_call('original numpy', original)
        serial = time_call('candidate serial', candidate)
        parallel = time_call('candidate parallel', lambda: candidate(parallel=True))
        print(f'   serial/original ratio {serial/base:.3f}, parallel/original {parallel/base:.3f}')


if __name__ == '__main__':
    main()
