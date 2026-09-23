"""B7-30: verify literal-divisor folding hazard + dump fresh IR for BOTH
specializations of the shipped kernel and count FP contraction evidence."""
import io
import os
import re
import sys
from contextlib import redirect_stderr

import numpy as np

os.environ["DRJIT_CACHE_DIR"] = "/tmp/b7_30_review_drjitcache"
os.makedirs(os.environ["DRJIT_CACHE_DIR"], exist_ok=True)
sys.path.insert(0, "/Users/alansynn/Workspace/solweig-v7-drjit/experiments/optimization_v7/drjit")
import drjit as dr
import drjit.llvm as ll
from llvm_longwave import configure_runtime, _pi_divisor

rec = configure_runtime(threads=4)
print("runtime:", rec)

# --- hazard A: literal divisor folds to fmul even with FastMath OFF ---
x = ll.Float(np.linspace(-3, 3, 64, dtype=np.float32))
y_lit = x / ll.Float(3.0)          # literal divisor
buf = ll.Float(np.array([3.0], dtype=np.float32))
y_data = x / dr.gather(ll.Float, buf, ll.UInt(0))  # runtime data divisor
dr.eval(y_lit, y_data)
a = y_lit.numpy().view(np.uint32)
b = y_data.numpy().view(np.uint32)
nd = int(np.count_nonzero(a != b))
print(f"hazard probe: literal vs data divisor (d=3.0), 64 linspace values: {nd}/64 differ bitwise")

# show an example pair
i = int(np.flatnonzero(a != b)[0]) if nd else 0
print(f"  example: x={x.numpy()[i]!r} lit={np.float32(y_lit.numpy()[i])!r} "
      f"data={np.float32(y_data.numpy()[i])!r} numpy_true={np.float32(np.float32(x.numpy()[i])/np.float32(3.0))!r}")

# --- fresh IR dump of BOTH shipped kernel specializations ---
from llvm_longwave import _kern_f64, _kern_f32, _run_symbolic, _pack, longwave_primary_drjit

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
    rf = np.float32(0.618)
    return [sh, vs, vb, sun, shade, solid, sine, cosine, directions, gate,
            solar_gate, np.ascontiguousarray(rng.random(P, dtype=np.float32)),
            np.ascontiguousarray(rng.random(P, dtype=np.float32)), s_sun, s_sh, lup, rf]

for spec in ("f64", "f32"):
    args = make_block(8, 3, spec)
    dr.set_log_level(4)
    dr.set_flag(dr.JitFlag.PrintIR, True)
    fd2 = os.dup(2)
    tmpname = f"/tmp/b7_30_drjit_review/logs/fd2_{spec}.txt"
    tmpf = open(tmpname, "w")
    os.dup2(tmpf.fileno(), 2)
    try:
        out = longwave_primary_drjit(*args)
        dr.sync_thread()
    finally:
        sys.stderr.flush()
        os.dup2(fd2, 2)
        os.close(fd2)
        tmpf.close()
        dr.set_flag(dr.JitFlag.PrintIR, False)
    ir = open(tmpname).read()
    path = f"/tmp/b7_30_drjit_review/logs/fresh_ir_{spec}.txt"
    open(path, "w").write(ir)
    counts = {
        "fdiv": len(re.findall(r"\bfdiv\b", ir)),
        "fma": len(re.findall(r"llvm\.fma|fmuladd", ir)),
        "fast_flagged_ops": len(re.findall(r"\bf(add|sub|mul|div)\b.*fast", ir)),
        "fptrunc": len(re.findall(r"\bfptrunc\b", ir)),
        "fpext": len(re.findall(r"\bfpext\b", ir)),
        "masked_gather": len(re.findall(r"masked\.gather", ir)),
        "masked_scatter": len(re.findall(r"masked\.scatter", ir)),
        "kernels": len(re.findall(r"define void @drjit_", ir)),
    }
    print(f"{spec} kernel IR: {counts}  -> {path}")
