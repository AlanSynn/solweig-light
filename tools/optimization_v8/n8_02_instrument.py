"""N8-02 worker-local instrumentation for the packed LW pipeline call path.

Installs process-local counters/timers by wrapping the REAL call path of
``pipeline.run_tile`` (b7-50 pattern) without touching src/:

  loader/prep : native_lw._ensure_loaded -> _cache_dir (mkdir), _build_needed
                (dylib.exists, stamp.exists, stamp.read_text, json.loads,
                _kernel_digest -> kernel read_bytes + sha256)
  C entry     : the ctypes function pointers in lw_native._LIBS[gang][1]
                ('f32'/'f64') -- the closest point to the admitted function
                pointer invocation reachable without editing src
  fallback    : native_lw.native_longwave_primary UnsupportedInput reasons
                (re-raised; cylinder_longwave's dispatch closure then takes
                the Numba fallback, which is timed by the _longwave_primary
                wrappers)
  stages      : Solweig_2022a_calc, Lcyl_v2022a_by_demand,
                define_patch_characteristics_primary, patch_radiation
                _classes/_block/_class_coefficients/patch_geometry, comfort
                utci_calculator_uniform, TransactionalOutputs write/checkpoint

One bounded terminal JSON record per process (env N8_02_COUNTERS_OUT); no
per-block log lines. All timings use time.perf_counter; Path-method spys
count only calls whose immediate caller frame is native_lw.py/lw_native.py.
"""
from __future__ import annotations

import atexit
import json
import os
import sys
import time
from collections import defaultdict

_NATIVE_MODULES = ('native_lw.py', 'lw_native.py')

T_INSTALL = None


class Rec:
    """Mutable counter bag dumped once at exit."""

    def __init__(self):
        self.t0 = time.perf_counter()
        self.counts = defaultdict(int)
        self.times_s = defaultdict(float)
        self.squares_s = defaultdict(float)  # for variance, bounded
        self.first_s = {}
        self.max_s = {}
        self.fallback_reasons = defaultdict(int)
        self.native_entry_specs = defaultdict(int)
        self.installed_at = None
        self.notes = []

    def hit(self, key, dt):
        self.counts[key] += 1
        self.times_s[key] += dt
        self.squares_s[key] += dt * dt
        if key not in self.first_s:
            self.first_s[key] = dt
        if dt > self.max_s.get(key, 0.0):
            self.max_s[key] = dt

    def dump(self):
        out = {
            'install_perf_counter': self.installed_at,
            'counts': dict(self.counts),
            'total_s': {k: round(v, 6) for k, v in self.times_s.items()},
            'mean_us': {k: round(self.times_s[k] / self.counts[k] * 1e6, 3)
                        for k in self.times_s if self.counts[k]},
            'first_call_s': {k: round(v, 6) for k, v in self.first_s.items()},
            'max_s': {k: round(v, 6) for k, v in self.max_s.items()},
            'fallback_reasons': dict(self.fallback_reasons),
            'native_entry_specs': dict(self.native_entry_specs),
            'notes': self.notes,
        }
        return out


REC = Rec()


def _wrap(module, name, key, record=True):
    """Replace module attribute with a counting/timing pass-through."""
    original = getattr(module, name)

    def wrapper(*args, **kwargs):
        if not record:
            return original(*args, **kwargs)
        t0 = time.perf_counter()
        try:
            return original(*args, **kwargs)
        finally:
            REC.hit(key, time.perf_counter() - t0)

    wrapper.__wrapped_original__ = original
    setattr(module, name, wrapper)
    return original


def _caller_is_native_module() -> bool:
    try:
        frame = sys._getframe(2)
        return frame.f_code.co_filename.endswith(_NATIVE_MODULES)
    except Exception:
        return False


