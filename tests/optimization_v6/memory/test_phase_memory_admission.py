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
    not resident arrays.

    X03 Stage-B amendment: the legacy component formula now governs only
    ABOVE the measured envelope table (4096^2 here); at calibrated pixel
    counts the reservation is the measured envelope x margin
    (test_simulation_envelope_table_recalibration)."""
    above = TileShapeDescriptor(4096, 4096, WORST_PATCHES, WORST_WIND, WORST_BLOCK)
    corrected = simulation_reservation(above, gdal_cache_bytes=0,
                                       export_overlap=False, native_bytes=0)
    expected_live = (192 + WORST_WIND) * above.pixels * 4 + 32 * above.pixels * 8
    assert corrected.live_array_bytes == expected_live
    delta = corrected.live_array_bytes - (192 + 32 + WORST_WIND) * above.pixels * 4
    assert delta == 32 * above.pixels * 4 == 2_147_483_648


def test_simulation_envelope_table_recalibration():
    """X03 Stage-B (C6-42 amendment): at calibrated pixel counts the
    simulation reservation is the MEASURED per-child peak RSS envelope
    (Stage-A/A2: 826,736,640 B at 1024^2; Stage-B0: 3,852,328,960 B at
    2048^2) x SIMULATION_ENVELOPE_MARGIN, plus the GDAL charge capped at
    GDAL_CHILD_CACHE_CAP_BYTES -- the same ceiling children receive via
    GDAL_CACHEMAX, so the permitted envelope equals the priced envelope.
    Evidence: phase2_x03_stage_{a,a2,b0}_findings.json."""
    import solweig_light.runtime_memory as rm

    sim = simulation_reservation(WORST_SHAPE, gdal_cache_bytes=GDAL_32GIB_HOST)
    assert sim.live_array_bytes == rm.SIMULATION_ENVELOPE_MARGIN * 826_736_640
    assert sim.payload_bytes == 0  # unknown_cold payload subsumed in the measurement
    # block 1024 scratch beyond the measured block-128 configuration
    # (hardening, Stage-B review MAJOR-1): 10,027,008 - 1,253,376
    assert sim.decoded_block_bytes == 8_773_632 and sim.native_bytes == 0
    assert sim.gdal_cache_bytes == 256 * MIB  # capped, not the 1.7 GiB 5%-of-32G
    assert sim.write_pulse_bytes == (DIGEST_PULSE_PLANES + CHECKPOINT_PULSE_PLANES) * PLANE_F32
    assert sim.total_bytes == (
        sim.live_array_bytes + sim.gdal_cache_bytes + sim.write_pulse_bytes
        + sim.export_stream_bytes + sim.decoded_block_bytes + sim.mapped_bytes
    ) == 2_916_802_560
    # at the MEASURED configuration (block 128, production default) the
    # residual is exactly zero and the price is the byte-identical E2E
    # measured value (job 14104820 admission echo)
    measured_shape = TileShapeDescriptor(1024, 1024, 153, 12, 128)
    assert simulation_reservation(
        measured_shape, gdal_cache_bytes=GDAL_32GIB_HOST).total_bytes == 2_908_028_928
    # every calibrated price covers margin x measured (I1); price grows with
    # pixels (I2); above the table the legacy envelope applies unchanged (I6 path)
    assert sim.total_bytes >= rm.SIMULATION_ENVELOPE_MARGIN * 826_736_640
    big = simulation_reservation(
        TileShapeDescriptor(2048, 2048, WORST_PATCHES, WORST_WIND, WORST_BLOCK),
        gdal_cache_bytes=GDAL_32GIB_HOST)
    assert big.total_bytes > sim.total_bytes
    assert big.live_array_bytes == rm.SIMULATION_ENVELOPE_MARGIN * 3_852_328_960
    above = simulation_reservation(
        TileShapeDescriptor(4096, 4096, WORST_PATCHES, WORST_WIND, WORST_BLOCK),
        gdal_cache_bytes=GDAL_32GIB_HOST)
    assert above.payload_bytes == RAW_PAYLOAD_WORST * 16  # legacy full-plane pricing
    assert above.native_bytes == 768 * MIB and above.decoded_block_bytes > 0


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
    with the same magnitude.

    X03 Stage-B amendment: under the measured envelope the unknown_cold raw
    payload is subsumed in the envelope (raw.payload_bytes == 0), so the
    native_cache mapping charge now appears as an ADDITION on top of the raw
    total instead of a like-for-like move."""
    raw = simulation_reservation(WORST_SHAPE, gdal_cache_bytes=0,
                                 export_overlap=False)
    mapped = simulation_reservation(WORST_SHAPE, visibility_mode=VISIBILITY_NATIVE_CACHE,
                                    gdal_cache_bytes=0, export_overlap=False)
    assert raw.payload_bytes == 0  # subsumed in the measured envelope
    assert mapped.payload_bytes == 0
    assert mapped.mapped_bytes == RAW_PAYLOAD_WORST
    assert mapped.total_bytes == raw.total_bytes + RAW_PAYLOAD_WORST


