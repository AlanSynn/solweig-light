#!/usr/bin/env python3
"""Same-interpreter, alternating checkout benchmark of complete own-met runs.

Raw scenes/caches/results belong under --workdir, never in the repository.
See development/docs/full_compute_benchmark.md for protocol and limitations.
"""
from __future__ import annotations

import argparse
import datetime as dt
import functools
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import resource
import shutil
import statistics
import subprocess
import sys
import time
import traceback
import zipfile

THREAD_ENV = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
              'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'BLIS_NUM_THREADS',
              'NUMBA_NUM_THREADS')
TOLERANCES = {'TMRT': .01, 'UTCI': .02, 'geometry': 1e-6, 'state': 0.}
SVF_FIELDS = {'svf','svfE','svfS','svfW','svfN','svfveg','svfEveg','svfSveg','svfWveg','svfNveg',
              'svfaveg','svfEaveg','svfSaveg','svfWaveg','svfNaveg'}
STATE_FIELDS = {'CI','firstdaytime','timestepdec','timeadd','Tgmap1','Tgmap1E',
                'Tgmap1S','Tgmap1W','Tgmap1N','TgOut1','Twater'}


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True, default=str) + '\n')
    os.replace(temporary, path)


def digest(path):
    hasher = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            hasher.update(block)
    return hasher.hexdigest()


def source_identity(checkout):
    checkout = Path(checkout).resolve()
    def git(*args):
        return subprocess.check_output(['git', '-C', str(checkout), *args])
    # Include untracked source bytes: git diff alone misses a newly added kernel.
    tracked_diff = git('diff', 'HEAD', '--binary')
    untracked = git('ls-files', '--others', '--exclude-standard', '--',
                    'src','tests','development/tools','development/docs',
                    'pyproject.toml','AGENTS.md','CLAUDE.md','README.md',
                    'setup.cfg','setup.py','pytest.ini','.github').decode().splitlines()
    allowed_suffixes={'.py','.pyi','.ispc','.c','.cc','.cpp','.h','.hpp','.json','.txt',
                      '.sh','.toml','.md','.yaml','.yml','.svg','.csv'}
    def source_asset(name):
        path=Path(name)
        if any(part in {'__pycache__','.pytest_cache','node_modules','.venv','build','dist'}
               or part.startswith(('pytest-of-root','solweig-runtime-'))
               or part.endswith(('.egg-info','.dist-info')) for part in path.parts):
            return False
        return path.suffix in allowed_suffixes or (path.parts[:2]==('tests','reference')
                                                   and path.suffix in {'.tif','.npz','.npy','.zip'})
    extra = {name: digest(checkout / name) for name in sorted(untracked)
             if source_asset(name) and (checkout / name).is_file()}
    source_files = {str(path.relative_to(checkout)): digest(path)
                    for path in sorted((checkout / 'src').rglob('*'))
                    if path.is_file() and '__pycache__' not in path.parts
                    and not any(part.endswith(('.egg-info','.dist-info')) for part in path.parts)
                    and path.suffix in {'.py','.pyi','.ispc','.c','.cc','.cpp','.h','.hpp','.json','.txt','.sh','.toml'}}
    return {'checkout': str(checkout), 'commit': git('rev-parse', 'HEAD').decode().strip(),
            'dirty_diff_sha256': hashlib.sha256(tracked_diff).hexdigest(),
            'dirty': bool(tracked_diff or extra), 'untracked_files': extra,
            'source_tree_sha256': hashlib.sha256(json.dumps(source_files, sort_keys=True).encode()).hexdigest(),
            'source_files': source_files}


def selected_met(path, date=None, start_time=None, end_time=None):
    """Retain original numeric row text; optional inclusive timestamp filtering."""
    lines = Path(path).read_text().splitlines()
    if len(lines) < 3:
        raise ValueError('Own-met file needs a header and multiple numeric rows')
    records = []
    for line in lines[1:]:
        if not line.strip():
            continue
        values = line.split()
        if len(values) < 24:
            raise ValueError('Own-met row has fewer than 24 columns')
        year, day, hour, minute = (int(float(value)) for value in values[:4])
        stamp = dt.datetime(year, 1, 1) + dt.timedelta(days=day-1, hours=hour, minutes=minute)
        records.append((stamp, line))
    if not records:
        raise ValueError('No meteorological rows')
    selected_date = dt.date.fromisoformat(date) if date else records[0][0].date()
    def bound(value):
        if value is None:
            return None
        return dt.datetime.fromisoformat(value if 'T' in value or ' ' in value
                                        else f'{selected_date.isoformat()}T{value}')
    start, end = bound(start_time), bound(end_time)
    if start and end and start > end:
        raise ValueError('start-time is after end-time')
    records = [(stamp, line) for stamp, line in records
               if (start is None or stamp >= start) and (end is None or stamp <= end)]
    if len(records) < 2:
        raise ValueError('Selected own-met interval must retain at least two rows')
    if any(b[0] <= a[0] for a, b in zip(records, records[1:])):
        raise ValueError('Selected meteorological timestamps must strictly increase')
    if not date:
        selected_date = records[0][0].date()
    return {'date': selected_date.isoformat(), 'timestamps': [stamp.isoformat() for stamp, _ in records],
            'text': '\n'.join([lines[0], *(line for _, line in records)]) + '\n'}