def _install_path_spies():
    """Count mkdir/stat-ish/read ops issued from the native loader modules."""
    import pathlib
    for meth, key in (('mkdir', 'fs.mkdir'), ('exists', 'fs.exists'),
                      ('read_text', 'fs.read_text'),
                      ('read_bytes', 'fs.read_bytes')):
        original = getattr(pathlib.Path, meth)

        def spy(self, *args, _original=original, _key=key, **kwargs):
            if _caller_is_native_module():
                t0 = time.perf_counter()
                try:
                    return _original(self, *args, **kwargs)
                finally:
                    REC.hit('native_prep.' + _key, time.perf_counter() - t0)
            return _original(self, *args, **kwargs)

        spy.__wrapped_original__ = original
        setattr(pathlib.Path, meth, spy)

    import json as _json
    _loads = _json.loads

    def loads_spy(*args, **kwargs):
        if _caller_is_native_module():
            t0 = time.perf_counter()
            try:
                return _loads(*args, **kwargs)
            finally:
                REC.hit('native_prep.json_loads', time.perf_counter() - t0)
        return _loads(*args, **kwargs)

    loads_spy.__wrapped_original__ = _loads
    _json.loads = loads_spy


def _install_native_entry_counters():
    """Wrap the loaded ctypes entry pointers (kernel-entry proof + time)."""
    import solweig_light.backends.native_lw as native_lw
    import solweig_light.backends.native.lw_native as lw_native

    # Time the loader chain per native call.
    _wrap(native_lw, '_ensure_loaded', 'native_prep.ensure_loaded_total')
    _wrap(native_lw, '_cache_dir', 'native_prep.cache_dir')
    _wrap(native_lw, '_build_needed', 'native_prep.build_needed')
    _wrap(native_lw, '_kernel_digest', 'native_prep.kernel_digest')
    _wrap(native_lw, '_build', 'native_prep.build')

    # Count + time UnsupportedInput fallback reasons at the adapter entry.
    original_call = native_lw.native_longwave_primary

    def counted_native_call(*args, **kwargs):
        t0 = time.perf_counter()
        try:
            result = original_call(*args, **kwargs)
        except native_lw.UnsupportedInput as error:
            reason = str(error).split(':', 1)[0].strip()
            if len(REC.fallback_reasons) < 64:
                REC.fallback_reasons[reason] += 1
            elif reason in REC.fallback_reasons:
                REC.fallback_reasons[reason] += 1
            else:
                REC.fallback_reasons['<overflow-other>'] += 1
            REC.hit('native_adapter.rejected', time.perf_counter() - t0)
            raise
        REC.hit('native_adapter.admitted', time.perf_counter() - t0)
        return result

    counted_native_call.__wrapped_original__ = original_call
    native_lw.native_longwave_primary = counted_native_call

    # Time lw_native.primary (validation + marshalling + pointer call).
    _wrap(lw_native, 'primary', 'native_adapter.lw_native_primary')

    # Kernel-entry proof: wrap the actual ctypes function pointers AFTER a
    # first load pins them. Do one load now (recorded as first-use).
    t0 = time.perf_counter()
    native_lw._ensure_loaded()
    REC.hit('native_prep.first_load_at_install', time.perf_counter() - t0)
    gang = native_lw.GANG
    lib, entries = lw_native._LIBS[gang]
    for spec, pointer in list(entries.items()):
        def entry_proof(*args, _pointer=pointer, _spec=spec, **kwargs):
            t0 = time.perf_counter()
            try:
                return _pointer(*args, **kwargs)
            finally:
                REC.native_entry_specs[_spec] += 1
                REC.hit('native_c_entry.' + _spec, time.perf_counter() - t0)
        entries[spec] = entry_proof
    REC.notes.append('ctypes entry pointers wrapped after first load '
                     f'(gang={gang}); counts are completed C invocations')


def _calibrate():
    """Measure this wrapper style's per-call overhead (diagnostic only)."""
    target = lambda: None  # noqa: E731
    ns = {}

    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        try:
            return target(*args, **kwargs)
        finally:
            ns['t'] = ns.get('t', 0.0) + (time.perf_counter() - t0)

    n = 20000
    t0 = time.perf_counter()
    for _ in range(n):
        target()
    bare = (time.perf_counter() - t0) / n
    t0 = time.perf_counter()
    for _ in range(n):
        wrapper()
    wrapped = (time.perf_counter() - t0) / n
    REC.notes.append(f'wrapper overhead self-test: bare={bare*1e9:.1f}ns '
                     f'wrapped={wrapped*1e9:.1f}ns delta={(wrapped-bare)*1e9:.1f}ns '
                     f'per call (timed-wrapper style used everywhere here)')


