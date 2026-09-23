#SOLWEIG-GPU: GPU-accelerated SOLWEIG model for urban thermal comfort simulation
#Copyright (C) 2022–2025 Harsh Kamath and Naveen Sudharsan

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
"""N8-13 native-consumer test bootstrap: pytest fixtures ONLY.

Shared helpers (frozen-module reuse, AoSoA packing; the helpers module
live in native_test_helpers.py -- uniquely named so combined test-tree
collection cannot shadow another package's conftest (N-D2 repair, same
class as the region bug the n8-rev-n8-14 delta review closed). Importing
the helpers module here keeps the side effects (sys.path, module under
test) identical for any test that still relies on conftest having run.
"""

import pytest

pytest.skip(
    'archived with the N8 native row and qualification machinery '
    '(n8_32 selection closed N9 F3 NATIVE_LOSS; archived at N9 F4 '
    'closed_cpu_only): research copies preserved under '
    'experiments/optimization_v8/native_dispatch/',
    allow_module_level=True)
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from native_test_helpers import _NATIVE_DIR, _PACKAGING_DIR  # noqa: F401
from solweig_light._native_dispatch import lw_native_aosoa  # noqa: F401  (side effect: import under test)


@pytest.fixture(scope='session')
def generation_dir(tmp_path_factory):
    """A content-verified N8-20 generation for this session.

    Prefers the canonical build under the experiment's own stage/ (built
    by build_aosoa.py; content-verified by the adapter's loader gate);
    falls back to an explicit build through the same N8-20 driver into a
    session temp dir; skips when ISPC is unavailable. In the fallback case
    the adapter's default stage is repointed at the temp staging so every
    call site resolves the same generation.
    """
    stage = _NATIVE_DIR / 'stage'
    if stage.is_dir():
        found = sorted(p for p in stage.iterdir()
                       if p.is_dir() and p.name.startswith('lw-g8-'))
        if found:
            return found[-1]
    ispc = shutil.which('ispc')
    if ispc is None and Path('/opt/homebrew/bin/ispc').is_file():
        ispc = '/opt/homebrew/bin/ispc'
    if ispc is None:
        pytest.skip('no published lw-g8 generation and no ispc to build one')
    staging = tmp_path_factory.mktemp('lw_aosoa_stage')
    cmd = [sys.executable, str(_PACKAGING_DIR / 'build_native.py'), 'build',
           '--kernel', str(_NATIVE_DIR / 'lw_primary_aosoa.ispc'),
           '--staging', str(staging), '--artifact', 'liblw_native_g8.dylib',
           '--target', 'neon-i32x8', '--ispc', ispc,
           '--ispc-version', '1.31.0']
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        pytest.skip(f'build through N8-20 driver failed (rc='
                    f'{proc.returncode}): {proc.stderr[-400:]}')
    import json
    gen_dir = Path(json.loads(proc.stdout)['generation_dir'])
    lw_native_aosoa._DEFAULT_STAGE = gen_dir.parent
    return gen_dir
