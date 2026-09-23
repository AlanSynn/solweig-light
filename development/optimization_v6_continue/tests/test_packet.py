"""Packet/tool checks only. No repository numerical kernel is imported."""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import branch_guard
import phase_model
import scope_contract
import thread_probe


def sample_record():
    return {'spatial_tiles':24,'dataset_kind':'actual_target','elapsed_seconds':1500,
        'source_sha':'test-source','wheel_sha256':'test-wheel','math_profile':'test-profile',
        'dataset_manifest_sha256':'test-dataset','protocol_sha256':'test-protocol',
        'effective_resources_verified':True,'required_publication_complete':True,
        'application_io_included':True,'within_resource_budget':True,
        'unchanged_physical_context_verified':True,'checkpoint_interval':1,
        'tiles':[{'spatial_id':f'position-{i}','shape':[1024,1024],'timesteps':24,
                  'patches':153,'status':'complete','outputs':sorted(scope_contract.OUTPUTS),
                  'numerical_reference_status':'verified'} for i in range(24)]}


class ContractTests(unittest.TestCase):
    def test_positive_record_scope_only(self):
        r=scope_contract.check(sample_record())
        self.assertTrue(r['record_eligible_for_target_claim_review'])
        self.assertFalse(r['numerical_data_verified_by_this_tool'])
    def test_two_spatial_not_twenty_four(self):
        r=json.loads((ROOT/'templates/historical_scope_not_target.json').read_text())
        self.assertFalse(scope_contract.check(r)['record_eligible_for_target_claim_review'])
    def test_synthetic_is_not_real_target(self):
        r=sample_record();r['dataset_kind']='synthetic_load'
        self.assertFalse(scope_contract.check(r)['record_eligible_for_target_claim_review'])
    def test_duplicate_context_rejected(self):
        r=sample_record();r['tiles'][1]['spatial_id']=r['tiles'][0]['spatial_id']
        self.assertFalse(scope_contract.check(r)['record_eligible_for_target_claim_review'])
    def test_missing_reference_unverified(self):
        r=sample_record();r['tiles'][4]['numerical_reference_status']='unavailable'
        self.assertFalse(scope_contract.check(r)['record_eligible_for_target_claim_review'])
    def test_nan_elapsed_rejected(self):
        r=sample_record();r['elapsed_seconds']=float('nan')
        self.assertFalse(scope_contract.check(r)['record_eligible_for_target_claim_review'])
    def test_incomplete_tile_rejected(self):
        r=sample_record();r['tiles'][-1]['status']='censored'
        self.assertFalse(scope_contract.check(r)['record_eligible_for_target_claim_review'])
    def test_omitted_output_rejected(self):
        r=sample_record();r['tiles'][0]['outputs'].remove('WBGT')
        self.assertFalse(scope_contract.check(r)['record_eligible_for_target_claim_review'])
    def test_changed_chronology_rejected(self):
        r=sample_record();r['tiles'][0]['timesteps']=12
        self.assertFalse(scope_contract.check(r)['record_eligible_for_target_claim_review'])


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.x=json.loads((ROOT/'templates/phase_model_hypothetical.json').read_text())
    def test_phase_sum(self):
        r=phase_model.estimate(self.x)
        expected=6*60*1.05 + 24*19.45/1.5 + 6*160*1.15/1.5 +90
        self.assertAlmostEqual(r['seconds'],expected)
        self.assertFalse(r['observed_target_demonstrated'])
    def test_serial_export_not_divided(self):
        r=phase_model.estimate(self.x)
        e=next(p for p in r['phases'] if p['name']=='still_serial_verified_export')
        self.assertEqual(e['waves'],24)
    def test_cpu_overreservation(self):
        self.x['phases'][0]['threads']=3
        with self.assertRaises(ValueError):phase_model.estimate(self.x)
    def test_memory_overreservation(self):
        self.x['phases'][0]['worker_gib']=4
        with self.assertRaises(ValueError):phase_model.estimate(self.x)
    def test_negative_cost_rejected(self):
        self.x['phases'][0]['seconds_per_tile']=-1
        with self.assertRaises(ValueError):phase_model.estimate(self.x)
    def test_boolean_count_rejected(self):
        self.x['spatial_tiles']=True
        with self.assertRaises(ValueError):phase_model.estimate(self.x)
    def test_actual_two_scene_arithmetic(self):
        self.assertAlmostEqual(24*(598.9/2)/60,119.78)
        self.assertAlmostEqual(60*2/598.9,0.20036734012356,places=10)


