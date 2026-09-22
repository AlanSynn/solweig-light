#!/usr/bin/env python3
"""Hypothetical analytical models, never framework/SOLWEIG measurement results."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from _common import number, positive_int


def speedup(fractions: list[float], local_speedups: list[float], overhead: float=0.0) -> dict:
    if len(fractions)!=len(local_speedups):raise ValueError('Lengths differ')
    f=[number(x,'fraction') for x in fractions]
    s=[number(x,'local speedup',positive=True) for x in local_speedups]
    d=number(overhead,'overhead')
    if sum(f)>1.0+1e-12:raise ValueError('Disjoint fractions must sum to <=1')
    remaining=max(0.0,1.0-sum(f))+sum(x/y for x,y in zip(f,s))+d
    if remaining<=0:raise ValueError('Model has no positive work')
    return {'measurement_class':'hypothetical_model','remaining_ratio':remaining,
            'speedup':1.0/remaining,'overhead_ratio':d}


def required_local_speedup(fraction:float, desired:float, overhead:float=0.0) -> float|None:
    f=number(fraction,'fraction');target=number(desired,'desired',positive=True)
    d=number(overhead,'overhead')
    if not 0<f<=1:raise ValueError('fraction must be in (0,1]')
    denom=1/target-1+f-d
    return None if denom<=0 else f/denom


def break_even_tiles(extra_setup:float, old_island:float, new_island:float, bridge:float) -> int|None:
    j=number(extra_setup,'extra setup');old=number(old_island,'old island')
    new=number(new_island,'new island');b=number(bridge,'bridge')
    saving=old-new-b
    if saving<=0:return None
    return max(1,math.floor(j/saving)+1) # Strictly positive total gain.


def phase_batch(tiles:int, phases:list[dict], cpu_budget:int, memory_budget_bytes:int,
                parent_reserve_bytes:int=0, overhead_seconds:float=0) -> dict:
    k=positive_int(tiles,'tiles');cpu=positive_int(cpu_budget,'cpu budget')
    memory=positive_int(memory_budget_bytes,'memory budget')
    parent=positive_int(parent_reserve_bytes,'parent reserve',zero=True)
    if parent>=memory:raise ValueError('Parent reserve consumes all memory')
    total=number(overhead_seconds,'overhead');rows=[]
    for p in phases:
        w=positive_int(p['workers'],'workers');h=positive_int(p['threads'],'threads')
        active=min(k,w)
        extra=positive_int(p.get('additional_threads',0),'additional threads',zero=True)
        private=positive_int(p['worker_bytes'],'worker memory',zero=True)
        if active*h+extra>cpu:raise ValueError('Phase exceeds CPU envelope')
        if parent+active*private>memory:raise ValueError('Phase exceeds memory envelope')
        cost=number(p['per_job_seconds'],'per-job seconds')
        ratio=number(p.get('speedup',1),'speedup',positive=True)
        contention=number(p.get('contention',1),'contention',positive=True)
        elapsed=math.ceil(k/active)*cost*contention/ratio
        rows.append({'name':p['name'],'waves':math.ceil(k/active),'seconds':elapsed,
                     'reserved_cpu':active*h+extra,'reserved_bytes':parent+active*private})
        total+=elapsed
    return {'measurement_class':'hypothetical_model','tiles':k,'seconds':total,
            'tiles_per_minute':60*k/total if total else None,'phases':rows,
            'note':'Per-job costs and contention are inputs, not measured by this tool.'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,help='JSON phases model inputs; omit for fixed labeled sensitivity examples')
    a=p.parse_args()
    if a.input:
        result=phase_batch(**json.loads(a.input.read_text()))
    else:
        result={'measurement_class':'hypothetical_model','scenarios':[
          dict(f=f,s=s,delta=d,**speedup([f],[s],d)) for f,s,d in
          [(0.2,2,0.03),(0.6,3,0.03),(0.8,4,0.05)]],
          'required_local_for_2x_when_f_0_6_delta_0_03':required_local_speedup(.6,2,.03)}
    print(json.dumps(result,indent=2,allow_nan=False))


if __name__=='__main__':main()
