"""Bitwise serial/parallel evidence for enabling existing wall pixel kernels."""
import numba
import numpy as np
import pytest
from solweig_light.radiation import wall_shadows


@pytest.mark.parametrize('family', [13, 23])
@pytest.mark.parametrize('dtype', [np.float32, np.float64])
@pytest.mark.parametrize('threads', [1, 4, 10])
@pytest.mark.parametrize('nonfinite', [False, True])
def test_wall_pixel_parallel_bitwise_serial(family, dtype, threads, nonfinite):
    rng = np.random.default_rng(310)
    a = rng.uniform(-2, 4, (9, 11)).astype(dtype)
    canopy = a + rng.uniform(0, 8, a.shape).astype(dtype)
    trunk = a + (canopy - a) * dtype(.25)
    bush = np.zeros_like(a)
    bush[2:4, 3:6] = dtype(1.00001)
    walls = rng.uniform(0, 4, a.shape).astype(dtype)
    walls[::3, ::2] = -0.
    aspect = rng.uniform(0, 2*np.pi, a.shape).astype(dtype)
    if nonfinite:
        a[4, 5] = np.nan
        canopy[3, 4] = np.inf
        trunk[5, 6] = -np.inf
        bush[2, 3] = np.nan
        walls[7, 8] = np.nan
        aspect[1, 2] = np.nan
    arguments = dict(a=a, azimuth=234.5, altitude=17.5, scale=1., walls=walls, aspect=aspect)
    if family == 23:
        arguments.update(vegdem=canopy, vegdem2=trunk, amaxvalue=12., bush=bush)
    calculate = getattr(wall_shadows, f'exact_{family}')
    previous = numba.get_num_threads()
    try:
        numba.set_num_threads(threads)
        with np.errstate(invalid='ignore'):
            expected = calculate(**arguments, parallel=False)
            actual = calculate(**arguments, parallel=True)
        for value, reference in zip(actual, expected, strict=True):
            assert value.dtype == reference.dtype
            np.testing.assert_array_equal(value.view(np.uint32), reference.view(np.uint32))
    finally:
        numba.set_num_threads(previous)
