"""Helper/specification tests only. No SOLWEIG or numerical backend is executed."""
from __future__ import annotations
import copy
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import performance_model as m
from claim_check import check
from prepare_worker import prepare
from install_assets import plan_install
from preflight import inspect
from _common import write_new_json


class Models(unittest.TestCase):
    def test_unchanged(self):
        self.assertEqual(m.speedup([.6],[1])['speedup'],1)
    def test_known_sensitivity(self):
        self.assertAlmostEqual(m.speedup([.6],[3],.03)['speedup'],1/.63)
    def test_multiple_disjoint(self):
        self.assertAlmostEqual(m.speedup([.2,.3],[2,3],.05)['remaining_ratio'],.75)
    def test_overlap_rejected(self):
        with self.assertRaises(ValueError):m.speedup([.6,.5],[2,2])
    def test_invalid_values(self):
        for x in (math.nan,math.inf,-1,True):
            with self.subTest(x=x),self.assertRaises(ValueError):m.speedup([x],[2])
    def test_required(self):
        self.assertAlmostEqual(m.required_local_speedup(.6,2,.03),8.57142857142858)
    def test_impossible(self):
        self.assertIsNone(m.required_local_speedup(.2,2,.03))
    def test_breakeven_strict(self):
        self.assertEqual(m.break_even_tiles(20,10,4,1),5)
        self.assertIsNone(m.break_even_tiles(20,10,9,2))
    def test_phase_serial_not_divided(self):
        x=m.phase_batch(24,[dict(name='serial',workers=1,threads=1,worker_bytes=100,per_job_seconds=10)],4,1000)
        self.assertEqual(x['seconds'],240)
    def test_phase_parallel(self):
        x=m.phase_batch(24,[dict(name='parallel',workers=4,threads=2,worker_bytes=100,per_job_seconds=10)],8,1000,overhead_seconds=10)
        self.assertEqual(x['seconds'],70)
        self.assertAlmostEqual(x['tiles_per_minute'],1440/70)
    def test_resource_rejection(self):
        p=[dict(name='x',workers=4,threads=2,worker_bytes=100,per_job_seconds=10)]
        with self.assertRaises(ValueError):m.phase_batch(24,p,4,1000)
        with self.assertRaises(ValueError):m.phase_batch(24,p,8,399)
    def test_model_label(self):
        self.assertEqual(m.speedup([.5],[2])['measurement_class'],'hypothetical_model')


def record_pair():
    f=json.loads((ROOT/'templates/final_freeze.json').read_text())
    r=json.loads((ROOT/'templates/final_result.json').read_text())
    f['status']='frozen';r['status']='completed'
    for key in ('source_sha','dependency_sha256','fixture_set_sha256','reference_set_sha256',
                'backend_id','clock_boundary','cache_regime'):
        f[key]=r[key]='synthetic_helper_test_'+key
    f['resource_envelope']={'cpu_budget':8,'memory_budget_bytes':12000}
    r.update(elapsed_seconds=1700,peak_process_tree_bytes=10000,cpu_budget=8,workers=4,
             effective_threads_per_worker=2,outputs_durable=True,synchronized=True,
             numeric_reference_coverage='all_frozen_jobs')
    for i in range(24):
        x=dict(job_id=f'test_{i}',rows=1024,cols=1024,timesteps=24,patches=153,
               input_manifest_sha256=f'test_input_{i}')
        f['jobs'].append(x)
        r['jobs'].append(dict(x,completed=True,numeric_reference_match=True,artifact_match=True))
    return f,r


