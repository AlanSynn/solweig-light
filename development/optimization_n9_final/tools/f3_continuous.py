#SOLWEIG-GPU: GPU-accelerated SOLWEIG model for urban thermal comfort simulation
#Copyright (C) 2022–2025 Harsh Kamath and Naveen Sudharsan

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
"""N9-F3 continuous composed A8/B/C comparison (protocol N9-CONT-v1).

ONE clock per arm call around the actual composed path (f0_protocol_freeze):
packed channel inputs + provenance scalars in -> owned [7, total] float32
out; descriptor/slot acquisition, decode, FULL exact classification, mask
clearing, guards, submission, join and output scatter all inside. Arms:

* A8   the branch accepted DEFAULT composition at main-facing defaults:
       ``patch_radiation._classes`` (retained dense [B,P] classification;
       the fused route is env-gated OFF and returns None, verified) +
       ``patch_radiation._block`` x3 + the ``_longwave_primary`` prange
       kernel, scattered into the owned frame -- the driver's legacy loop
       byte-for-byte (cylinder_longwave.define_patch_characteristics_primary,
       env unset).  The protected-path check times the same cell once more
       through the candidate source's production entry seam
       (``_lw_region_route`` consult + legacy loop) vs the bare legacy loop;
       the delta is the candidate source's per-call dispatch overhead.
* B    ``_lw_dispatch._execute_row('B', ...)`` -- the N9-F1S bounded stream:
       plan_invocation + AosoaBStreamConsumer (Numba lw_primary_b,
       SELF_PARALLEL) over H bounded BlockSlots.
* C    ``_lw_dispatch._execute_row('C', ...)`` -- same stream with
       AosoaCStreamConsumer (native primary_aosoa leaf, BLOCK_FANOUT).

Matched threads: ONE budget N=4 for the session (the N8-02 tier-B/chronology
configuration: threads=4, cpu_budget=4, workers=1); numba set_num_threads(4)
before any JIT. Stream arms run at H=4 (budget 4, the matched configuration
and the gate arm) and H=1 (budget 1, bounded-execution scaling cell).

Cells: B=1024 (primary) and B=128 (secondary) x mixes all-binary/mix/
all-raw. Fixtures reuse quiet_window_abc's construction verbatim
(_patch/_channels, P=153, seeds) + adversarial_inputs provenance scalars
(f64 surface profile); classification inputs use the production sky table
(create_patches(2) = 153 patches) and the REAL scene SVF raster values
tiled to the cell extent. Parity precheck (A8 == B == C, bitwise uint32 on
the [7,total] output) is mandatory before ANY timed cell.

Window gate (amended N8 tier-B, frozen): 1-min loadavg < 5.0 AND available
memory (vm_stat free+inactive+speculative, 16 KB pages) >= 92,000 pages at
session start; per-rep loadavg annotated; any timed-rep annotation > 8.0
censors the session (raw retained). At most TWO scheduled opportunities.

Usage:
  f3_continuous.py --check-only   # parity precheck only, no timing
  f3_continuous.py --timed       # gate -> parity -> warm -> timed -> verdict
"""
from __future__ import annotations

import argparse
import dataclasses
import importlib.util
import json
import os
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]

# --- thread budget + cache/env pinning BEFORE any numerical import ----------
_TIER_THREADS = 4          # N8-02 tier-B configuration (threads=4, cpu=4)
_TIER_CPU_BUDGET = 4
for _name in ('BLIS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMBA_NUM_THREADS',
              'NUMEXPR_NUM_THREADS', 'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
              'VECLIB_MAXIMUM_THREADS'):
    os.environ[_name] = str(_TIER_THREADS)
os.environ.setdefault('NUMBA_CACHE_DIR', str(_REPO / '.numba_cache' / 'f3'))
os.environ['SOLWEIG_LIGHT_NATIVE_CACHE'] = str(
    _REPO / 'experiments' / 'optimization_v8' / 'native' / 'stage')
# The default composition must be measured AT the defaults:
for _name in ('SOLWEIG_LIGHT_FUSED_RAD', 'SOLWEIG_LIGHT_PATCH_CLASS_TABLES',
              'SOLWEIG_LIGHT_LW_BACKEND'):
    os.environ.pop(_name, None)
sys.path.insert(0, str(_REPO / 'src'))

