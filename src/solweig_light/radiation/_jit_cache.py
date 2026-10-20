"""Source and runtime namespace for persistent Numba entrypoint caches."""
from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path
import struct
import sys

import llvmlite
import numba
import numpy as np

# cache-namespace-v1

def _framed(hasher, label, value):
    label = label.encode("utf-8")
    value = bytes(value)
    hasher.update(len(label).to_bytes(8, "big"))
    hasher.update(label)
    hasher.update(len(value).to_bytes(8, "big"))
    hasher.update(value)


def bind_cache_identity(function, *, dependencies=()):
    """Namespace Numba's cache without wrapping or changing function code.

    Composed kernels explicitly name their imported compiled dependencies as
    package-relative source files. Include the complete compiled call chain
    at every persistent layer: an outer cache can contain an imported leaf's
    machine code without consulting that leaf's cache during a warm load.
    This is a scoped declaration, not automatic dependency discovery.
    """
    runtime = {
        "python_implementation": platform.python_implementation(),
        "python_version": list(sys.version_info[:3]),
        "python_cache_tag": sys.implementation.cache_tag,
        "numpy": np.__version__,
        "numba": numba.__version__,
        "llvmlite": llvmlite.__version__,
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "byteorder": sys.byteorder,
        "pointer_bits": struct.calcsize("P") * 8,
    }
    hasher = hashlib.sha256()
    _framed(hasher, "defining_module", Path(function.__code__.co_filename).read_bytes())
    _framed(hasher, "namespace_helper", Path(__file__).read_bytes())
    package_root = Path(__file__).resolve().parents[1]
    for dependency in sorted(set(dependencies)):
        relative = Path(dependency)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("JIT cache dependencies must be package-relative source files")
        _framed(hasher, "dependency:" + relative.as_posix(),
                (package_root / relative).read_bytes())
    _framed(
        hasher,
        "runtime",
        json.dumps(runtime, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    )
    function.__qualname__ = function.__qualname__ + "__jitcache_" + hasher.hexdigest()
    return function
