"""L0/L1: error and close-out precedence is checkpoint-exact versus the base.

The accepted sequence discovers trouble in this order, per demanded channel
(shadow, vegetation, vegetation_building, diffuse):

    owner open checks (stable sorted-by-id owner order)
    -> per-leaf interval checks
    -> that channel's fresh decode streams' reserved codes (patch-major,
       pixel-inner)

so a reserved code in an EARLIER channel surfaces before a LATER channel's
open/range error. Every scenario here plants competing errors in different
checkpoints and asserts the prepared path raises the identical type and
message at the identical point (and returns bitwise-identical channels when
nothing is planted).
"""
import numpy as np
import pytest

from conftest import (mapped_roundtrip, original_longwave, original_shortwave,
                      outcome, packed, recipe_longwave, recipe_shortwave,
                      reserved_ternary)

from solweig_light.geometry.visibility import LazyDiffVisibility, PackedVisibility
from solweig_light.geometry.visibility_prepared import prepare_channels

RANGE_MESSAGE = 'Visibility block interval out of range'
RESERVED_MESSAGE = 'Reserved visibility code'
CLOSED_MESSAGE = 'Native visibility is closed'


def scenario(shadow, vegetation, vegetation_building, diffuse, start, stop, patches):
    """Compare the full original demand sequence against the prepared one."""
    baseline = outcome(original_shortwave, shadow, vegetation, vegetation_building,
                       diffuse, start, stop, patches)
    prepared = outcome(recipe_shortwave, shadow, vegetation, vegetation_building,
                       diffuse, start, stop, patches)
    assert baseline[0] == prepared[0]
    if baseline[0] == 'ok':
        for one, other in zip(baseline[1], prepared[1]):
            assert np.array_equal(one.view(np.uint32), other.view(np.uint32))
    else:
        assert baseline[1] is prepared[1], (baseline, prepared)
        assert baseline[2] == prepared[2], (baseline, prepared)
    return baseline


def test_reserved_in_shadow_precedes_closed_vegetation(tmp_path):
    rows = cols = 4
    bad = reserved_ternary(rows, cols, 2, [3])
    clean = PackedVisibility.from_dense(np.zeros((rows, cols, 2), np.float32))
    closed = mapped_roundtrip(tmp_path, clean, 'veg')
    closed.close()
    diffuse = LazyDiffVisibility(bad, closed)
    result = scenario(bad, closed, clean, diffuse, 0, 16, 2)
    assert result[:3] == ('err', IndexError, RESERVED_MESSAGE)


def test_reserved_in_shadow_precedes_range_error_in_building():
    rows = cols = 4
    bad = reserved_ternary(rows, cols, 2, [7])
    clean = PackedVisibility.from_dense(np.zeros((rows, cols, 2), np.float32))
    short_building = PackedVisibility.from_dense(np.zeros((rows, cols, 1), np.float32))
    diffuse = LazyDiffVisibility(clean, clean)
    # patches=2 is valid for shadow/vegetation but exceeds the building's one
    # patch; shadow's reserved discovery must still surface first.
    result = scenario(bad, clean, short_building, diffuse, 0, 16, 2)
    assert result[:3] == ('err', IndexError, RESERVED_MESSAGE)


def test_range_error_in_shadow_precedes_reserved_in_vegetation():
    rows = cols = 4
    shadow = PackedVisibility.from_dense(np.zeros((rows, cols, 2), np.float32))
    bad = reserved_ternary(rows, cols, 2, [1])
    diffuse = LazyDiffVisibility(shadow, bad)
    result = scenario(shadow, bad, shadow, diffuse, 5, 3, 2)  # start > stop
    assert result[:3] == ('err', IndexError, RANGE_MESSAGE)


def test_closed_shadow_owner_precedes_reserved_in_building(tmp_path):
    rows = cols = 4
    clean = PackedVisibility.from_dense(np.zeros((rows, cols, 2), np.float32))
    bad = reserved_ternary(rows, cols, 2, [9])
    shadow = mapped_roundtrip(tmp_path, clean, 'sh')
    shadow.close()
    diffuse = LazyDiffVisibility(shadow, clean)
    try:
        result = scenario(shadow, clean, bad, diffuse, 0, 16, 2)
        assert result[:3] == ('err', RuntimeError, CLOSED_MESSAGE)
    finally:
        shadow.close()


