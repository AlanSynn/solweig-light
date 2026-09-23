#SOLWEIG-GPU: GPU-accelerated SOLWEIG model for urban thermal comfort simulation
#Copyright (C) 2022–2025 Harsh Kamath and Naveen Sudharsan
import pytest
pytest.skip(
    'archived with the N8 native row and qualification machinery '
    '(N9 F4 closed_cpu_only): research copies preserved under '
    'experiments/optimization_v8/native_dispatch/',
    allow_module_level=True)

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
"""N8-10 acceptance tests for the workflow-owned native handle.

Every dossier 'Small acceptance tests' bullet is a test here:

* repeated executes perform ZERO source-opens/JSON/stat/hash (IoSpy);
* the ACTUAL C entry counter increases for admitted calls (entries-dict
  replacement, the N8-02-instrumented technique reviewed sound by
  n8_30_review_n8_02_profile.json); unsupported input takes the original
  fallback and performs no C entry;
* two concurrent preparations use one generation with no half-built state;
* workflow-generation and PID changes cannot reuse stale pointer state;
* missing binary vs corrupt digest vs unsupported ISA vs admitted native
  error are DISTINCT types (plus stale-handle);
* captured f32/f64 outputs stay bitwise equal through the handle path vs
  the current shipped path on the frozen N8-04 adversarial grid.
"""
import builtins
import contextlib
import ctypes
import hashlib
import json
import os
import shutil
import subprocess
import threading

import numpy as np
import pytest
from numpy import float32 as F32

from solweig_light._native_dispatch import native_handle
import lw_reference_oracle as oracle
from lw_identity_grid import adversarial_inputs, kernel_pair

NUMBA_KERNEL, _ = kernel_pair()

TAXONOMY = ('MissingNativeArtifact', 'CorruptNativeArtifact',
            'UnsupportedNativeISA', 'NativeExecutionError',
            'StaleNativeHandle')


# ---------------------------------------------------------------------------
# spies
# ---------------------------------------------------------------------------

class IoSpy:
    """Wrap os/open/json/hashlib/subprocess/ctypes/shutil entry points and
    count calls.  Armed ONLY around execute() calls, so any nonzero count
    is per-call preparation work leaking into the hot path."""

    _TARGETS = (
        (os, 'mkdir', 'os.mkdir'), (os, 'makedirs', 'os.makedirs'),
        (os, 'stat', 'os.stat'), (os, 'lstat', 'os.lstat'),
        (builtins, 'open', 'open'),
        (json, 'loads', 'json.loads'), (json, 'load', 'json.load'),
        (hashlib, 'sha256', 'hashlib.sha256'),
        (subprocess, 'run', 'subprocess.run'),
        (subprocess, 'Popen', 'subprocess.Popen'),
        (ctypes, 'CDLL', 'ctypes.CDLL'),
        (shutil, 'which', 'shutil.which'),
    )

    def __init__(self):
        self.counts = {}
        self._patches = []
        self._armed = False

    def __enter__(self):
        for target, name, label in self._TARGETS:
            original = getattr(target, name)

            def wrapper(*args, __orig=original, __label=label, **kwargs):
                if self._armed:
                    self.counts[__label] = self.counts.get(__label, 0) + 1
                return __orig(*args, **kwargs)

            setattr(target, name, wrapper)
            self._patches.append((target, name, original))
        self._armed = True
        return self

    def __exit__(self, *exc):
        self._armed = False
        for target, name, original in reversed(self._patches):
            setattr(target, name, original)
        self._patches.clear()
        return False


@contextlib.contextmanager
def counting_spy(module, attr):
    """Count calls to ``module.attr`` during the window (restores after)."""
    calls = []
    original = getattr(module, attr)

    def wrapper(*args, **kwargs):
        calls.append((args, kwargs))
        return original(*args, **kwargs)

    setattr(module, attr, wrapper)
    try:
        yield calls
    finally:
        setattr(module, attr, original)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _dispatch(handle, args):
    """Mirror cylinder_longwave._lw_kernel: UnsupportedInput -> Numba.
    (caller-owned ``out`` is a native-adapter extension; the fallback kernel
    allocates its own result exactly as the shipped dispatcher does.)"""
    try:
        return handle.execute(**args)
    except native_handle.UnsupportedInput:
        fallback = {k: v for k, v in args.items() if k != 'out'}
        return NUMBA_KERNEL(**fallback)


