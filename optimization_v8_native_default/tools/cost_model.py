"""Transparent hypothetical arithmetic only. No backend or SOLWEIG execution."""
from __future__ import annotations
import argparse
import json
import math


def number(value: float, name: str, lo: float=0, strict: bool=False) -> float:
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
        raise ValueError(f'{name} must be finite numeric')
    v=float(value)
    if v<lo or (strict and v==lo):raise ValueError(f'{name} out of range')
    return v


def calls(tiles: int, records: int, pixels: int, dispatch: int) -> int:
    for name,v in [('tiles',tiles),('records',records),('pixels',pixels),('dispatch',dispatch)]:
        if type(v) is not int or v<1:raise ValueError(name+' must be a positive integer')
    return tiles*records*((pixels+dispatch-1)//dispatch)


def speedup(fraction: float, region_speedup: float, overhead: float=0.0) -> float:
    f=number(fraction,'fraction');s=number(region_speedup,'speedup',strict=True)
    d=number(overhead,'overhead')
    if f>1:raise ValueError('fraction must be <=1')
    return 1.0/(1-f+f/s+d)


def required_speedup(fraction: float, target: float, overhead: float=0.0) -> float | None:
    f=number(fraction,'fraction');t=number(target,'target',strict=True);d=number(overhead,'overhead')
    if f>1:raise ValueError('fraction must be <=1')
    den=1/t-1+f-d
    if f==0:return 1.0 if 1/(1+d)>=t else None
    return f/den if den>0 else None


def phase_total(phases: list[dict], cpu_budget: int, memory_budget_bytes: int, setup_s: float=0.0) -> float:
    if type(cpu_budget)is not int or cpu_budget<1 or type(memory_budget_bytes)is not int or memory_budget_bytes<1:
        raise ValueError('budgets must be positive integers')
    total=number(setup_s,'setup_s')
    for p in phases:
        k,w,h=p['jobs'],p['workers'],p['threads_per_worker']
        for v in (k,w,h):
            if type(v)is not int or v<1:raise ValueError('phase dimensions must be positive integers')
        if w*h>cpu_budget:raise ValueError('phase exceeds CPU budget')
        mem=number(p['bytes_per_worker'],'bytes_per_worker')
        shared=number(p.get('shared_bytes',0),'shared_bytes')
        if w*mem+shared>memory_budget_bytes:raise ValueError('phase exceeds memory budget')
        # job_s must already be measured/assumed UNDER the selected concurrency.
        total+=math.ceil(k/w)*number(p['job_s_at_concurrency'],'job_s_at_concurrency')
    return total


def examples() -> dict:
    n=calls(4,24,1024**2,1024)
    return {'evidence_kind':'hypothetical_arithmetic_not_benchmark','calls':n,
            'overhead_seconds':{str(us):n*us*1e-6 for us in (25,50,100,200)},
            'scenarios':[{'f':f,'s':s,'delta':d,'total_speedup':speedup(f,s,d)} for f,s,d in
                         [(0.5,2,0.02),(0.6,3,0.03),(0.7,4,0.03)]],
            'required_region_for_total_2x_at_f_0_6_delta_0_03':required_speedup(.6,2,.03)}

if __name__=='__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(examples(),indent=2,allow_nan=False))