def environment():
    versions = {}
    for name in ('numpy', 'numba', 'llvmlite', 'scipy', 'GDAL', 'pytz', 'timezonefinder', 'psutil'):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    import numba
    from osgeo import gdal
    from solweig_light import runtime
    memory={}
    for key,name in (('physical_bytes','_physical_memory_bytes'),
                     ('available_host_bytes','_available_host_memory_bytes'),
                     ('container_limit_bytes','_container_memory_limit_bytes')):
        try:
            memory[key]=getattr(runtime,name)()
        except Exception as error:
            memory[key]=None
            memory[key+'_unavailable_reason']=f'{type(error).__name__}: {error}'
    return {'python': sys.version, 'executable': sys.executable, 'platform': platform.platform(),
            'dependencies': versions, 'gdal_runtime': gdal.VersionInfo(),'memory':memory,
            'thread_environment': {name: os.environ.get(name) for name in THREAD_ENV},
            'numba_threads': numba.get_num_threads(), 'cpu_count': os.cpu_count(),
            'affinity': sorted(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else None,
            'numba_cache_dir': os.environ.get('NUMBA_CACHE_DIR'),
            'gdal_cachemax': os.environ.get('GDAL_CACHEMAX'),
            'backend_environment': {name:os.environ.get(name) for name in (
                'SOLWEIG_LIGHT_ANILUM_PACKED','SOLWEIG_LIGHT_FUSED_RAD','SOLWEIG_LIGHT_GVF_PREPARE',
                'SOLWEIG_LIGHT_LSIDE_DISPATCH','SOLWEIG_LIGHT_LW_BACKEND','SOLWEIG_LIGHT_NATIVE_CACHE',
                'SOLWEIG_LIGHT_PATCH_CLASS_TABLES','SOLWEIG_LIGHT_PREPARED_VIS',
                'NUMBA_CPU_NAME','NUMBA_CPU_FEATURES','NUMBA_THREADING_LAYER','OMP_PROC_BIND','OMP_PLACES')}}


def _usage():
    result = {}
    for name, kind in (('self', resource.RUSAGE_SELF), ('children', resource.RUSAGE_CHILDREN)):
        value = resource.getrusage(kind)
        # Linux ru_maxrss is KiB; macOS reports bytes. It is a high-water mark,
        # not an additive process-tree total.
        result[name] = {'user_seconds': value.ru_utime, 'system_seconds': value.ru_stime,
                        'maxrss_bytes': value.ru_maxrss * (1 if sys.platform == 'darwin' else 1024)}
    return result


def _install_hooks():
    """Called by generated sitecustomize in parent and native worker processes."""
    root = os.environ.get('SOLWEIG_BENCH_EVENTS')
    if not root:
        return
    import solweig_light.api as api
    import solweig_light.pipeline as pipeline
    path = Path(root) / f'events-{os.getpid()}.jsonl'
    def emit(record):
        with path.open('a') as stream:
            stream.write(json.dumps(record, default=str) + '\n')
    emit({'event': 'startup', 'pid': os.getpid(), 'environment': environment()})
    def wrap(module, name, stage):
        original = getattr(module, name)
        @functools.wraps(original)
        def measured(*args, **kwargs):
            started = time.perf_counter()
            before = _usage()
            profile = None
            if stage in ('svf','tile') and os.environ.get('SOLWEIG_BENCH_PROFILE') == '1':
                import cProfile
                profile = cProfile.Profile()
                profile.enable()
            status = 'failed'
            try:
                value = original(*args, **kwargs)
                status = 'passed'
                return value
            finally:
                if profile:
                    profile.disable()
                    profile.dump_stats(str(Path(root) / f'profile-{stage}-{os.getpid()}-{time.time_ns()}.pstats'))
                emit({'event': 'stage', 'stage': stage, 'pid': os.getpid(), 'status': status,
                      'wall_seconds': time.perf_counter()-started,
                      'usage_before': before, 'usage_after': _usage()})
        setattr(module, name, measured)
    for name, stage in (('preprocess', 'preprocess'), ('run_walls_aspect', 'walls'),
                        ('_calculate_svf', 'svf'), ('run_utci_tiles', 'tmrt_utci')):
        wrap(api, name, stage)
    wrap(pipeline, 'run_tile', 'tile')


def _child(spec_path):
    spec = json.loads(Path(spec_path).read_text())
    result = {'status': 'failed', 'invocation': spec}
    try:
        import solweig_light
        actual = Path(solweig_light.__file__).resolve()
        expected = Path(spec['checkout']).resolve() / 'src'
        if not actual.is_relative_to(expected):
            raise RuntimeError(f'Wrong package import: {actual}; expected under {expected}')
        event_files=list((Path(spec['run'])/'events').glob('events-*.jsonl'))
        if not event_files:
            raise RuntimeError('Stage instrumentation did not load; inspect stderr.log')
        result['environment'] = environment()
        result['package'] = str(actual)
        before = _usage()
        start = time.perf_counter()
        # The only hook overhead inside this timer is stage event recording.
        with solweig_light.runtime_options(solweig_light.RuntimeOptions(**spec['runtime'])):
            solweig_light.thermal_comfort(**spec['kwargs'])
        result.update(status='passed', workflow_wall_seconds=time.perf_counter()-start,
                      usage_before=before, usage_after=_usage())
    except BaseException:
        result['traceback'] = traceback.format_exc()
    write_json(Path(spec['run']) / 'child-result.json', result)
    return 0 if result['status'] == 'passed' else 1


def array_metrics(left, right):
    """Chunk metric: special masks, finite values/bits, and NaN payloads separate."""
    import numpy as np
    if left.shape != right.shape or left.dtype != right.dtype:
        return {'schema_equal': False, 'values': 0, 'finite_values': 0, 'max_abs_error': None,
                'special_masks_equal': False, 'finite_bitwise_equal': False,
                'all_bitwise_equal': False, 'nan_payloads_equal': False,
                'reference_nan_count': 0, 'candidate_nan_count': 0}
    if left.dtype.kind not in 'fc':
        equal = left.tobytes() == right.tobytes()
        return dict(schema_equal=True, values=left.size, finite_values=left.size,
                    max_abs_error=float(np.max(np.abs(left.astype(np.float64)-right.astype(np.float64)))) if left.size else 0.,
                    special_masks_equal=True, finite_bitwise_equal=equal,
                    all_bitwise_equal=equal, nan_payloads_equal=True,
                    reference_nan_count=0,candidate_nan_count=0)
    if left.dtype.kind == 'c':
        raise ValueError('Complex benchmark artifacts are unsupported')
    finite = np.isfinite(left) & np.isfinite(right)
    nan_a, nan_b = np.isnan(left), np.isnan(right)
    masks = all(np.array_equal(fn(left), fn(right)) for fn in (np.isnan, np.isposinf, np.isneginf))
    error = float(np.max(np.abs(left[finite].astype(np.float64)-right[finite].astype(np.float64)))) if finite.any() else 0.
    return dict(schema_equal=True, values=left.size, finite_values=int(finite.sum()),
                max_abs_error=error, special_masks_equal=masks,
                finite_bitwise_equal=masks and left[finite].tobytes() == right[finite].tobytes(),
                all_bitwise_equal=left.tobytes() == right.tobytes(),
                nan_payloads_equal=np.array_equal(nan_a, nan_b) and left[nan_a].tobytes() == right[nan_b].tobytes(),
                reference_nan_count=int(nan_a.sum()),candidate_nan_count=int(nan_b.sum()))


def combine_metrics(records, tolerance):
    return {'passed': all(record['schema_equal'] and record['special_masks_equal']
                          and record['max_abs_error'] is not None and record['max_abs_error'] <= tolerance
                          for record in records),
            'tolerance_absolute': tolerance, 'max_abs_error': max((record['max_abs_error'] or 0. for record in records), default=0.),
            'finite_values': sum(record['finite_values'] for record in records),
            'reference_nan_count': sum(record['reference_nan_count'] for record in records),
            'candidate_nan_count': sum(record['candidate_nan_count'] for record in records),
            **{key: all(record[key] for record in records) for key in
               ('schema_equal', 'special_masks_equal', 'finite_bitwise_equal', 'all_bitwise_equal', 'nan_payloads_equal')}}


def raster_signature(path):
    from osgeo import gdal
    dataset = gdal.Open(str(path))
    if dataset is None:
        raise ValueError(f'Cannot open {path}')
    bands = []
    for index in range(1, dataset.RasterCount+1):
        band = dataset.GetRasterBand(index)
        nodata = band.GetNoDataValue()
        bands.append({'dtype': gdal.GetDataTypeName(band.DataType), 'metadata': band.GetMetadata(),
                      'description': band.GetDescription(), 'nodata': 'NaN' if isinstance(nodata, float) and math.isnan(nodata) else nodata,
                      'mask_flags': band.GetMaskFlags()})
    return {'width': dataset.RasterXSize, 'height': dataset.RasterYSize, 'count': dataset.RasterCount,
            'transform': dataset.GetGeoTransform(), 'projection': dataset.GetProjection(),
            'metadata': dataset.GetMetadata(), 'bands': bands}


def compare_tiff(left, right, tolerance):
    import numpy as np
    from osgeo import gdal
    a, b = gdal.Open(str(left)), gdal.Open(str(right))
    signature_a, signature_b = raster_signature(left), raster_signature(right)
    records = []
    masks_equal = True
    bands = []
    schema = signature_a == signature_b
    if schema:
        for index in range(1, a.RasterCount+1):
            x, y = a.GetRasterBand(index), b.GetRasterBand(index)
            band_records = []
            band_masks_equal = True
            for row in range(0, a.RasterYSize, 128):
                for col in range(0, a.RasterXSize, 128):
                    window = (col, row, min(128, a.RasterXSize-col), min(128, a.RasterYSize-row))
                    band_records.append(array_metrics(x.ReadAsArray(*window), y.ReadAsArray(*window)))
                    band_masks_equal &= np.array_equal(x.GetMaskBand().ReadAsArray(*window), y.GetMaskBand().ReadAsArray(*window))
            band_result=combine_metrics(band_records,tolerance)
            band_result.update(band=index,validity_masks_equal=bool(band_masks_equal))
            band_result['passed']=bool(band_result['passed'] and band_masks_equal)
            bands.append(band_result)
            records.extend(band_records)
            masks_equal &= band_masks_equal
    result = combine_metrics(records, tolerance)
    result.update(schema_equal=schema, validity_masks_equal=bool(masks_equal),
                  passed=bool(schema and masks_equal and records and result['passed']),
                  reference_schema=signature_a, candidate_schema=signature_b, bands=bands)
    return result


def _compare_npy(left, right, tolerance):
    import numpy as np
    a, b = np.load(left, mmap_mode='r', allow_pickle=False), np.load(right, mmap_mode='r', allow_pickle=False)
    if a.shape != b.shape or a.dtype != b.dtype:
        return combine_metrics([array_metrics(a, b)], tolerance)
    iterator=np.nditer([a,b],flags=['external_loop','buffered','zerosize_ok'],
                       op_flags=[['readonly'],['readonly']],order='C',buffersize=65536)
    records=[array_metrics(x,y) for x,y in iterator]
    if not records:records=[array_metrics(a,b)]
    return combine_metrics(records, tolerance)


def _extract_npz(path, target):
    """Stream members to disk; compare memory-mapped NPY instead of full cubes."""
    target.mkdir(parents=True, exist_ok=True)
    result = {}
    with zipfile.ZipFile(path) as archive:
        for index, name in enumerate(archive.namelist()):
            if not name.endswith('.npy') or name in result:
                raise ValueError(f'Unexpected or duplicate NPZ member {name}')
            destination = target / f'{index}.npy'
            with archive.open(name) as source, destination.open('wb') as output:
                shutil.copyfileobj(source, output, 1024*1024)
            result[name] = destination
    return result


def checkpoint_inventory(scene, expected_steps):
    records = {}
    root = Path(scene) / '.solweig-light' / 'transactions'
    for path in sorted(root.glob('*/transaction.json')):
        record = json.loads(path.read_text())
        checkpoint = record['checkpoint']
        if checkpoint['next_timestep'] != expected_steps:
            raise ValueError(f'Incomplete state cursor {path}')
        generation = checkpoint['generation']
        if Path(generation).name != generation:
            raise ValueError('Unsafe state generation')
        directory = path.parent / generation
        if digest(directory/'state.json') != checkpoint['state_sha256']:
            raise ValueError('State manifest checksum mismatch')
        payload = json.loads((directory/'state.json').read_text())
        if payload.get('schema')!=1 or set(payload.get('fields',{}))!=STATE_FIELDS:
            raise ValueError('Final state schema/field set is incomplete')
        def verify(value):
            if isinstance(value, dict):
                if 'file' in value:
                    if Path(value['file']).name != value['file'] or digest(directory/value['file']) != value['sha256']:
                        raise ValueError('State array checksum mismatch')
                for child in value.values(): verify(child)
            elif isinstance(value, list):
                for child in value: verify(child)
        verify(payload)
        complete = json.loads((path.parent/'complete.json').read_text())
        if complete['signature'] != record['signature']:
            raise ValueError('Completion signature mismatch')
        stamps = record['signature']['timestamps']
        if len(stamps) != expected_steps:
            raise ValueError('Checkpoint timestamp count mismatch')
        key = '|'.join(sorted(Path(name).name for name in record['signature']['outputs']))
        records[key] = {'directory': str(directory), 'payload': payload, 'timestamps': stamps,
                        'next_timestep': checkpoint['next_timestep']}
    if not records:
        raise ValueError('No final state checkpoints')
    return records


def compare_states(left, right):
    results = {}
    def compare(a, b, da, db, key):
        if isinstance(a, dict) and isinstance(b, dict) and 'file' in a and 'file' in b:
            schema = {k:v for k,v in a.items() if k not in {'file','sha256'}} == {k:v for k,v in b.items() if k not in {'file','sha256'}}
            result = _compare_npy(Path(da)/a['file'], Path(db)/b['file'], TOLERANCES['state'])
            result['passed'] &= schema
            results[key] = result
        elif isinstance(a, dict) and isinstance(b, dict) and set(a) == set(b):
            for name in a: compare(a[name], b[name], da, db, key+'.'+name)
        elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
            for index, (x,y) in enumerate(zip(a,b)): compare(x,y,da,db,f'{key}[{index}]')
        else: results[key] = {'passed': a == b, 'reference': a, 'candidate': b}
    if set(left) != set(right):
        return {'passed': False, 'error': 'State transaction set differs'}
    for key in left:
        a,b=left[key],right[key]
        results[key+'.timestamps']={'passed': a['timestamps'] == b['timestamps']}
        compare(a['payload'], b['payload'], a['directory'], b['directory'], key)
    return {'passed': all(item['passed'] for item in results.values()), 'fields': results}



def public_files(root, suffixes):
    """Public artifacts exclude dot-prefixed transaction/staging components."""
    root=Path(root)
    return {str(path.relative_to(root)):path for path in root.rglob('*')
            if path.suffix.lower() in suffixes
            and not any(part.startswith('.') for part in path.relative_to(root).parts)
            and path.is_file()}


def compare_runs(left, right, scratch):
    left, right, scratch = Path(left), Path(right), Path(scratch)
    records = {}
    a,b=public_files(left/'scene',{'.tif','.tiff'}),public_files(right/'scene',{'.tif','.tiff'})
    missing = sorted(set(a)^set(b))
    for key in sorted(set(a)&set(b)):
        family = Path(key).name.split('_',1)[0].upper()
        tolerance = TOLERANCES.get(family, TOLERANCES['geometry'])
        records[key]=compare_tiff(a[key],b[key],tolerance)
    # Legacy SVF ZIPs contain all fifteen fields; /vsizip/ avoids extracting TIFFs.
    geometry_a,geometry_b=left/'scene/processed_inputs/SVF',right/'scene/processed_inputs/SVF'
    zips_a,zips_b=public_files(geometry_a,{'.zip'}),public_files(geometry_b,{'.zip'})
    missing.extend('ZIP:'+name for name in sorted(set(zips_a)^set(zips_b)))
    for archive_key in sorted(set(zips_a)&set(zips_b)):
        path,other=zips_a[archive_key],zips_b[archive_key]
        with zipfile.ZipFile(path) as archive, zipfile.ZipFile(other) as other_archive:
            names=archive.namelist()
            if sorted(names)!=sorted(other_archive.namelist()):
                missing.append('SVF zip member set')
                continue
        for name in names:
            records[f'{archive_key}/{name}']=compare_tiff(f'/vsizip/{path}/{name}',f'/vsizip/{other}/{name}',TOLERANCES['geometry'])
    npzs_a,npzs_b=public_files(geometry_a,{'.npz'}),public_files(geometry_b,{'.npz'})
    missing.extend('NPZ:'+name for name in sorted(set(npzs_a)^set(npzs_b)))
    for archive_key in sorted(set(npzs_a)&set(npzs_b)):
        path,other=npzs_a[archive_key],npzs_b[archive_key]
        members_a=_extract_npz(path,scratch/'reference'/archive_key)
        members_b=_extract_npz(other,scratch/'candidate'/archive_key)
        if set(members_a)!=set(members_b): missing.append('visibility NPZ member set')
        for name in sorted(set(members_a)&set(members_b)):
            records[f'{archive_key}/{name}']=_compare_npy(members_a[name],members_b[name],0.)
    for side in (left,right):
        for family in ('TMRT','UTCI'):
            matches=list((side/'scene/output_folder').rglob(f'{family}_*.tif'))
            if not matches: missing.append(f'{side.name}: missing {family}')
    state=compare_states(json.loads((left/'inventory.json').read_text())['states'],
                         json.loads((right/'inventory.json').read_text())['states'])
    return {'passed': not missing and bool(records) and all(v['passed'] for v in records.values()) and state['passed'],
            'missing_artifacts': missing, 'artifacts': records, 'final_state': state}



def raster_values(path):
    import numpy as np
    from osgeo import gdal
    dataset=gdal.Open(str(path))
    result={'finite_values':0,'nan_values':0,'positive_infinity_values':0,
            'negative_infinity_values':0,'finite_min':None,'finite_max':None}
    for index in range(1,dataset.RasterCount+1):
        band=dataset.GetRasterBand(index)
        for row in range(0,dataset.RasterYSize,128):
            for col in range(0,dataset.RasterXSize,128):
                values=band.ReadAsArray(col,row,min(128,dataset.RasterXSize-col),min(128,dataset.RasterYSize-row))
                finite=np.isfinite(values)
                result['finite_values']+=int(finite.sum())
                result['nan_values']+=int(np.isnan(values).sum())
                result['positive_infinity_values']+=int(np.isposinf(values).sum())
                result['negative_infinity_values']+=int(np.isneginf(values).sum())
                if finite.any():
                    low,high=float(values[finite].min()),float(values[finite].max())
                    result['finite_min']=low if result['finite_min'] is None else min(result['finite_min'],low)
                    result['finite_max']=high if result['finite_max'] is None else max(result['finite_max'],high)
    return result


def inventory(run, expected_steps, expected_size):
    import numpy as np
    scene=Path(run)/'scene'
    rasters={str(path.relative_to(scene)): {'sha256':digest(path),'schema':raster_signature(path),'values':raster_values(path)}
             for path in sorted((scene/'output_folder').rglob('*.tif'))}
    if any(item['values']['finite_values']==0 for item in rasters.values()):
        raise ValueError('TMRT/UTCI output is entirely nonfinite')
    if set(Path(name).name for name in rasters)!={'TMRT_0_0.tif','UTCI_0_0.tif'}:
        raise ValueError('Expected exactly one tile with TMRT and UTCI outputs')
    if not rasters or any(item['schema']['count'] != expected_steps for item in rasters.values()):
        raise ValueError('Output band count differs from expected steps')
    if any((item['schema']['width'],item['schema']['height'])!=(expected_size,expected_size) for item in rasters.values()):
        raise ValueError('Output dimensions differ from requested logical tile')
    geometry=scene/'processed_inputs/SVF'
    archive=geometry/'svfs_0_0.zip'
    visibility=geometry/'shadowmats_0_0.npz'
    total=geometry/'SkyViewFactor_0_0.tif'
    if not all(path.is_file() for path in (archive,visibility,total)):
        raise ValueError('Missing default legacy geometry exports')
    with zipfile.ZipFile(archive) as stream:
        if set(stream.namelist())!={name+'.tif' for name in SVF_FIELDS} or len(stream.namelist())!=15:
            raise ValueError('Legacy SVF ZIP must contain all fifteen fields')
    channels={}
    with zipfile.ZipFile(visibility) as stream:
        if set(stream.namelist())!={'shadowmat.npy','vegshadowmat.npy','vbshmat.npy'} or len(stream.namelist())!=3:
            raise ValueError('Legacy visibility must contain all three channels')
        for name in stream.namelist():
            with stream.open(name) as member:
                version=np.lib.format.read_magic(member)
                reader=np.lib.format.read_array_header_1_0 if version==(1,0) else np.lib.format.read_array_header_2_0
                shape,fortran,dtype=reader(member)
            if shape!=(expected_size,expected_size,153) or dtype!=np.dtype(np.float32):
                raise ValueError('Legacy visibility shape/dtype must preserve all 153 patches')
            channels[name]={'shape':shape,'dtype':str(dtype),'fortran':fortran}
    return {'outputs':rasters,'states':checkpoint_inventory(scene,expected_steps),
            'legacy_geometry':{'archive_sha256':digest(archive),'visibility_sha256':digest(visibility),
                               'total_sha256':digest(total),'channels':channels}}


def invoke(spec, hook, jit, threads):
    run=Path(spec['run'])
    if (run/'spec.json').exists():
        raise FileExistsError(f'Trial already exists: {run}')
    run.mkdir(parents=True,exist_ok=True)
    (run/'events').mkdir()
    write_json(run/'spec.json',spec)
    env=os.environ.copy()
    env.update({name:str(threads) for name in THREAD_ENV})
    env.update(PYTHONPATH=os.pathsep.join((str(Path(spec['checkout'])/'src'),str(hook))),
               NUMBA_CACHE_DIR=str(jit), SOLWEIG_BENCH_EVENTS=str(run/'events'),
               SOLWEIG_BENCH_PROFILE='1' if spec['regime']=='profiled' else '0',
               GDAL_CACHEMAX='256')
    # Backends may retain compiled native objects in their checkout. See the
    # report's explicit first-use scope; source checkouts are not destroyed.
    started=time.perf_counter()
    with (run/'stdout.log').open('wb') as stdout, (run/'stderr.log').open('wb') as stderr:
        process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--child',str(run/'spec.json')],
                                 cwd=spec['checkout'],env=env,stdout=stdout,stderr=stderr)
        peak_tree_rss=0
        samples=0
        try:
            import psutil
        except ImportError:
            psutil=None
        monitor_error=None
        try:
            monitored=psutil.Process(process.pid) if psutil else None
        except (psutil.NoSuchProcess,psutil.AccessDenied,OSError) as error:
            monitored=None
            monitor_error=f'{type(error).__name__}: {error}'
        while process.poll() is None:
            if monitored:
                try:
                    members=[monitored,*monitored.children(recursive=True)]
                    total=0
                    for member in members:
                        try:total+=member.memory_info().rss
                        except (psutil.NoSuchProcess,psutil.AccessDenied):pass
                    peak_tree_rss=max(peak_tree_rss,total)
                    samples+=1
                except (psutil.NoSuchProcess,psutil.AccessDenied):pass
            time.sleep(.05)
    result=json.loads((run/'child-result.json').read_text()) if (run/'child-result.json').exists() else {'status':'failed'}
    result.update(process_returncode=process.returncode,process_wall_seconds=time.perf_counter()-started,
                  sampled_peak_process_tree_rss_bytes=peak_tree_rss if monitored else None,
                  rss_sampling_interval_seconds=.05,rss_samples=samples,
                  rss_monitor_unavailable_reason=monitor_error if psutil else 'psutil not installed')
    events=[]
    for path in sorted((run/'events').glob('*.jsonl')):
        events.extend(json.loads(line) for line in path.read_text().splitlines())
    result['events']=events
    required={'preprocess','walls','svf','tmrt_utci'}
    completed={event.get('stage') for event in events if event.get('event')=='stage' and event.get('status')=='passed'}
    if not required.issubset(completed):
        result.update(status='failed',instrumentation_error=f'Missing completed stages: {sorted(required-completed)}')
    result['stages']={event['stage']:event['wall_seconds'] for event in events
                      if event['event']=='stage' and event['stage']!='tile'}
    if result['status']=='passed' and process.returncode==0:
        try:
            write_json(run/'inventory.json',inventory(run,spec['expected_steps'],spec['kwargs']['tile_size']))
        except BaseException:
            result.update(status='failed',inventory_error=traceback.format_exc())
    else: result['status']='failed'
    write_json(run/'result.json',result)
    return result


