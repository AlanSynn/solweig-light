"""B7-30 divide probe, fixed: two-patch block where out1 == f32(r2/pi_bits).

patch0: sh=1, vs=1, vb=1  -> sky true (A0 += sky_down[0] = 2x), mask false
patch1: sh=0, vs=5, vb=2  -> sky false, mask true, solid=cosine=1, sine=0
gate false everywhere, lup=0, rf=1.0f.
=> r0=2x, r1=2x, r2=x, reflected=f32(x/pi); A9 = reflected; out1 = reflected.
out0 = A0 = 2x (cross-check).
"""
import sys
import numpy as np

sys.path.insert(0, "/Users/alansynn/Workspace/solweig-v7-drjit/experiments/optimization_v7/drjit")
sys.path.insert(0, "/Users/alansynn/Workspace/solweig-v7-drjit/src")
from llvm_longwave import longwave_primary_drjit  # noqa: E402
from solweig_light.radiation.cylinder_longwave import _longwave_primary_serial  # noqa: E402

PI = np.float32(np.pi)
recip = np.float32(1.0 / PI)

# rate check on standard-normal values (the author's claimed probe domain)
rng = np.random.default_rng(7)
xs = rng.standard_normal(262144).astype(np.float32)
nd = int(np.count_nonzero((xs / PI).view(np.uint32) != (xs * recip).view(np.uint32)))
print(f"standard-normal domain: {nd}/262144 values where x/pi != x*RN32(1/pi)")

# arbitrary-bit-pattern domain (includes denormals)
raw = np.frombuffer(np.random.default_rng(9).bytes(4 * 262144), dtype=np.float32)
fin = raw[np.isfinite(raw) & (raw != 0)]
diff = np.flatnonzero((fin / PI).view(np.uint32) != (fin * recip).view(np.uint32))
print(f"arbitrary-bits domain : {diff.size}/{fin.size} differing")

def block_for(x):
    x = np.float32(x)
    P = 2
    sh = np.array([[1.0, 0.0]], dtype=np.float32)
    vs = np.array([[1.0, 5.0]], dtype=np.float32)
    vb = np.array([[1.0, 2.0]], dtype=np.float32)
    sun = np.zeros((1, P), dtype=bool)
    shade = np.zeros((1, P), dtype=bool)
    solid = np.array([0.0, 1.0], dtype=np.float32)   # p0 irrelevant (veg/sky chains don't use solid for sky)
    sine = np.array([0.0, 0.0], dtype=np.float32)
    cosine = np.array([0.0, 1.0], dtype=np.float32)
    directions = np.zeros((P, 4), dtype=np.float32)
    gate_arr = np.zeros((P, 4), dtype=bool)
    solar_gate = np.zeros(P, dtype=bool)
    sky_down = np.array([np.float32(2.0) * x, 0.0], dtype=np.float32)
    sky_side = np.array([0.0, 0.0], dtype=np.float32)
    args = [sh, vs, vb, sun, shade, solid, sine, cosine, directions, gate_arr,
            solar_gate, sky_down, sky_side, np.float64(1.0), np.float64(1.0),
            np.array([0.0], dtype=np.float32), np.float32(1.0)]
    return args, x

n_tested = 0
n_candidate_true = 0
n_baseline_true = 0
n_candidate_matches_baseline = 0
worst = None
for k in diff[:2048]:
    x = fin[k]
    two_x = np.float32(2.0) * x
    if not np.isfinite(two_x) or np.float32(two_x * np.float32(0.5)) != x:
        continue  # r2 must come back to x exactly
    args, x = block_for(x)
    out = longwave_primary_drjit(*args)
    ref = _longwave_primary_serial(*args)
    true_bits = (np.float32(x / PI)).view(np.uint32)
    recip_bits = (np.float32(x * recip)).view(np.uint32)
    c_bits = out[0, 1].view(np.uint32)
    b_bits = ref[0, 1].view(np.uint32)
    # cross-check out0 == 2x
    assert np.array_equal(out.view(np.uint32), ref.view(np.uint32)), "candidate vs baseline mismatch"
    assert out[0, 0].view(np.uint32) == two_x.view(np.uint32), "A0 path sanity"
    n_tested += 1
    n_candidate_true += int(c_bits == true_bits)
    n_baseline_true += int(b_bits == true_bits)
    n_candidate_matches_baseline += int(c_bits == b_bits)
    if worst is None and c_bits != recip_bits:
        worst = {"x": float(x), "cand": hex(c_bits), "recip": hex(recip_bits),
                 "true": hex(true_bits)}
print(f"distinguishable x tested: {n_tested}")
print(f"candidate == TRUE fdiv  : {n_candidate_true}/{n_tested}")
print(f"baseline  == TRUE fdiv  : {n_baseline_true}/{n_tested}")
print(f"candidate != recip-mul  : (first differing from reciprocal) {worst}")