def test_phase_shape_differentiation_corrects_over_admission():
    """M2 §6g: preprocess used ~0.2 GiB but paid the 3.4742 GiB simulation
    estimate.  The corrected phase reservations are differentiated.

    X03 Stage-B amendment: the simulation phase itself was the remaining
    over-priced member — the component model charged ~5.35 GiB against a
    measured 0.77 GiB child RSS (24/24 records).  Under the measured
    envelope the simulation child is now the LIGHTEST phase at 1024^2
    (pre < sim < geo), which is the correction working as intended; the
    legacy 3.4742 GiB estimate stays as the above-table conservative bound."""
    pre = preprocess_reservation(WORST_SHAPE, gdal_cache_bytes=GDAL_32GIB_HOST)
    geo = geometry_reservation(WORST_SHAPE, gdal_cache_bytes=GDAL_32GIB_HOST)
    sim = simulation_reservation(WORST_SHAPE, gdal_cache_bytes=GDAL_32GIB_HOST)
    assert pre.total_bytes < sim.total_bytes < geo.total_bytes
    assert sim.total_bytes < LEGACY_WORST_CASE_BYTES  # repriced below the legacy estimate
    assert pre.total_bytes == (
        PREPROCESS_F64_PLANES * WORST_PIXELS * 8
        + GDAL_32GIB_HOST + 768 * MIB + DEFAULT_EXPORT_STREAM_BYTES
    )
    # exact recalibrated components (Stage-A/A2/B0 measured envelope table)
    assert sim.total_bytes == 2_916_802_560
    assert geo.total_bytes == 4_758_857_318
    assert sim.write_pulse_bytes == (DIGEST_PULSE_PLANES + CHECKPOINT_PULSE_PLANES) * PLANE_F32
    assert sim.gdal_cache_bytes == 256 * MIB  # capped, matches the child GDAL_CACHEMAX


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


def test_boundary_12gib_admits_four_workers_rejects_five():
    """Recalibrated boundary (X03 Stage-B amendment): at 12 GiB with the
    measured-envelope price (3 x 0.77 GiB + capped GDAL + pulse + stream =
    2,908,028,928 B/worker), the 1024/P153 production case admits 4
    concurrent workers and rejects 5x1.  The boundary moved OUT by 2 workers
    versus the component model: the component model was the conservative
    side at calibrated shapes (measured RSS <= envelope, 24/24 records)."""
    sim = simulation_reservation(WORST_SHAPE, gdal_cache_bytes=GDAL_32GIB_HOST)
    geo = geometry_reservation(WORST_SHAPE, gdal_cache_bytes=GDAL_32GIB_HOST)
    tree_two_sim = 2 * sim.total_bytes + DEFAULT_PARENT_FOOTPRINT_BYTES
    tree_four_sim = 4 * sim.total_bytes + DEFAULT_PARENT_FOOTPRINT_BYTES
    tree_five_sim = 5 * sim.total_bytes + DEFAULT_PARENT_FOOTPRINT_BYTES
    tree_geo_sim = geo.total_bytes + sim.total_bytes + DEFAULT_PARENT_FOOTPRINT_BYTES
    assert tree_two_sim <= BUDGET_12GIB          #  6,263,101,850 <= 12 GiB
    assert tree_geo_sim <= BUDGET_12GIB          #  8,105,156,608 <= 12 GiB
    assert tree_four_sim <= BUDGET_12GIB         # 12,096,706,970 <= 12 GiB
    assert tree_five_sim > BUDGET_12GIB          # 15,013,509,530 > 12 GiB

    mixed = _worst_jobs(PHASE_GEOMETRY, 1) + _worst_jobs(PHASE_SIMULATION, 1)
    plan = plan_phase_admission(
        mixed, budget_bytes=BUDGET_12GIB, active_workers=2,
        gdal_cache_bytes=GDAL_32GIB_HOST, threads_per_worker=2,
    )
    assert plan.status == "admitted"
    assert plan.admissible_workers == 2
    assert plan.native_threads == 4  # 2 workers x 2 threads (2x2)

    five = _worst_jobs(PHASE_SIMULATION, 5)
    plan_q = plan_phase_admission(
        five, budget_bytes=BUDGET_12GIB, gdal_cache_bytes=GDAL_32GIB_HOST,
        policy="queue",
    )
    assert (plan_q.status, plan_q.admissible_workers, plan_q.deferred_count) == (
        "queued", 4, 1,
    )
    with pytest.raises(ResourceAdmissionError) as excinfo:
        plan_phase_admission(
            five, budget_bytes=BUDGET_12GIB, gdal_cache_bytes=GDAL_32GIB_HOST,
            policy="reject",
        )
    # the rejection names the arithmetic, not a vague failure:
    # 5 x 2,916,802,560 B (5x1 worst case, block1024)
    assert "14,584,012,800" in str(excinfo.value)


