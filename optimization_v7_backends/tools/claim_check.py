#!/usr/bin/env python3
"""Check final-record scope consistency, not authenticity or physical measurement validity."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from _common import number, positive_int


def check(freeze:dict, result:dict) -> dict:
    errors=[]
    try:
        if freeze.get('status')!='frozen':errors.append('Protocol is not frozen')
        if result.get('status')!='completed':errors.append('Run did not complete')
        if freeze.get('corpus_kind')!='actual_target' or result.get('run_class')!='actual_target':
            errors.append('Not the actual target corpus')
        for key in ('source_sha','dependency_sha256','fixture_set_sha256','reference_set_sha256',
                    'backend_id','clock_boundary','cache_regime'):
            if not freeze.get(key) or freeze[key]!=result.get(key):errors.append(f'Identity missing/different: {key}')
        target=freeze['target']
        k=positive_int(target['spatial_tiles'],'spatial tiles')
        canonical={'spatial_tiles':24,'rows':1024,'cols':1024,'timesteps_per_tile':24,'patches':153}
        if any(type(target.get(key)) is not int or target.get(key)!=value for key,value in canonical.items()):
            errors.append('Frozen objective is not the original 24-spatial-tile target')
        if number(target['seconds'],'seconds limit',positive=True)>1800:
            errors.append('Frozen deadline relaxes the original 1800-second target')
        expected=freeze['jobs'];jobs=result['jobs']
        if len(expected)!=k or len(jobs)!=k:errors.append('Spatial job count differs from frozen target')
        def index(items):
            out={}
            for item in items:
                name=item.get('job_id')
                if not isinstance(name,str) or not name or name in out:
                    raise ValueError('Missing or duplicate spatial job id')
                out[name]=item
            return out
        ei=index(expected);ji=index(jobs)
        if set(ei)!=set(ji):errors.append('Spatial job identities differ')
        for name,x in ji.items():
            if name not in ei:continue
            e=ei[name]
            for key in ('rows','cols','timesteps','patches','input_manifest_sha256'):
                if e.get(key) is None or x.get(key)!=e.get(key):errors.append(f'{name}: {key} differs/missing')
            if not e.get('input_manifest_sha256'):errors.append(f'{name}: no input manifest identity')
            for key,tk in (('rows','rows'),('cols','cols'),('timesteps','timesteps_per_tile'),('patches','patches')):
                if x.get(key)!=target.get(tk):errors.append(f'{name}: target {key} mismatch')
            if x.get('completed') is not True or x.get('numeric_reference_match') is not True or x.get('artifact_match') is not True:
                errors.append(f'{name}: incomplete numeric/artifact coverage')
        if result.get('device_type')!='cpu':errors.append('Primary comparison must execute on CPU')
        if result.get('outputs_durable') is not True or result.get('synchronized') is not True:
            errors.append('Results not durably complete/synchronized')
        if result.get('aborted') is not False:errors.append('Aborted status is missing/true')
        if result.get('numeric_reference_coverage')!='all_frozen_jobs':errors.append('Full frozen numeric coverage not recorded')
        t=number(result['elapsed_seconds'],'elapsed seconds',positive=True)
        limit=number(target['seconds'],'seconds limit',positive=True)
        if t>limit:errors.append('Elapsed time exceeds target')
        envelope=freeze['resource_envelope']
        cap=positive_int(envelope['cpu_budget'],'CPU cap')
        budget=positive_int(envelope['memory_budget_bytes'],'memory cap')
        if result.get('cpu_budget')!=cap:errors.append('CPU budget differs from protocol')
        w=positive_int(result['workers'],'workers');h=positive_int(result['effective_threads_per_worker'],'effective threads')
        other=positive_int(result.get('additional_concurrent_threads',0),'additional threads',zero=True)
        if min(w,k)*h+other>cap:errors.append('Declared active threads exceed CPU envelope')
        peak=positive_int(result['peak_process_tree_bytes'],'peak memory')
        if peak>budget:errors.append('Memory cap exceeded')
    except (KeyError,TypeError,ValueError) as error:
        errors.append('Invalid/incomplete record: '+str(error))
        t=None;k=None
    return {'schema':'solweig-claim-consistency-v1','record_consistent':not errors,
            'errors':errors,'tiles_per_minute':60*k/t if k and t and not errors else None,
            'authenticates_measurement':False,
            'note':'This only checks declared records. Actual source/data/timing/outputs and independent review are still required; it cannot certify real-versus-replicated scenes.'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--freeze',type=Path,required=True);p.add_argument('--result',type=Path,required=True)
    a=p.parse_args();out=check(json.loads(a.freeze.read_text()),json.loads(a.result.read_text()))
    print(json.dumps(out,indent=2));return 0 if out['record_consistent'] else 2


if __name__=='__main__':raise SystemExit(main())
