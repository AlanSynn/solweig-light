#!/usr/bin/env python3
"""Explicit barrier-phase what-if calculator; it never establishes measured speedups."""
from __future__ import annotations
import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path


def finite(v,name,positive=False):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v):
        raise ValueError(f'{name} must be finite numeric')
    if v<0 or (positive and v<=0): raise ValueError(f'{name} has invalid sign')
    return float(v)


def positive_int(v,name):
    if isinstance(v,bool) or not isinstance(v,int) or v<1: raise ValueError(f'{name} must be positive integer')
    return v


def estimate(data: dict) -> dict:
    k=positive_int(data['spatial_tiles'],'spatial_tiles')
    cpu=positive_int(data['cpu_budget'],'cpu_budget')
    ram=finite(data['memory_budget_gib'],'memory_budget_gib',True)
    parent=finite(data.get('parent_gib',0),'parent_gib')
    setup=finite(data.get('global_setup_seconds',0),'global_setup_seconds')
    if parent>=ram: raise ValueError('No worker memory remains')
    records=[]
    for stage in data['phases']:
        w=positive_int(stage['workers'],'workers');h=positive_int(stage['threads'],'threads')
        if w*h>cpu: raise ValueError(f"CPU overreservation in {stage['name']}")
        mem=finite(stage['worker_gib'],'worker_gib',True)
        if parent+w*mem>ram: raise ValueError(f"Memory overreservation in {stage['name']}")
        # seconds_per_tile refers to this stage at the stated threads, or must
        # have its thread-change effect included explicitly in inflation.
        t=finite(stage['seconds_per_tile'],'seconds_per_tile')
        r=finite(stage.get('implementation_gain',1),'implementation_gain',True)
        chi=finite(stage.get('inflation',1),'inflation',True)
        waves=math.ceil(k/w)
        seconds=waves*t*chi/r
        records.append({'name':stage['name'],'waves':waves,'workers':w,'threads':h,
                        'seconds':seconds,'reserved_gib':parent+w*mem})
    total=setup+sum(s['seconds'] for s in records)
    if total<=0: raise ValueError('Total time must be positive')
    return {'schema':'sw6-hypothetical-phase-model-v1','input_evidence_class':data.get('evidence_class','hypothetical'),
            'output_class':'conditional_model_not_measured','spatial_tiles':k,'phases':records,
            'seconds':total,'minutes':total/60,'tiles_per_minute':60*k/total,
            'model_under_1800':total<=1800,'observed_target_demonstrated':False,
            'assumptions':'homogeneous tiles; phase barriers; no unmodeled overlap; explicit inflation includes thread/contended effects',
            'caveat':'Do not use logical bytes as measured DRAM; model pass is not an executed target pass.'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input',type=Path);p.add_argument('--out',type=Path)
    a=p.parse_args()
    try: result=estimate(json.loads(a.input.read_text()))
    except (KeyError,ValueError,TypeError) as e: p.exit(2,str(e)+'\n')
    text=json.dumps(result,indent=2)+'\n'
    if a.out: a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(text)
    else: print(text,end='')

if __name__=='__main__': main()
