"""Call-through census probe for C6-02 (instrumentation only, never a mock).

Every wrapper calls through to the original real producer and records
fingerprints/durations without altering arguments, return values, threading,
or caching behavior.  Events are appended, one JSON object per line, to a
per-process file under SOLWEIG_CENSUS_RECORD_DIR.

The census test process installs the probe directly (install/rearm with
role='parent').  Tile worker children spawned by the public workflow
(``execute_tiles``) are instrumented through a generated ``sitecustomize``
module on their inherited PYTHONPATH: it calls autostart(), and a meta-path
finder patches each target module immediately after its normal execution, so
the real workflow code is imported and wrapped unchanged.
"""
from __future__ import annotations

import hashlib
import importlib.abc
import json
import os
import sys
import time

TARGET_MODULES = (
    'solweig_light.cache.geometry',
    'solweig_light.geometry.svf',
    'solweig_light.pipeline',
    'solweig_light.geometry.service',
)

# The nineteen producer results in the exact tuple order that
# geometry/svf.py:153-154 returns; geometry/service.py RESULT_NAMES and
# pipeline.py SVF_NAMES are the identical sequence.
RESULT_NAMES = ('svf svfaveg svfE svfEaveg svfEveg svfN svfNaveg svfNveg svfS '
                'svfSaveg svfSveg svfveg svfW svfWaveg svfWveg vegshmat '
                'vbshvegshmat shmat svftotal').split()
PRODUCER_PARAMS = ('patch_option', 'amaxvalue', 'a', 'vegdem', 'vegdem2', 'bush', 'scale')

_RECORD_DIR = None
_ROLE = 'unmarked'
_HEADER_EMITTED = False
_PATCHED_MODULES = set()
_WRAPPERS = {}
_ORIGINALS = {}
_PACKAGE_FILE = None
_FINDER = None


def _emit(event):
    if _RECORD_DIR is None:
        return
    try:
        record = dict(event)
        record.setdefault('role', _ROLE)
        record['pid'] = os.getpid()
        record['ppid'] = os.getppid()
        record['wall_time'] = time.time()
        if not _HEADER_EMITTED:
            record['process'] = {'executable': sys.executable, 'cwd': os.getcwd(),
                                 'solweig_file': _PACKAGE_FILE,
                                 'thread_env': {name: os.environ.get(name)
                                                for name in ('NUMBA_NUM_THREADS', 'OMP_NUM_THREADS',
                                                             'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS')},
                                 'pythonpath': os.environ.get('PYTHONPATH', '')}
        path = os.path.join(_RECORD_DIR, f'{_ROLE}-{os.getpid()}.jsonl')
        if not _HEADER_EMITTED:
            globals()['_HEADER_EMITTED'] = True  # process block only on the first record per rearm
        with open(path, 'a', encoding='utf8') as stream:
            stream.write(json.dumps(record, sort_keys=True, default=repr) + '\n')
    except Exception:
        pass


def _attribute_call():
    """Classify the in-package caller frame; read-only stack inspection."""
    frame = sys._getframe(2)
    while frame is not None:
        name = frame.f_code.co_filename.replace(os.sep, '/')
        if '/solweig_light/geometry/service.py' in name:
            return 'standalone', 'geometry/service.py:%d' % frame.f_code.co_firstlineno
        if '/solweig_light/pipeline.py' in name:
            return 'pipeline', 'pipeline.py:%d' % frame.f_code.co_firstlineno
        frame = frame.f_back
    return 'unknown', None


def _fp_scalar(value):
    if isinstance(value, bool) or value is None:
        return {'type': type(value).__name__, 'value': value}
    if isinstance(value, (int, float)):
        return {'type': type(value).__name__, 'hex': float(value).hex()}
    numpy = sys.modules.get('numpy')
    if numpy is not None and isinstance(value, numpy.generic):
        return {'type': str(type(value).__name__), 'hex': float(value).hex()}
    return {'type': type(value).__name__, 'repr': repr(value)}


def _fp_array(value):
    import numpy as np
    array = np.ascontiguousarray(np.asarray(value))
    return {'dtype': array.dtype.str, 'shape': list(array.shape),
            'sha256': hashlib.sha256(array.tobytes(order='C')).hexdigest()}


def _fp_field(value):
    """Fingerprint one producer result without mutating it."""
    import numpy as np
    if isinstance(value, np.ndarray):
        return {'representation': 'ndarray', **_fp_array(value)}
    if hasattr(value, 'to_dense'):
        return {'representation': 'packed-to-dense', **_fp_array(value.to_dense())}
    return {'representation': 'other', 'repr': repr(value)}