def _wrap_entries(handle):
    """Replace entries with counting wrappers (proven-sound N8-02 technique);
    returns the counter dict."""
    counts = {'f32': 0, 'f64': 0}
    for spec in ('f32', 'f64'):
        original = handle._entries[spec]

        def wrapper(*a, __orig=original, __spec=spec, **kw):
            counts[__spec] += 1
            return __orig(*a, **kw)

        handle._entries[spec] = wrapper
    return counts


def _grid(B=7, P=13, seed=5):
    return adversarial_inputs(B, P, seed=seed)


# ---------------------------------------------------------------------------
# 1. zero preparation IO in the hot path + admitted C-entry proof
# ---------------------------------------------------------------------------

def test_execute_zero_preparation_io(nh, artifact_dir):
    handle = nh.prepare_native_handle(artifact_dir=artifact_dir)
    counts = _wrap_entries(handle)
    bundles = [_grid(7, 13, 5), _grid(8, 8, 6), _grid(9, 153, 7),
               _grid(1, 1, 8), _grid(11, 2, 9)]
    expected = {'f32': 0, 'f64': 0}
    with IoSpy() as spy:
        for _rep in range(10):
            for bundle in bundles:
                handle.execute(**bundle)          # f64 profile (float scalars)
                expected['f64'] += 1
                f32args = dict(bundle)
                f32args['surface_sun'] = F32(bundle['surface_sun'])
                f32args['surface_sh'] = F32(bundle['surface_sh'])
                handle.execute(**f32args)         # f32 profile
                expected['f32'] += 1
                out = np.empty((bundle['sh'].shape[0], 7), F32)
                handle.execute(out=out, **bundle)  # caller-provided out
                expected['f64'] += 1
    assert spy.counts == {}, spy.counts
    assert counts == expected


def test_zero_pixel_early_return_no_c_entry(nh, artifact_dir):
    handle = nh.prepare_native_handle(artifact_dir=artifact_dir)
    counts = _wrap_entries(handle)
    out = handle.execute(**_grid(0, 3, 10))
    assert out.shape == (0, 7) and out.dtype == F32
    assert counts == {'f32': 0, 'f64': 0}


def test_identity_reports_no_io(nh, artifact_dir):
    handle = nh.prepare_native_handle(artifact_dir=artifact_dir)
    with IoSpy() as spy:
        ident = handle.identity()
    assert spy.counts == {}
    assert ident['kernel_sha256'] == handle.kernel_digest
    assert ident['pid'] == os.getpid()
    assert ident['gang'] == 8
    assert set(ident['scalar_entry_map']) == {'f32', 'f64'}
    assert ident['stamp']['kernel_sha256'] == ident['kernel_sha256']


# ---------------------------------------------------------------------------
# 2. unsupported input -> original fallback, no C entry
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('mutate', [
    'dtype',            # sh promoted to float64
    'P_too_large',      # P > 609
    'scalar_mismatch',  # f32 surface_sun with f64 surface_sh
    'python_refl',      # Python float reflection_factor
    'out_alias',        # caller out overlapping sh's bytes
    'out_readonly',     # read-only caller out
    'bad_stride',       # non C-contiguous vb
])
def test_unsupported_input_falls_back_no_c_entry(nh, artifact_dir, mutate):
    handle = nh.prepare_native_handle(artifact_dir=artifact_dir)
    counts = _wrap_entries(handle)
    args = _grid(7, 13, 11)
    if mutate == 'dtype':
        args['sh'] = args['sh'].astype(np.float64)
    elif mutate == 'P_too_large':
        args = _grid(2, 610, 12)
    elif mutate == 'scalar_mismatch':
        args['surface_sun'] = F32(args['surface_sun'])
    elif mutate == 'python_refl':
        args['reflection_factor'] = float(args['reflection_factor'])
    elif mutate == 'out_alias':
        buf = np.zeros(7 * 13, F32)
        args['sh'] = buf.reshape(7, 13)     # extent [0, 364)
        args['out'] = buf[:49].reshape(7, 7)  # extent [0, 196): overlaps
    elif mutate == 'out_readonly':
        out = np.zeros((7, 7), F32)
        out.flags.writeable = False
        args['out'] = out
    elif mutate == 'bad_stride':
        args['vb'] = np.asfortranarray(args['vb'])
    with pytest.raises(nh.UnsupportedInput):
        handle.execute(**args)
    assert counts == {'f32': 0, 'f64': 0}
    # the ORIGINAL fallback semantics: dispatch falls back to Numba
    result = _dispatch(handle, args)
    kernel_args = {k: v for k, v in args.items() if k != 'out'}
    assert oracle.bitwise_equal(result, NUMBA_KERNEL(**kernel_args))