import numpy as np  # noqa: E402
import numba  # noqa: E402

N9_DIR = _REPO / 'optimization_n9_final'
EVIDENCE = N9_DIR / 'evidence'
P_PATCHES = 153
LANE_WIDTH = 8
BLOCK_SIZES = (1024, 128)          # primary first; both matter (frozen)
MIXES = ('all-binary', 'mix', 'all-raw')   # brief: binary / mixed / raw
MIX_LABEL = {'all-binary': 'binary', 'mix': 'mixed', 'all-raw': 'raw'}
REPS = 9
H_BUDGETS = (4, 1)                 # H=4 matched (gate arm); H=1 scaling cell
LOAD_START_MAX = 5.0
LOAD_CENSOR = 8.0
MIN_AVAIL_PAGES = 92_000
SENTINEL_U32 = 0x7FC0DEAD          # NaN-payload poison for the extent check
REAL_SVF = (_REPO / 'tests' / 'reference' / 'state_sequence_original_cpu'
            / 'scene' / 'processed_inputs' / 'SVF' / 'SkyViewFactor_0_0.tif')


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')


# ---------------------------------------------------------------------------
# Environment observations
# ---------------------------------------------------------------------------

def loadavg() -> tuple[float, float, float]:
    return os.getloadavg()


def memory_view() -> dict:
    """vm_stat page counts; 'available' = free+inactive+speculative."""
    out = subprocess.run(['/usr/bin/vm_stat'], capture_output=True,
                         text=True).stdout
    pages = {}
    page_size = 16384
    for line in out.splitlines():
        if 'page size of' in line:
            page_size = int(line.split('page size of')[1].split()[0])
        if ':' in line:
            key, value = line.split(':', 1)
            value = value.strip().rstrip('.').strip()
            if value.isdigit():
                pages[key.strip()] = int(value)
    free = pages.get('Pages free', 0)
    inactive = pages.get('Pages inactive', 0)
    speculative = pages.get('Pages speculative', 0)
    return {'page_size': page_size, 'pages_free': free,
            'pages_inactive': inactive, 'pages_speculative': speculative,
            'pages_available': free + inactive + speculative,
            'bytes_available': (free + inactive + speculative) * page_size}


def window_gate() -> tuple[bool, dict]:
    snapshot = {'loadavg': list(loadavg()), 'memory': memory_view(),
                'at_utc': _now_utc()}
    ok = (snapshot['loadavg'][0] < LOAD_START_MAX
          and snapshot['memory']['pages_available'] >= MIN_AVAIL_PAGES)
    snapshot['gate'] = ('pass' if ok else 'FAIL')
    snapshot['rule'] = (f'1-min loadavg < {LOAD_START_MAX} AND available '
                        f'>= {MIN_AVAIL_PAGES} pages (16 KB)')
    return ok, snapshot


def admitted_processes() -> list[str]:
    """Admitted process inventory: this harness + kernel tasks only."""
    out = subprocess.run(['/bin/ps', '-eo', 'pcpu,comm'], capture_output=True,
                         text=True).stdout.splitlines()[1:]
    return sorted({line.split(None, 1)[1].strip().rsplit('/', 1)[-1]
                   for line in out if line.strip()
                   and float(line.split(None, 1)[0] or 0) > 50.0})


# ---------------------------------------------------------------------------
# Fixtures (quiet_window_abc construction, verbatim; real classification inputs)
# ---------------------------------------------------------------------------

