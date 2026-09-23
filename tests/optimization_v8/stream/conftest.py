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
"""N9-F1S stream-test bootstrap.

All shared state lives in ``stream_test_helpers`` (uniquely named);
test modules import from THERE, never from ``conftest`` -- bare
``conftest`` is not a unique module name across the optimization_v8
tree and can be shadowed by another suite's conftest in combined
sessions.
"""
import stream_test_helpers  # noqa: F401  (bootstrap + thread pinning)


def pytest_sessionfinish(session, exitstatus):
    # Never leak region-owner threads across the suite.
    from solweig_light._native_dispatch.region import reset_pools_for_tests
    reset_pools_for_tests()
