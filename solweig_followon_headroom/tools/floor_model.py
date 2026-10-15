"""Conditional floor arithmetic, not a SOLWEIG performance benchmark.

Only uses Python's standard library. Inputs may be recorded measurements;
outputs are derived bounds/scenarios, never new execution measurements.
"""
from __future__ import annotations
import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path


def nonnegative(value: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError(f'{name} must be finite and nonnegative')
    return value


def accelerated(seconds: float, speedup: float) -> float:
    seconds = nonnegative(seconds, 'seconds')
    speedup = float(speedup)
    if math.isnan(speedup) or speedup <= 0:
        raise ValueError('speedup must be positive; +infinity means ideal elimination')
    return 0.0 if math.isinf(speedup) else seconds / speedup


def stage_speedup(nonaccelerated_fraction: float, kernel_speedup: float) -> float:
    e = nonnegative(nonaccelerated_fraction, 'nonaccelerated_fraction')
    if e > 1:
        raise ValueError('fraction must be <= 1')
    remaining = e + accelerated(1 - e, kernel_speedup)
    return math.inf if remaining == 0 else 1 / remaining


def max_nonaccelerated_fraction(target_stage_speedup: float, kernel_speedup: float) -> float | None:
    target, kernel = float(target_stage_speedup), float(kernel_speedup)
    if not math.isfinite(target) or not math.isfinite(kernel) or target <= 1 or kernel <= 1:
        raise ValueError('finite target and kernel speedups > 1 required')
    if target > kernel:
        return None
    return (1 / target - 1 / kernel) / (1 - 1 / kernel)


@dataclass(frozen=True)
class Chain:
    walls_s: float
    svf_s: float
    run_s: float
    spatial_tiles: int
    timesteps: int

    def __post_init__(self):
        for name in ('walls_s', 'svf_s', 'run_s'):
            nonnegative(getattr(self, name), name)
        for name in ('spatial_tiles', 'timesteps'):
            if type(getattr(self, name)) is not int or getattr(self, name) < 1:
                raise ValueError(f'{name} must be a positive integer')
        if self.total_s <= 0:
            raise ValueError('total must be positive')

    @property
    def total_s(self) -> float:
        return self.walls_s + self.svf_s + self.run_s

    def scenario(self, svf_speedup: float = 1, run_speedup: float = 1,
                 overhead_s: float = 0, target_s: float = 1800) -> dict:
        overhead_s = nonnegative(overhead_s, 'overhead_s')
        target_s = nonnegative(target_s, 'target_s')
        g = accelerated(self.svf_s, svf_speedup)
        r = accelerated(self.run_s, run_speedup)
        total = self.walls_s + g + r + overhead_s
        remaining = target_s - self.walls_s - g - overhead_s
        return {
            'evidence_class': 'derived_conditional_scenario',
            'svf_speedup': 'ideal_elimination' if math.isinf(svf_speedup) else svf_speedup,
            'run_speedup': 'ideal_elimination' if math.isinf(run_speedup) else run_speedup,
            'total_s': total,
            'minutes': total / 60,
            'speedup_vs_reported_s10_chain': self.total_s / total if total else None,
            'tiles_per_minute': self.spatial_tiles * 60 / total if total else None,
            'run_speedup_required_for_target': self.run_s / remaining if remaining > 0 else None,
            'run_target_feasible_with_fixed_svf': remaining > 0,
            'boundary': 'same stage barriers, fixed walls, same workload and shape except declared speedups',
        }

    def linear_time_envelope(self, steps: int, svf_speedup: float = 1) -> dict:
        if type(steps) is not int or steps < 1:
            raise ValueError('steps must be positive integer')
        run = self.run_s * steps / self.timesteps
        original = self.walls_s + self.svf_s + run
        changed = self.walls_s + accelerated(self.svf_s, svf_speedup) + run
        return {
            'evidence_class': 'hypothetical_average_step_sensitivity',
            'steps': steps,
            'baseline_model_s': original,
            'candidate_model_s': changed,
            'speedup': original / changed,
            'svf_fraction': self.svf_s / original,
            'assumptions': ['zero per-invocation fixed run cost', 'same average day/night cost',
                            'same geometry and 24 spatial tiles', 'not a measured corner or forecast'],
        }


def admissible_shapes(cpu_budget: int, tiles: int, memory_budget: int,
                      parent_reserve: int, worker_bytes_by_threads: dict[int, int]) -> list[dict]:
    """Enumerate capacity only. Memory values MUST come from audited candidate admission.

    A returned shape is not performance-qualified. Thread IDs/logical CPUs are
    not assumed equivalent physical cores. No oversubscription or shared-page credit.
    """
    if any(type(x) is not int or x < 1 for x in (cpu_budget, tiles, memory_budget)):
        raise ValueError('positive integer CPU, tile and memory budgets required')
    if type(parent_reserve) is not int or parent_reserve < 0:
        raise ValueError('invalid parent reserve')
    result = []
    for h, m in sorted(worker_bytes_by_threads.items()):
        if type(h) is not int or h < 1 or type(m) is not int or m < 1:
            raise ValueError('positive integer threads and worker bytes required')
        for w in range(1, min(tiles, cpu_budget // h) + 1):
            charged = parent_reserve + w * m
            if charged <= memory_budget:
                result.append({'workers': w, 'threads_per_worker': h,
                               'charged_bytes': charged, 'native_threads': w * h,
                               'status': 'capacity_admissible_not_timed'})
    return result


def report() -> dict:
    chain = Chain(20.0, 4063.1, 2529.7, 24, 24)
    return {
        'title': 'S10 follow-on conditional floors',
        'source': 'User-provided verified S10-36 observational record; raw file not read here',
        'supplied_s10': asdict(chain),
        'total_s': chain.total_s,
        'actual_target_status': 'unverified',
        'new_solweig_measurements': False,
        'current_tiles_per_minute': 24 * 60 / chain.total_s,
        'svf_share': chain.svf_s / chain.total_s,
        'whole_svf_scenarios': [chain.scenario(k) for k in (1, 2, 3, 5, 7, 8, math.inf)],
        'residual_svf_scenarios_with_8x_kernel': [
            {'nonaccelerated_fraction': e, 'svf_stage_speedup': stage_speedup(e, 8),
             'chain': chain.scenario(stage_speedup(e, 8))}
            for e in (0, .02, .05, .1, .2, .3, .5)],
        'nonaccelerated_fraction_limit_5x_phase_8x_kernel': max_nonaccelerated_fraction(5, 8),
        'nonaccelerated_fraction_limit_7x_phase_8x_kernel': max_nonaccelerated_fraction(7, 8),
        'hypothetical_time_envelope': [
            {'steps': t, 'g5': chain.linear_time_envelope(t, 5),
             'g7': chain.linear_time_envelope(t, 7)} for t in (1, 24, 48, 72, 168)],
        'hypothetical_svf_run_crossover_steps': chain.svf_s / (chain.run_s / 24),
        'small_fixed_residual_ceiling_if_same_boundary': [
            {'residual_s': x, 'total_s': 1.093,
             'maximum_speedup': 1.093 / (1.093 - x),
             'fraction': x / 1.093,
             'condition': 'only valid if residual and total enclose the same execution boundary'}
            for x in (.13, .14)],
        'warnings': [
            'Do not multiply worker and kernel speedups that consume the same 24-CPU allocation.',
            'Zero-SVF floor assumes run, barriers and walls unchanged; not a universal hardware floor.',
            'A single 24-step time does not identify fixed cost or a 1/72-step runtime.',
            'No confidence interval or headroom exhaustion proof follows from one timed pair.',
        ],
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    data = json.dumps(report(), indent=2, allow_nan=False) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(data)
    else:
        print(data, end='')


if __name__ == '__main__':
    main()
