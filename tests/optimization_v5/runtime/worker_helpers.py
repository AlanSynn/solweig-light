"""Shared helpers for persistent-worker checks on the tiny real scene.

Fixtures copy ``tests/reference/small_original_cpu`` scene inputs into tmp
directories; the numerical pipeline is never mocked.  Worker discovery and
RSS sampling use stdlib ``ps`` (psutil is not a project dependency), which
reports the same resident-set figures on macOS and Linux.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import threading
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
REFERENCE = ROOT / "tests/reference/small_original_cpu/scene"
FLAGS = {f"save_{name}": True for name in
         ("tmrt", "kup", "kdown", "lup", "ldown", "shadow", "wbgt", "ta", "wind")}
REQUIRED_INPUTS = ("Building_DSM", "Trees", "DEM", "walls", "aspect", "metfiles")
PIPELINE_MEMORY_BUDGET = 4 * 1024**3


def prepare_scene(destination: Path) -> Path:
    """Copy the reference processed inputs into ``destination``."""
    prepared = Path(destination) / "processed_inputs"
    shutil.copytree(REFERENCE / "processed_inputs", prepared)
    return prepared


def tile_paths(prepared: Path) -> dict:
    from solweig_light.pipeline import files_by_key

    return {name: files_by_key(Path(prepared) / name)["0_0"] for name in REQUIRED_INPUTS}


def tile_job(base_path, prepared, *, flags=None, selected_date_str="2020-07-18") -> dict:
    return dict(base_path=str(base_path), preprocess_dir=str(prepared),
                selected_date_str=selected_date_str, tile="0_0",
                paths=tile_paths(prepared),
                flags=dict(FLAGS if flags is None else flags))


def extend_met_file(prepared: Path, days: int) -> Path:
    """Repeat the fixture's single day into ``days`` distinct days in place."""
    metfile = next((Path(prepared) / "metfiles").glob("*.txt"))
    header = metfile.read_text().splitlines()[0]
    day = np.loadtxt(metfile, skiprows=1)
    blocks = []
    for offset in range(days):
        values = day.copy()
        values[:, 1] += offset
        blocks.append(values)
    np.savetxt(metfile, np.concatenate(blocks), header=header, comments="", fmt="%.12g")
    return metfile


def tiff_digests(base_path, tile="0_0") -> dict[str, str]:
    outputs = Path(base_path) / "output_folder" / tile
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(outputs.glob("*.tif"))}


def child_worker_pids() -> set[int]:
    """Worker processes that are direct children of this pytest process."""
    listing = subprocess.run(["ps", "-axo", "pid=,ppid=,command="],
                             capture_output=True, text=True).stdout
    pids = set()
    for line in listing.splitlines():
        fields = line.strip().split(None, 2)
        if len(fields) == 3 and "runtime_worker" in fields[2] and fields[1] == str(os.getpid()):
            pids.add(int(fields[0]))
    return pids


def sample_rss_kib(pid: int) -> int | None:
    """Resident set size of ``pid`` in KiB, or None once it has exited."""
    result = subprocess.run(["ps", "-o", "rss=", "-p", str(pid)],
                            capture_output=True, text=True)
    value = result.stdout.strip()
    return int(value) if value else None


class WorkerMonitor:
    """Watch the pool's worker processes while ``execute_tiles`` runs.

    Samples one worker's RSS and records wall-clock (monotonic) detection
    times of per-job publications, so RSS can be read at the worker's idle
    points between sequential jobs.
    """

    def __init__(self, bases, field="UTCI"):
        self.publication_paths = [
            Path(base) / "output_folder" / "0_0" / f"{field}_0_0.tif" for base in bases
        ]
        self.publications: list[tuple[int, float]] = []
        self.pids: set[int] = set()
        self.samples: list[tuple[float, int]] = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._watch, daemon=True)

    def _watch(self) -> None:
        deadline = time.monotonic() + 600
        published = [False] * len(self.publication_paths)
        pid = None
        misses = 0
        while not self._stop.is_set() and time.monotonic() < deadline:
            self.pids |= child_worker_pids()
            for index, path in enumerate(self.publication_paths):
                if not published[index] and path.is_file():
                    published[index] = True
                    self.publications.append((index, time.monotonic()))
            if pid is None:
                if not self.pids:
                    time.sleep(0.05)
                    continue
                pid = min(self.pids)
            rss = sample_rss_kib(pid)
            if rss is None:
                # ``ps`` can transiently miss a live pid; only a repeated miss
                # means the worker exited.
                misses += 1
                if misses > 3:
                    break
            else:
                misses = 0
                if rss > 0:
                    # A zero figure is a reaped-but-unwaited or dying process,
                    # never a live interpreter; keep sampling.
                    self.samples.append((time.monotonic(), rss))
            time.sleep(0.05)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *exc_info):
        self._stop.set()
        self._thread.join(timeout=10)

    def rss_after(self, index: int, window: float = 2.0) -> int:
        """Last sampled RSS in KiB within (previous publication, pub + window]."""
        stamps = {index: stamp for index, stamp in self.publications}
        assert index in stamps, f"publication of job {index} was not observed"
        start = stamps.get(index - 1, 0.0)
        within = [rss for stamp, rss in self.samples if start < stamp <= stamps[index] + window]
        assert within, f"no RSS samples observed for job {index}"
        return within[-1]
