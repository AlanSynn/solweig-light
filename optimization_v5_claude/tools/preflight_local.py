#!/usr/bin/env python3
"""Nonsecret local configuration inventory. NO API/model call or backend verification."""
from __future__ import annotations
import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

MODEL_KEYS=('ANTHROPIC_MODEL','ANTHROPIC_DEFAULT_OPUS_MODEL',
            'ANTHROPIC_DEFAULT_SONNET_MODEL','ANTHROPIC_DEFAULT_HAIKU_MODEL',
            'CLAUDE_CODE_SUBAGENT_MODEL')


def safe_model(value) -> str|None:
    if value is None:return None
    value=str(value)
    if re.fullmatch(r'[A-Za-z0-9_./:\[\]-]{1,120}',value):return value
    return '<nonstandard value redacted>'


def host_only(value) -> str|None:
    if value is None:return None
    try:
        parsed=urlsplit(str(value))
        return parsed.hostname or '<host unavailable>'
    except ValueError:
        return '<invalid URL>'


def summarize_settings(data: dict) -> dict:
    env=data.get('env',{})
    if not isinstance(env,dict):env={}
    return {'requested_model_setting':safe_model(data.get('model')),
            'configured_provider_host':host_only(env.get('ANTHROPIC_BASE_URL')),
            'alias_requests':{k:safe_model(env[k]) for k in MODEL_KEYS if k in env},
            'worktree_base_ref':data.get('worktree',{}).get('baseRef') if isinstance(data.get('worktree'),dict) else None,
            'credential_fields_present':any(k in env for k in ('ANTHROPIC_AUTH_TOKEN','ANTHROPIC_API_KEY')),
            'backend_verified':False}


def collect(settings_files: list[Path], env: dict|None=None,cli: str='claude') -> dict:
    env=os.environ if env is None else env
    files=[]
    for path in settings_files:
        # Caller names these files explicitly; no recursive credential/config scan.
        data=json.loads(path.read_text())
        if not isinstance(data,dict):raise ValueError('Settings must be a JSON object')
        files.append({'file':str(path),'summary':summarize_settings(data)})
    executable=shutil.which(cli)
    version=None
    flags={k:False for k in ('--model','--agent','--settings','--effort','--setting-sources')}
    errors=[]
    if executable:
        try:
            version=subprocess.run([executable,'--version'],capture_output=True,text=True,
                                   timeout=15,check=True).stdout.strip()[:240]
            help_text=subprocess.run([executable,'--help'],capture_output=True,text=True,
                                     timeout=15,check=True).stdout
            flags={k:k in help_text for k in flags}
        except (subprocess.SubprocessError,OSError) as error:
            errors.append(type(error).__name__)
    env_summary=summarize_settings({'env':{k:env[k] for k in
        (*MODEL_KEYS,'ANTHROPIC_BASE_URL','ANTHROPIC_AUTH_TOKEN','ANTHROPIC_API_KEY') if k in env}})
    return {'schema':1,'classification':'local_nonsecret_diagnostic_only',
            'cli_present':bool(executable),'cli_version':version,'help_flags':flags,
            'settings_files':files,'shell_environment':env_summary,
            'effective_precedence_resolved':False,'errors':errors,
            'backend_verified':False,'api_calls_made':False,
            'note':'No subscription/auth/tool-use/backend test. Managed/project precedence and actual served metadata require a separate authorized route smoke.'}


def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--settings-file',type=Path,action='append',default=[])
    ap.add_argument('--cli',default='claude');ap.add_argument('--output',type=Path)
    a=ap.parse_args()
    try:report=collect(a.settings_file,cli=a.cli)
    except (ValueError,OSError) as error:ap.exit(2,f'Cannot read named settings: {error}\n')
    text=json.dumps(report,indent=2)+'\n'
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(text)
    else:print(text,end='')
    return 0

if __name__=='__main__':raise SystemExit(main())
