#SOLWEIG-GPU: GPU-accelerated SOLWEIG model for urban thermal comfort simulation
#Copyright (C) 2022–2025 Harsh Kamath and Naveen Sudharsan

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful, but
#WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#General Public License for more details.
"""N8-22 legacy-DX parity pins: today's observable behavior is unchanged.

The selector exists in experiments/ only; these tests pin that its
existence changes nothing a user can observe:

* every legacy ``SOLWEIG_LIGHT_LW_BACKEND`` value keeps its CURRENT
  ``cylinder_longwave._lw_kernel`` resolution behavior (identity for
  non-expert values, the native dispatch wrapper for native/ispc),
  including the exact loud missing-build error wording;
* the auto path provably resolves to legacy A in the live dispatcher;
* no new environment variable exists (the selector reads exactly the one
  legacy name, and the src/ env-var surface still equals the frozen
  ``evidence/dx_baseline/branch_surface.json`` snapshot);
* importing ``solweig_light`` never pulls the policy module in;
* the policy module does no IO at import and no IO on a pure resolve
  (subprocess audit-hook proof), and never spawns or opens sockets;
* the shipped state has no activatable rows anywhere under the policy
  directory (registry empty; template pending).
"""
import ast
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'experiments' / 'optimization_v8' / 'policy'))
sys.path.insert(0, str(REPO / 'tests' / 'optimization_v8' / 'dx'))

import lw_default_policy as policy  # noqa: E402

import solweig_light.radiation.cylinder_longwave as cyl  # noqa: E402
from solweig_light.backends import native_lw  # noqa: E402

ENV = policy.LW_BACKEND_ENV

NON_EXPERT_VALUES = [None, '', 'numba', 'NUMBA', ' numba ', 'bogus', 'auto',
                     'ispo', '0', 'native-ish']
EXPERT_VALUES = ['native', 'ispc', 'NATIVE', 'Native', ' native\t', '\nISPC ']


def _set_env(monkeypatch, value):
    if value is None:
        monkeypatch.delenv(ENV, raising=False)
    else:
        monkeypatch.setenv(ENV, value)


# ---------------------------------------------------------------------------
# Live dispatcher parity per env value (byte-compat with current src)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize('value', NON_EXPERT_VALUES)
def test_non_expert_values_return_the_plain_numba_kernel(monkeypatch, value):
    """Auto -> A provable at the src level: with any non-expert value the
    live dispatcher returns the legacy kernel objects themselves."""
    _set_env(monkeypatch, value)
    assert cyl._lw_kernel(parallel=True) is cyl._longwave_primary
    assert cyl._lw_kernel(parallel=False) is cyl._longwave_primary_serial


@pytest.mark.parametrize('value', EXPERT_VALUES)
def test_expert_values_wrap_the_native_backend(monkeypatch, value):
    """native/ispc (after the legacy strip().lower()) resolve to the
    dispatch wrapper around native_lw.native_longwave_primary with the
    documented UnsupportedInput fallback -- pinned structurally, so no
    build is ever triggered by this test."""
    _set_env(monkeypatch, value)
    for parallel, kernel in ((True, cyl._longwave_primary),
                             (False, cyl._longwave_primary_serial)):
        resolved = cyl._lw_kernel(parallel=parallel)
        assert callable(resolved) and resolved.__name__ == 'dispatch'
        contents = [cell.cell_contents for cell in resolved.__closure__]
        assert kernel in contents
        assert native_lw.native_longwave_primary in contents
        assert native_lw.UnsupportedInput in contents


def test_policy_env_name_matches_src_constant():
    assert policy.LW_BACKEND_ENV == cyl._LW_BACKEND_ENV \
        == 'SOLWEIG_LIGHT_LW_BACKEND'


def test_policy_classification_matches_src_behavior(monkeypatch):
    """For every value class, the selector's classification agrees with
    what the live dispatcher actually did (expert iff a wrapper)."""
    for value in NON_EXPERT_VALUES[1:] + EXPERT_VALUES:
        _set_env(monkeypatch, value)
        resolved = cyl._lw_kernel(parallel=True)
        src_expert = resolved is not cyl._longwave_primary
        selection_expert = policy._explicit_value(os.environ) \
            in policy.EXPERT_VALUES
        assert src_expert == selection_expert, value


# ---------------------------------------------------------------------------
# Loud legacy error wording, byte-pinned
# ---------------------------------------------------------------------------


def test_missing_ispc_error_wording_is_byte_identical(monkeypatch, tmp_path):
    """SOLWEIG_LIGHT_LW_BACKEND=native with no ispc fails with EXACTLY the
    current message (paths substituted); never a silent fallback."""
    monkeypatch.setattr('shutil.which', lambda name: None)
    monkeypatch.setattr(native_lw, '_ISPC_FALLBACK',
                        str(tmp_path / 'no' / 'ispc'))
    cache = tmp_path / 'cache'
    expected = (
        'SOLWEIG_LIGHT_LW_BACKEND=native requested but ispc was not found. '
        'Install ISPC (>= 1.31) or build the library manually: '
        f'cd {native_lw._SRC_DIR} && ISPC=<ispc-path> zsh build.sh, then '
        f'copy liblw_native_g*dylib into {cache}')
    with pytest.raises(RuntimeError) as excinfo:
        native_lw._build(cache)
    assert str(excinfo.value) == expected


