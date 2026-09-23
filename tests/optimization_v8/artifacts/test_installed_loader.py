#SOLWEIG-GPU: GPU-accelerated SOLWEIG model for urban thermal comfort simulation
#Copyright (C) 2022–2025 Harsh Kamath and Naveen Sudharsan
import pytest
pytest.skip(
    'archived with the N8 native row and qualification machinery '
    '(n8_32 selection closed N9 F3 NATIVE_LOSS; archived at N9 F4 closed_cpu_only): research copies preserved under '
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
"""N8-21 tests: trusted installed-artifact loader (BUILD_DESIGN section 8).

Mutation-based: every corruption class is created by mutating a COPY of
the real staged proof generation inside a fake installed package tree
(the staged original is never touched; a final integrity test asserts
that).  The three behavioral gates proved here:

* absent artifact -> QUIET decline (zero stdout/stderr, no subprocess, no
  write anywhere, developer builder never entered);
* present-but-corrupt artifact -> RECORDED decline on auto (still quiet,
  still no writes) + LOUD explicit CorruptNativeArtifact naming the
  packaging defect;
* qualified artifact on a qualified host -> verified load once per
  workflow generation (second load performs no re-hash).

Containment mutations (N8-30 review note N5) are asserted to be rejected
BEFORE the escaped file is opened or hashed.
"""
import hashlib
import importlib
import inspect
import json
import shutil
import sys
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pytest

import build_native
from solweig_light._native_dispatch import installed_loader
from solweig_light._native_dispatch import native_handle

REAL_PACKAGE = installed_loader.PACKAGE
REPO = Path(__file__).resolve().parents[3]
STAGE_DIR = REPO / 'experiments' / 'optimization_v8' / 'packaging' / 'stage'


def staged_copy_setup(ng: Path) -> None:
    """Generation-tree setup: a copy of the staged proof generation."""
    shutil.copytree(staged_gen_dir(), ng / staged_gen_dir().name)


def source_no_native_setup(ng: Path) -> None:
    """Generation-tree setup: the declared no-native fallback manifest,
    produced by the real N8-20 fallback builder (tmp-only writes)."""
    build_native.source_fallback_manifest(staging=ng, kernel=None,
                                          gen_prefix='lw')


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def ng_dir(root: Path) -> Path:
    return root / 'backends' / 'native_generated'


def only_generation(root: Path) -> Path:
    gens = [d for d in ng_dir(root).iterdir() if d.is_dir()]
    assert len(gens) == 1
    return gens[0]


def staged_gen_dir() -> Path:
    manifests = sorted(STAGE_DIR.glob('*/manifest.json'))
    if not manifests:
        pytest.skip('[no-staged-artifact] staged proof generation missing '
                    '(run build_native.py on the B7 kernel)')
    return manifests[-1].parent


def load_manifest(gen_dir: Path) -> dict:
    return json.loads((gen_dir / 'manifest.json').read_text())


def write_manifest(gen_dir: Path, manifest: dict) -> None:
    (gen_dir / 'manifest.json').write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + '\n')


def rederive(gen_dir: Path, mutate) -> Path:
    """Mutate the manifest and republish it CONSISTENTLY (recompute the
    content-derived generation name and rename the directory): this
    simulates a wheel legitimately built with the mutated metadata, so
    the corruption must be caught by the targeted gate rather than by
    the generation-name check."""
    manifest = load_manifest(gen_dir)
    mutate(manifest)
    manifest['generation'] = build_native.generation_name(manifest)
    new_dir = gen_dir.parent / manifest['generation']
    assert new_dir != gen_dir, 'mutation did not change the fingerprint'
    gen_dir.rename(new_dir)
    write_manifest(new_dir, manifest)
    return new_dir


def edit_in_place(gen_dir: Path, mutate) -> Path:
    """Mutate the manifest WITHOUT renaming: content no longer derives
    the directory name (the republish/content-drift mutation)."""
    manifest = load_manifest(gen_dir)
    mutate(manifest)
    write_manifest(gen_dir, manifest)
    return gen_dir


def flip_sha_field(entry: dict) -> None:
    sha = entry['sha256']
    entry['sha256'] = ('0' if sha[0] != '0' else '1') + sha[1:]


def flip_byte(path: Path, offset_from_end: int = 10) -> None:
    data = bytearray(path.read_bytes())
    data[len(data) - offset_from_end] ^= 0x01
    path.write_bytes(bytes(data))


