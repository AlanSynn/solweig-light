#!/usr/bin/env python3
"""Shared native-thread helpers for the C6-01 child-isolated harness.

Limits must exist in the child environment BEFORE the first numerical import;
`child_environment` builds that mapping and `host_facts` records what macOS
exposes (sched_getaffinity does not exist there).
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

# Same variable set the production scheduler sets before worker first import
# (src/solweig_light/runtime_worker.py::_THREAD_LIMIT_VARS).
THREAD_LIMIT_VARS = (
    "BLIS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMBA_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
)


def child_environment(threads: int, numba_cache_dir: str, override: bool = True) -> dict[str, str]:
    """Environment for a fresh child with native limits set before any import.

    With ``override=False`` (old-style demonstration label) the inherited
    environment is kept untouched so Numba falls back to its own default pool.
    """
    if isinstance(threads, bool) or not isinstance(threads, int) or threads < 1:
        raise ValueError("threads must be a positive integer")
    env = os.environ.copy()
    if override:
        for name in THREAD_LIMIT_VARS:
            env[name] = str(threads)
    env["NUMBA_CACHE_DIR"] = numba_cache_dir
    return env


def host_facts() -> dict:
    """Static host facts; macOS has no os.sched_getaffinity or psrset."""
    facts: dict = {
        "platform": "macOS (darwin); os.sched_getaffinity and psrset unavailable",
        "python_os_cpu_count": os.cpu_count(),
        "sched_getaffinity": None,
        "os_getloadavg": list(os.getloadavg()),
        "sysctl": {},
    }
    try:
        os.sched_getaffinity(0)
        facts["sched_getaffinity"] = "present"
    except AttributeError:
        pass
    keys = (
        "hw.ncpu",
        "hw.perflevel0.physicalcpu",
        "hw.perflevel1.physicalcpu",
        "hw.physicalcpu",
        "hw.memsize",
        "machdep.cpu.brand_string",
    )
    for key in keys:
        try:
            value = subprocess.run(["sysctl", "-n", key], capture_output=True,
                                   text=True, timeout=10).stdout.strip()
            facts["sysctl"][key] = value
        except Exception as error:
            facts["sysctl"][key] = f"unavailable: {type(error).__name__}"
    return facts


def heavy_jobs(threshold_pct: float = 50.0, top: int = 8) -> dict:
    """Snapshot of local CPU load and the heaviest user processes right now."""
    load = list(os.getloadavg())
    try:
        rows = subprocess.run(
            ["ps", "-eo", "pcpu,comm"], capture_output=True, text=True, timeout=10
        ).stdout.splitlines()[1:]
        parsed = []
        for row in rows:
            parts = row.strip().split(None, 1)
            if len(parts) == 2:
                try:
                    parsed.append((float(parts[0]), parts[1]))
                except ValueError:
                    continue
        parsed.sort(reverse=True)
        heavy = [{"pcpu": p, "command": c} for p, c in parsed[:top] if p >= threshold_pct]
        busy = [entry for entry in heavy if "Chrome" not in entry["command"]
                and "WindowServer" not in entry["command"] and "Google" not in entry["command"]]
    except Exception as error:
        heavy, busy = [], []
        load_error = f"{type(error).__name__}: {error}"
    else:
        load_error = None
    return {"loadavg": load, "heavy_processes": heavy,
            "busy_non_browser": busy, "ps_error": load_error,
            "exclusive_now": not busy}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=1, sort_keys=False) + "\n")