# ---------------------------------------------------------------------------
# No new DX: env vars, package import surface, dx baseline
# ---------------------------------------------------------------------------


def test_policy_module_reads_only_the_legacy_env_name():
    source = policy.__file__
    tree = ast.parse(Path(source).read_text())
    env_names = {node.value for node in ast.walk(tree)
                 if isinstance(node, ast.Constant)
                 and isinstance(node.value, str)
                 and node.value.startswith('SOLWEIG_LIGHT_')}
    assert env_names == {'SOLWEIG_LIGHT_LW_BACKEND'}, env_names


def test_policy_module_has_no_io_process_or_network_imports():
    source = Path(policy.__file__).read_text()
    for banned in ('import subprocess', 'import socket', 'import requests',
                   'import urllib', 'os.system', 'popen'):
        assert banned not in source, banned


def test_src_env_var_surface_equals_frozen_dx_baseline():
    """Re-derive the dx-baseline env-var scan for src/ and compare with the
    frozen branch_surface.json: this packet adds no environment variable
    to the package DX surface."""
    import dx_snapshot
    frozen = json.loads(dx_snapshot.BRANCH_SURFACE_PATH.read_text())
    current = dx_snapshot._env_vars_read_from_tree(
        REPO / 'src' / 'solweig_light')
    assert current == frozen['env_vars_read']


def test_importing_solweig_light_never_pulls_the_policy_module():
    code = textwrap.dedent('''
        import sys
        import solweig_light
        leaked = [name for name in sys.modules
                  if 'lw_default_policy' in name
                  or 'optimization_v8' in name]
        print(json.dumps(leaked))
    ''')
    proc = subprocess.run([sys.executable, '-c', 'import json\n' + code],
                          capture_output=True, text=True, cwd=str(REPO))
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == []


# ---------------------------------------------------------------------------
# No IO at import / pure resolve (audit hook in a fresh interpreter)
# ---------------------------------------------------------------------------


NO_IO_PROBE = textwrap.dedent('''
    import json, sys

    # Preload every stdlib module the policy module touches so the audit
    # window below sees only the module under test.
    import __future__, hashlib, os, platform, threading, dataclasses
    import pathlib

    EVENTS = []
    def hook(event, args):
        EVENTS.append((event, args))

    sys.path.insert(0, sys.argv[1])
    sys.addaudithook(hook)
    import lw_default_policy as policy

    # Pure resolve: injected env + injected empty registry -> no file, no
    # process, no network may be touched (today's auto path is A).
    selection = policy.resolve_lw_backend(env={}, registry={
        'schema': policy.REGISTRY_SCHEMA, 'records': []})
    assert selection.row == 'A', selection

    interesting = [e for e in EVENTS if e[0] in (
        'open', 'subprocess.Popen', 'os.system', 'socket.connect',
        'socket.getaddrinfo', 'socket.bind')]
    # Importing the module itself opens its .py and cached .pyc (the
    # interpreter tags the bytecode file); nothing else may be touched.
    def own_module_path(args):
        if not args:
            return False
        base = str(args[0]).replace('\\\\', '/').rsplit('/', 1)[-1]
        return base.startswith('lw_default_policy.')
    stray = [e for e in interesting
             if e[0] != 'open' or not own_module_path(e[1])]
    print(json.dumps({'events': len(EVENTS), 'stray': str(stray[:5])}))
    assert not stray, stray[:5]
''')


def test_policy_module_does_no_io_at_import_or_pure_resolve(tmp_path):
    proc = subprocess.run(
        [sys.executable, '-c', NO_IO_PROBE,
         str(REPO / 'experiments' / 'optimization_v8' / 'policy')],
        capture_output=True, text=True, cwd=str(REPO))
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)['stray'] == '[]'


# ---------------------------------------------------------------------------
# Shipped state: no activatable rows anywhere under the policy dir
# ---------------------------------------------------------------------------


def test_no_qualified_rows_ship_anywhere_under_policy_dir():
    policy_dir = REPO / 'experiments' / 'optimization_v8' / 'policy'
    offenders = []
    for path in sorted(policy_dir.rglob('*.json')):
        try:
            payload = json.loads(path.read_text())
        except ValueError:
            continue
        candidates = payload if isinstance(payload, list) else \
            payload.get('records', []) if isinstance(payload, dict) else []
        for record in candidates if isinstance(candidates, list) else []:
            if isinstance(record, dict) \
                    and record.get('schema') == policy.ROW_RECORD_SCHEMA \
                    and record.get('status') == policy.STATUS_QUALIFIED:
                offenders.append(str(path))
    assert offenders == []


def test_shipped_template_is_pending_and_inert():
    template = json.loads((REPO / 'experiments' / 'optimization_v8' / 'policy'
                           / 'templates' / 'row_record_pending.json')
                          .read_text())
    assert template['schema'] == policy.ROW_RECORD_SCHEMA
    assert template['status'] == 'pending'
    ok, reason = policy.validate_row_record(template)
    assert ok is False and reason.startswith('[not-qualified]'), reason
