"""Validate local packet links, DAG, fields and file hashes. Not model validation."""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path


def validate(root:Path,verify_hashes:bool=True):
    errors=[]
    data=json.loads((root/'TASKS_CLAUDE.yaml').read_text())
    tasks=data['tasks'];by={t['id']:t for t in tasks}
    if len(by)!=len(tasks):errors.append('duplicate task ids')
    visiting,seen=set(),set()
    def visit(key):
        if key in visiting:raise ValueError('cyclic DAG')
        if key in seen:return
        if key not in by:raise ValueError('unknown dependency '+key)
        visiting.add(key)
        for dep in by[key]['depends_on']:visit(dep)
        visiting.remove(key);seen.add(key)
    try:
        for key in by:visit(key)
    except ValueError as exc:errors.append(str(exc))
    for t in tasks:
        for rel in t['read_context']:
            if not (root/rel).is_file():errors.append('missing task context '+rel)
        if not t.get('completion_condition') or not t.get('owned_files'):errors.append('underspecified task '+t['id'])
    text=(root/'START_HERE.txt').read_text()
    if len(text)>4000:errors.append(f'START_HERE length {len(text)} >4000')
    c=json.loads((root/'CANDIDATES.json').read_text());candidates=c['candidates']
    ids=[x['id'] for x in candidates]
    if len(ids)!=len(set(ids)) or c['candidate_count']!=len(ids):errors.append('candidate count/ids invalid')
    src={x['id'] for x in json.loads((root/'SOURCES.json').read_text())['repository_sources']}
    for x in candidates:
        if any(s not in src for s in x['source_ids']):errors.append('unknown source '+x['id'])
        if not (root/x['dossier']).exists():errors.append('missing dossier '+x['id'])
        for k in ('proof_and_guard','cost_model','small_deciding_experiment','reject_or_defer_when'):
            if not x.get(k):errors.append('missing '+k+' '+x['id'])
    for f in root.rglob('*.md'):
        for url in re.findall(r'\]\(([^)]+)\)',f.read_text()):
            if '://' in url or url.startswith('#'):continue
            p=(f.parent/url.split('#')[0]).resolve()
            if not p.exists():errors.append('broken link '+str(f.relative_to(root))+':'+url)
    if verify_hashes and (root/'MANIFEST.json').exists():
        m=json.loads((root/'MANIFEST.json').read_text())
        for path,sha in m['files'].items():
            p=root/path
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=sha:
                errors.append('manifest mismatch '+path)
    return {'evidence_class':'packet_structure_check_only','success':not errors,'errors':errors,
            'candidate_count':len(candidates),'task_count':len(tasks),'start_characters':len(text),
            'project_executed':False,'performance_measured':False}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--no-hashes',action='store_true');a=p.parse_args()
    r=validate(a.root,not a.no_hashes);print(json.dumps(r,indent=2));raise SystemExit(0 if r['success'] else 1)
if __name__=='__main__':main()
