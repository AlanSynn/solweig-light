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
"""N9-F1S bounded stream dispatch for the primary-output longwave reduction.

Replaces the whole-scene materialization in ``radiation._lw_dispatch`` with
a bounded producer/consumer stream: the AoSoA visibility payload and the
sun/shade masks are produced PER REGION inside the consumer's ``produce``
into pre-sized owned ``BlockSlot`` buffers (~14*B*P payload bytes per slot
for capacity B and P patches -- 2.09 MiB at B=1024/P=153), never
``0,total`` whole-scene tensors (2142 MiB at N=1024^2). Slicing a full
tensor is not bounded production; nothing here allocates one.

The three N9-F0 frozen records live here (f0_interface_freeze, "Stream
surface"):

* ``InvocationPlan`` -- minted ONCE per routed call, BEFORE any block:
  exact-type channel admission (any decline -> ``None`` PRE-LAUNCH, the
  caller keeps legacy), the producer's own range contract
  ``0 <= start <= stop <= total`` validated through ``_leased``, the
  prepared classification coefficients, lane width, granted thread budget,
  shared patch-level arguments, and (row C) the resolved+verified native
  artifact identity. Immutable after mint; workers receive only the plan
  and the borrowed descriptors. Never returned through public API, so it
  is forgeable by no public call. Public defensive adapters
  (``produce_blocks_aosoa`` / ``classify_block_aosoa`` /
  ``lw_primary_b`` / ``primary_aosoa``) are unchanged for unknown callers.
* ``BorrowedVisibility`` -- zero-copy per-patch payload descriptor views
  plus mode bytes, held under ONE top-level lease acquired once at mint
  (the producer's own ``_leased``: stable id-sorted lock order + the full
  range check) and released after the region join. Workers use the pinned
  read-only descriptors WITHOUT re-acquiring leaf locks: the per-block
  lock churn disappears and the RLock-reentry hazard cannot exist because
  no worker ever enters the public leasing function -- the lease is held
  by the submitting thread only, and kernels touch bytes, not locks.
* ``BlockSlot`` -- bounded owned buffers at the plan's block capacity
  (3x uint32 + 2x bool ``[G_cap, P, W]`` + one float32 ``[capacity, 7]``
  output frame). Slots are keyed by the IN-FLIGHT scratch slot id
  (``ctx.slot.id`` -- lease-exclusive per executing block by the region
  owner's construction), never by block index, so H concurrently
  executing blocks never alias. H follows the granted budget: budget=1
  allocates one slot and the owner runs with zero background threads;
  budget=4 fans out four blocks on four disjoint slots.

Per-block observable order is the frozen one: classification BEFORE
decode, then sh, vs, vb decode in original order (a reserved code raises
at the lowest block that carries one, at the producer's own patch-major
position). Canonical first-error cancellation is the region owner's
(lowest block index, produce-before-consume); nothing here reorders it.
A mid-stream producer decline cannot exist: admission was validated in
the plan, before any launch, and the pinned kernels have no decline
return -- a reserved code is an error, never a silent fallback.

Slot-reuse contract: the producer overwrites every valid lane of the
payload slots, and the mask views passed to ``classify_block_aosoa`` are
sliced to the block's EXACT gang count (the F1M scratch contract sizes
supplied scratch for the same (start, stop, patches, width) it is
given; F1M then clears that valid extent itself) -- inactive valid
lanes are False, padding lanes stay untouched and are never read. A
full-capacity clear before the call additionally keeps a reused slot's
poison lanes from drifting across blocks.
"""
from __future__ import annotations

import threading
from contextlib import ExitStack
from dataclasses import dataclass
from typing import Any

import numpy as np


def _AosoaNativeCBase():
    """The measured whole-scene C consumer, as this module's mixin base.

    The dispatcher imports THIS module lazily (inside ``_execute_row``),
    so importing it here cannot cycle; the module body of
    ``radiation._lw_dispatch`` is import-light.
    """
    from solweig_light.radiation._lw_dispatch import AosoaNativeCConsumer
    return AosoaNativeCConsumer


