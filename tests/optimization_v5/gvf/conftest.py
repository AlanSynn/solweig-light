"""Caps numba threads at 2 for the GVF v5 differentials before numba loads."""
import os

os.environ.setdefault('NUMBA_NUM_THREADS', '2')

import numba
import pytest


@pytest.fixture(autouse=True)
def bounded_threads():
    previous = numba.get_num_threads()
    numba.set_num_threads(max(1, min(2, previous)))
    yield
    numba.set_num_threads(previous)
