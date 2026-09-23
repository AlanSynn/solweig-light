#!/usr/bin/env python3
"""Validate final-record shape and contradictions only, NOT evidence truth."""
import argparse
import json
import re
from pathlib import Path

STATUSES={'closed_native_qualified','closed_cpu_only','blocked_no_safe_merge'}
def errors(record):
    e=[]
    if not isinstance(record,dict): return ['record must be a JSON object']
    if record.get('schema')!='solweig.final-optimization.v1': e.append('invalid schema')
    if record.get('status') not in STATUSES:e.append('status is not terminal')
    if record.get('source_branch')!='perf/native-optimization': e.append('wrong source branch')
    if record.get('target_branch')!='main':e.append('wrong target branch')
    for key in ('source_sha','target_sha','source_tree_sha'):
        if not isinstance(record.get(key),str) or not re.fullmatch(r'[0-9a-f]{40}',record[key]):e.append(key+' must be a full SHA')
    for key in ('native_goal_achieved','native_research_closed_for_release','ready_for_merge','required_release_safety_passed'):
        if type(record.get(key)) is not bool:e.append(key+' must be Boolean')
    if record.get('native_research_closed_for_release') is not True:e.append('native must close for this release')
    if record.get('ready_for_merge') and not record.get('required_release_safety_passed'):e.append('merge-ready without safety pass')
    for k in ('evidence_paths','exclusions','outstanding_claims','limitations','remote_actions_performed'):
        if not isinstance(record.get(k),list):e.append(k+' must be a list')
    if not record.get('evidence_paths'):e.append('evidence paths required; schema does not verify contents')
    if record.get('remote_actions_performed') not in ([],None):e.append('this local-finalization task authorizes no remote actions')
    if record.get('actual_target_status') not in ('demonstrated_once','unverified','not_attempted','failed'):e.append('invalid actual target scope')
    if not isinstance(record.get('upstream_comparison_status'),str):e.append('upstream comparison status required')
    status=record.get('status')
    if status=='closed_cpu_only':
        if record.get('native_goal_achieved') is not False:e.append('CPU-only cannot claim native success')
        if record.get('default_backend')!='numba':e.append('CPU-only must use verified numba route')
    if status=='closed_native_qualified':
        if record.get('native_goal_achieved') is not True:e.append('native qualification requires native success')
        if record.get('default_backend')!='qualified_native_with_cpu_fallback':e.append('wrong native policy')
    if status=='blocked_no_safe_merge' and record.get('ready_for_merge') is not False:e.append('blocked cannot be merge-ready')
    for key in ('native_goal_open','remaining_flip_conditions'):
        if key in record:e.append('open-ended handoff field forbidden: '+key)
    return e

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('record',type=Path)
    a=ap.parse_args()
    try:out=errors(json.loads(a.record.read_text()))
    except (OSError,ValueError) as exc:out=[str(exc)]
    print(json.dumps({'structurally_valid':not out,'errors':out,
       'evidence_verified':False,'approval_authority':False},indent=2))
    raise SystemExit(1 if out else 0)
