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
"""N9 legacy-DX parity pins: today's observable behavior is unchanged.

N9 F4 removed the selection policy from the runtime (the bounded Numba
stream IS the structural default); these tests pin that the removal
changes nothing a legacy user can observe:

* the legacy ``SOLWEIG_LIGHT_LW_BACKEND`` values keep their CURRENT
  ``cylinder_longwave._lw_kernel`` resolution behavior (identity for
  non-expert values, the native dispatch wrapper for native/ispc),
  including the exact loud missing-build error wording;
* with the env UNSET, the driver route is STRUCTURAL: admitted packed
  invocations take the bounded stream, everything else declines
  structurally to the trusted legacy loop -- and NO registry is read
  anywhere in the path (the qualification selector module is gone from
  the package and never imported by a routed call);
* ``SOLWEIG_LIGHT_LW_BACKEND=native`` still stands the stream route
  down and reaches the B7-32 loud-error route (never a silent
  fallback);
* ``cylinder_longwave`` remains the ONLY env-read site of the LW seam
  and the dispatch module reads no environment at all;
* importing ``solweig_light`` never pulls any of ``_native_dispatch``
  in.
"""
import ast
import importlib.util
import json
import subprocess
import sys
import textwrap
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[3]

import solweig_light.radiation.cylinder_longwave as cyl  # noqa: E402
from solweig_light.backends import native_lw  # noqa: E402

ENV = 'SOLWEIG_LIGHT_LW_BACKEND'

# The v6 cylinder family's conftest, loaded by file path under a UNIQUE
# module name: a bare `import conftest` is shadowed by sibling suites in
# one pytest session.
_V6_CONFTEST = (Path(__file__).resolve().parents[2] / 'optimization_v6'
                / 'cylinder_lw' / 'conftest.py')
_spec = importlib.util.spec_from_file_location('_n9dx_v6_conftest',
                                               str(_V6_CONFTEST))
_v6 = importlib.util.module_from_spec(_spec)
sys.modules['_n9dx_v6_conftest'] = _v6
_spec.loader.exec_module(_v6)
lcyl_arguments = _v6.lcyl_arguments
packed = _v6.packed

_ROWS, _COLS, _PATCHES = 37, 53, 153

NON_EXPERT_VALUES = [None, '', 'numba', 'NUMBA', ' numba ', 'bogus', 'auto',
                     'ispo', '0', 'native-ish']
EXPERT_VALUES = ['native', 'ispc', 'NATIVE', 'Native', ' native\t', '\nISPC ']


def _set_env(monkeypatch, value):
    if value is None:
        monkeypatch.delenv(ENV, raising=False)
    else:
        monkeypatch.setenv(ENV, value)


@pytest.fixture(autouse=True)
def _parity_env(monkeypatch):
    """Start every test from the shipped no-env state; never leak
    region-owner threads."""
    monkeypatch.delenv(ENV, raising=False)
    yield
    import solweig_light._native_dispatch.region.region_pool as rp
    rp.reset_pools_for_tests()


@pytest.fixture()
def rng():
    return np.random.default_rng(20260922)


@pytest.fixture()
def packed_args(rng):
    """Driver arguments over adversarial PACKED channels (admitted by
    the structural route: mixed binary/ternary/raw storage)."""
    gen = np.random.default_rng(20260922)
    return lcyl_arguments(rng, rows=_ROWS, cols=_COLS,
                          shmat=packed(gen, _ROWS, _COLS, _PATCHES,
                                       ('binary', 'ternary', 'raw')),
                          vegshmat=packed(gen, _ROWS, _COLS, _PATCHES,
                                          ('ternary', 'raw', 'binary')),
                          vbshvegshmat=packed(gen, _ROWS, _COLS, _PATCHES,
                                              ('raw', 'binary', 'ternary')))


@pytest.fixture()
def region_spy(monkeypatch):
    """Record every execute_regions call, then run the real executor."""
    import solweig_light._native_dispatch.region.region_pool as rp
    calls = []
    real = rp.execute_regions

    def spy(plan, consumer, output, **kwargs):
        report = real(plan, consumer, output, **kwargs)
        calls.append((plan, consumer, output, report))
        return report

    monkeypatch.setattr(rp, 'execute_regions', spy)
    return calls


def _assert_no_policy_in_path():
    """The qualification selector is gone from the package (N9 F4) and
    the call just made imported no stale copy."""
    assert importlib.util.find_spec(
        'solweig_light._native_dispatch.lw_default_policy') is None
    assert 'solweig_light._native_dispatch.lw_default_policy' \
        not in sys.modules


