#!/usr/bin/env python3
"""Validate this strategy packet and small abstract algebra models only.

Not an upstream oracle, actual SOLWEIG kernel test, installed pipeline test or
performance benchmark. NumPy and PyYAML are needed only for these analysis checks.
"""
from __future__ import annotations
import importlib.util
import itertools
import json
import math
from pathlib import Path
import platform
import sys
import time
import unittest
import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from throughput_model import evaluate, greedy_makespan, run

DETAILS = {}


def f32(x):
    return np.float32(x)


def bits(x):
    return np.asarray(x, dtype=np.float32).view(np.uint32)


def ordered_sum(values):
    s = f32(0)
    for v in values:
        s = f32(s + v)
    return s


class PacketChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((ROOT / 'STRATEGIES.json').read_text())['entries']
        cls.tasks = yaml.safe_load((ROOT / 'TASKS_OPTIMIZATION.yaml').read_text())['tasks']
        cls.config = json.loads((ROOT / 'throughput_inputs.json').read_text())

    def test_goal_length(self):
        goal = (ROOT / 'GOAL.txt').read_text()
        self.assertLessEqual(len(goal) + len('/goal '), 4000)
        DETAILS['goal_codepoints'] = len(goal)
        DETAILS['goal_with_command_codepoints'] = len(goal) + 6

    def test_catalog_counts_and_ids(self):
        ids = [r['id'] for r in self.catalog]
        self.assertEqual(len(ids), 56)
        self.assertEqual(len(set(ids)), len(ids))
        self.assertEqual(sum(r['priority']=='quarantined' for r in self.catalog),8)
        self.assertTrue(all(r['status']=='proposed_not_production_verified' for r in self.catalog))
        DETAILS['catalog_candidates'] = 48
        DETAILS['catalog_quarantined'] = 8

    def test_source_ids_resolve(self):
        sources = (ROOT / 'SOURCES.md').read_text()
        for row in self.catalog:
            for source in row['sources']:
                self.assertIn('| ' + source + ' |', sources)

    def test_task_dependencies(self):
        nodes = {t['id']:t for t in self.tasks}
        self.assertEqual(len(nodes),len(self.tasks))
        visited=set();active=set()
        def visit(node):
            self.assertNotIn(node,active)
            if node in visited:return
            active.add(node)
            for parent in nodes[node]['depends_on']:
                self.assertIn(parent,nodes)
                visit(parent)
            active.remove(node);visited.add(node)
        for node in nodes:visit(node)
        DETAILS['dependency_acyclic_tasks'] = len(nodes)

    def test_task_strategy_ids(self):
        ids={r['id'] for r in self.catalog}
        for task in self.tasks:
            self.assertTrue(set(task['strategy_ids'])<=ids)
        self.assertTrue(all(t['status']=='pending' for t in self.tasks))

    def test_no_fake_goal_pass(self):
        result=run(self.config)
        self.assertFalse(result['solweig_executed'])
        for r in result['all_settings']:
            self.assertFalse(r['actual_goal_passed'])
            self.assertFalse(r['calibrated_forecast'])

    def test_known_schedule_example(self):
        scenario=next(s for s in self.config['scenarios'] if s['id']=='target_portfolio')
        result=evaluate(self.config,scenario,4,2)
        self.assertAlmostEqual(result['cpu_schedule_seconds'],1578.0)
        self.assertAlmostEqual(result['assumed_resident_gib'],8.8)
        self.assertTrue(result['unknown_memory_or_io_costs'])
        stress=evaluate(self.config,scenario,4,2,1.2)
        self.assertAlmostEqual(stress['cpu_schedule_seconds'],1875.6)
        self.assertFalse(stress['model_target_met'])

    def test_resource_admission(self):
        result=evaluate(self.config,self.config['scenarios'][0],8,2)
        self.assertFalse(result['analytically_admissible'])
        self.assertIsNone(result['screening_seconds'])

    def test_invalid_values_rejected(self):
        bad=dict(self.config['scenarios'][0],work_reductions={'geometry':0})
        with self.assertRaises(ValueError):evaluate(self.config,bad,1,1)
        with self.assertRaises(ValueError):evaluate(self.config,self.config['scenarios'][0],0,1)
        with self.assertRaises(ValueError):greedy_makespan([1,float('nan')],2)

    def test_list_schedule(self):
        self.assertEqual(greedy_makespan([8,7,6,5],2),13)
        self.assertEqual(greedy_makespan([1,2,3],1),6)

    def test_absorbing_projection_abstract(self):
        count=0
        # These are post-special-first-step states, not actual geometric rays.
        for B0,V0 in itertools.product((0,1),repeat=2):
            for length in range(5):
                for seq in itertools.product(range(8),repeat=length):
                    B,V=B0,V0;vb=f32(0)
                    for symbol in seq:
                        block=(symbol>>2)&1;canopy=(symbol>>1)&1;trunk=symbol&1
                        B=int(B or block)
                        V=max(V,canopy-trunk)
                        if V*B>0:V=0
                        vb=f32(vb+f32(V))
                    expected=(1-B,1-V,1-(int(vb>0)-V))
                    b,v,e=B0,V0,0
                    for symbol in seq:
                        block=(symbol>>2)&1;canopy=(symbol>>1)&1;trunk=symbol&1
                        b=int(b or block)
                        v=int((v or (canopy and not trunk)) and not b)
                        e=int(e or v)
                        if b:break  # after at least one ordinary step
                    actual=(1-b,1-v,1-(e-v))
                    self.assertEqual(actual,expected)
                    count+=1
        DETAILS['abstract_sky_state_sequences'] = count
        DETAILS['abstract_sky_scope'] = 'post-first-step symbolic finite no-positive-bush recurrence only'

    def test_repeated_add_not_multiplication(self):
        c=f32(.2)
        a=ordered_sum([c]*7)
        b=f32(f32(7)*c)
        self.assertNotEqual(int(bits(a)),int(bits(b)))
        DETAILS['repeated_add_counterexample']={'add':float(a),'multiply':float(b)}

    def test_reassociation_counterexample(self):
        a,b,c=f32(1e8),f32(-1e8),f32(1)
        left=f32(f32(a+b)+c);right=f32(a+f32(b+c))
        self.assertNotEqual(float(left),float(right))

    def test_exact_finite_state_partial_eval(self):
        rng=np.random.default_rng(311)
        n,p=97,153
        coeff=rng.normal(size=p).astype(np.float32)
        angles=rng.random(p,dtype=np.float32)
        states=rng.integers(0,3,size=(n,p))
        table=np.empty((p,3),dtype=np.float32)
        for j in range(p):
            for k in range(3):
                table[j,k]=f32(f32(f32(k)*coeff[j])*angles[j])
        direct=np.empty(n,dtype=np.float32);cached=np.empty_like(direct)
        for i in range(n):
            d=c=f32(0)
            for j in range(p):
                term=f32(f32(f32(states[i,j])*coeff[j])*angles[j])
                d=f32(d+term);c=f32(c+table[j,states[i,j]])
            direct[i]=d;cached[i]=c
        self.assertTrue(np.array_equal(bits(direct),bits(cached)))
        DETAILS['synthetic_exact_table_contributions'] = n*p

    def test_pixel_order_interchange(self):
        rng=np.random.default_rng(919)
        values=rng.normal(size=(37,153)).astype(np.float32)
        reference=np.array([ordered_sum(row) for row in values],dtype=np.float32)
        for block in (1,3,16,37,64):
            out=np.zeros(37,dtype=np.float32)
            for start in range(0,37,block):
                stop=min(37,start+block)
                for patch in range(153):
                    out[start:stop]=np.add(out[start:stop],values[start:stop,patch])
            self.assertTrue(np.array_equal(bits(reference),bits(out)))
        DETAILS['synthetic_ordered_partitions'] = 5

    def test_bush_control_prepass_abstract(self):
        rng=np.random.default_rng(414)
        cases=0
        for n in (1,7,23):
            for steps in (1,2,9):
                for trial in range(8):
                    a=rng.normal(size=n).astype(np.float32)
                    bush=rng.normal(size=n).astype(np.float32)*f32(2)
                    if trial==6:bush[0]=np.nan
                    if trial==7:bush[0]=np.inf
                    tv=rng.normal(size=(steps,n)).astype(np.float32)
                    shifted=rng.normal(size=(steps,n)).astype(np.float32)
                    bp=(bush>1).astype(np.float32)
                    def original_flag(row):
                        with np.errstate(invalid='ignore'):
                            return bool(np.max((row>a).astype(np.float32)*bush)>0)
                    flags=[original_flag(row) for row in tv]
                    if np.isfinite(bush).all():
                        sparse=[bool(np.any((row>a)&(bush>0))) for row in tv]
                        self.assertEqual(flags,sparse)
                    original=np.zeros(n,dtype=np.float32)
                    for k in range(steps):
                        if original_flag(tv[k]):original=np.maximum(original,shifted[k])*bp
                    projected=np.zeros(n,dtype=np.float32)
                    for x in range(n):
                        for k in range(steps):
                            if flags[k]:projected[x]=f32(np.maximum(projected[x],shifted[k,x])*bp[x])
                    self.assertTrue(np.array_equal(bits(original),bits(projected)))
                    cases+=1
        DETAILS['abstract_input_only_control_prepass_cases']=cases
        DETAILS['bush_test_scope']='arbitrary prepared temporary arrays and g update, not full shadow/SVF/first-step pipeline'


def main():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(PacketChecks)
    start=time.perf_counter()
    import io
    capture=io.StringIO()
    result=unittest.TextTestRunner(stream=capture,verbosity=2).run(suite)
    report={
        'schema':1,'classification':'packet_integrity_and_abstract_algebra_checks_only',
        'successful':result.wasSuccessful(),'tests_run':result.testsRun,
        'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),
        'analysis_elapsed_seconds':time.perf_counter()-start,
        'environment':{'python':sys.version,'numpy':np.__version__,'pyyaml':yaml.__version__,
                       'platform':platform.platform()},
        'details':DETAILS,
        'production_solweig_executed':False,'original_oracle_executed':False,
        'target_hardware_benchmark_executed':False,'universal_equivalence_proved':False,
        'log':capture.getvalue()
    }
    (ROOT/'evidence/analysis_selftests.json').write_text(json.dumps(report,indent=2)+'\n')
    print(capture.getvalue(),end='')
    raise SystemExit(0 if result.wasSuccessful() else 1)

if __name__=='__main__':main()
