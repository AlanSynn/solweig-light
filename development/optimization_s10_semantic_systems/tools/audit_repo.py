"""Read-only AST/source inventory. Does NOT execute the project or prove routes."""
from __future__ import annotations
import argparse, ast, hashlib, json, re, subprocess
from pathlib import Path

MARKERS = {
 'scalar_guard':r'ndim\s*!=\s*0',
 'scalar_extraction':r'\.item\(',
 'materialization':r'ascontiguousarray|\.tobytes\(|BytesIO|\.copy\(',
 'thread_boundary':r'thread_budget|threads_per_worker|set_num_threads|prange\(',
 'io_identity':r'InputGuard|content_fingerprint|_digest\(|fsync|ReadAsArray|read_raster',
 'fallback':r'return reference\(|return _fallback\(|return None',
}

def git(root:Path,*args:str)->str|None:
    p=subprocess.run(['git','-C',str(root),*args],capture_output=True,text=True,check=False)
    return p.stdout.strip() if p.returncode==0 else None


def inventory(repo:Path)->dict:
    repo=repo.resolve()
    base=repo/'src'/'solweig_light'
    if not base.is_dir(): raise ValueError('Expected src/solweig_light under explicit repository root')
    files=[]
    for path in sorted(base.rglob('*.py')):
        if not path.resolve().is_relative_to(repo):
            raise ValueError(f'External source symlink refused: {path}')
        raw=path.read_bytes()
        if len(raw)>2*1024*1024: raise ValueError(f'Unexpectedly large source file: {path}')
        text=raw.decode('utf8')
        tree=ast.parse(text,filename=str(path))
        defs=[{'name':n.name,'line':n.lineno,'end_line':n.end_lineno}
              for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))]
        imports=[]
        for n in ast.walk(tree):
            if isinstance(n,ast.Import): imports.extend(a.name for a in n.names)
            if isinstance(n,ast.ImportFrom): imports.append('.'*n.level+(n.module or ''))
        hits={k:[i for i,line in enumerate(text.splitlines(),1) if re.search(v,line)]
              for k,v in MARKERS.items()}
        files.append({'path':str(path.relative_to(repo)),'sha256':hashlib.sha256(raw).hexdigest(),
                      'bytes':len(raw),'definitions':defs,'import_syntax':sorted(set(imports)),
                      'candidate_markers':hits})
    return {'evidence_class':'read_only_source_inventory_not_execution',
            'head':git(repo,'rev-parse','HEAD'),'branch':git(repo,'branch','--show-current'),
            'main':git(repo,'rev-parse','main'),'dirty_paths':git(repo,'status','--porcelain'),
            'integration_branch_expected':'perf/s10-semantic-systems','file_count':len(files),'files':files,
            'limits':['AST markers are leads, not performance or semantic findings.',
                      'Import syntax is not complete dynamic dependency closure.',
                      'No numerical code, private inputs or model providers executed.']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    out=a.output.resolve()
    if out.is_relative_to((a.repo.resolve()/'src')):
        raise ValueError('Evidence output cannot modify product source')
    result=inventory(a.repo)
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x') as f: json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({'file_count':result['file_count'],'head':result['head'],'output':str(out)}))
if __name__=='__main__':main()