@contextmanager
def hash_spy():
    """Count sha256 work inside build_native.verify_generation."""
    calls: list[Path] = []
    original = build_native._sha256_file

    def wrapper(path):
        calls.append(Path(path))
        return original(path)

    build_native._sha256_file = wrapper
    try:
        yield calls
    finally:
        build_native._sha256_file = original


@contextmanager
def builder_spy():
    """Prove the legacy developer builder is never entered: auto must
    never call native_lw's cache/build machinery nor expert_build."""
    import solweig_light.backends.native_lw as native_lw
    calls: list[str] = []
    saved = {}
    targets = (
        (native_lw, ('_cache_dir', '_kernel_digest', '_build_needed',
                     '_build', '_ensure_loaded', 'native_longwave_primary')),
        (native_handle, ('expert_build',)),
    )
    for module, names in targets:
        for name in names:
            original = getattr(module, name)
            saved[(module, name)] = original

            def recorder(*args, _orig=original, _label=f'{module.__name__}.'
                                               f'{name}', **kwargs):
                calls.append(_label)
                return _orig(*args, **kwargs)

            setattr(module, name, recorder)
    try:
        yield calls
    finally:
        for (module, name), original in saved.items():
            setattr(module, name, original)


class IoSpy:
    """Hardened IO purity spy (N8-30 review note N1: pathlib reads route
    through io.open, NOT builtins.open -- both are patched, plus the
    low-level os.open).  Records file opens (read vs write mode),
    filesystem mutations, subprocess spawns and network calls."""

    WRITE_OS = ('mkdir', 'makedirs', 'rename', 'replace', 'unlink',
                'remove', 'rmdir', 'symlink', 'link', 'truncate', 'mknod',
                'mkfifo', 'chmod')
    WRITE_SHUTIL = ('copyfile', 'copy', 'copy2', 'copytree', 'move',
                    'rmtree')
    WRITE_TEMPFILE = ('mkstemp', 'mkdtemp', 'NamedTemporaryFile',
                      'TemporaryDirectory')
    SUBPROCESS = ('run', 'call', 'check_call', 'check_output', 'Popen',
                  'getoutput', 'getstatusoutput')
    OS_SPAWN = ('system', 'popen', 'posix_spawn', 'posix_spawnp')

    def __init__(self):
        self.write_ops: list[tuple] = []
        self.read_opens: list[str] = []
        self.subprocess_ops: list[tuple] = []
        self.net_ops: list[tuple] = []
        self._saved: dict[tuple, object] = {}

    def _patch(self, module, name, wrapper):
        self._saved[(module, name)] = getattr(module, name)
        setattr(module, name, wrapper)

    def __enter__(self):
        import builtins
        import io as io_module
        import os as os_module
        import shutil as shutil_module
        import socket as socket_module
        import subprocess as subprocess_module
        import tempfile as tempfile_module

        def wrap_open(original):
            def open_(file, mode='r', *args, **kwargs):
                path = str(file)
                if any(flag in mode for flag in 'wax+'):
                    self.write_ops.append(('open', path, mode))
                else:
                    self.read_opens.append(path)
                return original(file, mode, *args, **kwargs)
            return open_

        self._patch(builtins, 'open', wrap_open(builtins.open))
        self._patch(io_module, 'open', wrap_open(io_module.open))

        def wrap_os_open(original):
            def os_open(path, flags, *args, **kwargs):
                write_flags = (os_module.O_WRONLY | os_module.O_RDWR
                               | os_module.O_CREAT | os_module.O_TRUNC
                               | os_module.O_APPEND)
                if flags & write_flags:
                    self.write_ops.append(('os.open', str(path), flags))
                return original(path, flags, *args, **kwargs)
            return os_open

        self._patch(os_module, 'open', wrap_os_open(os_module.open))

        def wrap_write(module, name):
            original = getattr(module, name)

            def record(*args, **kwargs):
                self.write_ops.append((name,) + tuple(map(str, args[:1])))
                return original(*args, **kwargs)
            return record

        for name in self.WRITE_OS:
            self._patch(os_module, name, wrap_write(os_module, name))
        for name in self.WRITE_SHUTIL:
            self._patch(shutil_module, name, wrap_write(
                shutil_module, name))
        for name in self.WRITE_TEMPFILE:
            self._patch(tempfile_module, name, wrap_write(
                tempfile_module, name))

        def wrap_spawn(module, name, sink):
            original = getattr(module, name)

            def record(*args, **kwargs):
                sink.append((name, str(args[:1])))
                return original(*args, **kwargs)
            return record

        for name in self.SUBPROCESS:
            self._patch(subprocess_module, name, wrap_spawn(
                subprocess_module, name, self.subprocess_ops))
        for name in self.OS_SPAWN:
            self._patch(os_module, name, wrap_spawn(
                os_module, name, self.subprocess_ops))
        self._patch(socket_module, 'socket', wrap_spawn(
            socket_module, 'socket', self.net_ops))
        self._patch(socket_module, 'create_connection', wrap_spawn(
            socket_module, 'create_connection', self.net_ops))
        return self

    def __exit__(self, *exc):
        for (module, name), original in self._saved.items():
            setattr(module, name, original)
        return False

    def assert_pure_load(self):
        assert self.write_ops == []      # no writes to HOME/temp/cache/etc
        assert self.subprocess_ops == []  # no compiler, no tool, no shell
        assert self.net_ops == []         # no network


