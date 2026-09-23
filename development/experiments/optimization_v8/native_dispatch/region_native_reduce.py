"""The whole-scene native handle consumer, archived with the N8 native
row (N9 F4). Extracted verbatim from the formerly-shipped
``solweig_light._native_dispatch.region.consumers``; the shipped package
no longer depends on any native-artifact machinery. Importable only from
a repo checkout via this archive package.
"""
from __future__ import annotations

_ORDERED = ('sh', 'vs', 'vb', 'sun', 'shade', 'solid', 'sine', 'cosine',
            'directions', 'gate', 'solar_gate', 'sky_down', 'sky_side',
            'surface_sun', 'surface_sh', 'lup', 'reflection_factor')


class _NativeHandleReduce:
    """Adapt NativeHandle.execute to the reduce_block(payload, frame) shape.

    The handle is prepared ONCE (outside the block loop -- N8-10's
    lifecycle) and its execute performs zero loader work per call; the
    caller-out path exercises the handle's own alias/writeability
    guards. post-launch failures surface as NativeExecutionError and
    propagate loudly through the region.
    """

    def __init__(self, **prepare_kwargs):
        # N8-41 vendoring: the N8-10 handle ships in this package (the
        # maintainer-tree copy resolved the bare ``loader`` namespace).
        from . import native_handle
        self._handle = native_handle.prepare_native_handle(**prepare_kwargs)

    @property
    def handle(self):
        return self._handle

    def __call__(self, payload, frame):
        return self._handle.execute(
            *(payload[name] for name in _ORDERED), out=frame)


def native_handle_reduce(**prepare_kwargs) -> _NativeHandleReduce:
    """Build a reduce_block for the N8-10 native handle (arm C).

    Importing/prepare happens lazily here so module import stays cheap
    and artifact-missing stays a caller-visible, catchable taxonomy
    error (MissingNativeArtifact etc.) rather than an import crash.
    """
    return _NativeHandleReduce(**prepare_kwargs)


