#SOLWEIG-GPU: GPU-accelerated SOLWEIG model for urban thermal comfort simulation
#Copyright (C) 2022–2025 Harsh Kamath and Naveen Sudharsan

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
"""N8-10 loader test bootstrap.

Puts the experiments loader dir and the frozen N8-04 reference dir on
sys.path (frozen reference oracle), imports the module under test, and
READ-ONLY reuses the N8-04
adversarial input constructor from
tests/optimization_v8/reference/test_typed_graph_identity.py via importlib
under a distinct module name -- nothing under tests/reference/ or
tests/optimization_v8/reference/ is modified.
"""
import importlib.util
import os
import shutil
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
# N8-41 vendoring: native_handle is imported from the package
# (solweig_light._native_dispatch); only the FROZEN reference suite
# stays on sys.path.
_REFERENCE_DIR = _REPO / 'tests' / 'optimization_v8' / 'reference'

if str(_REFERENCE_DIR) not in sys.path:
    sys.path.insert(0, str(_REFERENCE_DIR))

from solweig_light._native_dispatch import native_handle  # noqa: E402  (the module under test)

# Read-only reuse of the frozen N8-04 adversarial grid constructor.
_spec = importlib.util.spec_from_file_location(
    'lw_identity_grid', _REFERENCE_DIR / 'test_typed_graph_identity.py')
lw_identity_grid = importlib.util.module_from_spec(_spec)
sys.modules['lw_identity_grid'] = lw_identity_grid
_spec.loader.exec_module(lw_identity_grid)


@pytest.fixture()
def nh():
    """Fresh module state per test (registry/negative cache/generation)."""
    native_handle.reset_for_tests()
    return native_handle


@pytest.fixture(scope='session')
def artifact_dir(tmp_path_factory):
    """A validated artifact directory for this session.

    Prefers a copy of the user-cache B7 artifacts (untrusted until the
    loader's own stamp/digest gate accepts them); falls back to an explicit
    expert build; skips if neither is possible.
    """
    src = Path(os.environ.get('SOLWEIG_LIGHT_NATIVE_CACHE',
                              Path.home() / '.cache' / 'solweig-light'
                              / 'native'))
    target = tmp_path_factory.mktemp('native_artifact')
    if (src / 'liblw_native_g8.dylib').is_file():
        for name in ('liblw_native_g4.dylib', 'liblw_native_g8.dylib',
                     'build_stamp.json'):
            if (src / name).is_file():
                shutil.copy2(src / name, target / name)
        try:
            native_handle.reset_for_tests()
            native_handle.prepare_native_handle(artifact_dir=target)
            return target
        except native_handle.NativeHandleError:
            pass  # unvalidated copy: fall through to an explicit rebuild
    if shutil.which('ispc') or Path('/opt/homebrew/bin/ispc').exists():
        native_handle.expert_build(target)
        return target
    pytest.skip('no validated native artifact available and no ispc to '
                'build one')