def assert_quiet_decline(capfd, status_prefix, *keywords):
    """Auto declined, nothing printed, reason recorded privately with the
    expected status and keywords."""
    reasons = installed_loader.decline_reasons()
    matching = [r for r in reasons if r.startswith(f'[{status_prefix}]')]
    assert matching, f'no [{status_prefix}] decline recorded: {reasons}'
    for keyword in keywords:
        assert keyword in matching[-1], (keyword, matching[-1])
    captured = capfd.readouterr()
    assert captured.out == ''
    assert captured.err == ''


# ---------------------------------------------------------------------------
# absent artifact: quiet decline, no builder, no env, no side effects
# ---------------------------------------------------------------------------


def test_auto_absent_on_real_package_is_fully_quiet(capfd):
    with builder_spy() as builder_calls, IoSpy() as spy:
        handle = installed_loader.auto_load(REAL_PACKAGE)
    assert handle is None
    assert_quiet_decline(capfd, 'declined-absent', 'native_generated')
    assert builder_calls == []  # auto NEVER enters the developer builder
    spy.assert_pure_load()


def test_loader_source_never_reads_environment():
    assert 'os.environ' not in inspect.getsource(installed_loader)


def test_auto_absent_ignores_dev_cache_env(capfd, tmp_path, monkeypatch):
    """A populated SOLWEIG_LIGHT_NATIVE_CACHE must not be picked up by
    auto: the dev cache is expert opt-in, resolution is package-only."""
    staged = staged_gen_dir() / 'liblw_native_g8.dylib'
    if staged.is_file():
        shutil.copy2(staged, tmp_path / 'liblw_native_g8.dylib')
        (tmp_path / 'build_stamp.json').write_text(json.dumps(
            {'kernel_sha256': '0' * 64, 'ispc': 'x',
             'built_utc': '2026-01-01T00:00:00Z'}))
    monkeypatch.setenv('SOLWEIG_LIGHT_NATIVE_CACHE', str(tmp_path))
    with builder_spy() as builder_calls, IoSpy() as spy:
        assert installed_loader.auto_load(REAL_PACKAGE) is None
    assert builder_calls == []
    spy.assert_pure_load()
    assert_quiet_decline(capfd, 'declined-absent', 'native_generated')


def test_explicit_absent_fails_loudly():
    with pytest.raises(installed_loader.MissingNativeArtifact,
                       match='no qualified native artifact in this '
                             'installation'):
        installed_loader.load_explicit(REAL_PACKAGE)


def test_source_no_native_manifest_is_quiet_absent(capfd, make_package):
    name, _root = make_package(source_no_native_setup)
    with builder_spy() as builder_calls, IoSpy() as spy:
        assert installed_loader.auto_load(name) is None
    assert builder_calls == []
    spy.assert_pure_load()
    assert_quiet_decline(capfd, 'declined-absent', 'source-no-native')
    with pytest.raises(installed_loader.MissingNativeArtifact):
        installed_loader.load_explicit(name)


def test_absent_state_cached_per_workflow_generation(make_package,
                                                     monkeypatch):
    name, _root = make_package()  # package exists, no native_generated
    calls = []
    original = installed_loader._resolve_package_root

    def counting(package):
        calls.append(package)
        return original(package)

    monkeypatch.setattr(installed_loader, '_resolve_package_root', counting)
    assert installed_loader.auto_load(name) is None
    assert installed_loader.auto_load(name) is None
    assert calls == [name]  # second call hit the negative cache
    native_handle.new_workflow_generation('w-retry')
    assert installed_loader.auto_load(name) is None
    assert calls == [name, name]  # a new generation re-resolves


