"""Read Git source with AST; not an operational signature/API validation."""
from __future__ import annotations
import argparse
import ast
import hashlib
from pathlib import Path
from _common import commit, emit, git, repo_root

PUBLIC=('thermal_comfort','preprocess','build_inputs','build_wind_ext_coeff',
        'run_walls_aspect','calculate_svf','run_utci_tiles')


def summarize(source: str) -> dict:
    tree=ast.parse(source)
    result={}
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in PUBLIC:
            result[node.name]={'arguments_ast':ast.dump(node.args,include_attributes=False),
                               'return_annotation':ast.dump(node.returns,include_attributes=False) if node.returns else None,
                               'decorators':[ast.dump(d,include_attributes=False) for d in node.decorator_list]}
    return result


def snapshot(repo: Path, ref: str) -> dict:
    sha=commit(repo,ref);files={}
    for rel in ('src/solweig_light/api.py','src/solweig_light/__init__.py',
                'src/solweig_light/cli.py','src/solweig_light/runtime.py','pyproject.toml'):
        source=git(repo,'show',sha+':'+rel)
        files[rel]={'sha256_of_git_text':hashlib.sha256(source.encode()).hexdigest()}
        if rel.endswith('/api.py'):files[rel]['public_source_signatures']=summarize(source)
        if rel.endswith('/runtime.py'):
            tree=ast.parse(source)
            files[rel]['runtime_options_fields']=[ast.dump(n,include_attributes=False)
                  for c in tree.body if isinstance(c,ast.ClassDef) and c.name=='RuntimeOptions'
                  for n in c.body if isinstance(n,ast.AnnAssign)]
    return {'schema':'sw8-source-surface-v1','evidence_kind':'source_ast_not_runtime',
            'commit':sha,'files':files,'operational_parity_tested':False}


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',default='.')
    p.add_argument('--ref',required=True);a=p.parse_args()
    try:emit(snapshot(repo_root(a.repo),a.ref));return 0
    except (ValueError,OSError,SyntaxError) as exc:emit({'error':str(exc)});return 2

if __name__=='__main__':raise SystemExit(main())
