"""L2 chronology differential probe (C6-70): per-call input/output hashing.

Run identically in the base tree and the integrated tree; compare the two
NDJSON logs byte-for-byte plus the final output TIFF hashes. Read-only
instrumentation: the radiation entries are wrapped, never edited.
"""
import dataclasses
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

TREE_UNDER_TEST = Path(sys.argv[1]).resolve()
WORK = Path(sys.argv[2]).resolve()
LOG = Path(sys.argv[3]).resolve()
INTEGRATED = Path('/Users/alansynn/Workspace/solweig-light-claude-v5')

sys.path.insert(0, str(TREE_UNDER_TEST / 'src'))
_spec = importlib.util.spec_from_file_location(
    'chronology_scene_fixtures',
    str(INTEGRATED / 'tests/optimization_v6/geometry_recipe/scene_fixtures.py'))
fixtures = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fixtures)

events = []


def sha_array(value):
    array = np.ascontiguousarray(value)
    digest = hashlib.sha256()
    digest.update(str(array.dtype).encode())
    digest.update(str(array.shape).encode())
    digest.update(array.tobytes())
    return digest.hexdigest()


def collect(prefix, value, sink):
    if isinstance(value, np.ndarray):
        sink.append((prefix, sha_array(value)))
    elif isinstance(value, (bool, int, float, str)) or value is None:
        sink.append((prefix, repr(value)))
    elif isinstance(value, dict):
        for key in sorted(value, key=repr):
            collect(f'{prefix}.{key!r}', value[key], sink)
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            collect(f'{prefix}[{index}]', item, sink)


def wrap(module, name, label, drop_kwargs=()):
    original = getattr(module, name)

    def wrapper(*args, **kwargs):
        signature = []
        collect('args', args, signature)
        collect('kwargs', kwargs, signature)
        signature = [entry for entry in signature
                     if not any(entry.startswith(f'kwargs.{drop}.')
                                for drop in drop_kwargs)]
        result = original(*args, **kwargs)
        outputs = []
        collect('out', result, outputs)
        events.append({'call': label,
                       'in': [f'{key}={value}' for key, value in signature],
                       'out': [f'{key}={value}' for key, value in outputs]})
        return result

    setattr(module, name, wrapper)
    return original


_demanded_active = [False]


def _log_event(label, signature, result):
    outputs = []
    collect('out', result, outputs)
    events.append({'call': label,
                   'in': [f'{key}={value}' for key, value in signature],
                   'out': [f'{key}={value}' for key, value in outputs]})


def wrap_demanded_lside(demand_module):
    """Install the demanded-wrapper FIRST.

    The integrated engine imports ``lside_veg_v2022a_demanded`` at module
    level, so the wrapper must exist before the engine module is imported;
    the base engine binds nothing from here (it calls the engine function
    directly) and this wrapper simply never fires."""
    if demand_module is None or not hasattr(demand_module, 'lside_veg_v2022a_demanded'):
        return
    original_demanded = demand_module.lside_veg_v2022a_demanded

    def demanded_wrapper(*args, **kwargs):
        signature = []
        collect('args', args, signature)
        collect('kwargs', kwargs, signature)
        signature = [entry for entry in signature
                     if not str(entry[0]).startswith('kwargs.demand')]
        _demanded_active[0] = True
        try:
            result = original_demanded(*args, **kwargs)
        finally:
            _demanded_active[0] = False
        _log_event('Lside', signature, result)
        return result

    demand_module.lside_veg_v2022a_demanded = demanded_wrapper


def wrap_engine_lside(engine_module):
    """Log direct engine calls (the base route); stay silent during the
    demanded wrapper's delegation window so fallback steps are not
    double-logged."""
    original_engine = engine_module.Lside_veg_v2022a

    def engine_wrapper(*args, **kwargs):
        if _demanded_active[0]:
            return original_engine(*args, **kwargs)
        signature = []
        collect('args', args, signature)
        collect('kwargs', kwargs, signature)
        result = original_engine(*args, **kwargs)
        _log_event('Lside', signature, result)
        return result

    engine_module.Lside_veg_v2022a = engine_wrapper


def main():
    scene = fixtures.build_scene(WORK / 'scene')
    from solweig_light import runtime_options, thermal_comfort
    from solweig_light.runtime import RuntimeOptions, get_runtime_options
    from solweig_light.radiation import patch_radiation

    wrap(patch_radiation, 'Kside_veg_v2022a', 'Kside_veg_v2022a')
    wrap(patch_radiation, 'define_patch_characteristics', 'longwave_patches')
    # Order matters: the demanded Lside wrapper must exist before the engine
    # module is imported (module-level from-import binds the function object).
    from solweig_light.radiation import pipeline_demand, cylinder_longwave
    wrap_demanded_lside(pipeline_demand)
    if hasattr(cylinder_longwave, 'Lcyl_v2022a_by_demand'):
        # Integrated tree: the engine call site imports this dispatcher
        # function-locally, so the module attribute is resolved at call time.
        # Distinct label: its signature/outputs differ from the base patch
        # entry; value equivalence is established transitively (Ldown and
        # the cylinder cardinals are consumed by the logged Lside/Kside
        # inputs and the final TIFFs), not by signature comparison.
        wrap(cylinder_longwave, 'Lcyl_v2022a_by_demand', 'longwave_demand')
    from solweig_light.radiation import engine
    wrap_engine_lside(engine)

    merged = dataclasses.replace(get_runtime_options(),
                                 memory_budget_bytes=12 * 1024 ** 3,
                                 workers=1)
    # execute_tiles always serves jobs from a persistent subprocess pool;
    # the wrappers above live in this process. Swap in an in-process loop
    # over the same job dicts calling the same run_tile entry: only the
    # transport differs, not the numerical work under test.
    import solweig_light.runtime as _runtime_module
    from solweig_light.pipeline import run_tile as _run_tile

    def _in_process_execute(jobs, options=None, **kwargs):
        return tuple(_run_tile(**job, runtime=options) for job in jobs)

    _real_execute_tiles = _runtime_module.execute_tiles
    _runtime_module.execute_tiles = _in_process_execute
    try:
        with runtime_options(merged):
            thermal_comfort(str(scene['dir']), fixtures.DATE,
                            own_met_file=str(scene['dir'] / 'met.txt'),
                            ERA_5_z0_find=False)
    finally:
        _runtime_module.execute_tiles = _real_execute_tiles

    with LOG.open('w') as handle:
        for event in events:
            handle.write(json.dumps(event, sort_keys=True) + '\n')

    output_hashes = {}
    for path in sorted(WORK.rglob('*')):
        if path.is_file() and path.suffix in ('.tif', '.tiff'):
            output_hashes[str(path.relative_to(WORK))] = hashlib.sha256(
                path.read_bytes()).hexdigest()
    (WORK / 'output_hashes.json').write_text(
        json.dumps(output_hashes, indent=2, sort_keys=True) + '\n')
    print(f'events={len(events)} tifs={len(output_hashes)}')


if __name__ == '__main__':
    main()
