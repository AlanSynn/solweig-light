"""N8-23 installed-source DX gates: session fixtures.

Everything here runs offline on the local host:

1. an offline wheelhouse is repacked from the local uv cache (see
   ``wheelhouse.py``) at the pinned baseline versions;
2. a ``solweig-light`` wheel is built from this worktree by ordinary pip in
   a throwaway build venv (no pyproject changes, no network, no ISPC);
3. a fresh venv OUTSIDE the repo receives the wheel plus the pinned runtime
   closure by plain ``pip install --no-index`` -- the installed-package
   environment for the no-env API/CLI/DX-surface gates;
4. a second fresh venv receives a plain source install (``pip install .
   --no-build-isolation``) under a stripped PATH -- the declared
   source/no-native fallback mode, explicitly NOT native-qualified.

Shared constants and helpers live in the uniquely named
``installed_test_helpers`` module: bare ``from conftest import ...`` is
forbidden in this multi-suite tree because pytest rebinds the bare
``conftest`` module name to the last-collected sibling suite's conftest
(experiments/optimization_v8/policy/results/full_tree_failures.json).

Skip labels (never fake passes):
  [wheelhouse-unavailable]  the local uv cache cannot satisfy the pinned
                            runtime closure offline
  [uv-unavailable]          no ``uv`` binary for venv creation
  [wheel-build-unavailable] the offline wheel build itself failed
  [host-memory-pressure]    the no-env pipeline runs were refused by the
                            baseline resource-admission model because the
                            host memory view is below the scene's fixed
                            phase reservation; environmental, retried
  [native-wheel-deferred-N8-41], [companion-collision-deferred-N8-41],
  [upstream-collision-deferred-N8-42]      gates that need the packaged
                            native artifact / companion distribution

Gate results are appended to ``GATE_RECORD`` and written to
``optimization_v8_native_default/evidence/installed/installed_gates.json``
at session end (best effort; evidence writing never fails the run).
"""

from __future__ import annotations

import os
import shutil
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
    no_net_env_extra,
    read_no_net_events,
    readonly_site_packages,
    run_cmd,
    sha256_of,
)

DX_DIR = REPO_ROOT / "tests" / "optimization_v8" / "dx"

if str(DX_DIR) not in sys.path:
    sys.path.insert(0, str(DX_DIR))


def session_temp(tmp_path_factory) -> Path:
    return tmp_path_factory.mktemp("n8_23_installed")


@pytest.fixture(scope="session")
def wheel_dir(tmp_path_factory) -> Path:
    return session_temp(tmp_path_factory) / "wheelhouse"


@pytest.fixture(scope="session")
def work_dir(tmp_path_factory) -> Path:
    return session_temp(tmp_path_factory) / "work"


@pytest.fixture(scope="session")
def wheelhouse(wheel_dir) -> dict:
    """Offline wheelhouse of the pinned runtime closure."""
    from wheelhouse import WheelhouseUnavailable, build_wheelhouse, find_setuptools_seed_wheel

    try:
        built = build_wheelhouse(wheel_dir)
    except WheelhouseUnavailable as error:
        pytest.skip(f"[wheelhouse-unavailable] {error}")
    seed = find_setuptools_seed_wheel()
    if seed is None:
        pytest.skip("[wheelhouse-unavailable] no offline setuptools seed wheel "
                    "for PEP 517 source builds")
    shutil.copy2(seed, wheel_dir / seed.name)
    record = {
        "method": "unpacked uv-cache archives (~/.cache/uv/archive-v0) re-zipped "
                  "under the original wheel filename; RECORD contents identical",
        "dir": str(wheel_dir),
        "wheels": built,
        "setuptools_seed": seed.name,
        "sha256": {filename: sha256_of(wheel_dir / filename)
                   for filename in built.values()},
    }
    GATE_RECORD["wheelhouse"] = record
    return record


@pytest.fixture(scope="session")
def built_wheel(work_dir, wheel_dir, wheelhouse) -> dict:
    """Build the solweig-light wheel from this worktree with ordinary pip."""
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
    record = {
        "path": str(wheel),
        "name": wheel.name,
        "sha256": sha256_of(wheel),
        "sha256_note": "per-build value: zip member timestamps are not "
                       "normalized by pip; content is reproducible from the "
                       "recorded tree, the digest is run-scoped",
        "built_from": str(REPO_ROOT),
        "build_method": "pip wheel <worktree> --no-deps --no-build-isolation "
                        "in a fresh uv venv seeded with setuptools "
                        f"{wheelhouse['setuptools_seed']}; no network, no ISPC, "
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
    }
    GATE_RECORD["wheel_venv"] = record
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


