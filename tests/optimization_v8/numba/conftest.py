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
"""N8-12 B-control test bootstrap.

Puts the experiment module and the FROZEN N8-04 reference suite (oracle,
adversarial grid, discriminators -- imported READ-ONLY, never modified) on
``sys.path``.

Thread discipline: same as the reference conftest -- the parallel kernel is
bit-deterministic at any thread count, but the count is pinned and REPORTED
(``LW_TEST_THREADS``). Only ``set_num_threads(min(4, NUMBA_NUM_THREADS))``
is used; no test here exports ``NUMBA_NUM_THREADS`` (the known v5 hazard).
"""
import sys
from pathlib import Path

import numba

# N8-41 vendoring: lw_b_control is imported from the package
# (solweig_light._native_dispatch); only the FROZEN reference suite
# stays on sys.path (read in place, never moved).
_HERE = Path(__file__).resolve().parent
_REFERENCE = _HERE.parents[0] / 'reference'
if str(_REFERENCE) not in sys.path:
    sys.path.insert(0, str(_REFERENCE))

LW_TEST_THREADS = max(1, min(4, numba.config.NUMBA_NUM_THREADS))
numba.set_num_threads(LW_TEST_THREADS)