#: The frozen 17-argument signature order (N8-04 contract; identical to
#: region.consumers / _lw_dispatch).
_ORDERED = ('sh', 'vs', 'vb', 'sun', 'shade', 'solid', 'sine', 'cosine',
            'directions', 'gate', 'solar_gate', 'sky_down', 'sky_side',
            'surface_sun', 'surface_sh', 'lup', 'reflection_factor')

#: Channel payloads produced per block; everything else in the payload is
#: patch-level shared state or the explicit row count.
_CHANNELS = ('sh', 'vs', 'vb')
_MASKS = ('sun', 'shade')

__all__ = ['InvocationPlan', 'BorrowedVisibility', 'BlockSlot',
           'plan_invocation', 'AosoaBStreamConsumer',
           'AosoaCStreamConsumer']


# ---------------------------------------------------------------------------
# Frozen records
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BorrowedVisibility:
    """Pinned per-channel decode descriptors (payloads typed-list, modes).

    The descriptors are the producer's own zero-copy per-patch readonly
    uint8 views plus mode bytes (``visibility_compiled._descriptor``,
    cached per channel); valid for the lease lifetime owned by the
    minting ``InvocationPlan``. Kernels never re-acquire leaf locks.
    """

    sh: Any    # (payloads, modes) for shmat
    vs: Any    # (payloads, modes) for vegshmat
    vb: Any    # (payloads, modes) for vbshvegshmat


