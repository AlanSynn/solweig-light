#SOLWEIG-GPU: GPU-accelerated SOLWEIG model for urban thermal comfort simulation
#Copyright (C) 2022–2025 Harsh Kamath and Naveen Sudharsan

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful, but
#WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#General Public License for more details.
"""N9-F4 policy-suite bootstrap.

The qualification suite (``test_lw_default_policy.py``) is archived with
the N8 native row: the selector and its loader are no longer part of the
installed runtime (repo-only research copies under
``experiments/optimization_v8/native_dispatch/``), and the fabricated-
evidence fixtures they needed are gone with them. What remains live in
this directory is the legacy-DX parity pin (``test_legacy_env_parity``
-- rewritten for the structural N9 route); it needs no fixtures beyond
the teardown hygiene below. The uniquely-named ``policy_test_helpers``
module stays on ``sys.path`` for the archived research copy.
"""
import sys
from pathlib import Path

import pytest

for _p in (Path(__file__).resolve().parent,):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


@pytest.fixture(autouse=True)
def _pool_teardown():
    """The same teardown hygiene the other suites keep: a suite that
    drove a routed call never leaks region-owner threads."""
    yield
    import solweig_light._native_dispatch.region.region_pool as rp
    rp.reset_pools_for_tests()