class Claims(unittest.TestCase):
    def test_consistent_declared_record(self):
        f,r=record_pair();out=check(f,r)
        self.assertTrue(out['record_consistent'])
        self.assertFalse(out['authenticates_measurement'])
    def test_two_scenes_not_24(self):
        f,r=record_pair();r['jobs']=r['jobs'][:2]
        self.assertFalse(check(f,r)['record_consistent'])
    def test_duplicate_ids(self):
        f,r=record_pair();r['jobs'][1]['job_id']=r['jobs'][0]['job_id']
        self.assertFalse(check(f,r)['record_consistent'])
    def test_gpu_not_cpu(self):
        f,r=record_pair();r['device_type']='gpu'
        self.assertFalse(check(f,r)['record_consistent'])
    def test_unsynchronized(self):
        f,r=record_pair();r['synchronized']=False
        self.assertFalse(check(f,r)['record_consistent'])
    def test_missing_reference(self):
        f,r=record_pair();r['numeric_reference_coverage']='two_scenes_only'
        self.assertFalse(check(f,r)['record_consistent'])
    def test_changed_source(self):
        f,r=record_pair();r['source_sha']='different'
        self.assertFalse(check(f,r)['record_consistent'])
    def test_timeout_and_memory(self):
        f,r=record_pair();r['elapsed_seconds']=1801
        self.assertFalse(check(f,r)['record_consistent'])
        r['elapsed_seconds']=1700;r['peak_process_tree_bytes']=12001
        self.assertFalse(check(f,r)['record_consistent'])
    def test_thread_oversubscription(self):
        f,r=record_pair();r['additional_concurrent_threads']=1
        self.assertFalse(check(f,r)['record_consistent'])
    def test_redefined_target_rejected(self):
        f,r=record_pair();f['target']['spatial_tiles']=2
        f['jobs']=f['jobs'][:2];r['jobs']=r['jobs'][:2]
        self.assertFalse(check(f,r)['record_consistent'])
    def test_relaxed_deadline_rejected(self):
        f,r=record_pair();f['target']['seconds']=9999;r['elapsed_seconds']=9990
        self.assertFalse(check(f,r)['record_consistent'])
    def test_templates_do_not_pass(self):
        f=json.loads((ROOT/'templates/final_freeze.json').read_text())
        r=json.loads((ROOT/'templates/final_result.json').read_text())
        self.assertFalse(check(f,r)['record_consistent'])


class Specification(unittest.TestCase):
    def test_start_length(self):
        s=(ROOT/'START_HERE.txt').read_text()
        self.assertLessEqual(len(s),4000)
        self.assertIn('perf/cpu-optimization',s)
    def test_dag(self):
        data=json.loads((ROOT/'TASKS_CLAUDE.yaml').read_text())
        items={x['id']:x for x in data['tasks']}
        self.assertEqual(len(items),len(data['tasks']))
        done=set();active=set()
        def visit(i):
            self.assertNotIn(i,active)
            if i in done:return
            active.add(i)
            for j in items[i]['depends_on']:
                self.assertIn(j,items);visit(j)
            active.remove(i);done.add(i)
        for i in items:visit(i)
        self.assertEqual(len(done),20)
    def test_dossiers_exist_and_tasks_pending(self):
        for t in json.loads((ROOT/'TASKS_CLAUDE.yaml').read_text())['tasks']:
            self.assertTrue((ROOT/t['dossier']).is_file())
            self.assertEqual(t['status'],'pending')
    def test_agent_frontmatter_minimal(self):
        agents=list((ROOT/'agents').glob('*.md'))
        self.assertEqual(len(agents),7)
        for p in agents:
            s=p.read_text();self.assertTrue(s.startswith('---\n'))
            header=s.split('---',2)[1]
            self.assertIn('name:',header);self.assertIn('description:',header)
            self.assertTrue('model: inherit' in header or 'model: opus' in header)
    def test_provenance_honesty(self):
        s=json.loads((ROOT/'SOURCE_STATUS.json').read_text())
        self.assertFalse(s['solweig_execution_by_packet_author'])
        self.assertFalse(s['backend_benchmark_executed'])
        self.assertEqual(s['required_branch'],'perf/cpu-optimization')
    def test_single_campaign_policy(self):
        s=(ROOT/'VALIDATION_POLICY.md').read_text()
        self.assertIn('one campaign',s)
        self.assertIn('zero',s)
        self.assertIn('one corrective retry',s.lower())
    def test_no_placeholders_installed_as_solweig(self):
        self.assertFalse((ROOT/'src/solweig_light').exists())
        self.assertNotIn('NotImplementedError', ''.join(p.read_text() for p in (ROOT/'tools').glob('*.py')))