def test_admitted_error_is_distinct_from_fallback(nh, artifact_dir):
    """A failure of an ADMITTED invocation must NOT fall back: it raises
    NativeExecutionError (loud), which _dispatch does not catch."""
    handle = nh.prepare_native_handle(artifact_dir=artifact_dir)
    args = _grid(4, 5, 13)

    def boom(*a, **kw):
        raise ValueError('synthetic post-launch failure')

    handle._entries['f64'] = boom
    with pytest.raises(nh.NativeExecutionError):
        handle.execute(**args)
    with pytest.raises(nh.NativeExecutionError):
        _dispatch(handle, args)   # falls back ONLY on UnsupportedInput


# ---------------------------------------------------------------------------
# 3. concurrency: one generation, no half-published state
# ---------------------------------------------------------------------------

def test_concurrent_prepare_single_generation(nh, artifact_dir):
    """Widen the validation window, then race 8 prepares across a barrier:
    exactly one CDLL load, one shared handle/generation, correct results."""
    barrier = threading.Barrier(8)
    results, errors = [], []
    real_sha = nh._sha256_file

    def slowed(path, *a, **kw):
        import time
        time.sleep(0.02)
        return real_sha(path, *a, **kw)

    nh._sha256_file = slowed
    try:
        def worker():
            barrier.wait()
            try:
                results.append(
                    nh.prepare_native_handle(artifact_dir=artifact_dir))
            except Exception as exc:              # pragma: no cover
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        with counting_spy(ctypes, 'CDLL') as cdll_calls:
            for t in threads:
                t.start()
            for t in threads:
                t.join()
    finally:
        nh._sha256_file = real_sha
    assert not errors, errors
    assert len(results) == 8
    assert len({h.generation for h in results}) == 1
    assert len({id(h) for h in results}) == 1      # one published handle
    assert len(cdll_calls) == 1                    # exactly one library load
    assert oracle.bitwise_equal(results[0].execute(**_grid(3, 7, 14)),
                                NUMBA_KERNEL(**_grid(3, 7, 14)))
    assert len(nh.registry_snapshot()) == 1


# ---------------------------------------------------------------------------
# 4. workflow generation and PID lifetimes
# ---------------------------------------------------------------------------

def test_workflow_generation_invalidation(nh, artifact_dir):
    old_token = nh.current_workflow_generation()
    h1 = nh.prepare_native_handle(artifact_dir=artifact_dir)
    assert h1.workflow_generation == old_token

    new_token = nh.new_workflow_generation()
    assert new_token != old_token
    h2 = nh.prepare_native_handle(artifact_dir=artifact_dir)
    assert h2 is not h1
    assert h2.workflow_generation == new_token
    # registry serves the new generation, not the stale one
    h3 = nh.prepare_native_handle(artifact_dir=artifact_dir)
    assert h3 is h2
    # a RUNNING workflow keeps its loaded generation: h1 still executes
    assert oracle.bitwise_equal(h1.execute(**_grid(4, 5, 15)),
                                NUMBA_KERNEL(**_grid(4, 5, 15)))


def test_pid_change_rejects_and_rebuilds(nh, artifact_dir):
    """Fork simulation via pid injection: stale handle refuses to execute;
    the child prepare loads a FRESH CDLL (no parent pointer reuse)."""
    real_getpid = nh._getpid
    parent_pid = real_getpid()
    h_parent = nh.prepare_native_handle(artifact_dir=artifact_dir)
    assert h_parent.pid == parent_pid

    nh._getpid = lambda: parent_pid + 1          # the forked child's pid
    try:
        with pytest.raises(nh.StaleNativeHandle):
            h_parent.execute(**_grid(4, 5, 16))
        with counting_spy(ctypes, 'CDLL') as cdll_calls:
            h_child = nh.prepare_native_handle(artifact_dir=artifact_dir)
        assert h_child is not h_parent
        assert h_child.pid == parent_pid + 1
        assert len(cdll_calls) == 1              # fresh load, no reuse
        assert oracle.bitwise_equal(h_child.execute(**_grid(4, 5, 16)),
                                    NUMBA_KERNEL(**_grid(4, 5, 16)))
        # the parent's handle still works for the parent
        nh._getpid = real_getpid
        assert h_parent.execute(**_grid(4, 5, 16)) is not None
    finally:
        nh._getpid = real_getpid


