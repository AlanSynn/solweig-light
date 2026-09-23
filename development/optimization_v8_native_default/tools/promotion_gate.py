"""Evaluate declared policy data, not evidence authenticity or production qualification."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import re
import statistics

QUALIFICATIONS=('numeric','dx','installed_wheel','source_fallback','independent_review','resources','cold_first_use')


def ratios(pairs: list[dict]) -> list[float]:
    if not isinstance(pairs,list) or len(pairs)<3:raise ValueError('need at least three completed pairs')
    out=[]
    for pair in pairs:
        a,c=pair['baseline_s'],pair['candidate_s']
        if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<=0 for v in (a,c)):
            raise ValueError('times must be finite and positive')
        out.append(a/c)
    return out


def assess(record: dict) -> dict:
    errors=[];summary=[]
    if record.get('schema')!='sw8-default-promotion-record-v1':errors.append('wrong record schema')
    if record.get('status')!='observed':errors.append('record is not an observed-result declaration')
    if record.get('branch')!='perf/native-optimization':errors.append('wrong integration branch')
    if record.get('protocol_frozen_before_candidates') is not True:errors.append('protocol not frozen before candidates')
    for field,n in [('source_sha',40),('protocol_sha256',64),('artifact_sha256',64)]:
        if not re.fullmatch('[0-9a-f]{'+str(n)+'}',str(record.get(field,''))):errors.append('missing/invalid '+field)
    for field in QUALIFICATIONS:
        if record.get('qualification',{}).get(field)!='passed':errors.append('qualification not passed: '+field)
    cells=record.get('cells',[])
    if not isinstance(cells,list):cells=[];errors.append('cells must be a list')
    primaries=[];guards=0;defaults=0;ids=set()
    for cell in cells:
        label=cell.get('id')
        if not label or label in ids:errors.append('missing/duplicate cell id')
        ids.add(label)
        prefix=str(label)+': '
        if cell.get('clean_complete') is not True:errors.append(prefix+'incomplete/censored/noisy evidence')
        if cell.get('matched_budget') is not True:errors.append(prefix+'unmatched resources')
        if cell.get('thread_observed') is not True:errors.append(prefix+'effective threads not observed')
        if cell.get('default_env_unset') is not True:errors.append(prefix+'candidate is not no-env default')
        if not cell.get('raw_evidence_paths'):errors.append(prefix+'raw evidence references missing')
        try:a=statistics.median(ratios(cell.get('pairs_current')))
        except (ValueError,KeyError,TypeError) as exc:
            errors.append(prefix+str(exc));continue
        row={'id':label,'paired_median_A0_over_candidate':a}
        if cell.get('kind')=='primary':
            try:b=statistics.median(ratios(cell.get('pairs_control')))
            except (ValueError,KeyError,TypeError) as exc:
                errors.append(prefix+str(exc));continue
            row['paired_median_B1_over_candidate']=b
            if a<1.05:errors.append(prefix+'native primary gain over A0 below 1.05')
            if b<1.05:errors.append(prefix+'gain over equivalent-layout B1 below 1.05')
            eligible,done=cell.get('eligible_work'),cell.get('native_executed_work')
            if (type(eligible)is not int or type(done)is not int or eligible<=0 or done<0 or done>eligible):
                errors.append(prefix+'invalid actual native work counters')
            elif done/eligible<.8:errors.append(prefix+'native coverage below 80 percent')
            primaries.append(a)
            if cell.get('main_defaults_covered') is True:defaults+=1
        elif cell.get('kind')=='guard':
            guards+=1
            if 1/a>1.03:errors.append(prefix+'guard paired median regression exceeds 3 percent')
        else:errors.append(prefix+'unknown cell kind')
        summary.append(row)
    geo=math.exp(sum(math.log(x) for x in primaries)/len(primaries)) if primaries else None
    if len(primaries)<4:errors.append('fewer than four primary evaluation cells')
    if defaults<1:errors.append('no primary main-default cell')
    if guards<1:errors.append('no protected fallback/default guard')
    if geo is None or geo<1.10:errors.append('primary geometric mean gain below 1.10')
    if record.get('actual_target_status')=='demonstrated_once':
        t=record.get('actual_target',{})
        if (t.get('workload_kind')!='actual_target' or t.get('spatial_tiles')!=24 or t.get('timesteps_per_tile')!=24
            or t.get('completed_tiles')!=24 or t.get('numeric_coverage')!='qualified'
            or t.get('memory_scope')!='process_tree' or t.get('resource_gate')!='passed'):
            errors.append('invalid actual-target scope/completion declaration')
        elapsed=t.get('elapsed_s')
        if isinstance(elapsed,bool) or not isinstance(elapsed,(int,float)) or not math.isfinite(elapsed) or not 0<elapsed<=1800:
            errors.append('actual target time gate not met')
    return {'schema':'sw8-declared-policy-gate-v1','policy_data_passed':not errors,
            'errors':errors,'cells':summary,'primary_geomean_A0_over_candidate':geo,
            'production_default_qualified':False,
            'evidence_authenticity_checked':False,
            'notice':'Structured policy check only. Independent review must verify raw execution, artifacts and provenance.'}


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('record',type=Path);a=p.parse_args()
    try:
        record=json.loads(a.record.read_text());report=assess(record)
    except (OSError,ValueError,TypeError,AttributeError) as exc:
        report={'policy_data_passed':False,'errors':[str(exc)],'production_default_qualified':False}
    print(json.dumps(report,indent=2,allow_nan=False));return 0 if report['policy_data_passed'] else 2

if __name__=='__main__':raise SystemExit(main())
