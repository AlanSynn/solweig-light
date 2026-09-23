#!/usr/bin/env python3
"""Standalone Numba configuration probe, NOT a SOLWEIG benchmark. Preview default."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

LIMIT_KEYS=('NUMBA_NUM_THREADS','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS',
            'NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS','BLIS_NUM_THREADS')


def child_environment(threads: int, cache: str) -> dict[str,str]:
    if isinstance(threads,bool) or not isinstance(threads,int) or threads<1:
        raise ValueError('threads must be a positive integer')
    env=os.environ.copy()
    for key in LIMIT_KEYS: env[key]=str(threads)
    env['NUMBA_CACHE_DIR']=cache
    return env


def probe_child(requested: int) -> dict:
    # These imports occur only after the launcher sets environment limits.
    import numpy as np
    import numba
    from numba import njit, prange
    @njit(parallel=True,fastmath=False,cache=False)
    def fill(out,ids):
        for i in prange(out.size):
            out[i]=np.float32(i)+np.float32(1)
            ids[i]=numba.get_thread_id()
    out=np.empty(65536,np.float32);ids=np.empty(out.size,np.int32)
    fill(out,ids)
    if not np.array_equal(out,np.arange(out.size,dtype=np.float32)+np.float32(1)):
        raise RuntimeError('Standalone probe arithmetic check failed')
    result={'requested_threads':requested,'configured_pool_threads':int(numba.config.NUMBA_NUM_THREADS),
            'effective_thread_mask':int(numba.get_num_threads()),
            'observed_probe_thread_ids':np.unique(ids).tolist(),
            'threading_layer':numba.threading_layer(),'python':sys.version.split()[0],
            'numpy':np.__version__,'numba':numba.__version__,'process_id':os.getpid(),
            'numba_env':os.environ.get('NUMBA_NUM_THREADS'),
            'scope':'standalone_numba_probe_not_solweig_or_target_host_benchmark'}
    if result['effective_thread_mask']!=requested or result['configured_pool_threads']!=requested:
        raise RuntimeError('Requested and actual probe thread settings disagree')
    return result


def launch(python: str, threads: list[int], timeout: float=120) -> dict:
    records=[]
    with tempfile.TemporaryDirectory(prefix='sw6-thread-probe-') as root:
        for n in threads:
            cache=str(Path(root)/str(n))
            cmd=[python,str(Path(__file__).resolve()),'--child',str(n)]
            p=subprocess.run(cmd,env=child_environment(n,cache),capture_output=True,text=True,timeout=timeout)
            if p.returncode:
                # Do not dump environment/settings; stderr is limited to this numerical child.
                raise RuntimeError(f'Probe h={n} failed with code {p.returncode}: {p.stderr[-2000:]}')
            records.append(json.loads(p.stdout))
    return {'schema':'sw6-thread-probes-v1','scope':'helper_execution_only','records':records,
            'solweig_executed':False,'target_host_performance_claim':False}


def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--threads',type=int,nargs='+',default=[1,2])
    ap.add_argument('--python',default=sys.executable)
    ap.add_argument('--out',type=Path)
    ap.add_argument('--execute',action='store_true')
    ap.add_argument('--child',type=int)
    a=ap.parse_args()
    if a.child is not None:
        print(json.dumps(probe_child(a.child)));return
    if any(n<1 for n in a.threads): ap.error('thread counts must be positive')
    if not a.execute:
        print(json.dumps({'preview':True,'threads':a.threads,'python':a.python,
              'action':'Run independent tiny Numba probes only with --execute; no repository code imported.'},indent=2));return
    result=launch(a.python,a.threads)
    text=json.dumps(result,indent=2)+'\n'
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(text)
    else: print(text,end='')

if __name__=='__main__': main()