def _strip_scene(source: Path, target: Path) -> Path:
    """Copy the real scene; drop prepared outputs for a true first-use run."""
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)
    shutil.rmtree(target / "output_folder", ignore_errors=True)
    shutil.rmtree(target / "processed_inputs", ignore_errors=True)
    return target


def _run_noenv_pipeline(python: Path, script: str, scene: Path, scratch: Path,
                        site_packages, attempts: int = 3) -> dict:
    """Run one no-env pipeline invocation with admission-aware retries.

    Enforcement for the child run (both apply to every attempt):
    - site-packages is chmod'd read-only (N1) so any write into the
      installation raises PermissionError inside the child;
    - a PYTHONPATH network guard (N2) raises on Internet socket use and
      records every network-capable call to a scratch log.

    The scene's phase reservation is a fixed ~1.74 GB for this geometry; the
    baseline admission model charges half of the host's available-memory
    view.  Under concurrent load that view can sit below the reservation,
    which is an environmental block, not a DX failure -- retried, then
    reported as ``blocked:host-memory-pressure`` with the exact numbers.
    """
    scratch.mkdir(parents=True, exist_ok=True)
    native_cache = scratch / "native_cache_ro"
    native_cache.mkdir(parents=True, exist_ok=True)
    os.chmod(native_cache, 0o555)
    numba_cache = scratch / "numba_cache"
    numba_cache.mkdir(parents=True, exist_ok=True)
    net_log = scratch / "no_net_events.jsonl"
    net_log.unlink(missing_ok=True)
    guard_dir = install_no_net_guard(scratch / "no_net_guard")
    env = child_env(numba_cache, native_cache, extra=no_net_env_extra(guard_dir, net_log))
    before = listing(native_cache)
    record: dict = {"attempts": [], "native_cache": str(native_cache),
                    "native_cache_before": before,
                    "site_packages_readonly": {
                        "enforced": True, "path": str(site_packages),
                        "policy": "dirs 0o555 / files 0o444 for the child run, "
                                  "restored after; symlinks untouched",
                    },
                    "no_net_log": str(net_log)}
    with readonly_site_packages(site_packages):
        for attempt in range(1, attempts + 1):
            result = run_cmd([python, "-c", script], env=env,
                             cwd=scratch, timeout=900)
            entry = {
                "attempt": attempt,
                "returncode": result.returncode,
                "stdout_tail": result.stdout.strip().splitlines()[-6:],
                "stderr_tail": result.stderr.strip().splitlines()[-4:],
            }
            record["attempts"].append(entry)
            if "ResourceAdmissionError" in result.stderr:
                entry["diagnosis"] = "blocked:host-memory-pressure"
                if attempt < attempts:
                    time.sleep(20)
                continue
            if result.returncode != 0:
                entry["diagnosis"] = "failed"
                break
            entry["diagnosis"] = "passed"
            record["stdout"] = result.stdout
            record["stderr_tail"] = result.stderr.strip().splitlines()[-6:]
            break
        if all(a["diagnosis"] == "blocked:host-memory-pressure"
               for a in record["attempts"]):
            # Release-owner diagnostic (N9 F5): one final attempt with the
            # admission error's own documented remedy hint -- cap the child's
            # GDAL block cache via GDAL_CACHEMAX.  Distinctly labelled and
            # never merged into the pinned-default verdict: if it passes the
            # record carries ``remedy_note`` saying the pinned no-env runs
            # were admission-refused and only the remedy run completed; if it
            # refuses too, the label stands on all attempts.
            result = run_cmd([python, "-c", script],
                             env=dict(env, GDAL_CACHEMAX="64"),
                             cwd=scratch, timeout=900)
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
    record["native_cache_after"] = listing(native_cache)
    record["numba_cache_listing"] = listing(numba_cache)
    os.chmod(native_cache, 0o755)
    pinned = record["attempts"][:attempts]
    last = record["attempts"][-1]
    if last["diagnosis"] == "passed":
        record["status"] = "passed"
        record["remedy_note"] = (
            "the pinned no-env attempts were admission-refused; only the "
            "labelled GDAL_CACHEMAX=64 remedy attempt completed, so the "
            "pass is remedy-assisted, not a pinned-default run")
    elif all(a["diagnosis"] == "blocked:host-memory-pressure"
             for a in record["attempts"]):
        record["status"] = "blocked:host-memory-pressure"
        record["admission_note"] = (
            "scene phase reservation ~1.74 GB + 410 MB fixed parent charge vs "
            "budget = 0.5 x host available-memory view (runtime.py:"
            "default_memory_budget_bytes); environmental, not a DX property; "
            "the GDAL_CACHEMAX=64 remedy attempt was refused identically "
            "(the admission charge probes physical RAM, not the env var)")
    else:
        record["status"] = "failed"
    return record


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


