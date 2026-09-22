"""Run only packet/helper tests; explicitly NOT a SOLWEIG/native qualification."""
from __future__ import annotations
import datetime
import io
import json
from pathlib import Path
import platform
import sys
import time
import unittest


def main() -> int:
    root=Path(__file__).resolve().parents[1]
    sys.path.insert(0,str(root/'tools'))
    started=time.perf_counter();stream=io.StringIO()
    suite=unittest.defaultTestLoader.discover(str(root/'tests'),pattern='test_*.py')
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    out=root/'evidence';out.mkdir(exist_ok=True)
    (out/'packet_test_log.txt').write_text(stream.getvalue())
    report={'schema':'sw8-packet-checks-v1','evidence_kind':'packet_tools_only',
            'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'python':platform.python_version(),'tests_run':result.testsRun,
            'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
            'elapsed_seconds':round(time.perf_counter()-started,3),'passed':result.wasSuccessful(),
            'solweig_executed':False,'native_benchmark_executed':False,'wheel_runtime_verified':False,
            'repository_user_branch_changed':False,'production_native_default_qualified':False,
            'note':'Synthetic records and dummy repositories/wheel archives test helpers, not the model.'}
    (out/'packet_checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(stream.getvalue());print(json.dumps(report,indent=2));return 0 if result.wasSuccessful() else 1

if __name__=='__main__':raise SystemExit(main())
