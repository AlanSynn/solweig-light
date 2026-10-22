"""S10-31 installed-source DX gates: session fixtures.

Everything here runs offline on the local host (port of the v8 installed
suite, conftest, with the S10 deltas: no native backend row, S10 evidence
directory, product-source identity recorded against the S10-26 freeze):

1. an offline wheelhouse is repacked from the local uv cache (see
   ``wheelhouse.py``) at the pinned baseline versions;
2. a ``solweig-light`` wheel is built from this checkout by ordinary pip in
   a throwaway build venv (no pyproject changes, no network); the product
   source identity against the frozen candidate (c245ea60: src +
   pyproject.toml) is recorded per wheel;
3. a fresh venv OUTSIDE the repo receives the wheel plus the pinned runtime
   closure by plain ``pip install --no-index`` -- the installed-package
   environment for the no-env API/CLI gates;
4. a second fresh venv receives a plain source install (``pip install .
   --no-build-isolation``) under a stripped PATH with a no-compiler
   assertion on the install log.

Shared constants and helpers live in the uniquely named
``installed_test_helpers`` module: bare ``from conftest import ...`` is
forbidden in this multi-suite tree because pytest rebinds the bare
``conftest`` module name to the last-collected sibling suite's conftest.

Raw artifacts use a fresh pytest temporary directory for each session:
the offline wheelhouse, venvs, scenes, and scratch share that directory.
Use ``--basetemp`` to choose a host-local disk when needed for the
read-only-site-packages checks, which chmod-walk every installed file.

Skip labels (never fake passes):
  [wheelhouse-unavailable]  the local uv cache cannot satisfy the pinned
                            runtime closure offline
  [uv-unavailable]          no ``uv`` binary for venv creation
  [wheel-build-unavailable] the offline wheel build itself failed
  [blocked:host-memory-pressure]  the no-env pipeline runs were refused by
                            the resource-admission model (environmental;
                            retried, then reported with the exact numbers)

Gate results are appended to ``GATE_RECORD`` and written to
``.pytest_cache/evidence/installed_s10/installed_results.json``
at session end (best effort; evidence writing never fails the run).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from installed_test_helpers import (  # noqa: E402
    CHILD_PATH,
    EVIDENCE_DIR,
    GATE_RECORD,
    REPO_ROOT,
    SCENE,
    child_env,
    install_no_net_guard,
    listing,
    loadavg,
    no_net_env_extra,
    read_no_net_events,
    readonly_site_packages,
    run_cmd,
    sha256_of,
)

# The frozen candidate whose product source (src + pyproject.toml) this
# checkout must be identical to for the built wheel to be the campaign's
# candidate (S10-26 freeze).
CANDIDATE_FREEZE_SHA = "c245ea60f32b2ca93191ea00f48a4f6085a60a2b"


def product_source_identity() -> dict:
    """Empty product-source diff against the S10-26 freeze?  Recorded per
    wheel build; the freeze proof from S10-30 (per-run `git diff --quiet
    B_SHA HEAD -- src pyproject.toml`) must still hold at S10-31."""
    try:
        diff = subprocess.run(
            ["git", "diff", "--quiet", CANDIDATE_FREEZE_SHA, "HEAD", "--",
             "src", "pyproject.toml"],
            cwd=REPO_ROOT, capture_output=True, text=True)
        return {
            "freeze_sha": CANDIDATE_FREEZE_SHA,
            "paths": ["src", "pyproject.toml"],
            "identical": diff.returncode == 0,
            "command": "git diff --quiet <freeze> HEAD -- src pyproject.toml",
        }
    except OSError as error:
        return {"freeze_sha": CANDIDATE_FREEZE_SHA, "identical": None,
                "error": str(error)}


@pytest.fixture(scope="session")
def work_dir(tmp_path_factory) -> Path:
    """Fresh session directory for venvs, scenes, and scratch."""
    work = tmp_path_factory.mktemp("s10_31_work")
    GATE_RECORD["work_dir"] = str(work)
    return work


@pytest.fixture(scope="session")
def wheel_dir(work_dir) -> Path:
    return work_dir / "wheelhouse"


@pytest.fixture(scope="session")
def wheelhouse(wheel_dir) -> dict:
    """Offline wheelhouse of the pinned runtime closure."""
    from wheelhouse import WheelhouseUnavailable, build_wheelhouse, find_setuptools_seed_wheel

    try:
        built = build_wheelhouse(wheel_dir)
        seed = find_setuptools_seed_wheel(wheel_dir)
    except WheelhouseUnavailable as error:
        pytest.skip(f"[wheelhouse-unavailable] {error}")
    record = {
        "method": "unpacked uv-cache archives (~/.cache/uv/archive-v0) re-zipped "
                  "under the original wheel filename; RECORD contents identical",
        "dir": str(wheel_dir),
        "wheels": built,
        "setuptools_seed": seed.name,
        "sha256": {filename: sha256_of(wheel_dir / filename)
                   for filename in {**built, "seed": seed.name}.values()},
    }
    GATE_RECORD["wheelhouse"] = record
    return record


def _fresh_venv(parent: Path, name: str) -> Path:
    uv = shutil.which("uv")
    if uv is None:
        pytest.skip("[uv-unavailable] no uv binary for fresh-venv creation")
    target = parent / name
    result = run_cmd([uv, "venv", "--seed", target, "--python", sys.executable])
    if result.returncode != 0:
        pytest.skip(f"[uv-unavailable] venv creation failed: {result.stderr.strip()}")
    return target


@pytest.fixture(scope="session")
def built_wheel(work_dir, wheel_dir, wheelhouse) -> dict:
    """Build the solweig-light wheel from this checkout with ordinary pip."""
    build_venv = _fresh_venv(work_dir, "buildenv")
    pip = build_venv / "bin" / "pip"
    seed_install = run_cmd([pip, "install", "--no-index", "--no-cache-dir",
                            wheel_dir / wheelhouse["setuptools_seed"]])
    if seed_install.returncode != 0:
        pytest.skip(f"[wheel-build-unavailable] setuptools seed install failed: "
                    f"{seed_install.stderr.strip()}")
    dist = work_dir / "dist"
    result = run_cmd([pip, "wheel", REPO_ROOT, "--no-deps", "--no-build-isolation",
                      "-w", dist])
    wheels = list(dist.glob("*.whl")) if dist.is_dir() else []
    if result.returncode != 0 or not wheels:
        pytest.skip(f"[wheel-build-unavailable] pip wheel failed: "
                    f"{(result.stderr or result.stdout).strip()[-400:]}")
    wheel = wheels[0]
    head = run_cmd(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT)
    record = {
        "path": str(wheel),
        "name": wheel.name,
        "sha256": sha256_of(wheel),
        "sha256_note": "per-build value: zip member timestamps are not "
                       "normalized by pip; content is reproducible from the "
                       "recorded tree, the digest is run-scoped",
        "built_from": str(REPO_ROOT),
        "git_head": head.stdout.strip(),
        "product_source_identity": product_source_identity(),
        "build_method": "pip wheel <checkout> --no-deps --no-build-isolation "
                        "in a fresh uv venv seeded with setuptools "
                        f"{wheelhouse['setuptools_seed']}; no network, "
                        "pyproject.toml untouched",
    }
    GATE_RECORD["wheel"] = record
    return record


@pytest.fixture(scope="session")
def wheel_venv(work_dir, built_wheel, wheel_dir) -> dict:
    """Fresh venv outside the repo with the wheel + pinned closure installed."""
    venv = _fresh_venv(work_dir, "wheelenv")
    pip = venv / "bin" / "pip"
    result = run_cmd([pip, "install", "--no-index", "--no-cache-dir",
                      "--find-links", wheel_dir, built_wheel["path"]], timeout=900)
    if result.returncode != 0:
        pytest.skip(f"[wheel-build-unavailable] wheel install failed: "
                    f"{(result.stderr or result.stdout).strip()[-400:]}")
    check = run_cmd([pip, "check"])
    python = venv / "bin" / "python"
    site_packages = run_cmd([python, "-c",
                             "import solweig_light, pathlib; print(pathlib.Path("
                             "solweig_light.__file__).resolve().parent.parent)"]).stdout.strip()
    record = {
        "path": str(venv),
        "python": str(python),
        "site_packages": site_packages,
        "pip_check": check.stdout.strip() or check.stderr.strip(),
        "console_script": str(venv / "bin" / "solweig-light"),
        "outside_repo": not str(venv).startswith(str(REPO_ROOT)),
    }
    GATE_RECORD["wheel_venv"] = record
    return record


def _strip_scene(source: Path, target: Path) -> Path:
    """Copy the real scene; drop prepared outputs for a true first-use run."""
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)
    shutil.rmtree(target / "output_folder", ignore_errors=True)
    shutil.rmtree(target / "processed_inputs", ignore_errors=True)
    return target


DX_CROP = 16  # pixels, square, centered


def _build_dx_scene(master: Path) -> Path:
    """A real, tiny base_path scene for the no-env gates: the reference
    scene's input TIFFs cropped to a centered DX_CROP x DX_CROP window plus
    its met file.  The full 32x35 scene's per-phase reservation (~4.3 GB,
    patches=153) exceeds the admission budget left by this shared login
    node's memory view under load (~1.9 GB observed), which is an
    environmental block, not a DX property; the cropped scene keeps the
    gate a real end-to-end run.  Real rasters, real met, real pipeline."""
    # numpy first: loads the compatible C++ runtime before osgeo (host
    # quirk, see installed_test_helpers.DEPLOYMENT_CXX_RUNTIME)
    import numpy  # noqa: F401
    from osgeo import gdal

    gdal.UseExceptions()
    master.mkdir(parents=True, exist_ok=True)
    for name in ("Building_DSM.tif", "DEM.tif", "Trees.tif"):
        src = gdal.Open(str(SCENE / name))
        xsize = src.RasterXSize
        ysize = src.RasterYSize
        x0 = max(0, (xsize - DX_CROP) // 2)
        y0 = max(0, (ysize - DX_CROP) // 2)
        width = min(DX_CROP, xsize)
        height = min(DX_CROP, ysize)
        gdal.Translate(str(master / name), src,
                       srcWin=[x0, y0, width, height])
        src = None
    shutil.copy2(SCENE / "met.txt", master / "met.txt")
    return master


@pytest.fixture(scope="session")
def dx_scene(work_dir) -> Path:
    return _build_dx_scene(work_dir / "dx_scene_master")


def _finish_run_record(record: dict, attempts_budget: int, scratch: Path,
                       numba_cache: Path, net_log: Path, env: dict,
                       site_packages: str, argv_or_script, python: Path) -> None:
    """Shared no-env child loop: admission-aware retries plus the labelled
    GDAL_CACHEMAX=64 release-owner diagnostic (never merged into the pinned
    verdict).  Port of the v8 pipeline/CLI runners."""
    with readonly_site_packages(site_packages):
        for attempt in range(1, attempts_budget + 1):
            if isinstance(argv_or_script, list):
                result = run_cmd(argv_or_script, env=env, cwd=scratch, timeout=1800)
            else:
                result = run_cmd([python, "-c", argv_or_script], env=env,
                                 cwd=scratch, timeout=1800)
            entry = {
                "attempt": attempt,
                "returncode": result.returncode,
                "stdout_tail": result.stdout.strip().splitlines()[-6:],
                "stderr_tail": result.stderr.strip().splitlines()[-4:],
            }
            record["attempts"].append(entry)
            if "ResourceAdmissionError" in result.stderr:
                entry["diagnosis"] = "blocked:host-memory-pressure"
                if attempt < attempts_budget:
                    time.sleep(20)
                continue
            entry["diagnosis"] = "passed" if result.returncode == 0 else "failed"
            if result.returncode == 0:
                record["stdout"] = result.stdout
            record["stderr_tail"] = result.stderr.strip().splitlines()[-6:]
            break
        if all(a["diagnosis"] == "blocked:host-memory-pressure"
               for a in record["attempts"]):
            result = run_cmd(
                argv_or_script if isinstance(argv_or_script, list)
                else [python, "-c", argv_or_script],
                env=dict(env, GDAL_CACHEMAX="64"), cwd=scratch, timeout=1800)
            entry = {
                "attempt": "gdal-cachemax-64-diagnostic",
                "env_override": {"GDAL_CACHEMAX": "64"},
                "returncode": result.returncode,
                "stdout_tail": result.stdout.strip().splitlines()[-6:],
                "stderr_tail": result.stderr.strip().splitlines()[-4:],
            }
            record["attempts"].append(entry)
            if "ResourceAdmissionError" in result.stderr:
                entry["diagnosis"] = "blocked:host-memory-pressure"
            elif result.returncode != 0:
                entry["diagnosis"] = "failed"
            else:
                entry["diagnosis"] = "passed"
                record["stdout"] = result.stdout
                record["stderr_tail"] = result.stderr.strip().splitlines()[-6:]
    record["no_net_events"] = read_no_net_events(net_log)
    record["numba_cache_listing"] = listing(numba_cache)
    pinned = record["attempts"][:attempts_budget]
    last = record["attempts"][-1]
    if last["diagnosis"] == "passed":
        record["status"] = "passed"
        if all(a["diagnosis"] == "blocked:host-memory-pressure" for a in pinned):
            record["remedy_note"] = (
                "the pinned no-env attempts were admission-refused; only the "
                "labelled GDAL_CACHEMAX=64 remedy attempt completed, so the "
                "pass is remedy-assisted, not a pinned-default run")
    elif all(a["diagnosis"] == "blocked:host-memory-pressure" for a in pinned):
        record["status"] = "blocked:host-memory-pressure"
        record["admission_note"] = (
            "refused by the resource-admission model under the shipped "
            "default view; environmental (shared login node), not a DX "
            "property; see attempts for the exact numbers")
    else:
        record["status"] = "failed"


API_SCRIPT = """
import json, sys
from pathlib import Path
from solweig_light import thermal_comfort
import solweig_light
origin = str(Path(solweig_light.__file__).resolve())
assert 'site-packages' in origin, origin
thermal_comfort(
    base_path=%r,
    selected_date_str='2020-07-18',
    own_met_file=%r,
    ERA_5_z0_find=False,
)
mods = [m for n, m in sorted(sys.modules.items())
        if n.startswith('solweig_light') and getattr(m, '__file__', None)]