def _markdown(report):
    lines=['# Full compute checkout comparison','',
           'Same interpreter and host; complete public own-met CPU workflow. Synthetic data are never labeled as the user dataset.', '',
           f"Status: **{report['status']}**. Dataset: **{report['dataset_label']}**.", '',
           'First-use rows use empty private Numba caches. Measured rows reuse only the corresponding variant’s JIT cache and always use a new scene and geometry cache. Disk exports and checkpoint interval 1 remain enabled.', '',
           '| Variant | Regime | Trial | Workflow seconds | Process seconds | Peak tree RSS bytes |',
           '|---|---|---:|---:|---:|---:|']
    for trial in report['trials']:
        result=trial['result']
        lines.append(f"| {trial['variant']} | {trial['regime']} | {trial['trial']} | {result.get('workflow_wall_seconds','failed')} | {result.get('process_wall_seconds','failed')} | {result.get('sampled_peak_process_tree_rss_bytes')} |")
    lines+=['','## Measured warm-JIT, cold-geometry medians','']
    for variant,value in report['medians'].items():lines.append(f'- {variant}: {value:.6f} seconds.')
    if report.get('relative_change_percent') is not None:
        lines.append(f"- Candidate wall-time change relative to paired same-host reference medians: {report['relative_change_percent']:+.2f}%.")
    lines+=['','## Correctness','',f"All paired comparisons passed: **{all(item['comparison']['passed'] for item in report['comparisons']) and bool(report['comparisons'])}**.",
            'TMRT absolute tolerance 0.01; UTCI 0.02; geometry 1e-6. Visibility and final state use exact value comparison. NaN/infinity masks, finite bitwise equality, all bits, and NaN payload equality are reported separately. Raster metadata and final state timestamps must match.', '',
            '## Scope and interpretation','',
            'Workflow timing includes preprocess, walls, full SVF with legacy exports, TMRT/UTCI, checkpoints and final outputs. Process timing additionally includes interpreter/import/instrumentation startup. Per-process startup and stage events contain dependency versions and actual thread caps. CPU usage uses resource.getrusage; RSS tree sampling is optional (psutil), with an explicitly reported 50 ms interval. Existing checkout-local native build caches and OS file caches are not purged; the first-use label refers specifically to the private Numba cache.', '',
            'No historical or cross-machine timing ratio is computed. Profiled trials are extra runs and excluded from performance medians.', '']
    if report.get('reported_note'):lines+=['## Historical figures as reported','',report['reported_note'],'']
    lines+=['Full provenance, stages, usage, output schemas, comparisons and failure details are in comparison.json. Raw scenes are retained alongside each trial.','']
    return '\n'.join(lines)



