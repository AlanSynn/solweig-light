"""N8-23 no-env API and CLI gates in the installed (fallback) venv.

DX gates 2+3 executed against the installed wheel venv: README-style
``thermal_comfort`` and a real console-script invocation, in a child
environment with every backend control unset, a minimal PATH (no ISPC, no
Homebrew zsh/build tools), the native developer cache pointed at a
non-writable directory, and the Numba JIT cache at a scratch location.
Assertions prove the installed fallback never builds native code and never
chatters about backends.

Label: every run here is the SOURCE/NO-NATIVE fallback channel -- necessary
but NOT native qualification (deferred to N8-41/42).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from installed_test_helpers import (
    EXPECTED_DEFAULT_OUTPUTS, FORBIDDEN_STDOUT_TOKENS, assert_no_net_events,
    child_env, install_no_net_guard, no_net_env_extra, read_no_net_events,
    readonly_site_packages,
)
from installed_test_helpers import run_cmd as _run

from osgeo import gdal  # noqa: E402  (repo venv: baseline GDAL present)

gdal.UseExceptions()


def _assert_default_outputs(record: dict, where: str):
    """Default-settings output contract: UTCI + TMRT, one band per record.

    Default means the pinned public signature: ``save_tmrt=True`` is the
    only non-False save default, and the run uses the full 48-record met of
    the real scene, so each output TIFF carries 48 bands.
    """
    output_dir = Path(record["scene"]) / "output_folder" / "0_0"
    assert set(record["output_files"]) == set(EXPECTED_DEFAULT_OUTPUTS), (
        f"{where}: unexpected output set {sorted(record['output_files'])}; "
        f"expected {sorted(EXPECTED_DEFAULT_OUTPUTS)}")
    for name in EXPECTED_DEFAULT_OUTPUTS:
        dataset = gdal.Open(str(output_dir / name))
        assert dataset is not None, f"{where}: {name} not readable"
        assert (dataset.RasterXSize, dataset.RasterYSize) == (35, 32), name
        assert dataset.RasterCount == 48, (
            f"{where}: {name} has {dataset.RasterCount} bands, expected one "
            "per met record (48)")
        band = dataset.GetRasterBand(1)
        values = band.ReadAsArray()
        assert values.size == 35 * 32, name
        assert band.GetMetadata().get("Time"), f"{where}: {name} lost Time metadata"
        dataset = None


def _no_backend_chatter(stdout: str, where: str):
    offenders = [token for token in FORBIDDEN_STDOUT_TOKENS if token in stdout.lower()]
    assert not offenders, f"{where}: backend chatter in stdout: {offenders}"


def test_noenv_api_readme_call(installed_api_run):
    """DX gate 2: installed no-env README-style thermal_comfort.

    When the host memory view sits below the scene's fixed phase
    reservation, the baseline admission model refuses before any work
    starts; that is an environmental block, reported as a labelled skip --
    never a fake pass and never a failure of the installed package.
    """
    # enforcement evidence holds even when the pipeline itself was
    # environmentally blocked: the child imported the full stack under the
    # guard and the read-only installation before admission refused
    assert_no_net_events(installed_api_run["no_net_events"], "api gate")
    assert installed_api_run["site_packages_readonly"]["enforced"] is True
    if installed_api_run["status"] == "blocked:host-memory-pressure":
        pytest.skip("[host-memory-pressure] baseline resource admission refused "
                    f"the no-env run: {installed_api_run.get('admission_note')}")
    assert installed_api_run["status"] == "passed", installed_api_run["attempts"]
    payload = installed_api_run["module_origins"]
    assert payload["exit_ok"] and not payload["bad_origins"], payload
    _no_backend_chatter(installed_api_run["stdout"], "api gate")
    assert "Running Solweig" in installed_api_run["stdout"]
    _assert_default_outputs(installed_api_run, "api gate")
    # auto never builds: the non-writable native cache stayed empty
    assert installed_api_run["native_cache_before"] == \
        installed_api_run["native_cache_after"] == []
    # Numba fallback actually did the work (JIT cache populated)
    assert installed_api_run["numba_cache_listing"], (
        "expected Numba JIT cache activity for the fallback execution")


def test_noenv_cli_help_matches_documented_surface(wheel_venv):
    """DX gate 3 (help surface): --help exits 0 with exactly the 27 documented
    flags of the frozen main surface, no additions, no omissions.

    Same no-env enforcement as the pipeline runs: read-only installation
    (N1) and the network guard (N2) active for both child invocations.
    """
    scratch = Path(wheel_venv["path"]).parent / "cli_help_scratch"
    (scratch / "numba").mkdir(parents=True, exist_ok=True)
    (scratch / "native").mkdir(parents=True, exist_ok=True)
    net_log = scratch / "no_net_events.jsonl"
    net_log.unlink(missing_ok=True)
    guard_dir = install_no_net_guard(scratch / "no_net_guard")
    env = child_env(scratch / "numba", scratch / "native",
                    extra=no_net_env_extra(guard_dir, net_log))
    with readonly_site_packages(wheel_venv["site_packages"]):
        result = _run([wheel_venv["console_script"], "--help"], env=env)
        assert result.returncode == 0, result.stderr
        _no_backend_chatter(result.stdout, "--help")
        import dx_snapshot as dx
        frozen = dx.load_surface(dx.MAIN_SURFACE_PATH)["package"]["cli"]["options"]
        help_text = result.stdout
        missing = [flag for flag in frozen if flag not in help_text]
        assert not missing, f"documented flags missing from --help: {missing}"
        offered = [line.strip().split()[0] for line in help_text.splitlines()
                   if line.strip().startswith("--")]
        extra = [flag for flag in offered if flag not in frozen]
        assert not extra, f"undocumented flags in --help: {extra}"
        version = _run([wheel_venv["console_script"], "--version"], env=env)
        assert version.returncode == 0, version.stderr
        frozen_version = dx.load_surface(dx.MAIN_SURFACE_PATH)["package"]["dunder_version"]
        assert version.stdout.strip() == f"solweig_light {frozen_version}"
    assert_no_net_events(read_no_net_events(net_log), "--help/--version")


def test_noenv_cli_real_invocation(installed_cli_run):
    """DX gate 3: the real documented CLI workflow runs in the installed venv."""
    assert_no_net_events(installed_cli_run["no_net_events"], "cli gate")
    assert installed_cli_run["site_packages_readonly"]["enforced"] is True
    if installed_cli_run["status"] == "blocked:host-memory-pressure":
        pytest.skip("[host-memory-pressure] baseline resource admission refused "
                    "the CLI run (same environmental block as the API gate)")
    assert installed_cli_run["status"] == "passed", installed_cli_run["attempts"]
    _no_backend_chatter(installed_cli_run["stdout"], "cli gate")
    assert "Running Solweig" in installed_cli_run["stdout"]
    _assert_default_outputs(installed_cli_run, "cli gate")
    assert installed_cli_run["native_cache_after"] == []
    assert installed_cli_run["numba_cache_listing"]