@dataclass(frozen=True)
class InvocationPlan:
    """Everything one routed call needs, validated ONCE before launch.

    ``lease`` is the top-level ExitStack over the three visibility leaves
    (producer lock order + full-range contract); ``close()`` releases it
    after the region join. ``generation_dir`` is the resolved content-
    verified artifact identity for row C (``None`` for row B); the
    generation was loaded (and therefore verified) at mint time.
    """

    row: str
    total: int
    patches: int
    width: int
    block_pixels: int
    thread_budget: int
    geometry: Any
    solar_gate: Any
    prepared: Any                      # (indices, coefficients, rad2deg)
    altitude: Any
    azimuth: Any
    asvf: Any
    solid: Any
    sine: Any
    cosine: Any
    directions: Any
    gate: Any
    sky_down: Any
    sky_side: Any
    surface_sun: Any
    surface_sh: Any
    lup: Any
    reflection_factor: Any
    borrowed: BorrowedVisibility
    lease: ExitStack
    generation_dir: str | None = None

    def close(self) -> None:
        """Release the top-level leaf lease (idempotent; after join)."""
        self.lease.close()

    @property
    def block_capacity(self) -> int:
        """Full-block row count the slots are sized for."""
        return self.block_pixels

    @property
    def slot_gangs(self) -> int:
        """Gang count of the capacity-sized slot buffers."""
        return -(-self.block_pixels // self.width)


class BlockSlot:
    """Bounded owned per-block buffers sized at the plan's capacity.

    ~14*B*P payload bytes (three uint32 channels + two bool masks) plus
    the float32 [capacity, 7] output frame. Valid lanes are fully
    rewritten every block; the mask slots are cleared by the stream
    consumer before classification, so no stale lane can ever be read.
    """

    __slots__ = ('sh', 'vs', 'vb', 'sun', 'shade', 'frame')

    def __init__(self, gangs: int, patches: int, width: int,
                 capacity: int) -> None:
        shape = (gangs, patches, width)
        self.sh = np.empty(shape, dtype=np.uint32)
        self.vs = np.empty(shape, dtype=np.uint32)
        self.vb = np.empty(shape, dtype=np.uint32)
        self.sun = np.empty(shape, dtype=np.bool_)
        self.shade = np.empty(shape, dtype=np.bool_)
        self.frame = np.empty((capacity, 7), dtype=np.float32)

    @property
    def payload_bytes(self) -> int:
        """The bounded decode payload: channels + masks (~14*B*P)."""
        return (self.sh.nbytes + self.vs.nbytes + self.vb.nbytes
                + self.sun.nbytes + self.shade.nbytes)


# ---------------------------------------------------------------------------
# Plan minting (once per routed call, before any block)
# ---------------------------------------------------------------------------

def _admitted_channels(channels) -> bool:
    """The plural producer's exact admission predicate, mirrored.

    ``produce_blocks_aosoa`` declines anything that is not an exact
    ``PackedVisibility`` or a ``MappedVisibility`` (duck types, lazy
    leaves, dense arrays); this stream must decline identically and it
    must do so HERE, pre-launch -- the per-block kernels have no decline
    return, so a mid-stream producer decline cannot exist.
    """
    from solweig_light.geometry.visibility import LazyDiffVisibility
    from .direct_aosoa import _admitted_leaf
    return all(_admitted_leaf(channel)
               and not isinstance(channel, LazyDiffVisibility)
               for channel in channels)


def plan_invocation(row, values, geometry, solar_gate, prepared, total,
                    block_pixels, factor, sun_surface, shade_surface,
                    width=8):
    """Mint the invocation plan, or return ``None`` (pre-launch decline).

    Every decline here sends the caller to its trusted legacy loop BEFORE
    any launch: non-admitted channels, an unresolvable classification
    table, or a lane-misaligned block size (the caller seam's own gate,
    restated for direct private callers). A row-C artifact that fails to
    resolve/verify raises loudly (``NativeArtifactError``) -- availability
    problems never silently rewrite the selection.

    Acquiring the leaf lease validates the full range contract
    ``0 <= 0 <= total <= leaf pixels`` in the producer's exact lock
    order; descriptors are pinned under the same lease.
    """
    if row not in ('B', 'C'):
        raise ValueError(f'unknown stream row {row!r}')
    if total < 1 or block_pixels < width or block_pixels % width:
        return None  # empty/degenerate or lane-misaligned: trusted legacy

    channels = (values['shmat'], values['vegshmat'],
                values['vbshvegshmat'])
    if not _admitted_channels(channels):
        return None

    # Classification coefficients: the accepted call's prepared tuple.
    # A driver-supplied prepared passes through unchanged; otherwise
    # resolve ONCE here -- None means the retained route declines
    # (identical to classify_block_aosoa's own None contract).
    if prepared is None:
        from solweig_light.radiation.patch_radiation import (
            _class_coefficients)
        prepared = _class_coefficients(
            values['solar_altitude'], values['solar_azimuth'], geometry,
            values['asvf'], solar_gate)
        if prepared is None:
            return None

    # One top-level lease: the producer's own lock order and range
    # contract over the FULL extent, held by the minting thread only.
    from .direct_aosoa import _leased
    lease = _leased(channels, 0, total, geometry.altitude.size)
    try:
        from solweig_light.geometry.visibility_compiled import _descriptor
        borrowed = BorrowedVisibility(sh=_descriptor(channels[0]),
                                      vs=_descriptor(channels[1]),
                                      vb=_descriptor(channels[2]))

        generation_dir = None
        if row == 'C':
            from . import lw_native_aosoa
            resolved = lw_native_aosoa._resolve_generation_dir(None)
            lw_native_aosoa.load_generation(resolved)
            generation_dir = str(resolved)

        from .region.region_pool import resolve_budget
        return InvocationPlan(
            row=row, total=total, patches=geometry.altitude.size,
            width=width, block_pixels=block_pixels,
            thread_budget=resolve_budget(), geometry=geometry,
            solar_gate=solar_gate, prepared=prepared,
            altitude=values['solar_altitude'],
            azimuth=values['solar_azimuth'], asvf=values['asvf'],
            solid=values['steradian'], sine=geometry.sine,
            cosine=geometry.cosine,
            directions=geometry.longwave_cardinal_cosine,
            gate=geometry.reflection_cardinal,
            sky_down=values['Lsky_down'][:, 2],
            sky_side=values['Lsky_side'][:, 2],
            surface_sun=sun_surface, surface_sh=shade_surface,
            lup=values['Lup'].reshape(-1), reflection_factor=factor,
            borrowed=borrowed, lease=lease,
            generation_dir=generation_dir)
    except BaseException:
        lease.close()
        raise


# ---------------------------------------------------------------------------
# Stream consumers
# ---------------------------------------------------------------------------

class _StreamBase:
    """Shared bounded produce stage for both rows.

    Per block, in the frozen observable order: clear the mask slots,
    classify the block into them, then decode sh, vs, vb into the slot's
    uint32 buffers using the pinned descriptors (no locks). The payload
    carries the SLOT views -- float32 for the native leaf (note-N6
    admission convention), raw uint32 for the Numba B leaf whose own
    adapter constructs the views inside its admitted call.
    """

    mode = None  # bound by the row subclasses

    def __init__(self, plan: InvocationPlan):
        self._plan = plan
        self._alloc_lock = threading.Lock()
        # H bounded slots: one per budget slot id the owner can lease.
        # The region owner's scratch pool has exactly `budget` slots, so
        # in-flight blocks never exceed this; a pool with a different
        # budget simply grows the table on first sight of a new id
        # (still bounded by the owner's real slot count).
        plan_gangs = plan.slot_gangs
        self._slots = {i: BlockSlot(plan_gangs, plan.patches, plan.width,
                                    plan.block_capacity)
                       for i in range(plan.thread_budget)}

    # -- slot ownership ----------------------------------------------------

    def _slot(self, ctx) -> BlockSlot:
        """This in-flight block's slot, keyed by its scratch lease id."""
        slot = self._slots.get(ctx.slot.id)
        if slot is None:
            with self._alloc_lock:
                slot = self._slots.get(ctx.slot.id)
                if slot is None:
                    plan = self._plan
                    slot = BlockSlot(plan.slot_gangs, plan.patches,
                                     plan.width, plan.block_capacity)
                    self._slots[ctx.slot.id] = slot
        return slot

    def slot_bytes(self) -> int:
        """Total owned slot payload (diagnostics/memory-budget tests)."""
        return sum(slot.payload_bytes for slot in self._slots.values())

    # -- the bounded produce stage -----------------------------------------

    def produce(self, ctx) -> dict:
        plan = self._plan
        start, stop = ctx.start, ctx.stop
        rows = stop - start
        if not 0 <= start <= stop <= plan.total or not 0 < rows <= \
                plan.block_pixels:
            raise ValueError(
                f'block [{start}:{stop}] outside the invocation plan '
                f'(total={plan.total}, capacity={plan.block_pixels})')
        slot = self._slot(ctx)
        gangs = -(-rows // plan.width)

        # Classification BEFORE decode (frozen per-block order). The mask
        # views are sliced to THIS block's exact gang count: the F1M
        # scratch-reuse contract validates supplied scratch for the exact
        # (start, stop, patches, width) shape, and a caller reusing scratch
        # must size the buffers for what it passes -- the final partial
        # block would otherwise fail validation. Leading-dim slices stay
        # C-contiguous and zero-copy; padding lanes of the tail gang are
        # never validated, never written, never read. The full-capacity
        # clear below is belt-and-braces only (F1M clears the valid extent
        # itself); it guarantees a reused slot's POISON lanes cannot drift
        # across blocks.
        sun, shade = slot.sun, slot.shade
        sun[...] = False
        shade[...] = False
        from .direct_aosoa import classify_block_aosoa
        sun, shade = classify_block_aosoa(
            plan.altitude, plan.azimuth, plan.geometry, plan.asvf,
            start, stop, active=plan.solar_gate, prepared=plan.prepared,
            width=plan.width, sun_out=sun[:gangs], shade_out=shade[:gangs])
        # The prepared coefficients were minted non-None; a None here
        # would be a mid-stream decline the plan forbids.
        assert sun is not None

        # sh, vs, vb decode in original observable order into the owned
        # slot buffers (pinned descriptors; no leaf locks in workers).
        from .direct_aosoa import _produce_patchmajor
        for name, desc, buf in (('sh', plan.borrowed.sh, slot.sh),
                                ('vs', plan.borrowed.vs, slot.vs),
                                ('vb', plan.borrowed.vb, slot.vb)):
            _produce_patchmajor(desc[0], desc[1], start, stop, plan.patches,
                                buf[:gangs], plan.width)

        payload = {
            'solid': plan.solid, 'sine': plan.sine, 'cosine': plan.cosine,
            'directions': plan.directions, 'gate': plan.gate,
            'solar_gate': plan.solar_gate, 'sky_down': plan.sky_down,
            'sky_side': plan.sky_side, 'surface_sun': plan.surface_sun,
            'surface_sh': plan.surface_sh,
            'lup': plan.lup[start:stop],
            'reflection_factor': plan.reflection_factor,
            'rows': rows,
        }
        for name, buf in (('sh', slot.sh), ('vs', slot.vs), ('vb', slot.vb),
                          ('sun', sun), ('shade', shade)):
            payload[name] = buf[:gangs]
        return payload

    def _frame(self, payload, ctx) -> np.ndarray:
        """The slot's output frame, [:rows] view (fully written by the leaf)."""
        slot = self._slot(ctx)
        return slot.frame[:payload['rows']]


class AosoaBStreamConsumer(_StreamBase):
    """SELF_PARALLEL stream consumer for row B (Numba ``lw_primary_b``).

    The kernel's prange owns the granted budget, so the owner grants it
    exclusively (in-flight == 1): only one slot is ever executing, and
    budget=1 runs with zero background threads. The leaf admission is
    the unchanged ``lw_primary_b`` (it builds the note-N6 float32 views
    inside its admitted call); a rejection propagates loudly.
    """

    mode = None  # bound at __init__ (ExecutionMode import stays lazy)

    def __init__(self, plan: InvocationPlan):
        super().__init__(plan)
        from solweig_light._native_dispatch.region.region_pool import (
            ExecutionMode)
        from solweig_light._native_dispatch import lw_b_control
        self.mode = ExecutionMode.SELF_PARALLEL
        self._lw_primary_b = lw_b_control.lw_primary_b

    def consume(self, payload, ctx) -> None:
        frame = self._frame(payload, ctx)
        self._lw_primary_b(
            *(payload[name] for name in _ORDERED), payload['rows'],
            parallel=True, out=frame)
        ctx.output[:, ctx.start:ctx.stop] = frame.T


class AosoaCStreamConsumer(_StreamBase, _AosoaNativeCBase()):
    """BLOCK_FANOUT stream consumer for row C (native ``primary_aosoa``).

    Subclasses the measured whole-scene C consumer so the routed C arm
    identity is unchanged (an instance still satisfies
    ``isinstance(consumer, _lw_dispatch.AosoaNativeCConsumer)``);
    produce/consume are the bounded stream -- MRO resolves both to this
    stream's ``_StreamBase``. The leaf runs single-threaded per call, so
    parallelism is the owner's block fanout over the H disjoint slots.
    The artifact identity was resolved, content-verified and loaded at
    mint time; the per-block call reuses the pinned generation (no
    loader work in workers). Post-launch native failures stay
    ``NativeExecutionError`` -- loud, never a fallback.
    """

    mode = None  # bound at __init__ (ExecutionMode import stays lazy)

    def __init__(self, plan: InvocationPlan):
        super().__init__(plan)
        from solweig_light._native_dispatch.region.region_pool import (
            ExecutionMode)
        from solweig_light._native_dispatch import lw_native_aosoa
        self.mode = ExecutionMode.BLOCK_FANOUT
        self._primary_aosoa = lw_native_aosoa.primary_aosoa

    def consume(self, payload, ctx) -> None:
        frame = self._frame(payload, ctx)
        self._primary_aosoa(
            payload['sh'].view(np.float32), payload['vs'].view(np.float32),
            payload['vb'].view(np.float32), payload['sun'], payload['shade'],
            payload['solid'], payload['sine'], payload['cosine'],
            payload['directions'], payload['gate'], payload['solar_gate'],
            payload['sky_down'], payload['sky_side'], payload['surface_sun'],
            payload['surface_sh'], payload['lup'],
            payload['reflection_factor'], payload['rows'], out=frame,
            generation_dir=self._plan.generation_dir)
        ctx.output[:, ctx.start:ctx.stop] = frame.T
