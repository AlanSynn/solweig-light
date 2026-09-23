"""Dev-tier timing probe for the prepared visibility decoder (NOT a test).

Compares the accepted per-channel decode sequence against the prepared
one-entry decode (with and without caller buffers) plus prepare-only cost on
a 128x128 scene, 153 patches, production block partition. Runs on a contended
development machine: numbers are recorded for evidence only, no claims.

Output: JSON to the path given as argv[1] (default: stdout).
"""
import json
import platform
import sys
import time
import pathlib

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / 'src'))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from conftest import packed, retained_route  # noqa: E402

from solweig_light.geometry.visibility import LazyDiffVisibility  # noqa: E402
from solweig_light.geometry.visibility_compiled import (  # noqa: E402
    decode_block, diff_from_shared_decoded)
from solweig_light.geometry.visibility_prepared import (  # noqa: E402
    decode_shortwave_block, prepare_channels)

ROWS = COLS = 128
PATCHES = 153
REPEAT = 30


def timeit(fn, repeat=REPEAT):
    best = float('inf')
    total = 0.0
    for _ in range(repeat):
        begin = time.perf_counter()
        fn()
        elapsed = time.perf_counter() - begin
        best = min(best, elapsed)
        total += elapsed
    return {'best_ms': best * 1e3, 'mean_ms': total / repeat * 1e3}


def main():
    out = {
        'python': sys.version.split()[0],
        'platform': platform.platform(),
        'processor': platform.processor(),
        'size': [ROWS, COLS], 'patches': PATCHES, 'repeat': REPEAT,
        'note': 'contended development tier; recording only, no claims',
    }
    try:
        import numba
        out['numba'] = numba.__version__
    except ImportError:
        out['numba'] = None
    try:
        import numpy
        out['numpy'] = numpy.__version__
    except ImportError:
        out['numpy'] = None

    rng = np.random.default_rng(20260921)
    shadow, vegetation, building = (packed(rng, ROWS, COLS, PATCHES, ('binary', 'ternary'))
                                    for _ in range(3))
    diffuse = LazyDiffVisibility(shadow, vegetation)
    blocks = [(start, min(start + 128, ROWS * COLS))
              for start in range(0, ROWS * COLS, 128)]

    with retained_route():
        # Warm every path once (JIT compile excluded from measurement).
        for start, stop in blocks:
            decode_block(shadow, start, stop, PATCHES)
            decode_block(vegetation, start, stop, PATCHES)
            decode_block(building, start, stop, PATCHES)
            sh = decode_block(shadow, start, stop, PATCHES)
            vs = decode_block(vegetation, start, stop, PATCHES)
            diff_from_shared_decoded(shadow, vegetation, diffuse, sh, vs,
                                     start, stop, PATCHES)
        prepared = prepare_channels(shadow, vegetation, building, diffuse)
        for start, stop in blocks:
            prepared.decode(start, stop, PATCHES)

        def original_sequence():
            for start, stop in blocks:
                sh = decode_block(shadow, start, stop, PATCHES)
                vs = decode_block(vegetation, start, stop, PATCHES)
                decode_block(building, start, stop, PATCHES)
                diff_from_shared_decoded(shadow, vegetation, diffuse, sh, vs,
                                         start, stop, PATCHES)

        def prepared_sequence():
            for start, stop in blocks:
                prepared.decode(start, stop, PATCHES)

        buffers = [np.empty((128, PATCHES), dtype=np.float32) for _ in range(4)]

        def prepared_buffered_sequence():
            for start, stop in blocks:
                prepared.decode(start, stop, PATCHES, buffers)

        out['original_4x_decode_block'] = timeit(original_sequence)
        out['prepared_decode'] = timeit(prepared_sequence)
        out['prepared_decode_caller_buffers'] = timeit(prepared_buffered_sequence)
        out['prepare_only'] = timeit(
            lambda: prepare_channels(shadow, vegetation, building, diffuse), REPEAT)
        # The drop-in wrapper adds one prepare per call (per-block use pattern).
        start, stop = blocks[0]
        out['dropin_single_block'] = timeit(
            lambda: decode_shortwave_block(shadow, vegetation, building, diffuse,
                                           start, stop, PATCHES))

    text = json.dumps(out, indent=2)
    if len(sys.argv) > 1:
        pathlib.Path(sys.argv[1]).write_text(text + '\n')
    print(text)


if __name__ == '__main__':
    main()
