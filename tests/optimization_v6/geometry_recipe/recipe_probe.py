"""Integration-simulation probe for C6-10 end-to-end runs (service-path patch).

This module is INSTRUMENTATION/INTEGRATION SIMULATION, not numerics: it makes
the tile-worker child derive the shared numerical recipe identity the way the
C6-10 integration patch (``integration_patch_C6-10.diff``, pipeline.py
section) does. The child's producer stays the unmodified ``pipeline.py``
``produce_geometry``; the parity test proves that producer's fields are
bitwise identical to the recipe producer's, so production-count behavior of
this simulation equals that of the real patched code.

The parent-side half of the simulation loads the diff's post-image of
``geometry/service.py`` directly (see ``test_end_to_end_single_production``);
both halves are labeled service-path patches. No numerical kernel is mocked:
``svf_calculator_compact`` is only wrapped call-through by the census probe.

Installed in the tile-worker child through a generated ``sitecustomize``
(the child inherits it on PYTHONPATH), mirroring the C6-02 census technique.
"""
from __future__ import annotations

import importlib.abc
import sys

TARGET_MODULE = 'solweig_light.identities'
_installed = False


def unified_geometry_identity(paths, patch_option):
    """The post-image of the patch's pipeline.py change: one shared recipe."""
    from solweig_light.geometry.recipe import numerical_geometry_recipe
    return numerical_geometry_recipe(paths, patch_option).identity


class _LoaderProxy:
    def __init__(self, loader, after_exec):
        self._loader = loader
        self._after_exec = after_exec

    def create_module(self, spec):
        return self._loader.create_module(spec)

    def exec_module(self, module):
        self._loader.exec_module(module)
        self._after_exec(module)

    def __getattr__(self, name):
        return getattr(self._loader, name)


class IdentityFinder(importlib.abc.MetaPathFinder):
    """Patch solweig_light.identities right after its ordinary execution."""

    def find_spec(self, fullname, path=None, target=None):
        if fullname != TARGET_MODULE:
            return None
        for finder in sys.meta_path:
            if finder is self:
                continue
            find = getattr(finder, 'find_spec', None)
            if find is None:
                continue
            spec = find(fullname, path, target)
            if spec is not None:
                break
        else:
            return None
        if spec is None or spec.loader is None:
            return None

        def after(module):
            module.geometry_identity = unified_geometry_identity

        spec.loader = _LoaderProxy(spec.loader, after)
        return spec


def install():
    global _installed
    if _installed:
        return
    # Capture the real base builder first: recipe.py binds
    # ``identities.geometry_identity`` at its own import time, exactly as the
    # real integration does (pipeline calls numerical_geometry_recipe, which
    # calls the real builder — no recursion in the patched code either).
    import solweig_light.geometry.recipe  # noqa: F401
    sys.meta_path.insert(0, IdentityFinder())
    module = sys.modules.get(TARGET_MODULE)
    if module is not None:
        module.geometry_identity = unified_geometry_identity
    _installed = True
