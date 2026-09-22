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
"""N8-11 layout-test bootstrap: import the experiment module by path.

All kernels here are serial (no prange, no set_num_threads, no
NUMBA_NUM_THREADS export), so the v5 thread-cap hazard does not apply.
"""
import sys
from pathlib import Path

_LAYOUT = str(Path(__file__).resolve().parents[3] / 'experiments' / 'optimization_v8' / 'layout')
if _LAYOUT not in sys.path:
    sys.path.insert(0, _LAYOUT)