# ---------------------------------------------------------------------------
# Live dispatcher parity per env value (byte-compat with current src)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize('value', NON_EXPERT_VALUES)
def test_non_expert_values_return_the_plain_numba_kernel(monkeypatch, value):
    """With any non-expert value the live dispatcher returns the legacy
    kernel objects themselves -- the exported kernel surface is
    unchanged, whatever the structural route does at the driver seam."""
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


def test_env_name_is_the_legacy_constant():
    assert cyl._LW_BACKEND_ENV == ENV


# ---------------------------------------------------------------------------
# (a) env unset: the route is structural, no registry read anywhere
# ---------------------------------------------------------------------------

def test_default_admitted_call_routes_the_stream_and_reads_no_registry(
        packed_args, region_spy):
    """No env, admitted packed channels: the bounded stream executes --
    and the qualification selector module (deleted in N9 F4) is neither
    present in the package nor imported anywhere along the way."""
    sys.modules.pop('solweig_light._native_dispatch.lw_default_policy',
                    None)   # defensive against any stale importer
    result = cyl.Lcyl_v2022a_primary(**packed_args)
    assert len(region_spy) == 1
    plan, consumer, output, report = region_spy[0]
    assert consumer.mode.value == 'self_parallel'
    assert report.blocks == plan.total_blocks
    assert result[0].shape == (_ROWS, _COLS)
    _assert_no_policy_in_path()


def test_default_declines_are_structural_and_never_read_a_registry(
        rng, region_spy):
    """No env, dense channels (a non-admitted payload): a STRUCTURAL
    pre-launch decline -- the trusted legacy loop serves the call, the
    region machinery is untouched, and no registry/policy module exists
    anywhere in the path."""
    sys.modules.pop('solweig_light._native_dispatch.lw_default_policy',
                    None)
    args = lcyl_arguments(rng, rows=_ROWS, cols=_COLS)  # dense mats
    result = cyl.Lcyl_v2022a_primary(**args)
    assert region_spy == []
    assert result[0].shape == (_ROWS, _COLS)
    _assert_no_policy_in_path()


def test_dispatch_module_reads_no_environment():
    """The N9 dispatch seam reads NO environment variables: the expert
    intercept stays in ``cylinder_longwave`` (the one legacy env-read
    site), so the package's env surface is exactly as frozen. Scanned at
    the AST level so prose in docstrings cannot fake either direction."""
    source = Path(cyl.__file__).read_text()
    cyl_envs = {node.value for node in ast.walk(ast.parse(source))
                if isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and node.value.startswith('SOLWEIG_LIGHT_')}
    assert cyl_envs == {ENV}, cyl_envs

    dispatch_source = importlib.util.find_spec(
        'solweig_light.radiation._lw_dispatch')
    assert dispatch_source is not None
    tree = ast.parse(Path(dispatch_source.origin).read_text())
    env_reads = [node for node in ast.walk(tree)
                 if isinstance(node, ast.Attribute)
                 and node.attr in ('environ', 'getenv')]
    assert env_reads == [], env_reads
    env_names = {node.value for node in ast.walk(tree)
                 if isinstance(node, ast.Constant)
                 and isinstance(node.value, str)
                 and node.value.startswith('SOLWEIG_LIGHT_')}
    assert env_names == set(), env_names


# ---------------------------------------------------------------------------
# (b) env=native: the B7-32 loud-error route, unchanged
# ---------------------------------------------------------------------------

def test_expert_env_stands_the_stream_route_down(packed_args, region_spy,
                                                 monkeypatch):
    """env=native/ispc: the stream route returns None at the seam (the
    region machinery is never touched) and the legacy B7-32 kernel
    resolver serves the call."""
    for value in ('native', 'ispc'):
        monkeypatch.setenv(ENV, value)
        result = cyl.Lcyl_v2022a_primary(**packed_args)
        assert result[0].shape == (_ROWS, _COLS)
    assert region_spy == []


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
# (c) package import surface: none of _native_dispatch
# ---------------------------------------------------------------------------

def test_importing_solweig_light_never_pulls_the_dispatch_package():
    code = textwrap.dedent('''
        import sys
        import solweig_light
        leaked = [name for name in sys.modules
                  if '_native_dispatch' in name
                  or 'optimization_v8' in name]
        print(json.dumps(leaked))
    ''')
    proc = subprocess.run([sys.executable, '-c', 'import json\n' + code],
                          capture_output=True, text=True, cwd=str(REPO))
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == []
