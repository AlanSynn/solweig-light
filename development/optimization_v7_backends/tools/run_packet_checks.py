#!/usr/bin/env python3
"""Run only packet/tool tests in disposable directories; never the SOLWEIG model."""
from __future__ import annotations
import argparse
import datetime
import hashlib
import io
import json
from pathlib import Path
import platform
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,help='New output file; defaults to stdout JSON after log')
    a=p.parse_args()
    if a.out and a.out.exists():
        p.error('Evidence path exists; choose a new path, no overwrite')
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_*.py')
    log=io.StringIO();result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    record={'schema':'solweig-v7-packet-checks-v1','measurement_class':'packet_helper_tests_only',
            'executed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'python':platform.python_version(),'host_system':platform.system(),
            'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
            'skipped':len(result.skipped),'successful':result.wasSuccessful(),
            'solweig_executed':False,'framework_backend_executed':False,
            'user_repository_modified':False,'claude_or_provider_called':False,
            'start_prompt_characters':len((ROOT/'START_HERE.txt').read_text()),
            'scope':'Stdlib analytical models, declared-record checks, document/task structure and disposable local Git/installer behavior. Synthetic helper records are not measurements.',
            'test_log':log.getvalue(),
            'tested_code_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest()
                     for folder in ('tools','tests') for f in sorted((ROOT/folder).glob('*.py'))}}
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True)
        with a.out.open('x') as f:json.dump(record,f,indent=2);f.write('\n')
        print(json.dumps({k:record[k] for k in ('tests_run','failures','errors','skipped','successful','start_prompt_characters')}))
    else:print(json.dumps(record,indent=2))
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':raise SystemExit(main())
