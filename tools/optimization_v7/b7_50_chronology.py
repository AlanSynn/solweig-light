"""B7-50: small chronology qualification of the integrated native backend.

Runs the public pipeline (run_tile, PIPELINE_CYLINDERS_ANISOTROPIC demand)
over the real 35x32 upstream-CPU reference scene twice — default backend and
SOLWEIG_LIGHT_LW_BACKEND=native — and compares every saved output array
bitwise (uint32 view, NaN payload/sign included). Default-path identity is
also asserted: a second default run must reproduce the first byte-for-byte.

Writes evidence/trials/b7_50_chronology.json. Dev-qualifies the integrated
dispatch; the final 24-tile 1024^2 campaign remains separate (B7-51/52).
"""
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path('/Users/alansynn/Workspace/solweig-light')
import sys  # noqa: E402
sys.path.insert(0, str(REPO / 'src'))

from solweig_light.pipeline import files_by_key, run_tile  # noqa: E402
from solweig_light.runtime import runtime_options  # noqa: E402

PREPARED = REPO / 'tests/reference/small_original_cpu/scene/processed_inputs'
DATE = '2020-07-18'
FLAGS = {f'save_{name}': True for name in
         ('tmrt', 'kup', 'kdown', 'lup', 'ldown', 'shadow', 'wbgt', 'ta', 'wind')}


def _run(tag, overrides, env):
    os.environ.update(env)
    paths = {name: files_by_key(PREPARED / name)['0_0'] for name in
             ('Building_DSM', 'Trees', 'DEM', 'walls', 'aspect', 'metfiles')}
    scratch = tempfile.mkdtemp(prefix=f'v7_b7_50_{tag}_')
    with runtime_options(overrides):
        run_tile(Path(scratch), PREPARED, DATE, '0_0', paths, FLAGS)
    for key in env:
        os.environ.pop(key, None)
    return Path(scratch)


def _arrays(root):
    from solweig_light.io.rasters import read_raster
    out = {}
    for tif in sorted(Path(root).rglob('*.tif*')):
        out[str(tif.relative_to(root))] = read_raster(tif)[0]
    return out


def _bitwise_equal(a, b):
    a, b = np.asarray(a), np.asarray(b)
    if a.shape != b.shape or a.dtype != b.dtype:
        return False
    if a.dtype.kind == 'f':
        return np.array_equal(a.view(np.uint32 if a.itemsize == 4 else np.uint64),
                              b.view(np.uint32 if b.itemsize == 4 else np.uint64))
    return np.array_equal(a, b)


def main():
    record = {'schema': 'solweig-v7-b7-50-chronology-v1',
              'scene': str(PREPARED), 'date': DATE,
              'started_utc': datetime.now(timezone.utc).isoformat()}
    runs = {}
    for tag, env in (('default_1', {}), ('default_2', {}),
                     ('native', {'SOLWEIG_LIGHT_LW_BACKEND': 'native'})):
        overrides = ({'threads_per_worker': 4, 'cpu_budget': 4}
                     if tag.endswith('tpw4') else {})
        runs[tag] = _run(tag, overrides, env)
        print(f'ran {tag} -> {runs[tag]}', flush=True)

    a1, a2, an = _arrays(runs['default_1']), _arrays(runs['default_2']), \
        _arrays(runs['native'])
    record['output_files'] = sorted(a1)
    record['default_identity'] = all(_bitwise_equal(a1[k], a2[k]) for k in a1)
    diffs = [k for k in a1 if not _bitwise_equal(a1[k], an.get(k, np.empty(0)))]
    record['native_bitwise_equal_to_default'] = not diffs
    record['differing_files'] = diffs
    record['file_count'] = len(a1)
    record['finished_utc'] = datetime.now(timezone.utc).isoformat()
    out = REPO / 'optimization_v7_backends/evidence/trials/b7_50_chronology.json'
    out.write_text(json.dumps(record, indent=1))
    print('default identity:', record['default_identity'],
          '| native == default:', record['native_bitwise_equal_to_default'],
          f"({record['file_count']} files)")
    print('written', out)


if __name__ == '__main__':
    main()
