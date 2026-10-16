"""X03 Stage-B recalibration invariants (protocol ``part_recalibration``).

The simulation reservation is repriced from the full-plane component model to
the MEASURED per-child peak RSS envelope table x ``SIMULATION_ENVELOPE_MARGIN``,
with the GDAL charge capped at ``GDAL_CHILD_CACHE_CAP_BYTES`` (the same ceiling
worker children receive via ``GDAL_CACHEMAX``, so the permitted envelope equals
the priced envelope by construction).  Evidence: Stage-A/A2 (job 14098987,
1024^2 envelope 826,736,640 B, n~40 children) and Stage-B0 (job 14100529,
2048^2 envelope 3,852,328,960 B, cross-thread TMRT bitwise 24/24), archived
under ``development/optimization_s11_envelope_headroom/evidence/``.

Each test here carries one frozen invariant (I1-I6).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[3] / "src"
sys.path.insert(0, str(SRC))  # noqa: E402

import solweig_light.runtime_memory as rm  # noqa: E402
from solweig_light.runtime_memory import (  # noqa: E402
    DEFAULT_PARENT_FOOTPRINT_BYTES,
    PhaseJob,
    TileShapeDescriptor,
    legacy_estimate_total_bytes,
    plan_phase_admission,
    simulation_reservation,
)

GIB = 1024 ** 3
MIB = 1024 * 1024
ENVELOPE_1024 = 826_736_640      # measured max, Stage-A/A2 (job 14098987)
ENVELOPE_2048 = 3_852_328_960    # measured max, Stage-B0 (job 14100529)
GDAL_32GIB_HOST = (32 * GIB * rm.DEFAULT_GDAL_CACHE_RATIO[0]) // rm.DEFAULT_GDAL_CACHE_RATIO[1]
LOGIN_GDAL_BYTES = 115 * MIB     # observed login-node resolved default
SHAPE_1024 = TileShapeDescriptor(1024, 1024, 153, 12, 1024)
SHAPE_2048 = TileShapeDescriptor(2048, 2048, 153, 12, 1024)
SHAPE_4096 = TileShapeDescriptor(4096, 4096, 153, 12, 1024)


def _price(shape, gdal=GDAL_32GIB_HOST, **kwargs):
    return simulation_reservation(shape, gdal_cache_bytes=gdal, **kwargs).total_bytes


def test_i1_price_covers_margin_times_measured_at_calibrated_points():
    """I1: at every calibrated shape the total is at least MARGIN x measured."""
    assert rm.SIMULATION_ENVELOPE_TABLE[0] == (1024 * 1024, ENVELOPE_1024)
    assert rm.SIMULATION_ENVELOPE_TABLE[1] == (2048 * 2048, ENVELOPE_2048)
    assert _price(SHAPE_1024) >= rm.SIMULATION_ENVELOPE_MARGIN * ENVELOPE_1024
    assert _price(SHAPE_2048) >= rm.SIMULATION_ENVELOPE_MARGIN * ENVELOPE_2048


def test_i2_monotone_in_pixels_and_patches():
    """I2: the total is monotone non-decreasing in pixels (across the
    below-table, between-entries, and above-table regions) and in patches
    (the payload term on non-unknown_cold modes and the pulse)."""
    pixel_sweep = [256, 512, 1000, 1024, 1025, 1500, 2047, 2048, 2049, 4096]
    totals = [
        _price(TileShapeDescriptor(n, n, 153, 12, min(n, 1024)))
        for n in pixel_sweep
    ]
    assert totals == sorted(totals)
    patch_sweep = [1, 2, 50, 153, 400]
    patch_totals = [
        _price(TileShapeDescriptor(512, 512, p, 12, 512),
               gdal=LOGIN_GDAL_BYTES, visibility_mode="binary")
        for p in patch_sweep
    ]
    assert patch_totals == sorted(patch_totals)


def test_i3_login_scale_refusal_preserved():
    """I3: at the observed login view (~2.2 GB budget, 0.43 GB parent,
    ~115 MiB GDAL default) one 1024^2/153 simulation job still refuses with
    the explicit arithmetic (price ~2.76 GB > base ~1.77 GB)."""
    with pytest.raises(rm.ResourceAdmissionError) as excinfo:
        plan_phase_admission(
            [PhaseJob("simulation", 1024, 1024, 153, 12, 1024)],
            budget_bytes=int(2.2 * GIB), gdal_cache_bytes=LOGIN_GDAL_BYTES,
        )
    message = str(excinfo.value)
    assert "needs about 2,760,179,712 B" in message
    assert "queueing cannot make this phase fit" in message


def test_i4_twelve_1024_jobs_fit_36gib_budget():
    """I4: 12 concurrent 1024^2/153 jobs fit a 36 GB budget minus parent --
    the X03 E2E finalist (12x2) admits under the recalibrated price."""
    jobs = [PhaseJob("simulation", 1024, 1024, 153, 12, 1024, tile=f"t{i}")
            for i in range(12)]
    plan = plan_phase_admission(
        jobs, budget_bytes=36 * GIB, gdal_cache_bytes=GDAL_32GIB_HOST,
        policy="queue",
    )
    assert (plan.status, plan.admissible_workers, plan.deferred_count) == (
        "admitted", 12, 0,
    )
    assert plan.reservations[0].total_bytes == 2_908_028_928
    assert 12 * 2_908_028_928 + DEFAULT_PARENT_FOOTPRINT_BYTES <= 36 * GIB


def test_i5_reject_semantics_unchanged():
    """I5: policy='reject' raises ResourceAdmissionError with the unchanged
    message shape; the empty-jobs guard and unknown-shape behavior are
    unchanged."""
    with pytest.raises(rm.ResourceAdmissionError, match="requested 14 concurrent"):
        plan_phase_admission(
            [PhaseJob("simulation", 1024, 1024, 153, 12, 1024)] * 14,
            budget_bytes=36 * GIB, gdal_cache_bytes=GDAL_32GIB_HOST,
            policy="reject",
        )
    with pytest.raises(ValueError, match="at least one job"):
        plan_phase_admission([], budget_bytes=36 * GIB)
    with pytest.raises(ValueError, match="phase"):
        PhaseJob("render", 64, 64)


def test_i6_legacy_estimate_untouched():
    """I6: ``legacy_estimate_total_bytes`` keeps the pre-C6-42 anchor
    (3,730,374,656 B at the M2 worst case) -- the above-table path and the
    public ``estimate_memory`` surface are unchanged by the recalibration."""
    assert legacy_estimate_total_bytes(SHAPE_1024) == 3_730_374_656
    assert _price(SHAPE_4096) > rm.SIMULATION_ENVELOPE_MARGIN * ENVELOPE_2048


def test_permitted_gdal_cache_equals_priced_cap():
    """The cap charged to the budget is the cap children receive: the child
    environment sets GDAL_CACHEMAX to at most GDAL_CHILD_CACHE_CAP_BYTES,
    so a child can never allocate more block cache than the reservation
    priced (protocol alternative D rejected the uncapped variant)."""
    from solweig_light.runtime import RuntimeOptions, _child_environment
    env = _child_environment(RuntimeOptions())
    cap_mib = rm.GDAL_CHILD_CACHE_CAP_BYTES // MIB
    assert int(env["GDAL_CACHEMAX"]) <= cap_mib
    assert int(env["GDAL_CACHEMAX"]) >= 1