def _wrap_svf(module, original):
    def wrapper(*args, **kwargs):
        route, caller = _attribute_call()
        inputs = None
        try:
            inputs = {name: (_fp_scalar(value) if index in (0, 1, 6) else _fp_array(value))
                      for index, (name, value) in enumerate(zip(PRODUCER_PARAMS, args))}
            inputs['extra_positional'] = [repr(value) for value in args[len(PRODUCER_PARAMS):]]
            inputs['kwargs'] = {key: repr(value) for key, value in sorted(kwargs.items())}
        except Exception as error:
            _emit({'event': 'census_error', 'where': 'svf-inputs', 'error': repr(error)})
        start = time.perf_counter()
        result = original(*args, **kwargs)
        duration = time.perf_counter() - start
        try:
            outputs = None
            if isinstance(result, tuple) and len(result) == len(RESULT_NAMES):
                outputs = {name: _fp_field(value) for name, value in zip(RESULT_NAMES, result)}
            elif isinstance(result, dict):
                outputs = {name: _fp_field(value) for name, value in sorted(result.items())}
            _emit({'event': 'svf_call', 'route': route, 'caller': caller,
                   'inputs': inputs, 'outputs': outputs, 'duration_s': duration})
        except Exception as error:
            _emit({'event': 'census_error', 'where': 'svf-outputs', 'error': repr(error),
                   'duration_s': duration, 'route': route, 'caller': caller})
        return result
    return wrapper


def _wrap_export(module, original):
    def wrapper(*args, **kwargs):
        route, caller = _attribute_call()
        start = time.perf_counter()
        try:
            return original(*args, **kwargs)
        finally:
            _emit({'event': 'export', 'route': route, 'caller': caller,
                   'duration_s': time.perf_counter() - start,
                   'args_repr': [repr(value) for value in args[:2]]})
    return wrapper


def _wrap_key_for(store_module, original):
    def wrapper(self, identity):
        route, caller = _attribute_call()
        try:
            copied = json.loads(store_module.canonical_json(identity))
        except Exception as error:
            copied = {'census_error': repr(error)}
        key = original(self, identity)
        _emit({'event': 'key_for', 'route': route, 'caller': caller,
               'identity': copied, 'key': key, 'model_version': self.model_version})
        return key
    return wrapper


def _wrap_get_or_create(store_module, original):
    def wrapper(self, identity, producer):
        route, caller = _attribute_call()
        try:
            copied = json.loads(store_module.canonical_json(identity))
        except Exception as error:
            copied = {'census_error': repr(error)}
        state = {'calls': 0, 'producer_s': 0.0}

        def counted():
            state['calls'] += 1
            start = time.perf_counter()
            try:
                return producer()
            finally:
                state['producer_s'] += time.perf_counter() - start

        start = time.perf_counter()
        try:
            handle = original(self, identity, counted)
        except BaseException as error:
            _emit({'event': 'get_or_create', 'route': route, 'caller': caller,
                   'identity': copied, 'error': type(error).__name__,
                   'cache_root': str(self.root), 'producer_calls': state['calls'],
                   'producer_duration_s': state['producer_s'],
                   'duration_s': time.perf_counter() - start})
            raise
        _emit({'event': 'get_or_create', 'route': route, 'caller': caller,
               'identity': copied, 'key': getattr(handle, 'key', None),
               'hit': bool(getattr(handle, 'hit', False)), 'cache_root': str(self.root),
               'producer_calls': state['calls'], 'producer_duration_s': state['producer_s'],
               'duration_s': time.perf_counter() - start})
        return handle
    return wrapper


def _fix_aliases():
    original = _ORIGINALS.get('svf_calculator_compact')
    wrapper = _WRAPPERS.get('svf_calculator_compact')
    if original is None or wrapper is None:
        return
    for module_name, attribute in (('solweig_light.pipeline', 'svf_calculator'),
                                   ('solweig_light.geometry.service', 'svf_calculator_compact')):
        module = sys.modules.get(module_name)
        if module is None:
            continue
        current = getattr(module, attribute, None)
        if current is original:
            setattr(module, attribute, wrapper)
        elif current is not wrapper and current is not None:
            _emit({'event': 'census_error', 'where': 'alias',
                   'error': f'{module_name}.{attribute} is neither the original nor the census wrapper'})
    original_export = _ORIGINALS.get('save_svf_zip_npz_outputs')
    wrapper_export = _WRAPPERS.get('save_svf_zip_npz_outputs')
    if original_export is None or wrapper_export is None:
        return
    module = sys.modules.get('solweig_light.geometry.service')
    if module is not None and getattr(module, 'save_svf_zip_npz_outputs', None) is original_export:
        setattr(module, 'save_svf_zip_npz_outputs', wrapper_export)


