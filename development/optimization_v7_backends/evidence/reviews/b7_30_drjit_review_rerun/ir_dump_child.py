import os
import sys

os.environ["DRJIT_CACHE_DIR"] = "/tmp/b7_30_review_drjitcache_ir"
os.makedirs(os.environ["DRJIT_CACHE_DIR"], exist_ok=True)
os.environ["DRJIT_LOG_LEVEL"] = "4"

import numpy as np
sys.path.insert(0, "/Users/alansynn/Workspace/solweig-v7-drjit/experiments/optimization_v7/drjit")
import drjit as dr
from llvm_longwave import configure_runtime, longwave_primary_drjit

configure_runtime(threads=4)
dr.set_log_level(4)
dr.set_flag(dr.JitFlag.PrintIR, True)

def make_block(B, P, spec):
    rng = np.random.default_rng(42)
    sh = rng.random((B, P), dtype=np.float32)
    vs = rng.random((B, P), dtype=np.float32)
    vb = rng.random((B, P), dtype=np.float32)
    sun = rng.random((B, P)) < 0.5
    shade = rng.random((B, P)) < 0.5
    solid = rng.random(P, dtype=np.float32)
    sine = rng.random(P, dtype=np.float32)
    cosine = rng.random(P, dtype=np.float32)
    directions = np.zeros((P, 4), dtype=np.float32)
    gate = np.zeros((P, 4), dtype=bool)
    solar_gate = rng.random(P) < 0.5
    if spec == "f64":
        s_sun, s_sh = np.float64(300.0), np.float64(400.0)
    else:
        s_sun, s_sh = np.float32(300.0), np.float32(400.0)
    lup = rng.random(B, dtype=np.float32)
    return [sh, vs, vb, sun, shade, solid, sine, cosine, directions, gate,
            solar_gate, np.ascontiguousarray(rng.random(P, dtype=np.float32)),
            np.ascontiguousarray(rng.random(P, dtype=np.float32)), s_sun, s_sh,
            lup, np.float32(0.618)]

spec = sys.argv[1]
out = longwave_primary_drjit(*make_block(8, 3, spec))
dr.eval()
print(f"DONE {spec} out0[0]={out[0, 0]!r}", file=sys.__stdout__)
