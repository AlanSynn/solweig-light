"""C6-42 m6: admission decision-table probe (synthetic descriptors, L0).

Produces m6_admission_decision_table.json from the private calculator only:
no raster files, no numerical runs.  Budget cells follow the M2 §7 scenarios
(12 GiB cap; 16 GiB = 50% default fraction of a 32 GiB host; a constrained
8 GiB; an infeasible 5.5 GiB for a single worst-case simulation job).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))

import solweig_light.runtime_memory as rm  # noqa: E402

GIB = 1024 ** 3
GDAL_32GIB_HOST = (32 * GIB * rm.DEFAULT_GDAL_CACHE_RATIO[0]) // rm.DEFAULT_GDAL_CACHE_RATIO[1]


def family(phase, count, **overrides):
    return [
        rm.PhaseJob(phase, 1024, 1024, 153, 12, 1024,
                    visibility_mode=rm.VISIBILITY_UNKNOWN_COLD,
                    tile=f"{phase}_{index}", **overrides)
        for index in range(count)
    ]


LEGACY_PER_WORKER_ESTIMATE = rm.legacy_estimate_total_bytes(
    rm.TileShapeDescriptor(1024, 1024, 153, 12, 1024)
)


def legacy_would_admit(budget, count):
    """Max parallelism the legacy public model (runtime.plan_admission)
    admits on estimate sums alone at this budget: K-largest sum <= budget.
    The legacy model has no parent/GDAL/raw-worst dimension, so this is the
    gap the corrected calculator closes (C6-60 review F6: 3x1 at 12 GiB is
    legacy-budget-admitted while raw-worst breaches)."""
    best = 0
    for k in range(1, count + 1):
        if k * LEGACY_PER_WORKER_ESTIMATE <= budget:
            best = k
    return best


def cell(name, jobs, budget, policy, writer_queue=0, active=None, threads=1):
    try:
        plan = rm.plan_phase_admission(
            jobs, budget_bytes=budget, gdal_cache_bytes=GDAL_32GIB_HOST,
            writer_queue_bytes=writer_queue, threads_per_worker=threads,
            policy=policy, active_workers=active,
        )
        return {
            "cell": name, "budget_bytes": budget, "policy": policy,
            "writer_queue_bytes": writer_queue, "outcome": plan.status,
            "legacy_would_admit": legacy_would_admit(budget, plan.requested_workers),
            "requested_workers": plan.requested_workers,
            "admissible_workers": plan.admissible_workers,
            "deferred_count": plan.deferred_count,
            "native_threads": plan.native_threads,
            "tree_at_admissible_bytes": (
                plan.parent_footprint_bytes + plan.writer_queue_bytes
                + sum(r.total_bytes for r in sorted(
                    plan.reservations, key=lambda r: -r.total_bytes
                )[:plan.admissible_workers])
            ),
        }
    except rm.ResourceAdmissionError as error:
        return {
            "cell": name, "budget_bytes": budget, "policy": policy,
            "writer_queue_bytes": writer_queue, "outcome": "rejected",
            "legacy_would_admit": legacy_would_admit(budget, len(jobs)),
            "reason": str(error),
        }


def main() -> None:
    shape = rm.TileShapeDescriptor(1024, 1024, 153, 12, 1024)
    legacy = rm.legacy_estimate_total_bytes(shape)
    sim = rm.simulation_reservation(shape, gdal_cache_bytes=GDAL_32GIB_HOST)
    geo = rm.geometry_reservation(shape, gdal_cache_bytes=GDAL_32GIB_HOST)
    pre = rm.preprocess_reservation(shape, gdal_cache_bytes=GDAL_32GIB_HOST)

    table = {
        "commit_base": "5e1fab46",
        "scenario": "1024x1024, 153 patches, 12 wind channels, block1024, "
                    "visibility unknown_cold (raw fallback), GDAL cache = 5% of 32 GiB host",
        "legacy_worst_case_bytes": legacy,
        "legacy_worst_case_gib": round(legacy / GIB, 4),
        "corrected_reservations_bytes": {
            "preprocess": pre.total_bytes,
            "geometry": geo.total_bytes,
            "simulation": sim.total_bytes,
        },
        "corrected_component_inventories": {
            "preprocess": pre.inventory(),
            "geometry": geo.inventory(),
            "simulation": sim.inventory(),
        },
        "inventory_lines": [line.to_dict() for line in rm.INVENTORY_LINES],
        "decision_table": [
            cell("12GiB sim x4 queue", family(rm.PHASE_SIMULATION, 4), 12 * GIB, "queue"),
            cell("12GiB sim x4 reject", family(rm.PHASE_SIMULATION, 4), 12 * GIB, "reject"),
            cell("12GiB sim x3 queue (C6-60 F6)",
                 family(rm.PHASE_SIMULATION, 3), 12 * GIB, "queue"),
            cell("12GiB sim x3 reject (C6-60 F6)",
                 family(rm.PHASE_SIMULATION, 3), 12 * GIB, "reject"),
            cell("12GiB geo+sim 2x2", family(rm.PHASE_GEOMETRY, 1) + family(rm.PHASE_SIMULATION, 1),
                 12 * GIB, "reject", active=2, threads=2),
            cell("12GiB geo x4 queue", family(rm.PHASE_GEOMETRY, 4), 12 * GIB, "queue"),
            cell("12GiB pre x4 queue", family(rm.PHASE_PREPROCESS, 4), 12 * GIB, "queue"),
            cell("16GiB sim x4 queue", family(rm.PHASE_SIMULATION, 4), 16 * GIB, "queue"),
            cell("16GiB sim x4 reject (4x1 default-budget)",
                 family(rm.PHASE_SIMULATION, 4), 16 * GIB, "reject"),
            cell("12GiB sim x4 queue + 1GiB writer queue",
                 family(rm.PHASE_SIMULATION, 4), 12 * GIB, "queue", writer_queue=1 * GIB),
            cell("8GiB sim x4 queue", family(rm.PHASE_SIMULATION, 4), 8 * GIB, "queue"),
            cell("5.5GiB sim x1 queue (infeasible)",
                 family(rm.PHASE_SIMULATION, 1), int(5.5 * GIB), "queue"),
        ],
    }
    destination = Path(__file__).resolve().parent / "m6_admission_decision_table.json"
    destination.write_text(json.dumps(table, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {destination}")
    for entry in table["decision_table"]:
        summary = entry.get("outcome")
        detail = (f"admissible={entry.get('admissible_workers')}"
                  f" deferred={entry.get('deferred_count')}"
                  f" tree={entry.get('tree_at_admissible_bytes')}"
                  if summary in ("admitted", "queued") else entry.get("reason", "")[:110])
        print(f"  {entry['cell']:<44} {summary:<9} {detail}")


if __name__ == "__main__":
    main()
