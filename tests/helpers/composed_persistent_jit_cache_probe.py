"""Tiny real-kernel probe for explicit composed JIT cache dependencies."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np

from exact_persistent_jit_cache_probe import descriptor, origin


TESTS_ROOT = Path(__file__).resolve().parents[1]


def identities(modules):
    return {
        f"{module.__name__}.{name}": getattr(module, name).py_func.__qualname__
        for module, names in modules for name in names
    }


def packed_case():
    sys.path.insert(0, str(TESTS_ROOT / "optimization_v8/stream"))
    from stream_test_helpers import make_case

    return make_case(8, 3, seed=19, modes_cycle=("binary",))


def longwave():
    from solweig_light._native_dispatch import direct_aosoa, lw_b_control, lw_batch

    case = packed_case()
    from stream_test_helpers import stream_plan

    plan = stream_plan(case, 8, block_pixels=8)
    assert plan is not None
    try:
        outputs = {}
        for parallel in (False, True):
            output = lw_batch.execute(plan, parallel=parallel)
            assert output is not None and np.isfinite(output).all()
            outputs[str(parallel)] = descriptor(output)
    finally:
        plan.close()
    assert outputs["False"] == outputs["True"]
    modules = (
        (lw_batch, ("_preflight_blocks", "_batch", "_batch_serial")),
        (direct_aosoa, ("_produce_patchmajor", "_preflight_packed",
                        "_classes_table_masked_aosoa")),
        (lw_b_control, ("lw_primary_b_serial",)),
    )
    return outputs, modules


def shortwave():
    from solweig_light._native_dispatch import direct_aosoa, lw_batch, sw_batch
    from solweig_light.geometry.visibility import LazyDiffVisibility

    case = packed_case()
    values = case["values"]
    values["diffsh"] = LazyDiffVisibility(values["shmat"], values["vegshmat"])
    lum = np.array([0.2, 0.3, 0.4], dtype=np.float32)
    outputs = {}
    for parallel in (False, True):
        initial = np.arange(7 * 8, dtype=np.float32).reshape(7, 8) / np.float32(8)
        output = sw_batch.execute(values, case["geometry"], case["prepared"],
            lum, case["sun_surface"], case["shade_surface"], 8, initial,
            parallel=parallel)
        assert output is not None and np.isfinite(output).all()
        outputs[str(parallel)] = descriptor(output)
    assert outputs["False"] == outputs["True"]
    modules = (
        (sw_batch, ("_block", "_batch", "_batch_serial", "_finite_output")),
        (lw_batch, ("_preflight_blocks",)),
        (direct_aosoa, ("_produce_patchmajor", "_preflight_packed",
                        "_classes_table_masked_aosoa")),
    )
    return outputs, modules


def ground_view():
    from solweig_light.radiation import ground_view, gvf_batch, gvf_prepared

    sys.path.insert(0, str(TESTS_ROOT / "optimization_v6/gvf_prepare"))
    from gvf_prepare_cases import build_scene, snapshots

    scene = build_scene(6, 7, first=1, second=2, seed=3)
    with np.errstate(invalid="ignore", divide="ignore"):
        step = gvf_prepared.prepare_gvf_step(**snapshots(scene))
        assert step is not None
        output = gvf_batch.run(step, 6, 7, block_rows=2)
    assert output is not None and np.isfinite(output).all()
    modules = (
        (gvf_batch, ("_run_owner", "_run", "_finite_accumulators")),
        (ground_view, ("_gather_block_serial",)),
    )
    return descriptor(output), modules


def sky_view():
    from solweig_light.geometry import svf

    fields = tuple(np.zeros((2, 3), dtype=np.float32) for _ in range(15))
    masks = tuple(np.full((2, 3), value, dtype=np.float32)
                  for value in (0.25, 0.5, 1.0))
    weights = np.array([0.2, 0.3], dtype=np.float32)
    directional = np.array([0.4, 0.6], dtype=np.float32)
    directions = (True, False, True, True)
    svf._accumulate_patch_f32(fields, masks, weights, directional, directions)
    return [descriptor(field) for field in fields], ((svf, ("_accumulate_patch_f32",)),)


def visibility():
    from solweig_light.geometry import visibility_compiled as compiled
    from solweig_light.geometry.visibility import LazyDiffVisibility, PackedVisibility

    shadow = np.array([[[0, 1, 2], [1, 0, 2], [1, 1, 0], [0, 1, 1]]], dtype=np.float32)
    vegetation = np.array([[[1, 0, 2], [0, 1, 1], [1, 0, 1], [1, 1, 0]]], dtype=np.float32)
    sh = PackedVisibility.from_dense(shadow)
    vs = PackedVisibility.from_dense(vegetation)
    direct = compiled.decode_block(sh, 0, 4, 3)
    diffuse = compiled.decode_block(LazyDiffVisibility(sh, vs), 0, 4, 3)
    assert direct is not None and diffuse is not None
    assert np.isfinite(direct).all() and np.isfinite(diffuse).all()
    modules = ((compiled, ("_decode", "_diff", "_decode_diff")),)
    return {"direct": descriptor(direct), "diffuse": descriptor(diffuse)}, modules


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("lw", "sw", "gvf", "svf", "visibility"), required=True)
    parser.add_argument("--order")  # Shared parent-process probe protocol.
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    outputs, modules = {"lw": longwave, "sw": shortwave,
                        "gvf": ground_view, "svf": sky_view,
                        "visibility": visibility}[args.mode]()
    result = {
        "outputs": outputs,
        "origins": {module.__name__: origin(module) for module, _ in modules},
        "cache_qualnames": identities(modules),
    }
    args.result.write_text(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
