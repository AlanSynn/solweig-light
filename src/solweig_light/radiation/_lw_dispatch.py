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
"""N8-40 staged region dispatch for the primary-output longwave reduction.

The selection policy is N8-22's ``resolve_lw_backend`` (records-blind; every
non-legacy row is disabled until a qualified record exists). This module is
the only caller of the experiment machinery from ``src``. In the shipped
state (empty qualification registry) every call resolves env unset ->
registry [absent] -> row A -> ``None`` -> the caller's legacy loop,
byte-identical to the unwired driver; the selector itself DOES run on
every routed call (see below) -- only the execution machinery is untouched.

Staged expert migration (n840-6 decision, deliberate per DX_CONTRACT): an
explicit ``SOLWEIG_LIGHT_LW_BACKEND=native|ispc`` request is served by the
legacy B7-32 dev-build route in ``cylinder_longwave._lw_kernel`` and never
reaches this module. The N8-22 expert route (installed artifact loader with
loud taxonomy errors) activates with the N8-41 wheels, when installed
artifacts actually exist to load.

The shipped state (empty qualification registry) DOES run the selector on
every routed call: ``resolve_lw_backend`` re-reads the shipped registry
file and re-derives its decision per driver call -- only the execution
machinery is untouched, because an empty registry fails closed to row A
before any of it is imported. The machinery itself is vendored under
``solweig_light._native_dispatch`` (N8-41, n841-7/n841-8); there is no
sys.path bootstrap anymore, and a broken selector module propagates its
import error instead of quietly resolving to row A. (Registry CONTENT
that is malformed rather than absent is the different failure the N8-22
taxonomy already governs: it fails closed to row A.)

Decline semantics: a producer/admission decline BEFORE launch (e.g.
``produce_blocks_aosoa`` returns ``None`` for a non-admitted channel, or
the caller's block size is not lane-aligned) returns ``None`` and the
caller runs the trusted Numba loop -- fallback OUTSIDE the admitted domain,
which the shipped B7-32 contract already establishes. A failure AFTER a
native launch propagates loudly; it is never converted into a fallback.

This module reads NO environment variables: the expert-env intercept lives
in the caller seam (``cylinder_longwave._lw_region_route``), keeping the
package's env-read surface exactly as frozen (DX parity gate).

Memory note: a routed call materializes the whole-scene AoSoA visibility
(3x uint32 [G,P,W]) plus directly-classified sun/shade masks (2x bool
[G,P,W]) once per call -- the producer cost the N8-31 frozen protocol
accounts per block size. Scope limits for qualified rows live in the
qualification records, not here.
"""
import numpy as np

#: Frozen 17-argument signature order (N8-04 contract; mirrored by
#: region.consumers).
_ORDERED = ('sh', 'vs', 'vb', 'sun', 'shade', 'solid', 'sine', 'cosine',
            'directions', 'gate', 'solar_gate', 'sky_down', 'sky_side',
            'surface_sun', 'surface_sh', 'lup', 'reflection_factor')

#: Names whose per-block slice is whole gangs of the [G, P, W] lane layout;
#: ``lup`` slices rows, everything else is patch-level and shared.
_GANG_SLICED = ('sh', 'vs', 'vb', 'sun', 'shade')

_LANE_WIDTH = 8


def region_route(values, geometry, solar_gate, prepared, total, block_pixels,
                 factor, sun_surface, shade_surface):
    """Execute the policy-selected row B/C; ``None`` routes the caller's
    legacy loop.

    ``values``/``geometry``/``solar_gate``/``prepared`` are the driver's
    own locals (``define_patch_characteristics_primary``); ``factor``,
    ``sun_surface`` and ``shade_surface`` are the already-computed scalars
    the legacy loop passes to the kernel. The caller has already stood down
    for an explicit expert-env request. Never raises for a decline:
    selection misses and producer declines return ``None``; only a
    post-selection machinery failure or a post-launch native error is loud.
    """
    if total < 1 or block_pixels < _LANE_WIDTH \
            or block_pixels % _LANE_WIDTH:
        return None  # empty/degenerate or lane-misaligned: trusted legacy
    # Vendored with the machinery (n841-7): the selector module is part of
    # the package, so it is simply imported -- a broken selector is a loud
    # failure, never a silent row-A resolution (pre-vendoring the
    # ImportError of an absent machinery tree declined quietly to A).
    from solweig_light._native_dispatch import lw_default_policy
    selection = lw_default_policy.resolve_lw_backend()
    if selection.row not in ('B', 'C'):
        return None  # auto fail-closed / legacy rows: unchanged behavior
    return _execute_row(selection.row, values, geometry, solar_gate,
                        prepared, total, block_pixels, factor, sun_surface,
                        shade_surface)