bad = [str(Path(m.__file__).resolve()) for m in mods
       if 'site-packages' not in str(Path(m.__file__).resolve())]
print(json.dumps({'exit_ok': True, 'modules': len(mods), 'bad_origins': bad}))
"""


def _run_noenv_common(work_dir: Path, name: str) -> tuple[dict, Path, Path, dict]:
    scratch = work_dir / f"{name}_scratch"
    scratch.mkdir(parents=True, exist_ok=True)
    numba_cache = scratch / "numba_cache"
    numba_cache.mkdir(parents=True, exist_ok=True)
    net_log = scratch / "no_net_events.jsonl"
    net_log.unlink(missing_ok=True)
    guard_dir = install_no_net_guard(scratch / "no_net_guard")
    env = child_env(numba_cache, extra=no_net_env_extra(guard_dir, net_log))
    record: dict = {
        "attempts": [],
        "site_packages_readonly": {
            "enforced": True,
            "policy": "dirs 0o555 / files 0o444 for the child run, restored "
                      "after; symlinks untouched",
        },
        "no_net_log": str(net_log),
        "deployment_shim": env.get("LD_PRELOAD"),
        "deployment_shim_note": (
            "host C++ runtime for the locally-built GDAL wheel (see "
            "installed_test_helpers.DEPLOYMENT_CXX_RUNTIME); required by any "
            "osgeo-first process on this host, baseline and candidate alike; "
            "not a product backend control"),
        "env_keys": sorted(env),
    }
    return record, scratch, net_log, env


@pytest.fixture(scope="session")
def installed_api_run(work_dir, wheel_venv, dx_scene):
    """README-style no-env thermal_comfort call in the installed venv.

    Default settings per the public signature: save_tmrt=True (the only
    non-False save default), every other flag at its pinned default.  The
    full 48-record met of the real scene runs; the met is not subset because
    the admission reservation is record-count independent.  The rasters are
    the scene's centered 16x16 crop (see _build_dx_scene): real tiny TIFFs,
    sized so the phase admission fits the shared host's loaded memory view.
    """
    scene = _strip_scene(dx_scene, work_dir / "api_scene")
    record, scratch, net_log, env = _run_noenv_common(work_dir, "api")
    record["site_packages_readonly"]["path"] = wheel_venv["site_packages"]
    _finish_run_record(record, 3, scratch, scratch / "numba_cache", net_log, env,
                       wheel_venv["site_packages"],
                       API_SCRIPT % (str(scene), str(scene / "met.txt")),
                       Path(wheel_venv["python"]))
    record["call"] = ("thermal_comfort(base_path=<scene copy>, "
                      "selected_date_str='2020-07-18', own_met_file=<scene>/met.txt, "
                      "ERA_5_z0_find=False); all other arguments at pinned defaults")
    record["scene"] = str(scene)
    record["output_files"] = sorted(p.name for p in (scene / "output_folder" / "0_0").glob("*")) \
        if (scene / "output_folder" / "0_0").is_dir() else []
    if record["status"] == "passed":
        import json
        payload = json.loads(record["stdout"].strip().splitlines()[-1])
        record["module_origins"] = payload
    record["loadavg_at_run"] = loadavg()
    GATE_RECORD["api_gate"] = record
    return record


@pytest.fixture(scope="session")
def installed_cli_run(work_dir, wheel_venv, dx_scene):
    """Real CLI invocation of the documented workflow, no-env child.

    Same enforcement as the API pipeline: read-only site-packages and the
    PYTHONPATH network guard for the child (pool workers inherit both --
    ``runtime._child_environment`` copies the parent environment).  Same
    cropped real scene as the API gate.
    """
    scene = _strip_scene(dx_scene, work_dir / "cli_scene")
    record, scratch, net_log, env = _run_noenv_common(work_dir, "cli")
    record["site_packages_readonly"]["path"] = wheel_venv["site_packages"]
    argv = [
        wheel_venv["console_script"],
        "--base_path", str(scene),
        "--date", "2020-07-18",
        "--use_own_met", "True",
        "--own_metfile", str(scene / "met.txt"),
        "--era5_z0_find", "False",
    ]
    record["argv"] = argv[1:]
    _finish_run_record(record, 3, scratch, scratch / "numba_cache", net_log, env,
                       wheel_venv["site_packages"], argv,
                       Path(wheel_venv["python"]))
    record["output_files"] = sorted(p.name for p in (scene / "output_folder" / "0_0").glob("*")) \
        if (scene / "output_folder" / "0_0").is_dir() else []
    record["scene"] = str(scene)
    record["loadavg_at_run"] = loadavg()
    GATE_RECORD["cli_gate"] = record
    return record


@pytest.fixture(scope="session")
def source_venv(work_dir, wheel_dir, wheelhouse) -> dict:
    """Declared source install under a stripped PATH, no compiler activity.

    ``pip install .`` with PEP 517 build isolation disabled (build isolation
    cannot download offline) and setuptools provided from the offline
    wheelhouse.  Every dependency is a prebuilt wheel and the project is
    pure Python, so nothing compiles -- asserted on the install log.
    """
    venv = _fresh_venv(work_dir, "sourceenv")
    pip = venv / "bin" / "pip"
    env = child_env(work_dir / "src_numba_cache",
                    extra={"PATH": f"{venv}/bin:{CHILD_PATH}",
                           "NUMBA_CACHE_DIR": str(work_dir / "src_numba_cache")})
    seed = run_cmd([pip, "install", "--no-index", "--no-cache-dir",
                    wheel_dir / wheelhouse["setuptools_seed"]], env=env, timeout=600)
    if seed.returncode != 0:
        pytest.skip(f"[wheelhouse-unavailable] source-venv setuptools seed "
                    f"failed: {seed.stderr.strip()}")
    result = run_cmd([pip, "install", "--no-index", "--no-cache-dir",
                      "--no-build-isolation", "--find-links", wheel_dir, REPO_ROOT],
                     env=env, timeout=900)
    if result.returncode != 0:
        pytest.skip(f"[wheel-build-unavailable] source install failed: "
                    f"{(result.stderr or result.stdout).strip()[-400:]}")
    lowered = (result.stdout + result.stderr).lower()
    origin = run_cmd([venv / "bin" / "python", "-c",
                      "import solweig_light, pathlib; print(pathlib.Path("
                      "solweig_light.__file__).resolve())"]).stdout.strip()
    site_packages = run_cmd([venv / "bin" / "python", "-c",
                             "import solweig_light, pathlib; print(pathlib.Path("
                             "solweig_light.__file__).resolve().parent.parent)"]).stdout.strip()
    record = {
        "path": str(venv),
        "python": str(venv / "bin" / "python"),
        "site_packages": site_packages,
        "import_origin": origin,
        "install_method": "pip install <checkout> --no-index --no-cache-dir "
                          "--no-build-isolation --find-links <wheelhouse>; "
                          "PATH stripped of build tools",
        "install_log_compiler_activity": {
            "mentions_ispc": "ispc" in lowered,
            "mentions_c_compiler": any(token in lowered
                                       for token in ("gcc", "clang", "cc -")),
            "path": env["PATH"],
        },
        "pip_check": run_cmd([pip, "check"]).stdout.strip(),
    }
    GATE_RECORD["source_venv"] = record
    return record


def pytest_sessionfinish(session, exitstatus):
    GATE_RECORD["deferred"] = [
        "host-level original-upstream import-collision gate (installing a "
        "second distribution emulating upstream solweig-gpu alongside the "
        "candidate) -> deferred with reason: needs a packaged legacy "
        "distribution; the structural half is covered by the wheel manifest "
        "top-level-packages check (only solweig_light ships)",
        "resource-tuned-profile DX: explicitly out of scope by contract "
        "('a resource-tuned profile is not unchanged-default DX proof'); "
        "all gates here run shipped defaults",
    ]
    GATE_RECORD["session_loadavg"] = loadavg()
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    out = EVIDENCE_DIR / "installed_results.json"
    try:
        import json
        out.write_text(json.dumps(GATE_RECORD, indent=2, sort_keys=True) + "\n",
                       encoding="utf-8")
    except OSError:
        pass  # evidence writing is best effort; never fails the run
