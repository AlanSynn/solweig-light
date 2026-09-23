"""B7-30 independent adversarial rerun: edge domains vs numba baseline.

Own cases (not the author's script): B=0/1/17, P=1/2/153, NaN/Inf/-0.0,
denormals, f64/f32/python-float surfaces, stride-12 sky views, canaries,
5 rejections, reflection-divide distinguishing-value probe.
Bitwise (uint32) vs BOTH numba baselines (serial + parallel).
"""
import hashlib
import json
import sys

import numpy as np

sys.path.insert(0, "/Users/alansynn/Workspace/solweig-v7-drjit/experiments/optimization_v7/drjit")
sys.path.insert(0, "/Users/alansynn/Workspace/solweig-v7-drjit/src")

from llvm_longwave import longwave_primary_drjit, Unsupported  # noqa: E402
from solweig_light.radiation.cylinder_longwave import (  # noqa: E402
    _longwave_primary, _longwave_primary_serial)

rng = np.random.default_rng(20260922)
results = []


def canaries(args):
    return [hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
            for a in args if isinstance(a, np.ndarray)]


def check_canaries(args, before):
    after = canaries(args)
    return before == after


def make_block(B, P, *, f64_surface=True, gate=None, stride12=False,
               poison=None, surf="f64"):
    sh = rng.random((B, P), dtype=np.float32)
    vs = rng.random((B, P), dtype=np.float32)
    vb = rng.random((B, P), dtype=np.float32)
    sun = rng.random((B, P)) < 0.5
    shade = rng.random((B, P)) < 0.5
    solid = rng.random(P, dtype=np.float32)
    sine = rng.random(P, dtype=np.float32)
    cosine = rng.random(P, dtype=np.float32)
    directions = np.zeros((P, 4), dtype=np.float32)
    gate_arr = np.zeros((P, 4), dtype=bool)
    if gate is None:
        solar_gate = rng.random(P) < 0.5
    else:
        solar_gate = np.full(P, gate, dtype=bool)
    sky_tab = rng.random((P, 3), dtype=np.float32)
    if stride12:
        sky_down = sky_tab[:, 2]
        sky_side = sky_tab[:, 2]
        assert sky_down.strides[0] == 12
    else:
        sky_down = np.ascontiguousarray(rng.random(P, dtype=np.float32))
        sky_side = np.ascontiguousarray(rng.random(P, dtype=np.float32))
    if surf == "f64":
        surface_sun = np.float64(rng.uniform(100, 400))
        surface_sh = np.float64(rng.uniform(300, 450))
    elif surf == "f32":
        surface_sun = np.float32(rng.uniform(100, 400))
        surface_sh = np.float32(rng.uniform(300, 450))
    else:
        surface_sun = float(rng.uniform(100, 400))
        surface_sh = float(rng.uniform(300, 450))
    lup = (rng.random(B, dtype=np.float32) * 300).astype(np.float32)
    rf = np.float32(0.6180339887)
    args = [sh, vs, vb, sun, shade, solid, sine, cosine, directions,
            gate_arr, solar_gate, sky_down, sky_side, surface_sun,
            surface_sh, lup, rf]
    if poison:
        poison(args)
    return args


def run_case(name, args, modes=("symbolic", "evaluated"), expect_reject=False):
    rec = {"case": name, "modes": list(modes)}
    before = canaries(args)
    try:
        ref_s = _longwave_primary_serial(*args)
        ref_p = _longwave_primary(*args)
    except Exception as e:
        rec["baseline_error"] = repr(e)
        results.append(rec)
        return rec
    rec["ok"] = True
    rec["unmodified"] = check_canaries(args, before)
    for mode in modes:
        try:
            out = longwave_primary_drjit(*args, loop_mode=mode)
        except Unsupported as e:
            rec[f"{mode}_rejected"] = str(e)
            continue
        rec[f"{mode}_bitwise_serial"] = bool(
            np.array_equal(out.view(np.uint32), ref_s.view(np.uint32)))
        rec[f"{mode}_bitwise_parallel"] = bool(
            np.array_equal(out.view(np.uint32), ref_p.view(np.uint32)))
        rec[f"{mode}_shape_ok"] = out.shape == ref_s.shape and out.dtype == np.float32
    rec["ok"] = all(v is True for k, v in rec.items()
                    if k.endswith(("_bitwise_serial", "_bitwise_parallel", "unmodified", "shape_ok")))
    results.append(rec)
    return rec


def reject_case(name, args):
    before = canaries(args)
    try:
        longwave_primary_drjit(*args)
        results.append({"case": name, "rejected": False, "ok": False})
        return
    except Unsupported as e:
        results.append({"case": name, "rejected": True, "unmodified": check_canaries(args, before),
                        "msg": str(e)[:80], "ok": check_canaries(args, before)})
        return
    except Exception as e:
        results.append({"case": name, "rejected": "other", "msg": repr(e)[:80], "ok": False})


def poison_nan(args):
    args[0][0, 0] = np.nan
    args[1][0, 0] = np.inf
    args[2][1 % args[2].shape[0], 0] = -np.inf


# --- admission cases ---
run_case("B17_P153_f64", make_block(17, 153))
run_case("B1_P1_gate", make_block(1, 1, gate=True))
run_case("B1_P1_nogate", make_block(1, 1, gate=False))
run_case("B4_P2", make_block(4, 2))
run_case("B0_P153", make_block(0, 153))
run_case("nan_inf_vis", make_block(5, 9, poison=poison_nan))
run_case("nan_lup", make_block(5, 9, poison=lambda a: a[15].__setitem__(2, np.nan)))
run_case("inf_skydown",
         make_block(5, 9, poison=lambda a: (a[11].__setitem__(3, np.inf), a[12].__setitem__(3, -np.inf))))