def _execute_row(row, values, geometry, solar_gate, prepared, total,
                 block_pixels, factor, sun_surface, shade_surface):
    """Produce the whole-scene AoSoA state, then dispatch through the ONE
    bounded region owner. Producer declines return None (pre-launch);
    everything after the first native launch is loud."""
    from solweig_light._native_dispatch import direct_aosoa as da

    patches = geometry.altitude.size
    aosoa = da.produce_blocks_aosoa(values['shmat'], values['vegshmat'],
                                    values['vbshvegshmat'], 0, total,
                                    patches, width=_LANE_WIDTH)
    if aosoa is None:
        return None  # non-admitted channel: trusted legacy, before launch
    sun_a, shade_a = da.classify_block_aosoa(
        values['solar_altitude'], values['solar_azimuth'], geometry,
        values['asvf'], 0, total, active=solar_gate, prepared=prepared,
        width=_LANE_WIDTH)
    if sun_a is None:
        return None  # retained per-patch classification route: legacy

    args = dict(zip(_ORDERED, (*aosoa, sun_a, shade_a)))
    args.update(solid=values['steradian'], sine=geometry.sine,
                cosine=geometry.cosine,
                directions=geometry.longwave_cardinal_cosine,
                gate=geometry.reflection_cardinal, solar_gate=solar_gate,
                sky_down=values['Lsky_down'][:, 2],
                sky_side=values['Lsky_side'][:, 2],
                surface_sun=sun_surface, surface_sh=shade_surface,
                lup=values['Lup'].reshape(-1), reflection_factor=factor)

    from solweig_light._native_dispatch.region.region_plan import plan_regions
    from solweig_light._native_dispatch.region.region_pool import execute_regions
    plan = plan_regions(total, block_pixels=block_pixels)
    output = np.empty((7, total), dtype=np.float32)
    if row == 'B':
        from solweig_light._native_dispatch.region.consumers import AosoaBConsumer
        consumer = AosoaBConsumer(args, width=_LANE_WIDTH)
    else:
        consumer = AosoaNativeCConsumer(args, width=_LANE_WIDTH)
    execute_regions(plan, consumer, output)
    return output


class AosoaNativeCConsumer:
    """BLOCK_FANOUT consumer over the N8-11 lane layout (arm C).

    Produce mirrors ``region.consumers.AosoaBConsumer`` (whole-scene
    [G, P, W] state, gang-aligned block edges); consume runs the N8-13
    native AoSoA entry per block. The ISPC entry is single-threaded per
    call, so parallelism comes from the region owner at block level and
    the leaves stay inside the granted budget (n840-2). The payloads are
    the raw uint32 producer output viewed as float32 per block -- the
    note-N6 admission convention; a raw uint32 feed silently drops the
    sky term and is never passed to the entry.
    """

    mode = None  # bound at __init__; ExecutionMode import stays lazy

    def __init__(self, args, width=_LANE_WIDTH):
        from solweig_light._native_dispatch.region.region_pool import ExecutionMode
        from solweig_light._native_dispatch import lw_native_aosoa
        primary_aosoa = lw_native_aosoa.primary_aosoa
        self.mode = ExecutionMode.BLOCK_FANOUT
        self._primary_aosoa = primary_aosoa
        self._args = dict(args)
        self._width = width

    def produce(self, ctx) -> dict:
        w = self._width
        start, stop = ctx.start, ctx.stop
        payload = {}
        for name in _ORDERED:
            value = self._args[name]
            if name in _GANG_SLICED:
                payload[name] = value[start // w:-(-stop // w)]
            elif name == 'lup':
                payload[name] = value[start:stop]
            else:
                payload[name] = value
        payload['rows'] = stop - start
        return payload

    def consume(self, payload, ctx) -> None:
        rows = payload['rows']
        frame = ctx.slot.buffer('frame', (ctx.block_capacity, 7),
                                np.float32)[:rows]
        self._primary_aosoa(
            payload['sh'].view(np.float32), payload['vs'].view(np.float32),
            payload['vb'].view(np.float32), payload['sun'], payload['shade'],
            payload['solid'], payload['sine'], payload['cosine'],
            payload['directions'], payload['gate'], payload['solar_gate'],
            payload['sky_down'], payload['sky_side'], payload['surface_sun'],
            payload['surface_sh'], payload['lup'],
            payload['reflection_factor'], rows, out=frame)
        ctx.output[:, ctx.start:ctx.stop] = frame.T
