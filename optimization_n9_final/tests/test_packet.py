"""Packet arithmetic/structure tests, not SOLWEIG numerical qualification."""
import importlib.util
from pathlib import Path
import unittest
import json
import math
import yaml

ROOT=Path(__file__).resolve().parents[1]
def module(name):
 spec=importlib.util.spec_from_file_location(name,ROOT/'tools'/f'{name}.py')
 obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj
cost=module('cost_model');check=module('check_final_record')

class PacketTests(unittest.TestCase):
    def record(self):
        # Fabricated structural test data, never real qualification.
        return dict(schema='solweig.final-optimization.v1',status='closed_cpu_only',
          source_branch='perf/native-optimization',target_branch='main',
          source_sha='1'*40,target_sha='2'*40,source_tree_sha='3'*40,
          native_goal_achieved=False,native_research_closed_for_release=True,
          default_backend='numba',ready_for_merge=True,required_release_safety_passed=True,
          actual_target_status='unverified',upstream_comparison_status='unverified',
          remote_actions_performed=[],evidence_paths=['fabricated-unit-test-fixture-only'],
          exclusions=[],outstanding_claims=[],limitations=[])
    def test_cost_identity(self):self.assertEqual(cost.total_speedup(.6,1),1)
    def test_cost_bounds(self):
        for v in [(-.1,2,0),(.5,0,0),(.5,2,-.1),(float('nan'),2,0)]:
            with self.assertRaises(ValueError):cost.total_speedup(*v)
    def test_scenario_not_measurement(self):
        s=cost.scenario();self.assertIn('hypothetical',s['evidence_class'])
        self.assertAlmostEqual(s['cells']['binary']['hypothetical_local_speedup'],1.2366656451)
    def test_memory_payload(self):
        self.assertEqual(cost.payload_bytes(1024**2),2142*1024**2)
        self.assertEqual(cost.payload_bytes(1024,slots=4),8773632)
    def test_negative_sizes(self):
        for x in (0,-1,True,1.5):
            with self.assertRaises(ValueError):cost.payload_bytes(x)
    def test_cpu_closure_structure(self):self.assertEqual(check.errors(self.record()),[])
    def test_native_false_success(self):
        r=self.record();r['native_goal_achieved']=True
        self.assertTrue(check.errors(r))
    def test_safety_required(self):
        r=self.record();r['required_release_safety_passed']=False
        self.assertTrue(check.errors(r))
    def test_open_forbidden(self):
        r=self.record();r['native_goal_open']=True
        self.assertTrue(check.errors(r))
    def test_branch(self):
        r=self.record();r['source_branch']='main'
        self.assertTrue(check.errors(r))
    def test_blocked(self):
        r=self.record();r['status']='blocked_no_safe_merge'
        self.assertTrue(check.errors(r))
        r['ready_for_merge']=False;self.assertEqual(check.errors(r),[])
    def test_native_shape(self):
        r=self.record();r.update(status='closed_native_qualified',native_goal_achieved=True,
           default_backend='qualified_native_with_cpu_fallback')
        self.assertEqual(check.errors(r),[])
    def test_no_remote(self):
        r=self.record();r['remote_actions_performed']=['push']
        self.assertTrue(check.errors(r))
    def test_short_prompt(self):self.assertLessEqual(len((ROOT/'START_HERE.txt').read_text()),4000)
    def test_dag(self):
        t=yaml.safe_load((ROOT/'TASKS.yaml').read_text());seen=set()
        for row in t['tasks']:
            self.assertNotIn(row['id'],seen);self.assertLessEqual(set(row['depends_on']),seen);seen.add(row['id'])
        self.assertEqual(len(seen),11)
    def test_probe_results_labeled(self):
        for file in ('decoder_probe_result.json','decoder_probe_result_v2.json'):
            v=json.loads((ROOT/'evidence'/file).read_text())
            self.assertIn('NOT SOLWEIG',v['scope'])
            self.assertEqual(v['exactness']['shape_start_width_cases'],64)
    def test_no_shipped_claim_record(self):self.assertFalse((ROOT/'FINAL_SELECTION.json').exists())

if __name__=='__main__':unittest.main()
