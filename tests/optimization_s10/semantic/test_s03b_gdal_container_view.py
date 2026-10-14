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
    """376 GB node, 6 GB step: the default run must admit after the fix and
    must still be refused when the container limit is absent (the recorded
    census behavior), pinning the causal direction."""
    container_host(monkeypatch)
    budget = rt.default_memory_budget_bytes()
    # The census repro cell: the landcover golden tile (32x35), not a
    # production-size tile — this configuration refused before the fix.
    job = rm.PhaseJob(phase='simulation', rows=32, cols=35)
    # Post-fix: the 5%-of-limit charge fits alongside one active worker.
    plan = rm.plan_phase_admission([job], budget_bytes=budget,
                                   active_workers=1, threads_per_worker=1)
    assert plan.admissible_workers >= 1
    # Causal guard: with no cgroup limit the physical-RAM charge (18.8 GB)
    # exceeds the whole budget again — the old, recorded refusal.
    monkeypatch.setattr(rm, '_container_memory_limit_bytes', lambda: None)
    with pytest.raises(rm.ResourceAdmissionError):
        rm.plan_phase_admission([job], budget_bytes=budget,
                                active_workers=1, threads_per_worker=1)
