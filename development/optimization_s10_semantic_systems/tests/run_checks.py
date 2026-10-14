"""Execute packet tests and record exact outcome; writes no project evidence."""
import datetime, hashlib, json, platform, sys, unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
suite=unittest.defaultTestLoader.discover(str(R/'tests'),pattern='test_*.py')
result=unittest.TextTestRunner(verbosity=2).run(suite)
record={'evidence_class':'packet_tools_and_standalone_semantic_checks_not_project_validation',
        'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'python':sys.version,
        'platform':platform.platform(),'tests_run':result.testsRun,
        'failures':[str(t) for t,_ in result.failures],'errors':[str(t) for t,_ in result.errors],
        'skipped':[str(t) for t,_ in result.skipped],'success':result.wasSuccessful(),
        'full_model_executed':False,'performance_measured':False,'gpu_executed':False,
        'repository_modified':False,
        'test_source_sha256':hashlib.sha256((R/'tests/test_packet_tools.py').read_bytes()).hexdigest()}
p=R/'evidence/packet_checks.json'
with p.open('x') as f:json.dump(record,f,indent=2);f.write('\n')
sys.exit(0 if result.wasSuccessful() else 1)
