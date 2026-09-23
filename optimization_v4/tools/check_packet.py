#!/usr/bin/env python3
"""Check this planning packet only. Never imports or runs SOLWEIG, Git or CI."""
from pathlib import Path
import hashlib
import io
import json
import platform
import re
import time
import unittest
from urllib.parse import unquote
import yaml

ROOT = Path(__file__).resolve().parents[1]

class PacketChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = json.loads((ROOT / 'validation_policy.json').read_text())
        cls.batch = json.loads((ROOT / 'templates/BATCH_PROTOCOL.json').read_text())
        cls.dag = yaml.safe_load((ROOT / 'TASKS_OPTIMIZATION.yaml').read_text())

    def test_goal_under_4000(self):
        self.assertLessEqual(len((ROOT / 'GOAL.txt').read_text()) + len('/goal '), 4000)

    def test_json_documents_parse(self):
        for path in ROOT.rglob('*.json'):
            with self.subTest(path=str(path.relative_to(ROOT))):
                json.loads(path.read_text())

    def test_yaml_documents_parse(self):
        for path in ROOT.rglob('*.yaml'):
            with self.subTest(path=str(path.relative_to(ROOT))):
                yaml.safe_load(path.read_text())

    def test_strategy_catalog_retained(self):
        entries = json.loads((ROOT / 'STRATEGIES.json').read_text())['entries']
        self.assertEqual(len(entries), 56)
        self.assertEqual(len({v['id'] for v in entries}), 56)
        self.assertEqual(sum(v['priority'] == 'quarantined' for v in entries), 8)

    def test_dag_acyclic_and_references(self):
        nodes = {v['id']: v for v in self.dag['tasks']}
        self.assertEqual(len(nodes), len(self.dag['tasks']))
        complete, visiting = set(), set()
        def visit(node):
            self.assertNotIn(node, visiting)
            if node in complete:
                return
            visiting.add(node)
            for dependency in nodes[node]['depends_on']:
                self.assertIn(dependency, nodes)
                visit(dependency)
            visiting.remove(node)
            complete.add(node)
        for node in nodes:
            visit(node)
        self.assertTrue(all(v['status'] == 'pending' for v in nodes.values()))

    def test_workers_cannot_run_large(self):
        packet = yaml.safe_load((ROOT / 'templates/TASK_PACKET.yaml').read_text())
        self.assertEqual(packet['limits']['maximum_tier'], 'L2')
        self.assertFalse(packet['limits']['large_1024_run_allowed'])
        self.assertFalse(self.policy['development_large_runs_allowed'])

    def test_full_chronology_on_small_grid(self):
        tier = self.policy['tiers']['L2']
        self.assertEqual(tier['chronological_steps'], [24, 48])
        self.assertEqual(tier['patches'], 153)
        self.assertTrue(tier['real_tiff_pipeline_required'])
        self.assertLessEqual(tier['preferred_max_side'], 128)

    def test_one_final_candidate_no_default_large_baseline(self):
        tier = self.policy['tiers']['L4']
        self.assertEqual(tier['candidate_runs'], 1)
        self.assertEqual(self.batch['candidate_trials'], 1)
        self.assertEqual(tier['new_baseline_runs'], 0)
        self.assertEqual(self.batch['new_baseline_trials'], 0)
        self.assertEqual(self.batch['paired_trials'], 0)
        self.assertFalse(tier['automatic_secondary_regimes'])
        self.assertEqual(tier['max_causally_fixed_candidate_retries'], 1)
        self.assertEqual(tier['target_seconds'], 1800)

    def test_separate_branch_no_remote_or_merge(self):
        branch = self.policy['branch']
        self.assertEqual(branch['integration'], 'perf/lean-cpu-v4')
        self.assertTrue(branch['separate_worktree'])
        self.assertTrue(branch['worker_branches'])
        for key in ('auto_push', 'auto_pr', 'auto_merge', 'touch_main'):
            self.assertFalse(branch[key])

    def test_ci_does_not_mask_required_checks(self):
        self.assertTrue(self.policy['ci']['small_real_e2e_preserved'])
        self.assertTrue(self.policy['ci']['required_checks_preserved'])
        self.assertFalse(self.policy['ci']['global_disable_allowed'])
        self.assertFalse(self.policy['ci']['large_runs_on_pr'])
        text = (ROOT / 'BRANCH_AND_CI.md').read_text()
        self.assertIn('pending', text)
        self.assertIn('default branch', text)
        self.assertIn('pull_request_target', text)

    def test_dependency_reuse_not_file_name_only(self):
        fields = self.policy['evidence_key_fields']
        for key in ('source_dependency_closure', 'fixture_and_reference_hashes',
                    'environment_compiler_math_profile', 'test_harness_and_rules'):
            self.assertIn(key, fields)

    def test_no_model_execution_claim(self):
        self.assertIsNone(self.policy['model_execution_results'])
        self.assertIsNone(self.batch['execution_results'])
        self.assertFalse(self.policy['release_matrix_automatic'])
        self.assertFalse(self.batch['merge_after_run'])

    def test_local_markdown_links(self):
        for path in ROOT.rglob('*.md'):
            for target in re.findall(r'\]\(([^\s)]+)(?:\s+[^)]*)?\)', path.read_text()):
                if target.startswith(('https:', 'http:', '#', 'mailto:')):
                    continue
                target = unquote(target.split('#', 1)[0])
                if target:
                    self.assertTrue((path.parent / target).exists(), f'{path}: {target}')

    def test_final_task_has_source_freeze_dependency(self):
        nodes = {v['id']: v for v in self.dag['tasks']}
        self.assertEqual(nodes['V4-72']['maximum_validation_tier'], 'L4')
        self.assertIn('V4-70', nodes['V4-72']['depends_on'])
        self.assertIn('V4-72', nodes['V4-71']['depends_on'])
        self.assertEqual(nodes['V4-71']['maximum_validation_tier'], 'none')


def main():
    start = time.perf_counter()
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(PacketChecks))
    report = {
        'schema': 1, 'classification': 'v4_document_and_policy_integrity_only',
        'successful': result.wasSuccessful(), 'tests_run': result.testsRun,
        'failures': len(result.failures), 'errors': len(result.errors),
        'skips': len(result.skipped), 'elapsed_seconds': time.perf_counter() - start,
        'goal_codepoints_with_command': len((ROOT / 'GOAL.txt').read_text()) + 6,
        'dag_task_count': len(yaml.safe_load((ROOT / 'TASKS_OPTIMIZATION.yaml').read_text())['tasks']),
        'python': platform.python_version(),
        'production_solweig_executed': False, 'original_oracle_executed': False,
        'target_benchmark_executed': False, 'repository_branch_created': False,
        'github_settings_changed': False, 'subagents_executed': False,
        'log': log.getvalue()
    }
    dest = ROOT / 'evidence/v4_packet_checks.json'
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, indent=2) + '\n')
    print(log.getvalue(), end='')
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    raise SystemExit(main())
