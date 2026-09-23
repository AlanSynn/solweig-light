#!/usr/bin/env python3
"""Preview-first project agent installation. Never edits provider auth or CI."""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path

PACKET=Path(__file__).resolve().parents[1]
BEGIN='<!-- BEGIN SOLWEIG CLAUDE V5 -->'
END='<!-- END SOLWEIG CLAUDE V5 -->'
BLOCK=BEGIN+'\n@optimization_v5_claude/CLAUDE_PROJECT_RULES.md\n'+END+'\n'


def command(repo: Path,*args: str) -> str:
    return subprocess.run(['git','-C',str(repo),*args],check=True,text=True,
                          capture_output=True).stdout.strip()


def safe_path(root: Path,path: Path) -> None:
    if not path.is_relative_to(root):
        raise ValueError('Install path escapes project')
    current=path
    while current != root:
        if current.is_symlink():
            raise ValueError('Refusing a symlinked instruction/agent path')
        current=current.parent


def plan_install(repo: Path) -> tuple[Path, list[tuple[Path,bytes|None,bytes]]]:
    root=Path(command(repo,'rev-parse','--show-toplevel')).resolve()
    # The import must work from this worktree, not only from the source of the installer.
    rules=root/'optimization_v5_claude/CLAUDE_PROJECT_RULES.md'
    safe_path(root,rules)
    if not rules.is_file():
        raise ValueError('Copy the nonsecret optimization_v5_claude packet into the target worktree first')
    changes=[]
    for source in sorted((PACKET/'agents').glob('sw-*.md')):
        dest=root/'.claude/agents'/source.name
        safe_path(root,dest)
        new=source.read_bytes()
        if dest.exists():
            if not dest.is_file() or dest.read_bytes()!=new:
                raise ValueError(f'Conflicting agent file: {dest.name}; no file was changed')
        else:
            changes.append((dest,None,new))
    claude=root/'CLAUDE.md'
    safe_path(root,claude)
    old=claude.read_bytes() if claude.exists() else None
    text=(old or b'').decode('utf8')
    if BEGIN in text or END in text:
        if BLOCK not in text:
            raise ValueError('Existing v5 marker has different contents; inspect it explicitly')
    else:
        new=(text.rstrip()+'\n\n' if text.strip() else '')+BLOCK
        changes.append((claude,old,new.encode()))
    return root,changes


def install(repo: Path,apply: bool=False) -> dict:
    root,changes=plan_install(repo)
    branch=command(root,'symbolic-ref','--short','HEAD')
    protected={'main','master','trunk'}
    try:
        protected.add(command(root,'symbolic-ref','--short','refs/remotes/origin/HEAD').removeprefix('origin/'))
    except subprocess.CalledProcessError:
        pass
    if apply and branch in protected:
        raise ValueError('Refusing to install in the default/protected checkout; use the optimization worktree')
    report={'mode':'apply' if apply else 'preview','branch':branch,
            'paths':[str(p.relative_to(root)) for p,_,_ in changes],
            'agents_available':len(list((PACKET/'agents').glob('sw-*.md'))),
            'global_settings_changed':False,'provider_auth_changed':False,
            'ci_changed':False,'model_calls_made':False}
    if apply:
        # Validate all paths/content before any write. Concurrent installers are not supported.
        for path,old,_ in changes:
            safe_path(root,path)
            current=path.read_bytes() if path.exists() else None
            if current!=old:
                raise ValueError('Target changed after preview; rerun against the new state')
        written=[]
        try:
            for path,old,new in changes:
                path.parent.mkdir(parents=True,exist_ok=True)
                if old is None:
                    with path.open('xb') as f:
                        f.write(new)
                else:
                    fd,tmp=tempfile.mkstemp(prefix='.claude-v5-',dir=path.parent)
                    try:
                        with os.fdopen(fd,'wb') as f:
                            f.write(new)
                        os.replace(tmp,path)
                    finally:
                        Path(tmp).unlink(missing_ok=True)
                written.append((path,old,new))
        except BaseException:
            # Do not overwrite an unrelated concurrent user's edit during rollback.
            for path,old,new in reversed(written):
                if path.exists() and path.read_bytes()==new:
                    if old is None:path.unlink()
                    else:path.write_bytes(old)
            raise
    return report


def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo',type=Path,default=Path('.'))
    ap.add_argument('--apply',action='store_true')
    a=ap.parse_args()
    try:result=install(a.repo,a.apply)
    except (ValueError,OSError,UnicodeError,subprocess.CalledProcessError) as error:
        ap.exit(2,f'Cannot install assets: {error}\n')
    print(json.dumps(result,indent=2));return 0

if __name__=='__main__':raise SystemExit(main())
