"""C6-42 phase memory admission tests (L0, synthetic shape descriptors only).

All shapes here are synthetic accounting inputs — no raster files, no
numerical runs, no 1024 simulation.  The worst-case numbers asserted are the
C6-03 M2 arithmetic (commit e7a2d6ec) reproduced from first principles by
``solweig_light.runtime_memory``; the M4 instrumented run (35x32) is cited in
evidence for the parent-footprint magnitude, not used as a bound.

The module under test is inert until the integrator wires it: nothing in
``src`` imports ``runtime_memory`` (asserted by test_module_is_inert).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
SRC = REPO / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from solweig_light.runtime import (  # noqa: E402
    ResourceAdmissionError,
    estimate_memory,
)
from solweig_light.runtime_memory import (  # noqa: E402
    CHECKPOINT_PULSE_PLANES,
    DEFAULT_EXPORT_STREAM_BYTES,
    DEFAULT_GDAL_CACHE_RATIO,
    DEFAULT_PARENT_FOOTPRINT_BYTES,
    DIGEST_PULSE_PLANES,
    DenseCubeFallbackNotChargedError,
    INVENTORY_LINES,
    PHASES,
    PHASE_GEOMETRY,
    PHASE_PREPROCESS,
    PHASE_SIMULATION,
    PREPROCESS_F64_PLANES,
    PhaseAdmissionPlan,
    PhaseJob,
    Reservation,
    TileShapeDescriptor,
    VISIBILITY_BINARY,
    VISIBILITY_NATIVE_CACHE,
    VISIBILITY_RAW,
    VISIBILITY_TERNARY,
    VISIBILITY_UNKNOWN_COLD,
    admission_inputs_from_options,
    default_gdal_cache_bytes,
    geometry_reservation,
    legacy_estimate_total_bytes,
    plan_phase_admission,
    preprocess_reservation,
    simulation_reservation,
)

GIB = 1024 ** 3
MIB = 1024 * 1024
# M2 §2 scenario: 1024x1024, 153 patches, 12 wind channels, block1024,
# GDAL cache at the unset-env default of 5% of a 32 GiB host.
WORST_ROWS = WORST_COLS = 1024
WORST_PATCHES = 153
WORST_WIND = 12
WORST_BLOCK = 1024
WORST_SHAPE = TileShapeDescriptor(WORST_ROWS, WORST_COLS, WORST_PATCHES, WORST_WIND, WORST_BLOCK)
WORST_PIXELS = WORST_ROWS * WORST_COLS
PLANE_F32 = WORST_PIXELS * 4
GDAL_32GIB_HOST = (32 * GIB * DEFAULT_GDAL_CACHE_RATIO[0]) // DEFAULT_GDAL_CACHE_RATIO[1]
BUDGET_12GIB = 12 * GIB

LEGACY_WORST_CASE_BYTES = 3_730_374_656  # 3.4742 GiB (M2 §2, D04)
RAW_PAYLOAD_WORST = 3 * WORST_PATCHES * WORST_PIXELS * 4  # 1,925,185,536 B


# ---------------------------------------------------------------------------
# Gate 1: the actual lifetime inventory, reproduced from first principles
# ---------------------------------------------------------------------------

def test_legacy_worst_case_reproduced_from_first_principles():
    """The M2 worst case (3,730,374,656 B = 3.4742 GiB) is reproduced exactly,
    and matches the public runtime estimate it anchors."""
    total = legacy_estimate_total_bytes(WORST_SHAPE)
    assert total == LEGACY_WORST_CASE_BYTES
    assert total == estimate_memory(
        WORST_ROWS, WORST_COLS, WORST_PATCHES, WORST_WIND, WORST_BLOCK
    ).total_bytes
    assert abs(total / GIB - 3.4742) < 0.0005


def test_dtype64_reserve_repriced_at_eight_bytes():
    """M2 §6b: the 32-plane float64 reserve was priced at float32; the
    corrected charge is 8 bytes/value, worth +128 MiB at 1024.  This prices
    the legacy promotion reserve at its denominated dtype (D04); per the
    C6-60 review (F7) no resident float64 family exists in-tile —
    walls/aspects are float32 residents — so the reserve is promotion slack,
    not resident arrays."""
    corrected = simulation_reservation(WORST_SHAPE, gdal_cache_bytes=0,
                                       export_overlap=False, native_bytes=0)
    expected_live = (192 + WORST_WIND) * PLANE_F32 + 32 * WORST_PIXELS * 8
    assert corrected.live_array_bytes == expected_live
    delta = corrected.live_array_bytes - (192 + 32 + WORST_WIND) * PLANE_F32
    assert delta == 32 * WORST_PIXELS * 4 == 134_217_728


def test_inventory_table_reconciles_with_legacy_envelope():
    """The enumerated M1 families fit the accounting envelope the reservation
    uses: persistent + core transients <= 192 f32 planes; adding the
    fallback-only route stays within 192 + 32 planes; the raw payload is
    charged separately (459 plane equivalents at 1024/P153)."""
    assert {line.phase for line in INVENTORY_LINES} == set(PHASES)
    for line in INVENTORY_LINES:
        assert line.lifetime in (
            "persistent_tile", "transient_stage", "transient_timestep", "pulse",
        )
        assert line.source.startswith("M1 S"), line.family

    def planes(phase, exclude_fallback=False):
        total = 0
        for line in INVENTORY_LINES:
            if line.phase != phase or line.bytes_per_value == 0:
                continue
            if exclude_fallback and "fallback" in line.family:
                continue
            total += line.planes
        return total

    sim_core = planes(PHASE_SIMULATION, exclude_fallback=True)
    sim_all = planes(PHASE_SIMULATION)
    # 6 f64-width planes (walls/aspects) are covered by the 32-plane reserve.
    assert sim_core <= 192, sim_core
    assert sim_all <= 192 + 32, sim_all
    # persistent+transient split sanity (78 persistent incl. state/wind,
    # rest transient or pulse)
    persistent = sum(
        line.planes for line in INVENTORY_LINES
        if line.phase == PHASE_SIMULATION and line.lifetime == "persistent_tile"
        and line.bytes_per_value
    )
    assert persistent == 40 + 18 + 2 + 12 + 6
    # C6-60 review F7: tile-resident walls/aspects are float32; float64 is
    # preprocess-intermediate only.
    walls_line = next(
        line for line in INVENTORY_LINES if line.family == "walls/aspects residents"
    )
    assert (walls_line.dtype, walls_line.bytes_per_value) == ("float32", 4)
    assert walls_line.planes == 2
    # packed payload = 459 f32 plane equivalents; excluded from plane counts
    payload_lines = [
        line for line in INVENTORY_LINES
        if line.bytes_per_value == 0 and "payload" in line.family
    ]
    assert len(payload_lines) == 2  # geometry + simulation rows
    assert RAW_PAYLOAD_WORST == 459 * PLANE_F32


def test_packed_mode_formulas_match_visibility_validation():
    """Payload bytes follow geometry/visibility.py:90-92 exactly."""
    binary = geometry_reservation(WORST_SHAPE, visibility_mode=VISIBILITY_BINARY,
                                  export_overlap=False, gdal_cache_bytes=0, native_bytes=0)
    ternary = geometry_reservation(WORST_SHAPE, visibility_mode=VISIBILITY_TERNARY,
                                   export_overlap=False, gdal_cache_bytes=0, native_bytes=0)
    assert binary.payload_bytes == 3 * WORST_PATCHES * ((WORST_PIXELS * 1 + 7) // 8)
    assert ternary.payload_bytes == 3 * WORST_PATCHES * ((WORST_PIXELS * 2 + 7) // 8)
    unknown = geometry_reservation(WORST_SHAPE, visibility_mode=VISIBILITY_UNKNOWN_COLD,
                                   export_overlap=False, gdal_cache_bytes=0, native_bytes=0)
    assert unknown.payload_bytes == RAW_PAYLOAD_WORST  # cold unknown reserves raw (D04)


def test_native_cache_mode_charges_resident_mapped_pages():
    """M2 §7: a read-only mapping becomes resident on touch; mmap is not free
    memory.  native_cache moves the payload charge from heap to mapped pages
    with the same magnitude."""
    raw = simulation_reservation(WORST_SHAPE, gdal_cache_bytes=0,
                                 export_overlap=False, native_bytes=0)
    mapped = simulation_reservation(WORST_SHAPE, visibility_mode=VISIBILITY_NATIVE_CACHE,
                                    gdal_cache_bytes=0, export_overlap=False, native_bytes=0)
    assert mapped.payload_bytes == 0
    assert mapped.mapped_bytes == RAW_PAYLOAD_WORST
    assert mapped.total_bytes == raw.total_bytes


def test_phase_shape_differentiation_corrects_over_admission():
    """M2 §6g: preprocess used ~0.2 GiB but paid the 3.4742 GiB simulation
    estimate.  The corrected phase reservations are differentiated (all
    corrected charges still included)."""
    pre = preprocess_reservation(WORST_SHAPE, gdal_cache_bytes=GDAL_32GIB_HOST)
    geo = geometry_reservation(WORST_SHAPE, gdal_cache_bytes=GDAL_32GIB_HOST)
    sim = simulation_reservation(WORST_SHAPE, gdal_cache_bytes=GDAL_32GIB_HOST)
    assert pre.total_bytes < geo.total_bytes < sim.total_bytes
    assert pre.total_bytes < LEGACY_WORST_CASE_BYTES < sim.total_bytes
    assert pre.total_bytes == (
        PREPROCESS_F64_PLANES * WORST_PIXELS * 8
        + GDAL_32GIB_HOST + 768 * MIB + DEFAULT_EXPORT_STREAM_BYTES
    )
    # exact corrected worst-case components (M2 §2 + §6 corrections)
    assert sim.total_bytes == 5_741_962_854
    assert geo.total_bytes == 4_758_857_318
    assert sim.write_pulse_bytes == (DIGEST_PULSE_PLANES + CHECKPOINT_PULSE_PLANES) * PLANE_F32
    assert sim.gdal_cache_bytes == GDAL_32GIB_HOST


def test_default_gdal_cache_derivation(monkeypatch):
    import solweig_light.runtime_memory as rm
    monkeypatch.setattr(rm, "_physical_memory_bytes", lambda: 32 * GIB)
    assert default_gdal_cache_bytes() == GDAL_32GIB_HOST == 1_717_986_918
    monkeypatch.setattr(rm, "_physical_memory_bytes", lambda: 16 * GIB)
    assert default_gdal_cache_bytes() == 858_993_459  # 5% of 16 GiB, floored


# ---------------------------------------------------------------------------
# Gate 2: admission boundary at a 12 GiB budget (1024/P153 worst case)
# ---------------------------------------------------------------------------

def _worst_jobs(phase, count):
    return [
        PhaseJob(phase, WORST_ROWS, WORST_COLS, WORST_PATCHES, WORST_WIND,
                 WORST_BLOCK, visibility_mode=VISIBILITY_UNKNOWN_COLD,
                 tile=f"{phase}_{index}")
        for index in range(count)
    ]


def test_boundary_12gib_admits_two_workers_rejects_four():
    """Corrected boundary: at 12 GiB with every M2 §6 charge applied, the
    1024/P153 raw worst case admits 2 concurrent workers (2x2 geometry +
    simulation fits) and rejects 4x1."""
    sim = simulation_reservation(WORST_SHAPE, gdal_cache_bytes=GDAL_32GIB_HOST)
    geo = geometry_reservation(WORST_SHAPE, gdal_cache_bytes=GDAL_32GIB_HOST)
    tree_two_sim = 2 * sim.total_bytes + DEFAULT_PARENT_FOOTPRINT_BYTES
    tree_three_sim = 3 * sim.total_bytes + DEFAULT_PARENT_FOOTPRINT_BYTES
    tree_geo_sim = geo.total_bytes + sim.total_bytes + DEFAULT_PARENT_FOOTPRINT_BYTES
    assert tree_two_sim <= BUDGET_12GIB          # 11,913,422,438 <= 12 GiB
    assert tree_geo_sim <= BUDGET_12GIB          # 10,930,316,902 <= 12 GiB
    assert tree_three_sim > BUDGET_12GIB         # 17,655,385,292 > 12 GiB

    mixed = _worst_jobs(PHASE_GEOMETRY, 1) + _worst_jobs(PHASE_SIMULATION, 1)
    plan = plan_phase_admission(
        mixed, budget_bytes=BUDGET_12GIB, active_workers=2,
        gdal_cache_bytes=GDAL_32GIB_HOST, threads_per_worker=2,
    )
    assert plan.status == "admitted"
    assert plan.admissible_workers == 2
    assert plan.native_threads == 4  # 2 workers x 2 threads (2x2)

    four = _worst_jobs(PHASE_SIMULATION, 4)
    plan_q = plan_phase_admission(
        four, budget_bytes=BUDGET_12GIB, gdal_cache_bytes=GDAL_32GIB_HOST,
        policy="queue",
    )
    assert (plan_q.status, plan_q.admissible_workers, plan_q.deferred_count) == (
        "queued", 2, 2,
    )
    with pytest.raises(ResourceAdmissionError) as excinfo:
        plan_phase_admission(
            four, budget_bytes=BUDGET_12GIB, gdal_cache_bytes=GDAL_32GIB_HOST,
            policy="reject",
        )
    # the rejection names the arithmetic, not a vague failure:
    # 4 x 5,741,962,854 B (4x1 raw worst case, block1024)
    assert "22,967,851,416" in str(excinfo.value)


def test_three_worker_boundary_raw_worst_and_legacy_gap():
    """C6-60 review F6 refinement: 4x1 is NOT the unique breach
    configuration.  At a 12 GiB budget the legacy model budget-admits 3x1
    (3 x 3,730,374,656 = 11,191,123,968 <= 12 GiB) while the raw-worst tree
    (3 x corrected reservation + parent = 17,655,385,292 B = 16.44 GiB)
    breaches the cap.  The corrected calculator charges every raw-worst
    component per worker, so budget-admission and raw-safety coincide:
    3x1 is rejected and the raw-safe worker count is 2."""
    three = _worst_jobs(PHASE_SIMULATION, 3)
    sim = simulation_reservation(WORST_SHAPE, gdal_cache_bytes=GDAL_32GIB_HOST)
    # every raw-worst component is charged inside one per-worker reservation
    assert sim.total_bytes == (
        sim.payload_bytes + sim.live_array_bytes + sim.decoded_block_bytes
        + sim.native_bytes + sim.gdal_cache_bytes + sim.write_pulse_bytes
        + sim.export_stream_bytes + sim.mapped_bytes
    )
    raw_worst_tree = 3 * sim.total_bytes + DEFAULT_PARENT_FOOTPRINT_BYTES
    assert raw_worst_tree == 17_655_385_292 > BUDGET_12GIB

    with pytest.raises(ResourceAdmissionError) as excinfo:
        plan_phase_admission(
            three, budget_bytes=BUDGET_12GIB, gdal_cache_bytes=GDAL_32GIB_HOST,
            policy="reject",
        )
    assert "only 2 fit" in str(excinfo.value)
    queued = plan_phase_admission(
        three, budget_bytes=BUDGET_12GIB, gdal_cache_bytes=GDAL_32GIB_HOST,
        policy="queue",
    )
    assert (queued.admissible_workers, queued.deferred_count) == (2, 1)

    # the legacy public model has no raw-worst dimension: it admits 3x1 on
    # estimate sums alone, which is exactly the gap the corrected calculator
    # closes (review F6: "3x1 ... raw worst ... 15.72 GiB > 12 GiB cap" under
    # m2's composition; identical conclusion at this composition).
    from solweig_light.runtime import RuntimeOptions, plan_admission
    legacy = RuntimeOptions(
        memory_budget_bytes=BUDGET_12GIB, workers=3, cpu_budget=3,
        threads_per_worker=1, block_pixels=1024,
    )
    legacy_jobs = [
        {"rows": WORST_ROWS, "cols": WORST_COLS, "patches": WORST_PATCHES,
         "windchannels": WORST_WIND}
        for _ in range(3)
    ]
    assert plan_admission(legacy_jobs, legacy).active_workers == 3


def test_writer_queue_shrinks_admissible_width():
    """D04 writer_queue_bytes term: a bounded staging queue is charged
    against the same budget and can reduce the safe width."""
    four = _worst_jobs(PHASE_SIMULATION, 4)
    plan = plan_phase_admission(
        four, budget_bytes=BUDGET_12GIB, gdal_cache_bytes=GDAL_32GIB_HOST,
        writer_queue_bytes=1 * GIB, policy="queue",
    )
    # base 12 - 0.4 - 1 = 10.6 GiB < 2 x 5.348 GiB, so only one of the four
    # jobs fits at a time; the other three stay queued
    assert (plan.admissible_workers, plan.deferred_count) == (1, 3)


def test_admission_inputs_from_existing_options():
    """Private planning reads the existing RuntimeOptions fields only (D04:
    no public signature/default/as_dict changes)."""
    from solweig_light.runtime import RuntimeOptions
    options = RuntimeOptions(
        memory_budget_bytes=BUDGET_12GIB, cpu_budget=4,
        workers=8, threads_per_worker=2,
    )
    inputs = admission_inputs_from_options(options)
    assert inputs == {
        "budget_bytes": BUDGET_12GIB,
        "active_workers": 2,  # min(8, 4 // 2)
        "threads_per_worker": 2,
    }
    assert inputs == json.loads(json.dumps(inputs))


# ---------------------------------------------------------------------------
# Gate 3: oversubscription — reject raises in-process; queue-or-fail explicit
# ---------------------------------------------------------------------------

def test_reject_policy_raises_in_process_runtime_error_identity():
    four = _worst_jobs(PHASE_SIMULATION, 4)
    with pytest.raises(ResourceAdmissionError) as excinfo:
        plan_phase_admission(
            four, budget_bytes=BUDGET_12GIB, gdal_cache_bytes=GDAL_32GIB_HOST,
            policy="reject",
        )
    # same class object as runtime.py exports (type identity survives
    # _child_exception rebuilds; m3 §7.4 — never plain pickling)
    assert type(excinfo.value) is ResourceAdmissionError
    import solweig_light.runtime_memory as rm
    assert rm.ResourceAdmissionError is ResourceAdmissionError


def test_queue_policy_defers_without_raising():
    four = _worst_jobs(PHASE_SIMULATION, 4)
    plan = plan_phase_admission(
        four, budget_bytes=BUDGET_12GIB, gdal_cache_bytes=GDAL_32GIB_HOST,
        policy="queue",
    )
    assert plan.status == "queued"
    assert plan.admitted_count == 2 and plan.deferred_count == 2
    assert plan.reservation_base_bytes == BUDGET_12GIB - DEFAULT_PARENT_FOOTPRINT_BYTES


def test_individually_infeasible_job_raises_in_both_policies():
    """A phase that can never fit raises even under queue policy: queueing
    cannot fix an impossible job (missing/absent relief is explicit, not a
    silent skip).  5.5 GiB budget leaves 5.1 GiB base < 5.348 GiB sim."""
    for policy in ("reject", "queue"):
        with pytest.raises(ResourceAdmissionError) as excinfo:
            plan_phase_admission(
                _worst_jobs(PHASE_SIMULATION, 1), budget_bytes=int(5.5 * GIB),
                gdal_cache_bytes=GDAL_32GIB_HOST, policy=policy,
            )
        assert "queueing cannot make this phase fit" in str(excinfo.value)


def test_tree_overheads_exhausting_budget_raise_before_reservations():
    with pytest.raises(ResourceAdmissionError, match="already exhausts"):
        plan_phase_admission(
            _worst_jobs(PHASE_SIMULATION, 1), budget_bytes=BUDGET_12GIB,
            gdal_cache_bytes=GDAL_32GIB_HOST,
            parent_footprint_bytes=BUDGET_12GIB,
        )


# ---------------------------------------------------------------------------
# Gate 4 (semantics): missing data errors, never fake zeros; JSON-safe
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad", [0, -4, True, 2.5, "1024", None])
def test_malformed_shape_raises_and_never_yields_zero_reservation(bad):
    with pytest.raises((ValueError, TypeError)):
        PhaseJob(PHASE_SIMULATION, bad, WORST_COLS)


def test_missing_shape_is_an_error_not_a_zero_charge():
    """A PhaseJob cannot even be constructed without dimensions — there is no
    code path that treats unknown shape as a 0-byte reservation."""
    import dataclasses
    fields = {f.name for f in dataclasses.fields(PhaseJob)}
    assert {"rows", "cols"} <= fields  # required positional, no defaults
    with pytest.raises(TypeError):
        PhaseJob(PHASE_SIMULATION)  # type: ignore[call-arg]


def test_dense_fallback_outside_geometry_is_a_descriptor_error():
    with pytest.raises(DenseCubeFallbackNotChargedError):
        plan_phase_admission(
            [PhaseJob(PHASE_SIMULATION, 64, 64, dense_fallback=True)],
            budget_bytes=BUDGET_12GIB, gdal_cache_bytes=0,
        )


def test_unknown_phase_and_visibility_rejected():
    with pytest.raises(ValueError, match="phase"):
        PhaseJob("render", 64, 64)
    with pytest.raises(ValueError, match="visibility_mode"):
        PhaseJob(PHASE_GEOMETRY, 64, 64, visibility_mode="holographic")
    with pytest.raises(ValueError, match="policy"):
        plan_phase_admission(
            [PhaseJob(PHASE_SIMULATION, 64, 64)], budget_bytes=BUDGET_12GIB,
            policy="yaw",
        )


def test_no_negative_budget_arithmetic():
    with pytest.raises(ValueError):
        plan_phase_admission(
            [PhaseJob(PHASE_SIMULATION, 64, 64)], budget_bytes=0,
        )
    with pytest.raises(ValueError):
        plan_phase_admission(
            [PhaseJob(PHASE_SIMULATION, 64, 64)], budget_bytes=BUDGET_12GIB,
            writer_queue_bytes=-1,
        )
    # no component of any reservation is ever negative
    for phase in PHASES:
        job = PhaseJob(phase, 64, 64)
        plan = plan_phase_admission([job], budget_bytes=BUDGET_12GIB, gdal_cache_bytes=0)
        for reservation in plan.reservations:
            for name, value in reservation.inventory().items():
                if name.endswith("_bytes"):
                    assert value >= 0, (phase, name)


def test_json_safety_round_trips():
    """D09: JSON-safe descriptors.  Every exported object survives
    json.dumps/json.loads with equality, including a full plan."""
    jobs = _worst_jobs(PHASE_GEOMETRY, 1) + _worst_jobs(PHASE_SIMULATION, 3)
    plan = plan_phase_admission(
        jobs, budget_bytes=BUDGET_12GIB, gdal_cache_bytes=GDAL_32GIB_HOST,
        writer_queue_bytes=256 * MIB, policy="queue",
    )
    revived = PhaseAdmissionPlan.from_dict(json.loads(json.dumps(plan.to_dict())))
    assert revived == plan
    for job in jobs:
        assert PhaseJob.from_dict(json.loads(json.dumps(job.to_dict()))) == job
    for reservation in plan.reservations:
        assert Reservation.from_dict(json.loads(json.dumps(reservation.to_dict()))) == reservation
    assert TileShapeDescriptor.from_dict(json.loads(json.dumps(WORST_SHAPE.to_dict()))) == WORST_SHAPE


def test_module_is_inert_until_wired():
    """Gate: no behavioural change without integration.  The private module
    adds no native-math imports of its own (numba would appear in sys.modules
    only if the module pulled it in).

    Integrated-tree form (C6-70): wiring is real, so the importer set is
    pinned to exactly the intended wiring points — api.py (W1 simulation
    admission) and runtime.py (W3 GDAL_CACHEMAX cap).  service.py (W2
    geometry-phase admission) is deliberately deferred to the C6-40 phase
    adapter per m7 §3; when it lands, extend this pin."""
    code = (
        "import sys; sys.path.insert(0, " + repr(str(SRC)) + "); "
        "import solweig_light.runtime; "
        "before = set(sys.modules); "
        "import solweig_light.runtime_memory; "
        "added = {m.split('.')[0] for m in set(sys.modules) - before}; "
        "assert 'numba' not in added, 'numba imported'; "
        "assert 'osgeo' not in added, 'gdal imported'"
    )
    subprocess.run([sys.executable, "-c", code], check=True)

    src_root = SRC / "solweig_light"
    importers = sorted(
        path.name
        for path in src_root.rglob("*.py")
        if path.name != "runtime_memory.py"
        and "runtime_memory" in path.read_text(encoding="utf-8")
    )
    assert importers == ["api.py", "runtime.py"], f"unexpected importers in src: {importers}"


def test_shape_from_building_dsm_missing_file_raises_explicitly():
    """Metadata-only shape helper fails explicitly on a missing raster —
    never a fabricated or zero-byte shape (success path needs a real raster
    and is left to the L2 integration gate, see m7 recipe)."""
    from solweig_light.runtime_memory import shape_from_building_dsm
    with pytest.raises(ResourceAdmissionError) as excinfo:
        shape_from_building_dsm({"Building_DSM": "/nonexistent/Building_DSM.tif"})
    assert "/nonexistent/Building_DSM.tif" in str(excinfo.value)
    with pytest.raises(ResourceAdmissionError, match="required"):
        shape_from_building_dsm({})


def test_visibility_mode_and_export_overlap_are_forwarded():
    """C6-42 review fix: plan_phase_admission must forward the per-job
    visibility_mode/export_overlap descriptors instead of silently reserving
    the raw fallback for every job (default descriptors are unchanged, so
    all boundary results are unchanged)."""
    binary = PhaseJob(
        PHASE_GEOMETRY, 1024, 1024, 153, 12, 1024,
        visibility_mode=VISIBILITY_BINARY, export_overlap=False, tile="b",
    )
    plan = plan_phase_admission(
        [binary], budget_bytes=BUDGET_12GIB, gdal_cache_bytes=GDAL_32GIB_HOST,
    )
    reservation = plan.reservations[0]
    assert reservation.visibility_mode == VISIBILITY_BINARY
    assert reservation.payload_bytes == 3 * WORST_PATCHES * ((WORST_PIXELS + 7) // 8)
    assert reservation.export_stream_bytes == 0

    default = PhaseJob(PHASE_GEOMETRY, 1024, 1024, 153, 12, 1024, tile="u")
    default_plan = plan_phase_admission(
        [default], budget_bytes=BUDGET_12GIB, gdal_cache_bytes=GDAL_32GIB_HOST,
    )
    assert default_plan.reservations[0].payload_bytes == RAW_PAYLOAD_WORST
    assert (default_plan.reservations[0].export_stream_bytes
            == DEFAULT_EXPORT_STREAM_BYTES)


def test_preprocess_jobs_reject_visibility_publication_descriptors():
    """Preprocess has no visibility payload and no publication window, so
    non-default visibility_mode/export_overlap raise instead of being
    silently ignored."""
    for kwargs in ({"visibility_mode": VISIBILITY_BINARY},
                   {"visibility_mode": VISIBILITY_RAW},
                   {"export_overlap": False}):
        with pytest.raises(ValueError, match="do not apply to preprocess"):
            plan_phase_admission(
                [PhaseJob(PHASE_PREPROCESS, 1024, 1024, 153, 12, 1024, **kwargs)],
                budget_bytes=BUDGET_12GIB, gdal_cache_bytes=GDAL_32GIB_HOST,
            )
    # defaults still admit
    plan = plan_phase_admission(
        [PhaseJob(PHASE_PREPROCESS, 1024, 1024, 153, 12, 1024)],
        budget_bytes=BUDGET_12GIB, gdal_cache_bytes=GDAL_32GIB_HOST,
    )
    assert plan.status == "admitted"


def test_reservation_inventory_reports_plane_equivalents():
    sim = simulation_reservation(WORST_SHAPE, gdal_cache_bytes=GDAL_32GIB_HOST)
    inv = sim.inventory()
    assert inv["payload_plane_equivalents_f32"] == 459
    assert inv["live_array_plane_equivalents_f32"] == 192 + 12 + 64  # 32 planes at f64
    assert json.dumps(inv)  # audit dict stays JSON-safe
