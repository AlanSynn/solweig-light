"""The returned GVF sum must not retain discarded directional accumulators."""
from types import SimpleNamespace
import weakref

import numpy as np

from solweig_light.radiation.gvf_prepared import _finish_prepared


def test_gvf_sum_releases_batched_accumulator_owner():
    shape = (7, 9)
    step = SimpleNamespace(azimuth_degrees=np.arange(5, 359, 20),
                           sky_emis=np.float32(300),
                           buildings=np.ones(shape, dtype=np.float32))
    accumulated = np.arange(16*np.prod(shape), dtype=np.float32).reshape((16, *shape)).copy()
    retained = tuple(plane.copy() for plane in accumulated)
    expected = _finish_prepared(step, retained)
    owner = weakref.ref(accumulated)
    actual = _finish_prepared(step, accumulated)
    for found, wanted in zip(actual, expected):
        assert found.dtype == wanted.dtype
        np.testing.assert_array_equal(found.view(np.uint32), wanted.view(np.uint32))
    del accumulated
    assert owner() is None
    assert actual[-2].base is None
