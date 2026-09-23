"""Synthetic packet-helper tests only. No SOLWEIG, native library or GPU is run."""
from __future__ import annotations
import copy
import json
import math
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from _common import BRANCH, PACKET, commit, git, no_symlink_ancestors
from cost_model import calls, speedup, required_speedup, phase_total
from promotion_gate import assess, ratios
from audit_wheel import audit
from preflight import inspect_repo
from prepare_worker import prepare
from install_assets import install
from snapshot_surface import summarize, snapshot


def synthetic_policy():
    """A fabricated well-formed record to exercise policy arithmetic, not evidence."""
    cells=[]
    for i in range(4):
        cells.append({'id':f'synthetic_primary_{i}','kind':'primary','clean_complete':True,
          'matched_budget':True,'thread_observed':True,'default_env_unset':True,
          'main_defaults_covered':i==0,'raw_evidence_paths':['SYNTHETIC_NOT_AN_EXECUTION'],
          'eligible_work':100,'native_executed_work':90,
          'pairs_current':[{'baseline_s':100,'candidate_s':80} for _ in range(3)],
          'pairs_control':[{'baseline_s':90,'candidate_s':80} for _ in range(3)]})
    cells.append({'id':'synthetic_guard','kind':'guard','clean_complete':True,
          'matched_budget':True,'thread_observed':True,'default_env_unset':True,
          'raw_evidence_paths':['SYNTHETIC_NOT_AN_EXECUTION'],
          'pairs_current':[{'baseline_s':100,'candidate_s':100} for _ in range(3)]})
    return {'schema':'sw8-default-promotion-record-v1','status':'observed',
       'evidence_kind':'SYNTHETIC_TOOL_TEST','branch':BRANCH,
       'source_sha':'1'*40,'protocol_sha256':'2'*64,'artifact_sha256':'3'*64,
       'protocol_frozen_before_candidates':True,
       'qualification':{k:'passed' for k in ('numeric','dx','installed_wheel','source_fallback',
                                          'independent_review','resources','cold_first_use')},
       'cells':cells,'actual_target_status':'unverified'}


class CostTests(unittest.TestCase):
    def test_call_count(self):self.assertEqual(calls(4,24,1024**2,1024),98304)
    def test_partial_dispatch(self):self.assertEqual(calls(2,3,9,4),18)
    def test_call_invalid(self):
        for value in (0,-1,True,1.5):
            with self.subTest(value=value),self.assertRaises(ValueError):calls(value,24,10,2)
    def test_amdahl(self):self.assertAlmostEqual(speedup(.6,3,.03),1/.63)
    def test_amdahl_invalid(self):
        for args in ((1.1,2,0),(.5,0,0),(.5,2,-1),(.5,2,float('nan'))):
            with self.subTest(args=args),self.assertRaises(ValueError):speedup(*args)
    def test_required(self):self.assertAlmostEqual(required_speedup(.6,2,.03),.6/.07)
    def test_unreachable(self):self.assertIsNone(required_speedup(.6,4,.03))
    def test_no_fraction(self):self.assertEqual(required_speedup(0,1),1);self.assertIsNone(required_speedup(0,2))
    def test_phase(self):
        p=[{'jobs':4,'workers':2,'threads_per_worker':2,'bytes_per_worker':100,
            'job_s_at_concurrency':8}]
        self.assertEqual(phase_total(p,4,1000,3),19)
    def test_cpu_budget(self):
        p=[{'jobs':4,'workers':2,'threads_per_worker':4,'bytes_per_worker':10,'job_s_at_concurrency':1}]
        with self.assertRaises(ValueError):phase_total(p,4,1000)
    def test_memory_budget(self):
        p=[{'jobs':4,'workers':2,'threads_per_worker':1,'bytes_per_worker':100,'shared_bytes':1,'job_s_at_concurrency':1}]
        with self.assertRaises(ValueError):phase_total(p,4,200)