def test_registry_keyed_by_pid_and_generation(nh, artifact_dir):
    h1 = nh.prepare_native_handle(artifact_dir=artifact_dir)
    real_getpid = nh._getpid
    nh._getpid = lambda: real_getpid() + 5
    try:
        nh.prepare_native_handle(artifact_dir=artifact_dir)
        assert len(nh.registry_snapshot()) == 2  # distinct pid keys
        nh.new_workflow_generation()
        nh.prepare_native_handle(artifact_dir=artifact_dir)
        assert len(nh.registry_snapshot()) == 3  # distinct generation keys
    finally:
        nh._getpid = real_getpid
    assert h1.execute(**_grid(2, 3, 17)) is not None


# ---------------------------------------------------------------------------
# 5. error taxonomy
# ---------------------------------------------------------------------------

def test_error_taxonomy_distinct(nh, artifact_dir, tmp_path, monkeypatch):
    # missing binary: empty dir, no artifact at all
    empty = tmp_path / 'empty'
    empty.mkdir()
    with pytest.raises(nh.MissingNativeArtifact) as missing:
        nh.prepare_native_handle(artifact_dir=empty)
    assert 'auto' in str(missing.value) and 'expert' in str(missing.value)

    # corrupt/mismatched digest: dylib present, stamp pinned to a WRONG
    # kernel digest
    corrupt = tmp_path / 'corrupt'
    corrupt.mkdir()
    (corrupt / 'liblw_native_g8.dylib').write_bytes(
        (artifact_dir / 'liblw_native_g8.dylib').read_bytes())
    (corrupt / 'build_stamp.json').write_text(json.dumps(
        {'kernel_sha256': '0' * 64, 'ispc': 'x', 'built_utc': 'x'}))
    with pytest.raises(nh.CorruptNativeArtifact):
        nh.prepare_native_handle(artifact_dir=corrupt)

    # dylib present but stamp missing entirely: unverifiable binding
    nostamp = tmp_path / 'nostamp'
    nostamp.mkdir()
    (nostamp / 'liblw_native_g8.dylib').write_bytes(
        (artifact_dir / 'liblw_native_g8.dylib').read_bytes())
    with pytest.raises(nh.CorruptNativeArtifact):
        nh.prepare_native_handle(artifact_dir=nostamp)

    # unsupported ISA: gang outside the reviewed domain / non-arm64 host
    with pytest.raises(nh.UnsupportedNativeISA):
        nh.prepare_native_handle(artifact_dir=artifact_dir, gang=6)
    monkeypatch.setattr(nh.platform, 'machine', lambda: 'x86_64')
    with pytest.raises(nh.UnsupportedNativeISA):
        nh.prepare_native_handle(artifact_dir=tmp_path / 'isa')
    monkeypatch.undo()

    # admitted native runtime error (entry fails after launch); the ISA
    # failure above was cached for that key, so advance the workflow first
    nh.new_workflow_generation()
    ok = nh.prepare_native_handle(artifact_dir=artifact_dir)
    original = ok._entries['f64']

    def boom(*a, **kw):
        raise OSError('synthetic post-launch failure')

    ok._entries['f64'] = boom
    with pytest.raises(nh.NativeExecutionError):
        ok.execute(**_grid(2, 3, 18))
    ok._entries['f64'] = original

    # pairwise distinct classes; none is the fallback signal
    classes = [nh.MissingNativeArtifact, nh.CorruptNativeArtifact,
               nh.UnsupportedNativeISA, nh.NativeExecutionError]
    for i, a in enumerate(classes):
        for b in classes[i + 1:]:
            assert a is not b
        assert issubclass(a, nh.NativeHandleError)
        assert not issubclass(a, nh.UnsupportedInput)


# ---------------------------------------------------------------------------
# 6. missing artifact: never auto-builds; failure cached per workflow
# ---------------------------------------------------------------------------

