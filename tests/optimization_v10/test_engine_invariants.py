"""First-evaluation semantics of the reused shortwave subexpressions."""

import numpy as np
import pytest

from solweig_light.radiation.engine import Kup_veg_2015a


def test_kup_direct_overflow_precedes_invalid_diffuse():
    ordinary = np.ones((2, 3), dtype=np.float32)
    overflowing = np.full_like(ordinary, np.finfo(np.float32).max)
    invalid_svf = np.full_like(ordinary, np.inf)
    # The first direct multiplication overflows. The later diffuse expression
    # also has 0*Inf, but must not replace that first exception after hoisting.
    with np.errstate(over='raise', invalid='raise'):
        with pytest.raises(FloatingPointError, match='overflow encountered in multiply'):
            Kup_veg_2015a(np.float32(2), np.float32(0), np.float32(1),
                         np.float32(45), invalid_svf, np.float32(.2),
                         ordinary, overflowing, ordinary, ordinary, ordinary,
                         ordinary, ordinary, ordinary, ordinary, ordinary, ordinary)


def test_kup_first_direct_sine_precedes_invalid_diffuse():
    ordinary = np.ones((2, 3), dtype=np.float32)
    infinite = np.full_like(ordinary, np.inf)
    # An infinite reflected term times sin(0) is the first invalid operation.
    # Configuring overflow to raise makes a reordered diffuse evaluation
    # observably wrong even when both calls eventually abort.
    with np.errstate(over='raise', invalid='raise'):
        with pytest.raises(FloatingPointError, match='invalid value encountered in multiply'):
            Kup_veg_2015a(np.float32(1), np.float32(2), np.float32(1),
                         np.float32(0), np.full_like(ordinary, np.finfo(np.float32).max),
                         np.float32(.2), ordinary, infinite, ordinary, ordinary,
                         ordinary, ordinary, ordinary, ordinary, ordinary, ordinary, ordinary)