run_case("neg_zero_sine", make_block(5, 9, poison=lambda a: a[7].__setitem__(4, np.float32(-0.0))))
run_case("neg_zero_vs", make_block(5, 9, poison=lambda a: a[1].__setitem__((0, 0), np.float32(-0.0))))
run_case("denormal_vis", make_block(5, 9, poison=lambda a: (
    a[0].__setitem__((0, 0), np.float32(1e-40)), a[1].__setitem__((0, 0), np.float32(1e-45)),
    a[2].__setitem__((0, 0), np.float32(0.999999)))))
run_case("f32_surface", make_block(17, 153, surf="f32"))
run_case("pyfloat_surface", make_block(17, 153, surf="pyfloat"))
run_case("stride12_sky", make_block(17, 153, stride12=True))
run_case("all_gate_true", make_block(9, 33, gate=True))
run_case("all_gate_false", make_block(9, 33, gate=False))
run_case("vis_all_zero", make_block(9, 33, poison=lambda a: (
    a[0].fill(0.0), a[1].fill(0.0), a[2].fill(0.0))))
run_case("vis_all_two", make_block(9, 33, poison=lambda a: (
    a[0].fill(2.0), a[1].fill(2.0), a[2].fill(2.0))))

# --- rejections (pre-launch, must raise Unsupported, inputs untouched) ---
good = make_block(4, 5)
reject_case("reject_f64_visibility",
            [good[0].astype(np.float64)] + list(good[1:]))
g2 = make_block(4, 5, surf="f32")
reject_case("reject_mixed_surface_specs",
            list(g2[:13]) + [np.float64(300.0), g2[14]] + list(g2[15:]))
reject_case("reject_pyfloat_rf",
            list(good[:16]) + [0.5])
big = make_block(4, 610)
reject_case("reject_P610", big)
g3 = make_block(4, 5)
reject_case("reject_f64_sun",
            list(g3[:3]) + [g3[3].astype(np.float64)] + list(g3[4:]))

# --- reflection divide: distinguishing-value probe ---
PI = np.float32(np.pi)
recip = np.float32(1.0 / PI)  # RN32(1/pi): what a reciprocal multiply would use
xs = np.frombuffer(rng.bytes(4 * 262144), dtype=np.float32)
finite = xs[np.isfinite(xs) & (xs != 0)]
true_div = (finite / PI).astype(np.float32)
recip_mul = (finite * recip).astype(np.float32)
diff = np.flatnonzero(true_div.view(np.uint32) != recip_mul.view(np.uint32))
probe = {"n_random": int(finite.size), "differing": int(diff.size)}
if diff.size:
    # hunt for a distinguishable value that survives r2 = f32(f32(2x)*0.5) == 2x exactly
    chosen = None
    for k in diff[:4096]:
        x2 = np.float32(2.0) * finite[k]  # feed as sky_down; A0 = sky_down; r2 = x
        if np.float32(np.float32(x2) * np.float32(0.5)) == finite[k] and np.isfinite(finite[k]):
            chosen = finite[k]
            break
    probe["chosen_x"] = float(chosen) if chosen is not None else None
    if chosen is not None:
        P, B = 1, 1
        sh = np.array([[0.0]], dtype=np.float32)      # mask true
        vs = np.array([[5.0]], dtype=np.float32)      # sky false, veg false
        vb = np.array([[5.0]], dtype=np.float32)
        sun = np.array([[False]]); shade = np.array([[False]])
        solid = np.array([1.0], dtype=np.float32)
        sine = np.array([1.0], dtype=np.float32)
        cosine = np.array([1.0], dtype=np.float32)
        directions = np.zeros((P, 4), dtype=np.float32)
        gate_arr = np.zeros((P, 4), dtype=bool)
        solar_gate = np.array([False])
        sky_down = np.array([np.float32(2.0) * chosen], dtype=np.float32)
        sky_side = np.array([0.0], dtype=np.float32)
        args = [sh, vs, vb, sun, shade, solid, sine, cosine, directions, gate_arr,
                solar_gate, sky_down, sky_side, np.float64(1.0), np.float64(1.0),
                np.array([0.0], dtype=np.float32), np.float32(1.0)]
        out = longwave_primary_drjit(*args)
        ref_s = _longwave_primary_serial(*args)
        expected_true = np.float32(chosen / PI)
        expected_recip = np.float32(chosen * recip)
        probe["candidate_out1_bits"] = hex(np.uint32(out[0, 1].view(np.uint32)))
        probe["baseline_out1_bits"] = hex(np.uint32(ref_s[0, 1].view(np.uint32)))
        probe["true_div_bits"] = hex(np.uint32(expected_true.view(np.uint32)))
        probe["recip_mul_bits"] = hex(np.uint32(expected_recip.view(np.uint32)))
        probe["candidate_matches_true_div"] = bool(
            out[0, 1].view(np.uint32) == expected_true.view(np.uint32))
        probe["candidate_matches_baseline"] = bool(
            np.array_equal(out.view(np.uint32), ref_s.view(np.uint32)))
results.append({"case": "reflection_divide_probe", **probe})

ok = all(r.get("ok", True) for r in results if "case" in r)
summary = {"schema": "b7-30-independent-adversarial-rerun", "all_ok": ok,
           "n_cases": len(results)}
print(json.dumps(summary, indent=1))
print(json.dumps(results, indent=1, default=str)[:9000])
json.dump({"summary": summary, "results": results},
          open("/tmp/b7_30_drjit_review/logs/rerun_adversarial.json", "w"), indent=1, default=str)
sys.exit(0 if ok else 1)
