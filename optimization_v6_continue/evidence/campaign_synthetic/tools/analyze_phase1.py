#!/usr/bin/env python3
"""C6-101r PHASE 3 analysis: attribution table from the PHASE 1 pstats dump.

Two views, both clearly labeled dev-tier SYNTHETIC single-lease observations:

1. ADDITIVE self-time (tottime) table by component family — naturally
   additive, no nesting choices.  njit kernels appear as their own entries
   with source file/line; their tottime IS the wall share of that kernel.
2. Stage/nested view from cumulative times (run_tile total; engine total;
   inside engine: GVF / Kside / cylinder-LW / Lside / residual; comfort;
   checkpoint) with explicit nested-overlap notes.

Also reports profiler distortion: median wall-rep simulation time vs the
profiled run's simulation time.  Writes phase1_attribution.json.
"""
from __future__ import annotations

import json
import pstats
import sys
from pathlib import Path

CAMPAIGN = Path(__file__).resolve().parents[1]
PHASE1 = CAMPAIGN / "phase1_profile.json"
PSTATS = CAMPAIGN / "runs" / "profile_t1024_tile0_0" / "pstats" / "profile_r0.pstats"
OUT = CAMPAIGN / "phase1_attribution.json"

# Additive families by (module substring, funcname substring); first match wins.
FAMILIES = [
    ("engine_radiation", ("radiation/engine.py",)),
    ("lside_demand", ("pipeline_demand.py",)),
    ("kside_cylsw", ("cylinder_shortwave.py",)),
    ("cyl_lw", ("cylinder_longwave.py",)),
    ("patch_radiation", ("radiation/patch_radiation.py",)),
    ("gvf_ground_view", ("ground_view.py",)),
    ("gvf_prepared", ("gvf_prepared.py",)),
    ("visibility", ("visibility",)),
    ("comfort", ("comfort/",)),
    ("io_persistence", ("persistence.py", "io/rasters", "io/")),
    ("pipeline_setup", ("pipeline.py",)),
    ("geometry_other", ("geometry/",)),
    ("solar_materials", ("radiation/solar.py", "radiation/materials.py", "radiation/lc.py")),
    ("runtime_cache", ("runtime", "cache/", "identities.py")),
    ("wall_shadows", ("wall_shadows.py",)),
    ("sleef_math", ("_sleef_classifier", "_math_profile")),
    ("checkpoint_digest_io", ("_hashlib", "Band_FlushCache", "Dataset_FlushCache",
                              "posix.fsync", "BandRasterIONumPy", "BufferedReader")),
    ("numba_dispatcher", ("numba",)),
    ("numpy_python_core", ("numpy", "~", "built-in", "{", "<")),
]


def family(filename: str, funcname: str) -> str:
    text = f"{filename} {funcname}"
    for name, patterns in FAMILIES:
        if any(pattern in text for pattern in patterns):
            return name
    return "other_unmapped"


