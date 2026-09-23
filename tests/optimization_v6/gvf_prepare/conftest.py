"""Caps numba threads at 2 for the GVF preparation differentials.

Same isolation policy as the v5 GVF suite: only this directory's tests are
capped, and only downwards, so shared pytest sessions never see their larger
pools rejected by other suites. Full isolation:
NUMBA_NUM_THREADS=2 <venv python> -m pytest tests/optimization_v6/gvf_prepare/
"""
import numba
import pytest


@pytest.fixture(autouse=True)
def bounded_threads():
    previous = numba.get_num_threads()
    numba.set_num_threads(max(1, min(2, previous)))
    yield
    numba.set_num_threads(previous)