# ---------------------------------------------------------------------------
# qualified generation: verified load of the real staged artifact
# ---------------------------------------------------------------------------


@pytest.fixture()
def staged_pkg(make_package, staged_generation):
    name, root = make_package(staged_copy_setup)
    return name, root, staged_generation


def test_staged_generation_loads(staged_pkg):
    name, _root, staged = staged_pkg
    handle = installed_loader.auto_load(name)
    assert handle is not None
    manifest = json.loads((staged / 'manifest.json').read_text())
    identity = handle.identity()
    assert identity['generation'] == manifest['generation']
    assert identity['abi_version'] == build_native.ABI_VERSION
    assert identity['kernel_sha256'] == manifest['kernel']['sha256']
    assert identity['math_profile'] == manifest['math_profile']['id']
    assert identity['gang'] == 8
    assert identity['scalar_entry_map'] == {'f32': 'lw_primary_f32',
                                            'f64': 'lw_primary_f64'}
    snapshot = installed_loader.registry_snapshot()
    assert snapshot and all(v.startswith('loaded:')
                            for v in snapshot.values())


def test_staged_generation_executes(staged_pkg):
    """End-to-end smoke: the CDLL admitted by this loader's gate actually
    executes through the reviewed N8-10 handle (bitwise parity of the
    execute surface itself is N8-10's proven scope)."""
    name, _root, _staged = staged_pkg
    handle = installed_loader.auto_load(name)
    rng = np.random.default_rng(11)
    b, p = 3, 5
    sh = (rng.standard_normal((b, p)) * .5).astype(np.float32)
    vs = (rng.standard_normal((b, p)) * .5).astype(np.float32)
    vb = (rng.standard_normal((b, p)) * .5).astype(np.float32)
    sun = rng.random((b, p)) > .5
    shade = rng.random((b, p)) > .5
    solid = rng.standard_normal(p).astype(np.float32)
    sine = rng.standard_normal(p).astype(np.float32)
    cosine = rng.standard_normal(p).astype(np.float32)
    directions = rng.standard_normal((p, 4)).astype(np.float32)
    gate = rng.random((p, 4)) > .5
    solar_gate = np.ones(p, dtype=bool)
    sky_down = rng.standard_normal(p).astype(np.float32)
    sky_side = rng.standard_normal(p).astype(np.float32)
    lup = rng.standard_normal(b).astype(np.float32)
    out = handle.execute(sh, vs, vb, sun, shade, solid, sine, cosine,
                         directions, gate, solar_gate, sky_down, sky_side,
                         surface_sun=0.93, surface_sh=0.93, lup=lup,
                         reflection_factor=np.float32(0.03))
    assert out.shape == (b, 7) and out.dtype == np.float32
    assert np.isfinite(out).all()


def test_explicit_load_returns_verified_handle(staged_pkg):
    name, _root, _staged = staged_pkg
    assert installed_loader.load_explicit(name) is \
        installed_loader.auto_load(name)


def test_second_load_does_not_rehash(staged_pkg):
    name, _root, _staged = staged_pkg
    with hash_spy() as first:
        handle = installed_loader.auto_load(name)
    assert first  # content verification genuinely hashed
    with hash_spy() as second:
        again = installed_loader.auto_load(name)
    assert again is handle
    assert second == []  # registry hit: no re-hash, no re-dlopen


def test_new_workflow_generation_reverifies(staged_pkg):
    name, _root, _staged = staged_pkg
    with hash_spy() as first:
        handle = installed_loader.auto_load(name)
    native_handle.new_workflow_generation('w-second')
    with hash_spy() as second:
        fresh = installed_loader.auto_load(name)
    assert fresh is not handle
    assert second  # a new generation re-verifies content
    assert handle.identity()['workflow_generation'] != \
        fresh.identity()['workflow_generation']


def test_staged_generation_load_is_pure(capfd, staged_pkg):
    name, _root, _staged = staged_pkg
    with builder_spy() as builder_calls, IoSpy() as spy:
        installed_loader.auto_load(name)
    assert builder_calls == []
    spy.assert_pure_load()
    captured = capfd.readouterr()
    assert captured.out == '' and captured.err == ''


