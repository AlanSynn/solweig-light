#!/usr/bin/env python3
"""C6-80 decoder re-measurement: original vs prepared visibility decode.

Parameterized re-run of the C6-50 dev-tier probe
(tests/optimization_v6/decoder/probe_decoder_timing.py; construction reused
verbatim via that module's conftest builders -- read-only import, no test
file is modified) at the C6-80 shapes 128 and 256 square, 153 patches, under
both block strides: the probe's original 128-pixel stride and the production
block_pixels=1024 partition.

Run: decoder_probe_v2.py --size 128 --out <json> [--stride 128] [--repeat 30]
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path

PARSER = argparse.ArgumentParser(description=__doc__)
PARSER.add_argument("--size", type=int, required=True)
PARSER.add_argument("--stride", type=int, default=128)
PARSER.add_argument("--repeat", type=int, default=30)
PARSER.add_argument("--decoder-tests", default=str(Path(
    "/Users/alansynn/Workspace/solweig-light-claude-v5/tests/optimization_v6/decoder")))
PARSER.add_argument("--site", default="/Users/alansynn/Workspace/solweig-light-claude-v5/src")
PARSER.add_argument("--out", required=True)
ARGS = PARSER.parse_args()

import os  # noqa: E402
for _name in ("BLIS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS",
              "NUMEXPR_NUM_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
              "VECLIB_MAXIMUM_THREADS"):
    os.environ[_name] = "2"  # census cap convention, matches recorded C6-50 probe

sys.path.insert(0, str(Path(ARGS.site).resolve()))
sys.path.insert(0, str(Path(ARGS.decoder_tests).resolve()))

import numpy as np  # noqa: E402
import numba  # noqa: E402
from conftest import packed, retained_route  # noqa: E402  (read-only reuse)
from solweig_light.geometry.visibility import LazyDiffVisibility  # noqa: E402
from solweig_light.geometry.visibility_compiled import (  # noqa: E402
    decode_block, diff_from_shared_decoded)
from solweig_light.geometry.visibility_prepared import (  # noqa: E402
    decode_shortwave_block, prepare_channels)

ROWS = COLS = ARGS.size
PATCHES = 153
STRIDE = ARGS.stride
REPEAT = ARGS.repeat


def timeit(fn, repeat=REPEAT):
    best = float("inf")
    total = 0.0
    for _ in range(repeat):
        begin = time.perf_counter()
        fn()
        elapsed = time.perf_counter() - begin
        best = min(best, elapsed)
        total += elapsed
    return {"best_ms": best * 1e3, "mean_ms": total / repeat * 1e3}


def main() -> int:
    rng = np.random.default_rng(20260921)
    shadow, vegetation, building = (packed(rng, ROWS, COLS, PATCHES, ("binary", "ternary"))
                                    for _ in range(3))
    diffuse = LazyDiffVisibility(shadow, vegetation)
    pixels = ROWS * COLS
    blocks = [(start, min(start + STRIDE, pixels)) for start in range(0, pixels, STRIDE)]

    with retained_route():
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

        buffers = [np.empty((STRIDE, PATCHES), dtype=np.float32) for _ in range(4)]

        def prepared_buffered_sequence():
            for start, stop in blocks:
                prepared.decode(start, stop, PATCHES, buffers)

        result = {
            "schema": "sw6-portfolio-decoder-probe-v1",
            "size": [ROWS, COLS], "patches": PATCHES, "stride": STRIDE,
            "blocks": len(blocks), "repeat": REPEAT,
            "native_threads": int(numba.get_num_threads()),
            "note": "single-lease dev tier, unrelated OS load recorded by scheduler; "
                    "no statistical claims; warm JIT (compile excluded)",
            "python": platform.python_version(),
            "numba": numba.__version__, "numpy": np.__version__,
            "original_4x_decode_block": timeit(original_sequence),
            "prepared_decode": timeit(prepared_sequence),
            "prepared_decode_caller_buffers": timeit(prepared_buffered_sequence),
            "prepare_only": timeit(
                lambda: prepare_channels(shadow, vegetation, building, diffuse)),
            "dropin_single_block": timeit(
                lambda: decode_shortwave_block(shadow, vegetation, building, diffuse,
                                               blocks[0][0], blocks[0][1], PATCHES)),
        }
    out = Path(ARGS.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps({"out": str(out), "size": ROWS, "stride": STRIDE,
                      "original_ms": result["original_4x_decode_block"]["best_ms"],
                      "prepared_ms": result["prepared_decode"]["best_ms"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
