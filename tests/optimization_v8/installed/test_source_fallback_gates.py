"""N8-23 DX gate 5: plain source install with no new native toolchain.

A second fresh venv installs the worktree by ordinary ``pip install .``
(PEP 517 build isolation disabled only because build isolation cannot
download offline; setuptools comes from the offline wheelhouse) under a
PATH stripped of ISPC and Homebrew build tools.  Every dependency is a
prebuilt wheel from the wheelhouse, so nothing compiles.

NOT native-qualified: the result is the declared source/no-native fallback
build -- a functioning installation on the existing Numba path with
identical user behavior to main, carrying no numerical certificate for any
native-default claim (experiments/optimization_v8/packaging/SOURCE_FALLBACK.md).
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from installed_test_helpers import (
    FORBIDDEN_STDOUT_TOKENS, SCENE, assert_no_net_events, child_env,
    install_no_net_guard, no_net_env_extra, read_no_net_events,
    readonly_site_packages,
)
from installed_test_helpers import run_cmd as _run

from osgeo import gdal  # noqa: E402

gdal.UseExceptions()

NOT_NATIVE_QUALIFIED = (
    "SOURCE/NO-NATIVE fallback install: explicitly NOT native-qualified; "
    "no numerical certificate for the native-default claim; native wheel "
    "qualification is N8-41/42")


@pytest.fixture(scope="session")
def source_smoke(work_dir, source_venv):
    """Import + tiny API path on Numba in the source venv.

    Tiny call = ``preprocess`` + ``calculate_svf`` on a copy of the real
    scene: genuine public workflows through the Numba/JIT path, without the
    utci phase's host-memory admission reservation (which is a separate
    gate in test_installed_noenv_gates.py).
    """
    scene = work_dir / "source_scene"
    if scene.exists():
        shutil.rmtree(scene)
    shutil.copytree(SCENE, scene)
    shutil.rmtree(scene / "output_folder", ignore_errors=True)
    shutil.rmtree(scene / "processed_inputs", ignore_errors=True)
    scratch = work_dir / "source_scratch"
    (scratch / "numba").mkdir(parents=True, exist_ok=True)
    (scratch / "native").mkdir(parents=True, exist_ok=True)
    net_log = scratch / "no_net_events.jsonl"
    net_log.unlink(missing_ok=True)
    guard_dir = install_no_net_guard(scratch / "no_net_guard")
    env = child_env(scratch / "numba", scratch / "native",
                    extra=no_net_env_extra(guard_dir, net_log))
    script = f"""
import json, sys
from pathlib import Path
import solweig_light
from solweig_light import preprocess, calculate_svf
origin = str(Path(solweig_light.__file__).resolve())
assert 'site-packages' in origin, origin
preprocess(base_path={str(scene)!r}, selected_date_str='2020-07-18',
           own_met_file={str(scene / 'met.txt')!r})
calculate_svf(base_path={str(scene / 'processed_inputs')!r})
mods = [m for n, m in sorted(sys.modules.items())
        if n.startswith('solweig_light') and getattr(m, '__file__', None)]
bad = [str(Path(m.__file__).resolve()) for m in mods
       if 'site-packages' not in str(Path(m.__file__).resolve())]
print(json.dumps({{'exit_ok': True, 'modules': len(mods), 'bad_origins': bad}}))
"""
    with readonly_site_packages(source_venv["site_packages"]):
        result = _run([source_venv["python"], "-c", script],
                      env=env, cwd=scratch, timeout=900)
    svf_files = sorted(p.name for p in (scene / "processed_inputs" / "SVF").glob("*")) \
        if (scene / "processed_inputs" / "SVF").is_dir() else []
    record = {
        "returncode": result.returncode,
        "stdout_tail": result.stdout.strip().splitlines()[-6:],
        "stderr_tail": result.stderr.strip().splitlines()[-4:],
        "svf_files": svf_files,
        "scene": str(scene),
        "no_net_events": read_no_net_events(net_log),
    }
    if result.returncode == 0:
        record["payload"] = json.loads(result.stdout.strip().splitlines()[-1])
        record["stdout"] = result.stdout
    return record


def test_source_install_succeeds_without_native_toolchain(source_venv):
    """Gate 5: ordinary source install under a stripped PATH, labelled."""
    assert source_venv["pip_check"].startswith("No broken requirements"), \
        source_venv["pip_check"]
    activity = source_venv["install_log_compiler_activity"]
    assert not activity["mentions_ispc"], "ISPC appeared in the source install log"
    assert NOT_NATIVE_QUALIFIED  # labelled context for failure output


def test_source_install_import_and_tiny_api_on_numba(source_venv, source_smoke):
    """The source install runs real public workflows on the Numba path."""
    assert source_smoke["returncode"] == 0, source_smoke["stderr_tail"]
    assert_no_net_events(source_smoke["no_net_events"], "source smoke")
    payload = source_smoke["payload"]
    assert payload["exit_ok"] and not payload["bad_origins"], payload
    offenders = [token for token in FORBIDDEN_STDOUT_TOKENS
                 if token in source_smoke["stdout"].lower()]
    assert not offenders, f"backend chatter from the source install run: {offenders}"
    svf = source_smoke["svf_files"]
    assert any(name.startswith("SkyViewFactor") for name in svf), svf
    tif = Path(source_smoke["scene"]) / "processed_inputs" / "SVF" / \
        next(name for name in svf if name.startswith("SkyViewFactor"))
    dataset = gdal.Open(str(tif))
    assert dataset is not None and dataset.RasterXSize == 35, tif
    dataset = None
    assert NOT_NATIVE_QUALIFIED


def test_source_install_console_script_exists(source_venv):
    scratch = Path(source_venv["path"]).parent / "src_cli_scratch"
    (scratch / "numba").mkdir(parents=True, exist_ok=True)
    (scratch / "native").mkdir(parents=True, exist_ok=True)
    result = _run([Path(source_venv["path"]) / "bin" / "solweig-light", "--version"],
                  env=child_env(scratch / "numba", scratch / "native"))
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "solweig_light 0.1.0.dev0"