class PolicyTests(unittest.TestCase):
    def test_synthetic_wellformed_is_not_production_proof(self):
        r=assess(synthetic_policy());self.assertTrue(r['policy_data_passed']);self.assertFalse(r['production_default_qualified'])
        self.assertFalse(r['evidence_authenticity_checked'])
    def test_template_rejected(self):
        self.assertFalse(assess(json.loads((ROOT/'templates/promotion_record.json').read_text()))['policy_data_passed'])
    def test_missing_wheel(self):
        r=synthetic_policy();r['qualification']['installed_wheel']='pending';self.assertFalse(assess(r)['policy_data_passed'])
    def test_no_default(self):
        r=synthetic_policy()
        for c in r['cells']:c['main_defaults_covered']=False
        self.assertFalse(assess(r)['policy_data_passed'])
    def test_force_native_not_default(self):
        r=synthetic_policy();r['cells'][0]['default_env_unset']=False;self.assertFalse(assess(r)['policy_data_passed'])
    def test_fallback_only(self):
        r=synthetic_policy();r['cells'][0]['native_executed_work']=0;self.assertFalse(assess(r)['policy_data_passed'])
    def test_fabricated_overcoverage(self):
        r=synthetic_policy();r['cells'][0]['native_executed_work']=101;self.assertFalse(assess(r)['policy_data_passed'])
    def test_loses_to_numba_control(self):
        r=synthetic_policy();r['cells'][0]['pairs_control']=[{'baseline_s':75,'candidate_s':80}]*3
        self.assertFalse(assess(r)['policy_data_passed'])
    def test_guard_regression(self):
        r=synthetic_policy();r['cells'][-1]['pairs_current']=[{'baseline_s':100,'candidate_s':104}]*3
        self.assertFalse(assess(r)['policy_data_passed'])
    def test_protocol_not_frozen(self):
        r=synthetic_policy();r['protocol_frozen_before_candidates']=False;self.assertFalse(assess(r)['policy_data_passed'])
    def test_bad_pair(self):
        for val in (0,-1,float('nan'),float('inf'),True):
            with self.subTest(value=val),self.assertRaises(ValueError):ratios([{'baseline_s':10,'candidate_s':val}]*3)
    def test_two_scene_target_rejected(self):
        r=synthetic_policy();r['actual_target_status']='demonstrated_once';r['actual_target']={
          'workload_kind':'synthetic','spatial_tiles':2,'timesteps_per_tile':24,'elapsed_s':598.9,
          'completed_tiles':2,'numeric_coverage':'qualified','memory_scope':'parent','resource_gate':'passed'}
        self.assertFalse(assess(r)['policy_data_passed'])
    def test_invalid_runtime_hash(self):
        r=synthetic_policy();r['artifact_sha256']='not-hash';self.assertFalse(assess(r)['policy_data_passed'])
    def test_small_evidence_remains_target_unverified(self):
        r=assess(synthetic_policy());self.assertTrue(r['policy_data_passed'])
        self.assertNotIn('actual_target_qualified',r)


class WheelTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.d=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def wheel(self,tag='py3-none-macosx_11_0_arm64',native=True,pure='false',extra=None,magic=b'\xcf\xfa\xed\xfe'):
        p=self.d/('fake-0.0-'+tag+'.whl')
        with zipfile.ZipFile(p,'w') as z:
            z.writestr('fake-0.0.dist-info/WHEEL',f'Wheel-Version: 1.0\nRoot-Is-Purelib: {pure}\nTag: {tag}\n')
            z.writestr('fake-0.0.dist-info/METADATA','Name: fake\nVersion: 0.0\n')
            if native:z.writestr('solweig_light/backends/native/libfake.dylib',magic+b'SYNTHETIC_NOT_EXECUTABLE')
            if extra:z.writestr(extra,b'x')
        return p
    def test_platform_native_static_only(self):
        r=audit(self.wheel(),True);self.assertTrue(r['static_checks_passed']);self.assertFalse(r['native_executed'])
    def test_no_native_rejected_when_required(self):self.assertFalse(audit(self.wheel(native=False),True)['static_checks_passed'])
    def test_source_wheel_allowed(self):self.assertTrue(audit(self.wheel(tag='py3-none-any',native=False,pure='true'))['static_checks_passed'])
    def test_native_any_rejected(self):self.assertFalse(audit(self.wheel(tag='py3-none-any'),True)['static_checks_passed'])
    def test_native_purelib_rejected(self):self.assertFalse(audit(self.wheel(pure='true'),True)['static_checks_passed'])
    def test_escape_rejected(self):self.assertFalse(audit(self.wheel(extra='../escape'))['static_checks_passed'])
    def test_magic_rejected(self):self.assertFalse(audit(self.wheel(magic=b'notbinary'))['static_checks_passed'])
    def test_symlink_rejected(self):
        p=self.wheel();i=zipfile.ZipInfo('link');i.create_system=3;i.external_attr=(stat.S_IFLNK|0o777)<<16
        with zipfile.ZipFile(p,'a') as z:z.writestr(i,'outside')
        self.assertFalse(audit(p)['static_checks_passed'])


class GitToolTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.d=Path(self.tmp.name);self.repo=self.d/'repo';self.repo.mkdir()
        subprocess.run(['git','init','-q',str(self.repo)],check=True)
        git(self.repo,'config','user.email','packet-test@example.invalid');git(self.repo,'config','user.name','Packet Test')
        git(self.repo,'checkout','-q','-b',BRANCH)
        (self.repo/'src/solweig_light').mkdir(parents=True)
        (self.repo/'src/solweig_light/__init__.py').write_text('')
        (self.repo/'src/solweig_light/api.py').write_text('def thermal_comfort(a, x=True):\n    return None\n')
        (self.repo/'src/solweig_light/cli.py').write_text('')
        (self.repo/'src/solweig_light/runtime.py').write_text('class RuntimeOptions:\n    block_pixels: int = 128\n')
        (self.repo/'pyproject.toml').write_text('[project]\nname="dummy"\n')
        (self.repo/PACKET).mkdir();(self.repo/PACKET/'CLAUDE_PROJECT_RULES.md').write_bytes((ROOT/'CLAUDE_PROJECT_RULES.md').read_bytes())
        git(self.repo,'add','src','pyproject.toml');git(self.repo,'commit','-q','-m','synthetic fixture')
        self.sha=git(self.repo,'rev-parse','HEAD')
    def tearDown(self):self.tmp.cleanup()
    def test_preflight_readonly(self):
        before=git(self.repo,'status','--porcelain=v1');r=inspect_repo(self.repo)
        self.assertTrue(r['same_branch']);self.assertFalse(r['numerical_execution'])
        self.assertEqual(before,git(self.repo,'status','--porcelain=v1'))
    def test_full_sha_required(self):
        with self.assertRaises(ValueError):commit(self.repo,'HEAD')
    def test_worker_dryrun(self):
        dest=self.d/'worker';r=prepare(self.repo,self.sha,dest)
        self.assertFalse(r['applied']);self.assertFalse(dest.exists())
    def test_worker_detached_apply(self):
        dest=self.d/'worker';prepare(self.repo,self.sha,dest,True)
        self.assertEqual(git(dest,'rev-parse','HEAD'),self.sha)
        with self.assertRaises(ValueError):git(dest,'symbolic-ref','--quiet','--short','HEAD')
        self.assertEqual(git(self.repo,'branch','--show-current'),BRANCH)
    def test_no_existing_dest_removal(self):
        dest=self.d/'existing';dest.mkdir();(dest/'keep').write_text('keep')
        with self.assertRaises(ValueError):prepare(self.repo,self.sha,dest,True)
        self.assertTrue((dest/'keep').exists())
    def test_wrong_branch_refused(self):
        git(self.repo,'checkout','-q','-b','other')
        with self.assertRaises(ValueError):install(self.repo,True,ROOT)
        with self.assertRaises(ValueError):prepare(self.repo,self.sha,self.d/'worker',True)
    def test_installer_dryrun(self):
        r=install(self.repo,False,ROOT);self.assertTrue(r['writes']);self.assertFalse((self.repo/'CLAUDE.md').exists())
    def test_installer_preserves_and_idempotent(self):
        original='# Existing user rules\nDo not erase.\n';(self.repo/'CLAUDE.md').write_text(original)
        r=install(self.repo,True,ROOT)
        self.assertTrue((self.repo/'CLAUDE.md').read_text().startswith(original))
        self.assertEqual((self.repo/r['backup']).read_text(),original)
        self.assertEqual(install(self.repo,True,ROOT)['writes'],[])
    def test_installer_conflict_no_partial_write(self):
        target=self.repo/'.claude/agents/sw8-layout.md';target.parent.mkdir(parents=True);target.write_text('user-owned')
        with self.assertRaises(ValueError):install(self.repo,True,ROOT)
        self.assertEqual(target.read_text(),'user-owned');self.assertFalse((self.repo/'CLAUDE.md').exists())
    def test_symlink_refused(self):
        dest=self.d/'outside';dest.write_text('protected');(self.repo/'CLAUDE.md').symlink_to(dest)
        with self.assertRaises(ValueError):install(self.repo,True,ROOT)
        self.assertEqual(dest.read_text(),'protected')
    def test_source_surface_is_not_runtime(self):
        r=snapshot(self.repo,self.sha);self.assertFalse(r['operational_parity_tested'])
        self.assertIn('thermal_comfort',r['files']['src/solweig_light/api.py']['public_source_signatures'])