class LocalGitTools(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='solweig-packet-test-')
        self.base=Path(self.tmp.name);self.repo=self.base/'repo';self.repo.mkdir()
        def g(*args):
            c=subprocess.run(['git','-C',str(self.repo),*args],capture_output=True,text=True)
            if c.returncode:raise RuntimeError(c.stderr)
            return c.stdout.strip()
        self.g=g
        self.g('init','-q');self.g('config','user.name','Packet Test');self.g('config','user.email','test@example.invalid')
        (self.repo/'tracked.txt').write_text('fixture\n')
        self.g('add','tracked.txt');self.g('commit','-q','-m','helper test fixture')
        self.g('branch','-M','perf/cpu-optimization');self.head=self.g('rev-parse','HEAD')
        packet=self.repo/'optimization_v7_backends';packet.mkdir()
        shutil.copy2(ROOT/'CLAUDE_PROJECT_RULES.md',packet/'CLAUDE_PROJECT_RULES.md')
        shutil.copytree(ROOT/'agents',packet/'agents')
    def tearDown(self):
        self.tmp.cleanup()
    def test_preflight_readonly(self):
        before=self.g('status','--porcelain=v1')
        out=inspect(self.repo)
        self.assertEqual(out['head'],self.head)
        self.assertFalse(out['kernel_executed'])
        self.assertEqual(before,self.g('status','--porcelain=v1'))
        self.assertNotIn('AUTH_TOKEN',json.dumps(out))
    def test_wrong_branch_refused(self):
        self.g('checkout','-q','-b','other')
        with self.assertRaises(ValueError):inspect(self.repo)
        self.assertEqual(self.g('branch','--show-current'),'other')
    def test_worker_dry_run_and_apply(self):
        dst=self.base/'worker'
        result=prepare(self.repo,self.head,dst)
        self.assertFalse(result['applied']);self.assertFalse(dst.exists())
        result=prepare(self.repo,self.head,dst,apply=True)
        self.assertTrue(result['applied']);self.assertEqual(self.g('rev-parse','HEAD'),self.head)
        count=self.g('for-each-ref','--format=%(refname)','refs/heads').splitlines()
        self.assertEqual(len(count),1)
        c=subprocess.run(['git','-C',str(dst),'symbolic-ref','-q','HEAD'],capture_output=True)
        self.assertNotEqual(c.returncode,0)
    def test_existing_worker_destination_refused(self):
        dst=self.base/'existing';dst.mkdir();(dst/'user.txt').write_text('keep')
        with self.assertRaises(ValueError):prepare(self.repo,self.head,dst,apply=True)
        self.assertEqual((dst/'user.txt').read_text(),'keep')
    def test_installer_preserves_and_idempotent(self):
        p=self.repo/'CLAUDE.md';p.write_text('Existing user rules\n')
        plan_install(self.repo);self.assertEqual(p.read_text(),'Existing user rules\n')
        out=plan_install(self.repo,apply=True)
        self.assertEqual(len(out['roles_to_add']),6)
        out=plan_install(self.repo,apply=True)
        self.assertFalse(out['claude_import_needed']);self.assertEqual(out['roles_to_add'],[])
        self.assertTrue(p.read_text().startswith('Existing user rules'))
    def test_opus_requires_routing_assertion(self):
        with self.assertRaises(ValueError):plan_install(self.repo,include_opus=True,apply=True)
        self.assertFalse((self.repo/'CLAUDE.md').exists())
    def test_conflict_no_overwrite(self):
        folder=self.repo/'.claude/agents';folder.mkdir(parents=True)
        (folder/'sw7-contract.md').write_text('User-owned conflicting role')
        with self.assertRaises(ValueError):plan_install(self.repo,apply=True)
        self.assertFalse((self.repo/'CLAUDE.md').exists())
        self.assertEqual((folder/'sw7-contract.md').read_text(),'User-owned conflicting role')
    def test_symlink_instruction_refused(self):
        target=self.base/'global.md';target.write_text('global preserved')
        (self.repo/'CLAUDE.md').symlink_to(target)
        with self.assertRaises(ValueError):plan_install(self.repo,apply=True)
        self.assertEqual(target.read_text(),'global preserved')
    def test_evidence_never_overwritten(self):
        p=self.base/'record.json';write_new_json(p,{'first':True})
        with self.assertRaises(FileExistsError):write_new_json(p,{'second':True})
        self.assertEqual(json.loads(p.read_text()),{'first':True})


if __name__=='__main__':unittest.main()