def positive_integer(value):
    try:
        number=int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError('must be a positive integer') from error
    if number<1:
        raise argparse.ArgumentTypeError('must be a positive integer')
    return number


def parser():
    result=argparse.ArgumentParser(description=__doc__)
    for name in ('reference-checkout','candidate-checkout','scene','workdir'):result.add_argument('--'+name,required=True,type=Path)
    result.add_argument('--met-file',type=Path)
    result.add_argument('--date',help='YYYY-MM-DD; defaults to first selected met row date')
    result.add_argument('--start-time',help='Inclusive ISO datetime or HH:MM; filters staged met rows')
    result.add_argument('--end-time',help='Inclusive ISO datetime or HH:MM; filters staged met rows')
    result.add_argument('--threads',type=int,default=1)
    result.add_argument('--repeats',type=int,default=3)
    result.add_argument('--memory-budget-mib',type=positive_integer,default=4096,
                        help='Fixed RuntimeOptions memory budget for both variants (default:4096 MiB)')
    result.add_argument('--expected-size',type=int,default=600)
    result.add_argument('--expected-steps',type=int,default=19)
    result.add_argument('--building-name',default='Building_DSM.tif')
    result.add_argument('--dem-name',default='DEM.tif')
    result.add_argument('--trees-name',default='Trees.tif')
    result.add_argument('--landcover-name',default='Landcover.tif')
    result.add_argument('--profile',action='store_true',help='One extra candidate run with SVF-stage and tile-worker cProfile; excluded from timings')
    result.add_argument('--dataset-label',default='provided_dataset',help='Use synthetic_generated explicitly for generated inputs')
    result.add_argument('--reported-note',help='Literal historical figures/provenance, never used to calculate a cross-machine ratio')
    return result


