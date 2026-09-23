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
"""Private N8-41 vendoring home for the longwave dispatch machinery.

This subpackage is the N8-22 qualification selector (``lw_default_policy``),
the N8-11 producer (``direct_aosoa``), the N8-12 Numba B consumer
(``lw_b_control``), the N8-13 native consumer (``lw_native_aosoa``), the
N8-14 region owner (``region``), the N8-10 native handle (``native_handle``)
and the N8-21 installed-artifact loader (``installed_loader``) -- relocated
from the maintainer tree (``experiments/optimization_v8/...``) by the N8-41
early vendoring (n841-7/n841-8). It is PRIVATE: nothing here is re-exported
from :mod:`solweig_light`, nothing here is a public or DX-contract surface,
and ``import solweig_light`` never imports any of it (pinned by
``tests/optimization_v8/policy/test_legacy_env_parity.py``).

Wheel gating is unchanged (n841-8): rows stay records-gated, the shipped
empty registry resolves row A, and the expert ``SOLWEIG_LIGHT_LW_BACKEND``
route keeps serving the legacy B7-32 dev-build path until the wheels-time
flip. The maintainer-tree copies of the relocated files remain in place
this commit as unused duplicates (evidence durability); deletion is a
later explicit step.

Repo anchors: two maintainer-tree locations stay resolution targets of
the vendored modules until the wheel-assembly work (n841-1/n841-3,
``install_assets``) gives them installed homes -- the N8-20 build driver
``build_native.py`` (reused READ-ONLY for artifact content verification by
``installed_loader`` and ``lw_native_aosoa``) and the N8-13 staged
generation directory (``lw_native_aosoa._DEFAULT_STAGE``). See
``experiments_dir`` below.

Wheel content (n841-3 install_assets): the shipped EMPTY qualification
registry (``qualification_registry.json`` next to ``lw_default_policy``)
ships as package data, so an installed selector resolves row A from empty
records BY DESIGN (the ``[absent]`` fail-closed path, never the
missing-file ``[malformed]`` accident of an unpackaged registry). The
promotion gate tool (``optimization_v8_native_default/tools/
promotion_gate.py``) deliberately stays maintainer-tree and ships in no
wheel: promotion gating is a qualification-time activity in a repo
checkout, never a user-runtime one. With the shipped-empty registry the
auto path returns before any record validation, so the resolve-time
promotion-gate re-verification (``lw_default_policy._assess_promotion``,
which resolves the tool repo-relatively and fails loudly -- never
mis-qualifying -- where the maintainer tree is absent) is unreachable in
every shipped-state resolve.
"""
from pathlib import Path

#: The maintainer-tree root of the relocated machinery, resolved from this
#: package (``src/solweig_light/_native_dispatch`` -> repo root). Present
#: only in a repo checkout.
_EXPERIMENTS_ROOT = Path(__file__).resolve().parents[3] \
    / 'experiments' / 'optimization_v8'


def experiments_dir(*parts: str) -> Path:
    """Anchor a vendored module's repo-checkout dependency.

    Returns the maintainer-tree path (never imports from it -- callers
    that need a module from there insert it on ``sys.path`` explicitly so
    ``sys.modules`` identity stays shared with the packaging/loader test
    suites). Raises ``FileNotFoundError`` when the maintainer tree is
    absent (installed wheel): the loud-and-clear failure beats silently
    pointing at a nonexistent location; the installed homes land with the
    N8-41 wheel assembly (n841-1/n841-3).
    """
    path = _EXPERIMENTS_ROOT.joinpath(*parts)
    if not path.is_dir():
        raise FileNotFoundError(
            f'solweig_light._native_dispatch repo anchor {path} is absent: '
            f'this module currently resolves maintainer-tree dependencies '
            f'(N8-20 build driver, N8-13 staging) from a repo checkout; '
            f'the packaged resolution lands with the N8-41 wheel work')
    return path