class PacketTests(unittest.TestCase):
    def test_start_length(self):self.assertLessEqual(len((ROOT/'START_HERE.txt').read_text()),4000)
    def test_dag(self):
        data=json.loads((ROOT/'TASKS_CLAUDE.yaml').read_text());tasks={t['id']:t for t in data['tasks']}
        self.assertEqual(len(tasks),len(data['tasks']));self.assertEqual(data['branch'],BRANCH)
        done=set()
        while len(done)<len(tasks):
            ready={k for k,t in tasks.items() if k not in done and set(t['depends_on'])<=done}
            self.assertTrue(ready,'cycle or missing dependency');done.update(ready)
    def test_dossier_links(self):
        for task in json.loads((ROOT/'TASKS_CLAUDE.yaml').read_text())['tasks']:
            with self.subTest(task=task['id']):self.assertTrue((ROOT/task['dossier']).is_file())
    def test_pending_tasks(self):
        for t in json.loads((ROOT/'TASKS_CLAUDE.yaml').read_text())['tasks']:self.assertEqual(t['status'],'pending')
    def test_source_status_honest(self):
        s=json.loads((ROOT/'SOURCE_STATUS.json').read_text())
        self.assertFalse(s['native_benchmark_executed_by_packet_author']);self.assertFalse(s['solweig_executed_by_packet_author'])
    def test_agents_minimal(self):
        for p in (ROOT/'agents').glob('*.md'):
            text=p.read_text();self.assertTrue(text.startswith('---\n'));self.assertIn('model: inherit',text)
            self.assertNotIn('bypassPermissions',text)
    def test_key_product_contracts(self):
        dx=(ROOT/'DX_CONTRACT.md').read_text();self.assertIn('Source',dx);self.assertIn('fallback',dx)
        self.assertIn('platform wheel',(ROOT/'PACKAGING_AND_DISTRIBUTION.md').read_text())
        self.assertIn('f64',(ROOT/'KERNEL_CONTRACT.md').read_text())
    def test_ast_defaults(self):
        a=summarize('def thermal_comfort(a, b=True):\n return None\n')
        b=summarize('def thermal_comfort(a, b=False):\n return None\n')
        self.assertNotEqual(a,b)

if __name__=='__main__':unittest.main()