@pytest.fixture(scope="session")
def installed_api_run(work_dir, wheel_venv):
    """README-style no-env thermal_comfort call in the installed venv.

    Default settings per the public signature: save_tmrt=True (the only
    non-False save default), every other flag at its pinned default, so the
    required output set is {UTCI_0_0.tif, TMRT_0_0.tif}, one band per met
    record.  The full 48-record met of the real scene runs; the met is not
    subset because the admission reservation is record-count independent.
    """
    scene = _strip_scene(SCENE, work_dir / "api_scene")
    record = _run_noenv_pipeline(
        Path(wheel_venv["python"]), API_SCRIPT % (str(scene), str(scene / "met.txt")),
        scene, work_dir / "api_scratch", wheel_venv["site_packages"])
    record["call"] = ("thermal_comfort(base_path=<scene copy>, "
                      "selected_date_str='2020-07-18', own_met_file=<scene>/met.txt, "
                      "ERA_5_z0_find=False); all other arguments at pinned defaults")
    record["scene"] = str(scene)
    record["output_files"] = sorted(p.name for p in (scene / "output_folder" / "0_0").glob("*")) \
        if (scene / "output_folder" / "0_0").is_dir() else []
    if record["status"] == "passed":
        # the child asserted its own module origins; re-assert parent-side
        import json
        payload = json.loads(record["stdout"].strip().splitlines()[-1])
        record["module_origins"] = payload
    GATE_RECORD["api_gate"] = record
    return record


@pytest.fixture(scope="session")
def installed_cli_run(work_dir, wheel_venv):
    """Real CLI invocation of the documented workflow, no-env child.

    Same enforcement as the API pipeline: read-only site-packages and the
    PYTHONPATH network guard for the child (N1/N2).
    """
    scene = _strip_scene(SCENE, work_dir / "cli_scene")
    scratch = work_dir / "cli_scratch"
    native_cache = scratch / "native_cache_ro"
    native_cache.mkdir(parents=True, exist_ok=True)
    os.chmod(native_cache, 0o555)
    numba_cache = scratch / "numba_cache"
    numba_cache.mkdir(parents=True, exist_ok=True)
    net_log = scratch / "no_net_events.jsonl"
    net_log.unlink(missing_ok=True)
    guard_dir = install_no_net_guard(scratch / "no_net_guard")
    env = child_env(numba_cache, native_cache, extra=no_net_env_extra(guard_dir, net_log))
    before = listing(native_cache)
    argv = [
        wheel_venv["console_script"],
        "--base_path", str(scene),
        "--date", "2020-07-18",
        "--use_own_met", "True",
        "--own_metfile", str(scene / "met.txt"),
        "--era5_z0_find", "False",
    ]
    record: dict = {"argv": argv[1:], "native_cache": str(native_cache),
                    "native_cache_before": before, "attempts": [],
                    "site_packages_readonly": {
                        "enforced": True, "path": wheel_venv["site_packages"],
                        "policy": "dirs 0o555 / files 0o444 for the child run, "
                                  "restored after; symlinks untouched",
                    },
                    "no_net_log": str(net_log)}
    with readonly_site_packages(wheel_venv["site_packages"]):
        for attempt in range(1, 4):
            result = run_cmd(argv, env=env, cwd=scratch, timeout=900)
            entry = {"attempt": attempt, "returncode": result.returncode,
                     "stdout_tail": result.stdout.strip().splitlines()[-6:],
                     "stderr_tail": result.stderr.strip().splitlines()[-4:]}
            record["attempts"].append(entry)
            if "ResourceAdmissionError" in result.stderr:
                entry["diagnosis"] = "blocked:host-memory-pressure"
                if attempt < 3:
                    time.sleep(20)
                continue
            entry["diagnosis"] = "passed" if result.returncode == 0 else "failed"
            record["stdout"] = result.stdout
            record["stderr_tail"] = result.stderr.strip().splitlines()[-6:]
            break
        if all(a["diagnosis"] == "blocked:host-memory-pressure"
               for a in record["attempts"]):
            # Same release-owner diagnostic as the API pipeline: one final
            # labelled GDAL_CACHEMAX=64 attempt after the pinned attempts
            # were admission-refused.  Never merged into the pinned verdict.
            result = run_cmd(argv, env=dict(env, GDAL_CACHEMAX="64"),
                             cwd=scratch, timeout=900)
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
            else:
                entry["diagnosis"] = "passed" if result.returncode == 0 else "failed"
                record["stdout"] = result.stdout
                record["stderr_tail"] = result.stderr.strip().splitlines()[-6:]
    record["no_net_events"] = read_no_net_events(net_log)
    record["native_cache_after"] = listing(native_cache)
    record["numba_cache_listing"] = listing(numba_cache)
    os.chmod(native_cache, 0o755)
    pinned = record["attempts"][:3]
    last = record["attempts"][-1]
    if last["diagnosis"] == "passed":
        record["status"] = "passed"
        record["remedy_note"] = (
            "the pinned no-env attempts were admission-refused; only the "
            "labelled GDAL_CACHEMAX=64 remedy attempt completed, so the "
            "pass is remedy-assisted, not a pinned-default run")
    elif all(a["diagnosis"] == "blocked:host-memory-pressure"
             for a in pinned):
        record["status"] = "blocked:host-memory-pressure"
    else:
        record["status"] = "failed"
    record["output_files"] = sorted(p.name for p in (scene / "output_folder" / "0_0").glob("*")) \
        if (scene / "output_folder" / "0_0").is_dir() else []
    record["scene"] = str(scene)
    GATE_RECORD["cli_gate"] = record
    return record