def test_three_worker_boundary_raw_worst_and_legacy_gap():
    """C6-60 review F6 refinement, superseded by the X03 Stage-B amendment.
    The historical gap ran one way: the legacy estimate admitted 3x1 while
    the corrected component model rejected it as raw-unsafe.  Under the
    measured envelope the direction INVERTS at calibrated shapes: the
    calibrated price (2,908,028,928 B) admits 4x1 where the legacy estimate
    (3,730,374,656 B) still caps at 3x1 -- safety now rests on measurement
    (child RSS <= 0.77 GiB envelope on 24/24 records, cross-thread bitwise
    24/24) instead of on the full-plane component upper bound, which remains
    in force above the table (test_dtype64_reserve_repriced_at_eight_bytes)."""
    sim = simulation_reservation(WORST_SHAPE, gdal_cache_bytes=GDAL_32GIB_HOST)
    # every charged component is still accounted inside one per-worker reservation
    assert sim.total_bytes == (
        sim.payload_bytes + sim.live_array_bytes + sim.decoded_block_bytes
        + sim.native_bytes + sim.gdal_cache_bytes + sim.write_pulse_bytes
        + sim.export_stream_bytes + sim.mapped_bytes
    )
    tree_four = 4 * sim.total_bytes + DEFAULT_PARENT_FOOTPRINT_BYTES
    tree_five = 5 * sim.total_bytes + DEFAULT_PARENT_FOOTPRINT_BYTES
    assert tree_four <= BUDGET_12GIB < tree_five  # 12,096,706,970 / 15,013,509,530

    with pytest.raises(ResourceAdmissionError) as excinfo:
        plan_phase_admission(
            _worst_jobs(PHASE_SIMULATION, 5), budget_bytes=BUDGET_12GIB,
            gdal_cache_bytes=GDAL_32GIB_HOST, policy="reject",
        )
    assert "only 4 fit" in str(excinfo.value)
    queued = plan_phase_admission(
        _worst_jobs(PHASE_SIMULATION, 5), budget_bytes=BUDGET_12GIB,
        gdal_cache_bytes=GDAL_32GIB_HOST, policy="queue",
    )
    assert (queued.admissible_workers, queued.deferred_count) == (4, 1)

    # the legacy public model keeps its own estimate-based arithmetic
    # unchanged: 3x1 fits (11,191,123,968 <= 12 GiB) -- the conservative
    # bound at calibrated shapes now, superseded by measurement rather
    # than by rejection.
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
    # base 12 - 0.4 - 1 = 10.6 GiB: 3 x 2.717 GiB = 8.15 GiB fits,
    # 4 x 2.717 GiB = 10.87 GiB does not, so one of the four stays queued
    # (recalibrated X03 Stage-B price; was (1, 3) under the component model)
    assert (plan.admissible_workers, plan.deferred_count) == (3, 1)


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
    # 5 jobs breach the recalibrated 12 GiB boundary (4 fit) — X03 Stage-B
    five = _worst_jobs(PHASE_SIMULATION, 5)
    with pytest.raises(ResourceAdmissionError) as excinfo:
        plan_phase_admission(
            five, budget_bytes=BUDGET_12GIB, gdal_cache_bytes=GDAL_32GIB_HOST,
            policy="reject",
        )
    # same class object as runtime.py exports (type identity survives
    # _child_exception rebuilds; m3 §7.4 — never plain pickling)
    assert type(excinfo.value) is ResourceAdmissionError
    import solweig_light.runtime_memory as rm
    assert rm.ResourceAdmissionError is ResourceAdmissionError


def test_queue_policy_defers_without_raising():
    # 6 jobs at the recalibrated price: 4 x 2.717 GiB fit the 11.6 GiB base,
    # 2 defer — X03 Stage-B (was 4 jobs at (2, 2) under the component model)
    six = _worst_jobs(PHASE_SIMULATION, 6)
    plan = plan_phase_admission(
        six, budget_bytes=BUDGET_12GIB, gdal_cache_bytes=GDAL_32GIB_HOST,
        policy="queue",
    )
    assert plan.status == "queued"
    assert plan.admitted_count == 4 and plan.deferred_count == 2
    assert plan.reservation_base_bytes == BUDGET_12GIB - DEFAULT_PARENT_FOOTPRINT_BYTES