class PacketTests(unittest.TestCase):
    def test_start_length_and_same_branch(self):
        s=(ROOT/'START_HERE.txt').read_text()
        self.assertLessEqual(len(s),4000)
        self.assertIn(branch_guard.BRANCH,s)
        self.assertIn('Do not create/switch a new named branch',s)
    def test_historical_catalog_preserved(self):
        entries=json.loads((ROOT/'reference/STRATEGIES.json').read_text())['entries']
        self.assertEqual(len(entries),56)
    def test_task_dag(self):
        d=json.loads((ROOT/'TASKS_CLAUDE.json').read_text());tasks=d['tasks'];ids={t['id'] for t in tasks}
        self.assertEqual(len(ids),len(tasks));seen=set();todo=tasks[:]
        while todo:
            ready=[t for t in todo if set(t['depends_on'])<=seen]
            self.assertTrue(ready,'cyclic or missing dependency')
            for t in ready: self.assertIn(t['id'],ids);seen.add(t['id']);todo.remove(t)
    def test_dossiers_exist(self):
        for t in json.loads((ROOT/'TASKS_CLAUDE.json').read_text())['tasks']:
            self.assertTrue((ROOT/t['dossier']).is_file())
    def test_no_model_provider_calls_in_helpers(self):
        for p in (ROOT/'tools').glob('*.py'):
            s=p.read_text()
            self.assertNotIn('requests.',s);self.assertNotIn('urllib.',s)
    def test_agents_no_implicit_worktree_or_permission_bypass(self):
        for p in (ROOT/'agents').glob('sw6-*.md'):
            s=p.read_text();front=s.split('---')[1]
            self.assertNotIn('isolation:',front)
            self.assertNotIn('bypassPermissions',front)
            self.assertRegex(front,r'name: sw6-')
    def test_thread_environment_no_parent_mutation(self):
        before=dict(os.environ);env=thread_probe.child_environment(2,'/tmp/probe-not-created')
        self.assertEqual(dict(os.environ),before)
        self.assertEqual(env['NUMBA_NUM_THREADS'],'2')
    def test_probe_preview_does_not_run_numba(self):
        p=subprocess.run([sys.executable,str(ROOT/'tools/thread_probe.py'),'--threads','1','2'],capture_output=True,text=True)
        self.assertEqual(p.returncode,0);self.assertTrue(json.loads(p.stdout)['preview'])
    def test_sources_key_evidence(self):
        ids={s['id'] for s in json.loads((ROOT/'SOURCES.json').read_text())['sources']}
        self.assertTrue({'S05','S06','S07','S08','O01','O02','O03','O04'}<=ids)


class BranchTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.repo=self.root/'repo';self.repo.mkdir()
        self.cmd('init','-q','-b',branch_guard.BRANCH)
        (self.repo/'example.txt').write_text('base\n')
        self.cmd('add','example.txt')
        self.cmd('-c','user.name=Packet Test','-c','user.email=packet-test@example.invalid','commit','-q','-m','temporary packet test')
        self.sha=self.cmd('rev-parse','HEAD')
    def tearDown(self):self.tmp.cleanup()
    def cmd(self,*args):
        p=subprocess.run(['git','-C',str(self.repo),*args],capture_output=True,text=True)
        if p.returncode: raise RuntimeError(p.stderr)
        return p.stdout.strip()
    def test_read_only_dirty_integration(self):
        (self.repo/'example.txt').write_text('user modification\n')
        before=self.cmd('status','--porcelain');r=branch_guard.audit(self.repo)
        self.assertEqual(self.cmd('rev-parse','HEAD'),self.sha)
        self.assertEqual(self.cmd('status','--porcelain'),before)
        self.assertTrue(r['dirty_status'])
    def test_wrong_branch_refused_unchanged(self):
        self.cmd('switch','-q','-c','test-other-local-branch')
        with self.assertRaises(ValueError): branch_guard.audit(self.repo)
        self.assertEqual(self.cmd('branch','--show-current'),'test-other-local-branch')
    def test_detached_worker_base(self):
        wt=self.root/'worker';self.cmd('worktree','add','--detach',str(wt),self.sha)
        r=branch_guard.audit(wt,'worker',self.sha)
        self.assertIsNone(r['branch']);self.assertEqual(self.cmd('branch','--show-current'),branch_guard.BRANCH)
        with self.assertRaises(ValueError):branch_guard.audit(wt,'worker',None)

if __name__=='__main__': unittest.main()
