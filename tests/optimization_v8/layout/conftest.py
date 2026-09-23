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
"""N8-11 layout-test bootstrap.

N8-41 vendoring: direct_aosoa is imported from the package
(solweig_light._native_dispatch); this suite needs no sys.path
bootstrap anymore.

All kernels here are serial (no prange, no set_num_threads, no
NUMBA_NUM_THREADS export), so the v5 thread-cap hazard does not apply.
"""
