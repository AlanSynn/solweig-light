#!/usr/bin/env python3
"""Packet/tool tests only. No SOLWEIG, target repository, model API or hosted CI."""
from __future__ import annotations
import ast
import importlib.util
import io
import json
import platform
import re
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from urllib.parse import unquote
import yaml

ROOT=Path(__file__).resolve().parents[1]

def load(name):
    spec=importlib.util.spec_from_file_location(name, ROOT/'tools'/f'{name}.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

prepare=load('prepare_worktree');installer=load('install_assets')
preflight=load('preflight_local');throughput=load('throughput_model')


def git(repo,*args):
    return subprocess.run(['git','-C',str(repo),*args],check=True,text=True,
                          capture_output=True).stdout.strip()


def fixture_repo(root):
    repo=root/'repo';repo.mkdir()
    git(repo,'init','-b','main')
    git(repo,'config','user.email','packet-test@example.invalid')
    git(repo,'config','user.name','Packet Test')
    (repo/'tracked.txt').write_text('baseline\n')
    git(repo,'add','tracked.txt');git(repo,'commit','-m','baseline')
    return repo


def place_rules(repo):
    p=repo/'optimization_v5_claude/CLAUDE_PROJECT_RULES.md'
    p.parent.mkdir();p.write_bytes((ROOT/'CLAUDE_PROJECT_RULES.md').read_bytes())


class PacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy=json.loads((ROOT/'validation_policy.json').read_text())
        cls.dag=yaml.safe_load((ROOT/'TASKS_CLAUDE.yaml').read_text())
        cls.entries=json.loads((ROOT/'STRATEGIES.json').read_text())['entries']

    def test_01_start_prompt_length(self):
        self.assertLessEqual(len((ROOT/'START_HERE.txt').read_text()),4000)
        self.assertFalse((ROOT/'START_HERE.txt').read_text().startswith('/goal'))

    def test_02_complete_catalog_preserved(self):
        ids=[e['id'] for e in self.entries]
        self.assertEqual(len(ids),56);self.assertEqual(len(set(ids)),56)
        self.assertEqual(sum(i.startswith('X') for i in ids),8)

    def test_03_dag_acyclic(self):
        nodes={t['id']:t for t in self.dag['tasks']}
        self.assertEqual(len(nodes),len(self.dag['tasks']))
        seen=set();active=set()
        def walk(n):
            self.assertIn(n,nodes)
            if n in seen:return
            self.assertNotIn(n,active);active.add(n)
            for d in nodes[n]['depends_on']:walk(d)
            active.remove(n);seen.add(n)
        for n in nodes:walk(n)
        self.assertEqual(len(seen),31)

    def test_04_no_required_astra_or_artificial_inference_cap(self):
        o=self.dag['orchestration']
        self.assertEqual(o['required_astra_calls'],0)
        self.assertIsNone(o['artificial_token_limit'])
        self.assertIsNone(o['artificial_total_agent_limit'])
        self.assertFalse(o['global_progress_polling'])
        self.assertEqual(o['maximum_simultaneous_benchmarks'],1)

    def test_05_retained_final_run_budget(self):
        p=self.policy['tiers']['L4']
        self.assertEqual(p['candidate_runs'],1)
        self.assertEqual(p['new_baseline_runs'],0)
        self.assertEqual(p['max_causally_fixed_candidate_retries'],1)
        self.assertFalse(self.policy['development_large_runs_allowed'])

    def test_06_final_gate_depends_on_freeze(self):
        n={t['id']:t for t in self.dag['tasks']}
        self.assertIn('C5-61',n['C5-62']['depends_on'])
        self.assertEqual(n['C5-62']['maximum_validation_tier'],'L4')
        self.assertEqual(sum(t['maximum_validation_tier']=='L4' for t in n.values()),1)

    def test_07_small_chronology_and_real_tiff_retained(self):
        l2=self.policy['tiers']['L2']
        self.assertEqual(l2['chronological_steps'],[24,48])
        self.assertEqual(l2['patches'],153)
        self.assertTrue(l2['real_tiff_pipeline_required'])

    def test_08_no_remote_merge_or_global_ci_disable(self):
        for key in ('auto_push','auto_pr','auto_merge','touch_main'):
            self.assertFalse(self.policy['branch'][key])
        self.assertFalse(self.policy['ci']['global_disable_allowed'])
        self.assertTrue(self.policy['ci']['required_checks_preserved'])

    def test_09_agent_frontmatter_and_unique_names(self):
        names=[]
        allowed={'name','description','tools','model','permissionMode','isolation'}
        for p in sorted((ROOT/'agents').glob('sw-*.md')):
            text=p.read_text();self.assertTrue(text.startswith('---\n'))
            data=yaml.safe_load(text.split('---',2)[1])
            self.assertLessEqual(set(data),allowed)
            self.assertIn(data['model'],('inherit','opus'))
            self.assertNotIn('bypassPermissions',data.values())
            names.append(data['name'])
        self.assertEqual(len(names),9);self.assertEqual(len(set(names)),9)

    def test_10_readonly_review_and_audit(self):
        for name in ('sw-opus-reviewer','sw-source-auditor'):
            text=(ROOT/'agents'/f'{name}.md').read_text()
            tools=yaml.safe_load(text.split('---',2)[1])['tools']
            self.assertNotIn('Bash',tools);self.assertNotIn('Write',tools)

    def test_11_short_always_loaded_rules(self):
        text=(ROOT/'CLAUDE_PROJECT_RULES.md').read_text()
        self.assertLess(len(text.splitlines()),100)
        self.assertNotIn('@STRATEGY_CATALOG',text)
        self.assertNotIn('@IMPLEMENTATION_BLUEPRINT',text)

    def test_12_all_machine_records_parse(self):
        for path in ROOT.rglob('*.json'):
            if 'inherited_v4' not in path.parts:json.loads(path.read_text())
        for path in ROOT.rglob('*.yaml'):yaml.safe_load(path.read_text())

    def test_13_all_python_syntax(self):
        for path in (ROOT/'tools').glob('*.py'):ast.parse(path.read_text(),filename=str(path))

    def test_14_markdown_local_links(self):
        for path in ROOT.rglob('*.md'):
            if 'inherited_v4' in path.parts:continue
            for value in re.findall(r'\]\(([^\s)]+)(?:\s+[^)]*)?\)',path.read_text()):
                if value.startswith(('http:','https:','#','mailto:')):continue
                value=unquote(value.split('#')[0])
                if value:self.assertTrue((path.parent/value).exists(),f'{path}: {value}')

    def test_15_redacted_configuration_no_auth_values(self):
        d={'env':{'ANTHROPIC_AUTH_TOKEN':'NEVER-ECHO-TOKEN',
                  'ANTHROPIC_BASE_URL':'https://user:password@example.invalid/private?key=SECRET',
                  'ANTHROPIC_DEFAULT_OPUS_MODEL':'glm-5.3'}}
        summary=preflight.summarize_settings(d);s=json.dumps(summary)
        for secret in ('NEVER-ECHO-TOKEN','password','SECRET','/private'):
            self.assertNotIn(secret,s)
        self.assertEqual(summary['configured_provider_host'],'example.invalid')
        self.assertFalse(summary['backend_verified'])

    def test_16_preflight_has_no_backend_claim(self):
        result=preflight.collect([],env={},cli='definitely-not-installed-claude-packet-test')
        self.assertFalse(result['api_calls_made'])
        self.assertFalse(result['backend_verified'])
        self.assertFalse(result['effective_precedence_resolved'])

    def test_17_worktree_preview_no_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);repo=fixture_repo(root);dst=root/'worker'
            before=git(repo,'rev-parse','HEAD')
            result=prepare.prepare(repo,dst,'perf/test')
            self.assertFalse(dst.exists());self.assertEqual(result['base_sha'],before)
            self.assertEqual(git(repo,'branch','--show-current'),'main')

    def test_18_worktree_apply_exact_base_temp_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);repo=fixture_repo(root);dst=root/'worker'
            base=git(repo,'rev-parse','HEAD')
            result=prepare.prepare(repo,dst,'perf/test',apply=True)
            self.assertEqual(result['actual_new_head'],base)
            self.assertEqual(git(repo,'branch','--show-current'),'main')
            self.assertEqual(git(dst,'branch','--show-current'),'perf/test')

    def test_19_worktree_dirty_source_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);repo=fixture_repo(root)
            (repo/'tracked.txt').write_text('user change\n')
            with self.assertRaises(ValueError):prepare.prepare(repo,root/'worker','perf/test',apply=True)
            self.assertFalse((root/'worker').exists())

    def test_20_worktree_existing_destination_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);repo=fixture_repo(root);dst=root/'worker';dst.mkdir()
            with self.assertRaises(ValueError):prepare.prepare(repo,dst,'perf/test',apply=True)

    def test_21_install_preview_no_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo=fixture_repo(Path(tmp));place_rules(repo)
            result=installer.install(repo)
            self.assertEqual(result['mode'],'preview')
            self.assertFalse((repo/'CLAUDE.md').exists())
            self.assertFalse((repo/'.claude').exists())

    def test_22_install_protected_branch_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo=fixture_repo(Path(tmp));place_rules(repo)
            with self.assertRaises(ValueError):installer.install(repo,True)
            self.assertFalse((repo/'.claude').exists())

    def test_23_install_preserves_existing_rules_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo=fixture_repo(Path(tmp));git(repo,'switch','-c','perf/test');place_rules(repo)
            (repo/'CLAUDE.md').write_text('Existing user safety rules.\n')
            installer.install(repo,True)
            text=(repo/'CLAUDE.md').read_text()
            self.assertTrue(text.startswith('Existing user safety rules.'))
            self.assertEqual(text.count(installer.BEGIN),1)
            self.assertEqual(installer.install(repo,True)['paths'],[])

    def test_24_install_conflict_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo=fixture_repo(Path(tmp));git(repo,'switch','-c','perf/test');place_rules(repo)
            dest=repo/'.claude/agents/sw-glm-implementer.md';dest.parent.mkdir(parents=True)
            dest.write_text('user-owned conflicting definition\n')
            with self.assertRaises(ValueError):installer.install(repo,True)
            self.assertEqual(dest.read_text(),'user-owned conflicting definition\n')
            self.assertFalse((repo/'CLAUDE.md').exists())

    def test_25_install_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);repo=fixture_repo(root);place_rules(repo)
            outside=root/'outside';outside.mkdir()
            (repo/'.claude').symlink_to(outside,target_is_directory=True)
            with self.assertRaises(ValueError):installer.install(repo)
            self.assertEqual(list(outside.iterdir()),[])

    def test_26_throughput_stays_hypothetical(self):
        cfg=json.loads((ROOT/'throughput_inputs.json').read_text())
        results=throughput.run(cfg)
        self.assertFalse(results['solweig_executed']);self.assertFalse(results['hardware_benchmarked'])
        for r in results['all_settings']:
            self.assertFalse(r['actual_goal_passed']);self.assertFalse(r['calibrated_forecast'])
        self.assertGreater(len(results['scenario_summaries']),0)

    def test_27_routing_and_domain_boundaries_documented(self):
        route=(ROOT/'MODEL_ROUTING.md').read_text()
        self.assertIn('ANTHROPIC_DEFAULT_OPUS_MODEL',route)
        self.assertIn('separate',route)
        self.assertIn('backend_verified: false',route)
        blueprint=(ROOT/'IMPLEMENTATION_BLUEPRINT.md').read_text()
        for text in ('first-step','positive-bush','signed zero','water','fallback','original patch order'):
            self.assertIn(text,blueprint)


