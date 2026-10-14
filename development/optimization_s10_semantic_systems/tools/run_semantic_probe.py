"""Run tiny transcribed-expression checks; not the installed SOLWEIG model."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'reference'/'prior_semantic_probe.py'

def load():
    spec=importlib.util.spec_from_file_location('s10_prior_semantic_probe',SOURCE)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run():
    m=load(); result=m.run()
    # A finite input can still make an unused table state overflow.
    surface=np.array([[np.finfo(np.float32).max]],np.float32)
    false=np.array([[False]]);true=np.array([[True]])
    with np.errstate(over='raise',invalid='raise'):
        observed=m.contribution(surface,false,np.float32(2),np.float32(1),false)
        old_safe=bool(np.array_equal(observed.view(np.uint32),np.zeros((1,1),np.float32).view(np.uint32)))
        rejected=False
        try:m.contribution(surface,true,np.float32(2),np.float32(1),true)
        except FloatingPointError:rejected=True
    if not old_safe or not rejected:
        raise AssertionError('Expected guarded-precomputation counterexample was not reproduced')
    result['extra_counterexample']={'finite_inputs_do_not_prove_safe_all_state_precompute':True,
        'original_used_state_safe':old_safe,'unused_state_raises_overflow':rejected}
    result['probe_sha256']=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    result['authoring_check']='new local reexecution of preserved transcribed NumPy probe'
    result['full_model_executed']=False;result['performance_measured']=False
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=run();a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({'evidence_class':result['evidence_class'],
                      'finite_values_checked':result['finite_contribution_values_checked'],
                      'performance_measured':False,'full_model_executed':False}))
if __name__=='__main__':main()