def _load_adversarial_inputs():
    reference = _REPO / 'tests' / 'optimization_v8' / 'reference'
    if str(reference) not in sys.path:
        sys.path.insert(0, str(reference))
    spec = importlib.util.spec_from_file_location(
        'lw_identity_grid', reference / 'test_typed_graph_identity.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules['lw_identity_grid'] = module
    spec.loader.exec_module(module)
    return module.adversarial_inputs


def _real_asvf(rows: int) -> np.ndarray:
    """Real scene SVF values tiled to ``rows`` (float32, driver provenance)."""
    from osgeo import gdal  # the pipeline's own raster reader
    dataset = gdal.Open(str(REAL_SVF))
    raster = np.asarray(dataset.GetRasterBand(1).ReadAsArray(),
                        dtype=np.float32)
    del dataset
    return np.resize(raster.reshape(-1), rows).astype(np.float32)


def build_cell(B: int, mix: str) -> dict:
    """One frozen cell: channels + values + geometry + classification inputs."""
    from solweig_light.geometry.visibility import PackedVisibility, _EncodedPatch
    from solweig_light.radiation.patch_radiation import (patch_geometry,
                                                         _class_coefficients)
    from solweig_light.geometry.shadows import create_patches

    adversarial_inputs = _load_adversarial_inputs()

    def _patch(mode, rng):
        if mode == 'raw':
            bits = rng.integers(0, 2 ** 32, size=B, dtype=np.uint64
                                ).astype(np.uint32)
            return _EncodedPatch(mode, bits.astype('<u4').tobytes())
        if mode == 'ternary':
            codes = rng.integers(0, 3, size=B).astype(np.uint8)
            padded = np.zeros((B + 3) // 4 * 4, dtype=np.uint8)
            padded[:B] = codes
            payload = (padded[0::4] | (padded[1::4] << 2) | (padded[2::4] << 4)
                       | (padded[3::4] << 6)).tobytes()
            return _EncodedPatch(mode, payload)
        codes = rng.integers(0, 2, size=B).astype(np.uint8)
        return _EncodedPatch(mode, np.packbits(codes, bitorder='little')
                             .tobytes())

    rotation = {'all-binary': ('binary',), 'all-raw': ('raw',),
                'mix': ('binary', 'raw', 'ternary')}[mix]
    rng = np.random.default_rng(100_003 * B + 7919 * MIXES.index(mix))
    channels = []
    for _ in range(3):
        patches = [_patch(rotation[i % len(rotation)], rng)
                   for i in range(P_PATCHES)]
        channels.append(PackedVisibility((1, B, P_PATCHES), tuple(patches)))

    base = adversarial_inputs(B, P_PATCHES, seed=97 * B)   # f64 surface profile
    assert isinstance(base['surface_sun'], float), 'f64 provenance required'

    # Production sky table: create_patches(2) = 153 patches (pipeline default).
    patch_alt, patch_azi = create_patches(2)[0], create_patches(2)[1]
    assert patch_alt.size == P_PATCHES
    geometry = patch_geometry(np.column_stack((patch_alt, patch_azi)))
    solar_altitude = np.array(52.0)      # 0-d float64, driver provenance
    solar_azimuth = np.array(173.0)
    from solweig_light.radiation import engine as rad_engine
    difference = np.asarray([np.abs(rad_engine._operate(
        np.subtract, solar_azimuth, value)) for value in geometry.azimuth])
    solar_gate = ((difference > 90) & (difference < 270)
                  & (solar_altitude > 0))
    asvf = _real_asvf(B)
    prepared = _class_coefficients(solar_altitude, solar_azimuth, geometry,
                                   asvf, solar_gate)
    assert prepared is not None and prepared[0].size, \
        'classification table must admit the fixture'

    values = {
        'shmat': channels[0], 'vegshmat': channels[1],
        'vbshvegshmat': channels[2],
        'solar_altitude': solar_altitude, 'solar_azimuth': solar_azimuth,
        'asvf': asvf, 'steradian': base['solid'],
        'Lsky_down': np.ascontiguousarray(
            np.stack([base['sky_down']] * 3, axis=1)),
        'Lsky_side': np.ascontiguousarray(
            np.stack([base['sky_side']] * 3, axis=1)),
        'Lup': base['lup'].reshape(-1, 1),
    }
    scalars = {'factor': base['reflection_factor'],
               'sun_surface': base['surface_sun'],
               'shade_surface': base['surface_sh']}
    return {'B': B, 'mix': mix, 'total': B, 'patches': P_PATCHES,
            'values': values, 'geometry': geometry, 'solar_gate': solar_gate,
            'scalars': scalars}


# ---------------------------------------------------------------------------
# Arms (ONE clock per call in the timed session)
# ---------------------------------------------------------------------------

def _legacy_loop(cell, prepared):
    """The driver's default block loop, byte-for-byte (env unset)."""
    from solweig_light.radiation.patch_radiation import _classes, _block
    from solweig_light.radiation.cylinder_longwave import _longwave_primary
    values, geometry = cell['values'], cell['geometry']
    gate = cell['solar_gate']
    total, B = cell['total'], cell['B']
    output = np.empty((7, total), dtype=np.float32)
    lup = values['Lup'].reshape(-1)
    for start in range(0, total, B):
        stop = min(start + B, total)
        sun, shade = _classes(values['solar_altitude'], values['solar_azimuth'],
                              geometry, values['asvf'], start, stop,
                              active=gate, prepared=prepared)
        sh = _block(values['shmat'], start, stop, cell['patches'])
        vs = _block(values['vegshmat'], start, stop, cell['patches'])
        vb = _block(values['vbshvegshmat'], start, stop, cell['patches'])
        reduced = _longwave_primary(
            sh, vs, vb, sun, shade, values['steradian'], geometry.sine,
            geometry.cosine, geometry.longwave_cardinal_cosine,
            geometry.reflection_cardinal, gate, values['Lsky_down'][:, 2],
            values['Lsky_side'][:, 2], cell['scalars']['sun_surface'],
            cell['scalars']['shade_surface'], lup[start:stop],
            cell['scalars']['factor'])
        output[:, start:stop] = reduced.T
    return output


def arm_a8(cell) -> np.ndarray:
    """A8: default composition on the candidate source (bare legacy loop)."""
    from solweig_light.radiation.patch_radiation import _class_coefficients
    values, geometry = cell['values'], cell['geometry']
    prepared = _class_coefficients(values['solar_altitude'],
                                   values['solar_azimuth'], geometry,
                                   values['asvf'], cell['solar_gate'])
    return _legacy_loop(cell, prepared)


def arm_a8_route(cell) -> np.ndarray:
    """A8 through the candidate source's production entry seam: the per-call
    ``_lw_region_route`` consult (registry read + fail-closed row A) followed
    by the unchanged legacy loop -- the protected default path under the
    candidate source. Used by the frozen 3%-regression check only."""
    from solweig_light.radiation.cylinder_longwave import _lw_region_route
    from solweig_light.radiation.patch_radiation import _class_coefficients
    values, geometry = cell['values'], cell['geometry']
    prepared = _class_coefficients(values['solar_altitude'],
                                   values['solar_azimuth'], geometry,
                                   values['asvf'], cell['solar_gate'])
    routed = _lw_region_route(values, geometry, cell['solar_gate'], prepared,
                              cell['total'], cell['B'],
                              cell['scalars']['factor'],
                              cell['scalars']['sun_surface'],
                              cell['scalars']['shade_surface'])
    if routed is not None:
        raise RuntimeError('route resolved under unset env; harness defect')
    return _legacy_loop(cell, prepared)


def _tier_options(budget: int):
    from solweig_light.runtime import RuntimeOptions
    return RuntimeOptions(threads_per_worker=budget,
                          cpu_budget=_TIER_CPU_BUDGET, workers=1)


def arm_stream(row: str, cell, budget: int) -> np.ndarray:
    """B/C: the N9-F1S bounded stream through _lw_dispatch._execute_row."""
    from solweig_light.radiation.patch_radiation import _class_coefficients
    from solweig_light.radiation._lw_dispatch import _execute_row
    from solweig_light.runtime import runtime_options
    values, geometry = cell['values'], cell['geometry']
    prepared = _class_coefficients(values['solar_altitude'],
                                   values['solar_azimuth'], geometry,
                                   values['asvf'], cell['solar_gate'])
    with runtime_options(_tier_options(budget)):
        output = _execute_row(row, values, geometry, cell['solar_gate'],
                              prepared, cell['total'], cell['B'],
                              cell['scalars']['factor'],
                              cell['scalars']['sun_surface'],
                              cell['scalars']['shade_surface'])
    if output is None:
        raise RuntimeError(f'row {row} declined an admitted cell; '
                           'harness/plan defect')
    return output


ARMS = ('A8', 'B4', 'B1', 'C4', 'C1')


def run_arm(name: str, cell) -> np.ndarray:
    if name == 'A8':
        return arm_a8(cell)
    if name == 'A8route':
        return arm_a8_route(cell)
    row, budget = name[0], int(name[1])
    return arm_stream(row, cell, budget)


# ---------------------------------------------------------------------------
# Parity precheck + native counter/extent verification
# ---------------------------------------------------------------------------

def _digest(out: np.ndarray) -> str:
    import hashlib
    return hashlib.sha256(
        np.ascontiguousarray(out).view(np.uint32).tobytes()).hexdigest()[:16]


def _finite_swap(cell):
    """Context-managed finite-scalar variant for the parity precheck.

    The N8-04 adversarial grid's patch-level scalar pools saturate every
    accumulator to canonical NaN at P=153 (verified pre-F3), which makes
    a bitwise check on that grid alone nearly powerless. The finite variant
    swaps ONLY the pool-drawn patch scalars (steradian, sky columns) for
    finite seeded draws -- same typed graph, same f64 surface provenance,
    same channels -- so the payloads actually move the output bits.
    """
    rng = np.random.default_rng(2026_0923 + cell['B'])
    sky_down = rng.uniform(200.0, 400.0, cell['patches']).astype(np.float32)
    sky_side = rng.uniform(50.0, 150.0, cell['patches']).astype(np.float32)
    saved = (dict(cell['values']), dict(cell['scalars']))
    cell['values']['steradian'] = rng.uniform(0.5, 1.5,
                                              cell['patches']).astype(
        np.float32)
    cell['values']['Lsky_down'] = np.ascontiguousarray(
        np.stack([sky_down] * 3, axis=1))
    cell['values']['Lsky_side'] = np.ascontiguousarray(
        np.stack([sky_side] * 3, axis=1))
    return saved


def _triple_bitwise(cell) -> dict:
    out_a8 = run_arm('A8', cell)
    out_b = run_arm('B4', cell)
    out_c = run_arm('C4', cell)
    for out in (out_a8, out_b, out_c):
        assert out.shape == (7, cell['total']) and out.dtype == np.float32
    pair = (np.array_equal(out_a8.view(np.uint32), out_b.view(np.uint32))
            and np.array_equal(out_a8.view(np.uint32), out_c.view(np.uint32)))
    return {'ok': bool(pair), 'shape': list(out_a8.shape),
            'digest_a8': _digest(out_a8), 'digest_b': _digest(out_b),
            'digest_c': _digest(out_c)}


def parity_cell(cell) -> dict:
    """Mandatory precheck: A8 == B4 == C4 bitwise on the [7,total] output,
    on the frozen adversarial grid AND on the finite-scalar variant."""
    grid = _triple_bitwise(cell)
    saved = _finite_swap(cell)
    try:
        finite = _triple_bitwise(cell)
    finally:
        cell['values'], cell['scalars'] = saved
    return {'grid': grid, 'finite': finite,
            'ok': bool(grid['ok'] and finite['ok']),
            'note': 'grid = N8-04 adversarial provenance (saturates to NaN '
                    'at P=153); finite = seeded finite patch scalars so '
                    'payload bits move the output. Both must agree.'}


class _CountingC:
    """Paired VERIFICATION consumer (untimed): counts native entries."""

    def __init__(self, plan):
        from solweig_light._native_dispatch.lw_stream import \
            AosoaCStreamConsumer
        self._inner = AosoaCStreamConsumer(plan)
        self.mode = self._inner.mode
        self.entries = 0

    def produce(self, ctx):
        return self._inner.produce(ctx)

    def consume(self, payload, ctx):
        self.entries += 1
        self._inner.consume(payload, ctx)


def verify_native_cell(cell, budget: int = 4) -> dict:
    """Untimed counter + completed-extent proof (paired verification run).

    Mirrors _lw_dispatch._execute_row with a pre-poisoned owned frame so any
    unwritten output element survives as the SENTINEL_U32 NaN payload."""
    from solweig_light._native_dispatch import lw_stream
    from solweig_light._native_dispatch.region.region_plan import plan_regions
    from solweig_light._native_dispatch.region.region_pool import (
        execute_regions, resolve_budget)
    from solweig_light.runtime import runtime_options
    values, geometry = cell['values'], cell['geometry']
    from solweig_light.radiation.patch_radiation import _class_coefficients
    prepared = _class_coefficients(values['solar_altitude'],
                                   values['solar_azimuth'], geometry,
                                   values['asvf'], cell['solar_gate'])
    with runtime_options(_tier_options(budget)):
        plan = lw_stream.plan_invocation(
            'C', values, geometry, cell['solar_gate'], prepared, cell['total'],
            cell['B'], cell['scalars']['factor'],
            cell['scalars']['sun_surface'], cell['scalars']['shade_surface'])
        if plan is None:
            raise RuntimeError('row C plan declined; harness defect')
        declared = plan_regions(cell['total'], block_pixels=cell['B'])
        output = np.full((7, cell['total']), np.float32(0.0), dtype=np.float32)
        output.view(np.uint32)[...] = SENTINEL_U32
        try:
            consumer = _CountingC(plan)
            report = execute_regions(declared, consumer, output)
        finally:
            plan.close()
    remaining = int(np.count_nonzero(output.view(np.uint32) == SENTINEL_U32))
    return {'declared_blocks': declared.total_blocks,
            'native_entries': consumer.entries,
            'counters_equal_declared': consumer.entries
            == declared.total_blocks,
            'sentinel_elements_remaining': remaining,
            'extent_complete': remaining == 0,
            'region_report': report.as_dict(),
            'budget': resolve_budget(budget)}


# ---------------------------------------------------------------------------
# Session driver
# ---------------------------------------------------------------------------

def cells_frozen() -> list[dict]:
    cells = []
    for B in BLOCK_SIZES:
        for mix in MIXES:
            cells.append({'B': B, 'mix': mix})
    return cells


def _archive(record: dict, tag: str) -> Path:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE / f'f3_continuous_{tag}_{_stamp()}.json'
    path.write_text(json.dumps(record, indent=1, sort_keys=True) + '\n')
    print(f'[archived] {path}', file=sys.stderr)
    return path


def run(check_only: bool) -> int:
    from solweig_light.radiation.patch_radiation import (_fused_enabled,
                                                         _classes_exact_enabled)
    assert not _fused_enabled() and not _classes_exact_enabled(), \
        'default-composition env gates must be OFF for A8'
    assert numba.config.NUMBA_NUM_THREADS == _TIER_THREADS
    numba.set_num_threads(_TIER_THREADS)
    record = {
        'recorded_utc': _now_utc(), 'protocol': 'N9-CONT-v1',
        'mode': 'check-only (no timing)' if check_only else 'TIMED',
        'host': {'machine': os.uname().machine, 'ncpu': os.cpu_count(),
                 'numba': numba.__version__,
                 'numba_threads': int(numba.get_num_threads()),
                 'tier_budget_N': _TIER_THREADS,
                 'tier_note': 'N8-02 tier-B configuration: threads=4, '
                              'cpu_budget=4, workers=1'},
        'env': {'SOLWEIG_LIGHT_FUSED_RAD': os.environ.get(
                    'SOLWEIG_LIGHT_FUSED_RAD'),
                'SOLWEIG_LIGHT_PATCH_CLASS_TABLES': os.environ.get(
                    'SOLWEIG_LIGHT_PATCH_CLASS_TABLES'),
                'SOLWEIG_LIGHT_LW_BACKEND': os.environ.get(
                    'SOLWEIG_LIGHT_LW_BACKEND'),
                'native_cache': os.environ['SOLWEIG_LIGHT_NATIVE_CACHE'],
                'numba_cache_dir': os.environ['NUMBA_CACHE_DIR']},
        'reps': REPS, 'cells': cells_frozen(), 'arms': ARMS,
    }
    built = []
    if not check_only:
        # Gate FIRST (before any harness self-load: the fixture build and
        # parity pass are real work and would inflate the loadavg the gate
        # sees -- the F3 opportunity-1 refusal lesson, recorded honestly).
        gate_ok, start_snapshot = window_gate()
        start_snapshot['admitted_busy_processes'] = admitted_processes()
        record['session_start_snapshot'] = start_snapshot
        if not gate_ok:
            record['status'] = 'WINDOW_GATE_REFUSED (opportunity consumed)'
            record['end_snapshot'] = {'loadavg': list(loadavg())}
            _archive(record, 'gaterefused')
            print(f'[F3] window gate FAILED at start {start_snapshot}; '
                  'refusing to time (opportunity consumed)', file=sys.stderr)
            return 2
    try:
        for spec in cells_frozen():
            cell = build_cell(spec['B'], spec['mix'])
            cell['parity'] = parity_cell(cell)
            built.append(cell)
            if not cell['parity']['ok']:
                record['parity_failed_cell'] = f"B={spec['B']} {spec['mix']}"
                record['per_cell'] = [
                    {'B': c['B'], 'mix': c['mix'], 'parity': c['parity']}
                    for c in built]
                _archive(record, 'parityfail')
                print(f'[F3] PARITY FAIL at B={spec["B"]} {spec["mix"]}; '
                      'no timed cell may run', file=sys.stderr)
                return 1
            print(f"[parity] B={spec['B']} {spec['mix']}: OK",
                  file=sys.stderr)
    except Exception as exc:
        record['fixture_error'] = f'{type(exc).__name__}: {exc}'
        _archive(record, 'error')
        raise
    record['per_cell'] = [{'B': c['B'], 'mix': c['mix'],
                           'parity': c['parity']} for c in built]
    if check_only:
        _archive(record, 'check')
        return 0

    # ---- warm pass (SEPARATE untimed; cold costs recorded, diagnostic) ---
    warm = {}
    for cell in built:
        entry = {}
        for arm in ARMS + ('A8route',):
            if arm == 'A8route' and cell['B'] != 1024:
                continue  # protected check runs on one primary cell
            t0 = time.perf_counter()
            run_arm(arm, cell)
            entry[arm] = round((time.perf_counter() - t0) * 1e3, 3)
        warm[f"B={cell['B']} {cell['mix']}"] = entry
        print(f"[warm] B={cell['B']} {cell['mix']}: {entry}", file=sys.stderr)
    record['warm_cold_first_call_ms'] = warm  # DIAGNOSTIC ONLY, never verdict

    # ---- native counter/extent verification (untimed, paired) ------------
    verify = {}
    for cell in built:
        verify[f"B={cell['B']} {cell['mix']}"] = verify_native_cell(cell)
        assert verify[f"B={cell['B']} {cell['mix']}"]['counters_equal_declared']
        assert verify[f"B={cell['B']} {cell['mix']}"]['extent_complete']
    record['native_verification'] = verify

    # ---- quiesce once after JIT before opening the clock -----------------
    time.sleep(65.0)
    record['pre_timing_loadavg'] = list(loadavg())
    # Strict re-check before the clock opens (stricter than the frozen
    # session-start gate; refuses rather than time into a bad window):
    pre_ok, pre_snapshot = window_gate()
    record['pre_timing_snapshot'] = pre_snapshot
    if not pre_ok:
        record['status'] = 'PRE_TIMING_GATE_REFUSED (opportunity consumed)'
        _archive(record, 'gaterefused')
        print(f'[F3] pre-timing gate FAILED {pre_snapshot}; refusing to '
              'time (opportunity consumed)', file=sys.stderr)
        return 2

    # ---- timed session: interleaved per rep, never arm-major -------------
    raw = {}
    censored = []
    for cell in built:
        key = f"B={cell['B']} {cell['mix']}"
        raw[key] = {arm: [] for arm in ARMS}
        for rep in range(REPS):
            order = ARMS if rep % 2 == 0 else tuple(reversed(ARMS))
            for arm in order:
                t0 = time.perf_counter()
                run_arm(arm, cell)
                raw[key][arm].append((time.perf_counter() - t0) * 1e3)
            load1 = loadavg()[0]
            if load1 > LOAD_CENSOR:
                censored.append({'cell': key, 'rep': rep, 'load1': load1})
            print(f'[cell {key}] rep {rep + 1}/{REPS} done '
                  f'(loadavg {load1:.1f})', file=sys.stderr)
    # protected/default-path check: candidate-source entry seam vs bare loop
    protected_cell = next(c for c in built if c['B'] == 1024
                          and c['mix'] == 'mix')
    raw['protected A8route vs A8 (B=1024 mix)'] = {'A8': [], 'A8route': []}
    for rep in range(REPS):
        order = ('A8', 'A8route') if rep % 2 == 0 else ('A8route', 'A8')
        for arm in order:
            t0 = time.perf_counter()
            run_arm(arm, protected_cell)
            raw['protected A8route vs A8 (B=1024 mix)'][arm].append(
                (time.perf_counter() - t0) * 1e3)
    record['raw_ms'] = raw
    record['censored_records'] = censored
    record['session_end_snapshot'] = {
        'loadavg': list(loadavg()), 'memory': memory_view(),
        'admitted_busy_processes': admitted_processes(), 'at_utc': _now_utc()}
    record['verdict'] = gate_math(raw, verify, censored)
    _archive(record, 'timed')
    print(json.dumps(record['verdict'], indent=1, sort_keys=True))
    return 0


# ---------------------------------------------------------------------------
# Frozen gate math (f0_protocol_freeze; unchanged from N8 gates 1-4)
# ---------------------------------------------------------------------------

def _stats(times: list[float]) -> dict:
    return {'min_ms': round(min(times), 4),
            'median_ms': round(statistics.median(times), 4),
            'raw_ms': [round(t, 4) for t in times]}


def gate_math(raw: dict, verify: dict, censored: list) -> dict:
    primary = [f'B=1024 {m}' for m in MIXES]
    secondary = [f'B=128 {m}' for m in MIXES]
    cells = {}
    geomeans = {'A8/C4': [], 'B4/C4': [], 'A8/C1': [], 'B4/C1': []}
    for key in primary + secondary:
        entry = {'primary': key in primary}
        for arm in ARMS:
            entry[arm] = _stats(raw[key][arm])
        for pair in geomeans:
            a, b = pair.split('/')
            ratios = [ra / rb for ra, rb in zip(raw[key][a], raw[key][b])]
            entry[f'pair_ratio_{pair}'] = {
                'min': round(min(ratios), 4),
                'median': round(statistics.median(ratios), 4),
                'raw': [round(r, 4) for r in ratios]}
            if key in primary:
                geomeans[pair].append(statistics.median(ratios))
        cells[key] = entry

    def geo(values):
        product = 1.0
        for v in values:
            product *= v
        return product ** (1.0 / len(values))

    coverage = all(v['counters_equal_declared'] and v['extent_complete']
                   for v in verify.values())
    protected = raw['protected A8route vs A8 (B=1024 mix)']
    p_a8, p_route = _stats(protected['A8']), _stats(protected['A8route'])
    regression = p_route['median_ms'] / p_a8['median_ms'] - 1.0

    cell_pass = {}
    for key in primary:  # gates bind at the matched budget H=4
        cell_pass[key] = bool(
            cells[key]['A8']['median_ms'] / cells[key]['C4']['median_ms']
            >= 1.05
            and cells[key]['B4']['median_ms']
            / cells[key]['C4']['median_ms'] >= 1.05)
    gates = {
        'censored': bool(censored),
        'cell_gate_both_controls_1_05': cell_pass,
        'geomean_speedup_A8_over_C4': geo(geomeans['A8/C4']),
        'geomean_speedup_B4_over_C4': geo(geomeans['B4/C4']),
        'geomean_speedup_A8_over_C1': geo(geomeans['A8/C1']),
        'gate1_geomean_A8_C4_ge_1_10':
            geo(geomeans['A8/C4']) >= 1.10,
        'gate2_every_primary_cell_both_1_05': all(cell_pass.values()),
        'gate3_protected_regression_pct': round(regression * 100, 3),
        'gate3_within_3pct': regression <= 0.03,
        'gate4_coverage': {'pass': coverage,
                           'per_cell': {k: {'declared': v['declared_blocks'],
                                            'entries': v['native_entries']}
                                        for k, v in verify.items()}},
    }
    if gates['censored']:
        label = 'UNQUALIFIED_BY_ENVIRONMENT_CENSORED'
    elif (gates['gate1_geomean_A8_C4_ge_1_10']
          and gates['gate2_every_primary_cell_both_1_05']
          and gates['gate3_within_3pct'] and coverage):
        label = 'NATIVE_WINS_PROVISIONAL'
    else:
        label = 'NATIVE_LOSS'
    gates['terminal_label'] = label
    gates['note'] = ('cell/geo gates bind at the matched budget N=4 '
                     '(C4/B4); C1/B1 are the H=1 bounded-execution cells. '
                     'median_ms ratios reported alongside per-pair medians.')
    return gates


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only', action='store_true',
                        help='parity precheck only; no timing')
    parser.add_argument('--timed', action='store_true',
                        help='one scheduled measurement opportunity')
    ns = parser.parse_args()
    if ns.check_only == ns.timed:
        parser.error('exactly one of --check-only / --timed is required')
    sys.exit(run(check_only=ns.check_only))
