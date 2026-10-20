"""Static certificates belong only to explicitly owned immutable snapshots."""
import numpy as np
import pytest
from solweig_light.radiation.static_geometry import (
    OwnedRadiationGeometry, radiation_geometry_scope, SVF_KEYS,
    classification_heights, owned_range)
from solweig_light.radiation._math_profile import tan32
from solweig_light.radiation.pipeline_demand import _array_range


def test_owned_tangent_and_ranges_are_exact_and_immutable():
    asvf=np.array([[0.,-0.,.6,1.5]],np.float32)
    fields={key:np.array([[0.,.5,1.]],np.float32) for key in SVF_KEYS}
    owned=OwnedRadiationGeometry(asvf,fields)
    with radiation_geometry_scope(owned):
        np.testing.assert_array_equal(classification_heights(owned.asvf).view('u4'),
                                      tan32(asvf).reshape(-1).view('u4'))
        assert np.shares_memory(classification_heights(owned.asvf),owned.heights)
        for key in SVF_KEYS:
            assert _array_range(owned.svf[key]) == (0.,1.)
            assert owned_range(owned.svf[key].copy()) is None
        asvf[:]=.9
        assert classification_heights(owned.asvf)[0] == 0
        assert not np.shares_memory(classification_heights(asvf),owned.heights)
        with pytest.raises(ValueError):
            owned.asvf.setflags(write=True)
        with pytest.raises(AttributeError):
            owned.asvf=asvf
    assert owned_range(owned.svf['svfE']) is None
