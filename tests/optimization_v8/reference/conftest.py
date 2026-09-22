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
"""N8-04 reference-test bootstrap.

Thread discipline: the parallel kernel is bit-deterministic at any thread
count (per-pixel accumulators, no cross-pixel reduction), but the count is
pinned anyway and REPORTED (module attribute ``LW_TEST_THREADS``) so runs are
reproducible. The known v5 hazard -- exporting NUMBA_NUM_THREADS while also
calling set_num_threads with a larger value -- is avoided: only
set_num_threads(min(4, NUMBA_NUM_THREADS)) is used, and no test here exports
NUMBA_NUM_THREADS.
"""
import sys
from pathlib import Path

import numba

_SYS_PATH_ADDED = str(Path(__file__).resolve().parent)
if _SYS_PATH_ADDED not in sys.path:
    sys.path.insert(0, _SYS_PATH_ADDED)

LW_TEST_THREADS = max(1, min(4, numba.config.NUMBA_NUM_THREADS))
numba.set_num_threads(LW_TEST_THREADS)
