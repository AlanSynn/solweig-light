#!/usr/bin/env python3
"""Append one narrow local CLAUDE import and add conflict-free optional roles; dry-run default."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
from _common import require_branch

NAME='optimization_v7_backends'
IMPORT='@optimization_v7_backends/CLAUDE_PROJECT_RULES.md'


def plan_install(repo: Path, *, include_opus: bool=False, route_confirmed: bool=False,
                 apply: bool=False) -> dict:
    root,_=require_branch(repo)
    packet=root/NAME
    if not (packet/'CLAUDE_PROJECT_RULES.md').is_file():
        raise ValueError('Put the packet under the repository root first')
    if include_opus and not route_confirmed:
        raise ValueError('Opus role requires an explicitly confirmed actual Opus route')
    destinations=[root/'CLAUDE.md',root/'.claude',root/'.claude/agents',packet,packet/'agents']
    if any(p.is_symlink() for p in destinations):
        raise ValueError('Refusing symlinked instruction/agent paths')
    claude=root/'CLAUDE.md'
    if claude.exists() and not claude.is_file():
        raise ValueError('CLAUDE.md is not a plain file')
    previous=claude.read_text(encoding='utf-8') if claude.exists() else ''
    new=previous
    if IMPORT not in previous.splitlines():
        new=previous.rstrip()+'\n\n'+IMPORT+'\n' if previous else IMPORT+'\n'
    changes=[]
    for source in sorted((packet/'agents').glob('*.md')):
        if source.is_symlink():raise ValueError('Refusing symlinked role')
        if 'opus' in source.name and not include_opus:continue
        dst=root/'.claude/agents'/source.name
        text=source.read_text(encoding='utf-8')
        if dst.is_symlink() or (dst.exists() and not dst.is_file()):
            raise ValueError('Refusing non-plain role destination')
        if dst.exists():
            if dst.read_text(encoding='utf-8')!=text:
                raise ValueError(f'Existing role differs: {dst.name}; no files changed')
        else:changes.append((dst,text))
    # Detect all conflicts before any instruction writes.
    report={'applied':apply,'claude_import_needed':new!=previous,
            'roles_to_add':[str(p.relative_to(root)) for p,_ in changes],
            'opus_route_asserted_by_caller':route_confirmed,
            'note':'No settings.json, provider, permissions, tools or credentials are changed. Frontmatter support must be checked in installed Claude Code.'}
    if apply:
        # Recheck to avoid overwriting a concurrently changed user instruction.
        now=claude.read_text(encoding='utf-8') if claude.exists() else ''
        if now!=previous:raise ValueError('CLAUDE.md changed during planning; retry without overwriting')
        if new!=previous:claude.write_text(new,encoding='utf-8')
        for dst,text in changes:
            dst.parent.mkdir(parents=True,exist_ok=True)
            with dst.open('x',encoding='utf-8') as stream:stream.write(text)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--with-opus-roles',action='store_true')
    p.add_argument('--opus-route-confirmed',action='store_true')
    p.add_argument('--apply',action='store_true')
    a=p.parse_args()
    print(json.dumps(plan_install(a.repo,include_opus=a.with_opus_roles,
          route_confirmed=a.opus_route_confirmed,apply=a.apply),indent=2))


if __name__=='__main__':
    try:main()
    except (OSError,ValueError) as e:
        print(str(e),file=sys.stderr);raise SystemExit(2)
