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
"""Repo-only research archive for the N8 native row and qualification
machinery (N9 F4: closed_cpu_only disposition).

Nothing in this package is importable from an installed wheel: it lives
under ``experiments/`` outside ``src/`` and ships in no package-data
glob. The archived modules are the N9-F3 terminal NATIVE_LOSS record's
research surface:

* ``lw_default_policy`` -- the N8-22 qualification selector (registry
  read per call; removed from the shipped path, which now decides
  structurally, see ``solweig_light.radiation._lw_dispatch``).
* ``qualification_registry.json`` -- the shipped-empty registry.
* ``lw_native_aosoa`` -- the N8-13 native AoSoA entry loader.
* ``installed_loader`` / ``native_handle`` / ``build_native`` -- the
  N8-21/N8-20 artifact identity, handle and build-driver machinery.
* ``aplus_decode`` -- the N9 A-plus comparator (mode-specialized decode
  + transcribed fused kernels, parity-pinned against the shipped A8
  legacy; never dispatched).
* ``region_native_reduce`` -- the whole-scene native handle consumer
  extracted from ``region.consumers`` when the shipped package dropped
  its native dependency.

The modules import each other with RELATIVE imports inside this package;
repo test suites reach them via ``sys.path`` insertion of this directory
(see ``tests/optimization_v8`` archived-feature markers and the n9
producer comparator test). ``experiments_dir`` keeps its original
anchor semantics (repo root / ``experiments`` / ``optimization_v8``).
"""
from pathlib import Path

#: The maintainer-tree root this archive's repo anchors resolve against:
#: ``experiments/optimization_v8`` (two levels up from this file).
_EXPERIMENTS_ROOT = Path(__file__).resolve().parents[1]


def experiments_dir(*parts: str) -> Path:
    """Anchor an archived module's repo-checkout dependency.

    Returns the maintainer-tree path (never imports from it -- callers
    that need a module from there insert it on ``sys.path`` explicitly so
    ``sys.modules`` identity stays shared with the packaging/loader test
    suites). Raises ``FileNotFoundError`` when the maintainer tree is
    absent.
    """
    path = _EXPERIMENTS_ROOT.joinpath(*parts)
    if not path.is_dir():
        raise FileNotFoundError(
            f'native_dispatch archive repo anchor {path} is absent: '
            f'this module resolves maintainer-tree dependencies '
            f'(N8-20 build driver, N8-13 staging) from a repo checkout')
    return path
