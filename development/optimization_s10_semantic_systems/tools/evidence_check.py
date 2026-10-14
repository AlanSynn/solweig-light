"""Mechanical claim-scope checks. Cannot attest an execution or approve release."""
from __future__ import annotations
import argparse, json, math
from pathlib import Path


def check_trial(r):
    errors=[]
    if r.get('evidence_class')!='measured': errors.append('not a measured trial record')
    if r.get('status')!='completed': errors.append('trial did not complete')
    duration=r.get('wall_seconds')
    if isinstance(duration,bool) or not isinstance(duration,(float,int)) or not math.isfinite(duration) or duration<=0:
        errors.append('invalid actual wall time')
    for key in ('source_sha','environment_hash','workload_manifest_sha256','pair_id','timer_boundary','raw_log'):
        if not r.get(key): errors.append(f'missing {key}')
    for key in ('spatial_tiles','timesteps_per_tile','actual_native_threads','admitted_workers','requested_cpu_budget'):
        v=r.get(key)
        if isinstance(v,bool) or not isinstance(v,int) or v<1: errors.append(f'invalid {key}')
    if r.get('timer_boundary') not in ('full_entry','complete_batch','full_stage','adapter','leaf'):
        errors.append('unrecognized timing boundary')
    if r.get('outputs_equal') is not True: errors.append('required output parity not recorded')
    if not r.get('correctness_reference'): errors.append('missing independent correctness reference')
    return errors


def target_review(r):
    errors=check_trial(r)
    if r.get('spatial_tiles')!=24:errors.append('24 time bands are not 24 spatial tiles')
    if r.get('timesteps_per_tile')!=24:errors.append('wrong target timestep count')
    if r.get('synthetic') is not False:errors.append('synthetic/unknown corpus does not verify real target')
    if r.get('timer_boundary') not in ('full_entry','complete_batch'):errors.append('partial boundary cannot verify target')
    if r.get('target_manifest_verified') is not True:errors.append('real target manifest not independently verified')
    if r.get('physical_settings_equal') is not True:errors.append('equal physical settings not recorded')
    duration=r.get('wall_seconds')
    if isinstance(duration,(int,float)) and not isinstance(duration,bool) and duration>1800:
        errors.append('target duration exceeded')
    if r.get('required_final_checks_passed') is not True:errors.append('final checks not recorded as passed')
    return {'mechanically_consistent_for_independent_review':not errors,'errors':errors,
            'certifies_actual_execution':False,'certifies_release':False,
            'note':'This validates claims/fields, not their truth. Inspect immutable logs, manifests and independent review.'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('record',type=Path);a=p.parse_args()
    r=json.loads(a.record.read_text());result=target_review(r)
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['mechanically_consistent_for_independent_review'] else 2)
if __name__=='__main__':main()
