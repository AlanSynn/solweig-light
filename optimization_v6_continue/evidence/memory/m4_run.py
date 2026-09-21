"""M4 instrumented spot-check at commit e7a2d6ec (35x32 reference tile, 24 steps).

Stdlib-only instrumentation (tracemalloc + resource.ru_maxrss + sampling thread).
No numerical work is altered: the simulation runs the unmodified
``run_utci_tiles`` path exactly as tests/integration/test_runtime_pipeline.py does.

Run:  PYTHONPATH=<worktree>/src python m4_run.py <output_json>
"""
import json
import resource
import sys
import threading
import time
import tracemalloc
import tempfile
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # worktree root
FIXTURE = ROOT / "tests/reference/small_original_cpu/scene/processed_inputs"
FLAGS = {f"save_{name}": True for name in (
    "tmrt", "kup", "kdown", "lup", "ldown", "shadow", "wbgt", "ta", "wind")}


def rss_mib():
    # macOS: ru_maxrss is bytes.
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 * 1024)


def main():
    out_path = Path(sys.argv[1])
    from solweig_light import run_utci_tiles
    from solweig_light.runtime import RuntimeOptions, runtime_options

    report = {
        "commit": "e7a2d6ec8594b234820e7783e0ca26d821de7f3d",
        "fixture": str(FIXTURE.relative_to(ROOT)),
        "tile": "0_0",
        "threads": 1,
        "instrumentation": ["tracemalloc", "resource.ru_maxrss", "sampling-thread"],
        "numerics_altered": False,
    }

    tmp = Path(tempfile.mkdtemp(prefix="m4-mem-"))
    prepared = tmp / "processed_inputs"
    shutil.copytree(FIXTURE, prepared)
    report["run_dir"] = "system temp (cleaned)"

    peak = {"rss": 0.0}
    stop = threading.Event()

    def sampler():
        while not stop.is_set():
            peak["rss"] = max(peak["rss"], rss_mib())
            time.sleep(0.02)

    try:
        report["rss_before_mib"] = rss_mib()
        tracemalloc.start()
        thread = threading.Thread(target=sampler, daemon=True)
        thread.start()

        t0 = time.perf_counter()
        options = RuntimeOptions(memory_budget_bytes=4 * 1024**3,
                                 cpu_budget=1, threads_per_worker=1,
                                 block_pixels=128)
        with runtime_options(options):
            run_utci_tiles(str(tmp), str(prepared), "2020-07-18", **FLAGS)
        elapsed = time.perf_counter() - t0

        stop.set()
        thread.join(timeout=1)
        current, peak_trace = tracemalloc.get_traced_memory()
        snap = tracemalloc.take_snapshot()
        tracemalloc.stop()

        top = []
        for stat in snap.statistics("lineno")[:10]:
            frame = stat.traceback[0]
            top.append({
                "site": f"{Path(frame.filename).name}:{frame.lineno}",
                "size_mib": round(stat.size / (1024 * 1024), 3),
                "count": stat.count,
            })

        report.update({
            "wall_seconds": round(elapsed, 3),
            "tracemalloc_peak_mib": round(peak_trace / (1024 * 1024), 3),
            "tracemalloc_end_mib": round(current / (1024 * 1024), 3),
            "rss_peak_mib_sampled": round(peak["rss"], 1),
            "rss_peak_mib_final": round(rss_mib(), 1),
            "top_allocation_sites": top,
        })
    finally:
        stop.set()
        shutil.rmtree(tmp, ignore_errors=True)

    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
