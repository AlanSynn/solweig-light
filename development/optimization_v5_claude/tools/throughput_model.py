#!/usr/bin/env python3
"""Analytical schedule screening, NOT a SOLWEIG benchmark or a calibrated forecast.

All supplied examples are hypothetical equivalent-core service demands. Observed
wall time at one thread setting cannot identify these demands. Unknown bandwidth
costs remain unknown; they are not implicitly certified as zero.
"""
from __future__ import annotations
import argparse
import heapq
import json
import math
from pathlib import Path
from typing import Any


def positive(x: Any, name: str, allow_zero: bool = False) -> float:
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        raise ValueError(f"{name} must be finite numeric")
    if x < 0 or (x == 0 and not allow_zero):
        raise ValueError(f"{name} is out of range")
    return float(x)


def work_demands(stages: list[dict[str, Any]], reductions: dict[str, float],
                 parallel_geometry: bool) -> tuple[float, float]:
    s = p = 0.0
    names = {stage['id'] for stage in stages}
    if set(reductions) - names:
        raise ValueError("unknown stage reduction")
    for stage in stages:
        work = positive(stage['core_seconds'], stage['id']) / positive(
            reductions.get(stage['id'], 1.0), stage['id'] + ' reduction')
        parallel = bool(stage['parallel']) or (parallel_geometry and stage['id'] == 'geometry')
        if parallel:
            p += work
        else:
            s += work
    return s, p


def greedy_makespan(times: list[float], workers: int, longest_first: bool = True) -> float:
    if workers < 1 or not times:
        raise ValueError("positive workers and nonempty times required")
    jobs = sorted(times, reverse=True) if longest_first else times
    heap = [0.0] * workers
    for elapsed in jobs:
        t = positive(elapsed, 'job time', allow_zero=True)
        heapq.heapreplace(heap, heap[0] + t)
    return max(heap)


def evaluate(config: dict[str, Any], scenario: dict[str, Any], workers: int,
             threads: int, contention: float = 1.0) -> dict[str, Any]:
    if (isinstance(workers, bool) or isinstance(threads, bool)
            or not isinstance(workers, int) or not isinstance(threads, int)
            or min(workers, threads) < 1):
        raise ValueError("integer positive worker/thread counts required")
    hardware = config['hardware_assumptions']
    cpu = positive(hardware['equivalent_cores'], 'equivalent_cores')
    budget = positive(hardware['ram_budget_gib'], 'ram_budget_gib')
    parent = positive(hardware['parent_and_shared_gib'], 'parent', True)
    base = positive(hardware['per_worker_base_gib'], 'worker base', True)
    scratch = positive(hardware['per_native_thread_scratch_gib'], 'scratch', True)
    resident = parent + workers * (base + threads * scratch)
    feasible = workers * threads <= cpu and resident <= budget
    weights = config.get('tile_weights') or [1.0] * int(config['tiles'])
    if len(weights) != config['tiles']:
        raise ValueError('tile weight count differs from tiles')
    weights = [positive(w, 'tile weight') for w in weights]
    s, p = work_demands(config['stages'], scenario['work_reductions'],
                        scenario['parallel_geometry'])
    slowdown = positive(contention, 'contention')
    overhead = positive(config['exclusive_batch_overhead_seconds'], 'overhead', True)
    job_times = [(s + p / threads) * w * slowdown for w in weights]
    body = greedy_makespan(job_times, workers)
    work_lower = sum(weights) * (s + p) / cpu
    caps = config.get('resource_measurements', {})
    dram_lower = disk_lower = None
    for label, destination in [('dram', 'dram'), ('disk', 'disk')]:
        amount = caps.get(f'{label}_gib_per_tile')
        bw = caps.get(f'{label}_effective_gib_per_second')
        if (amount is None) != (bw is None):
            raise ValueError(f'{label} amount and effective bandwidth must be supplied together')
        value = None if amount is None else len(weights) * positive(amount, label, True) / positive(bw, label+' bandwidth')
        if destination == 'dram':
            dram_lower = value
        else:
            disk_lower = value
    serial_span_lower = max(weights) * s
    lower_candidates = [work_lower, serial_span_lower] + [x for x in (dram_lower, disk_lower) if x is not None]
    screening = overhead + max([body] + [x for x in (dram_lower, disk_lower) if x is not None])
    return {
        'scenario': scenario['id'], 'workers': workers, 'threads_per_worker': threads,
        'analytically_admissible': feasible, 'assumed_resident_gib': resident,
        'serial_core_seconds_per_tile': s, 'parallel_core_seconds_per_tile': p,
        'contention_multiplier': slowdown,
        'cpu_schedule_seconds': overhead + body,
        'resource_lower_bound_seconds': overhead + max(lower_candidates),
        'serial_only_span_lower_seconds': serial_span_lower,
        'dram_lower_bound_seconds': dram_lower, 'disk_lower_bound_seconds': disk_lower,
        'screening_seconds': screening if feasible else None,
        'tiles_per_minute': 60 * len(weights) / screening if feasible else None,
        'model_target_met': feasible and screening <= config['target_seconds'],
        'unknown_memory_or_io_costs': dram_lower is None or disk_lower is None,
        'calibrated_forecast': False,
        'actual_goal_passed': False,
        'interpretation': 'Hypothetical screening only; max(resource bounds,CPU schedule) assumes favorable overlap and is not a proven runtime bound.'
    }


def run(config: dict[str, Any]) -> dict[str, Any]:
    results = []
    for scenario in config['scenarios']:
        for workers, threads in config['settings']:
            results.append(evaluate(config, scenario, workers, threads))
    recommended = []
    for scenario in config['scenarios']:
        candidates = [r for r in results if r['scenario'] == scenario['id'] and r['analytically_admissible']]
        if candidates:
            best = min(candidates, key=lambda r: r['screening_seconds'])
            stress = evaluate(config, scenario, best['workers'], best['threads_per_worker'], 1.2)
            recommended.append({'scenario': scenario['id'], 'best_screening': best,
                                'twenty_percent_body_slowdown': stress})
    return {'schema': 1, 'status': 'uncalibrated_analytical_scenarios',
            'solweig_executed': False, 'hardware_benchmarked': False,
            'all_settings': results, 'scenario_summaries': recommended}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path(__file__).resolve().parents[1] / 'throughput_inputs.json')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = run(json.loads(args.config.read_text()))
    data = json.dumps(result, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(data)
    else:
        print(data, end='')


if __name__ == '__main__':
    main()