# ---------------------------------------------------------------------------
# present-but-corrupt: recorded decline on auto, loud on explicit
# ---------------------------------------------------------------------------


def _truncate_dylib_and_fix_manifest(gen: Path) -> Path:
    """Truncate the dylib AND 'fix' the manifest to match (hash and size
    of the truncated bytes, consistently re-derived name): only the
    Mach-O structural walk can still catch this corruption."""
    dylib = gen / 'liblw_native_g8.dylib'
    dylib.write_bytes(dylib.read_bytes()[:100])

    def mutate(m):
        m['artifacts'][0]['sha256'] = build_native._sha256_file(dylib)
        m['artifacts'][0]['bytes'] = 100

    return rederive(gen, mutate)


CORRUPT_CASES = [
    pytest.param(lambda gen: (gen / 'liblw_native_g8.dylib').write_bytes(
        (gen / 'liblw_native_g8.dylib').read_bytes()[:100]),
        'content verification failed', id='truncated-dylib'),
    pytest.param(lambda gen: flip_byte(gen / 'liblw_native_g8.dylib'),
                 'content verification failed', id='single-bitflip-dylib'),
    pytest.param(lambda gen: rederive(
        gen, lambda m: flip_sha_field(m['artifacts'][0])),
        'hash mismatch', id='manifest-sha-mismatch'),
    pytest.param(lambda gen: edit_in_place(gen, lambda m: m.pop(
        'math_profile')), 'schema violations', id='missing-manifest-field'),
    pytest.param(lambda gen: edit_in_place(gen, lambda m: m['artifacts'][0]
                                           .pop('bytes')),
                 'schema violations', id='missing-artifact-bytes-field'),
    pytest.param(_truncate_dylib_and_fix_manifest,
                 'load commands extend past end of file',
                 id='truncated-dylib-fixed-manifest-macho-catch'),
    pytest.param(lambda gen: edit_in_place(gen, lambda m: m['kernel']
                                           .__setitem__('sha256', 'e' * 64)),
                 'generation name mismatch', id='content-drift-no-rename'),
    pytest.param(lambda gen: gen.rename(gen.parent / ('lw-g8-' + '0' * 16)),
                 'generation name mismatch', id='dir-renamed-forgery'),
    pytest.param(lambda gen: rederive(gen, lambda m: m['abi'].__setitem__(
        'abi_version', 2)), 'abi_version', id='abi-version-mismatch'),
    pytest.param(lambda gen: rederive(gen, lambda m: m['abi'].__setitem__(
        'wrapper_abi_layout_version', 'lw-region-abi-2')),
        'wrapper ABI layout', id='wrapper-abi-mismatch'),
    pytest.param(lambda gen: rederive(gen, lambda m: m['math_profile']
                                      .update({'id': 'lw-primary-fast',
                                               'fast_math': True})),
        'outside the loader qualified allow-list', id='math-profile-fast'),
    pytest.param(lambda gen: rederive(gen, lambda m: m.__setitem__(
        'build_mode', 'mystery-mode')), 'unknown build_mode',
        id='unknown-build-mode'),
    pytest.param(lambda gen: rederive(gen, lambda m: m['build']
                                      .update({'target': 'avx2-i32x8'})),
        'outside the qualified targets', id='unqualified-target-in-wheel'),
    # n8-30 review note N1 regressions: the reused build_native validator
    # has NON-TYPED failure surfaces.  Each exotic state below used to crash
    # auto_load with a raw exception; it must instead take the same recorded
    # declined-corrupt path (fail closed), with the failure class named.
    pytest.param(lambda gen: (gen / 'liblw_native_g8.dylib').chmod(0o000),
                 'PermissionError',
                 id='unreadable-listed-member-permissionerror'),
    pytest.param(lambda gen: edit_in_place(gen, lambda m: m.__setitem__(
        'artifacts', [m['artifacts'][0]['path']])),
        'AttributeError', id='artifacts-entries-are-strings-attributeerror'),
    pytest.param(lambda gen: rederive(gen, lambda m: m['fma_audit'].pop(
        'asm_sha256')), 'KeyError', id='fma-audit-without-asm-sha-keyerror'),
]


