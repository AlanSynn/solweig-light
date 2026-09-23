#!/usr/bin/env python3
"""Diagnostic arithmetic; never a benchmark or default-promotion certificate."""
import argparse
import json
import math
from pathlib import Path

CELLS = {
    'binary': {'A_min_sum_ms':3.3627,'C_min_sum_ms':3.4655,'producer_ms':2.9534,'leaf_ms':.2451,'mask_pack_ms':.1972},
    'mixed': {'A_min_sum_ms':2.7487,'C_min_sum_ms':2.9668,'producer_ms':2.4561,'leaf_ms':.2534,'mask_pack_ms':.1975},
    'raw': {'A_min_sum_ms':.5485,'C_min_sum_ms':.7338,'producer_ms':.2243,'leaf_ms':.2527,'mask_pack_ms':.1973},
}

def finite(x):
    if isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x):
        raise ValueError('finite number required')
    return float(x)

def total_speedup(fraction, stage_speedup, overhead=0):
    f,s,d=map(finite,(fraction,stage_speedup,overhead))
    if not 0<=f<=1 or s<=0 or d<0: raise ValueError('invalid cost inputs')
    return 1/(1-f+f/s+d)

def payload_bytes(pixels, patches=153, slots=1):
    for x in (pixels,patches,slots):
        if isinstance(x,bool) or not isinstance(x,int) or x<=0: raise ValueError('positive integer required')
    return 14*pixels*patches*slots

def scenario(producer_speedup=1.2, guard_ms=.0122, extra_classifier_ms=0.):
    r,g,q=map(finite,(producer_speedup,guard_ms,extra_classifier_ms))
    if r<=0 or g<0: raise ValueError('invalid assumption')
    rows={}
    for name,c in CELLS.items():
        # Classifier difference is unknown. Zero is a hypothetical assumption.
        remaining=c['producer_ms']/r+c['leaf_ms']+g+.0007+q
        if remaining<=0:raise ValueError('nonpositive hypothetical time')
        den=c['A_min_sum_ms']/1.10-c['leaf_ms']-g-.0007-q
        rows[name]={**c,'hypothetical_new_ms':remaining,
             'hypothetical_local_speedup':c['A_min_sum_ms']/remaining,
             'producer_factor_needed_for_local_1_10':c['producer_ms']/den if den>0 else None}
    return {'evidence_class':'hypothetical_cost_attribution_not_executed_pipeline',
       'assumptions':{'producer_speedup':r,'guard_ms':g,'classifier_cost_difference_ms':q,
          'view_ms':.0007,'mask_packing_removed_in_actual_new_source': 'required_not_proven_here',
          'new_scheduler_cost':'not modeled; continuous measurement mandatory'},
       'cells':rows,
       'space_payload_only_bytes':{'full_1024':payload_bytes(1024**2),'full_2048':payload_bytes(2048**2),
          'one_block_1024':payload_bytes(1024),'four_blocks_1024':payload_bytes(1024,slots=4)}}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--producer-speedup',type=float,default=1.2)
    ap.add_argument('--guard-ms',type=float,default=.0122)
    ap.add_argument('--extra-classifier-ms',type=float,default=0.)
    ap.add_argument('--output',type=Path)
    a=ap.parse_args();v=scenario(a.producer_speedup,a.guard_ms,a.extra_classifier_ms)
    text=json.dumps(v,indent=2,allow_nan=False)+'\n'
    if a.output:a.output.write_text(text)
    else:print(text,end='')
