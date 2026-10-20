"""Explicit tile-owned immutable radiation geometry and admission certificates.

This is an ownership object, not an identity/mtime cache. Construction takes
private byte-backed snapshots; callers use those exact read-only arrays for
the scope lifetime. A changed or copied caller array never inherits a
certificate. No dynamic radiation, temperature, or visibility is retained.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from types import MappingProxyType
import numpy as np

_CURRENT = ContextVar('solweig_owned_radiation_geometry', default=None)
SVF_KEYS = ('svfE','svfS','svfW','svfN','svfEveg','svfSveg','svfWveg',
            'svfNveg','svfEaveg','svfSaveg','svfWaveg','svfNaveg')


def _snapshot(value):
    array = np.ascontiguousarray(value)
    return np.frombuffer(array.tobytes(),dtype=array.dtype).reshape(array.shape)


class OwnedRadiationGeometry:
    """Own immutable asvf, its exact tangent, and twelve SVF range proofs.

    Resident cost is asvf + its tangent + twelve SVF snapshots. At 600x600
    float32 this is 20,160,000 bytes. The snapshots preserve shape, dtype,
    NaN payloads and signed zero. General public calls need no such owner.
    """
    __slots__ = ('asvf','heights','svf','_ranges','nbytes','_sealed')

    def __setattr__(self,name,value):
        if getattr(self,'_sealed',False):
            raise AttributeError('owned radiation geometry is immutable')
        object.__setattr__(self,name,value)

    def __init__(self, asvf, svf):
        from ._math_profile import tan32
        from .pipeline_demand import _array_range
        self.asvf = _snapshot(asvf)
        # Only finite in-profile inputs are hoisted: exotic inputs retain
        # the exact original warning/decode ordering at the runtime call.
        if (self.asvf.dtype == np.float32 and
            bool((np.isfinite(self.asvf)&(np.abs(self.asvf)<np.float32(125))).all())):
            self.heights = _snapshot(tan32(self.asvf))
        else:
            self.heights = None
        fields = {key:_snapshot(svf[key]) for key in SVF_KEYS}
        self.svf = MappingProxyType(fields)
        self._ranges = tuple((fields[key],_array_range(fields[key])) for key in SVF_KEYS)
        self.nbytes = self.asvf.nbytes + sum(a.nbytes for a in fields.values())
        if self.heights is not None:
            self.nbytes += self.heights.nbytes
        self._sealed = True


@contextmanager
def radiation_geometry_scope(geometry):
    """Bind one explicitly owned geometry to the current execution context."""
    if not isinstance(geometry,OwnedRadiationGeometry):
        raise TypeError('radiation geometry scope requires OwnedRadiationGeometry')
    token = _CURRENT.set(geometry)
    try:
        yield geometry
    finally:
        _CURRENT.reset(token)


def owned_range(array):
    geometry = _CURRENT.get()
    if geometry is not None:
        for source, bounds in geometry._ranges:
            if array is source:
                return bounds
    return None


def owned_tangent(asvf):
    """Return the active owner's exact tangent, else no certificate."""
    geometry = _CURRENT.get()
    if geometry is not None and asvf is geometry.asvf:
        return geometry.heights
    return None


def classification_heights(asvf, start=0, stop=None):
    """Exact profile tangent, reusing only the active owner's exact array."""
    geometry = _CURRENT.get()
    if geometry is not None and asvf is geometry.asvf and geometry.heights is not None:
        return geometry.heights.reshape(-1)[start:stop]
    from ._math_profile import tan32
    return np.ascontiguousarray(tan32(np.asarray(asvf).reshape(-1)[start:stop])).reshape(-1)