def main(argv=None):
    args=parser().parse_args(argv)
    if min(args.threads,args.repeats,args.expected_size,args.expected_steps)<1:raise ValueError('Counts must be positive')
    work=args.workdir.resolve()
    for checkout in (args.reference_checkout.resolve(),args.candidate_checkout.resolve()):
        if work.is_relative_to(checkout):
            raise ValueError('Keep --workdir outside both source checkouts')
    work.mkdir(parents=True,exist_ok=False)
    scene=args.scene.resolve()
    sources={'reference':source_identity(args.reference_checkout),'candidate':source_identity(args.candidate_checkout)}
    names={path.name.lower():path for path in scene.iterdir() if path.is_file()}
    inputs={}
    for key,name in (('building',args.building_name),('dem',args.dem_name),('trees',args.trees_name),('landcover',args.landcover_name)):
        path=names.get(name.lower())
        if path is None:raise ValueError(f'Missing {name}; provide its filename override')
        signature=raster_signature(path)
        if (signature['width'],signature['height'],signature['count'])!=(args.expected_size,args.expected_size,1):
            raise ValueError(f'{path}: expected one-band {args.expected_size} by {args.expected_size}')
        inputs[key]={'path':str(path),'name':path.name,'sha256':digest(path),'schema':signature}
    alignment={(tuple(item['schema']['transform']),item['schema']['projection']) for item in inputs.values()}
    if len(alignment)!=1:raise ValueError('Input raster geotransforms/projections differ')
    met=args.met_file.resolve() if args.met_file else None
    if met is None:
        matches=[path for path in scene.iterdir() if path.is_file() and path.suffix.lower() in {'.txt','.met'}]
        if len(matches)!=1:raise ValueError('Pass --met-file: auto detection requires exactly one root .txt/.met file')
        met=matches[0]
    selection=selected_met(met,args.date,args.start_time,args.end_time)
    if len(selection['timestamps'])!=args.expected_steps:
        raise ValueError(f"Selected {len(selection['timestamps'])} met rows; expected {args.expected_steps}")
    hook=work/'hooks';hook.mkdir()
    hook_code=("import importlib.util, os\n"
               f"_spec=importlib.util.spec_from_file_location('_full_compute_bench_hooks', {str(Path(__file__).resolve())!r})\n"
               "_module=importlib.util.module_from_spec(_spec)\n_spec.loader.exec_module(_module)\n_module._install_hooks()\n")
    (hook/'sitecustomize.py').write_text(hook_code)
    jits={name:work/f'jit-{name}' for name in sources}
    report={'schema':1,'harness_sha256':digest(__file__),'status':'running','dataset_label':args.dataset_label,'reported_note':args.reported_note,
            'sources':sources,'inputs':inputs,'met':{'path':str(met),'sha256':digest(met),
            'selected_sha256':hashlib.sha256(selection['text'].encode()).hexdigest(),
            'date':selection['date'],'timestamps':selection['timestamps']},
            'configuration':vars(args),'tolerances':TOLERANCES,'trials':[],'comparisons':[],'medians':{}}
    def run(variant,regime,index):
        run_root=work/f'{regime}-{index:02d}-{variant}'
        staged=run_root/'scene'
        # Stage only the four original inputs, never any prior computed cache.
        # Install them before starting the timed child workflow.
        staging=work/f'.stage-{regime}-{index:02d}-{variant}';staging.mkdir()
        for value in inputs.values():
            destination=staging/value['name']
            shutil.copyfile(value['path'],destination)
            if digest(destination)!=value['sha256']:
                raise ValueError(f"Input changed while staging: {value['path']}")
        (staging/'met.txt').write_text(selection['text'])
        runtime=dict(cpu_budget=args.threads,workers=1,threads_per_worker=args.threads,
                     memory_budget_bytes=args.memory_budget_mib*1024*1024,
                     checkpoint_interval=1,cache_enabled=True,cache_dir=str(staged/'.solweig-light/geometry'),resume=False)
        kwargs=dict(base_path=str(staged),selected_date_str=selection['date'],
                    building_dsm_filename=inputs['building']['name'],dem_filename=inputs['dem']['name'],
                    trees_filename=inputs['trees']['name'],landcover_filename=inputs['landcover']['name'],
                    ERA_5_z0_find=False,tile_size=args.expected_size,overlap=0,use_own_met=True,
                    own_met_file=str(staged/'met.txt'),use_uhi=True,save_tmrt=True)
        spec=dict(run=str(run_root),checkout=sources[variant]['checkout'],runtime=runtime,kwargs=kwargs,
                  regime=regime,expected_steps=args.expected_steps)
        # This trial root is new; invoke refuses an existing spec.json.
        run_root.mkdir()
        os.replace(staging,staged)
        result=invoke(spec,hook,jits[variant],args.threads)
        record=dict(variant=variant,regime=regime,trial=index,run=str(run_root),result=result)
        report['trials'].append(record);write_json(work/'comparison.json',report)
        return record
    for variant in ('reference','candidate'):
        first=run(variant,'first_use',0)
        if first['result']['status']!='passed':
            report.update(status='failed',failure=f'{variant} first-use workflow/completeness failed; measured trials not started')
            write_json(work/'comparison.json',report)
            (work/'comparison.md').write_text(_markdown(report))
            return 1
    for index in range(args.repeats):
        records={}
        for variant in (('reference','candidate') if index%2==0 else ('candidate','reference')):
            records[variant]=run(variant,'measured',index)
            if records[variant]['result']['status']!='passed':
                report.update(status='failed',failure=f'{variant} trial {index} workflow failed; later runs not started')
                write_json(work/'comparison.json',report)
                (work/'comparison.md').write_text(_markdown(report))
                return 1
        if all(record['result']['status']=='passed' for record in records.values()):
            scratch=work/f'compare-{index:02d}'
            try:
                comparison=compare_runs(records['reference']['run'],records['candidate']['run'],scratch)
            except BaseException:
                comparison={'passed':False,'error':traceback.format_exc()}
            finally:
                shutil.rmtree(scratch,ignore_errors=True)
        else:comparison={'passed':False,'error':'A workflow failed; inspect trial results/logs'}
        report['comparisons'].append({'trial':index,'comparison':comparison})
        write_json(work/'comparison.json',report)
        if not comparison['passed']:
            report.update(status='failed',failure=f'Trial {index} correctness/completeness failed; later trials not started')
            write_json(work/'comparison.json',report)
            (work/'comparison.md').write_text(_markdown(report))
            return 1
    if args.profile:run('candidate','profiled',0)
    for variant in sources:
        samples=[item['result']['workflow_wall_seconds'] for item in report['trials']
                 if item['variant']==variant and item['regime']=='measured' and item['result']['status']=='passed']
        if len(samples)==args.repeats:report['medians'][variant]=statistics.median(samples)
    report['sources_after']={name:source_identity(value['checkout']) for name,value in sources.items()}
    report['sources_unchanged']=all(report['sources_after'][name]['source_tree_sha256']==value['source_tree_sha256']
                                     and report['sources_after'][name]['dirty_diff_sha256']==value['dirty_diff_sha256']
                                     for name,value in sources.items())
    report['harness_unchanged']=digest(__file__)==report['harness_sha256']
    report['status']='passed' if report['harness_unchanged'] and report['sources_unchanged'] and all(item['result']['status']=='passed' for item in report['trials']) and all(item['comparison']['passed'] for item in report['comparisons']) else 'failed'
    report['relative_change_percent']=None
    if report['status']=='passed' and len(report['medians'])==2:
        report['relative_change_percent']=(report['medians']['candidate']/report['medians']['reference']-1)*100
    write_json(work/'comparison.json',report)
    (work/'comparison.md').write_text(_markdown(report))
    print(work/'comparison.md')
    return 0 if report['status']=='passed' else 1


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--child':raise SystemExit(_child(sys.argv[2]))
    raise SystemExit(main())