def test_individually_infeasible_job_raises_in_both_policies():
    """A phase that can never fit raises even under queue policy: queueing
    cannot fix an impossible job (missing/absent relief is explicit, not a
    silent skip).  A 2.5 GiB budget leaves 2,254,857,830 B base < the
    2,908,028,928 B recalibrated simulation price (X03 Stage-B)."""
    for policy in ("reject", "queue"):
        with pytest.raises(ResourceAdmissionError) as excinfo:
            plan_phase_admission(
                _worst_jobs(PHASE_SIMULATION, 1), budget_bytes=int(2.5 * GIB),
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
    admission), runtime.py (W3 GDAL_CACHEMAX cap) and, since the C6-40
    landing, runtime_phases.py (the sanctioned geometry-phase adapter that
    took over the deferred W2 admission).  No other src importer is legal."""
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
    assert importers == ["api.py", "runtime.py", "runtime_phases.py"], (
        f"unexpected importers in src: {importers}")


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
    # X03 Stage-B: under the measured envelope the payload is subsumed
    # (0 plane equivalents) and live = 3 x 0.77 GiB = 2,480,209,920 B,
    # i.e. 591 whole f32 planes at 1024^2 (2,480,209,920 // 4,194,304;
    # the measured envelope is not a whole-plane multiple, floor is intended).
    assert inv["payload_plane_equivalents_f32"] == 0
    assert inv["live_array_plane_equivalents_f32"] == 591
    assert sim.total_bytes == 2_916_802_560
    assert json.dumps(inv)  # audit dict stays JSON-safe


def test_underfill_admits_at_job_count():
    """X05 (user-approved public-behavior change, 2026-10-16): a phase whose
    job count is below the requested worker width admits at the job count
    instead of refusing with a misleading "only N fit" message.  Discovered
    by the S11-7 corner matrix (1-tile 2048^2 scene at workers>=2); present
    on main before the campaign.  The concurrent demand can never exceed the
    number of jobs."""
    one = _worst_jobs(PHASE_SIMULATION, 1)
    plan = plan_phase_admission(
        one, budget_bytes=36 * GIB, active_workers=4,
        gdal_cache_bytes=GDAL_32GIB_HOST, policy="reject",
    )
    assert plan.status == "admitted"
    assert plan.admissible_workers == 1
    assert plan.admitted_count == 1 and plan.deferred_count == 0

    geo_one = [
        PhaseJob(PHASE_GEOMETRY, WORST_ROWS, WORST_COLS, WORST_PATCHES,
                 WORST_WIND, WORST_BLOCK, tile="geo_0")
    ]
    geo_plan = plan_phase_admission(
        geo_one, budget_bytes=36 * GIB, active_workers=4,
        gdal_cache_bytes=GDAL_32GIB_HOST, policy="reject",
    )
    assert geo_plan.status == "admitted"
    assert geo_plan.admissible_workers == 1


def test_underfill_queue_policy_admits_not_queues():
    """X05: under the queue policy an under-filled width is admitted, not
    deferred -- min(requested, len(jobs)) == admissible."""
    one = _worst_jobs(PHASE_SIMULATION, 1)
    plan = plan_phase_admission(
        one, budget_bytes=36 * GIB, active_workers=4,
        gdal_cache_bytes=GDAL_32GIB_HOST, policy="queue",
    )
    assert plan.status == "admitted"
    assert plan.admitted_count == 1 and plan.deferred_count == 0


def test_overcommit_four_jobs_two_fit_still_refuses():
    """X05 guard: the clamp only removes the under-fill refusal.  Genuine
    over-commit -- four jobs where only three fit the 9 GiB base -- still
    refuses with the unchanged "requested 4 concurrent" message (mirrors the
    geometry-adapter pin)."""
    four = _worst_jobs(PHASE_SIMULATION, 4)
    with pytest.raises(ResourceAdmissionError, match="requested 4 concurrent"):
        plan_phase_admission(
            four, budget_bytes=9 * GIB, active_workers=4,
            gdal_cache_bytes=GDAL_32GIB_HOST, policy="reject",
        )


def test_production_12x2_width_unchanged_by_clamp():
    """X05 guard: the accepted E2E configuration (24 tiles, width 12) plans
    identically -- min(12, 24) == 12, all twelve admitted, none deferred."""
    jobs = _worst_jobs(PHASE_SIMULATION, 24)
    plan = plan_phase_admission(
        jobs, budget_bytes=36 * GIB, active_workers=12,
        gdal_cache_bytes=GDAL_32GIB_HOST, policy="reject",
    )
    assert plan.status == "admitted"
    assert plan.admissible_workers == 12
    assert plan.admitted_count == 12 and plan.deferred_count == 0
