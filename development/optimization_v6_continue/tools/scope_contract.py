#!/usr/bin/env python3
"""Check reporting scope. This validates a RECORD, not its files or numerical truth."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

OUTPUTS={'UTCI','TMRT','Kup','Kdown','Lup','Ldown','Shadow','WBGT','Ta','Wind'}


def check(record: dict) -> dict:
    problems=[]
    tiles=record.get('tiles',[])
    if not isinstance(tiles,list): tiles=[];problems.append('tiles must be a list')
    if record.get('spatial_tiles')!=24 or len(tiles)!=24:
        problems.append('Original target requires 24 actual spatial tiles, not time bands or two scenes')
    ids=[t.get('spatial_id') for t in tiles if isinstance(t,dict)]
    if len(ids)!=len(tiles) or any(not isinstance(x,str) or not x for x in ids) or len(set(ids))!=len(ids):
        problems.append('Distinct nonempty spatial identities are required')
    if record.get('dataset_kind')!='actual_target': problems.append('Synthetic/load fixtures are not the actual-target dataset')
    for i,t in enumerate(tiles):
        if not isinstance(t,dict): problems.append(f'tile {i} is not a record');continue
        if t.get('shape')!=[1024,1024]: problems.append(f'tile {i} target shape differs')
        if t.get('timesteps')!=24 or t.get('patches')!=153: problems.append(f'tile {i} time/patch work differs')
        if t.get('status')!='complete': problems.append(f'tile {i} did not complete')
        if set(t.get('outputs',[]))!=OUTPUTS: problems.append(f'tile {i} output set differs')
        if t.get('numerical_reference_status')!='verified': problems.append(f'tile {i} large numerical coverage unverified')
    seconds=record.get('elapsed_seconds')
    if isinstance(seconds,bool) or not isinstance(seconds,(int,float)) or not math.isfinite(seconds) or not 0<seconds<=1800:
        problems.append('Elapsed seconds absent/invalid/over target')
    for name in ['source_sha','wheel_sha256','math_profile','dataset_manifest_sha256','protocol_sha256']:
        if not isinstance(record.get(name),str) or not record[name]: problems.append(f'{name} absent')
    for name in ['effective_resources_verified','required_publication_complete','application_io_included','within_resource_budget','unchanged_physical_context_verified']:
        if record.get(name) is not True: problems.append(f'{name} not established')
    if record.get('checkpoint_interval')!=1: problems.append('Checkpoint policy differs from selected target')
    return {'schema':'sw6-scope-record-check-v1','scope_only':True,
            'record_eligible_for_target_claim_review':not problems,'problems':problems,
            'numerical_data_verified_by_this_tool':False,'speed_measurement_executed_by_this_tool':False,
            'note':'A passing record check is not proof its stated results are true. Independent source/output/run evidence is still required.'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('record',type=Path);a=p.parse_args()
    result=check(json.loads(a.record.read_text()));print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['record_eligible_for_target_claim_review'] else 2)
if __name__=='__main__': main()
