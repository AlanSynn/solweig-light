"""S03b: the GDAL cache default and its admission charge share one view.

The census recorded the default run refused inside a 6 GB Slurm step on a
376 GB node: the per-worker GDAL charge derived from physical RAM while the
budget derived from the cgroup view, so the charge exceeded the entire
budget. D07 requires the reservation to match the applied cache cap; the fix
derives both from the most restrictive stable view (physical RAM vs finite
cgroup limit). These tests pin the probe algebra, the admission outcome in
the census configuration, and the unchanged ordinary-host default.
"""
import pytest

import solweig_light.runtime as rt
import solweig_light.runtime_memory as rm

PHYSICAL = 376 * 1024**3
LIMIT = 6 * 1024**3
HEADROOM = 5 * 1024**3 + 860 * 1024**2


def container_host(monkeypatch, limit=LIMIT):
    monkeypatch.setattr(rm, '_physical_memory_bytes', lambda: PHYSICAL)
    monkeypatch.setattr(rm, '_container_memory_limit_bytes',
                        (lambda: limit) if limit is not None else (lambda: None))
    # The budget side (runtime.default_memory_budget_bytes) probes the same
    # views through runtime's own module globals.
    monkeypatch.setattr(rt, '_physical_memory_bytes', lambda: PHYSICAL)
    monkeypatch.setattr(rt, '_available_host_memory_bytes', lambda: PHYSICAL)
    monkeypatch.setattr(rt, '_container_memory_headroom_bytes',
                        (lambda: HEADROOM) if limit is not None else (lambda: None))


def test_container_limit_caps_default(monkeypatch):
    container_host(monkeypatch)
    assert rm.default_gdal_cache_bytes() == (LIMIT * 5) // 100


def test_no_limit_keeps_physical_view(monkeypatch):
    container_host(monkeypatch, limit=None)
    assert rm.default_gdal_cache_bytes() == (PHYSICAL * 5) // 100


def test_larger_than_physical_limit_ignored(monkeypatch):
    container_host(monkeypatch, limit=400 * 1024**3)
    assert rm.default_gdal_cache_bytes() == (PHYSICAL * 5) // 100


def test_census_configuration_admits(monkeypatch):
    """376 GB node, 6 GB step: admission outcome for the census cell.

    S10 recorded this cell refusing because the physical-RAM GDAL charge
    (18.8 GB) exceeded the whole budget; the S10 view-sharing fix made it
    admit.  The X03 Stage-B recalibration (protocol
    ``phase2_x03_stage_b_protocol.json``, part_recalibration ``table_safety``:
    "small tiles price at the 1024^2 entry") re-floors the simulation price
    at the MEASURED production envelope -- 3 x 826,736,640 B + capped GDAL
    + pulse/stream = 2,815,852,800 B for any tile up to 1024^2 -- which
    exceeds the 6 GB step's reservation base (2,705,745,510 B after parent)
    in BOTH container-view arms.  The refusal is the conservative direction
    (never under-price a child) and names its arithmetic; production 1024^2
    tiles on compute budgets are unaffected.  The D07 charge/budget
    view-sharing property itself is unchanged and stays pinned by
    ``test_container_limit_caps_default`` / ``test_no_limit_keeps_physical_view``."""
    container_host(monkeypatch)
    budget = rt.default_memory_budget_bytes()
    # The census repro cell: the landcover golden tile (32x35), not a
    # production-size tile.
    job = rm.PhaseJob(phase='simulation', rows=32, cols=35)
    # Capped-charge arm: the GDAL charge is now min(5%-of-limit, 256 MiB), so
    # the cached-view failure mode stays closed -- but the envelope floor
    # (2,815,852,800 B) exceeds the 2,705,745,510 B base and refuses.
    with pytest.raises(rm.ResourceAdmissionError) as excinfo:
        rm.plan_phase_admission([job], budget_bytes=budget,
                                active_workers=1, threads_per_worker=1)
    assert "2,815,852,800" in str(excinfo.value)
    assert "2,705,745,510" in str(excinfo.value)
    # No-limit arm: same envelope floor, same refusal (the old physical-RAM
    # 18.8 GB charge no longer exists on any arm -- the cap bounds it).
    monkeypatch.setattr(rm, '_container_memory_limit_bytes', lambda: None)
    with pytest.raises(rm.ResourceAdmissionError):
        rm.plan_phase_admission([job], budget_bytes=budget,
                                active_workers=1, threads_per_worker=1)
