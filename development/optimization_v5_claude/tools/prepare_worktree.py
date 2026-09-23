#!/usr/bin/env python3
"""Preview-first explicit-base Git worktree creation. No force/reset/stash/network."""
from __future__ import annotations
import argparse
import json
import subprocess
from pathlib import Path


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(['git', '-C', str(repo), *args], text=True,
                          capture_output=True, check=check)


def prepare(repo: Path, destination: Path, branch: str, base: str = 'HEAD',
            apply: bool = False) -> dict:
    root = Path(git(repo, 'rev-parse', '--show-toplevel').stdout.strip()).resolve()
    if git(root, 'check-ref-format', '--branch', branch, check=False).returncode:
        raise ValueError('Invalid branch name')
    if branch in {'main','master','trunk'}:
        raise ValueError('An optimization branch name is required')
    if git(root, 'show-ref', '--verify', '--quiet', 'refs/heads/'+branch,
           check=False).returncode == 0:
        raise ValueError('Branch already exists; choose an unused suffix, not force/reset')
    destination = destination.expanduser().resolve()
    if destination.exists():
        raise ValueError('Destination already exists; choose a new path')
    # Tracked modifications could be essential. Never silently drop or auto-stash them.
    for args in [('diff','--quiet'),('diff','--cached','--quiet')]:
        if git(root,*args,check=False).returncode:
            raise ValueError('Tracked user changes exist; resolve a safe snapshot before branching')
    untracked = git(root,'ls-files','--others','--exclude-standard','-z').stdout.split('\0')
    untracked = [x for x in untracked if x]
    unsafe = [x for x in untracked if not x.startswith('optimization_v5_claude/')]
    if unsafe:
        raise ValueError('Untracked non-packet files exist; identify their role before branching')
    sha = git(root,'rev-parse','--verify',base+'^{commit}').stdout.strip()
    command = ['git','-C',str(root),'worktree','add','-b',branch,str(destination),sha]
    report = {'mode':'apply' if apply else 'preview','base_sha':sha,
              'branch':branch,'destination':str(destination),'command':command,
              'untracked_packet_files_not_in_base':len(untracked),
              'packet_copy_required':bool(untracked),'network_used':False,
              'user_changes_stashed_or_reset':False}
    if apply:
        subprocess.run(command,check=True,capture_output=True,text=True)
        actual = git(destination,'rev-parse','HEAD').stdout.strip()
        if actual != sha:
            raise RuntimeError('Created worktree HEAD differs from requested base')
        report['actual_new_head']=actual
    return report


def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo',type=Path,default=Path('.'))
    ap.add_argument('--destination',type=Path,required=True)
    ap.add_argument('--branch',default='perf/claude-glm53-cpu-v5')
    ap.add_argument('--base',default='HEAD')
    ap.add_argument('--apply',action='store_true')
    a=ap.parse_args()
    try:
        result=prepare(a.repo,a.destination,a.branch,a.base,a.apply)
    except (ValueError,RuntimeError,subprocess.CalledProcessError) as error:
        ap.exit(2,f'Cannot prepare worktree: {error}\n')
    print(json.dumps(result,indent=2))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