def main() -> int:
    stats = pstats.Stats(str(PSTATS))
    rows = []
    for (filename, lineno, funcname), (cc, nc, tt, ct, callers) in stats.stats.items():
        rows.append({"family": family(str(filename), str(funcname)),
                     "file": str(filename), "line": lineno, "func": funcname,
                     "ncalls": nc, "self_s": round(tt, 4), "cum_s": round(ct, 4)})

    total_self = sum(row["self_s"] for row in rows)
    by_family: dict[str, dict] = {}
    for row in rows:
        slot = by_family.setdefault(row["family"], {"self_s": 0.0, "ncalls": 0})
        slot["self_s"] += row["self_s"]
        slot["ncalls"] += row["ncalls"]
    for name, slot in by_family.items():
        slot["self_s"] = round(slot["self_s"], 4)
        slot["pct_of_total_self"] = round(100.0 * slot["self_s"] / total_self, 2) if total_self else 0.0

    def find(path_part: str, funcname: str) -> dict:
        for row in rows:
            if path_part in row["file"] and row["func"] == funcname:
                return row
        return {"self_s": 0.0, "cum_s": 0.0, "ncalls": 0}

    run_tile = find("pipeline.py", "_run_tile")
    engine = find("radiation/engine.py", "Solweig_2022a_calc")
    engine_dispatch_gvf = find("radiation/engine.py", "gvf_2018a")
    kside = find("radiation/patch_radiation.py", "Kside_veg_v2022a")
    cyl_lw = find("radiation/cylinder_longwave.py", "Lcyl_v2022a_by_demand")
    if cyl_lw["cum_s"] == 0.0:
        cyl_lw = find("radiation/cylinder_longwave.py", "Lcyl_v2022a")
    lside_demand = find("pipeline_demand.py", "lside_veg_v2022a_demanded")
    if lside_demand["cum_s"] == 0.0:
        lside_demand = find("radiation/engine.py", "Lside_veg_v2022a")
    sunonsurface = find("radiation/engine.py", "sunonsurface_2018a")
    utci = find("comfort/utci.py", "utci_calculator_uniform")
    wbgt_globe = find("comfort/wbgt.py", "black_globe_temperature")
    wbgt_wet = find("comfort/wbgt.py", "isobaric_wet_bulb_temperature_from_rh")
    checkpoint = find("persistence.py", "write")
    decode_block = find("visibility_compiled.py", "decode_block")
    decode_at = find("visibility_compiled.py", "_decode_at")
    decode_prepared = find("visibility_prepared.py", "decode_shortwave_block")
    prepared_gvf = find("gvf_prepared.py", "prepared_gvf_step")
    cyl_sw = find("cylinder_shortwave.py", "kside_cylinder_anisotropic")

    nested = {
        "engine_total": engine,
        "engine_gvf_dispatcher": engine_dispatch_gvf,
        "engine_gvf_prepared_step": prepared_gvf,
        "engine_Kside_wrapper": kside,
        "engine_Kside_of_which_cylinder_sw": cyl_sw,
        "engine_cylinder_longwave_demand": cyl_lw,
        "engine_Lside_demand": lside_demand,
        "engine_sunonsurface": sunonsurface,
        "engine_residual_estimate": {
            "self_s": round(engine["cum_s"] - engine_dispatch_gvf["cum_s"]
                            - kside["cum_s"] - cyl_lw["cum_s"] - lside_demand["cum_s"]
                            - sunonsurface["cum_s"], 4),
            "note": "cum(engine) minus the named sub-components; includes engine-body "
                    "numpy assembly (_operate etc.), TsWaveDelay, Kup/Kdown/Ldown math, "
                    "and any double-count guard error"},
        "comfort_utci": utci,
        "comfort_wbgt": {"globe": wbgt_globe, "wetbulb": wbgt_wet},
        "checkpoint_write": checkpoint,
        "visibility_decode_nested": {"decode_block": decode_block,
                                     "_decode_at": decode_at,
                                     "decode_prepared_shortwave": decode_prepared,
                                     "note": "nested INSIDE Kside/cylinder components; "
                                             "never additive with them"},
    }

    phase1 = json.loads(PHASE1.read_text())
    wall_sims = [slot["stages_s"]["simulation_total_wall"]
                 for slot in phase1["slots"]
                 if slot.get("stages_s") and slot.get("mode") in ("wall", "profile")]
    wall_reps = [slot["stages_s"]["simulation_total_wall"]
                 for slot in phase1["slots"] if slot.get("mode") == "wall" and slot.get("stages_s")]
    profile_rep = [slot["stages_s"]["simulation_total_wall"]
                   for slot in phase1["slots"] if slot.get("mode") == "profile" and slot.get("stages_s")]
    wall_sims.sort()
    median_wall = wall_sims[len(wall_sims) // 2] if wall_sims else None
    distortion = {
        "wall_reps_s": wall_reps,
        "wall_median_s": median_wall,
        "profiled_run_s": profile_rep[0] if profile_rep else None,
        "distortion_pct": (round(100.0 * (profile_rep[0] - median_wall) / median_wall, 1)
                           if profile_rep and median_wall else None),
        "note": "profiled total vs median unprofiled wall; positive = profiler overhead",
    }

    top = sorted(rows, key=lambda row: -row["self_s"])[:25]
    payload = {
        "schema": "sw6-campaign-synthetic-phase1-attribution-v1",
        "label": "SYNTHETIC dev-tier in-sim attribution; single-lease observation; "
                 "no statistical/actual-target claims",
        "pstats": str(PSTATS),
        "profiled_total_self_s": round(total_self, 4),
        "families_additive_self": dict(sorted(by_family.items(),
                                              key=lambda item: -item[1]["self_s"])),
        "stage_nested_cum": nested,
        "profiler_distortion": distortion,
        "top25_self_entries": top,
    }
    OUT.write_text(json.dumps(payload, indent=1) + "\n")
    print(json.dumps({"families": payload["families_additive_self"],
                      "distortion": distortion,
                      "engine_cum_s": engine["cum_s"],
                      "run_tile_cum_s": run_tile["cum_s"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