def install():
    """Install all instrumentation; call after solweig_light imports."""
    global T_INSTALL
    T_INSTALL = time.perf_counter()
    _calibrate()
    import solweig_light.pipeline as pipeline
    import solweig_light.radiation.engine as engine
    import solweig_light.radiation.cylinder_longwave as cyl
    import solweig_light.radiation.patch_radiation as prad
    from solweig_light import persistence

    # whole-timestep radiation and its LW island
    _wrap(pipeline, 'Solweig_2022a_calc', 'stage.solweig_calc')
    _wrap(cyl, 'Lcyl_v2022a_by_demand', 'stage.lcyl_by_demand')
    _wrap(cyl, 'define_patch_characteristics_primary', 'stage.dpc_primary')
    # per-block stages inside define_patch_characteristics_primary
    _wrap(prad, '_classes', 'stage.classifier_classes')
    _wrap(prad, '_block', 'stage.decode_block_x3')
    _wrap(prad, '_class_coefficients', 'stage.coefficients_prepared')
    _wrap(prad, 'patch_geometry', 'stage.patch_geometry')
    # the retained-route Numba kernels (also the fallback target under native)
    _wrap(cyl, '_longwave_primary', 'island.numba_lw_primary')
    _wrap(cyl, '_longwave_primary_serial', 'island.numba_lw_primary_serial')
    # comfort + durable IO
    _wrap(pipeline, 'utci_calculator_uniform', 'stage.utci')
    _wrap(persistence.TransactionalOutputs, 'write', 'stage.output_write')
    _wrap(persistence.TransactionalOutputs, 'checkpoint', 'stage.output_checkpoint')
    # preparation side: legacy geometry load, geometry store, raster reads
    import solweig_light.cache as _cache_pkg
    from solweig_light.io import rasters as _rasters
    for module, name, key in (
            (_cache_pkg, 'load_legacy_geometry', 'stage.geometry_legacy_load'),
            (pipeline, 'read_raster', 'stage.read_raster_pipeline'),
            (_rasters, 'read_raster', 'stage.read_raster_module')):
        if hasattr(module, name):
            _wrap(module, name, key)
        else:
            REC.notes.append(f'optional wrap point missing: {name}')
    if hasattr(_cache_pkg, 'GeometryStore'):
        _wrap(_cache_pkg.GeometryStore, 'get_or_create', 'stage.geometry_store')

    _install_path_spies()

    native_loaded = 'solweig_light.backends.native_lw' in sys.modules
    if os.environ.get('SOLWEIG_LIGHT_LW_BACKEND', '').strip().lower() in ('native', 'ispc'):
        # native arm: loader + entry counters active
        _install_native_entry_counters()
    else:
        # default arm: prove the native path is never taken. Wrap the module
        # attribute WITHOUT loading anything; a nonzero count would falsify
        # the code-reading claim, zero is the measurement.
        import solweig_light.backends.native_lw as native_lw
        import solweig_light.backends.native.lw_native as lw_native
        _wrap(native_lw, '_ensure_loaded', 'native_prep.ensure_loaded_total')
        _wrap(lw_native, 'primary', 'native_adapter.lw_native_primary')
        REC.notes.append('default arm: native modules pre-imported by the '
                         'instrument itself (not by the pipeline); counts '
                         'below isolate pipeline-initiated calls. sys.modules '
                         'evidence distinguishes the two.')
        REC.notes.append(f'native_lw already imported before install: '
                         f'{native_loaded}')

    out = os.environ.get('N8_02_COUNTERS_OUT')
    if out:
        atexit.register(_dump, out)
    REC.installed_at = time.perf_counter() - REC.t0


def _dump(path):
    payload = REC.dump()
    payload['sys_modules_native'] = {
        name: (name in __import__('sys').modules)
        for name in ('solweig_light.backends.native_lw',
                     'solweig_light.backends.native.lw_native')}
    payload['env_lw_backend'] = os.environ.get('SOLWEIG_LIGHT_LW_BACKEND', '')
    payload['native_cache_env'] = os.environ.get('SOLWEIG_LIGHT_NATIVE_CACHE', '')
    payload['pid'] = os.getpid()
    with open(path, 'w') as handle:
        json.dump(payload, handle, indent=1, sort_keys=True)