@pytest.mark.parametrize('mutate,keyword', CORRUPT_CASES)
def test_corrupt_artifact_recorded_decline_and_loud_explicit(
        capfd, make_package, mutate, keyword):
    name, root = make_package(staged_copy_setup)
    mutate(only_generation(root))
    with builder_spy() as builder_calls, IoSpy() as spy:
        assert installed_loader.auto_load(name) is None
    assert_quiet_decline(capfd, 'declined-corrupt', keyword)
    assert builder_calls == []  # never a hidden rebuild
    spy.assert_pure_load()
    with pytest.raises(installed_loader.CorruptNativeArtifact,
                       match='packaging defect') as excinfo:
        installed_loader.load_explicit(name)
    assert keyword in str(excinfo.value)


def test_corrupt_reason_matches_recorded_decline(capfd, make_package):
    name, root = make_package(staged_copy_setup)
    flip_byte(only_generation(root) / 'liblw_native_g8.dylib')
    outcome = installed_loader.attempt_load(name)
    assert outcome.status == 'declined-corrupt'
    recorded = [r for r in installed_loader.decline_reasons()
                if r.startswith('[declined-corrupt]')][-1]
    assert outcome.reason in recorded  # the log line carries the reason
    with pytest.raises(installed_loader.CorruptNativeArtifact) as excinfo:
        installed_loader.load_explicit(name)
    assert 'packaging defect' in str(excinfo.value)
    assert outcome.reason[:80] in str(excinfo.value)


def test_corrupt_decline_cached_until_new_generation(capfd, make_package,
                                                     monkeypatch):
    name, root = make_package(staged_copy_setup)
    flip_byte(only_generation(root) / 'liblw_native_g8.dylib')
    calls = []
    original = installed_loader._resolve_package_root

    def counting(package):
        calls.append(package)
        return original(package)

    monkeypatch.setattr(installed_loader, '_resolve_package_root', counting)
    installed_loader.auto_load(name)
    installed_loader.auto_load(name)
    assert calls == [name]  # decline is cached per workflow generation
    native_handle.new_workflow_generation('w-after-repair')
    shutil.rmtree(ng_dir(root))
    assert installed_loader.auto_load(name) is None  # now plain absent
    assert calls == [name, name]


def test_in_lock_untyped_validator_failure_declines_not_crashes(
        capfd, make_package, monkeypatch):
    """n8-30 delta note N6: the in-lock untyped-failure clause (the
    mid-load external-mutation surface folded into N1) is deterministically
    testable at the _verified_manifest seam, per the reviewer's delta
    section 9 probe -- no verify->dlopen race required."""
    name, root = make_package(staged_copy_setup)  # valid: all gates pass
    def mid_load_swap(_outcome):
        raise KeyError('asm_sha256')  # manifest swapped between gate & load
    monkeypatch.setattr(installed_loader, '_verified_manifest', mid_load_swap)
    with builder_spy() as builder_calls, IoSpy() as spy:
        assert installed_loader.auto_load(name) is None
    assert_quiet_decline(capfd, 'declined-corrupt', 'KeyError')
    assert builder_calls == []
    spy.assert_pure_load()
    with pytest.raises(installed_loader.CorruptNativeArtifact,
                       match='packaging defect') as excinfo:
        installed_loader.load_explicit(name)
    assert 'KeyError' in str(excinfo.value)


# ---------------------------------------------------------------------------
# path containment (N8-30 note N5): rejected BEFORE open/hash
# ---------------------------------------------------------------------------


def test_manifest_dotdot_path_rejected_before_open(capfd, make_package,
                                                   tmp_path):
    name, root = make_package(staged_copy_setup)
    gen = only_generation(root)
    escaped = tmp_path / 'escaped.dylib'
    shutil.copy2(gen / 'liblw_native_g8.dylib', escaped)
    edit_in_place(gen, lambda m: m['artifacts'][0].__setitem__(
        'path', '../escaped.dylib'))
    with IoSpy() as spy, hash_spy() as hashed:
        assert installed_loader.auto_load(name) is None
    assert_quiet_decline(capfd, 'declined-corrupt', 'containment violation')
    assert str(escaped.resolve()) not in spy.read_opens
    assert escaped.resolve() not in hashed
    with pytest.raises(installed_loader.CorruptNativeArtifact,
                       match='containment'):
        installed_loader.load_explicit(name)


