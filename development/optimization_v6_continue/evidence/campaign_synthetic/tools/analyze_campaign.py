#!/usr/bin/env python3
"""C6-101r PHASE 3 analysis: paired-campaign tables + bitwise parity verdict.

Reads campaign_v1.json (+ .jsonl); writes campaign_verdict.json and prints
markdown fragments.  Cold and warm speedups are reported SEPARATELY (never
blended); warm numbers are medians of the warm_full reps; cold cells report
each rep.  Bitwise parity is judged per tile across every measured run.
Dev-tier SYNTHETIC single-lease observations only.
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

CAMPAIGN = Path(__file__).resolve().parents[1]
DATA = CAMPAIGN / "campaign_v1.json"
OUT = CAMPAIGN / "campaign_verdict.json"

V5 = {"dense1024_candidate_s": 289.765, "vegetation1024_candidate_s": 302.396}


def main() -> int:
    payloads = json.loads(DATA.read_text())
    slots = payloads["slots"]
    measured = [slot for slot in slots if "stages_s" in slot]
    skipped = [slot for slot in slots if slot.get("status") == "SKIPPED_TIME_BUDGET"]
    failed = [slot for slot in slots if slot.get("status") == "FAILED_OR_TIMED_OUT"]

    cells: dict[tuple, list] = {}
    for slot in measured:
        cells.setdefault((slot["config"], slot["tree"], slot["temp"]), []).append(slot)

    table = []
    for (config, tree, temp), group in sorted(cells.items()):
        def field(name: str) -> float:
            return round(statistics.median(slot["stages_s"][name] for slot in group), 2)
        table.append({
            "config": config, "tree": tree, "temp": temp, "reps": len(group),
            "total_measured_s": [slot["stages_s"]["total_measured"] for slot in group],
            "total_median_s": field("total_measured"),
            "walls_median_s": field("walls_aspect"),
            "svf_median_s": field("svf_geometry_total"),
            "sim_median_s": field("simulation_total"),
            "sim_values_s": [slot["stages_s"]["simulation_total"] for slot in group],
            "loadavg_median": round(statistics.median(
                slot["host_before"]["loadavg"][0] for slot in group), 1),
        })

    speedups = []
    for config in ("T4", "S1"):
        for temp in ("cold", "warm_full"):
            base = next((row for row in table if row["config"] == config
                         and row["tree"] == "base" and row["temp"] == temp), None)
            integrated = next((row for row in table if row["config"] == config
                               and row["tree"] == "integrated" and row["temp"] == temp), None)
            if not base or not integrated:
                continue
            if temp == "cold":
                label = "cold (fresh dir + fresh JIT cache)"
                base_s, int_s = base["total_measured_s"], integrated["total_measured_s"]
                # nearest-rep pairing, reported per rep
                pairs = None
            else:
                label = "warm_full medians"
                base_s, int_s = [base["total_median_s"]], [integrated["total_median_s"]]
                pairs = None
            best_base, best_int = min(base_s), min(int_s)
            speedups.append({
                "config": config, "comparison": label,
                "base_total_s": base_s, "integrated_total_s": int_s,
                "integrated_vs_base_best_rep": round(best_base / best_int, 3),
                "sim_stage": {"base_s": base["sim_values_s"],
                              "integrated_s": integrated["sim_values_s"],
                              "integrated_vs_base_median_sim": round(
                                  statistics.median(base["sim_values_s"])
                                  / statistics.median(integrated["sim_values_s"]), 3)},
            })

    parity: dict[str, dict] = {}
    for slot in measured:
        for tile, info in slot.get("simulation_tiff_digest_per_tile", {}).items():
            entry = parity.setdefault(tile, {"digests": {}, "runs": 0})
            entry["runs"] += 1
            entry["digests"].setdefault(info["digest"], []).append(
                f"{slot['tree']}/{slot['config']}/{slot['temp']}/r{slot['rep']}")
    parity_verdict = {tile: {"all_bitwise_identical": len(info["digests"]) == 1,
                             "distinct_digest_count": len(info["digests"]),
                             "runs": info["runs"],
                             "digest_runs": info["digests"]}
                      for tile, info in sorted(parity.items())}
    all_identical = all(v["all_bitwise_identical"] for v in parity_verdict.values()) \
        and bool(parity_verdict)

    host = [slot["host_before"] for slot in measured]
    loadavgs = sorted(slot["loadavg"][0] for slot in host)
    busy = sum(1 for slot in host if slot["busy_non_browser"])
    host_summary = {
        "runs": len(host),
        "loadavg1_min_median_max": [loadavgs[0], loadavgs[len(loadavgs) // 2], loadavgs[-1]],
        "slots_with_busy_non_browser_process": busy,
        "note": "host carries unrelated OS/browser/system activity and other session "
                "agents' work; exclusivity claimed only as 'no competing program work "
                "of this task alongside'",
    }

    t4_warm_int = next((row for row in table if row["config"] == "T4"
                        and row["tree"] == "integrated" and row["temp"] == "warm_full"), None)
    crosscheck = {
        "v5_campaign_reference_s": V5,
        "this_campaign_integrated_T4_warm_sim_median_s_per_4tile_run":
            t4_warm_int["sim_median_s"] if t4_warm_int else None,
        "note": "v5 numbers are per-single-tile thermal_comfort on a different real "
                "fixture; this campaign is 4 synthetic tiles per run through the "
                "3-stage public workflow (walls+svf inside the timer). Same order of "
                "magnitude expected; absolute gaps explained by scene content, "
                "transport, stage inclusion, and host load.",
    }

    payload = {
        "schema": "sw6-campaign-synthetic-verdict-v1",
        "label": "SYNTHETIC dev-tier paired campaign; single-lease; no statistical or "
                 "actual-target claims",
        "protocol_head_trees": payloads["trees"],
        "table": table,
        "speedups": speedups,
        "bitwise_parity_per_tile": parity_verdict,
        "bitwise_parity_all_identical": all_identical,
        "skipped_slots": [slot["slot"] for slot in skipped],
        "failed_slots": [{"slot": slot["slot"], "stderr_tail": slot.get("stderr_tail")}
                         for slot in failed],
        "host_summary": host_summary,
        "v5_crosscheck": crosscheck,
    }
    OUT.write_text(json.dumps(payload, indent=1) + "\n")
    print(json.dumps(payload, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