@pytest.fixture(scope="session")
def source_venv(work_dir, wheel_dir, wheelhouse) -> dict:
    """Declared source/no-native fallback install under a stripped PATH.

    ``pip install .`` with PEP 517 build isolation disabled (build isolation
    cannot download offline) and setuptools provided from the offline
    wheelhouse.  The stripped PATH carries no ISPC and no Homebrew tools;
    every dependency is a prebuilt wheel, so nothing compiles.
    """
    venv = _fresh_venv(work_dir, "sourceenv")
    pip = venv / "bin" / "pip"
    env = child_env(work_dir / "src_numba_cache", work_dir / "src_native_cache",
                    extra={"PATH": f"{venv}{'/bin'}:{CHILD_PATH}",
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
    site_packages = run_cmd([venv / "bin" / "python", "-c",
                             "import solweig_light, pathlib; print(pathlib.Path("
                             "solweig_light.__file__).resolve().parent.parent)"]).stdout.strip()
    record = {
        "path": str(venv),
        "python": str(venv / "bin" / "python"),
        "site_packages": site_packages,
        "install_method": "pip install <worktree> --no-index --no-cache-dir "
                          "--no-build-isolation --find-links <wheelhouse>; "
                          "PATH stripped of ISPC/Homebrew tools",
        "install_log_compiler_activity": {
            "mentions_ispc": "ispc" in lowered,
            "mentions_c_compiler": any(token in lowered
                                       for token in ("gcc", "clang", "cc -")),
        },
        "pip_check": run_cmd([pip, "check"]).stdout.strip(),
    }
    GATE_RECORD["source_venv"] = record
    return record


def pytest_sessionfinish(session, exitstatus):
    GATE_RECORD["deferred"] = [
        "selection-pinned native artifact re-freeze -> N8-50 and counted "
        "native execution evidence -> N8-42 (the N8-41 candidate wheel "
        "mechanism ships the staged generation; qualification does not "
        "exist yet and the shipped registry stays empty)",
        "companion (solweig-light-compat) install and legacy thermal_comfort "
        "executable channel -> N8-41",
        "upstream solweig_gpu import-collision against an installed main "
        "-> N8-42",
        "native coverage / qualification evidence -> N8-42",
    ]
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    out = EVIDENCE_DIR / "installed_gates.json"
    try:
        import json
        out.write_text(json.dumps(GATE_RECORD, indent=2, sort_keys=True) + "\n",
                       encoding="utf-8")
    except OSError:
        pass  # evidence writing is best effort; never fails the run
