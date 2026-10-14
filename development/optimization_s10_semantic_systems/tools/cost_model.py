"""Analytical calculators. Outputs are calculations, never new performance measurements."""
from __future__ import annotations
import argparse
import heapq
import json
import math
from pathlib import Path
from typing import Any


def number(x: Any, name: str, *, positive: bool = False) -> float:
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        raise ValueError(f'{name} must be a finite number')
    if x < 0 or (positive and x <= 0):
        raise ValueError(f'{name} must be {"positive" if positive else "nonnegative"}')
    return float(x)


def integer(x: Any, name: str, *, positive: bool = False) -> int:
    number(x, name, positive=positive)
    if not isinstance(x, int):
        raise ValueError(f'{name} must be an integer')
    return x


def amdahl(parts: list[dict], overhead_fraction: float = 0) -> dict:
    """Each part covers disjoint baseline service. All other service is unchanged."""
    overhead = number(overhead_fraction, 'overhead_fraction')
    ids, total, residual = set(), 0.0, 0.0
    for part in parts:
        key = part['id']
        if not isinstance(key, str) or not key or key in ids:
            raise ValueError('Part ids must be unique nonempty strings; do not double count')
        ids.add(key)
        f = number(part['fraction'], 'fraction')
        s = number(part['speedup'], 'speedup', positive=True)
        total += f
        residual += f / s
    if total > 1 + 1e-12:
        raise ValueError('Disjoint fractions exceed one')
    factor = max(0.0, 1.0-total) + residual + overhead
    if factor <= 0:
        raise ValueError('Invalid residual service')
    return {'remaining_service_fraction': factor, 'total_speedup': 1/factor,
            'unmodified_fraction': max(0.0, 1-total), 'new_overhead_fraction': overhead,
            'claim': 'conditional_analysis_not_measured_speedup'}


def required_stage_speedup(fraction: float, target_speedup: float,
                           overhead_fraction: float = 0) -> dict:
    f = number(fraction, 'fraction', positive=True)
    if f > 1: raise ValueError('fraction cannot exceed one')
    target = number(target_speedup, 'target_speedup', positive=True)
    if target < 1: raise ValueError('target_speedup must be >= 1')
    overhead = number(overhead_fraction, 'overhead_fraction')
    denominator = 1/target - 1 + f - overhead
    return {'finite_solution': denominator > 0,
            'minimum_stage_speedup': f/denominator if denominator > 0 else None,
            'claim': 'necessary_under_the_stated_disjoint_service_model_not_a_guarantee'}


def phase_model(config: dict) -> dict:
    """Sequential stage barriers, identical resource reservation per active job.

    Job times are input estimates at the named H. Greedy list scheduling uses
    those estimates; real concurrency/bandwidth effects must be in contention.
    It is not a simulator of the OS, cache, GPU overlap or heterogeneous cores.
    """
    cpus = integer(config['cpu_budget'], 'cpu_budget', positive=True)
    budget = integer(config['memory_budget_bytes'], 'memory_budget_bytes', positive=True)
    shared = integer(config.get('shared_bytes', 0), 'shared_bytes')
    if shared >= budget: raise ValueError('No memory left for workers')
    base = number(config.get('overhead_seconds', 0), 'overhead_seconds')
    rows, total, peak = [], base, shared
    seen = set()
    for phase in config['phases']:
        name = phase['id']
        if name in seen: raise ValueError('Duplicate phase id')
        seen.add(name)
        w = integer(phase['workers'], 'workers', positive=True)
        h = integer(phase['threads_per_worker'], 'threads_per_worker', positive=True)
        reserve = integer(phase['bytes_per_worker'], 'bytes_per_worker', positive=True)
        if w*h > cpus: raise ValueError(f'{name}: requested CPU budget exceeded')
        if shared+w*reserve > budget: raise ValueError(f'{name}: requested memory budget exceeded')
        jobs = [number(x, 'job_seconds') for x in phase['job_seconds']]
        if not jobs: raise ValueError(f'{name}: no jobs')
        speed = number(phase.get('implementation_speedup', 1), 'implementation_speedup', positive=True)
        contention = number(phase.get('contention_factor', 1), 'contention_factor', positive=True)
        queue = [0.0]*min(w, len(jobs))
        heapq.heapify(queue)
        for t in jobs:
            first = heapq.heappop(queue)
            heapq.heappush(queue, first+t*contention/speed)
        elapsed = max(queue)
        total += elapsed
        peak = max(peak, shared+min(w, len(jobs))*reserve)
        rows.append({'id':name,'modeled_seconds':elapsed,'workers':min(w,len(jobs)),
                     'threads_per_worker':h,'input_job_count':len(jobs)})
    targets = integer(config.get('completed_jobs', 1), 'completed_jobs', positive=True)
    return {'evidence_class':'model_calculation_not_benchmark',
            'input_evidence_class':config.get('evidence_class','unspecified'),
            'total_seconds':total,'throughput_jobs_per_minute':60*targets/total if total else None,
            'reserved_peak_bytes':peak,'phases':rows,
            'limits':['Not calibrated unless all input costs/contended times are independently measured.',
                      'No stage overlap assumed; serial phases remain serial.',
                      'Do not treat jobs as spatial tiles unless the input manifest says so.']}


def sensitivity() -> dict:
    # User report, rounded and minima-based, NOT independently verified.
    sim, fixed = 37.5, .5+36.7
    rows=[]
    for s in [2,3,5]:
        a=amdahl([{'id':'daytime_lw','fraction':.45,'speedup':s}])
        new=sim*a['remaining_service_fraction']
        rows.append({'assumed_daytime_lw_speedup':s,'conditional_sim_speedup':sim/new,
                     'conditional_stage_sum_speedup':(sim+fixed)/(new+fixed)})
    return {'evidence_class':'hypothetical_sensitivity_using_unverified_user_report',
            'baseline':{'shape':[512,512],'sim_seconds':sim,'other_stage_seconds':fixed,
                        'day_lw_fraction_assumed':.45},
            'rows':rows,'not_measured':['source-matched unprofiled fractions','new implementation','M4 throughput','24-tile target']}


def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input',type=Path)
    ap.add_argument('--output',type=Path)
    args=ap.parse_args()
    result=phase_model(json.loads(args.input.read_text())) if args.input else sensitivity()
    text=json.dumps(result,indent=2,allow_nan=False)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open('x') as stream: stream.write(text)
    else: print(text,end='')

if __name__=='__main__': main()
