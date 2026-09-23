"""Caps numba threads at 2 for the GVF v5 differentials.

Only this directory's tests are capped, and only downwards (min(2, current)),
so shared pytest sessions never see their larger pools rejected by other
suites. For the full isolation run use:
NUMBA_NUM_THREADS=2 uv run --extra test pytest tests/optimization_v5/gvf/
"""
import numba
import pytest


@pytest.fixture(autouse=True)
def bounded_threads():
    previous = numba.get_num_threads()
    numba.set_num_threads(max(1, min(2, previous)))
    yield
    numba.set_num_threads(previous)