def patch_module(fullname, module):
    """Wrap the freshly (or previously) executed target module in place."""
    if fullname in _PATCHED_MODULES:
        return
    _PATCHED_MODULES.add(fullname)
    global _PACKAGE_FILE
    if _PACKAGE_FILE is None:
        _PACKAGE_FILE = getattr(module, '__file__', None)
        _emit({'event': 'package', 'solweig_file': _PACKAGE_FILE})
    if fullname == 'solweig_light.cache.geometry':
        store = module.GeometryStore
        _ORIGINALS['key_for'] = store.key_for
        _ORIGINALS['get_or_create'] = store.get_or_create
        store.key_for = _wrap_key_for(module, _ORIGINALS['key_for'])
        store.get_or_create = _wrap_get_or_create(module, _ORIGINALS['get_or_create'])
        _WRAPPERS['key_for'] = store.key_for
        _WRAPPERS['get_or_create'] = store.get_or_create
    elif fullname == 'solweig_light.geometry.svf':
        _ORIGINALS['svf_calculator_compact'] = module.svf_calculator_compact
        module.svf_calculator_compact = _wrap_svf(module, _ORIGINALS['svf_calculator_compact'])
        _WRAPPERS['svf_calculator_compact'] = module.svf_calculator_compact
        _ORIGINALS['save_svf_zip_npz_outputs'] = module.save_svf_zip_npz_outputs
        module.save_svf_zip_npz_outputs = _wrap_export(module, _ORIGINALS['save_svf_zip_npz_outputs'])
        _WRAPPERS['save_svf_zip_npz_outputs'] = module.save_svf_zip_npz_outputs
        _fix_aliases()
    elif fullname in ('solweig_light.pipeline', 'solweig_light.geometry.service'):
        _fix_aliases()


class _LoaderProxy:
    def __init__(self, loader, after_exec):
        self._loader = loader
        self._after_exec = after_exec

    def create_module(self, spec):
        return self._loader.create_module(spec)

    def exec_module(self, module):
        self._loader.exec_module(module)
        self._after_exec(module)

    def __getattr__(self, name):
        return getattr(self._loader, name)


class CensusFinder(importlib.abc.MetaPathFinder):
    """Patch target modules right after their ordinary execution."""

    def find_spec(self, fullname, path=None, target=None):
        if fullname not in TARGET_MODULES:
            return None
        for finder in sys.meta_path:
            if finder is self:
                continue
            find = getattr(finder, 'find_spec', None)
            if find is None:
                continue
            spec = find(fullname, path, target)
            if spec is not None:
                break
        else:
            return None
        if spec is None or spec.loader is None:
            return None
        module_name = fullname

        def after(module):
            try:
                patch_module(module_name, module)
            except Exception as error:
                _emit({'event': 'census_error', 'where': 'patch:%s' % module_name,
                       'error': repr(error)})

        spec.loader = _LoaderProxy(spec.loader, after)
        return spec


def rearm(record_dir, role):
    """Point the already-installed wrappers at a fresh per-run record dir."""
    global _RECORD_DIR, _ROLE, _HEADER_EMITTED, _FINDER
    _RECORD_DIR = str(record_dir)
    _ROLE = str(role)
    _HEADER_EMITTED = False
    os.makedirs(_RECORD_DIR, exist_ok=True)
    if _FINDER is None:
        _FINDER = CensusFinder()
        # Prepend: the finder must see the import before PathFinder claims it.
        sys.meta_path.insert(0, _FINDER)
    for name in TARGET_MODULES:
        module = sys.modules.get(name)
        if module is not None:
            try:
                patch_module(name, module)
            except Exception as error:
                _emit({'event': 'census_error', 'where': 'patch:%s' % name, 'error': repr(error)})
    _emit({'event': 'header', 'target_modules': list(TARGET_MODULES)})


def install(record_dir, role):
    rearm(record_dir, role)


def autostart():
    record_dir = os.environ.get('SOLWEIG_CENSUS_RECORD_DIR')
    if not record_dir:
        return
    rearm(record_dir, os.environ.get('SOLWEIG_CENSUS_ROLE', 'child'))