def test_reserved_in_vegetation_surfaces_when_shadow_clean():
    rows = cols = 4
    clean = PackedVisibility.from_dense(np.zeros((rows, cols, 2), np.float32))
    bad = reserved_ternary(rows, cols, 2, [15])
    diffuse = LazyDiffVisibility(clean, bad)
    result = scenario(clean, bad, clean, diffuse, 0, 16, 2)
    assert result[:3] == ('err', IndexError, RESERVED_MESSAGE)


def test_building_reserved_precedes_closed_direct_diffuse(tmp_path):
    rows = cols = 4
    clean = PackedVisibility.from_dense(np.zeros((rows, cols, 2), np.float32))
    bad = reserved_ternary(rows, cols, 2, [0])
    diffuse = mapped_roundtrip(tmp_path, clean, 'diffuse')
    diffuse.close()
    try:
        result = scenario(clean, clean, bad, diffuse, 0, 16, 2)
        assert result[:3] == ('err', IndexError, RESERVED_MESSAGE)
    finally:
        diffuse.close()


def test_direct_diffuse_reserved_surfaces_last():
    rows = cols = 4
    channels = [PackedVisibility.from_dense(np.zeros((rows, cols, 2), np.float32))
                for _ in range(3)]
    bad = reserved_ternary(rows, cols, 2, [10])
    result = scenario(*channels, bad, 0, 16, 2)
    assert result[:3] == ('err', IndexError, RESERVED_MESSAGE)


def test_lazy_pair_reserved_in_shadow_leaf_precedes_vegetation_leaf():
    rows = cols = 4
    channels = [PackedVisibility.from_dense(np.zeros((rows, cols, 2), np.float32))
                for _ in range(3)]
    both_bad = reserved_ternary(rows, cols, 2, [2])
    diffuse = LazyDiffVisibility(both_bad, both_bad)
    result = scenario(*channels, diffuse, 0, 16, 2)
    assert result[:3] == ('err', IndexError, RESERVED_MESSAGE)


def test_lazy_pair_reserved_only_in_vegetation_leaf():
    rows = cols = 4
    channels = [PackedVisibility.from_dense(np.zeros((rows, cols, 2), np.float32))
                for _ in range(3)]
    clean = PackedVisibility.from_dense(np.zeros((rows, cols, 2), np.float32))
    bad = reserved_ternary(rows, cols, 2, [2])
    diffuse = LazyDiffVisibility(clean, bad)
    result = scenario(*channels, diffuse, 0, 16, 2)
    assert result[:3] == ('err', IndexError, RESERVED_MESSAGE)


def test_reuse_slot_reports_closed_owner_after_building_checks(tmp_path):
    """diff_from_shared_decoded re-checks the shared leaves after vb's demand."""
    rows = cols = 4
    clean = PackedVisibility.from_dense(np.zeros((rows, cols, 2), np.float32))
    shadow = mapped_roundtrip(tmp_path, clean, 'sh')
    vegetation = mapped_roundtrip(tmp_path, clean, 'veg')
    diffuse = LazyDiffVisibility(shadow, vegetation)
    try:
        result = scenario(shadow, vegetation, clean, diffuse, 0, 16, 2)
        assert result[0] == 'ok'
    finally:
        shadow.close()
    result = scenario(shadow, vegetation, clean, diffuse, 0, 16, 2)
    assert result[:3] == ('err', RuntimeError, CLOSED_MESSAGE)


def test_interval_boundary_matrix_matches_base():
    rows = cols = 4
    channels = [PackedVisibility.from_dense(np.zeros((rows, cols, 2), np.float32))
                for _ in range(3)]
    diffuse = LazyDiffVisibility(channels[0], channels[1])
    for start, stop, patches in ((-1, 16, 2), (0, 17, 2), (9, 3, 2), (0, 16, 3),
                                 (0, 16, -1), (17, 16, 2), (-2, -1, 0)):
        baseline = outcome(original_shortwave, *channels, diffuse, start, stop, patches)
        assert baseline[0] == 'err' and baseline[1] is IndexError and baseline[2] == RANGE_MESSAGE
        assert scenario(*channels, diffuse, start, stop, patches) == baseline