def test_missing_artifact_never_builds_and_is_cached(nh, tmp_path):
    empty = tmp_path / 'none'          # does not even exist
    with pytest.raises(nh.MissingNativeArtifact):
        nh.prepare_native_handle(artifact_dir=empty)
    # auto must never invoke the expert builder
    with counting_spy(subprocess, 'run') as runs:
        with counting_spy(subprocess, 'Popen') as pops:
            with pytest.raises(nh.MissingNativeArtifact):
                nh.prepare_native_handle(artifact_dir=empty)
    assert runs == [] and pops == []
    # cached failure: the retry does ZERO filesystem work
    with IoSpy() as spy:
        with pytest.raises(nh.MissingNativeArtifact):
            nh.prepare_native_handle(artifact_dir=empty)
    assert spy.counts == {}, spy.counts
    # a new workflow generation retries (cache is per workflow)
    nh.new_workflow_generation()
    with IoSpy() as spy:
        with pytest.raises(nh.MissingNativeArtifact):
            nh.prepare_native_handle(artifact_dir=empty)
    assert spy.counts != {}            # IO was attempted again


def test_negative_cache_does_not_shadow_valid_artifact(nh, artifact_dir):
    """Failure cache is keyed per artifact dir: a failure for one dir cannot
    block a different (valid) dir, and never caches input validation."""
    empty = artifact_dir.parent / 'definitely-missing'
    with pytest.raises(nh.MissingNativeArtifact):
        nh.prepare_native_handle(artifact_dir=empty)
    good = nh.prepare_native_handle(artifact_dir=artifact_dir)
    assert good.execute(**_grid(3, 5, 19)) is not None


def test_prepare_does_not_mutate_lw_native_globals(nh, artifact_dir):
    import solweig_light.backends.native.lw_native as lw_native
    libs_before = dict(lw_native._LIBS)
    dir_before = lw_native._LIB_DIR
    handle = nh.prepare_native_handle(artifact_dir=artifact_dir)
    handle.execute(**_grid(3, 5, 20))
    assert dict(lw_native._LIBS) == libs_before
    assert lw_native._LIB_DIR == dir_before


def test_env_artifact_dir_resolution(nh, artifact_dir, monkeypatch):
    monkeypatch.setenv('SOLWEIG_LIGHT_NATIVE_CACHE', str(artifact_dir))
    handle = nh.prepare_native_handle()      # artifact_dir=None -> env
    assert handle.execute(**_grid(3, 5, 21)) is not None


# ---------------------------------------------------------------------------
# 7. bitwise parity with the current shipped path on the frozen grid
# ---------------------------------------------------------------------------

B_GRID = (1, 7, 8, 9, 11, 13)
P_GRID = (1, 2, 3, 5, 7, 11, 13, 153)


@pytest.mark.parametrize('surface_st', ('f64', 'f32'))
@pytest.mark.parametrize('P', P_GRID)
@pytest.mark.parametrize('B', B_GRID)
def test_handle_bitwise_equals_current_path_and_oracle(
        nh, artifact_dir, B, P, surface_st):
    from solweig_light.backends import native_lw
    args = adversarial_inputs(B, P, seed=1000 * B + P, surface_st=surface_st)
    expected = oracle.lw_primary_reference(surface_st=surface_st, **args)
    handle = nh.prepare_native_handle(artifact_dir=artifact_dir)
    via_handle = handle.execute(**args)
    via_current = native_lw.native_longwave_primary(**args)
    assert oracle.bitwise_equal(via_handle, expected), (B, P, surface_st)
    assert oracle.bitwise_equal(via_handle, via_current), (B, P, surface_st)


def test_handle_parity_strided_sky_columns(nh, artifact_dir):
    from solweig_light.backends import native_lw
    base = adversarial_inputs(5, 13, seed=77)
    table_down = np.zeros((13, 3), F32)
    table_down[:, 2] = base['sky_down']
    table_side = np.zeros((13, 3), F32)
    table_side[:, 2] = base['sky_side']
    strided = dict(base)
    strided['sky_down'] = table_down[:, 2]      # element stride 12 bytes
    strided['sky_side'] = table_side[:, 2]
    handle = nh.prepare_native_handle(artifact_dir=artifact_dir)
    assert oracle.bitwise_equal(handle.execute(**strided),
                                NUMBA_KERNEL(**base))
    assert oracle.bitwise_equal(handle.execute(**strided),
                                native_lw.native_longwave_primary(**strided))
    # one-element strided view with an arbitrary stride
    one = adversarial_inputs(2, 1, seed=78)
    col = np.zeros(7, F32)
    col[3] = one['sky_down'][0]
    one['sky_down'] = col[3:4:3]
    assert oracle.bitwise_equal(handle.execute(**one), NUMBA_KERNEL(**one))
    # negative-stride sky columns: the native paths agree with a flat copy
    rev = dict(base)
    rev['sky_down'] = base['sky_down'][::-1]    # view, stride -4
    flat = dict(base)
    flat['sky_down'] = np.ascontiguousarray(rev['sky_down'])
    assert oracle.bitwise_equal(handle.execute(**rev),
                                NUMBA_KERNEL(**flat))


