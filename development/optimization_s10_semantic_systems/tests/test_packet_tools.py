"""Tests of packet tooling, NOT of SOLWEIG. Synthetic records are deliberately fabricated."""
import copy, json, math, sys, tempfile, unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import cost_model as cm
import audit_repo as ar
import profile_descriptor as pd
import evidence_check as ec
import check_packet as cp
import run_semantic_probe as sp

class CostTests(unittest.TestCase):
    def test_amdahl_disjoint(self):
        r=cm.amdahl([{'id':'lw','fraction':.45,'speedup':2}])
        self.assertAlmostEqual(r['total_speedup'],1/.775)
    def test_no_gain_with_no_parts(self):self.assertEqual(cm.amdahl([])['total_speedup'],1)
    def test_fraction_overflow_rejected(self):
        with self.assertRaises(ValueError):cm.amdahl([{'id':'a','fraction':1.1,'speedup':2}])
    def test_duplicate_cost_rejected(self):
        with self.assertRaises(ValueError):cm.amdahl([{'id':'a','fraction':.1,'speedup':2}]*2)
    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError):cm.amdahl([],float('nan'))
    def test_required_speed(self):
        self.assertAlmostEqual(cm.required_stage_speedup(.6,2,.03)['minimum_stage_speedup'],.6/.07)
    def test_infeasible_requirement(self):
        self.assertFalse(cm.required_stage_speedup(.1,2)['finite_solution'])
    def config(self):
        return {'cpu_budget':4,'memory_budget_bytes':1000,'shared_bytes':100,'completed_jobs':4,
                'overhead_seconds':1,'evidence_class':'hypothetical',
                'phases':[{'id':'serial_export','workers':1,'threads_per_worker':1,'bytes_per_worker':100,'job_seconds':[2]*4},
                          {'id':'sim','workers':2,'threads_per_worker':2,'bytes_per_worker':200,'job_seconds':[4]*4}]}
    def test_serial_phase_not_divided(self):
        r=cm.phase_model(self.config());self.assertEqual(r['total_seconds'],17)
    def test_cpu_budget_rejected(self):
        c=self.config();c['phases'][1]['workers']=3
        with self.assertRaises(ValueError):cm.phase_model(c)
    def test_memory_budget_rejected(self):
        c=self.config();c['memory_budget_bytes']=450
        with self.assertRaises(ValueError):cm.phase_model(c)
    def test_time_class_not_measured(self):
        self.assertEqual(cm.phase_model(self.config())['evidence_class'],'model_calculation_not_benchmark')
    def test_hypothesis_is_labelled(self):
        self.assertIn('unverified',cm.sensitivity()['evidence_class'])

class ScopeTests(unittest.TestCase):
    def record(self):
        # Fake values for checking validation logic only, never benchmark evidence.
        return {'evidence_class':'measured','status':'completed','wall_seconds':1000,
                'source_sha':'a'*40,'environment_hash':'b'*64,'workload_manifest_sha256':'c'*64,
                'pair_id':'synthetic-test','timer_boundary':'complete_batch','raw_log':'TEST-ONLY',
                'spatial_tiles':24,'timesteps_per_tile':24,'actual_native_threads':2,'admitted_workers':2,
                'requested_cpu_budget':4,'outputs_equal':True,'correctness_reference':'TEST-ONLY',
                'synthetic':False,'target_manifest_verified':True,'physical_settings_equal':True,
                'required_final_checks_passed':True}
    def test_mechanical_consistency_is_not_attestation(self):
        r=ec.target_review(self.record());self.assertTrue(r['mechanically_consistent_for_independent_review'])
        self.assertFalse(r['certifies_actual_execution']);self.assertFalse(r['certifies_release'])
    def test_two_tiles_not_twenty_four(self):
        r=self.record();r['spatial_tiles']=2;self.assertFalse(ec.target_review(r)['mechanically_consistent_for_independent_review'])
    def test_synthetic_target_refused(self):
        r=self.record();r['synthetic']=True;self.assertFalse(ec.target_review(r)['mechanically_consistent_for_independent_review'])
    def test_leaf_target_refused(self):
        r=self.record();r['timer_boundary']='leaf';self.assertFalse(ec.target_review(r)['mechanically_consistent_for_independent_review'])
    def test_unavailable_refused(self):
        r=self.record();r['status']='unavailable';self.assertFalse(ec.target_review(r)['mechanically_consistent_for_independent_review'])
    def test_template_none_fields_safe(self):
        r=json.loads((ROOT/'templates/trial.json').read_text());self.assertFalse(ec.target_review(r)['mechanically_consistent_for_independent_review'])
    def test_target_over_time_refused(self):
        r=self.record();r['wall_seconds']=1801;self.assertFalse(ec.target_review(r)['mechanically_consistent_for_independent_review'])

class AuditTests(unittest.TestCase):
    def test_inventory_is_readonly_and_syntax_only(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);p=r/'src/solweig_light';p.mkdir(parents=True)
            f=p/'example.py';f.write_text('def f(a):\n    if a.ndim != 0: return None\n')
            before=f.read_bytes();got=ar.inventory(r)
            self.assertEqual(got['file_count'],1);self.assertEqual(before,f.read_bytes())
            self.assertEqual(got['files'][0]['candidate_markers']['scalar_guard'],[2])
            self.assertEqual(got['evidence_class'],'read_only_source_inventory_not_execution')
    def test_wrong_source_refused(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):ar.inventory(Path(d))
    def test_singleton_not_scalar(self):
        r=pd.describe(np.array([[2]],dtype=np.float32));self.assertTrue(r['is_singleton_array'])
        self.assertFalse(pd.describe(np.float32(2))['is_singleton_array'])
    def test_large_field_not_serialized(self):self.assertIsNone(pd.describe(np.ones((5,6)))['singleton_bits_hex'])
    def test_object_not_logged(self):
        with self.assertRaises(ValueError):pd.describe(np.array([object()],dtype=object))

class PacketTests(unittest.TestCase):
    def test_structure(self):self.assertTrue(cp.validate(ROOT,verify_hashes=False)['success'])
    def test_all_candidates_have_domain_cost_and_stop(self):
        c=json.loads((ROOT/'CANDIDATES.json').read_text())['candidates']
        self.assertEqual(len(c),73)
        for x in c:
            for k in ['proof_and_guard','cost_model','small_deciding_experiment','reject_or_defer_when']:
                self.assertTrue(x[k])
    def test_research_is_fenced(self):
        c=json.loads((ROOT/'CANDIDATES.json').read_text())['candidates']
        self.assertTrue(all(x['semantic_level']=='R' for x in c if x['id'].startswith('Q')))
    def test_new_semantic_probe(self):
        r=sp.run();self.assertEqual(r['finite_contribution_values_checked'],44064)
        self.assertFalse(r['full_model_executed']);self.assertFalse(r['performance_measured'])
        self.assertTrue(r['extra_counterexample']['unused_state_raises_overflow'])

if __name__=='__main__':unittest.main()