def test_longwave_precedence_matches_base(tmp_path):
    rows = cols = 4
    clean = PackedVisibility.from_dense(np.zeros((rows, cols, 2), np.float32))
    bad = reserved_ternary(rows, cols, 2, [5])
    building = mapped_roundtrip(tmp_path, clean, 'vb')

    def compare(shadow, vegetation, vegetation_building, start, stop, patches):
        baseline = outcome(original_longwave, shadow, vegetation, vegetation_building,
                           start, stop, patches)
        prepared = outcome(recipe_longwave, shadow, vegetation, vegetation_building,
                           start, stop, patches)
        assert baseline[0] == prepared[0]
        if baseline[0] == 'ok':
            for one, other in zip(baseline[1], prepared[1]):
                assert np.array_equal(one.view(np.uint32), other.view(np.uint32))
        else:
            assert baseline == prepared
        return baseline

    try:
        assert compare(clean, clean, building, 0, 16, 2)[0] == 'ok'
        assert compare(bad, clean, building, 0, 16, 2)[:3] == ('err', IndexError, RESERVED_MESSAGE)
        assert compare(clean, clean, building, 0, 16, 4)[:3] == ('err', IndexError, RANGE_MESSAGE)
        building.close()
        # Vegetation's reserved code surfaces before the building open check.
        assert compare(clean, bad, building, 0, 16, 2)[:3] == ('err', IndexError, RESERVED_MESSAGE)
        assert compare(clean, clean, building, 0, 16, 2)[:3] == ('err', RuntimeError, CLOSED_MESSAGE)
    finally:
        building.close()


def test_prepared_decode_reports_closed_owner_at_open_checkpoint(tmp_path):
    """Close invalidates the borrowed descriptor by protocol, so preparation
    declines and the original path reports the closed owner identically."""
    rows = cols = 4
    clean = packed(np.random.default_rng(3), rows, cols, 2, ('binary',))
    shadow = mapped_roundtrip(tmp_path, clean, 'sh')
    vegetation = packed(np.random.default_rng(4), rows, cols, 2, ('ternary',))
    building = mapped_roundtrip(tmp_path, clean, 'vb')
    diffuse = LazyDiffVisibility(shadow, vegetation)
    try:
        assert outcome(original_shortwave, shadow, vegetation, building, diffuse,
                       0, 16, 2)[0] == 'ok'
    finally:
        shadow.close()
        building.close()
    # The protocol nulls each owner's cached descriptor at close, so closed
    # owners are never admitted with stale borrows.
    assert prepare_channels(shadow, vegetation, building, diffuse) is None
    result = outcome(recipe_shortwave, shadow, vegetation, building, diffuse, 0, 16, 2)
    baseline = outcome(original_shortwave, shadow, vegetation, building, diffuse, 0, 16, 2)
    assert result == baseline
    assert result[:3] == ('err', RuntimeError, CLOSED_MESSAGE)


def test_prepared_decode_preflight_precedes_later_closed_owner(tmp_path):
    """Reserved discovery in shadow precedes a later channel's open check,
    through preparation decline and complete fallback as well."""
    rows = cols = 4
    bad = reserved_ternary(rows, cols, 2, [3])
    clean = PackedVisibility.from_dense(np.zeros((rows, cols, 2), np.float32))
    vegetation = mapped_roundtrip(tmp_path, clean, 'veg')
    diffuse = LazyDiffVisibility(bad, vegetation)
    try:
        assert outcome(original_shortwave, bad, vegetation, clean, diffuse, 0, 16, 2)[:3] \
            == ('err', IndexError, RESERVED_MESSAGE)
    finally:
        vegetation.close()
    assert prepare_channels(bad, vegetation, clean, diffuse) is None
    result = outcome(recipe_shortwave, bad, vegetation, clean, diffuse, 0, 16, 2)
    baseline = outcome(original_shortwave, bad, vegetation, clean, diffuse, 0, 16, 2)
    assert result == baseline
    assert result[:3] == ('err', IndexError, RESERVED_MESSAGE)


def test_prepare_admission_never_raises_and_never_prefires():
    """Admission alone must not raise for payloads the base only rejects later."""
    rows = cols = 4
    bad = reserved_ternary(rows, cols, 2, [0])
    channels = [PackedVisibility.from_dense(np.zeros((rows, cols, 2), np.float32))
                for _ in range(2)]
    # Reserved codes do not surface at prepare time; decode reports them.
    prepared = prepare_channels(bad, *channels, LazyDiffVisibility(bad, channels[0]))
    assert prepared is not None
    result = outcome(prepared.decode, 0, 16, 2)
    assert result[:3] == ('err', IndexError, RESERVED_MESSAGE)


@pytest.mark.parametrize('counts', [(1, 1, 1), (2, 2, 2)])
def test_zero_patch_demands_match_base(counts):
    channels = [PackedVisibility.from_dense(np.zeros((4, 4, count), np.float32))
                for count in counts]
    diffuse = LazyDiffVisibility(channels[0], channels[1])
    result = scenario(*channels, diffuse, 0, 16, 0)
    assert result[0] == 'ok' and all(channel.shape == (16, 0) for channel in result[1])