def main():
    start=time.perf_counter();out=io.StringIO()
    result=unittest.TextTestRunner(stream=out,verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(PacketTests))
    report={'schema':1,'classification':'v5_packet_and_local_helper_tests_only',
            'successful':result.wasSuccessful(),'tests_run':result.testsRun,
            'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),
            'elapsed_seconds':time.perf_counter()-start,'python':platform.python_version(),
            'start_prompt_characters':len((ROOT/'START_HERE.txt').read_text()),
            'strategy_count':len(json.loads((ROOT/'STRATEGIES.json').read_text())['entries']),
            'task_count':len(yaml.safe_load((ROOT/'TASKS_CLAUDE.yaml').read_text())['tasks']),
            'agent_template_count':len(list((ROOT/'agents').glob('sw-*.md'))),
            'production_solweig_executed':False,'original_oracle_executed':False,
            'target_benchmark_executed':False,'claude_cli_executed':False,
            'provider_model_calls_executed':False,'user_repository_branch_created':False,
            'temporary_fixture_git_operations_executed':True,'github_ci_changed':False,
            'log':out.getvalue()}
    path=ROOT/'evidence/v5_packet_checks.json';path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(report,indent=2)+'\n')
    print(out.getvalue(),end='')
    print(json.dumps({k:v for k,v in report.items() if k!='log'},indent=2))
    return 0 if result.wasSuccessful() else 1

if __name__=='__main__':raise SystemExit(main())
