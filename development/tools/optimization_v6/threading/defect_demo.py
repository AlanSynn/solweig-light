#!/usr/bin/env python3
"""C6-01 defect demonstration: RuntimeOptions(threads_per_worker=H) does NOT
set Numba's native thread mask, but DOES flip the GVF dispatch route.

One process, inherited environment (no thread overrides), the exact old
portfolio pattern: iterate RuntimeOptions inside runtime_options() and call
the dispatch. The GVF leaves are intercepted with call-recording sentinels so
the real engine dispatch runs while the heavy kernel does not (the demo needs
the route decision, not kernel output; kernel routes under real loads are
observed separately by child_runner.py).

Run: defect_demo.py [--site <src>] --out <json>
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from pathlib import Path

PARSER = argparse.ArgumentParser(description=__doc__)
PARSER.add_argument("--site", default=str(Path(__file__).resolve().parents[3] / "src"))
PARSER.add_argument("--out", required=True)
ARGS = PARSER.parse_args()

ENV_THREADS = {name: os.environ.get(name) for name in
               ("NUMBA_NUM_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
                "BLIS_NUM_THREADS")}

T_START = time.monotonic()

import numpy as np  # noqa: E402
import numba  # noqa: E402

sys.path.insert(0, str(Path(ARGS.site).resolve()))
from solweig_light import RuntimeOptions, runtime_options  # noqa: E402
from solweig_light.runtime import get_runtime_options  # noqa: E402
from solweig_light.radiation import engine, ground_view  # noqa: E402

DEFAULT_MASK = int(numba.get_num_threads())
CONFIG_THREADS = int(numba.config.NUMBA_NUM_THREADS)

OBSERVED: list[dict] = []


class _RouteObserved(Exception):
    """Raised by the leaf recorder after the real dispatch chose a route."""


def _intercept(name: str, route_name: str) -> None:
    def recorder(*args, **kwargs):
        OBSERVED.append({"context_threads_per_worker":
                         get_runtime_options().threads_per_worker,
                         "numba_get_num_threads": int(numba.get_num_threads()),
                         "route": route_name})
        raise _RouteObserved(route_name)
    setattr(ground_view, name, recorder)


_intercept("_gvf_fused", "gvf_fused_g03")
_intercept("gvf_2018a", "gvf_serial_full")


def probe(threads_per_worker: int) -> dict:
    """Call the real engine dispatch under one RuntimeOptions context."""
    tiny = np.zeros((4, 4), dtype=np.float32)
    args = (tiny, tiny, tiny, 0.5, tiny, tiny, tiny, tiny, tiny, tiny,
            tiny, tiny, tiny, 0.9, 0.1, 4, 4, 273.15, tiny, tiny, tiny)
    before_mask = int(numba.get_num_threads())
    try:
        with runtime_options(RuntimeOptions(threads_per_worker=threads_per_worker,
                                            cpu_budget=4, workers=1)):
            engine.gvf_2018a(*args)
        raised = None
    except _RouteObserved as error:
        raised = str(error)
    entry = dict(OBSERVED[-1]) if OBSERVED and OBSERVED[-1].get(
        "context_threads_per_worker") == threads_per_worker else {}
    return {"requested_threads_per_worker": threads_per_worker,
            "context_threads_per_worker_seen_by_engine": entry.get(
                "context_threads_per_worker"),
            "native_mask_inside_context": entry.get("numba_get_num_threads"),
            "native_mask_before_context": before_mask,
            "route_taken": entry.get("route"),
            "route_exception": raised}


results = [probe(1), probe(4)]

# Positive control: only numba.set_num_threads moves the native mask.
set_threads_before = int(numba.get_num_threads())
try:
    numba.set_num_threads(2)
    control = {"set_num_threads_called": True,
               "mask_before": set_threads_before,
               "mask_after": int(numba.get_num_threads())}
except Exception as error:
    control = {"set_num_threads_called": False,
               "error": f"{type(error).__name__}: {error}"}
finally:
    numba.set_num_threads(DEFAULT_MASK)

mask_constant = len({entry["numba_get_num_threads"] for entry in OBSERVED}) == 1
routes = {entry["route"] for entry in OBSERVED}
record = {
    "schema": "sw6-thread-defect-demo-v1",
    "claim": "The old portfolio harness set RuntimeOptions(threads_per_worker=H) "
             "in one process and called run_tile directly: the context var "
             "selects the GVF dispatch route but does NOT change Numba's native "
             "thread mask, so its H labels confound algorithm route and native "
             "parallelism.",
    "method": "Real engine.gvf_2018a dispatch executed under each "
              "runtime_options context; ground_view leaf targets intercepted "
              "with recording sentinels (kernel body not executed; no inputs "
              "fabricated for numerics).",
    "environment_inherited_thread_vars": ENV_THREADS,
    "numba_config_NUMBA_NUM_THREADS": CONFIG_THREADS,
    "default_native_mask": DEFAULT_MASK,
    "probes": results,
    "positive_control_set_num_threads": control,
    "demonstrated": {"native_mask_constant_across_contexts": mask_constant,
                     "route_flipped": len(routes) > 1,
                     "defect_confirmed": bool(mask_constant and len(routes) > 1)},
    "versions": {"python": platform.python_version(), "numpy": np.__version__,
                 "numba": numba.__version__,
                 "llvmlite": __import__("llvmlite").__version__,
                 "machine": platform.machine()},
    "module_origin": Path(engine.__file__).resolve().as_posix(),
    "elapsed_s": round(time.monotonic() - T_START, 3),
}

Path(ARGS.out).parent.mkdir(parents=True, exist_ok=True)
Path(ARGS.out).write_text(json.dumps(record, indent=1) + "\n")
print(json.dumps({"out": ARGS.out, "defect_confirmed": record["demonstrated"]["defect_confirmed"],
                  "routes_seen": sorted(routes), "native_masks_seen":
                  sorted({entry["numba_get_num_threads"] for entry in OBSERVED})}))