def test_manifest_absolute_path_rejected(capfd, make_package, tmp_path):
    name, root = make_package(staged_copy_setup)
    gen = only_generation(root)
    escaped = tmp_path / 'absolute.dylib'
    shutil.copy2(gen / 'liblw_native_g8.dylib', escaped)
    edit_in_place(gen, lambda m: m['artifacts'][0].__setitem__(
        'path', str(escaped)))
    with IoSpy() as spy, hash_spy() as hashed:
        assert installed_loader.auto_load(name) is None
    assert_quiet_decline(capfd, 'declined-corrupt', 'absolute path')
    assert str(escaped.resolve()) not in spy.read_opens
    assert escaped.resolve() not in hashed


def test_manifest_nul_and_traversal_names_rejected(make_package):
    name, root = make_package(staged_copy_setup)
    gen = only_generation(root)
    for bad in ('a/../b', './x', 'a\0b', '..'):
        edit_in_place(gen, lambda m, bad=bad: m['artifacts'][0]
                      .__setitem__('path', bad))
        installed_loader.reset_for_tests()
        outcome = installed_loader.attempt_load(name)
        assert outcome.status == 'declined-corrupt', (bad, outcome.reason)


def test_generation_dir_symlink_escape_rejected(capfd, make_package,
                                                tmp_path):
    name, root = make_package()  # empty native_generated
    outside = tmp_path / 'outside'
    shutil.copytree(staged_gen_dir(), outside / staged_gen_dir().name)
    (ng_dir(root) / staged_gen_dir().name).symlink_to(
        outside / staged_gen_dir().name, target_is_directory=True)
    with IoSpy() as spy:
        assert installed_loader.auto_load(name) is None
    assert_quiet_decline(capfd, 'declined-corrupt',
                         'outside the installed package')
    outside_dylib = str((outside / staged_gen_dir().name
                         / 'liblw_native_g8.dylib').resolve())
    assert outside_dylib not in spy.read_opens


def test_member_symlink_escape_rejected_before_hash(capfd, make_package,
                                                    tmp_path):
    name, root = make_package(staged_copy_setup)
    gen = only_generation(root)
    outside = tmp_path / 'member-outside'
    outside.mkdir()
    outside_dylib = outside / 'liblw_native_g8.dylib'
    shutil.copy2(gen / 'liblw_native_g8.dylib', outside_dylib)
    (gen / 'liblw_native_g8.dylib').unlink()
    (gen / 'liblw_native_g8.dylib').symlink_to(outside_dylib)
    with IoSpy() as spy, hash_spy() as hashed:
        assert installed_loader.auto_load(name) is None
    assert_quiet_decline(capfd, 'declined-corrupt', 'symlink escape')
    assert str(outside_dylib.resolve()) not in spy.read_opens
    assert outside_dylib.resolve() not in hashed


def test_native_root_symlink_escape_rejected(capfd, make_package,
                                             tmp_path):
    name, root = make_package()  # creates a real native_generated dir
    outside = tmp_path / 'root-outside'
    shutil.copytree(staged_gen_dir(), outside / staged_gen_dir().name)
    real_ng = ng_dir(root)
    real_ng.rmdir()
    real_ng.symlink_to(outside, target_is_directory=True)
    assert installed_loader.auto_load(name) is None
    assert_quiet_decline(capfd, 'declined-corrupt',
                         'outside the installed package root')


def test_generation_inside_dev_cache_root_rejected(tmp_path, monkeypatch):
    """Even a fully valid generation is rejected when the package itself
    resolves inside the legacy developer cache (the packaged loader
    never reads that tree).  The dev-cache root is faked via monkeypatch
    so the test never touches the real user cache."""
    monkeypatch.setattr(installed_loader, '_dev_cache_root',
                        lambda: tmp_path / 'devcache')
    pkg_parent = tmp_path / 'devcache' / 'native'
    name = 'fake_native_pkg_devcache'
    root = pkg_parent / name
    ng = root / 'backends' / 'native_generated'
    shutil.copytree(staged_gen_dir(), ng / staged_gen_dir().name)
    (root / '__init__.py').write_text('')
    sys.path.insert(0, str(pkg_parent))
    try:
        importlib.import_module(name)
        outcome = installed_loader.attempt_load(name)
        assert outcome.status == 'declined-corrupt'
        assert 'developer cache' in outcome.reason
        assert outcome.handle is None
    finally:
        sys.modules.pop(name, None)
        sys.path.remove(str(pkg_parent))


# ---------------------------------------------------------------------------
# unqualified host: ordinary quiet decline + loud explicit capability gap
# ---------------------------------------------------------------------------