def test_handle_parity_p609_and_b0(nh, artifact_dir):
    args = adversarial_inputs(3, 609, seed=75)
    handle = nh.prepare_native_handle(artifact_dir=artifact_dir)
    assert oracle.bitwise_equal(handle.execute(**args),
                                oracle.lw_primary_reference(**args))
    zero = adversarial_inputs(0, 3, seed=76)
    out = handle.execute(**zero)
    assert out.shape == (0, 7) and out.dtype == F32


def test_caller_out_written_bitwise(nh, artifact_dir):
    args = _grid(7, 13, 22)
    handle = nh.prepare_native_handle(artifact_dir=artifact_dir)
    out = np.full((7, 7), np.nan, F32)
    returned = handle.execute(out=out, **args)
    assert returned is out
    assert oracle.bitwise_equal(out, NUMBA_KERNEL(**args))


# ---------------------------------------------------------------------------
# 8. expert build route (explicit only) and atomic publication
# ---------------------------------------------------------------------------

def test_expert_build_publishes_stamp_last_and_atomically(nh, tmp_path,
                                                          monkeypatch):
    """Ordering proof without running ispc: dylib renames happen before the
    stamp rename; the stamp goes through temp+fsync+rename; no temp or
    workdir remnants survive in the published directory."""
    target = tmp_path / 'pub'
    target.mkdir()
    fake_dylib = b'\xca\xfe\xba\xbe not a real dylib'

    def fake_run(cmd, **kw):                     # stand-in for the compiler
        work = kw['cwd']
        for gang in (4, 8):
            (work / f'liblw_native_g{gang}.dylib').write_bytes(fake_dylib)

        class P:
            returncode = 0
            stdout = ''
            stderr = ''
        return P()

    renames = []
    real_replace = os.replace

    def spy_replace(a, b):
        renames.append(os.path.basename(str(b)))
        return real_replace(a, b)

    monkeypatch.setattr(subprocess, 'run', fake_run)
    monkeypatch.setattr(os, 'replace', spy_replace)
    stamp = nh.expert_build(target)

    assert stamp['kernel_sha256'] == nh._sha256_file(nh._PACKAGE_KERNEL)
    dylib_renames = [n for n in renames if n.endswith('.dylib')]
    assert len(dylib_renames) == 2
    assert renames.count('build_stamp.json') == 1
    assert renames.index('build_stamp.json') > max(
        i for i, n in enumerate(renames) if n.endswith('.dylib'))
    assert json.loads((target / 'build_stamp.json').read_text()) == stamp
    # no temp/workdir remnants in the published dir
    assert sorted(p.name for p in target.iterdir()) == [
        'build_stamp.json', 'liblw_native_g4.dylib', 'liblw_native_g8.dylib']


def test_expert_build_real_ispc_artifact_passes_prepare(nh, tmp_path):
    """The real expert route (skipped without ispc): a fresh build is a
    valid artifact for prepare and reproduces the frozen bits."""
    if not (shutil.which('ispc')
            or nh.Path('/opt/homebrew/bin/ispc').exists()):
        pytest.skip('ispc not available')
    target = tmp_path / 'built'
    stamp = nh.expert_build(target)
    assert stamp['kernel_sha256'] == nh._sha256_file(nh._PACKAGE_KERNEL)
    handle = nh.prepare_native_handle(artifact_dir=target)
    args = adversarial_inputs(9, 153, seed=71)
    assert oracle.bitwise_equal(handle.execute(**args),
                                oracle.lw_primary_reference(**args))


# ---------------------------------------------------------------------------
# module public surface
# ---------------------------------------------------------------------------

def test_public_surface(nh):
    for name in ('prepare_native_handle', 'expert_build',
                 'new_workflow_generation', 'current_workflow_generation',
                 'registry_snapshot', 'NativeHandle', 'NativeHandleSpec',
                 'UnsupportedInput', *TAXONOMY):
        assert hasattr(nh, name), name
