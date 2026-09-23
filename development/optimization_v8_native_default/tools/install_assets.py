"""Append short CLAUDE rules and nonconflicting agents; dry-run by default."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
from _common import PACKET, atomic_write, emit, no_symlink_ancestors, repo_root, require_branch, require_project


def install(repo: Path, apply: bool = False, packet: Path | None = None) -> dict:
    require_branch(repo);require_project(repo)
    packet = packet or Path(__file__).resolve().parents[1]
    installed = repo / PACKET / 'CLAUDE_PROJECT_RULES.md'
    no_symlink_ancestors(installed)
    if not installed.is_file() or installed.read_bytes() != (packet/'CLAUDE_PROJECT_RULES.md').read_bytes():
        raise ValueError('Place the unchanged packet at the repository root first')
    target = repo/'CLAUDE.md';no_symlink_ancestors(target)
    old = target.read_text(encoding='utf-8') if target.exists() else ''
    line = '@' + PACKET + '/CLAUDE_PROJECT_RULES.md'
    changes = []
    for source in sorted((packet/'agents').glob('*.md')):
        dest=repo/'.claude/agents'/source.name;no_symlink_ancestors(dest)
        text=source.read_text(encoding='utf-8')
        if dest.exists():
            if dest.read_text(encoding='utf-8') != text:
                raise ValueError(f'Existing nonidentical agent preserved: {dest}')
        else:
            changes.append((dest,text))
    if line not in old.splitlines():
        new=old + ('\n' if old and not old.endswith('\n') else '') + '\n' + line + '\n'
        changes.append((target,new))
    backup=None
    if any(dest==target for dest,_ in changes) and old:
        backup=repo/'.claude/sw8-backups'/('CLAUDE.'+hashlib.sha256(old.encode()).hexdigest()[:16]+'.md')
        no_symlink_ancestors(backup)
        if backup.exists() and backup.read_text(encoding='utf-8')!=old:
            raise ValueError('Backup collision; refusing all writes')
    # All conflicts checked before any writes; no permissions/provider config touched.
    if apply:
        if backup is not None and not backup.exists():atomic_write(backup,old)
        for dest,text in changes:atomic_write(dest,text)
    return {'schema':'sw8-asset-plan-v1','applied':apply,
            'writes':[str(p.relative_to(repo)) for p,_ in changes],
            'backup':str(backup.relative_to(repo)) if backup else None,
            'global_configuration_changed':False,'automatic_commit':False}


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',default='.')
    p.add_argument('--apply',action='store_true');a=p.parse_args()
    try:emit(install(repo_root(a.repo),a.apply));return 0
    except (ValueError,OSError) as exc:emit({'error':str(exc),'applied':False});return 2

if __name__=='__main__':raise SystemExit(main())