def test_wrong_arch_manifest_declines_quietly(capfd, make_package):
    name, root = make_package(staged_copy_setup)

    def to_x86(m):
        m['platform']['arch'] = 'x86_64'
        m['platform']['requirements'] = ['cpu-feature:avx2']

    rederive(only_generation(root), to_x86)
    with builder_spy() as builder_calls:
        assert installed_loader.auto_load(name) is None
    assert builder_calls == []
    assert_quiet_decline(capfd, 'declined-unqualified', 'arm64')
    with pytest.raises(installed_loader.UnsupportedNativeISA,
                       match='outside the qualified arm64'):
        installed_loader.load_explicit(name)


def test_wrong_os_manifest_declines_quietly(capfd, make_package):
    name, root = make_package(staged_copy_setup)
    rederive(only_generation(root), lambda m: m['platform'].__setitem__(
        'os', 'linux'))
    assert installed_loader.auto_load(name) is None
    assert_quiet_decline(capfd, 'declined-unqualified', 'artifact os')
    with pytest.raises(installed_loader.UnsupportedNativeISA,
                       match='artifact os'):
        installed_loader.load_explicit(name)


def test_min_os_above_host_declines_quietly(capfd, make_package):
    name, root = make_package(staged_copy_setup)
    rederive(only_generation(root), lambda m: m['platform'].__setitem__(
        'os_min_version', '99.0'))
    assert installed_loader.auto_load(name) is None
    assert_quiet_decline(capfd, 'declined-unqualified', 'older than')
    with pytest.raises(installed_loader.UnsupportedNativeISA,
                       match='older than'):
        installed_loader.load_explicit(name)


def test_missing_neon_feature_declines_quietly(capfd, make_package,
                                               monkeypatch):
    name, root = make_package(staged_copy_setup)
    monkeypatch.setattr(installed_loader, '_host_neon', lambda: 0)
    assert installed_loader.auto_load(name) is None
    assert_quiet_decline(capfd, 'declined-unqualified', 'NEON unavailable')
    with pytest.raises(installed_loader.UnsupportedNativeISA,
                       match='NEON unavailable'):
        installed_loader.load_explicit(name)


def test_unrecognized_requirement_fails_closed(capfd, make_package):
    name, root = make_package(staged_copy_setup)
    rederive(only_generation(root), lambda m: m['platform'].__setitem__(
        'requirements', ['cpu-feature:sve2']))
    assert installed_loader.auto_load(name) is None
    assert_quiet_decline(capfd, 'declined-unqualified', 'not recognized')
    with pytest.raises(installed_loader.UnsupportedNativeISA,
                       match='not recognized'):
        installed_loader.load_explicit(name)


# ---------------------------------------------------------------------------
# multi-candidate generations
# ---------------------------------------------------------------------------


def test_corrupt_sibling_recorded_but_qualified_sibling_loads(
        capfd, make_package):
    name, root = make_package(staged_copy_setup)
    good = only_generation(root)
    sibling = ng_dir(root) / 'sibling'
    shutil.copytree(good, sibling)
    rederive(sibling, lambda m: flip_sha_field(m['artifacts'][0]))
    with builder_spy() as builder_calls:
        handle = installed_loader.auto_load(name)
    assert handle is not None
    assert handle.generation == load_manifest(good)['generation']
    reasons = installed_loader.decline_reasons()
    assert any(r.startswith('[declined-corrupt]') and 'hash mismatch' in r
               for r in reasons)
    assert builder_calls == []
    captured = capfd.readouterr()
    assert captured.out == '' and captured.err == ''


def test_all_candidates_corrupt_fails_explicit_loudly(make_package):
    name, root = make_package(staged_copy_setup)
    flip_byte(only_generation(root) / 'liblw_native_g8.dylib')
    assert installed_loader.auto_load(name) is None
    with pytest.raises(installed_loader.CorruptNativeArtifact,
                       match='packaging defect'):
        installed_loader.load_explicit(name)


# ---------------------------------------------------------------------------
# staged-original integrity (the suite only ever mutated copies)
# ---------------------------------------------------------------------------


def test_staged_original_never_mutated(staged_generation, staged_integrity):
    for name, digest in staged_integrity.items():
        current = hashlib.sha256(
            (staged_generation / name).read_bytes()).hexdigest()
        assert current == digest, f'staged fixture {name} was mutated'
